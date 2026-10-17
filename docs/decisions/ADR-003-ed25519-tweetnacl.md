# ADR-003: Ed25519 from TweetNaCl, imported byte for byte and checked, for update signatures

## Context
`rlxboot` verifies an update on the Lexra core with no libc, no `malloc` and no exception handler (`notes/rlxboot.md` § 1), and the repository's claim is that its code is its own and provable. A verifier is "the one place where those two halves come apart" (`notes/rlxboot.md` § 5).
## Decision
The container's 96-byte header, which carries the payload's SHA-256, is signed with Ed25519, RFC 8032 (`notes/update-chain.md` § 1). Ed25519 verification and SHA-512 are imported from TweetNaCl 20140427, public domain, sha256 `02e65bc3…`: [`mk-import.sh`](../../src/rlxboot/test/mk-import.sh) regenerates `src/lib/ed25519.c` and `src/lib/sha512.c` by copying named line ranges, and [`check-import.sh`](../../src/rlxboot/test/check-import.sh) fails on a one-byte difference. No imported line is edited; there are deletions and one structural split. The recorded reason for importing: "RFC 8032's five vectors cannot refute a carry bug that shows on one input in 2^30, so a hand-written implementation would be a published claim whose refutation condition this project cannot write." (`SOURCES.json`, entry `tweetnacl`)
## Alternatives considered
- **Hand-written field arithmetic mod 2^255−19**: rejected on that refutation-condition argument, "not a difficulty one"; the import "costs exactly one thing -- it must be labelled".
- **TweetNaCl's own `crypto_sign_open`**: not retained. It copies the message into a variable-size caller buffer, which would sit in the trust path, and it accepts `s ≥ L`; rlxfw's wrapper refuses `s ≥ L` with its own reason code, driven on the host by a constructed `s + L` (`notes/rlxboot.md` § 5).
- **Another signature scheme, or another Ed25519 implementation**: the recorded reason for Ed25519 over other schemes, and for TweetNaCl over other implementations, was not found; looked in `notes/rlxboot.md`, `notes/update-chain.md`, `SOURCES.json`, `docs/sbom.md`, `docs/threat-model.md` and `docs/GATE-RESULTS.md` entry 16.
## Consequences
- The two files are labelled imports, never described as rlxfw's code (`docs/sbom.md`, row `X1a`). `src/lib/ed25519.c` carries the build's one warning exemption, `-Wno-sign-compare`, because editing imported crypto to silence a warning "is not a trade this gate makes".
- SHA-256 is rlxfw's own (`src/rlxboot/sha256b.c`), for the mirror-image reason: a hash has no rare-input failure mode of that kind, and the RFC 6234 vectors exercise the whole round schedule; it is cross-checked three ways.
- The host signer, [`tools/rlxsign.py`](../../tools/rlxsign.py), is a second, pure-Python implementation from the RFC, so signer and verifier are compared rather than one agreeing with itself; OpenSSL's Ed25519 is a third (`notes/update-chain.md` § 3).
- 量 `R8a`: a correct container verified and booted, a flipped payload bit was refused at the digest, a lower version was refused (`FW-170`). The production seed never enters the repository; its public half is compiled into `rlxboot` (`notes/rlxboot.md`, its 2026-10-05 section).
## Evidence
[`notes/rlxboot.md`](../../notes/rlxboot.md) § 1, § 5 and its 2026-10-05 section; [`notes/update-chain.md`](../../notes/update-chain.md) § 1 and § 3; [`SOURCES.json`](../../SOURCES.json), entry `tweetnacl`; [`docs/sbom.md`](../sbom.md), row `X1a`; [`docs/threat-model.md`](../threat-model.md) § 9; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 16 (`R8a`); [`SPEC.md`](../../SPEC.md) `FW-170`. Decided 2026-09-30, in `R8a`.
## Status
In force.
