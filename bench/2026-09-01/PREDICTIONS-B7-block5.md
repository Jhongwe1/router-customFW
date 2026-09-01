# `R4-1` — the scripted reset, predicted before power

**Frozen 2026-09-01, twenty-third segment, at the desk.** Nothing in this file
has been sent to the device.

🔴 **The directory is named for the day this block was FROZEN, not for the day
the seating happens.** If the seating slips to another date the directory does
not move: `check-predictions.py` proves the ordering by mtime, and renaming or
re-touching a frozen block destroys the only evidence that the prediction came
first. Seating 8's card carried the opposite defect — a directory named for a
day the seating did not happen on — and this is the repair, stated once here
rather than remembered.

---

## 0. What this block is for, and the one risk in it

`R4` exists to make `edit → result` fast. `R4-0` measured the loop and found
that the machine pipeline is 50–71 s while the loop as served is about 17×
that, and the largest single thing standing between them is **a human being
physically present to power-cycle the board**. This block tests the command
that would remove that.

🔴 **The risk, stated first.** `J BFC00000` is read as writing `WDTCNR = 0` and
then spinning at `0x804092EC` with interrupts masked. If that reading is wrong
— if the watchdog does not bite — **the board is in an infinite loop that only
the power switch leaves**. The cost is one power cycle. It is not a brick risk:
no flash write is issued by this block, `AUTOBURN` is read before anything, and
`J BFC00000` touches one register and no flash.

**Because of that, `Y-j1` is placed early**: if it wedges, the seating loses a
power cycle and not a seating.

## 1. What this block inherits, with its marks

| | source | mark |
|---|---|---|
| `J BFC00000` is special-cased at `0x804092D4`: `lui v0,0xbfc0` / `bne` / `ori v0,v0,0x311c` / `sw zero,0(v0)` / `j 0x804092ec` | `docs/loader-command-semantics.md` §7, four sources | 讀 |
| `WDTCNR` is at `0xB800311C`; `WDTE[7:0]` at 31:24, `0xA5` = stopped; `OVSEL[3:0]` `0000` = the shortest of ten timeouts | D §8.2.9 Table 27, E, B, A | 讀 ×4 |
| `WDTCNR` reads `0xA5000000` at the prompt after a power-up | `SPEC.md` `B7` | 量 |
| the loader never writes `WDTCNR` anywhere else | `SPEC.md` `CLK-11` | 讀 |
| `WatchDogIND` is bit 20: `0` after a power-on or pin reset, `1` after a watchdog reset, write 1 to clear | D §8.2.9 Table 27 | 讀 |
| after a watchdog reset the loader prints `Reboot Result from Watchdog Timeout!` where a cold boot prints a single space, immediately after `ramSize: 32M` | `SPEC.md` `C-8`, three instances | 量 |
| the timeout at `OVSEL=1001` is 1118.133 ms and at `OVSEL=1000` is 557.583 ms, ratio 2.0053 | `SPEC.md` `CLK-08` | 量 |
| therefore `OVSEL=0000`, which `WDTCNR = 0` selects, is 1118.133 ÷ 2⁹ = **2.184 ms** | halving | 推 |
| the board reaches a typeable `<RealTek>` in 2.176–2.636 s from the line coming up, n=14 | `SPEC.md` `CLK-18` | 量 |
| after a reset the loader re-stages `0x80500000` from flash, so a missed ESC window boots the **vendor** firmware | seating 8 reel segment 7 | 量 |

⚠️ **One residual travels with the first row and is not resolved here**:
whether *every* path reaching `0x804092E8` passes through the two
`sw zero,0(0xB8003000)` sites at `0x804086E4` and `0x80408700` that mask
interrupts is **untraced**. It does not change any prediction below — the spin
is left by the watchdog either way — but it is the reason "interrupts are off"
is not asserted anywhere in this block.

## 2. The cells

`<n>` is the capture's own name. Every capture carries a terminator.

| cell | sent | predicted | what refutes it |
|---|---|---|---|
| **`Y-A`** | — (power applied with the capture already open, ESC heartbeat) | boot text, and **a single space** after `ramSize: 32M`; `<RealTek>` within 2.176–2.636 s of the first byte | the discriminator string present on a **cold** boot → `C-8` does not discriminate and every cell below is uninterpretable. **This is the negative control for `Y-j1`** |
| **`Y-ab`** | `DW 8040D4A0 1` | `00000000` | anything else → `AUTOBURN` is armed; **stop the seating** |
| **`Y-wd0`** | `DW B800311C 1` | `A5000000` — the stop pattern, `WatchDogIND` **clear** | bit 20 already set after a power-up → the bit is not a post-reset indicator on this part, and `Y-wd1` proves nothing. **This is the negative control for `Y-wd1`** |
| **`Y-j1`** | `J BFC00000`, ESC heartbeat running after the send | the echo, then the boot text, then **`Reboot Result from Watchdog Timeout!`** where `Y-A` printed a space, then `<RealTek>` | ① nothing at all and no prompt → the spin is not left; the board is wedged and needs the power switch. ② boot text **with a space** → something other than the watchdog reset the board. ③ boot text and no ESC window → the reset works and the recipe is unusable, which is a finding and not a failure |
| **`Y-wd1`** | `DW B800311C 1` | **`A5100000`** — the same stop pattern with bit 20 **set** | `A5000000` → `WatchDogIND` does not survive on this part; `C-8`'s string is then the only observable and this row is recorded 未定. Any other value → the loader writes `WDTCNR` on a path `CLK-11` did not find |
| **`Y-r02`…`Y-r20`** | `J BFC00000` ×19 | each: the discriminator string, then `<RealTek>` | any one that does not return to a prompt. **The count is the cell**, not any single reset |

### 2.1 The timing cell, and why it is separable even at 2 ms resolution

Read from `Y-j1.timing` against `Y-j1.log`: the gap between the **last byte of
the command echo** and the **first byte the board prints afterwards**.

* **predicted 推**: under **50 ms**. The watchdog is 2.184 ms and a warm reset's
  pre-`Booting` silence is 0.001–0.010 s (`CLK-15`'s warm group), so the sum is
  a few milliseconds.
* **refuted by**: a gap over **100 ms**. The rival model — `WDTCNR = 0` not
  selecting the shortest timeout — puts it at 1118 ms, which is **20× above the
  refutation threshold**, so the two are separable even though the console
  channel quantises at about 2 ms.
* 🟢 **A third outcome is a real answer**: if the gap is at the quantisation
  floor and cannot be resolved further, that is what an automated loop needs to
  know — the reset is fast enough that the loop need not wait for it.

## 3. `N = 20`, and what 20 can and cannot show

**N is 20 and it is written here before the seating.**

*Why not fewer*: the step list's own stated risk is a reset that works once and
wedges on the third, which is worse than one that never works, because the loop
will be trusted.

*Why not more*: each reset costs about 10 s of console (2.2–2.6 s to the prompt
plus the capture's own hold), so 20 is about 200 s of a seating.

🔴 **What 20 consecutive successes prove, stated so it cannot be overstated**:
with no failures in 20 trials the 95 % upper bound on the per-reset failure
probability is `1 − 0.05^(1/20)` = **13.9 %**. That is enough to refute a reset
that fails often. **It is not enough to call the loop reliable** — a rate low
enough to trust an unattended loop would need several hundred, which no seating
can hold. The number that matters comes from `R4-3`'s tool running for a while,
and this block does not pretend otherwise.

## 4. What refutes the block as a whole

> **否證** — the recipe is refuted by the **absence** of `C-8`'s discriminator.
> If the console prints a single space where `Reboot Result from Watchdog
> Timeout!` was predicted, the reset did not happen, and *the board came back*
> is not a substitute: the board comes back from a cold boot too, which is
> exactly what `Y-A` records.

> **And the reverse is a separate claim.** The discriminator appearing proves a
> watchdog reset occurred. It does **not** prove the ESC window is reachable
> afterwards; `Y-j1`'s third refutation direction is that cell, and a run that
> gets the string and no prompt has answered one question and failed the other.

## 5. Abort conditions

* `Y-ab` reads anything but `00000000` → **stop**, nothing else runs.
* `Y-wd0` reads anything but `A5000000` → `Y-wd1` is uninterpretable; run it
  anyway and record the pair, but the `WatchDogIND` row closes 未定.
* `Y-j1` returns nothing and no prompt within its capture → the board is
  wedged. **Power-cycle, and do not repeat `J BFC00000`.** Record the wedge; it
  refutes `LDR-33` and it is the most valuable outcome in this block.
* A missed ESC window boots the vendor firmware (about 2 minutes). Let it
  finish, then power-cycle; do not interrupt it.

## 6. Flash

**This block issues no flash write and runs no `FLR` bracket.** `J BFC00000`
touches `WDTCNR` and nothing else, `AUTOBURN` is read first, and every other
command here is a `DW`. If this block shares a seating with a payload of mine,
that seating's own `G8a`/`G8b` bracket covers the seating and this block adds
nothing to it and takes nothing from it.

```cells
bench/2026-09-01/Y-A
bench/2026-09-01/Y-ab
bench/2026-09-01/Y-wd0
bench/2026-09-01/Y-j1
bench/2026-09-01/Y-wd1
bench/2026-09-01/Y-r02
bench/2026-09-01/Y-r03
bench/2026-09-01/Y-r04
bench/2026-09-01/Y-r05
bench/2026-09-01/Y-r06
bench/2026-09-01/Y-r07
bench/2026-09-01/Y-r08
bench/2026-09-01/Y-r09
bench/2026-09-01/Y-r10
bench/2026-09-01/Y-r11
bench/2026-09-01/Y-r12
bench/2026-09-01/Y-r13
bench/2026-09-01/Y-r14
bench/2026-09-01/Y-r15
bench/2026-09-01/Y-r16
bench/2026-09-01/Y-r17
bench/2026-09-01/Y-r18
bench/2026-09-01/Y-r19
bench/2026-09-01/Y-r20
```
