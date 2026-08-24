# PREDICTIONS — block 11: `G7`. R0 closes here.

**Written before `J 80500000`.** Last cell of `bench/2026-08-24d/`. Ends with a
kernel running and the loader gone.

## What is different about this jump

`G6` booted bytes **the loader staged itself** from flash. `G7` boots bytes that
came **over the wire**, into an address that was poisoned first and verified
after:

- `G4`: 987,138 bytes to `0x80A00000`, read back, `cmp` byte-identical, sha256
  `396561a0…45a03e90`.
- `G5-poison1/2/3`: `5A5A5A5A` written to `0x80500000`, `0x80580000`,
  `0x805F0FF0`; `G5-pv1/2/3` confirmed all three landed with words 2–4 untouched.
- `G5`: re-pointed `LOADADDR` to `0x80500000` through `rescue`, uploaded again.
- `G5-rb1/2/3`: `00000000 00008021 40906000 00000000` / `9D7111B4 08ABB9AE
  978855A8 E63174AD` / `00000000 00000000 00000000 00000000` — the dump's own
  bytes at three points spread across 964 KiB.
- `G8a`: `AUTOBURN` still `00000000`, and both flash regions **byte-identical**
  to the baseline taken before any kernel ran this session.

```cells
bench/2026-08-24d/G7
```

**Command**: `--send 'J 80500000' --seconds 60`

## Prediction

🔴 **The same output as `G6`, line for line.** `G6` was compared against
`upstream/dumps/uart-boot.log` from `decompressing kernel:` onward and came back
**63 lines compared, 63 identical, 0 differing**. `G7` is compared against `G6`
itself — same board, same power-cycle-adjacent conditions, forty minutes apart.

**The question R0 asks is not "did a kernel boot".** It is *"did the network
path deliver the same bytes"*, and a difference here is a **transport fault**
caught against a reference produced on this board rather than against a hope.
Without `G6` a successful `G7` would prove only that *some* image booted.

| reading | verdict |
|---|---|
| identical to `G6` from `decompressing kernel:` to `boa: starting server` | ✅ **R0 closes.** The device executed an image it received over the network, and the two flash regions checked are unchanged |
| boots but differs | 🔴 a transport fault, localised by the first differing line |
| `---Jump to address=80500000` then silence | 🔴 two causes, not one: jumped and the target was silent, or never jumped |
| output stopping **mid-line** | 🔴 **its own row.** This is what upstream's `P9-12` actually got, from an `andi` in a load delay slot. The image here is the vendor's, so that particular cause is off the table — which makes this outcome more interesting, not less |

## What R0 is entitled to claim when this passes, and what it is not

**Entitled**: the vendor kernel booted from RAM, from bytes delivered over TFTP
to a verified address, with `AUTOBURN` measured off at the instruction the burn
path reads, and **the loader head and the `cr6c` header unchanged** across the
whole session — checked against a baseline taken in the previous power cycle,
before any kernel executed.

**Not entitled**: *"zero flash bytes written."* `G8-pre`, `G8a` and `G8b` reach
**512 bytes of a 4,194,304-byte part**. A full re-dump hashed against `FLS-14`
is what that sentence would cost, and it is 105 minutes.

## After this cell

The loader is gone. **Power cycle #2**, and `G8b` — the same two `FLR` reads,
`cmp`'d against `G8a` — lands in `bench/2026-08-24e/`. That is the half `G8a`
could not do from its own position: `G8a` covers the transfers, `G8b` covers
`G7`'s kernel, **and `G7` runs the vendor kernel, which has an MTD driver and
every ability to write**.

⚠️ **Sequencing, which cost a cycle earlier today**: the ESC stream starts
**before** power is re-applied. Capture first, then pull, then re-plug.
