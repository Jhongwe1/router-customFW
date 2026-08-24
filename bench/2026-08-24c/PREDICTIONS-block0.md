# PREDICTIONS — seating 2 part three, block 0

**Written before power was applied.** `tools/check-predictions.py` checks that
claim against this file's mtime and each capture's `.log` mtime. Nothing in this
file may be edited after the block has run — even a typo fix moves the mtime and
the check fails, correctly. Corrections go in a new file.

Power cycle: the **third** of seating 2 (part one `bench/2026-08-24/`, part two
`bench/2026-08-24b/`, this one). Instrument: `tools/console-capture.py` **1.2**
— every ESC loop now writes its own terminating CR, so **no `flush-` cell sits
inside this block**; `A0` is where that is tested on silicon.

Board state before this block: **unpowered since ~05:00**, ~3 h. `ethtool
enxfc19286184c9` read `Link detected: no` beforehand — two causes, board off or
cable out, and the block does not depend on which.

---

## What this block is for

Three of these nine cells did not exist this morning. They exist because the
board being **off** turns two things that were going to cost something into
things that cost nothing:

1. **Part two left 23 distinctive words in DRAM** — `C7A00001…C7A0000C` at
   `0x81000400` and `C7B00001…C7B0000B` at `0x81000440`, `bench/2026-08-24b/`
   `C7a.log`, `C7a-rb.log`, `C7b.log`, `C7b-rb.log`. Reading them cold is the
   refutation `D2b`/`D2c` need, against 23 words over hours instead of 2 words
   over minutes — and it removes their dependency on `§G`'s first power cycle,
   which **only exists if `G1` matches**.
2. **`D2c`'s expected value in `RUNSHEET.md` is stale and would have failed for
   the wrong reason.** It reads `5EA72D2B A5A5A5A5 11744D3C E1553515`, and words
   3–4 there come from `G4-addr-probe` — measured on the *previous* power cycle,
   i.e. that cycle's uninitialised DRAM. `G0-head` re-takes them on this one.

## Cells, in order

```cells
bench/2026-08-24c/A-catch
bench/2026-08-24c/A0
bench/2026-08-24c/X1
bench/2026-08-24c/X2
bench/2026-08-24c/X3
bench/2026-08-24c/B7-cold
bench/2026-08-24c/G0-head
bench/2026-08-24c/G0-mid
bench/2026-08-24c/G0-tail
```

Every command below is `/usr/bin/python3 tools/console-capture.py capture --port
/dev/ttyUSB0 --baud 38400 --out bench/2026-08-24c/<cell>` plus the arguments in
the row. **No line is 128 characters**; the longest is 14.

`DW` reply size is `len(cmd) + 2 + 47 × lines + 9` bytes, and that formula
predicted six reply sizes exactly in part two. It is checked here against three
independent part-two captures: `A0` 71, `E9b` 118, `C7a-rb` 213 — exact on all
three. So every byte count below is a prediction, not a description.

---

### A-catch — `--esc 45 --seconds 65 --cr-settle 3`

The capture starts first; power is applied while ESC is streaming.

| | prediction |
|---|---|
| boot text | the **first 181 bytes** byte-identical to `bench/2026-08-24b/A-catch.log` — `\r\nBooting...\r\n\x00chipName: UNKNOWN\n\rramSize: 32M\n\r \n\r---RealTek(RTL8196E)…\n\r---Ethernet init Okay!\n\r<RealTek>`. Part two's was byte-identical to part one's; this would be a third |
| after the prompt | *n* × (128 ESC → `\n\rUnknown command !\r\n\r<RealTek>`). *n* is **not** predicted — it depends on when power is applied |
| **the last bytes** | 🔴 **a prompt, not a run of ESC.** With residue `r > 0`: `Unknown command !` then `<RealTek>`. With `r == 0` (~1 in 128): a **bare prompt, no `Unknown command !`** — `flush-cont.log`'s shape |
| metadata | `tool_version: "1.2"`, `cr.esc.written: true`, `cr.esc.log_offset` set, `cr.esc.prompt_seen: true`, `cr.esc.waited_s` well under 3 |

**Refutes**: that 1.2's terminator fires on the device at all. If the log ends on
ESC, or `cr.esc` is `{}` or absent, the tool did not do what its 25-case suite
says it does, **and every `flush-` cell goes back into the sheet before `§D`**.

### A0 — `--send 'DW 8040DBC0 1' --seconds 4`

| | prediction |
|---|---|
| bytes | **71**, byte-identical to `bench/2026-08-24b/A0.log` |
| content | `8040DBC0:\t8040B070\t00000000\t80409A9C\t8040B074` then `<RealTek>` |

**Two jobs.** Rule 1: first cell of any seating, one command with a precomputed
answer, and it re-establishes that re-opening the port did not reset the board
(`BRD-09`). And 🔴 **it is 1.2's positive control on silicon, with the failure
already measured**: in part two, `A0`'s first attempt came back
`Unknown command !` because `A-catch` left 12 ESC bytes in `readline`. **Any
`Unknown command !` in this capture refutes the auto-CR**, and the fallback is a
`flush` cell in front of every command in this block.

### X1 — `--send 'DW 81000400 16' --seconds 5` · X2 — `--send 'DW 81000440 16' --seconds 5`

| | prediction |
|---|---|
| bytes | **213** each |
| X1 most likely | the 32-byte-period descriptor pattern rebuilt: `00000400 00000001 FFFFFFFF 00000000` / `00000000 00000000 81000418 81000418` / same at `+0x20` with `81000438` |
| X2 most likely | the same period continuing, self-pointers `81000458` / `81000478` |
| **required of both** | 🔴 **not `C7A0000n`, not `C7B0000n`** |

**Refutes** — and this is the point of the pair:

- any `C7A`/`C7B` word still present ⇒ DRAM contents survive a multi-hour power
  cycle ⇒ **`D2b` and `D2c` are void before they are typed**, the same way `E5`
  was void when its "before" state was already its "after".
- the descriptor pattern present ⇒ **the structure is built during boot**, which
  dates `C-17` and which `C7-pre` could not do. `C7a` overwrote descriptor 0
  *including its `list_head` at `0x81000418`* and part two ran on regardless, so
  "rebuilt" here is a real reconstruction and not a survivor.
- neither pattern — garbage — ⇒ DRAM did not survive **and** nothing rebuilt the
  table by prompt time. Then `X3`'s reading is the one `D0a-restore` uses and
  `D2b`'s three-outcome table needs a fourth row.

### X3 — `--send 'DW 81000000 1' --seconds 4`

| | prediction |
|---|---|
| bytes | **71** |
| content | `81000000:\t00000400\t00000001\tFFFFFFFF\t00000000` |

Derived, not recalled: part one's `C3b` read `0x81000100` as
`00000400 11111111 FFFFFFFF 00000000` with word 2 carrying `C3a`'s write, so the
untouched record is `00000400 00000001 FFFFFFFF 00000000`.

🔴 **This is the value `D0a-restore` will write back, and reading it here is what
makes that a restore instead of a recital.** `D0a` overwrites words 1–2 of this
record with `DEADBEEF CAFEBABE`, and `§G` then runs a 987,138-byte TFTP transfer
which — *推*, `C-17` — may use this region as its buffer pool.

### B7-cold — `--send 'DW B8003110 1' --seconds 4`

| | prediction |
|---|---|
| bytes | **71** |
| content | `B8003110:\tC0000000\t80000000\t000E0000\tA5000000` — exact, all four words, from `B7` |

`D2`'s power-on baseline, taken on **this** power cycle rather than carried from
part one. Word 4 bit 20 (`WatchDogIND`) = 0 after a power-on reset; `WDTE[7:0]`
= `0xA5` = the stop pattern, so the watchdog is stopped. `D2` reads this same
word after a warm reset and asks whether bit 20 moved.

**Refuted by**: any difference from `B7`. `WDTCNR` has no writer in this loader
outside two `sw zero`-then-spin sites, so a different value here means the
premise that `A5000000` is the hardware reset default is wrong.

### G0-head / G0-mid / G0-tail — `--send 'DW 80A00000 16' | 'DW 80A78000 16' | 'DW 80AF1000 16' --seconds 5`

| | prediction |
|---|---|
| bytes | **213** each |
| values | 🔴 **not predicted, deliberately.** `G4-addr-probe` read the head as `55617135 0077BF55 11744D3C E1553515 / 75576793 732111E3 1D187415 0501F751` **on the previous power cycle**, and that is uninitialised DRAM — there is no reason for it to repeat |
| **required of all three** | no pointer-shaped word (nothing in `0x80000000`–`0x81FFFFFF`), no word equal to its own address or a neighbouring one, no repeating period |

**Refutes**: the choice of `0x80A00000` as `§G`'s upload address. `G0` exists
because `0x81000000` was chosen by an argument (*"far above the loader's image"*)
and `C7-pre` then measured a live structure there. **Any pointer-shaped word in
any of the three and the address is re-chosen.** Three 64-byte windows across
964 KiB is still three windows — stated so the write-up cannot claim more.

Free and unasked, at zero cost: **if `G0-head`'s first eight words come back
byte-identical to `G4-addr-probe`'s across a power cycle**, this device's SDRAM
power-on state is deterministic at that address. Nothing predicts that and
nothing turns on it; it is one `cmp`.

`G0-head` also supplies **`D2c`'s words 3–4**, which is what makes `D2c`'s tail a
control rather than a comparison against a dead power cycle.

---

## What this block does not do

- It does not touch `§F`. `F1` (`PHYR 5 2`) needs the operator's explicit yes.
- It writes **nothing**: nine `DW` reads and one ESC stream. No `EW`, no `EB`,
  no `J`, no flash.
- `G0`'s three windows do not speak for 964 KiB, and this block claims only what
  the three windows hold.
