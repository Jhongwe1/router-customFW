/*
 * rtl819x-switch.c -- rlxfw's switch-core driver for the RTL8196E.
 *
 * R6-2: "the switch to a dumb state from my code -- all ports one VLAN, no
 * acceleration", whose DoD is *a register read-back whose value differs from
 * RESET*, and whose named failure mode is *that a dumb switch looks identical
 * to a switch nobody configured*.
 *
 * ======================================================================
 * WHY THIS DRIVER EXISTS IN THIS SHAPE, WHICH IS A MEASUREMENT PROBLEM
 * BEFORE IT IS A CONFIGURATION PROBLEM
 * ======================================================================
 *
 * 🔴 `bench/2026-09-17b/PREDICTIONS-B25-block24.md:96` recorded, before this
 * driver existed, that the DoD is *"not satisfiable today: none of the eight
 * has a known reset value"*.  That sentence was true of the method available
 * on 2026-09-17 morning and it is not true of this part.
 *
 * 讀 `rtl865xc_asicregs.h:1399-1446`: `SSIR` (alias `SIRR`) at
 * `SWMISC_BASE + 0x04` = `0xBB804204` carries `SwitchFullRst = (1<<2)`,
 * commented *"Reset all tables & queues"*, and `TRXRDY = (1<<0)`,
 * *"Start normal TX and RX"*.  讀 `rtl865x_asicCom.c:2002-2040`: the vendor's
 * own bring-up asserts it.  So the reset state is not a documentary gap --
 * it is a state this driver can ENTER and then read, on this die.
 *
 * That turns `D2` from a substitution into a measurement, and it makes the
 * proof four-cornered rather than two:
 *
 *   S0   the loader's state          -- 量 already, bench/2026-09-17b block 24
 *   S0'  after early kernel init,    -- latched by this driver at
 *        before the vendor NIC          subsys_initcall.  NOBODY HAS EVER
 *        driver runs                    MEASURED THIS STATE.
 *   S1   after FULL_RST              -- `reset` verb.  The reset baseline.
 *   S3   this driver's dumb config   -- `dumb` verb.
 *
 * `D2` is then **S3 != S1**, register by register, with:
 *
 *   - a POSITIVE control on the reset: at least one register must satisfy
 *     S1 != S0'.  If `FULL_RST` moves nothing, the write did nothing and the
 *     whole block is void.  That is the refutation condition, written here
 *     before the verb was run once.
 *   - a NEGATIVE control on the writes: a register this driver never writes
 *     must satisfy S3 == S1.  If everything moves, something other than this
 *     driver is moving it.
 *   - a ROUND TRIP: restore S0' and read again.  If a register does not come
 *     back, it is not a plain read/write cell and a read-back is not the
 *     proof `D2` assumes it is.  This part has one such register already --
 *     `WDTCLR` does not read back (`SPEC.md` `FW-52`) -- so this is a
 *     measured hazard and not a hypothetical one.
 *
 * ⚠️ THE LIMIT, STATED HERE RATHER THAN LEFT TO BE FOUND.  `FULL_RST` is a
 * SOFT reset of "tables & queues".  It is NOT proven identical to a power-on
 * reset.  What this driver can support is *differs from the state this part's
 * own documented full reset leaves it in* -- strictly stronger than "differs
 * from loader-state", strictly weaker than "differs from the power-on
 * default".  The gap is named, not hidden.
 *
 * 🟢 And there is an independent check available on exactly one register.
 * The draft datasheet's Table 64 gives per-bit defaults for `PCRP0`-`PCRP4`
 * which assemble to `0x007F....`, and this unit reads `PCRP0 = 0x007F0039`.
 * So after `FULL_RST`, `PCRP0`'s top half is PREDICTED to be `0x007F`.  If it
 * is, the "full reset as a reset baseline" method is validated against a
 * documentary source on the one register that has one.  If it is not, the
 * method is refuted -- which is also a result, and is why the prediction is
 * written down here.
 *
 * ======================================================================
 * WHY `MSCR` AND `VCR0` ARE IN THE TABLE THOUGH NOTHING HAS EVER READ THEM
 * ======================================================================
 *
 * 🔴🔴 `SPEC.md` `NET-21` derives this project's switch-register population
 * from 48 `lui ...,0xbb80` sites in the LOADER, converging on 13 addresses.
 * That is *what one agent touched*.  It is not *what configures the switch*.
 * 量 2026-09-17 (`tools/hdrcensus.py`): of the 21 addresses the vendor header
 * declares in the ALE block, NINETEEN have never been printed by this
 * repository -- and `MSCR`, the switch's operation-layer mode register, is
 * one of them.  `VCR0`, which holds the 802.1Q-unaware bit, is another.
 *
 * A census whose population is one agent's behaviour is blind to everything
 * that agent ignores.  Both registers are the direct object of R6-2's own
 * one-line definition, and neither was in the census that was supposed to
 * load it.
 *
 * ======================================================================
 * WHAT THIS DRIVER DOES NOT DO
 * ======================================================================
 *
 * 1. It does not touch the CPU-port DMA rings, the interrupt, or any
 *    `net_device`.  That is R6-3 and it is a different driver.
 * 2. It writes NOTHING at boot.  Every write is behind a verb AND behind an
 *    explicit runtime unlock, so a boot of this image is read-only by
 *    construction and `n_writes` reads 0 on a capture that proves it.
 * 3. It does not write the VLAN TABLE.  The table is reached indirectly
 *    through the TACI block (`SWTACR`/`SWTAA`/`TCR7`), which is a protocol
 *    and not a register write.  推 that `En1QtagVIDignore` makes the table
 *    irrelevant for a dumb switch; that 推 is untested and the table is left
 *    alone until it is.
 * 4. It says nothing about whether the silicon agrees with the header.  This
 *    project has one measured counter-example already: the header names
 *    `PCRP5` at `0xBB804118` and the die reads `00000000` where every
 *    neighbour reads `xx7F00xx`.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/spinlock.h>
#include <linux/delay.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/module.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/addrspace.h>
#include <asm/uaccess.h>

#define RTL819X_SW_VERSION	"rtl819x-switch 1.3"

/* 0xBB800000 through KSEG1.  讀 `rtl865xc_asicregs.h:147,171`:
 * `REAL_SWCORE_BASE 0xBB800000`, and `SWCORE_BASE` takes it in every build
 * that is not one of the three RTL865X_MODEL_* host simulators. */
#define RTL819X_SW_PHYS		0x1B800000
#define RTL819X_SW_SIZE		0x00008000

/* 0xB8000010, `SYS_CLK_MAG` (`:3521`), which is in the SYSTEM block and not
 * the switch core.  Only the vendor's reset recipe touches it. */
#define RTL819X_SYS_CLK_MAG_PHYS	0x18000010
#define RTL819X_CM_ACTIVE_SWCORE	(1u << 11)	/* :3524 */
#define RTL819X_CM_PROTECT		(1u << 27)	/* :3525 */

/* SSIR/SIRR, `:1402`/`:1435`, and its three named bits `:1442`-`:1444`. */
#define RTL819X_SW_SSIR		0x4204
#define RTL819X_SW_FULL_RST	(1u << 2)
#define RTL819X_SW_SEMI_RST	(1u << 1)
#define RTL819X_SW_TRXRDY	(1u << 0)

/* The registers this driver's dumb configuration writes.  Offsets 讀 from
 * `rtl865xc_asicregs.h`; every one of them was re-derived by
 * `tools/hdrcensus.py` from the same header under `-D CONFIG_RTL_8196E`
 * rather than copied out of a note. */
#define RTL819X_SW_MSCR		0x4410		/* :1483 */
#define RTL819X_SW_SWTCR0	0x4418		/* :1486 */
#define RTL819X_SW_SWTCR1	0x441C		/* :1487 */
#define RTL819X_SW_VCR0		0x4A00		/* :2299 */
#define RTL819X_SW_PVCR0	0x4A08		/* :2301 */
#define RTL819X_SW_PVCR4	0x4A18		/* :2305 */

/* Port status, one register per port.  量 two sources, which is the rule
 * for a register entering code: derived from `rtl865xc_asicregs.h`
 * (`PCRAM_BASE = SWCORE_BASE + 0x4100` at :1132, `PSRP0 = 0x028 +
 * PCRAM_BASE` at :1143, `PortStatusLinkUp = (1<<4)` at :1332), and
 * cross-checked against readings this repository already holds --
 * `PSRP6` at `0xBB804140` reading `0000007A`, which the same base
 * arithmetic produces.  Ports 0-4 are the ones with PHYs behind them;
 * 5-8 are not (`NET-40`). */
#define RTL819X_SW_PSRP0	0x4128
#define RTL819X_SW_NPHYPORT	5
#define RTL819X_PSRP_LINKUP	(1u << 4)

/* MSCR fields, `:1553`-`:1562`. */
#define RTL819X_MSCR_MODE_L2	(1u << 0)
#define RTL819X_MSCR_MODE_L3	(1u << 1)
#define RTL819X_MSCR_MODE_L4	(1u << 2)
#define RTL819X_MSCR_EGRESS_ACL	(1u << 3)
#define RTL819X_MSCR_INGRESS_ACL (1u << 4)
#define RTL819X_MSCR_ENABLE_ST	(1u << 5)

/* VCR0 fields, `:2340`, `:2387`. */
#define RTL819X_VCR0_1QTAG_IGNORE	(1u << 31)
#define RTL819X_VCR0_INGRESS_FILT_MASK	0x1FFu

/* PVCR packs TWO ports per word: PVID[11:0] + priority[14:12] for the even
 * port, PVID[27:16] + priority[30:28] for the odd one (`:2393`-`:2430`).
 * 🟢 量 2026-09-17: decoding block 26's readings that way gives ports 0-3 on
 * VID 9, port 4 on VID 8, port 8 on VID 9 -- and this image's OWN boot line
 * `eth1 added. vid=8 Member port 0x10` says bit 4, i.e. port 4, by a path
 * that shares no code with the register read. */
#define RTL819X_PVID_DUMB	1u
#define RTL819X_PVCR_PAIR(v)	(((v) & 0xFFFu) | (((v) & 0xFFFu) << 16))

#define RTL819X_SW_PROC_NAME	"rtl819x-switch"

/* The unlock token.  It is a word rather than a flag so that `unlock` cannot
 * be reached by a stray byte on a serial line -- this board's console is the
 * only channel and `FW-41` measured ash putting a refused write's payload on
 * it minus its last character. */
#define RTL819X_SW_UNLOCK_TOKEN	"i-mean-it"

/* ------------------------------------------------------------------------
 * The census table.  One array, so `dump`, `snap` and `diff` are generic and
 * a register is added in exactly one place.
 *
 * `both` marks the twelve that already have a loader-state AND a Linux-state
 * reading (`docs/loader-phy-and-switch.md` § 2026-09-17).  It is printed so a
 * reader can tell a register with two prior readings from one with none
 * without consulting another file.
 * ------------------------------------------------------------------------ */

struct rtl819x_sw_reg {
	const char	*name;
	u16		off;
	u8		both;	/* has a prior loader- AND Linux-state reading */
	u8		dumb;	/* this driver's `dumb` verb writes it */
};

static const struct rtl819x_sw_reg rtl819x_sw_regs[] = {
	{ "CVIDR",	0x4200, 0, 0 },	/* chip version id -- the read-path control */
	{ "SSIR",	0x4204, 0, 0 },
	{ "MACCR",	0x4000, 1, 0 },
	{ "MDCIOCR",	0x4004, 1, 0 },
	{ "MDCIOSR",	0x4008, 1, 0 },
	{ "PITCR",	0x4100, 0, 0 },
	{ "PCRP0",	0x4104, 0, 0 },
	{ "PCRP1",	0x4108, 0, 0 },
	{ "PCRP2",	0x410C, 0, 0 },
	{ "PCRP3",	0x4110, 0, 0 },
	{ "PCRP4",	0x4114, 0, 0 },
	{ "PCRP5",	0x4118, 0, 0 },
	{ "PCRP6",	0x411C, 0, 0 },
	{ "PSRP0",	0x4128, 0, 0 },
	{ "PSRP3",	0x4134, 0, 0 },
	{ "PSRP5",	0x413C, 0, 0 },
	{ "PSRP6",	0x4140, 0, 0 },
	{ "PSRP7",	0x4144, 0, 0 },
	{ "P0GMIICR",	0x414C, 1, 0 },
	{ "MEMCR",	0x4234, 1, 0 },
	{ "TEACR",	0x4400, 0, 0 },
	{ "ALECR",	0x440C, 0, 0 },
	{ "MSCR",	0x4410, 0, 1 },	/* never read on this die before today */
	{ "SWTCR0",	0x4418, 1, 1 },
	{ "SWTCR1",	0x441C, 0, 1 },	/* never read on this die before today */
	{ "FFCR",	0x4428, 1, 0 },
	{ "VCR0",	0x4A00, 0, 1 },	/* never read on this die before today */
	{ "VCR1",	0x4A04, 0, 0 },
	{ "PVCR0",	0x4A08, 1, 1 },
	{ "PVCR1",	0x4A0C, 0, 1 },
	{ "PVCR2",	0x4A10, 0, 1 },
	{ "PVCR3",	0x4A14, 0, 1 },
	{ "PVCR4",	0x4A18, 0, 1 },
	{ "PBVCR0",	0x4A1C, 0, 0 },
	{ "SWTACR",	0x4D00, 1, 0 },
	{ "SWTAA",	0x4D08, 1, 0 },
	{ "TCR7",	0x4D3C, 1, 0 },
};

#define RTL819X_SW_NREG	ARRAY_SIZE(rtl819x_sw_regs)

/* Four slots: 0 is latched at init (S0'), 1..3 are the operator's. */
#define RTL819X_SW_NSLOT	4
#define RTL819X_SW_SLOT_BOOT	0

static u32 rtl819x_sw_slot[RTL819X_SW_NSLOT][RTL819X_SW_NREG];
static u8  rtl819x_sw_slot_full[RTL819X_SW_NSLOT];

static DEFINE_SPINLOCK(rtl819x_sw_lock);

static int  rtl819x_sw_unlocked;		/* writes permitted at all */
static unsigned long rtl819x_sw_n_writes;	/* THE number */
static unsigned long rtl819x_sw_n_reads;
static unsigned long rtl819x_sw_n_refused;	/* writes the guard stopped */
static unsigned long rtl819x_sw_n_reset;
static unsigned long rtl819x_sw_n_dumb;
static unsigned long rtl819x_sw_n_restore;

/* Latched at init before anything else, so a later reader can see whether the
 * switch moved between boot and now without having captured the boot. */
static u32 rtl819x_sw_boot_cvidr;
static void rtl819x_sw_lde_note(unsigned int off, u32 v);	/* 1.2, below */
static inline void __iomem *rtl819x_sw_reg(unsigned int off)
{
	return (void __iomem *)KSEG1ADDR(RTL819X_SW_PHYS + off);
}

static inline u32 rtl819x_sw_rd(unsigned int off)
{
	u32 v = __raw_readl(rtl819x_sw_reg(off));
	rtl819x_sw_lde_note(off, v);	/* 1.2: keep a PSRP bit 8 this read consumed */
	rtl819x_sw_n_reads++;
	return v;
}

/* THE ONLY CONFIGURATION WRITE PATH, so `n_writes` counts writes, not callers
 * who remembered to, and the guard comes BEFORE the store.  1.3: MDIO commands
 * (MDCIOCR stores) have one path of their own, `rtl819x_mdio_xfer` at the end
 * of this file, with their own counters and their own gate. */
static int rtl819x_sw_wr(unsigned int off, u32 v)
{
	if (!rtl819x_sw_unlocked) {
		rtl819x_sw_n_refused++;
		return -EPERM;
	}
	__raw_writel(v, rtl819x_sw_reg(off));
	rtl819x_sw_n_writes++;
	return 0;
}

/* R6-4.  THE ONE THING `rtl819x-nic.c` BORROWS FROM THIS DRIVER.
 *
 * `ethtool rlx0` wants a link state.  The CPU port does not have one in
 * any useful sense -- it has no PHY, so its fabric link is up by
 * construction and `PSRP6` bit 4 has read set in every reading this
 * project has taken.  Reporting that would be reporting a constant, and
 * `RUNSHEET.md:317`'s house rule is that a tool which always says 1
 * cannot fail.
 *
 * So this answers the question a user of `rlx0` actually has: is any
 * jack live?  It has two states, and the operator changes it with a
 * cable, which makes it an observable rather than a field.
 *
 * ⚠️ It is deliberately NOT a snapshot read.  It goes to the silicon on
 * every call, because a cached answer would make the cable stop being
 * the control.  `n_linkq` is its own denominator so the ethtool path is
 * separable from every other read this driver does -- without it,
 * `n_reads` moving would not say who moved it.
 *
 * 🔴 Returns 0 rather than an error when nothing is linked, and -ENODEV
 * only before this driver has latched.  A caller that cannot tell those
 * apart must treat both as down, which is what the NIC driver does. */
static unsigned long rtl819x_sw_n_linkq;
static int rtl819x_sw_latched;

int rtl819x_sw_any_link(void)
{
	unsigned int p;
	int any = 0;

	if (!rtl819x_sw_latched)
		return -ENODEV;
	rtl819x_sw_n_linkq++;
	for (p = 0; p < RTL819X_SW_NPHYPORT; p++)
		if (rtl819x_sw_rd(RTL819X_SW_PSRP0 + p * 4)
		    & RTL819X_PSRP_LINKUP)
			any = 1;
	return any;
}

/* Slot 0's value for a named register, or 0xDEADxxxx if the name is not in
 * the table.  A miss returns a value that cannot be mistaken for a register
 * reading rather than 0, because 0 is a perfectly ordinary thing for these
 * registers to hold and a typo would then be invisible. */
static u32 rtl819x_sw_boot_of(const char *name)
{
	unsigned int i;

	for (i = 0; i < RTL819X_SW_NREG; i++)
		if (!strcmp(rtl819x_sw_regs[i].name, name))
			return rtl819x_sw_slot[RTL819X_SW_SLOT_BOOT][i];
	return 0xDEADBEEFu;
}

static void rtl819x_sw_snapshot(int slot)
{
	unsigned int i;

	for (i = 0; i < RTL819X_SW_NREG; i++)
		rtl819x_sw_slot[slot][i] = rtl819x_sw_rd(rtl819x_sw_regs[i].off);
	rtl819x_sw_slot_full[slot] = 1;
}

/* ------------------------------------------------------------------------
 * The reset verbs.
 *
 * TWO recipes, deliberately, because they are not known to be equivalent and
 * this is the only instrument that could say so.
 *
 *   `reset full`    SSIR |= FULL_RST, then wait.  What the register's own
 *                   comment promises.
 *   `reset vendor`  the whole of `FullAndSemiReset()` for this part, which
 *                   follows FULL_RST with a 650 ms clock-gate cycle of the
 *                   switch core.
 *
 * 🔴 讀 `rtl865x_asicCom.c:2002-2016`: on the 8196E the vendor does NOT trust
 * `FULL_RST` alone.  Whether the extra 650 ms changes any register is
 * unmeasured by anybody, and `resetcmp` in the card is what asks.
 *
 * Neither sets TRXRDY.  Restarting traffic is `start`, a separate verb, so
 * that "the switch was reset" and "the switch was restarted" are two
 * observable events and not one.
 * ------------------------------------------------------------------------ */

static int rtl819x_sw_do_reset(int vendor_recipe)
{
	void __iomem *clk = (void __iomem *)KSEG1ADDR(RTL819X_SYS_CLK_MAG_PHYS);
	u32 v;
	int rc;

	v = rtl819x_sw_rd(RTL819X_SW_SSIR);
	rc = rtl819x_sw_wr(RTL819X_SW_SSIR, v | RTL819X_SW_FULL_RST);
	if (rc)
		return rc;
	mdelay(300);

	if (vendor_recipe) {
		/* This touches SYS_CLK_MAG, which is NOT in the switch window
		 * and NOT in the census table -- so it is written directly and
		 * counted, rather than pretending the table covers it. */
		if (!rtl819x_sw_unlocked) {
			rtl819x_sw_n_refused++;
			return -EPERM;
		}
		__raw_writel(__raw_readl(clk) | RTL819X_CM_PROTECT, clk);
		__raw_writel(__raw_readl(clk) & ~RTL819X_CM_ACTIVE_SWCORE, clk);
		rtl819x_sw_n_writes += 2;
		mdelay(300);
		__raw_writel(__raw_readl(clk) | RTL819X_CM_ACTIVE_SWCORE, clk);
		__raw_writel(__raw_readl(clk) & ~RTL819X_CM_PROTECT, clk);
		rtl819x_sw_n_writes += 2;
		mdelay(50);
	}

	rtl819x_sw_n_reset++;
	rlxfw_markx("SW-RST", vendor_recipe ? 2u : 1u);
	return 0;
}

/* ------------------------------------------------------------------------
 * The dumb configuration.
 *
 * Nine writes.  Each one is preceded by a read of the same register in the
 * same verb, because eight of the nine registers have no prior reading on
 * this die at all and the read is therefore the measurement, not a courtesy.
 * ------------------------------------------------------------------------ */

static int rtl819x_sw_do_dumb(void)
{
	u32 v;
	int rc;

	/* L2 only: clears Mode_enL3/enL4, both ACLs, spanning tree and NAT
	 * test mode in one word.  This is "no acceleration", exactly. */
	(void)rtl819x_sw_rd(RTL819X_SW_MSCR);
	rc = rtl819x_sw_wr(RTL819X_SW_MSCR, RTL819X_MSCR_MODE_L2);
	if (rc)
		return rc;

	/* 802.1Q-unaware, admit all frame types on every port, no VLAN
	 * ingress filtering.  Setting bit 31 and clearing the rest does all
	 * three, because AdmitAllFrame is 0 for every port. */
	(void)rtl819x_sw_rd(RTL819X_SW_VCR0);
	rc = rtl819x_sw_wr(RTL819X_SW_VCR0, RTL819X_VCR0_1QTAG_IGNORE);
	if (rc)
		return rc;

	/* Every port's PVID to 1.  PVCR0..3 carry two ports each; PVCR4
	 * carries port 8 alone, so its high half is left zero rather than
	 * written with a PVID for a port that does not exist. */
	(void)rtl819x_sw_rd(RTL819X_SW_PVCR0 + 0x00);
	rc = rtl819x_sw_wr(RTL819X_SW_PVCR0 + 0x00,
			   RTL819X_PVCR_PAIR(RTL819X_PVID_DUMB));
	if (rc)
		return rc;
	(void)rtl819x_sw_rd(RTL819X_SW_PVCR0 + 0x04);
	rc = rtl819x_sw_wr(RTL819X_SW_PVCR0 + 0x04,
			   RTL819X_PVCR_PAIR(RTL819X_PVID_DUMB));
	if (rc)
		return rc;
	(void)rtl819x_sw_rd(RTL819X_SW_PVCR0 + 0x08);
	rc = rtl819x_sw_wr(RTL819X_SW_PVCR0 + 0x08,
			   RTL819X_PVCR_PAIR(RTL819X_PVID_DUMB));
	if (rc)
		return rc;
	(void)rtl819x_sw_rd(RTL819X_SW_PVCR0 + 0x0C);
	rc = rtl819x_sw_wr(RTL819X_SW_PVCR0 + 0x0C,
			   RTL819X_PVCR_PAIR(RTL819X_PVID_DUMB));
	if (rc)
		return rc;
	(void)rtl819x_sw_rd(RTL819X_SW_PVCR4);
	rc = rtl819x_sw_wr(RTL819X_SW_PVCR4, RTL819X_PVID_DUMB);
	if (rc)
		return rc;

	/* SWTCR0: clear the NAPT trap/learn/delete bits and the unknown-VID
	 * trap, leave WANRouteMode at Forward (0), and KEEP the rest of the
	 * word -- `MultiPortModeP` is nine bits of port configuration this
	 * driver has no business inventing a value for.  Read-modify-write,
	 * and the read is in the capture. */
	v = rtl819x_sw_rd(RTL819X_SW_SWTCR0);
	v &= ~((1u << 15) | (1u << 14) | (3u << 3) | (1u << 2) | (1u << 1) |
	       (1u << 0));
	rc = rtl819x_sw_wr(RTL819X_SW_SWTCR0, v);
	if (rc)
		return rc;

	/* SWTCR1: every stateful-inspection enable off.  Whole-word, because
	 * every named bit in it is an accelerator of some kind. */
	(void)rtl819x_sw_rd(RTL819X_SW_SWTCR1);
	rc = rtl819x_sw_wr(RTL819X_SW_SWTCR1, 0);
	if (rc)
		return rc;

	rtl819x_sw_n_dumb++;
	rlxfw_mark("SW-DUMB");
	return 0;
}

/* Write a slot back, register by register, skipping the ones a slot cannot
 * legitimately restore: `CVIDR` is a version id and `MDCIOSR`/`PSRP*` are
 * status.  Writing a status register back is not a restore, it is a write to
 * a register whose behaviour under write is unknown. */
static int rtl819x_sw_do_restore(int slot)
{
	unsigned int i;
	int rc;

	if (!rtl819x_sw_slot_full[slot])
		return -ENODATA;

	for (i = 0; i < RTL819X_SW_NREG; i++) {
		const struct rtl819x_sw_reg *r = &rtl819x_sw_regs[i];

		if (!r->dumb)
			continue;	/* only what `dumb` disturbed */
		rc = rtl819x_sw_wr(r->off, rtl819x_sw_slot[slot][i]);
		if (rc)
			return rc;
	}
	rtl819x_sw_n_restore++;
	rlxfw_markx("SW-RESTORE", (unsigned)slot);
	return 0;
}

/* ------------------------------------------------------------------------
 * /proc
 * ------------------------------------------------------------------------ */

/* 🔴 `read_proc_t` sprintfs into ONE 4,096-byte page with no bounds check --
 * the same hard limit `rtl819x-spi` 1.1's two-level map was shaped by.  The
 * table is 37 registers at ~22 bytes plus ~20 fields, which is ~1.2 KiB; the
 * budget below is what keeps that a fact rather than a hope. */
#define RTL819X_SW_PAGE_BUDGET	3600
static int rtl819x_sw_lde_lines(char *page);	/* 1.2, below */
static int rtl819x_sw_read_proc(char *page, char **start, off_t off,
				int count, int *eof, void *data)
{
	unsigned int i;
	int len = 0;

	len += sprintf(page + len, "version %s\n", RTL819X_SW_VERSION);
	len += sprintf(page + len, "nreg %u\n", (unsigned)RTL819X_SW_NREG);
	len += sprintf(page + len, "unlocked %d\n", rtl819x_sw_unlocked);
	len += sprintf(page + len, "n_writes %lu\n", rtl819x_sw_n_writes);
	len += sprintf(page + len, "n_refused %lu\n", rtl819x_sw_n_refused);
	len += sprintf(page + len, "n_reads %lu\n", rtl819x_sw_n_reads);
	len += sprintf(page + len, "n_reset %lu\n", rtl819x_sw_n_reset);
	len += sprintf(page + len, "n_dumb %lu\n", rtl819x_sw_n_dumb);
	len += sprintf(page + len, "n_restore %lu\n", rtl819x_sw_n_restore);
	len += sprintf(page + len, "boot_cvidr %08X\n", rtl819x_sw_boot_cvidr);

	for (i = 0; i < RTL819X_SW_NSLOT; i++)
		len += sprintf(page + len, "slot%u_full %d\n", i,
			       (int)rtl819x_sw_slot_full[i]);
	len += rtl819x_sw_lde_lines(page + len);	/* 1.2: before the table */
	/* live, plus slot 0 (S0', latched at subsys_initcall) beside it, so a
	 * single read answers "did this move since boot" without arithmetic
	 * by the reader. */
	for (i = 0; i < RTL819X_SW_NREG && len < RTL819X_SW_PAGE_BUDGET; i++) {
		const struct rtl819x_sw_reg *r = &rtl819x_sw_regs[i];

		len += sprintf(page + len, "r %-9s %04X %08X %08X %d%d\n",
			       r->name, r->off, rtl819x_sw_rd(r->off),
			       rtl819x_sw_slot[RTL819X_SW_SLOT_BOOT][i],
			       (int)r->both, (int)r->dumb);
	}

	*eof = 1;
	return len;
}

static int rtl819x_sw_verb_diff(int a, int b)
{
	unsigned int i, n = 0;

	if (!rtl819x_sw_slot_full[a] || !rtl819x_sw_slot_full[b])
		return -ENODATA;

	for (i = 0; i < RTL819X_SW_NREG; i++)
		if (rtl819x_sw_slot[a][i] != rtl819x_sw_slot[b][i])
			n++;

	/* The COUNT is the mark.  A per-register list would not survive
	 * `FW-47`'s character interleaving on this console, and the register
	 * values are all in the /proc dump anyway. */
	rlxfw_markx("SW-DIFF", n);
	return 0;
}

static int rtl819x_sw_write_proc(struct file *file, const char __user *ubuf,
				 unsigned long count, void *data)
{
	char buf[48];
	unsigned long n = count;

	if (n >= sizeof(buf))
		return -EINVAL;
	if (copy_from_user(buf, ubuf, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "unlock " RTL819X_SW_UNLOCK_TOKEN)) {
		rtl819x_sw_unlocked = 1;
		rlxfw_mark("SW-UNLOCK");
		return (int)count;
	}
	if (!strcmp(buf, "lock")) {
		rtl819x_sw_unlocked = 0;
		rlxfw_mark("SW-LOCK");
		return (int)count;
	}
	if (!strncmp(buf, "snap ", 5)) {
		unsigned long s = simple_strtoul(buf + 5, NULL, 0);

		if (s >= RTL819X_SW_NSLOT || s == RTL819X_SW_SLOT_BOOT)
			return -EINVAL;	/* slot 0 is the boot latch; it is
					 * not the operator's to overwrite */
		rtl819x_sw_snapshot((int)s);
		rlxfw_markx("SW-SNAP", (unsigned)s);
		return (int)count;
	}
	if (!strncmp(buf, "diff ", 5)) {
		unsigned long a = simple_strtoul(buf + 5, NULL, 0);
		const char *p = strchr(buf + 5, ' ');
		unsigned long b;
		int rc;

		if (!p)
			return -EINVAL;
		b = simple_strtoul(p + 1, NULL, 0);
		if (a >= RTL819X_SW_NSLOT || b >= RTL819X_SW_NSLOT)
			return -EINVAL;
		rc = rtl819x_sw_verb_diff((int)a, (int)b);
		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "reset full") || !strcmp(buf, "reset vendor")) {
		int rc = rtl819x_sw_do_reset(buf[6] == 'v');

		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "start")) {
		u32 v = rtl819x_sw_rd(RTL819X_SW_SSIR);
		int rc = rtl819x_sw_wr(RTL819X_SW_SSIR, v | RTL819X_SW_TRXRDY);

		if (!rc)
			rlxfw_mark("SW-START");
		return rc ? rc : (int)count;
	}
	if (!strcmp(buf, "dumb")) {
		int rc = rtl819x_sw_do_dumb();

		return rc ? rc : (int)count;
	}
	if (!strncmp(buf, "restore ", 8)) {
		unsigned long s = simple_strtoul(buf + 8, NULL, 0);
		int rc;

		if (s >= RTL819X_SW_NSLOT)
			return -EINVAL;
		rc = rtl819x_sw_do_restore((int)s);
		return rc ? rc : (int)count;
	}

	return -EINVAL;
}

/* ------------------------------------------------------------------------
 * Registration.
 *
 * subsys_initcall, for one reason and not by convention: slot 0 must be
 * latched BEFORE the vendor's Ethernet driver configures the switch, and that
 * driver is device_initcall class.  That latch is `S0'` and it is a state
 * nothing in this project has ever measured -- so every boot of this image
 * yields a reading that costs nothing and did not exist before.
 * ------------------------------------------------------------------------ */
static void __init rtl819x_sw_lde_boot(void);	/* 1.2, below */
static int __init rtl819x_sw_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("SW0");

	rtl819x_sw_latched = 1;	/* before the first read, so the accessor
				 * above is live for the rest of boot */
	rtl819x_sw_boot_cvidr = rtl819x_sw_rd(0x4200);
	rlxfw_markx("SW1", rtl819x_sw_boot_cvidr);

	rtl819x_sw_snapshot(RTL819X_SW_SLOT_BOOT);
	rtl819x_sw_lde_boot();	/* 1.2: the other PSRPs, then SW7 = S0' bit-8 mask */
	/* The ones that have never been read on this die, marked individually
	 * so they are in the boot capture of EVERY boot rather than only in a
	 * /proc read somebody remembered to take.
	 *
	 * 🔴 Looked up BY NAME and not by array index.  An index here would be
	 * silently wrong the first time a register is inserted above it, and
	 * the mark would then carry the wrong register's value under the right
	 * register's name -- which is the one failure mode a boot capture
	 * cannot show, because both are just eight hex digits. */
	rlxfw_markx("SW2", rtl819x_sw_boot_of("MSCR"));
	rlxfw_markx("SW3", rtl819x_sw_boot_of("SWTCR1"));
	rlxfw_markx("SW4", rtl819x_sw_boot_of("VCR0"));
	rlxfw_markx("SW5", rtl819x_sw_boot_of("PVCR0"));

	pde = create_proc_entry(RTL819X_SW_PROC_NAME, 0644, NULL);
	if (!pde) {
		rlxfw_mark("SW6-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_sw_read_proc;
	pde->write_proc = rtl819x_sw_write_proc;
	rlxfw_mark("SW6");

	return 0;
}

subsys_initcall(rtl819x_sw_init);

/* ========================================================================
 * 1.2 (R6b-6, 2026-09-26): EVERY PSRP READ THIS DRIVER MAKES KEEPS WHAT IT
 * CONSUMES.
 *
 * Appended rather than threaded through the file, and every line above that
 * changed is one that was blank or is changed in place (the version string,
 * three prototypes, and the three call sites -- `rtl819x_sw_rd`, the /proc
 * page, the init), so no line number above this block moved: 量 at
 * `f758d62`, seventeen committed files cite this driver by line, 23
 * citations, and none of the cited ranges holds a changed line (FW-110).
 *
 * WHY.  `PSRP` bit 8, `LinkDownEventFlag`, is a latch that CLEARS WHEN READ.
 * Two sources: the vendor header, `rtl865xc_asicregs.h:1328`
 * (`LinkDownEventFlag (1<<8)`, "Port Link Down Event detecting monitor
 * flag"), and the datasheet's Table 65 (docs/loader-phy-and-switch.md, the
 * PSRP paragraph); and 量 `SPEC.md` `NET-11`, where one read of a port whose
 * jack was already empty cleared it.  So every reader of `PSRP` destroys the
 * evidence the next reader would need.  1.1 had three such readers -- the
 * slot-0 snapshot, the `/proc` table and `rtl819x_sw_any_link()`, which
 * `rtl819x-nic`'s ethtool `get_link` calls -- and none of them kept the bit.
 * A cable pull followed by `get_link` would therefore leave NO trace in any
 * later read, and R6b-6's positive control would be erased by the call it
 * controls.
 *
 * WHAT 1.2 DOES.  `rtl819x_sw_rd()` -- the one read path -- hands every value
 * to `rtl819x_sw_lde_note()`, which counts a set bit 8 per port and stamps
 * the jiffies of the last one.  `/proc/rtl819x-switch` prints, BEFORE the
 * register table (so the table's last line is still the page's last line, the
 * terminator every card waits for):
 *
 *     n_linkq %lu                          get_link's own counter, never
 *                                          printed by 1.1
 *     lde0 %02X                            S0' mask: bit p set if PSRPp's
 *                                          bit 8 was set at subsys_initcall
 *     psrp%u %08X up %u lde %lu lj %lu     x8: the live word, bit 4, the
 *                                          count, the last one's jiffies
 *     jiffies %lu                          the clock `lj` is read against,
 *                                          printed after the eight reads
 *
 * Each `psrpN` line is read live and printed AFTER that read's accounting, so
 * a latch its own read consumed is already in its `lde`.  The boot adds
 * `RLXFW-SW7=000000XX`, the S0' mask, and reads the PSRPs the census table
 * does not hold (1, 2 and 4 today) so that the mask covers all eight.
 *
 * WHAT `lde` IS, AND IS NOT.
 *   - A count of THIS DRIVER'S reads that saw the latch set.  It is a lower
 *     bound on link-down events: the latch saturates, so two events between
 *     two reads count once.
 *   - Blind to the vendor's reads.  `rtl865x_proc_debug.c`'s `port_status`
 *     printer reads every PSRP twice and never prints bit 8, so a card that
 *     reads `/proc/rtl865x/port_status` between two reads of this file makes
 *     `lde` under-count.  That is why such a card reads this file FIRST.
 *   - Not a statement about PSRP8, which is not read: nothing has ever read
 *     it under Linux, and the datasheet's port table stops at PSRP7.
 *
 * WHAT IT COSTS.  Three reads at subsys_initcall (the PSRPs the table lacks),
 * each of which clears that port's bit 8 before the vendor's probe; the
 * vendor's one consumer of bit 8, `re865x_setPhyGrayCode`, is under
 * CONFIG_RTL8196C_ETH_IOT, which this image does not set, and runs only
 * from its link DSR.  About 20 boot-capture bytes (the SW7 line: `bootbytes`
 * derives it from the source, never by hand).  At most 438 bytes of /proc
 * page: walked from the formats, every field at its widest, the page's worst
 * case goes from 1,642 to 2,080 of 4,096, so the table's budget check above
 * (3,600) is never what ends it.  No write: `n_writes` is untouched.
 *
 * Included here, not with the includes above, so that no line above moves.
 */
#include <linux/jiffies.h>

/* The counters are unlocked, and that is a stated assumption turned into a
 * refusal rather than left as a comment: this .config has SMP off and
 * PREEMPT_NONE, and no reader runs in interrupt context -- `rtl819x_sw_rd`'s
 * callers are the /proc handlers, `rtl819x_sw_any_link` (ethtool, process
 * context under rtnl_lock) and this file's initcall. */
#if defined(CONFIG_SMP) || defined(CONFIG_PREEMPT)
#error "rtl819x-switch 1.2 keeps its PSRP bit-8 counters unlocked; they need a lock before this build can be SMP or preemptible"
#endif

/* PSRP0..PSRP7 at 0xBB804128 + 4p.  Two sources: `rtl865xc_asicregs.h:1143`-
 * `:1150` (`PSRPn (0x028 + 4n + PCRAM_BASE)`), and the reads this project has
 * decoded against the vendor's `port_status` (量 `NET-10`); the LinkUp and
 * bit-8 fields are `NET-11`'s.  PSRP8 is excluded (see above). */
#define RTL819X_SW_NPSRP	8
#define RTL819X_PSRP_LDE	(1u << 8)	/* LinkDownEventFlag, :1328 */
#define RTL819X_SW_PSRP_LAST	(RTL819X_SW_PSRP0 + (RTL819X_SW_NPSRP - 1) * 4)

static unsigned long rtl819x_sw_lde_n[RTL819X_SW_NPSRP];
static unsigned long rtl819x_sw_lde_j[RTL819X_SW_NPSRP];
static u32 rtl819x_sw_lde0;

/* noinline: `rtl819x_sw_rd` is inlined at every call site, and this keeps
 * each of them to one call rather than a copy of the range check. */
static noinline void rtl819x_sw_lde_note(unsigned int off, u32 v)
{
	unsigned int p;

	if (off < RTL819X_SW_PSRP0 || off > RTL819X_SW_PSRP_LAST || (off & 3))
		return;
	if (!(v & RTL819X_PSRP_LDE))
		return;
	p = (off - RTL819X_SW_PSRP0) >> 2;
	rtl819x_sw_lde_n[p]++;
	rtl819x_sw_lde_j[p] = jiffies;
}

/* Is `off` in the census table -- i.e. did the slot-0 snapshot read it?
 * Asked of the table, not typed as "1, 2 and 4", so a register added to or
 * removed from the table cannot leave a port out of the S0' mask. */
static int __init rtl819x_sw_in_table(unsigned int off)
{
	unsigned int i;

	for (i = 0; i < RTL819X_SW_NREG; i++)
		if (rtl819x_sw_regs[i].off == off)
			return 1;
	return 0;
}

static void __init rtl819x_sw_lde_boot(void)
{
	unsigned int p;
	u32 m = 0;

	for (p = 0; p < RTL819X_SW_NPSRP; p++)
		if (!rtl819x_sw_in_table(RTL819X_SW_PSRP0 + p * 4))
			(void)rtl819x_sw_rd(RTL819X_SW_PSRP0 + p * 4);
	for (p = 0; p < RTL819X_SW_NPSRP; p++)
		if (rtl819x_sw_lde_n[p])
			m |= 1u << p;
	rtl819x_sw_lde0 = m;
	rlxfw_markx("SW7", m);
}

/* The lines `read_proc` prints before its register table.  Worst case, every
 * counter at its widest (a 32-bit %lu is 10 digits): 19 + 8 + 8 x 49 + 19 =
 * 438 bytes, against the page budget above. */
static int rtl819x_sw_lde_lines(char *page)
{
	unsigned int p;
	int len = 0;

	len += sprintf(page + len, "n_linkq %lu\n", rtl819x_sw_n_linkq);
	len += sprintf(page + len, "lde0 %02X\n", rtl819x_sw_lde0);
	for (p = 0; p < RTL819X_SW_NPSRP; p++) {
		u32 v = rtl819x_sw_rd(RTL819X_SW_PSRP0 + p * 4);

		len += sprintf(page + len, "psrp%u %08X up %u lde %lu lj %lu\n",
			       p, v, (v & RTL819X_PSRP_LINKUP) ? 1u : 0u,
			       rtl819x_sw_lde_n[p], rtl819x_sw_lde_j[p]);
	}
	len += sprintf(page + len, "jiffies %lu\n", jiffies);
	return len;
}

/* ========================================================================
 * 1.3 (R6b-7): AN mii_bus FOR THE FIVE EMBEDDED PHYs, AND THE ONE PATH THIS
 * DRIVER ISSUES MDIO COMMANDS THROUGH.
 *
 * Appended, as 1.2 was.  Above this block only the version string and the
 * comment over `rtl819x_sw_wr` changed, each in place, so no line above
 * moves (FW-110).
 *
 * THE REGISTER CONTRACT.  MDCIOCR 0xBB804004: bit 31 COMMAND (1 = write),
 * 28:24 PHYADD, 20:16 REGADD, 15:0 WRDATA.  MDCIOSR 0xBB804008: bit 31 STATUS
 * (1 = in progress), 15:0 RDATA.  讀 x3: the datasheet's Tables 58-59,
 * `rtl865xc_asicregs.h:1046-1062`, and the loader's primitives at 0x80402F80
 * and 0x80402FF8 (SPEC.md NET-15).  One store of the whole word issues the
 * command; STATUS clear is completion.  MDCIOSR 30:16: the datasheet says
 * Reserved and the header names bit 30 `MDCIOSR_ReadError` (:1267) -- two
 * sources that disagree, so 未定: this block records those bits (`hi`) and
 * never decides on them.
 *
 * NO 10 ms DELAY.  The tree that builds delays only on 8198 and 8196C
 * revision A (`rtl865x_asicL2.c:5558-5564`, whose erratum is "mdio data read
 * will delay 1 mdc clock"); the loader delays 10 ms before every poll,
 * unconditionally (0x80402FC0).  量: on PHY 0 the vendor's UNDELAYED /proc
 * path read registers 2, 3, 0 and 1 as 001C, C880, 1100 and 78C9
 * (bench/2026-09-19 C19-PHYID, C20-PHYST) -- the values the loader's DELAYED
 * read returned for the same registers (F2, E6, X8, E12d).  A shifted or
 * late-latched RDATA would have made the two paths disagree.  That is four
 * values on PHY 0 only; `scan` against the loader's MDIOR rows re-tests it
 * on 0-4.
 *
 * WHO ELSE ISSUES MDIO COMMANDS IN THIS IMAGE, AND WHY IRQs GO OFF.  讀, a
 * call census of r6b6q's vmlinux: 25 read and 43 write call sites in 20
 * vendor functions, all through the vendor's two accessors.  All run in
 * process context -- the probe, the /proc writers, re865x_close -- except
 * `one_sec_timer`, a kernel timer that re865x_open arms for eth0 only and
 * that runs `refine_phy_setting()` once a second (`rtl_nic.c:3813-3841`):
 * page-0 writes to registers 25, 26, 17 and 21 of PHYs 0-4, under
 * local_irq_save.  None of them takes a lock this driver could share.  On
 * this .config (UP, PREEMPT_NONE, refused otherwise by 1.2's #error) another
 * MDIO user can run between our store of MDCIOCR and our read of MDCIOSR
 * only from interrupt context, so every transaction runs with IRQs off; and
 * `pread` runs its page select, its read and its page restore inside ONE
 * IRQs-off section, because a timer tick between them would land
 * refine_phy_setting's page-0 writes on the selected page.
 *
 * WHAT IRQs OFF COSTS, AT WORST.  A transaction polls STATUS at most
 * RTL819X_MDIO_BOUND + 1 times before its store and as many after it, with
 * udelay(1) between polls: <= 2 x 10 ms of delay, nominal.  `pread` holds
 * IRQs off across at most seven transactions (six, and one retried restore
 * whose first attempt never stored, so has no poll after it): <= 13 x 10 ms
 * = 130 ms, nominal, plus the reads.  推 a transaction that completes takes
 * tens of us (`spin` measures it); the worst case is the failure the bound
 * exists for.  At HZ 100 it would cost ~13 ticks, and at 38400 baud the
 * UART's FIFO overruns after ~4 ms of host input, so a card does not type
 * while a pread may be timing out.
 *
 * WHAT IS GATED.  Every MDCIOCR store -- a read is a store too (NET-16) --
 * needs `unlock mdio-i-mean-it` on /proc/rtl819x-mdio: a gate of its own,
 * because /init writes the switch's unlock on every boot
 * (config/rlxfw-init.sh).  So a boot issues no MDIO command, `mdio_rd` and
 * `mdio_wr` read 0 until a card unlocks, and this file's header item 2 stays
 * true.  `probe` and `pread` also refuse (-EAGAIN, counted in `again`, the
 * one-shot probe not spent) unless `bound` is RTL819X_MDIO_BOUND: `bound`
 * exists to make `scan` time out on purpose, and at a small bound a probe
 * would spend its one shot on phylib's -EIO and a pread's restore could be
 * refused, leaving the PHY on page 1.
 *
 * THE ONLY PHY WRITES: REGISTER 31, THE PAGE SELECT, VALUES 1 AND 0.  讀 x2,
 * code only -- the loader's PORT1 (0x8040A0A0, docs/loader-phy-and-switch.md
 * section 4) and the tree that builds (`Set_GPHYWB`, rtl865x_asicL2.c:1230-
 * 1266) both select a page by writing it to register 31 and restore by
 * writing 0; the datasheet has no PHY register map.  C-18 needs page 1 alone,
 * and 7 is the vendor's gateway to register 30's extension pages
 * (`Set_GPHYWB`'s page >= 31 arm), so `pread` takes page 0 (no select: the
 * control) or 1 and nothing else.  What register 31 reads back is 未定 -- no
 * source reads it -- so `p0`, `ps` and `p1` are recorded, and the page-0
 * control is what says whether the select changed what is read.  The
 * restore is made whatever happened before it; if its store is refused
 * because a command is still in flight (-EBUSY), it waits out one more full
 * bound and stores again.  Left: hardware busy past both bounds (~20 ms),
 * or a register 31 that reads 0 whatever it holds -- `dirty` and `rs` say
 * which was seen.  The bus's own write op refuses always (`wr_refused`), so
 * a phylib write would be counted rather than done.
 *
 * WHY phy_mask IS ~0 AT REGISTRATION.  phylib calls an address empty only
 * when `(id & 0x1fffffff) == 0x1fffffff` (phy_device.c:231).  Register 2
 * reads 0x0000 at 5-31 (量 SPEC.md NET-24), so their IDs cannot be all-ones
 * in bits 28:0 whatever register 3 holds, and an unmasked scan would
 * register 27 phantom phy_devices.  The bus registers with every address
 * masked -- registration issues no MDIO command -- and `probe` scans 0-4 one
 * by one through `mdiobus_scan`, phylib's own path.  phylib turns every
 * failed read into -EIO (get_phy_id), so each of 0-4 also keeps the rc of the
 * last transaction the bus's read op issued to it (`xrc`).  5-31 are only
 * ever READ (`scan`).  On a loud image (PRINTK=y) a probe prints
 * `rtl819x-mdio: probed` (mdio_bus.c:129); the quiet image prints nothing.
 *
 * WHY NOTHING IS ATTACHED.  rlx0 is the CPU port and has no PHY (NET-39).
 * Nothing in rlxfw calls phy_connect or phy_attach; genphy matches only ID
 * FFFFFFFF and config/rlxfw-kernel.delta pins every other phy_driver off, so
 * the five devices stay unbound, and `drv` and `att` print that per address.
 * `pread` takes bus->mdio_lock, the lock phylib's own reads take, before
 * IRQs go off.
 *
 * THE PAGE.  /proc/rtl819x-mdio prints cached results only: a `cat` issues
 * no MDIO command (`mdio_rd` does not move across one), which matters
 * because one `cat` renders twice (FW-64).  The rows print last, under a
 * budget, and `jiffies` is the last line.
 */
#include <linux/err.h>
#include <linux/mutex.h>
#include <linux/phy.h>

#ifndef CONFIG_PHYLIB
#error "rtl819x-switch 1.3 registers an mii_bus: CONFIG_PHYLIB, and CONFIG_NET_ETHERNET which it depends on, must be y (config/rlxfw-kernel.delta)"
#endif

#define RTL819X_SW_MDCIOCR	0x4004
#define RTL819X_SW_MDCIOSR	0x4008
#define RTL819X_MDIO_WRITE	(1u << 31)		/* MDCIOCR COMMAND */
#define RTL819X_MDIO_PHYADD(a)	(((u32)(a) & 0x1Fu) << 24)
#define RTL819X_MDIO_REGADD(r)	(((u32)(r) & 0x1Fu) << 16)
#define RTL819X_MDIO_STATUS	(1u << 31)		/* MDCIOSR, 1 = in progress */
#define RTL819X_MDIO_RDATA	0xFFFFu
#define RTL819X_MDIO_HIBITS	0x7FFF0000u		/* 30:16, 未定: recorded only */
#define RTL819X_MDIO_NPHY	5			/* MDIO 0-4 (NET-39) */
#define RTL819X_MDIO_NADDR	32
#define RTL819X_MDIO_NROW	6			/* registers 0-5 per scan row */
#define RTL819X_MDIO_NPR	8			/* pread results kept */
#define RTL819X_MDIO_PAGEREG	31
#define RTL819X_MDIO_PAGE	1			/* the one page pread selects */
#define RTL819X_MDIO_BOUND	10000u	/* polls of (read + udelay(1)): >= 10 ms */
#define RTL819X_MDIO_NOXFER	1			/* xrc/rs: none issued */
#define RTL819X_MDIO_PROC	"rtl819x-mdio"
#define RTL819X_MDIO_TOKEN	"mdio-i-mean-it"

struct rtl819x_mdio_row {
	int		v[RTL819X_MDIO_NROW];	/* >= 0 a reading, < 0 an errno */
	u32		hi;	/* OR of MDCIOSR 30:16 over the row's reads */
	u32		psrp;	/* PSRPa read after the row, a < 5 */
	unsigned int	n;	/* times scanned; 0 = never, and not printed */
};

struct rtl819x_mdio_pr {
	u8	a, page, reg;
	u8	rt;		/* 1: the restore's store was retried */
	int	p0;		/* register 31 before: must read 0 */
	int	ps;		/* register 31 after the select: page, if it reads back */
	int	v;		/* the reading */
	int	rs;		/* the restore's store: 0, or its errno */
	int	p1;		/* register 31 after the restore: must read 0 */
	int	rc;
	u32	psrp0, psrp1;	/* PSRPa either side of the section */
};

static struct mii_bus *rtl819x_mdio_bus;
static int rtl819x_mdio_reg_rc = 1;	/* 1: `probe` never ran */
static int rtl819x_mdio_scan_rc[RTL819X_MDIO_NPHY] = {	/* 1: not scanned */
	RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER,
	RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER
};
static int rtl819x_mdio_xrc[RTL819X_MDIO_NPHY] = {
	RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER,
	RTL819X_MDIO_NOXFER, RTL819X_MDIO_NOXFER
};
static int rtl819x_mdio_unlocked;
static int rtl819x_mdio_dirty;		/* a+1 of a PHY whose restore did not verify */
static unsigned int rtl819x_mdio_bound = RTL819X_MDIO_BOUND;
static unsigned long rtl819x_mdio_n_rd, rtl819x_mdio_n_wr;
static unsigned long rtl819x_mdio_n_to, rtl819x_mdio_n_busy;
static unsigned long rtl819x_mdio_n_retry;	/* restores stored a second time */
static unsigned long rtl819x_mdio_n_refused, rtl819x_mdio_n_wr_refused;
static unsigned long rtl819x_mdio_n_again;	/* probe/pread refused at a small bound */
static unsigned long rtl819x_mdio_n_spin;	/* completed polls */
static unsigned int rtl819x_mdio_spin_min, rtl819x_mdio_spin_max;
static u32 rtl819x_mdio_hi_or, rtl819x_mdio_last_hi;
static struct rtl819x_mdio_row rtl819x_mdio_rows[RTL819X_MDIO_NADDR];
static u32 rtl819x_mdio_scanned;
static unsigned long rtl819x_mdio_scan_j;
static struct rtl819x_mdio_pr rtl819x_mdio_prs[RTL819X_MDIO_NPR];
static unsigned int rtl819x_mdio_npr;

/* One MDIO transaction.  THE ONLY PLACE MDCIOCR IS STORED.  The caller holds
 * IRQs off.  Returns the 16-bit reading, 0 for a completed write, -EBUSY
 * (STATUS still set before the store, which is then NOT made: a command
 * already in flight) or -ETIMEDOUT (STATUS still set after the store; 145 on
 * this arch, arch/rlx/include/asm/errno.h:98) at the bound -- the loader's
 * own wait has no bound at all (SPEC.md NET-17). */
static int rtl819x_mdio_xfer(int write, int a, int r, u16 val)
{
	unsigned int n;
	u32 st;

	rtl819x_mdio_last_hi = 0;
	for (n = 0; __raw_readl(rtl819x_sw_reg(RTL819X_SW_MDCIOSR)) &
		    RTL819X_MDIO_STATUS; n++) {
		if (n >= rtl819x_mdio_bound) {
			rtl819x_mdio_n_busy++;
			return -EBUSY;
		}
		udelay(1);
	}
	__raw_writel((write ? RTL819X_MDIO_WRITE | val : 0) |
		     RTL819X_MDIO_PHYADD(a) | RTL819X_MDIO_REGADD(r),
		     rtl819x_sw_reg(RTL819X_SW_MDCIOCR));
	if (write)
		rtl819x_mdio_n_wr++;
	else
		rtl819x_mdio_n_rd++;
	for (n = 0; ; n++) {
		st = __raw_readl(rtl819x_sw_reg(RTL819X_SW_MDCIOSR));
		if (!(st & RTL819X_MDIO_STATUS))
			break;
		if (n >= rtl819x_mdio_bound) {
			rtl819x_mdio_n_to++;
			return -ETIMEDOUT;
		}
		udelay(1);
	}
	if (!rtl819x_mdio_n_spin++ || n < rtl819x_mdio_spin_min)
		rtl819x_mdio_spin_min = n;
	if (n > rtl819x_mdio_spin_max)
		rtl819x_mdio_spin_max = n;
	rtl819x_mdio_last_hi = st & RTL819X_MDIO_HIBITS;
	rtl819x_mdio_hi_or |= rtl819x_mdio_last_hi;
	return write ? 0 : (int)(st & RTL819X_MDIO_RDATA);
}

/* The bus's read op: every phylib read of this bus comes through here, and
 * for 0-4 it keeps what the transaction itself returned, because phylib
 * reports every failure as -EIO. */
static int rtl819x_mdio_read(struct mii_bus *bus, int a, int r)
{
	unsigned long flags;
	int v;

	if (!rtl819x_mdio_unlocked) {
		rtl819x_mdio_n_refused++;
		v = -EPERM;
	} else {
		local_irq_save(flags);
		v = rtl819x_mdio_xfer(0, a, r, 0);
		local_irq_restore(flags);
	}
	if (a >= 0 && a < RTL819X_MDIO_NPHY)
		rtl819x_mdio_xrc[a] = v < 0 ? v : 0;
	return v;
}

/* The bus's write op refuses, always.  Nothing in rlxfw writes a PHY through
 * the bus; phylib would only through a bound phy_driver or an attached
 * netdev, and neither may exist here.  A non-zero `wr_refused` says one
 * tried. */
static int rtl819x_mdio_write(struct mii_bus *bus, int a, int r, u16 val)
{
	rtl819x_mdio_n_wr_refused++;
	return -EPERM;
}

/* `probe`: register the bus with every address masked, then let phylib scan
 * 0-4.  One-shot, even after a failure: a second mdiobus_scan of an address
 * registers a second device under the same name, which device_register
 * refuses, and mdio_bus.c:218 then overwrites phy_map with NULL.  Refused
 * without spending the shot while `bound` is not RTL819X_MDIO_BOUND. */
static int rtl819x_mdio_probe(void)
{
	struct mii_bus *bus;
	struct phy_device *pd;
	unsigned int a, m = 0;
	int rc;

	if (rtl819x_mdio_reg_rc != 1)
		return -EEXIST;
	if (rtl819x_mdio_bound != RTL819X_MDIO_BOUND) {
		rtl819x_mdio_n_again++;
		return -EAGAIN;
	}
	bus = mdiobus_alloc();
	if (!bus) {
		rtl819x_mdio_reg_rc = -ENOMEM;
		return -ENOMEM;
	}
	bus->name = RTL819X_MDIO_PROC;
	snprintf(bus->id, MII_BUS_ID_SIZE, "rlxsw");
	bus->read = rtl819x_mdio_read;
	bus->write = rtl819x_mdio_write;
	bus->phy_mask = ~0u;	/* register() scans nothing, issues nothing */
	rc = mdiobus_register(bus);
	rtl819x_mdio_reg_rc = rc;
	if (rc) {
		mdiobus_free(bus);
		rlxfw_markx("MD1-REG", (unsigned)-rc);
		return rc;
	}
	rtl819x_mdio_bus = bus;
	for (a = 0; a < RTL819X_MDIO_NPHY; a++) {
		pd = mdiobus_scan(bus, a);
		rtl819x_mdio_scan_rc[a] = IS_ERR(pd) ? (int)PTR_ERR(pd) :
					  (pd ? 0 : -ENODEV);
		if (bus->phy_map[a])
			m |= 1u << a;
	}
	rlxfw_markx("MD1", m);
	return 0;
}

/* `scan lo hi`: registers 0-5 of every address in [lo, hi] through
 * mdiobus_read, and PSRPa after each row for a < 5 through the one switch
 * read path, so a PSRP bit 8 consumed here is counted (1.2).  Reading
 * register 1 clears the PHY's latched-low link bit (推, IEEE 802.3
 * 22.2.4.2.13): a card that wants a link-down latch reads it before a scan.
 * The bound's positive control: at `bound 0` a read whose STATUS is still
 * set when first polled prints E145, and the next one may print E016. */
static int rtl819x_mdio_scan(unsigned int lo, unsigned int hi)
{
	struct rtl819x_mdio_row *w;
	unsigned int a, r;

	for (a = lo; a <= hi; a++) {
		w = &rtl819x_mdio_rows[a];
		w->hi = 0;
		for (r = 0; r < RTL819X_MDIO_NROW; r++) {
			w->v[r] = mdiobus_read(rtl819x_mdio_bus, a, r);
			w->hi |= rtl819x_mdio_last_hi;
		}
		w->psrp = a < RTL819X_MDIO_NPHY ?
			  rtl819x_sw_rd(RTL819X_SW_PSRP0 + a * 4) : 0;
		w->n++;
		rtl819x_mdio_scanned |= 1u << a;
	}
	rtl819x_mdio_scan_j = jiffies;
	rlxfw_markx("MD2", (hi << 8) | lo);
	return 0;
}

/* `pread a page reg`: one register of PHY a on page 1, for C-18's page-1
 * reads; page 0 reads the same register number unpaged, the control that the
 * select changed what is read (讀: the vendor's 8196E init leaves page-1
 * register 16 bits 15:13 at 110 on PHYs 0-4, Setting_RTL8196E_PHY,
 * rtl865x_asicL2.c:4177).  At page 1, in ONE IRQs-off section: read register
 * 31 (must be 0, or nothing is written), select the page, read register 31
 * back, read the register, restore page 0 (retried once if refused busy),
 * read register 31 back (must be 0, and the restore must have been stored,
 * or every later pread is refused: the PHY may be left on a page the
 * vendor's page-0 writes would then land on).  PSRPa is read either side
 * through the one switch read path.  The vendor's Setting_RTL8196E_PHY and
 * enable_EEE set EnForceMode on PCRP0-4 around their paged writes and its
 * /proc `extRead` does not; this does not, so the switch's own PHY polling
 * may meet a selected page (推), and PSRP bit 8 either side is the only
 * detector here -- valid only while no vendor eth is open, whose link DSR
 * reads PSRP too. */
static int rtl819x_mdio_pread(unsigned int a, unsigned int page,
			      unsigned int reg)
{
	struct rtl819x_mdio_pr *p;
	unsigned long flags;
	int rc;

	if (rtl819x_mdio_bound != RTL819X_MDIO_BOUND) {
		rtl819x_mdio_n_again++;
		return -EAGAIN;
	}
	if (rtl819x_mdio_dirty)
		return -EIO;
	p = &rtl819x_mdio_prs[rtl819x_mdio_npr++ % RTL819X_MDIO_NPR];
	memset(p, 0, sizeof(*p));
	p->a = a;
	p->page = page;
	p->reg = reg;
	p->rs = RTL819X_MDIO_NOXFER;
	p->psrp0 = rtl819x_sw_rd(RTL819X_SW_PSRP0 + a * 4);

	mutex_lock(&rtl819x_mdio_bus->mdio_lock);
	local_irq_save(flags);
	if (!page) {		/* the same register unpaged: the control */
		p->v = rtl819x_mdio_xfer(0, a, reg, 0);
		rc = p->v < 0 ? p->v : 0;
		goto out;
	}
	p->p0 = rtl819x_mdio_xfer(0, a, RTL819X_MDIO_PAGEREG, 0);
	if (p->p0 != 0) {	/* not on page 0, or unreadable: write nothing */
		rc = p->p0 < 0 ? p->p0 : -EPROTO;
		goto out;
	}
	rc = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, (u16)page);
	p->ps = rc ? rc : rtl819x_mdio_xfer(0, a, RTL819X_MDIO_PAGEREG, 0);
	p->v = rc ? rc : rtl819x_mdio_xfer(0, a, reg, 0);
	p->rs = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);  /* always */
	if (p->rs == -EBUSY) {	/* never stored: one more full bound */
		p->rt = 1;
		rtl819x_mdio_n_retry++;
		p->rs = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);
	}
	p->p1 = rtl819x_mdio_xfer(0, a, RTL819X_MDIO_PAGEREG, 0);
	if (p->rs == -EBUSY || p->p1 != 0) {
		rtl819x_mdio_dirty = (int)a + 1;
		rc = -EIO;
	} else {
		rc = p->v < 0 ? p->v : p->ps != (int)page ? -EPROTO : 0;
	}
out:
	local_irq_restore(flags);
	mutex_unlock(&rtl819x_mdio_bus->mdio_lock);

	p->psrp1 = rtl819x_sw_rd(RTL819X_SW_PSRP0 + a * 4);
	p->rc = rc;
	rlxfw_markx("MD3", (a << 16) | (page << 8) | reg);
	return rc;
}

/* Rows print last, each only while len is under the budget, so the page
 * ends inside one 4,096-byte page whatever the counters hold.  Walked from
 * the formats with every field at its type's widest (32-bit longs, as here;
 * a row's values are the read op's, 0-FFFF or E001/E016/E145): everything
 * before the rows is <= 1,735 B, a row <= 69 B and the trailer <= 19 B, so
 * the page is <= 3,962 B and the budget is a guard that cannot fire at these
 * widths (tools/mdiocheck.py K16 measures all four). */
#define RTL819X_MDIO_PAGE_BUDGET	3900
static int rtl819x_mdio_read_proc(char *page, char **start, off_t off,
				  int count, int *eof, void *data)
{
	struct phy_device *pd;
	const struct rtl819x_mdio_row *w;
	const struct rtl819x_mdio_pr *p;
	unsigned int a, r, i, n;
	int len = 0;

	len += sprintf(page + len, "version %s\n", RTL819X_SW_VERSION);
	len += sprintf(page + len, "unlocked %d\n", rtl819x_mdio_unlocked);
	len += sprintf(page + len, "bus %d reg_rc %d\n",
		       rtl819x_mdio_bus != NULL, rtl819x_mdio_reg_rc);
	len += sprintf(page + len, "bound %u\n", rtl819x_mdio_bound);
	len += sprintf(page + len, "mdio_rd %lu\n", rtl819x_mdio_n_rd);
	len += sprintf(page + len, "mdio_wr %lu\n", rtl819x_mdio_n_wr);
	len += sprintf(page + len, "mdio_to %lu busy %lu retry %lu\n",
		       rtl819x_mdio_n_to, rtl819x_mdio_n_busy,
		       rtl819x_mdio_n_retry);
	len += sprintf(page + len, "refused %lu wr_refused %lu again %lu\n",
		       rtl819x_mdio_n_refused, rtl819x_mdio_n_wr_refused,
		       rtl819x_mdio_n_again);
	len += sprintf(page + len, "spin %lu %u %u\n", rtl819x_mdio_n_spin,
		       rtl819x_mdio_spin_min, rtl819x_mdio_spin_max);
	len += sprintf(page + len, "hi_or %08X\n", rtl819x_mdio_hi_or);
	len += sprintf(page + len, "dirty %d\n", rtl819x_mdio_dirty);
	len += sprintf(page + len, "scanned %08X j %lu\n",
		       rtl819x_mdio_scanned, rtl819x_mdio_scan_j);

	for (a = 0; a < RTL819X_MDIO_NPHY; a++) {
		pd = rtl819x_mdio_bus ? rtl819x_mdio_bus->phy_map[a] : NULL;
		if (pd)
			len += sprintf(page + len,
				       "phy%u id %08X rc %d xrc %d drv %d att %d\n",
				       a, pd->phy_id, rtl819x_mdio_scan_rc[a],
				       rtl819x_mdio_xrc[a],
				       pd->dev.driver != NULL,
				       pd->attached_dev != NULL);
		else
			len += sprintf(page + len, "phy%u id - rc %d xrc %d\n",
				       a, rtl819x_mdio_scan_rc[a],
				       rtl819x_mdio_xrc[a]);
	}

	n = rtl819x_mdio_npr < RTL819X_MDIO_NPR ? rtl819x_mdio_npr :
						 RTL819X_MDIO_NPR;
	for (i = 0; i < n; i++) {
		p = &rtl819x_mdio_prs[(rtl819x_mdio_npr - n + i) %
				      RTL819X_MDIO_NPR];
		len += sprintf(page + len,
			       "pr a%u p%u r%02u v %d p0 %d ps %d p1 %d rs %d rt %u rc %d psrp %08X %08X\n",
			       p->a, p->page, p->reg, p->v, p->p0, p->ps,
			       p->p1, p->rs, p->rt, p->rc, p->psrp0, p->psrp1);
	}

	for (a = 0; a < RTL819X_MDIO_NADDR &&
		    len < RTL819X_MDIO_PAGE_BUDGET; a++) {
		w = &rtl819x_mdio_rows[a];
		if (!w->n)
			continue;
		len += sprintf(page + len, "a%02u", a);
		for (r = 0; r < RTL819X_MDIO_NROW; r++)
			len += w->v[r] < 0 ?
			       sprintf(page + len, " E%03d", -w->v[r]) :
			       sprintf(page + len, " %04X", w->v[r]);
		len += sprintf(page + len, " hi %04X psrp %08X n %u\n",
			       w->hi >> 16, w->psrp, w->n);
	}

	len += sprintf(page + len, "jiffies %lu\n", jiffies);	/* terminator */
	*eof = 1;
	return len;
}

/* Exactly n space-separated numbers, each starting with a digit, the last one
 * ending the string.  simple_strtoul skips nothing and reads a field that does
 * not start with a digit as 0 (lib/vsprintf.c), so without this a doubled
 * space would turn `pread 0  1` into a read of register 1 on page 0, and
 * trailing letters would be ignored rather than refused. */
static int rtl819x_mdio_nums(const char *s, unsigned long *v, int n)
{
	char *e;
	int i;

	for (i = 0; i < n; i++) {
		if (*s < '0' || *s > '9')
			return -EINVAL;
		v[i] = simple_strtoul(s, &e, 0);
		if (*e != (i + 1 < n ? ' ' : '\0'))
			return -EINVAL;
		s = e + 1;
	}
	return 0;
}

static int rtl819x_mdio_write_proc(struct file *file, const char __user *ubuf,
				   unsigned long count, void *data)
{
	char buf[48];
	unsigned long n = count, v[3];
	int rc;

	if (n >= sizeof(buf))
		return -EINVAL;
	if (copy_from_user(buf, ubuf, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "unlock " RTL819X_MDIO_TOKEN)) {
		rtl819x_mdio_unlocked = 1;
		rlxfw_mark("MD-UNLOCK");
		return (int)count;
	}
	if (!strcmp(buf, "lock")) {
		rtl819x_mdio_unlocked = 0;
		rlxfw_mark("MD-LOCK");
		return (int)count;
	}
	if (!strncmp(buf, "bound ", 6)) {	/* the timeout's positive control */
		if (rtl819x_mdio_nums(buf + 6, v, 1) || v[0] > RTL819X_MDIO_BOUND)
			return -EINVAL;
		rtl819x_mdio_bound = (unsigned int)v[0];
		return (int)count;
	}

	/* Everything below issues MDIO commands. */
	if (!rtl819x_mdio_unlocked) {
		rtl819x_mdio_n_refused++;
		return -EPERM;
	}
	if (!strcmp(buf, "probe")) {
		rc = rtl819x_mdio_probe();
		return rc ? rc : (int)count;
	}
	if (!rtl819x_mdio_bus)
		return -ENODEV;
	if (!strncmp(buf, "scan ", 5)) {
		if (rtl819x_mdio_nums(buf + 5, v, 2) || v[0] > v[1] ||
		    v[1] >= RTL819X_MDIO_NADDR)
			return -EINVAL;
		rc = rtl819x_mdio_scan((unsigned int)v[0], (unsigned int)v[1]);
		return rc ? rc : (int)count;
	}
	if (!strncmp(buf, "pread ", 6)) {
		/* PHYs 0-4 only; page 0 (no select: the control) or page 1
		 * (register 31 <- 1, then <- 0); never register 31 itself. */
		if (rtl819x_mdio_nums(buf + 6, v, 3) ||
		    v[0] >= RTL819X_MDIO_NPHY || v[1] > RTL819X_MDIO_PAGE ||
		    v[2] >= RTL819X_MDIO_PAGEREG)
			return -EINVAL;
		rc = rtl819x_mdio_pread((unsigned int)v[0], (unsigned int)v[1],
					(unsigned int)v[2]);
		return rc ? rc : (int)count;
	}
	return -EINVAL;
}

/* The /proc entry only: no MDIO command and no phylib call at boot, so the
 * boot capture does not change (and nothing prints unless this fails). */
static int __init rtl819x_mdio_init(void)
{
	struct proc_dir_entry *pde;

	pde = create_proc_entry(RTL819X_MDIO_PROC, 0644, NULL);
	if (!pde) {
		rlxfw_mark("MD0-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_mdio_read_proc;
	pde->write_proc = rtl819x_mdio_write_proc;
	return 0;
}

device_initcall(rtl819x_mdio_init);
