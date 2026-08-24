# PREDICTIONS — block 10: `G8a`, the flash evidence for everything before `G7`

**Written before the first `FLR` of this power cycle.** Last block of
`bench/2026-08-24d/` before `G7`.

## Ordering, and both halves of it are load-bearing

🔴 **`DW 8040D4A0 1` has to be read *here*.** Every reset puts `AUTOBURN` back
to `1` — its initialiser in the image is `1` (`0x8040D4A0`) and `B6` measured `1`
on the device — and `G7` ends in a power cycle. So the same read afterwards
returns `00000001` and means nothing. **The word that matters is the one the burn
path saw *during* the two transfers**, and this is the last moment it can be
read.

🔴 **`FLR` writes the TFTP length global `0x8040DD28`**, so **no `put` or `get`
may follow it**. `G5` was the last transfer; this is the first moment `FLR` is
allowed.

## Cells

```cells
bench/2026-08-24d/G8a-ab
bench/2026-08-24d/G8a-flr0
bench/2026-08-24d/G8a-y0
bench/2026-08-24d/G8a-rd0
bench/2026-08-24d/G8a-flr6
bench/2026-08-24d/G8a-y6
bench/2026-08-24d/G8a-rd6
```

| | command | prediction |
|---|---|---|
| **G8a-ab** | `DW 8040D4A0 1` | **71 bytes**, word 1 = **`00000000`** — `AUTOBURN` still off after both uploads |
| **G8a-flr0** | `FLR 80A00000 000000 100` | `Flash read from 00000000 to 80A00000 with 00000100 bytes`, then `(Y)es , (N)o ? --> `. **104 bytes**, the size `G8pre-flr0` measured |
| **G8a-y0** | `Y` | `Flash Read Successed!` then `<RealTek>`, **35 bytes** |
| **G8a-rd0** | `DW 80A00000 64` | **777 bytes**, and 🔴 **byte-identical to `bench/2026-08-24c/G8pre-rd0.log`** |
| **G8a-flr6 / y6** | `FLR 80A00100 060000 100` · `Y` | as above |
| **G8a-rd6** | `DW 80A00100 64` | **777 bytes**, 🔴 **byte-identical to `bench/2026-08-24c/G8pre-rd6.log`** |

## What this establishes, and it is bounded

Between `G8-pre` and this block the device has: booted the vendor kernel from
RAM (`G6`), autobooted the vendor kernel from flash once, and received **two**
987,138-byte TFTP uploads with `AUTOBURN` off. **`G8-pre` read these same two
regions before any of that**, in the previous power cycle, and all 128 words
matched the dump.

So this is a **same-session `cmp` on two transcripts of the same command**, and a
single changed byte shows up without anyone reading hex — which is the point of
comparing captures rather than values.

| reading | verdict |
|---|---|
| both `.log`s byte-identical to `G8-pre`'s | ✅ nothing wrote the loader head or the `cr6c` header across two kernel boots and two uploads |
| any difference | 🔴 **stop.** Something wrote flash this session. `G7` does not run until it is understood — and the two dumps plus `G8-pre` mean the before-state is not in doubt |

🔴 **Reach, stated here because this is where it will be quoted from**: two
`0x100`-byte reads are **512 bytes of a 4,194,304-byte part**. The evidence line
R0 is entitled to is *"the loader head and the `cr6c` header are unchanged"* —
**not** *"zero flash bytes written"*, which needs a full re-dump hashed against
`FLS-14` and costs the 105 minutes that row records.

`0x80A00000` currently holds `G4`'s uploaded image; `FLR` overwrites the first
`0x200` bytes of it. That is harmless — `G7` jumps to `0x80500000`, which `G5`
verified at three points across 964 KiB.
