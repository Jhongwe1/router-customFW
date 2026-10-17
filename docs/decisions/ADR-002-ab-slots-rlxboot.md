# ADR-002: A/B update slots verified by `rlxboot`, not a single slot plus a recovery image

## Context
The stock loader is never replaced ([ADR-006](ADR-006-flash-write-rule.md)), and it boots an image at any of its 64 KiB scan candidates whose header reads `cs6c` with a zero 16-bit sum (讀, `check_image()`; `bank_offset` 量 0 on this unit). rlxfw's image in a container rounds up to 1,179,648 bytes of the 4 MiB flash. A slot write can be cut by power at any point, and the one recovery path outside rlxfw is a TFTP upload at the loader's prompt.
## Decision
Two slots, A at `0x070000` and B at `0x190000`, each 1,179,648 bytes, reachable only through `rlxboot`, a second-stage loader the stock loader starts from `0x010000`; a read-only copy, `rlxboot-rescue`, sits at `0x020000`, the one image the stock loader still boots when `0x010000` is broken. `rlxboot` copies both slots to RAM, verifies each copy — Ed25519 over the header, the payload digest, the signed destination, the version against the anti-rollback bitmap at `0x3F0000` — and boots the valid one with the higher version; if neither verifies it halts. The recorded reason: "Slots A and B are reachable only by `rlxboot`, and that is the whole design: the signature check and the anti-rollback counter are on the only path that leads to them." (`notes/update-chain.md` § 6)
## Alternatives considered
- **One slot of 3,670,016 bytes** with the same `rlxboot`, rescue copy and barrier, recorded as what a larger image would force: "with one slot there is nothing to fall back to when a write is interrupted", so a power cut would be survived by `rlxboot-rescue` plus a TFTP upload rather than by A/B (`notes/update-chain.md` § 6).
- **Slot A at `0x030000`**, the obvious layout: slot A would hold four of the loader's six scan candidates, and the loader could boot slot bytes directly, without `rlxboot`. `0x030000`–`0x06FFFF` is left erased instead; an erased word reads neither `cs6c` nor `cr6c` (讀).
- **A run-time *RAM first* choice** between a staged container and the slots: DRAM survives a power cycle (量, `MEM-17`), so a stale container from any earlier seating could win over both slots. The choice is fixed when the image is built (`notes/rlxboot.md`).
## Consequences
- 量 `R8b`: an update written to a flash slot boots through `rlxboot`; ten power cuts inside a slot write each booted the other slot; a torn `rlxboot` handed over to its rescue copy through the loader's own scan.
- For a `cr6c` header the loader also searches for a rootfs at eleven candidates, all inside slot A, and once slot A held a container it stopped silently at `<RealTek>`; `rlxboot` and its rescue copy carry `cs6c` instead (量, `FW-241`), found by the gate failing once.
- 2,883,584 of 4,194,304 bytes are used; a slot can grow to 1,835,008 bytes before the layout changes.
- Not established: an update the device performs itself — `R8b`'s writes went through an armed image RAM-booted through the loader, and the image in the slots has no write path — and a counter that has advanced: none has, so the bitmap's monotonicity is unread (`docs/threat-model.md` § 9).
## Evidence
[`notes/update-chain.md`](../../notes/update-chain.md) § 4 and § 6; [`notes/rlxboot.md`](../../notes/rlxboot.md), its 2026-10-05 section; [`docs/threat-model.md`](../threat-model.md) § 9; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entries 16 (`R8a`), 18 (`R8`) and 20 (`R8b`); [`SPEC.md`](../../SPEC.md) `FW-170`, `FW-241`, `MEM-17`. Decided: the layout and the single-slot comparison 2026-09-30 (`R8a-1`); booting from the slots, and the fixed selector, 2026-10-05 (`R8b-1`).
## Status
In force: `v1.0` (2026-10-09) is an image the device boots from slot A through `rlxboot`.
