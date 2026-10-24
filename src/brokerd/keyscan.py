#!/usr/bin/env python3
"""src/brokerd/keyscan.py -- how many times a key header's 32 bytes occur in a file.

    keyscan.py <file> <key header>

The header is src/rlxboot/prodkey.h or devkey.h, and the key is read out of
its own `#define RLXBOOT_PRODKEY_HEX` / `RLXBOOT_DEVKEY_HEX` line, so no key
is restated here.  Prints the count of (possibly overlapping) occurrences of
those bytes in <file>; exit 0.  Exit 2, one line, when the header holds no
such line or more than one, or a file cannot be read: a scanner that cannot
say which key it looked for has not looked.

src/brokerd/Makefile's target rule reads the stripped brokerd with it --
the production key at least once, the development key never -- and first
reads an object compiled with the development key, which must show it: the
control that the scanner sees a key that is there.
"""
import re
import sys

PAT = re.compile(r'#define\s+RLXBOOT_(?:PROD|DEV)KEY_HEX\s*\\\s*"([0-9a-f]{64})"')


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 2
    try:
        text = open(argv[2], "r", encoding="utf-8").read()
        data = open(argv[1], "rb").read()
    except OSError as exc:
        sys.stderr.write("keyscan.py: REFUSED: %s\n" % exc)
        return 2
    keys = PAT.findall(text)
    if len(keys) != 1:
        sys.stderr.write("keyscan.py: REFUSED: %s holds %d key lines, want 1\n"
                         % (argv[2], len(keys)))
        return 2
    key = bytes.fromhex(keys[0])
    n, at = 0, data.find(key)
    while at >= 0:
        n += 1
        at = data.find(key, at + 1)
    sys.stdout.write("%d\n" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
