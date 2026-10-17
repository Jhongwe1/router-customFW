# `rtl819x-nic.c`: the file head until 2026-10-18

The comment that opened
[`kernel/linux-2.6.30/drivers/net/rtl819x-nic.c`](../../kernel/linux-2.6.30/drivers/net/rtl819x-nic.c)
until 2026-10-18 — lines 1–195 at commit `bb3fb844` — moved here
verbatim by `P5e-3` ③, so that the file's first `#include` sits by line 60.
It is kept as a record of what the head said; the driver's current page
is [nic](nic.md).

The source marks inside the block are the repository's: 量 measured on the
device, 讀 read out of code or a dump, 推 inferred and pending a measurement.
The file itself now spells them MEASURED, READ and INFERRED. A line number
inside the block that names `rtl819x-nic.c` counts the file's lines at `bb3fb844`.

```c
/*
 * rtl819x-nic.c -- rlxfw's CPU-port DMA driver for the RTL8196E switch core.
 *
 * R6-3: "the CPU port's DMA rx/tx rings, the interrupt, and NAPI", whose DoD
 * is *the checkpoint ladder is walked and NOT skipped: loopback -> one-way TX
 * -> RX -> NAPI, each rung with an observable before the next is attempted*,
 * and whose named failure mode is *`OWN`-bit write ordering and big-endian
 * descriptor fields* -- the plan's own refutation condition being *frames go
 * out and none come back*, which is what a wrong field layout looks like from
 * the outside.
 *
 * ======================================================================
 * WHY THIS DRIVER CAN START FROM A KNOWN STATE, WHICH IS A MEASUREMENT
 * AND NOT AN ASSUMPTION
 * ======================================================================
 *
 * The vendor's Ethernet driver is in this image and owns this hardware.  It
 * is not removed, and that is deliberate: 讀 `rtl_nic.c:6214-6215`, its
 * `re865x_probe()` writes `CPUIIMR = 0` and `CPUICR &= ~(TXCMD|RXCMD)` --
 * i.e. the vendor's probe DISARMS the DMA engine the loader left running.
 *
 * 量 confirms both halves on this die:
 *
 *   loader state   `CPUICR = 0xC4000000`  bench/2026-09-19b/X7-cpufull-a
 *   Linux state    `CPUICR = 0x00000000`  bench/2026-09-17b block 26 §2.4
 *
 * 🔴 SO REMOVING THE VENDOR DRIVER WOULD BE THE DANGEROUS CHOICE, NOT THE
 * SAFE ONE.  The loader leaves RXCMD set with ring bases at `0xA040FC70`,
 * which is physical `0x0040FC70` -- memory Linux will hand out.  Something
 * must turn that engine off before the kernel reuses those pages, and in this
 * image the only thing that does is the vendor's probe.
 *
 * The other half of the arrangement is the interrupt.  讀 `rtl_nic.c:4227`:
 *
 *	rc = request_irq(dev->irq, interrupt_isr, IRQF_DISABLED, dev->name, dev);
 *
 * -- `IRQF_DISABLED`, NOT `IRQF_SHARED`, and it is called from
 * `re865x_open()` (`:4174`), i.e. on the first `ifconfig up`, not from probe.
 * So on an image where no vendor interface is ever brought up, IRQ 12 is
 * unclaimed and this driver can take it exclusively.  That is a condition,
 * not a wish: `irqon` reports the `request_irq` return value rather than
 * assuming it, and a `-EBUSY` there means somebody opened an interface.
 *
 * ⚠️ IRQ 12 IS NOT LINE 25.  `notes/switch-driver.md:438-442`: the switch
 * core is `BSP_SWCORE_IRQ` = 12 = LOPI base 8 + 4, gated by `GIMR` bit 15
 * (`BSP_SW_IE`), and it does NOT go through the ICTL cascade that `R5-3`'s
 * timer used at line 25.  None of that driver's interrupt experience carries
 * across and this comment exists so nobody assumes it does.
 *
 * ======================================================================
 * WHY THERE ARE NO C BITFIELDS IN THIS FILE
 * ======================================================================
 *
 * The vendor describes the packet header as `struct rtl_pktHdr` in
 * `common/mbuf.h`, and it is C bitfields with NO endian conditional -- 量,
 * `grep -c ENDIAN common/mbuf.h` = 0.  The layout is therefore an UNSTATED
 * ABI CONSEQUENCE: it is whatever this compiler happens to do with bitfields
 * on a big-endian target, and it is exactly the thing this gate's 否證 ① is
 * about.  Copying the struct would make the driver's correctness depend on a
 * property no source file states.
 *
 * So every field here is an explicit shift and mask over `u32` words, and
 * each one carries the byte and bit range it came from.  The point is
 * auditability: a descriptor built by this file can be checked against a
 * `DW` hexdump by eye, which a bitfield struct cannot.
 *
 * The layout below is 量 TWICE, by routes that share no code:
 *
 *   (a) ON THIS DIE, from the loader's own live and working rings --
 *       `bench/2026-09-19b/X9-rings` and `X10-descs`, read at the loader
 *       prompt before anything booted.  Pkthdr descriptors at `A040FDD8`,
 *       `FDF0`, `FE08`, `FE20` -- three intervals of 0x18, so the stride is
 *       24 and not the 32 the header's own comment claims.  mbuf descriptors
 *       at `A040FF30`, `FF48`, `FF60`, `FF78`, same stride.  The data
 *       buffers are `A040FF9A`, `A041079A`, `A0410F9A`, `A041179A` --
 *       EXACTLY 0x800 apart, which is the third independent confirmation of
 *       the 2048-byte mbuf (the others being `CPUICR[26:24] = 4` and the
 *       `0x0800` in the descriptor's own `m_extsize`).
 *
 *   (b) FROM THE SOURCE, by compiling the vendor struct under two different
 *       compilers and dumping the assignments.  See `notes/nic-driver.md`.
 *
 * 🟢 The two agree field for field.  That is 否證 ① answered at the desk,
 * before a single frame is transmitted, and it is the reason this driver is
 * being written with a layout rather than with a hypothesis.
 *
 * ⚠️ 量 also says the buffers sit at `...9A`, i.e. 2 MOD 4.  That is the
 * two-byte reserve that makes an IP header land 4-byte aligned behind a
 * 14-byte Ethernet header.  It is preserved here -- `NIC_RX_OFFSET` -- and it
 * is NOT a detail this driver would have arrived at by reasoning.
 *
 * ======================================================================
 * WHY EVERYTHING IS UNCACHED, WHICH THIS GATE PRE-REGISTERED
 * ======================================================================
 *
 * `CPU-45` is answered and the answer is that this D-cache is NOT coherent
 * with a real bus master: seating 26 had the switch's RX DMA overwrite DRAM
 * under a resident line and the cached read returned the OLD value, twice,
 * with the "it was just evicted" escape closed by the data itself.
 *
 * `R6`'s own 否證 `D1` says, written before any of this existed, that the
 * consequence is *the driver uses uncached mappings throughout -- with the
 * throughput cost measured rather than assumed, because an uncached ring is
 * a different D5*.  This file does exactly that: rings, descriptors AND
 * packet buffers are all reached through KSEG1.  The cost is R6-5's to
 * measure; it is not paid here on a guess that it is small.
 *
 * ⚠️ `kmalloc` returns a KSEG0 address and the allocator may leave dirty
 * lines over it.  `alloc` therefore writes back and invalidates the whole
 * region ONCE before the KSEG1 alias is ever used.  Without that, a dirty
 * cache line could be written back over data the engine had already DMA'd --
 * which is the same non-coherence, in the direction that is easy to forget.
 *
 * ======================================================================
 * WHAT THIS DRIVER DOES NOT DO
 * ======================================================================
 *
 * 1. ~~It registers no `net_device` and no `ethtool` ops~~, and it touches
 *    no PHY.  🔄 2026-09-22: TWO THIRDS OF THIS ITEM EXPIRED AND NOBODY
 *    DELETED IT.  `R6-4` landed on 2026-09-19: `register_netdev()` runs
 *    behind the `netdev on` verb and `nic_netdev_ops` is installed at
 *    init.  1.3 adds `nic_ethtool_ops` (get_drvinfo, get_link,
 *    get_ringparam): it expired too.  🟢 THE PHY THIRD IS STILL TRUE, and it
 *    is true for a reason rather than by omission: 讀 + 量, the CPU port
 *    has no PHY behind it at all -- MDIO address 6 is silent while 0-4
 *    answer, `PCRP6`'s `EnablePHYIf` is clear, `PSRP6`'s EEE field is 0,
 *    and the CPU interface is in the SYSTEM window (0xB8010000) rather
 *    than the switch core's.  A `phy_device` attached to `rlx0` would
 *    have to name an MII address belonging to a different port.  The
 *    `mii_bus` that IS correct here belongs to `rtl819x-switch.c` and
 *    serves ports 0-4; it is named as not done rather than skipped.
 * 2. It writes NOTHING at boot.  Every hardware write is behind a verb AND
 *    behind a runtime unlock, so `n_writes` reading 0 on a boot capture is a
 *    measurement and not a promise.
 * 3. It does not configure the switch core; others set its traps.  讀
 *    `rtl865x_asicL2.c:4694,4703`, the vendor's PROBE already sets
 *    `SWTCR0 |= NAPTF2CPU` and `FFCR |= EN_UNMCAST_TOCPU` on SWCORE=y, and
 *    leaves unknown UNICAST untrapped (`FFCR &= ~EN_UNUNICAST_TOCPU`).  On
 *    SWCORE=n no probe runs: rtl819x-switch 1.6's `vlan`, which /init
 *    types, sets FFCR to 3 (EnUnkUC2CPU | EnUnkMC2CPU), so unknown unicast
 *    is trapped there too.  A driver that expects arbitrary unicast before
 *    R6-4 binds a MAC address depends on which image it runs in.
 * 4. It does not copy `swNic_receive`'s checksum test.  讀
 *    `rtl865xc_swNic.c:604`: the vendor DROPS any frame whose `ph_flags`
 *    lacks BOTH `CSUM_IP_OK` and `CSUM_TCPUDP_OK`.
 *    🔴 THE REASON THIS COMMENT FIRST GAVE WAS WRONG AND THE SILICON SAID SO.
 *    It read *"An ARP frame carries neither"*.  量 2026-09-19,
 *    `bench/2026-09-19b/C32-nic10`: a broadcast ARP request delivered to the
 *    CPU port arrives with `ph_flags = 0x8063`, which INCLUDES both bits.  So
 *    the vendor's test would have passed that frame and the worked example
 *    was invented rather than measured.  The rule survives and is narrower:
 *    the test is a filter on a field this driver has not characterised, its
 *    two bits are set by hardware for reasons nothing here has established,
 *    and adopting it would make RX depend on that.  What is measured is the
 *    VALUE, twice: 0x80E3 for a frame the loader received and 0x8063 for one
 *    Linux received, each decomposing into named bits with no residue.
 * 5. It implements NAPI's MECHANISM -- mask at interrupt, bounded poll,
 *    unmask at exhaustion -- ~~but does not bind a `struct napi_struct`,
 *    because in 2.6.30 that needs a `net_device` and the `net_device` is
 *    R6-4~~.  🔄 2026-09-22: EXPIRED, same day and same step as item 1,
 *    and it survived three seatings of being false.  `netif_napi_add()`
 *    binds `nic_napi` at init and `nic_poll` is the real NAPI poll.  Both
 *    items were found by an audit and not by a test, which is the point
 *    worth keeping: nothing in this repository checks a comment.
 *
 * ======================================================================
 * THE LADDER, AND THE OBSERVABLE EACH RUNG MUST PRODUCE
 * ======================================================================
 *
 *   rung 0  swint     `CPUICR |= SWINTSET` with the engine ON and the mask
 *                     OPEN.  Observable: `n_irq` moves and `/proc/interrupts`
 *                     grows a line 12 that was not there before.
 *                     🔴 The ONLY reason this rung is written this way is
 *                     that seating 27 REFUTED it written the other way:
 *                     `SPEC.md` `NET-47`, `SWINTSET` with the engine off and
 *                     the mask closed leaves no trace and raises no
 *                     `CPUIISR` bit, with an off-card control (an
 *                     `0x04000000` written down the same path STUCK) proving
 *                     that is the die and not the instrument.
 *                     ⚠️ And there is no named pending bit to look for: 量,
 *                     `rtl865xc_asicregs.h` defines no `SW_INT_IP`.  `n_irq`
 *                     is the observable; a `CPUIISR` bit is a bonus.
 *   rung 1  lb on; tx one frame.  Observable: the frame appears in the RX
 *                     ring with the payload this driver wrote.  No PHY, no
 *                     cable, no switch forwarding involved.
 *   rung 2  lb off; tx.  Observable: the workstation's capture.
 *   rung 3  rx        Observable: a frame the workstation sent, decoded.
 *                     ⚠️ RX IS ATTEMPTED BEFORE TX ON PURPOSE.  `ph_flags`
 *                     on transmit is the one field that cannot be derived
 *                     from the layout, and a received frame carries the
 *                     ASIC's own value for it.  Measuring beats guessing and
 *                     the ordering is free.
 *   rung 4  poll      Observable: interrupts masked during the poll, frames
 *                     drained, mask restored, `n_irq` still moving after.
 */
```
