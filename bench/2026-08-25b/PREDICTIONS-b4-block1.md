# PREDICTIONS — Session B4, `R1g-4b`, block 1: `H2`, the upload and the run

**Written at the bench, immediately before its own cells, and after block 0's
eight readings are on disk.** It is conditional on them — that is why it is not
in block 0. `tools/check-predictions.py` checks the ordering.

**Block 0 held on the readings this block depends on**, and each is named where
it is used below:

| | |
|---|---|
| `H0a` | byte-identical to `bench/2026-08-25/H0a.log`. Words 0–10 are the dispatcher, so `0x80000080` is populated and `probe2` may run |
| `H0b` | `exception_handlers[9] = 80400BE8`, 量 **on this boot**. A fault under `SAFE_A0` prints |
| `H0c` | word 0 `5A5AA5A5`, opcode 22 `BLEZL` — `cache.S`'s no-brick argument holds on this boot. Words 1–31 are this boot's bias and **differ from 2026-08-25 by 20 bits in the first seven words**, which is the whole reason the cell was re-taken |
| `H0d-b` | `55711135 …` — neither `DEADC0DE` nor `524C5832`. Nothing has ever written `0x80A01000` |

## Cells, in order

```cells
bench/2026-08-25b/H2a-ab
bench/2026-08-25b/H2a
```

`H2-rescue.json` and `H2a-put.json` are not `console-capture` captures and have
no `.log`, so they are not in the list — the transport's own transcripts, checked
by `--expect-load` and by `H2a-ab`'s word 1. `H2b`–`H2f` are **readings out of
`H2a`**, not separate captures.

---

## The upload

| # | cell | expected |
|---:|---|---|
| 1 | `H2-rescue` | in the transcript, in this order: `AutoBurning=0`, `Set TFTP Load Addr 0x80500000`, `Now your Target IP is 10.1.1.1`. A `load_addr` key in the JSON, because `--load-addr` was given |
| 2 | `H2a-ab` | **71 bytes**, `8040D4A0:` then word 1 = **`00000000`**. 🔴 **If it is not `00000000`, stop. Nothing is uploaded.** Read here and not after the `put`, because the word that matters is the one the burn path sees **during** the transfer |
| 3 | `H2a-put` | **9,392 bytes** accepted, `sha256 78beb72f77f601017f363d14de9467646f3ff9a4515e3673b64972b74c745261`. `--expect-load 80500000` satisfied against the transcript |

🔴 The image is **`tools/rlxprobe/build/probe2/probe2.bin`**. The sheet said
`build/p2a/probe2/probe2.bin` until tonight and that file **exists**, is
**6,656** bytes, `8a15b501c160dd59…`, and is the withdrawn pre-fix payload.

⚠️ `--load-addr` takes `0x80500000`; `--expect-load` takes `80500000`. Opposite
conventions, one minute apart.

---

## `H2a` — the run. Every field, and where each prediction comes from

Report structure: banner + 29 `field()`s + `rows.printed` census lines + `end`.
**Predicted length `2552 + 51 × (rows.printed − 32)` bytes**, plus **91** if the
`count.delta is NOT a tick count` line fires. Model 量 tonight against two
controls: it reproduces `probe1`'s measured **1,543** bytes
(`bench/2026-08-25/H1b.log`) and `probe2`'s qemu run at **5,875** exactly.
At `rows.printed = 39` and the verdict line firing: **3,000 bytes, 0.781 s**.

| field | prediction | where it comes from |
|---|---|---|
| banner | `*** rlxprobe P2 3ab0e572 ***` | `RLX_NONCE` |
| `pc=` | 🔴 **`80501054`**, exact | 量 tonight: `rlx_pc` returns `$ra`; the `jal` is at `0x8050104c`, its delay slot at `…50`, so `$ra` = `…54` |
| `rb=` | 🔴 **`80a01000`**, lower case | `report.c:18`'s digit table is `"0123456789abcdef"`. **`80A01000` upper case is a string a correct run never produces**, and `rb=80a00000` means the stale binary went up |
| `flags=` | **`50010002`** | `0x50` tag, `RESET`=1 in bit 16, `CCTL 0x002` in the low half, every qemu knob clear. Second stale-build leg, and it comes back over the wire |
| `status=` | **§H2b below** | |
| `vec=` | `80000080` | |
| `handler_words=` | **`00000016`** (22) | 量: `rlx_exc_end − rlx_exc_entry` = `0x58` |
| `install.changed=` | 🔴 **`0000002b`** (43), **exact** | 量 tonight from `H0a` and `H0c` — see below |
| `install.bad=` | **`00000000`** | Must-fix 2. Non-zero means the uncached stores did not land, and the payload refuses to `break` |
| `break.count=` | **`00000001`** | `break` traps on every MIPS ever built |
| `break.cause=` | **`00000024`**; only `cause & 0x7c == 0x24` is load-bearing | ExcCode 9 = `Bp`, in bits 6:2. Bits 15:8 are `IP[7:0]` and could carry a pending interrupt, so the full word is predicted weakly |
| `break.epc=` | 🔴 **`80500270`**, exact | 量 tonight: `break` (`0000000d`) is at `0x80500270` in `rlx_do_break`, not in a delay slot, so `BD`=0 and `EPC` is the instruction itself |
| the six counts | **sum to `00000100`** (256) | a partition; the payload's own arithmetic |
| `rows.printed=` | **`00000027`** (39) if `Random` alone moves; `0000002e` (46) if `Count` moves too; `00000020` (32) only if **nothing** moves | see §H2d |
| `count.*` | **§H2e below** | |
| `restore.mismatch=` | **`00000000`**, over all 64 words of both vectors | |
| `restore.stillhandler=` | **`00000000`** | of the positions the install demonstrably changed, none still holds our handler |
| `status_end=` | 🔴 **equal to `status`, except possibly bits 5:4** | derived, below |
| `sum=` | not predicted — it is the checksum of the data this cell is measuring | |

### `install.changed = 0000002b`, and it is arithmetic rather than a threshold

The sheet's expected value was *non-zero*, which nothing can fail. Tonight it is
a number, because `H0c` was taken at 32 words. The 22 emitted handler words are
量 from `build/probe2/probe2.elf` (`0x80500210`–`0x80500267`):

```
3C1A8050 275A25B0 3C1B2000 035BD025 401B6800 00000000 00000000 AF5B0004
401B7000 00000000 00000000 AF5B0008 8F5B0000 00000000 277B0001 AF5B0000
401A7000 00000000 00000000 275A0004 03400008 42000010
```

Compared position by position against tonight's own pre-install reads:

| vector | pre-install | positions differing | coincidences |
|---|---|---:|---|
| general `0x80000080` | `H0a` | **21** of 22 | index 10 — the handler's third `nop` on `H0a[10] = 00000000` |
| UTLB `0x80000000` | `H0c` | **22** of 22 | none; no bias word equals its handler word |

**21 + 22 = 43 = `0x0000002b`.**

✅ The model has a positive control that already fired: the qemu build is 25
handler words × 2 vectors = 50 positions with the vector page starting as zeros,
so it predicts `50 − 20` (ten `nop`s × two vectors) = **30**, and the qemu run
量 tonight reported `install.changed=0000001e` = **30**, exact.

**Refutation**: `0000002c` (44) would mean position 10 of the general vector was
not `00000000` when the install read it — i.e. something wrote the vector page
between `H0a` and the install. Anything below 43 means a store did not land, and
`install.bad` should then be non-zero; **43 with `install.bad != 0` is the
combination that says the read-back and the change count disagree**, and neither
number would then be usable.

---

## `H2b` — `status=`, and `CPU-27`

🔴 **The full word is not predicted, and that is deliberate.** A previous draft
carried `1000FC01` "traced through ten writes to Status"; that value existed in
exactly one place and was withdrawn. This block does not resurrect it.

R3000 `Status` layout, per field, with what this repository actually has:

| bits | field | prediction | mark |
|---|---|---|---|
| **22** | **`BEV`** | 🔴 **`0`** — and it is the only load-bearing bit | 讀, one source: `docs/loader-phy-and-switch.md` §2, set at `0x80406694`, called from `0x80408634`, on the boot path, never re-masked. **This cell is what makes it 量** |
| 15:10 | `IM[7:2]` | `1` (unmasked) → `0x0000FC00` | 讀, same source |
| 9:8 | `IM[1:0]` | `0`, software interrupts | 推 |
| 17, 16 | `SwC`, `IsC` | `0` | 推 — this payload contains no `mtc0` to CP0 12 (量, zero hits in the disassembly), and `probe1` cell 4's corruption was caused by a routine not linked here |
| 0 | `IEc` | **`0`** | 讀 — `J <addr>` clears `IE` and zeroes `GIMR0` on every path |
| 31:28 | `CU3..CU0` | **not predicted** | the withdrawn `1000FC01` is the only place `CU0=1` was ever written down |
| 19 | `CM` | not predicted | |

🔴 **If `BEV` reads 1**, the payload refuses to install, `progress` stops at
`00000010`, and `R1-gate`'s stop-loss applies: the census falls back to the
no-handler subset and `F50b` resolves against `Count`/`Compare`, i.e. **`R5-0`'s
timer driver becomes a prerequisite**. That is a decision, not a gap. The report
is then **242 bytes** and ends after `vec=`.

### `status_end` — a derived prediction, and it tests `rfe` rather than the payload

This payload writes `Status` nowhere. But the handler returns with `rfe`, and on
an R3000 an exception shifts the three-deep `(KU,IE)` stack left and `rfe` shifts
it right — **`rfe` copies `p→c` and `o→p` and leaves `o` alone**. So for a
starting `(o₀, p₀, c₀)`:

```
exception entry :  (o, p, c)  <-  (p0, c0, 00)
rfe             :  (o, p, c)  <-  (p0, p0, c0)
```

**`status_end` must equal `status` except in bits 5:4 (`KUo`, `IEo`), which after
the first exception equal `status`'s bits 3:2 (`KUp`, `IEp`), and it is stable
from then on.** If `status[5:4] == status[3:2]` — which it will be if all six
bits are 0 at the prompt — then **`status_end == status` exactly**.

🔴 **A difference anywhere else refutes the R3000 `rfe` model on this core**, and
that is worth more than the census. It costs nothing: both words are already in
the report and in block words 6 and 30.

---

## `H2c` — the `break` control

`count=00000001`, `cause & 0x7c = 0x24`, `epc=80500270`.

🔴 **The positive control on the handler**, and its failure is now decomposed
into two distinguishable observations rather than one hang:

| reading | what it says |
|---|---|
| `install.bad != 0` | the bytes are **not** at the vector. The uncached stores did not land. The payload refuses to `break` and copies the vectors back |
| `install.bad = 0` **and** `break.count = 0` | the bytes **are** there and the core did not fetch them — **the I-cache did not see them**. That refutes `CCTL 0x002` on a different address range and a different store path from `H1`'s, and it is the strongest single reading available tonight |
| silence | `rlx_do_break` now carries `SAFE_A0`, and `H0b` measured `exception_handlers[9] = 80400BE8` **on this boot**, so a fault prints `Undefined Exception happen.` twice and hangs. Do not touch the power for 60 s, then power-cycle and `DW 80A01000 817` |

---

## `H2d` — the census

### 🔴 Row `0x08` is the positive control this census could not otherwise have

`rlx_cp0_stubs + 8×12` = `0x80500330` = `mfc0 v0, c0_random` — 量 tonight from
the disassembly. **`Random` free-runs downward on an R3000**, and `CPU-08` holds
**32 TLB entries, 量 on this device**, so the TLB is real.

**Prediction: row `0x08` reads state `04` `S_MOVES`**, with `v1` and `v2` two
different small integers, neither equal to `C0DE0008` / `D1CE0008`.

**Why it matters more than any other row.** `F50b` is decided by *`Count` does
not move*. Without a register that **does** move on this silicon, that reading is
unfalsifiable — the mechanism could be broken and produce the same answer.
qemu's row `0x48` = `S_MOVES` is a control on **qemu**. Row `0x08` is the control
on **this die**, and it is free.

**Refutation**: if row `0x08` is not `04`, then either `Random` is not
free-running on this core, or the double-read mechanism does not work — and
**until that is separated, no `S_NOWRITE` or `S_ZERO` anywhere in the census
means anything.**

### The rows that are the point

| row | rd/sel | instruction (量) | prediction |
|---|---|---|---|
| `0x08` | 1/0 | `mfc0 v0,c0_random` | **`04` S_MOVES** — the control above |
| `0x48` | 9/0 | `mfc0 v0,$9` | `F50b`. An R3000-class CP0 has no `Count`; expect `00` `S_ZERO` or `03` `S_NOWRITE`. **`04` refutes the R3000 expectation with two reads and no arithmetic** |
| `0x60` | 12/0 | `mfc0 v0,c0_status` | `01` `S_VALUE`, and both reads must equal `status=` |
| `0x78` | 15/0 | `mfc0 v0,c0_prid` | 🔴 **`0000CD01`**, written before the run. `52481` = `0xCD01`, from this unit's own kernel printing a decimal. **A reading in the 5281 range is worth MORE than one in the 4181 range** — it refutes a Realtek datasheet and two public kernel trees at once. **Do not write `RLX5281` either way until `R1e` closes** |
| `0x80` | 16/0 | `mfc0 v0,$16` | `Config`. **`Config.M == 0` proves outright this is not a MIPS32 core.** If it is `S_ZERO` or `S_NOWRITE`, there is no `Config` and `CPU-25` cannot come from CP0 |
| `0x81` | 16/1 | `.word 0x40028001` | `Config1`. **If `Config.M == 1` and this answers, `IS/IL/IA` and `DS/DL/DA` close all three parts of `CPU-25` in one row** — the free route the `GEOM=1` decision named |
| `0xa0` | 20/0 | `mfc0 v0,$20` | Lexra's `CCTL`. `probe1`'s `XCT0` row read `00000000` and could not separate *implemented and reads zero* from *destination never written*. 🔴 **Under two primes it separates: `00` S_ZERO means it reads zero, `03` S_NOWRITE means `mfc0 $20` writes nothing.** The write side is already 量 — cells 2/3/6 prove `mtc0 $t,$20` has an effect — so this row decides whether `CCTL` is a write-only command register, and that sentence goes straight into `R5b`'s MTD driver |

### The counts, under three hypotheses about this core

`i = rd × 8 + sel`, 256 rows, and the six states partition them.

| | what it is | `rows.printed` | what it would mean |
|---|---|---|---|
| **H-ignore** | select is ignored — 8 identical answers per `rd`. What an R3000-class CP0 does | **32 + 7 × (registers in `S_MOVES`)** → `0x27` with `Random` alone | the expected case |
| **H-decode** | select is decoded, `sel != 0` mostly unimplemented | large, and the 96 cap bites with `rows.suppressed` beside it | this core is not R3000-class in its CP0 decode |
| **H-trap** | reading an unimplemented `rd` traps | `traps` non-zero, and `state` carries `ExcCode` in bits 12:8 | architecturally UNDEFINED is being implemented as a trap, which is a real finding |

🔴 **`rows.printed = 32` is NOT the select answer**, and the sheet said it was
until tonight. The predicate compares `(v1, v2, state)` against the register's
own `sel = 0` row, so **a register whose value changes between the two reads
cannot equal its own earlier row** and prints all eight of its selects even on a
core that ignores select entirely. **The select question is answered by WHICH
rows print, not by how many.**

### What the census cannot do, and the payload says so itself

`S_ZERO` does not distinguish *implemented and zero* from *not implemented and
the bus returned zero*. Nothing in this payload can, and it is reported as its
own state rather than folded into one that has an explanation.

---

## `H2e` — `count.*`, and it decides `F50b`

Read `count.before` / `count.after` **first**. Both destinations are primed, with
**different** values, because priming both with zero would have made the
instrument's failure wear the result's clothes.

| | `count.before` | `count.after` | `count.delta` | `count.row48` | verdict |
|---|---|---|---|---|---|
| **(A)** no `Count`, `mfc0` does not write `rt` | `c0de0009` | `d1ce0009` | 🔴 **`10f00000`** | `03` `S_NOWRITE` | the delta is arithmetic on primes. **`F50b` is answered by the row, not by the delta** |
| **(B)** no `Count`, `mfc0` writes 0 | `00000000` | `00000000` | `00000000` | `00` `S_ZERO` | the same conclusion by a different route |
| **(C)** `Count` runs | two real values | | large | `04` `S_MOVES` | the R3000 expectation is refuted |

🔴 **`0x10f00000`, and `exc.S:201` says `0x110f0000`.** 量 tonight:
`0xD1CE0009 − 0xC0DE0009 = 0x10F00000`; the comment has two digits transposed.
It is a comment, so the emitted binary is unaffected — **but it is the number a
reader would check the reading against**, and a correct `(A)` run would have been
called a mismatch. Fixed at the desk after the seating, not before, because the
`.bin` about to go up is the one whose `sha256` is recorded.

**Under (C), what magnitude?** The loop is three instructions × 100,000
iterations. `CLK-03` 量 2026-08-25: Δ = 123.7 ms for 16,777,216 iterations of the
same three-instruction shape, i.e. **7.37 ns per iteration** → the loop takes
**0.74 ms**. An R4000-class `Count` increments at half the pipeline clock, so at
400 MHz / 2 it would move by ≈**147,000** (`0x00023E00`), and at 200 MHz / 2 by
≈73,700. **A delta of a few hundred thousand is `Count`; `0x10f00000` is the
prime subtraction; `0` is no `Count`.**

**Two independent cross-checks, and neither existed before this build.**
`count.traps` brackets the call the way the census brackets its stubs — a trapped
`mfc0` leaves the destination alone and produces the same residue arithmetic.
And `count.row48` is the same register through the same instruction on a
different path.

⚠️ **The payload's own verdict line has a gap and it is named here rather than
patched at the bench.** It fires on `cnt_traps != 0 || row48 == S_TRAP ||
row48 == S_NOWRITE` — **it does not name `S_ZERO`**. Under **(B)** the delta is
`00000000`, which is the right answer, so the missing case costs nothing this
run; under a core that returns 0 for *some* reads it would. Recorded, not fixed.

**What `F50b` becomes:**

| | `R5-0`'s SoC timer driver | `R1c`'s timing |
|---|---|---|
| (A) or (B) | **a prerequisite**, not a bonus | loses its first route |
| (C) | a bonus | keeps it |

---

## `H2f` — the restore

`restore.mismatch = 00000000` over all 64 words of both vectors, read back
through KSEG1. `restore.stillhandler = 00000000`.

The `saved != entry` guard is what makes the second one a control rather than a
coincidence: **seven** of the device handler's 22 words are `nop`, and counting
every coincidental match returned 20 on a qemu run whose restore was perfect.
(The sheet said *ten of 22*; that is the qemu build's 25 words with 10 `nop`s.)

**Neither can tell you whether `saved_vec` itself is right.** `H2h` is what
covers that, and only on the UTLB half — see block 2.

---

## What this block does not do

- It writes **no flash**. `AUTOBURN` is read `00000000` at the burn path's own
  instruction, before the transfer, and `probe2.bin` carries none of `burn()`'s
  eight section signatures and is not 4 KiB-aligned.
- It does not measure `CPU-25` by a cache walk. `GEOM=0`: `rlx_r3k_size` needs
  isolation, `probe1` cell 4 measured that this core does not isolate, so the
  routine can only return `0` — which is its own *the core does not answer*
  value. Rows `0x80`/`0x81` are the free route and a `probe3` eviction walk is
  the real one.
- It does not measure a hazard or a time. Both need `R1b`'s harness.
- **The qemu run proves control flow and nothing else.** qemu interlocks the load
  delay slot and this core does not.
