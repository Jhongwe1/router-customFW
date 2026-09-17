# Block 25 — `CPU-45` gets a real bus master, and it is the one already running

**Frozen before power to these cells.** Seating 26, `bench/2026-09-17b/`,
**declared date 2026-09-17**. Same power cycle as block 24 (spent 11:02); the
board has not left the loader prompt.

---

## 0. What this block is

`R6`'s precondition is `SPEC.md` `CPU-45`: **is this D-cache coherent with
memory written by something other than the CPU?** Four proxy attempts across
three seatings returned negative and uninformative. `R6-0`'s redesign starts
from the weakness `docs/rlx-cache-and-cp0.md` § ② states about itself, and this
block is the first cell on this question that uses an engine instead of a model.

### 0.1 🔴 The reframing, and it is why a redesign is required rather than preferred

**量** `CPU-70` (seating 24): an **uncached read invalidates a resident line**
(`l.aba.c1` = 545, against 552 derived for *invalidated* and 46 for *not*).

**推, and it disqualifies the proxy** — the proxy protocol is *write through the
KSEG1 alias, then read through the KSEG0 alias*. If an uncached **access**
invalidates the line, the proxy's own write destroys the line under test before
the verifying read happens; the read then misses, fetches from DRAM, and
returns the new value — **which is indistinguishable from a snoop.** ⚠️ `CPU-70`
measured a *read*; that a write does likewise is 推. It does not need proving,
because the burden runs the other way: for `c-A`'s *fresh* to be evidence **for**
coherence, somebody would have to show the uncached write does **not**
invalidate, and nobody has.

**So the four negatives were never evidence that this cache is coherent.** They
are equally consistent with the vendor document's own position plus a
self-inflicted invalidation. 🔴 **And the bias has a direction: the proxy fails
toward a FALSE ALL-CLEAR**, which would license cached descriptor rings on a
part whose own vendor says they are unsafe. That is `PROGRESS.md`'s
*intermittent, load-dependent data corruption*, arrived at by an instrument.

### 0.2 A design of mine was killed at the desk today, and it failed the same way

Before this card existed, the proposal was to use the **loader's TFTP receive**
as the bus master. 讀, two independent desk passes reached the same kill:
`0x80401A18` calls `0x80406D0C`, which is `lbu` / **`sb` at `0x80406D24`** in a
count loop — **the CPU copies every TFTP byte into `LOADADDR`.** 算 agrees from
the other side: `MBUF_2048BYTES` against a 1,059,840-byte upload means the DMA
fills 2 KiB mbufs and software moves them on.

🔴 **It would not have failed quietly.** A CPU `sb` to a KSEG0 address whose
line is resident *hits and updates the line*, so the verifying read returns the
NEW bytes — **a false positive for coherence**, the identical bias to the proxy
it was meant to replace. **Recorded because it was nearly built.**

### 0.3 What replaces it

讀, three independent sources now say this cache does not snoop:

1. The core vendor document § 5.1, verbatim: *"Caches do not snoop the system
   bus"*. ⚠️ 讀 ×1, and it is the **LX4189**, a sister core.
2. **The vendor's Linux driver bets its product on it** — 量 over the building
   drop: rings, `rtl_pktHdr` and `rtl_mBuf` are `kmalloc(...) | UNCACHE_MASK`
   (`0x20000000`, six call sites at `rtl865xc_swNic.c:1188-1242`), payloads get
   explicit `_dma_cache_wback_inv()` at six more, and there is **no**
   `dma_alloc_coherent`, `dma_map_single` or `virt_to_phys` in all 79 files
   (grep exits 1; positive control hits `sunbmac.c` in the same kernel).
3. **This unit's own loader does the same** — 讀, seven sites force every packet
   buffer to KSEG1 (`lui 0xa000; or` at `0x80403D74`, `0x80403FDC`, `0x80404094`,
   `0x80404118`, `0x80404174`, `0x804041DC`, `0x80404258`).

🔴 **Three 讀 sources are not a measurement**, and this block exists because
`CLAUDE.md`'s rule is that a value entering code needs two agreeing sources —
while `R6`'s descriptor rings need the *silicon's* answer, not the vendor's
opinion of it.

---

## 1. The engine, and why it costs nothing

**量 today, this power cycle**: the loader printed `---Ethernet init Okay!`, so
the switch's CPU-port DMA is programmed and running. It writes received frames
into DRAM mbufs **with the CPU storing nothing**. One Ethernet frame on the
wire is the entire treatment: **no TFTP, no upload, no `AUTOBURN` change, no
filename, no `J`, zero writes of any kind.**

The register block is `CPU_IFACE_BASE`, 讀 `rtl865xc_asicregs.h:491`
*(`SYSTEM_BASE+0x10000`, and the header's own comment says `0xB8010000`)*:

| offset | symbol | |
|---|---|---|
| `0x000` | `CPUICR` | interface control |
| `0x004`–`0x018` | `CPURPDCR0`–`5` | Rx pkthdr descriptor control |
| `0x01c` | **`CPURMDCR0`** | **Rx mbuf descriptor control — the ring of data buffers** |
| `0x020`/`0x024` | `CPUTPDCR0`/`1` | Tx pkthdr |
| `0x028` | `CPUIIMR` | interrupt mask |
| `0x02c` | `CPUIISR` | interrupt status |

🔴 **`SPEC.md` has no row for `0xB8010000`.** These are the first readings.

---

## 2. The predictions

### 2.1 `C1-DMA0` — `DW B8010000 1`

Prints four words: `CPUICR`, `CPURPDCR0`, `CPURPDCR1`, `CPURPDCR2`. **71 bytes.**

**`CPUICR` = `C4000000`**, and the prediction is a decode rather than a copy —
讀 `rtl865xc_asicregs.h:527-537`, re-derived here bit by bit:

| bits | field | value | meaning |
|---|---|---|---|
| 31 | `TXCMD` | 1 | Tx enabled |
| 30 | `RXCMD` | **1** | **Rx enabled — this is what makes the experiment possible** |
| 29:28 | `BUSBURST_32WORDS` | `00` | 32-word burst |
| 26:24 | `MBUF_2048BYTES` | `100` | **2048-byte mbufs** |

> **否證** — if bit 30 is **0**, RX DMA is off and every cell below is void as
> an instrument, not negative as a result. **That is the single check this
> whole block rests on and it is read first.**

> **否證** — if `CPUICR` is anything other than `C4000000`, the three constants
> that let a desk read this unit's loader against the vendor's driver do not
> all transfer, and the `0xB8010000` map goes back to 讀.

**`CPURPDCR0`–`2`**: 推 — ring base pointers, so `8xxxxxxx` or `Axxxxxxx`.
Anything else (zero, or a value with the low bits set) means the descriptor
rings are not where this reading assumes.

### 2.2 `C2-DMA1` — `DW B8010010 1`

Prints `CPURPDCR3`, `CPURPDCR4`, `CPURPDCR5`, **`CPURMDCR0`**. **71 bytes.**

**`CPURMDCR0`** is the address this block needs: 推 — a **KSEG1** pointer,
`Axxxxxxx`, because § 0.3 ③ measured the loader forcing every packet buffer
uncached at seven sites.

> 🔴 **`DW B8010020` IS NOT TYPED ON THIS CARD.** It would print `CPUTPDCR0`,
> `CPUTPDCR1`, `CPUIIMR` and **`CPUIISR`** — an interrupt-status register whose
> read semantics are unknown here, and `NET-11`'s `PSRP` bit 8 is this
> project's own precedent for a status bit consumed by reading it.

### 2.3 `C3-RING` — `DW <CPURMDCR0 with bit 29 cleared> 32`

🔴 **The address is not on this card because it is not knowable before `C2`
runs.** What *is* pre-registered is its shape: 32 words of the Rx mbuf
descriptor ring, in which **the buffer pointers are the words matching
`A0xxxxxx` or `80xxxxxx`**. **401 bytes** (`8 lines × 47 = 376`, plus a
14-character command, 2 echo-tail and 9 prompt).

🔴 **That number was 326 in the draft of this card and `cardcheck numbers`
refused it before the card was frozen** — two errors compounding, a miscounted
line total and a command length written as 13 where it is 14. It is recorded
here because a pair of wrong numbers whose *difference* happens to be right is
the one defect class this repository has no checker for, and this time the
difference was wrong too, which is the only reason it was catchable.

⚠️ This is the same situation as seating 16's nineteen `BIS-*` rungs, which
were deliberately off-card because a bisection's rungs cannot be predicted from
the desk. **The rule that keeps it honest is that the DECISION RULE is frozen
here, before any of it runs**, so no reading can be re-interpreted after the
fact.

---

## 3. 🔴 The `CPU-45` protocol and its decision rule, frozen before anything runs

Let **B** be a data buffer address taken from `C3-RING`, and **L** a
16-byte-aligned line at **offset ≈ 1400** inside it.

| | step | why |
|---|---|---|
| 1 | `DW 80…L 4` — **cached** read | read-allocate is 量 (`t-hit`), so this makes the line resident. Value **V0** |
| 2 | host sends **six ~1500-byte broadcast UDP frames** | the MAC DMAs them into the ring. Six, so the ring certainly wraps past B |
| 3 | `DW 80…L 4` — **cached** read | **THE MEASUREMENT.** Value **V1** |
| 4 | `DW A0…L 4` — **uncached** read | **positive control**: what DRAM actually holds. Value **V2**. 🔴 **MUST BE LAST** — `CPU-70` measured that an uncached read invalidates the line |

### 3.1 The rule, and it is written here so no reading can be re-read later

* **`V1 == V0` and `V2 != V0`** → the cache returned stale data after a real bus
  master wrote DRAM. 🔴 **NOT COHERENT, and it is airtight**: a miss would have
  fetched V2, so the line *was* resident. **There is no *it was evicted*
  escape, which is exactly what every previous attempt lacked.**
* **`V1 == V2 != V0`** → **ambiguous.** Snooped, or evicted, or the loader's own
  parsing touched the line. Recorded as *cannot distinguish*, which
  `R6-1`'s DoD names as an acceptable result. **It is NOT written up as
  coherent.**
* **`V2 == V0`** → the DMA never wrote this line. **The cell measured nothing**;
  pick another buffer or offset. Not a result in either direction.

### 3.2 🔴 The confound this design is built around, and the mitigation

The loader **reads received frames uncached while parsing them**, and `CPU-70`
says an uncached read invalidates a resident line. **On any byte the loader
parses, both hypotheses predict V1 == V2** — the cell would be dead.

**Mitigation, and it is the whole reason for offset 1400**: the loader examines
roughly the first 42 bytes (Ethernet + IP + UDP headers), decides the frame is
not for it, and drops it. A line at offset ≈1400 of a 2048-byte mbuf is inside
the frame and **outside anything the CPU touches**. ⚠️ **推** — that the parse
stops there is read from the loader, not measured. If `V1 == V2` on every
buffer, this is the first thing to suspect and § 3.1's third branch covers it.

### 3.3 What is NOT claimed

* **A `V1 == V2` reading does not establish coherence.** Writing it up that way
  is the failure mode this entire block exists to avoid.
* Nothing here measures the D-cache's **write policy** (`CPU-19` 殘留 ①), which
  is a separate question and still has **zero** measurements.
* Nothing here measures D-side line size or associativity.

---

## 4. The guards

* **Zero writes.** Every board cell is a `DW`. No `EW`, `EB`, `FLW`, `FLR`,
  `PHYW`, `MDIOW`, `PORT1`, `J`, no TFTP, no upload.
* **`AUTOBURN` is left at `00000001`** — 量 `X2-autoburn`, its documented
  power-on state. Nothing is uploaded, so nothing needs it changed.
* `DW B8010020` is never typed (§ 2.2).
* 🔴 `DW`'s KSEG0 is a **default for bare addresses, not a mask** — 量
  `bench/2026-08-25/H0a3.log`, where `DW A0000080 32` echoed `A0000080:`. That
  is what makes steps 3 and 4 two different reads of one address, and without
  it this block is impossible.
* The host frames are **broadcast UDP to port 9**, so no board IP is needed and
  no `IPCONFIG` is sent.

---

## 5. The cells

```
#-- L. CPUICR + CPURPDCR0/1/2.  First reading of 0xB8010000 in this project.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C1-DMA0 --send 'DW B8010000 1' --until 'RealTek>' --seconds 15
#-- L. CPURPDCR3/4/5 + CPURMDCR0, the Rx mbuf ring base this block needs.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-17b/C2-DMA1 --send 'DW B8010010 1' --until 'RealTek>' --seconds 15
```

### 5.1 The numbers this card states, and where each is re-derived FROM

```cardnum
cells-fence	2	count bench/2026-09-17b/PREDICTIONS-B26-block25.md ^bench/2026-09-17b/C[0-9]+-[A-Za-z0-9]+$
dw4-bytes	71	dwreply 4
ring-bytes	401	dwreply 32
declared-date	1	count bench/2026-09-17b/PREDICTIONS-B26-block25.md [*][*]declared date 2026-09-17[*][*]
send-over-127	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']{128,}'
no-flr	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']*(EW |EB |FLW )
no-phy-verb	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']*(PHYR |PHYW |MDIOR |MDIOW |PORT1)
no-jump	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']*J [0-9A-F]
no-cpuiisr	0	count bench/2026-09-17b/PREDICTIONS-B26-block25.md -{2}send '[^']*DW B8010020
```

---

## 6. The fence

```cells
bench/2026-09-17b/C1-DMA0
bench/2026-09-17b/C2-DMA1
```

🔴 **`2 of 2` is a small number on purpose, and the scope is stated rather than
assumed.** Everything in § 3 runs as **declared off-card `X` cells**, because
its addresses come out of `C2`'s own output and a card cannot predict them.
What makes that honest is § 3.1: **the decision rule is frozen here, in this
commit, before a single one of those rungs runs.** A reading taken against a
rule written afterwards is not a result, and this is the mechanism that stops
it being one.
