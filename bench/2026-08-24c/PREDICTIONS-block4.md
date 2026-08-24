# PREDICTIONS — block 4: `G1`, is the whole image already in RAM?

**Written before the reads.** Same power cycle as blocks 0–3c. Three `DW`s,
nothing written, no power cycle. This is the last block of `bench/2026-08-24c/`
— everything after it costs a power cycle and lands in `24d`.

## What `G1` decides

`B4` measured the first 16 bytes at `0x80500000` matching flash `0x060010`, and
`C-16` records that **nothing yet explains how they got there** —
`check_image()` reads `gCHKKEY_HIT` in its first two instructions and returns
before any header copy, so it cannot be the thing that filled RAM.

If the **tail and the middle** also match the dump, the loader has already staged
all **964 KiB** and `J 80500000` boots the vendor kernel from RAM with no network
at all. That is `G6`, and it becomes the reference the network path is compared
against. If they do not match, only the header region was copied and `G6` is
skipped — **which also costs `§G` one of its two power cycles.**

## Expected values, cut from the payload itself

Not from the sheet: read out of
`$FWRE_WORK/rebuild/r0-vendor-kernel.bin` (987,138 bytes, sha256
`396561a0…45a03e90`) at the offsets those addresses map to, `base = 0x80500000`.

| address | file offset | expected |
|---|---|---|
| `0x80500000` | `+0x00000` | `00000000 00008021 40906000 00000000` |
| `0x80580000` | `+0x80000` | `9D7111B4 08ABB9AE 978855A8 E63174AD` |
| `0x805F0FF0` | `+0xF0FF0` | `00000000 00000000 00000000 00000000` |

The middle and tail agree with what `RUNSHEET.md` `G1` carried; **that agreement
is itself a check that has now been made** rather than assumed, and the head is a
third point the sheet did not have.

```cells
bench/2026-08-24c/G1a
bench/2026-08-24c/G1b
bench/2026-08-24c/G1c
```

| | command | prediction | what it refutes |
|---|---|---|---|
| **G1a** | `DW 80500000 1` | `00000000 00008021 40906000 00000000`, **71 bytes** | reproduces `B4` on **this** power cycle rather than carrying it from a previous one. `C-16`'s subject |
| **G1b** | `DW 80580000 1` | `9D7111B4 08ABB9AE 978855A8 E63174AD`, **71 bytes** | 🔴 the middle. Distinctive, high-entropy, and it cannot arrive by accident |
| **G1c** | `DW 805F0FF0 1` | `00000000 00000000 00000000 00000000`, **71 bytes** | 🔴 the tail — **and today made this test much stronger than it was when written.** Uninitialised DRAM on this board is not zeros: `X1`, `X3`, `X4`, `G0-head/mid/tail` all read high-entropy bias garbage, and the bias is 89.5 % reproducible across a power cycle. So sixteen zero bytes here **can only have been written**, where in the original sheet they could have been read as "nothing is there" |

## What each outcome does to `§G`

| `G1a` | `G1b` / `G1c` | consequence |
|---|---|---|
| matches | **both match** | the whole 964 KiB is staged. **`G6` runs**, `§G` costs its two power cycles, and the reference boot exists |
| matches | either differs | only the header region was copied. **`G6` is skipped**, `§G` costs **one** power cycle, and `G7` alone has no reference — a successful boot would then prove only that *some* image booted, which is exactly what `G6` exists to prevent |
| differs | — | 🔴 `B4` does not reproduce, and `C-16`'s question changes from *"what copied it"* to *"what copied it that time"* |

**Either way `§G` proceeds** — `G6` is a control, not a precondition. What
changes is what `G7` is entitled to claim, and the power-cycle count.
