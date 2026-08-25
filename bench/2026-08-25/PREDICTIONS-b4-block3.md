# PREDICTIONS — Session B4, block 3 (`H3a-early`, the free half of `C-17`)

**Written 2026-08-25 at the bench, after `H1c` and before this read is sent.**
Blocks 0 and 1 are on disk and their cells have run. **Block 2 does not exist
this seating** — that number belongs to `H2`, which is `R1g-4b`.

**This block holds one cell, and it holds one cell on purpose.** The remaining
`H3` cells — `H3b`'s four cable moves, `H3a`'s `J BFC00000`, `H3c`'s two `EW`
arming reads — need the operator's hands or a further reset, and a predicted cell
that does not run is a failure, correctly. They get their own block when the
operator is at the board.

## Why this read is free, and why it is now rather than after `H3a`

`RUNSHEET.md` §"Running order" already argued it: `H3a`'s `J BFC00000` exists to
produce *a warm reset with no kernel run since*, and **`H1b` already produced
exactly that** — `rlx_reset` writes the same `WDTCNR = 0` that `J BFC00000`'s
path does, and nothing between `H1b` and here has run a kernel. So the condition
`C-17` needs exists right now, and reading it costs one command.

If the reading is there, `H3a`'s own `J BFC00000` becomes a **second instance**
rather than the only one — and it is then the first thing dropped if the seating
runs long.

```cells
bench/2026-08-25/H3a-early
```

### `H3a-early` — `--send 'DW 81000400 16' --seconds 5`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H3a-early --send 'DW 81000400 16' --seconds 5
```

| | prediction |
|---|---|
| bytes | **214**, 4 lines — `len(cmd) 15 + 2 + 47 × 4 + 9` |
| content | 🔴 **bias garbage, and specifically NOT the 32-byte-periodic structure `C7-pre` measured.** The discriminator is `0x81000418`: `C7-pre` read `next = prev = &next` there — a word equal to its own address — and **uninitialised DRAM cannot produce its own address** |

**What each outcome means, written before the read:**

| what comes back | reading |
|---|---|
| garbage, no self-referential word | **the structure at `0x81000400` was written by the vendor kernel**, and `C-17`'s remaining half closes: it is not the loader's buffer pool. Consistent with `24d`'s `G0-head-24d`, which found the same window holding real content after a kernel had run |
| the 32-byte-periodic structure, `0x81000418` pointing at itself | 🔴 **something other than the vendor kernel writes it**, and since no kernel has run on this power cycle that something is the loader or `probe1`. `probe1` writes only `[0x80A00000, 0x80A00280)`, so it would be the loader — which is what `C-17` originally suspected and what `§G`'s upload-address choice was moved away from |
| all zero | neither; record it and do not read it as either outcome |

⚠️ **The expected value is a weak pass either way and this file says so before the
read.** `MEM-15` measured that a seconds-long power-off keeps DRAM contents, so
*the structure is absent* is also what a long power-off predicts. **What makes
this read decisive is only the self-referential word**: garbage cannot forge a
pointer to its own address, so a *positive* is strong and a *negative* is weak.
The board has been powered continuously since 14:10 today and the last kernel to
run on it was `G7`'s on 2026-08-24, about sixteen hours ago — which `MEM-15`'s own
sixteen-hour observation says is long enough for retention to be gone.

**Refutes**: `C-17`'s remaining half — *which execution wrote that structure*.
