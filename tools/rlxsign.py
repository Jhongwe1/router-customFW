#!/usr/bin/env python3
"""Ed25519 (RFC 8032) keygen-from-seed, sign and verify, in pure Python.

Why this exists rather than an import
-------------------------------------
`SPEC-R8a.md` § 3 pins the update chain's signature to Ed25519 and pins the
*development* key to a fixed seed, so that the host signer here and the target
verifier in `src/lib/ed25519.c` can be written by two agents who never exchange
a key: both derive the same public key from 32 bytes of `0x42`, and **a mismatch
between the two derived public keys is the finding**.  That cross-check only
works if this side is an implementation rather than a wrapper: a wrapper agrees
with itself.  `hashlib` supplies SHA-512 and nothing else is imported.

This is a HOST tool.  It is not the thing that runs on the device, it is not
constant-time, and it must never be used to sign anything that matters -- the
scalar lives in Python ints in a garbage-collected heap.  What it is for is
producing `RLXU` containers at the desk and checking them.

The controls, and what each one can catch
-----------------------------------------
`--self-test` runs, in this order:

  V1-V4   the RFC 8032 § 7.1 vectors whose message bytes can be reproduced
          exactly here: TEST 1 (length 0), TEST 2 (length 1), TEST 3
          (length 2) and TEST SHA(abc) (length 64).  For each: the public key
          derived from the RFC's secret key, and the RFC's signature
          reproduced byte for byte, and then verified.
          ⚠️ **§ 7.1's fifth vector, TEST 1024, is NOT here.**  Its message is
          1,023 bytes of arbitrary data which this session has no offline copy
          of, and a message transcribed from memory would either fail against
          the RFC's signature (a false red) or, worse, be "repaired" by
          re-signing it -- which deletes the control and leaves a vector that
          can only ever agree with this file.  `O3` below covers the same
          ground with a second implementation instead of a remembered constant.
  N1-N3   the three negative controls § 3 names: one flipped bit in the
          signature, in the message, and in the public key, each REJECTED.
          Without these, `verify()` returning True unconditionally is green.
  N4-N6   the malleability and canonicality rejections RFC 8032 § 5.1.7
          requires: S >= L, a non-canonical encoded y (y >= p), and a
          signature of the wrong length.
  S1      sign/verify round trip over 0..600-byte messages including the
          SHA-512 block boundaries (55, 56, 63, 64, 111, 112, 127, 128) --
          this is what a broken length-padding in the hash shows up as.
  O1-O4   **the second source.**  OpenSSL 3's Ed25519 is an independent
          implementation and is not a Python module: O1 has it derive the
          public key from § 3's seed, O2 has it verify a signature made here,
          O3 has this file verify a signature OpenSSL made over a 1,023-byte
          message (the length TEST 1024 uses) and over 4 KiB, and O4 has
          OpenSSL reject a signature this file made over a *different*
          message -- because an O2 that cannot fail proves nothing.
          These SKIP if `openssl` has no Ed25519, and a skip is printed.

A self-test that skips O1-O4 and passes V1-V4 has checked this implementation
against constants only.  That is weaker, and the skip line says so.

Exit
    0  every control that ran passed
    1  a control failed
    2  usage / input refusal -- one line, no traceback
"""

import argparse
import hashlib
import os
import subprocess
import sys

VERSION = "rlxsign 1.0"

# ---------------------------------------------------------------- the curve
# RFC 8032 § 5.1: edwards25519 over GF(2^255-19), group order L.
P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, P - 2, P) % P
_SQRT_M1 = pow(2, (P - 1) // 4, P)

# The base point B, RFC 8032 § 5.1.
_BY = 4 * pow(5, P - 2, P) % P


def _recover_x(y, sign):
    """x for a given y and sign bit, or None if the point is not on the curve.

    RFC 8032 § 5.1.3.  `None` is a rejection and every caller must treat it as
    one: returning 0 here would silently accept a public key that decodes to
    nothing, and the signature check on the identity is not hard to satisfy.
    """
    if y >= P:
        return None                      # non-canonical encoding -- reject
    x2 = (y * y - 1) * pow(_D * y * y + 1, P - 2, P) % P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (P + 3) // 8, P)
    if x * x % P != x2:
        x = x * _SQRT_M1 % P
    if x * x % P != x2:
        return None                      # y is not the y of any curve point
    if x & 1 != sign:
        x = P - x
    return x


_B = (_recover_x(_BY, 0), _BY, 1, _recover_x(_BY, 0) * _BY % P)


def _add(p1, p2):
    """Extended-coordinate addition, RFC 8032 § 5.1.4."""
    x1, y1, z1, t1 = p1
    x2, y2, z2, t2 = p2
    a = (y1 - x1) * (y2 - x2) % P
    b = (y1 + x1) * (y2 + x2) % P
    c = 2 * t1 * t2 * _D % P
    dd = 2 * z1 * z2 % P
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s, pt):
    """s * pt.  Fixed-shape double-and-add: this is a host tool, not the target."""
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _add(q, pt)
        pt = _add(pt, pt)
        s >>= 1
    return q


def _eq(p1, p2):
    x1, y1, z1, _ = p1
    x2, y2, z2, _ = p2
    return (x1 * z2 - x2 * z1) % P == 0 and (y1 * z2 - y2 * z1) % P == 0


def _encode(pt):
    x, y, z, _ = pt
    zi = pow(z, P - 2, P)
    x, y = x * zi % P, y * zi % P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decode(b):
    """A 32-byte encoded point -> extended coordinates, or None to REJECT."""
    if len(b) != 32:
        return None
    y = int.from_bytes(b, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % P)


def _sha512_int(b):
    return int.from_bytes(hashlib.sha512(b).digest(), "little")


# ---------------------------------------------------------------- the API
def secret_to_public(seed):
    """seed (32 bytes) -> the 32-byte public key.  RFC 8032 § 5.1.5."""
    if len(seed) != 32:
        raise ValueError("an Ed25519 seed is 32 bytes, not %d" % len(seed))
    h = bytearray(hashlib.sha512(seed).digest()[:32])
    h[0] &= 248
    h[31] &= 127
    h[31] |= 64
    return _encode(_mul(int.from_bytes(h, "little"), _B))


def sign(seed, msg):
    """-> the 64-byte signature of `msg` under `seed`.  RFC 8032 § 5.1.6."""
    if len(seed) != 32:
        raise ValueError("an Ed25519 seed is 32 bytes, not %d" % len(seed))
    hh = hashlib.sha512(seed).digest()
    a = bytearray(hh[:32])
    a[0] &= 248
    a[31] &= 127
    a[31] |= 64
    s = int.from_bytes(a, "little")
    prefix = hh[32:]
    pub = _encode(_mul(s, _B))
    r = _sha512_int(prefix + msg) % L
    big_r = _encode(_mul(r, _B))
    k = _sha512_int(big_r + pub + msg) % L
    return big_r + int.to_bytes((r + k * s) % L, 32, "little")


def verify(pub, msg, sig):
    """-> True only if `sig` is a valid Ed25519 signature of `msg` under `pub`.

    Every early return is a rejection, and RFC 8032 § 5.1.7's two canonicality
    conditions are among them: `S >= L` (malleability) and an encoded point
    whose y is >= p.  The group equation is checked in the *cofactored-free*
    form [S]B = R + [k]A, which is what the RFC's verification section states.
    """
    if len(sig) != 64 or len(pub) != 32:
        return False
    big_r = _decode(sig[:32])
    if big_r is None:
        return False
    big_a = _decode(pub)
    if big_a is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= L:
        return False
    k = _sha512_int(sig[:32] + pub + msg) % L
    return _eq(_mul(s, _B), _add(big_r, _mul(k, big_a)))


# ----------------------------------------------------- the development key
# SPEC-R8a.md § 3.  IN THE TREE ON PURPOSE, and it is not a secret: anyone who
# reads this line can sign a container that this project's verifier accepts.
# That is the point -- it lets two independently written implementations be
# compared without a key exchange.  `R8b` needs a key that is NOT here; see
# notes/update-chain.md § Keys.
DEV_SEED = bytes([0x42]) * 32


def dev_public_hex():
    return secret_to_public(DEV_SEED).hex()


# ---------------------------------------------------------------- refusals
def die(msg):
    print("rlxsign: %s" % msg, file=sys.stderr)
    raise SystemExit(2)


def read_seed(args):
    """The seed named on the command line, or the development seed.

    A seed given as hex and a seed given as a file are different mistakes, so
    they get different refusals; `--dev-seed` is explicit rather than a default
    so that nothing signs with the published key by accident.
    """
    named = [k for k in ("seed_hex", "seed_file", "dev_seed") if args.get(k)]
    if len(named) != 1:
        die("give exactly one of --seed-hex, --seed-file, --dev-seed "
            "(got %d)" % len(named))
    if args.get("dev_seed"):
        return DEV_SEED
    if args.get("seed_hex"):
        t = args["seed_hex"].strip()
        try:
            b = bytes.fromhex(t)
        except ValueError:
            die("--seed-hex is not hex: %r" % t[:40])
        if len(b) != 32:
            die("--seed-hex decodes to %d bytes, and a seed is 32" % len(b))
        return b
    path = args["seed_file"]
    if not os.path.isfile(path):
        die("no such seed file: %s" % path)
    b = open(path, "rb").read()
    if len(b) == 65 and b[64:] == b"\n":
        b = b[:64]
    if len(b) == 64:
        try:
            b = bytes.fromhex(b.decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            die("%s is 64 bytes but not 64 hex digits" % path)
    if len(b) != 32:
        die("%s holds %d bytes; a seed is 32 raw bytes or 64 hex digits"
            % (path, len(b)))
    return b


# ---------------------------------------------------------------- self-test
# RFC 8032 § 7.1, the four vectors whose messages are reproducible here.
# (secret key, public key, message, signature), all hex.
RFC8032 = [
    ("V1", "TEST 1 (length 0)",
     "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
     "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f"
     "b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("V2", "TEST 2 (length 1)",
     "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
     "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da0"
     "85ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("V3", "TEST 3 (length 2)",
     "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
     "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac1"
     "8ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
    ("V4", "TEST SHA(abc) (length 64)",
     "833fe62409237b9d62ec77587520911e9a759cec1d19755b7da901b96dca3d42",
     "ec172b93ad5e563bf4932c70e1245034c35467ef2efd4d64ebf819683467e2bf",
     "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
     "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
     "dc2a4459e7369633a52b1bf277839a00201009a3efbf3ecb69bea2186c26b589"
     "09351fc9ac90b3ecfdfbc7c66431e0303dca179c138ac17ad9bef1177331a704"),
]

_PKCS8_ED25519 = bytes.fromhex("302e020100300506032b657004220420")
_SPKI_ED25519 = bytes.fromhex("302a300506032b6570032100")


def _openssl_ok():
    try:
        r = subprocess.run(["openssl", "list", "-public-key-algorithms"],
                           capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return b"ED25519" in r.stdout.upper()


def _openssl_pub(seed, tmp):
    """OpenSSL's own derivation of the public key from `seed`, or None."""
    der = os.path.join(tmp, "k.der")
    with open(der, "wb") as fh:
        fh.write(_PKCS8_ED25519 + seed)
    r = subprocess.run(["openssl", "pkey", "-inform", "DER", "-in", der,
                        "-pubout", "-outform", "DER"],
                       capture_output=True, timeout=30)
    if r.returncode != 0 or not r.stdout.startswith(_SPKI_ED25519):
        return None
    return r.stdout[len(_SPKI_ED25519):]


def _openssl_sign(seed, msg, tmp):
    der, m, s = (os.path.join(tmp, n) for n in ("k.der", "m.bin", "s.bin"))
    with open(der, "wb") as fh:
        fh.write(_PKCS8_ED25519 + seed)
    with open(m, "wb") as fh:
        fh.write(msg)
    r = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", der,
                        "-keyform", "DER", "-rawin", "-in", m, "-out", s],
                       capture_output=True, timeout=30)
    if r.returncode != 0:
        return None
    return open(s, "rb").read()


def _openssl_verify(pub, msg, sig, tmp):
    """-> True / False / None (OpenSSL could not be driven)."""
    pk, m, s = (os.path.join(tmp, n) for n in ("pub.der", "m.bin", "s.bin"))
    with open(pk, "wb") as fh:
        fh.write(_SPKI_ED25519 + pub)
    with open(m, "wb") as fh:
        fh.write(msg)
    with open(s, "wb") as fh:
        fh.write(sig)
    r = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin",
                        "-inkey", pk, "-keyform", "DER", "-rawin",
                        "-in", m, "-sigfile", s],
                       capture_output=True, timeout=30)
    if r.returncode not in (0, 1):
        return None
    return r.returncode == 0


def self_test():
    rows = []
    skips = []

    def add(cid, what, ok, detail=""):
        rows.append((cid, what, ok, detail))

    # ------------------------------------------------------------- V1-V4
    for cid, name, sk, pk, msg, sig in RFC8032:
        seed, want_pk, m, want_sig = (bytes.fromhex(sk), bytes.fromhex(pk),
                                      bytes.fromhex(msg), bytes.fromhex(sig))
        got_pk = secret_to_public(seed)
        got_sig = sign(seed, m)
        ok = (got_pk == want_pk and got_sig == want_sig
              and verify(want_pk, m, want_sig))
        add(cid, "RFC 8032 " + name, ok,
            "pk %s sig %s verify %s"
            % (got_pk == want_pk, got_sig == want_sig,
               verify(want_pk, m, want_sig)))

    # ------------------------------------------------------------- N1-N6
    seed = bytes.fromhex(RFC8032[2][2])
    pub = secret_to_public(seed)
    msg = b"rlxfw R8a negative control"
    sig = sign(seed, msg)
    add("N0", "the signature the negatives are derived from verifies",
        verify(pub, msg, sig), "positive control for N1-N3")

    def flip(b, i, bit=0):
        out = bytearray(b)
        out[i] ^= 1 << bit
        return bytes(out)

    bad_sig = all(not verify(pub, msg, flip(sig, i, b))
                  for i in range(64) for b in (0, 7))
    add("N1", "one flipped bit in the SIGNATURE is rejected (128 flips)",
        bad_sig)
    bad_msg = all(not verify(pub, flip(msg, i), sig) for i in range(len(msg)))
    add("N2", "one flipped bit in the MESSAGE is rejected (%d flips)"
        % len(msg), bad_msg)
    bad_pub = all(not verify(flip(pub, i), msg, sig) for i in range(32))
    add("N3", "one flipped bit in the PUBLIC KEY is rejected (32 flips)",
        bad_pub)

    s_big = sig[:32] + int.to_bytes(
        int.from_bytes(sig[32:], "little") + L, 32, "little")
    add("N4", "S >= L is rejected (RFC 8032 5.1.7 malleability)",
        len(s_big) == 64 and not verify(pub, msg, s_big))
    noncanon = int.to_bytes(P + 1, 32, "little")
    add("N5", "a non-canonical encoded y (y >= p) is rejected",
        not verify(noncanon, msg, sig)
        and not verify(pub, msg, noncanon + sig[32:]))
    add("N6", "a signature of the wrong length is rejected",
        not verify(pub, msg, sig[:63]) and not verify(pub, msg, sig + b"\0"))

    # ---------------------------------------------------------------- S1
    lens = [0, 1, 2, 3, 31, 32, 33, 55, 56, 57, 63, 64, 65, 111, 112, 113,
            127, 128, 129, 255, 256, 257, 599, 600]
    dev_pub = secret_to_public(DEV_SEED)
    ok = True
    for n in lens:
        m = bytes((i * 7 + 3) & 0xFF for i in range(n))
        if not verify(dev_pub, m, sign(DEV_SEED, m)):
            ok = False
            break
    add("S1", "sign/verify round trip at %d lengths incl. SHA-512 block "
        "boundaries" % len(lens), ok, "0..600 bytes")

    # ---------------------------------------------------------------- O1-O4
    import tempfile
    if not _openssl_ok():
        skips.append(("openssl has no Ed25519 -- the ONLY second source, so "
                      "V1-V4 are then checks against constants alone", 4))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            mine = secret_to_public(DEV_SEED)
            theirs = _openssl_pub(DEV_SEED, tmp)
            add("O1", "OpenSSL derives the SAME public key from SPEC 3's seed",
                theirs is not None and theirs == mine,
                "mine %s theirs %s" % (mine.hex()[:16],
                                       theirs.hex()[:16] if theirs else "ERR"))
            m = b"RLXU cross-source"
            v = _openssl_verify(mine, m, sign(DEV_SEED, m), tmp)
            add("O2", "OpenSSL VERIFIES a signature made here", v is True,
                "openssl said %s" % v)
            ok3 = True
            detail = []
            for n in (1023, 4096):
                m = bytes((i * 31 + 17) & 0xFF for i in range(n))
                s = _openssl_sign(DEV_SEED, m, tmp)
                good = s is not None and verify(mine, m, s)
                detail.append("%d:%s" % (n, good))
                ok3 = ok3 and good
            add("O3", "this file verifies OpenSSL's signature over 1023 and "
                "4096 bytes", ok3, " ".join(detail))
            m = b"RLXU cross-source"
            v = _openssl_verify(mine, m + b"!", sign(DEV_SEED, m), tmp)
            add("O4", "OpenSSL REJECTS a signature over a different message "
                "(O2's control)", v is False, "openssl said %s" % v)

    print("%s -- self-test" % VERSION)
    ok = fail = 0
    for cid, what, good, detail in rows:
        if good:
            ok += 1
            print("  ok     %-4s %-58s %s" % (cid, what, detail))
        else:
            fail += 1
            print("  FAIL   %-4s %-58s %s" % (cid, what, detail))
    for why, n in skips:
        print("  (skipped: %d case(s): %s)" % (n, why))
    print("  %d passed, %d failed" % (ok, fail))
    print("  dev public key (seed = 32 x 0x42): %s" % dev_public_hex())
    return 1 if fail else 0


# ---------------------------------------------------------------- the CLI
def cmd_pubkey(args):
    print(secret_to_public(read_seed(args)).hex())
    return 0


def cmd_sign(args):
    if not os.path.isfile(args["file"]):
        die("no such file to sign: %s" % args["file"])
    msg = open(args["file"], "rb").read()
    sig = sign(read_seed(args), msg)
    if args.get("out"):
        with open(args["out"] + ".tmp", "wb") as fh:
            fh.write(sig)
        os.replace(args["out"] + ".tmp", args["out"])
        print("%s  %d bytes" % (args["out"], len(sig)))
    else:
        print(sig.hex())
    return 0


def cmd_verify(args):
    for k in ("file", "sig"):
        if not os.path.isfile(args[k]):
            die("no such file: %s" % args[k])
    msg = open(args["file"], "rb").read()
    sig = open(args["sig"], "rb").read()
    if len(sig) == 129 and sig[128:] == b"\n":
        sig = sig[:128]
    if len(sig) == 128:
        try:
            sig = bytes.fromhex(sig.decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            die("%s is 128 bytes but not 128 hex digits" % args["sig"])
    if args.get("pubkey_hex"):
        try:
            pub = bytes.fromhex(args["pubkey_hex"].strip())
        except ValueError:
            die("--pubkey-hex is not hex")
    else:
        pub = secret_to_public(read_seed(args))
    if len(pub) != 32:
        die("a public key is 32 bytes, not %d" % len(pub))
    good = verify(pub, msg, sig)
    print("%s: signature %s" % (args["file"], "OK" if good else "BAD"))
    return 0 if good else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="rlxsign.py", description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="run the controls and exit")
    sub = ap.add_subparsers(dest="cmd")

    def keyargs(p):
        p.add_argument("--seed-hex", help="32-byte seed as 64 hex digits")
        p.add_argument("--seed-file", help="file holding the seed")
        p.add_argument("--dev-seed", action="store_true",
                       help="SPEC-R8a 3's published development seed "
                            "(32 x 0x42) -- not a secret, never production")

    p = sub.add_parser("pubkey", help="print the public key for a seed")
    keyargs(p)
    p.set_defaults(func=cmd_pubkey)

    p = sub.add_parser("sign", help="sign a file")
    p.add_argument("file")
    p.add_argument("--out", help="write the 64 raw bytes here (default: hex "
                                 "to stdout)")
    keyargs(p)
    p.set_defaults(func=cmd_sign)

    p = sub.add_parser("verify", help="verify a detached signature")
    p.add_argument("file")
    p.add_argument("--sig", required=True, help="the 64-byte signature")
    p.add_argument("--pubkey-hex", help="the public key, 64 hex digits")
    keyargs(p)
    p.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.cmd:
        ap.print_usage(sys.stderr)
        die("no subcommand.  `--self-test` runs the controls")
    return args.func(vars(args))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        die("interrupted")
    except (ValueError, OSError) as exc:
        # A refusal is one line and a reason.  A traceback out of a signer is
        # a tool telling the operator to read Python instead of the problem.
        die("%s" % exc)
