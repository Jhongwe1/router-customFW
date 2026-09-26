/*
 * rtl819x-view.c -- a read-only view of the RTL8196E's switch registers, its
 * MIB counters, its CPU interface, PIN_MUX, and two of its tables.
 *
 * R6b-8 8c.  One node, /proc/rtl819x-view, and three verbs written to it:
 *
 *     mib              the 225 MIB words of ports 0-6, one load each
 *     tbl vlan|netif   the VLAN table's 16 slots or the netif table's 8, read
 *                      the way the vendor's own reader reads them
 *     peek A [n]       n words (1-16, default 1) from the KSEG1 address A
 *
 * A `cat` prints the cached result of the last verb that loaded anything, and
 * loads nothing itself -- which matters because one `cat` renders the page
 * twice (FW-64).
 *
 * ======================================================================
 * WHY A FILE OF ITS OWN
 * ======================================================================
 *
 * Not a 1.4 of rtl819x-switch.c.  Seating 43's third press pins HEAD's
 * rtl819x-switch.c and tools/mdiocheck.py by sha, and mdiocheck cuts that
 * driver from its 1.3 banner to the END OF THE FILE, so a block appended
 * there would enter mdiocheck's harness and fail it.  This file shares no
 * code and no symbol with it: rtl819x-switch keeps its own read path, its
 * PSRP bookkeeping and its MDIO gate, and nothing here calls them.
 *
 * ======================================================================
 * WHAT MAY BE LOADED: THE ADMISSION TABLE
 * ======================================================================
 *
 * A word is loaded only if it lies inside one of four named blocks AND two of
 * three sources place it: B, the header the build compiles
 * (drivers/net/rtl819x/AsicDriver/rtl865xc_asicregs.h, sha256 e29c3051...);
 * D, the draft datasheet; and 量, a reading this repository already holds.
 * That is CLAUDE.md's rule for a register value entering code, applied to an
 * address entering a read path.  298 words pass, and they are the table
 * below, word for word -- every run carries its sources.  One-source words
 * (QNUMCR, CSCR, EEECR, IBCR0-2, WFQRCRPn and the rest) are NOT admitted:
 * 8c-cells reads the ones it needs through the vendor's /proc/rtl865x/memory
 * and the loader's DW, and 8d admits each once that second reading exists.
 *
 * Everything else is refused BEFORE ANY LOAD, the whole request with it:
 * `peek A n` checks all n words first, and loads none unless all n pass.
 * Flash (0xBD000000-0xBD3FFFFF, 0xBFC00000 up) is in no block, so H601
 * (flash 0x6000-0x7FFF) cannot reach a capture through this node.  The
 * admission is by exact KSEG1 address: the KSEG0 alias of an admitted
 * register (0x9B80xxxx) and its physical address are refused like any other.
 *
 * PSRP0-PSRP8 (0xBB804128-0xBB804148) are refused with a reason of their
 * own, `psrp`: bit 8, LinkDownEventFlag, clears when read (B :1328, D Table
 * 65, 量 NET-11), and /proc/rtl819x-switch 1.2 already reads them and keeps
 * what it consumes.  A read here would consume it where nothing keeps it.
 *
 * ======================================================================
 * WHAT THIS DRIVER DOES NOT DO
 * ======================================================================
 *
 * 1. It STORES TO NO REGISTER, ever: there is no store accessor in this file,
 *    and so no unlock.  NET-109's ByPassTCRC cell, which needs a write, goes
 *    through the vendor's /proc/rtl865x/memory (decision D4).
 * 2. It loads nothing at boot.  The initcall creates the node and prints
 *    nothing unless that fails (RLXFW-VW0-NOPROC).
 * 3. It issues no table command.  `tbl` never writes SWTACR, SWTAA, a TCR
 *    or EN_STOP_TLU, so the table engine runs nothing and no table can
 *    change because of it; see the table read below.
 * 4. It issues no MDIO command.  MDIO stays rtl819x-switch 1.3's.
 * 5. It says nothing about read side effects beyond the ones named here:
 *    none is known for the 298 (推), and which of them were read on this die
 *    before is in the sources column.  The MIB's read-to-clear is 未定.
 *
 * ======================================================================
 * THE TABLE READ
 * ======================================================================
 *
 * 讀 `_rtl8651_readAsicEntry`, drivers/net/rtl819x/AsicDriver/96E/
 * rtl865x_asicBasic.S:1043-1215, the reader the vendor's VLAN and netif
 * getters call.  Per slot: load SWTACR (0xBB804D00) until bit 0,
 * ACTION_START (B :209-:211), reads clear -- the vendor's wait is unbounded;
 * this one gives up after RTL819X_VIEW_BOUND polls with udelay(1) between
 * them, 1.3's MDIO bound, and returns -EBUSY with the slot named and no
 * table load after it.  Then, up to ten times (`li $16,10`): the slot's
 * eight words at 0xBB000000 + (type << 16) + (slot << 5) into a first buffer,
 * the same eight into a second, compared word by word.  Equal ends the
 * tries; after ten unequal ones the vendor copies the SECOND buffer out and
 * returns success.  This prints that second buffer, the number of tries, and
 * `eq` or `mis`.  The StopTLU variant (:1216 on) sets EN_STOP_TLU in SWTCR0
 * and has no C caller in the tree (讀, grep); it is not what this copies.
 * Base 0xBB000000 is REAL_SWTBL_BASE (B :151), the type numbers are the
 * enum in rtl865x_asicBasic.h (VLAN 6, netif 4), the slot counts are
 * rtl865x_asicCom.h's (16 VLAN slots under CONFIG_RTL_8196E, 8 netifs), and
 * the 32-byte stride is the `sll $2,$18,5` of the reader; 量 SWTAA reads
 * BB060100 at the loader and BB040020 under Linux (NET-28), both inside
 * these windows on slot boundaries.  D has no table section.
 *
 * ⚠️ `rtl8651_getAsicVlan` reads index = vid (rtl865x_asicCom.c:146) while
 * the vendor's writer searches for a free slot, so a slot number here is NOT
 * a VID; the decoder never takes one for the other.
 *
 * ======================================================================
 * THE MIB
 * ======================================================================
 *
 * The 32 words per port that the vendor's `rtl865xC_dumpAsicDiagCounter`
 * (rtl865x_asicCom.c:1776 on) reads, for ports 0-6 (0-5 and the CPU port),
 * and CpuEvent: 7 x 32 + 1 = 225.  Loaded per port in ascending address
 * order, RX then TX, and CpuEvent last; the vendor's order is unsequenced C
 * (printf arguments), so no order is copied.  Out: MIB_CONTROL at 0x000 (a
 * write restarts the counters; it is never read either), etherStatsOctets
 * (0x10C/0x110), ifOutDiscards (0x814), 0x828 and 0x830, which the vendor's
 * dump does not read (B only), and ports 7-8 (B only).  The byte counters are
 * a word pair (lo, lo + 4); the pair can tear across a carry between its two
 * loads, and nothing here can tell (推).
 *
 * ======================================================================
 * THE PAGE
 * ======================================================================
 *
 *     version rtl819x-view 1.0
 *     admit %u                 words the table admits, summed at render
 *     last %s j %lu rc %d      none|mib|vlan|netif|peek, its jiffies, its rc
 *     n_mib %lu n_tbl %lu n_peek %lu refused %lu busy %lu ld %lu
 *     ref %08X %s              the last refused word and none|out|psrp
 *     ...the last verb's result...
 *     jiffies %lu              the terminator
 *
 * `refused` counts -EACCES refusals, `busy` the tbl verbs refused -EBUSY,
 * `ld` every load this file has made.  A refused or malformed request
 * changes no cached result.  The result's own lines, and the page's size,
 * are over the /proc section below.
 *
 * ======================================================================
 * WHAT IT CANNOT SEE
 * ======================================================================
 *
 * The silicon.  tools/viewcheck.py drives this file on the host against a
 * model written from the same sources as the table, so a misreading shared
 * by both passes there.  How long SWTACR stays busy, whether a table slot
 * tears, whether a MIB read clears a counter: the bench says.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/proc_fs.h>
#include <linux/delay.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/jiffies.h>

#include <linux/rlxfw-mark.h>
#include <asm/io.h>
#include <asm/uaccess.h>

#define RTL819X_VIEW_VERSION	"rtl819x-view 1.0"
#define RTL819X_VIEW_PROC	"rtl819x-view"

/* The counters and the cache are unlocked, as rtl819x-switch 1.2's are, and
 * for the same stated reason turned into a refusal: this .config is UP and
 * PREEMPT_NONE, no verb sleeps once it has started loading, and both /proc
 * handlers run in process context. */
#if defined(CONFIG_SMP) || defined(CONFIG_PREEMPT)
#error "rtl819x-view 1.0 keeps its counters and its cache unlocked; they need a lock before this build can be SMP or preemptible"
#endif

/* The MIB block, B :275 (MIB_COUNTER_BASE = SWCORE_BASE + 0x1000), and the
 * per-port stride, B :280 (MIB_ADDROFFSETBYPORT). */
#define RTL819X_VIEW_MIB	0xBB801000u
#define RTL819X_VIEW_MIB_END	0xBB802000u
#define RTL819X_VIEW_MIB_STRIDE	0x80u
#define RTL819X_VIEW_MIB_PORTS	7		/* 0-5 and the CPU port */
#define RTL819X_VIEW_NMIB	225		/* 7 x 32 + CpuEvent */

/* PSRP0-PSRP8, B :1143-:1151: refused with their own reason. */
#define RTL819X_VIEW_PSRP0	0xBB804128u
#define RTL819X_VIEW_PSRP8	0xBB804148u

/* The table read.  SWTACR B :196, ACTION_START B :211; REAL_SWTBL_BASE
 * B :151; entry length 8 words, rtl865x_asicBasic.h:13. */
#define RTL819X_VIEW_SWTACR	0xBB804D00u
#define RTL819X_VIEW_ACTION	(1u << 0)
#define RTL819X_VIEW_TBL_BASE	0xBB000000u
#define RTL819X_VIEW_ENTRY	8
#define RTL819X_VIEW_MAXSLOT	16
#define RTL819X_VIEW_TRIES	10		/* the reader's `li $16,10` */
#define RTL819X_VIEW_BOUND	10000u		/* SWTACR polls, udelay(1) apart */

#define RTL819X_VIEW_PEEK_MAX	16
#define RTL819X_VIEW_FIELD_MAX	10		/* "0x" and eight hex digits */
#define RTL819X_VIEW_NW		RTL819X_VIEW_NMIB	/* the largest result */

/* ------------------------------------------------------------------------
 * The admission table.  One row is a run of `n` consecutive words starting
 * at KSEG1 address `a`, repeated `rep` times `stride` bytes apart (the MIB's
 * seven ports; 1 and 0 everywhere else).  Each row's comment is: the names,
 * B's lines, then the second source.  量 "DW X n" is a loader dump of n words
 * from X committed under bench/; D is a table of the draft datasheet.
 * ------------------------------------------------------------------------ */

struct rtl819x_view_run {
	u32	a;
	u8	n;
	u8	rep;
	u16	stride;
};

static const struct rtl819x_view_run rtl819x_view_runs[] = {
	/* ---- the switch block, 0xBB804000-0xBB804FFF: 54 words ---- */
	{ 0xBB804000,  4, 1, 0 },	/* MACCR MDCIOCR MDCIOSR PMCR, B :997-:1000; 量 DW BB804000 4, D Table 57 (04, 08) */
	{ 0xBB804044,  1, 1, 0 },	/* BSCR, B :1014; D Tables 60-61 */
	{ 0xBB804100, 10, 1, 0 },	/* PITCR PCRP0-PCRP8, B :1133-:1142; D Table 62 (all but 18), 量 DW BB804100 8, DW BB804114 4 */
	{ 0xBB80414C,  2, 1, 0 },	/* P0GMIICR P5GMIICR, B :1152-:1153; 量 DW BB80414C 4 */
	{ 0xBB804200,  4, 1, 0 },	/* CVIDR SSIR CRMR BISTCR, B :1401-:1406; 量 DW BB804200 4 */
	{ 0xBB804234,  4, 1, 0 },	/* MEMCR, BISTTSDR0|1 (one address, two names), BISTTSDR2, BISTTSDR3, B :1438, :1407-:1410; 量 DW BB804234 4 */
	{ 0xBB804300,  2, 1, 0 },	/* LEDCREG (LEDCR) LEDCR1, B :2627-:2628, :2633; D Tables 67-70 */
	{ 0xBB80430C,  1, 1, 0 },	/* LEDBCR, B :2629; D Tables 67-70 */
	{ 0xBB804400, 14, 1, 0 },	/* TEACR TEATCR RMACR ALECR MSCR L4TOCR SWTCR0 SWTCR1 PLITIMR DACLRCR FFCR MGFCR_E0R0-R2, B :1479-:1493; 量 DW at 4400, 4410, 4418, 4428 x4, contiguous */
	{ 0xBB804A00,  8, 1, 0 },	/* VCR0 VCR1 PVCR0-PVCR4 PBVCR0, B :2299-:2306; 量 DW at 4A00, 4A08, 4A10 x4, and rtl819x-switch 1.3's table */
	{ 0xBB804D00,  3, 1, 0 },	/* SWTACR SWTASR SWTAA, B :196-:198; 量 DW BB804D00 4 */
	{ 0xBB804D3C,  1, 1, 0 },	/* TCR7, B :206; 量 DW BB804D3C 4 */

	/* ---- the MIB, 0xBB801000: 225 words.  B :275-:315; 量 the vendor's
	 * asicCounter dump of exactly these words in 291 committed bench/
	 * files, equal to the netdev's own counts byte for byte (NET-46) and
	 * cumulative across 76 reads (notes/nic-driver.md section 26).  D has
	 * no MIB section.  Ports 0-6, 0x80 apart. ---- */
	{ 0xBB801100,  2, 7, 0x80 },	/* ifInOctets, lo and hi, B :282 */
	{ 0xBB801108,  1, 7, 0x80 },	/* ifInUcastPkts, B :283 */
	{ 0xBB801114, 18, 7, 0x80 },	/* etherStatsUndersizePkts ... dot3InPauseFrames, B :285-:302 */
	{ 0xBB801800,  2, 7, 0x80 },	/* ifOutOctets, lo and hi, B :303 */
	{ 0xBB801808,  3, 7, 0x80 },	/* ifOutUcastPkts ifOutMulticastPkts ifOutBroadcastPkts, B :304-:306 */
	{ 0xBB801818,  4, 7, 0x80 },	/* single, multiple collision, deferred, late collision, B :308-:311 */
	{ 0xBB80182C,  1, 7, 0x80 },	/* dot3OutPauseFrames, B :313 */
	{ 0xBB801834,  1, 7, 0x80 },	/* etherStatsCollisions, B :315 */
	{ 0xBB801084,  1, 1, 0 },	/* etherStatsCpuEventPkt (CpuEvent), B :281 */

	/* ---- the CPU interface, 0xB8010000: 17 words.  D has none. ---- */
	{ 0xB8010000, 15, 1, 0 },	/* CPUICR CPURPDCR0-5 CPURMDCR0 CPUTPDCR0-1 CPUIIMR CPUIISR, CPUQDM0|1 2|3 4|5 (half-words, read as the word pair), B :492-:519; 量 NET-48 (DW B8010000 16, twice, identical) */
	{ 0xB8010060,  2, 1, 0 },	/* CPUTPDCR2 CPUTPDCR3, B :508-:509; 量 NET-48 (DW B8010060 4) */

	/* ---- PIN_MUX: 2 words.  No reading on this die yet. ---- */
	{ 0xB8000040,  2, 1, 0 },	/* PIN_MUX_SEL PIN_MUX_SEL2, B :3115-:3116; D Tables 35-36 */
};

#define RTL819X_VIEW_NRUN	ARRAY_SIZE(rtl819x_view_runs)

/* Admission verdicts, and the page's names for a refusal's reason. */
#define RTL819X_VIEW_IN		0
#define RTL819X_VIEW_OUT	1
#define RTL819X_VIEW_PSRP	2
static const char *const rtl819x_view_why[] = { "none", "out", "psrp" };

/* The two tables `tbl` reads: the name typed, the type number, the slots. */
struct rtl819x_view_tbl {
	const char	*name;
	u8		type;
	u8		slots;
};

static const struct rtl819x_view_tbl rtl819x_view_tbls[] = {
	{ "vlan",  6, 16 },	/* TYPE_VLAN_TABLE; RTL865XC_VLANTBL_SIZE, rtl865x_asicCom.h:13-14 */
	{ "netif", 4,  8 },	/* TYPE_NETINTERFACE_TABLE; RTL865XC_NETIFTBL_SIZE, rtl865x_asicCom.h:19 */
};

/* What `last` says: none, mib, then the tables in the order above, peek. */
#define RTL819X_VIEW_L_NONE	0
#define RTL819X_VIEW_L_MIB	1
#define RTL819X_VIEW_L_TBL	2	/* + index into rtl819x_view_tbls */
#define RTL819X_VIEW_L_PEEK	4
static const char *const rtl819x_view_lname[] = {
	"none", "mib", "vlan", "netif", "peek"
};

/* The cache: the last verb's result, which is all a `cat` prints. */
static int rtl819x_view_last;
static unsigned long rtl819x_view_last_j;
static int rtl819x_view_last_rc;
static u32 rtl819x_view_w[RTL819X_VIEW_NW];
static u8 rtl819x_view_t[RTL819X_VIEW_MAXSLOT];		/* tries per slot */
static u8 rtl819x_view_eq[RTL819X_VIEW_MAXSLOT];	/* 1: the two buffers agreed */
static unsigned int rtl819x_view_nslot;		/* slots read */
static int rtl819x_view_busy_s = -1;		/* the slot refused -EBUSY */
static unsigned long rtl819x_view_polls;	/* SWTACR loads in the last tbl */
static u32 rtl819x_view_pa;			/* the last peek's address */
static unsigned int rtl819x_view_pn;		/* and its word count */

static unsigned long rtl819x_view_n_mib, rtl819x_view_n_tbl;
static unsigned long rtl819x_view_n_peek, rtl819x_view_n_refused;
static unsigned long rtl819x_view_n_busy, rtl819x_view_n_ld;
static u32 rtl819x_view_ref_a;
static int rtl819x_view_ref_why;

/* THE ONLY LOAD IN THIS FILE, so `ld` counts loads and not callers who
 * remembered to.  There is no store accessor at all. */
static inline u32 rtl819x_view_ld(u32 a)
{
	rtl819x_view_n_ld++;
	return __raw_readl((void __iomem *)(unsigned long)a);
}

/* RTL819X_VIEW_IN if the table admits `a`, else the reason it does not.
 * The table alone decides; the PSRP range only names the reason. */
static int rtl819x_view_admit(u32 a)
{
	const struct rtl819x_view_run *r;
	unsigned int i, k;
	u32 b;

	for (i = 0; i < RTL819X_VIEW_NRUN; i++) {
		r = &rtl819x_view_runs[i];
		for (k = 0; k < r->rep; k++) {
			b = r->a + k * r->stride;
			if (a >= b && a < b + 4u * r->n && !((a - b) & 3u))
				return RTL819X_VIEW_IN;
		}
	}
	if (a >= RTL819X_VIEW_PSRP0 && a <= RTL819X_VIEW_PSRP8)
		return RTL819X_VIEW_PSRP;
	return RTL819X_VIEW_OUT;
}

static unsigned int rtl819x_view_nadmit(void)
{
	unsigned int i, n = 0;

	for (i = 0; i < RTL819X_VIEW_NRUN; i++)
		n += rtl819x_view_runs[i].n * rtl819x_view_runs[i].rep;
	return n;
}

static int rtl819x_view_in_mib(const struct rtl819x_view_run *r)
{
	return r->a >= RTL819X_VIEW_MIB && r->a < RTL819X_VIEW_MIB_END;
}

/* Words per port: the MIB rows that repeat per port. */
static unsigned int rtl819x_view_mib_nper(void)
{
	unsigned int i, n = 0;

	for (i = 0; i < RTL819X_VIEW_NRUN; i++)
		if (rtl819x_view_in_mib(&rtl819x_view_runs[i]) &&
		    rtl819x_view_runs[i].rep == RTL819X_VIEW_MIB_PORTS)
			n += rtl819x_view_runs[i].n;
	return n;
}

/* The MIB words the table admits outside the per-port rows (CpuEvent). */
static unsigned int rtl819x_view_mib_nsys(void)
{
	unsigned int i, n = 0;

	for (i = 0; i < RTL819X_VIEW_NRUN; i++)
		if (rtl819x_view_in_mib(&rtl819x_view_runs[i]) &&
		    rtl819x_view_runs[i].rep != RTL819X_VIEW_MIB_PORTS)
			n += rtl819x_view_runs[i].n * rtl819x_view_runs[i].rep;
	return n;
}

/* ------------------------------------------------------------------------
 * The verbs.  Each validates everything before its first load; a request
 * refused there changes no cached result.
 * ------------------------------------------------------------------------ */

/* `mib`: every admitted word of the MIB block, per port and ascending, then
 * CpuEvent.  Refused -EIO before any load if the table does not hold exactly
 * the words the cache has room for -- the table is const, so this can only
 * fire on an edit of it, and it stops that edit overrunning the cache. */
static int rtl819x_view_mib(void)
{
	const struct rtl819x_view_run *r;
	unsigned int p, i, k, n = 0;

	if (rtl819x_view_mib_nper() * RTL819X_VIEW_MIB_PORTS +
	    rtl819x_view_mib_nsys() != RTL819X_VIEW_NMIB)
		return -EIO;
	for (p = 0; p < RTL819X_VIEW_MIB_PORTS; p++)
		for (i = 0; i < RTL819X_VIEW_NRUN; i++) {
			r = &rtl819x_view_runs[i];
			if (!rtl819x_view_in_mib(r) ||
			    r->rep != RTL819X_VIEW_MIB_PORTS)
				continue;
			for (k = 0; k < r->n; k++)
				rtl819x_view_w[n++] = rtl819x_view_ld(r->a +
						p * r->stride + 4u * k);
		}
	for (i = 0; i < RTL819X_VIEW_NRUN; i++) {
		r = &rtl819x_view_runs[i];
		if (!rtl819x_view_in_mib(r) || r->rep == RTL819X_VIEW_MIB_PORTS)
			continue;
		for (k = 0; k < r->n; k++)
			rtl819x_view_w[n++] = rtl819x_view_ld(r->a + 4u * k);
	}
	rtl819x_view_last = RTL819X_VIEW_L_MIB;
	rtl819x_view_last_rc = 0;
	rtl819x_view_last_j = jiffies;
	rtl819x_view_n_mib++;
	return 0;
}

/* `tbl vlan|netif`: see THE TABLE READ above.  Loads SWTACR and the table's
 * own words and nothing else; stores nothing. */
static int rtl819x_view_tbl(unsigned int ti)
{
	const struct rtl819x_view_tbl *t = &rtl819x_view_tbls[ti];
	u32 base = RTL819X_VIEW_TBL_BASE + ((u32)t->type << 16);
	u32 b0[RTL819X_VIEW_ENTRY];
	u32 *b1, a;
	unsigned int s, k, n, tries;
	int eq = 0, rc = 0;

	rtl819x_view_nslot = 0;
	rtl819x_view_busy_s = -1;
	rtl819x_view_polls = 0;
	for (s = 0; s < t->slots; s++) {
		for (n = 0; ; n++) {
			rtl819x_view_polls++;
			if (!(rtl819x_view_ld(RTL819X_VIEW_SWTACR) &
			      RTL819X_VIEW_ACTION))
				break;
			if (n >= RTL819X_VIEW_BOUND) {
				rtl819x_view_n_busy++;
				rtl819x_view_busy_s = (int)s;
				rc = -EBUSY;
				goto out;
			}
			udelay(1);
		}
		a = base + (s << 5);
		b1 = &rtl819x_view_w[s * RTL819X_VIEW_ENTRY];
		for (tries = 1; ; tries++) {
			for (k = 0; k < RTL819X_VIEW_ENTRY; k++)
				b0[k] = rtl819x_view_ld(a + 4u * k);
			for (k = 0; k < RTL819X_VIEW_ENTRY; k++)
				b1[k] = rtl819x_view_ld(a + 4u * k);
			eq = 1;
			for (k = 0; k < RTL819X_VIEW_ENTRY; k++)
				if (b0[k] != b1[k])
					eq = 0;
			if (eq || tries >= RTL819X_VIEW_TRIES)
				break;
		}
		rtl819x_view_t[s] = (u8)tries;
		rtl819x_view_eq[s] = (u8)eq;
		rtl819x_view_nslot = s + 1;
	}
out:
	rtl819x_view_last = RTL819X_VIEW_L_TBL + (int)ti;
	rtl819x_view_last_rc = rc;
	rtl819x_view_last_j = jiffies;
	rtl819x_view_n_tbl++;
	return rc;
}

/* `peek A [n]`: every word of [A, A + 4n) admitted, or the whole request
 * refused before any load, counted, the first refused word and its reason
 * kept for the page. */
static int rtl819x_view_peek(unsigned long a, unsigned long n)
{
	unsigned int i;
	u32 w;
	int why;

	if ((a & 3) || n < 1 || n > RTL819X_VIEW_PEEK_MAX)
		return -EINVAL;
	for (i = 0; i < n; i++) {
		w = (u32)a + 4u * i;
		why = rtl819x_view_admit(w);
		if (why != RTL819X_VIEW_IN) {
			rtl819x_view_n_refused++;
			rtl819x_view_ref_a = w;
			rtl819x_view_ref_why = why;
			return -EACCES;
		}
	}
	for (i = 0; i < n; i++)
		rtl819x_view_w[i] = rtl819x_view_ld((u32)a + 4u * i);
	rtl819x_view_pa = (u32)a;
	rtl819x_view_pn = (unsigned int)n;
	rtl819x_view_last = RTL819X_VIEW_L_PEEK;
	rtl819x_view_last_rc = 0;
	rtl819x_view_last_j = jiffies;
	rtl819x_view_n_peek++;
	return 0;
}

/* ------------------------------------------------------------------------
 * /proc
 *
 * After the five header lines, the last verb's result:
 *
 *   mib    mib base BB801000 stride 080 ports 7 words 225
 *          mo  the 32 offsets of a port's words from the MIB base, port 0
 *          m0 .. m6  32 words each, in the order of `mo`, port p at +0x80p
 *          mc  CpuEvent: its offset, its word
 *   tbl    tbl vlan|netif base %08X slots %u words 8 polls %lu
 *          sNN tK eq|mis  the eight words of the second buffer, per slot
 *          busy sNN       only after -EBUSY, the slot it stopped at
 *   peek   peek %08X n %u, then `a ADDRESS WORD` per word
 *
 * Result lines print only while the page is under the budget.  Walked from
 * the formats with every field at its type's widest (32-bit longs, as on
 * this kernel): everything before the result is <= 193 B, the widest result
 * (mib's) is <= 2,231 B and the trailer <= 19 B, so the page is <= 2,443 B,
 * and the budget is a guard that cannot fire at these widths
 * (tools/viewcheck.py V14 measures all four).
 * ------------------------------------------------------------------------ */

#define RTL819X_VIEW_PAGE_BUDGET	3900

static int rtl819x_view_mib_lines(char *page, int len)
{
	const struct rtl819x_view_run *r;
	unsigned int nper = rtl819x_view_mib_nper();
	unsigned int p, i, k, n = 0;

	len += sprintf(page + len, "mib base %08X stride %03X ports %u words %u\n",
		       RTL819X_VIEW_MIB, RTL819X_VIEW_MIB_STRIDE,
		       (unsigned int)RTL819X_VIEW_MIB_PORTS,
		       (unsigned int)RTL819X_VIEW_NMIB);
	len += sprintf(page + len, "mo");
	for (i = 0; i < RTL819X_VIEW_NRUN; i++) {
		r = &rtl819x_view_runs[i];
		if (rtl819x_view_in_mib(r) && r->rep == RTL819X_VIEW_MIB_PORTS)
			for (k = 0; k < r->n; k++)
				len += sprintf(page + len, " %03X",
					       r->a + 4u * k - RTL819X_VIEW_MIB);
	}
	len += sprintf(page + len, "\n");
	for (p = 0; p < RTL819X_VIEW_MIB_PORTS &&
		    len < RTL819X_VIEW_PAGE_BUDGET; p++) {
		len += sprintf(page + len, "m%u", p);
		for (k = 0; k < nper; k++)
			len += sprintf(page + len, " %08X", rtl819x_view_w[n++]);
		len += sprintf(page + len, "\n");
	}
	n = nper * RTL819X_VIEW_MIB_PORTS;
	for (i = 0; i < RTL819X_VIEW_NRUN && len < RTL819X_VIEW_PAGE_BUDGET; i++) {
		r = &rtl819x_view_runs[i];
		if (!rtl819x_view_in_mib(r) || r->rep == RTL819X_VIEW_MIB_PORTS)
			continue;
		for (k = 0; k < r->n; k++)
			len += sprintf(page + len, "mc %03X %08X\n",
				       r->a + 4u * k - RTL819X_VIEW_MIB,
				       rtl819x_view_w[n++]);
	}
	return len;
}

static int rtl819x_view_tbl_lines(char *page, int len, unsigned int ti)
{
	const struct rtl819x_view_tbl *t = &rtl819x_view_tbls[ti];
	unsigned int s, k;

	len += sprintf(page + len, "tbl %s base %08X slots %u words %u polls %lu\n",
		       t->name, RTL819X_VIEW_TBL_BASE + ((u32)t->type << 16),
		       (unsigned int)t->slots, (unsigned int)RTL819X_VIEW_ENTRY,
		       rtl819x_view_polls);
	for (s = 0; s < rtl819x_view_nslot && len < RTL819X_VIEW_PAGE_BUDGET;
	     s++) {
		len += sprintf(page + len, "s%02u t%u %s", s,
			       (unsigned int)rtl819x_view_t[s],
			       rtl819x_view_eq[s] ? "eq" : "mis");
		for (k = 0; k < RTL819X_VIEW_ENTRY; k++)
			len += sprintf(page + len, " %08X",
				       rtl819x_view_w[s * RTL819X_VIEW_ENTRY + k]);
		len += sprintf(page + len, "\n");
	}
	if (rtl819x_view_busy_s >= 0)
		len += sprintf(page + len, "busy s%02d\n", rtl819x_view_busy_s);
	return len;
}

static int rtl819x_view_peek_lines(char *page, int len)
{
	unsigned int i;

	len += sprintf(page + len, "peek %08X n %u\n", rtl819x_view_pa,
		       rtl819x_view_pn);
	for (i = 0; i < rtl819x_view_pn && len < RTL819X_VIEW_PAGE_BUDGET; i++)
		len += sprintf(page + len, "a %08X %08X\n",
			       rtl819x_view_pa + 4u * i, rtl819x_view_w[i]);
	return len;
}

static int rtl819x_view_read_proc(char *page, char **start, off_t off,
				  int count, int *eof, void *data)
{
	int len = 0;

	len += sprintf(page + len, "version %s\n", RTL819X_VIEW_VERSION);
	len += sprintf(page + len, "admit %u\n", rtl819x_view_nadmit());
	len += sprintf(page + len, "last %s j %lu rc %d\n",
		       rtl819x_view_lname[rtl819x_view_last],
		       rtl819x_view_last_j, rtl819x_view_last_rc);
	len += sprintf(page + len,
		       "n_mib %lu n_tbl %lu n_peek %lu refused %lu busy %lu ld %lu\n",
		       rtl819x_view_n_mib, rtl819x_view_n_tbl,
		       rtl819x_view_n_peek, rtl819x_view_n_refused,
		       rtl819x_view_n_busy, rtl819x_view_n_ld);
	len += sprintf(page + len, "ref %08X %s\n", rtl819x_view_ref_a,
		       rtl819x_view_why[rtl819x_view_ref_why]);

	if (rtl819x_view_last == RTL819X_VIEW_L_MIB)
		len = rtl819x_view_mib_lines(page, len);
	else if (rtl819x_view_last == RTL819X_VIEW_L_PEEK)
		len = rtl819x_view_peek_lines(page, len);
	else if (rtl819x_view_last >= RTL819X_VIEW_L_TBL &&
		 rtl819x_view_last < RTL819X_VIEW_L_PEEK)
		len = rtl819x_view_tbl_lines(page, len, (unsigned int)
				(rtl819x_view_last - RTL819X_VIEW_L_TBL));

	len += sprintf(page + len, "jiffies %lu\n", jiffies);	/* terminator */
	*eof = 1;
	return len;
}

/* Exactly n space-separated numbers, each starting with a digit and at most
 * RTL819X_VIEW_FIELD_MAX characters long, the last one ending the string --
 * rtl819x-switch 1.3's parser, with the length cap added.  simple_strtoul
 * skips nothing, reads a field that does not start with a digit as 0 and
 * checks no overflow (lib/vsprintf.c).  The cap refuses `0x1BB804000`; a
 * ten-digit decimal above 4294967295 still wraps modulo 2^32 on this 32-bit
 * kernel, and the wrapped word is what the admission check sees and what the
 * page prints, so a wrap can reach only an admitted word, under its own
 * address. */
static int rtl819x_view_nums(const char *s, unsigned long *v, int n)
{
	char *e;
	int i;

	for (i = 0; i < n; i++) {
		if (*s < '0' || *s > '9')
			return -EINVAL;
		v[i] = simple_strtoul(s, &e, 0);
		if (e - s > RTL819X_VIEW_FIELD_MAX ||
		    *e != (i + 1 < n ? ' ' : '\0'))
			return -EINVAL;
		s = e + 1;
	}
	return 0;
}

static int rtl819x_view_write_proc(struct file *file, const char __user *ubuf,
				   unsigned long count, void *data)
{
	char buf[48];
	unsigned long n = count, v[2];
	unsigned int i;
	int rc;

	if (n >= sizeof(buf))
		return -EINVAL;
	if (copy_from_user(buf, ubuf, n))
		return -EFAULT;
	buf[n] = '\0';
	while (n && (buf[n - 1] == '\n' || buf[n - 1] == '\r'))
		buf[--n] = '\0';

	if (!strcmp(buf, "mib")) {
		rc = rtl819x_view_mib();
		return rc ? rc : (int)count;
	}
	if (!strncmp(buf, "tbl ", 4)) {
		for (i = 0; i < ARRAY_SIZE(rtl819x_view_tbls); i++)
			if (!strcmp(buf + 4, rtl819x_view_tbls[i].name)) {
				rc = rtl819x_view_tbl(i);
				return rc ? rc : (int)count;
			}
		return -EINVAL;
	}
	if (!strncmp(buf, "peek ", 5)) {
		if (!rtl819x_view_nums(buf + 5, v, 1))
			v[1] = 1;
		else if (rtl819x_view_nums(buf + 5, v, 2))
			return -EINVAL;
		rc = rtl819x_view_peek(v[0], v[1]);
		return rc ? rc : (int)count;
	}
	return -EINVAL;
}

/* The /proc entry only: no load at boot, and nothing printed unless this
 * fails. */
static int __init rtl819x_view_init(void)
{
	struct proc_dir_entry *pde;

	pde = create_proc_entry(RTL819X_VIEW_PROC, 0644, NULL);
	if (!pde) {
		rlxfw_mark("VW0-NOPROC");
		return 0;
	}
	pde->read_proc  = rtl819x_view_read_proc;
	pde->write_proc = rtl819x_view_write_proc;
	return 0;
}

device_initcall(rtl819x_view_init);
