# PREDICTIONS — block 0b: what builds the structures at `0x81000400` and `0x81800000`

**Written before any of these captures ran**, same power cycle as block 0, same
instrument (`console-capture.py` 1.2). This block writes **nothing** — six `DW`
reads and one cable insertion.

## Why this block exists — block 0 refuted something nobody was testing

`X1` was supposed to answer *"did DRAM survive the power cycle"*. It did answer
it — **zero `C7A`/`C7B` survivors, so `D2b`/`D2c` are live**. But it also read
`0x81000400` as **uninitialised DRAM**, and part two read a live 32-byte-periodic
descriptor table at that exact address, at the exact same point in the boot.

The position is not in doubt. Part two's `.log` mtimes give the order
`A-catch → flush → A0 → C7-pre`; today's are `A-catch → A0 → X1`. **`C7-pre` and
`X1` are the same cell in the same slot, four captures apart, and they disagree.**

| | part two, `C7-pre` | today, `X1` |
|---|---|---|
| `0x81000400` | `00000400 00000001 FFFFFFFF 00000000` | `57890336 73F64BB7 34361357 BB0563F3` |
| `0x81000410` | `00000000 00000000 81000418 81000418` | `BF100273 5B335215 5ABF3B7E 1003B831` |
| period | 32 bytes, four records read | none |

**That today's reading is uninitialised DRAM and not a different structure is
itself measured, not assumed.** Two independent signatures:

1. **The power-on bias is 89.5 % stable across a 16-hour power-off.** `G0-head`
   against part two's `G4-addr-probe`, same address, two power cycles:
   **27 of 256 bits differ (10.5 %)**, where independent content would differ in
   ~50 %. Word 2 differs in **one** bit.
2. **The bias repeats with a 1 KiB period.** `0x81000000` against `0x81000400`
   in the same capture pair: 20/128 bits differ, and the word at `+0x08` is
   **identical** (`34361357`). That is DRAM row structure, not data.

*量* for both numbers. *推* for "SDRAM power-on cell bias" as the mechanism —
**refutation: a third power cycle**, and `§G` supplies two for free.

## The three hypotheses, and the free experiment for each

| | hypothesis | what would confirm it | cost |
|---|---|---|---|
| **H1** | the loader builds the pool **when the link comes up**. Part two booted with a cable in a jack (seating 1 left one in jack 2; `E10b`, which reads all-ports-down, is cell 11 — *after* `C7-pre`). Today booted with no cable in any jack — `ethtool` `Link detected: no` before power was applied | `X1c` shows the descriptor pattern | **this block** |
| **H1′** | it is built by **`IPCONFIG`**, not by link-up | `0x81000400` shows the pattern after `G2`'s `rescue` and not before | free, `§G` `G2` |
| **H2** | **nothing in the loader builds it.** It is retained content from a previous boot — a `list_head` at `+0x18` pointing to itself is what `INIT_LIST_HEAD` leaves, and the loader ran with a **short** power-off before parts one and two against **16 hours** today | the pattern is back after `G6`'s power cycle, which lasts seconds | free, `§G` `G6` |

🔴 **`C-17`'s premise is what is at stake.** It records the structure as *"most
likely the loader's network buffer pool"* and reasons *"uninitialised DRAM cannot
produce its own address, so something wrote both"*. The second half stands — a
self-pointer is not a bias pattern. **The first half has never been tested, and
under `H2` it is wrong**: the writer would be the *vendor kernel*, not the
loader, and `C-17` would be a question about DRAM retention rather than about the
loader at all.

**It also decides whether `D0a` needs `D0a-restore`.** If `H1`/`H1′`, the pool
exists by `§G` time and a corrupted descriptor 0 sits under a 987 KiB transfer.
If `H2`, `0x81000000` is unused DRAM at the loader prompt and the restore is
unnecessary. Today the trigger condition becomes a reading instead of a guess.

## Cells

```cells
bench/2026-08-24c/X1b
bench/2026-08-24c/X4
bench/2026-08-24c/E10c
bench/2026-08-24c/E10d
bench/2026-08-24c/X1c
bench/2026-08-24c/X4b
```

| | command | prediction | what it refutes |
|---|---|---|---|
| **X1b** | `DW 81000400 16` — **nothing changed** | **byte-identical to `X1`**, 213 bytes | 🔴 **the control that makes `X1c` mean anything.** Without it, "the pattern appeared" cannot be told from "it appears on its own given time". If `X1b` already differs from `X1`, something is writing that region while the prompt idles and **neither the cable nor `IPCONFIG` is the trigger** |
| **X4** | `DW 81800000 8` — before | not predicted; **required**: no pointer-shaped word. Part two read `81C09988 81810000 00000058 81800058 / 0000000F FFFFFFFF 00002534 00000001` — three pointers and `+0x0C` = base + `+0x08`'s value | the same question at the second structure. If `0x81800000` still holds its pointers today while `0x81000400` does not, the two have different writers and `C-17` is two questions |
| **E10c** | `DW BB804128 8` — no cable | `000010E0 000010E0 000010E0 000010E0 / 000010E0 000000E2 0000007A 0000007A` — **byte-identical to `E10b`** | that the board agrees with `ethtool` about there being no link. Third power cycle for `E10b`'s all-down reading, and words 6–8 invariant for the ninth time |
| **E10d** | `DW BB804128 8` — **cable in jack 2** | **word 3 = `000010F9`**, the other four `000010E0`. `000011F9` is also a pass — bit 8 is the down latch. Jack 2 → `PSRP2` is `E11a`'s measurement; `0xF9` not `0x99` because this partner is the RTL8153 and `PSRP` bits 6,5 follow its PAUSE advertisement (`E12b`) | 🔴 **that the link is up on the board and not merely on the host.** `ethtool` is the host's view; this is the switch's. Without it, a `X1c` that does not change has two explanations — no trigger, or no link |
| **X1c** | `DW 81000400 16` — after link-up | 🔴 **not predicted — this is the discriminator, and both outcomes are results.** `00000400 00000001 FFFFFFFF 00000000 / 00000000 00000000 81000418 81000418` ⇒ **`H1` confirmed**, the loader builds it on link-up, `C-17` is answered and the structure IS the network path. Byte-identical to `X1b` ⇒ **`H1` refuted**, and the next test is `G2`'s `IPCONFIG` | `H1`. A third reading — changed but not into the descriptor pattern — is recorded as its own row and not squeezed into either |
| **X4b** | `DW 81800000 8` — after link-up | as `X4`; the pointers appearing here and not at `0x81000400` (or the reverse) separates the two writers | `H1` at the second address |

## What this block cannot tell me

- It cannot separate `H1` from `H1′` if the answer is negative — only `G2` can.
- It cannot test `H2` at all. That needs a **short** power cycle, and `G6`'s is
  the one already being paid for.
- Six words at `0x81800000` and sixteen at `0x81000400` are two windows. Neither
  speaks for the 16 MiB between them.
