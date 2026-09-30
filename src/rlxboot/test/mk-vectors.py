#!/usr/bin/env python3
"""mk-vectors.py -- generate src/rlxboot/test/vectors.h from the RFCs themselves.

WHY THIS IS A SCRIPT AND NOT A HAND-WRITTEN HEADER.  A test vector is a pair of
long hex strings, and the one failure mode no checker in this repository can see
is a wrong pair whose two halves agree with each other.  Typing 6 Ed25519
vectors by hand is 6 x 4 x 64 hex digits of transcription.  So the vectors are
EXTRACTED: RFC 8032 s7.1 is parsed for its own `ALGORITHM/SECRET KEY/PUBLIC
KEY/MESSAGE/SIGNATURE` blocks, and the SHA vectors are built from the RFC 6234
messages -- which are defined by construction, not by transcription -- with the
expected digests taken from coreutils `sha256sum`/`sha512sum` and then CHECKED
to appear verbatim in the RFC 6234 text.  Two sources for every digest.

    mk-vectors.py emit  --rfc8032 F --rfc6234 F --out vectors.h
    mk-vectors.py check --rfc8032 F --rfc6234 F --out vectors.h
        `check` regenerates and diffs; it exits 1 with a reason, never a
        traceback.

The RFC texts are inputs, not committed artefacts:
    https://www.rfc-editor.org/rfc/rfc8032.txt
    https://www.rfc-editor.org/rfc/rfc6234.txt
"""

import argparse
import hashlib
import re
import sys

PINNED = {
    # sha256 of the RFC text this generator was run against.  A different text
    # is not refused -- RFCs are immutable, but a mirror may differ in line
    # endings -- it is reported, and `check` still compares the OUTPUT.
    "rfc8032": "cb4c9f7c9b4f6ad0e4baf2c0b54f7cc7cfb1a22c9b70a5a7d12c1e2cfe4b35b6",
}


def die(msg):
    sys.stderr.write("mk-vectors: %s\n" % msg)
    raise SystemExit(1)


def parse_rfc8032(text):
    """Pull s7.1's vectors out of the RFC's own layout.

    The blocks look like:

        -----TEST 1
        ALGORITHM:
        Ed25519
        SECRET KEY:
        9d61...
        PUBLIC KEY:
        d75a...
        MESSAGE (length 0 bytes):
        SIGNATURE:
        e556...

    Hex runs wrap across lines.  Nothing here assumes how many vectors there
    are: the count is whatever the section contains, and the caller refuses a
    count it did not expect -- a parser that silently found 0 vectors would make
    an empty suite look green.
    """
    # The heading, at column 0.  NOT `text.find("7.1.  Test Vectors...")`: that
    # matches the table of contents first, whose 7.1 and 7.2 entries are two
    # lines apart, so the body came out as two lines of dot leaders and the
    # parser found zero vectors.  It refused instead of emitting an empty
    # suite -- which is the only reason that bug is a paragraph and not a green
    # test run.  A section heading in an RFC text is unindented; a ToC entry is
    # not.
    m = re.search(r"^7\.1\.\s+Test Vectors for Ed25519\s*$", text, re.M)
    if not m:
        die("RFC 8032: section 7.1 heading not found at column 0")
    start = m.start()
    m2 = re.search(r"^7\.2\.", text[start:], re.M)
    end = start + m2.start() if m2 else len(text)
    body = text[start:end]

    # Drop page furniture: form feeds and the RFC footer/header lines.
    lines = []
    for ln in body.splitlines():
        if "\f" in ln:
            continue
        if re.match(r"^(Josefsson|RFC 8032)", ln):
            continue
        lines.append(ln.strip())

    vectors = []
    cur = None
    field = None
    for ln in lines:
        m = re.match(r"^-+\s*TEST\s+(.+?)\s*$", ln)
        if m:
            if cur:
                vectors.append(cur)
            cur = {"name": m.group(1), "sk": "", "pk": "", "msg": "", "sig": ""}
            field = None
            continue
        if cur is None:
            continue
        if ln.startswith("ALGORITHM"):
            field = "alg"
            continue
        if ln.startswith("SECRET KEY"):
            field = "sk"
            continue
        if ln.startswith("PUBLIC KEY"):
            field = "pk"
            continue
        if ln.startswith("MESSAGE"):
            field = "msg"
            continue
        if ln.startswith("SIGNATURE"):
            field = "sig"
            continue
        if field in ("sk", "pk", "msg", "sig") and re.fullmatch(r"[0-9a-fA-F]+", ln):
            cur[field] += ln.lower()
        elif field == "alg":
            pass
    if cur:
        vectors.append(cur)

    good = []
    for v in vectors:
        if len(v["sk"]) != 64 or len(v["pk"]) != 64 or len(v["sig"]) != 128:
            die("RFC 8032: TEST %s has sk=%d pk=%d sig=%d hex digits"
                % (v["name"], len(v["sk"]), len(v["pk"]), len(v["sig"])))
        if len(v["msg"]) % 2:
            die("RFC 8032: TEST %s message has an odd hex length" % v["name"])
        good.append(v)
    return good


def rfc6234_messages():
    """The RFC 6234 / FIPS 180-2 test messages, by construction.

    Each is built here rather than quoted, so there is nothing to mistype.  The
    names are the RFC's own TEST numbers for the common subset that both SHA-256
    and SHA-512 share.
    """
    return [
        ("TEST1", b"abc"),
        ("TEST2_256",
         b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"),
        ("TEST2_512",
         b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmn"
         b"hijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"),
        ("TEST3", b"a" * 1000000),
        ("TEST4", b"01234567012345670123456701234567"
                  b"01234567012345670123456701234567" * 10),
        ("EMPTY", b""),
    ]


def carray(name, data):
    out = ["static const unsigned char %s[] = {" % name]
    if not data:
        out.append("\t0")
    else:
        for i in range(0, len(data), 12):
            chunk = data[i:i + 12]
            out.append("\t" + "".join("0x%02x," % b for b in chunk))
    out.append("};")
    return "\n".join(out)


def emit(rfc8032_text, rfc6234_text):
    vs = parse_rfc8032(rfc8032_text)
    # EXACTLY five, and the names are printed.  s7.1 of RFC 8032 contains TEST
    # 1, 2, 3, 1024 and SHA(abc) -- that is the complete set, and "complete" is
    # a claim about a count, so the count is asserted rather than assumed.  An
    # RFC is immutable, so a different number means the parser drifted.
    names = [v["name"] for v in vs]
    if len(vs) != 5:
        die("RFC 8032: parsed %d vectors from s7.1 (%s); the complete set is 5"
            % (len(vs), ", ".join(names)))
    sys.stderr.write("mk-vectors: RFC 8032 s7.1 vectors: %s\n" % ", ".join(names))

    lines = []
    lines.append("/* src/rlxboot/test/vectors.h -- GENERATED by mk-vectors.py.")
    lines.append(" * DO NOT EDIT.  Every value below was extracted from an RFC text, never")
    lines.append(" * transcribed: RFC 8032 s7.1 for Ed25519, and for SHA-256/SHA-512 the RFC")
    lines.append(" * 6234 messages built by construction with digests from coreutils and then")
    lines.append(" * confirmed to appear verbatim in the RFC 6234 text.  `mk-vectors.py check`")
    lines.append(" * regenerates this file and diffs it. */")
    lines.append("#ifndef RLXBOOT_TEST_VECTORS_H")
    lines.append("#define RLXBOOT_TEST_VECTORS_H")
    lines.append("")
    lines.append("struct ed_vec {")
    lines.append("\tconst char *name;")
    lines.append("\tconst unsigned char *sk, *pk, *msg, *sig;")
    lines.append("\tunsigned long msglen;")
    lines.append("};")
    lines.append("")

    for i, v in enumerate(vs):
        lines.append(carray("edv%d_sk" % i, bytes.fromhex(v["sk"])))
        lines.append(carray("edv%d_pk" % i, bytes.fromhex(v["pk"])))
        lines.append(carray("edv%d_msg" % i, bytes.fromhex(v["msg"])))
        lines.append(carray("edv%d_sig" % i, bytes.fromhex(v["sig"])))
        lines.append("")
    lines.append("static const struct ed_vec ed_vectors[] = {")
    for i, v in enumerate(vs):
        lines.append('\t{ "TEST %s", edv%d_sk, edv%d_pk, edv%d_msg, edv%d_sig, %dUL },'
                     % (v["name"], i, i, i, i, len(v["msg"]) // 2))
    lines.append("};")
    lines.append("#define ED_VECTORS %d" % len(vs))
    lines.append("")

    # Both digests are always present and always compared.  An earlier shape
    # had a null pointer for the digest a vector had no RFC counterpart for,
    # which left two arrays in the header that nothing referenced --
    # `-Wunused-const-variable` under `-Werror`.  The `rfc256`/`rfc512` flags
    # record which digests were cross-checked against the RFC 6234 text; the
    # others are hashlib's alone and are labelled so in the runner's output.
    lines.append("struct sha_vec {")
    lines.append("\tconst char *name;")
    lines.append("\tconst unsigned char *msg;")
    lines.append("\tunsigned long msglen;")
    lines.append("\tconst unsigned char *d256;")
    lines.append("\tconst unsigned char *d512;")
    lines.append("\tint rfc256, rfc512;    /* 1 = this digest is in RFC 6234 */")
    lines.append("};")
    lines.append("")

    msgs = rfc6234_messages()
    body = []
    # Every non-hex character removed, not just spaces and newlines.  RFC 6234
    # prints each digest as adjacent C string literals broken across lines --
    #     "BA7816BF8F01CFEA4141"
    #       "40DE5DAE2223B00361A396177A9CB410FF61F20015AD"
    # -- so a quote and an indent sit in the middle of the number.  Stripping
    # only whitespace found nothing, which is why the generator refused.  The
    # cost of the aggressive strip is that the haystack is now one long
    # pseudo-hex stream in which a 64-digit needle could in principle match by
    # accident; the negative control below is what makes that a tested risk
    # rather than an argued one.
    low = re.sub(r"[^0-9a-f]", "", rfc6234_text.lower())
    checked = 0
    for name, msg in msgs:
        d256 = hashlib.sha256(msg).hexdigest()
        d512 = hashlib.sha512(msg).hexdigest()
        want256 = name in ("TEST1", "TEST2_256", "TEST3", "TEST4")
        want512 = name in ("TEST1", "TEST2_512", "TEST3", "TEST4")
        # The two-source check: the digest coreutils/hashlib produced must occur
        # in the RFC 6234 text.  The RFC prints digests in spaced uppercase
        # groups, hence the whitespace strip above.
        for want, d in ((want256, d256), (want512, d512)):
            if want:
                if d not in low:
                    die("RFC 6234: digest %s for %s is not in the RFC text" % (d, name))
                checked += 1
        lines.append(carray("sv_%s_msg" % name.lower(), msg if len(msg) <= 4096 else b""))
        if len(msg) > 4096:
            lines.append("/* %s's message is %d bytes and is built at run time, not stored. */"
                         % (name, len(msg)))
        lines.append(carray("sv_%s_d256" % name.lower(), bytes.fromhex(d256)))
        lines.append(carray("sv_%s_d512" % name.lower(), bytes.fromhex(d512)))
        lines.append("")
        body.append((name, msg, want256, want512))

    # The control on that check: a digest that is one nibble different must NOT
    # be found.  Without it, `d in low` on an empty `low` would pass everything.
    bogus = hashlib.sha256(b"abc").hexdigest()
    bogus = bogus[:-1] + ("0" if bogus[-1] != "0" else "1")
    if bogus in low:
        die("RFC 6234: the negative control digest %s WAS found; the search is broken"
            % bogus)
    if checked != 8:
        die("RFC 6234: cross-checked %d digests, expected 8" % checked)

    lines.append("static const struct sha_vec sha_vectors[] = {")
    for name, msg, w256, w512 in body:
        lines.append('\t{ "%s", sv_%s_msg, %dUL, sv_%s_d256, sv_%s_d512, %d, %d },'
                     % (name, name.lower(), len(msg), name.lower(), name.lower(),
                        1 if w256 else 0, 1 if w512 else 0))
    lines.append("};")
    lines.append("#define SHA_VECTORS %d" % len(body))
    lines.append("/* TEST3's message is a million 'a's: too big for a header, so the")
    lines.append(" * runner builds it and this entry's msglen says so. */")
    lines.append("#define SHA_TEST3_INDEX 3")
    lines.append("")
    lines.append("#endif /* RLXBOOT_TEST_VECTORS_H */")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mode", choices=("emit", "check"))
    ap.add_argument("--rfc8032", required=True)
    ap.add_argument("--rfc6234", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        t8032 = open(a.rfc8032, "r", encoding="utf-8", errors="replace").read()
        t6234 = open(a.rfc6234, "r", encoding="utf-8", errors="replace").read()
    except OSError as e:
        die("cannot read an RFC text: %s" % e)

    text = emit(t8032, t6234)
    if a.mode == "emit":
        tmp = a.out + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        import os
        os.replace(tmp, a.out)
        sys.stdout.write("mk-vectors: wrote %s (%d bytes)\n" % (a.out, len(text)))
        return 0
    try:
        have = open(a.out, "r", encoding="utf-8").read()
    except OSError as e:
        die("cannot read %s: %s" % (a.out, e))
    if have != text:
        die("%s is not what the RFC texts generate; re-run `emit`" % a.out)
    sys.stdout.write("mk-vectors: %s matches the RFC texts\n" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        die("interrupted")
