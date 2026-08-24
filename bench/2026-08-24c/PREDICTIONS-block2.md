# PREDICTIONS — block 2: arming `D2b` and `D2c`

**Written before the first `EW`.** Same power cycle as blocks 0, 0b and 1; same
instrument (`console-capture.py` 1.2). Cable is in the jack the operator calls
**port 2**, confirmed on the board by `E10d` (`PSRP2` bit 4 set, `PSRP1` bit 8
latched from the departure).

**These are the first writes of the session.** Two `EW`s into DRAM, then two
`DW`s that read them back. No flash, no `J`, no `EB`.

## What changed in `§D` because of what today measured

`RUNSHEET.md`'s `§D` was written against part two's DRAM. Three of its numbers
are stale, and two of them would have failed for reasons that are not findings.

| | as the sheet has it | why it is wrong today | what replaces it |
|---|---|---|---|
| `D2c` expected | `5EA72D2B A5A5A5A5 11744D3C E1553515` | words 3–4 come from `G4-addr-probe`, measured on the **previous** power cycle — that is last cycle's uninitialised DRAM, and this device's power-on bias is only 89.5 % stable | `5EA72D2B A5A5A5A5 13344D3C A1573115`, from `G0-head` **this** power cycle |
| `D2b` outcome 2 | `00000400 00000001 FFFFFFFF 00000000` = "the table's initialiser re-ran" | there **is** no table at `0x81000000` this boot. `X3` read `00000144 7BB04BB7 34361357 AB2563FB` — bias noise. The row cannot occur as written | rewritten below, against `X3`'s measured value |
| `D0a-restore` in `§D` | restore the descriptor before `§G`'s transfer | `X1`/`X1b`/`X1c`/`X4`/`X4b` show no structure at `0x81000000` **or** `0x81000400` at the loader prompt, with a live link. `D0a` corrupts nothing | moves to `§G`, immediately before `G4`, gated on a `DW 81000000 1` taken after `G2` — which tests `H1′` in the same read |

## Cells

```cells
bench/2026-08-24c/D0a
bench/2026-08-24c/D0b
bench/2026-08-24c/D0-rb1
bench/2026-08-24c/D0-rb2
```

A silent `EW` reply is **`len(cmd) + 11`** bytes — echo, `\n`, `\r`, `<RealTek>`.
Checked against part one: `C1` (29 chars) → **40**, `C3a` (20 chars) → **31**.
Both commands below are 29 characters, so both are **40 bytes**.

| | command | prediction | what it refutes |
|---|---|---|---|
| **D0a** | `EW 81000000 DEADBEEF CAFEBABE` | silent, **40 bytes** | nothing on its own — it is `D2b`'s payload. `C1`'s pattern, re-armed, so the two are directly comparable |
| **D0b** | `EW 80A00000 5EA72D2B A5A5A5A5` | silent, **40 bytes** | 🔴 the value is **deliberately not** `DEADBEEF CAFEBABE`. Reading it back proves *this* write arrived, not that *some* write once did — the two addresses cannot be confused for each other |
| **D0-rb1** | `DW 81000000 1` | **71 bytes**, `81000000:\t DEADBEEF\tCAFEBABE\t34361357\tAB2563FB` | 🔴 **the pairing `§D` had lost.** `D0a`'s expected reading is *silent*, and a silent `EW` is indistinguishable from a refused one. Without this, "the canary is gone after the reset" cannot be told from "the write never landed" — and `C1`'s own verdict in this file says an expected answer of *nothing* cannot tell a silent mechanism from an input that never arrived. Words 3–4 are `X3`'s, untouched, and are the free control that `EW` wrote **two** words and not four |
| **D0-rb2** | `DW 80A00000 1` | **71 bytes**, `80A00000:\t5EA72D2B\tA5A5A5A5\t13344D3C\tA1573115` | as above at the second address. Words 3–4 are `G0-head`'s, and they are what `D2c` will compare against after the reset |

## `D2b` and `D2c`, rewritten — read as one result, and it now has four rows

`D1` is a **warm** reset (`J BFC00000` → `WDTCNR = 0` → watchdog). DRAM is not
power-cycled, so the question is what, if anything, rewrites these two addresses
across it.

| `D2b` at `0x81000000` | `D2c` at `0x80A00000` | what it is |
|---|---|---|
| `DEADBEEF CAFEBABE 34361357 AB2563FB` | `5EA72D2B A5A5A5A5 13344D3C A1573115` | **DRAM survived the warm reset and nothing rewrote either address.** `C-8` gets its second discriminator: a canary tells warm from cold with no status bit involved |
| `00000400 00000001 FFFFFFFF 00000000` | canary intact | 🔴 **the descriptor table appeared during the warm boot.** Then something *does* build it, the trigger is on the warm-reset path and not on link-up, and `C-17` gets dated. Would be a finding in its own right |
| `00000144 7BB04BB7 34361357 AB2563FB` — `X3`'s exact pre-write value back | either | 🔴 **nothing predicts this.** DRAM re-acquiring its power-on bias without power being removed has no mechanism in any model here. Record it and stop; do not reason forward from it |
| anything else | not `5EA72D2B` | **DRAM contents did not survive a warm reset.** Then neither cell discriminates, `C-8` has no second observable, and R4's `bench-ci` needs a third |

**The refutation `D3` was supposed to supply is already banked**, and it did not
cost `§G`'s first power cycle: `X1`/`X2` found **zero** `C7A`/`C7B` survivors
from part two across a 16-hour power-off, against 23 distinctive words. So
`D2b`/`D2c` are measuring retention rather than something that is simply always
there, and `D2b-cold` is no longer a dependency of `§G` — which matters, because
`G6` only exists if `G1` matches.
