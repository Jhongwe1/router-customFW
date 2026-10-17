# Architecture decision records

The decisions that shaped rlxfw, one page each: Context, Decision, Alternatives considered, Consequences, Evidence, Status. Every reason on a page is one the repository recorded, and its Evidence section says where; a page names the date the decision was taken. Measured claims are marked 量, claims read out of code or a dump 讀, inferences pending a measurement 推.

- [ADR-006](ADR-006-flash-write-rule.md) — Flash writes only under the owner's dated yes for that exact payload; the loader and `H601` never written.
- [ADR-010](ADR-010-bench-card-predictions.md) — Bench cards carry predictions frozen before power, and the relaxation of 2026-09-27.
