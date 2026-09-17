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

#define RTL819X_SW_VERSION	"rtl819x-switch 1.0"

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

static inline void __iomem *rtl819x_sw_reg(unsigned int off)
{
	return (void __iomem *)KSEG1ADDR(RTL819X_SW_PHYS + off);
}

static inline u32 rtl819x_sw_rd(unsigned int off)
{
	u32 v = __raw_readl(rtl819x_sw_reg(off));

	rtl819x_sw_n_reads++;
	return v;
}

/* THE ONLY WRITE PATH.  Everything that writes goes through here, so
 * `n_writes` is a count of writes and not a count of callers who remembered
 * to increment it, and the guard is ordered BEFORE the store rather than
 * logged after it. */
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

static int __init rtl819x_sw_init(void)
{
	struct proc_dir_entry *pde;

	rlxfw_mark("SW0");

	rtl819x_sw_boot_cvidr = rtl819x_sw_rd(0x4200);
	rlxfw_markx("SW1", rtl819x_sw_boot_cvidr);

	rtl819x_sw_snapshot(RTL819X_SW_SLOT_BOOT);

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
