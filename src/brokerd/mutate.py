#!/usr/bin/env python3
"""src/brokerd/mutate.py -- plant one named defect in a COPY of a source file.

The real sources never carry a mutation switch: every mutant is a copy made
here, so nothing that could be flipped ships.  Each mutation REFUSES unless its
anchor matches exactly once, because a sed that silently matched nothing turns a
mutation run into a green line that means nothing.

    mutate.py <name> <src> <dst>
"""
import sys

MUTATIONS = {
    # The constant-time compare given an early exit.  Functionally identical,
    # so the unit suite must NOT catch it -- that is the point of having it.
    "early": (
        "\tfor (i = 0; i < n; i++)\n"
        "\t\td = (unsigned char)(d | (unsigned char)(p[i] ^ q[i]));\n",
        "\tfor (i = 0; i < n; i++) {\n"
        "\t\td = (unsigned char)(d | (unsigned char)(p[i] ^ q[i]));\n"
        "\t\tif (d != 0)\n\t\t\tbreak;\n"
        "\t}\n",
    ),
    # The body_len bound removed: an attacker's 32-bit length reaches the copy.
    "nobound": (
        "\tif (blen > PROTO_REQ_BODY_MAX)\n\t\treturn PROTO_E_BODYLEN;\n",
        "\tif (0)\n\t\treturn PROTO_E_BODYLEN;\n",
    ),
    # One byte past the end: the classic off-by-one, for the fuzzer.
    "off1": (
        "\tif (blen > PROTO_REQ_BODY_MAX)\n",
        "\tif (blen > PROTO_REQ_BODY_MAX + 1)\n",
    ),
}


def main(argv):
    if len(argv) != 4:
        sys.stderr.write(__doc__)
        return 2
    name, src, dst = argv[1], argv[2], argv[3]
    if name not in MUTATIONS:
        sys.stderr.write("mutate.py: REFUSED: unknown mutation %r; have %s\n"
                         % (name, ", ".join(sorted(MUTATIONS))))
        return 2
    old, new = MUTATIONS[name]
    with open(src, "r", encoding="utf-8") as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        sys.stderr.write("mutate.py: REFUSED: anchor for %r matches %d times in "
                         "%s, want exactly 1\n" % (name, n, src))
        return 1
    out = text.replace(old, new, 1)
    if out == text:
        sys.stderr.write("mutate.py: REFUSED: %r changed nothing\n" % name)
        return 1
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    import os
    os.replace(tmp, dst)
    sys.stdout.write("mutate.py: planted %s in %s\n" % (name, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
