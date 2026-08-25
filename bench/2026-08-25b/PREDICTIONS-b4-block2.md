# PREDICTIONS — Session B4, `R1g-4b`, block 2: the block from RAM, and the warm reads

**Written at the bench, after `H2a`'s UART report and before any of the reads
below.** Conditional on `H2a`, which is why it is not block 1.

`H2a` ran to `rlxprobe: end`, the watchdog reset landed
(`Reboot Result from Watchdog Timeout!` in the same capture) and the loader is
back at the prompt. `RESET=1`, so `start.S` called `rlx_reset` the instant `main`
returned and **`trap_init` has already re-run**.

## Cells, in order

```cells
bench/2026-08-25b/flush-h2a
bench/2026-08-25b/H2g-hdr
bench/2026-08-25b/H2g
bench/2026-08-25b/H2h-gen
bench/2026-08-25b/H2h-utlb
bench/2026-08-25b/SPI-warm
```

**The block comes before the ride-along** — `H2g` is the only irreplaceable
reading of the six, so a console that dies mid-block costs `SPI-warm` and not the
census.

---

## `flush-h2a` — `--send '' --seconds 2`

**11 bytes, a bare prompt, no `Unknown command !`** — `flush-cont.log`'s shape.
That `console-capture`'s own ESC terminator went out. ≈31 bytes with
`Unknown command !` means it did not, and the next command line would be appended
to the residue (`LDR-16`).

---

## `H2g-hdr` — `DW 80A01000 40`, **495 bytes**

🔴 **All forty words are predicted exactly, from `H2a`'s own report.** This is the
two-channel check: the UART said these numbers once; the block has to say them
again through a completely different path — the loader's `DW`, reading DRAM the
payload wrote through KSEG1, after a watchdog reset.

| word | name | predicted |
|---:|---|---|
| 0 | `H_MAGIC` | `524C5832` |
| 1 | `H_NONCE` | `3AB0E572` |
| 2 | `H_PROGRESS` | **`00000090`** — `P_SEALED`. Anything less says where the run stopped |
| 3 | `H_PC` | `80501054` |
| 4 | `H_VERSION` | `00030001` |
| 5 | `H_FLAGS` | `50010002` |
| 6 | `H_STATUS` | `1000FC00` |
| 7 | `H_VEC` | `80000080` |
| 8 | `H_HWORDS` | `00000016` |
| 9 | `H_INS_CHANGED` | `0000002B` |
| 10 | `H_INS_BAD` | `00000000` |
| 11 | `H_INS_FIRSTBAD` | **`FFFFFFFF`** — never assigned, because nothing was bad |
| 12 | `H_BRK_COUNT` | `00000001` |
| 13 | `H_BRK_CAUSE` | `00000024` |
| 14 | `H_BRK_EPC` | `80500270` |
| 15 | `H_ROWS_DONE` | **`00000100`** — 256, all rows completed |
| 16 | `H_TRAPS` | `00000000` |
| 17 | `H_VALUES` | `00000028` |
| 18 | `H_ZEROS` | `000000D0` |
| 19 | `H_NOWRITE` | `00000000` |
| 20 | `H_MOVES` | `00000008` |
| 21 | `H_MIXED` | `00000000` |
| 22 | `H_CNT_SPINS` | `000186A0` |
| 23 | `H_CNT_BEFORE` | `00000000` |
| 24 | `H_CNT_AFTER` | `00000000` |
| 25 | `H_CNT_DELTA` | `00000000` |
| 26 | `H_CNT_TRAPS` | `00000000` |
| 27 | `H_CNT_ROW48` | `00000000` |
| 28 | `H_RES_MISMATCH` | `00000000` |
| 29 | `H_RES_STILLHDL` | `00000000` |
| 30 | `H_STATUS_END` | `1000FC00` |
| 31 | `H_ROWS_PRINTED` | `00000027` |
| 32–39 | `H_SAVED0..7` | 🔴 **`401B6800 00000000 00000000 3C1A8041 275AEB40 337B007C 035BD021 8F5A0000`** — the first eight words of the general vector **as `probe2` saved them**, which must equal `bench/2026-08-25b/H0a.log`'s first eight words, read 6 minutes earlier by the loader through a different command |

Words 32–39 are the strongest single line in this block: **the payload's own copy
of the vector, taken through KSEG1 by our code, against the loader's `DW` read of
the same address before the upload.** Two instruments, two moments, one answer.

⚠️ The loader prints **upper** case and the payload prints **lower**. `rb=80a01000`
on the wire is the same word as `80A01000` here.

---

## `H2g` — `DW 80A01000 817`, **9,661 bytes / 2.52 s**

🔴 **817 and not 809.** `RB_POISON_W = RB_WORDS + 8 = 817`; `LDR-07` rounds `809`
up to **812** printed words, which shows only three of the eight margin words.
`817` rounds to **820**.

| words | predicted |
|---|---|
| 0–39 | as `H2g-hdr` above |
| 40–807 | the 256 census rows, three words each: `v1 v2 state`. Row *i* is at word `40 + 3i` |
| **808** | `H_SUM` = **`EC84408D`** — `sum=ec84408d` on the wire |
| **809–816** | **`DEADC0DE` ×8** — the poison margin. Data here means the run wrote past its own block |
| **817–819** | 🔴 **NOT `DEADC0DE`** — DRAM the poison loop never reached. **This is the positive control on the poison**: without it, a loop that ran too far would look exactly like one that stopped correctly |

Spot checks inside the census region, from `H2a`'s printed rows:

| row | word index | `v1 v2 state` |
|---|---:|---|
| `0x08` `Random` | 64–66 | `00000A00 00001100 00000004` |
| `0x48` `Count` | 256–258 | `00000000 00000000 00000000` |
| `0x60` `Status` | 328–330 | `1000FC00 1000FC00 00000001` |
| `0x70` `EPC` | 376–378 | `80500270 80500270 00000001` |
| `0x78` `PRId` | 400–402 | `0000CD01 0000CD01 00000001` |
| `0xA0` `CCTL` | 520–522 | `00000000 00000000 00000000` |

---

## `H2h-gen` — `DW 80000080 32`, **401 bytes**

**Byte-identical to `bench/2026-08-25b/H0a.log`.**

⚠️ **What this can and cannot say, and the sheet's row overclaimed it.** The
watchdog reset re-ran `trap_init`, so this is a check on **the loader**, not on
`probe2`'s restore. It would come back correct even if `probe2` had left the
general vector full of handler words. `restore.mismatch` is the check on the
restore, and it reads the vector before the reset.

---

## `H2h-utlb` — `DW 80000000 32`, **401 bytes**

🔴 **Byte-identical to `bench/2026-08-25b/H0c.log` — tonight's, never
2026-08-25's.** This is the half that checks `probe2`, because **nothing on a
warm reset writes `0x80000000`**: the loader never populates the UTLB refill
vector, so what is there is what `probe2` put back.

Tonight's own measurement is why the baseline had to be re-taken: this boot's
`H0c` words 1–7 differ from 2026-08-25's by **20 of 224 bits**. Against the old
capture, a perfect restore would have shown of order sixteen differing bits and
the sheet calls a difference a failure — **a guaranteed false alarm reading as
*`probe2` corrupted physical 0`***.

| reading | what it says |
|---|---|
| identical to tonight's `H0c` | the restore put back what was there, over all 32 words, and `restore.mismatch = 0` is corroborated through a second instrument |
| differs in the **first 22** words only | `probe2` wrote the vector and did not restore it — but `restore.mismatch` read `00000000`, so the two would disagree and **neither number is usable** |
| differs beyond word 21 | something outside `probe2`'s 22-word window wrote the page. Nothing in this payload does |

---

## `SPI-warm` — `DW B8001200 4`, **71 bytes**

The warm half of `CLK-15 冷暖差`. Same command, after a **watchdog** reset — the
same reset class `CLK-15`'s warm population was measured on.

`SPI-cold`, 量 tonight, the first reading of this window on this device:

```
B8001200:  3FC00000  0BA08000  D8050000  FFFF0002
           SFCR      SFCR2     SFCSR     SFDR
```

| | prediction |
|---|---|
| the four words | 🔴 **not predicted.** A predicted value here would be the map the cell is testing |
| the decision | **all four identical → the SPI-divider hypothesis is excluded**, and the next candidate for the cold-minus-warm 4.5–14.5 ms is the NOR's own power-on wake-up. **`SFCR` differing → the divider is the mechanism**, and the differing field names itself |

🔴 **Two of block 0's predictions about this window were refuted and both are kept.**

1. **`SFCSR & 0xF8000000 == 0xF8000000`** — predicted from D table 10's reset
   values. **Measured `D8050000`**, so `& 0xF8000000` = `D8000000`. `LEN` is `01`
   (2 bytes), not the reset `11`, and `CMD_BYTE` is **`0x05`** — the SPI
   `RDSR` (Read Status Register) opcode. **The loader does not leave this
   controller at reset; it leaves it configured for status polling.** `SFCR2`'s
   top byte is `0x0B`, the `Fast Read` opcode, which is the MMIO read command.
2. **`SFDR` contains `1C 70 16`** — predicted because `ComSrlCmd_RDID()` runs
   twice on every boot and ends with `lw` from `SFDR`, and `REG-21`'s descriptor
   at `0x8040FBD4` holds `001C7016 1C701600`. **Measured `FFFF0002`.** So either
   `SFDR` does not retain the last transaction's data, or something read it
   since, or the last transaction was the `RDSR` that `CMD_BYTE` records.
   **The positive control I designed for this cell did not fire**, and the cell
   therefore rests on the weaker control that all four words decode sensibly
   against D table 10 — which they do.

⚠️ **A ride-along whose positive control failed is a ride-along that can report
*identical* for a reason that is not about the device.** If cold and warm agree
word for word, that is compatible with *the divider does not change* **and** with
*this window does not reflect boot-time configuration at all*, and this cell
cannot separate them. Said before the reading, not after.
