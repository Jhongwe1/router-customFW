# PREDICTIONS — Session B4, block 10 (`H3c`, `CLK-08b`: is the watchdog's residual fixed or proportional?)

**Written 2026-08-25 at the bench, after `H3a` and before the first `EW`.**

## The question, and why the last attempt could not answer it

`D4`/`D4c` (2026-08-24) armed the watchdog by hand at two `OVSEL` settings and
measured **1122.5–1149.9 ms** (`OVSEL=1001`, `EW B800311C 240000`) and
**549.6–577.4 ms** (`OVSEL=1000`, `EW B800311C 40000`), against computed
**1174.376 ms** and **587.188 ms**. `CLK-08` closed on the divided/undivided
choice — the undivided candidate is 83.9 ms, 14× away — but **the shape of the
residual did not close**:

| model | predicts | prior estimator (`D4 − D1`, boot cancels) |
|---|---|---|
| **fixed lag** `L` | the two shortfalls are **equal**, ratio 1.00 | 37.2 ms and 24.9 ms |
| **proportional** | `D4`'s shortfall is **twice** `D4c`'s, ratio 2.00 | ratio **1.495** |

**1.495 sits exactly between the two models**, and the two hypotheses differ by
about 15 ms — **smaller than one tick of the 20.35 ms ESC heartbeat the previous
run was quantised to.** `CLK-16` measured that grid: requested 20.00, achieved
20.35/20.32; requested 2.00, achieved **2.32**.

**So the deciding experiment is a finer heartbeat, not a third `OVSEL` point.**
`RUNSHEET.md` `H3c` says so explicitly: *do not run a third point* —
`OVSEL=0111` predicts 286.2 ms proportional against 263.6 ms fixed, 22.6 ms
apart, which the old grid could not separate either.

```cells
bench/2026-08-25/H3c-D4
bench/2026-08-25/flush-h3c-D4
bench/2026-08-25/H3c-D4c
bench/2026-08-25/flush-h3c-D4c
```

### The two cells

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H3c-D4  --send 'EW B800311C 240000' \
    --esc-after 20 --seconds 45 --esc-period 0.002
… flush …
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H3c-D4c --send 'EW B800311C 40000' \
    --esc-after 20 --seconds 45 --esc-period 0.002
```

**Why `240000` and `40000`.** `OVSEL[3:0]` is split across two fields:
`OVSEL[1:0]` at bits 22:21, `OVSEL[3:2]` at bits 18:17. `1001` → `1<<21 | 1<<18`
= `0x240000`; `1000` → `1<<18` = `0x40000`. `WDTE` = `0x00`, which is ≠ `0xA5`
and therefore **enables** the watchdog. Both cells end in a watchdog reset, which
is the point of both, and the board hands its own prompt back.

| | prediction |
|---|---|
| `esc.esc_after.achieved_period_s` | **≈ 0.00232 s** in both `.meta.json` — `CLK-16`'s measured 2 ms grid, and it is what makes the rest of this block worth running. **A capture whose achieved period comes back near 0.020 measured nothing new** and must be re-run rather than interpreted |
| `H3c-D4` interval | **1122.5–1149.9 ms** (the prior window), now resolved to ±2.32 ms |
| `H3c-D4c` interval | **549.6–577.4 ms**, likewise |
| ratio of the two intervals | **2.000** — the ESC-echo counts gave exactly this last time (56 : 28) without a single timestamp, and it confirms the split-field `OVSEL` decode independently |
| both boots | `Reboot Result from Watchdog Timeout!`, `CLK-13`'s fifth and sixth instances, and **here it does discriminate**: the watchdog was armed by `EW` from the prompt and the loader executed nothing afterwards |
| `Booting → banner` | 🔄 **0.567–0.607 s**, and this is a corrected form. Twice today I wrote the observed sample range as if it were a bound (`0.577–0.590`, then `0.573–0.590`) and twice the next reading fell just outside it — 0.573, then 0.5714. **A sample range is not a tolerance.** `CLK-15` records the boot-to-boot spread as **3.5 %, unexplained**; ±3.5 % about the n=8 mean of 0.580 s is 0.567–0.601, and that is the interval a prediction is entitled to |

### 🔴 The reading, written before the run

Let `S₄ = 1174.376 − measured(D4)` and `S₄c = 587.188 − measured(D4c)`.

| `S₄ / S₄c` | reading |
|---|---|
| **≈ 1.0** | **fixed lag.** There is a constant `L` between arming and the counter starting, independent of the count — a property of the arming path, and it goes in the driver's timeout as an offset |
| **≈ 2.0** | **proportional.** The base clock the watchdog counts is ~2–3 % slower than `CLK-08b`'s 14.53–15.26 MHz, and the residual is a rate error rather than a lag |
| **anything else, with both shortfalls resolved to ±3 ms** | 🔴 **neither model, and that is the most valuable outcome** — it would mean the residual has a term nobody has proposed, and `SPEC.md` §17 gets a new blank instead of a filled row |

⚠️ **What this cannot settle.** The interval measured is *arming → first
post-reset console byte*, which is `timeout + reset→first-byte`. `CLK-14` puts
the second term at **2.07 ms** from one measurement, so it is inside the residual
being decomposed and is not separately resolved here. **If `S₄` and `S₄c` come
back equal at ≈2 ms, the residual is `CLK-14` and there is no lag at all** — an
outcome neither model named.
