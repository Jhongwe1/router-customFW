# PREDICTIONS — block 12: `G8b`, the half `G8a` could not do

**Written before power is re-applied.** `bench/2026-08-24e/`, the second of
`§G`'s two power cycles, taken to recover the loader after `G7`.

## Why this block exists separately from `G8a`

`G8a` was read while the loader was still up, and it covers **the two
transfers**. It cannot cover `G7`, because `G7` had not happened yet.

🔴 **`G7` runs the vendor kernel, which has an MTD driver and every ability to
write.** It has now been running for the length of this power cycle, with a live
network and `boa` serving on port 80 — ping `10.1.1.1` answered 2/2 at 3.6 ms
after the stale ARP entry was cleared. **This block is the only thing that checks
what it did to flash.**

The comparison is `cmp` on two transcripts of the same command, so a single
changed byte shows up without anyone reading hex.

## Cells

```cells
bench/2026-08-24e/A-catch
bench/2026-08-24e/A0
bench/2026-08-24e/G8b-ab
bench/2026-08-24e/X1-24e
bench/2026-08-24e/G8b-flr0
bench/2026-08-24e/G8b-y0
bench/2026-08-24e/G8b-rd0
bench/2026-08-24e/G8b-flr6
bench/2026-08-24e/G8b-y6
bench/2026-08-24e/G8b-rd6
```

| | command | prediction | what it refutes |
|---|---|---|---|
| **A-catch** | `--esc 45 --seconds 65 --cr-settle 3` | boot region **181 bytes byte-identical** to `24c`/`24d`'s — the **fifth** consecutive power cycle. Ends on `Unknown command !` + `<RealTek>`; `cr.esc.written: true` | 1.2's terminator, fifth independent time. **And the `0xFF` again**: present on `24c`'s cold boot (after 16 h off), absent on `24d`'s (after seconds). This cycle also follows a seconds-long off, so *推* predicts **absent** |
| **A0** | `DW 8040DBC0 1` | **71 bytes**, byte-identical to `24c`/`24d`'s `A0.log` | rule 1 |
| **G8b-ab** | `DW 8040D4A0 1` | **`00000001`** | 🔴 **the positive control on `G8a`'s ordering argument.** `G8a` was read before this power cycle *because* "every reset puts `AUTOBURN` back to `1`". That has been an argument from the image's initialiser plus `B6`; this makes it a measurement **on this cycle**. If it reads `00000000`, the reason `G8a` had to be read when it was is wrong — and the guard's whole model needs re-examining |
| **X1-24e** | `DW 81000400 16` | `00000400 00000001 FFFFFFFF 00000000` / `00000000 00000000 81000418 81000418` | the **third** instance of short-power-off DRAM retention, after a third kernel run. `X1-24d` showed it; `G0-head-24d` showed it with content **I** wrote via `FLR`. A garbage reading here would mean retention is not reliable across cycles and the `H2` conclusion needs bounding |
| **G8b-flr0 / y0 / rd0** | `FLR 80A00000 000000 100` · `Y` · `DW 80A00000 64` | 104 / 35 / **777 bytes**; `rd0` 🔴 **byte-identical to `24d/G8a-rd0.log`** | that `G7`'s kernel did not write the loader head |
| **G8b-flr6 / y6 / rd6** | `FLR 80A00100 060000 100` · `Y` · `DW 80A00100 64` | as above; `rd6` 🔴 **byte-identical to `24d/G8a-rd6.log`** | that `G7`'s kernel did not write the `cr6c` header |

## What R0 is entitled to say when this passes

**Entitled**: the vendor kernel booted from RAM from bytes delivered over TFTP to
an address that was poisoned first and verified at three points across 964 KiB;
`AUTOBURN` measured `00000000` at the instruction the burn path reads, during the
transfers; and **the loader head and the `cr6c` header are unchanged** across
three kernel boots and two uploads, checked against a baseline taken before any
kernel executed this session.

**Not entitled**: *"zero flash bytes written."* `G8-pre`, `G8a` and `G8b` reach
**512 bytes of a 4,194,304-byte part** — two addresses chosen because they are
the two that would change. A full re-dump hashed against `FLS-14` is what that
sentence costs, and it is 105 minutes.

⚠️ **Sequencing**: the capture starts **before** power is pulled. The
mis-sequencing earlier today cost one power cycle and is recorded in
`24d/PREDICTIONS-block7.md`.
