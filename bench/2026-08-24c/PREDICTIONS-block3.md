# PREDICTIONS — block 3: `§D`, the two warm resets

**Written before `J BFC00000`.** Same power cycle as blocks 0–2, same instrument
(`console-capture.py` 1.2). `D1` and `D4` each reset the board; **neither is a
power cycle**, so this stays in `bench/2026-08-24c/`.

Armed and read back this session: `0x81000000` = `DEADBEEF CAFEBABE 34361357
AB2563FB`, `0x80A00000` = `5EA72D2B A5A5A5A5 13344D3C A1573115` (`D0-rb1`,
`D0-rb2`, both 71 bytes, both exact).

## Cells

```cells
bench/2026-08-24c/D1
bench/2026-08-24c/flush-d1
bench/2026-08-24c/D2
bench/2026-08-24c/D2b
bench/2026-08-24c/D2c
bench/2026-08-24c/D4
bench/2026-08-24c/flush-d3
bench/2026-08-24c/D2d
bench/2026-08-24c/D2e
```

`D1b` and `D4b` are not captures — they are `console-capture.py report`
invocations over `D1` and `D4`, and they appear in the results, not here.

---

### D1 — `--send 'J BFC00000' --esc-after 20 --seconds 45`

`J BFC00000` writes `WDTCNR = 0` at `0x804012F8` and spins with a `j` to itself
and a `nop` in the delay slot. **Only the watchdog can leave that loop.**
`WDTE[7:0] = 0x00` ≠ `0xA5` enables it; `OVSEL[3:0] = 0000` is the shortest of
ten timeouts.

| | prediction |
|---|---|
| structure | `J BFC00000\n\r---Jump to address=BFC00000`, a silence, then the stage-1 boot text |
| boot text | byte-identical to `A-catch`'s 181-byte region **without** its leading `0xFF` — that byte arrived 340 ms before `Booting...` on the cold boot and is *推* a power-on line-settle artefact, so a warm reset should not produce one. **If a `0xFF` appears here too, that inference is refuted** and the byte is something the board sends |
| tail | 🔴 the auto-CR: `Unknown command !` + `<RealTek>` (or a bare prompt if the residue lands on a 128 boundary) |
| metadata | `cr.esc_after.written: true`, `prompt_seen: true`, `log_offset` set |

**Acceptance is not "it reset" — it is "the ESC window appears again
afterwards".** A `J` that jumped and left the board silent and a `J` that never
jumped look identical for the first twenty seconds.

### flush-d1 — `--send '' --seconds 2`

🔴 **This is 1.2's control on silicon, and its expectation is inverted from what
`RUNSHEET` carried until today.**

| reading | verdict |
|---|---|
| **11 bytes, a bare prompt, no `Unknown command !`** | ✅ **pass.** `D1`'s own capture consumed its residue — the terminator went out and the loader acted on it. `flush-cont.log` is the 11-byte shape |
| 31 bytes, `Unknown command !` + `<RealTek>` | 🔴 **fail.** Residue was still in `readline`, i.e. 1.2 did not do on the device what its 25-case suite says it does. Every `flush-` cell goes back into the sheet and `D2` is re-read |

The tool's suite proves what was **written to the port**. Only this proves what
the **loader did with it**, and that is why the cell was kept instead of deleted.

### D1b — *(no capture)* `report D1 --from 'Jump to address=BFC00000' --to 'RealTek\(RTL8196E\)'`

**A wall-clock interval, order of a second. Value not predicted.**

🔴 **What this number is NOT: the watchdog timeout.** `OVSEL[3:0] = 0000` is
2^15 base-clock ticks, and against the measured **200.0049 MHz ± 7 ppm** that is
**163.8 µs** undivided or **2.29 ms** through `CDBR`'s divisor of 14 — both far
below this instrument's floor (the CP2102 latency timer, 1–16 ms typical,
unmeasured here). So the interval is the **post-reset boot time**, which is what
`C-8`'s owner actually needs: R4's `bench-ci` sets its timeout from it.

**Free cross-check available for the first time**: the cold boot measured
**power-applied → first byte ≈ 340 ms** (`A-catch.timing`, the `0xFF` at
t=18.984 and `\r\nBooting...` at t=19.324). `D1b` measures jump → banner on a
warm reset. The two are different quantities and should not match; a suspicious
agreement means one of them is not measuring what it says.

**Refuted by**: an interval over ~10 s (nothing in the model predicts that), or
the banner never arriving (then `D1` failed, not this cell).

### D2 — `DW B8003110 1`

**71 bytes.** Word 4 is `WDTCNR` at `0xB800311C`; the discriminator is **bit 20,
`WatchDogIND`**.

| word 4 | verdict |
|---|---|
| `A5100000` | 🔴 bit 20 latched. **`C-8` gets its discriminator**: "did the watchdog fire" is answerable from a status bit, with no canary needed |
| `A5000000` | 🔴 `WatchDogIND` does **not** survive the reset it reports. `C-8` loses that discriminator and falls back to `D2b`/`D2c` |

`B7-cold` measured `C0000000 80000000 000E0000 A5000000` on **this** power cycle,
so the power-on baseline is not carried from part one. **There is no software in
this path**: the loader never writes `WDTCNR` except at two `sw zero`-then-spin
sites, so this reads the hardware directly.

### D2b / D2c — `DW 81000000 1`, `DW 80A00000 1`

**71 bytes each.** Read as one result, four rows:

| `D2b` at `0x81000000` | `D2c` at `0x80A00000` | what it is |
|---|---|---|
| `DEADBEEF CAFEBABE 34361357 AB2563FB` | `5EA72D2B A5A5A5A5 13344D3C A1573115` | **DRAM survived the warm reset and nothing rewrote either address.** `C-8` gets a second discriminator that needs no status bit |
| `00000400 00000001 FFFFFFFF 00000000` | canary intact | 🔴 **the descriptor table appeared during the warm boot** — so something does build it, the trigger is on the warm path and not link-up, and `C-17` gets dated |
| `00000144 7BB04BB7 34361357 AB2563FB` — `X3`'s exact pre-write value | either | 🔴 **nothing predicts this.** DRAM re-acquiring its power-on bias with power never removed has no mechanism in any model here. Record and stop |
| anything else | not `5EA72D2B` | **DRAM did not survive a warm reset.** Neither cell discriminates and R4 needs a third observable |

Words 3–4 in each are the free control: `D0a`/`D0b` wrote **two** words, so if
words 3–4 have moved, something other than retention is in play.

### D4 — `--send 'EW B800311C 240000' --esc-after 20 --seconds 45`

**The cell that actually measures the watchdog**, by changing the experiment
rather than the instrument. `OVSEL[3:0] = 1001` — the **longest** of ten
timeouts, split across two fields: `OVSEL[1:0]` at bits 22:21 gives `1 << 21`,
`OVSEL[3:2]` at bits 18:17 gives `1 << 18`. `WDTE = 0x00` ≠ `0xA5` enables it;
bit 20 written `0` is a no-op on a write-1-to-clear bit.

**Marginal risk over `D1` is nil** — both end in a watchdog reset, which is the
point of both.

| `D4b − D1b` | verdict |
|---|---|
| **≈ 1.177 s** | the watchdog counts the **divided** clock (2^24 / (200.0049 MHz / 14)) |
| **≈ 84.1 ms** | it counts the **raw** clock (2^24 / 200.0049 MHz) |
| any other power of two | 🔴 the `OVSEL` field is packed differently than the datasheet's Table 27 was read — **which the measurement identifies rather than hides** |

The two candidates are **14× apart** and both are far above the timestamp floor,
where `D1`'s 163.8 µs and 2.29 ms were both far below it. `D1` is this cell's
control: `D1b` is boot + a timeout of ≈ 0, so `D4b − D1b` is the timeout alone
and the boot cancels. Fills `SPEC.md` `CLK-08`.

### flush-d3 — `--send '' —seconds 2`

**11 bytes, bare prompt**, as `flush-d1`. The name is the pre-flight audit's and
is kept so the requirement it came from stays traceable; what it now follows is
`D4`, since `D3` is retired. 🔴 **Two instances of the same control is the
point** — `flush-d1` follows `D1`'s `--esc-after 20` and this follows `D4`'s, so
the terminator gets two independent chances to fail to go out. One instance is
an anecdote.

### D2d / D2e — `DW B8003110 1`, `DW 81000000 1`, after `D4`'s reset

| | prediction | why |
|---|---|---|
| **D2d** | whatever `D2` read | 🔴 **`D2` measured `WatchDogIND` after a reset caused by `WDTCNR = 0`; this measures it after one caused by a real timeout.** Both are watchdog resets, so they should agree — and if they do not, "watchdog reset" is two different events and `C-8`'s discriminator only works for one of them |
| **D2e** | whatever `D2b` read | the canary across a **second** warm reset. If it survived one and not two, retention is time-dependent, not reset-dependent — and that changes what R4's `bench-ci` can rely on |
