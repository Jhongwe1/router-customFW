#!/usr/bin/env python3
"""mkprodkey.py -- write, and check, the header that gives a KEY=prod rlxboot
its update key (the R8b spec's D15).

    mkprodkey.py write --pubkey <64 hex> [--out PATH]
    mkprodkey.py none [--out PATH]
    mkprodkey.py check [PATH]
    mkprodkey.py --self-test

PATH defaults to `prodkey.h` beside this script: the file a KEY=prod build
stages, compiles in and hashes into BUILD_ID (the Makefile's PRODKEY_H).

WHAT GOES IN.  The owner generates a 32-byte seed outside this repository and
outside WSL and gives the main line only its public half, as printed by
`tools/rlxsign.py pubkey --seed-file <seed>`.  The public half is not a secret
and is meant to be committed: then anyone can rebuild the exact flash image
from the tree, and BUILD_ID names the key.  What must never enter the tree or
$FWRE_WORK is the seed (`devkey.h` states that requirement; D15 meets it).

WHAT `write` AND `check` REFUSE, each with one line and exit 2:
  - text that is not exactly 64 hex digits;
  - the DEVELOPMENT key -- its seed (32 x 0x42) is published in this tree, so
    an image trusting it accepts a container anyone signed.  The dev key is
    taken from two places that must agree: `devkey.h`'s RLXBOOT_DEVKEY_HEX,
    and `tools/rlxsign.py` deriving it from the seed;
  - 32 bytes that are not the encoding of a curve point: rlxboot would refuse
    every container, and that would be found on the bench, a seating late;
  - a point of small order (8 * A = identity): with such a key a forger
    succeeds about one try in eight;
  - (`check` only) a header holding no key -- the placeholder `none` writes,
    which is what is committed until the owner's key exists -- or one whose
    three copies of the key (the comment, RLXBOOT_PRODKEY_HEX, and the
    rlxboot_prodkey[] array) disagree, i.e. a header edited by hand.

THE CURVE ARITHMETIC IS `tools/rlxsign.py`'s, imported rather than written a
second time: one host implementation of edwards25519 in this tree, whose own
`--self-test` holds the RFC 8032 vectors and an OpenSSL second source.  This
file uses its point decoder, scalar multiplication and point comparison; if
those names move, every command here refuses rather than passing.

WHAT THIS DOES NOT ESTABLISH.  That the key is the owner's: a public key says
nothing about who holds its seed, and the only thing that ties a container to
the owner's yes is that the owner signs it.  Nor that any container verifies
under it: that is a signature check, rlxboot's, at boot.

Exit: 0 ok, 1 a self-test control failed, 2 a refusal.
"""

import os
import re
import sys
import tempfile

sys.dont_write_bytecode = True       # an import must not write into the tree

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "tools"))
DEFAULT_OUT = os.path.join(HERE, "prodkey.h")
DEVKEY_H = os.path.join(HERE, "devkey.h")


def die(msg):
    sys.stdout.flush()
    sys.stderr.write("mkprodkey: REFUSED -- %s\n" % msg)
    raise SystemExit(2)


_RLXSIGN = []


def _curve():
    if _RLXSIGN:
        return _RLXSIGN[0]
    sys.path.insert(0, TOOLS)
    try:
        import rlxsign
    except ImportError as e:
        die("cannot import tools/rlxsign.py (%s): no curve arithmetic, no "
            "check" % e)
    for name in ("_decode", "_mul", "_eq", "secret_to_public", "DEV_SEED"):
        if not hasattr(rlxsign, name):
            die("tools/rlxsign.py has no %s; this file's checks need it" % name)
    _RLXSIGN.append(rlxsign)
    return rlxsign


def dev_key_hex():
    """The development public key, from devkey.h AND derived by rlxsign;
    a refusal if the two disagree."""
    try:
        txt = open(DEVKEY_H, "r", encoding="utf-8").read()
    except OSError as e:
        die("cannot read %s: %s" % (DEVKEY_H, e))
    m = re.search(r'#define\s+RLXBOOT_DEVKEY_HEX\s*\\?\s*"([0-9a-f]{64})"', txt)
    if not m:
        die("%s holds no RLXBOOT_DEVKEY_HEX" % DEVKEY_H)
    derived = _curve().secret_to_public(_curve().DEV_SEED).hex()
    if derived != m.group(1):
        die("devkey.h says %s and rlxsign derives %s from the dev seed"
            % (m.group(1), derived))
    return derived


def why_bad(key_hex):
    """None if `key_hex` may be a production key, else the reason it may not."""
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key_hex or ""):
        return "a public key is exactly 64 hex digits; got %r" % (key_hex or "")[:80]
    k = key_hex.lower()
    if k == dev_key_hex():
        return ("that is the DEVELOPMENT key (seed 32 x 0x42, published in "
                "devkey.h): an image trusting it accepts what anyone signs")
    rs = _curve()
    pt = rs._decode(bytes.fromhex(k))
    if pt is None:
        return ("%s is not the encoding of a point on edwards25519; rlxboot "
                "would refuse every container" % k)
    if rs._eq(rs._mul(8, pt), (0, 1, 1, 0)):
        return ("%s is a point of small order (8 * A is the identity); a "
                "forger needs about eight tries" % k)
    return None


def render(key_hex):
    """The header's whole text.  `key_hex` is None for the placeholder."""
    head = (
        "/* prodkey.h -- the update key a KEY=prod rlxboot trusts: the PUBLIC half of\n"
        " * the owner's production key (the R8b spec's D15).\n"
        " * GENERATED by src/rlxboot/mkprodkey.py -- do not edit; run it again.\n"
        " *\n")
    if key_hex is None:
        return head + (
            " *   public key  NONE -- the production key has not been generated\n"
            " *\n"
            " * A KEY=prod build (the Makefile's default) REFUSES while this file holds\n"
            " * no key: `mkprodkey.py check` says so before anything is compiled, and\n"
            " * main.c stops at #error if the Makefile is bypassed.  When the owner's\n"
            " * public key arrives:\n"
            " *\n"
            " *   python3 src/rlxboot/mkprodkey.py write --pubkey <64 hex>\n"
            " *\n"
            " * A development image needs no key here: build it with KEY=dev.\n"
            " */\n"
            "#ifndef RLXBOOT_PRODKEY_H\n"
            "#define RLXBOOT_PRODKEY_H\n"
            "#endif /* RLXBOOT_PRODKEY_H */\n")
    b = bytes.fromhex(key_hex)
    rows = []
    for i in range(0, 32, 8):
        rows.append("\t" + ",".join("0x%02x" % x for x in b[i:i + 8]))
    return head + (
        " *   public key  %s\n"
        " *\n"
        " * `mkprodkey.py check` reads this file before every KEY=prod build and\n"
        " * refuses unless the line above, RLXBOOT_PRODKEY_HEX and rlxboot_prodkey[]\n"
        " * hold the same 32 bytes, they are not the development key, and they\n"
        " * decode to a curve point of large order.  The seed this was derived from\n"
        " * is not in this repository and must never be (devkey.h).\n"
        " */\n"
        "#ifndef RLXBOOT_PRODKEY_H\n"
        "#define RLXBOOT_PRODKEY_H\n"
        "\n"
        "#define RLXBOOT_PRODKEY_HEX \\\n"
        "\t\"%s\"\n"
        "\n"
        "static const unsigned char rlxboot_prodkey[32] = {\n"
        "%s\n"
        "};\n"
        "\n"
        "#endif /* RLXBOOT_PRODKEY_H */\n") % (key_hex, key_hex, ",\n".join(rows))


def put(path, text):
    """Build first, then tmp + os.replace: never a half-written header."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except OSError as e:
        die("cannot write %s: %s" % (path, e))


def read_key(path):
    """-> the key's hex if `path` holds one consistent key; refuses otherwise.
    Returns None, without refusing, for the placeholder."""
    try:
        txt = open(path, "r", encoding="utf-8").read()
    except OSError as e:
        die("cannot read %s: %s" % (path, e))
    c = re.search(r"^ \*   public key  (\S+)", txt, re.M)
    d = re.search(r'#define RLXBOOT_PRODKEY_HEX \\\n\t"([0-9a-f]{64})"', txt)
    a = re.search(r"static const unsigned char rlxboot_prodkey\[32\] = \{([^}]*)\};",
                  txt)
    if c and c.group(1) == "NONE" and not d and not a:
        return None
    if not (c and d and a):
        die("%s is neither the placeholder nor a whole key header (comment %s, "
            "define %s, array %s); regenerate it with `write`"
            % (path, bool(c), bool(d), bool(a)))
    arr = re.findall(r"0x([0-9a-f]{2})", a.group(1))
    if len(arr) != 32:
        die("%s: rlxboot_prodkey[] holds %d bytes, not 32" % (path, len(arr)))
    ah = "".join(arr)
    if not (c.group(1) == d.group(1) == ah):
        die("%s: the three copies of the key disagree -- comment %s, define %s, "
            "array %s; was it edited by hand?" % (path, c.group(1), d.group(1), ah))
    return ah


def cmd_write(argv):
    key, out = None, DEFAULT_OUT
    it = iter(argv)
    for a in it:
        if a == "--pubkey":
            key = next(it, None)
        elif a == "--out":
            out = next(it, None)
        else:
            die("write: unknown argument %r" % a)
    if key is None or out is None:
        die("write needs --pubkey <64 hex> [--out PATH]")
    bad = why_bad(key)
    if bad:
        die(bad)
    key = key.lower()
    put(out, render(key))
    if read_key(out) != key:
        die("%s did not read back as %s" % (out, key))
    print("mkprodkey: wrote %s" % out)
    print("mkprodkey: public key %s" % key)
    return 0


def cmd_none(argv):
    out = DEFAULT_OUT
    if argv[:1] == ["--out"] and len(argv) == 2:
        out = argv[1]
    elif argv:
        die("none takes only [--out PATH]")
    put(out, render(None))
    print("mkprodkey: wrote %s -- the placeholder: a KEY=prod build refuses "
          "while it is in place" % out)
    return 0


def cmd_check(argv):
    if len(argv) > 1:
        die("check takes one PATH")
    path = argv[0] if argv else DEFAULT_OUT
    if not os.path.isfile(path):
        die("%s does not exist; a KEY=prod build needs it (`write`), or "
            "build with KEY=dev" % path)
    key = read_key(path)
    if key is None:
        die("%s holds NO production key (it is the placeholder).  When the "
            "owner's public key arrives: python3 src/rlxboot/mkprodkey.py write "
            "--pubkey <64 hex>.  For a development image: KEY=dev" % path)
    bad = why_bad(key)
    if bad:
        die("%s: %s" % (path, bad))
    print("mkprodkey: %s holds production key %s" % (path, key))
    return 0


# ---------------------------------------------------------------- self-test

def self_test():
    """Every refusal shown refusing, and the permitting path shown permitting,
    through the same functions the commands use, in a scratch directory."""
    import contextlib
    import io

    rs = _curve()
    rows = []
    reasons = []

    def run(fn, *args):
        """-> (exit code, the refusal's text) without leaving the process; the
        command's own output is swallowed and the reason kept for the row."""
        err, out = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                rc = fn(list(args))
        except SystemExit as e:
            rc = int(e.code or 0)
        why = err.getvalue().strip().replace("mkprodkey: REFUSED -- ", "")
        if why:
            reasons.append(why)
        return rc, why

    def add(cid, what, good):
        rows.append((cid, what, good, reasons[-1] if reasons else ""))
        del reasons[:]

    tmp = tempfile.mkdtemp(prefix="mkprodkey-")
    try:
        good_key = rs.secret_to_public(os.urandom(32)).hex()
        p = os.path.join(tmp, "k.h")

        rc_w, _ = run(cmd_write, "--pubkey", good_key, "--out", p)
        rc_c, _ = run(cmd_check, p)
        add("K1", "a random valid key: write 0, check 0, reads back",
            rc_w == 0 and rc_c == 0 and read_key(p) == good_key)

        rc_w, _ = run(cmd_write, "--pubkey", good_key.upper(), "--out", p)
        add("K2", "upper-case hex is accepted and stored lower-case",
            rc_w == 0 and read_key(p) == good_key)

        n = os.path.join(tmp, "none.h")
        rc_n, _ = run(cmd_none, "--out", n)
        rc_c, _ = run(cmd_check, n)
        add("K3", "the placeholder: none 0, check REFUSES (2)",
            rc_n == 0 and rc_c == 2 and read_key(n) is None)

        dev = dev_key_hex()
        rc_w, _ = run(cmd_write, "--pubkey", dev, "--out",
                      os.path.join(tmp, "dev.h"))
        dv = os.path.join(tmp, "dev2.h")
        put(dv, render(dev))             # a header holding it, bypassing write
        rc_c, _ = run(cmd_check, dv)
        add("K4", "the development key: write REFUSES, a header holding it "
            "is REFUSED by check", rc_w == 2 and rc_c == 2
            and not os.path.exists(os.path.join(tmp, "dev.h")))

        # The first y >= 2 whose encoding is not a point -- found, not
        # remembered -- and a non-canonical y (>= p).
        y = 2
        while rs._decode(int.to_bytes(y, 32, "little")) is not None:
            y += 1
        notpt = int.to_bytes(y, 32, "little").hex()
        noncanon = (b"\xff" * 31 + b"\x7f").hex()
        rc1, _ = run(cmd_write, "--pubkey", notpt, "--out", p)
        rc2, _ = run(cmd_write, "--pubkey", noncanon, "--out", p)
        add("K5", "not a curve point (y=%d), and y >= p: both REFUSED" % y,
            rc1 == 2 and rc2 == 2)

        ident = int.to_bytes(1, 32, "little").hex()      # (0, 1): order 1
        zero = bytes(32).hex()                           # y = 0: order 4
        rc1, _ = run(cmd_write, "--pubkey", ident, "--out", p)
        rc2, _ = run(cmd_write, "--pubkey", zero, "--out", p)
        add("K6", "small order: the identity and y = 0, both REFUSED",
            rc1 == 2 and rc2 == 2)

        bad = [good_key[:63], good_key + "0", "g" + good_key[1:], ""]
        rcs = [run(cmd_write, "--pubkey", b, "--out", p)[0] for b in bad]
        add("K7", "63, 65, non-hex and empty: all REFUSED", rcs == [2] * 4)

        # A header edited by hand: one array byte changed.
        run(cmd_write, "--pubkey", good_key, "--out", p)
        txt = open(p, encoding="utf-8").read()
        first = "0x" + good_key[:2]
        flip = "0x%02x" % (int(good_key[:2], 16) ^ 1)
        put(p, txt.replace("\t" + first + ",", "\t" + flip + ",", 1))
        rc_c, _ = run(cmd_check, p)
        add("K8", "one array byte changed by hand: check REFUSES", rc_c == 2)

        rc_c, _ = run(cmd_check, os.path.join(tmp, "missing.h"))
        add("K9", "a header that does not exist: check REFUSES", rc_c == 2)

        rc_w, _ = run(cmd_write, "--pubkey", good_key, "--out",
                      os.path.join(tmp, "no-such-dir", "k.h"))
        add("K10", "an unwritable --out: write REFUSES with a reason, no "
            "traceback", rc_w == 2)
    finally:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)

    print("mkprodkey -- self-test")
    fails = 0
    for cid, what, good, why in rows:
        print("  %s  %-3s %s" % ("ok  " if good else "FAIL", cid, what))
        if why:
            print("            last refusal: %s" % why[:150])
        fails += 0 if good else 1
    print("  %d passed, %d failed" % (len(rows) - fails, fails))
    return 1 if fails else 0


def main(argv):
    if argv[:1] == ["--self-test"] and len(argv) == 1:
        return self_test()
    if not argv:
        die("usage: mkprodkey.py write --pubkey <64 hex> [--out PATH] | none "
            "[--out PATH] | check [PATH] | --self-test")
    cmd, rest = argv[0], argv[1:]
    if cmd == "write":
        return cmd_write(rest)
    if cmd == "none":
        return cmd_none(rest)
    if cmd == "check":
        return cmd_check(rest)
    die("unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
