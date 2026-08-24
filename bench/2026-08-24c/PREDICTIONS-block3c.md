# PREDICTIONS — block 3c: a second `OVSEL` point, to name the 2 % residual

**Written before `D4c`.** Same power cycle. One warm reset, self-recovering; no
power cycle and no operator action.

## Why a second point

`D4` measured the `OVSEL[3:0] = 1001` timeout as **1.145 s, +0 / −0.020** — the
uncertainty is the ESC echo cadence, which is the heartbeat the measurement uses:
the loader echoes each ESC the tool streams, one per ~20 ms, and the echoes stop
the instant the board dies. Last echo at t=1.159, command executed by t=0.014.

| candidate | computed | measured |
|---|---|---|
| divided clock, `2^24 × 14 / 200.0049 MHz` | **1174.4 ms** | 1145 ms |
| raw clock, `2^24 / 200.0049 MHz` | 83.9 ms | — |

**The selection is not in doubt** — the two candidates are 14× apart and the
reading sits within 2.5 % of one of them. What is in doubt is the residual: the
measurement is **29 ms short**, consistently signed, and the base clock is known
to ±7 ppm so it cannot be the clock.

**One point cannot tell a scale error from a fixed lag.** Two can:

| if `D4c` at `OVSEL = 1000` reads | then |
|---|---|
| ≈ **573 ms** (same 2.5 % short) | a **scale** error — the effective divisor is ~14.36 rather than 14, or the count is `2^n × k` with `k` slightly under 14. `CDBR = 0x000E0000` was read as divisor 14 from one source; this would put that reading in question |
| ≈ **558 ms** (same 29 ms short) | a **fixed lag** — a constant offset between `EW` executing and the counter starting, or a compare at `2^n − k`. The timeout scales correctly and only the origin is displaced |
| ≈ **587 ms** (on the nose) | the residual is specific to `OVSEL = 1001` and neither explanation holds. Record and stop |

## The command

`OVSEL[3:0]` is split across two fields — `OVSEL[1:0]` at bits 22:21,
`OVSEL[3:2]` at bits 18:17. `D4`'s `0x240000` decodes as `[1:0] = 01 → 1<<21`
and `[3:2] = 10 → 2<<17`, i.e. `OVSEL = 1001 = 9`. `D1`'s `WDTCNR = 0` is
`OVSEL = 0000` and timed out in ~2.3 ms, so the mapping is `OVSEL = n → 2^(15+n)`
and `D4`'s 9 → `2^24`. **Both ends of that mapping are now measured**, which is
what licenses computing a third point rather than guessing it.

`OVSEL = 1000 = 8` → `[1:0] = 00 → 0`, `[3:2] = 10 → 2<<17 = 0x40000`.
`WDTE = 0x00` ≠ `0xA5` enables it. So: **`EW B800311C 40000`**.

```cells
bench/2026-08-24c/D4c
bench/2026-08-24c/flush-d4c
bench/2026-08-24c/D2g
```

| | command | prediction |
|---|---|---|
| **D4c** | `EW B800311C 40000` `--esc-after 20 --seconds 45` | the board resets on its own. `Reboot Result from Watchdog Timeout!` in the boot text for the **third** time. Interval command→last-echo per the table above; reset→first-byte ≈ **345 ms**, matching `D1` and `D4` |
| **flush-d4c** | `--send '' --seconds 2` | **11 bytes, bare prompt** — the **third** independent instance of `console-capture.py` 1.2's terminator working on the device |
| **D2g** | `DW 80A00000 1` | `5EA72D2B A5A5A5A5 13344D3C A1573115` — the canary across a **third** warm reset. Survived two |

**Refuted by**: the board not resetting at all (then `OVSEL = 1000` is not the
field decode above), or an interval outside 400–700 ms (then the
`OVSEL = n → 2^(15+n)` mapping that `D1` and `D4` bracket does not hold in the
middle, which would be a stranger result than either row of the table).
