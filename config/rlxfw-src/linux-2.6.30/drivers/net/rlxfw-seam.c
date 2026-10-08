/*
 * rlxfw-seam.c -- what code outside the vendor Ethernet tree still needs from
 * it when that tree is not built.   R6b-8 8b.   THIS FILE IS NOT REALTEK'S.
 *
 * ======================================================================
 * WHAT IT IS
 * ======================================================================
 *
 * `CONFIG_RTL_819X_SWCORE=n` (config/rlxfw-kernel.delta: `quiet` and
 * `loud` since R6b-8 8g) drops `drivers/net/rtl819x/` and
 * `drivers/net/rtk_vlan.o` from the link.  Ten symbols that code OUTSIDE
 * that tree references are then defined nowhere -- R6-4's count, in four
 * places (config/host-compat/0007's header, and the R6-4 row of
 * config/rlxfw-kernel.delta).  The vendor callers may change only through
 * a marks row or a host-compat patch, and six of the ten sit in compiler-
 * output `.S` files and a WLAN driver whose conditional structure is not
 * this project's, so the ten are PROVIDED here instead, each with the value
 * the vendor's own code gives when it has nothing to report.
 *
 * The body is under `#ifndef CONFIG_RTL_819X_SWCORE`, so the SWCORE=y image
 * -- the mainline until 8g -- links the vendor's ten and this file adds only
 * `rlxfw_seam_id`, the witness `config/rlxfw-marks.tsv` MK12 reads in both
 * images (`str:rlxfw-seam`).  A body built beside the vendor's would be a
 * second definition of each name and the link would say so.
 *
 * ======================================================================
 * THE ONE WRITE: THE LOADER'S DMA ENGINE
 * ======================================================================
 *
 * The loader leaves the CPU port's DMA engine RUNNING: `CPUICR = C4000000`
 * at the prompt (量 `bench/2026-09-19b/X7-cpufull-a`), RXCMD set, rings at
 * `0xA040FC70` -- physical `0x0040FC70`, memory this kernel uses.
 * With SWCORE=y the vendor's `re865x_probe()` disarms it at
 * `device_initcall` (讀 `rtl_nic.c:6224-6225` in the staged tree:
 * `CPUIIMR = 0x00` then `CPUICR &= ~(TXCMD | RXCMD)`), and `RLXFW-N1` reads
 * `00000000` at `late_initcall` after it (量: 63 such lines in the committed
 * bench files at 95dabac, and no other value of N1 in any of them).  With
 * SWCORE=n nothing does, and `rtl819x-nic.c`'s own header says
 * why that is the dangerous state (`docs/KNOWN-ISSUES.md`, `R6-4`'s `D4`
 * row: "Remove the driver and something else must do that first").
 *
 * So the seam's `bsp_swcore_init()` makes the vendor's two writes, in the
 * vendor's order.  It is called from `bsp_setup()` (the `B07` mark's
 * anchor), the first call in `arch_mem_init()`, so it runs before
 * `bootmem_init()` and `paging_init()` (`B08`) -- before any allocator
 * exists, and EARLIER than the vendor's `device_initcall`.  A disarm moved
 * into `rtl819x-nic`'s `late_initcall` would be later than today's, and is
 * the wrong place.
 *
 * Each register and bit has two sources, as `rtl819x-nic.c` records for the
 * same names: 讀 `rtl865xc_asicregs.h` (`CPUICR` :492, `CPUIIMR` :512,
 * `TXCMD` :527, `RXCMD` :528, `CPU_IFACE_BASE` :491) and 量 on this die
 * (`CPUICR` `C4000000` at the loader, `00000000` under Linux after the
 * vendor's probe; `CPUIIMR` `000007F8` at the loader, whose decode against
 * the header has no residue -- `notes/nic-driver.md` § 2).
 *
 * The two marks put the before and after on every boot capture of the
 * SWCORE=n image, where `N1` alone would show only the after:
 *
 *   RLXFW-SM0=XXXXXXXX   CPUICR as the loader left it (predicted C4000000)
 *   RLXFW-SM1=XXXXXXXX   CPUICR read back after the write (predicted with
 *                        bits 31 and 30 clear, the rest as SM0)
 *
 * The SWCORE=y image prints neither: the vendor's `bsp_swcore_init()` runs
 * there, and the absence of both lines is how a capture says which one ran.
 *
 * ======================================================================
 * WHAT THIS FILE DOES NOT DO
 * ======================================================================
 *
 * 1. It does not configure the switch.  Every switch register the vendor's
 *    probe wrote is left here as the loader left it.  rtl819x-switch's verbs,
 *    which /init types, take some over: 1.5's `init` sets `EnablePHYIf`
 *    (`notes/switch-driver.md` § 8.3); 1.6's `vlan` writes the VLAN group.
 * 2. It does not check `REVR`.  The vendor's `bsp_swcore_init()` returns
 *    non-zero for an unrecognised chip, and `bsp_setup()` then halts; this
 *    board's `REVR` is `8196E001` (量, `SPEC.md` `REG-29`) and `RLXFW-B07`
 *    reads `00000000` (量: 169 such lines in the committed bench files at
 *    95dabac, and no other value in a capture), so the seam returns 0 and
 *    the halt branch is not taken.
 * 3. It does not bound the window before it runs.  From kernel entry to
 *    `bsp_setup()` the loader's engine is still armed, on this image as on
 *    every earlier one; the seam shortens the window the vendor's probe
 *    closed later, it does not remove it.  What owns `0x8040FC70` in each
 *    image's `System.map` is `notes/switch-driver.md` § 13's reading.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>

/* The witness, in both images.  Not static and not const-folded away: a
 * global definition is kept by the compiler, and MK12's `str:rlxfw-seam`
 * finds it in `.rodata` of the SWCORE=y image, where nothing else of this
 * file is linked. */
const char rlxfw_seam_id[] = "rlxfw-seam 1.0";

#ifndef CONFIG_RTL_819X_SWCORE

struct net_device;

/* ----------------------------------------------------------------------
 * 1. bsp_swcore_init -- the BSP.  Caller: boards/rtl8196e/bsp/setup.c:173
 * in the staged tree (`ret = bsp_swcore_init(version);`, under
 * CONFIG_RTL_819X, which stays y; the declaration is setup.c:31).  Vendor
 * definition: drivers/net/rtl819x/AsicDriver/96E/rtl865x_asicBasic.S:393.
 * ---------------------------------------------------------------------- */
#define SEAM_CPU_IFACE_PHYS	0x18010000	/* CPU_IFACE_BASE, :491 */
#define SEAM_CPUICR		0x000		/* :492 */
#define SEAM_CPUIIMR		0x028		/* :512 */
#define SEAM_TXCMD		(1u << 31)	/* :527 */
#define SEAM_RXCMD		(1u << 30)	/* :528 */

static inline void __iomem *seam_reg(unsigned int off)
{
	return (void __iomem *)CKSEG1ADDR(SEAM_CPU_IFACE_PHYS + off);
}

int bsp_swcore_init(unsigned int version)
{
	u32 icr = __raw_readl(seam_reg(SEAM_CPUICR));

	rlxfw_markx("SM0", icr);
	__raw_writel(0, seam_reg(SEAM_CPUIIMR));
	__raw_writel(icr & ~(SEAM_TXCMD | SEAM_RXCMD), seam_reg(SEAM_CPUICR));
	rlxfw_markx("SM1", __raw_readl(seam_reg(SEAM_CPUICR)));
	return 0;
}

/* ----------------------------------------------------------------------
 * 2-4. The vendor fast path, the .S files in net/rtl/fastpath/96E/: compiler
 * output with no cpp conditionals, so its three calls survive any
 * configuration.  (Spelt this way because a slash-star inside a comment is
 * a warning, and the first build of this file had one.)
 * ---------------------------------------------------------------------- */

/* 2. Callers: fast_l2tp_core.S:334 and :422 (`jal`); the return value is
 * overwritten at both (`lui $2` at :337, `li $2,2` at :425).  Vendor
 * definition: drivers/net/rtl819x/common/rtl865x_netif.c:4085, which looks
 * the name up in the switch's netif table.  There is no such table here, so
 * the answer is the vendor's own not-found value, RTL_EENTRYNOTFOUND
 * (drivers/net/rtl819x/common/rtl_errno.h:22). */
int rtl865x_setNetifType(char *name, unsigned int ifType)
{
	return -3;	/* RTL_EENTRYNOTFOUND */
}

/* 3. Caller: fastpath_core.S:3016, in rtl_br_fdb_time_update(), which moves
 * a bridge FDB timestamp only when the hardware age is exactly 150, 300 or
 * 450 (:3020-:3036).  Vendor definition: drivers/net/rtl819x/l2Driver/
 * rtl865x_fdb.c:234, which reads the switch's L2 table.  0 is none of the
 * three, so the bridge's own ageing stands -- the "no hardware entry"
 * answer.  Reachable only with a bridge, which no rlxfw image configures
 * (推). */
int rtl_get_hw_fdb_age(unsigned int fid, void *mac, unsigned int flags)
{
	return 0;
}

/* 4. Caller: filter.S:8211; the return value is discarded (the caller
 * returns 0 whatever it gets, :8217).  Vendor definition: drivers/net/
 * rtl819x/igmpsnooping/igmp_delete.c:116, which creates a netlink socket
 * for the vendor's IGMP-snooping table and returns -EIO when it cannot
 * (:122).  No socket is created here, so the failure value is the true
 * one. */
int igmp_delete_init_netlink(void)
{
	return -EIO;
}

/* ----------------------------------------------------------------------
 * 5-9. The WLAN driver's bridge shortcut, drivers/net/wireless/rtl8192cd/
 * (the tree that builds; rtl8192e/ does not).  Vendor definitions:
 * drivers/net/rtl819x/rtl_nic.c:210-226, set non-NULL only by the vendor
 * Ethernet RX path (rtl_nic.c:2707-2715).  The WLAN objects the link names
 * (讀, probe cell r6b8bp1's link) read them in 8192cd_rx.o (8192cd_rx.c:878-896,
 * get_eth_cached_dev) and write only NULL and zeroes in 8192cd_osdep.o
 * (8192cd_osdep.c:7885-7897, clear_shortcut_cache).  Zero storage is the
 * vendor's empty-cache state, and nothing here fills it.
 * ---------------------------------------------------------------------- */
struct net_device *cached_dev;
struct net_device *cached_dev2;
unsigned char cached_eth_addr[6];	/* ETHER_ADDR_LEN */
unsigned char cached_eth_addr2[6];

/* 9. Caller: 8192cd_osdep.c:7983, update_hw_l2table("wlan", mac) when a
 * WLAN station associates, under CONFIG_RTL_819X (the eCos arm at :7974 is
 * not built).  Vendor definition: drivers/net/rtl819x/
 * l2Driver/rtl865x_fdb.c:879, which refreshes or removes that MAC's entry
 * in the switch's L2 table.  rlxfw writes no dynamic L2 entry, so there is
 * nothing to refresh. */
void update_hw_l2table(const char *srcName, const unsigned char *addr)
{
}

/* ----------------------------------------------------------------------
 * 10. The feature glue.  Readers: net/rtl/features/rtl_features.c:1103,
 * :1117, :1125 (rtl865x_getWanDev, compiled under CONFIG_NET_SCHED &&
 * CONFIG_RTL_IPTABLES_FAST_PATH), and the constants it compares against
 * come from include/net/rtl/rtl_nic.h through config/host-compat/0008.
 * Vendor definition: drivers/net/rtl819x/rtl_nic.c:517, GATEWAY_MODE
 * (0, include/net/rtl/rtl_nic.h:228) on this configuration; nothing writes
 * it once rtl_nic.c is not built.
 * ---------------------------------------------------------------------- */
int rtl865x_curOpMode;	/* 0 == GATEWAY_MODE */

#endif /* !CONFIG_RTL_819X_SWCORE */
