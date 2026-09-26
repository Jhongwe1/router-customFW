#!/usr/bin/env python3
"""mdiocheck -- rtl819x-switch 1.3's MDIO block, compiled and driven on the host.

WHAT IT CHECKS, AND WHY IT CAN
------------------------------
`R6b-7` appended one block to `rtl819x-switch.c`: the bus's read and write
ops, `probe`, `scan`, `pread`, `bound`, the gate, and /proc/rtl819x-mdio.
This tool cuts that block out of the driver UNCHANGED (from its banner to the
end of the file) and compiles it with the host's gcc in the kernel's dialect
(`-std=gnu89 -Werror`) inside a generated harness that supplies, in place of
the kernel:

  * a scripted MDIO controller -- MDCIOCR 0x4004 / MDCIOSR 0x4008, STATUS
    held for a scripted number of reads after each store, a PHY model on
    MDIO 0-4 with a page-select register 31 (pages 0 and 1), and 0x0000 at
    5-31 (SPEC.md NET-24);
  * phylib's register/scan/read path, transcribed from the staged 2.6.30
    tree (mdio_bus.c:87-139, :182-221, :234-246; phy_device.c:187-236):
    mask, get_phy_id's -EIO, the 0x1fffffff empty test, device_register
    refusing a second device of one name;
  * IRQs-off sections, udelay and a mutex that are COUNTED: every MDCIOCR
    store records whether IRQs were off and in which section, the delay spent
    inside each section is summed, and a mutex taken with IRQs off is a
    violation;
  * the kernel's own simple_strtoul (lib/vsprintf.c:36-75, no whitespace
    skipped) and this arch's errno values (ETIMEDOUT 145,
    arch/rlx/include/asm/errno.h:98).

Cases (each prints one `  ok`/`  FAIL` line with exactly two leading spaces):

  K0   the block compiles as the kernel's dialect, warnings as errors, and the
       harness's errno table is this arch's
  K1   boot: /proc/rtl819x-mdio byte for byte, and no MDIO store
  K2   locked: probe, scan and pread refused (-EPERM, counted), no store;
       `bound` accepted while locked, issuing nothing
  K3   the token: the switch's `unlock i-mean-it` does not unlock this gate,
       a near miss does not either, `unlock mdio-i-mean-it` does, `lock` locks
  K4   probe: refused -EAGAIN at a small bound WITHOUT spending the one shot;
       permitted at the fixed bound: ten reads (regs 2, 3 of 0-4), the exact
       MDCIOCR words, phy0-4 `id 001CC880 rc 0 xrc 0 drv 0 att 0`, five
       devices `rlxsw:00`..`rlxsw:04`, MD1 1F; a second probe -EEXIST
  K5   scan and pread before a probe: -ENODEV, no store
  K6   scan 0 31: 192 reads, every row's six values and PSRP (0-4 only),
       every store with IRQs off, no PSRP read with IRQs off
  K7   the bound's positive control: at `bound 0` with STATUS held 3 reads a
       row reads E145 E016 E016 E145 E016 E016 (mdio_to 2, busy 4, 2 reads
       issued); back at 10000 it reads 0000 and mdio_to does not move
  K8   pread's refusals, each beside a permitted neighbour: address 5, page 2
       and 7, register 31, a missing field, a doubled space, a trailing
       letter -- -EINVAL; any page at a bound that is not 10000 -- -EAGAIN,
       counted, no pr line, no store
  K9   pread a 1 r: exactly six stores (read 31, 31<-1, read 31, read r,
       31<-0, read 31), all in ONE IRQs-off section, the mutex taken once
       outside it, PSRP read outside it; `ps 1 p1 0 rs 0 rt 0 rc 0`
  K10  pread a 0 r: one read, no write, `rs 1`
  K11  a PHY not on page 0: -EPROTO after one read, and NOTHING written
  K12  a register 31 that reads 0 whatever it holds: -EPROTO, value kept,
       not dirty
  K13  the restore refused busy once: stored on the retry (`rt 1`, retry 1),
       not dirty
  K14  the restore refused busy twice: dirty, -EIO, every later pread -EIO
       with no store -- also when register 31 reads 0 (the restore was never
       stored, so a 0 read back proves nothing)
  K15  IRQs-off time: no section in any case above exceeds 13 x bound of
       udelay, the block comment's figure (an upper bound by counting, not a
       maximum any scripted case reaches; the largest here is 3 x bound)
  K16  the page at every field's widest (32-bit longs): the block comment's
       header, row, trailer and total figures are the measured ones, all 32
       rows print, and the page fits in 4,096 bytes
  K17  `cat` renders twice and issues no MDIO command
  K18  the bus's write op refuses and counts, no store
  K19  stuck hardware: probe runs, phylib's rc is -5 and the kept xrc -16 on
       every address, and the one shot is spent (the named residual)
  K20  the select timed out: the restore is still stored and verified
  K21  MDCIOSR 30:16 kept in `hi` and `hi_or`; MD2 and MD3 mark values
  K22  the /proc entry failing at init marks MD0-NOPROC and nothing else
  K23  scan's and bound's refusals beside permitted neighbours: lo > hi, hi
       32, a doubled space, a trailing letter, a missing field, bound 10001,
       -1, 5x -- -EINVAL; `bound 0x10` reads 16; an unknown verb -EINVAL

M0..M20 then mutate a COPY of the block, one defect each, and require the case
named for it to go red.  M0 is the unmutated copy through the same path: if it
is not green, no kill is counted.  A mutant whose anchor does not occur
exactly once, that does not compile, or whose named case stays green is a
survivor, never a kill.

WHAT IT CANNOT SEE
------------------
The silicon: how long STATUS stays set, what register 31 reads back, whether
the switch's PHY poller meets a selected page, what MDCIOSR 30:16 means.
The fake is a model written from the same sources the driver was, so a
misreading shared by both passes here; the bench is the second source.
Nor the rest of the kernel: phylib's device model beyond the name check,
sysfs, and whether rsdk's gcc 3.4.6 compiles the block -- the image build
answers that.

Needs gcc and nothing else: no toolchain, no $FWRE_WORK, no device.
    mdiocheck.py [--source PATH] [--keep DIR] [--no-mutants]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "config", "rlxfw-src", "linux-2.6.30", "drivers",
                      "net", "rtl819x-switch.c")
CFLAGS = ["-std=gnu89", "-O1", "-Wall", "-Wextra", "-Wno-unused-parameter",
          "-Wdeclaration-after-statement", "-Wstrict-prototypes", "-Werror"]
BANNER = " * 1.3 (R6b-7): AN mii_bus"
PAGE = 4096

# arch/rlx/include/asm/errno.h (EPROTO :48, ETIMEDOUT :98) and
# include/asm-generic/errno-base.h for the rest -- this arch's values.
ERRNO = {"EPERM": 1, "EIO": 5, "EAGAIN": 11, "ENOMEM": 12, "EFAULT": 14,
         "EBUSY": 16, "EEXIST": 17, "ENODEV": 19, "EINVAL": 22,
         "EPROTO": 71, "ETIMEDOUT": 145}

HARNESS = r"""
#include <sys/types.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#undef ETIMEDOUT
#define ETIMEDOUT 145	/* arch/rlx/include/asm/errno.h:98, not the host's */
#undef EPROTO
#define EPROTO 71

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define __init
#define __user
#define CONFIG_PHYLIB 1
#define RTL819X_SW_VERSION "@VERSION@"
#define RTL819X_SW_PSRP0 0x4128
#define MII_BUS_ID_SIZE 17
#define PHY_MAX_ADDR 32
#define UNUSED __attribute__((unused))

/* ------------------------------------------------ the counted kernel */
static unsigned long jiffies = 4242;
static int irq_depth, irq_sections, irq_imbalance;
static unsigned long delay_sec, delay_max, delay_total;
static int mutex_viol, mutex_locks;
static int illegal_writes, reserved_bits, stores_outside;
static int psrp_rd, psrp_bad, psrp_insec;
static char last_mark[64];
static int n_marks;
static u32 psrp_val[5] = { 0x10E0, 0x10E0, 0x10E0, 0x10F9, 0x10E0 };

static UNUSED int irq_enter(void)
{
	int prev = irq_depth;

	if (irq_depth == 0) {
		irq_sections++;
		delay_sec = 0;
	}
	irq_depth++;
	return prev;
}
static UNUSED void irq_leave(unsigned long f)
{
	irq_depth--;
	if (irq_depth != (int)f)
		irq_imbalance++;
	if (irq_depth == 0 && delay_sec > delay_max)
		delay_max = delay_sec;
}
#define local_irq_save(f)	do { (f) = (unsigned long)irq_enter(); } while (0)
#define local_irq_restore(f)	irq_leave(f)
static UNUSED void udelay(unsigned long us)
{
	delay_total += us;
	if (irq_depth)
		delay_sec += us;
}
struct mutex { int held; };
static UNUSED void mutex_lock(struct mutex *m)
{
	if (irq_depth || m->held)
		mutex_viol++;
	m->held = 1;
	mutex_locks++;
}
static UNUSED void mutex_unlock(struct mutex *m)
{
	if (!m->held)
		mutex_viol++;
	m->held = 0;
}
static void mark_puts(const char *s)
{
	snprintf(last_mark, sizeof(last_mark), "%s", s);
	n_marks++;
}
static void mark_hex(const char *s, unsigned int v)
{
	snprintf(last_mark, sizeof(last_mark), "%s%08X", s, v);
	n_marks++;
}
#define rlxfw_mark(tag)		mark_puts("RLXFW-" tag)
#define rlxfw_markx(tag, v)	mark_hex("RLXFW-" tag "=", (unsigned int)(v))

/* lib/vsprintf.c:36-75, transcribed: no whitespace is skipped. */
static unsigned int k_guess_base(const char *cp)
{
	if (cp[0] == '0') {
		if ((cp[1] | 0x20) == 'x' && isxdigit((unsigned char)cp[2]))
			return 16;
		return 8;
	}
	return 10;
}
static UNUSED unsigned long simple_strtoul(const char *cp, char **endp,
					   unsigned int base)
{
	unsigned long result = 0;

	if (!base)
		base = k_guess_base(cp);
	if (base == 16 && cp[0] == '0' && (cp[1] | 0x20) == 'x')
		cp += 2;
	while (isxdigit((unsigned char)*cp)) {
		unsigned int value = isdigit((unsigned char)*cp) ? *cp - '0' :
				     (*cp | 0x20) - 'a' + 10;
		if (value >= base)
			break;
		result = result * base + value;
		cp++;
	}
	if (endp)
		*endp = (char *)cp;
	return result;
}
static UNUSED unsigned long copy_from_user(void *d, const void *s,
					   unsigned long n)
{
	memcpy(d, s, n);
	return 0;
}

/* ------------------------------------------------ the MDIO controller */
static u32 phyreg[5][2][32];	/* addr, page, reg */
static u32 page31[5];
static int reg31_readable = 1, stuck;
static long status_left;
static long busy_post;
static long post_next[16];	/* per upcoming store; -1 = busy_post */
static int n_post_next;
static u32 hibits, rdata;
struct st { u32 w; int irq; int sec; };
static struct st stores[8192];
static int n_stores, n_dumped;

static void phy_init_model(void)
{
	int a, p, r;

	for (a = 0; a < 5; a++)
		for (p = 0; p < 2; p++)
			for (r = 0; r < 32; r++)
				phyreg[a][p][r] = (u32)((p << 15) | (a << 8) | r);
	for (a = 0; a < 5; a++) {
		phyreg[a][0][0] = 0x1100;
		phyreg[a][0][1] = a == 3 ? 0x78ED : 0x78C9;
		phyreg[a][0][2] = 0x001C;
		phyreg[a][0][3] = 0xC880;
		phyreg[a][0][4] = 0x01E1;
		phyreg[a][0][5] = a == 3 ? 0xCDE1 : 0x0001;
		phyreg[a][1][19] = 0x5400;
	}
	for (r = 0; r < 16; r++)
		post_next[r] = -1;
}
static u32 fake_readl(unsigned int off)
{
	if (off != 0x4008) {
		fprintf(stderr, "harness: read of %04X\n", off);
		exit(9);
	}
	if (stuck)
		return 0x80000000u | hibits;
	if (status_left > 0) {
		status_left--;
		return 0x80000000u | hibits;
	}
	return hibits | (rdata & 0xFFFFu);
}
static void fake_writel(u32 v, unsigned int off)
{
	unsigned int a = (v >> 24) & 0x1F, r = (v >> 16) & 0x1F;

	if (off != 0x4004) {
		fprintf(stderr, "harness: write of %04X\n", off);
		exit(9);
	}
	if (n_stores < 8192) {
		stores[n_stores].w = v;
		stores[n_stores].irq = irq_depth > 0;
		stores[n_stores].sec = irq_sections;
	}
	n_stores++;
	if (!irq_depth)
		stores_outside++;
	if (v & 0x60E00000u)
		reserved_bits++;
	if (v & 0x80000000u) {
		if (a < 5 && r == 31)
			page31[a] = v & 0xFFFFu;
		else
			illegal_writes++;
	} else if (a >= 5) {
		rdata = 0;
	} else if (r == 31) {
		rdata = reg31_readable ? page31[a] : 0;
	} else {
		rdata = page31[a] < 2 ? phyreg[a][page31[a]][r] : 0xDEAD;
	}
	if (n_post_next > 0) {
		status_left = post_next[0] >= 0 ? post_next[0] : busy_post;
		memmove(post_next, post_next + 1, sizeof(post_next) - sizeof(long));
		post_next[15] = -1;
		n_post_next--;
	} else {
		status_left = busy_post;
	}
}
static UNUSED void *rtl819x_sw_reg(unsigned int off)
{
	return (void *)(uintptr_t)off;
}
static UNUSED u32 __raw_readl(void *p)
{
	return fake_readl((unsigned int)(uintptr_t)p);
}
static UNUSED void __raw_writel(u32 v, void *p)
{
	fake_writel(v, (unsigned int)(uintptr_t)p);
}
static UNUSED u32 rtl819x_sw_rd(unsigned int off)
{
	psrp_rd++;
	if (irq_depth)
		psrp_insec++;
	if (off < 0x4128 || off > 0x4138 || (off & 3)) {
		psrp_bad++;
		return 0;
	}
	return psrp_val[(off - 0x4128) / 4];
}

/* ------------------------------------------------ phylib, 2.6.30's shape */
struct device_driver { int x; };
struct device { struct device_driver *driver; char name[48]; int live; };
struct net_device { int x; };
struct mii_bus;
struct phy_device {
	u32 phy_id;
	int addr;
	struct device dev;
	struct net_device *attached_dev;
	struct mii_bus *bus;
};
struct mii_bus {
	const char *name;
	char id[MII_BUS_ID_SIZE];
	void *priv;
	int (*read)(struct mii_bus *bus, int phy_id, int regnum);
	int (*write)(struct mii_bus *bus, int phy_id, int regnum, u16 val);
	int (*reset)(struct mii_bus *bus);
	struct mutex mdio_lock;
	void *parent;
	int state;
	struct device dev;
	struct phy_device *phy_map[PHY_MAX_ADDR];
	u32 phy_mask;
	int *irq;
};
#define IS_ERR(p)	((unsigned long)(p) >= (unsigned long)-4095)
#define PTR_ERR(p)	((long)(p))
#define ERR_PTR(e)	((void *)(long)(e))
static char devnames[64][48];
static int n_devs;

static int device_register(struct device *d)	/* the name check only */
{
	int i;

	for (i = 0; i < n_devs; i++)
		if (!strcmp(devnames[i], d->name))
			return -EEXIST;
	if (n_devs < 64)
		snprintf(devnames[n_devs++], 48, "%s", d->name);
	d->live = 1;
	return 0;
}
static UNUSED struct mii_bus *mdiobus_alloc(void)
{
	struct mii_bus *b = calloc(1, sizeof(*b));

	if (b)
		b->state = 1;			/* MDIOBUS_ALLOCATED */
	return b;
}
static UNUSED void mdiobus_free(struct mii_bus *b)
{
	free(b);
}
static int get_phy_id(struct mii_bus *bus, int addr, u32 *id)	/* :187 */
{
	int r = bus->read(bus, addr, 2);

	if (r < 0)
		return -EIO;
	*id = (u32)(r & 0xffff) << 16;
	r = bus->read(bus, addr, 3);
	if (r < 0)
		return -EIO;
	*id |= (u32)(r & 0xffff);
	return 0;
}
static UNUSED struct phy_device *mdiobus_scan(struct mii_bus *bus, int addr)
{
	struct phy_device *pd;
	u32 id = 0;
	int r = get_phy_id(bus, addr, &id);

	if (r)
		return ERR_PTR(r);
	if ((id & 0x1fffffff) == 0x1fffffff)	/* phy_device.c:231 */
		return NULL;
	pd = calloc(1, sizeof(*pd));
	pd->phy_id = id;
	pd->addr = addr;
	pd->bus = bus;
	snprintf(pd->dev.name, sizeof(pd->dev.name), "%s:%02x", bus->id, addr);
	if (device_register(&pd->dev)) {
		free(pd);
		pd = NULL;
	}
	bus->phy_map[addr] = pd;		/* mdio_bus.c:218 */
	return pd;
}
static UNUSED int mdiobus_register(struct mii_bus *bus)	/* :87 */
{
	int i, err;

	if (!bus || !bus->name || !bus->read || !bus->write)
		return -EINVAL;
	snprintf(bus->dev.name, sizeof(bus->dev.name), "%s", bus->id);
	if (device_register(&bus->dev))
		return -EINVAL;
	bus->mdio_lock.held = 0;
	if (bus->reset)
		bus->reset(bus);
	for (i = 0; i < PHY_MAX_ADDR; i++) {
		bus->phy_map[i] = NULL;
		if ((bus->phy_mask & (1u << i)) == 0) {
			struct phy_device *pd = mdiobus_scan(bus, i);
			if (IS_ERR(pd)) {
				err = (int)PTR_ERR(pd);
				return err;
			}
		}
	}
	bus->state = 2;				/* MDIOBUS_REGISTERED */
	return 0;
}
static UNUSED int mdiobus_read(struct mii_bus *bus, int addr, u16 regnum)
{
	int v;

	mutex_lock(&bus->mdio_lock);
	v = bus->read(bus, addr, regnum);
	mutex_unlock(&bus->mdio_lock);
	return v;
}

/* ------------------------------------------------ /proc */
struct file;
struct proc_dir_entry {
	int (*read_proc)(char *page, char **start, off_t off, int count,
			 int *eof, void *data);
	int (*write_proc)(struct file *file, const char *buf,
			  unsigned long count, void *data);
};
static struct proc_dir_entry the_pde;
static int pde_fail, pde_made;
static UNUSED struct proc_dir_entry *create_proc_entry(const char *name,
						       int mode, void *parent)
{
	if (pde_fail || strcmp(name, "rtl819x-mdio"))
		return NULL;
	pde_made = 1;
	return &the_pde;
}
#define device_initcall(fn)	static int (*harness_init)(void) = fn

#include "@BLOCK@"

/* ------------------------------------------------ the widest page */
static void set_widest(void)
{
	static struct mii_bus wb;
	static struct phy_device wp[5];
	int i, r;

	rtl819x_mdio_unlocked = INT_MIN;
	rtl819x_mdio_reg_rc = INT_MIN;
	rtl819x_mdio_bound = 0xFFFFFFFFu;
	rtl819x_mdio_n_rd = rtl819x_mdio_n_wr = 0xFFFFFFFFUL;
	rtl819x_mdio_n_to = rtl819x_mdio_n_busy = 0xFFFFFFFFUL;
	rtl819x_mdio_n_retry = rtl819x_mdio_n_refused = 0xFFFFFFFFUL;
	rtl819x_mdio_n_wr_refused = rtl819x_mdio_n_again = 0xFFFFFFFFUL;
	rtl819x_mdio_n_spin = 0xFFFFFFFFUL;
	rtl819x_mdio_spin_min = rtl819x_mdio_spin_max = 0xFFFFFFFFu;
	rtl819x_mdio_hi_or = 0xFFFFFFFFu;
	rtl819x_mdio_dirty = INT_MIN;
	rtl819x_mdio_scanned = 0xFFFFFFFFu;
	rtl819x_mdio_scan_j = 0xFFFFFFFFUL;
	jiffies = 0xFFFFFFFFUL;
	for (i = 0; i < 5; i++) {
		rtl819x_mdio_scan_rc[i] = INT_MIN;
		rtl819x_mdio_xrc[i] = INT_MIN;
		wp[i].phy_id = 0xFFFFFFFFu;
		wp[i].dev.driver = (struct device_driver *)&wp[i];
		wp[i].attached_dev = (struct net_device *)&wp[i];
		wb.phy_map[i] = &wp[i];
	}
	rtl819x_mdio_bus = &wb;
	rtl819x_mdio_npr = 0xFFFFFFFFu;
	for (i = 0; i < 8; i++) {
		struct rtl819x_mdio_pr *p = &rtl819x_mdio_prs[i];
		p->a = p->page = p->reg = p->rt = 255;
		p->p0 = p->ps = p->v = p->rs = p->p1 = p->rc = INT_MIN;
		p->psrp0 = p->psrp1 = 0xFFFFFFFFu;
	}
	/* a row's values are the read op's: 0..FFFF, or -EPERM/-EBUSY/
	 * -ETIMEDOUT -- three digits at most */
	for (i = 0; i < 32; i++) {
		rtl819x_mdio_rows[i].n = 0xFFFFFFFFu;
		rtl819x_mdio_rows[i].hi = 0xFFFFFFFFu;
		rtl819x_mdio_rows[i].psrp = 0xFFFFFFFFu;
		for (r = 0; r < 6; r++)
			rtl819x_mdio_rows[i].v[r] = -ETIMEDOUT;
	}
}

static void stat_line(void)
{
	int i;

	printf("STAT depth=%d sections=%d imbalance=%d dmax=%lu mutex_viol=%d "
	       "mutex_locks=%d outside=%d illegal=%d reserved=%d psrp_rd=%d "
	       "psrp_bad=%d psrp_insec=%d nstores=%d page31=%u,%u,%u,%u,%u "
	       "marks=%d mark=%s pde=%d devs=",
	       irq_depth, irq_sections, irq_imbalance, delay_max, mutex_viol,
	       mutex_locks, stores_outside, illegal_writes, reserved_bits,
	       psrp_rd, psrp_bad, psrp_insec, n_stores, page31[0], page31[1],
	       page31[2], page31[3], page31[4], n_marks,
	       last_mark[0] ? last_mark : "-", pde_made);
	for (i = 0; i < n_devs; i++)
		printf("%s%s", i ? "," : "", devnames[i]);
	printf("\n");
}

int main(void)
{
	static char page[3 * PAGE_SZ];
	char line[512], buf[512];
	int rc, i;
	long a, b, c;

	phy_init_model();
	printf("ERRNO EPERM=%d EIO=%d EAGAIN=%d ENOMEM=%d EFAULT=%d EBUSY=%d "
	       "EEXIST=%d ENODEV=%d EINVAL=%d EPROTO=%d ETIMEDOUT=%d\n",
	       EPERM, EIO, EAGAIN, ENOMEM, EFAULT, EBUSY, EEXIST, ENODEV,
	       EINVAL, EPROTO, ETIMEDOUT);
	printf("BOUND %u\n", RTL819X_MDIO_BOUND);
	while (fgets(line, sizeof(line), stdin)) {
		line[strcspn(line, "\n")] = '\0';
		if (!strcmp(line, "init")) {
			rc = harness_init();
			printf("OP init -> %d\n", rc);
		} else if (!strncmp(line, "w ", 2)) {
			snprintf(buf, sizeof(buf), "%s\n", line + 2);
			rc = the_pde.write_proc(NULL, buf, strlen(buf), NULL);
			printf("OP w %s -> %d\n", line + 2, rc);
		} else if (!strcmp(line, "r")) {
			char *start = NULL;
			int eof = 0;

			memset(page, 0x5A, sizeof(page));
			rc = the_pde.read_proc(page, &start, 0, PAGE_SZ, &eof,
					       NULL);
			page[rc < 0 ? 0 : rc] = '\0';
			printf("PAGE-BEGIN\n%sPAGE-END len=%d eof=%d\n", page, rc,
			       eof);
		} else if (sscanf(line, "set busy_post %ld", &a) == 1) {
			busy_post = a;
		} else if (sscanf(line, "set status_left %ld", &a) == 1) {
			status_left = a;
		} else if (sscanf(line, "set post_next %ld %ld", &a, &b) == 2) {
			post_next[a] = b;
			if (a + 1 > n_post_next)
				n_post_next = (int)a + 1;
		} else if (sscanf(line, "set stuck %ld", &a) == 1) {
			stuck = (int)a;
		} else if (sscanf(line, "set reg31r %ld", &a) == 1) {
			reg31_readable = (int)a;
		} else if (sscanf(line, "set page31 %ld %ld", &a, &b) == 2) {
			page31[a] = (u32)b;
		} else if (sscanf(line, "set hibits %li", &a) == 1) {
			hibits = (u32)a;
		} else if (sscanf(line, "set pdefail %ld", &a) == 1) {
			pde_fail = (int)a;
		} else if (!strcmp(line, "stores")) {
			for (i = n_dumped; i < n_stores && i < 8192; i++)
				printf("ST %d %08X irq %d sec %d\n", i, stores[i].w,
				       stores[i].irq, stores[i].sec);
			n_dumped = n_stores;
			printf("ST-END\n");
		} else if (!strcmp(line, "stat")) {
			stat_line();
		} else if (!strcmp(line, "widest")) {
			set_widest();
		} else if (sscanf(line, "buswrite %ld %ld %ld", &a, &b, &c) == 3) {
			rc = rtl819x_mdio_bus->write(rtl819x_mdio_bus, (int)a,
						     (int)b, (u16)c);
			printf("OP buswrite -> %d\n", rc);
		} else {
			printf("HARNESS unknown op: %s\n", line);
			return 3;
		}
		fflush(stdout);
	}
	return 0;
}
"""


def die(msg, rc=3):
    print("REFUSED: " + msg)
    sys.exit(rc)


def extract(src_text):
    """(block text, version string) or die with the reason."""
    lines = src_text.splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if ln.startswith(BANNER)]
    if len(hits) != 1:
        die("the 1.3 banner %r occurs %d times in the driver, not once"
            % (BANNER, len(hits)))
    start = hits[0] - 1
    if not lines[start].startswith("/* ====="):
        die("the line above the 1.3 banner is not its /* ===== rule")
    m = re.findall(r'^#define RTL819X_SW_VERSION\t"([^"]+)"$', src_text, re.M)
    if len(m) != 1:
        die("RTL819X_SW_VERSION is defined %d times" % len(m))
    return "".join(lines[start:]), m[0]


class Run:
    """One harness process over one script, parsed."""

    def __init__(self, exe, script):
        p = subprocess.run([exe], input="\n".join(script) + "\n",
                           capture_output=True, text=True, timeout=120)
        self.rc = p.returncode
        self.err = p.stderr
        self.ops, self.pages, self.stats, self.stores = [], [], [], []
        self.errno = {}
        self.bound = None
        cur = None
        st = []
        for ln in p.stdout.split("\n"):
            if cur is not None:
                m = re.match(r"PAGE-END len=(-?\d+) eof=(\d+)$", ln)
                if m:
                    self.pages.append(("".join(cur), int(m.group(1))))
                    cur = None
                else:
                    cur.append(ln + "\n")
                continue
            if ln == "PAGE-BEGIN":
                cur = []
            elif ln.startswith("OP "):
                m = re.match(r"OP (.*) -> (-?\d+)$", ln)
                self.ops.append((m.group(1), int(m.group(2))))
            elif ln.startswith("STAT "):
                d = {}
                for kv in ln[5:].split(" "):
                    k, _, v = kv.partition("=")
                    d[k] = v
                self.stats.append(d)
            elif ln.startswith("ST "):
                f = ln.split()
                st.append((int(f[1]), int(f[2], 16), int(f[4]), int(f[6])))
            elif ln == "ST-END":
                self.stores.append(st)
                st = []
            elif ln.startswith("ERRNO "):
                for kv in ln[6:].split(" "):
                    k, _, v = kv.partition("=")
                    self.errno[k] = int(v)
            elif ln.startswith("BOUND "):
                self.bound = int(ln.split()[1])

    def op(self, i):
        return self.ops[i][1]

    def stat(self, i, k):
        return self.stats[i][k]

    def field(self, page_i, key):
        """The rest of the first page line starting with `key `."""
        for ln in self.pages[page_i][0].split("\n"):
            if ln.startswith(key + " "):
                return ln[len(key) + 1:]
        return None


def rd(a, r):
    return (a << 24) | (r << 16)


def wr(a, r, v):
    return 0x80000000 | (a << 24) | (r << 16) | v


UNLOCK = "w unlock mdio-i-mean-it"
PROBED = ["init", UNLOCK, "w probe", "stores"]
PAGE1 = 0x8000		# the fake's page-1 marker bit


def boot_page(bound=10000):
    lines = ["version rtl819x-switch 1.3", "unlocked 0", "bus 0 reg_rc 1",
             "bound %d" % bound, "mdio_rd 0", "mdio_wr 0",
             "mdio_to 0 busy 0 retry 0", "refused 0 wr_refused 0 again 0",
             "spin 0 0 0", "hi_or 00000000", "dirty 0", "scanned 00000000 j 0"]
    lines += ["phy%d id - rc 1 xrc 1" % a for a in range(5)]
    lines += ["jiffies 4242"]
    return "".join(x + "\n" for x in lines)


def comment_figures(block):
    """The page figures the block's own comment claims."""
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in block.split("\n"))
    m = re.search(r"everything before the rows is <= ([\d,]+) B, a row <= "
                  r"(\d+) B and the trailer <= (\d+) B, so the page is "
                  r"<= ([\d,]+) B", body)
    if not m:
        return None
    return tuple(int(g.replace(",", "")) for g in m.groups())


def comment_irq_bound(block):
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in block.split("\n"))
    m = re.search(r"<= (\d+) x 10 ms = (\d+) ms, nominal", body)
    return (int(m.group(1)), int(m.group(2))) if m else None


def cases(exe, block, version):
    """Yield (name, ok, detail) for K1..K22 (K0 is the compile)."""
    B = 10000
    dmax_seen = []

    def track(run):
        for s in run.stats:
            dmax_seen.append(int(s["dmax"]))
        return run

    # K1 boot
    r = track(Run(exe, ["init", "r", "stat"]))
    ok = (r.rc == 0 and r.op(0) == 0 and version == "rtl819x-switch 1.3"
          and r.pages[0][0] == boot_page() and r.stat(0, "nstores") == "0"
          and r.stat(0, "pde") == "1")
    yield "K1", ok, "boot page %s" % ("exact" if ok else repr(r.pages[:1])[:300])

    # K2 locked
    r = track(Run(exe, ["init", "w probe", "w scan 0 4", "w pread 0 1 16",
                        "w bound 0", "w bound 10000", "r", "stat"]))
    e = -ERRNO["EPERM"]
    ok = (r.rc == 0 and [r.op(i) for i in (1, 2, 3)] == [e, e, e]
          and r.op(4) == 8 and r.op(5) == 12
          and r.field(0, "refused") == "3 wr_refused 0 again 0"
          and r.field(0, "bound") == "10000"
          and r.stat(0, "nstores") == "0")
    yield "K2", ok, "ops %s" % [x[1] for x in r.ops]

    # K3 token
    r = track(Run(exe, ["init", "w unlock i-mean-it", "r",
                        "w unlock mdio-i-mean-it2", "r",
                        UNLOCK, "r", "stat", "w lock", "r", "stat"]))
    ok = (r.rc == 0 and r.op(1) == e and r.field(0, "unlocked") == "0"
          and r.op(2) == e and r.field(1, "unlocked") == "0"
          and r.op(3) == len("unlock mdio-i-mean-it\n")
          and r.field(2, "unlocked") == "1"
          and r.stat(0, "mark") == "RLXFW-MD-UNLOCK"
          and r.op(4) == 5 and r.field(3, "unlocked") == "0"
          and r.stat(1, "mark") == "RLXFW-MD-LOCK"
          and r.stat(1, "nstores") == "0")
    yield "K3", ok, "ops %s" % [x[1] for x in r.ops]

    # K4 probe
    r = track(Run(exe, ["init", UNLOCK, "w bound 0", "w probe", "r", "stat",
                        "w bound 10000", "w probe", "r", "stat", "stores",
                        "w probe", "stat"]))
    want_words = [w for a in range(5) for w in (rd(a, 2), rd(a, 3))]
    phy_ok = all(r.field(1, "phy%d" % a) ==
                 "id 001CC880 rc 0 xrc 0 drv 0 att 0" for a in range(5))
    ok = (r.rc == 0 and r.op(3) == -ERRNO["EAGAIN"]
          and r.field(0, "refused") == "0 wr_refused 0 again 1"
          and r.field(0, "bus") == "0 reg_rc 1"
          and r.stat(0, "nstores") == "0"
          and r.op(5) == 6 and r.field(1, "bus") == "1 reg_rc 0"
          and r.field(1, "mdio_rd") == "10" and r.field(1, "mdio_wr") == "0"
          and phy_ok and r.stat(1, "mark") == "RLXFW-MD1=0000001F"
          and r.stat(1, "devs") ==
          "rlxsw,rlxsw:00,rlxsw:01,rlxsw:02,rlxsw:03,rlxsw:04"
          and [s[1] for s in r.stores[0]] == want_words
          and all(s[2] == 1 for s in r.stores[0])
          and r.op(6) == -ERRNO["EEXIST"] and r.stat(2, "nstores") == "10")
    yield "K4", ok, "ops %s rd %s" % ([x[1] for x in r.ops],
                                      r.field(1, "mdio_rd") if len(r.pages) > 1 else "-")

    # K5 before probe
    r = track(Run(exe, ["init", UNLOCK, "w scan 0 4", "w pread 0 1 16",
                        "stat"]))
    ok = (r.rc == 0 and r.op(2) == -ERRNO["ENODEV"]
          and r.op(3) == -ERRNO["ENODEV"] and r.stat(0, "nstores") == "0")
    yield "K5", ok, "ops %s" % [x[1] for x in r.ops]

    # K6 scan 0 31
    r = track(Run(exe, PROBED + ["w scan 0 31", "r", "stat", "stores"]))
    rows_ok = True
    for a in range(32):
        if a < 5:
            v = ["1100", "78ED" if a == 3 else "78C9", "001C", "C880",
                 "01E1", "CDE1" if a == 3 else "0001"]
            ps = "%08X" % (0x10F9 if a == 3 else 0x10E0)
        else:
            v, ps = ["0000"] * 6, "00000000"
        want = " ".join(v) + " hi 0000 psrp %s n 1" % ps
        if r.field(0, "a%02d" % a) != want:
            rows_ok = False
    sc = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == len("scan 0 31\n") and rows_ok
          and r.field(0, "mdio_rd") == "202" and len(sc) == 192
          and [s[1] for s in sc] == [rd(a, x) for a in range(32)
                                     for x in range(6)]
          and all(s[2] == 1 for s in sc) and r.stat(0, "outside") == "0"
          and r.stat(0, "psrp_rd") == "5" and r.stat(0, "psrp_insec") == "0"
          and r.stat(0, "psrp_bad") == "0" and r.stat(0, "mutex_viol") == "0"
          and r.field(0, "scanned") == "FFFFFFFF j 4242")
    yield "K6", ok, "rows %s rd %s" % (rows_ok, r.field(0, "mdio_rd"))

    # K7 the bound's positive control
    r = track(Run(exe, PROBED + ["set busy_post 3", "w bound 0", "w scan 5 5",
                                 "r", "set busy_post 0", "w bound 10000",
                                 "w scan 5 5", "r"]))
    ok = (r.rc == 0
          and r.field(0, "a05") == "E145 E016 E016 E145 E016 E016 hi 0000 "
                                   "psrp 00000000 n 1"
          and r.field(0, "mdio_to") == "2 busy 4 retry 0"
          and r.field(0, "mdio_rd") == "12"
          and r.field(1, "a05") == "0000 0000 0000 0000 0000 0000 hi 0000 "
                                   "psrp 00000000 n 2"
          and r.field(1, "mdio_to") == "2 busy 4 retry 0"
          and r.field(1, "mdio_rd") == "18")
    yield "K7", ok, "a05 %s | %s" % (r.field(0, "a05") if r.pages else "-",
                                     r.field(0, "mdio_to") if r.pages else "-")

    # K8 pread refusals beside their neighbours
    einval, eagain = -ERRNO["EINVAL"], -ERRNO["EAGAIN"]
    r = track(Run(exe, PROBED + [
        "w pread 5 1 16", "w pread 4 1 16",          # address
        "w pread 0 2 16", "w pread 0 7 16", "w pread 0 1 16",  # page
        "w pread 0 1 31", "w pread 0 1 30",          # register
        "w pread 0 1", "w pread 0  1", "w pread 0 1 16x",  # malformed
        "stat", "w bound 9999", "w pread 0 1 16", "w pread 0 0 16",
        "stat", "r", "w bound 10000", "w pread 0 0 16", "stat"]))
    rcs = [r.op(i) for i in range(3, len(r.ops))]
    n1 = int(r.stat(0, "nstores")) if r.stats else -1
    n2 = int(r.stat(1, "nstores")) if len(r.stats) > 1 else -1
    prs = [ln for ln in r.pages[0][0].split("\n") if ln.startswith("pr ")] \
        if r.pages else []
    ok = (r.rc == 0
          and rcs == [einval, len("pread 4 1 16\n"), einval, einval,
                      len("pread 0 1 16\n"), einval, len("pread 0 1 30\n"),
                      einval, einval, einval, len("bound 9999\n"), eagain,
                      eagain, len("bound 10000\n"), len("pread 0 0 16\n")]
          and n1 == 10 + 3 * 6 and n2 == n1 and len(prs) == 3
          and r.field(0, "refused") == "0 wr_refused 0 again 2"
          and int(r.stat(2, "nstores")) == n2 + 1)
    yield "K8", ok, "rcs %s stores %d/%d prs %d" % (rcs, n1, n2, len(prs))

    # K9 pread a 1 r
    r = track(Run(exe, PROBED + ["stat", "w pread 2 1 19", "stores", "r",
                                 "stat"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == len("pread 2 1 19\n")
          and [x[1] for x in s] == [rd(2, 31), wr(2, 31, 1), rd(2, 31),
                                    rd(2, 19), wr(2, 31, 0), rd(2, 31)]
          and all(x[2] == 1 for x in s) and len({x[3] for x in s}) == 1
          and r.field(0, "pr") == "a2 p1 r19 v %d p0 0 ps 1 p1 0 rs 0 rt 0 "
                                  "rc 0 psrp 000010E0 000010E0" % 0x5400
          and int(r.stat(1, "mutex_locks")) == int(r.stat(0, "mutex_locks")) + 1
          and r.stat(1, "mutex_viol") == "0" and r.stat(1, "psrp_insec") == "0"
          and r.stat(1, "page31") == "0,0,0,0,0" and r.stat(1, "illegal") == "0"
          and r.stat(1, "imbalance") == "0" and r.stat(1, "depth") == "0"
          and r.field(0, "mdio_wr") == "2" and r.field(0, "dirty") == "0"
          and r.stat(1, "mark") == "RLXFW-MD3=00020113")
    yield "K9", ok, "stores %s pr %s" % (["%08X" % x[1] for x in s],
                                         r.field(0, "pr") if r.pages else "-")

    # K10 page 0 control
    r = track(Run(exe, PROBED + ["w pread 2 0 16", "stores", "r"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == len("pread 2 0 16\n")
          and [x[1] for x in s] == [rd(2, 16)]
          and r.field(0, "pr") == "a2 p0 r16 v %d p0 0 ps 0 p1 0 rs 1 rt 0 "
                                  "rc 0 psrp 000010E0 000010E0" % 0x0210
          and r.field(0, "mdio_wr") == "0")
    yield "K10", ok, "pr %s" % (r.field(0, "pr") if r.pages else "-")

    # K11 not on page 0: nothing written
    r = track(Run(exe, PROBED + ["set page31 2 1", "w pread 2 1 19", "stores",
                                 "r", "stat"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == -ERRNO["EPROTO"]
          and [x[1] for x in s] == [rd(2, 31)]
          and r.field(0, "pr", ) == "a2 p1 r19 v 0 p0 1 ps 0 p1 0 rs 1 rt 0 "
                                    "rc -71 psrp 000010E0 000010E0"
          and r.field(0, "mdio_wr") == "0" and r.field(0, "dirty") == "0"
          and r.stat(0, "page31") == "0,0,1,0,0")
    yield "K11", ok, "pr %s" % (r.field(0, "pr") if r.pages else "-")

    # K12 register 31 reads 0 whatever it holds
    r = track(Run(exe, PROBED + ["set reg31r 0", "w pread 2 1 19", "stores",
                                 "r", "stat"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == -ERRNO["EPROTO"] and len(s) == 6
          and r.field(0, "pr") == "a2 p1 r19 v %d p0 0 ps 0 p1 0 rs 0 rt 0 "
                                  "rc -71 psrp 000010E0 000010E0" % 0x5400
          and r.field(0, "dirty") == "0" and r.stat(0, "page31") == "0,0,0,0,0")
    yield "K12", ok, "pr %s" % (r.field(0, "pr") if r.pages else "-")

    # K13 restore refused busy once, stored on the retry
    r = track(Run(exe, PROBED + ["set post_next 3 %d" % (2 * (B + 1)),
                                 "w pread 2 1 19", "stores", "r", "stat"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == -ERRNO["ETIMEDOUT"]
          and [x[1] for x in s] == [rd(2, 31), wr(2, 31, 1), rd(2, 31),
                                    rd(2, 19), wr(2, 31, 0), rd(2, 31)]
          and len({x[3] for x in s}) == 1
          and r.field(0, "pr") == "a2 p1 r19 v -145 p0 0 ps 1 p1 0 rs 0 rt 1 "
                                  "rc -145 psrp 000010E0 000010E0"
          and r.field(0, "mdio_to") == "1 busy 1 retry 1"
          and r.field(0, "dirty") == "0" and r.stat(0, "page31") == "0,0,0,0,0")
    yield "K13", ok, "pr %s | %s" % (r.field(0, "pr") if r.pages else "-",
                                     r.field(0, "mdio_to") if r.pages else "-")

    # K14 restore refused busy twice: dirty, and the refusal after it
    for tag, extra in (("K14", []), ("K14b", ["set reg31r 0"])):
        r = track(Run(exe, PROBED + extra + [
            "set post_next 3 %d" % (3 * (B + 1)), "w pread 2 1 19",
            "stores", "r", "stat", "w pread 0 1 16", "w pread 0 0 16",
            "stores", "r"]))
        s = r.stores[1] if len(r.stores) > 1 else []
        after = r.stores[2] if len(r.stores) > 2 else [None]
        ps_p1 = "ps 0 p1 0" if extra else "ps 1 p1 1"
        ok = (r.rc == 0 and r.op(3) == -ERRNO["EIO"]
              and [x[1] for x in s] == [rd(2, 31), wr(2, 31, 1), rd(2, 31),
                                        rd(2, 19), rd(2, 31)]
              and r.field(0, "pr") == "a2 p1 r19 v -145 p0 0 %s "
                                      "rs -16 rt 1 rc -5 psrp 000010E0 "
                                      "000010E0" % ps_p1
              and r.field(0, "dirty") == "3"
              and r.field(0, "mdio_to") == "1 busy 2 retry 1"
              and r.op(4) == -ERRNO["EIO"]
              and r.op(5) == -ERRNO["EIO"] and after == []
              and len([ln for ln in r.pages[1][0].split("\n")
                       if ln.startswith("pr ")]) == 1)
        yield tag, ok, "pr %s" % (r.field(0, "pr") if r.pages else "-")

    # K19 stuck hardware (before K15, which reads every case's sections)
    r = track(Run(exe, ["init", UNLOCK, "set stuck 1", "w probe", "r", "stat",
                        "w probe", "w pread 0 1 16", "r", "stat"]))
    phys = [r.field(0, "phy%d" % a) for a in range(5)] if r.pages else []
    ok = (r.rc == 0 and r.op(2) == 6 and r.field(0, "bus") == "1 reg_rc 0"
          and phys == ["id - rc -5 xrc -16"] * 5
          and r.field(0, "mdio_rd") == "0"
          and r.field(0, "mdio_to") == "0 busy 5 retry 0"
          and r.stat(0, "nstores") == "0"
          and r.op(3) == -ERRNO["EEXIST"] and r.op(4) == -ERRNO["EBUSY"]
          and r.field(1, "pr") == "a0 p1 r16 v 0 p0 -16 ps 0 p1 0 rs 1 rt 0 "
                                  "rc -16 psrp 000010E0 000010E0"
          and int(r.stat(1, "dmax")) == B)
    yield "K19", ok, "phys %s" % phys

    # K20 the select timed out: the restore still stored and verified
    r = track(Run(exe, PROBED + ["set post_next 1 %d" % (B + 1 + 5),
                                 "w pread 2 1 19", "stores", "r", "stat"]))
    s = r.stores[1] if len(r.stores) > 1 else []
    ok = (r.rc == 0 and r.op(3) == -ERRNO["ETIMEDOUT"]
          and [x[1] for x in s] == [rd(2, 31), wr(2, 31, 1), wr(2, 31, 0),
                                    rd(2, 31)]
          and r.field(0, "pr") == "a2 p1 r19 v -145 p0 0 ps -145 p1 0 rs 0 "
                                  "rt 0 rc -145 psrp 000010E0 000010E0"
          and r.field(0, "dirty") == "0" and r.stat(0, "page31") == "0,0,0,0,0")
    yield "K20", ok, "pr %s" % (r.field(0, "pr") if r.pages else "-")

    # K15 IRQs-off time, over every section of every case so far
    cb = comment_irq_bound(block)
    ok = (cb == (13, 130) and dmax_seen and max(dmax_seen) <= cb[0] * B
          and max(dmax_seen) >= 3 * B)
    yield "K15", ok, "comment %s, max section %s us over %d readings" % (
        cb, max(dmax_seen) if dmax_seen else "-", len(dmax_seen))

    # K16 the widest page
    r = Run(exe, ["init", "widest", "r"])
    text, n = r.pages[0] if r.pages else ("", -1)
    lines = text.split("\n")
    first = next((i for i, ln in enumerate(lines) if ln.startswith("a00 ")), None)
    rows = [ln for ln in lines if re.match(r"a\d\d ", ln)]
    head = sum(len(ln) + 1 for ln in lines[:first]) if first is not None else -1
    rowlen = {len(ln) + 1 for ln in rows}
    trailer = len(lines[-2]) + 1 if len(lines) > 1 else -1
    fig = comment_figures(block)
    ok = (r.rc == 0 and len(rows) == 32 and len(rowlen) == 1
          and fig == (head, rowlen.pop() if len(rowlen) == 1 else -1, trailer, n)
          and n <= PAGE and lines[-2].startswith("jiffies 4294967295")
          and n == len(text))
    yield "K16", ok, "comment %s, measured head %d rows %d trailer %d total %d" % (
        fig, head, len(rows), trailer, n)

    # K17 cat issues no MDIO command
    r = track(Run(exe, PROBED + ["w scan 0 4", "stat", "r", "r", "stat"]))
    ok = (r.rc == 0 and r.stat(0, "nstores") == r.stat(1, "nstores")
          and len(r.pages) == 2 and r.pages[0] == r.pages[1]
          and r.field(1, "mdio_rd") == "40")
    yield "K17", ok, "stores %s -> %s" % (r.stat(0, "nstores") if r.stats else "-",
                                          r.stat(1, "nstores") if len(r.stats) > 1 else "-")

    # K18 the bus's write op
    r = track(Run(exe, PROBED + ["buswrite 0 0 4660", "r", "stat"]))
    ok = (r.rc == 0 and r.op(3) == -ERRNO["EPERM"]
          and r.field(0, "refused") == "0 wr_refused 1 again 0"
          and r.stat(0, "nstores") == "10" and r.field(0, "mdio_wr") == "0")
    yield "K18", ok, "ops %s" % [x[1] for x in r.ops]

    # K21 MDCIOSR 30:16 and the mark values
    r = track(Run(exe, PROBED + ["set hibits 0x40000000", "w scan 0 0",
                                 "set hibits 0", "w scan 5 7", "r", "stat"]))
    ok = (r.rc == 0 and r.field(0, "hi_or") == "40000000"
          and (r.field(0, "a00") or "").endswith("hi 4000 psrp 000010E0 n 1")
          and (r.field(0, "a05") or "").endswith("hi 0000 psrp 00000000 n 1")
          and r.stat(0, "mark") == "RLXFW-MD2=00000705"
          and r.field(0, "scanned") == "000000E1 j 4242")
    yield "K21", ok, "hi_or %s a00 %s" % (r.field(0, "hi_or") if r.pages else "-",
                                          r.field(0, "a00") if r.pages else "-")

    # K22 the /proc entry failing at init
    r = Run(exe, ["set pdefail 1", "init", "stat"])
    ok = (r.rc == 0 and r.op(0) == 0 and r.stat(0, "mark") == "RLXFW-MD0-NOPROC"
          and r.stat(0, "marks") == "1" and r.stat(0, "pde") == "0"
          and r.stat(0, "nstores") == "0")
    yield "K22", ok, "mark %s" % (r.stat(0, "mark") if r.stats else "-")

    # K23 scan's and bound's refusals, each beside a permitted neighbour
    r = track(Run(exe, PROBED + [
        "w scan 5 4", "w scan 0 32", "w scan  3", "w scan 0 4x", "w scan 0",
        "w scan 3 3", "w bound 10001", "w bound -1", "w bound 5x",
        "w bound 0x10", "r", "w bound 10000", "w nonsense", "w probe ",
        "stat"]))
    rcs = [r.op(i) for i in range(3, len(r.ops))]
    ok = (r.rc == 0
          and rcs == [einval, einval, einval, einval, einval,
                      len("scan 3 3\n"), einval, einval, einval,
                      len("bound 0x10\n"), len("bound 10000\n"), einval,
                      einval]
          and r.field(0, "bound") == "16"
          and r.stat(0, "nstores") == str(10 + 6)
          and r.field(0, "scanned") == "00000008 j 4242")
    yield "K23", ok, "rcs %s" % rcs


def build(block, version, work, tag):
    """Compile the harness around `block`; (exe or None, compiler output)."""
    d = os.path.join(work, tag)
    inc = os.path.join(d, "include", "linux")
    os.makedirs(inc, exist_ok=True)
    # The block's three kernel includes: the harness above has already
    # defined everything they would, so each is an empty file here.
    for h in ("err.h", "mutex.h", "phy.h"):
        with open(os.path.join(inc, h), "w", encoding="utf-8") as fh:
            fh.write("/* mdiocheck: supplied by the harness */\n")
    bpath = os.path.join(d, "block.c")
    with open(bpath, "w", encoding="utf-8") as fh:
        fh.write(block)
    h = (HARNESS.replace("@BLOCK@", bpath).replace("@VERSION@", version)
         .replace("PAGE_SZ", str(PAGE)))
    hpath = os.path.join(d, "harness.c")
    with open(hpath, "w", encoding="utf-8") as fh:
        fh.write(h)
    exe = os.path.join(d, "harness")
    p = subprocess.run(["gcc"] + CFLAGS + ["-I", os.path.join(d, "include"),
                                           "-o", exe, hpath],
                       capture_output=True, text=True)
    return (exe if p.returncode == 0 else None), p.stdout + p.stderr


def evaluate(block, version, work, tag):
    exe, out = build(block, version, work, tag)
    if exe is None:
        return None, out
    return {name: (ok, det) for name, ok, det in cases(exe, block, version)}, ""


# Each mutant: (id, what it breaks, the case that must go red, old, new).
MUTANTS = [
    ("M1", "probe's bound guard removed", "K4",
     "\tif (rtl819x_mdio_bound != RTL819X_MDIO_BOUND) {\n\t\trtl819x_mdio_n_again++;\n\t\treturn -EAGAIN;\n\t}\n\tbus = mdiobus_alloc();",
     "\tbus = mdiobus_alloc();"),
    ("M2", "pread's bound guard removed", "K8",
     "\tif (rtl819x_mdio_bound != RTL819X_MDIO_BOUND) {\n\t\trtl819x_mdio_n_again++;\n\t\treturn -EAGAIN;\n\t}\n\tif (rtl819x_mdio_dirty)",
     "\tif (rtl819x_mdio_dirty)"),
    ("M3", "the restore is not retried", "K13",
     "\tif (p->rs == -EBUSY) {\t/* never stored: one more full bound */",
     "\tif (0) {"),
    ("M4", "dirty ignores a restore that was never stored", "K14b",
     "\tif (p->rs == -EBUSY || p->p1 != 0) {", "\tif (p->p1 != 0) {"),
    ("M5", "pread accepts pages up to 7", "K8",
     "v[1] > RTL819X_MDIO_PAGE ||", "v[1] > 7 ||"),
    ("M6", "the -EAGAIN refusal spends the one shot", "K4",
     "\t\trtl819x_mdio_n_again++;\n\t\treturn -EAGAIN;\n\t}\n\tbus = mdiobus_alloc();",
     "\t\trtl819x_mdio_n_again++;\n\t\trtl819x_mdio_reg_rc = -EAGAIN;\n\t\treturn -EAGAIN;\n\t}\n\tbus = mdiobus_alloc();"),
    ("M7", "the bus's read op stores with IRQs on", "K6",
     "\t\tlocal_irq_save(flags);\n\t\tv = rtl819x_mdio_xfer(0, a, r, 0);\n\t\tlocal_irq_restore(flags);",
     "\t\tflags = 0;\n\t\tv = rtl819x_mdio_xfer(0, a, r, 0);\n\t\t(void)flags;"),
    ("M8", "pread's restore in a second IRQs-off section", "K9",
     "\tp->rs = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);  /* always */",
     "\tlocal_irq_restore(flags);\n\tlocal_irq_save(flags);\n\tp->rs = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);"),
    ("M9", "a cat issues an MDIO read", "K17",
     "\tlen += sprintf(page + len, \"version %s\\n\", RTL819X_SW_VERSION);",
     "\tif (rtl819x_mdio_bus)\n\t\t(void)rtl819x_mdio_bus->read(rtl819x_mdio_bus, 0, 1);\n\tlen += sprintf(page + len, \"version %s\\n\", RTL819X_SW_VERSION);"),
    ("M10", "registration scans every address", "K4",
     "\tbus->phy_mask = ~0u;", "\tbus->phy_mask = 0;"),
    ("M11", "the switch's token opens this gate", "K3",
     "#define RTL819X_MDIO_TOKEN\t\"mdio-i-mean-it\"",
     "#define RTL819X_MDIO_TOKEN\t\"i-mean-it\""),
    ("M12", "the bus's write op permits", "K18",
     "\trtl819x_mdio_n_wr_refused++;\n\treturn -EPERM;",
     "\trtl819x_mdio_n_wr_refused++;\n\treturn 0;"),
    ("M13", "the transaction's rc is not kept", "K19",
     "\t\trtl819x_mdio_xrc[a] = v < 0 ? v : 0;", "\t\t(void)v;"),
    ("M14", "a busy pre-check reported as a timeout", "K7",
     "\t\t\trtl819x_mdio_n_busy++;\n\t\t\treturn -EBUSY;",
     "\t\t\trtl819x_mdio_n_busy++;\n\t\t\treturn -ETIMEDOUT;"),
    ("M15", "the row budget cuts rows", "K16",
     "#define RTL819X_MDIO_PAGE_BUDGET\t3900",
     "#define RTL819X_MDIO_PAGE_BUDGET\t3000"),
    ("M16", "no restore after a failed select", "K20",
     "\tp->rs = rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);  /* always */",
     "\tp->rs = rc ? RTL819X_MDIO_NOXFER : rtl819x_mdio_xfer(1, a, RTL819X_MDIO_PAGEREG, 0);"),
    ("M17", "the page-0 check before the select removed", "K11",
     "\tif (p->p0 != 0) {\t/* not on page 0, or unreadable: write nothing */",
     "\tif (p->p0 < 0) {"),
    ("M18", "scan reads a PSRP past port 4", "K6",
     "\t\tw->psrp = a < RTL819X_MDIO_NPHY ?", "\t\tw->psrp = a < 8 ?"),
    ("M19", "a write command without its COMMAND bit", "K9",
     "(write ? RTL819X_MDIO_WRITE | val : 0)", "(write ? val : 0)"),
    ("M20", "a numeric field need not start with a digit", "K8",
     "\t\tif (*s < '0' || *s > '9')\n\t\t\treturn -EINVAL;\n", ""),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--keep", help="keep the build directory here")
    ap.add_argument("--no-mutants", action="store_true")
    a = ap.parse_args()
    if not shutil.which("gcc"):
        die("no gcc on PATH: this tool compiles the block with the host's gcc")
    if not os.path.isfile(a.source):
        die("no such file: %s" % a.source)
    block, version = extract(open(a.source, encoding="utf-8").read())
    work = a.keep or tempfile.mkdtemp(prefix="mdiocheck-")
    os.makedirs(work, exist_ok=True)
    print("mdiocheck 1.0")
    print("  source  %s  (block %d lines, version %r)"
          % (a.source, block.count("\n"), version))
    try:
        exe, out = build(block, version, work, "M0")
        if exe is None:
            print("  FAIL K0  the block does not compile in the harness:")
            print(out)
            return 1
        probe = Run(exe, [])
        eok = probe.errno == ERRNO and probe.bound == 10000
        print("  %s K0  compiles with %s; errno %s; bound %s"
              % ("ok  " if eok else "FAIL", " ".join(CFLAGS),
                 "= arch/rlx's" if probe.errno == ERRNO else probe.errno,
                 probe.bound))
        fails = 0 if eok else 1
        results = {}
        for name, ok, det in cases(exe, block, version):
            results[name] = ok
            print("  %s %-4s %s" % ("ok  " if ok else "FAIL", name, det))
            fails += 0 if ok else 1
        print("RESULT: %d case(s), %d failed" % (len(results) + 1, fails))
        if fails:
            return 1
        if a.no_mutants:
            return 0
        print("")
        print("mutants (M0 is the unmutated block through the same path)")
        m0, why = evaluate(block, version, work, "M0b")
        if m0 is None or not all(ok for ok, _ in m0.values()):
            print("  FAIL M0   the unmutated copy is not green: no kill counts")
            return 1
        print("  ok   M0   unmutated copy green on %d cases" % len(m0))
        survivors = 0
        for mid, what, named, old, new in MUTANTS:
            n = block.count(old)
            if n != 1:
                print("  FAIL %-4s anchor occurs %d times (%s)" % (mid, n, what))
                survivors += 1
                continue
            res, why = evaluate(block.replace(old, new), version, work, mid)
            if res is None:
                print("  FAIL %-4s does not compile (%s): %s"
                      % (mid, what, why.strip().splitlines()[-1:] or ""))
                survivors += 1
                continue
            red = sorted(k for k, (ok, _) in res.items() if not ok)
            killed = named in red
            survivors += 0 if killed else 1
            print("  %s %-4s %-46s named %-5s red %s"
                  % ("ok  " if killed else "FAIL", mid, what, named,
                     ",".join(red) or "-"))
        print("RESULT: %d mutant(s), %d killed by the case named for them, "
              "%d survived" % (len(MUTANTS), len(MUTANTS) - survivors,
                               survivors))
        return 1 if survivors else 0
    finally:
        if not a.keep:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
