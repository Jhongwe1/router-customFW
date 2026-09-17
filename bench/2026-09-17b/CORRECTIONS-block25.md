# `CPU-45` is answered — this D-cache is NOT coherent with a real bus master

Card: `bench/2026-09-17b/PREDICTIONS-B26-block25.md`, frozen at `e85fd0c`
**with its decision rule**, before any of the rungs below existed.
Cells ran 11:36–11:45 on 2026-09-17. **Zero flash writes, zero uploads, zero
`J`, no `AUTOBURN` change, no power cycle** — the board has been at the loader
prompt since 11:02.

---

## 1. The two carded cells — both predictions exact

```
DW B8010000 1   ->  B8010000:  C4000000  A040FC74  00000000  00000000
DW B8010010 1   ->  B8010010:  00000000  00000000  00000000  A040FCDC
```

* **`CPUICR` = `C4000000`**, predicted as a decode rather than a copy: `TXCMD`
  (bit 31) = 1, **`RXCMD` (bit 30) = 1**, `BUSBURST_32WORDS` (29:28) = `00`,
  **`MBUF_2048BYTES` (26:24) = `100`**. 🟢 The 否證 the whole block rested on —
  *if bit 30 is 0 every cell below is void* — did not fire.
* `CPURPDCR0` = **`A040FC74`**, `CPURMDCR0` = **`A040FCDC`**: both **KSEG1**,
  which is § 0.3 ③'s 讀 (seven `lui 0xa000` sites in this unit's loader) turned
  **量**. **The loader keeps its DMA structures in uncached memory**, on the
  silicon, measured.
* `CPURPDCR1`–`5` are all `00000000`: only ring 0 is in use.

🔴 **`SPEC.md` had no row for `0xB8010000`.** These are its first readings.

---

## 2. The ring, walked off-card

Declared off-card because the addresses come out of `C2`'s own output — the
same situation as seating 16's nineteen `BIS-*` rungs, and the reason the
decision rule was frozen in `e85fd0c` instead.

| capture | what |
|---|---|
| `X7-mbufring` | `DW A040FCDC 32` — **401 bytes, the card's predicted size exactly** |
| `X8-pkthdrring` | `DW A040FC74 32` — 401 bytes |
| `X9`–`X11` | one mbuf, one 24-byte structure, one pkthdr |
| `X12-mbufs` | `DW A040FF30 24` — all four RX mbufs in one read |

🟢 **A free instrument control**: `X7` and `X8` overlap at `A040FCDC` and both
read `A040FF7B` there. Two cells, two commands, one address, same word.

**The RX mbuf ring**, at `0xA040FCD0`, four entries — `A040FF31`, `A040FF48`,
`A040FF61`, `A040FF7B` — where bit 0 is `DESC_OWNED_BIT` and bit 1 is
`DESC_WRAP` (讀 `rtl865xc_asicregs.h:552-554`). So three buffers belonged to the
switch core and one (`A040FF48`, bit 0 clear) to the CPU, and the fourth wraps.
⚠️ `CPURMDCR0` reads `A040FCDC`, the **fourth** entry rather than the base —
推, it is the engine's current position.

**The four data buffers**, from `X12`:

| mbuf | data pointer |
|---|---|
| `A040FF30` | `A040FF9A` |
| `A040FF48` | `A041079A` |
| `A040FF60` | `A0410F9A` |
| `A040FF78` | `A041179A` |

🟢 **Spacing `0x800` = 2048** — which is `MBUF_2048BYTES`, the field decoded out
of `CPUICR` in § 1. **A constant read from a register field, confirmed
independently by the actual spacing of the buffers it describes.**

---

## 3. 🔴🔴 The result

Protocol exactly as frozen: cached read (V0) → **a real bus master writes DRAM**
→ cached read (V1) → uncached read (V2), last, because `CPU-70`.

The treatment is **eight 1472-byte broadcast UDP frames** from the workstation.
The board has no IP and none was given; broadcast needs no ARP, and the MAC
DMAs every frame into the ring regardless of what the loader later does with it.

Line under test: data start + 1400, rounded down to 16-byte alignment.

### 3.1 Run 1 — `X13`/`X17`/`X21`, pattern `bytes(range(256))`

| buffer | cached V0 | cached V1 **after the DMA wrote** | uncached V2 | verdict |
|---|---|---|---|---|
| 0 `80410510` | `00000000` ×4 | **`00000000` ×4** | `4C4D4E4F 50515253 54555657 58595A5B` | 🔴 **STALE** |
| 1 `80410D10` | `00000000` ×4 | `4C4D4E4F …` | `4C4D4E4F …` | ambiguous |
| 2 `80411510` | `00000000` ×4 | **`00000000` ×4** | `4C4D4E4F 50515253 54555657 58595A5B` | 🔴 **STALE** |
| 3 `80411D10` | `00000000` ×4 | `4C4D4E4F …` | `4C4D4E4F …` | ambiguous |

### 3.2 🟢 The payload value was computed before the frames were sent

The line sits at buffer offset 1398. A frame is 14 (Ethernet) + 20 (IP) + 8
(UDP) = 42 bytes of header, so the payload index there is 1398 − 42 = **1356**,
and the pattern is a byte counter, so 1356 mod 256 = **76 = `0x4C`**. The
sixteen bytes must therefore be `4C 4D 4E … 5B`, i.e.
**`4C4D4E4F 50515253 54555657 58595A5B`**.

**That is what came back, on all four buffers.** It confirms three things at
once that nothing here set out to test: the DMA wrote where it was predicted
to, the mbuf data pointer is the first byte of the Ethernet header, and **this
switch inserts no CPU tag ahead of the frame**.

### 3.3 Run 2 — `X25`/`X26`/`X27`, a **different** pattern, and it also tested `CPU-70`

Pattern `(i+128) mod 256`, so the predicted V2 is
`CCCDCECF D0D1D2D3 D4D5D6D7 D8D9DADB`.

🔴 **A second prediction was written down before run 2 ran**: V0 should read
**run 1's** pattern rather than `00000000`, because run 1's step 4 was an
**uncached read of all four lines** and `CPU-70` measured that an uncached read
invalidates a resident line. If V0 came back `00000000` on buffers 0 and 2,
`CPU-70` would be contradicted on this path.

| buffer | V0 | V1 | V2 | verdict |
|---|---|---|---|---|
| 0 `80410510` | `4C4D4E4F …` | **`4C4D4E4F …`** | `CCCDCECF D0D1D2D3 D4D5D6D7 D8D9DADB` | 🔴 **STALE** |
| 1 `80410D10` | `4C4D4E4F …` | `CCCDCECF …` | `CCCDCECF …` | ambiguous |
| 2 `80411510` | `4C4D4E4F …` | **`4C4D4E4F …`** | `CCCDCECF D0D1D2D3 D4D5D6D7 D8D9DADB` | 🔴 **STALE** |
| 3 `80411D10` | `4C4D4E4F …` | `CCCDCECF …` | `CCCDCECF …` | ambiguous |

🟢 **Three predictions hit**: V0 is run 1's pattern on all four; V2 is the new
pattern on all four; and the same two buffers are stale again.

🟢🟢 **So `CPU-70` is confirmed on a second, independent path** — a real
DMA-written buffer rather than the A–B–A timing ladder it was measured on.

---

## 4. Why this is airtight, and what it is not

### 4.1 The decisive branch

For buffers 0 and 2, in both runs:

1. **V2 ≠ V0** → the bus master definitely wrote that DRAM address.
2. **V1 == V0** → the cached read returned the old value.
3. **A miss would have fetched V2.** Therefore the line *was* resident.

**There is no *it was evicted* escape** — and that is precisely what every
previous attempt on this question lacked. `docs/probe3-cells.md:770` registered
only `equal` as a refuter, and `c-A` could not tell *no read-allocate* from
*the alias is snooped* from *the line was evicted*. Here the eviction branch is
closed by the data itself: an evicted line reads V2, not V0.

**量: this D-cache holds stale lines after a real bus master overwrites the
underlying DRAM. It does not snoop.**

### 4.2 🔴 The ambiguous buffers are the control working, not a failure

Buffers 1 and 3 read the new value from cache in both runs. Per the frozen rule
that is *snooped, or evicted, or the loader touched it* — and **the first is
excluded by buffers 0 and 2 in the same run.** A cache either snoops or it does
not; it cannot snoop for two buffers and not for the other two in the same
experiment. So the mechanism on 1 and 3 is eviction or a CPU access, **and it
cannot rescue a coherence reading.**

⚠️ **推, and it is a residual rather than an answer**: the split is structural,
not noise — the *same* two buffers both runs. The four addresses are `0x800`
apart, so under an 8 KiB 2-way cache with 16-byte lines (讀, and the D-side
geometry has never been measured) buffers 0 and 2 share one set and buffers 1
and 3 share another. **Whatever distinguishes those two sets is unmeasured**,
and the experiment that would settle it is the D-side geometry ladder that has
never run.

### 4.3 What this does NOT establish

1. **Nothing about the D-cache's write policy** (`CPU-19` 殘留 ①). Still zero
   measurements. This block only ever reads.
2. **Nothing about D-side line size or associativity** — both still 讀 with no
   measurement, and § 4.2's 推 needs them.
3. It does not measure the cost of uncached rings, which is `R6-1`'s
   `D5` and a separate number.
4. ⚠️ The loader's own RX parsing is 推 to stop at ~42 bytes. The design rests
   on it, and buffers 1 and 3 are exactly where that assumption could be
   failing.

---

## 5. What it means for `R6`

`PROGRESS.md`'s `R6` stop-loss was written before any of this and says: *"`R6`
carries the conservative cost: rings **and** payload buffers in the uncached
window, which is what the vendor's own driver does for the rings. The
throughput number in `R6`'s DoD is then measured rather than assumed."*

🟢 **That row was a precaution and is now a requirement, by measurement.** The
three 讀 sources — the core vendor document, the vendor's Linux driver, and this
unit's loader — all said the cache does not snoop. **The silicon agrees**, and
`R6-3`'s rings go in KSEG1 because of a reading rather than because of a
vendor's opinion.

🔴 **And `R6`'s 否證 ② is now a live, named risk rather than a hypothetical**:
*if corruption is intermittent and load-dependent, that is `D1` not having been
answered*. `D1` is answered. If it happens anyway, the cause is somewhere else
and the gate does not get to blame coherency.
