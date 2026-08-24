# PREDICTIONS — block 9: `G4` and `G5`, the transport

**Written before the first TFTP packet.** `bench/2026-08-24d/`. Guard state,
measured moments ago and not assumed: `G2-rb` read `0x8040D4A0` word 1 =
`00000000`, so `AUTOBURN` is **off**; `G2-rescue.json` records
`load_addr: 0x80a00000`.

## `G4` — the round trip, proved without executing anything

```
loader-tftp.py put --host 10.1.1.1 --image $FWRE_WORK/rebuild/r0-vendor-kernel.bin
                   --rescue-report bench/2026-08-24d/G2-rescue.json
                   --expect-load 80A00000 --yes --report bench/2026-08-24d/G4-put.json
loader-tftp.py get --host 10.1.1.1 -o bench/2026-08-24d/G4-back.bin --force
cmp G4-back.bin r0-vendor-kernel.bin
```

| | prediction |
|---|---|
| `put` | **987,138 bytes**, sha256 `396561a0…45a03e90`, 1,929 blocks of 512 |
| `get` | the same 987,138 bytes back |
| `cmp` | **byte-identical** |

**Flag conventions, verified against the pinned `4d3ff26` today, not recalled**:
`--image` (not `--file`), `--rescue-report` **required**, `--yes` **required**,
and `--expect-load` is `int(s, 16)` — **bare `80A00000`, no `0x`** — the
**opposite** convention to `rescue --load-addr`, which is `int(s, 0)` and took
`0x80A00000`. Same session, twenty minutes apart.

🔴 **Blind spot, stated because it is why `G5` exists**: `put` and `get` both
serve `[0x8040D3A8]`, so a round trip **cannot** catch a load address that is
consistently wrong. `G4` proves the bytes survived the wire; it does not prove
where they landed.

🔴 **Never a filename containing `nfjrom` or `boot.img`** — those two force the
load address to `0x80000000` and auto-execute the moment the transfer ends, with
nobody at the console. `loader-tftp.py` refuses them without `--allow-autoexec`.

## `G5` — where it landed, which `G4` structurally cannot test

Poison three points spread across 964 KiB, upload again, read the three back.

```cells
bench/2026-08-24d/G5-poison1
bench/2026-08-24d/G5-poison2
bench/2026-08-24d/G5-poison3
bench/2026-08-24d/G5-rb1
bench/2026-08-24d/G5-rb2
bench/2026-08-24d/G5-rb3
```

| | command | prediction |
|---|---|---|
| **G5-poison1/2/3** | `EW 80500000 5A5A5A5A` · `EW 80580000 5A5A5A5A` · `EW 805F0FF0 5A5A5A5A` | silent, **31 bytes** each (`len(cmd) + 11`) |
| *(then)* | `rescue … --load-addr 0x80500000 -o G5-rescue.json`, then `put … --expect-load 80500000 --yes` | `Set TFTP Load Addr 0x80500000`; 987,138 bytes |
| **G5-rb1** | `DW 80500000 1` | `00000000 00008021 40906000 00000000` |
| **G5-rb2** | `DW 80580000 1` | `9D7111B4 08ABB9AE 978855A8 E63174AD` |
| **G5-rb3** | `DW 805F0FF0 1` | `00000000 00000000 00000000 00000000` |

All three expected values were **cut from the payload file today** at offsets
`+0x00000`, `+0x80000`, `+0xF0FF0`, and `G1a`/`G1b`/`G1c` then read exactly those
three from DRAM before anything was uploaded.

🔴 **Poisoning first is what makes a match mean anything.** `G1` showed the
loader had already staged the correct bytes at `0x80500000`, so an unpoisoned
re-read would pass whether or not a single packet arrived. `5A5A5A5A` at each
point after the poison and the dump's own bytes after the upload is the only
sequence that discriminates.

🔴 **The second `LOADADDR` goes through `rescue` too**, for the same reason as
`G2`: `--expect-load` is checked against a transcript, and a `LOADADDR` typed
outside one leaves nothing to check against. `LOADADDR` is on `console-dump.py
cmd`'s refusal list and `rescue` is where it has a deliberate home.

⏱ **`--max-rescue-age` defaults to 3600 s** and `G2`'s transcript was produced
minutes ago **on this power cycle**, which is what it is for: `AUTOBURN` is RAM
state that a power cycle clears, so a transcript from before the cycle would
describe a switch that has since flipped back.

## What this block cannot tell you

- **Nothing about flash.** `G8a` and `G8b` do that, and `G8-pre` gave them a
  same-session baseline — 128 words at flash `0x000000` and `0x060000`, all
  matching the dump, read before any kernel executed this session.
- **Nothing about execution.** `G7` does that, and it is deliberately after
  `G8a` because `FLR` writes the TFTP length global and no transfer may follow
  it.
