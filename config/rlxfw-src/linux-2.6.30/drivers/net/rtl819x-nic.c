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
 * 1. It registers no `net_device` and no `ethtool` ops, and it touches no
 *    PHY.  That is R6-4.
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
 *    unmask at exhaustion -- but does not bind a `struct napi_struct`,
 *    because in 2.6.30 that needs a `net_device` and the `net_device` is
 *    R6-4.  The rung this file can walk is the masking and the re-arm race;
 *    the binding is named as not done rather than quietly skipped.
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
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

#define RTL819X_NIC_VERSION	"rtl819x-nic 1.0"
#define RTL819X_NIC_PROC_NAME	"rtl819x-nic"

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
#define NIC_BUF_SZ		2048	/* must agree with NIC_MBUF_2048 */
#define NIC_RX_OFFSET		2	/* 量: the loader's buffers are at
					 * `...9A`, 2 mod 4 */
#define NIC_DESC_BYTES		24	/* 量: stride on this die, and the
					 * header's "exactly 32 bytes" comment
					 * is wrong -- sizeof is 24 under
					 * CONFIG_RTL_8196E */

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

		bf = nic_dw(nic_rx_mb, i, 3);
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
		m = __raw_readl(nic_reg(NIC_CPUIIMR));
		__raw_writel(m | NIC_IE_RX_DONE_ALL | NIC_IE_PKTHDR_RUNOUT |
			     NIC_IE_MBUF_RUNOUT, nic_reg(NIC_CPUIIMR));
		spin_unlock_irqrestore(&nic_lock, flags);
	}
	return done;
}

static int nic_xmit(struct sk_buff *skb, struct net_device *dev)
{
	unsigned int i;
	unsigned long flags;
	u32 e, bf, len, k, icr, wrap, ph;

	if (!nic_engine_on) {
		dev_kfree_skb(skb);
		dev->stats.tx_dropped++;
		return NETDEV_TX_OK;
	}

	spin_lock_irqsave(&nic_lock, flags);

	i = nic_tx_idx;
	e = nic_re(nic_tx_ring, i);
	if (e & NIC_DESC_OWN) {
		/* The engine still owns this slot.  Stop the queue and tell
		 * the stack to retry -- do NOT drop, and do NOT free the skb,
		 * which the caller still owns after NETDEV_TX_BUSY. */
		netif_stop_queue(dev);
		nic_n_xmit_busy++;
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

static const struct net_device_ops nic_netdev_ops = {
	.ndo_open		= nic_ndo_open,
	.ndo_stop		= nic_ndo_stop,
	.ndo_start_xmit		= nic_xmit,
	.ndo_get_stats		= nic_ndo_stats,
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
	int rc;

	if (!nic_allocated)
		return -ENXIO;
	if (nic_engine_on)
		return -EBUSY;

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
	nic_wr(NIC_CPUTPDCR1, 0);
	nic_wr(NIC_CPUTPDCR2, 0);
	nic_wr(NIC_CPUTPDCR3, 0);

	nic_armed = 1;
	rlxfw_markx("N-ARM", nic_rx_ring);
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
			u32 bf = nic_dw(nic_rx_mb, i, 3);
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
	nic_wr(NIC_CPUIIMR, NIC_IIMR_LADDER);
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
	len += sprintf(page + len, "n_skb_fail %lu\n", nic_n_skb_fail);
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

	if (nic_allocated) {
		len += sprintf(page + len, "rx_ring %08X\n", nic_rx_ring);
		len += sprintf(page + len, "mb_ring %08X\n", nic_mb_ring);
		len += sprintf(page + len, "tx_ring %08X\n", nic_tx_ring);
		len += sprintf(page + len, "bufs %08X\n", nic_bufs);
		len += sprintf(page + len, "rx_idx %u\n", nic_rx_idx);
		len += sprintf(page + len, "tx_idx %u\n", nic_tx_idx);

		for (i = 0; i < NIC_RX_DESC; i++)
			len += sprintf(page + len,
				       "rxd%u %08X len %u f %04X pl %02X\n",
				       i, nic_re(nic_rx_ring, i),
				       NIC_PH_LEN(nic_dw(nic_rx_ph, i, 1)),
				       NIC_PH_FLAGS(nic_dw(nic_rx_ph, i, 3)),
				       NIC_PH_PORTLIST(nic_dw(nic_rx_ph, i,
							      3)));
		for (i = 0; i < NIC_TX_DESC; i++)
			len += sprintf(page + len,
				       "txd%u %08X len %u\n",
				       i, nic_re(nic_tx_ring, i),
				       NIC_PH_LEN(nic_dw(nic_tx_ph, i, 1)));
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
		len += sprintf(page + len, "rx_bytes ");
		for (i = 0; i < n; i++)
			len += sprintf(page + len, "%02X", nic_last_rx[i]);
		len += sprintf(page + len, "\n");
	}

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
	nic_ndev->irq = NIC_IRQ;
	nic_ndev->watchdog_timeo = 5 * HZ;
	memcpy(nic_ndev->dev_addr, nic_mac, 6);
	netif_napi_add(nic_ndev, &nic_napi, nic_poll, NIC_NAPI_WEIGHT);
	rlxfw_markx("N6", (u32)NIC_NAPI_WEIGHT);

	return 0;
}

late_initcall(rtl819x_nic_init);
