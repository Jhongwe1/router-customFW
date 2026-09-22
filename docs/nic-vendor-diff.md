# `rtl819x-nic` against the vendor's driver, field by field

`R6`'s `D3` carries this as its written refutation condition:

> **否證 `D3`** — if frames go out and none come back, the descriptor field
> layout is wrong for big-endian. The honest output is a **field-by-field
> comparison against the vendor's driver**, written down, and not a retry.

`D3` passed without that document existing. `D5` has now failed four seatings
with the blocker renamed four times (`NET-59` → `NET-61` → `NET-67` →
`NET-78`), each name refuted by the next seating's measurements. This file is
the comparison, written because a search with no reference implementation can
only exclude one candidate per power cycle.

⚠️ **This is not `docs/driver-diff.md`.** That file's scope is `R5`'s six
drivers against third-party ports (`docs/driver-diff.md:20`); 量,
`grep -ci "nic|ethernet|rtl865x|swNic|eth0"` over it is **0**. The two files do
not overlap and neither supersedes the other.

## Method

**Vendor side**, all 讀, from the tree `SOURCES.json` gives role **base**:
`src-vendor/rtl819x-toolchain/linux-2.6.30/drivers/net/rtl819x/`, pin
`5c9be5d943318fdb4d048ae22078129594eb5a10`. Every `#if` below is resolved
against **this board's** config, `boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW`,
and the resolution is printed rather than assumed — `NET-79` records what
happens when it is not (`TX 1024 / RX 512` is the `CONFIG_RTL_8198` branch and
was quoted for this board for one segment).

**rlxfw side**, all 讀, from
`config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c`.

**A third side where it exists**: this die's own loader, 量, from the TX and RX
descriptor templates read at the loader prompt before any driver ran
(`bench/2026-09-19b/X14-rings-post`). Where the loader agrees with the vendor
source, a constant this project inherited by measurement is confirmed by a
source that shares no code with it.

### Config resolution for this board

量 on the committed config file:

| symbol | this board |
|---|---|
| `CONFIG_RTL_8196E` | `=y` |
| `CONFIG_RTL_8198` | **absent** |
| `CONFIG_RTL_ETH_PRIV_SKB` | `=y` |
| `CONFIG_RTK_VLAN_SUPPORT` | `=y` (runtime flag, default 0 — below) |
| `CONFIG_RTL_MULTI_LAN_DEV` | **absent** |
| `CONFIG_POCKET_ROUTER_SUPPORT` | **absent** |
| `CONFIG_RTL_HW_VLAN_SUPPORT` | **absent** |
| `CONFIG_RTL_LOCAL_PUBLIC` | **absent** |
| `CONFIG_RTL_HW_QOS_SUPPORT` | **absent** |
| `CONFIG_RTL_IGMP_SNOOPING` | `=y` |

## 1. The summary table

Each row says whether it is a candidate for `NET-78` — *the engine consumes
every descriptor, clears every OWN bit, advances its position pointers, and
puts no frame on the wire, while RX stays healthy* (`SPEC.md` `NET-78`).

| # | axis | vendor (讀) | rlxfw (讀) | `NET-78` candidate |
|---|---|---|---|---|
| 1 | **TX mode for ordinary unicast** | **hardware lookup** — `ph_portlist = 0x07`, `ph_flags` carries `PKTHDR_HWLOOKUP\|PKTHDR_BRIDGING` | **direct** — `ph_portlist = 0x3F`, no lookup bits | 🔴 **yes, §2** |
| 2 | `ph_vlanId` | `txInfo->vid = cp->id`, set per frame | word 4 written **0**, every frame | 🔴 **yes, §2** |
| 3 | `portlist == 0` guard | frees the skb, returns FAILED | **none** | ⚠️ instrument, §2 |
| 4 | ring depth | TX **128** / RX **256**, usable 127 | TX **4** / RX **8** | 🟡 §3 |
| 5 | packet data buffers | zero-copy from the skb + `_dma_cache_wback_inv()` | byte-at-a-time copy into an uncached bounce buffer | 🔴 **no** — §4, but it is `D5`'s ceiling |
| 6 | full-ring behaviour | reclaim in place, retry ≤128, then drop and report success | `netif_stop_queue` + `NETDEV_TX_BUSY` | 🔴 **no** — `n_tx_full 0`, `NET-80` |
| 7 | rings / descriptors memory | `UNCACHED_MALLOC` | KSEG1 alias of one `kmalloc` | 🟢 same |
| 8 | `ph_flags` TX / RX template | `0x8800` / `0x9000`, derived | `0x8800` / `0x9000`, measured | 🟢 **confirmed, §5** |
| 9 | RX buffer lookup | **follows `ph_mbuf`**, the pointer in the pkthdr's word 0 — one consumption index | **indexes the mbuf ring** with the pkthdr ring's `i` | 🔴 **no** — it is `NET-61`'s, §6 |
| 10 | register programming order | all 4 TX bases, then 6 RX pkthdr bases, then 1 mbuf base, under `local_irq_save` | same order | 🟢 same |

## 2. The largest divergence: the vendor does not name egress ports, and rlxfw floods

讀 `rtl_nic.c:4951-4970`, the vendor's two TX modes:

```c
static inline void rtl_direct_txInfo(uint32 port_mask, rtl_nicTx_info *txInfo)
{
	txInfo->portlist   = port_mask & 0x3f;
	txInfo->srcExtPort = 0;
	txInfo->flags      = (PKTHDR_USED | PKT_OUTGOING);
}

static inline void rtl_hwLookup_txInfo(rtl_nicTx_info *txInfo)
{
	txInfo->portlist   = RTL8651_CPU_PORT;      /* must be set 0x7 */
	txInfo->srcExtPort = PKTHDR_EXTPORT_LIST_CPU;
	txInfo->flags      = (PKTHDR_USED | PKTHDR_HWLOOKUP | PKTHDR_BRIDGING | PKT_OUTGOING);
}
```

and `rtl_nic.c:5029-5075`, which chooses between them:

```c
txInfo->vid   = cp->id;
txInfo->txIdx = 0;
if ((skb->data[0] & 0x01) == 0) {                     /* unicast */
	if (rtl_isHwlookup(skb, cp, &portlist) == TRUE)
		rtl_hwLookup_txInfo(txInfo);
	else
		rtl_direct_txInfo(portlist, txInfo);
} else {                                              /* mcast / bcast */
	rtl_direct_txInfo(cp->portmask, txInfo);
}
...
if (txInfo->portlist == 0) { dev_kfree_skb_any(skb); return FAILED; }
```

讀 `rtl_nic.c:4988-5028`, `rtl_isHwlookup()` with this board's config
substituted — four of its five `#if` gates are absent, so it reduces to:

```c
if (rtk_vlan_support_enable == 1) { *portlist = cp->portmask; return FALSE; }
if (rtl_isWanDev(cp) != TRUE && rtl_ip_option_check(skb) != TRUE) return TRUE;
*portlist = cp->portmask; return FALSE;
```

讀 `rtl_nic.c:6645`: `rtk_vlan_support_enable = 0` is the initialised value,
and `:8538-8570` are the only writers, all on a `/proc` path.

**So on this board, in its default runtime state, an ordinary unicast frame
leaving a LAN netdev goes out in HARDWARE LOOKUP mode**: the ASIC's L2 table
decides the egress port, `ph_portlist` is the magic `0x07`
(讀 `rtl865xc_swNic.h:155`), and `ph_flags` carries `PKTHDR_HWLOOKUP` (`0x0020`)
and `PKTHDR_BRIDGING` (`0x0040`) — 讀 `common/mbuf.h:117-124`.

rlxfw, 讀 `rtl819x-nic.c:1629-1631`:

```c
nic_dw_set(nic_tx_ph, i, 1, NIC_PH_MK1(len + 4, 0, 0));
nic_dw_set(nic_tx_ph, i, 3, NIC_PH_MK3(NIC_PH_FLAGS_TX_DEFAULT, 0x3F));
nic_dw_set(nic_tx_ph, i, 4, 0);
```

| field | vendor, this board | rlxfw |
|---|---|---|
| `ph_portlist` | `0x07` (lookup) | `0x3F` |
| `ph_flags` | `0x8860` | `0x8800` |
| `ph_srcExtPortNum` | `PKTHDR_EXTPORT_LIST_CPU` = 3 | `0` |
| `ph_vlanId` | `cp->id` | `0` |

🔴 **`RTL8651_MAC_NUMBER` is 6** (讀 `l2Driver/rtl865x_fdb.h:3`,
`AsicDriver/rtl865x_asicCom.h:24`), so in direct mode `0x3F` is *every* MAC.
**rlxfw floods every frame it transmits, unicast included.** The vendor floods
nothing: multicast and broadcast get `cp->portmask` (讀, and 量
`notes/nic-driver.md:536-538` — the boot log's `Member port` field is a bitmask
and `eth4` is `0x8`, one port), and unicast is either looked up or given a
portlist derived from the destination MAC.

🔴 **And `_swNic_send` would have masked it**: 讀 `rtl865xc_swNic.c:730-734`,
`ph_portlist = nicTx->portlist & 0x1f` on every branch except
`CONFIG_8198_PORT5_GMII/RGMII`, which this board does not define. rlxfw writes
the descriptor itself, so its bit 5 is not masked by anything.

⚠️ **Where this reading is weakest.** rlxfw's `0x3F` is not invented: 量,
`bench/2026-09-19b/X14-rings-post`, this die's own loader left `8800003F` in
word 3 of a TX descriptor after a real transfer. **The loader is bare metal with
no L2 table, so direct-plus-flood is the right mode for the loader** — the
divergence is that a loader convention was carried into a Linux driver where
the vendor uses a different mechanism. Both are modes the hardware offers.

推, and the experiment that decides it: flooding a unicast makes the switch
take a forwarding decision for five ports instead of one, and four of them have
no link. Whether that costs per-port egress resources that `GDSR0` does not
show is **not established** — `GDSR0` read `0012001E` with all three run-out and
flow-control flags clear across the fault (量, `SPEC.md` `NET-78`), and
`GDSR0` is a *shared descriptor* counter, not a per-port queue. **The reading
that decides it is the switch's per-port MIB counters across the fault**, which
`NET-78` 殘留 already names as missing and which are reachable through the
vendor's `/proc/rtl865x/asicCounter` without a new image.

⚠️ `ph_vlanId = 0` is a second, independent thing in the same word family and
it has the same shape: the driver **has** the macro — `NIC_PH_MK4(vid)`,
讀 `rtl819x-nic.c:501` — and `nic_xmit` does not call it. Whether VLAN 0 is a
member set the switch resolves is unmeasured; `R6-2` put the switch in a dumb
state whose `PVCR0`–`PVCR4` values are committed (`bench/2026-09-21d`), so this
can be settled at the desk against those, **before any power is spent**.

⚠️ The `portlist == 0` guard has no rlxfw equivalent. It cannot fire on a
constant `0x3F`, so it is an instrument rather than a candidate — but it is the
vendor saying, in code, that a frame with no egress port is a frame to free
rather than to hand to the engine.

## 3. Ring depth, and why the descriptor pool is not the story

讀 `rtl865xc_swNic.h:78-88`, `#else` branch plus `DELAY_REFILL_ETH_RX_BUF`
(讀 `include/net/rtl/rtl_types.h:430-434`): `NUM_TX_PKTHDR_DESC` **128**,
`NUM_RX_PKTHDR_DESC` **256**, usable TX depth 127 because
`rtl865xc_swNic.c:701-704` keeps `next_index != txPktDoneDescIndex`.

rlxfw: `NIC_TX_DESC 4`, `NIC_RX_DESC 8` (讀 `rtl819x-nic.c:406-407`), chosen so
a full ring dump fits in one 4,096-byte `/proc` page — `FW-46` measured this
image has no `dd` and no `md5sum`, so the dump *is* the instrument.

🔴 **32× on both rings, and it is measured not to be `NET-78`'s cause**: 量
`SPEC.md` `NET-80`, `n_tx_full` read **0** — the ring never filled, and the
board became unreachable having transmitted 37 frames with all four TX
descriptors CPU-owned.

⚠️ **But it is a reason the engine's position register carries less information
than it looks like it does.** 量 `NET-78`: `tpdcr0_pos` read `A15B8044`
*unchanged* across the fault, and `A15B8044` is `tx_ring` base + 4, i.e. index
1. `n_tx` was 5 at the first sample and 37 at the second. **5 mod 4 = 1 and
37 mod 4 = 1.** On a four-entry ring the position register aliases every four
frames, so *unchanged* is exactly what a fully-running engine would print at
those two sample points. The row's own conclusion — that the engine ran and
returned every descriptor — is supported by the OWN bits and by `n_tx`
advancing; it is **not** additionally supported by `tpdcr0_pos`, and nothing had
said so.

## 4. Buffers: the vendor is zero-copy on the same non-coherent cache

讀 `rtl865xc_swNic.c:750`, `_swNic_send`:

```c
pPkthdr->ph_mbuf->m_data = (output);      /* the skb's own data */
pPkthdr->ph_mbuf->m_extbuf = (output);
```

and 讀 `rtl_nic.c:5159`, immediately before the call:

```c
_dma_cache_wback_inv((unsigned long) tx_skb->data, tx_skb->len);
```

with the RX counterpart at `rtl865xc_swNic.c:253` and `:349`
(`_dma_cache_wback_inv((unsigned long)skb->head, skb->truesize)` on refill).
讀 `rtl865xc_swNic.c:37`: `_dma_cache_wback_inv` is a function pointer the
architecture exports.

So the vendor puts **rings and descriptors** in uncached memory
(`UNCACHED_MALLOC`, six call sites, 讀 `rtl865xc_swNic.c:1188-1242`) and leaves
**packet data** cached, with explicit maintenance at the two hand-off points.

rlxfw puts all three in KSEG1 and copies, 讀 `rtl819x-nic.c:1611-1612`
(TX, `__raw_writeb`) and `:912-914` (RX, `__raw_readb`) — byte at a time,
because 讀 `:823-830`: the buffers are 2 mod 4 and a word-wise copy would be an
unaligned load, which on this core faults rather than trapping to a slow path.

🔴 **This is not a candidate for `NET-78`** — a copy that is too slow does not
make the engine drop frames it has accepted. **It is `D5`'s ceiling.** Per
1,446-byte frame rlxfw issues ~1,446 uncached single-byte bus transactions in
each direction where the vendor issues one cache-writeback over ~91 lines.
量 `SPEC.md` `NET-76`: 29.761 Mbit/s aggregate, 1,290 frames/s each way,
sustained over 1,899.593 s. ~~**Whether that number is the path or the copy is
unknown, and it cannot be known without a reference** — which is what the
`eth4` contrast is for.~~ 🔄 **2026-09-22: the contrast was taken, by § 11 of
this file, one section later — and this sentence was never revisited.** 量
`NET-84`/`NET-85`, both board→host: the vendor reaches **25.4 Mbit/s** and
rlxfw **23.3**, so the byte-at-a-time uncached copy costs **8–13 %** in that
direction and is **not** a ceiling anywhere near the 29.761. ⚠️ **The
qualifier that survives is narrower and is about direction, not about the
copy**: there is no vendor figure for the board RECEIVING, so nothing here
bounds the copy's cost on the RX side — which is the side `D5` measures.
`notes/nic-driver.md` § 16.3c.

⚠️ `D1` (`CPU-45`) answered *not coherent* and this driver's response was to
make everything uncached, recorded at `rtl819x-nic.c:92-113` as a measured
requirement. The vendor's source shows the other available response on the same
silicon. **Changing it is out of scope here and is named, not done**: it is one
of four things that would change at once, and `NET-78` is undetermined.

## 5. Two constants this project inherited by measurement, confirmed by source

量, this die's loader templates (`bench/2026-09-19b/X14-rings-post`):
TX pkthdr word 3 = `0x88000000` → `ph_flags` **`0x8800`**;
RX pkthdr word 3 = `0x90000000` → `ph_flags` **`0x9000`**.

讀, the vendor's `swNic_init`, `rtl865xc_swNic.c:1270-1276` (TX) and
`:1333-1339` (RX):

```c
pPkthdr->ph_flags = PKTHDR_USED | PKT_OUTGOING;   /* TX */
pPkthdr->ph_flags = PKTHDR_USED | PKT_INCOMING;   /* RX */
```

讀 `common/mbuf.h:25`, `:111`, `:118-119`: `BUF_USED = 0x80`,
`PKTHDR_USED = (BUF_USED << 8) = 0x8000`, `PKT_OUTGOING = 0x0800`,
`PKT_INCOMING = 0x1000`. So `0x8800` and `0x9000`.

🟢 **Both match to the bit, from two sources that share no code** — a
bare-metal loader's live rings on this die, and a Linux driver's source in a
GPL drop. `rtl819x-nic.c:519-525` calls `ph_flags` *the one field this driver
cannot derive*; on the **template** values it now is derived, and they agree.
⚠️ That says nothing about the *per-frame* `ph_flags`, which §2 shows the
vendor changes and rlxfw does not.

## 6. The one path nobody has read, and it is the one `NET-61` is about

量, over the whole repository excluding `upstream/`: `swNic_getRxringIdx` and
`__swNic_geRxRingIdx` — `rtl865xc_swNic.c:386-517`, the function pair that
decides **which RX ring and which descriptor index the driver reads next** —
are cited **zero** times.

⚠️ **The adjacent claim is narrower than it looks and is corrected here.**
`swNic_receive` itself (`rtl865xc_swNic.c:577-692`) **is** read, at two points:
`:604` (the `ph_flags` checksum drop, quoted at `rtl819x-nic.c:143-150`) and
`:650` (the FCS in `ph_len`, quoted at `:1555`). And the register programming
order **is** read — `rtl819x-nic.c:1963` cites `rtl865xc_swNic.c:1306-1384` and
`:1438` cites `:1134-1384`, both accurately. A sweep restricted to `notes/`,
`docs/` and `SPEC.md` misses these, because this project puts that kind of
reading in the driver's own comments.

🔴 **What was genuinely unread is the index machinery — and reading it produced
the largest result in this file.**

讀 `rtl865xc_swNic.c:386-410`, `__swNic_geRxRingIdx()`: the vendor's only test
for "is there a frame" is the OWN bit of
`rxPkthdrRing[ring][currRxPkthdrDescIndex[ring]]`, under `local_irq_save`, with
a `DELAY_REFILL_ETH_RX_BUF` guard against the refill cursor
(`rxDescReadyForHwIndex`, `rxDescCrossBoundFlag`). 讀 `:414-437`,
`swNic_getRxringIdx()` walks the rings from high priority down — and it is
inside `#if defined(RTL_MULTIPLE_RX_TX_RING)`, which 量 is **defined nowhere in
the tree**, so on this board `swNic_receive` runs the `#else`: `rxRingIdx = 0`,
one ring.

讀 `rtl865xc_swNic.c:597-628`, how the vendor reaches a received frame's buffer:

```c
pPkthdr = (struct rtl_pktHdr *) (rxPkthdrRing[rxRingIdx][currRxPktDescIdx]
                                 & ~(DESC_OWNED_BIT | DESC_WRAP));
...
info->input = pPkthdr->ph_mbuf->skb;
info->len   = pPkthdr->ph_len - 4;
info->pid   = pPkthdr->ph_portlist;
info->vid   = pPkthdr->ph_vlanId;
```

🔴🔴 **The vendor never indexes the mbuf ring to consume a frame.** It reads one
pkthdr ring entry, masks off `OWN` and `WRAP` to get the pkthdr's address, and
then **follows the pointer in that pkthdr's word 0** (`ph_mbuf`) to the mbuf and
its buffer. There is exactly one consumption index in the vendor's RX path,
`currRxPkthdrDescIndex[ring]`; `currRxMbufDescIndex` exists but belongs to
refill.

rlxfw, 讀 `rtl819x-nic.c:1394` and `:908`:

```c
u32 e = nic_re(nic_rx_ring, i);      /* OWN, from the PKTHDR ring at i */
...
bf = nic_dw(nic_rx_mb, i, 3);        /* buffer address, from the MBUF ring at the SAME i */
```

**`SPEC.md` `NET-61` measured this as a defect from the outside** — a burst
offsets the engine's two RX position registers, rlxfw indexes both rings with
one `nic_rx_idx`, and frames get delivered carrying another frame's length.
**The vendor's source is structurally immune to it**, and the difference is one
dereference.

🟢 **rlxfw already holds the pointer and does not read it.** 讀
`rtl819x-nic.c:1925` — at ring build, `nic_dw_set(nic_rx_ph, i, 0, mb)` writes
each RX pkthdr's own mbuf-descriptor address into word 0. It is written every
time the rings are built and never read on the harvest path.

推, and it is a *design* claim rather than a measurement: harvesting via
`nic_dw(nic_rx_ph, i, 0)` instead of `nic_rx_mb + i` removes the class of fault
`NET-61` detects, rather than detecting it. ⚠️ **It is not free and the cost is
named**: the two rings would then be allowed to drift, so `n_dsync`'s detector
(`SPEC.md` `NET-70`, with its three-way positive control) stops being a fault
indicator and becomes a *normal* reading — which means the change must keep the
counter and re-state what a non-zero value means, or it trades a measured
instrument for an unmeasured assumption. **Out of scope here; named, with its
cost, and it is not `NET-78`.**

## 7. What this file does NOT establish

1. **It does not identify `NET-78`.** It supplies four candidates with their
   deciding readings; none has been taken.
2. **It is single-sourced.** `SOURCES.json:115-118` declares `utessel-edimax`
   as *"A SECOND independent implementation of the rtl819x network driver …
   incl. `rtl_nic.c`"*, `needed_by: R6`, `fetch: later`; 量, it has never been
   cloned and is cited nowhere, as are `openwrt-rtk` and `vankel-rtl819x-sdk`.
   **This project's rule that a register reading needs two sources has never
   been applied to the NIC axis.** Carried forward, not done here.
3. **It does not read the vendor's RX index machinery** (§6) — named, not done.
4. **`rtl_isWanDev(cp)` is not resolved for `eth4`.** §2's conclusion assumes
   `eth4` is a LAN device. 量 `notes/nic-driver.md:536-538` gives `eth4` port 3
   as a member-port bitmask; it does not say LAN or WAN. If `eth4` is the WAN
   device, `rtl_isHwlookup` returns FALSE and the vendor uses direct mode with
   `cp->portmask` = `0x8` — **which changes §2's first row but not its point**,
   because `0x8` is still one port against rlxfw's six.
5. **Nothing here has been measured on the silicon.** Every rlxfw row is 讀 of
   a source file, and the driver rows describe `rtl819x-nic 1.1` as committed,
   not as any particular image.

## 8. Candidates for `NET-78`, ranked, each with the reading that decides it

| | candidate | 讀/推 | deciding reading | costs power |
|---|---|---|---|---|
| ① | The frame is flooded to six MACs in direct mode where the vendor looks up one, and the egress decision for the four dark ports consumes something `GDSR0` cannot see | 讀 the divergence, 推 the mechanism | the switch's **per-port MIB counters** across the fault, via `/proc/rtl865x/asicCounter` — `NET-78` 殘留 already names it | no new image |
| ② | ~~`ph_vlanId = 0` on every frame, against a switch whose dumb-state VLAN configuration is committed~~ | — | 🔴 **REFUTED at the desk, §9** | — |
| ③ | The TX pkthdr's word 2 is written once at init and never per frame, and the ASIC may write it back — and `/proc` does not print it | 讀 | add `txd%u ph2/ph3/ph4` to the dump; needs a build | one image |
| ④ | The vendor's `eth4` carries the same load without failing | — | `ifconfig rlx0 down` (讀 `rtl819x-nic.c:1699-1712`: it `free_irq`s), then `ifconfig eth4 … up` (讀 `rtl_nic.c:4192-4210`: first open calls `rtl865x_init_hw()`), then the same `iperf3` | rides an existing boot |

⚠️ **④ is recorded in this repository as impossible and it is not.**
`docs/KNOWN-ISSUES.md:870` and `:941` say the contrast cannot be taken because
`ifconfig eth4 up` returns `SIOCSIFFLAGS: Device or resource busy`. 量, the
capture that reading comes from — `bench/2026-09-20/X9-eth4.log` — sends
`ifconfig eth4 10.1.1.4 up` with **`rlx0` still up**, which
`bench/2026-09-20/X11-eth4off.log` confirms in the same seating. 量
`notes/nic-driver.md:518-519`, seating 28: with `ifconfig rlx0 down` first, the
handover **worked** — `12: 2 RLX LOPI eth4`, `UP BROADCAST RUNNING`.
`notes/nic-driver.md:986-988` states it correctly (*"cannot be re-measured
**while `rlx0` is bound**"*); `:1428-1430` drops the qualifier and turns a
conditional failure into a property of the driver. **推 that the handover
works; the cell that decides it is three commands.**

## 9. Candidate ② is refuted, at the desk, on captures already committed

`ph_vlanId = 0` can only matter if something consults a VLAN table for these
frames. It does not, and the refutation has four legs, three of them measured.

**① VLAN ingress filtering is OFF on every port, and was off across the fault.**
讀 `AsicDriver/rtl865xc_asicregs.h:2387-2391`: `VCR0` bits 8:0 are
`EnVlanInF_MASK (0x1ff << 0)`, *Enable Vlan Ingress Filtering*, one bit per port
over nine ports. 量 `bench/2026-09-21d/C2-SWPRE.log`, `C4-SWPRE2.log`,
`C8-SWPOST.log` — the three dumps `NET-78` took before `ndo_open`, after it, and
after the failure:

```
r VCR0      4A00 00000000 000001FF 01
```

讀 `rtl819x-switch.c:560-564`, the row is
`r <name> <off> <live> <S0' latched at subsys_initcall> <both><dumb>`. So
**live `0x00000000`** against **`0x000001FF` at `subsys_initcall`**, and
`NET-78` measured all 37 registers byte-identical across the three dumps —
so it was `0` before the fault, during it, and after it.

**② And it was the VENDOR'S OWN PROBE that cleared it, not rlxfw.** 讀
`AsicDriver/rtl865x_asicL2.c:4691`:

```c
WRITE_MEM32( VCR0, READ_MEM32( VCR0 ) & (~EN_ALL_PORT_VLAN_INGRESS_FILTER) );
/* Disable VLAN ingress filter of all ports */ /* Please reference to the maintis bug 2656# */
```

量, the same dumps: `n_dumb 0`, `n_reset 0`, `n_restore 0`, `n_writes 1` —
and the one write is `SIRR`'s `TRXRDY` from the `start` verb
(`bench/2026-09-21d/C1-SW.log` is that cell). **rlxfw's `dumb` verb does write
`VCR0` — the row's `dumb` flag digit is `1`, which is `NET-43`–`NET-45`'s
*2 of 37* — but it never ran in this seating.** The vendor's probe runs at
`device_initcall`, after rlxfw's `subsys_initcall` snapshot, and 量 `FW-31` it
executes on every boot of every rlxfw image.

⚠️ **`rtl819x-nic.c:136` already cites `rtl865x_asicL2.c:4694` and `:4703`
out of that same function.** `:4691` is three lines earlier and was read past.
No conclusion in this repository depended on it; it is recorded because the
next person to open that function should know the whole of it is load-bearing.

**③ In direct mode the driver names the egress ports, so the VLAN member set is
not what decides egress.** 推 — this is the one leg that is not measured. It
follows from §2: `ph_flags = 0x8800` carries neither `PKTHDR_HWLOOKUP` nor
`PKTHDR_BRIDGING`, and `ph_portlist` is the literal mask.

**④ And the frames are not leaving tagged.** 量, across four seatings: the
host's captures decode ordinary untagged ARP and ICMP, and `NET-76` carried
2,450,389 frames out of this driver in one run. If the switch tagged egress
frames with `ph_vlanId`, every one of them would have been an 802.1Q frame
carrying VLAN 0.

🔴 **Refuting ② makes ① stronger, not weaker.** With ingress filtering off on
all nine ports and no lookup bit in `ph_flags`, the only thing deciding where a
frame rlxfw transmits goes is `ph_portlist = 0x3F`.

⚠️ **What this does not say.** It does not say VLAN state is irrelevant to
`NET-78` — the per-port PVIDs are live and not what `subsys_initcall` saw
(量: `PVCR0`–`PVCR4` read `00090009 / 00090009 / 00010008 / 00010001 /
00000009` against a snapshot of `00080008 ×4 / 00000001`, so ports 0–3 carry
PVID 9, port 4 carries 8, ports 5–7 carry 1 and port 8 carries 9). 讀
`rtl865x_asicCom.c:964-970`, the vendor's `rtl8651_clearRegister()` zeroes
`VCR0` and `PVCR0`–`PVCR4`, and `:169-178` is a per-port PVID setter that runs
later — so those values are the vendor's init, arrived at in two stages.
**What is refuted is that `ph_vlanId = 0` on a transmitted descriptor is the
cause; the PVID configuration itself has not been ruled out of anything.**

## 10. The seating this file buys, and the order it has to run in

⚠️ **This is a card DESIGN, not a card.** The card is frozen immediately before
power, under `bench/<date>/`, and `check-predictions` reads its mtime — writing
one now would destroy that evidence. What is below are the constraints that are
expensive to rediscover, recorded because the next seating costs a power cycle.

### The ordering rule, and why it is not a preference

量 `SPEC.md` `NET-75`: in the wedged state the kernel keeps printing and the tty
keeps echoing, but **the shell does not execute** — `echo`, an ash builtin that
forks nothing and touches no `/proc`, returns one line (its echo) instead of
two. 量 the same row: `busybox reboot -f` does not recover it either, because
the shell never runs it. Seating 31 sent 7,489 bytes of ESC and seating 32 sent
7,883, both with no prompt.

🔴 **So a cell that wedges the board ends that boot.** Every wedge belongs at
the END of its boot, and anything that needs a live shell goes before it.

🔴 **And the handover is one-way per boot.** 量 `NET-58`: re-opening `rlx0`
does not re-arm the descriptor bases, and the engine then walks off the ring
and DMAs into arbitrary DRAM. So `eth4` → `rlx0` in the same boot is not
available. `busybox reboot -f` costs **2.407 s** and no power press
(`SPEC.md` `FW-37`), and that is what separates the boots.

### Boot 1 — the vendor baseline

| cell | what | observable, and what refutes it |
|---|---|---|
| `V1` | boot, `ping` both ways, `cat /proc/rtl819x-nic` whole | the pre-state; `n_writes 0` |
| `V2` | `ifconfig rlx0 down`; `cat /proc/interrupts` | **line 12 gone.** 讀 `rtl819x-nic.c:1699-1712`, `nic_ndo_stop()` calls `free_irq(NIC_IRQ, …)`. If line 12 is still there the read did not happen and the rest of boot 1 is void |
| `V3` | `ifconfig eth4 10.1.1.4 up`; `ifconfig eth4`; `cat /proc/interrupts` | `12: n RLX LOPI eth4`, `UP BROADCAST RUNNING`. 🔴 **If it returns `EBUSY` here, with `rlx0` down, then `notes/nic-driver.md:1428-1430` is right and `:518-519` was something else — record it and stop boot 1** |
| `V4` | `cat /proc/rtl819x-nic` with `rlx0` down | 🟢 **rlxfw's `/proc` is now a read-only observer of the vendor's hardware state.** `now_icr`, `rpdcr0_pos`, `rmdcr0_pos`, `tpdcr0_pos` read hardware registers, not driver state, and a `cat` writes nothing (`n_writes` is a separate counter). Whether `rtl865x_init_hw()` re-armed shows as the bases LEAVING rlxfw's `A15B80xx` |
| `V5` | `ping` both ways over `eth4` | the vendor's driver carrying ICMP |
| `V6` | **`iperf3 -c <host>` on the vendor's driver** | see below |
| `V7` | `/proc/rtl819x-nic`, the 37 switch registers, `GDSR0`, host `tcpdump` | taken whatever `V6` did |

**`V6` has three outcomes and all three are worth the seating**, written before
the board is powered:

* **The vendor wedges too** → the fault is not in this driver. `D5` is not
  reachable on this hardware by this method, and `R6-7` writes that with the
  measurement behind it.
* **The vendor survives and gives a number** → there is a platform baseline, a
  single-variable differential, and every later hypothesis becomes an A/B.
* **The vendor survives at about 30 Mbit/s** → § 4's copy cost is excluded and
  `NET-76`'s 29.761 Mbit/s is the path, not the driver's bounce buffer.

### Boot 2 — the candidate `NET-77` left out

`NET-77` narrowed the remaining causes to two: *data actually flowing on an
established connection*, and *`iperf3` the program*. 量, re-reading that row's
own `/proc/net/snmp` numbers, **there is a third and it is perfectly confounded
with the second**: every non-wedging rung is `PassiveOpens`/`OutRsts` — the
board is the server, or refusing — and every wedging run is `ActiveOpens`,
**the board opening an outbound TCP connection**. Four and four, no exceptions.

| cell | what | what it separates |
|---|---|---|
| `W0` | host-side precondition, its own cell: start the listener/generator and **prove it is alive** (`ss -ltn`) | 🔴 `FW-102`: block 35's `T6` was VOID because `nohup … &` inside a heredoc died with its parent. `looprun`'s `S5c` has this shape; the card must too |
| `W1` | board runs `iperf3 -s`, host runs `iperf3 -c` | board = server, real bulk, `iperf3` running. **If it does not wedge, direction is the factor** |
| `W2` | board runs `iperf3 -s`, host pushes with **`socat`** | real TCP data, none of `iperf3`'s protocol. Separates *data* from *the program* |
| `W3` | `cat /proc/net/snmp` whole | every rung reconciled from the board's own side |
| `W4` | **last**: board runs `iperf3 -c` | the known wedge, as the positive control. This cell ends the boot |

⚠️ **Do not plan a `telnetd` bulk ladder.** 量,
`bench/2026-09-21c/PREDICTIONS-B37-block35.md:34-41`: this image has no
`/dev/ptmx` and no `/dev/pts`, so `busybox telnetd` cannot allocate a pty —
`T4` completed a handshake and `T5` had no listener left to talk to. That route
needs a different image.

⚠️ **`cat` is two `read_proc` invocations on this kernel** (`SPEC.md` `FW-64`),
and this image's `ping` ignores `-c`. Both are already recorded; both have
turned a good cell into a wrong number before.

### What this seating does NOT do

It does not add `txd ph2/ph3/ph4` to the dump and it does not set
`-DRTL_DEBUG_NIC_SKB_BUFFER`. Both change `RECIPE_ID`, so they ride one image
together, and that image is not this seating's — **a card that predicts a boot
capture's byte count has to be written against the image that will actually
boot.**

---

## 11. What § 10's seating returned — the baseline exists

Seating 35, 2026-09-21, boot 1. Card
`bench/2026-09-21e/PREDICTIONS-B40-block38.md`, frozen before any cell ran.

### 11.1 🟢🟢 The vendor's driver carries `iperf3` on this board and survives it

`V6` was the cell the seating existed for, and § 10 wrote its three outcomes
before the board was powered. It returned the second **and** the third:

| instrument | figure |
|---|---|
| the board's own `iperf3 -c`, sender side | **31.3 MBytes / 10.34 s / 25.4 Mbit/s**, `Retr 0` |
| the host's `iperf3 -s`, receiver side | **31.3 MBytes / 11.53 s / 22.7 Mbit/s** |
| the host's steady-state 1-second intervals | 25.9 → **26.8 Mbit/s** |

Both ends ran the **same binary** — `iperf 3.1.3`, 252,644 bytes, sha256
`3144db60…` — natively on the board and under `qemu-mips-static` on the host,
which is what `NET-60` requires. Afterwards `V7-PING` was 4 of 4 both ways and
`V7-ALIVE` returned two lines.

🔴 **The pre-registered guess was that the vendor would survive** (§ 2.5 of the
card, on 讀 `NET-79`'s ring depths and never-stop-the-queue contract) and it
held. Had it wedged, the fault would have been below both drivers and every
driver-side candidate in `NET-78` would have died with it.

⚠️ **The two figures are not one figure.** 22.7 Mbit/s is the whole
transaction including setup; 26.8 Mbit/s is the steady state; 25.4 Mbit/s is
the sender's own average over a shorter window. Compared at the same
instrument — the host's receiver side — the vendor's 22.7 sits beside rlxfw's
**23.3 Mbit/s** (`NET-85`), and compared at steady state the vendor's 26.8
sits above rlxfw's 23.2–24.4. **rlxfw reaches 0.87–0.92× of the vendor on this
board**, and that ratio is the thing this file was written to make possible.

### 11.2 🟢 The handover is real, and the reason it was thought impossible is not

| cell | reading |
|---|---|
| `V2-DOWN` | after `ifconfig rlx0 down`, `/proc/interrupts` has **no line 12** |
| `V3-ETH4` | `ifconfig eth4 10.1.1.4 up` → `UP BROADCAST RUNNING`, `Interrupt:12`, and `12: 12 RLX LOPI eth4` |
| `V5` | `ping` 4 of 4 in **both** directions on 10.1.1.4 |

So `docs/KNOWN-ISSUES.md`'s two `EBUSY` rows are refuted **on the device**:
the capture they rest on never ran `ifconfig rlx0 down` first. § 8 ④ of this
file predicted exactly that at the desk one segment earlier, 推; it is 量 now,
and it cost three commands on a boot that was happening anyway.

### 11.3 🟢 The two drivers do not share rings, so boot 1's readings are unambiguous

`V4-NIC` is rlxfw's `/proc` read **while its own device is down** and the
vendor's is up. The three engine position registers had left rlxfw's ring
addresses:

| field | rlxfw up (`V1`) | vendor up (`V4`) |
|---|---|---|
| `rpdcr0_pos` | `A15B8014` | **`A15B2C00`** |
| `rmdcr0_pos` | `A15B8034` | **`A15B0000`** |
| `tpdcr0_pos` | `A15B8044` | **`A1FCA400`** |

讀 `rtl_nic.c:4192-4210`, the vendor's first open calls `rtl865x_init_hw()`,
a full re-init including every descriptor base — and this is that re-init seen
from the other driver's `/proc`. 🟢 The control in the same cells: `n_writes`
is **16 before and 16 after** three `cat`s, while `n_reads` goes 33 → 45, so
rlxfw's `/proc` really is a read-only observer.

### 11.4 What boot 2 onwards did to § 10's ladder

The `W` ladder's first rung wedged the board, which is the strongest of the
outcomes § 2.6 of the card listed, and the rest of the seating is in
`notes/nic-driver.md` § 14. In one line: `NET-77`'s three candidates are all
refuted, the minimal reproducer is **347 inbound frames at 0.5 Mbit/s with no
TCP and no listener**, and the vendor's ring-full contract does not rescue it
because the engine never returns the descriptor — 1,548 OWN-bit reads, zero
recoveries.

---

## 12. The loader's TX path — the third implementation, read end to end

The other two implementations of this engine are the vendor's Linux driver
(§§ 1–9, from source) and rlxfw's. The third is **this unit's own second-stage
loader**, bare metal, no Linux, no NAPI, no interrupts — and it was the only
one nobody had read.

Method is `docs/loader-command-semantics.md`'s, unchanged:

```
mips-linux-gnu-objdump -D -b binary -m mips:3000 -EB \
    --adjust-vma=0x80400000 $W/stage2.bin
```

🟢 **The VMA control holds instruction for instruction**: `0x8040591C`…
`0x80405934` reproduce `docs/loader-flash-write.md`'s quoted `lui v0,0xb800` /
`ori a0,v0,0x1208` / `lui v1,0x800` / `lw` / `and` / `beqz` exactly, so the
addresses below are this unit's.

**The whole NIC surface is five instructions wide.** 量: `lui …,0xb801` — the
CPU-interface block at `0xB8010000` — occurs **5 times** in 12,288 lines.

### 12.1 The send routine, `0x80403CF0`

```c
loader_tx_send(pkt, len)
{
    next = (tx_idx + 1 == ring_count) ? 0 : tx_idx + 1;
    if (next == tx_done_idx) {
        printf("Tx Desc full!\n");          /* 0x8040AC40 */
        return -1;
    }
    memcpy(...);                             /* 0x80406D0C */
    if (ring[tx_idx] & OWN) {                /* 0x80403DAC */
        printf("\nAssertion fail at file");  /* 0x8040AC50 */
        for (;;) ;                           /* 0x80403DC8: j 0x80403DC8 */
    }
    ... build pkthdr ...
    *(u8 *)(hdr + 15) = 63;                  /* 0x80403E58: li v0,63 */
    ring[tx_idx] |= OWN;                     /* 0x80403E80 */
    CPUICR |= TXFD;                          /* 0x80403E88, 1<<23 */
    tx_count++;                              /* 0x8040EAC8 */
    tx_idx = next;
    return 0;                                /* no wait, no poll */
}
```

🟢 **`ph_portlist = 0x3F` is literally `li v0,63 ; sb v0,15(a0)`**, which is
`NET-81`'s reading of this unit's live ring arriving from the code side.

🔴 **The vendor's own bare-metal author treats a stuck descriptor as
impossible.** Not a retry, not a recovery, not a reset — an assertion and a
one-instruction infinite loop. That is the strongest statement available about
how this condition was expected to behave.

### 12.2 The reclaim, `0x80403ED0`, and when it runs

```c
loader_tx_reclaim()
{
    while (tx_done_idx != tx_idx) {
        if (ring[tx_done_idx] & OWN) break;
        tx_done_idx = (tx_done_idx + 1 == ring_count) ? 0 : tx_done_idx + 1;
    }
}
```

量: it has exactly **two** call sites, both inside the NIC service loop at
`0x804023C4`:

```c
loader_nic_service()
{
    CPUIISR = CPUIISR;            /* 0x804023CC-D4: W1C, EVERYTHING, every entry */
    goto check;
loop:
    loader_tx_reclaim();          /* 0x804023F0 */
    handle_rx();                  /* 0x804023F8 -> 0x80402040 */
check:
    if (rx_receive(&buf, &len) == 0) goto loop;   /* 0x80403AB8 */
    loader_tx_reclaim();          /* 0x80402418, once more on the way out */
}
```

So the loader **reclaims on every pass of a polled service loop, whether or
not it transmitted**, and **clears the entire `CPUIISR` unconditionally on
every entry**. rlxfw has no reclaim walk and no done-index at all: it frees
the skb synchronously in `nic_xmit` and learns the ring's state only when it
next transmits.

### 12.3 🔴 The ring depths, and the hypothesis they kill

量 `bench/2026-09-19b/X7-cpufull-a` (`DW B8010000 16`, loader state) together
with `X14-rings-post`, counting `DESC_WRAP` (bit 1) to find each ring's end:

| ring | register | base | depth |
|---|---|---|---|
| RX pkthdr 0 | `CPURPDCR0` | `A040FC70` | **4** |
| RX mbuf | `CPURMDCR0` | `A040FCD0` | **4** |
| TX 0 | `CPUTPDCR0` | `A040FC88` | **4** |
| TX 1 | `CPUTPDCR1` | `A040FCA0` | 2 |

**The loader runs the same four TX descriptors rlxfw does** — and it drives
TFTP transfers of a megabyte at a time, with long gaps between sends, and it
does not wedge. 🔴 **So "four is too shallow" is refuted as the explanation.**
It may still be worth more margin; it is not the difference.

### 12.4 The one configuration divergence this read found

量, loader state: `CPUIIMR = 0x000007F8` — `RX_DONE_IE0..5` (bits 3–8) and
`TX_DONE_IE0/1` (bits 9–10), nothing else. rlxfw runs `0x007E0FFE`: bits 1–11
**and** 17–22, i.e. it additionally unmasks `TX_ALL_DONE`, `MBUF_DESC_RUNOUT`
and all six `PKTHDR_DESC_RUNOUT`. ⚠️ rlxfw matches the vendor's **Linux**
driver here (讀 `rtl_nic.c:10809`), so the loader is the odd one out and this
is a divergence to know about rather than a defect.

### 12.5 🟢 What this read buys: a bench cell that needs no image and no boot

~~量 `looprun`'s `S5c`, every seating: **at the loader prompt the board answers
ARP.**~~ 🔴 **REFUTED on the silicon 2026-09-21 (seating 36), and the correction
is one command.** `S5c` passes *after* `S5`, the rescue, which sends
`IPCONFIG`; 讀 `RUNSHEET.md:566` has said since 2026-08-24 that *the loader
answers the network only after this*, and 量 `tools/looprun.py:345-363` puts
the rescue before `S5c` in the plan. **So no `S5c` reading has ever been taken
on a bare cold boot.** Measured on one: `arping` 5 transmitted / 0 received and
`ip neigh` `INCOMPLETE` three times, **twice** — once with an ESC stream up and
once with the console quiet and nothing holding the port, which is what rules
out the instrument. After `IPCONFIG 10.1.1.1` the same probe reads
`56:0a:01:01:01:e8 REACHABLE`, and bytes 2–5 of that address are `0a:01:01:01`
= 10.1.1.1, so the loader synthesises its MAC from what `IPCONFIG` gave it.
`SPEC.md` `NET-95`.

The corrected sentence: **after `IPCONFIG`**, the loader answers ARP at its
prompt. That is this service loop running, and transmitting, on the same engine
and the same four descriptors.

So the loader is a **test harness that is already on the device**:

> Blast UDP at the board **while it sits at the loader prompt**, exactly as
> `Y1` does to Linux, then ask whether it still answers ARP.

* **It survives** → the engine is fine under this traffic and the fault is in
  rlxfw's software. Every driver-side candidate stays alive and the search has
  a control it has never had.
* **It stops answering ARP** → the fault is below both implementations, rlxfw
  is exonerated, and `R6-5`'s whole framing changes — including whether `D5`
  is reachable on this hardware at all.

🔴 **Either answer is worth more than another driver iteration**, and it costs
no TFTP, no boot and no image: the board is at that prompt after every reset
this project already performs.

---

## 13. What § 12.5's seating returned — the engine is fine, and the fault is above it

量 2026-09-21, seating 36, `bench/2026-09-21f`, card `PREDICTIONS-B41-block39.md`.
One cold power-on at 22:22, no image, no boot, no TFTP.

### 13.1 🔴 The framing had to be corrected before a single frame went out

§ 12.5 said *at the loader prompt the board answers ARP*. It does not, until
`IPCONFIG` has been typed — see § 12.5, corrected in place. Two probes on the
bare cold boot, one with an ESC stream up and one with the console quiet and
nothing holding the port, both read `arping` **0 received** and `ip neigh`
**`INCOMPLETE`**. The second is what rules out the instrument; `RUNSHEET.md:566`
is what named the cause.

### 13.2 🟢🟢 The loader does not stop transmitting, at 16× the dose

`A3` walked the ladder and `A5` held its top for 30 s. Every rung kept ARP
requests going for the whole of the rung, so the TX ring was cycling **during**
the blast and not only asked about afterwards.

| rung | requested | frames | seconds | actual | ARP during | after |
|---|---|---:|---:|---|---|---|
| `A3` 1 | 0.5 Mbit/s | **347** | **8.01** | 0.501 | 8/8 | ANSWERS |
| `A3` 2 | 1.0 | 693 | 8.01 | 1.001 | 8/8 | ANSWERS |
| `A3` 3 | 2.0 | 1,385 | 8.01 | 2.001 | 8/8 | ANSWERS |
| `A3` 4 | 4.0 | 2,768 | 8.00 | 4.001 | 8/8 | ANSWERS |
| `A3` 5 | 8.0 | 5,534 | 8.00 | 8.001 | 8/8 | ANSWERS |
| `A5` | 8.0 | **20,748** | 30.00 | 8.000 | 27/27 | ANSWERS |

🟢 **Rung 1 is `Y5`'s dose and not merely close to it**: `NET-87` records `Y5`
as *347 frames / 8.01 s / 0.5 Mbit/s*, and `tools/netblast.py` carries
`y5-rateladder.py`'s `blast()` unchanged with a self-test (`C1a`–`C1e`) that
re-derives that file's constants from the file and refuses on drift.

🟢 **It is not the assertion path.** `A3-CON` and `A5-CON` are console captures
that send nothing; both are **0 bytes**, so `0x80403DC8`'s
`printf("Assertion fail") ; j self` never ran. 🟢 **And the board never reset**:
`A7-PROMPT` and `S0-catch` hold **0** occurrences of
`Reboot Result from Watchdog Timeout!` while `B1-rz` holds **1**, which is the
positive control that makes those two zeros readings rather than absences.

### 13.3 🟢🟢 And the frames reached the ENGINE, which is the half that makes 13.2 worth anything

Everything in 13.2 is compatible with a host that sent 31,475 datagrams into a
switch that dropped them. `X5`–`X7` close it with the loader's own globals, and
the decode has a second source for every word.

| address | instruction site | what it is | idle control | across one 8 Mbit/s × 8 s rung |
|---|---|---|---|---|
| `0x8040EAC4` | `lw / addiu 1 / sw` at `0x80403B14`, inside `rx_receive` (`0x80403AB8`) | received frames | unchanged | **31,638 → 37,182 = +5,544** against **5,534** sent |
| `0x8040EAC8` | the identical idiom at `0x80403EA0`, inside `tx_send` — § 12.1 already named this one | `tx_count` | unchanged | **103 → 109 = +6** |
| `0x8040EAC0` | reclaim's head, `beq` against `0x8040EABC` = § 12.2's `while (tx_done_idx != tx_idx)` | `tx_done_idx` | unchanged | **3 → 1** |

🔴 **The negative control is the whole reason these are readings**: `X5-globA`
and `X5-globB`, 10 s apart with nothing sent, are **byte-identical**. These
words do not free-run.

🟢 **Three ways, and the residual is accounted for rather than absent.**
+5,544 against 5,534 sent leaves **10**,
and exactly one pre-probe and one post-probe ran inside that bracket, each a
handful of ARP and ICMP frames (推 for the decomposition — no capture of the
wire was taken; 量 for the +10). `tx_done_idx` 3 → 1 is `(3 + 6) mod 4` on the
4-deep ring of § 12.3, so **the reclaim walk retired exactly the six
descriptors `tx_send` queued** — a check the other two counters cannot fake.

⚠️ `CPUIISR` read **`00000000`** at `X4` against `NET-48`'s cold-loader
`80000000`. That is § 12.2's *"clears the entire `CPUIISR` unconditionally on
every entry"* arriving from the silicon side — and it also means this register
**cannot** accumulate run-out evidence under the loader, so it is not available
as an instrument here.

### 13.4 🔴🔴 The single-variable comparison, same power-up, twenty minutes apart

`B1`–`B2` booted `s32a` through `looprun` on the **same power-up** (`S4`'s
watchdog reset, zero power presses) and ran the same generator at the same dose
down the same cable into the same switch port.

| | dose | result |
|---|---|---|
| **loader** | 347 frames, then 31,128 more up to 8 Mbit/s (31,475 total) | **ANSWERS**, every rung |
| **rlxfw** | **347 frames**, 8.01 s, 0.501 Mbit/s | **SILENT** |

`B1-PING` before it was **4/4, 0 % loss**, so the ladder had something to
break. At +16 s the four TX descriptors read `A15B81D1 / 81E9 / 8201 / 821B`
against `81D0 / 81E8 / 8200 / 821A` before — **bit 0 set on all four** — with
`n_tx_stop 1`, `tx_stopped 1`, `n_tx_recovered 0`, and `tx` frozen at **17**
while `rx` kept climbing.

🔴 **So the engine is not the difference. Whatever stops rlxfw is above it**,
and for the first time that sentence rests on a reference implementation
measured on the same silicon within the same power-up rather than on the
absence of an alternative.

---

## 14. The recovery, measured — and it is three calls the driver already has

§ 13.4 leaves the fault above the engine. `R6-5`'s remaining question was
which of two repairs to build: *deeper ring + a real timeout* (if the stall
clears itself) or *detect the stall and re-arm* (if it does not).

### 14.1 🔴 It does not clear itself, over 600 seconds

Four readings after one wedge, each paired with a ping:

| t | `n_irq` | `n_tx` | `n_rx` | txd OWN | `n_tx_recovered` | ping |
|---|---:|---:|---:|---|---:|---|
| before | 10 | 5 | 5 | `0 0 0 0` | 0 | 4/4 |
| +16 s | 377 | **17** | 363 | `1 1 1 1` | 0 | 0/4 |
| +46 s | 383 | **17** | 369 | `1 1 1 1` | 0 | 0/4 |
| +120 s | 389 | **17** | 375 | `1 1 1 1` | 0 | 0/4 |
| +600 s | 395 | **17** | 381 | `1 1 1 1` | 0 | 0/4 |

🟢 **The internal control is in the same columns.** `n_rx` and `n_irq` both
advance **exactly +6** per interval, and exactly one ping (4 ICMP requests plus
2 ARP) runs between consecutive cells. So the receive side is not merely alive,
it is losing nothing, while the transmit side does not move for ten minutes.
`NET-88` bounded recovery on a microsecond scale; this bounds it at 600 s.
`SPEC.md` `NET-99`.

### 14.2 🔴 `SOFTRST` alone is not it, and two facts fell out of finding that

讀 `rtl865xc_asicregs.h:527-548` calls `CPUICR` bit 22 *"Re-initialize all
descriptors"*. Written to a wedged engine through the vendor's
`/proc/rtl865x/memory` — `0xC4400000`, the live value with bit 22 set:

* 🟢 **It self-clears, and it clears `TXCMD` and `RXCMD` with it.** Read back
  `04000000`, on three sources: the vendor handler's own
  `dat 0xc4400000: 0x4000000`, an independent `echo read`, and rlxfw's
  `now_icr`. Nothing in this repository said either of those things.
* 🔴 **It does not touch the OWN bits in the DRAM ring.** All four descriptors
  unchanged, ping still dead.
* 🟢 **And it really reached the hardware**, which is a negative control rather
  than an assumption: with the engine off `n_rx` froze at **387** — it did not
  even count the 6 frames of the ping taken in that window — and resumed
  390 → 396 after `engine on`.

`SPEC.md` `NET-100`.

### 14.3 🟢🟢 `engine off` → `arm` → `engine on` recovers it, twice

讀 `rtl819x-nic.c:2052-2058`: `arm`'s TX loop writes each slot as
`address | WRAP` with **no OWN bit**, which is `NET-72`'s one remaining
candidate. 量, on a **pristine** wedge — fresh boot, ping 4/4, `Y5`'s dose,
dead, nothing else written to the engine:

```
RLXFW-N-ENGOFF
RLXFW-N-ARM=A15B8000   RLXFW-N-ARMR=00000000
RLXFW-N-ENGON=C4000000
```

→ descriptors back to `A15B81D0 / 81E8 / 8200 / 821A`, **ping 4/4, 0 % loss**.
Wedged again at the same dose and recovered again on the same boot:
`n_tx_stop 2`, `n_tx_wake 2`, `tx_stopped 0`, ping 4/4.

🟢 **The queue half is already in the driver, and which code does it is a
reading rather than a guess.** The dump taken after the recovery but *before*
the ping reads `tx_stopped 1` / `n_tx_wake 0`; the one after it reads
`tx_stopped 0` / `n_tx_wake 1`. The host's ARP-for-`10.1.1.3` arrives, and the
level test at `rtl819x-nic.c:1077` — which runs on **any** interrupt, not only
`TX_DONE` — sees the freed ring and calls `netif_wake_queue()` itself.

🔴 **Three things the repair may not be**, each excluded by a measurement
rather than by preference:

* not `ndo_stop`/`ndo_open`: `X16` re-opened an interface that had just
  recovered and **broke it again** (100 % loss, `n_tx_stop` back to 1), which
  is `NET-58` reproduced;
* not `watchdog_timeo`: `NET-55`/`NET-57` measured it dead on this board;
* not `arm` with the engine running: that is `NET-64`'s hard hang, which is
  why `engine off` is first.

`SPEC.md` `NET-101`.

### 14.4 ⚠️ What § 13 and § 14 do NOT establish

* **Why the engine stops.** Nothing here explains it. The repair restores the
  ring; it does not name the mechanism, and `NET-67 殘留` stays open.
* **The run-out mask divergence of § 12.4 is untested, and it cannot be tested
  without an image.** A cell was written to set `CPUIIMR` to the loader's
  `0x000007F8` through the vendor's `/proc` and was **discarded at the desk**:
  讀 `rtl819x-nic.c:1475-1478`, the NAPI-complete path ORs the run-out bits back
  in on every completion, so the write would be undone by the first arriving
  packet — and the read-back cell would have shown a **false green**, because
  `echo read` puts no traffic on the wire.
* **Whether the loader would wedge at a dose above 8 Mbit/s.** The ladder
  stopped there. 8.6 Mbit/s is where `Y1` took rlxfw down, so the loader has
  been tested past that point and no further.
* **The recovery has been measured three times on one board on one evening**,
  twice from a pristine wedge and once from a ring that had also had `SOFTRST`
  written to it. It has never run from inside the driver, because the detector
  does not exist yet.


## 15. What seating 37 returned — the divergence that mattered was not the one this file was chasing

量 2026-09-22, `bench/2026-09-22`, image `s99c`. The driver side is
`notes/nic-driver.md` § 16; what belongs here is what it says about **this
file's comparison**.

### 15.1 🔴 § 12.4's configuration divergence is refuted as the cause of the stall

§ 12.4 found one configuration difference between the loader and rlxfw and
called it *a divergence to know about*. `NET-67 殘留` then promoted it to the
strongest remaining candidate. It is not the cause.

`E1-SET` set `CPUIIMR` to the loader's `0x000007F8` through the new `iimr`
verb. **Two sources agree it took**: `iimr_base 000007F8` (what the driver
believes it armed) and `now_iimr 000007F8` (the register read back). Under that
mask, `Y5`'s dose still stopped the transmit queue **twice** — `n_tx_stop`
24 → 26, `n_recov_fire` 23 → 25.

🟢 **This is the measurement § 14.4 said could not be made without an image,
and the reason it could not is now visible in the result.** 讀
`rtl819x-nic.c`'s NAPI-complete path as it was: it OR-ed the three RX-work
enables back in on every completion, so a mask written through the vendor's
`/proc/rtl865x/memory` would have been undone by the first arriving packet —
and the read-back cell would have read it back unchanged, because `echo read`
puts nothing on the wire. In `1.2` the restore is bounded by `iimr_base`, which
is why the two sources can be compared at all.

⚠️ **The cell has a defect of its own, recorded rather than repaired**:
`recover 1` was left armed, so `netblast`'s ladder reported `ANSWERS` and the
verdict has to be read from `n_tx_stop` rather than from the ladder's own
line. 🟢 The card's four-row discriminator did what it was written for: `n_rx`
kept climbing and `now_iisr` read `00000000`, so this was the TX wedge and not
`bench/2026-09-19b/C58-afterflood2`'s RX-deaf failure, which the same mask
could have reproduced.

### 15.2 🟢🟢 The divergence that DID matter is § 6's, and it is rate-dependent

§ 6 read the vendor's receive path and found it following `pPkthdr->ph_mbuf`
where rlxfw indexes the mbuf ring. Measured on the die, in both modes, sharing
one denominator:

| load | frames | `n_ph_diff` moved by | throughput |
|---|---:|---:|---|
| UDP ladder, 43 frame/s | 1,094 | **0** | — |
| bulk TCP, ~1,500 frame/s | ~141,000 | **~141,000** | 0.06 → **17.0 Mbit/s** |

**So the two implementations differ in a way that costs 250× at the load a
router actually carries, and nothing at the load this file had been using to
reproduce the fault.** 🔴 That is the strongest argument in this document for
reading a second implementation rather than reasoning from one: the difference
was in § 6 from the day it was written, and every experiment since had been run
at a rate where it does not show.

### 15.3 ⚠️ What § 15 does not establish

* Why the pairing decouples at high frame rate. The correlation is two points
  on one board on one evening; the mechanism is unread. `NET-103 殘留`.
* Why the engine stops retiring a TX descriptor. Two candidates died in § 15.1
  and § 16.4 and neither was replaced.
* Whether the loader would show the same pairing behaviour. The loader's
  service loop is polled and its rings are 4 deep, so the comparison is not
  obviously transferable, and it was not attempted.
