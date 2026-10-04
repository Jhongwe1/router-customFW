#!/usr/bin/env python3
"""diffprobe -- one request/reply row per probe, the SAME instrument on both
columns of `R9`'s differential table.

WHY THIS FILE EXISTS, AND WHAT THE TWO EXISTING INSTRUMENTS CANNOT DO
=====================================================================
`R9` publishes a three-column table whose rows have to be taken with one
instrument on both the vendor firmware and rlxfw.  Nothing committed does that:

  * `tools/hostprobe.py` says of itself that it "records those host events with
    timestamps and nothing else -- never a packet's contents, never a frame".
    Its `tcp` event is a `connect()` outcome, and its own *what it does not
    establish* lists the gap this file fills: "`tcp ... result=ok` means the
    kernel completed a handshake on a listening socket; it does not mean the
    daemon has called `accept()` or would answer a request."  A differential row
    needs the answer, not the handshake.
  * `R7`'s host readings (`bench/2026-09-30/R78-host.txt`) came from a DECLARED
    OFF-CARD CELL -- a shell line, not a reusable instrument -- so they cannot be
    re-taken against the other column by the same code.
  * No tool under `tools/` speaks HTTP at all (量 2026-10-04: no
    `http.client`, `urllib.request` or hand-rolled `GET ` in any of them).

And the vendor column has no other channel.  The vendor firmware HAS NO SHELL
(量, `docs/GATE-RESULTS.md` `P2`'s "⊘ Structural, not deferred": no getty, no
login, `/etc/inittab` wholly commented, `TELNET_ENABLED` 0).  So the only live
vendor-side evidence besides its boot console is network-facing, and this is the
tool that reads it.

WHAT IT IS NOT
--------------
It does not choose the probes.  The probe list is `config/fix-cases.toml`,
written elsewhere; this file is the instrument and the case file is the
contract between the two halves.  It does not grade a reply either: a case's
`expect` is carried into the record as PROSE and never compared, because a
tool that scored its own cases would decide `R9`'s table.

THE CASE FILE -- the contract, version 1
========================================
TOML, read with `tomllib` (stdlib since 3.11; WSL's `/usr/bin/python3` is
3.12.3).  Top level:

    version = 1                  # required, must be 1

and one `[[case]]` table per probe:

    [[case]]
    id     = "H1"                # required; unique; [A-Za-z0-9][A-Za-z0-9_-]*
    kind   = "http"              # required; "http" or "tcp-connect"
    port   = 80                  # required; 1..65535
    why    = "boa's root document"   # required; non-empty prose
    method = "GET"               # http only; GET HEAD POST PUT OPTIONS DELETE
    path   = "/"                 # http only; must start with "/"
    host_header = "10.1.1.1"     # http only; optional, default the target
    headers = { Accept = "*/*" }  # http only; optional; str -> str
    send   = ""                  # http only; optional request body, ASCII
    body   = "digest"            # http only; "none" | "digest" | "excerpt"
    expect = "200, some HTML"    # optional PROSE, carried, never compared

`kind = "tcp-connect"` takes no `method`/`path`/`body`: it is `connect()` and
close, for a port whose protocol is not HTTP.  It is kept here rather than left
to `hostprobe` so that one run, one record and one provenance block cover every
port of a column.

An unknown key, a duplicate `id`, a missing required key, a `body` outside the
three modes, a port outside 1..65535 and a `path` not starting with `/` are each
a REFUSAL naming the case and the key.  There is no default case list: a file
with no `[[case]]` is refused, because an empty list would produce an empty
record and an empty record compares equal to another empty one.

THE FIVE REPLY STATES, AND WHY *empty body* IS NOT *no reply*
=============================================================
These are different findings about a daemon and collapsing them is the defect
this section exists to prevent.  A daemon that answered `200` with a
zero-length body is serving; a daemon that accepted the connection and sent
nothing is not.  `reply` is one of:

    no-connect    `connect()` did not complete.  `result` carries hostprobe's
                  own classification (refused / timeout / unreachable / error)
                  and `why` the errno name.  NOTHING was sent.
    no-reply      the connection completed, the request went out, and ZERO
                  bytes came back.  `why` separates the two ways that happens:
                  `eof` (the peer closed) and `timeout` (the peer held the
                  connection open and said nothing).
    malformed     bytes came back and they are not an HTTP reply: no CRLFCRLF
                  inside `--header-max`, a closed connection mid-headers, or a
                  first line that is not `HTTP/x.y NNN`.  `why` says which.
    headers-only  a well-formed reply whose body is ZERO bytes.
                  `body_state` is `empty` and `body_sha256` is `-`.
    body          a well-formed reply with a body of one or more bytes.

🔴 `body_sha256` is `-` for `headers-only` ON PURPOSE.  sha256 of the empty
string is a real digest (`e3b0c442...`), so writing it would make *the daemon
answered with no body* indistinguishable, in the one field a table is most
likely to be read from, from *the daemon answered with a body that happened to
be empty* -- and from a row whose body was never read.  `body_state` carries
that distinction and the digest field refuses to carry it.  `U2`/`U3` hold it
in BOTH directions.

`connect-ok` is the fifth state and belongs only to `kind = "tcp-connect"`.

WHAT MAY LEAVE THIS PROCESS -- the reason this tool is not hostprobe
=====================================================================
This tool records CONTENTS, which is exactly what `hostprobe` refuses to do,
so the address gate is stricter here rather than looser.

The gate is `hostprobe`'s, IMPORTED and not restated -- `Redactor`,
`load_mac_allowlist`, `canonical_mac`, `MAC_TEXT_RX` are loaded out of
`tools/hostprobe.py` by path, the way `hostprobe` itself loads
`tools/audit-bench-log.py`'s `ALLOW` and the way `leakscan.py` loads it.  There
is no second copy of the pattern or of the list here (CLAUDE.md: a new tool
imports the rule rather than restating it).  Every string this process writes
-- row lines, the meta, stdout, stderr, `compare`'s table -- goes through one
`Redactor`, so a hardware address the owner's allowlist does not name is
written `unlisted-N`, N its order of first appearance in the run.

🔴 AND A BODY EXCERPT IS WITHHELD, NOT REDACTED, when the scan finds an
address the allowlist does not name.  `hostprobe`'s `A3` does the same with a
failing `ip neigh` poll's output, for the same reason: a redacted blob is still
a blob, and the thing worth recording about it is the COUNT.  So
`body = "excerpt"` yields `body_state=withheld`, `excerpt=-` and
`addr_labelled=N`, and N is the comparable field.  This is a containment rule
that does not depend on how the experiment comes out: it fires on the bytes
measured, not on whether they were expected.

🔴 It matters here and not in the abstract.  讀 `upstream/notes/auth-flow.md`:
`GET /config.dat` on this vendor build is UNAUTHENTICATED and expected to
answer `200` with a `COMPCS` blob -- the unit's whole configuration.  A case
pointed at a path like that must declare `body = "none"` or `"digest"`, and
`--body-max` bounds how much is read whatever it declares.

WHAT IS AND IS NOT WITHHELD, stated so the judgement can be overruled
---------------------------------------------------------------------
`body_sha256` is the sha256 of the RAW bytes read, and it is NOT suppressed by
the address scan.  The reading of CLAUDE.md § Never taken here: the forbidden
thing is "`H601`'s bytes, or their sha256", and a digest of an HTTP body is
neither -- it is not those 8,192 bytes and not their digest.  The bytes
themselves travel only in an excerpt, and that is what the withholding rule
covers.  If the owner reads that rule more widely, the change is one branch in
`body_fields()` and `U7` is the case that would then need its expectation
flipped.

COMPARABILITY -- the two columns, or no table
=============================================
A differential row is worth nothing if the two columns were taken through
different things.  Every run records a PROVENANCE block, and `compare` reads
both records' blocks and REFUSES rather than printing a table when they
disagree.  The fields, and why each one is in the set:

    tool, tool_version   the same code wrote both rows
    cases_sha256         the same case file, byte for byte
    cases_version        the schema
    target               the same address
    host, kernel, python the same workstation
    iface, src           the same cable and the same source address, read from
                         `ip -4 route get TARGET` through hostprobe's own
                         `route_verdict`
    connect_timeout_s, read_timeout_s, header_max, body_max, drain_max
                         the same bounds -- a digest of a body truncated at two
                         different bounds is two different measurements

🔴 `iface` is the one field that needs a word.  This host's adapter is named
`enx<12 hex>` by systemd, which IS a hardware address, so the redactor would
write it `unlisted-N` -- and labels are per run (`hostprobe`'s own note:
"`unlisted-1` in two runs need not be one address"), so comparing two labels
would be comparing nothing.  The owner's allowlist names this desk's adapter,
so its name is written verbatim and the two runs compare.  Any OTHER adapter
is labelled, and `compare` REFUSES a record whose `iface` is a label, naming
the reason: comparability cannot be established for an adapter the allowlist
does not name.  That is the right verdict either way -- it is not a workaround
for the redactor.

WHAT GOES RED, AND THE CONTROL THAT SHOWS IT CAN
================================================
A `compare` that printed `0 differences` would be making a claim, and the two
ways of printing it have to be told apart:

  * a column in which NO case connected is REFUSED, not reported.  `--probe`
    exits 2 and writes no record, and `compare` refuses a record whose
    `connected` count is 0.  `U9` is that case; `U9b` is the permitting half
    (one connection out of four is enough to report, and the three failures are
    rows).
  * `compare --require-same FIELD[,FIELD...]` exits 1 when a named field
    differs.  `U10` plants a one-field difference between two otherwise
    identical servers and requires exit 1 naming that case and field; `U11` is
    the negative half -- the same server twice, exit 0, zero differences.
    Without `--require-same`, `compare` reports and exits 0, because for `R9` a
    difference is the point and not a failure.

REFUTATION CONDITIONS -- written before the code they test
==========================================================
D1  `reply` tells the five states apart.  Refuted by a reply whose state is
    wrong in either direction.  Controls `U1` (a body), `U2` (headers-only ->
    `empty`, digest `-`), `U3` (accepted and closed -> `no-reply` `eof`), `U3b`
    (accepted and held -> `no-reply` `timeout`), `U4` (a closed port ->
    `no-connect` `refused`), `U5` (garbage, and a reply cut off mid-headers ->
    `malformed`, each with its own `why`), `U6` (`tcp-connect` -> `connect-ok`,
    and the same port through `http` is a different row).
    🔴 `U2` vs `U3`/`U3b` is D1's whole point and is asserted as an
    INEQUALITY, not as two separate expectations.
D2  No hardware address the allowlist does not name leaves this process.
    Refuted by any artefact of a run -- rows, meta, stdout, stderr, `compare`'s
    table -- holding one.  Controls `U7` (a body carrying an unlisted address:
    `withheld`, `addr_labelled` 1, and the address absent from every artefact in
    six spellings, scanned by a scanner written apart from the tool's own
    pattern), `U8` (an ALLOWLISTED address in a body is written verbatim -- the
    permitting half, without which the gate could be a blanket), `U8b` (the
    allowlist unavailable refuses a `probe` before any file exists, and the
    same run with it present runs).
D3  Bounds hold.  No single probe can produce unbounded output.  Control `U12`:
    a 1 MiB body under `--body-max 256` gives `body_bytes=256`,
    `body_truncated=1`, a `dropped` count, and a record whose whole size is
    under a stated cap.
D4  Comparability is checked and not assumed.  Controls `U13` (each field of
    the set differing in turn: refused, naming the field and both values) and
    `U13b` (identical blocks compare, the permitting half).
D5  Every refusal is one line with a reason and no traceback, before any output
    file exists.  Controls `U14`-`U22`, each refused for ITS reason, with the
    permitting half beside it.
D6  The record reads back.  Controls `U23` (every row line parses with this
    file's own reader; the meta carries every declared key) and `U24`
    (`capdate`'s own reader dates the meta from `started_wallclock`, which is
    what keeps a committed record datable -- a record without it turns
    `capdate` red for the whole bench directory).

WHAT IT DOES NOT ESTABLISH
==========================
* That a daemon is correct, or that a reply is the one a browser would get.
  One request, one socket, no cookies, no redirect following, no TLS.
* WHEN a byte crossed the cable.  `t_raw` is when the probe's own `recv`
  returned; `dur_ms` is the whole exchange.  `hostprobe` owns the timeline.
* Anything about a port not in the case file.  This tool does not scan.
* That two equal `body_sha256` values mean two equal bodies, when
  `body_truncated` is 1 on either side: they mean two equal PREFIXES of the
  bound's length.  A prefix digest finds the first difference and nothing
  past it.
* That a withheld excerpt's body held an address.  `MAC_TEXT_RX` is wider than
  one address on purpose (twelve hex digits bounded by non-hex), so a binary
  body will often be withheld on a false match.  That is the direction this
  instrument is deliberately wrong in: a false positive costs an excerpt, a
  miss is a leak.
* Which daemon owns a port.  `docs/KNOWN-ISSUES.md` already records 52869 and
  52881 as 推 `wscd`'s and `miniigd`'s; a reply does not settle it.

Run
    tools/diffprobe.py probe --cases config/fix-cases.toml \\
        --column vendor --target 10.1.1.1 --out bench/<date>/V-DIFF
    tools/diffprobe.py probe --cases config/fix-cases.toml \\
        --column rlxfw  --target 10.1.1.1 --out bench/<date>/R-DIFF
    tools/diffprobe.py compare bench/<date>/V-DIFF bench/<date>/R-DIFF
    tools/diffprobe.py report bench/<date>/V-DIFF
    tools/diffprobe.py --self-test

Exit
    0  the run or the comparison completed
    1  a finding: an instrument failed, or a `--require-same` field differed
    2  REFUSED -- one line, a reason, no traceback, and no output file
"""
import argparse
import contextlib
import errno
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time

try:
    import tomllib
except ImportError:                                   # pragma: no cover
    tomllib = None

TOOL = "diffprobe"
TOOL_VERSION = "1.0"
THIS = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(THIS))
HOSTPROBE_PATH = os.path.join(ROOT, "tools", "hostprobe.py")
CAPDATE_PATH = os.path.join(ROOT, "tools", "capdate.py")

#: Bounds.  Every one is in the comparability set, because a digest taken under
#: one bound is not comparable with a digest taken under another.
DEFAULT_CONNECT_TIMEOUT_S = 2.0
DEFAULT_READ_TIMEOUT_S = 3.0
DEFAULT_HEADER_MAX = 8192
DEFAULT_BODY_MAX = 4096
DEFAULT_DRAIN_MAX = 1 << 20
#: Per-header and per-row caps, so one hostile reply cannot grow a record.
MAX_HEADERS = 64
MAX_HEADER_VALUE = 256
MAX_EXCERPT = 512
#: Compared by name but never by value: the value moves by construction.
VOLATILE_HEADERS = ("date",)

KINDS = ("http", "tcp-connect")
BODY_MODES = ("none", "digest", "excerpt")
METHODS = ("GET", "HEAD", "POST", "PUT", "OPTIONS", "DELETE")
REPLY_STATES = ("no-connect", "no-reply", "malformed", "headers-only", "body",
                "connect-ok")
BODY_STATES = ("not-requested", "no-reply", "empty", "digest", "excerpt",
               "withheld")
ID_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
CASE_KEYS_REQUIRED = ("id", "kind", "port", "why")
CASE_KEYS_HTTP = ("method", "path", "host_header", "headers", "send", "body")
CASE_KEYS_OPTIONAL = ("expect", "register_id") + CASE_KEYS_HTTP
#: The tier of `config/fix-cases.toml` whose evidence is live and
#: network-facing -- the only tier this instrument can take (PROGRESS.md's
#: `V-A` row).  `V-B` is static, `V-C` the boot console, `V-D` ⊘ Structural.
LIVE_TIER = "V-A"
STATUS_RX = re.compile(r"^HTTP/(\d)\.(\d) (\d{3})(?: (.*))?$")

#: The fields `compare` reads out of both metas before it prints anything.
PROVENANCE_FIELDS = ("tool", "tool_version", "cases_sha256", "cases_version",
                     "target", "host", "kernel", "python", "iface", "src",
                     "connect_timeout_s", "read_timeout_s", "header_max",
                     "body_max", "drain_max")
#: The per-case fields a row carries, in the order a row line writes them.
ROW_FIELDS = ("id", "kind", "port", "method", "path", "t_raw", "dur_ms",
              "reply", "result", "why", "status", "reason", "hdr_n",
              "hdr_names", "hdr_sha256", "body_state", "body_bytes",
              "body_truncated", "dropped", "body_sha256", "addr_labelled",
              "excerpt")
#: What `compare` puts side by side.  Deliberately not every row field: `t_raw`
#: and `dur_ms` are timings and belong to `hostprobe`'s axis, not to a
#: differential row.
COMPARE_FIELDS = ("reply", "result", "why", "status", "reason", "hdr_n",
                  "hdr_names", "hdr_sha256", "body_state", "body_bytes",
                  "body_truncated", "body_sha256", "addr_labelled", "excerpt")

HEADER_ROWS = ("# %s %s rows: one line per case, `k=v` in ROW_FIELDS order; "
               "t_raw is absolute CLOCK_MONOTONIC_RAW seconds, the clock "
               "hostprobe 1.3 and console-capture 1.5 are read on"
               % (TOOL, TOOL_VERSION))


class Refused(Exception):
    """Anything this tool will not answer.  One line, exit 2, no file."""


# ---------------------------------------------------------------------------
# hostprobe, imported by path.  The address gate and the route reading have one
# owner and this file keeps no copy of either (CLAUDE.md: a new tool imports
# the rule).
# ---------------------------------------------------------------------------
def load_hostprobe(path=None):
    path = path or HOSTPROBE_PATH
    try:
        ldr = importlib.machinery.SourceFileLoader("diffprobe_hostprobe", path)
        spec = importlib.util.spec_from_loader("diffprobe_hostprobe", ldr)
        mod = importlib.util.module_from_spec(spec)
        ldr.exec_module(mod)
    except (Exception, SystemExit) as e:
        raise Refused("%s could not be loaded (%s: %s); this tool records reply "
                      "CONTENTS and will not do that without its address gate"
                      % (_rel(path), type(e).__name__, e)) from None
    for name in ("Redactor", "load_mac_allowlist", "canonical_mac",
                 "MAC_TEXT_RX", "route_verdict", "classify_errno",
                 "AllowlistUnavailable"):
        if not hasattr(mod, name):
            raise Refused("%s has no %s; this tool imports hostprobe's address "
                          "gate rather than restating it, and cannot run "
                          "without it" % (_rel(path), name))
    return mod


def _rel(path):
    try:
        r = os.path.relpath(path, ROOT)
    except ValueError:
        return path
    return path if r.startswith("..") else r


HP = None          #: the hostprobe module, set by use_gate()
REDACT = None      #: one Redactor per process, so a run has one label map


def use_gate(hostprobe_path=None, allowlist_path=None):
    """Load hostprobe and the owner's allowlist into this process.

    Refuses rather than falling back: without the allowlist every address in a
    reply would be labelled, a record would be unreadable, and a later run with
    the list present would disagree with it for no reason on the wire.
    """
    global HP, REDACT
    HP = load_hostprobe(hostprobe_path)
    try:
        allowed = HP.load_mac_allowlist(allowlist_path)
    except HP.AllowlistUnavailable as e:
        raise Refused("the hardware-address allowlist is unavailable (%s). This "
                      "tool writes reply contents, so it refuses rather than "
                      "labelling every address it meets" % e) from None
    REDACT = HP.Redactor(allowed=allowed, loaded=True)
    return REDACT


def say(msg, err=False):
    """The one print path.  Every line through the redactor."""
    text = REDACT.text(msg) if REDACT is not None else str(msg)
    print(text, file=sys.stderr if err else sys.stdout)


def now_raw():
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)


# ---------------------------------------------------------------------------
# Tokens.  A row line is whitespace-delimited `k=v`, so a value carries no
# whitespace and no `=` -- `esc()` is reversible and `unesc()` is its inverse,
# which U23 drives in both directions.
# ---------------------------------------------------------------------------
_SAFE = set(chr(c) for c in range(0x21, 0x7F)) - set("%=")


def esc(s):
    out = []
    for ch in str(s):
        out.append(ch if ch in _SAFE
                   else "".join("%%%02X" % b for b in ch.encode("utf-8")))
    return "".join(out) or "-"


def unesc(s):
    if s == "-":
        return ""
    out = bytearray()
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 3 <= len(s):
            try:
                out.append(int(s[i + 1:i + 3], 16))
            except ValueError:
                raise ValueError("bad %%-escape at %d in %r" % (i, s))
            i += 3
        else:
            out += s[i].encode("utf-8")
            i += 1
    return out.decode("utf-8", "replace")


def tok(v):
    if v is None or v == "":
        return "-"
    return esc(v)


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# The case file.
# ---------------------------------------------------------------------------
def load_cases(path):
    """(version, [case], sha256) or Refused.  Reads nothing but the file."""
    if tomllib is None:
        raise Refused("this Python has no `tomllib` (added in 3.11); bench "
                      "commands run /usr/bin/python3, which is 3.12 here")
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise Refused("cannot read the case file %s: %s" % (_rel(path), e))
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise Refused("%s is not readable TOML: %s" % (_rel(path), e))
    ver = doc.get("version")
    if ver != 1:
        raise Refused("%s has version %r; this tool reads version 1 only"
                      % (_rel(path), ver))
    raws = doc.get("case")
    if not isinstance(raws, list) or not raws:
        raise Refused("%s holds no [[case]] table. An empty case list would "
                      "produce an empty record, and two empty records compare "
                      "equal -- so it is refused rather than run" % _rel(path))
    unknown_top = sorted(set(doc) - {"version", "case"})
    if unknown_top:
        raise Refused("%s has unknown top-level key(s) %s; version 1 takes "
                      "`version` and `[[case]]` only"
                      % (_rel(path), ", ".join(unknown_top)))
    cases, seen = [], set()
    for i, c in enumerate(raws, 1):
        cases.append(_one_case(path, i, c, seen))
    return ver, cases, sha(raw)


def _one_case(path, i, c, seen):
    where = "%s [[case]] #%d" % (_rel(path), i)
    if not isinstance(c, dict):
        raise Refused("%s is not a table" % where)
    for k in CASE_KEYS_REQUIRED:
        if k not in c:
            raise Refused("%s has no `%s`" % (where, k))
    cid = c["id"]
    if not isinstance(cid, str) or not ID_RX.match(cid):
        raise Refused("%s: id %r is not [A-Za-z0-9][A-Za-z0-9_-]*" % (where, cid))
    if cid in seen:
        raise Refused("%s: id %r appears twice; a row is cited by its id, so "
                      "two cases cannot share one" % (where, cid))
    seen.add(cid)
    where = "%s (%s)" % (where, cid)
    kind = c["kind"]
    if kind not in KINDS:
        raise Refused("%s: kind %r is not one of %s"
                      % (where, kind, "/".join(KINDS)))
    port = c["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise Refused("%s: port %r is not an integer in 1..65535" % (where, port))
    why = c["why"]
    if not isinstance(why, str) or not why.strip():
        raise Refused("%s: `why` is empty; a probe with no stated reason does "
                      "not belong in a differential table" % where)
    allowed = set(CASE_KEYS_REQUIRED) | set(CASE_KEYS_OPTIONAL)
    if kind == "tcp-connect":
        allowed -= set(CASE_KEYS_HTTP)
    unknown = sorted(set(c) - allowed)
    if unknown:
        raise Refused("%s: unknown key(s) %s for kind %r"
                      % (where, ", ".join(unknown), kind))
    rid = c.get("register_id", "")
    if not isinstance(rid, str) or (rid and not ID_RX.match(rid)):
        raise Refused("%s: register_id %r is not a row id" % (where, rid))
    out = dict(id=cid, kind=kind, port=port, why=why.strip(), register_id=rid,
               expect=str(c.get("expect", "")).strip(),
               method="", path="", host_header="", headers=[], send="",
               body="none")
    if kind == "http":
        method = c.get("method", "GET")
        if method not in METHODS:
            raise Refused("%s: method %r is not one of %s"
                          % (where, method, "/".join(METHODS)))
        p = c.get("path", "/")
        if not isinstance(p, str) or not p.startswith("/"):
            raise Refused("%s: path %r does not start with `/`" % (where, p))
        if any(ch in p for ch in " \r\n\t"):
            raise Refused("%s: path %r holds whitespace" % (where, p))
        hdrs = c.get("headers", {})
        if not isinstance(hdrs, dict):
            raise Refused("%s: `headers` is not a table of str -> str" % where)
        pairs = []
        for k, v in hdrs.items():
            if not isinstance(v, str):
                raise Refused("%s: header %r has a non-string value %r"
                              % (where, k, v))
            if not re.match(r"^[A-Za-z0-9][A-Za-z0-9-]*$", k) or \
               any(ch in v for ch in "\r\n"):
                raise Refused("%s: header %r: %r is not a single header line"
                              % (where, k, v))
            pairs.append((k, v))
        send = c.get("send", "")
        if not isinstance(send, str):
            raise Refused("%s: `send` is not a string" % where)
        try:
            send.encode("ascii")
        except UnicodeEncodeError:
            raise Refused("%s: `send` is not ASCII" % where)
        body = c.get("body", "digest")
        if body not in BODY_MODES:
            raise Refused("%s: body %r is not one of %s"
                          % (where, body, "/".join(BODY_MODES)))
        hh = c.get("host_header", "")
        if not isinstance(hh, str) or any(ch in hh for ch in " \r\n"):
            raise Refused("%s: host_header %r is not one token" % (where, hh))
        out.update(method=method, path=p, host_header=hh, headers=pairs,
                   send=send, body=body)
    return out


# ---------------------------------------------------------------------------
# `R9-1`'s register, and the coverage accounting that keeps a hole from
# reading as a zero.
#
# 量 2026-10-04 on the committed `config/fix-cases.toml`: 141 `[[row]]`,
# `schema_version = 1`, tiers V-A 89 / V-B 29 / V-C 10 / V-D 13, and NOT ONE
# row carries a port, a path or a method (`grep -cE '^(port|path|method) ='`
# reads 0).  So the register is NOT a probe list and this tool cannot read it
# as one -- `load_cases` refuses it outright, because its top level has
# `schema_version` and `[[row]]` where a case file has `version` and
# `[[case]]`.
#
# What the register IS, for this instrument, is the KEYED POPULATION.  Each
# `V-A` row says the case needs live, network-facing evidence; `R9-6`'s DoD
# says the host runs EVERY `V-A` probe.  89 of them, one vendor boot, and no
# file yet maps a row to a request.  So a case may cite its row by
# `register_id`, and with `--register` this tool:
#
#   * refuses a case citing a row that does not exist;
#   * refuses a case citing a row whose tier is NOT `V-A` -- the defect
#     `R9-1`'s own DoD names, "silently converts a `V-D` into a fake `V-A`";
#   * names every `V-A` row NO case covers, and REFUSES unless each one is
#     exempted by `--allow-uncovered` BY NAME (CLAUDE.md: by name, never by
#     date or pattern);
#   * sweeps that exemption list BOTH WAYS -- an exemption naming a row that
#     IS covered, or a row that is not `V-A` at all, is itself a refusal, so
#     the list cannot go stale unreported.
#
# Without `--register` the `register_id` is carried into the record and not
# checked, so a probe list can be written and run before the mapping exists.
# ---------------------------------------------------------------------------
def load_register(path):
    """(schema_version, {id: row}, sha256) or Refused."""
    if tomllib is None:
        raise Refused("this Python has no `tomllib` (added in 3.11)")
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise Refused("cannot read the register %s: %s" % (_rel(path), e))
    try:
        doc = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise Refused("%s is not readable TOML: %s" % (_rel(path), e))
    if "schema_version" not in doc:
        raise Refused("%s has no `schema_version`; it is not `R9-1`'s register "
                      "(a case file has `version` and `[[case]]`, a register "
                      "`schema_version` and `[[row]]`)" % _rel(path))
    rows = doc.get("row")
    if not isinstance(rows, list) or not rows:
        raise Refused("%s holds no [[row]]; an empty register would make every "
                      "coverage count 0 for free" % _rel(path))
    out = {}
    for i, r in enumerate(rows, 1):
        if not isinstance(r, dict) or "id" not in r or "evidence_tier" not in r:
            raise Refused("%s [[row]] #%d has no `id` or no `evidence_tier`"
                          % (_rel(path), i))
        if r["id"] in out:
            raise Refused("%s [[row]] #%d repeats id %r"
                          % (_rel(path), i, r["id"]))
        out[r["id"]] = r
    live = [k for k, r in out.items() if r["evidence_tier"] == LIVE_TIER]
    if not live:
        raise Refused("%s holds no `%s` row. A register with no live tier would "
                      "make this instrument's coverage vacuous -- every case "
                      "would be uncovered-by-nothing and the count would be 0 "
                      "by construction" % (_rel(path), LIVE_TIER))
    return doc["schema_version"], out, sha(raw)


def check_coverage(reg, cases, allow_uncovered, reg_path):
    """Tie the case list to the register, or Refuse.  -> the record's block."""
    live = sorted(k for k, r in reg.items() if r["evidence_tier"] == LIVE_TIER)
    cited = {}
    for c in cases:
        rid = c.get("register_id", "")
        if not rid:
            raise Refused(
                "case %s carries no `register_id`, and --register %s was "
                "given. With a register every probe names the row it is "
                "evidence for, or the table cannot say which rows this run "
                "covered" % (c["id"], _rel(reg_path)))
        if rid not in reg:
            raise Refused("case %s cites register_id %r, which is not a row of "
                          "%s" % (c["id"], rid, _rel(reg_path)))
        tier = reg[rid]["evidence_tier"]
        if tier != LIVE_TIER:
            raise Refused(
                "case %s cites %s, whose evidence_tier is %r and not %r. This "
                "instrument sends a request and reads a reply, so probing a "
                "row of another tier would publish a static or ⊘ Structural "
                "row as live evidence -- a fake %s, which is `R9-1`'s own "
                "named defect"
                % (c["id"], rid, tier, LIVE_TIER, LIVE_TIER))
        cited.setdefault(rid, []).append(c["id"])
    uncovered = [k for k in live if k not in cited]
    allow = [a for a in allow_uncovered if a]
    # BOTH WAYS.  A list that may only grow is a list nobody re-derives.
    stale = [a for a in allow if a in cited]
    notlive = [a for a in allow if a not in live]
    if stale:
        raise Refused("--allow-uncovered names %s, which %s covered. An "
                      "exemption for a row that no longer needs one is a stale "
                      "list, not a pass"
                      % (", ".join(stale),
                         "is" if len(stale) == 1 else "are"))
    if notlive:
        raise Refused("--allow-uncovered names %s, which %s not a %s row of %s"
                      % (", ".join(notlive),
                         "is" if len(notlive) == 1 else "are",
                         LIVE_TIER, _rel(reg_path)))
    missing = [k for k in uncovered if k not in allow]
    if missing:
        raise Refused(
            "%d of %d %s row(s) of %s have no probe in this case file: %s%s. "
            "`R9-6`'s DoD is that the host runs EVERY %s probe, and a run that "
            "silently covered %d of them would publish a coverage hole as a "
            "result. Add a case, or exempt each row BY NAME with "
            "--allow-uncovered"
            % (len(missing), len(live), LIVE_TIER, _rel(reg_path),
               ", ".join(missing[:12]),
               "" if len(missing) <= 12 else " (+%d more)" % (len(missing) - 12),
               LIVE_TIER, len(cited)))
    return {"path": _rel(os.path.abspath(reg_path)), "live_tier": LIVE_TIER,
            "live_rows": len(live), "covered": len(cited),
            "uncovered": uncovered, "allowed_uncovered": sorted(allow),
            "by_row": dict((k, sorted(v)) for k, v in cited.items())}


# ---------------------------------------------------------------------------
# The exchange.  Every read is bounded and every bound is in the record.
# ---------------------------------------------------------------------------
def build_request(case, target):
    host = case["host_header"] or target
    lines = ["%s %s HTTP/1.1" % (case["method"], case["path"]),
             "Host: %s" % host]
    have = set(k.lower() for k, _v in case["headers"])
    for k, v in case["headers"]:
        lines.append("%s: %s" % (k, v))
    if "connection" not in have:
        lines.append("Connection: close")
    if case["send"] and "content-length" not in have:
        lines.append("Content-Length: %d" % len(case["send"]))
    return ("\r\n".join(lines) + "\r\n\r\n" + case["send"]).encode("ascii")


def read_reply(sock, bounds):
    """(buf, header_end, why) -- bounded.  `why` is why reading stopped:
    eof, timeout, header-overflow, body-bound, or errno:NAME."""
    header_max, body_max, drain_max = bounds
    buf = bytearray()
    header_end = -1
    why = None
    while True:
        if header_end >= 0 and len(buf) - header_end >= body_max:
            why = "body-bound"
            break
        try:
            chunk = sock.recv(8192)
        except socket.timeout:
            why = "timeout"
            break
        except OSError as e:
            why = "errno:%s" % errno.errorcode.get(e.errno, str(e.errno))
            break
        if not chunk:
            why = "eof"
            break
        buf += chunk
        if header_end < 0:
            i = bytes(buf).find(b"\r\n\r\n")
            if i >= 0:
                header_end = i + 4
                # The bound is on the HEADER BLOCK, not on how much had been
                # read when the terminator turned up: one recv can carry the
                # whole of an over-long block, and the first draft let a
                # 9,022-byte block through an 8,192-byte bound that way
                # (量, U5 caught it: `headers-only`, not `malformed`).
                if header_end > header_max:
                    why = "header-overflow"
                    break
            elif len(buf) > header_max:
                why = "header-overflow"
                break
    dropped = 0
    if why == "body-bound":
        # Drain and COUNT, never store: a row says how much it did not keep.
        while dropped < drain_max:
            try:
                chunk = sock.recv(8192)
            except (socket.timeout, OSError):
                break
            if not chunk:
                break
            dropped += len(chunk)
    return bytes(buf), header_end, why, dropped


def parse_headers(block):
    """[(lower name, value)] from the bytes before CRLFCRLF, status line cut
    off already.  Bounded by MAX_HEADERS and MAX_HEADER_VALUE."""
    out = []
    for line in block.split(b"\r\n"):
        if not line:
            continue
        if b":" not in line:
            continue
        k, v = line.split(b":", 1)
        out.append((k.decode("latin-1").strip().lower(),
                    v.decode("latin-1").strip()[:MAX_HEADER_VALUE]))
        if len(out) >= MAX_HEADERS:
            break
    return out


def count_unlisted(text):
    """How many address-shaped runs in `text` the allowlist does not name.

    Pure: it allocates no label and reads only the loaded allowlist, so a
    withholding decision does not depend on what the run has already seen.
    """
    n = 0
    for m in HP.MAC_TEXT_RX.finditer(str(text)):
        c = HP.canonical_mac(m.group(0))
        if c is None or c not in REDACT.allowed:
            n += 1
    return n


def body_fields(mode, state, body, truncated):
    """(body_state, body_sha256, excerpt, addr_labelled) for one reply.

    `headers-only` carries `body_sha256` `-` whatever the mode asks for: the
    empty string's digest would make an empty body look like a measured one.
    """
    if state in ("no-connect", "malformed"):
        return "not-requested", "", "", 0
    if state == "no-reply":
        return "no-reply", "", "", 0
    if state == "connect-ok":
        return "not-requested", "", "", 0
    if state == "headers-only":
        return "empty", "", "", 0
    if mode == "none":
        return "not-requested", "", "", 0
    if mode == "digest":
        return "digest", sha(body), "", 0
    text = body.decode("latin-1")
    n = count_unlisted(text)
    if n:
        # hostprobe's A3: the output is WITHHELD, not redacted.  The count is
        # what a differential row needs and the bytes are not.
        return "withheld", sha(body), "", n
    return "excerpt", sha(body), text[:MAX_EXCERPT], 0


def probe_one(case, target, bounds, timeouts):
    """One case -> one row dict.  Opens one socket and closes it."""
    connect_timeout, read_timeout = timeouts
    row = dict((f, "") for f in ROW_FIELDS)
    row.update(id=case["id"], kind=case["kind"], port=case["port"],
               method=case["method"], path=case["path"],
               body_truncated=0, dropped=0, addr_labelled=0, hdr_n=0)
    t0 = now_raw()
    row["t_raw"] = "%.6f" % t0
    sock = None
    try:
        sock = socket.create_connection((target, case["port"]),
                                        timeout=connect_timeout)
    except socket.timeout:
        row.update(reply="no-connect", result="timeout", why="ETIMEDOUT")
    except OSError as e:
        res, name = HP.classify_errno(e.errno or 0)
        if not e.errno:
            res, name = "error", type(e).__name__
        row.update(reply="no-connect", result=res, why=name)
    if sock is not None:
        try:
            if case["kind"] == "tcp-connect":
                row.update(reply="connect-ok", result="ok", why="-")
            else:
                sock.settimeout(read_timeout)
                sock.sendall(build_request(case, target))
                buf, hend, why, dropped = read_reply(sock, bounds)
                row["dropped"] = dropped
                row["body_truncated"] = 1 if why == "body-bound" else 0
                row["result"] = "ok"
                row["why"] = why
                if not buf:
                    row["reply"] = "no-reply"
                elif why == "header-overflow":
                    row["reply"] = "malformed"
                    row["why"] = "header-overflow"
                elif hend < 0:
                    row["reply"] = "malformed"
                    row["why"] = "no-crlfcrlf-%s" % why
                else:
                    first, _, rest = buf[:hend - 4].partition(b"\r\n")
                    m = STATUS_RX.match(first.decode("latin-1").strip())
                    if not m:
                        row["reply"] = "malformed"
                        row["why"] = "not-a-status-line"
                    else:
                        # One recv can bring more body than the bound, so the
                        # bound is applied HERE as well as in the read loop:
                        # body_bytes is what the digest covers and nothing else.
                        body = buf[hend:]
                        over = len(body) - bounds[1]
                        if over > 0:
                            row["dropped"] += over
                            row["body_truncated"] = 1
                            body = body[:bounds[1]]
                        row["status"] = m.group(3)
                        row["reason"] = (m.group(4) or "").strip()
                        hdrs = parse_headers(rest)
                        row["hdr_n"] = len(hdrs)
                        row["hdr_names"] = ",".join(sorted(k for k, _v in hdrs))
                        stable = sorted((k, v) for k, v in hdrs
                                        if k not in VOLATILE_HEADERS)
                        row["hdr_sha256"] = sha(
                            "\n".join("%s:%s" % kv for kv in stable)
                            .encode("utf-8"))
                        row["reply"] = "headers-only" if not body else "body"
                        row["body_bytes"] = len(body)
                        st, dg, ex, n = body_fields(case["body"], row["reply"],
                                                    body, row["body_truncated"])
                        row.update(body_state=st, body_sha256=dg, excerpt=ex,
                                   addr_labelled=n)
        except OSError as e:
            row.update(reply="malformed",
                       why="errno:%s" % errno.errorcode.get(e.errno,
                                                            str(e.errno)))
        finally:
            try:
                sock.close()
            except OSError:
                pass
    if not row["body_state"]:
        st, dg, ex, n = body_fields(case["body"], row["reply"] or "no-connect",
                                    b"", 0)
        row.update(body_state=st, body_sha256=dg, excerpt=ex, addr_labelled=n)
    row["dur_ms"] = "%.3f" % ((now_raw() - t0) * 1e3)
    return row


# ---------------------------------------------------------------------------
# Provenance.
# ---------------------------------------------------------------------------
def host_route(target, ip_cmd):
    """(iface, src) through hostprobe's own route_verdict, or Refused."""
    try:
        p = subprocess.run([ip_cmd, "-4", "route", "get", target],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as e:
        raise Refused("`%s -4 route get %s` could not run: %s"
                      % (ip_cmd, target, e))
    ok, dev, src, whynot = HP.route_verdict(target, p.returncode,
                                            (p.stdout or "") + (p.stderr or ""))
    if not ok:
        raise Refused(whynot)
    return dev, src


def provenance(target, cases_sha, cases_ver, bounds, timeouts, ip_cmd):
    header_max, body_max, drain_max = bounds
    dev, src = host_route(target, ip_cmd)
    u = os.uname()
    return {
        "tool": TOOL, "tool_version": TOOL_VERSION,
        "cases_sha256": cases_sha, "cases_version": cases_ver,
        "target": target,
        "host": platform.node(), "kernel": "%s %s" % (u.sysname, u.release),
        "python": platform.python_version(),
        # An `enx<12 hex>` name IS an address: the redactor labels it unless the
        # owner's allowlist names this desk's adapter, and `compare` refuses a
        # labelled one rather than comparing two per-run labels.
        # 🔴 `text()` and NOT `address()`: `address()` takes its argument as
        # KNOWN to be an address and labels anything the allowlist does not
        # name, so it labelled `dptest0` -- an interface name that is not an
        # address at all -- and every comparison then refused.  量, U10/U11/
        # U13b/U15 all went red on it.  `text()` labels only the runs
        # MAC_TEXT_RX finds, which is what an interface name needs.
        "iface": REDACT.text(dev), "src": src,
        "connect_timeout_s": timeouts[0], "read_timeout_s": timeouts[1],
        "header_max": header_max, "body_max": body_max, "drain_max": drain_max,
    }


# ---------------------------------------------------------------------------
# The record: PREFIX.rows + PREFIX.meta.json, each through .tmp + os.replace.
# ---------------------------------------------------------------------------
def fmt_row(row):
    return " ".join("%s=%s" % (f, tok(row[f])) for f in ROW_FIELDS)


def parse_row(line):
    """{field: str} for one row line, or ValueError.  U23 drives it."""
    pairs = [kv.split("=", 1) for kv in line.split()]
    if any(len(p) != 2 for p in pairs):
        raise ValueError("not whitespace-separated `k=v`")
    keys = tuple(k for k, _v in pairs)
    if keys != ROW_FIELDS:
        raise ValueError("fields %s; the format is %s"
                         % (",".join(keys), ",".join(ROW_FIELDS)))
    return dict((k, unesc(v)) for k, v in pairs)


def write_record(prefix, rows, meta, force):
    rows_path, meta_path = prefix + ".rows", prefix + ".meta.json"
    for p in (rows_path, meta_path):
        if os.path.exists(p) and not force:
            raise Refused("%s exists; pass --force to overwrite, or choose "
                          "another --out" % _rel(p))
    d = os.path.dirname(os.path.abspath(prefix))
    if not os.path.isdir(d):
        raise Refused("%s is not a directory; name bench/<date>/ for the day "
                      "the captures are taken" % _rel(d))
    body = HEADER_ROWS + "\n"
    body += "# cases %d  connected %d  column %s\n" % (
        len(rows), sum(1 for r in rows if r["reply"] != "no-connect"),
        meta["column"])
    body += "".join(fmt_row(r) + "\n" for r in rows)
    body = REDACT.text(body)
    blob = json.dumps(REDACT.obj(meta), indent=2, sort_keys=True) + "\n"
    with open(rows_path + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    os.replace(rows_path + ".tmp", rows_path)
    with open(meta_path + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob)
    os.replace(meta_path + ".tmp", meta_path)
    return rows_path, meta_path


def read_record(prefix):
    """(meta, {id: row}) or Refused."""
    if prefix.endswith(".rows") or prefix.endswith(".meta.json"):
        prefix = re.sub(r"\.(rows|meta\.json)$", "", prefix)
    rows_path, meta_path = prefix + ".rows", prefix + ".meta.json"
    try:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, ValueError) as e:
        raise Refused("cannot read %s: %s" % (_rel(meta_path), e))
    if not isinstance(meta, dict) or meta.get("tool") != TOOL:
        raise Refused("%s was not written by %s (tool=%r)"
                      % (_rel(meta_path), TOOL, (meta or {}).get("tool")))
    try:
        with open(rows_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        raise Refused("cannot read %s: %s" % (_rel(rows_path), e))
    rows = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        try:
            r = parse_row(line)
        except ValueError as e:
            raise Refused("%s:%d is malformed: %s" % (_rel(rows_path), n, e))
        if r["id"] in rows:
            raise Refused("%s:%d repeats id %r" % (_rel(rows_path), n, r["id"]))
        rows[r["id"]] = r
    if not rows:
        raise Refused("%s holds no row" % _rel(rows_path))
    return meta, rows


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------
def check_comparable(ma, mb, na, nb):
    """Refused unless the two records' provenance blocks agree."""
    for side, m, nm in ((0, ma, na), (1, mb, nb)):
        prov = m.get("provenance")
        if not isinstance(prov, dict):
            raise Refused("%s carries no provenance block; it cannot be a "
                          "column of a differential table" % nm)
        missing = [f for f in PROVENANCE_FIELDS if f not in prov]
        if missing:
            raise Refused("%s's provenance has no %s"
                          % (nm, ", ".join(missing)))
        if str(prov["iface"]).startswith("unlisted-"):
            raise Refused(
                "%s was taken through an adapter the owner's allowlist does "
                "not name (iface reads %r). A per-run label is not an identity "
                "-- `unlisted-1` in two runs need not be one adapter -- so "
                "comparability cannot be established and no table is printed"
                % (nm, prov["iface"]))
        if int(m.get("connected", 0)) <= 0:
            raise Refused("%s has connected=0: not one case completed a "
                          "connection, so every row in it is a statement about "
                          "the host and none about the board" % nm)
    pa, pb = ma["provenance"], mb["provenance"]
    bad = [(f, pa[f], pb[f]) for f in PROVENANCE_FIELDS if pa[f] != pb[f]]
    if bad:
        lines = ["the two columns are not comparable; %d provenance field(s) "
                 "differ:" % len(bad)]
        lines += ["  %-18s %s != %s" % (f, a, b) for f, a, b in bad]
        raise Refused("\n".join(lines))


def compare(pa, pb, require_same=(), out=None):
    out = out if out is not None else sys.stdout
    """(n_diff, n_required_diff).  Prints one block per case."""
    ma, ra = read_record(pa)
    mb, rb = read_record(pb)
    na, nb = _rel(pa), _rel(pb)
    check_comparable(ma, mb, na, nb)
    ids = sorted(set(ra) | set(rb))
    only_a = sorted(set(ra) - set(rb))
    only_b = sorted(set(rb) - set(ra))
    if only_a or only_b:
        raise Refused("the two columns hold different case ids (%s only in %s; "
                      "%s only in %s). The same case file produced both or "
                      "neither is a column"
                      % (",".join(only_a) or "-", na,
                         ",".join(only_b) or "-", nb))
    bad = [f for f in require_same if f not in COMPARE_FIELDS]
    if bad:
        raise Refused("--require-same %s: not comparable field(s); the fields "
                      "are %s" % (",".join(bad), ",".join(COMPARE_FIELDS)))
    out.write("%-6s %-16s %-30s %-30s %s\n"
              % ("id", "field", ma["column"], mb["column"], "verdict"))
    ndiff = nreq = 0
    for cid in ids:
        a, b = ra[cid], rb[cid]
        for f in COMPARE_FIELDS:
            va, vb = a.get(f, ""), b.get(f, "")
            if va == vb:
                continue
            ndiff += 1
            req = f in require_same
            nreq += 1 if req else 0
            out.write("%-6s %-16s %-30s %-30s %s\n"
                      % (cid, f, REDACT.text(va or "-")[:30],
                         REDACT.text(vb or "-")[:30],
                         "DIFF (required same)" if req else "DIFF"))
    out.write("%d case(s), %d differing field(s)%s\n"
              % (len(ids), ndiff,
                 "" if not require_same else
                 ", %d of them required to be the same" % nreq))
    return ndiff, nreq


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------
def run_probe(args):
    ver, cases, cases_sha = load_cases(args.cases)
    if args.body_max < 1:
        raise Refused("--body-max 0 cannot tell an empty body from an unread "
                      "one; pass 1 or more, or `body = \"none\"` per case")
    if args.header_max < 16:
        raise Refused("--header-max %d is below the shortest status line plus "
                      "CRLFCRLF; a reply could not be parsed at all"
                      % args.header_max)
    bounds = (args.header_max, args.body_max, args.drain_max)
    timeouts = (args.connect_timeout, args.read_timeout)
    # Coverage is decided BEFORE a packet leaves, so a refusal here costs no
    # probe against a board that may be the one-shot vendor boot (`R9-6`).
    regblock = None
    if args.register:
        _sv, reg, regsha = load_register(args.register)
        regblock = check_coverage(reg, cases,
                                  args.allow_uncovered.split(","),
                                  args.register)
        regblock["schema_version"] = _sv
        regblock["sha256"] = regsha
    prov = provenance(args.target, cases_sha, ver, bounds, timeouts, args.ip)
    rows_path = args.out + ".rows"
    if os.path.exists(rows_path) and not args.force:
        raise Refused("%s exists; pass --force to overwrite, or choose another "
                      "--out" % _rel(rows_path))
    start_raw, start_real = now_raw(), time.time()
    rows = [probe_one(c, args.target, bounds, timeouts) for c in cases]
    end_raw = now_raw()
    connected = sum(1 for r in rows if r["reply"] != "no-connect")
    if connected == 0:
        raise Refused(
            "not one of %d case(s) completed a connection to %s. A column of "
            "rows that all read `no-connect` is a statement about this host or "
            "this cable and none about the board, so no record is written -- "
            "the first results were %s"
            % (len(rows), args.target,
               "; ".join("%s:%s/%s" % (r["id"], r["result"], r["why"])
                         for r in rows[:4])))
    meta = {
        "tool": TOOL, "tool_version": TOOL_VERSION, "column": args.column,
        "clock": "CLOCK_MONOTONIC_RAW",
        "start_raw": start_raw, "end_raw": end_raw, "start_real": start_real,
        "started_wallclock": time.strftime("%Y-%m-%dT%H:%M:%S%z",
                                           time.localtime(start_real)),
        "cases": len(rows), "connected": connected,
        "cases_path": _rel(os.path.abspath(args.cases)),
        "provenance": prov,
        "bounds": {"max_headers": MAX_HEADERS,
                   "max_header_value": MAX_HEADER_VALUE,
                   "max_excerpt": MAX_EXCERPT},
        "volatile_headers": list(VOLATILE_HEADERS),
        "row_fields": list(ROW_FIELDS),
        "compare_fields": list(COMPARE_FIELDS),
        "case_prose": dict((c["id"], {"why": c["why"], "expect": c["expect"],
                                      "body": c["body"],
                                      "register_id": c["register_id"]})
                           for c in cases),
        "register": regblock,
        "labels": dict(REDACT.labels),
    }
    rp, mp = write_record(args.out, rows, meta, args.force)
    say("%s %s column=%s %d case(s), %d connected -> %s, %s"
        % (TOOL, TOOL_VERSION, args.column, len(rows), connected,
           _rel(rp), _rel(mp)))
    if regblock:
        say("  register %s: %d %s row(s), %d covered, %d exempted by name"
            % (regblock["path"], regblock["live_rows"], LIVE_TIER,
               regblock["covered"], len(regblock["allowed_uncovered"])))
    for r in rows:
        say("  %-6s %-5s %-12s %-14s %-4s %-12s %s"
            % (r["id"], r["port"], r["kind"], r["reply"],
               r["status"] or "-", r["body_state"],
               tok(r["why"])))
    return 0


def run_report(prefix, out=None):
    out = out if out is not None else sys.stdout
    meta, rows = read_record(prefix)
    p = meta.get("provenance", {})
    out.write("%s %s column=%s  %s\n"
              % (meta.get("tool"), meta.get("tool_version"),
                 meta.get("column"), meta.get("started_wallclock")))
    out.write("  target=%s iface=%s src=%s body_max=%s cases=%s connected=%s\n"
              % (p.get("target"), p.get("iface"), p.get("src"),
                 p.get("body_max"), meta.get("cases"), meta.get("connected")))
    for cid in sorted(rows):
        r = rows[cid]
        out.write("  %-6s %-5s %-12s %-14s %-4s %-12s %s\n"
                  % (cid, r["port"], r["kind"], r["reply"], r["status"] or "-",
                     r["body_state"], r["why"] or "-"))
    return 0


# ---------------------------------------------------------------------------
# The self-test.  Fake HTTP listeners on 127.0.0.1 and a FAKE `ip`, the way
# hostprobe's own suite works: nothing leaves loopback, no device is touched,
# no port of the board is opened, and nothing is installed.
# ---------------------------------------------------------------------------
#: NOT in tools/audit-bench-log.py's ALLOW -- U7 requires it to be withheld.
UNLISTED_MAC = "de:ad:be:ef:00:11"
#: IS in that ALLOW (this desk's bench adapter) -- U8 is the permitting half,
#: without which the gate could be a blanket that withholds everything.
ALLOWED_MAC = "fc:19:28:61:84:c9"
#: A fake `ip -4 route get`: a unicast route with a dev and a src, so
#: route_verdict passes on a loopback target that the real `ip` calls `local`.
_FAKE_IP = ("#!/usr/bin/env python3\n"
            "import sys\n"
            "print('%s dev dptest0 src 10.9.9.2 uid 1000' % sys.argv[-1])\n"
            "print('    cache')\n")


class _Fake(threading.Thread):
    """One listener on 127.0.0.1 whose reply is scripted per request path.

    `script` is {path: action}; an action is one of
      ("close",)                  accept and close with no byte sent
      ("hold", seconds)           accept, say nothing, then close
      ("raw", bytes)              send those bytes verbatim
      ("reply", status, hdrs, body)       a well-formed reply with a body
      ("headers-only", status, hdrs)      a well-formed reply, zero-byte body
    """

    def __init__(self, script, default=("close",)):
        threading.Thread.__init__(self, daemon=True)
        self.script, self.default = dict(script), default
        self.ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ls.bind(("127.0.0.1", 0))
        self.ls.listen(16)
        self.port = self.ls.getsockname()[1]
        self.stopped = False
        self.seen = []

    def run(self):
        while not self.stopped:
            try:
                conn, _ = self.ls.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,),
                             daemon=True).start()

    def _serve(self, conn):
        conn.settimeout(5.0)
        try:
            req = conn.recv(65536)
        except OSError:
            req = b""
        line = req.split(b"\r\n", 1)[0].decode("latin-1")
        self.seen.append(line)
        parts = line.split(" ")
        path = parts[1] if len(parts) >= 3 else "/"
        try:
            self._act(conn, self.script.get(path, self.default))
        except OSError:
            pass
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            conn.close()
        except OSError:
            pass

    @staticmethod
    def _head(status, hdrs, extra):
        s = "HTTP/1.1 %s\r\n" % status
        for k, v in hdrs:
            s += "%s: %s\r\n" % (k, v)
        return (s + extra + "\r\n").encode("latin-1")

    def _act(self, conn, act):
        kind = act[0]
        if kind == "close":
            return
        if kind == "hold":
            time.sleep(act[1])
            return
        if kind == "raw":
            conn.sendall(act[1])
            return
        if kind == "reply":
            conn.sendall(self._head(act[1], act[2],
                                    "Content-Length: %d\r\n" % len(act[3]))
                         + act[3])
            return
        if kind == "headers-only":
            conn.sendall(self._head(act[1], act[2], "Content-Length: 0\r\n"))
            return
        raise AssertionError("unknown fake action %r" % (kind,))

    def close(self):
        self.stopped = True
        try:
            self.ls.close()
        except OSError:
            pass


def _dead_port():
    """A port nothing listens on: bound, read, closed.  connect() -> RST."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _toml(cases, version=1, extra_top=""):
    out = ["version = %d" % version]
    if extra_top:
        out.append(extra_top)
    for c in cases:
        out.append("")
        out.append("[[case]]")
        for k, v in c.items():
            if isinstance(v, int) and not isinstance(v, bool):
                out.append("%s = %d" % (k, v))
            elif isinstance(v, dict):
                out.append("%s = { %s }"
                           % (k, ", ".join('%s = "%s"' % kv
                                           for kv in v.items())))
            else:
                out.append('%s = "%s"' % (k, v))
    return "\n".join(out) + "\n"


def _write(path, text, mode=None):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    if mode is not None:
        os.chmod(path, mode)
    return path


def _call(argv):
    """main(argv) in-process -> (rc, stdout+stderr).  Exercises refuse_args
    and the one print path, not just the library."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            rc = main(argv)
        except SystemExit as e:                     # argparse's own exits
            rc = e.code if isinstance(e.code, int) else 2
    return rc, buf.getvalue()


#: U7's scanner, written apart from the tool's own pattern: the six spellings
#: an address can reach a file in.  If the tool's MAC_TEXT_RX were wrong, this
#: would still find a leak.
def _spellings(mac):
    h = mac.replace(":", "").lower()
    return [mac.lower(), mac.upper(),
            mac.replace(":", "-").lower(), mac.replace(":", "-").upper(),
            h, h.upper(), "enx" + h]


def _scan_artefacts(paths, mac):
    hits = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for sp in _spellings(mac):
            if sp in text:
                hits.append((p, sp))
    return hits


def run_self_test(out=None):
    out = out or sys.stdout
    rows_ok, rows_bad = [], []

    def one_line(s):
        # A failure message often quotes a captured log, and a captured log can
        # hold a line of the shape `  ok    ...`.  ci-census parses case lines
        # by `^ {2}(ok|FAIL)\s{2,}`, so a multi-line FAIL message could forge a
        # case of the outer suite.  Every message is collapsed to one line.
        return " ".join(str(s).split())

    def case(cid, why, fn):
        try:
            fn()
        except AssertionError as e:
            rows_bad.append(cid)
            out.write("  FAIL  %-7s %s -- %s\n" % (cid, why, one_line(e)))
            return
        except Exception as e:                      # noqa: BLE001
            rows_bad.append(cid)
            out.write("  FAIL  %-7s %s -- %s: %s\n"
                      % (cid, why, type(e).__name__, one_line(e)))
            return
        rows_ok.append(cid)
        out.write("  ok    %-7s %s\n" % (cid, why))

    def eq(got, want, what):
        assert got == want, "%s: got %r, wanted %r" % (what, got, want)

    td = tempfile.mkdtemp(prefix="diffprobe-selftest-")
    bench = os.path.join(td, "bench")
    os.makedirs(bench)
    fake_ip = _write(os.path.join(td, "fakeip.py"), _FAKE_IP,
                     stat.S_IRWXU)
    dead = _dead_port()
    srv = _Fake({
        "/body": ("reply", "200 OK", [("Server", "fake/1"),
                                      ("Content-Type", "text/html")],
                  b"<html>hi</html>"),
        "/empty": ("headers-only", "200 OK", [("Server", "fake/1")]),
        "/close": ("close",),
        "/hold": ("hold", 4.0),
        "/garbage": ("raw", b"NOT-HTTP-AT-ALL\r\n\r\nx"),
        "/cut": ("raw", b"HTTP/1.1 200 OK\r\nServer: fake"),
        "/hdrbig": ("raw", b"HTTP/1.1 200 OK\r\nX: " + b"y" * 9000
                    + b"\r\n\r\n"),
        "/unlisted": ("reply", "200 OK", [],
                      ("mac is %s here" % UNLISTED_MAC).encode()),
        "/allowed": ("reply", "200 OK", [],
                     ("mac is %s here" % ALLOWED_MAC).encode()),
        "/big": ("reply", "200 OK", [], b"B" * (1 << 20)),
    })
    srv.start()
    base = [dict(id="BODY", kind="http", port=srv.port, path="/body",
                 body="digest", why="a well-formed reply with a body"),
            dict(id="EMPTY", kind="http", port=srv.port, path="/empty",
                 body="digest", why="a well-formed reply with no body"),
            dict(id="CLOSE", kind="http", port=srv.port, path="/close",
                 body="digest", why="accepted, then closed with no byte"),
            dict(id="HOLD", kind="http", port=srv.port, path="/hold",
                 body="digest", why="accepted, then silent"),
            dict(id="GARB", kind="http", port=srv.port, path="/garbage",
                 body="digest", why="bytes that are not an HTTP reply"),
            dict(id="CUT", kind="http", port=srv.port, path="/cut",
                 body="digest", why="headers cut off mid-way"),
            dict(id="HDRBIG", kind="http", port=srv.port, path="/hdrbig",
                 body="digest", why="headers past --header-max"),
            dict(id="UNL", kind="http", port=srv.port, path="/unlisted",
                 body="excerpt", why="a body carrying an unlisted address"),
            dict(id="ALW", kind="http", port=srv.port, path="/allowed",
                 body="excerpt", why="a body carrying an allowlisted address"),
            dict(id="BIG", kind="http", port=srv.port, path="/big",
                 body="digest", why="a body past --body-max"),
            dict(id="CONN", kind="tcp-connect", port=srv.port,
                 why="connect and close, no request"),
            dict(id="DEAD", kind="http", port=dead, path="/body",
                 body="digest", why="a port nothing listens on")]
    cases_path = _write(os.path.join(td, "cases.toml"), _toml(base))
    common = ["--cases", cases_path, "--target", "127.0.0.1",
              "--ip", fake_ip, "--read-timeout", "0.6",
              "--connect-timeout", "1.0", "--body-max", "256"]
    pfx = os.path.join(bench, "A-DIFF")
    rc, log = _call(["probe", "--out", pfx, "--column", "fakeA"] + common)
    assert rc == 0, "the main probe run exited %d:\n%s" % (rc, log)
    use_gate()
    meta, R = read_record(pfx)

    case("U1", "a reply with a body: body/200/digest, the digest of the bytes",
         lambda: (eq(R["BODY"]["reply"], "body", "reply"),
                  eq(R["BODY"]["status"], "200", "status"),
                  eq(R["BODY"]["reason"], "OK", "reason"),
                  eq(R["BODY"]["body_state"], "digest", "body_state"),
                  eq(R["BODY"]["body_sha256"], sha(b"<html>hi</html>"), "sha"),
                  eq(R["BODY"]["hdr_names"],
                     "content-length,content-type,server", "hdr_names"),
                  eq(R["BODY"]["body_bytes"], "15", "body_bytes")))
    case("U2", "an EMPTY body: headers-only/empty, and NO digest",
         lambda: (eq(R["EMPTY"]["reply"], "headers-only", "reply"),
                  eq(R["EMPTY"]["body_state"], "empty", "body_state"),
                  eq(R["EMPTY"]["body_bytes"], "0", "body_bytes"),
                  eq(R["EMPTY"]["body_sha256"], "", "body_sha256"),
                  eq(R["EMPTY"]["status"], "200", "status")))
    case("U3", "accepted then closed: no-reply/eof, no status",
         lambda: (eq(R["CLOSE"]["reply"], "no-reply", "reply"),
                  eq(R["CLOSE"]["why"], "eof", "why"),
                  eq(R["CLOSE"]["status"], "", "status"),
                  eq(R["CLOSE"]["body_state"], "no-reply", "body_state")))
    case("U3b", "accepted then silent: no-reply/timeout, told from eof",
         lambda: (eq(R["HOLD"]["reply"], "no-reply", "reply"),
                  eq(R["HOLD"]["why"], "timeout", "why"),
                  assert_ne(R["HOLD"]["why"], R["CLOSE"]["why"], "why")))
    case("U3c", "D1's point: *empty body* is not *no reply*, both directions",
         lambda: (assert_ne(R["EMPTY"]["reply"], R["CLOSE"]["reply"], "reply"),
                  assert_ne(R["EMPTY"]["reply"], R["HOLD"]["reply"], "reply"),
                  assert_ne(R["EMPTY"]["body_state"], R["CLOSE"]["body_state"],
                            "body_state"),
                  assert_ne(R["EMPTY"]["body_state"], R["HOLD"]["body_state"],
                            "body_state"),
                  eq(R["EMPTY"]["status"], "200", "an empty body has a status"),
                  eq(R["CLOSE"]["status"], "", "no reply has none"),
                  assert_ne(R["EMPTY"]["body_sha256"], sha(b""),
                            "the empty string's digest must not be written")))
    case("U4", "a dead port: no-connect/refused/ECONNREFUSED, nothing sent",
         lambda: (eq(R["DEAD"]["reply"], "no-connect", "reply"),
                  eq(R["DEAD"]["result"], "refused", "result"),
                  eq(R["DEAD"]["why"], "ECONNREFUSED", "why"),
                  eq(R["DEAD"]["body_state"], "not-requested", "body_state")))
    case("U5", "three malformed shapes, three distinct whys",
         lambda: (eq(R["GARB"]["reply"], "malformed", "GARB reply"),
                  eq(R["GARB"]["why"], "not-a-status-line", "GARB why"),
                  eq(R["CUT"]["reply"], "malformed", "CUT reply"),
                  eq(R["CUT"]["why"], "no-crlfcrlf-eof", "CUT why"),
                  eq(R["HDRBIG"]["reply"], "malformed", "HDRBIG reply"),
                  eq(R["HDRBIG"]["why"], "header-overflow", "HDRBIG why"),
                  eq(len({R["GARB"]["why"], R["CUT"]["why"],
                          R["HDRBIG"]["why"]}), 3, "three distinct whys")))
    case("U6", "tcp-connect is connect-ok and not a reply state",
         lambda: (eq(R["CONN"]["reply"], "connect-ok", "reply"),
                  eq(R["CONN"]["kind"], "tcp-connect", "kind"),
                  eq(R["CONN"]["body_state"], "not-requested", "body_state"),
                  eq(R["CONN"]["status"], "", "status"),
                  assert_ne(R["CONN"]["reply"], R["BODY"]["reply"],
                            "same port, two kinds, two states")))
    case("U7", "an unlisted address in a body: WITHHELD, counted, and absent "
               "from every artefact in seven spellings",
         lambda: (eq(R["UNL"]["body_state"], "withheld", "body_state"),
                  eq(R["UNL"]["addr_labelled"], "1", "addr_labelled"),
                  eq(R["UNL"]["excerpt"], "", "excerpt"),
                  eq(_scan_artefacts([pfx + ".rows", pfx + ".meta.json"],
                                     UNLISTED_MAC), [], "a leak"),
                  eq([s for s in _spellings(UNLISTED_MAC) if s in log], [],
                     "a leak on stdout")))
    case("U8", "an ALLOWLISTED address in a body is written verbatim "
               "(the permitting half)",
         lambda: (eq(R["ALW"]["body_state"], "excerpt", "body_state"),
                  eq(R["ALW"]["addr_labelled"], "0", "addr_labelled"),
                  assert_in(ALLOWED_MAC, R["ALW"]["excerpt"], "excerpt")))
    case("U12", "a 1 MiB body is bounded: 256 kept, truncated, dropped counted,"
                " and the record stays small",
         lambda: (eq(R["BIG"]["body_bytes"], "256", "body_bytes"),
                  eq(R["BIG"]["body_truncated"], "1", "body_truncated"),
                  assert_gt(int(R["BIG"]["dropped"]), 0, "dropped"),
                  eq(R["BIG"]["body_sha256"], sha(b"B" * 256), "sha of 256 B"),
                  assert_lt(os.path.getsize(pfx + ".rows"), 65536,
                            ".rows size")))
    case("U23", "every row line round-trips through this file's own reader, "
                "and the meta carries every declared key",
         lambda: _u23(pfx, meta, R))
    case("U24", "capdate's own reader dates the meta from started_wallclock",
         lambda: _u24(pfx))

    # ---- U9: a column that never connected is refused, not reported --------
    def u9():
        d2 = os.path.join(bench, "nc")
        os.makedirs(d2, exist_ok=True)
        cp = _write(os.path.join(td, "nc.toml"),
                    _toml([dict(id="D1", kind="http", port=dead, path="/",
                                body="digest", why="dead"),
                           dict(id="D2", kind="tcp-connect", port=dead,
                                why="dead too")]))
        p = os.path.join(d2, "N-DIFF")
        rc, lg = _call(["probe", "--cases", cp, "--out", p, "--column", "x",
                        "--target", "127.0.0.1", "--ip", fake_ip,
                        "--connect-timeout", "1.0"])
        eq(rc, 2, "exit code")
        assert "not one of 2 case(s) completed a connection" in lg, lg
        assert not os.path.exists(p + ".rows"), "a record was written anyway"
        assert not os.path.exists(p + ".meta.json"), "a meta was written"
    case("U9", "a column in which nothing connected is REFUSED and writes no "
               "record (a tool reporting 0 is making a claim)", u9)

    def u9b():
        cp = _write(os.path.join(td, "mix.toml"),
                    _toml([dict(id="D1", kind="http", port=dead, path="/",
                                body="digest", why="dead"),
                           dict(id="L1", kind="http", port=srv.port,
                                path="/body", body="digest", why="live")]))
        p = os.path.join(bench, "M-DIFF")
        rc, lg = _call(["probe", "--cases", cp, "--out", p, "--column", "x"]
                       + ["--target", "127.0.0.1", "--ip", fake_ip,
                          "--read-timeout", "0.6", "--connect-timeout", "1.0"])
        eq(rc, 0, "exit code")
        m, rr = read_record(p)
        eq(m["connected"], 1, "connected")
        eq(rr["D1"]["reply"], "no-connect", "the failure is still a row")
    case("U9b", "one live case out of two is enough to report, and the failure "
                "is still a row (the permitting half)", u9b)

    # ---- U10/U11: the planted mismatch, and its negative half --------------
    pa = os.path.join(bench, "P-A")
    pb = os.path.join(bench, "P-B")
    pc = os.path.join(bench, "P-C")
    one = _write(os.path.join(td, "one.toml"),
                 _toml([dict(id="X", kind="http", port=srv.port, path="/x",
                             body="digest", why="one path, two columns")]))
    onecommon = ["--cases", one, "--target", "127.0.0.1", "--ip", fake_ip,
                 "--read-timeout", "0.6", "--connect-timeout", "1.0",
                 "--body-max", "256"]
    srv.script["/x"] = ("reply", "200 OK", [("Server", "aaa")], b"same-body")
    rc_a, _ = _call(["probe", "--out", pa, "--column", "colA"] + onecommon)
    rc_b, _ = _call(["probe", "--out", pb, "--column", "colB"] + onecommon)
    srv.script["/x"] = ("reply", "200 OK", [("Server", "bbb")], b"same-body")
    rc_c, _ = _call(["probe", "--out", pc, "--column", "colC"] + onecommon)

    def u10():
        eq((rc_a, rc_c), (0, 0), "the two probe runs")
        buf = io.StringIO()
        use_gate()
        nd, nr = compare(pa, pc, ("hdr_sha256",), out=buf)
        t = buf.getvalue()
        assert_gt(nd, 0, "differences")
        eq(nr, 1, "required-same differences")
        assert "X" in t and "hdr_sha256" in t and "DIFF (required same)" in t, t
        rc, lg = _call(["compare", pa, pc, "--require-same", "hdr_sha256"])
        eq(rc, 1, "`compare --require-same` exit code on a planted mismatch")
        assert "hdr_sha256" in lg, lg
    case("U10", "a PLANTED one-field mismatch goes RED: compare names the case "
                "and the field and exits 1", u10)

    def u11():
        eq(rc_b, 0, "the second probe run")
        buf = io.StringIO()
        use_gate()
        nd, nr = compare(pa, pb, ("hdr_sha256", "body_sha256", "status"),
                         out=buf)
        eq((nd, nr), (0, 0), "differences against an unchanged server")
        rc, lg = _call(["compare", pa, pb, "--require-same",
                        "hdr_sha256,body_sha256,status"])
        eq(rc, 0, "exit code")
        assert "0 differing field(s)" in lg, lg
    case("U11", "the same server twice: zero differences, exit 0 -- so U10's "
                "red is the plant and not the instrument", u11)

    # ---- U13: comparability -----------------------------------------------
    def u13():
        use_gate()
        for f in PROVENANCE_FIELDS:
            p = _clone_record(pa, os.path.join(bench, "Q-%s" % f),
                              {f: "POISONED"})
            try:
                compare(p, pb, (), out=io.StringIO())
            except Refused as e:
                assert f in str(e), "%s: the refusal does not name it: %s" % (f, e)
            else:
                raise AssertionError("%s differing did not refuse" % f)
        p = _clone_record(pa, os.path.join(bench, "Q-IFACE"),
                          {"iface": "unlisted-1"})
        try:
            compare(p, pb, (), out=io.StringIO())
        except Refused as e:
            assert "allowlist does not name" in str(e), e
        else:
            raise AssertionError("a labelled iface did not refuse")
    case("U13", "each provenance field differing in turn refuses, naming it; a "
                "labelled iface refuses for its own reason", u13)

    def u13b():
        use_gate()
        nd, nr = compare(pa, pb, (), out=io.StringIO())
        eq(nr, 0, "required-same differences")
    case("U13b", "two records with identical provenance DO compare "
                 "(the permitting half)", u13b)

    # ---- U14..U22: the refusals, each with its permitting half -------------
    def _refuses(argv, needle, what):
        rc, lg = _call(argv)
        eq(rc, 2, "%s: exit code (output: %s)" % (what, lg.strip()[:200]))
        assert needle in lg, "%s: wanted %r, got: %s" % (what, needle, lg)
        assert "Traceback" not in lg, "%s: a traceback: %s" % (what, lg)

    def u14():
        for name, text, needle in (
                ("badver", _toml([dict(id="A", kind="http", port=80, path="/",
                                       why="w")], version=2), "version 2"),
                ("nocase", "version = 1\n", "holds no [[case]]"),
                ("dupid", _toml([dict(id="A", kind="http", port=80, path="/",
                                      why="w"),
                                 dict(id="A", kind="tcp-connect", port=81,
                                      why="w")]), "appears twice"),
                ("badkind", _toml([dict(id="A", kind="ftp", port=80,
                                        why="w")]), "is not one of"),
                ("badport", _toml([dict(id="A", kind="http", port=99999,
                                        path="/", why="w")]),
                 "not an integer in 1..65535"),
                ("badbody", _toml([dict(id="A", kind="http", port=80, path="/",
                                        body="all", why="w")]),
                 "is not one of none/digest/excerpt"),
                ("badpath", _toml([dict(id="A", kind="http", port=80,
                                        path="x", why="w")]),
                 "does not start with"),
                ("nowhy", _toml([dict(id="A", kind="http", port=80, path="/",
                                      why=" ")]), "`why` is empty"),
                ("unkkey", _toml([dict(id="A", kind="tcp-connect", port=80,
                                       path="/", why="w")]),
                 "unknown key(s) path"),
                ("badtop", _toml([dict(id="A", kind="http", port=80, path="/",
                                       why="w")], extra_top="colour = 1"),
                 "unknown top-level key"),
                ("badtoml", "version = = 1\n", "not readable TOML")):
            cp = _write(os.path.join(td, "%s.toml" % name), text)
            _refuses(["probe", "--cases", cp, "--out",
                      os.path.join(bench, "X-%s" % name), "--column", "x",
                      "--target", "127.0.0.1", "--ip", fake_ip], needle, name)
        _refuses(["probe", "--cases", os.path.join(td, "nope.toml"), "--out",
                  os.path.join(bench, "X-miss"), "--column", "x",
                  "--target", "127.0.0.1", "--ip", fake_ip],
                 "cannot read the case file", "a missing case file")
    case("U14", "eleven malformed case files and a missing one, each refused "
                "for ITS reason, no traceback", u14)

    def u15():
        _refuses(["probe"] + common + ["--out", os.path.join(bench, "X-t"),
                                       "--column", "x", "--target", "boom"],
                 "not a dotted IPv4", "a bad target")
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", fake_ip, "--out", os.path.join(bench, "X-b"),
                  "--column", "x", "--body-max", "0"],
                 "cannot tell an empty body from an unread one", "--body-max 0")
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", fake_ip, "--out", os.path.join(bench, "X-h"),
                  "--column", "x", "--header-max", "4"],
                 "below the shortest status line", "--header-max 4")
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", fake_ip, "--out", os.path.join(bench, "X-r"),
                  "--column", "x", "--read-timeout", "0"],
                 "must be positive", "--read-timeout 0")
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", fake_ip, "--out", os.path.join(bench, "X-c"),
                  "--column", "!!"], "is not a name", "a bad --column")
        _refuses(["compare", pa, pa], "the same record", "a self-comparison")
        _refuses(["compare", pa, pb, "--require-same", "nosuch"],
                 "not comparable field(s)", "an unknown --require-same field")
    case("U15", "every argument refusal, each for its own reason, and all of "
                "them from refuse_args before a socket opens", u15)

    def u16():
        rc, lg = _call(["probe", "--out", pfx, "--column", "fakeA"] + common)
        eq(rc, 2, "exit code")
        assert "exists; pass --force" in lg, lg
        rc, lg = _call(["probe", "--out", pfx, "--column", "fakeA", "--force"]
                       + common)
        eq(rc, 0, "--force does overwrite (the permitting half): %s" % lg)
    case("U16", "an existing --out refuses, and --force permits", u16)

    def u8b():
        global HP, REDACT
        try:
            use_gate(allowlist_path=os.path.join(td, "no-allowlist.py"))
        except Refused as e:
            assert "allowlist is unavailable" in str(e), e
        else:
            raise AssertionError("a missing allowlist did not refuse")
        use_gate()
        assert ALLOWED_MAC in REDACT.allowed, \
            "the real allowlist does not name the bench adapter"
        try:
            use_gate(hostprobe_path=os.path.join(td, "no-hostprobe.py"))
        except Refused as e:
            assert "could not be loaded" in str(e), e
        else:
            raise AssertionError("a missing hostprobe did not refuse")
        use_gate()
    case("U8b", "no allowlist and no hostprobe each refuse the gate; the real "
                "pair loads and names the bench adapter", u8b)

    def u17():
        bad = _write(os.path.join(td, "localip.py"),
                     "#!/usr/bin/env python3\nprint('local 127.0.0.1 dev lo "
                     "src 127.0.0.1')\n", stat.S_IRWXU)
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", bad, "--out", os.path.join(bench, "X-lo"),
                  "--column", "x"],
                 "one of this host's own addresses", "a local route")
        nosrc = _write(os.path.join(td, "nosrc.py"),
                       "#!/usr/bin/env python3\nprint('10.9.9.9 dev dptest0')\n",
                       stat.S_IRWXU)
        _refuses(["probe", "--cases", cases_path, "--target", "127.0.0.1",
                  "--ip", nosrc, "--out", os.path.join(bench, "X-ns"),
                  "--column", "x"], "HOST FAULT", "a route with no src")
        rc, lg = _call(["probe", "--cases", cases_path, "--target",
                        "127.0.0.1", "--ip", fake_ip, "--out",
                        os.path.join(bench, "X-ok"), "--column", "x",
                        "--read-timeout", "0.6", "--connect-timeout", "1.0",
                        "--body-max", "256"])
        eq(rc, 0, "a route WITH a src passes (the permitting half): %s" % lg)
    case("U17", "the host's own address and a route with no src each refuse "
                "through hostprobe's route_verdict; a good route passes", u17)

    # ---- U18..U21: the register tie-in and its coverage accounting ---------
    regpath = _write(os.path.join(td, "reg.toml"), """schema_version = 1

[[row]]
id = "FCA"
evidence_tier = "V-A"
title = "a live, network-facing row"

[[row]]
id = "FCB"
evidence_tier = "V-A"
title = "a second live row, deliberately left uncovered"

[[row]]
id = "FCD"
evidence_tier = "V-D"
title = "needs a shell, so it is Structural and not probeable"
""")

    def _one_live(rid, cid="L1"):
        return _write(os.path.join(td, "reg-%s-%s.toml" % (rid, cid)),
                      _toml([dict(id=cid, kind="http", port=srv.port,
                                  path="/body", body="digest",
                                  register_id=rid, why="cites %s" % rid)]))

    def _probe_with(cp, out_name, extra=()):
        return _call(["probe", "--cases", cp, "--out",
                      os.path.join(bench, out_name), "--column", "x",
                      "--target", "127.0.0.1", "--ip", fake_ip,
                      "--read-timeout", "0.6", "--connect-timeout", "1.0",
                      "--body-max", "256", "--register", regpath] + list(extra))

    def u18():
        rc, lg = _probe_with(_one_live("FCD", "D1"), "G-vd")
        eq(rc, 2, "a V-D row is refused")
        assert "and not %r" % LIVE_TIER in lg and "FCD" in lg, lg
        assert "'V-D'" in lg, "the refusal does not name the actual tier: %s" % lg
        assert "a fake %s" % LIVE_TIER in lg, \
            "the refusal does not name R9-1's defect: %s" % lg
        rc, lg = _probe_with(_one_live("FCA"), "G-va",
                             ["--allow-uncovered", "FCB"])
        eq(rc, 0, "a V-A row with the other exempted passes: %s" % lg)
        m, _r = read_record(os.path.join(bench, "G-va"))
        eq(m["register"]["live_rows"], 2, "live_rows")
        eq(m["register"]["covered"], 1, "covered")
        eq(m["register"]["uncovered"], ["FCB"], "uncovered")
    case("U18", "a case citing a non-V-A row is refused naming the tier; a V-A "
                "row passes and the record carries the coverage block", u18)

    def u19():
        rc, lg = _probe_with(_one_live("FCA"), "G-hole")
        eq(rc, 2, "an uncovered V-A row refuses")
        assert "FCB" in lg and "have no probe in this case file" in lg, lg
        assert "1 of 2" in lg, "the refusal does not count: %s" % lg
        rc, lg = _probe_with(_one_live("FCA"), "G-stale",
                             ["--allow-uncovered", "FCA,FCB"])
        eq(rc, 2, "a STALE exemption refuses")
        assert "FCA" in lg and "stale list" in lg, lg
        rc, lg = _probe_with(_one_live("FCA"), "G-notlive",
                             ["--allow-uncovered", "FCB,FCD"])
        eq(rc, 2, "an exemption naming a non-V-A row refuses")
        assert "FCD" in lg, lg
        # And the vacuous register: with no V-A row at all, every coverage
        # count is 0 BY CONSTRUCTION and nothing could ever be uncovered, so
        # the guard refuses the register rather than passing it.  量: without
        # this assertion the guard had no case and mutant M17 survived.
        dead = _write(os.path.join(td, "reg-dead.toml"),
                      "schema_version = 1\n\n[[row]]\nid = \"FCZ\"\n"
                      "evidence_tier = \"V-D\"\ntitle = \"no live row here\"\n")
        rc, lg = _call(["probe", "--cases", _one_live("FCA"), "--out",
                        os.path.join(bench, "G-dead"), "--column", "x",
                        "--target", "127.0.0.1", "--ip", fake_ip,
                        "--register", dead])
        eq(rc, 2, "a register with no V-A row refuses")
        assert "holds no `%s` row" % LIVE_TIER in lg and "vacuous" in lg, lg
    case("U19", "an uncovered V-A row refuses and is NAMED and COUNTED; the "
                "exemption list is swept BOTH ways (stale, and not-V-A)", u19)

    def u20():
        rc, lg = _probe_with(_one_live("NOSUCH"), "G-miss")
        eq(rc, 2, "a register_id naming no row refuses")
        assert "NOSUCH" in lg and "not a row of" in lg, lg
        bare = _write(os.path.join(td, "bare.toml"),
                      _toml([dict(id="B1", kind="http", port=srv.port,
                                  path="/body", body="digest",
                                  why="no register_id")]))
        rc, lg = _probe_with(bare, "G-bare", ["--allow-uncovered", "FCA,FCB"])
        eq(rc, 2, "a case with no register_id refuses under --register")
        assert "carries no `register_id`" in lg, lg
        rc, lg = _call(["probe", "--cases", bare, "--out",
                        os.path.join(bench, "G-noreg"), "--column", "x",
                        "--target", "127.0.0.1", "--ip", fake_ip,
                        "--read-timeout", "0.6", "--connect-timeout", "1.0",
                        "--body-max", "256"])
        eq(rc, 0, "the same case file WITHOUT --register runs: %s" % lg)
        m, _r = read_record(os.path.join(bench, "G-noreg"))
        eq(m["register"], None, "register block")
    case("U20", "a register_id naming no row, and a missing register_id under "
                "--register, each refuse; without --register the same file "
                "runs (the permitting half)", u20)

    def u21():
        rp = os.path.join(ROOT, "config", "fix-cases.toml")
        if not os.path.exists(rp):
            raise AssertionError("config/fix-cases.toml is not in the tree; "
                                 "R9-1 owns it and this case reads it live")
        sv, reg, _h = load_register(rp)
        live = [k for k, r in reg.items()
                if r["evidence_tier"] == LIVE_TIER]
        assert_gt(len(reg), 0, "rows")
        assert_gt(len(live), 0, "%s rows" % LIVE_TIER)
        # It is a REGISTER and not a case file, and the case reader must say so
        # rather than half-reading it.
        try:
            load_cases(rp)
        except Refused as e:
            assert "version" in str(e), \
                "the case reader's refusal does not name the schema: %s" % e
        else:
            raise AssertionError("the case reader accepted the register")
    case("U21", "the COMMITTED register loads, holds at least one V-A row, and "
                "is refused by the CASE reader -- a live population", u21)

    srv.close()
    n = len(rows_ok) + len(rows_bad)
    out.write("%d ok, %d FAIL, %d case(s)\n" % (len(rows_ok), len(rows_bad), n))
    if rows_bad:
        # Kept on a red run: the fixtures are the evidence.  Removed on a green
        # one, so a suite that runs on every push does not fill /tmp.
        out.write("red: %s\n" % ", ".join(rows_bad))
        out.write("fixtures kept under %s\n" % td)
        return 1
    shutil.rmtree(td, ignore_errors=True)
    return 0


def assert_ne(a, b, what):
    assert a != b, "%s: both read %r, and they are different findings" % (what, a)


def assert_in(needle, hay, what):
    assert needle in str(hay), "%s: %r not in %r" % (what, needle, hay)


def assert_gt(a, b, what):
    assert a > b, "%s: %r is not greater than %r" % (what, a, b)


def assert_lt(a, b, what):
    assert a < b, "%s: %r is not less than %r" % (what, a, b)


def _u23(pfx, meta, rows):
    with open(pfx + ".rows", encoding="utf-8") as fh:
        text = fh.read()
    assert text.startswith("# %s %s rows:" % (TOOL, TOOL_VERSION)), \
        "the first line does not declare the tool and version"
    body = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    assert len(body) == len(rows), "%d row line(s) for %d row(s)" \
        % (len(body), len(rows))
    for ln in body:
        parse_row(ln)                         # raises on any format drift
    for k in ("tool", "tool_version", "column", "clock", "start_raw",
              "end_raw", "start_real", "started_wallclock", "cases",
              "connected", "cases_path", "provenance", "row_fields",
              "compare_fields", "case_prose", "labels", "volatile_headers"):
        assert k in meta, "the meta has no %s" % k
    assert meta["row_fields"] == list(ROW_FIELDS), "row_fields drifted"
    for f in PROVENANCE_FIELDS:
        assert f in meta["provenance"], "provenance has no %s" % f
    assert set(meta["case_prose"]) == set(rows), "case_prose does not cover"
    broken = "id=X kind=http"
    try:
        parse_row(broken)
    except ValueError:
        pass
    else:
        raise AssertionError("the reader accepted a hand-broken line")


def _u24(pfx):
    ldr = importlib.machinery.SourceFileLoader("diffprobe_capdate",
                                               CAPDATE_PATH)
    spec = importlib.util.spec_from_loader("diffprobe_capdate", ldr)
    mod = importlib.util.module_from_spec(spec)
    ldr.exec_module(mod)
    when, why = mod.capture_when(pfx + ".meta.json")
    assert when is not None, "capdate could not date the record: %s" % why
    with open(pfx + ".meta.json", encoding="utf-8") as fh:
        j = json.load(fh)
    j.pop("started_wallclock")
    p2 = pfx + "-nowall.meta.json"
    with open(p2, "w", encoding="utf-8") as fh:
        json.dump(j, fh)
    when2, why2 = mod.capture_when(p2)
    assert when2 is None and "started_wallclock" in (why2 or ""), \
        "a meta without the key was dated anyway: %r" % (when2,)
    os.remove(p2)


def _clone_record(src, dst, prov_changes):
    """Copy a record, changing provenance fields.  U13's poison."""
    with open(src + ".rows", encoding="utf-8") as fh:
        rows = fh.read()
    with open(src + ".meta.json", encoding="utf-8") as fh:
        meta = json.load(fh)
    meta["provenance"].update(prov_changes)
    with open(dst + ".rows", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(rows)
    with open(dst + ".meta.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    return dst


# ---------------------------------------------------------------------------
# Arguments.  One function reads nothing but the parsed arguments, so a card's
# check and the run refuse the same arguments for the same reason (FW-124).
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(prog="diffprobe.py", add_help=True,
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("probe", help="run the case file against one column")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--column", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--connect-timeout", type=float,
                   default=DEFAULT_CONNECT_TIMEOUT_S)
    p.add_argument("--read-timeout", type=float, default=DEFAULT_READ_TIMEOUT_S)
    p.add_argument("--header-max", type=int, default=DEFAULT_HEADER_MAX)
    p.add_argument("--body-max", type=int, default=DEFAULT_BODY_MAX)
    p.add_argument("--drain-max", type=int, default=DEFAULT_DRAIN_MAX)
    p.add_argument("--ip", default="ip")
    p.add_argument("--register", default="")
    p.add_argument("--allow-uncovered", default="")
    p.add_argument("--force", action="store_true")

    c = sub.add_parser("compare", help="two records -> a differential table")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--require-same", default="")

    r = sub.add_parser("report", help="print one record")
    r.add_argument("prefix")
    return ap


def refuse_args(args):
    """Every refusal that reads nothing but the arguments."""
    if getattr(args, "self_test", False):
        return
    if not getattr(args, "cmd", None):
        raise Refused("no action; the actions are probe, compare, report, and "
                      "--self-test")
    if args.cmd == "probe":
        if not str(args.column).strip() or \
           not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$", args.column):
            raise Refused("--column %r is not a name; it labels a column of "
                          "R9's table (vendor, rlxfw)" % args.column)
        try:
            socket.inet_aton(args.target)
        except OSError:
            raise Refused("--target %r is not a dotted IPv4 address"
                          % args.target)
        for name, v in (("--connect-timeout", args.connect_timeout),
                        ("--read-timeout", args.read_timeout)):
            if not v > 0:
                raise Refused("%s %r must be positive; a non-positive timeout "
                              "would read `no-reply` on every case" % (name, v))
        if args.body_max < 1:
            raise Refused("--body-max 0 cannot tell an empty body from an "
                          "unread one; pass 1 or more, or `body = \"none\"`")
        if args.header_max < 16:
            raise Refused("--header-max %d is below the shortest status line "
                          "plus CRLFCRLF" % args.header_max)
        if args.drain_max < 0:
            raise Refused("--drain-max %d is negative" % args.drain_max)
    if args.cmd == "compare":
        if os.path.abspath(re.sub(r"\.(rows|meta\.json)$", "", args.a)) == \
           os.path.abspath(re.sub(r"\.(rows|meta\.json)$", "", args.b)):
            raise Refused("both columns are the same record (%s); a record "
                          "compared with itself differs nowhere by "
                          "construction" % _rel(args.a))


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        refuse_args(args)
    except Refused as e:
        print("diffprobe: REFUSED: %s" % e, file=sys.stderr)
        return 2
    if args.self_test:
        return run_self_test()
    try:
        use_gate()
        if args.cmd == "probe":
            return run_probe(args)
        if args.cmd == "compare":
            req = tuple(f for f in args.require_same.split(",") if f)
            ndiff, nreq = compare(args.a, args.b, req)
            return 1 if nreq else 0
        if args.cmd == "report":
            return run_report(args.prefix)
    except Refused as e:
        print("diffprobe: REFUSED: %s" % (REDACT.text(str(e))
                                          if REDACT is not None else e),
              file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
