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

def scan(name, text):
    hits = []
    for label, rx in PATTERNS:
        for m in rx.finditer(text):
            ln = text.count('\n', 0, m.start()) + 1
            hits.append((label, ln, m.group(0)))
    return hits

def main(paths):
    print("=== POSITIVE CONTROL: every pattern must fire on a synthetic file ===")
    ctl = scan("control", CONTROL)
    fired = {h[0] for h in ctl}
    missing = [l for l, _ in PATTERNS if l not in fired]
    for label, ln, txt in ctl:
        print(f"  fired  {label:22s} line {ln}: {txt!r}")
    if missing:
        print(f"\n  FAIL: these patterns never fired, so a clean result means nothing: {missing}")
        return 2
    print(f"\n  ok  all {len(PATTERNS)} patterns fire on the control\n")

    print("=== THE ACTUAL LOGS ===")
    total = 0
    for p in paths:
        text = io.open(p, encoding='utf-8', errors='replace').read()
        hits = scan(p, text)
        total += len(hits)
        print(f"  {os.path.basename(p):22s} {len(text):6d} bytes  {len(hits)} hit(s)")
        for label, ln, txt in hits:
            print(f"      HIT {label} line {ln}: {txt!r}")
    print()
    if total == 0:
        print("  ok  nothing in any log matches a pattern that demonstrably fires")
        return 0
    print(f"  {total} hit(s) -- review each before committing")
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
