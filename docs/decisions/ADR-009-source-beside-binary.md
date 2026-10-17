# ADR-009: The corresponding source ships beside the binary in the same release (GPL-2.0 § 3(a)), not a written offer

## Context
The image carries GPL-2.0 code — Realtek's `linux-2.6.30` tree and BSP, busybox, rlxfw's own kernel sources — and LGPL-2.1 uClibc linked statically into every ELF (`docs/offer.md` § 2). The base drop is a third party's repository: it reports no licence and can be deleted or rewritten by its owner (量, `docs/sbom.md` § 2.4). No release before `v1.0` carried a binary: `v0.2`–`v0.6` have no asset (量 2026-10-08).
## Decision
"Every release of this repository that carries a binary asset carries, as a second asset of the same release, the corresponding-source archive of that binary." (`docs/offer.md` § 0) [`tools/srcarchive.py`](../../tools/srcarchive.py) builds the archive from the release commit out of the declarations the build reads: the drop's declared paths, read at its pin, the repository at that commit, and a generated per-file modification record, with a manifest inside that is the authority on what it holds. `docs/release-process.md` phase C uploads the binaries with their archive, or uploads none of them.
## Alternatives considered
- **A written offer under § 3(b)**, the form `docs/offer.md` took on 2026-10-04, when it said it did not bind yet because no release carried a binary. Replaced on 2026-10-05, the recorded reason being that the source beside the binary leaves "no three-year clock, no medium and no charge" (`docs/offer.md` § 0; [`LOG.md`](../../LOG.md), its 2026-10-05 entry).
- **Pointing at the drop's URL**: "a URL it does not control is neither" a supply of source nor a written offer (推, `docs/sbom.md` § 2.4). The archive carries the drop's declared paths, so a recipient needs nothing from that repository to read the source of the binary.
## Consequences
- `v1.0` is the first release with a binary, and it ships the image and `T.rlxu` together with their archive (`docs/offer.md` § 0).
- Two gaps are stated rather than closed: iperf3 cannot be built from a clean clone (`SBOM-3`), and no pinned tree holds gcc or binutils source, so the archive has nothing for `libgcc.a` (`SBOM-4`) (`docs/offer.md` § 4). 推 The toolchain still comes only from the third party's repository (§ 2).
- The archive is not a promise of a bit-for-bit rebuild: a third party rebuilding the recipe gets a different banner and sha256 (`P4A-1`, `docs/offer.md` § 3).
- No tag is signed, so an archive is tied to something unsigned; what a recipient can check is the commit id and the sha256 of every asset, which the release notes list (`docs/offer.md` § 0).
## Evidence
[`docs/offer.md`](../offer.md) § 0, § 2, § 3 and § 4; [`docs/release-process.md`](../release-process.md); [`docs/sbom.md`](../sbom.md) § 2.4; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 23 (`P4b`), its ruling 1; [`docs/history/changelog-through-v1.0.md`](../history/changelog-through-v1.0.md), the written offer of 2026-10-04; [`LOG.md`](../../LOG.md), the 2026-10-05 entry (124th segment). Decided 2026-10-05, by the main session under the owner's delegation of that day.
## Status
In force: `v1.0` (2026-10-09) shipped under it.
