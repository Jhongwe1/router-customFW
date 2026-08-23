# Block 1 — the PHY reads that license §F, and the button GPIO that gives D3 a positive control

Written before any cell in this block was sent. `tools/check-predictions.py`
checks that against the captures' mtimes.

Context: the timer gate passed (`E1b`/`E2b`, 100.0078 Hz over 253.270 s), so
`phy_read()`'s `delay(10)` returns and PHY commands are licensed on this boot.
The cable is in physical jack 5, which `E11e` measured as **port 1**, so the PHY
address to read is **1** — taken from `E9`'s `ExtPHYID`, not from the jack
number, which is `E12`'s stated rule and the reason `E11e` mattered.

```cells
bench/2026-08-24b/E12b
bench/2026-08-24b/E12c
bench/2026-08-24b/E12d
bench/2026-08-24b/E12e
bench/2026-08-24b/B7a
bench/2026-08-24b/B7b
bench/2026-08-24b/E9b
```

Every cell is a read. Nothing in this block writes memory, resets the board, or
touches the flash path. Byte counts are computed the same way `A0` was verified:
echo = command + `\n\r` (2), each data line = 9 + 4×9 + 2 = 47, trailer
`<RealTek>` = 9.

---

## `E12b` — `PHYR 1 5`, the ANLPAR of the port that is linked right now

**This is the judgment on bits 6 and 5 of `PSRP`.** Seating 1 read `PHYR 2 5` →
`C1E1`, whose **bit 10 (PAUSE) is 0**, against a PC NIC, and its `PSRP2` had
bits 6,5 **clear**. Today's partner is an RTL8153 and every linked reading has
bits 6,5 **set**. If bits 6,5 are the negotiated flow control, this partner must
be advertising PAUSE.

- **Predicted**: bit 10 (`0x0400`) of the returned `ANLPAR` is **1**.
- **Refuted by**: bit 10 = 0. Then bits 6,5 of `PSRP` are not negotiated flow
  control and the explanation offered for the seating-1/seating-2 difference is
  wrong, with nothing to replace it.
- Also predicted: selector bits 4:0 = `00001` (802.3), as in seating 1.
- Not predicted, record it: bit 11 (ASM_DIR), bit 15 (NP), bit 14 (ACK).

## `E12c` — `PHYR 1 1`, the BMSR of the same port

Positive control that `phy_read()` works on this boot **before `F1` pokes an
address that may not answer**. `F1`'s risk is that a hang cannot be told from a
timer fault; this cell removes the timer from the list of causes.

- **Predicted**: `78ED` — bit 2 (Link Status) = 1 and bit 5 (Autoneg Complete)
  = 1, capability bits 15:11 identical to seating 1's `78ED`/`78C9` pair.
- **Refuted by**: bit 2 = 0 while `PSRP1` says LinkUp — then `PSRP` and `BMSR`
  disagree about link and one of them is not reading the port it is thought to.

## `E12d` — `PHYR 0 1`, the BMSR of an **unlinked** port

The paired negative control, on this boot rather than seating 1's. Jack 1 (WAN)
= port 0 and it has no cable.

- **Predicted**: `78C9` — bits 2 and 5 both **0**, bits 15:11 unchanged from
  `E12c`. Same part, different link state.
- **Refuted by**: `78ED` — then the value does not track link and `E12c` proves
  nothing.

## `E12e` — `PHYR 0 5`, the ANLPAR of the unlinked port

**No source predicts this and seating 1 never read it.** A link partner ability
register with no link partner is either zeroed or stale.

- **Not predicted.** Recorded as a measurement.
- What it decides: if it returns the *same* value as `E12b`, the register is not
  per-port and `E12b`'s reading is void.

## `B7a` — `DW B8003500 1`, button **released**

From the audit's read of `stage2-vma.dis`: `0x804083AC` (called unconditionally
from main at `0x80406778`) clears bit 5 of `0xB8003500` (`PABCD_CNR`) and of
`0xB8003508` (`PABCD_DIR`); `0x80408DE4` reads `0xB800350C` and masks `0x20`.
One `DW` prints all four words: w1 = CNR, w3 = DIR, w4 = DAT.

- **Predicted**: 71 bytes; w1 bit 5 = 0 and w3 bit 5 = 0 (the init ran).
- **Not predicted**: w4 bit 5, the button itself. This cell is the *released*
  half of a pair; the reading that matters is whether it **moves** when the
  button is held, which is `D3`'s positive control and needs the operator.
- **Refuted by**: w1 or w3 bit 5 = 1 — then `0x804083AC` did not run on this
  boot and `w4` is not the button.

## `B7b` — `DW B8000000 1`, the strap word the button read is multiplexed on

`0x80408DE4` first tests `(readl(0xB800000C) & 0xF) == 13` and takes the button
state from `[0x8040DD4C]+0x44` if so. `0xB800000C` is word 4 of this read.

- **Predicted**: 71 bytes. **Low nibble of word 4 ≠ 13** — because if it were,
  the loader would not be reading the GPIO at all and `B7a` would be measuring
  the wrong thing.
- **Refuted by**: low nibble = 13. Then `B7a`/`D3-gpio-held` are void as
  designed and the button state lives in a RAM structure instead.

## `E9b` — `DW BB804100 8`, `E9` re-read on this power cycle

`F2` (`MDIOR 2`) checks its 32-line sweep against `E9`'s `ExtPHYID` map. That map
was read on **seating 1's** power cycle. Re-establishing it here costs one read
and makes `F2` a comparison within one boot.

- **Predicted**, byte for byte from seating 1's `E9`:
  `00000000 007F0039 047F0039 087F0039` / `0C7F0039 107F0039 00000000 187F0038`
  — `PITCR` = 0, `ExtPHYID` (bits 30:26) = 0,1,2,3,4 across `PCRP0`–`PCRP4`,
  and `0x187F0038` carrying 6.
- **Refuted by**: any difference. `PCRP1`–`PCRP4` are reset defaults the loader
  never writes, so a change means either the loader's behaviour differs between
  boots or these are not the registers they are taken for. **The cable has moved
  four times this boot and sits in a different jack than in seating 1** — if
  `PCRP` were link-dependent, that would show here, and it must not.

---

## Cells deliberately NOT in this block, with the reason

- **`DW B8003000 1` (GIMR/GISR before a PHY read).** `E3` measured `GIMR` bit 8
  already 1 at the prompt, so a before/after around `PHYR` has nothing to flip —
  that is exactly how `E5` was void on arrival. Recovering it needs `EW` to clear
  the bit first, which is `C5`, and `C5` already ran. A read that cannot fail is
  not worth a cell.
- **`C1` re-arm and the `0x80A00000` canary.** They belong *after* `§F`: if `F1`
  hangs, the recovery is a power cycle and DRAM is lost, so arming before `§F`
  would have to be redone.
- **`F1`, `F2`, `§D`, `§G`.** Outside the authorised range — each needs an
  explicit yes.
