# Architecture decision records

The decisions that shaped rlxfw, one page each: Context, Decision, Alternatives considered, Consequences, Evidence, Status. Every reason on a page is one the repository recorded, and its Evidence section says where; a page names the date the decision was taken. Measured claims are marked 量, claims read out of code or a dump 讀, inferences pending a measurement 推.

- [ADR-001](ADR-001-vendor-kernel-base.md) — Linux 2.6.30 from the vendor's GPL drop as the kernel base, not a mainline kernel.
- [ADR-002](ADR-002-ab-slots-rlxboot.md) — A/B update slots verified by `rlxboot`, not a single slot plus a recovery image.
- [ADR-003](ADR-003-ed25519-tweetnacl.md) — Ed25519 from TweetNaCl, imported byte for byte and checked, for update signatures.
- [ADR-004](ADR-004-init-never-execs-shell.md) — PID 1 never execs a shell.
- [ADR-005](ADR-005-codegen-constraints.md) — `-fno-if-conversion` and the other code-generation constraints for this core.
- [ADR-006](ADR-006-flash-write-rule.md) — Flash writes only under the owner's dated yes for that exact payload; the loader and `H601` never written.
- [ADR-007](ADR-007-timer-one-role.md) — The timer driver is either a clocksource or a clockevent device, not both.
- [ADR-008](ADR-008-blind-drivers.md) — Drivers written blind first, then diffed against the two public RTL8196E trees.
- [ADR-010](ADR-010-bench-card-predictions.md) — Bench cards carry predictions frozen before power, and the relaxation of 2026-09-27.
