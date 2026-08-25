# PREDICTIONS — Session B4, block 1 (`H1`, `probe1`)

**Written 2026-08-25 at the bench, after block 0 and before `H1a` sends its first
byte.** Block 0's nine captures are already on disk; nothing in `H1` has run.
`tools/check-predictions.py` checks that claim against this file's mtime and each
capture's `.log` mtime. **Not edited after the block has run** — a typo fix moves
the mtime and the check fails, correctly.

## What block 0 established, and why `H1` is allowed to run

Written here because `RUNSHEET.md` §H0 makes `H1` conditional on exactly one of
the seven reads, and the other six change what a silent board would *mean*.

| | measured, 2026-08-25 | consequence for `H1` |
|---|---|---|
| **`H0c` word 0** | `5A5AA5A5`, opcode `010110` = **22 = `BLEZL`** | 🔴 **the gate. Not `j` (2) and not `jal` (3)**, so `cache.S`'s no-demonstrated-brick-path argument holds *by measurement* rather than by assuming the pattern is there. **`probe1` may run** |
| `H0a` | 32/32 words identical to the block-0 prediction | the vector is at `0x80000080`. Does not gate `H1` — no `probe1` cell touches a vector — but it makes *board went silent* mean `do_reserved`, a bounded two-prints-and-hang, rather than *unexplained* |
| `H0b` | `[0]=80400580`, `[23]=804007C0`, **the other thirty `80400BE8`** | same: the hang is the print-and-hang, and it is where a fault lands |
| `H0d-a` | `55617135 00F73F55 11744D3C E1553515` — **not** `DEADC0DE`, **not** `524C5831` | the block about to be read back is this seating's or it is nothing. This is the before-picture |

**`H0d-a` is also the reason one sentence in this file is a prediction and not a
description**: the same address read on 2026-08-24 (`G4-addr-probe`) gave
`55617135 0077BF55 11744D3C E1553515` — three of four words identical across a
power cycle and **word 1 differing in two bits**. Cold SDRAM here is strongly
biased and **not** deterministic, so *the region looks like noise* is not an
authentication. The magic word, the nonce and the seal are.

## The build, identified before it is uploaded

```
sha256      fbac7d60319aacf9e86a4a673f899eaf41d3659ad9d55417da4c4c70c6d289f6
size        19792 bytes        load 0x80500000       first word 3c1d8051
nonce       9d34f1c7           RESULT_BASE 0x80A00000    RB_WORDS 137
GEOM=0 (not armed)             RESET=1                   victims 0x80500c00..0x80504c00
hazlint     0 violations in 81 loads; gate-check refused a planted hazard, exit 1
stale-build lui 0x80a0 ×1, 0xa0a0 ×2, and `0x80a1|0xa0a1` **0 times**
```

Built into an emptied directory. `make show` did not print
`*** NOT A DEVICE BUILD ***` and did not print `Nothing to be done`.

---

## Cells, in order

```cells
bench/2026-08-25/H1a-ab
bench/2026-08-25/H1b
bench/2026-08-25/flush-h1b
bench/2026-08-25/H1c
```

`H1a`'s two non-capture steps — `console-dump.py rescue` and `loader-tftp.py put`
— write JSON, not `.log`, so they are not in the list above. They are
`bench/2026-08-25/H1-rescue.json` and `bench/2026-08-25/H1a-put.json`.
**`H1d` is deliberately absent**: it runs only if `H1b` and `H1c` disagree, and a
predicted cell that does not run is a failure, correctly.

---

### `H1a` step 1 — `rescue`

```
/usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 \
    --port /dev/ttyUSB0 --baud 38400 \
    --load-addr 0x80500000 -o bench/2026-08-25/H1-rescue.json
```

| | prediction |
|---|---|
| transcript, in this order | `AutoBurning=0` · `Set TFTP Load Addr 0x80500000` · `Now your Target IP is 10.1.1.1` |
| `load_addr` key | present, and equal to `0x80500000` — it is recorded only when `--load-addr` is given |

⚠️ **`--load-addr` is `int(s, 0)`, so `0x80500000` with the `0x`; `--expect-load`
below is `int(s, 16)`, so bare `80500000`.** Opposite conventions in the same
cell. 🔴 **And `0x80500000` and not `0x80A00000`**: `§G`'s `G2`/`G4` carry
`0x80A00000`, which is `probe1`'s own `RESULT_BASE`, and an image landing there
followed by `J 80500000` boots the staged vendor kernel — loader gone, one power
cycle, and `--expect-load` cannot catch it because `put` and `get` both serve
`[0x8040D3A8]`.

### `H1a` step 2 — the guard, and it is read before the upload

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H1a-ab --send 'DW 8040D4A0 1' --seconds 4
```

| | prediction |
|---|---|
| bytes | **71**, 1 line — `len(cmd) 13 + 2 + 47 + 9` |
| content | `8040D4A0:` then **`00000000`** in the first column |

🔴 **If the first word is not `00000000`, the seating stops here and nothing is
uploaded.** `AUTOBURN` is read at exactly one instruction, `0x80401B9C`, on the
upload-completion path, and this is the word that instruction will see *during*
the transfer. The loader's own `AutoBurning=0` echo is the loader saying what it
thinks; this is the switch.

### `H1a` step 3 — `put`

```
/usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 \
    --image tools/rlxprobe/build/probe1/probe1.bin \
    --rescue-report bench/2026-08-25/H1-rescue.json \
    --expect-load 80500000 --yes --report bench/2026-08-25/H1a-put.json
```

19,792 bytes. `--filename` is left at its default `image`; **never a name
containing `nfjrom` or `boot.img`**, which this loader executes with nobody at
the console.

---

### `H1b` — the run

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H1b --send 'J 80500000' --esc-after 60 --seconds 120
```

**The report, 1,543 bytes at 38400 8N1 = 0.4018 s**, composed as
`32 banner + 144 six field()s + 13 × 104 rows + 15 end`:

```
*** rlxprobe P1 9d34f1c7 ***
rlxprobe: pc=805xxxxx
rlxprobe: rb=80a00000
rlxprobe: vic=80500c00
rlxprobe: flags=00000001
rlxprobe: t=43010000 v=80500c00 pr=… ex=… mb=… ma=… g=… vd=…      ← 13 of these
rlxprobe: seq=0000000d
rlxprobe: sum=xxxxxxxx
rlxprobe: end
```

⚠️ **The payload prints hex in LOWER case; the loader prints UPPER.** So `rb=80a00000`,
and `pc=` must begin **`805`**. **If `pc=` begins `a05`, the operator typed
`J A0500000`** and every cache cell is vacuous. **Grepping this capture for
`80A00000` returns nothing on a correct run.**

**The thirteen rows, in the order `CELLS[]` runs them — risk order, not numeric
order.** `tag = 'C' | cell<<16 | member`; `vaddr = 0x80500C00 + slot × 0x400`,
member 1 being seven slots (**7 KiB**) further on, which is why eviction has to
explain both members of a pair or neither:

| row | `t=` | cell | treatment | `v=` |
|---:|---|---|---|---|
| 0 | `43010000` | **1** | none, stored **cached** | `80500c00` |
| 1 | `43010001` | **1** | none, stored cached | `80502c00` |
| 2 | `43050000` | **5** | none, stored **uncached** | `80501000` |
| 3 | `43050001` | **5** | none, stored uncached | `80503000` |
| 4 | `43040000` | 4 | `Status.IsC` path | `80501400` |
| 5 | `43040001` | 4 | `Status.IsC` path | `80503400` |
| 6 | `43020000` | 2 | `CCTL 0x002` alone | `80501800` |
| 7 | `43020001` | 2 | `CCTL 0x002` alone | `80503800` |
| 8 | `43030000` | 3 | `CCTL 0x200` then `0x002` | `80501c00` |
| 9 | `43030001` | 3 | `CCTL 0x200` then `0x002` | `80503c00` |
| 10 | `43060000` | 6 | `CCTL 0x002`, stored uncached | `80502000` |
| 11 | `43060001` | 6 | `CCTL 0x002`, stored uncached | `80504000` |
| 12 | `58435430` | — | `'XCT0'`, the first read anyone has taken of CP0 register 20 | `00000000` |

Constants: `mb`/`ex` old = **`240211a1`**, new = **`240222b2`** (lower case on
this channel).

`vd` ladder: `01` STALE · `02` FRESH · `03` NOSTORE · `04` VOIDPRIME ·
`05` NOTVICTIM · `06` WEIRD · `07` CORRUPT.

#### 🔴 The refutation condition, and it is on cell 1 — rows 0 and 1

Cell 1 stores through the cached window and applies **no treatment at all**. It
must read **`vd=00000001` STALE**. If either member reads `02` FRESH, then either
this core has no I-cache, or the line was evicted between the two calls, or the
caches are coherent — **and under any of the three the other five cells passed
without being tested. The gate does not close; it closes on *cell 1 did not hold*
and a redesign.** `04`, `05` and `06` on cell 1 void the table exactly as `02`
does: they are the harness reporting that it is itself wrong.

**`03` NOSTORE on cell 1 is not a pass either**, and it is not a failure. It is
the write-back case, and the next table is how it is read.

#### 🆕 Cell 1 against cell 5 on the `ma` column — the write-back discriminator

Cited from `RUNSHEET.md` §H1, which wrote it before this seating. The two cells
differ in **exactly one variable** — cell 1 stores through the cached window,
cell 5 through KSEG1 — and both apply `T_NONE`, so `ma` (`mem_after`, an
**uncached** read-back) partitions cleanly:

| cell 1 `ma` (rows 0,1) | cell 5 `ma` (rows 2,3) | reading |
|---|---|---|
| `240222b2` | `240222b2` | **D-cache is write-through** (or does not allocate on write). Both cells report `01` STALE and the only stale thing is the I-cache. This is the case the verdict names were written for |
| `240211a1` | `240222b2` | 🔴 **D-cache is write-back.** Cell 1's cached store is still sitting dirty. Cell 1 reports `03` NOSTORE **and that verdict name must not be read as "the store did not happen"** — it did |
| `240211a1` | `240211a1` | the store did not happen at all. Instrument failure, not a cache finding — check `mb` and `05` NOTVICTIM before reading anything else |
| `240222b2` | `240211a1` | **impossible under any cache model.** It refutes the KSEG1-alias assumption the whole payload rests on, and it is worth more than the cell it broke |

**否證 of the table itself** — if cell 1 and cell 5 disagree on `ex` (executed)
rather than on `ma`, this table does not apply: that reading is about the
I-cache, not the D-cache.

🔴 **The consequence, written before the run because it is the one that reaches a
driver.** Four of the six cells store through the cached window — 1, 4, 2, 3 — so
in the write-back case **all four inherit it**. Cell 2 (`CCTL 0x002` alone) then
reads `03` NOSTORE while cell 3 (`0x200` then `0x002`) reads `02` FRESH, and the
natural reading — *"invalidating I alone is insufficient on this core"* — **is
wrong**. `0x002` alone is sufficient; what `0x200` added was getting the store out
of the D-cache. That sentence would go into `notes/cache-model.md` and then into
`R5b`'s MTD driver as the flush recipe. **In the write-back case the flush answer
comes from `5 → 6`, not from `2 → 3`** — those are the two cells that store
uncached and are therefore not contaminated.

#### Expected on the device, and it is the opposite of qemu

qemu came back **FRESH** on cells 1 and 5, because TCG invalidates a translation
block when a store lands on translated code. **A device run that looks like the
qemu run is the run that refutes the experiment, not the one that confirms it.**

#### Cell 4 runs third, knowingly

`CELLS[]` runs cell 4 — the `Status.IsC` path, the only cell with a demonstrated
kill under qemu — ahead of cells 2, 3 and 6. Carried, not fixed: the kill's
mechanism is now the `V_CORRUPT` guard; rows 0–3 (**the negative control and the
write-back discriminator**) are banked before it runs; and `rlx_isc_inv` is
entered with `$a0` = the victim address, so a fault there **prints**.
**If `H1b` stops after row 3, that is this defect**, and `H1c` still recovers
rows 0–3.

#### The reset, and the free `CLK-03` discriminator in `.timing`

`rlx_reset` drains the UART on `TEMT`, counts 16,777,216 iterations of a
three-instruction loop, then writes `WDTCNR = 0`. `--esc-after 60` streams ESC
across it — **ten times the 6.02 s budget**, and `--seconds 120` doubles as the
sixty-second silence observation the fault box requires.

```
Δ = t(first byte after the reset) − t(last byte of `rlxprobe: end`)
  = delay loop + [4.5, 4.6] ms
```

**Predicted, before the run:** **130.4 ms** if (400 MHz **and** 3 cycles per
iteration) · **172.3 ms** at 4 cycles · **256.2 ms** at 200 MHz. `CLK-15` got a
3.5 % 全距 over n=9 through this same `.timing` mechanism, so those are separated
by far more than the instrument's spread. ⚠️ **This measures `f/CPI`, not `f`** —
400 MHz with 6 cycles per iteration is indistinguishable from 200 MHz with 3 — so
a reading near 256 ms refutes the **combination** (the banner's 400 MHz **and** a
filled-delay-slot three-cycle loop), which is still a result. `CLK-03` has had no
experiment assigned to it; this is one, and it costs nothing.

🆕 **A second free reading in the same capture.** The post-reset boot text is a
**warm** reset with the capture already running, so its byte 0 → `Booting...`
interval is the counterpart of the 0.349 s measured on this morning's cold
power-on. Block 0 measured the cold case at n=2 (0.340 / 0.349 s) and the warm
captures of 2026-08-24 show no such gap at all. **Predicted: no ~345 ms gap
before `Booting...` here**, and `Booting → banner` in **0.577–0.590 s**.

### `flush-h1b`

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/flush-h1b --send '' --seconds 2
```

| | prediction |
|---|---|
| bytes | a **bare prompt, 11 bytes**, no `Unknown command !` |

That is `terminate_esc_line`'s own CR having gone out. ≈31 bytes with
`Unknown command !` means it did not, and the next command line would have been
appended to the residue (`LDR-16`).

### `H1c` — the same block from RAM

```
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 \
    --out bench/2026-08-25/H1c --send 'DW 80A00000 137' --seconds 8
```

| | prediction |
|---|---|
| bytes | **1671**, **35 lines** — `len(cmd) 15 + 2 + 47 × 35 + 9`. `DW` rounds **up**, so 137 prints **140** words |
| word 0 | `524C5831` (`'RLX1'`) |
| word 1 | `9D34F1C7` — the nonce |
| word 2 | `00010001` |
| word 3 | `pc`, agreeing with `H1b`'s `pc=` |
| word 4 | `0000000D` — `seq`, 13 rows completed |
| word 5 | `00000010` — `RB_ROWS` = 16 |
| word 6 | `00000001` — flags, KSEG0 |
| word 7 | `80500C00` — `victims` |
| words 8–111 | the thirteen rows, eight words each, **the same values `H1b` printed** |
| **words 112–135** | 🆕 **`DEADC0DE`, and they are correct** — `RB_ROWS` is 16, only 13 are used |
| word 136 | the seal, agreeing with `H1b`'s `sum=` |
| words 137–139 | `DEADC0DE` — the round-up |

🔴 **137, not 88.** `88` returns the header and ten rows, dropping cell 6's two
victims, the `XCT0` row, and **the seal — the only word that separates a completed
run from a truncated one.** ⚠️ **Upper case here, lower case in `H1b`. Two
channels, two cases, one word**, and comparing them by eye is the whole point.

**Refutes**: that the UART report and the RAM block agree. Two channels, because
`P9-12` lost its nonce to a 16-byte FIFO. **A reader who takes `DEADC0DE` where a
row should be as a truncated run will abort `H1` for nothing.**

---

## What block 1 cannot tell you

- **It measures which flush works on this die.** Not why, and it licenses no
  statement about the Lexra family.
- **`CPU-25` is not measured.** `GEOM=0`, so the cache-sizing walk does not run;
  size, line size and associativity stay blank. That is a choice: `GEOM=1` writes
  1 MiB of real memory at `0x80B00000` if this core does not implement
  `Status.IsC`, and this seating has no before/after read of that window.
- **No hazard and no time is measured by the payload itself.** Both need `R1b`'s
  controlled-loop harness. The `Δ` above comes from the capture's timestamps, not
  from the payload.
- **`Status.BEV`, `PRId` and `F50b` are not answered.** They live in `H2`, which
  is `R1g-4b`. **`R1-gate` does not close on this seating** — `R1d` can, `R1e`
  cannot. **Do not write `RLX5281`.**
- **Whether the loader's `J` flushes the caches is not established.** Only the
  `J BFC00000` special case has been disassembled.
