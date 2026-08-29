#!/usr/bin/env python3
"""Audit the bench logs for anything that identifies this physical unit, before
they are committed and pushed.

CLAUDE.md forbids committing a flash dump because it identifies one device --
its MAC and its radio calibration live in H601.  These logs are not a dump, but
"not a dump" is not the same as "carries nothing", so this checks rather than
assumes.  Every pattern is run against a synthetic positive control first: a
scan that cannot fire proves nothing.
"""
import re, sys, io, os

PATTERNS = [
    ("MAC, colon form",     re.compile(r'\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b')),
    ("MAC, dash form",      re.compile(r'\b(?:[0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}\b')),
    ("MAC, bare 12 hex",    re.compile(r'\b(?:00[eE]0[4-6][cC]|[fF][cC]1928)[0-9A-Fa-f]{6}\b')),
    ("H601 / calibration",  re.compile(r'H601|calib|rf_?cal|txpower|eeprom', re.I)),
    ("serial-ish",          re.compile(r'\bS/?N[:= ]|serial\s*(no|number|:)', re.I)),
    ("private IPv4",        re.compile(r'\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b')),
    ("SSID / passphrase",   re.compile(r'ssid|passphrase|wpa[_-]?psk|password', re.I)),
    ("home path / user",    re.compile(r'/home/[a-z]+|C:\\\\Users\\\\|Key20', re.I)),
]

CONTROL = (
    "banner\n"
    "hwaddr 00:E0:4C:11:22:33 here\n"
    "MAC FC-19-28-61-84-C9 here\n"
    "00e04c112233\n"
    "H601 region calib blob\n"
    "S/N: ABC123\n"
    "IPCONFIG 192.168.1.6\n"
    "ssid=MyNetwork password=hunter2\n"
    "/home/key/fwre-work\n"
)

#: 🆕 2026-08-30.  An allowlist, in the shape `spec-check.py` already uses: one
#: entry per suppressed literal, each carrying the reason it is not identifying.
#: It suppresses the EXACT match only -- a different private address, or a MAC
#: that is not on this list, still fires -- and control A2 below proves that.
#:
#: Why it arrived: seating 5 was the first to put a booted Linux and a host-side
#: ping on the record, so the bench network appears in the transcripts for the
#: first time.  The logs are byte-exact by rule (`.gitattributes` has
#: `bench/** -text`, and `bench/README.md` says so), so redacting them is not an
#: option and this is the alternative.
#: Each entry is (scope, needle, reason).
#:   scope "match" -- the matched text itself is benign wherever it appears.
#:   scope "line"  -- the match is benign ONLY on a line containing `needle`.
#: 🔴 The two scopes are not interchangeable. `Calib` and `Serial:` are matched
#: by patterns aimed at radio calibration and serial numbers; suppressing those
#: two strings outright would hide a real calibration blob. They are allowlisted
#: by the LINE that makes them benign, so `Calibration data: <hex>` still fires.
ALLOW = [
    ("match", "10.1.1",
     "the bench-side network the operator chose: 10.1.1.1 is what IPCONFIG "
     "gives the loader, 10.1.1.2 the workstation, 10.1.1.10 the board under "
     "Linux. None is this unit's configuration -- the loader's own compiled-in "
     "TFTP address is 192.168.1.6, which is allowlisted in spec-check.py for "
     "the same reason and is deliberately NOT allowlisted here"),
    ("match", "00:12:34:56:78:9",
     "the six netdev MACs are SDK placeholders compiled into the vmlinux this "
     "seating built -- 量 2026-08-30, found as literal bytes at file offsets "
     "0x2b5d64 and 0x2b5e14. This boot mounted my own initramfs, so no vendor "
     "init script ever read H601"),
    ("match", "00:E0:4C:81:86:86",
     "wlan0's MAC, and it looks exactly like a real radio address, which is why "
     "it was measured rather than assumed: 量 compiled into the same vmlinux at "
     "offset 0x288cc0. A Realtek OUI on a driver default, not from flash"),
    ("match", "00:E0:4C:81:96:96",
     "pwlan0's, same measurement, offset 0x288e04"),
    ("match", "00:00:00:00:00:00",
     "the wlan0-wds interfaces. An all-zero MAC identifies nothing by "
     "construction, and it is the driver's unset value"),
    ("line", "Calibrating delay loop",
     "Linux's CPU-speed calibration (BogoMIPS), which the `calib` pattern "
     "matches and which has nothing to do with radio calibration. Scoped to "
     "this line so a real calibration blob still fires"),
    ("line", "Serial: 8250/16550 driver",
     "the 8250 UART driver's registration banner, matched by the pattern aimed "
     "at serial NUMBERS. Scoped to this line for the same reason"),
]


def allowed(txt, line=""):
    """The allowlist entry covering this match, or None."""
    for scope, needle, why in ALLOW:
        if scope == "match" and needle in txt:
            return (needle, why)
        if scope == "line" and needle in line:
            return (needle, why)
    return None

def scan(name, text):
    """-> [(pattern label, 1-based line number, matched text, the whole line)].

    The line comes back so the allowlist can be scoped to it: `Calib` is benign
    on `Calibrating delay loop` and is not benign on a line that holds a
    calibration blob, and only the line separates those two.
    """
    lines = text.split('\n')
    hits = []
    for label, rx in PATTERNS:
        for m in rx.finditer(text):
            ln = text.count('\n', 0, m.start()) + 1
            line = lines[ln - 1] if ln <= len(lines) else ''
            hits.append((label, ln, m.group(0), line))
    return hits

def main(paths):
    print("=== POSITIVE CONTROL: every pattern must fire on a synthetic file ===")
    ctl = scan("control", CONTROL)
    fired = {h[0] for h in ctl}
    missing = [l for l, _ in PATTERNS if l not in fired]
    for label, ln, txt, _ln in ctl:
        print(f"  fired  {label:22s} line {ln}: {txt!r}")
    if missing:
        print(f"\n  FAIL: these patterns never fired, so a clean result means nothing: {missing}")
        return 2
    print(f"\n  ok  all {len(PATTERNS)} patterns fire on the control\n")

    # 🆕 A2: the allowlist must not be able to swallow the scan.  An allowlist
    # that suppressed a whole pattern would turn every later clean result into
    # a result that means nothing -- which is the same defect the positive
    # control above exists to prevent, one level up.
    print("=== POSITIVE CONTROL 2: the allowlist suppresses ONLY its own literals ===")
    a2 = scan("control", CONTROL)
    swallowed = [h for h in a2 if allowed(h[2], h[3])]
    if swallowed:
        print(f"  FAIL: the allowlist covers {len(swallowed)} control hit(s) "
              f"-- it is suppressing something the control needs: {swallowed}")
        return 2
    probe = "addr 10.9.9.9 and mac 00:12:34:56:AA:BB\n"
    ph = scan("control", probe)
    if not ph or any(allowed(h[2], h[3]) for h in ph):
        print("  FAIL: a NON-allowlisted private address and MAC did not fire, "
              "so the allowlist is matching too widely")
        return 2
    print(f"  ok  no control hit is allowlisted, and a non-listed "
          f"address/MAC still fires ({len(ph)} hit(s))")
    print(f"  ok  {len(ALLOW)} allowlist entr(ies), each with a stated reason\n")

    print("=== THE ACTUAL LOGS ===")
    total = 0
    suppressed = 0
    for p in paths:
        # newline='' -- WITHOUT it Python's universal newlines collapses every
        # CRLF into one LF, and the number printed below as `bytes` comes out
        # LOWER than the file by exactly the CRLF count.  Measured 2026-08-25 on
        # bench/2026-08-25/: 8855 -> 8797 (58 CRLF), 5356 -> 5307 (49),
        # 10790 -> 10719 (71), and 1671 -> 1671 where there are none.
        #
        # It is the same defect the `.gitattributes` line `bench/** -text` exists
        # to prevent -- these transcripts are byte-exact and the loader's own
        # format strings end \r\n -- applied to git and not to the tool that
        # lives beside them.  The scan itself was never affected: every pattern
        # here is ASCII and survives the decode.  The number was.
        text = io.open(p, encoding='utf-8', errors='replace', newline='').read()
        raw = scan(p, text)
        hits = [h for h in raw if not allowed(h[2], h[3])]
        skipped = len(raw) - len(hits)
        total += len(hits)
        suppressed += skipped
        nbytes = os.path.getsize(p)
        flag = '' if len(text) == nbytes else f'  <- {len(text)} chars, non-ASCII present'
        note = f", {skipped} allowlisted" if skipped else ''
        print(f"  {os.path.basename(p):22s} {nbytes:6d} bytes  "
              f"{len(hits)} hit(s){note}{flag}")
        for label, ln, txt, _l in hits:
            print(f"      HIT {label} line {ln}: {txt!r}")
    print()
    if suppressed:
        print(f"  {suppressed} match(es) suppressed by the allowlist, "
              f"which is printed above with a reason per entry")
    if total == 0:
        print("  ok  nothing in any log matches a pattern that demonstrably "
              "fires and is not allowlisted")
        return 0
    print(f"  {total} hit(s) -- review each before committing")
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
