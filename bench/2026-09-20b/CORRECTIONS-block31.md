# Corrections to block 31's card — written before the corrected cells ran

`PREDICTIONS-B33-block31.md` is frozen at `806ab84` and is not edited.

---

## 0. 🔴 The card's ladder has no known-good rung, and every one of its six rungs is confounded by the same thing

### What the cells actually say

All 19 cells passed their gate. The readings:

| cell | frames per datagram | host | `ReasmOKs` after |
|---|---:|---|---:|
| block 32 `H4-f6` | **6** | **20 / 20** | 42 |
| `Y1-slow14` (`-i 1.0`) | 14 | 0 / 10 | 42 |
| `Y4-hi14` (`high_thresh` ×16) | 14 | 0 / 145 | 42 |
| `Y8-f7` | **7** | 0 / 179 | 42 |
| `Y10-f8` | 8 | 0 / 179 | 42 |
| `Y12-f9` | 9 | 0 / 179 | 42 |
| `Y14-f10` | 10 | 0 / 179 | 42 |

**`ReasmOKs` is 42 at every single read of this block, and `FragCreates` is 183 at
every single read.** 42 and 183 are block 32's numbers: the board has not
assembled one datagram or emitted one reply fragment since block 32's `H4-f6`,
which was **20/20 at six frames**.

### 🔴 So the card asked the wrong question

The card treats each rung as an independent trial of a fragment count. It is not.
Seven frames failing thirty minutes after six frames succeeded is **either** a
boundary between 6 and 7 **or** a board that has been in a non-reassembling state
since `H5`, and the card cannot tell them apart because **it never re-establishes
the baseline.**

Block 32's ladder climbed from a known-good rung and was safe from this. Block 31
starts in an unknown state and stays there. ⚠️ The same applies to both
separators: `Y1-slow14`'s rate axis and `Y4-hi14`'s threshold axis were both run
**inside** the suspect state, so neither separates anything about a healthy board.

**A ladder that does not re-measure its own baseline cannot distinguish a
threshold from a latch.** That is the defect, it is the card's and not the
board's, and it is worth more written down than the six rungs are.

### 🟢 Two things survive the confound, because they are per-rung deltas

Neither depends on the board being healthy.

**① Every fragment reaches the IP layer, exactly.**

| rung | frames | `ΔInReceives` | pings × frames |
|---|---:|---:|---:|
| `Y9` | 7 | **1253** | 179 × 7 = **1253** |
| `Y11` | 8 | **1432** | 179 × 8 = **1432** |
| `Y13` | 9 | **1611** | 179 × 9 = **1611** |
| `Y15` | 10 | **1790** | 179 × 10 = **1790** |

Four rungs, four exact hits, with the ping count itself derived from
`-w 10 ÷ -i 0.05`. **Nothing is lost on the wire, in the switch or in the
driver.**

**② Exactly one fragment per datagram never enters `ip_defrag`.**

`ΔInReceives − ΔReasmReqds` is **180, 179, 180, 179** against a ping count of
**179**. 讀 `net/ipv4/ip_fragment.c`: `ip_defrag()` increments
`IPSTATS_MIB_REASMREQDS` on entry, once per fragment. So one fragment of every
datagram is dropped between `ip_rcv`'s counter and `ip_defrag` — and
`InHdrErrors`, `InAddrErrors` and `InDiscards` are all **0**, so it is dropped by
a path with no counter in this table.

**A datagram missing one fragment can never be reassembled**, which is why no
threshold and no rate makes any difference: the queue is waiting for something
that is not coming.

**③ And the threshold cell did separate one thing after all.** With
`ipfrag_high_thresh` at 4 MB, `Y5-snmp2` shows `ReasmFails +11` with
`ReasmTimeout` **+11** — every failure in that window was an **expiry**, where at
256 KB they were **evictions** (`Y0` had `ReasmFails` 218 against `ReasmTimeout`
3). One variable, two regimes, same underlying cause. That reading is clean
because it is about *how* a doomed queue dies, not about whether it dies.

---

## 1. The corrected cells

Three questions, three cells each costing one ping or one `cat`, all inside the
shell block 32 left alive (`Y16-live`, 41 bytes, prompt back).

```commands
#-- Z1-netstat  THE MISSING COUNTER.  /proc/net/snmp's Ip: row has no field for
#--             a packet dropped by ip_rcv's truncation test; /proc/net/netstat's
#--             IpExt: row has InTruncatedPkts.  PREDICTION: it is LARGE and near
#--             the number of failed datagrams.  If it is 0, truncation is not
#--             where the fragment goes and the search moves to ip_local_deliver.
CAP --out bench/2026-09-20b/Z1-netstat --send 'cat /proc/net/netstat' --seconds 25
#-- Z2-f6       THE LATCH CONTROL, and the cell block 31 should have opened with.
#--             Byte-identical to block 32's H4-f6, which was 20/20.
#--             PREDICTION if LATCHED: 0 received.  If NOT latched: 20 received,
#--             and then 7 frames really is the boundary.
HOST bench/2026-09-20b/Z2-f6 :: ping -I enxfc19286184c9 -c 20 -s 8000 -i 0.05 -w 10 -q 10.1.1.3
#-- Z3-snmp     ReasmOKs +20 (not latched) or +0 (latched).  This is the verdict.
CAP --out bench/2026-09-20b/Z3-snmp --send 'cat /proc/net/snmp' --seconds 25
#-- Z4-f1       ONE frame, no fragmentation at all.  Separates "reassembly is
#--             broken" from "the interface is broken": an unfragmented echo does
#--             not touch ip_defrag.  Block 32's H2-f1 was 20/20.
HOST bench/2026-09-20b/Z4-f1 :: ping -I enxfc19286184c9 -c 20 -s 1400 -i 0.05 -w 10 -q 10.1.1.3
#-- Z5-snmp     IcmpMsg InType8/OutType0 +20 if the interface is fine.
CAP --out bench/2026-09-20b/Z5-snmp --send 'cat /proc/net/snmp' --seconds 25
#-- Z6-netstat2 InTruncatedPkts delta across Z2+Z4, which is what makes Z1 a
#--             measurement rather than a cumulative number of unknown age.
CAP --out bench/2026-09-20b/Z6-netstat2 --send 'cat /proc/net/netstat' --seconds 25
#-- Z7-nic      tx_stopped must still be 0 and n_writes must still be 14.
CAP --out bench/2026-09-20b/Z7-nic --send 'cat /proc/rtl819x-nic' --seconds 25
#-- Z8-live
CAP --out bench/2026-09-20b/Z8-live --send 'echo RLXFW-LIVE-MARK' --seconds 12
```

These are **off-card** `Z*` cells, declared here rather than added to a frozen
fence, the same treatment `bench/2026-09-20`'s forty-three `X*` cells got.

### What each outcome licenses

| `Z2-f6` | `Z4-f1` | conclusion |
|---|---|---|
| 20/20 | 20/20 | **not latched.** The boundary is genuinely between 6 and 7 fragments, and block 31's ladder stands after all |
| 0/20 | 20/20 | **latched, and only reassembly is latched.** The interface, the driver and ICMP are all fine; something in `ip_defrag`'s state or in the one dropped fragment persists |
| 0/20 | 0/20 | **latched, and wider than reassembly.** The interface stopped answering anything, and `Z7-nic` decides whether the driver knows |

⚠️ **Whatever `Z2` says, the six rungs of block 31 do not become a fragment-count
boundary retroactively.** If `Z2` is 20/20 the rungs are *consistent* with one,
but they were run without the control and a later block has to re-run them with
`Z2`'s form as rung zero.

### What `Z1`–`Z8` read

| cell | reading |
|---|---|
| `Z1-netstat` | **`InTruncatedPkts 1096`**, `InNoRoutes 0` |
| `Z2-f6` | **168 transmitted, 20 received, 88.1 % loss** — where the byte-identical `H4-f6` was **20/20, 0 %** thirty minutes earlier |
| `Z3-snmp` | `ReasmOKs` 42 → **63** (+21), `FragCreates` 183 → **309** (+126 = 21 × 6, exact) |
| `Z4-f1` | **24 transmitted, 20 received, 16.7 % loss** — unfragmented, where `H2-f1` was 20/20 |
| `Z5-snmp` | `ΔInReceives` +24 exact; `IcmpMsg InType8` 82 → **102** |
| `Z6-netstat2` | `InTruncatedPkts` → **1250**, **Δ +154** against 147 + 4 = **151** failed datagrams |
| `Z7-nic` | `tx_stopped 0`, `n_writes` **14** |
| `Z8-live` | 41 bytes |

**Not latched — degraded.** Reassembly still works; it just has to win six coin
flips instead of one. And an **unfragmented** datagram loses too, which takes
reassembly out of the causal chain entirely: 4 of 24 single-frame echoes never
reached ICMP.

---

## 2. The chain, and the one link left

Eight links, each with its own measurement:

| # | link | evidence |
|---|---|---|
| 1 | ≥ 8 back-to-back frames arrive at an 8-entry ring, against a byte-at-a-time copy at ~1.88 MB/s | 讀 `NIC_RX_DESC 8`; 量 switch port 3 `pause 1764` |
| 2 | **`MBUF_RUNOUT` fires** | 量 `seen_iisr` `0000320E` → **`0001320E`**; 讀 `rtl819x-nic.c:292`, bit 16 is `NIC_IP_MBUF_RUNOUT`. First seen at `C16-f14` |
| 3 | the two RX position registers **desynchronise by exactly 4 and stay there** | 量, below |
| 4 | the driver indexes **both** rings with one `nic_rx_idx`, and `nic_refill` refills both at the same `i` | 讀 `:748` (OWN from `nic_rx_ring`), `:755` (length from `nic_rx_ph`), `:1227-1234` |
| 5 | frames are then delivered carrying another frame's length | 量 `InTruncatedPkts` 1250, one per failed datagram |
| 6 | and that counter is **not in `/proc/net/snmp`**, which is why every visible drop counter read 0 | 量 `InHdrErrors` / `InAddrErrors` / `InDiscards` all **0** |
| 7 | it never recovers on its own | 量 `H4-f6` 20/20 against the byte-identical `Z2-f6` 20/168 |
| 8 | **the wire is clean, so the truncation is mine** | 量 switch port 3: 13,541 frames, `CRCAlignErr 0`, `Drop 0`, `< 64: 0 pkts` |

`rx_ring` is `A15B8000` and `mb_ring` is `A15B8020`, four bytes per entry:

| cell | `rpdcr0_pos` → idx | `rmdcr0_pos` → idx | Δ |
|---|---|---|---:|
| `C8-BASE` | `A15B8018` → 6 | `A15B8038` → 6 | **0** |
| `C11-frag1` | `A15B8004` → 1 | `A15B8024` → 1 | **0** |
| `C12-f1` | `A15B801C` → 7 | `A15B803C` → 7 | **0** |
| `C13-f3` | `A15B8010` → 4 | `A15B8030` → 4 | **0** |
| `C14-f6` | `A15B8018` → 6 | `A15B8038` → 6 | **0** |
| **`C16-f14`** | `A15B8018` → 6 | `A15B8028` → **2** | **4** |
| `C17-f41` | `A15B8004` → 1 | `A15B8034` → **5** | **4** |
| `Y6-nic` | `A15B8014` → 5 | `A15B8024` → **1** | **4** |
| `Z7-nic` | `A15B801C` → 7 | `A15B802C` → **3** | **4** |

Five reads and ~12,000 frames after the run-out, Δ is **4 every time**. And
`rx_idx` equals the `rp` index in all nine, so the OWN test is right and the
length read is four slots wrong.

### The link that is missing: causality by repair

Everything above is a correlation with a mechanism. 讀 `nic_do_arm()`
(`:1187-1213`) writes `CPURPDCR0 ← nic_rx_ring` and `CPURMDCR0 ← nic_mb_ring`,
so **`arm` puts both positions back to their bases** — it is the repair, and it
needs `!nic_engine_on`, so `engine off` first.

```commands
#-- Z9-arm    engine off, arm, engine on.  PREDICTION: rp index == rm index in
#--           Z10.  If they are still 4 apart, arm does not reset them and this
#--           whole repair route is wrong -- which is a reading, not a failure.
CAP --out bench/2026-09-20b/Z9-arm --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --seconds 25
#-- Z10-nic   the register evidence, taken BEFORE any traffic so it is clean
#--           whatever the ping then does.
CAP --out bench/2026-09-20b/Z10-nic --send 'cat /proc/rtl819x-nic' --seconds 25
#-- Z11-f6    the byte-identical ping for the third time.  H4-f6 20/20,
#--           Z2-f6 20/168.  PREDICTION: 20/20 if the desync is the cause.
HOST bench/2026-09-20b/Z11-f6 :: ping -I enxfc19286184c9 -c 20 -s 8000 -i 0.05 -w 10 -q 10.1.1.3
#-- Z12-snmp  ReasmOKs +20 and ReasmFails +0 is the repaired shape.
CAP --out bench/2026-09-20b/Z12-snmp --send 'cat /proc/net/snmp' --seconds 25
#-- Z13-net2  InTruncatedPkts delta 0 is the same statement one layer down.
CAP --out bench/2026-09-20b/Z13-net2 --send 'cat /proc/net/netstat' --seconds 25
#-- Z14-nic2  and whether the ping desynced them again.
CAP --out bench/2026-09-20b/Z14-nic2 --send 'cat /proc/rtl819x-nic' --seconds 25
#-- Z15-live
CAP --out bench/2026-09-20b/Z15-live --send 'echo RLXFW-LIVE-MARK' --seconds 12
```

⚠️ **The known flaw in this test, stated before it runs.** `nic_do_arm()` does
**not** reset `nic_rx_idx`, which is 7 at `Z7-nic`. So after the repair the
hardware restarts at ring index 0 while the driver still polls index 7, and the
driver is now out of step with the hardware even though the two hardware rings
are back in step. Header and buffer will still come from the **same** slot, so
frames should not be truncated — but they may be delivered in the wrong order
for the first eight. **`Z10-nic` is read before any traffic precisely so the
register answer survives whatever `Z11` does.**

🔴 **If `Z11` is bad, the fallback is `busybox reboot -f`** — 量 `FW-37`, 2.407 s
to the loader prompt, no power press — followed by the same ping on a fresh boot.
That is a weaker causal claim (a reboot repairs everything) but it settles
*state versus fragment count*, which is the question block 31 could not answer.
