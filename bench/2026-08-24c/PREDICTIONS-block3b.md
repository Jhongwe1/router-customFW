# PREDICTIONS — block 3b: what put `00000144` back at `0x81000000`

**Written before `D0a2`.** Same power cycle, same instrument. This block adds
three cells to block 3 and re-arms one word; `D4`, `flush-d3`, `D2d` and `D2e`
are block 3's and predicted there.

## The observation

| when | `0x81000000` |
|---|---|
| `X3`, cold boot, before any write | `00000144 7BB04BB7 34361357 AB2563FB` |
| `D0-rb1`, after `EW … DEADBEEF CAFEBABE` | `DEADBEEF CAFEBABE 34361357 AB2563FB` |
| `D2b`, after `D1`'s warm reset | **`00000144`** `CAFEBABE 34361357 AB2563FB` |

**Word 1 returned to the exact value it held before anything was written. Word 2,
four bytes away, kept `CAFEBABE`.** And `D2c` at `0x80A00000` kept **both** its
written words.

## Two hypotheses, and the earlier evidence now points at the second

**H-decay** — the warm reset re-initialises the DRAM controller, refresh pauses
for some milliseconds, and the weakest cells decay back to their power-on bias.
Word 1's cells decayed; word 2's did not. *Consistent with* the 89.5 %-stable
bias measured earlier.

**H-write** — 🔴 **something writes `0x00000144` to `0x81000000` on every boot**,
cold and warm, and DRAM retention is fine.

**The 1 KiB bias period discriminates them, and it was already measured before
either hypothesis existed.** `X3` against `X1` — `0x81000000` against
`0x81000400`, same capture pair, one row apart:

| offset | `0x81000000` | `0x81000400` | bits differing |
|---|---|---|---|
| `+00` | `00000144` | `57890336` | **13 / 32** |
| `+04` | `7BB04BB7` | `73F64BB7` | 4 / 32 |
| `+08` | `34361357` | `34361357` | **0 / 32** |
| `+0c` | `AB2563FB` | `BB0563F3` | 3 / 32 |

**Word 1 is the outlier, by a factor of three or more over every other word in
the window.** If `00000144` were this address's power-on bias, it should track
its 1 KiB neighbour like the other three do. It does not — it breaks the
periodicity that holds everywhere else. That is what `H-write` predicts and
`H-decay` does not, and it was in the data before the question was asked.

**`D2c` is the second strike against `H-decay`**: both canary words at
`0x80A00000` survived the same reset intact. A refresh pause that reached one
word at `0x81000000` and neither word 964 KiB away is a strange decay pattern.

## The experiment

Word 1 currently **already holds** `00000144`, so `D2e` alone cannot separate the
hypotheses — under both it reads `00000144` and means nothing. So word 1 is
re-armed first, with a **new** value, so that reading it back proves *this* write
arrived rather than that *some* write once did.

```cells
bench/2026-08-24c/D0a2
bench/2026-08-24c/D0a2-rb
bench/2026-08-24c/D2f
```

| | command | prediction | what it decides |
|---|---|---|---|
| **D0a2** | `EW 81000000 F00DFACE` — **one value, so one word** | silent, **31 bytes** (`len(cmd) + 11`; `C3a`, 20 chars, was 31) | word 2 stays `CAFEBABE` untouched and is the in-place control: a write that touched two words would show here |
| **D0a2-rb** | `DW 81000000 1` | **71 bytes**, `F00DFACE CAFEBABE 34361357 AB2563FB` | that `EW` with one value writes exactly one word. If word 2 moved, `EW`'s arity is not what part one's `C1`/`C3a` established |
| **D2f** | `DW 80A00000 1`, **after `D4`'s reset** | `5EA72D2B A5A5A5A5 13344D3C A1573115` | the canary at the second address across a **second** warm reset. Survived one; if it fails the second, retention is time-dependent rather than reset-dependent, and R4's `bench-ci` cannot lean on it |

**And then `D2e` (block 3) becomes the discriminator:**

| `D2e` word 1, after `D4`'s reset | verdict |
|---|---|
| **`00000144`** | 🔴 **`H-write` confirmed, twice reproduced.** Something writes `0x00000144` to `0x81000000` on every boot. `0x81000000` is then a **bad canary address** — it is written by the loader — and `D2b`'s whole design moves to `D2c`'s address. It also reopens `C-17`: part one's and part two's readings at this address were never uninitialised DRAM |
| **`F00DFACE`** | 🔴 **`H-write` refuted, `H-decay` stands.** DRAM retention across a warm reset is **word-granular and not uniform**, which is a stronger claim about this board than either cell set out to make, and it is a hazard for every future canary |
| anything else | record it and stop; do not reason forward |

**Either answer costs `D2b` its address.** Under `H-write` the address is
written by software; under `H-decay` it is unreliable by hardware. `D2c` at
`0x80A00000` is the discriminator that survives either way, and it has now
survived one warm reset intact.

## Free second job for `D4`, and it is about the line `D1` printed

`D1`'s warm boot printed **`Reboot Result from Watchdog Timeout!`** where the
cold boot printed a single space. So the loader reports the cause of reset in its
boot text — **`C-8`'s discriminator, with no register read at all** — and it read
`WatchDogIND` before `D2` could, which is why `D2` found bit 20 **clear**
(`A5000000`). *推*: the loader reads it and clears it, write-1-to-clear.

But `D1`'s reset was caused by the loader's **own** `J BFC00000` path, so a RAM
flag set before the spin would produce the same line — and DRAM survives a warm
reset, as `D2c` just showed. **`D4` separates them for free**: it arms the
watchdog with `EW` from the prompt, and the loader executes nothing afterwards.

| after `D4` | verdict |
|---|---|
| the line appears again | the loader reads a **hardware** bit. `C-8` closes on the boot text |
| the line is absent | the line is a **software** flag on `J BFC00000`'s path only, and it says nothing about a watchdog reset the loader did not initiate — which is exactly the case R4's `bench-ci` runs in |
