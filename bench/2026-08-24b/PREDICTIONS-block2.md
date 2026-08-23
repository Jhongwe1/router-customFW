# Block 2 — the button, read as a bit that moves instead of as an absence

Written before the button is touched. `tools/check-predictions.py` checks that
against the captures' mtimes.

```cells
bench/2026-08-24b/B7c
bench/2026-08-24b/flush-b7c
```

## Why this is a cell and not a step of `D3`

`RUNSHEET.md` `D3` presses the button and asks for "a full stage-1 cold boot",
with "anything less — nothing, or a reboot without the stage-1 lines" meaning
GPIO rather than `RESET#`. **That is a cell whose negative branch is an
absence**, and this repository's own rule (`RUNSHEET.md` `C1`'s verdict) says an
expected answer of *nothing* cannot tell a silent mechanism from one that never
received the input.

`B7a` measured, on this boot: `PABCD_CNR` = `0xFFFFFFDF` — **bit 5 is the only
cleared bit in the whole 32-bit word**, matching the disassembly's claim that
`0x804083AC` clears bit 5 of `0xB8003500` and `0xB8003508`; `PABCD_DIR` bit 5 =
0 (input); `PABCD_DAT` = `0x0000003C`, **bit 5 = 1**. `B7b` measured
`(0xB800000C & 0xF)` = `0xF`, not 13, so the loader's button read is not
multiplexed onto the RAM structure at `[0x8040DD4C]+0x44` and this pin is the
one it uses.

Operator's report, 2026-08-24: the small button beside the power button performs
a factory reset **when held for about ten seconds**. A hardware `RESET#` cannot
carry a hold-duration semantic — distinguishing one second from ten requires
software timing a GPIO. *Inferred, and it is evidence about the vendor kernel's
behaviour rather than about the wiring*; this cell is the measurement.

## `B7c` — `DW B8003500 1` with the button **held down**

Sent through `--esc-after 20 --seconds 35`, so the branch this cell does not
expect is recoverable: if the button is `RESET#`, the board is in reset when the
command is sent, the command goes nowhere, and the reboot that follows the
release is caught by the ESC stream inside the same capture — a prompt, not a
power cycle. That is `D1`'s instrument used for its other purpose.

Nothing is armed in DRAM at this point (`C1`'s scratch word has not been
re-written this boot, the `0x80A00000` canary has not been placed), which is why
this cell is placed here and not later.

**Three branches, and each is distinguishable in the log:**

| | log contains | reading |
|---|---|---|
| **A — GPIO** | `B8003500:` with w1 = `FFFFFFDF`, w3 = `FF000000`, **w4 = `0000001C`** | the button is `PABCD` bit 5, active low. `C-14` answered with a bit that moved. **`D3` will then NOT produce a cold boot**, and `D2b`'s refutation has to be re-planned around a power cycle |
| **B — `RESET#`** | no `B8003500:` line at all; `Booting...` and the stage-1 banner appear during the ESC stream | `C-14` answered the other way. `D3` stands as written and `D2b`'s cold-boot control works |
| **C — neither** | `B8003500:` with **w4 bit 5 still 1** (`0000003C`) | 🔴 **the button is not on this pin.** `B7a` measured a pin that is not the button, the disassembly reading is about something else, and `C-14`'s negative branch goes back to being an absence |

**Also predicted, in branch A**: w1 and w3 unchanged. A change in `CNR` or `DIR`
would mean pressing the button does more than drive one pin.
**Also predicted, in branch A**: w4 changes in **bit 5 only** — `0x3C` → `0x1C`.
Any other bit moving means more than one thing sits on this port and `B7a`'s
reading of "bit 5 is the button" is under-determined.

**Not predicted**: how many `Unknown command !` lines the ESC stream produces.
Measured this boot: ESC leaves the host at 50.2/s and the loader's line buffer is
128 bytes, so ~20 s of streaming is ~1000 bytes ≈ 7 fills plus a residue. The
count and the residue are recorded, not predicted, and the residue is what
`flush-b7c` consumes.

## `flush-b7c` — `--send ''`

Required because `B7c` streams ESC and the stream ends on a wall-clock deadline
with no terminator, leaving a partial line in the loader's 128-byte buffer.

- **Predicted**: `Unknown command !` then `<RealTek>` — the same 31-byte shape as
  `bench/2026-08-24b/flush.log`, because the residue is non-empty for any ESC
  count that is not an exact multiple of 128.
- **Refuted by**: a bare prompt with no `Unknown command !` — then the ESC count
  happened to be an exact multiple of 128 (1 chance in 128), or the residue model
  is wrong. The `B7c` log's own ESC count decides which, and it is in the file.
