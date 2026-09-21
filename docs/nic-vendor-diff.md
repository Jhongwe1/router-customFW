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

rlxfw, 讀 `rtl819x-nic.c:1113-1115`:

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
讀 `rtl819x-nic.c:415` — and `nic_xmit` does not call it. Whether VLAN 0 is a
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

rlxfw: `NIC_TX_DESC 4`, `NIC_RX_DESC 8` (讀 `rtl819x-nic.c:351-352`), chosen so
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

rlxfw puts all three in KSEG1 and copies, 讀 `rtl819x-nic.c:1095-1096`
(TX, `__raw_writeb`) and `:912-914` (RX, `__raw_readb`) — byte at a time,
because 讀 `:823-830`: the buffers are 2 mod 4 and a word-wise copy would be an
unaligned load, which on this core faults rather than trapping to a slow path.

🔴 **This is not a candidate for `NET-78`** — a copy that is too slow does not
make the engine drop frames it has accepted. **It is `D5`'s ceiling.** Per
1,446-byte frame rlxfw issues ~1,446 uncached single-byte bus transactions in
each direction where the vendor issues one cache-writeback over ~91 lines.
量 `SPEC.md` `NET-76`: 29.761 Mbit/s aggregate, 1,290 frames/s each way,
sustained over 1,899.593 s. **Whether that number is the path or the copy is
unknown, and it cannot be known without a reference** — which is what the
`eth4` contrast is for.

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
GPL drop. `rtl819x-nic.c:433-439` calls `ph_flags` *the one field this driver
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
`:604` (the `ph_flags` checksum drop, quoted at `rtl819x-nic.c:131-138`) and
`:650` (the FCS in `ph_len`, quoted at `:1555`). And the register programming
order **is** read — `rtl819x-nic.c:1373` cites `rtl865xc_swNic.c:1306-1384` and
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

rlxfw, 讀 `rtl819x-nic.c:891` and `:908`:

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
`rtl819x-nic.c:1335` — at ring build, `nic_dw_set(nic_rx_ph, i, 0, mb)` writes
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
| ④ | The vendor's `eth4` carries the same load without failing | — | `ifconfig rlx0 down` (讀 `rtl819x-nic.c:1183-1193`: it `free_irq`s), then `ifconfig eth4 … up` (讀 `rtl_nic.c:4192-4210`: first open calls `rtl865x_init_hw()`), then the same `iperf3` | rides an existing boot |

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

讀 `rtl819x-switch.c:508-512`, the row is
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

⚠️ **`rtl819x-nic.c:124` already cites `rtl865x_asicL2.c:4694` and `:4703`
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
| `V2` | `ifconfig rlx0 down`; `cat /proc/interrupts` | **line 12 gone.** 讀 `rtl819x-nic.c:1183-1193`, `nic_ndo_stop()` calls `free_irq(NIC_IRQ, …)`. If line 12 is still there the read did not happen and the rest of boot 1 is void |
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
