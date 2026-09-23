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
 *    init.  1.3 adds `nic_ethtool_ops` (get_drvinfo + get_link), so the
 *    ethtool third expires too.  🟢 THE PHY THIRD IS STILL TRUE, and it
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
 * 3. It does not configure the switch core.  It does not have to: 讀
 *    `rtl865x_asicL2.c:4694,4703`, the vendor's PROBE already sets
 *    `SWTCR0 |= NAPTF2CPU` and `FFCR |= EN_UNMCAST_TOCPU`, so broadcast and
 *    multicast are already trapped to the CPU port on any boot of this
 *    image.  ⚠️ Note the asymmetry the same read found: unknown UNICAST is
 *    explicitly NOT trapped (`FFCR &= ~EN_UNUNICAST_TOCPU`).  A driver that
 *    expects to receive arbitrary unicast before R6-4 binds a MAC address
 *    would be expecting something this configuration does not do.
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

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/delay.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/slab.h>
#include <linux/interrupt.h>
#include <linux/jiffies.h>
#include <linux/timer.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>
#include <linux/ethtool.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

#define RTL819X_NIC_VERSION	"rtl819x-nic 1.4"

/* R6-4.  `rtl819x-switch.c` owns the switch core's window; this is the one
 * thing this driver borrows from it, for `ethtool -> get_link`.  Both are
 * `obj-y` in the same image, so there is no module boundary and no
 * EXPORT_SYMBOL; the switch driver is `subsys_initcall` (4), this one is
 * `late_initcall` (7), and `get_link` runs later than both.
 * Returns 1 if any of PSRP0..PSRP4 has LinkUp, 0 if none. */
extern int rtl819x_sw_any_link(void);
#define RTL819X_NIC_PROC_NAME	"rtl819x-nic"

/* 🔴 `read_proc` is handed ONE 4,096-byte page and `nic_read_proc` does not
 * bounds-check, so an overflow is not a truncated dump -- it is a store past
 * the page.  `rtl819x-spi` 1.1 met this same limit and answered it by putting
 * its 1,024-line map on a SECOND /proc file.  That answer is wrong here: this
 * dump's readers are cells in frozen cards, and a second file moves every one
 * of them.
 *
 * 量 2026-09-22, `scratchpad/pagebudget.py` walking every `sprintf` format in
 * this handler and charging each conversion its widest expansion (`%u` 10
 * digits, `%d` 11, `%08X` 8, `rx_bytes` at its 64-byte cap, the three loops at
 * their full trip counts): **3,829 of 4,096 = 93.5 %**.  The realistic figure
 * is about 2.1 KB -- the largest dump committed before tonight is 1,244 B
 * (`bench/2026-09-19b/C58-afterflood2.log`).
 *
 * So the page is not expected to overflow.  The cap exists because *not
 * expected* is not a bound, and because the three cheapest things to add to
 * this driver are all `sprintf` lines.  A capped dump SAYS `truncated 1`
 * instead of corrupting memory.
 *
 * 🔴 THE CHECK IS PER ITERATION AND NOT PER BLOCK, and the first version of
 * this cap got that wrong: gating ENTRY to the descriptor loops bounds
 * nothing, because a loop admitted at 3,899 then emits up to 618 more bytes
 * and lands at 4,517.  Inside the loops the ceiling is provable by reading:
 * the fixed scalar run is 2,297 worst case, a loop cannot start an iteration
 * above 3,900, the longest line is 61, and the marker is 12 -- so the handler
 * cannot write past **3,973** of 4,096.  The hexdump's guard is exact rather
 * than per-iteration, because a frame dump cut in half is worse than one that
 * is absent. */
#define NIC_PROC_CAP		3900

/* ------------------------------------------------------------------------
 * The register block.
 *
 * `CPU_IFACE_BASE = SYSTEM_BASE + 0x10000` = 0xB8010000, 讀
 * `rtl865xc_asicregs.h:491` with `REAL_SYSTEM_BASE 0xB8000000` at `:148`.
 *
 * 🔴 This is the SYSTEM block, next door to the timer at 0xB8003100.  It is
 * NOT `0xBB800000` (the switch core, where rtl819x-switch.c lives) and it is
 * NOT `0xBB000000` (the switch TABLE window).  Writing CPUICR at either of
 * those would write into a different peripheral.
 *
 * Every offset below was read at the loader prompt on this die before this
 * driver existed -- `bench/2026-09-19b/X7-cpufull-a`, a single
 * `DW B8010000 16`, twice, byte-identical.
 * ------------------------------------------------------------------------ */
#define NIC_PHYS		0x18010000

#define NIC_CPUICR		0x000	/* :492  */
#define NIC_CPURPDCR0		0x004	/* :494  RX pkthdr ring 0 base */
#define NIC_CPURMDCR0		0x01C	/* :502  RX mbuf ring base */
#define NIC_CPUTPDCR0		0x020	/* :503  TX ring 0 base */
#define NIC_CPUTPDCR1		0x024	/* :504  */
#define NIC_CPUIIMR		0x028	/* :512  */
#define NIC_CPUIISR		0x02C	/* :513  W1C */

/* 🔴 NOT an indexed macro.  讀 `rtl865xc_asicregs.h:505`, the vendor's own
 * `CPUTPDCR(idx)` is WRONG for idx 2 and 3 -- TX bases are non-contiguous
 * (0x020/0x024 then 0x060/0x064), so the macro resolves idx 2 to 0xB8010028
 * = CPUIIMR and idx 3 to 0xB801002C = CPUIISR.  量: both indexed macros have
 * zero call sites in the whole vendor tree, so the vendor never steps on it
 * and the landmine is live for anyone who writes the helper the macro looks
 * like an invitation to write.  These two are spelled out instead. */
#define NIC_CPUTPDCR2		0x060	/* :508  8196E only */
#define NIC_CPUTPDCR3		0x064	/* :509  */

/* CPUICR fields, 讀 `:527-548`, and re-derived against this die's own
 * `C4000000`: TXCMD | RXCMD | BUSBURST_32WORDS(00) | MBUF_2048BYTES(4<<24). */
#define NIC_TXCMD		(1u << 31)
#define NIC_RXCMD		(1u << 30)
#define NIC_BUSBURST_32W	(0u << 28)
#define NIC_MBUF_2048		(4u << 24)	/* :537 -- an INTEGER 0..4, not
						 * one-hot.  A driver treating
						 * bit 24 as "2048" selects
						 * 256. */
#define NIC_TXFD		(1u << 23)	/* TX doorbell */
#define NIC_SOFTRST		(1u << 22)
#define NIC_STOPTX		(1u << 21)
#define NIC_SWINTSET		(1u << 20)
#define NIC_LBMODE		(1u << 19)
#define NIC_LBSPEED		(1u << 18)	/* 🔴 the header defines BOTH
						 * `LB10MHZ` and `LB100MHZ` as
						 * (1<<18), `:543-544`, with
						 * contradictory comments.  One
						 * of them is wrong and nothing
						 * in the material says which.
						 * `NET-38 殘留 ③`. */

/* Descriptor ownership, 讀 `:549-554`, and 量 on this die: the loader's idle
 * RX rings hold entries with bit 0 SET and its idle TX rings hold entries
 * with bit 0 CLEAR.  An idle receive ring is owned by the hardware (it is
 * waiting to fill it) and an idle transmit ring is owned by the CPU (there is
 * nothing to send) -- and the loader's TFTP demonstrably works, so that
 * reading is anchored to a path known to function. */
#define NIC_DESC_OWN		(1u << 0)	/* 1 = SWCORE owns, 0 = CPU */
#define NIC_DESC_WRAP		(1u << 1)	/* last entry of the ring */
#define NIC_DESC_ADDR		0xFFFFFFFCu

/* CPUIIMR / CPUIISR, 讀 `:561-640`.  Only the ones this driver uses.
 *
 * 🟢 The decode is checked against this die: the loader leaves
 * `CPUIIMR = 0x000007F8`, which is EXACTLY `RX_DONE_IE_ALL (0x3f<<3)` |
 * `TX_DONE_IE_ALL (0x3<<9)` with no residue, and `CPUIISR = 0x80000000`,
 * which is exactly `LINK_CHANGE_IP` -- one latched link-change that nothing
 * ever wrote back to clear.  That also explains why the same value appears
 * in loader state and in Linux state: W1C bits do not decay. */
#define NIC_IE_LINK_CHANGE	(1u << 31)
#define NIC_IE_RX_DONE_ALL	(0x3fu << 3)
#define NIC_IE_TX_DONE_ALL	(0x3u << 9)
#define NIC_IE_TX_ALL_DONE_ALL	(0x3u << 1)
#define NIC_IE_PKTHDR_RUNOUT	(0x3fu << 17)
#define NIC_IE_MBUF_RUNOUT	(1u << 11)	/* 🔴 mask bit 11, but the
						 * matching STATUS bit is 16
						 * (`:630`).  Every other
						 * pair in this block shares a
						 * position.  Undetermined and
						 * the vendor cannot settle it
						 * -- its live branch never
						 * enables bit 11. */
#define NIC_IP_MBUF_RUNOUT	(1u << 16)

/* What this driver unmasks.
 *
 * 🔴🔴 THE FIRST VERSION OF THIS CONSTANT WEDGED THE INTERFACE UNDER LOAD AND
 * THE MEASUREMENT IS `bench/2026-09-19b/C58-afterflood2`.  It read
 * `(RX_DONE_ALL | TX_DONE_ALL | TX_ALL_DONE_ALL)` = 0x7FE, dropping the
 * run-out enables on the stated ground that only the sources this ladder
 * observes should be on.  量, under four concurrent 1400-byte floods: the RX
 * pkthdr ring ran out, `CPUIISR` latched bit 17 `PKTHDR_DESC_RUNOUT_IP0`, and
 * because bits 17-22 were masked NO INTERRUPT FIRED -- so NAPI was never
 * scheduled, two filled descriptors were never harvested or handed back, and
 * the interface went permanently deaf with every error counter reading zero.
 * `n_rx 6411` against `n_tx 6154`, 65 % loss, and `now_iisr` still holding
 * 0x00020000 at rest, which proves the ISR had not run since -- the ISR W1Cs
 * everything it reads.
 *
 * 🟢 THE LESSON IS ABOUT THE VENDOR'S CONSTANT, NOT ABOUT THIS BIT.  The
 * vendor writes `CPUIIMR = 0x807E01FE` and `0x007E0000` is exactly the field
 * dropped here.  A constant read out of a working driver carries knowledge
 * that its own source does not explain, and the part of it that could not be
 * justified from first principles was the part that mattered.  Dropping a bit
 * because its purpose is not understood is not conservatism.
 *
 * ⚠️ `MBUF_DESC_RUNOUT`'s enable is bit 11 and its STATUS is bit 16, 讀
 * `rtl865xc_asicregs.h:585-586` and `:630-631` -- the only pair in this block
 * that does not share a position.  That asymmetry is load-bearing here and is
 * why the enable and the status are two separate constants below.
 *
 * LINK_CHANGE is still deliberately masked: it is not needed by any rung, and
 * an unserviced link-change would free-run with the cable in and make `n_irq`
 * unreadable as evidence. */
#define NIC_IIMR_LADDER		(NIC_IE_RX_DONE_ALL | NIC_IE_TX_DONE_ALL | \
				 NIC_IE_TX_ALL_DONE_ALL | \
				 NIC_IE_PKTHDR_RUNOUT | NIC_IE_MBUF_RUNOUT)

/* The STATUS bits that mean "there is RX work to do".  Note the bit-16/bit-11
 * asymmetry above: this is the IP side and it is not NIC_IIMR_LADDER's. */
#define NIC_IP_RX_WORK		(NIC_IE_RX_DONE_ALL | NIC_IE_PKTHDR_RUNOUT | \
				 NIC_IP_MBUF_RUNOUT)

#define NIC_IRQ			12	/* BSP_SWCORE_IRQ, 讀
					 * `boards/rtl8196e/bsp/bspchip.h:108`,
					 * corroborated by the chip table at
					 * `:81` and by LOPI base 8 + 4. */

/* ------------------------------------------------------------------------
 * Ring geometry.
 *
 * Deliberately small.  The vendor uses 256 RX / 128 TX; this ladder needs
 * neither, and a ring that fits in one 4,096-byte /proc page can be DUMPED
 * IN FULL, which is the whole instrument.  `FW-46` measured that this image's
 * busybox has no `dd` and no `md5sum`, so nothing on the device can digest a
 * buffer -- printing it is the only way to see it.
 *
 * ⚠️ The three vendor trees DISAGREE on the vendor's own sizes for exactly
 * this config symbol (base tree 256/128, wecb and saturn49 512/1024).  That
 * is another reason not to inherit a number from them.
 * ------------------------------------------------------------------------ */
#define NIC_RX_DESC		8
#define NIC_TX_DESC		4

/* s32a.  How many times tx_mode 1 re-reads the OWN bit of the slot it wants
 * before it gives up and drops the frame.
 *
 * 讀 `rtl_nic.c:5122`, the vendor's own constant for the same decision:
 *
 *     #define	RTL_NIC_TX_RETRY_MAX		(128)
 *
 * The number is copied rather than chosen, and it is NOT claimed to be tuned:
 * the vendor's iteration does real work (swNic_txDone walks its ring), ours is
 * one uncached read of one word, so 128 of ours is a far shorter wall-clock
 * window than 128 of theirs.  What matters is that the loop is BOUNDED and that
 * the bound is a number somebody can point at.  `tx_retry_max_seen` reports the
 * high-water actually reached, so whether 128 was ever approached is measured
 * rather than argued. */
#define NIC_TX_RETRY_MAX	128

#define NIC_TXMODE_STOPQ	0	/* today's path: netif_stop_queue + BUSY  */
#define NIC_TXMODE_VENDOR	1	/* 讀 rtl_nic.c:5161-5171: poll, then drop */

/* s99a (c).  How a pkthdr's `ph_mbuf` word relates to its own slot index.
 * Three states and not two on purpose: AGREE alone says the detector does not
 * fire spuriously, SKEW alone says it fires, and only BAD -- a value that is
 * not a slot address at all -- says it can tell a usable pointer from a word
 * the engine used for something else. */
#define NIC_PHC_AGREE		0
#define NIC_PHC_SKEW		1
#define NIC_PHC_BAD		2
#define NIC_BUF_SZ		2048	/* must agree with NIC_MBUF_2048 */
#define NIC_RX_OFFSET		2	/* 量: the loader's buffers are at
					 * `...9A`, 2 mod 4 */
#define NIC_DESC_BYTES		24	/* 量: stride on this die, and the
					 * header's "exactly 32 bytes" comment
					 * is wrong -- sizeof is 24 under
					 * CONFIG_RTL_8196E */
/* 🔴 2026-09-22: THAT IS TRUE OF `rtl_pktHdr` AND FALSE OF `rtl_mBuf`, and
 * this one constant is the stride for BOTH rings.  讀 `common/mbuf.h:33-49`,
 * counted by declaration order: `m_next` 0, `m_pkthdr` 4, `m_len` 8,
 * `m_flags` 10, one pad byte at 11 so `m_data` can be 4-aligned, `m_data` 12,
 * `m_extbuf` 16, `m_extsize` 20, `m_reserved[2]` 22, **`skb` 24** --
 * sizeof(struct rtl_mBuf) = **28**.
 *
 * The CONSTANT is still right for this driver and the REASON was wrong.  24
 * is correct here because rlxfw lays out its own mbuf descriptors at that
 * stride (`nic_do_alloc`) and nothing in hardware strides the descriptor
 * ARRAY -- the engine is given per-slot absolute pointers.  It is NOT the
 * vendor's divisor: `rtl865xc_swNic.c:370` divides by
 * `sizeof(struct rtl_mBuf)` = 28, so porting that line literally would be
 * wrong by 4 in 28 per slot.
 *
 * ⚠️ One consequence is load-bearing for `NET-82` below: rlxfw's mbuf
 * descriptors are 24 bytes and therefore have NO `skb` word.  The vendor's
 * receive path takes `pPkthdr->ph_mbuf->skb` (`:629`) -- byte 24, which does
 * not exist here.  rlxfw's analogue is `m_data` at word 3, which is what it
 * writes at alloc and refill and what it reads at harvest.  That is rlxfw's
 * own construction and not a port of the vendor's line, and it is said here
 * so nobody later "corrects" word 3 to word 6. */

/* Descriptor words.  Word i is bytes 4i..4i+3, big-endian, so bit 31 of word
 * i is the most significant bit of byte 4i -- which is how a `DW` hexdump
 * reads, and that is the point.
 *
 * pkthdr, 量 on this die and confirmed by compiling the vendor struct:
 *   w0  bytes  0..3   ph_mbuf              (pointer to the mbuf descriptor)
 *   w1  bytes  4..5   ph_len               (INCLUDES the 4-byte FCS)
 *       byte   6 hi   ph_queueId
 *       byte   6 lo   ph_extPortList       (must be 0 for TX)
 *       byte   7      ph_srcExtPortNum
 *   w2  bytes  8..11  (ph_pppoeIdx straddles; unused here, written 0)
 *   w3  bytes 12..13  ph_flags
 *       byte  14      reserved
 *       byte  15      ph_portlist          (RX: source port; TX: dest mask)
 *   w4  bit   31      ph_vlanId_resv
 *       bits  30..28  ph_txPriority
 *       bits  27..16  ph_vlanId
 *       bytes 18..19  ph_flags2
 *   w5  bytes 20..23  (PTP byte at 20)
 *
 * mbuf:
 *   w0  m_next     w1  m_pkthdr
 *   w2  bytes 8..9 m_len, bytes 10..11 m_flags
 *   w3  m_data     w4  m_extbuf
 *   w5  bytes 20..21 m_extsize
 */
#define NIC_PH_LEN(w1)		(((w1) >> 16) & 0xFFFFu)
#define NIC_PH_MK1(len, extport, srcext) \
	((((u32)(len) & 0xFFFFu) << 16) | \
	 (((u32)(extport) & 0x0Fu) << 8) | ((u32)(srcext) & 0xFFu))
#define NIC_PH_FLAGS(w3)	(((w3) >> 16) & 0xFFFFu)
#define NIC_PH_PORTLIST(w3)	((w3) & 0xFFu)
#define NIC_PH_MK3(flags, portlist) \
	((((u32)(flags) & 0xFFFFu) << 16) | ((u32)(portlist) & 0xFFu))
#define NIC_PH_VLAN(w4)		(((w4) >> 16) & 0x0FFFu)
#define NIC_PH_MK4(vid)		(((u32)(vid) & 0x0FFFu) << 16)

#define NIC_MB_LEN(w2)		(((w2) >> 16) & 0xFFFFu)
#define NIC_MB_FLAGS(w2)	((w2) & 0xFFFFu)
#define NIC_MB_MK2(len, flags) \
	((((u32)(len) & 0xFFFFu) << 16) | ((u32)(flags) & 0xFFFFu))
#define NIC_MB_MK5(extsize)	(((u32)(extsize) & 0xFFFFu) << 16)

/* 量, from the loader's working rings on this die: every mbuf descriptor in
 * every ring carries `m_flags = 0x009C`, which decomposes with no residue
 * into MBUF_USED | MBUF_EXT | MBUF_PKTHDR | MBUF_EOR.  Used as a measured
 * constant rather than reassembled from four names whose values would be a
 * second thing to get right. */
#define NIC_MB_FLAGS_INIT	0x009Cu

/* 量, the loader's idle TX pkthdr template on this die (`A040FCE8`, word 3 =
 * `0x88000000`) and its idle RX pkthdr template (`A040FDD8`, word 3 =
 * `0x90000000`).  Both carry 0x8000; the differing bit is 0x0800 on TX and
 * 0x1000 on RX.
 *
 * 🔴 THIS IS THE ONE FIELD THIS DRIVER CANNOT DERIVE.  It is a default, it
 * is overridable from the `tx` verb, and the ladder measures the ASIC's own
 * value on a RECEIVED frame before it relies on this one.  That ordering is
 * the mitigation and it is why rung 3 is attempted before rung 2. */
#define NIC_PH_FLAGS_TX_DEFAULT	0x8800u

/* ------------------------------------------------------------------------
 * State.  All of it file-static; this driver is built in and has no exit.
 * ------------------------------------------------------------------------ */
static DEFINE_SPINLOCK(nic_lock);

static int  nic_unlocked;		/* the write guard */
static int  nic_allocated;
static int  nic_armed;
static int  nic_irq_taken;
static int  nic_engine_on;

static unsigned long nic_n_reads;
static unsigned long nic_n_writes;
static unsigned long nic_n_refused;
static unsigned long nic_n_irq;		/* rung 0's observable */
static unsigned long nic_n_irq_spurious;
static unsigned long nic_n_tx;
static unsigned long nic_n_rx;
static unsigned long nic_n_rx_empty;
static unsigned long nic_n_poll;
static unsigned long nic_n_poll_masked;
static u32 nic_last_iisr;		/* what the ISR saw, last time */
static u32 nic_seen_iisr;		/* every bit the ISR has EVER seen */
static int nic_irq_rc = -1;		/* the request_irq return value */

static u32 nic_boot_icr, nic_boot_iimr, nic_boot_iisr;
static u32 nic_boot_rpdcr0, nic_boot_rmdcr0, nic_boot_tpdcr0;

/* One allocation, three regions, all reached through KSEG1. */
static void *nic_alloc_raw;		/* the KSEG0 pointer kmalloc gave us */
static u32   nic_alloc_bytes;
static u32   nic_rx_ring;		/* KSEG1: NIC_RX_DESC u32 entries */
static u32   nic_mb_ring;		/* KSEG1: NIC_RX_DESC u32 entries */
static u32   nic_tx_ring;		/* KSEG1: NIC_TX_DESC u32 entries */
static u32   nic_rx_ph;			/* KSEG1: NIC_RX_DESC pkthdrs */
static u32   nic_rx_mb;			/* KSEG1: NIC_RX_DESC mbufs */
static u32   nic_tx_ph;			/* KSEG1: NIC_TX_DESC pkthdrs */
static u32   nic_tx_mb;			/* KSEG1: NIC_TX_DESC mbufs */
static u32   nic_bufs;			/* KSEG1: (RX+TX) * NIC_BUF_SZ */

static unsigned int nic_rx_idx;		/* next RX descriptor to inspect */
static unsigned int nic_tx_idx;		/* next TX descriptor to fill */

/* The last frame this driver received, kept whole so it can be printed.  One
 * frame, not a queue: the instrument is "show me the bytes", not throughput. */
#define NIC_KEEP 128
static u8  nic_last_rx[NIC_KEEP];
static u32 nic_last_rx_len;
static u32 nic_last_rx_ph1, nic_last_rx_ph3, nic_last_rx_ph4;

/* ------------------------------------------------------------------------
 * R6-4's state.  A `net_device` and a real NAPI instance, neither of which
 * exists at boot: the device is ALLOCATED at late_initcall and REGISTERED
 * only by a verb, so an image carrying this driver still comes up with
 * nothing of mine bound to anything.
 *
 * THE MAC ADDRESS IS LOCALLY ADMINISTERED AND THAT IS A CONTAINMENT DECISION,
 * NOT A SHORTCUT.  This unit's real address lives in `H601`, the 8 KiB region
 * CLAUDE.md forbids touching and whose CONTENT may not enter this repository
 * -- not even its digest.  A driver that read it would put this device's
 * identity into every capture of every seating from here on.  So the address
 * is fixed at 02:52:4C:58:46:57 -- 0x02 marks it locally administered, and
 * the remaining five bytes are ASCII "RLXFW".
 *
 * 🟢 That turns a limitation into R6-4's own DoD requirement.  The gate asks
 * for a POSITIVE discriminator -- "a string only my driver produces" rather
 * than the vendor's absence -- and an address no Realtek OUI can contain,
 * on an interface named `rlx0` where the vendor's are `eth0`..`eth5`, is
 * exactly that.  ⚠️ The limitation is still real and is named here: this
 * driver cannot yet be the interface a shipped firmware uses, because a
 * shipped firmware must present the address on the label.  Reading `H601`
 * safely is a separate problem and it is not solved by this file.
 * ------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------
 * R6-5's desync detector -- `NET-61` and `NET-62`.
 *
 * The engine keeps TWO RX positions, one per ring.  Seating 30 measured them
 * coming exactly 4 slots apart and STAYING there (`SPEC.md` `NET-61`: nine
 * readings, five Delta 0 and four Delta 4, about 12,000 frames, no
 * exceptions), after which this driver reads OWN from one ring and the length
 * from the other with ONE index -- so a frame is delivered carrying another
 * frame's length.
 *
 * NOTHING IN THIS DRIVER COULD SEE THAT.  `n_rx` counted every one of 5,281
 * frames while 218 datagrams died above it -- 量 seating 30, and it is why
 * `PROGRESS.md`'s D6 row says *zero drops by the driver's own counters* would
 * be "true and meaningless".  This is the counter that makes that row mean
 * something.
 *
 * OBSERVE-ONLY: it never acts, so it cannot be a second variable in the
 * experiment it exists to instrument.  Two KSEG1 loads per POLL and not per
 * frame, which is the budget `notes/nic-driver.md` 10.4 set for it.
 * ------------------------------------------------------------------------ */
static unsigned long nic_n_dsync_chk;	/* checks performed -- the denominator */
static unsigned long nic_n_dsync;		/* checks that saw Delta != 0 */
static unsigned int  nic_dsync_last_d;
static unsigned int  nic_dsync_first_d;
static u32 nic_dsync_first_rp, nic_dsync_first_rm;
static unsigned long nic_dsync_first_nrx;
static unsigned int  nic_dsync_test_d;	/* `dsynctest`'s answer */
static int nic_dsync_test_seen;

#define NIC_NAPI_WEIGHT	16

static struct net_device *nic_ndev;
static struct napi_struct nic_napi;
static int nic_ndev_registered;
static int nic_ndev_up;
static unsigned long nic_n_napi_poll;
static unsigned long nic_n_napi_complete;
static unsigned long nic_n_xmit;
static unsigned long nic_n_xmit_busy;
static unsigned long nic_n_skb_fail;
static unsigned long nic_n_arm_flush;	/* CPU-owned slots `arm` discarded */

/* R6-4a.  The TX queue's stop/wake ledger.  Four counters and one state,
 * because `n_xmit_busy` alone cannot tell "the stop path was never
 * reached" from "it was reached and the wake worked" -- both read 0.
 * 量 `bench/2026-09-19b`, four concurrent 1400-byte floods on two images:
 * `n_xmit_busy 0` every time, which is the first reading and was mistaken
 * for nothing at all.
 *
 *   n_tx_stop        netif_stop_queue() calls from nic_xmit
 *   n_tx_wake        netif_wake_queue() calls from nic_isr's level test
 *   n_tx_wake_race   netif_wake_queue() calls from the post-stop re-test
 *   n_tx_timeout     ndo_tx_timeout entries -- the recovery of last
 *                    resort, and the reading that REFUTES the
 *                    interrupt-driven wake if it is ever non-zero
 *
 * `n_tx_stop` is kept separate from `n_xmit_busy` although today they
 * move together: the first counts a transition of the QUEUE's state, the
 * second counts a RETURN VALUE, and a later change to either path must
 * not silently merge two different measurements. */
static unsigned long nic_n_tx_stop;
static unsigned long nic_n_tx_wake;
static unsigned long nic_n_tx_wake_race;
static unsigned long nic_n_tx_timeout;

/* ------------------------------------------------------------------------
 * s99a (b) -- THE INTERRUPT MASK AS A VARIABLE, so `NET-67 殘留`'s strongest
 * remaining candidate can be run as a single-variable A/B on one boot.
 *
 * 量 `docs/nic-vendor-diff.md` 12.4: at the loader prompt this die's
 * `CPUIIMR` is `0x000007F8` -- RX_DONE 0..5 and TX_DONE 0/1, nothing else --
 * while this driver arms `NIC_IIMR_LADDER` = `0x007E0FFE`, which additionally
 * unmasks TX_ALL_DONE (bits 1-2), MBUF_DESC_RUNOUT's enable (bit 11) and all
 * six PKTHDR_DESC_RUNOUT (bits 17-22).  The loader carries 31,475 frames at
 * 16x the dose that wedges this driver (`NET-98`), so the divergence is worth
 * testing; it is not evidence on its own, because the loader also POLLS
 * (`12.2`: a service loop with two reclaim call sites) and therefore does not
 * depend on any of those interrupts for liveness.
 *
 * 🔴 WHY THIS CANNOT BE DONE FROM /proc WITH THE OLD CODE, which is the
 * reason it needs an image at all: 讀 the unmask in `nic_poll` below -- it
 * OR-ed the three RX-work enables back in on EVERY napi_complete.  A mask
 * written through the vendor's `/proc/rtl865x/memory` would be restored by
 * the first arriving packet, and the read-back cell would have shown a FALSE
 * GREEN because `echo read` puts no traffic on the wire.  A cell written to
 * do it was discarded at the desk for that reason (`14.4`).  So the restore
 * is bounded by this variable, and the variable is what the verb sets.
 *
 * 🔴 THE A/B HAS A CONFOUND AND IT IS NAMED HERE RATHER THAN LEFT TO BE
 * FOUND.  `NIC_IIMR_LADDER`'s own comment records that dropping the run-out
 * enables -- mask `0x7FE`, which is the loader's `0x7F8` plus TX_ALL_DONE --
 * made this interface PERMANENTLY DEAF under load
 * (`bench/2026-09-19b/C58-afterflood2`): the pkthdr ring ran out, `CPUIISR`
 * latched bit 17, no interrupt fired, NAPI was never scheduled.  So arm B may
 * reproduce that RX failure instead of illuminating the TX wedge.  The two
 * are DISTINGUISHABLE and the discriminator is already printed: the RX-deaf
 * failure freezes `n_rx` and leaves a run-out bit standing in `now_iisr`,
 * while the TX wedge keeps `n_rx` climbing with all four `txd` OWN bits set
 * and `now_iisr` clear.  A card that reads only "did it stop answering"
 * cannot tell them apart; one that reads `n_rx` and `now_iisr` can.
 *
 * 🟢 TWO SOURCES: `iimr_base` is what this driver believes it armed and
 * `now_iimr` is the register read back.  If they disagree, something else is
 * writing `CPUIIMR` -- which is the very defect 14.4 warned about, arriving
 * as a reading instead of as a worry. */
static u32 nic_iimr_base = NIC_IIMR_LADDER;

/* ------------------------------------------------------------------------
 * s99a (a) -- THE STALL DETECTOR AND ITS RECOVERY.  `P2`'s only new code.
 *
 * WHAT IS ALREADY MEASURED, so that what is new here is small:
 *   `NET-99`  the stall does not clear itself in 600 s -- four readings,
 *             `n_tx` frozen at 17 throughout, `n_rx`/`n_irq` advancing
 *             exactly +6 per interval as the internal control;
 *   `NET-101` `engine off` -> `arm` -> `engine on` clears all four OWN bits
 *             and restores ping 4/4, twice, from a pristine wedge;
 *   `:754`    the level test already in this file wakes the queue on any
 *             interrupt once the slot is CPU-owned again.
 * So the recovery is three calls this driver already has, and the only thing
 * missing was something to notice.
 *
 * THREE THINGS IT MAY NOT BE, each excluded by a measurement:
 *   not `watchdog_timeo`  -- `NET-55`/`NET-57`: the vendor's `ether_setup`
 *                            sets `tx_queue_len = 0`, so every net_device on
 *                            this board gets `noqueue_qdisc`, so
 *                            `dev_watchdog_up()` is never called.  The timer
 *                            below is a private one for exactly that reason.
 *   not `ndo_stop`/`ndo_open` -- `NET-58`, reproduced on demand as `X16`:
 *                            re-opening an interface that had just recovered
 *                            broke it again, because `ndo_open` skips
 *                            `alloc`/`arm` when they are already done.
 *   not `arm` with the engine running -- `NET-64`'s hard hang.  Which is why
 *                            `nic_do_engine(0)` is ordered first below and
 *                            why `nic_do_arm()`'s own `-EBUSY` guard is left
 *                            in place as the second layer.
 *
 * WHY A TIMER AND NOT THE ISR.  The obvious cheap form is to recover from
 * `nic_tx_try_wake()`, which already runs on every interrupt.  量 `NET-99`:
 * during the wedge `n_irq` advanced ONLY because the host kept pinging -- six
 * interrupts per probe and nothing in between.  A recovery hung off the
 * interrupt therefore does not run on a board that has gone quiet, which is
 * the case where it is most needed.  The kernel's own answer to this is
 * `dev_watchdog`, and the only reason it is unavailable is `NET-57`.
 *
 * 🔄 1.4, 2026-09-23: DEFAULT ON.  `NET-107`: seating 37's 17 Mbit/s had
 * `recover 1` typed, and a boot that typed nothing read 0.06.  `recover 0`
 * still reaches the old arm, so one boot can still carry both arms.
 *
 * THE READOUT IS FOUR-STATE, which is what stops a counter reading 0 for two
 * different reasons -- the defect this project recorded as `n_arm_flush`
 * reading 0 both when `arm` never ran and when `arm` ran and worked:
 *
 *   arm  fire  ok   meaning
 *   0    0     0    the queue never stopped; there was nothing to recover
 *   >0   0     0    it stopped and `:754`'s wake handled it inside recov_ms
 *   >0   >0    0    the recovery ran and every attempt returned an error
 *   >0   >0    >0   the recovery ran and all three calls returned 0
 *
 * and `recov_rc` carries WHICH call failed rather than collapsing to a count.
 *
 * 🔴 REFUTATION CONDITIONS, written before the board is powered:
 *   - `n_recov_ok >= 1` with the ping after it still 0/4 REFUTES "these three
 *     calls are a recovery" -- they returned 0 and the interface did not come
 *     back.  `NET-101` measured the opposite twice, by hand.
 *   - `n_recov_arm == 0` on a board that is wedged with `recover 1` set
 *     REFUTES the whole detector: the wedge is then reached without
 *     `netif_stop_queue()` ever being called, and `n_tx_stop` is where to
 *     look.
 *   - `n_recov_spurious` climbing with `n_recov_fire` at 0 means the timer
 *     is firing on transients the level test has already cleared, i.e.
 *     `recov_ms` is too short to be a stall detector.
 * ------------------------------------------------------------------------ */
#define NIC_RECOV_MS_MIN	10u
#define NIC_RECOV_MS_MAX	600000u

static int		 nic_recov_mode = 1;	/* 1 = on, the default since 1.4 */
static unsigned int	 nic_recov_ms = 1000;
static struct timer_list nic_recov_timer;
static int		 nic_recov_timer_ready;
static int		 nic_recov_busy;
static unsigned long	 nic_n_recov_arm;
static unsigned long	 nic_n_recov_fire;
static unsigned long	 nic_n_recov_spurious;
static unsigned long	 nic_n_recov_ok;
static unsigned long	 nic_n_recov_fail;
static unsigned long	 nic_n_recov_wake;
static unsigned long	 nic_recov_j_arm;
static unsigned long	 nic_recov_j_fire;
static int		 nic_recov_rc[3];

/* ------------------------------------------------------------------------
 * s99a (c) -- `NET-82`, AS AN INSTRUMENT FIRST AND A CHANGE SECOND.
 *
 * 讀 `rtl865xc_swNic.c:597-628`: the vendor consumes a received frame with
 * ONE index.  It tests OWN on `rxPkthdrRing[currRxPkthdrDescIndex]`, masks
 * `OWN|WRAP` off to get the pkthdr's address, and then FOLLOWS that pkthdr's
 * `ph_mbuf` pointer to the mbuf and the buffer.  It never indexes the mbuf
 * ring to find a buffer; `currRxMbufDescIndex` exists and belongs to refill.
 *
 * 讀 this file at `nic_do_alloc`: rlxfw writes `rx_ph[i].w0 = &rx_mb[i]` when
 * it builds the ring, and `nic_refill()` does NOT rewrite w0.  So after a
 * frame has been delivered, `rx_ph[i].w0` holds whatever the ENGINE left
 * there.  That makes one word a direct test of `NET-61`'s mechanism:
 *
 *   if `rx_ph[i].w0` still equals `&rx_mb[i]`, the engine paired the two
 *   rings the way this driver's indexing assumes;
 *   if it does not, the engine used a different mbuf slot for this pkthdr
 *   and `nic_dw(nic_rx_mb, i, 3)` is reading SOMEBODY ELSE'S BUFFER.
 *
 * 🔴 WHY THIS IS NOT SIMPLY "SWITCH TO THE VENDOR'S WAY".  `NET-70`'s
 * `n_dsync` detector -- which has a three-state positive control and has read
 * 0 through every wedge -- measures the two hardware POSITION registers.  It
 * cannot see what the engine wrote into a descriptor.  Swapping the harvest
 * to follow the pointer would REMOVE this class of fault rather than observe
 * it, and would leave `n_dsync` non-zero as a NORMAL reading with nothing
 * left that distinguishes normal from broken.  `SPEC.md` `NET-82` says the
 * cost has to be written down before the change is made; so the change is
 * behind `nic_ph_follow`, and the counters below are collected in BOTH
 * modes.  `n_ph_diff` is the finding; `n_ph_chk` is its denominator.
 *
 * 🔄 1.3, 2026-09-22: THE DEFAULT IS NOW 1, AND THE COST IS PAID RATHER
 * THAN WAIVED.  `NET-82`'s condition was that the cost be written down
 * first; `NET-102` and `NET-103` (seating 37) are that writing-down.  What
 * is given up is real and is stated here: following the pointer REMOVES
 * this fault class rather than observing it, so `n_dsync` is no longer a
 * quantity whose zero means anything about this path.
 *
 * 🟢 What replaces it is NOT an argument, it is two properties of the
 * code.  (a) The comparison at `nic_ph_class()` is UNCONDITIONAL -- the
 * switch picks which answer to return, not whether to look -- so
 * `n_ph_chk` and `n_ph_diff` count the same thing in both modes and the
 * fault class stays visible in the default build.  (b) `phfollow 0` still
 * reaches the old path, and it has a MEASURED signature to be recognised
 * by: 0.04-0.07 Mbit/s against 17 Mbit/s, `NET-102`.
 *
 * 🔴 What is lost is a property of the TEXT, and it is named rather than
 * quietly dropped: while the default was 0, every return in that mode was
 * literally `nic_dw(nic_rx_mb, i, 3)`, so *the default is today's
 * behaviour* could be read off the source.  It cannot any more.  The
 * replacement is weaker in kind and stronger in evidence: from 1.4 a boot
 * capture carries `RLXFW-N7` (1.3 said so, emitted none); modes differ 250x.
 *
 * 🔴 THE BOUNDS TEST IS NOT DEFENSIVE PROGRAMMING, IT IS THE SAFETY
 * ARGUMENT.  `ph0` is a word a DMA engine wrote into memory this driver does
 * not otherwise validate.  Dereferencing it unchecked is the same shape as
 * the mechanism `NET-64`'s retracted draft feared -- and here it is cheap to
 * close by construction: the follow is taken only when `ph0` lies inside this
 * driver's own mbuf descriptor array.  A pointer outside it is not a crash,
 * it is a reading, and `n_ph_bad` is where it lands.
 * ------------------------------------------------------------------------ */
static int		 nic_ph_follow = 1;	/* 1 = follow ph_mbuf; NET-102 */
/* NET-67 H1.  How many TX ring bases `arm` writes: 1 (today) or 4. */
static int		 nic_tx_rings = 1;
static u32		 nic_idle_ring;		/* one word, CPU-owned, WRAP */
static u32		 nic_idle_ph;		/* its pkthdr, never read     */
/* R6-4 ethtool.  `n_et_link` is the denominator: without it `et_link_last`
 * cannot tell "no jack is live" from "nobody ever asked". */
static unsigned long	 nic_n_et_link;
static u32		 nic_et_link_last = 0xFFFFFFFFu;
static unsigned long	 nic_n_ph_chk;		/* the denominator */
static unsigned long	 nic_n_ph_diff;		/* w0 != &rx_mb[i] */
static unsigned long	 nic_n_ph_bad;		/* w0 outside the mbuf array */
static unsigned long	 nic_n_ph_used;		/* harvests that FOLLOWED it */
static u32		 nic_ph_first_w0;
static u32		 nic_ph_first_exp;
static unsigned long	 nic_ph_first_nrx;
static u32		 nic_ph_last;		/* the raw w0, last harvest  */
static u32		 nic_ph_last_bf;	/* the m_data it resolved to */
static unsigned int	 nic_ph_last_j;		/* the slot it named	     */
/* 🔴 `nic_ph_last_bf` is assigned ONLY on the SKEW branch and
 * `nic_ph_last_j` on EVERY call, so the two adjacent dump lines describe
 * different events whenever the last frame was an AGREE -- and no field
 * said which case a dump was in.  量 `CORRECTIONS-block40.md` § 5.3: the
 * dereference identity this driver's own comment states held in 10 of 25
 * dumps and failed in 15, tracking the windows where `n_ph_diff` did not
 * move.  This field is written unconditionally beside `nic_ph_last_j`, so
 * a reader can tell the cases apart.  It is ADDED rather than moving
 * `nic_ph_last_j`, because moving it would change the meaning of a field
 * 25 committed dumps already carry. */
static int		 nic_ph_last_cls = -1;	/* AGREE/SKEW/BAD, always  */
static int		 nic_ph_test_cls = -1;	/* `phtest`'s answer	     */
static unsigned int	 nic_ph_test_j;
static int		 nic_ph_test_seen;

/* `nic_ph_buf()` itself is defined with the harvest path below, because it
 * calls the descriptor accessors, which are declared after this block. */

/* s32a.  The switch, and six readings that make its effect falsifiable.
 *
 *   tx_mode            0 = netif_stop_queue (today), 1 = the vendor's contract
 *   n_tx_full          times nic_xmit found its slot engine-owned.  Counted in
 *                      BOTH modes, so the two modes are compared on the same
 *                      denominator rather than on two different ones.
 *   n_tx_retry         total OWN re-reads across all calls (mode 1 only)
 *   tx_retry_max_seen  the most re-reads any single call needed.  This is what
 *                      says whether NIC_TX_RETRY_MAX was ever approached.
 *   n_tx_recovered     calls where the engine returned the slot before the
 *                      bound.  🔴 THIS IS THE ONE THAT ANSWERS AN OPEN
 *                      QUESTION: > 0 means the engine resumes by itself, which
 *                      no reading in this project has ever been able to see,
 *                      because the queue-stop killed the interface at the first
 *                      full ring and nothing transmitted again.
 *   n_tx_drop_full     frames dropped after the bound (mode 1 only)
 *
 * `n_tx_full` is kept separate from `n_xmit_busy` for the same reason
 * `n_tx_stop` already is: one counts an OBSERVATION of ring state, the other a
 * RETURN VALUE, and in mode 1 there is no BUSY return at all -- so a later
 * reader who merged them would find n_xmit_busy 0 and conclude the ring never
 * filled. */
static int           nic_tx_mode = NIC_TXMODE_STOPQ;
static unsigned long nic_n_tx_full;
static unsigned long nic_n_tx_retry;
static unsigned long nic_tx_retry_max_seen;
static unsigned long nic_n_tx_recovered;
static unsigned long nic_n_tx_drop_full;

/* s32a.  Which context nic_xmit is called from.  No behaviour depends on this;
 * it exists because mode 1 spins with interrupts already disabled by the
 * spin_lock_irqsave below, and "is that safe here" is a question about the
 * caller's context that this project has never measured on this die. */
static unsigned long nic_n_xmit_hardirq;
static unsigned long nic_n_xmit_softirq;
static unsigned long nic_n_xmit_process;

static const u8 nic_mac[6] = { 0x02, 0x52, 0x4C, 0x58, 0x46, 0x57 };

/* ------------------------------------------------------------------------
 * Register access.  `CKSEG1ADDR`, not the bare `KSEG1ADDR` -- 11 of the 13
 * uses across rlxfw's drivers are `CKSEG1ADDR` and the two that are not are
 * in the newest file, so matching the newest file would propagate the
 * outlier.
 * ------------------------------------------------------------------------ */
static inline void __iomem *nic_reg(unsigned int off)
{
	return (void __iomem *)CKSEG1ADDR(NIC_PHYS + off);
}

static u32 nic_rd(unsigned int off)
{
	u32 v = __raw_readl(nic_reg(off));

	nic_n_reads++;
	return v;
}

/* THE ONLY WRITE PATH.  The guard is ordered BEFORE the store and the
 * counter after it, so `n_writes` counts writes rather than counting callers
 * who remembered; and `n_refused` exists so that `n_writes == 0` is a
 * falsifiable reading rather than an absence.
 *
 * The offset allow-list is a second layer.  This driver owns one 0x68-byte
 * register block and a typo in a verb argument must not reach the timer at
 * 0xB8003100, which is 0x2F00 away in the SAME peripheral window. */
static int nic_wr(unsigned int off, u32 v)
{
	if (!nic_unlocked) {
		nic_n_refused++;
		return -EPERM;
	}
	if (off > NIC_CPUTPDCR3 || (off & 3)) {
		nic_n_refused++;
		return -ENODEV;
	}
	__raw_writel(v, nic_reg(off));
	nic_n_writes++;
	return 0;
}

/* Descriptor accessors.  A descriptor is 6 words at a KSEG1 address. */
static inline u32 nic_dw(u32 base, unsigned int idx, unsigned int word)
{
	return __raw_readl((void __iomem *)(base + idx * NIC_DESC_BYTES
					    + word * 4));
}

static inline void nic_dw_set(u32 base, unsigned int idx, unsigned int word,
			      u32 v)
{
	__raw_writel(v, (void __iomem *)(base + idx * NIC_DESC_BYTES
					 + word * 4));
}

static inline u32 nic_re(u32 ring, unsigned int idx)
{
	return __raw_readl((void __iomem *)(ring + idx * 4));
}

static inline void nic_re_set(u32 ring, unsigned int idx, u32 v)
{
	__raw_writel(v, (void __iomem *)(ring + idx * 4));
}

/* ------------------------------------------------------------------------
 * The interrupt handler.
 *
 * Shape 讀 from `rtl_nic.c:3729-3731`: read CPUIISR, write it straight back
 * (W1C), THEN mask it with CPUIIMR.  Reading before clearing and clearing the
 * whole word is what makes a shared-status register safe; masking afterwards
 * is only for deciding what to do.
 *
 * 🔴 It must stay short.  `FW-45`/`CLK-28`: this board runs a watchdog that
 * bites at ~1.33 s under Linux, kicked every 10 ms by the vendor's tick, so a
 * long interrupt-blocked window resets the board.  There is no work here
 * beyond counters for exactly that reason -- the frames are harvested by a
 * verb, in process context, under no deadline.
 * ------------------------------------------------------------------------ */
/* Forward declarations.  R6-4's netdev layer is written next to the ISR it
 * belongs with, and it calls the R6-3 primitives, which are defined below it
 * because that is the order they were written and measured in.  Declaring
 * rather than reordering keeps every line the ladder ran against where it
 * was. */
static int nic_do_alloc(void);
static int nic_do_arm(void);
static int nic_do_engine(int on);
static void nic_refill(unsigned int i);

/* R6-4a.  Restart the transmit queue if -- and only if -- the slot that
 * `nic_xmit` will look at next is CPU-owned again.
 *
 * 🔴 THE TEST IS A LEVEL, NOT AN EDGE, AND THAT IS THE WHOLE DESIGN.  The
 * obvious form is "the ISR saw TX_DONE, therefore wake", and an edge can
 * be consumed by an ISR invocation that runs while the queue is not yet
 * stopped -- after which no further edge is owed and the queue stays
 * stopped for the life of the interface.  This form re-evaluates the
 * condition `nic_xmit` itself tests, on EVERY interrupt whatever raised
 * it, so a lost TX_DONE costs a delay until the next interrupt of any
 * kind instead of costing the interface.
 *
 * 🟢 That the source exists at all is 量 on this die and not assumed.
 * `bench/2026-09-19b/C19-nic6.log` is a single `tx` verb with `n_rx 0`,
 * and it reads `n_irq 1` with `last_iisr 0000320E` -- bits 1 and 2
 * (TX_ALL_DONE) and bit 9 (TX_DONE).  One transmit, one interrupt, TX
 * completion in its status word.  `seen_iisr` carries the same bits in
 * every later capture of that seating.
 *
 * Cost in interrupt context: one KSEG1 read, one bit test, and on the
 * rare taken branch a `test_and_clear_bit` plus a softirq raise.
 * Bounded, no loop -- `FW-45`'s ~1.33 s hardware watchdog is nowhere
 * near.  量 the config this builds under: `CONFIG_CPU_HAS_LLSC` is
 * ABSENT, so `test_and_clear_bit` takes arch/rlx's `raw_local_irq_save`
 * fallback (`arch/rlx/include/asm/bitops.h`, the `#else` of the
 * `#ifdef CONFIG_CPU_HAS_LLSC` pairs) -- not an `ll`/`sc` pair, and so
 * not the `simulate_llsc` emulator either.  `napi_schedule_prep` in the
 * handler below already does the same class of operation, 12,623 times
 * in `bench/2026-09-19b/C58-afterflood2.log`.
 *
 * ⚠️ `nic_tx_idx` is read here with no lock.  量: this image is built
 * `# CONFIG_SMP is not set` and `CONFIG_PREEMPT_NONE=y`, and the only
 * writer is inside `nic_xmit`'s `spin_lock_irqsave`, which on that
 * configuration is a `local_irq_save` -- so this handler cannot observe
 * a half-updated index.  UNDER SMP OR PREEMPTION THAT IS FALSE and this
 * function would have to take `nic_lock`. */
static int nic_tx_try_wake(void)
{
	if (!nic_ndev || !nic_ndev_up || !nic_allocated)
		return 0;
	/* s99a.  The recovery below tears the rings down and puts them back,
	 * and between `arm` and `engine on` this function would see every TX
	 * slot CPU-owned and wake a queue whose engine is off -- after which
	 * `nic_xmit` drops the frame at its `!nic_engine_on` gate.  Not fatal
	 * and it would be counted, but it is a second variable inside the one
	 * experiment this image exists for.  One flag removes it.  The window
	 * is real: the recovery runs in softirq and this runs in hardirq. */
	if (nic_recov_busy)
		return 0;
	if (!netif_queue_stopped(nic_ndev))
		return 0;
	if (nic_re(nic_tx_ring, nic_tx_idx) & NIC_DESC_OWN)
		return 0;

	/* s99a.  The cheap path won, so the stall timer is not owed a firing.
	 * `del_timer` and NOT `del_timer_sync`: this runs in interrupt context,
	 * where the _sync form may not be called. */
	if (nic_recov_timer_ready)
		del_timer(&nic_recov_timer);

	nic_n_tx_wake++;
	netif_wake_queue(nic_ndev);
	return 1;
}

/* s99a.  Arm the stall timer.  Called from `nic_xmit`'s stop path, i.e. at
 * the one transition that can begin a stall, and only after the post-stop
 * re-test has already failed -- so a stop that the engine undid within the
 * same critical section never arms anything.
 *
 * ⚠️ `mod_timer` is called with `nic_lock` held and interrupts off.  That is
 * safe -- it takes the timer base's own lock, which nothing here holds -- and
 * it is the reason the arm is not done after the unlock: between the unlock
 * and the arm, the ISR can run, wake the queue and `del_timer` a timer that
 * does not exist yet, leaving it armed over a queue that is already running.
 * The spurious branch in `nic_recov_fn` would catch that, but catching it is
 * worse than not creating it. */
static void nic_recov_arm(void)
{
	if (!nic_recov_mode || !nic_recov_timer_ready)
		return;
	nic_n_recov_arm++;
	nic_recov_j_arm = jiffies;
	mod_timer(&nic_recov_timer, jiffies + msecs_to_jiffies(nic_recov_ms));
}

static void nic_recov_disarm(void)
{
	if (nic_recov_timer_ready)
		del_timer(&nic_recov_timer);
}

/* s99a.  The recovery itself -- `NET-101`'s three calls, from inside the
 * driver for the first time.
 *
 * Runs in softirq (timer) context.  `nic_do_arm()` takes `nic_lock` with
 * interrupts off for its 52 uncached descriptor stores, which is the same
 * lock and the same cost `nic_xmit` already pays for up to 1518 `writeb`s, so
 * `FW-45`'s ~1.33 s watchdog is nowhere near.  `nic_poll` also runs in
 * softirq, so on this image -- `# CONFIG_SMP is not set`, `CONFIG_PREEMPT_NONE=y`
 * -- the two cannot interleave. */
static void nic_recov_fn(unsigned long data)
{
	int rc0, rc1, rc2;

	if (!nic_recov_mode)
		return;
	if (!nic_ndev || !nic_ndev_up || !nic_allocated)
		return;

	/* THE SAME LEVEL `:754` TESTS, re-evaluated here.  If the engine
	 * retired the slot after the timer was armed but before it fired, this
	 * is not a stall and nothing is touched. */
	if (!netif_queue_stopped(nic_ndev) ||
	    !(nic_re(nic_tx_ring, nic_tx_idx) & NIC_DESC_OWN)) {
		nic_n_recov_spurious++;
		return;
	}

	nic_n_recov_fire++;
	nic_recov_j_fire = jiffies;
	nic_recov_busy = 1;

	/* ORDER IS LOAD-BEARING: `engine off` FIRST.  `NET-64` hard-hung this
	 * board -- 0 console bytes for 112 minutes -- by arming a running
	 * engine.  Each step is skipped if the one before it failed, so a
	 * refusal cannot leave the ring half re-established. */
	rc0 = nic_do_engine(0);
	rc1 = rc0 ? 1 : nic_do_arm();
	rc2 = rc1 ? 1 : nic_do_engine(1);
	nic_recov_rc[0] = rc0;
	nic_recov_rc[1] = rc1;
	nic_recov_rc[2] = rc2;

	if (rc0 || rc1 || rc2) {
		nic_n_recov_fail++;
		nic_recov_busy = 0;
		return;
	}
	nic_n_recov_ok++;

	/* `arm` zeroed both indices and handed every TX slot back, so the
	 * level is true and the queue can run.
	 *
	 * 🔴 THIS IS A DEPARTURE FROM WHAT `NET-101` MEASURED AND IT IS
	 * DELIBERATE.  By hand, the queue stayed stopped after the three writes
	 * and was woken only when the host's next ARP arrived and `:754` saw
	 * the freed ring -- `tx_stopped 1 / n_tx_wake 0` before the ping,
	 * `0 / 1` after.  That is fine when someone is pinging and useless when
	 * nothing is: a TX-wedged board may have nothing left to talk to it.
	 * The wake is counted SEPARATELY from `n_tx_wake` so the two paths stay
	 * distinguishable in a dump. */
	nic_recov_busy = 0;
	if (netif_queue_stopped(nic_ndev)) {
		nic_n_recov_wake++;
		netif_wake_queue(nic_ndev);
	}
}

static irqreturn_t nic_isr(int irq, void *dev_id)
{
	u32 isr;

	isr = __raw_readl(nic_reg(NIC_CPUIISR));
	__raw_writel(isr, nic_reg(NIC_CPUIISR));	/* W1C */

	nic_last_iisr = isr;
	nic_seen_iisr |= isr;
	nic_n_irq++;

	if (!isr)
		nic_n_irq_spurious++;

	/* R6-4: NAPI, and the ORDER here is the whole of it.
	 *
	 * `napi_schedule_prep` first, so that if a poll is already scheduled
	 * or running this interrupt adds nothing and, crucially, does NOT
	 * mask -- masking without scheduling is how an interface goes deaf
	 * with every counter looking healthy.
	 *
	 * The mask goes down BEFORE `__napi_schedule`: between those two the
	 * poll cannot yet be running, so nothing can race the unmask that
	 * `nic_poll` does at the end.  The reverse order has a window in
	 * which the poll completes and unmasks, and then this line masks
	 * again with no poll left to undo it.
	 *
	 * 🔴 Written with `__raw_writel` and not `nic_wr` deliberately: this
	 * is interrupt context, and `nic_wr` takes the unlock decision and
	 * bumps a non-atomic counter.  The write guard's job is to stop a
	 * BOOT from writing, and by the time an interrupt can arrive the
	 * unlock has already been given; making n_writes racy would cost a
	 * measurement to protect nothing. */
	/* 🔴 The condition is NIC_IP_RX_WORK and not RX_DONE alone, for the
	 * reason NIC_IIMR_LADDER's comment records: a descriptor run-out means
	 * there are filled descriptors waiting AND no free ones, which is
	 * exactly when a poll is most needed and is precisely the case the
	 * first version of this driver could not see. */
	if (nic_ndev_up && (isr & NIC_IP_RX_WORK)) {
		if (napi_schedule_prep(&nic_napi)) {
			u32 m = __raw_readl(nic_reg(NIC_CPUIIMR));

			__raw_writel(m & ~(NIC_IE_RX_DONE_ALL |
					   NIC_IE_PKTHDR_RUNOUT |
					   NIC_IE_MBUF_RUNOUT),
				     nic_reg(NIC_CPUIIMR));
			__napi_schedule(&nic_napi);
		}
	}

	/* R6-4a.  The TX-queue wake, placed AFTER the NAPI block so that
	 * block's mask/schedule ordering -- which its own comment says is
	 * the whole of it -- is not disturbed.  Deliberately NOT gated on
	 * `isr & NIC_IE_TX_DONE_ALL`; see nic_tx_try_wake(). */
	nic_tx_try_wake();

	return IRQ_HANDLED;
}

/* ------------------------------------------------------------------------
 * R6-4: the NAPI poll, the transmit path, and the net_device.
 * ------------------------------------------------------------------------ */

/* Harvest at most `budget` frames into sk_buffs.  Returns how many.
 *
 * ⚠️ The copy is byte-wise and that is a MEASUREMENT PROBLEM DEFERRED, not an
 * oversight.  The DMA buffers are 2 mod 4 (`NIC_RX_OFFSET`, which is what
 * makes the IP header land aligned behind a 14-byte Ethernet header), so a
 * word-at-a-time copy out of them would be an unaligned load, which on this
 * core is a fault and not a slow path.  Making it fast means either aligning
 * the buffer and unaligning the IP header, or using the unaligned load/store
 * instructions -- and which of those is worth it is an R6-5 question with a
 * number attached, so it is not guessed at here. */
/* Delta between the two RX positions, in slots, on the ring's own modulus.
 *
 * Both arguments are ABSOLUTE addresses -- `SPEC.md` `NET-32` and the
 * `rpdcr0_pos` note further down: these registers read back the engine's
 * CURRENT POSITION, not the base this driver wrote.  The index is
 * `(pos - base) / 4`, which is the arithmetic `NET-61` used to turn
 * `A15B8000`/`A15B8020` into its nine-row table.
 *
 * SEPARATED FROM THE REGISTER READ ON PURPOSE, so the same arithmetic can be
 * exercised with typed values through `dsynctest`.  A detector that has only
 * ever reported 0 is a claim with no control.
 *
 * The subtraction is unsigned and wraps mod 2^32; NIC_RX_DESC is 8, which
 * divides 2^32, so the `%` recovers the right slot difference.  ⚠️ On an
 * 8-slot ring 4 is its own negative, so this reports HOW FAR apart and not
 * WHICH ring leads -- `NET-61`'s residual, which this function does not
 * close. */
static unsigned int nic_dsync_calc(u32 rp, u32 rm)
{
	unsigned int pi = ((rp - nic_rx_ring) / 4) % NIC_RX_DESC;
	unsigned int mi = ((rm - nic_mb_ring) / 4) % NIC_RX_DESC;

	return (pi - mi) % NIC_RX_DESC;
}

/* One check.  Reads each position ONCE and passes those same two values to
 * both the comparison and the first-occurrence record, so what is recorded is
 * what was compared and not a second, later read. */
static void nic_dsync_check(void)
{
	u32 rp, rm;
	unsigned int d;

	if (!nic_allocated)
		return;

	rp = nic_rd(NIC_CPURPDCR0);
	rm = nic_rd(NIC_CPURMDCR0);
	d = nic_dsync_calc(rp, rm);

	nic_n_dsync_chk++;
	if (!d)
		return;

	if (!nic_n_dsync) {
		nic_dsync_first_rp = rp;
		nic_dsync_first_rm = rm;
		nic_dsync_first_nrx = nic_n_rx;
		nic_dsync_first_d = d;
	}
	nic_n_dsync++;
	nic_dsync_last_d = d;
}

/* One inspection.  Returns the buffer address to use and records what it
 * saw.  Called from both harvest paths so the two cannot drift apart -- the
 * failure `nic_dsync_calc` was separated out to avoid. */
/* THE ARITHMETIC HALF, SPLIT OUT SO IT CAN BE DRIVEN WITH TYPED VALUES.
 * Pure: it touches no hardware and reads one ring base.  `phtest` puts
 * declared values through this exact code, for the reason `dsynctest` exists
 * beside `n_dsync` -- a detector that has only ever reported AGREE is a claim
 * with no control, and `n_ph_diff 0` would otherwise be unfalsifiable.
 *
 * The stride is `NIC_DESC_BYTES` and that is rlxfw's own mbuf stride, not
 * `sizeof(struct rtl_mBuf)` = 28.  See the note at NIC_DESC_BYTES. */
static int nic_ph_class(u32 w0, unsigned int i, unsigned int *j_out)
{
	*j_out = i;
	if (w0 == nic_rx_mb + i * NIC_DESC_BYTES)
		return NIC_PHC_AGREE;
	if (w0 < nic_rx_mb ||
	    w0 >= nic_rx_mb + NIC_RX_DESC * NIC_DESC_BYTES ||
	    ((w0 - nic_rx_mb) % NIC_DESC_BYTES) != 0)
		return NIC_PHC_BAD;
	*j_out = (w0 - nic_rx_mb) / NIC_DESC_BYTES;
	return NIC_PHC_SKEW;
}

/* THE HARDWARE HALF.  Resolve the data buffer for the frame in RX pkthdr slot
 * `i`, and measure whether the two routes to it disagree.
 *
 * 🔴 THE COMPARISON IS UNCONDITIONAL AND THE SWITCH ONLY PICKS THE ANSWER.
 * Putting the comparison inside the switch would confound "the pointer was
 * different" with everything else `phfollow 1` does; this way a single boot in
 * the DEFAULT mode already says whether the switch can matter at all.
 *
 * 🔴 And in mode 0 every return below is literally `nic_dw(nic_rx_mb, i, 3)`
 * -- the expression this replaced -- so "the default is today's behaviour" is
 * a property of the text rather than of a test.
 *
 * The two bound tests are separate because they fail for different reasons: a
 * `w0` outside the descriptor array means word 0 is not a live `ph_mbuf` at
 * all (or the engine writes a PHYSICAL address where this driver wrote
 * KSEG1 -- `ph_last` prints the value so that case is read rather than
 * guessed); a `bf` outside the RX buffer region means word 3 of an otherwise
 * legitimate mbuf is not a buffer of ours. */
static u32 nic_ph_buf(unsigned int i)
{
	u32 w0 = nic_dw(nic_rx_ph, i, 0) & NIC_DESC_ADDR;
	unsigned int j;
	int cls;
	u32 bf;

	nic_n_ph_chk++;
	nic_ph_last = w0;
	cls = nic_ph_class(w0, i, &j);
	nic_ph_last_j = j;
	nic_ph_last_cls = cls;	/* unconditional -- see the declaration */

	if (cls == NIC_PHC_AGREE)
		return nic_dw(nic_rx_mb, i, 3);

	if (!nic_n_ph_diff) {
		nic_ph_first_w0  = w0;
		nic_ph_first_exp = nic_rx_mb + i * NIC_DESC_BYTES;
		nic_ph_first_nrx = nic_n_rx;
	}
	nic_n_ph_diff++;

	if (cls == NIC_PHC_BAD) {
		nic_n_ph_bad++;
		return nic_dw(nic_rx_mb, i, 3);
	}

	bf = nic_dw(nic_rx_mb, j, 3);
	nic_ph_last_bf = bf;
	/* RX buffers are the FIRST NIC_RX_DESC of the buffer region; the TX
	 * half is never a legitimate RX m_data. */
	if (bf < nic_bufs || bf >= nic_bufs + NIC_RX_DESC * NIC_BUF_SZ) {
		nic_n_ph_bad++;
		return nic_dw(nic_rx_mb, i, 3);
	}

	if (nic_ph_follow) {
		nic_n_ph_used++;
		return bf;
	}
	return nic_dw(nic_rx_mb, i, 3);
}

static int nic_napi_harvest(int budget)
{
	int done = 0;

	while (done < budget) {
		unsigned int i = nic_rx_idx;
		u32 e = nic_re(nic_rx_ring, i);
		u32 w1, len, bf, k;
		struct sk_buff *skb;

		if (e & NIC_DESC_OWN)
			break;

		w1 = nic_dw(nic_rx_ph, i, 1);
		len = NIC_PH_LEN(w1);
		len = (len >= 4) ? (len - 4) : len;	/* ph_len carries FCS */
		if (len > NIC_BUF_SZ - NIC_RX_OFFSET)
			len = 0;

		nic_last_rx_ph1 = w1;
		nic_last_rx_ph3 = nic_dw(nic_rx_ph, i, 3);
		nic_last_rx_ph4 = nic_dw(nic_rx_ph, i, 4);

		bf = nic_ph_buf(i);		/* s99a (c): was nic_dw(nic_rx_mb, i, 3) */
		skb = len ? dev_alloc_skb(len + 2) : NULL;
		if (skb) {
			skb_reserve(skb, 2);
			for (k = 0; k < len; k++)
				skb->data[k] =
					__raw_readb((void __iomem *)(bf + k));
			skb_put(skb, len);
			skb->protocol = eth_type_trans(skb, nic_ndev);
			nic_ndev->stats.rx_packets++;
			nic_ndev->stats.rx_bytes += len;
			netif_receive_skb(skb);
		} else {
			nic_n_skb_fail++;
			nic_ndev->stats.rx_dropped++;
		}

		nic_refill(i);
		nic_rx_idx = (i + 1) % NIC_RX_DESC;
		nic_n_rx++;
		done++;
	}
	return done;
}

static int nic_poll(struct napi_struct *napi, int budget)
{
	int done;

	nic_n_napi_poll++;
	/* BEFORE the harvest, so it observes the state the harvest is about
	 * to act on rather than the state the harvest left behind. */
	nic_dsync_check();
	done = nic_napi_harvest(budget);

	/* Under budget means the ring ran dry, which is the only safe moment
	 * to say the poll is finished.  `napi_complete` BEFORE the unmask:
	 * if a frame lands in between, the interrupt it raises finds NAPI not
	 * scheduled and schedules it, which is correct.  Unmasking first
	 * leaves a window where an interrupt arrives, `napi_schedule_prep`
	 * refuses because this poll has not completed yet, and the frame
	 * waits for the next unrelated interrupt -- a stall that no counter
	 * of drops would show. */
	if (done < budget) {
		unsigned long flags;
		u32 m;

		napi_complete(napi);
		nic_n_napi_complete++;

		spin_lock_irqsave(&nic_lock, flags);
		/* Clear any run-out that latched while this poll was draining
		 * the ring, BEFORE unmasking.  The descriptors have just been
		 * handed back, so the condition is no longer true; leaving the
		 * stale status set and then unmasking would take an interrupt
		 * for a run-out that is already over. */
		__raw_writel(NIC_IE_PKTHDR_RUNOUT | NIC_IP_MBUF_RUNOUT,
			     nic_reg(NIC_CPUIISR));
		/* s99a: bounded by `nic_iimr_base` and no longer by the
		 * compiled constant.  This one line is why the run-out mask
		 * A/B needs an image: with the old form, a mask written from
		 * outside was restored here by the next arriving packet, and
		 * an `echo read` -- which puts nothing on the wire -- read it
		 * back unchanged and called that a pass. */
		m = __raw_readl(nic_reg(NIC_CPUIIMR));
		__raw_writel(m | (nic_iimr_base &
				  (NIC_IE_RX_DONE_ALL | NIC_IE_PKTHDR_RUNOUT |
				   NIC_IE_MBUF_RUNOUT)), nic_reg(NIC_CPUIIMR));
		spin_unlock_irqrestore(&nic_lock, flags);
	}
	return done;
}

static int nic_xmit(struct sk_buff *skb, struct net_device *dev)
{
	unsigned int i;
	unsigned long flags;
	u32 e, bf, len, k, icr, wrap, ph;

	/* s32a: context census.  Before the early return, so the denominator is
	 * every call rather than every call that got as far as the ring. */
	if (in_irq())
		nic_n_xmit_hardirq++;
	else if (in_softirq())
		nic_n_xmit_softirq++;
	else
		nic_n_xmit_process++;

	if (!nic_engine_on) {
		dev_kfree_skb(skb);
		dev->stats.tx_dropped++;
		return NETDEV_TX_OK;
	}

	spin_lock_irqsave(&nic_lock, flags);

	i = nic_tx_idx;
	e = nic_re(nic_tx_ring, i);
	if (e & NIC_DESC_OWN)
		nic_n_tx_full++;

	/* s32a MODE 1 -- the vendor's ring-full contract, 讀 rtl_nic.c:5161-5171.
	 *
	 * Poll the OWN bit of the slot we want, bounded; if it frees, fall
	 * through and transmit; if it does not, DROP the frame and report
	 * NETDEV_TX_OK.  The queue is never stopped, so there is nothing that
	 * has to be woken, so there is no liveness dependency on an interrupt.
	 *
	 * 🔴 Spinning with interrupts off is correct HERE and would not be in
	 * general: the OWN bit is cleared by the engine's own DMA write, not by
	 * anything this CPU runs, so the condition can change while interrupts
	 * are masked.  That is the same reason the vendor's swNic_txDone polls
	 * inside local_irq_save (rtl865xc_swNic.c:795-833).
	 *
	 * ⚠️ WHAT THIS DOES NOT DO: it does not make the engine resume, and it
	 * does not reclaim anything -- this driver frees the skb synchronously
	 * at the end of nic_xmit, so there is no completion queue to drain.
	 * The only thing the vendor's swNic_txDone does for us is the OWN-bit
	 * read, and that is what this loop is. */
	if ((e & NIC_DESC_OWN) && nic_tx_mode == NIC_TXMODE_VENDOR) {
		unsigned int r = 0;

		while (e & NIC_DESC_OWN) {
			if (++r > NIC_TX_RETRY_MAX) {
				nic_n_tx_retry += r;
				if (r > nic_tx_retry_max_seen)
					nic_tx_retry_max_seen = r;
				nic_n_tx_drop_full++;
				spin_unlock_irqrestore(&nic_lock, flags);
				dev_kfree_skb(skb);
				dev->stats.tx_dropped++;
				return NETDEV_TX_OK;
			}
			e = nic_re(nic_tx_ring, i);
		}
		nic_n_tx_retry += r;
		if (r > nic_tx_retry_max_seen)
			nic_tx_retry_max_seen = r;
		nic_n_tx_recovered++;
		/* the slot is ours; fall through to the transmit below */
	}

	if (e & NIC_DESC_OWN) {
		/* The engine still owns this slot.  Stop the queue and tell
		 * the stack to retry -- do NOT drop, and do NOT free the skb,
		 * which the caller still owns after NETDEV_TX_BUSY. */
		netif_stop_queue(dev);
		nic_n_tx_stop++;
		nic_n_xmit_busy++;

		/* RE-TEST AFTER THE STOP.  The engine can retire this slot
		 * between the read above and the stop.
		 *
		 * 🔴 ON THIS BUILD THAT WINDOW CANNOT LOSE THE WAKE, AND WHAT
		 * CLOSES IT IS NOT IN THIS FILE.  量 `# CONFIG_SMP is not set`
		 * and `CONFIG_PREEMPT_NONE=y`, so the `spin_lock_irqsave`
		 * above is a `local_irq_save` and nic_isr cannot run inside
		 * it; the completion latches in CPUIISR, which is sticky W1C,
		 * and the interrupt is delivered the instant the unlock below
		 * restores the mask.  The ISR then finds the queue stopped and
		 * the slot free and wakes it.
		 *
		 * This re-test is here anyway for three reasons, none of which
		 * is the classic race: a correctness argument that rests on
		 * two Kconfig lines nobody reading this file can see is a bad
		 * place to leave it; it removes a whole interrupt's latency
		 * from the common case; and `n_tx_wake_race` then MEASURES how
		 * often the window is real instead of leaving it argued.
		 *
		 * Waking while returning NETDEV_TX_BUSY is correct, 讀
		 * `net/sched/sch_generic.c:124-178`: qdisc_restart requeues
		 * the skb and then zeroes its return ONLY if the queue is
		 * still stopped, so an un-stopped queue makes __qdisc_run loop
		 * and re-offer the same skb -- which now finds a free slot.
		 * That loop is bounded by its own `jiffies != start_time`. */
		e = nic_re(nic_tx_ring, i);
		if (!(e & NIC_DESC_OWN)) {
			nic_n_tx_wake_race++;
			netif_wake_queue(dev);
		} else {
			/* s99a.  The queue is stopped and the slot is still the
			 * engine's -- the one transition that can begin a stall.
			 * Arming here and not after the unlock is deliberate; see
			 * `nic_recov_arm()`. */
			nic_recov_arm();
		}

		spin_unlock_irqrestore(&nic_lock, flags);
		return NETDEV_TX_BUSY;
	}

	len = skb->len;
	if (len > NIC_BUF_SZ - NIC_RX_OFFSET - 8) {
		spin_unlock_irqrestore(&nic_lock, flags);
		dev_kfree_skb(skb);
		dev->stats.tx_dropped++;
		return NETDEV_TX_OK;
	}

	bf = nic_bufs + (NIC_RX_DESC + i) * NIC_BUF_SZ + NIC_RX_OFFSET;
	for (k = 0; k < len; k++)
		__raw_writeb(skb->data[k], (void __iomem *)(bf + k));
	/* 讀 `rtl865xc_swNic.c:718-721`: a runt is padded to 64 and the FCS is
	 * counted in ph_len.  Both are the ASIC's arithmetic. */
	while (len < 60) {
		__raw_writeb(0, (void __iomem *)(bf + len));
		len++;
	}

	nic_dw_set(nic_tx_mb, i, 3, bf);
	nic_dw_set(nic_tx_mb, i, 4, bf);
	nic_dw_set(nic_tx_mb, i, 2, NIC_MB_MK2(len, NIC_MB_FLAGS_INIT));
	nic_dw_set(nic_tx_mb, i, 5, NIC_MB_MK5(NIC_BUF_SZ - NIC_RX_OFFSET));

	nic_dw_set(nic_tx_ph, i, 1, NIC_PH_MK1(len + 4, 0, 0));
	/* ph_flags 0x8800 and portlist 0x3F are not chosen: they are what this
	 * die's own loader puts in a TX descriptor, 量
	 * `bench/2026-09-19b/X14-rings-post` word 3 of `A040FCE8` reading
	 * `8800003F` after a real transfer. */
	nic_dw_set(nic_tx_ph, i, 3, NIC_PH_MK3(NIC_PH_FLAGS_TX_DEFAULT, 0x3F));
	nic_dw_set(nic_tx_ph, i, 4, 0);

	wrap = (i == NIC_TX_DESC - 1) ? NIC_DESC_WRAP : 0;
	ph = nic_tx_ph + i * NIC_DESC_BYTES;
	nic_re_set(nic_tx_ring, i, ph | NIC_DESC_OWN | wrap);	/* OWN last */

	icr = __raw_readl(nic_reg(NIC_CPUICR));
	__raw_writel(icr | NIC_TXFD, nic_reg(NIC_CPUICR));	/* doorbell */

	nic_tx_idx = (i + 1) % NIC_TX_DESC;
	nic_n_tx++;
	nic_n_xmit++;
	spin_unlock_irqrestore(&nic_lock, flags);

	dev->stats.tx_packets++;
	dev->stats.tx_bytes += len;
	dev->trans_start = jiffies;
	dev_kfree_skb(skb);
	return NETDEV_TX_OK;
}

static int nic_ndo_open(struct net_device *dev)
{
	int rc;

	/* House rule 6 applies to this path too: every hardware write is
	 * behind the runtime unlock, including the ones an `ifconfig up`
	 * causes.  The device is not registered at boot, so nothing can reach
	 * here without a verb having been typed first -- but saying so with a
	 * refusal is worth more than saying it in a comment. */
	if (!nic_unlocked) {
		nic_n_refused++;
		return -EPERM;
	}

	if (!nic_allocated) {
		rc = nic_do_alloc();
		if (rc)
			return rc;
	}
	if (!nic_armed) {
		rc = nic_do_arm();
		if (rc)
			return rc;
	}
	if (!nic_irq_taken) {
		nic_irq_rc = request_irq(NIC_IRQ, nic_isr, IRQF_DISABLED,
					 "rtl819x-nic", &nic_lock);
		if (nic_irq_rc)
			return nic_irq_rc;
		nic_irq_taken = 1;
	}

	napi_enable(&nic_napi);
	nic_ndev_up = 1;

	rc = nic_do_engine(1);
	if (rc) {
		nic_ndev_up = 0;
		napi_disable(&nic_napi);
		return rc;
	}

	netif_start_queue(dev);
	rlxfw_mark("N-NDOPEN");
	return 0;
}

static int nic_ndo_stop(struct net_device *dev)
{
	netif_stop_queue(dev);
	nic_ndev_up = 0;
	/* s99a.  Before `napi_disable`, so a timer that fires during the
	 * teardown cannot find `nic_ndev_up` still set. */
	nic_recov_disarm();
	napi_disable(&nic_napi);
	nic_do_engine(0);
	if (nic_irq_taken) {
		free_irq(NIC_IRQ, &nic_lock);
		nic_irq_taken = 0;
	}
	rlxfw_mark("N-NDSTOP");
	return 0;
}

static struct net_device_stats *nic_ndo_stats(struct net_device *dev)
{
	return &dev->stats;
}

/* R6-4a.  The recovery of last resort, and an instrument.
 *
 * 讀 `rtl819x-nic.c:1654`: this driver has ALWAYS set
 * `dev->watchdog_timeo = 5 * HZ`.  讀 `net/sched/sch_generic.c:240-249`:
 * `__netdev_watchdog_up()` arms the timer only
 * `if (dev->netdev_ops->ndo_tx_timeout)` -- so until this line existed
 * that assignment was DEAD CODE and the watchdog was never started.  讀
 * `:227` of the same file: when it does fire it calls `ndo_tx_timeout`
 * with NO NULL check, so the pairing is not optional in either
 * direction.
 *
 * 量 that the handler can really be entered: `netif_carrier_ok()` is
 * `!test_bit(__LINK_STATE_NOCARRIER)` (`netdevice.h:1532-1535`), this
 * driver never calls `netif_carrier_off()`, and that bit has zero
 * occurrences in `net/core/dev.c` -- so the carrier precondition is
 * satisfied by default rather than by anything this driver does.
 *
 * IT TOUCHES NO HARDWARE.  Resetting the DMA engine from a timer, on a
 * part whose ingress path has wedged once with the mechanism
 * unidentified (`notes/nic-driver.md` § 6.2), would be a repair nobody
 * could afterwards distinguish from the fault.  It re-runs the same
 * level test the ISR runs, and counts the entry.
 *
 * `dev->trans_start` is deliberately NOT refreshed.  While the engine is
 * genuinely stuck this handler is re-entered every `watchdog_timeo`, so
 * `n_tx_timeout` reads as a RATE -- entries per 5 s of stall -- rather
 * than as a single event; and `n_tx_timeout 0` after a load is then the
 * evidence that the interrupt-driven wake never needed help.
 *
 * 量 the console cost, which is the thing that could have made this
 * unsafe under `FW-45`'s ~1.33 s hardware watchdog: `dev_watchdog`
 * guards the call with `WARN_ONCE`, and this image is built
 * `# CONFIG_BUG is not set`, under which `WARN(cond, fmt)` reduces to
 * `!!(cond)` (`include/asm-generic/bug.h:90-112`) -- no printk, no
 * dump_stack, zero bytes on a 38400 baud console.  A `loud` image would
 * print one backtrace, once. */
static void nic_ndo_tx_timeout(struct net_device *dev)
{
	nic_n_tx_timeout++;
	dev->stats.tx_errors++;
	nic_tx_try_wake();
}

/* ----------------------------------------------------------------------
 * ethtool.  `R6-4`'s *What it produces* column named *basic ethtool ops*
 * and this driver carried one occurrence of the word: a comment saying
 * there were none.
 *
 * 🔴 `get_link` is deliberately NOT `ethtool_op_get_link`.  That helper
 * is `netif_carrier_ok()` = `!test_bit(__LINK_STATE_NOCARRIER)`; this
 * driver never calls `netif_carrier_off()`, so the bit is never set and
 * the helper could only ever return 1.  `RUNSHEET.md:317` is the house
 * rule -- *a tool that always says 1 cannot fail* -- and a field that
 * cannot fail is not an observable.
 *
 * 🟢 What it reads instead is the switch's per-port LinkUp bits, which
 * the operator can flip with a cable.  That is the right SEMANTIC as well
 * as the testable one: 讀 + 量, the CPU port this driver serves has no
 * PHY behind it -- MDIO address 6 is silent while 0-4 answer, `PCRP6`'s
 * `EnablePHYIf` is clear, `PSRP6`'s EEE field is 0, and the CPU interface
 * lives in the SYSTEM window rather than the switch core's.  So `rlx0`'s
 * own link is up by construction and reporting it would be reporting a
 * constant.  What a user of `rlx0` wants to know is whether a jack is
 * live.
 *
 * ⚠️ It does NOT call `netif_carrier_on/off`.  Carrier gates the
 * datapath, and this image already carries the changes it exists to
 * test.  The coupling is named rather than taken: `ethtool rlx0` can
 * report no link while the interface still transmits, and that is a true
 * statement about a CPU port whose fabric link is independent of the
 * jacks.
 * ---------------------------------------------------------------------- */
static void nic_et_drvinfo(struct net_device *dev,
			   struct ethtool_drvinfo *di)
{
	strncpy(di->driver,   "rtl819x-nic", sizeof(di->driver) - 1);
	strncpy(di->version,  RTL819X_NIC_VERSION, sizeof(di->version) - 1);
	strncpy(di->bus_info, "platform", sizeof(di->bus_info) - 1);
}

static u32 nic_et_get_link(struct net_device *dev)
{
	int v = rtl819x_sw_any_link();

	nic_n_et_link++;
	if (v < 0)		/* switch not latched -- say no, never yes */
		v = 0;
	nic_et_link_last = (u32)v;
	return (u32)v;
}

static void nic_et_ringparam(struct net_device *dev,
			     struct ethtool_ringparam *rp)
{
	rp->rx_max_pending = NIC_RX_DESC;
	rp->tx_max_pending = NIC_TX_DESC;
	rp->rx_pending     = NIC_RX_DESC;
	rp->tx_pending     = NIC_TX_DESC;
}

static const struct ethtool_ops nic_ethtool_ops = {
	.get_drvinfo	= nic_et_drvinfo,
	.get_link	= nic_et_get_link,
	.get_ringparam	= nic_et_ringparam,
};

static const struct net_device_ops nic_netdev_ops = {
	.ndo_open		= nic_ndo_open,
	.ndo_stop		= nic_ndo_stop,
	.ndo_start_xmit		= nic_xmit,
	.ndo_get_stats		= nic_ndo_stats,
	.ndo_tx_timeout		= nic_ndo_tx_timeout,
	.ndo_validate_addr	= eth_validate_addr,
	.ndo_change_mtu		= eth_change_mtu,
};

/* ------------------------------------------------------------------------
 * alloc -- build the rings in memory.  NO hardware write happens here, which
 * is why it is a separate verb from `arm`: a ring that exists and is not
 * pointed at by any register can be dumped and checked by eye first.
 * ------------------------------------------------------------------------ */
static int nic_do_alloc(void)
{
	u32 need, base, p;
	unsigned int i;

	if (nic_allocated)
		return -EEXIST;

	/* rings + descriptors + buffers, with room to align the base to 4. */
	need = (NIC_RX_DESC * 4) * 2 + (NIC_TX_DESC * 4)
	     + (NIC_RX_DESC * NIC_DESC_BYTES) * 2
	     + (NIC_TX_DESC * NIC_DESC_BYTES) * 2
	     + (NIC_RX_DESC + NIC_TX_DESC) * NIC_BUF_SZ
	     + 4 + NIC_DESC_BYTES	/* NET-67 H1's idle TX ring */
	     + 64;

	nic_alloc_raw = kmalloc(need, GFP_KERNEL);
	if (!nic_alloc_raw)
		return -ENOMEM;
	nic_alloc_bytes = need;
	memset(nic_alloc_raw, 0, need);

	/* 🔴 The one cache operation in this driver, and it is here rather
	 * than anywhere else on purpose.  `kmalloc` handed back a KSEG0
	 * address; every access after this line is through KSEG1.  A dirty
	 * line left over the region would, at an unpredictable later moment,
	 * be written back OVER data the engine had already DMA'd.  That is
	 * `CPU-45`'s non-coherence in the direction that is easy to forget,
	 * and one write-back-invalidate before the alias is first used is the
	 * whole fix. */
	dma_cache_wback_inv((unsigned long)nic_alloc_raw, need);

	base = (((u32)(unsigned long)nic_alloc_raw) + 3) & ~3u;
	base = CKSEG1ADDR(CPHYSADDR(base));

	p = base;
	nic_rx_ring = p;	p += NIC_RX_DESC * 4;
	nic_mb_ring = p;	p += NIC_RX_DESC * 4;
	nic_tx_ring = p;	p += NIC_TX_DESC * 4;
	nic_rx_ph   = p;	p += NIC_RX_DESC * NIC_DESC_BYTES;
	nic_rx_mb   = p;	p += NIC_RX_DESC * NIC_DESC_BYTES;
	nic_tx_ph   = p;	p += NIC_TX_DESC * NIC_DESC_BYTES;
	nic_tx_mb   = p;	p += NIC_TX_DESC * NIC_DESC_BYTES;
	/* Buffers: NIC_RX_OFFSET is added per descriptor, not here, so the
	 * region itself stays aligned and only the DMA target is 2 mod 4 --
	 * which is what the loader's own rings look like on this die. */
	nic_bufs    = p;
	p += (NIC_RX_DESC + NIC_TX_DESC) * NIC_BUF_SZ;

	/* NET-67 H1's idle TX ring, carved LAST so not one address above it
	 * moves -- every base a frozen card predicts is unchanged, which is
	 * what keeps this image comparable with the ten before it. */
	nic_idle_ring = p;	p += 4;
	nic_idle_ph   = p;	p += NIC_DESC_BYTES;

	/* RX: pkthdr[i] <-> mbuf[i], mbuf[i] -> buffer[i], both rings owned by
	 * the engine, last entry wrapping.
	 *
	 * The ORDER within each descriptor does not matter here because
	 * nothing is armed yet.  It matters in `refill`, where it does happen
	 * in the vendor's order and says so. */
	for (i = 0; i < NIC_RX_DESC; i++) {
		u32 ph = nic_rx_ph + i * NIC_DESC_BYTES;
		u32 mb = nic_rx_mb + i * NIC_DESC_BYTES;
		u32 bf = nic_bufs + i * NIC_BUF_SZ + NIC_RX_OFFSET;
		u32 wrap = (i == NIC_RX_DESC - 1) ? NIC_DESC_WRAP : 0;

		nic_dw_set(nic_rx_ph, i, 0, mb);
		nic_dw_set(nic_rx_ph, i, 1, 0);
		nic_dw_set(nic_rx_ph, i, 2, 0);
		nic_dw_set(nic_rx_ph, i, 3, 0);
		nic_dw_set(nic_rx_ph, i, 4, 0);
		nic_dw_set(nic_rx_ph, i, 5, 0);

		nic_dw_set(nic_rx_mb, i, 0, 0);
		nic_dw_set(nic_rx_mb, i, 1, ph);
		nic_dw_set(nic_rx_mb, i, 2,
			   NIC_MB_MK2(0, NIC_MB_FLAGS_INIT));
		nic_dw_set(nic_rx_mb, i, 3, bf);
		nic_dw_set(nic_rx_mb, i, 4, bf);
		nic_dw_set(nic_rx_mb, i, 5,
			   NIC_MB_MK5(NIC_BUF_SZ - NIC_RX_OFFSET));

		nic_re_set(nic_rx_ring, i, ph | NIC_DESC_OWN | wrap);
		nic_re_set(nic_mb_ring, i, mb | NIC_DESC_OWN | wrap);
	}

	/* TX: owned by the CPU, no buffer attached -- which is exactly what
	 * the loader's idle TX rings look like on this die (`A040FE40`, whose
	 * m_data and m_extbuf are both zero). */
	for (i = 0; i < NIC_TX_DESC; i++) {
		u32 ph = nic_tx_ph + i * NIC_DESC_BYTES;
		u32 mb = nic_tx_mb + i * NIC_DESC_BYTES;
		u32 wrap = (i == NIC_TX_DESC - 1) ? NIC_DESC_WRAP : 0;

		nic_dw_set(nic_tx_ph, i, 0, mb);
		nic_dw_set(nic_tx_ph, i, 1, 0);
		nic_dw_set(nic_tx_ph, i, 2, 0);
		nic_dw_set(nic_tx_ph, i, 3,
			   NIC_PH_MK3(NIC_PH_FLAGS_TX_DEFAULT, 0));
		nic_dw_set(nic_tx_ph, i, 4, 0);
		nic_dw_set(nic_tx_ph, i, 5, 0);

		nic_dw_set(nic_tx_mb, i, 0, 0);
		nic_dw_set(nic_tx_mb, i, 1, ph);
		nic_dw_set(nic_tx_mb, i, 2,
			   NIC_MB_MK2(0, NIC_MB_FLAGS_INIT));
		nic_dw_set(nic_tx_mb, i, 3, 0);
		nic_dw_set(nic_tx_mb, i, 4, 0);
		nic_dw_set(nic_tx_mb, i, 5, 0);

		nic_re_set(nic_tx_ring, i, ph | wrap);	/* OWN clear = CPU */
	}

	nic_rx_idx = 0;
	nic_tx_idx = 0;
	nic_allocated = 1;
	rlxfw_markx("N-ALLOC", base);
	return 0;
}

/* arm -- point the hardware at the rings.  讀 `rtl865xc_swNic.c:1306-1384`:
 * the vendor writes all four TX bases, then all six RX pkthdr bases, then the
 * mbuf base, with interrupts off and no fence or read-back between them and
 * the later enable.
 *
 * Unused rings are written ZERO rather than left alone.  The loader leaves
 * `CPURPDCR1..5` at zero and the engine is content, so zero is a value this
 * die is known to accept for an unused ring -- which is better than leaving
 * the loader's stale `A040Fxxx` pointers in registers while the engine is
 * enabled. */
static int nic_do_arm(void)
{
	unsigned long flags;
	unsigned int i;
	int rc;

	if (!nic_allocated)
		return -ENXIO;
	if (nic_engine_on)
		return -EBUSY;

	/* THE WRITE GUARD IS ASKED HERE AND NOT BY THE FIRST `nic_wr` BELOW.
	 * The descriptor stores are `nic_re_set`/`nic_dw_set` and do not go
	 * through `nic_wr`, so a locked driver would flush the whole ring and
	 * THEN return -EPERM -- a refusal that has already done the thing it
	 * refused, and left the software index describing a ring the hardware
	 * is no longer pointed at.  That is the very skew this function was
	 * changed to remove, reproduced by the guard firing.  Reachable by
	 * typing: neither `alloc` nor `arm` has an unlock precondition.
	 * `n_refused` is incremented here because `nic_wr` is never reached. */
	if (!nic_unlocked) {
		nic_n_refused++;
		return -EPERM;
	}

	/* RE-ESTABLISH BOTH RINGS AND ZERO BOTH INDICES, TOGETHER, BEFORE THE
	 * BASE REGISTERS ARE WRITTEN.
	 *
	 * 量 `bench/2026-09-20b/R9-NB0` and `N1`, the two dumps either side of
	 * `A1`'s re-arm.  BEFORE: `rx_idx 1`, `rpdcr0_pos A15B8004`,
	 * `rmdcr0_pos A15B8024` -- slot 1 on both -- and all eight ring words
	 * SWCORE-owned, so THE RING WAS CLEAN.  AFTER the arm and one ping:
	 * `rp 1 rm 1` again but `rx_idx 2`, and `rxd0 A15B8050 len 1446` is
	 * `L1`'s reply-less ping sitting CPU-owned in a slot this driver will
	 * not look at for a full lap.  The base write restarted the hardware at
	 * slot 0; nothing restarted the software.  So `arm` creates an INDEX
	 * SKEW, and the skew then manufactures the hole one frame at a time.
	 *
	 * ⚠️ On that run the index reset alone would have sufficed, and this
	 * function cannot tell which case it is in.  `engine off` writes
	 * CPUIIMR 0 and does NOT call `napi_disable()`, and `arm` is a separate
	 * /proc write, so a frame already delivered and not yet harvested is
	 * still CPU-owned here -- a hole the engine stalls on.  Handing every
	 * slot back makes the post-arm state the post-alloc state, and the
	 * post-alloc state is the only one measured to work end to end
	 * (`R6-BASE` -> `R8-B0`, 20 of 20).  ⚠️ True of the ring words and of
	 * what `nic_refill` writes; it does NOT restore `rx_ph[i].dw0`,
	 * `rx_mb[i].dw1`, `rx_mb[i].dw5` or `rx_ph[i].dw3`, exactly as on every
	 * ordinary harvest.
	 *
	 * 🔴 IT DISCARDS THOSE FRAMES.  `n_rx` does not move and `rx_dropped`
	 * does not move, so `n_arm_flush` is what stops "arm destroyed nothing"
	 * being unfalsifiable -- the same reason `n_dsync_chk` exists beside
	 * `n_dsync`.
	 *
	 * 讀 `rtl865xc_swNic.c:1134-1384`: the vendor's only arm is inside
	 * `swNic_init`, which builds every descriptor, zeroes
	 * `currRxPkthdrDescIndex[]` and `currRxMbufDescIndex`, and writes
	 * `CPURPDCR0`/`CPURMDCR0` LAST, all under `local_irq_save`.  The vendor
	 * never re-arms a live ring.  ⚠️ `swNic_resetDescriptors` (`:1406`)
	 * looks like a lighter precedent and is NOT one: its body clears
	 * TXCMD|RXCMD and returns, inside `#ifdef FAT_CODE`, which the tree
	 * defines nowhere (量, two hits -- the `#ifdef` and its `#endif`).
	 *
	 * TX is the SAME bit with the opposite RESTING value, not an inverted
	 * polarity: OWN set is the engine's on both rings (`NIC_DESC_OWN`, and
	 * 讀 `rtl865xc_asicregs.h:553-554`), but an idle TX slot is the CPU's.
	 * A slot left SWCORE-owned here is a stale buffer the engine transmits
	 * the moment it is enabled.
	 *
	 * 🔴 THE LOCK IS NOT DECORATION AND `nic_engine_on` IS NOT A SUBSTITUTE
	 * FOR IT.  `nic_do_engine(0)` does not `napi_disable()`, so a poll
	 * scheduled before the mask was cleared can still run `nic_poll` in
	 * softirq and write `nic_rx_idx` and call `nic_refill()` in the middle
	 * of this loop.  52 uncached stores with interrupts off, against the up
	 * to 1518 `__raw_writeb` `nic_xmit` already does inside this lock. */
	spin_lock_irqsave(&nic_lock, flags);
	for (i = 0; i < NIC_RX_DESC; i++) {
		if (!(nic_re(nic_rx_ring, i) & NIC_DESC_OWN))
			nic_n_arm_flush++;
		nic_refill(i);
	}
	for (i = 0; i < NIC_TX_DESC; i++) {
		u32 wrap = (i == NIC_TX_DESC - 1) ? NIC_DESC_WRAP : 0;

		nic_re_set(nic_tx_ring, i,
			   (nic_tx_ph + i * NIC_DESC_BYTES) | wrap);
	}
	nic_rx_idx = 0;
	nic_tx_idx = 0;
	spin_unlock_irqrestore(&nic_lock, flags);

	rc = nic_wr(NIC_CPURPDCR0, nic_rx_ring);
	if (rc)
		return rc;
	nic_wr(NIC_CPURPDCR0 + 0x04, 0);
	nic_wr(NIC_CPURPDCR0 + 0x08, 0);
	nic_wr(NIC_CPURPDCR0 + 0x0C, 0);
	nic_wr(NIC_CPURPDCR0 + 0x10, 0);
	nic_wr(NIC_CPURPDCR0 + 0x14, 0);
	nic_wr(NIC_CPURMDCR0, nic_mb_ring);
	nic_wr(NIC_CPUTPDCR0, nic_tx_ring);
	/* NET-67 H1.  `nic_tx_rings == 1` is what every seating so far ran:
	 * three TX bases holding ZERO while `TXFD` is a single doorbell bit
	 * with no ring number (`rtl865xc_asicregs.h:538`).  This die's own
	 * loader runs TX0 AND TX1 armed (量 `NET-48`: A040FC88 / FCA0) and
	 * the vendor's `swNic_init` arms four -- so three zeroed bases is a
	 * difference between this driver and BOTH implementations that do not
	 * wedge, and no seating has read it.  At 4 they hold a well-formed
	 * one-entry ring whose descriptor is CPU-owned, so an engine that
	 * walks all four bases finds nothing to send instead of a base of
	 * zero.  The idle ring is SHARED by all three on purpose: the engine
	 * never takes ownership of it, so there is nothing to race. */
	if (nic_tx_rings == 4) {
		nic_re_set(nic_idle_ring, 0, nic_idle_ph | NIC_DESC_WRAP);
		nic_wr(NIC_CPUTPDCR1, nic_idle_ring);
		nic_wr(NIC_CPUTPDCR2, nic_idle_ring);
		nic_wr(NIC_CPUTPDCR3, nic_idle_ring);
	} else {
		nic_wr(NIC_CPUTPDCR1, 0);
		nic_wr(NIC_CPUTPDCR2, 0);
		nic_wr(NIC_CPUTPDCR3, 0);
	}

	nic_armed = 1;
	rlxfw_markx("N-ARM", nic_rx_ring);
	/* A mark only the re-establishing arm emits, so a capture can say WHICH
	 * arm ran without resting on `RLXFW-ID0` alone.  🔴 It does NOT claim
	 * the ring is repaired: 量 `Z10-nic`, `arm` already zeroed both
	 * hardware positions BEFORE this change, and 量 `Z11-f6` read 11/181
	 * (93.9 % loss) after exactly that repair where a fresh boot reads
	 * 20/20.  This makes `arm` non-fatal; it does not make it a repair. */
	rlxfw_markx("N-ARMR", (u32)nic_n_arm_flush);
	return 0;
}

/* refill one RX descriptor.
 *
 * 🔴 THE ORDER IS THE POINT OF THIS FUNCTION and it is the vendor's, 讀
 * `rtl865xc_swNic.c:342-383`: the MBUF ownership goes back first (`:376`),
 * the PKTHDR ownership second (`:359`/`:379`).  The engine needs somewhere to
 * put bytes before it needs a header slot to describe them; handing back the
 * header first gives it a slot pointing at a buffer it does not yet own.
 *
 * No barrier is needed and none is used.  Both rings are KSEG1, so the store
 * is on the bus by the time the next instruction issues -- which is also why
 * `rtl865xc_swNic.c` contains no `wmb()`, `mb()` or `sync` anywhere (量, zero
 * hits).  On a cached ring this function would be wrong without one. */
static void nic_refill(unsigned int i)
{
	u32 wrap = (i == NIC_RX_DESC - 1) ? NIC_DESC_WRAP : 0;
	u32 ph = nic_rx_ph + i * NIC_DESC_BYTES;
	u32 mb = nic_rx_mb + i * NIC_DESC_BYTES;
	u32 bf = nic_bufs + i * NIC_BUF_SZ + NIC_RX_OFFSET;

	nic_dw_set(nic_rx_mb, i, 3, bf);
	nic_dw_set(nic_rx_mb, i, 4, bf);
	nic_dw_set(nic_rx_mb, i, 2, NIC_MB_MK2(0, NIC_MB_FLAGS_INIT));
	nic_dw_set(nic_rx_ph, i, 1, 0);

	nic_re_set(nic_mb_ring, i, mb | NIC_DESC_OWN | wrap);
	nic_re_set(nic_rx_ring, i, ph | NIC_DESC_OWN | wrap);
}

/* Harvest at most `budget` frames.  Returns how many were taken.
 *
 * Bounded by construction: the loop cannot run longer than the ring, so it
 * cannot hold the CPU past the watchdog even if the engine is handing back
 * descriptors as fast as they are consumed.  The vendor's equivalent is a
 * `while (1)` with no budget (`rtl_nic.c:3139`); that is the shape `IRQ-13`'s
 * lost-interrupt window came out of, and it is not copied. */
static unsigned int nic_harvest(unsigned int budget)
{
	unsigned int took = 0;

	while (took < budget && took < NIC_RX_DESC) {
		unsigned int i = nic_rx_idx;
		u32 e = nic_re(nic_rx_ring, i);
		u32 w1, len;

		if (e & NIC_DESC_OWN)		/* engine still owns it */
			break;

		w1 = nic_dw(nic_rx_ph, i, 1);
		len = NIC_PH_LEN(w1);

		nic_last_rx_ph1 = w1;
		nic_last_rx_ph3 = nic_dw(nic_rx_ph, i, 3);
		nic_last_rx_ph4 = nic_dw(nic_rx_ph, i, 4);

		/* 讀 `rtl865xc_swNic.c:650`: the ASIC counts the 4-byte FCS in
		 * ph_len, symmetric with the +4 the vendor's TX adds. */
		nic_last_rx_len = (len >= 4) ? (len - 4) : len;
		if (nic_last_rx_len > NIC_KEEP)
			nic_last_rx_len = NIC_KEEP;
		if (nic_last_rx_len) {
			u32 bf = nic_ph_buf(i);	/* s99a (c) */
			u32 k;

			for (k = 0; k < nic_last_rx_len; k++)
				nic_last_rx[k] =
					__raw_readb((void __iomem *)(bf + k));
		}

		nic_refill(i);
		nic_rx_idx = (i + 1) % NIC_RX_DESC;
		nic_n_rx++;
		took++;
	}

	if (!took)
		nic_n_rx_empty++;
	return took;
}

/* Transmit one marker frame.
 *
 * The frame is deliberately unmistakable: a broadcast destination, a
 * locally-administered source `02:52:4C:58:46:57` (02 plus ASCII "RLXFW"),
 * EtherType 0x88B5 -- IEEE 802a local experimental 1, which no other traffic
 * on this desk uses -- and a payload beginning "RLXFW-NIC" with a sequence
 * number.  A capture on the workstation cannot mistake it for anything, and
 * neither can rung 1, which has to recognise it coming back.
 *
 * ORDER, 讀 `rtl865xc_swNic.c:692-774`: fill every field, THEN set OWN
 * (`:760`), THEN ring the doorbell `CPUICR |= TXFD` (`:771`).  If OWN were
 * set first the engine could fetch a descriptor whose length and buffer had
 * not been written; that is this gate's own named failure mode and this
 * ordering is the answer to it. */
static int nic_do_tx(u32 portlist, u32 flags, u32 vid, u32 payload_len)
{
	static const u8 dst[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
	static const u8 src[6] = { 0x02, 0x52, 0x4C, 0x58, 0x46, 0x57 };
	unsigned int i = nic_tx_idx;
	u32 bf, e, frame, k;
	u32 icr;

	if (!nic_armed)
		return -ENXIO;
	if (!nic_engine_on)
		return -EAGAIN;

	e = nic_re(nic_tx_ring, i);
	if (e & NIC_DESC_OWN)		/* engine still has this slot */
		return -EBUSY;

	if (payload_len < 32)
		payload_len = 32;
	if (payload_len > NIC_BUF_SZ - 64)
		payload_len = NIC_BUF_SZ - 64;

	bf = nic_bufs + (NIC_RX_DESC + i) * NIC_BUF_SZ + NIC_RX_OFFSET;

	for (k = 0; k < 6; k++)
		__raw_writeb(dst[k], (void __iomem *)(bf + k));
	for (k = 0; k < 6; k++)
		__raw_writeb(src[k], (void __iomem *)(bf + 6 + k));
	__raw_writeb(0x88, (void __iomem *)(bf + 12));
	__raw_writeb(0xB5, (void __iomem *)(bf + 13));

	for (k = 0; k < payload_len; k++) {
		static const char tag[] = "RLXFW-NIC ";
		u8 b;

		if (k < 10)
			b = (u8)tag[k];
		else if (k == 10)
			b = (u8)('0' + (nic_n_tx % 10));
		else
			b = (u8)(0x40 + (k & 0x3F));
		__raw_writeb(b, (void __iomem *)(bf + 14 + k));
	}

	frame = 14 + payload_len;
	/* 讀 `rtl865xc_swNic.c:718-721`: ph_len carries the FCS, and a runt is
	 * padded to 64 before the +4.  Both are the ASIC's arithmetic, not a
	 * convention this driver gets to choose. */
	if (frame < 60)
		frame = 60;

	nic_dw_set(nic_tx_mb, i, 3, bf);
	nic_dw_set(nic_tx_mb, i, 4, bf);
	nic_dw_set(nic_tx_mb, i, 2, NIC_MB_MK2(frame, NIC_MB_FLAGS_INIT));
	nic_dw_set(nic_tx_mb, i, 5, NIC_MB_MK5(NIC_BUF_SZ - NIC_RX_OFFSET));

	nic_dw_set(nic_tx_ph, i, 1, NIC_PH_MK1(frame + 4, 0, 0));
	nic_dw_set(nic_tx_ph, i, 3, NIC_PH_MK3(flags, portlist));
	nic_dw_set(nic_tx_ph, i, 4, NIC_PH_MK4(vid));

	/* OWN last, and only now. */
	{
		u32 wrap = (i == NIC_TX_DESC - 1) ? NIC_DESC_WRAP : 0;
		u32 ph = nic_tx_ph + i * NIC_DESC_BYTES;

		nic_re_set(nic_tx_ring, i, ph | NIC_DESC_OWN | wrap);
	}

	/* The doorbell is a read-modify-write on the register that also holds
	 * TXCMD, RXCMD, the burst size and the mbuf size.  讀
	 * `rtl865xc_swNic.c:771`.  There is no separate doorbell register --
	 * which means a driver that writes CPUICR with `=` at the wrong moment
	 * disables the engine while trying to kick it. */
	icr = nic_rd(NIC_CPUICR);
	nic_wr(NIC_CPUICR, icr | NIC_TXFD);

	nic_tx_idx = (i + 1) % NIC_TX_DESC;
	nic_n_tx++;
	return 0;
}

/* engine on/off.  讀 `rtl865x_asicCom.c:1352-1355`: the vendor writes CPUICR
 * with `=`, not `|=` -- burst size and mbuf size go in the same store as the
 * enables -- then W1Cs stale pending, then opens the mask.  That order is
 * kept.  The W1C matters here more than it does for the vendor: this die has
 * a LINK_CHANGE_IP latched since before the kernel started (量, `CPUIISR`
 * reads 0x80000000 at the loader prompt), so an unmasked handler would take
 * an interrupt for an event that happened before it existed. */
static int nic_do_engine(int on)
{
	int rc;

	if (!nic_armed)
		return -ENXIO;

	if (!on) {
		rc = nic_wr(NIC_CPUIIMR, 0);
		if (rc)
			return rc;
		nic_wr(NIC_CPUICR, nic_rd(NIC_CPUICR)
				   & ~(NIC_TXCMD | NIC_RXCMD));
		nic_engine_on = 0;
		rlxfw_mark("N-ENGOFF");
		return 0;
	}

	rc = nic_wr(NIC_CPUICR,
		    NIC_TXCMD | NIC_RXCMD | NIC_BUSBURST_32W | NIC_MBUF_2048);
	if (rc)
		return rc;
	nic_wr(NIC_CPUIISR, nic_rd(NIC_CPUIISR));	/* W1C stale */
	nic_wr(NIC_CPUIIMR, nic_iimr_base);		/* s99a: a variable */
	nic_engine_on = 1;
	rlxfw_markx("N-ENGON", nic_rd(NIC_CPUICR));
	return 0;
}

/* ------------------------------------------------------------------------
 * /proc
 * ------------------------------------------------------------------------ */
static int nic_read_proc(char *page, char **start, off_t off, int count,
			 int *eof, void *data)
{
	int len = 0;
	unsigned int i;

	len += sprintf(page + len, "version %s\n", RTL819X_NIC_VERSION);
	len += sprintf(page + len, "unlocked %d\n", nic_unlocked);
	len += sprintf(page + len, "allocated %d\n", nic_allocated);
	len += sprintf(page + len, "armed %d\n", nic_armed);
	len += sprintf(page + len, "engine_on %d\n", nic_engine_on);
	len += sprintf(page + len, "irq_taken %d\n", nic_irq_taken);
	len += sprintf(page + len, "irq_rc %d\n", nic_irq_rc);

	len += sprintf(page + len, "n_reads %lu\n", nic_n_reads);
	len += sprintf(page + len, "n_writes %lu\n", nic_n_writes);
	len += sprintf(page + len, "n_refused %lu\n", nic_n_refused);
	len += sprintf(page + len, "n_irq %lu\n", nic_n_irq);
	len += sprintf(page + len, "n_irq_spurious %lu\n", nic_n_irq_spurious);
	len += sprintf(page + len, "n_tx %lu\n", nic_n_tx);
	len += sprintf(page + len, "n_rx %lu\n", nic_n_rx);
	len += sprintf(page + len, "n_rx_empty %lu\n", nic_n_rx_empty);
	len += sprintf(page + len, "n_poll %lu\n", nic_n_poll);
	len += sprintf(page + len, "n_poll_masked %lu\n", nic_n_poll_masked);
	len += sprintf(page + len, "last_iisr %08X\n", nic_last_iisr);
	len += sprintf(page + len, "seen_iisr %08X\n", nic_seen_iisr);

	/* R6-4.  `nd_name` is the POSITIVE discriminator the gate asks for:
	 * an interface this driver named, beside the vendor's eth0..eth5. */
	len += sprintf(page + len, "nd_alloc %d\n", nic_ndev ? 1 : 0);
	len += sprintf(page + len, "nd_registered %d\n", nic_ndev_registered);
	len += sprintf(page + len, "nd_up %d\n", nic_ndev_up);
	len += sprintf(page + len, "nd_name %s\n",
		       nic_ndev ? nic_ndev->name : "-");
	len += sprintf(page + len, "n_napi_poll %lu\n", nic_n_napi_poll);
	len += sprintf(page + len, "n_napi_complete %lu\n",
		       nic_n_napi_complete);
	len += sprintf(page + len, "n_xmit %lu\n", nic_n_xmit);
	len += sprintf(page + len, "n_xmit_busy %lu\n", nic_n_xmit_busy);
	len += sprintf(page + len, "tx_mode %d\n", nic_tx_mode);
	len += sprintf(page + len, "n_tx_full %lu\n", nic_n_tx_full);
	len += sprintf(page + len, "n_tx_retry %lu\n", nic_n_tx_retry);
	len += sprintf(page + len, "tx_retry_max_seen %lu\n",
		       nic_tx_retry_max_seen);
	len += sprintf(page + len, "n_tx_recovered %lu\n", nic_n_tx_recovered);
	len += sprintf(page + len, "n_tx_drop_full %lu\n", nic_n_tx_drop_full);
	len += sprintf(page + len, "n_xmit_ctx %lu/%lu/%lu\n",
		       nic_n_xmit_hardirq, nic_n_xmit_softirq,
		       nic_n_xmit_process);
	len += sprintf(page + len, "n_skb_fail %lu\n", nic_n_skb_fail);
	len += sprintf(page + len, "n_tx_stop %lu\n", nic_n_tx_stop);
	len += sprintf(page + len, "n_tx_wake %lu\n", nic_n_tx_wake);
	len += sprintf(page + len, "n_tx_wake_race %lu\n",
		       nic_n_tx_wake_race);
	len += sprintf(page + len, "n_tx_timeout %lu\n", nic_n_tx_timeout);
	/* A STATE, not a count.  `n_tx_stop == n_tx_wake` cannot say whether
	 * the queue is stopped RIGHT NOW, and that is the reading by which a
	 * wedged interface is told from a busy one.  -1 when there is no
	 * net_device, so the field never has to be read as 0-meaning-two-
	 * things.  量 the page budget this sits in: the largest committed
	 * dump of this file is `bench/2026-09-19b/C58-afterflood2.log` at
	 * 1,244 bytes including the echoed command; these five lines add
	 * about 110, against the 4,096 `read_proc` gives and does not
	 * bound-check. */
	len += sprintf(page + len, "tx_stopped %d\n",
		       nic_ndev ? netif_queue_stopped(nic_ndev) : -1);
	if (nic_ndev)
		len += sprintf(page + len,
			       "nd_stats rx %lu/%lu tx %lu/%lu drop %lu/%lu\n",
			       nic_ndev->stats.rx_packets,
			       nic_ndev->stats.rx_bytes,
			       nic_ndev->stats.tx_packets,
			       nic_ndev->stats.tx_bytes,
			       nic_ndev->stats.rx_dropped,
			       nic_ndev->stats.tx_dropped);

	/* Boot state: what this driver found at late_initcall, before it
	 * wrote anything.  `boot_icr 00000000` is the whole evidence that the
	 * vendor's probe disarmed the engine on THIS boot. */
	len += sprintf(page + len, "boot_icr %08X\n", nic_boot_icr);
	len += sprintf(page + len, "boot_iimr %08X\n", nic_boot_iimr);
	len += sprintf(page + len, "boot_iisr %08X\n", nic_boot_iisr);
	len += sprintf(page + len, "boot_rpdcr0 %08X\n", nic_boot_rpdcr0);
	len += sprintf(page + len, "boot_rmdcr0 %08X\n", nic_boot_rmdcr0);
	len += sprintf(page + len, "boot_tpdcr0 %08X\n", nic_boot_tpdcr0);

	len += sprintf(page + len, "now_icr %08X\n", nic_rd(NIC_CPUICR));
	len += sprintf(page + len, "now_iimr %08X\n", nic_rd(NIC_CPUIIMR));
	len += sprintf(page + len, "now_iisr %08X\n", nic_rd(NIC_CPUIISR));
	/* 🔴 These two read back the engine's CURRENT POSITION, not the base
	 * this driver wrote -- `SPEC.md` `NET-32`, and 量 again on this die at
	 * the loader prompt, where a cold `CPURMDCR0` reads exactly the base
	 * and a used one reads 12 bytes further on.  Printed under names that
	 * say so. */
	len += sprintf(page + len, "rpdcr0_pos %08X\n",
		       nic_rd(NIC_CPURPDCR0));
	len += sprintf(page + len, "rmdcr0_pos %08X\n",
		       nic_rd(NIC_CPURMDCR0));
	len += sprintf(page + len, "tpdcr0_pos %08X\n",
		       nic_rd(NIC_CPUTPDCR0));
	/* 🔴 The other three TX ring bases, which `nic_do_arm` writes ZERO to
	 * and which no seating has ever read back.  This die's own loader runs
	 * TX0 and TX1 armed (量 `NET-48`: A040FC88 / FCA0) and the vendor's
	 * `swNic_init` arms four; `TXFD` is one doorbell bit with NO ring
	 * number (`rtl865xc_asicregs.h:538`).  So "three of the four bases are
	 * zero" is a difference between this driver and BOTH implementations
	 * that do not wedge, and it has never been on a dump. */
	len += sprintf(page + len, "tpdcr1_pos %08X\n",
		       nic_rd(NIC_CPUTPDCR1));
	len += sprintf(page + len, "tpdcr2_pos %08X\n",
		       nic_rd(NIC_CPUTPDCR2));
	len += sprintf(page + len, "tpdcr3_pos %08X\n",
		       nic_rd(NIC_CPUTPDCR3));

	/* R6-5's desync ledger.  `n_dsync_chk` is the denominator: without it
	 * `n_dsync 0` cannot tell "it never happened" from "nobody looked". */
	len += sprintf(page + len, "n_arm_flush %lu\n", nic_n_arm_flush);

	/* s99a (b).  `iimr_base` is what this driver believes it armed;
	 * `iimr_ladder` is the compiled default, printed so a card can read
	 * the A arm's value instead of typing it; `now_iimr` above is the
	 * register.  Two of the three are independent sources. */
	len += sprintf(page + len, "iimr_base %08X\n", nic_iimr_base);
	len += sprintf(page + len, "iimr_ladder %08X\n",
		       (u32)NIC_IIMR_LADDER);

	/* s99a (a).  The stall detector's ledger.  See the four-state table
	 * by `nic_recov_mode`'s declaration: `n_recov_arm` separates "the
	 * queue never stopped" from "it stopped and the cheap path won", and
	 * `n_recov_fire` separates that from "the recovery ran". */
	len += sprintf(page + len, "recov_mode %d\n", nic_recov_mode);
	len += sprintf(page + len, "recov_ms %u\n", nic_recov_ms);
	len += sprintf(page + len, "recov_jiffies %u\n",
		       (unsigned)msecs_to_jiffies(nic_recov_ms));
	len += sprintf(page + len, "n_recov_arm %lu\n", nic_n_recov_arm);
	len += sprintf(page + len, "n_recov_fire %lu\n", nic_n_recov_fire);
	len += sprintf(page + len, "n_recov_spurious %lu\n",
		       nic_n_recov_spurious);
	len += sprintf(page + len, "n_recov_ok %lu\n", nic_n_recov_ok);
	len += sprintf(page + len, "n_recov_fail %lu\n", nic_n_recov_fail);
	len += sprintf(page + len, "n_recov_wake %lu\n", nic_n_recov_wake);
	len += sprintf(page + len, "recov_rc %d %d %d\n",
		       nic_recov_rc[0], nic_recov_rc[1], nic_recov_rc[2]);
	len += sprintf(page + len, "recov_j_arm %lu\n", nic_recov_j_arm);
	len += sprintf(page + len, "recov_j_fire %lu\n", nic_recov_j_fire);

	/* s99a (c).  `NET-82`.  `n_ph_diff` over `n_ph_chk` is the reading;
	 * `ph_first_*` is the first occurrence kept whole, because a rate
	 * cannot say WHICH slot the engine paired with which.  `n_ph_used` is
	 * 0 after `phfollow 0` (1 is the default), so a dump says which behaviour
	 * produced the frames it is describing. */
	len += sprintf(page + len, "ph_follow %d\n", nic_ph_follow);
	len += sprintf(page + len, "n_ph_chk %lu\n", nic_n_ph_chk);
	len += sprintf(page + len, "n_ph_diff %lu\n", nic_n_ph_diff);
	len += sprintf(page + len, "n_ph_bad %lu\n", nic_n_ph_bad);
	len += sprintf(page + len, "n_ph_used %lu\n", nic_n_ph_used);
	len += sprintf(page + len, "ph_first_w0 %08X\n", nic_ph_first_w0);
	len += sprintf(page + len, "ph_first_exp %08X\n", nic_ph_first_exp);
	len += sprintf(page + len, "ph_first_nrx %lu\n", nic_ph_first_nrx);
	len += sprintf(page + len, "ph_agree %lu\n",
		       nic_n_ph_chk - nic_n_ph_diff);
	len += sprintf(page + len, "ph_last %08X\n", nic_ph_last);
	len += sprintf(page + len, "ph_last_j %u\n", nic_ph_last_j);
	len += sprintf(page + len, "ph_last_bf %08X\n", nic_ph_last_bf);
	len += sprintf(page + len, "ph_last_cls %d\n", nic_ph_last_cls);
	len += sprintf(page + len, "tx_rings %d\n", nic_tx_rings);
	len += sprintf(page + len, "n_et_link %lu\n", nic_n_et_link);
	len += sprintf(page + len, "et_link_last %08X\n", nic_et_link_last);
	len += sprintf(page + len, "ph_test_cls %d\n", nic_ph_test_cls);
	len += sprintf(page + len, "ph_test_j %u\n", nic_ph_test_j);
	len += sprintf(page + len, "ph_test_seen %d\n", nic_ph_test_seen);
	len += sprintf(page + len, "j_now %lu\n", jiffies);
	/* ⚠️ `n_dsync_chk` EQUALS `n_napi_poll` -- one check per poll.  The
	 * counter that is ~2x is `n_reads`, because the check is two
	 * `nic_rd()` per poll, so `n_reads` is no longer the small auditable
	 * number it was before this driver version.
	 *
	 * 🔴 `FW-107`: until 2026-09-22 this comment hung the factor on
	 * `n_dsync_chk`, and it is the comment that exists to prevent a
	 * misreading.  量 2026-09-21, three dumps: `n_dsync_chk` 5 / 350 /
	 * 73,810 against `n_napi_poll` 5 / 350 / 73,810, while `n_reads` reads
	 * 18 / 720 / 147,628 = 2x + 8 / 2x + 20 / 2x + 8. */
	len += sprintf(page + len, "n_dsync_chk %lu\n", nic_n_dsync_chk);
	len += sprintf(page + len, "n_dsync %lu\n", nic_n_dsync);
	len += sprintf(page + len, "dsync_last_d %u\n", nic_dsync_last_d);
	len += sprintf(page + len, "dsync_first_d %u\n", nic_dsync_first_d);
	len += sprintf(page + len, "dsync_first_rp %08X\n",
		       nic_dsync_first_rp);
	len += sprintf(page + len, "dsync_first_rm %08X\n",
		       nic_dsync_first_rm);
	len += sprintf(page + len, "dsync_first_nrx %lu\n",
		       nic_dsync_first_nrx);
	len += sprintf(page + len, "dsync_test_d %u\n", nic_dsync_test_d);
	len += sprintf(page + len, "dsync_test_seen %d\n",
		       nic_dsync_test_seen);

	if (nic_allocated) {
		len += sprintf(page + len, "rx_ring %08X\n", nic_rx_ring);
		len += sprintf(page + len, "mb_ring %08X\n", nic_mb_ring);
		len += sprintf(page + len, "tx_ring %08X\n", nic_tx_ring);
		len += sprintf(page + len, "bufs %08X\n", nic_bufs);
		/* 🔴 rx_ph and rx_mb were NOT printed, and the `phtest` comment
		 * claims its arguments are computed from bases "this same file
		 * prints".  That was true of `dsynctest` and false of `phtest`:
		 * block 40 derived A15B8110 at the desk from alloc arithmetic
		 * instead.  Printing them makes the claim true. */
		len += sprintf(page + len, "rx_ph %08X\n", nic_rx_ph);
		len += sprintf(page + len, "rx_mb %08X\n", nic_rx_mb);
		len += sprintf(page + len, "tx_ph %08X\n", nic_tx_ph);
		len += sprintf(page + len, "tx_mb %08X\n", nic_tx_mb);
		len += sprintf(page + len, "idle_ring %08X\n", nic_idle_ring);
		len += sprintf(page + len, "rx_idx %u\n", nic_rx_idx);
		len += sprintf(page + len, "tx_idx %u\n", nic_tx_idx);

		for (i = 0; i < NIC_RX_DESC; i++) {
			if (len > NIC_PROC_CAP)
				goto truncated;
			len += sprintf(page + len,
				       "rxd%u %08X len %u f %04X pl %02X\n",
				       i, nic_re(nic_rx_ring, i),
				       NIC_PH_LEN(nic_dw(nic_rx_ph, i, 1)),
				       NIC_PH_FLAGS(nic_dw(nic_rx_ph, i, 3)),
				       NIC_PH_PORTLIST(nic_dw(nic_rx_ph, i,
							      3)));
		}
		for (i = 0; i < NIC_TX_DESC; i++) {
			if (len > NIC_PROC_CAP)
				goto truncated;
			len += sprintf(page + len,
				       "txd%u %08X len %u\n",
				       i, nic_re(nic_tx_ring, i),
				       NIC_PH_LEN(nic_dw(nic_tx_ph, i, 1)));
		}
		/* s99a (c)'s SECOND WITNESS, and it does not depend on any of the
		 * new code being right.  `ph` is pkthdr word 0 exactly as the
		 * engine left it.  `ml` is the mbuf's `m_len`, which `nic_refill()`
		 * zeroes only for the slot it is handed -- so a non-zero `ml` on
		 * slot j is the ENGINE saying it put a frame in mbuf j, written by
		 * hardware and readable with `phfollow` never touched. */
		for (i = 0; i < NIC_RX_DESC; i++) {
			if (len > NIC_PROC_CAP)
				goto truncated;
			len += sprintf(page + len,
				       "mbd%u %08X ph %08X ml %u\n",
				       i, nic_re(nic_mb_ring, i),
				       nic_dw(nic_rx_ph, i, 0),
				       NIC_MB_LEN(nic_dw(nic_rx_mb, i, 2)));
		}
	}

	/* The last received frame, printed as hex.  `FW-46`: this image's
	 * busybox has no `dd` and no `md5sum`, so there is no second way to
	 * get bytes off this device.  Capped so the whole handler stays well
	 * inside the single 4,096-byte page `read_proc` is given and does not
	 * bound-check. */
	len += sprintf(page + len, "rx_len %u\n", nic_last_rx_len);
	len += sprintf(page + len, "rx_ph1 %08X\n", nic_last_rx_ph1);
	len += sprintf(page + len, "rx_ph3 %08X\n", nic_last_rx_ph3);
	len += sprintf(page + len, "rx_ph4 %08X\n", nic_last_rx_ph4);
	if (nic_last_rx_len) {
		unsigned int n = nic_last_rx_len;

		if (n > 64)
			n = 64;
		/* 9 for the label, 2 per byte, 1 for the newline.  Checked
		 * against the whole block rather than per byte, because a
		 * hexdump cut in half is worse than one that is absent. */
		if (len + 9 + 2 * (int)n + 1 > NIC_PROC_CAP)
			goto truncated;
		len += sprintf(page + len, "rx_bytes ");
		for (i = 0; i < n; i++)
			len += sprintf(page + len, "%02X", nic_last_rx[i]);
		len += sprintf(page + len, "\n");
	}

	*eof = 1;
	return len;

truncated:
	/* Reached only if the cap was hit.  `truncated 0` is never printed --
	 * its ABSENCE is the normal state, so a card asserts on the absence and
	 * a present line is the finding. */
	len += sprintf(page + len, "truncated 1\n");
	*eof = 1;
	return len;
}

static int nic_write_proc(struct file *file, const char __user *buffer,
			  unsigned long count, void *data)
{
	char buf[48];
	unsigned long n = count;
	int i;

	if (n >= sizeof(buf))
		n = sizeof(buf) - 1;
	if (copy_from_user(buf, buffer, n))
		return -EFAULT;
	buf[n] = '\0';
	/* CRLF is universal on this console and an unstripped '\r' makes every
	 * strcmp below fail while the value on screen looks right.  This
	 * project has recorded that exact failure three times in one seating. */
	for (i = (int)n - 1; i >= 0; i--) {
		if (buf[i] == '\r' || buf[i] == '\n' || buf[i] == ' ')
			buf[i] = '\0';
		else
			break;
	}

	if (!strcmp(buf, "unlock")) {
		nic_unlocked = 1;
		rlxfw_mark("N-UNLOCK");
		return (int)count;
	}
	if (!strcmp(buf, "lock")) {
		nic_unlocked = 0;
		return (int)count;
	}
	if (!strcmp(buf, "alloc")) {
		int rc = nic_do_alloc();

		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "arm")) {
		int rc = nic_do_arm();

		return rc ? rc : (int)count;
	}
	/* THE DETECTOR'S POSITIVE CONTROL.  Two absolute addresses in hex, put
	 * through the SAME arithmetic the poll path uses.  No register is read
	 * and no hardware is touched, so it is free and can be run on a live
	 * board at any moment.  The card computes both arguments from the
	 * `rx_ring`/`mb_ring` this same file prints, so a wrong base makes the
	 * control FAIL rather than pass quietly. */
	if (!strncmp(buf, "dsynctest ", 10)) {
		char *p = buf + 10;
		u32 rp, rm;

		/* Without this the control computes against a ring base of
		 * ZERO and can pass on a driver that has no ring at all. */
		if (!nic_allocated)
			return -ENXIO;

		rp = simple_strtoul(p, &p, 16);
		while (*p == ' ')
			p++;
		rm = simple_strtoul(p, &p, 16);
		nic_dsync_test_d = nic_dsync_calc(rp, rm);
		nic_dsync_test_seen = 1;
		return (int)count;
	}
	/* One check on demand, for a cell that wants a reading at a moment of
	 * its own choosing rather than at whenever the next poll happens. */
	if (!strcmp(buf, "dsyncchk")) {
		nic_dsync_check();
		return (int)count;
	}
	if (!strcmp(buf, "irqon")) {
		if (nic_irq_taken)
			return -EEXIST;
		/* IRQF_DISABLED and NOT shared, matching the vendor -- if it
		 * comes back -EBUSY then a vendor interface was opened and
		 * this whole arrangement's precondition is false.  The return
		 * value is kept and printed rather than collapsed to a
		 * failure, because WHICH error it is, is the finding. */
		nic_irq_rc = request_irq(NIC_IRQ, nic_isr, IRQF_DISABLED,
					 "rtl819x-nic", &nic_lock);
		if (nic_irq_rc)
			return nic_irq_rc;
		nic_irq_taken = 1;
		rlxfw_mark("N-IRQON");
		return (int)count;
	}
	if (!strcmp(buf, "irqoff")) {
		if (!nic_irq_taken)
			return -ENXIO;
		free_irq(NIC_IRQ, &nic_lock);
		nic_irq_taken = 0;
		return (int)count;
	}
	/* s99a (a).  `recover 0` / `recover 1`.  Default 1 since 1.4
	 * (`NET-107`); `recover 0` returns to `s32a`'s behaviour, which is
	 * what still lets one boot carry the broken arm and the repaired
	 * arm with nothing else changed.
	 *
	 * Turning it OFF also disarms, so a cell can stop the detector while a
	 * wedge is being read rather than racing it. */
	if (!strncmp(buf, "recover ", 8)) {
		if (!strcmp(buf + 8, "0")) {
			nic_recov_mode = 0;
			nic_recov_disarm();
		} else if (!strcmp(buf + 8, "1")) {
			nic_recov_mode = 1;
			/* 🔴 ARM IMMEDIATELY IF THE QUEUE IS ALREADY STOPPED.
			 * `nic_recov_arm()` is otherwise called only at the
			 * stop TRANSITION, so a detector switched on over an
			 * existing stall would wait for a second stall that
			 * can never come -- the queue is stopped, so nothing
			 * calls `nic_xmit` again (`NET-57`: `tx_queue_len 0`
			 * means `dev_queue_xmit` does not offer to a stopped
			 * queue).  That is `NET-99` read from the driver's
			 * side: `n_tx` frozen at 17 for 600 s is exactly a
			 * transition that never repeats.
			 *
			 * 🟢 What it buys is the single-variable experiment:
			 * wedge with the detector OFF, read the wedge whole,
			 * then switch the detector on IN FRONT OF the fault.
			 * The fault is already present when the variable
			 * moves, so nothing else has to be held constant. */
			if (nic_ndev && nic_ndev_up &&
			    netif_queue_stopped(nic_ndev))
				nic_recov_arm();
		} else {
			return -EINVAL;
		}
		return (int)count;
	}
	/* The stall threshold in MILLISECONDS.  Bounded rather than free: a
	 * value under a tick would make the timer fire on the healthy
	 * transient the ISR's wake already handles, and `n_recov_spurious` is
	 * what would show it.  `recov_jiffies` in the dump is what it actually
	 * programs, so the conversion is readable rather than assumed. */
	if (!strncmp(buf, "recovms ", 8)) {
		char *p = buf + 8;
		unsigned long v = simple_strtoul(p, &p, 0);

		if (*p || v < NIC_RECOV_MS_MIN || v > NIC_RECOV_MS_MAX)
			return -EINVAL;
		nic_recov_ms = (unsigned int)v;
		return (int)count;
	}
	/* s99a (b).  `iimr <hex>` -- the run-out mask A/B.  Any 32-bit value
	 * is accepted, including ones this driver would never choose, because
	 * refusing them is refusing the experiment.  It is a hardware write
	 * and goes through `nic_wr`, so the unlock guard applies; when the
	 * engine is off it is recorded and `engine on` writes it. */
	/* s99a (c).  `phfollow 0` indexes the mbuf ring by the pkthdr's index,
	 * which is what every measurement in this repository was taken under;
	 * `phfollow 1` follows `ph_mbuf`, which is what the vendor does.  The
	 * counters are collected either way, so the two arms share a
	 * denominator instead of each having its own. */
	/* s99a (c)'s POSITIVE CONTROL.  `phtest <hex-w0> <slot>` puts a typed
	 * value through `nic_ph_class()` -- the same code the harvest uses --
	 * and reports the class and the slot it resolved to.  It reads no
	 * register and touches no hardware, so it is free and can be run on a
	 * live board at any moment.
	 *
	 * Requires `alloc`: the classification is relative to `nic_rx_mb`, and
	 * classifying against a base of zero would let the control pass on a
	 * driver that has no ring.  That is the same hole `dsynctest`'s own
	 * `-ENXIO` closes.
	 *
	 * ⚠️ WHAT IT DOES NOT COVER, said rather than left to be found: the
	 * DEREFERENCE.  It exercises classification and the index arithmetic
	 * only.  The load has its own check -- `ph_last_bf` must equal
	 * `bufs + ph_last_j * NIC_BUF_SZ + NIC_RX_OFFSET`, and `bufs` is
	 * printed in the same dump, so that is a prediction rather than a
	 * restatement. */
	if (!strncmp(buf, "phtest ", 7)) {
		char *p = buf + 7;
		unsigned long v, ix;

		if (!nic_allocated)
			return -ENXIO;
		v = simple_strtoul(p, &p, 16);
		while (*p == ' ')
			p++;
		ix = simple_strtoul(p, &p, 10);
		if (ix >= NIC_RX_DESC)
			return -EINVAL;
		nic_ph_test_cls = nic_ph_class((u32)v, (unsigned int)ix,
					       &nic_ph_test_j);
		nic_ph_test_seen = 1;
		return (int)count;
	}
	if (!strncmp(buf, "txrings ", 8)) {
		if (!strcmp(buf + 8, "1"))
			nic_tx_rings = 1;
		else if (!strcmp(buf + 8, "4"))
			nic_tx_rings = 4;
		else
			return -EINVAL;
		/* Takes effect at the NEXT `arm`, because that is where the base
		 * registers are written.  Saying so here is cheaper than a card
		 * discovering it. */
		return (int)count;
	}

	if (!strncmp(buf, "phfollow ", 9)) {
		if (!strcmp(buf + 9, "0"))
			nic_ph_follow = 0;
		else if (!strcmp(buf + 9, "1"))
			nic_ph_follow = 1;
		else
			return -EINVAL;
		return (int)count;
	}
	if (!strncmp(buf, "iimr ", 5)) {
		char *p = buf + 5;
		u32 v = (u32)simple_strtoul(p, &p, 16);

		if (*p)
			return -EINVAL;
		nic_iimr_base = v;
		if (nic_engine_on) {
			int rc = nic_wr(NIC_CPUIIMR, nic_iimr_base);

			if (rc)
				return rc;
		}
		return (int)count;
	}
	if (!strcmp(buf, "engine on")) {
		int rc = nic_do_engine(1);

		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "engine off")) {
		int rc = nic_do_engine(0);

		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "swint")) {
		/* Rung 0.  RMW, because CPUICR also holds the enables. */
		u32 icr = nic_rd(NIC_CPUICR);
		int rc = nic_wr(NIC_CPUICR, icr | NIC_SWINTSET);

		return rc ? rc : (int)count;
	}
	/* s32a.  One verb, two values, and it refuses anything else rather than
	 * treating an unparsed argument as 0 -- which would silently put the
	 * board back in the mode the cell was written to leave. */
	if (!strncmp(buf, "txmode ", 7)) {
		if (!strcmp(buf + 7, "0"))
			nic_tx_mode = NIC_TXMODE_STOPQ;
		else if (!strcmp(buf + 7, "1"))
			nic_tx_mode = NIC_TXMODE_VENDOR;
		else
			return -EINVAL;
		return (int)count;
	}
	if (!strncmp(buf, "txstall ", 8)) {
		/* R6-4a's POSITIVE CONTROL, and the reason the next seating's
		 * first flood can test ONE thing instead of two.
		 *
		 * `n_xmit_busy 0` after a flood is ambiguous: it is what a
		 * working wake looks like AND what a stop path that was never
		 * reached looks like.  量 `bench/2026-09-19b/L2-after` and
		 * `M7-after`: four concurrent 1400-byte floods never exhausted
		 * four TX descriptors on either image, so the ambiguity is
		 * measured rather than feared.  This verb takes the load out
		 * of the question -- stop the engine consuming descriptors,
		 * offer five frames, and the fifth MUST take the stop path.
		 *
		 * TXCMD and not STOPTX (bit 21).  Either would do it; TXCMD is
		 * a bit this driver already writes on every `engine on` and
		 * whose value is anchored by this die's own `CPUICR C4000000`
		 * at the loader prompt, while `NIC_STOPTX` is 讀 out of
		 * `rtl865xc_asicregs.h` and has never been exercised here.
		 *
		 * `nic_engine_on` is deliberately LEFT SET: clearing it would
		 * make nic_xmit drop the skb (`:758-762`) instead of stopping
		 * the queue, which is the opposite of what this control is
		 * for.  RXCMD is left set so the interface can still be pinged
		 * while transmit is stalled, which is the negative half of the
		 * reading.
		 *
		 * ⚠️ REFUTATION CONDITION FOR THE CONTROL ITSELF: if
		 * `txstall off` does not restore transmit -- a ping after it
		 * fails, or the `txd*` OWN bits stay set -- then clearing
		 * TXCMD mid-flight wedges this engine, the control is VOID,
		 * and the seating falls back to the flood alone.  That has to
		 * be on the card before the board is powered. */
		u32 icr;
		int rc;

		if (!nic_armed)
			return -ENXIO;
		icr = nic_rd(NIC_CPUICR);
		if (!strcmp(buf + 8, "on")) {
			rc = nic_wr(NIC_CPUICR, icr & ~NIC_TXCMD);
		} else if (!strcmp(buf + 8, "off")) {
			rc = nic_wr(NIC_CPUICR, icr | NIC_TXCMD);
			if (!rc)
				rc = nic_wr(NIC_CPUICR,
					    nic_rd(NIC_CPUICR) | NIC_TXFD);
		} else {
			return -EINVAL;
		}
		return rc ? rc : (int)count;
	}
	if (!strncmp(buf, "lb ", 3)) {
		u32 icr = nic_rd(NIC_CPUICR);
		int rc;

		if (!strcmp(buf + 3, "on"))
			rc = nic_wr(NIC_CPUICR, icr | NIC_LBMODE);
		else if (!strcmp(buf + 3, "off"))
			rc = nic_wr(NIC_CPUICR, icr & ~NIC_LBMODE);
		else
			return -EINVAL;
		return rc ? rc : (int)count;
	}
	if (!strncmp(buf, "tx ", 3)) {
		/* `tx <portlist> [flags] [vid] [len]`.  The portlist is an
		 * ARGUMENT and not a constant because the CPU port's index is
		 * contested four ways in this repository (`NET-37`), so it is
		 * a swept parameter rather than a guess compiled in. */
		char *p = buf + 3;
		unsigned long pl, fl = NIC_PH_FLAGS_TX_DEFAULT, vid = 0;
		unsigned long ln = 46;
		int rc;

		pl = simple_strtoul(p, &p, 0);
		if (*p)
			fl = simple_strtoul(p + 1, &p, 0);
		if (*p)
			vid = simple_strtoul(p + 1, &p, 0);
		if (*p)
			ln = simple_strtoul(p + 1, &p, 0);
		rc = nic_do_tx((u32)pl, (u32)fl, (u32)vid, (u32)ln);
		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "rx")) {
		nic_harvest(NIC_RX_DESC);
		return (int)count;
	}
	if (!strncmp(buf, "poll", 4)) {
		/* Rung 4 -- NAPI's mechanism without NAPI's binding.  Mask the
		 * RX sources, drain with a budget, W1C what we consumed, then
		 * unmask.  The race NAPI exists to close is between the last
		 * empty poll and the unmask: a frame arriving in that window
		 * must still raise an interrupt afterwards, which is why the
		 * unmask happens AFTER the final empty harvest and not before.
		 */
		unsigned long flags;
		u32 iimr;
		unsigned int got;

		if (!nic_engine_on)
			return -EAGAIN;

		spin_lock_irqsave(&nic_lock, flags);
		iimr = nic_rd(NIC_CPUIIMR);
		nic_wr(NIC_CPUIIMR, iimr & ~NIC_IE_RX_DONE_ALL);
		nic_n_poll_masked++;
		spin_unlock_irqrestore(&nic_lock, flags);

		got = nic_harvest(NIC_RX_DESC);
		nic_n_poll++;

		spin_lock_irqsave(&nic_lock, flags);
		nic_wr(NIC_CPUIISR, NIC_IE_RX_DONE_ALL);
		nic_wr(NIC_CPUIIMR, iimr);
		spin_unlock_irqrestore(&nic_lock, flags);

		return (int)count;
	}
	if (!strncmp(buf, "netdev ", 7)) {
		/* R6-4.  Registration is a verb and not a boot action, so an
		 * image carrying this driver still comes up with nothing of
		 * mine bound to anything -- which is what makes `n_writes 0`
		 * on a boot capture mean something. */
		if (!nic_ndev)
			return -ENODEV;
		if (!strcmp(buf + 7, "on")) {
			int rc;

			if (nic_ndev_registered)
				return -EEXIST;
			if (!nic_unlocked) {
				nic_n_refused++;
				return -EPERM;
			}
			rc = register_netdev(nic_ndev);
			if (rc)
				return rc;
			nic_ndev_registered = 1;
			rlxfw_mark("N-NDREG");
			return (int)count;
		}
		if (!strcmp(buf + 7, "off")) {
			if (!nic_ndev_registered)
				return -ENXIO;
			unregister_netdev(nic_ndev);
			nic_ndev_registered = 0;
			rlxfw_mark("N-NDUNREG");
			return (int)count;
		}
		return -EINVAL;
	}
	if (!strcmp(buf, "disarm")) {
		nic_do_engine(0);
		if (nic_irq_taken) {
			free_irq(NIC_IRQ, &nic_lock);
			nic_irq_taken = 0;
		}
		nic_wr(NIC_CPURPDCR0, 0);
		nic_wr(NIC_CPURMDCR0, 0);
		nic_wr(NIC_CPUTPDCR0, 0);
		nic_armed = 0;
		rlxfw_mark("N-DISARM");
		return (int)count;
	}

	return -EINVAL;
}

/* ------------------------------------------------------------------------
 * Registration.
 *
 * `late_initcall` (level 7), for one reason and not by convention: the
 * vendor's `re865x_probe()` is `module_init`, i.e. `device_initcall`, level
 * 6, and it is the thing that turns the loader's DMA engine OFF.  Latching
 * this driver's boot state at level 7 therefore reads the engine AFTER the
 * vendor disarmed it, which is the state every verb below assumes.
 *
 * Latching it at level 4 like `rtl819x-switch.c` would read the LOADER's
 * still-running engine and every subsequent step would be starting from a
 * state that no longer exists by the time a verb is typed.  The two drivers
 * want opposite sides of the same boundary, and each says which and why.
 * ------------------------------------------------------------------------ */
static int __init rtl819x_nic_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("N0");

	nic_boot_icr    = nic_rd(NIC_CPUICR);
	nic_boot_iimr   = nic_rd(NIC_CPUIIMR);
	nic_boot_iisr   = nic_rd(NIC_CPUIISR);
	nic_boot_rpdcr0 = nic_rd(NIC_CPURPDCR0);
	nic_boot_rmdcr0 = nic_rd(NIC_CPURMDCR0);
	nic_boot_tpdcr0 = nic_rd(NIC_CPUTPDCR0);

	/* Marked individually so they are in the boot capture of EVERY boot
	 * rather than only in a /proc read somebody remembered to take.
	 * `N1` is the one that carries a prediction: it must read 00000000,
	 * and if it does not, the vendor's probe did not disarm the engine on
	 * this boot and every verb below is operating on a running engine. */
	rlxfw_markx("N1", nic_boot_icr);
	rlxfw_markx("N2", nic_boot_iimr);
	rlxfw_markx("N3", nic_boot_iisr);
	rlxfw_markx("N4", nic_boot_rmdcr0);

	/* s99a.  Initialised before the /proc entry exists, so no verb can
	 * reach a timer that has not been set up. */
	init_timer(&nic_recov_timer);
	nic_recov_timer.function = nic_recov_fn;
	nic_recov_timer.data = 0;
	nic_recov_timer_ready = 1;

	pde = create_proc_entry(RTL819X_NIC_PROC_NAME, 0644, NULL);
	if (!pde) {
		rlxfw_mark("N5-NOPROC");
		return 0;
	}
	pde->read_proc  = nic_read_proc;
	pde->write_proc = nic_write_proc;
	rlxfw_mark("N5");

	/* R6-4.  ALLOCATED here, REGISTERED only by a verb.  `alloc_netdev`
	 * with "rlx%d" rather than `alloc_etherdev`, whose format is "eth%d"
	 * -- the name is half of this gate's positive discriminator and it
	 * must not collide with the vendor's six interfaces.
	 *
	 * A failure here emits its own mark and returns 0.  An initcall that
	 * fails the boot to report that an OPTIONAL device could not be
	 * allocated would trade a working system for a diagnostic, and this
	 * driver's whole arrangement is that nothing depends on it. */
	nic_ndev = alloc_netdev(0, "rlx%d", ether_setup);
	if (!nic_ndev) {
		rlxfw_mark("N6-NONDEV");
		return 0;
	}
	nic_ndev->netdev_ops = &nic_netdev_ops;
	SET_ETHTOOL_OPS(nic_ndev, &nic_ethtool_ops);
	nic_ndev->irq = NIC_IRQ;
	nic_ndev->watchdog_timeo = 5 * HZ;
	memcpy(nic_ndev->dev_addr, nic_mac, 6);
	netif_napi_add(nic_ndev, &nic_napi, nic_poll, NIC_NAPI_WEIGHT);
	rlxfw_markx("N6", (u32)NIC_NAPI_WEIGHT);

	/* 1.4.  The two behaviours this boot STARTS in, in every boot capture:
	 * ph_follow << 4 | recov_mode, so a 1.4 boot that types nothing reads
	 * 00000011.  A verb typed later changes the /proc dump, not this line. */
	rlxfw_markx("N7", (u32)((nic_ph_follow << 4) | nic_recov_mode));

	return 0;
}

late_initcall(rtl819x_nic_init);
