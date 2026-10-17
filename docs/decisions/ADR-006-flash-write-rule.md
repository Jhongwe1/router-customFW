# ADR-006: Flash writes only under the owner's dated yes; the loader and `H601` never written

## Context
There is one N150RT and no spare. Its 4 MiB SPI NOR holds the stock loader at `0x000000`–`0x005FFF` and `H601` at `0x006000`–`0x007FFF`, this unit's MAC and radio calibration, which no reset restores. Nothing on the device guards either region: the loader's `EW` and `EB` write any address with no bound check (量, `LDR-08`, `LDR-09`), and its `burn()` has an upper bound only and accepts a `boot` section (讀, `LDR-28`), so only this project's own tools can enforce a rule about them. The one recovery path is the loader's own TFTP rescue.
## Decision
No path ever writes the loader region or `H601`. The mainline was zero-write through `R9`, and a write needs the owner's explicit yes. Since 2026-09-23 that yes is dated, names the exact payload and sits as an `owner-yes` row on the bench card, compared byte for byte by `tools/cardcheck.py`, which refuses `FLW`, `EW`, `EB` and every `AUTOBURN` but `AUTOBURN 0` without one (`FW-113`).
## Alternatives considered
- **A second recovery path through an SPI programmer clip**, not taken on 2026-08-23: the clip's far end is soldered, so its `VCC` line cannot be opened, and with the board powered `CLK` and `CS#` are SoC outputs the programmer would drive against. "A recovery path that might cost the device is not a recovery path."
- **`P1`'s erase-and-write-back sector check and its cleared-MAC injection**, struck 2026-09-16: the owner had delegated the decision, and a delegation is not the explicit yes the rule asks for; clearing the MAC writes `H601`. `trywrite`, which calls the driver's write and erase pointers and is refused by both, and a simulated `FAIL-MAC` replaced them.
- **The rule kept as a habit**: on 2026-09-23 the card checker passed `FLW 0 0 0` and `EW 8040D4A0 1`, so the rule had no enforcer at the card layer; it became a tool refusal.
## Consequences
- The one component that could enforce a root of trust is the one component rlxfw may never replace (`docs/threat-model.md` § 6); `rlxboot` runs after it, never in its place.
- *Not one flash byte is written* cannot be claimed: 量 2026-09-08 and 2026-09-09, the flash differed from the 2026-08-16 dump in two 4 KiB sectors, at `0x9000` and `0xD000`, cause undetermined (`FLS-26`). Records state the commands issued and the reach of the read-back brackets instead.
- `P1` did not test whether this flash can be written, and `cardcheck` reads single-quoted `--send` strings, never an upload (`FW-113`).
- 量 `R8b`: 33 driver write verbs, each under a dated yes for that exact string, through rlxfw's own install path; no `FLW`, `EW`, `EB` or non-zero `AUTOBURN` sent; the loader region read equal at five points.
## Evidence
[`CLAUDE.md`](../../CLAUDE.md) § Never and § Flash; [`docs/threat-model.md`](../threat-model.md) § 6; [`notes/power-and-programmer.md`](../../notes/power-and-programmer.md) § 4; [`docs/loader-flash-write.md`](../loader-flash-write.md) § 1; [`docs/mfgtest.md`](../mfgtest.md) § 1; [`SPEC.md`](../../SPEC.md) `FW-113`, `LDR-08`, `LDR-09`, `LDR-28`, `FLS-26`; [`docs/GATE-RESULTS.md`](../GATE-RESULTS.md) entry 20 (`R8b`); in [`docs/log/2026-08.md`](../log/2026-08.md) the 2026-08-23 entries `DAY-ZERO` 2b and 2c, and `S0b` (that day's third segment); in [`docs/log/2026-09.md`](../log/2026-09.md) the 81st, 102nd and 104th segments. Decided: the two regions and the explicit yes in the first `CLAUDE.md`, 2026-08-23; the dated yes per payload 2026-09-23 (`P2-2`).
## Status
In force. The zero-write mainline ended as scheduled when `R9` closed (2026-10-04); the forbidden regions and the dated yes did not change.
