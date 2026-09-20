# The CPU-port DMA driver — `rtl819x-nic.c`

**Owner file for `R6-3` and `R6-4`.** Every number about the RTL8196E's CPU
interface — the register block at `0xB8010000`, the descriptor layout, the
interrupt, NAPI, and the `net_device` — lands here first and in `SPEC.md` in
the same commit.

Created 2026-09-19 (seating 28, eighty-eighth segment). Its creation discharges
an obligation `notes/switch-driver.md` § 7 wrote for itself: *"This section is
in the wrong file and says so … It moves the day `R6-3`'s driver note
appears."* § 8 below is that section, moved.

---

## 0. What this driver is, in one paragraph

A built-in Linux 2.6.30 driver that owns the RTL8196E switch core's CPU port:
its four TX descriptor rings, its six RX pkthdr rings and one RX mbuf ring, its
interrupt on LOPI line 12, a NAPI poll, and a `net_device` called `rlx0`. It
ships **inert** — every hardware write is behind a `/proc` verb *and* behind a
runtime unlock, so `n_writes` reading 0 on a boot capture is a measurement and
not a promise. The vendor's Ethernet driver stays in the image and is never
opened; that is a deliberate arrangement and § 1 says why.

---

## 1. Why the vendor's driver stays in the image

It would be natural to remove it — `R6-4`'s DoD even asks for *"my driver bound
and the vendor's **not** loaded"*. **Removing it is the dangerous choice**, and
this is 量 rather than argued:

| state | `CPUICR` | source |
|---|---|---|
| at the loader prompt | `C4000000` | `bench/2026-09-19b/X7-cpufull-a` |
| under Linux, no interface opened | `00000000` | `bench/2026-09-17b` block 26 § 2.4, and `RLXFW-N1` on every boot of this image |

The loader leaves the DMA engine **running**, with RXCMD set and ring bases
pointing at `0xA040FC70`, i.e. physical `0x0040FC70` — memory Linux will hand
out. 讀 `rtl_nic.c:6214-6215`: the vendor's `re865x_probe()` writes
`CPUIIMR = 0` then `CPUICR &= ~(TXCMD|RXCMD)`. **In this image that probe is
the only thing that turns the engine off before the kernel reuses those
pages.**

The other half is the interrupt. 讀 `rtl_nic.c:4227`:

```c
rc = request_irq(dev->irq, interrupt_isr, IRQF_DISABLED, dev->name, dev);
```

`IRQF_DISABLED`, **not** `IRQF_SHARED`, and it is called from `re865x_open()`
— the first `ifconfig up`, not probe. So on an image where no vendor interface
is ever brought up, IRQ 12 is unclaimed. 量: `irq_rc 0` on every boot where
this driver asked for it, and `12: … rtl819x-nic` in `/proc/interrupts`.

⚠️ **What this arrangement can and cannot claim.** It cannot claim the vendor
is absent. It can claim, with three independent measurements, that the vendor
is not carrying the traffic: a non-shared `request_irq` on line 12 **succeeded**
(so the vendor does not hold it), `CPUICR` read `00000000` until this driver
wrote it, and the rings the engine is using are at addresses this driver
allocated and printed. 🔴 **`R6-4`'s DoD is therefore partially met and the gap
is named**: *bound and demonstrably carrying the traffic*, not *the only driver
present*.

---

## 2. The register block — 量 at the loader prompt

`CPU_IFACE_BASE = SYSTEM_BASE + 0x10000` = `0xB8010000`, 讀
`rtl865xc_asicregs.h:491`, whose own comment gives the address, with
`REAL_SYSTEM_BASE 0xB8000000` at `:148`.

🔴 **It is the SYSTEM block, next door to the timer at `0xB8003100`.** It is
not `0xBB800000` (the switch core, where `rtl819x-switch.c` lives) and not
`0xBB000000` (the switch *table* window). Writing `CPUICR` at either would
write into a different peripheral.

量 `bench/2026-09-19b/X7-cpufull-a` and `X8-cpufull-b` — one `DW B8010000 16`,
twice, **byte-identical**, at a cold loader prompt before anything booted:

| offset | symbol | cold loader value |
|---|---|---|
| `+0x000` | `CPUICR` | `C4000000` |
| `+0x004` | `CPURPDCR0` | `A040FC70` |
| `+0x008`–`+0x018` | `CPURPDCR1`–`5` | `00000000` ×5 |
| `+0x01C` | `CPURMDCR0` | `A040FCD0` |
| `+0x020` | `CPUTPDCR0` | `A040FC88` |
| `+0x024` | `CPUTPDCR1` | `A040FCA0` |
| `+0x028` | `CPUIIMR` | `000007F8` |
| `+0x02C` | `CPUIISR` | `80000000` |
| `+0x030`–`+0x038` | `CPUQDM0`–`5` | `00000000` ×3 words |
| `+0x03C` | — | **`0000206F`**, unnamed in the header |
| `+0x060` | `CPUTPDCR2` | `A040FCB0` |
| `+0x064` | `CPUTPDCR3` | `A040FCC0` |
| `+0x068` | — | **`007F07F0`**, unnamed |

**Two reads back to back were byte-identical over all sixteen words.** That
settles a question `bench/2026-09-17b` block 25 explicitly refused to ask —
*"an interrupt-status register whose read semantics are unknown here, and
`NET-11`'s `PSRP` bit 8 is this project's own precedent for a status bit
consumed by reading it"*. 量: **`CPUIISR` is not read-to-clear.** ⚠️ The
narrow claim is that the whole block is stable across two consecutive reads;
it does not prove that no bit anywhere in it is read-sensitive at a value
this die did not hold at the time.

🟢 **Two decodes with no residue.** `CPUIIMR = 0x000007F8` is exactly
`RX_DONE_IE_ALL (0x3f<<3)` | `TX_DONE_IE_ALL (0x3<<9)`. `CPUIISR = 0x80000000`
is exactly `LINK_CHANGE_IP`. The second explains a reading that had been
sitting in two different states: the same value appears at the loader prompt
and under Linux because W1C bits do not decay, and nothing had written it back.

⚠️ **The loader's `0x7F8` and this driver's `0x7FE` differ by bits 1 and 2, and that is deliberate.** `0x7FE` = `0x7F8` \| `TX_ALL_DONE_IE_ALL (0x3<<1)`. The loader asks to be told when ONE TX descriptor completes; this driver also asks to be told when the whole TX ring has drained. Every `now_iimr 000007FE` in §§ 4 and 6 is that value and no other.

🟢 **`CPUTPDCR2`/`3` were predicted before they were read.** `X9` dumped the
loader's DRAM and found **four** ring structures at `A040FC88`, `A040FCA0`,
`A040FCB0` and `A040FCC0`, where the header declares only two TX bases in the
contiguous range. `X11` then read `0xB8010060` and got `A040FCB0 A040FCC0`.
**The ring census closes from the memory side and the register side
independently.**

🔴 **Do not use the header's `CPUTPDCR(idx)` macro** (`:505`). TX bases are
non-contiguous, so it resolves idx 2 to `0xB8010028` = `CPUIIMR` and idx 3 to
`0xB801002C` = `CPUIISR`. 量: both indexed macros have **zero** call sites in
the whole vendor tree, so the vendor never steps on it — the landmine is live
only for someone who writes the helper the macro looks like an invitation to
write. This driver spells the two out.

⚠️ **Every value in the header rests on ONE Realtek file copied three times.**
量: `md5` of the CPU-interface region of `rtl865xc_asicregs.h` is
`3efda24f9606bdf037ecb6a11b0fe7e7` in all three GPL drops. And the draft
datasheet has **nothing**: zero hits for `CPUICR`, `CPUIISR`, `CPUIIMR`,
`CPURPDCR`, `CPUTPDCR`, `CPURMDCR`, `SWINTSET`, `LBMODE`, `TXFD` or
`BUSBURST`, and zero occurrences of `B801` anywhere in an 11,467-line text
extract. §11 "CPU Interface (NIC)" is a feature list. **This is materially
weaker footing than `REG-35` or `WDT-1` had**, which is why § 3 was measured
on the die rather than transcribed.

---

## 3. The descriptor layout, closed at the loader prompt before any driver ran

`R6`'s named failure mode is *`OWN`-bit write ordering and big-endian
descriptor fields*, and the plan's own 否證 ① is *frames go out and none come
back* — a symptom that is expensive to diagnose from the outside. It was
closed from the inside first, at zero cost, using a step the seating had to
take anyway.

### 3.1 The method

`X9`/`X10` dumped the loader's live rings and descriptors at a **cold** loader
prompt. A 1,076,224-byte TFTP upload was then pushed through the loader's own
RX path — `looprun` S6, which the seating needed in order to load an image at
all. `X13`/`X14` read **the same two windows again**. The before and the after
are the same loader session; nothing was reset between them.

### 3.2 The ring

A ring entry is **one 32-bit word**: `descriptor_address | OWN(bit 0) |
WRAP(bit 1)`. Pointer is bits 31:2, so 4-byte alignment and nothing stronger.

**OWN = 1 means the SWITCH CORE owns it.** 量 on this die: the loader's idle
RX rings hold entries with bit 0 **set** and its idle TX rings hold entries
with bit 0 **clear**. An idle receive ring is owned by the hardware (waiting to
fill it); an idle transmit ring is owned by the CPU (nothing to send). That
reading is anchored to a path known to work, because the loader's TFTP
demonstrably functions. 讀 agrees: `rtl865xc_asicregs.h:549-554` defines
`DESC_RISC_OWNED (0<<0)` and `DESC_SWCORE_OWNED (1<<0)`.

### 3.3 The transition, measured

| | cold (`X9`) | after 1 MiB TFTP (`X14`) |
|---|---|---|
| RX pkthdr ring entry 1 | `A040FDF1` | **`A040FDF0`** |
| RX mbuf ring entry 1 | `A040FF49` | **`A040FF48`** |
| `CPURPDCR0` | `A040FC70` | **`A040FC78`** (+8 = 2 entries) |
| `CPURMDCR0` | `A040FCD0` | **`A040FCD8`** (+8 = 2 entries) |
| `CPUTPDCR0` | `A040FC88` | **`A040FC8C`** (+4 = 1 entry) |
| `CPUIISR` | `80000000` | **`00000000`** |

🟢 **The pkthdr ring and the mbuf ring move together, at the same index.** That
is the pairing proven rather than assumed.

🟢 **`NET-32` is measured directly.** Those registers hold the engine's
**current position**, not the base: at a cold prompt `CPURMDCR0` reads exactly
the base, and after traffic it has advanced by whole 4-byte entries.
🔴 **Program one as a base and the engine starts mid-ring.**

🔴 **The loader's network path clears `CPUIISR`.** The latched `LINK_CHANGE_IP`
was gone after the transfer. Something in the loader's TFTP code writes it
back; nothing in this project had looked.

### 3.4 The fields

Descriptors are **24 bytes** — every pointer in every ring is 0x18 apart, in
both directions, in all four rings. 🔴 **The header's own comment
"Each pkthdr is exactly 32 bytes" is wrong**, and `SPEC.md` `NET-38 殘留`
carried a 推 that the running kernel uses 32. The stride on this die is 24 and
the compiled `sizeof` under `CONFIG_RTL_8196E` is 24.

`struct rtl_pktHdr`, big-endian, first-declared bitfield in the most
significant bits:

| bytes | field | measured value |
|---|---|---|
| 0–3 | `ph_mbuf` | points at the paired mbuf descriptor; the mbuf points back |
| 4–5 | `ph_len` | **includes the 4-byte FCS** |
| 6 hi | `ph_queueId` | 0 |
| 6 lo | `ph_extPortList` | **8** = `PKTHDR_EXTPORTMASK_CPU` on a CPU-delivered frame |
| 7 | `ph_srcExtPortNum` | |
| 12–13 | `ph_flags` | **`0x80E3`** loader-received, **`0x8063`** Linux-received, **`0x8800`** on TX |
| 15 | `ph_portlist` | RX: source port (**3**). TX: destination mask (**`0x3F`**) |
| 16 b30–28 | `ph_txPriority` | |
| 16–17 b27–16 | `ph_vlanId` | **8** under the loader, **9** under Linux |
| 18–19 | `ph_flags2` | |

`struct rtl_mBuf`, ASIC-visible part:

| bytes | field | measured |
|---|---|---|
| 0 | `m_next` | 0 |
| 4 | `m_pkthdr` | back-pointer |
| 8–9 | `m_len` | |
| 10–11 | `m_flags` | **`0x009C`** in every descriptor in every ring |
| 12 | `m_data` | |
| 16 | `m_extbuf` | equals `m_data` |
| 20–21 | `m_extsize` | **`0x0800` = 2048** |

🟢 **The 2048-byte mbuf is confirmed THREE ways that share nothing**:
`CPUICR[26:24] = 4` = `MBUF_2048BYTES`; the `0x0800` in `m_extsize`; and the
data pointers `A040FF9A`, `A041079A`, `A0410F9A`, `A041179A` being **exactly
0x800 apart**.

🟢 **`ph_flags 0x80E3` decomposes with no residue** into `PKTHDR_ASICHOLD` |
`PKT_MCAST` | `PKTHDR_BRIDGING` | `PKTHDR_HWLOOKUP` | `CSUM_IP_OK` |
`CSUM_TCPUDP_OK`, and `0x8063` is the same without `PKT_MCAST`. `ph_vlanId 8`
is `NET-04`'s WAN vid under the loader and 9 is the LAN vid under Linux, which
is `PVCR` having been reconfigured between the two states.

⚠️ **The buffers sit at `…9A` — 2 mod 4.** That is the two-byte reserve which
makes an IP header land 4-byte aligned behind a 14-byte Ethernet header. It is
**not** a detail this driver would have arrived at by reasoning, and it has a
cost: a word-at-a-time copy out of such a buffer is an unaligned load, which on
this core faults rather than being slow. Every copy in this driver is
byte-wise for that reason, and making it fast is an `R6-5` question with a
number attached.

### 3.5 Why no C bitfields

`struct rtl_pktHdr` is C bitfields with **no endian conditional** (量,
`grep -c ENDIAN common/mbuf.h` = 0). Its layout is an *unstated ABI
consequence* of what this compiler does with bitfields on a big-endian target.
Copying it would make the driver's correctness depend on a property no source
file states, and that property is exactly what 否證 ① is about. Every field in
`rtl819x-nic.c` is an explicit shift and mask, so a descriptor it builds can be
checked against a `DW` hexdump by eye.

---

## 4. The `R6-3` ladder

Each rung has an observable taken before the next was attempted.

### Rung 0 — the software interrupt: 🔴 REFUTED, with a positive control

`CPUICR` bit 20 `SWINTSET` was written with the **engine on** (`C4000000`),
the **mask open** (`000007FE`), this driver's ISR installed on line 12 and
`/proc/interrupts` showing it. `n_irq` stayed **0**; line 12 stayed **0**;
`n_writes` moved 14 → 15, so the write happened.

Seating 27 (`SPEC.md` `NET-47`) refuted this with the engine **off** and the
mask **closed**, and left three candidates: the engine must be on, the mask
must be open, or bit 20 is not `SWINTSET` on this part. **This seating closes
the first two**, and the control is in the same boot: rung 1 delivered a real
interrupt through the same line, the same mask, the same ISR, minutes later.

讀 supports it: 量, `SWINTSET`, `SOFTRST` and `STOPTX` each have **exactly one
grep hit in the whole vendor tree — their own `#define`**. No vendor code ever
writes any of the three, so nothing in the GPL drop shows they do what their
comments say.

🔴 **`/proc/interrupts`'s ` SW: 0` line is NOT evidence here.** 讀
`arch/rlx/kernel/irq.c:176-180,224`: `cnt_swcore` and its four siblings are
`extern int` owned by the **vendor's** ISR, which never runs in this
arrangement. A counter that cannot move is not a measurement.

⚠️ And there is no pending bit to look for: 量, `rtl865xc_asicregs.h` defines
no `SW_INT_IP`. `NET-38 殘留 ①`'s 推 that it is bit 0 has **no source behind
it**.

### Rung 1 — loopback: 🟢

`CPUICR |= LBMODE` gave `now_icr C4080000`, the predicted value. One frame
transmitted; `rx_len 60` against a predicted 60 (64 minus FCS); and

```
rx_bytes FFFFFFFFFFFF 02524C584657 88B5 524C5846572D4E494320 30 4B4C4D4E4F…
```

— broadcast, the driver's locally-administered source, EtherType `0x88B5`,
ASCII `"RLXFW-NIC "`, sequence digit `0`, then the `0x40 + (k & 0x3F)` filler.
Byte for byte the frame the driver wrote. All three position registers advanced
one entry; `rxd0` went `A1560051` → `A1560050`.

🟢 **`n_irq 1`.** That is what settles rung 0.

### Rung 2 — one-way TX: 🟢

Two frames, both captured on the workstation, with payload sequence digits
`1` and `2` (the loopback frame having been `0`). **Three independent
sources**: the driver's `n_tx`, the sequence digit inside the payload, and the
host's capture.

### Rung 3 — RX: 🟢

Seven frames — four host-generated `0x88B5` broadcasts and three broadcast
ARPs. `n_rx` 1 → 8, exactly +7. The decoded frame is an ARP request with
sender `fc:19:28:61:84:c9` (the workstation adapter's own MAC) and target
`0A010101` = 10.1.1.1.

### Rung 4 — NAPI's mechanism: 🟢

Across the masked poll, `n_irq` stayed at **15** (mask down), `n_rx` went
**8 → 13**, and `n_writes` moved by exactly **3** — mask down, W1C, mask up.
Then a second burst took `n_irq` **15 → 20**: **the restored mask really
re-arms**. That is the race NAPI exists to close and the only part of it that
fails silently.

### The three-state control

`/proc/interrupts` has **no line 12** before `irqon`; a line
`12: … RLX LOPI rtl819x-nic (0x20)` during; and **no line 12** after `disarm`.
`RLX LOPI`, not the ICTL cascade `R5-3` used at line 25 — which
`notes/switch-driver.md:438-442` predicted.

---

## 5. `R6-4` — the `net_device`

`rlx0`, `HWaddr 02:52:4C:58:46:57`, registered by a verb and not at boot.

```
64 bytes from 10.1.1.3: icmp_seq=2 ttl=64 time=1.62 ms
4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 1.374/1.810/2.462/0.404 ms
10.1.1.3 dev enxfc19286184c9 lladdr 02:52:4c:58:46:57 REACHABLE
```

Board → host is 4/4 as well, at the board's 10 ms clock granularity.

Counters reconcile exactly: `n_rx 5` / `n_tx 5` (one ARP plus four ICMP each
way), `n_napi_poll 5` / `n_napi_complete 5`, and `nd_stats rx 5/452 tx 5/452` —
4 × 98 + 60 = **452** to the byte.

### 5.1 The MAC address is a containment decision

This unit's real address lives in `H601`, whose **content** may not enter this
repository — not even its digest. A driver that read it would put this
device's identity into every capture from here on. So the address is fixed and
locally administered: `0x02` plus ASCII `"RLXFW"`.

🟢 That converts a limitation into `R6-4`'s own DoD requirement, which asks for
a **positive** discriminator rather than the vendor's absence. An address no
Realtek OUI can contain, on an interface named `rlx0` beside the vendor's
`eth0`…`eth7`, is exactly that, and the host's ARP table holds it.
⚠️ The limitation is still real: a shipped firmware must present the address on
the label, and reading `H601` safely is a separate problem this file does not
solve.

### 5.2 `SIRR`'s `TRXRDY` is necessary — an A/B on one boot

讀 `rtl865x_asicCom.c:1360`, `TRXRDY` is set in `rtl865x_start()`, which is
called only from `ndo_open` — never, in this arrangement, by the vendor.

Seating 28's first `R6-4` boot set it **before** testing, so whether it was
needed was a confound. The next boot resolved it, holding everything else:
same boot, same interface, same address, same driver state, **one variable**.

| | ping | `n_rx` | neighbour |
|---|---|---|---|
| `TRXRDY` clear | 0 of 4 | 0 | INCOMPLETE |
| `TRXRDY` set | 4 of 4 | 5 | REACHABLE |

🟢 **So the vendor's probe alone is not enough**, and `rtl819x-switch.c`'s
`start` verb is a precondition for any traffic, not a tidy-up.

### 5.3 A correction to what `J` leaves behind

`bench/2026-09-19b/C23-swstate` reads `PCRP0` live `007F0039` against a
`subsys_initcall` snapshot of `007F0038`. Bit 0 is `EnablePHYIf`
(`rtl865xc_asicregs.h:1258`). So it is **clear** when `rtl819x-switch.c`
latches slot 0 and **set** by the time Linux is up — i.e. the vendor's
**probe** re-enables the PHY interfaces, not `ndo_open`. The carried-forward
note that a payload entered by `J` inherits five disabled PHY interfaces is
true of the loader hand-off and does **not** survive the vendor probe.

---

## 6. The load test, and a defect the driver still has

A single flood ping: **5,979 of 5,980** round trips in 4.843 s, 0.0167 % loss,
rtt 0.626/0.782/14.441/0.205 ms. `n_irq 11984` against `n_tx 5992` + `n_rx
5992` — **exactly two interrupts per round trip**. `n_skb_fail 0`,
`n_irq_spurious 0`, drops 0/0.

⚠️ **That is a latency and reliability reading, not a throughput reading.**
Flood ping runs at `pipe 2`; the offered load was nowhere near the link. `R6-5`
owns throughput.

### 6.1 A predicted failure that did not fire

Pre-registered before the flood: `nic_xmit` calls `netif_stop_queue()` when the
engine still owns the next TX descriptor and **nothing in this driver ever
calls `netif_wake_queue()`**, so the first time the offered load outruns the
engine, TX should stop permanently.

量: `n_xmit_busy 0`, both floods. **The defect is real and this load never
reached it** — four TX descriptors were never exhausted at `pipe 2`. Carried
forward with its own refutation condition: a load with a real window (an
`iperf3` stream, `R6-5`) should reach it, and if `n_xmit_busy` moves while the
interface keeps working, the analysis above is wrong.

### 6.1a What the driver actually sustains

量 `bench/2026-09-19b/L2-after` and `M7-after` — four concurrent floods at
1400 bytes, on cold-booted hardware, on BOTH images:

| | `r6nic3` (with run-out enables) | `r6nic2` (without) |
|---|---|---|
| frames each way | 7,466 | 7,539 |
| bytes each way | 10,755,068 | 10,864,442 |
| loss | **0.0536 %** | **0.0531 %** |
| rtt min/avg/max | 1.29 / 3.16 / 14.6 ms | 1.45 / 3.13 / 6.4 ms |
| `n_napi_poll` / `n_napi_complete` | 476 / 12 | 478 / 9 |
| `n_xmit_busy`, `n_skb_fail`, `n_irq_spurious`, drops | all 0 | all 0 |

≈ **1.88 MB/s each way** over 5.79 s. ⚠️ Still ping-bound — each flood waits
for a reply — so it is a floor on what the path can do and not a throughput
measurement. `R6-5` owns that.

🟢 **`n_napi_poll 476` against `n_napi_complete 12` is NAPI doing its job**:
the poll is hitting its budget of 16 and staying scheduled, so it drains
~15.7 frames per invocation instead of taking an interrupt per frame.

### 6.2 A failure that did fire — and a diagnosis this seating REFUTED

Four concurrent floods at 1400 bytes: ~65 % loss and then a **permanently deaf
interface**. `bench/2026-09-19b/C58-afterflood2`:

```
now_iisr  00020000     PKTHDR_DESC_RUNOUT_IP0, latched
now_iimr  000007FE     and bits 17-22 are NOT in the mask
rxd0/rxd1 OWN clear, len 1446, unharvested;  n_rx 6411 > n_tx 6154
```

**The diagnosis written at the time**: the RX pkthdr ring ran out → the engine
latched the run-out → the mask omitted it, so no interrupt fired → NAPI never
ran → nothing was harvested or refilled. The supporting observation is real
and stands: the ISR W1Cs everything it reads, and bit 17 was **still set at
rest**, which proves the ISR had not run since.

It reads like the vendor's constant carrying knowledge its source does not
explain — `CPUIIMR = 0x807E01FE`, of which `0x007E0000` is exactly the field
this driver had dropped.

🔴🔴 **THAT DIAGNOSIS IS REFUTED, AND THE EXPERIMENT BUILT TO PROVE IT IS WHAT
KILLED IT.** The obvious comparison — C58 (unfixed, wedged) against L2 (fixed,
healthy) — has **two** variables, because a cold power cycle happened between
them. So the unfixed image `r6nic2` was reloaded onto the *same cold-booted
hardware*, with no power cycle, and given the identical flood: `M7-after`,
**7,539 frames at 0.0531 % loss, survived a 5-packet HOST-side `ping -c 5` afterwards at 0 % loss**, with `now_iimr 000007FE` —
the mask that supposedly caused the wedge. § 6.1a's table is the two side by
side and they are statistically indistinguishable.

**So the mask never caused anything.** The wedge was switch/PHY ingress state,
which § 6.4 had already localised with the vendor's own driver as the control,
and the cold power cycle is what cleared it. What survives from C58 is a set of
readings about a *wedged* machine — a latched run-out, an ISR that had stopped
running — which are symptoms of the stall and not its cause.

⚠️ **The `PKTHDR_DESC_RUNOUT`-is-a-level-condition reading also loses its
force.** It rested on `ndo_open` W1Cing `CPUIISR` while an `ifconfig down`/`up`
left bit 17 set — but on wedged hardware the ring genuinely was starved, so
re-latching is equally explained by the hardware fault. Recorded as
**undetermined**, not as established.

### 6.3 The fix stays, and what it may be claimed to do

`rtl819x-nic.c` carries `NIC_IE_PKTHDR_RUNOUT | NIC_IE_MBUF_RUNOUT` in the
mask, schedules NAPI on `NIC_IP_RX_WORK` rather than RX-done alone, and W1Cs
the run-out before unmasking. Image `r6nic3`, `RECIPE_ID 7fe2f8c3`, boot
capture 1,874 bytes as predicted, `RLXFW-ID0` printed by the board.

**It is kept**, because the vendor sets those bits and a descriptor run-out
that raises no interrupt is a real hazard whatever happened here.
🔴 **It may NOT be claimed to have fixed anything.** 量: with it, 0.0536 %
loss; without it, 0.0531 %; `seen_iisr` carries no run-out bit in either run,
so the path it adds was **never exercised**. It is an untested guard.

⚠️ Two intermediate readings also came out negative and are recorded so they
are not re-derived: a three-state A/B through the vendor's
`/proc/rtl865x/memory` on the wedged machine — `0x000007FE`, `0x007E07FE`
(bit 11 cleared) and `0x007E0FFE` — gave `n_rx 0` in all three, so
`MBUF_DESC_RUNOUT_IE`'s bit-11/bit-16 asymmetry is **not** implicated and the
suspicion against it is withdrawn.

### 6.4 The fault was below both drivers

Isolation, in order:

1. **TX works.** Two raw `tx` verbs; the host captured both frames verbatim.
2. **Interrupts work.** `n_irq 2`, `last_iisr 00003206`, `/proc/interrupts`
   line 12 = 2 — two TX-done for two transmits.
3. **The host transmits.** `tcpdump` on the workstation saw all four
   `0x88B5` frames and three ARP requests leave; `TX: 15004 packets, 0 errors,
   0 dropped, 0 carrier, 0 collsns`.
4. **The board's port has link.** `PSRP3` live `000000F9`, bit 4 `LinkUp` set.
5. 🟢🟢 **The vendor's own driver cannot receive either.** `ifconfig rlx0 down`
   released IRQ 12, `ifconfig eth4 10.1.1.4 up` took it —
   `12: 2 RLX LOPI eth4` — and `eth4` came up `UP BROADCAST RUNNING`, sent
   **2** packets and received **0**.

**So the fault is not in this driver.** It is switch or PHY ingress state that
a watchdog reset did not clear, with the vendor's driver as the control.

6. 🟢🟢 **And a cold power-on clears it.** One power press, then the same
   image, the same verbs, the same address: **4 of 4, 0 % loss,
   rtt 1.246/1.639/2.069/0.295 ms**. The loader's own discriminator confirms
   it was cold — `Reboot Result from Watchdog Timeout!` is printed after every
   watchdog reset and was **absent** from this boot banner.

**`FW-37` said `busybox reboot -f` resets this board, and it does — it is a
watchdog bite. This seating narrows that: it resets the CPU, and it does NOT
restore the switch's ingress path from this state.** The mechanism is
unidentified; only its location and its remedy are measured.

⚠️ Port 3 is `eth4`: the boot log's `Member port` field is a **bitmask** —
`eth0 0x1` = port 0, `eth2 0x2` = port 1, `eth3 0x4` = port 2,
`eth4 0x8` = port 3, `eth1 0x10` = port 4 — and every frame received in this
seating carried `ph_portlist 3`.

---

## 7. Instrument findings this seating produced

* 🔴 **This image's busybox has no `grep` and no `killall`.** 量: three probe
  cells returned `/bin/sh: grep: not found` and were **blind**, printing a
  clean `rc=0`. `FW-46`'s family, and the reason `tools/imgprocs.py` exists:
  every command a card types must be checked against the image first.
  Filtering belongs on the host, where the instruments are.
* 🔴 **`ping` on this image defaults to 4 packets.** That is why `FW-46`'s
  *"`ping` ignores `-c`"* was subtle for so long — `ping -c 4` and plain `ping`
  produce identical output, so the bug was invisible at the value everyone used.
* ⚠️ `rlxfw_mark()` interleaves character-by-character with ash's echo
  (`FW-47`), visible in almost every verb cell here; the marks are present and
  a naive `grep` for them would miss them.

---

## 8. The CPU interface's control bits (`NET-38`) — moved from `notes/switch-driver.md` § 7

🔴 **THREE readings in the moved text are refuted by the seating that moved it, not two.** The stub left in `notes/switch-driver.md` names two — `SWINTSET`, and the 24-vs-32 pkthdr stride. The third is this section's *"the interrupt does not go through the ICTL cascade … the vendor's NIC driver owns IRQ 12"*: the cascade half is confirmed (§ 4), and the ownership half is **refuted** by § 1 — 讀 `rtl_nic.c:4227` puts the vendor's `request_irq` in `re865x_open()`, not probe, and 量 `irq_rc 0` says line 12 was unclaimed. A fourth is weakened rather than refuted: the 推 that `CPUIISR` bit 0 is the software-interrupt pending bit has, per § 4, no source behind it at all. **The stub's count of two is wrong and this line is the correction; the moved text below is still not edited.**

**Moved here verbatim from `notes/switch-driver.md` § 7 on 2026-09-19**, which is the day that section said it would move: *"It moves the day `R6-3`'s driver note appears."* The subheadings are renumbered 7.x → 8.x and nothing else in the text is changed — including the readings it makes that later sections of this file went on to refute, which are marked where they are refuted and not edited here.


**This section is in the wrong file and says so.** It belongs to `R6-3`'s NIC
driver, which does not exist yet, and this project's convention is that a
finding lands in an owning file in the same commit — not that it waits for the
right file to be created. It moves the day `R6-3`'s driver note appears.

`CPU_IFACE_BASE = 0xB8010000` (讀 `rtl865xc_asicregs.h:491`, whose own comment
gives the address). `CPUICR` is at `+0x000`.

### `CPUICR` control bits, 讀 `:527-548`

| bit | name | |
|---:|---|---|
| 31 / 30 | `TXCMD` / `RXCMD` | enable TX / RX |
| 29:28 | bus burst | `32WORDS` is 0 |
| 26:24 | mbuf size | `MBUF_2048BYTES` is `(4<<24)` |
| 23 | `TXFD` | notify TX descriptor fetch |
| 22 | `SOFTRST` | *"Re-initialize all descriptors"* |
| 21 | `STOPTX` | |
| **20** | **`SWINTSET`** | *"Set software interrupt"* |
| **19** | **`LBMODE`** | *"Loopback mode"* |
| 18 | `LB10MHZ` **and** `LB100MHZ` | 🔴 **two names, one bit** (`:543`, `:544`) — nothing says which is right |
| 17 / 16 | `MITIGATION` / `EXCLUDE_CRC` | |

🟢 `TXCMD|RXCMD|BUSBURST_32WORDS|MBUF_2048BYTES` = **`0xC4000000`**, and
`SPEC.md` `NET-32` 量 exactly that on this die. The arithmetic closes with no
residual, which is a free confirmation of this field map.

### 🟢🟢 `SWINTSET` puts a rung BELOW the plan's first, and it costs nothing

讀 `plan/router-rebuild-plan.md:1416`, the plan's checkpoint ladder is
*loopback → 單向 TX → RX → NAPI，不要跳*. Writing `SWINTSET` raises the NIC's
interrupt **with no ring, no descriptor, no PHY and no cable**.

That matters because of what it separates. From outside, *loopback does not
work* and *my interrupt never arrives* are the same observation — and so are
three other failures. A rung that exercises only the interrupt path removes one
of them before the descriptor code is ever written.

### 🔴 And there is no software-interrupt STATUS bit in any source

量: `grep -n 'SWINT\|SW_INT\|SOFT_INT'` over the whole header returns **one
line**, `:541`, which is `SWINTSET` itself. The `CPUIISR` bit list occupies
1, 2, 3–8, 9, 10, 16, 17–22, 23, 24, 25–30 and 31 — **bit 0 is the only
unassigned bit.** 推 that it is the one; that is an inference and not a reading.

🟢 **So the first rung is a DISCOVERY cell rather than a pass/fail**: read the
whole `CPUIISR` word, write `CPUICR \|= SWINTSET`, read it again — whichever
bit changed is the pending bit, and that names something no source in this
project documents.

⚠️ **`CPUIIMR` must not be touched.** With the mask closed no interrupt fires,
so the vendor's handler never runs, so its
`REG32(CPUIISR) = REG32(CPUIISR)` ack never clears the bit. That is exactly
`SPEC.md` `IRQ-09`'s shape — the vendor's read-modify-write on a
write-1-to-clear register clearing pending bits belonging to drivers it has
never heard of — and the masked-observation strategy has already held twice on
this device (`IRQ-08`, `IRQ-09`).

⚠️ **Whether `SWINTSET` self-clears is undetermined**, so the cell reads
`CPUICR`, sets the bit, and writes the original value back.

🔴 **The interrupt does not go through the ICTL cascade.** 讀: the NIC is
IRQ 12 = LOPI 4 and needs **both** `GIMR` bit 15 (`BSP_SW_IE`) and
`IRR1[31:28]`. `R5-3`'s timer went through the cascade at line 25, so none of
that experience carries across. ⚠️ And the vendor's NIC driver owns IRQ 12, so
a driver of mine cannot `request_irq` it unshared — which is a second reason
the first rung is a polled read rather than a handler.

### 8.1 What a minimal ladder actually touches, and why `ph_queueId` can wait

量 2026-09-17, `grep -ran` over the whole vendor Ethernet tree:

| field | hits | |
|---|---:|---|
| `ph_queueId` | **1** | its own declaration, and nothing else |
| `ph_mbuf` | 50 | control |
| `m_data` | 28 | control |
| `m_len` | 14 | control |
| `ph_len` | 11 | control |
| `ph_flags` | 10 | control |
| `ph_extPortList` | 10 | control |

🔴🔴 **That refutes an argument this segment made and nearly acted on.** The
argument was: *the vendor's driver works on this silicon, therefore the layout
its compiler produced equals the layout the hardware expects, therefore copying
the declaration is safe without knowing any absolute bit position.*

Steps one, three and four hold. **Step two fails exactly on `ph_queueId`**:
"the driver works" constrains only the fields the working path **touches**, and
nothing touches that one. Copying the declaration would inherit a bit position
**no code has ever exercised** — the header's `/* bit 2~0 */` comment and the
MSB-first allocation disagree, and no execution has ever arbitrated between
them.

🟢 **But the useful answer is that it does not matter yet.** A minimal RX/TX
ladder touches **zero bitfields**:

* **RX** — the ring word (`OWN`/`WRAP`), `ph_mbuf` @0, `ph_len` @4
  (⚠️ minus 4: the ASIC counts the FCS), `m_data` @12, and the mbuf ring word.
* **TX** — adds `m_len` @8, `m_extbuf` @16, `m_extsize` @20,
  `ph_portlist` @15, and `CPUICR |= TXFD`.

All naturally-aligned scalars. So `R6-3`'s first rungs can be written and run
before the bitfield question is settled, and settling it is `R6-4`/`R6-6` work
rather than a blocker.

### 8.2 🔴 The GPL drop's `mbuf.h` is a REDUCED copy

量: `common/mbuf.h:186-208` defines `PKTHDR_PHUNNUMBER_SET/CLEAR/TEST`, all of
which dereference **`ph_unnumber`** — and a scan of `struct rtl_pktHdr`'s own
body finds no such field. The macros are therefore dead code that would not
compile if anything called them.

⚠️ 推, and **not verified here**: that the header's `sizeof(rtl_pktHdr)` is
therefore 24 where the running kernel uses 32. The struct's own comment says
*"Each pkthdr is exactly 32 bytes"*.

**The operational rule either way: do not copy `32` out of that comment into an
allocation.** Compute the size, or take it from the running kernel's own
behaviour.

### 8.3 ⚠️ A correction to this segment's own tooling claim

This segment reported that there is no unwrapped route to a MIPS disassembler
on this host, so the vendor toolchain's `objdump` would have to be wrapped in
`tools/vendor-tripwire.sh`. **That was wrong, and the control was run on the
wrong binary**: plain `objdump` is x86-only here, but 量
`/usr/bin/mips-linux-gnu-objdump` exists and `-i` lists **33** MIPS targets,
including `elf32-tradbigmips`. **An unwrapped, non-vendor disassembler is
available**, which removes the reason the vendor binary would ever be run.

---

## 9. What this file does NOT establish

1. **Throughput.** Every number here is ping-bound, so 1.88 MB/s each way is a
   floor and not a rate. `R6-5`.
2. **That the run-out fix does anything** — § 6.3. It is kept as a guard and
   is measured to be inert at every load this desk can offer.
3. **WHY the ingress path wedged.** Its location is measured (below both
   drivers) and its remedy is measured (a cold power-on). The mechanism is
   unidentified, and the flood that produced it has not been shown to be what
   produced it — it happened once, and once is not a reproduction.
4. **The `netif_wake_queue` defect** — § 6.1, real and unreached: `n_xmit_busy`
   read 0 in every flood on both images, so four TX descriptors were never
   exhausted at `pipe 2`–`pipe 4`.
5. **`ph_queueId`'s layout.** 量: referenced exactly once in the whole vendor
   Ethernet tree — its own declaration — while `ph_mbuf` fires 50 times,
   `m_data` 28, `ph_len` 11. *"The vendor driver works, so its compiled layout
   is the hardware's"* constrains **only the fields the working path touches**.
6. **Whether TX rings 2 and 3 interrupt at all.** `CPUIIMR`/`CPUIISR` define
   only two TX rings' worth of bits while this part has four, and no source in
   any drop resolves it.
7. **The two unnamed `CPUIISR` bits.** `last_iisr` carried bits 12 and 13 on
   every transmit in this seating; the header names neither.


## 7. `R6-4a` — the TX queue was stopped and nothing ever restarted it

🔴 **Written at the desk on 2026-09-20 and NOT YET RUN ON THE SILICON.**
Everything in this section is 讀 out of the source or 量 on committed captures.
The register readings it predicts are `R6-5`'s to take.

### 7.1 The defect

讀 `rtl819x-nic.c`: `nic_xmit` finds the engine still owns the next slot,
calls `netif_stop_queue(dev)` and returns `NETDEV_TX_BUSY` — correctly, because
the caller still owns the skb after that return. 量 before this change:
`netif_wake_queue` appeared **zero** times in the file. Once that path is taken,
transmit is dead for the life of the interface.

⚠️ **The counter that should have said so cannot.** `n_xmit_busy` read **0**
in every flood of seating 28, on both images — and `0` is what a working wake
looks like **and** what a stop path that was never reached looks like. Four
concurrent 1400-byte ping floods never exhausted four TX descriptors, so the
ambiguity is measured rather than feared.

### 7.2 Why the wake is LEVEL-triggered

The obvious design — *the ISR saw `TX_DONE`, so wake* — is edge-triggered, and
an edge can be consumed by an interrupt that runs before the stop takes effect;
after that, no edge is owed and the queue stays stopped forever.

`nic_tx_try_wake()` instead re-tests **exactly what `nic_xmit` tests** — is the
queue stopped, and is `nic_tx_idx`'s descriptor free — on **every** interrupt,
whatever raised it. A lost `TX_DONE` then costs a delay and not the interface.

🟢 **The TX-completion interrupt is real on this die and was already being
discarded.** 讀: `NIC_IE_TX_DONE_ALL` and `TX_ALL_DONE` are in
`NIC_IIMR_LADDER`, and `nic_isr` W1Cs them and then acts only on
`NIC_IP_RX_WORK`. 量 `bench/2026-09-19b/C19-nic6.log`: one `tx` verb, `n_rx 0`,
**`n_irq 1`, `last_iisr 0000320E`** — bit 9 is `TX_DONE`. One transmit, one
interrupt, TX completion in its status word.

**Two sites were rejected and the reasons are measured.** `nic_poll` — 讀
`nic_isr`, NAPI is scheduled only on RX bits, so a TX-only stall never polls.
The top of `nic_xmit` — 讀 `net/sched/sch_generic.c:145-147`, a stopped queue is
never offered to the driver.

### 7.3 The classic race cannot happen here, and the remedy stays anyway

量 on this image's own `.config`: `# CONFIG_SMP is not set` and
`CONFIG_PREEMPT_NONE=y`. So `spin_lock_irqsave(&nic_lock)` in `nic_xmit` is a
`local_irq_save` and `nic_isr` **cannot** run between the descriptor read and
the `netif_stop_queue`. The hardware can still retire the slot inside that
window — but `CPUIISR` is sticky write-1-to-clear, so the interrupt is
*pending*, not lost, and is delivered the instant the unlock restores the mask.

🔴 **What closes the race is therefore two Kconfig lines, neither of them in
this file.** The post-stop re-test is added anyway, for three reasons that are
not the race: a correctness argument resting on two symbols nobody reading this
driver can see is a bad place to leave it; it removes a whole interrupt's
latency from the common case; and `n_tx_wake_race` then **measures** how often
the window is real instead of leaving it argued.

Waking while returning `NETDEV_TX_BUSY` is correct — 讀
`net/sched/sch_generic.c:124-178`: `qdisc_restart` requeues the skb and zeroes
its return **only if the queue is still stopped**, so an un-stopped queue makes
`__qdisc_run` re-offer the same skb, bounded by its own `jiffies != start_time`.

### 7.4 🔴 `watchdog_timeo = 5 * HZ` has been DEAD CODE since it was written

讀 `net/sched/sch_generic.c:240-249`: `__netdev_watchdog_up()` arms the timer
only `if (dev->netdev_ops->ndo_tx_timeout)`. This driver set `watchdog_timeo`
and never supplied that handler, so **the netdev watchdog has never started for
`rlx0`**, and the assignment has been inert for its whole life. 讀 `:227` of the
same file: when it does fire it calls `ndo_tx_timeout` with **no NULL check**,
so the pairing is mandatory in both directions.

`nic_ndo_tx_timeout` is added, and **it touches no hardware**. Resetting the DMA
engine from a timer, on a part whose ingress path has wedged once with the
mechanism unidentified (§ 6.2), would be a repair nobody could afterwards
distinguish from the fault. It re-runs the same level test the ISR runs and
counts the entry. `dev->trans_start` is deliberately **not** refreshed, so while
the engine is genuinely stuck the handler is re-entered every `watchdog_timeo`
and `n_tx_timeout` reads as a **rate** — entries per 5 s of stall — rather than
as a single event.

量 the console cost, because that is what could have made it unsafe under
`FW-45`'s ~1.33 s hardware watchdog: `dev_watchdog` guards the call with
`WARN_ONCE`, and this image is `# CONFIG_BUG is not set`, under which
`WARN(cond, fmt)` reduces to `!!(cond)` — no printk, no `dump_stack`, **zero
bytes** on a 38400 baud console. A `loud` image would print one backtrace, once.

⚠️ The vendor has both halves and recovers nothing — 讀 `rtl_nic.c:5183-5186`
is one `printk`. This diverges deliberately.

### 7.5 The ledger, and why five fields and not one

| field | what it counts |
|---|---|
| `n_tx_stop` | `netif_stop_queue()` calls from `nic_xmit` |
| `n_tx_wake` | `netif_wake_queue()` from the ISR's level test |
| `n_tx_wake_race` | `netif_wake_queue()` from the post-stop re-test |
| `n_tx_timeout` | `ndo_tx_timeout` entries — the reading that **refutes** the interrupt-driven wake if it is ever non-zero |
| `tx_stopped` | a **STATE**, `netif_queue_stopped()` at read time, `-1` with no netdev |

`tx_stopped` is not derivable from the others: `n_tx_stop == n_tx_wake` cannot
say whether the queue is stopped **now**, and that is the reading by which a
wedged interface is told from a busy one. `n_tx_stop` is kept separate from
`n_xmit_busy` although today they move together — the first counts a transition
of the QUEUE's state, the second counts a RETURN VALUE, and a later change to
either path must not silently merge two different measurements.

### 7.6 The positive control, and why the flood alone is not one

🔴 **`txstall on|off`.** The flood cannot be the test, because
`n_xmit_busy 0` after it is ambiguous (§ 7.1). This verb takes the load out of
the question: clear `CPUICR.TXCMD` so the engine stops consuming descriptors,
offer five frames, and the fifth **must** take the stop path. `txstall off`
restores it. One cell, two-sided, one image.

`TXCMD` and not `STOPTX`: `TXCMD` is a bit this driver already writes on every
`engine on` and whose value is anchored by this die's own `CPUICR C4000000` at
the loader prompt, while `NIC_STOPTX` is 讀 out of a vendor header and has never
been exercised here. `nic_engine_on` is deliberately **left set** — clearing it
makes `nic_xmit` *drop* the skb instead of stopping the queue, which is the
opposite of what this control is for. `RXCMD` is left set so the interface can
still be pinged while transmit is stalled, which is the negative half.

🔴 **A trap this verb walks into, caught before the card was written.**
`CLAUDE.md` 量 that this image's `ping` ignores `-c` and always sends **four**
packets — and the ring holds **four**. One `ping` fills it exactly and never
reaches the fifth frame. **The cell needs two `ping` runs**, or the control is
void while looking like it ran.

⚠️ **Refutation of the control itself, which must be on the card before
power**: if `txstall off` does not restore transmit — a ping after it fails, or
the `txd*` OWN bits stay set — then clearing `TXCMD` mid-flight wedges this
engine, the control is VOID, and the seating falls back to the flood alone.

### 7.7 The refutation condition for `R6-5`'s bench run

With `txstall` run **first** and the throughput load after, `/proc` must read
`n_tx_stop > 0`, `n_tx_wake > 0`,
`n_tx_wake + n_tx_wake_race >= n_tx_stop`, `tx_stopped 0`, `n_tx_timeout 0`,
and the stream must still be running at the read.

**Refuted by**: `n_tx_stop > 0` with both wake counters 0 (wrong wake site);
`tx_stopped 1` at rest with the stream dead (the wake fired and was
insufficient); **`n_tx_timeout > 0`** — the ISR wake missed and only the 5 s
watchdog saved it, so the design is wrong even though the link survived; or
`n_tx_wake` exceeding `n_tx_stop + n_tx_wake_race` by more than 1 (the counters
do not measure what they claim).

**The ordering is the point.** `txstall` settles *reachability* and *the wake
fires* before any load; the load then tests only *does it hold under load*. A
first flood run against an untested wake would have been testing two things at
once, and a green result could not have said which.

## 8. `R6-4a`'s first silicon run — what it established and what it refuted

🟢 **Measured 2026-09-20, seating 29, `bench/2026-09-20/`.** Everything here ran
on the die. § 7 above is the desk half and is deliberately not edited; this is
what happened when it met the hardware.

### 8.1 🟢 § 7.7's acceptance set is MET, and the first attempt's "refutation" was an artefact

Block 29's `D8`–`D11`, one fresh boot, no interface re-open:

| cell | `n_tx_stop` | `n_tx_wake` | `n_tx_wake_race` | `tx_stopped` | `now_icr` |
|---|---:|---:|---:|---:|---|
| `D8-BASE` | 0 | 0 | 0 | 0 | `C4000000` |
| `D9-STALL` | **1** | 0 | 0 | **1** | **`44000000`** |
| `D10-OFF` | 1 | **1** | 0 | **0** | **`C4000000`** |
| `D11-RECOV` | 1 | 1 | 0 | 0 | `C4000000` |

`D11`'s ping came back **3 of 4**, so transmit resumed and the control is not
void. § 7.7 asks for `n_tx_stop > 0`, `n_tx_wake > 0`,
`n_tx_wake + n_tx_wake_race >= n_tx_stop`, `tx_stopped 0`, and the stream still
alive: **all five hold.**

🔴 **Block 28 read `n_tx_stop 2` with `n_tx_wake 0`, which is exactly § 7.7's
stated refutation — *wrong wake site*. It was not that.** `nic_tx_try_wake()`
returns 0 while the current TX descriptor is still `OWN`ed, and § 8.3's runaway
engine meant that descriptor would never be retired. **The wake site is right;
its precondition had been destroyed.** Telling those two apart is what the
second card existed for, and a card that had stopped at the first reading would
have recorded a working driver as broken.

🟢 **Two predictions hit exactly.** `n_writes` moves **+1** on `txstall on` and
**+2** on `txstall off` (the restore and the doorbell) — 14 → 15 → 17. And
`now_icr` returns to `C4000000`, **not** `C4800000`, so **`TXFD` is a
self-clearing doorbell**, which § 3.3 recorded as unmeasured anywhere in this
repository.

### 8.2 🔴 `ndo_tx_timeout` still cannot fire, and § 7.4 needs a correction

§ 7.4 says the watchdog was dead because the driver set `watchdog_timeo` and
supplied no `ndo_tx_timeout`, and that `R6-4a` fixes it by supplying one.
**Supplying one is not enough.** 讀, three lines:

* `net/ethernet/eth.c:349-353` — under `CONFIG_RTL_819X`, Realtek's
  `ether_setup` sets `dev->tx_queue_len = 0` (*"reduce queue size for max free
  sdram"*); the `#else` arm is the usual 1000.
* `net/sched/sch_generic.c:589` — a zero-length device gets `&noqueue_qdisc`.
* `:605-606` — `need_watchdog` is set **only** for a non-noqueue qdisc, and
  `:630` is its only reader and `dev_watchdog_up()`'s only caller.

∴ the timer is never armed. 量 `X18`: `tx_stopped 1` for minutes with
`n_tx_timeout 0`. **`SPEC.md` `NET-57`.**

🔴 **And the larger consequence lands on § 7's own argument.**
`rtl819x-nic.c:967-972` argues that returning `NETDEV_TX_BUSY` while waking is
correct because *"qdisc_restart requeues the skb"*. `noqueue_qdisc.enqueue` is
**NULL**, so `dev_queue_xmit` never reaches `qdisc_restart` and the frame is
freed. **The argument is right for the kernel it cites and wrong for this
board.** It is not deleted: what is wrong is not the reasoning but an unstated
assumption that this device has a qdisc at all.

### 8.3 🔴 A re-opened interface resumes the DMA engine outside its ring

量 `X12`: `ifconfig rlx0 down ; ifconfig rlx0 10.1.1.3 up` printed `ENGOFF`,
`NDSTOP`, `ENGON`, `NDOPEN` and **no `RLXFW-N-ALLOC` and no `RLXFW-N-ARM`** —
`ndo_open` skips both when `nic_allocated`/`nic_armed` are already set, so
nothing rewrites the descriptor base registers. 量 `X23`: with the engine on,
`rpdcr0_pos` advanced `A15B1C00` → `A15B1C64` while `rx_ring` is `A15B8000`.
It was reading descriptors from outside the ring and writing frame data wherever
those words pointed. `X25`'s `ifconfig down` stopped it (`engine_on 0`,
`now_icr 04000000`, both position registers frozen at `X26`).

🟢 **A fresh boot does not have this**: `D5-UP` and `X41` both print
`N-ALLOC=A15B8000` and `N-ARM=A15B8000`. **`SPEC.md` `NET-58`.**

### 8.4 🔴🔴 The network was PHYSICALLY faulty for all of block 28, and no software reading could have said so

量, and it is the reading `SPEC.md` `NET-54 殘留` named as missing from seating
28's set: the switch's own port-3 receive counters were **frozen** while the
host's `tcpdump` showed six ARP replies and three broadcasts leaving the
adapter. Not counted, not even as errors. A cable re-seat at both ends —
**single variable, no power cycle, no software change** — took port 3 from
`Rcv 600` to `Rcv 2124` (the counter prints no separator) with fifteen new broadcasts and **zero** new
`CRCAlignErr`.

⚠️ **推, and the honest form of it**: `NET-54`'s shape is the same, and a cold
power-on involves handling the board. **Refuted by** `NET-54` reproducing with
the cable demonstrably untouched. **`SPEC.md` `NET-56`.**

### 8.5 🔴 A real TCP load hangs the whole board, and the mechanism is undetermined

Two independent reproductions: `D14` (`-t 10`, default 128 KiB blksize) and
`X45` (`-l 32K -t 2`). Both left the console **completely silent** — `X34` sent
nothing for 100 s and captured **0 bytes** — with ping dead and
`busybox reboot -f` ineffective (`X35`: 7,489 bytes, all ESC, no loader prompt).

🔴 **It is not a panic.** `arch/rlx/kernel/traps.c:52` is
`#define printk panic_printk` with `CONFIG_PANIC_PRINTK=y`, so `die()` reaches
the console even at `CONFIG_PRINTK=n`, and nothing printed. And
`CONFIG_RTL_WTDOG=n` means no armed watchdog will recover it.

⚠️ `-l 8K` survived, but its control connection broke before any data moved
(`NET-60`), so it is **not** evidence that a small blksize is safe.
**`SPEC.md` `NET-59`, and it is the first thing the next seating must narrow.**

### 8.6 What this run did NOT establish

1. **No throughput number exists.** `D5` is not met. Every `iperf3` run on the
   die either failed its control exchange or hung the board.
2. **`D6` was never attempted.** The 30-minute flood did not start.
3. **The hang is not isolated** — § 8.5.
4. **The vendor-driver contrast could not be taken**: `ifconfig eth4 up` returns
   `SIOCSIFFLAGS: Device or resource busy` because this driver holds a
   non-shared `request_irq(12)` (量 `X9`). So *below both drivers* — `NET-54`'s
   own phrase — cannot be re-measured while `rlx0` is bound.


## 10. `R6-5` seating 30 — why a datagram loses exactly one fragment

**量 2026-09-20, blocks 30–32 and their corrections.** Everything in this
section is from `bench/2026-09-20b/`.

### 10.1 What was refuted first

Block 30's ladder was written to test three hypotheses and refuted all three.

| hypothesis | pre-registered discriminator | reading |
|---|---|---|
| interrupt storm | `n_irq` explodes | **1,936 interrupts for 5,281 frames** = 2.7 frames per interrupt |
| TX-queue death | `tx_stopped` goes to 1 | **0** at every rung — 🔴 **and that refutation is VACUOUS.** 量 `n_tx`: `C14-f6` 214, `C16-f14` 216, `C17-f41` 217, so the 14- and 41-frame rungs applied **no transmit load** (two ARP replies). The hypothesis was never tested; the deepest TX burst the ladder produced was six, the rung that worked. See § 10.6 |
| softirq livelock | `time_squeeze` explodes | `/proc/net/softnet_stat` column 3 = **`00000000`**, first reading of that file on this board |

The TX-queue hypothesis was this file's own § 7, and the experiment written to
confirm it refuted it instead.

### 10.2 The chain that survived

1. A burst of frames arrives back-to-back into an **8**-entry RX ring faster than
   the driver hands descriptors back. ⚠️ **The evidence is the switch's `pause`
   counter and `MBUF_RUNOUT` itself, not a copy rate**: 1.88 MB/s is recorded at
   `:701` of this file as a *ping-bound floor*, and quoting it as the copy rate
   was an error in this section's first draft.
2. `MBUF_RUNOUT` fires: `seen_iisr` goes `0000320E` → `0001320E`, and bit 16 is
   `NIC_IP_MBUF_RUNOUT` (`rtl819x-nic.c:292`). First seen at `C16-f14`.
3. The engine's two RX position registers desynchronise by **exactly 4** and
   stay there. Indices are `(pos − base) / 4` with `rx_ring A15B8000` and
   `mb_ring A15B8020`:

   | capture | `rp` | `rm` | Δ |
   |---|---:|---:|---:|
   | `C8-BASE` | 6 | 6 | 0 |
   | `C11-frag1` | 1 | 1 | 0 |
   | `C12-f1` | 7 | 7 | 0 |
   | `C13-f3` | 4 | 4 | 0 |
   | `C14-f6` | 6 | 6 | 0 |
   | `C16-f14` | 6 | **2** | **4** |
   | `C17-f41` | 1 | **5** | **4** |
   | `Y6-nic` | 5 | **1** | **4** |
   | `Z7-nic` | 7 | **3** | **4** |

4. The driver reads OWN from `nic_rx_ring[i]` (`:751`), the length from
   `nic_rx_ph[i]` (`:758`) and the buffer address from `nic_rx_mb[i]` (`:768`) with
   one `i`, and `nic_refill` (`:1227-1241`, the two `nic_re_set` calls that hand
   ownership back are at `:1239-1240`) refills both at that same `i`. **Nothing
   re-synchronises them.** 🟢 `bf` is a pure function of `i` (`:1232`), so the
   address is never wrong — only the length is.
5. Frames are then delivered carrying another frame's length, and `ip_rcv`
   drops them — `InTruncatedPkts` **1250**, one per failed datagram.
6. Switch port 3 received **13,541** frames with `CRCAlignErr 0`, `Drop 0` and
   `< 64: 0 pkts`, so the wire and the switch are clean and the truncation is
   this driver's.

### 10.3 Causality, both ways

`arm` writes `CPURPDCR0 ← nic_rx_ring` and `CPURMDCR0 ← nic_mb_ring`
(`:1187-1213`), so it is the repair. 量: Δ went **4 → 0** with no traffic
between (`Z10-nic`), and **0 → 4** after one six-frame ping run (`Z14-nic2`).

⚠️ It did not restore the symptom — `Z11-f6` was 11/181 where the
byte-identical `H4-f6` had been 20/20 — so either something else accumulates or
the rings re-desynchronise within the first datagrams. A fresh boot does restore
it: `R8-B0` is 20/20 (`NET-63`).

### 10.4 What this costs the driver, and what a fix has to contain

Stated so the fix is not designed in the same breath as the measurement.

* `nic_do_arm()` must reset `nic_rx_idx` (and `nic_tx_idx`). **Not doing so hard-hung the board** — `NET-64`.
* `:768` reads `bf` out of a descriptor the DMA engine writes and `:772-774`
  dereferences it with no bound check. A validated `bf` turns a bus hang into a
  dropped frame, and it is the difference between a measurement that ends a
  seating and one that does not.
* The poll path needs to notice the desync. Both positions are readable; a
  compare costs two KSEG1 loads.
* The copy rate is the underlying cause of the run-out, and this file's own
  § 6 already records that the alternatives were left as an `R6-5` question with
  a number attached. It now has one.

🔴 **None of these belongs in the image that measured the fault.**

### 10.5 Three counters, three sources, one number

量: `/proc/net/softnet_stat` column 1 read `0x14a1` at `C19-soft`; the driver's
own `n_rx` read 5281 at `C17-f41`; the switch MIB's port 3 `Unicast` read 5281
at `X2-asic`. 0x14a1 is 5281. **Three counters that share no code, and not one
of them was written to agree with the others.**

Column 3 of `softnet_stat` is `time_squeeze` and it read `00000000` — the first
reading of that file on this board. 讀 `net/core/dev.c:2954`: it is incremented
exactly where `net_rx_action` breaks on its two-jiffy limit, and `:3185` prints
it. ⚠️ That refutes a softirq livelock **at the load actually applied** and not
in general.


### 10.5a 🔴 `ping -c N -w D` does not send N packets

量 2026-09-20, and it matters because four of this seating's rungs derive a
frame count from `-c`.

iputils' own man page, verbatim: *"ping does not stop after count packets are
sent, it waits either for deadline expire or until count probes are
**answered**"*. So with a deadline **and** loss, `-c` bounds the number of
**replies**, not the number of requests.

量, the two rungs where it bit: `-c 20 -s 20000 -i 0.1 -w 15` sent **145**
packets (15.38 s ÷ 0.106 s) and `-c 10 -s 60000 -i 0.2 -w 15` sent **74**
(15.25 s ÷ 0.206 s).

🟢 **The measurement survived because the driver closes on the larger number**:
145 × 14 = 2,030 against `Δn_rx` +2,032, and 74 × 41 = 3,034 against +3,035,
with the residuals being ARP. 🔴 **But block 32's card computed its expected
frame counts from `-c`**, and on a lossy rung that arithmetic is wrong. A card
that needs an exact request count must read it back from the host's own
`packets transmitted` line and not from the flag it typed.

`SPEC.md` `FW-97`.

### 10.6 🔴 What an adversarial pass took back out of § 10

A second reader was given the cards, the captures and the driver and asked to
refute. Five things in the first draft of this section did not survive, and the
corrections are in `bench/2026-09-20b/CORRECTIONS-block32.md` § 2 with their
measurements:

* **`NET-59` was never a hang.** The board was draining a queue of `connect()`
  calls at **189 s** each — `3+6+12+24+48+96` from `TCP_SYN_RETRIES 5` and
  `TCP_TIMEOUT_INIT 3*HZ`, against two measured completion intervals of
  **188.6 s** and **189.3 s**. `bench/2026-09-20/D23-ST3` typed
  `cat /proc/stat` and returned an `iperf3` JSON. `busybox reboot -f` was never
  executed; it sat behind further runs.
* **The TX-queue-death refutation was vacuous** (§ 10.1's table now says so),
  and the fault then appeared for real in `Z11-f6`: five counters across three
  subsystems all reading **19**.
* **The `+1` on `ReasmOKs` is `Icmp InErrors 1`** — one datagram reassembled out
  of the wrong bytes and failed at ICMP. It is the most direct evidence in the
  seating and the draft filed it as noise.
* **Δ = 4 on an 8-entry ring is its own negative**, so which ring leads is
  undetermined; the draft's headline picked one.
* **The `41 vs 22` liveness payload is an "is the shell busy" gate**, not an "is
  the board alive" gate: `X45-l32k-live`'s 22 bytes were taken 35 s into a 189 s
  `connect()`.

---

## 11. `R6-5` seating 31 — the board is MUTE, not deaf, and `NET-61` is not what stops `D5`

Seating 30 concluded that a burst desynchronises the engine's two RX position
registers and that this is what prevents a throughput number. Seating 31 built
an image to remove that obstacle, instrumented it, and **refuted the
attribution**. Everything below is 量 on 2026-09-21, image `s31b`,
`RECIPE_ID f179cf21`, four cold power-ons.

### 11.1 The one change that made the fault visible

Every previous observation of this fault ran the client in the **foreground**,
so the board's shell was blocked behind it and `/proc` could not be read. The
board looked silent because nothing could ask it anything.

Seating 31 put a single `&` on the board's `iperf3` line. The shell stayed
free, and the driver's own counters became readable **during** the fault.

🔴 **That is the whole methodological content of this section.** The fault had
been observed four times across three seatings and was opaque every time for a
reason that had nothing to do with the fault.

### 11.2 What the counters say

| | before | during | after | late |
|---|---|---|---|---|
| `n_rx` | 10 | 19 | 23 | **27** → 35 → **38** |
| `n_napi_poll` | 8 | 16 | 20 | 24 |
| `n_tx` | 7 | 23 | **26** | **26** |
| `n_xmit_busy` | 0 | 0 | 1 | 1 |
| `n_tx_stop` | 0 | 0 | **1** | **1** |
| `tx_stopped` | 0 | 0 | **1** | **1** |
| `n_tx_wake` | 0 | 0 | **0** | **0** |
| `n_tx_timeout` | 0 | 0 | 0 | 0 |
| `n_dsync` | 0 | 0 | **0** | **0** |
| `n_skb_fail` | 0 | 0 | 0 | 0 |
| `seen_iisr` | `0000320E` | `0000320E` | `0000320E` | `0000320E` |

**`n_rx` rises while the host reports zero replies.** The board receives the
ICMP requests and cannot send the answers.

### 11.3 The smoking gun

`bench/2026-09-21/W6-TXD`:

```
txd0 A15B81D1   txd1 A15B81E9   txd2 A15B8201   txd3 A15B821B
```

Bit 0 set on all four. 讀 `NIC_DESC_OWN`: `1 = SWCORE owns, 0 = CPU`. **All
four TX descriptors are engine-owned**, and `tx_idx 2` points at one of them.

The chain, each link with its evidence:

1. Sustained TCP makes the board transmit continuously. 量: the frozen `txd`
   lengths are 82 / 74 / 82 / 74 — ACK-sized.
2. **The engine stops retiring TX descriptors.** 🔴 *Why* is not established;
   see 11.6.
3. All four fill.
4. `nic_xmit` reads slot `tx_idx`, finds `NIC_DESC_OWN`, calls
   `netif_stop_queue`. 量: `n_tx_stop 1`, `tx_stopped 1`, `n_xmit_busy 1`.
5. The wake path — `nic_tx_try_wake`, from the ISR — tests **the same slot**.
   It never becomes CPU-owned. 量: `n_tx_wake 0` while `n_irq` rises 43 → 47.
6. `ndo_tx_timeout` cannot fire: `NET-57`, `tx_queue_len = 0` makes this a
   `noqueue` device. 量: `n_tx_timeout 0`.

### 11.4 What this refutes, by name

* 🔴 **`NET-54`'s "ingress wedge"** — ingress is healthy throughout.
* 🔴 **"the board went deaf"** — it hears every frame.
* 🔴 **`NET-64`'s "hard hang"** — the kernel runs, the driver polls, and the
  tty echoes. 量 twice, and the echo is exact: `X5-ECHO2` returned **24 bytes**,
  precisely `echo RLXFW-ECHO-PROBE2\r\n`, with `X6-SILENT2` reading **0 bytes
  over 30 s with `sent: null`** — a true silence taken with the instrument
  demonstrably running.
* 🔴 **`NET-61` as `D5`'s blocker** — `n_dsync 0` through all three wedges,
  with the detector's three-way positive control (0 / 4 / 1) proven in the same
  boot. **The desync is not involved.**

⚠️ **And it is not rate-dependent.** The bandwidth ladder wedged on its first
rung, `-b 1M`: 1.25 MB over 10 s, against 2.59 MB carried in the run before it
and against 14-frame ping bursts the same boot handled without trouble.

### 11.5 🟢 `arm` recovers it, so `NET-54`'s recovery cost is wrong here

量, on an already-wedged board, costing nothing:

```
after `engine off ; arm ; engine on`:
txd0 A15B81D0  txd1 A15B81E8  txd2 A15B8200  txd3 A15B821A    <- bit 0 CLEAR
tx_stopped 1 -> 0     n_tx_wake 0 -> 1     n_tx 26 -> 31
```

`ifconfig rlx0 down ; ifconfig rlx0 10.1.1.3 up` then took ping to **2/4**.

`docs/KNOWN-ISSUES.md` carries `NET-54` as *only a cold power-on cleared it*.
**For this fault that is false**, and what makes it false is the TX reclaim loop
added to `nic_do_arm()` this seating.

🔴 **The recovery is not durable** — the next traffic re-wedged it
(`R6-REST` returned 1 byte). It buys a power cycle back, not a working path.

⚠️ **And the RX half of the same change is untriggered code**: `n_arm_flush 0`
at every read across six arms. The reason the loop stays is the TX side.

### 11.6 What § 11 does NOT establish

* **Why the engine stops retiring TX descriptors.** Nothing was read on the
  engine's side of the ring: `tpdcr0_pos` was not sampled across a wedge, and
  `/proc/rtl865x/asicCounter`'s CPU-port `Snd` was never read. Those are the
  two cheapest next readings and neither costs power.
* **Why the recovery is partial and why it decays.** Three readings gave three
  results — `arm` alone moved the counters but left ping at 0/4; one
  `ifconfig down/up` reached 2/4; a second returned to 0/4.
* **Whether the fault needs TCP.** Every wedge tonight was TCP. A long ping
  flood — RX plus TX, no TCP — is the discriminator and was not run.
* 🔴 **One dump of the whole seating is anomalous and nothing in the block explains it.** `R4-FINAL` — an off-card read taken after the interface cycle, when ping was already only 2/4 — carries `seen_iisr 0002320E`, **bit 17 `PKTHDR_RUNOUT`, sticky, and the only non-`0000320E` reading of the night**; `n_dsync 1` with `dsync_last_d 4`; `rx_idx 5` against a hardware position of slot 2; and `rxd0`/`rxd1` both CPU-owned at `len 102`. 未定 — **one observation, off-card, and taken in a state that was already degraded.** It is recorded because it is the only place all night where a run-out bit set at all, and because the block's own "driver index == hardware index held at every read" is a claim about the CARDED cells and this dump is not one of them.
* **`D5` and `D6` were not obtained.** `NET-60`'s half *is* closed: 量 `V1`,
  `Reverse mode, remote host 10.1.1.2 is sending`, so 3.1.3 at both ends
  completes the control exchange 3.16 could not.
