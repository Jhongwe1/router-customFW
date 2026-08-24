# PREDICTIONS — block 5: `G8-pre`, a flash baseline taken *before* any kernel runs

**Written before the first `FLR`.** Same power cycle as blocks 0–4. Six
captures, **no flash written** — `FLR` is the read primitive, `FLW` is the write
one and is on this session's do-not-type list.

## Why this block was added today

`§G` as written has `G8a` (after the transfers) and `G8b` (after `G7`'s kernel
boot), and both compare flash against **the backup dump** — taken on a different
day, on a different power cycle.

🔴 **But `G6` also boots the vendor kernel**, from RAM, before `G8a` exists, and
that kernel has an MTD driver and every ability to write. So the first kernel
execution of the session had **no before-reading at all**, and `G8a`'s
"unchanged" would have rested on a cross-session comparison.

This block takes the baseline **in this power cycle, before any kernel has
executed**, so `G8a` and `G8b` become same-session `cmp`s.

**`FLR` is safe to run here and only here.** `0x80409A04` stores its length
argument into `0x8040DD28`, the same global the TFTP read path serves from, so
**no `put` or `get` may follow an `FLR`**. There are no transfers yet, and the
power cycle after `G6` clears it — this is the one moment in `§G` where `FLR` is
free.

**Argument order, three sources, no device needed**: `FLR <dst_RAM> <src_flash>
<len>`, all three `strtoul(_, _, 16)` with **no bound check on any of them**.
The printf at `0x80409A18` renders `Flash read from %X to %X with %X bytes`
taking `argv[1]` first, which is the third source. A mistyped destination writes
a flash region over whatever is at it — including the loader's own `.data` at
`0x8040D000`+ — and the `(Y)es` prompt is the only thing between a typo and that.
**Both destinations here are inside `0x80A00000`–`0x80A00200`**, which `G0`
probed and which `G4` is going to overwrite anyway.

## Expected values, cut from the dump

`flash-n150rt-console-1.bin` and `-2.bin`, **4,194,304 bytes each, byte-identical
to each other**, sha256 `a800059a9b8c414d…` — the dump this whole sheet was cut
from. Two independent dumps agreeing is the control on the expectation itself.

**flash `0x000000`, the loader head** → `0x80A00000`:

```
+000: 0BF00004 00000000 00000000 00000000
+010: 00004021 40886000 00000000 3C01B800
+020: 00017825 8DEE0000 00000000 000E7025
+030: 3C018196 3421E000 00017825 15CF000A
```

**flash `0x060000`, the `cr6c` header** → `0x80A00100`:

```
+000: 63723663 80500000 00060000 000F1002
+010: 00000000 00008021 40906000 00000000
+020: 00000000 00000000 3C10805F 26101000
+030: 3C11805F 26311428 02004021 AD000000
```

`0x63723663` is `"cr6c"`; then `startAddr`, flash offset, length — the corrected
field order, and `000F1002` = 987,138 is the payload size this session verified.

🔴 **And `+0x010` here is `00000000 00008021 40906000 00000000`, which is byte
for byte what `G1a` just read at `0x80500000`.** Flash `0x060010` is where the
staged image begins, so `G1` and this block corroborate each other from opposite
directions — one through DRAM, one through the SPI part.

**All 64 words of each read must match the dump**, not just the 16 shown; the
comparison is done programmatically against the file.

```cells
bench/2026-08-24c/G8pre-flr0
bench/2026-08-24c/G8pre-y0
bench/2026-08-24c/G8pre-rd0
bench/2026-08-24c/G8pre-flr6
bench/2026-08-24c/G8pre-y6
bench/2026-08-24c/G8pre-rd6
```

| | command | prediction |
|---|---|---|
| **G8pre-flr0** | `FLR 80A00000 000000 100` | echo, `Flash read from 0 to 80A00000 with 100 bytes`, then `(Y)es , (N)o ? --> ` and **no `<RealTek>`** — the loader is waiting on a second line. Size not predicted: `%X` of a parsed `0` renders unpadded and has not been seen on silicon |
| **G8pre-y0** | `Y` | the read executes. A success line, then `<RealTek>`. **`Y` or `y` only** — anything else declines |
| **G8pre-rd0** | `DW 80A00000 64` | **777 bytes** (`14 + 2 + 47×16 + 9`), 16 lines, 64 words, matching the dump at `0x000000` |
| **G8pre-flr6** | `FLR 80A00100 060000 100` | as `flr0`, `Flash read from 60000 to 80A00100 with 100 bytes` |
| **G8pre-y6** | `Y` | as `y0` |
| **G8pre-rd6** | `DW 80A00100 64` | **777 bytes**, matching the dump at `0x060000` |

## What it refutes

- **that flash currently matches the backup at these two regions.** Nothing has
  written flash in this project, so a mismatch would mean either the dump is not
  this device's current state or something wrote flash since — and either is a
  finding that stops `§G` before a kernel is ever executed.
- **that `FLR` works at all on this device.** It has never been run here. If it
  does not, `G8a`/`G8b` are unavailable and R0's flash evidence has to be
  re-planned **now**, at the desk, rather than after two power cycles have been
  spent.
- **the three-captures-per-read claim**, which is desk-verified and has never
  been run: if `Y` on a separate line is not accepted, the confirmation prompt
  needs a different approach and `console-capture.py`'s one-line-per-send rule is
  what has to change.
