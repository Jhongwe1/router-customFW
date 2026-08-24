# PREDICTIONS — block 8: re-probing the upload address, then `G2`

**Written before the reads.** `bench/2026-08-24d/`, the power cycle that
recovered the loader after `G6`.

## Why `G0` has to be re-read on this cycle

`G0` chose `0x80A00000` as `§G`'s upload address, and its refutation condition
was **"any pointer-shaped word and the address is re-chosen"**. This morning
`G0-head`/`G0-mid`/`G0-tail` found none — 48 words, no aligned pointer, no
self-reference, no period.

🔴 **`X1-24d` has just changed what a pointer-shaped word in DRAM *means*.** The
structure at `0x81000400` is the **vendor kernel's**, retained across a
seconds-long power-off, and this morning's readings were taken after a 16-hour
one. So on **this** cycle, DRAM anywhere may hold the previous kernel's content,
pointers and all — and a pointer there would mean *"a dead kernel's leftovers"*,
not *"something live is using this"*.

**`G0`'s test was built for the wrong failure mode and this is the correction**:

| `G0-head-24d` at `0x80A00000` | meaning | does `§G` proceed? |
|---|---|---|
| high-entropy garbage, like this morning | the region was never touched by the kernel either | **yes**, unchanged |
| pointer-shaped / structured words | **retained kernel content, not live loader state.** The loader is the only thing running now and it did not put them there | **yes** — and `G4` overwrites them, which is the point |
| **the same words this morning's `G0-head` read** | 🔴 nothing predicts this. Bias would have to reproduce across a kernel boot that used the region | stop and record |

**What would still stop `§G`** is unchanged and is not this cell: `G2`'s
`AUTOBURN` read. That is the guard.

## Cells

```cells
bench/2026-08-24d/G0-head-24d
bench/2026-08-24d/G2-rb
bench/2026-08-24d/X1-post
```

`G2` itself is `upstream/tools/console-dump.py rescue`, which writes a JSON
transcript rather than a `.log`, so it is not in the cells block. Its output is
`bench/2026-08-24d/G2-rescue.json`.

| | command | prediction | what it refutes |
|---|---|---|---|
| **G0-head-24d** | `DW 80A00000 16` | **213 bytes.** Value not predicted — see the table above | that the upload address is in use by anything **running** |
| **G2** *(not a cell)* | `console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x80A00000 -o bench/2026-08-24d/G2-rescue.json` | in the transcript, in this order: `AutoBurning=0`, then the loader echoing `0x80a00000`, then `Now your Target IP is 10.1.1.1` | ⚠️ **`--load-addr` is `int(s, 0)` — `0x80A00000` with the `0x`.** `--expect-load` in `G4` is `int(s, 16)` — bare `80A00000`. Opposite conventions, same session, verified against the pinned tools today |
| **G2-rb** | `DW 8040D4A0 1` | **71 bytes**, word 1 = **`00000000`** | 🔴 **the operative guard, read at exactly one instruction — `0x80401B9C`, on the upload-completion path.** `C6` proved the switch works; this is it re-sent because the power cycle put `AUTOBURN` back to `1` (its initialiser in the image is `1`, and `B6` measured `1` on the device). **If word 1 is not `00000000`, nothing is uploaded and I stop.** |
| **X1-post** | `DW 81000400 16` | 🔴 **the `H1′` test, and it is now nearly settled in advance.** `X1-24d` already read the structure **before** `IPCONFIG` ran, so `IPCONFIG` cannot be what creates it. This read asks the remaining question: does bringing the loader's network up **modify** it? Prediction: **byte-identical to `X1-24d`** | `H1′`. A change here means the loader does use this region once its network is up — which would make it live again for the duration of `G4`'s transfer, and `D0a`-style writes into it genuinely dangerous |

## What `H2`'s confirmation does to the rest of `§G`

- **`C-17` is answered**: the writer is the **vendor kernel**, not the loader.
  *"Most likely the loader's network buffer pool"* is withdrawn. The residual
  question is no longer "what allocates it" but **"how long does this DRAM retain
  content"**, which is a different question with a different owner.
- **`D0a-restore` is cancelled outright.** It was gated on the structure being
  live loader state. It is not.
- **Every future canary is affected**: this DRAM retains *content*, not merely
  bias, across a short power-off. A canary that survives a power cycle proves
  nothing unless the power-off is long — and `X1`/`X2` this morning, across 16
  hours with zero survivors, is what makes `D2b`/`D2c` sound.
