# PREDICTIONS — block 13: `G8b`, retried with a window that cannot be missed

**Written before power is re-applied.** `bench/2026-08-24f/`. Supersedes
`bench/2026-08-24e/PREDICTIONS-block12.md`, whose cells other than `A-catch`
never ran.

## Two missed catches today, two different causes, and the second is a procedure defect

| | cycle | what happened | cause |
|---|---|---|---|
| **1** | `24d`'s predecessor | told the operator to re-plug **first**, then say so. ESC started after the window closed | **sequencing** — mine. Fixed by starting the capture first |
| **2** | `24e` | capture started first and correctly, ESC ran 45 s, **the boot began at t=64.2 s** — nineteen seconds after the stream stopped | **window length**. `A-catch.meta.json` records `prompt_seen: false`, `waited_s: 3.015`, and the CR landing at offset 4422 with `Booting...` at 4426 |

🔴 **The second is a defect in the procedure, not in the operator.** The cost is
wildly asymmetric: an extra ESC second is free — the tool streams at ~50 bytes/s
into a buffer the loader empties every 128 bytes — while a missed window costs a
**power cycle**, which is the most expensive unit at this bench. A 45-second
window was sized for a laboratory, not for someone who has to physically reach a
barrel jack.

**Standing change**: `--esc 180 --seconds 200`. Three minutes of slack. The only
cost is that the capture file grows by ~7 KB of ESC echo, and the 1.2 terminator
tidies the buffer at the end regardless.

`bench/2026-08-24e/A-catch` is kept as the record of the failure mode — it is the
first capture in this project that shows what a missed ESC window looks like from
the instrument's side, and `cr.prompt_seen: false` beside a full 3-second settle
is exactly the signature.

## Cells

```cells
bench/2026-08-24f/A-catch2
bench/2026-08-24f/A0
bench/2026-08-24f/G8b-ab
bench/2026-08-24f/X1-24f
bench/2026-08-24f/G8b-flr0
bench/2026-08-24f/G8b-y0
bench/2026-08-24f/G8b-rd0
bench/2026-08-24f/G8b-flr6
bench/2026-08-24f/G8b-y6
bench/2026-08-24f/G8b-rd6
```

| | command | prediction | what it refutes |
|---|---|---|---|
| **A-catch2** | `--esc 180 --seconds 200 --cr-settle 3` | boot region **181 bytes, byte-identical** to `24c`/`24d`; ends on `Unknown command !` + `<RealTek>`; `cr.esc.written: true`, **`prompt_seen: true`** | the fifth power cycle with identical boot text, and 1.2's terminator for the fifth time. 🔴 **`prompt_seen` is now doing real work**: `24e` recorded `false` and that is what a missed window looks like |
| **A0** | `DW 8040DBC0 1` | **71 bytes**, byte-identical to `24c`/`24d`'s | rule 1 |
| **G8b-ab** | `DW 8040D4A0 1` | **`00000001`** | 🔴 **the positive control on `G8a`'s ordering.** "Every reset puts `AUTOBURN` back to `1`" has been an argument from the image's initialiser plus `B6`. This makes it a measurement. `00000000` here would mean `G8a`'s placement rested on a false premise |
| **X1-24f** | `DW 81000400 16` | `00000400 00000001 FFFFFFFF 00000000` / `00000000 00000000 81000418 81000418` | short-power-off DRAM retention, **fourth** instance. Two kernel runs have intervened since `X1-24d` |
| **G8b-flr0 / y0 / rd0** | `FLR 80A00000 000000 100` · `Y` · `DW 80A00000 64` | 104 / 35 / **777 bytes**; `rd0` 🔴 **byte-identical to `24d/G8a-rd0.log`** | that `G7`'s kernel did not write the loader head |
| **G8b-flr6 / y6 / rd6** | `FLR 80A00100 060000 100` · `Y` · `DW 80A00100 64` | as above; `rd6` 🔴 **byte-identical to `24d/G8a-rd6.log`** | that `G7`'s kernel did not write the `cr6c` header |

## What has run between `G8a` and this block

`G7`'s network-delivered kernel (live on the network, `boa` serving, ping 2/2 at
3.6 ms), **plus two further vendor-kernel autoboots** from the two missed
catches. So this block now covers **three** kernel executions rather than one —
the missed cycles cost time and bought coverage.

**Reach is unchanged and is what R0 may quote**: two `0x100`-byte reads are
**512 bytes of a 4,194,304-byte part**. *"The loader head and the `cr6c` header
are unchanged"* — not *"zero flash bytes written."*
