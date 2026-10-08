#!/usr/bin/env python3
"""mdiocheck -- rtl819x-switch 1.3's MDIO block, 1.4's `phyif` block, 1.5's
`init` verb and `reset` guard and 1.6's `vlan` verb, compiled and driven on
the host.

WHAT IT CHECKS, AND WHY IT CAN
------------------------------
`R6b-7` appended one block to `rtl819x-switch.c`: the bus's read and write
ops, `probe`, `scan`, `pread`, `bound`, the gate, and /proc/rtl819x-mdio.
`R6b-10` appended a second after it (1.4): arm II's one write class,
`EnablePHYIf` set in PCRP0-PCRP4, behind its own token.  `R6b-8` 8d appended
a third (1.5): `init`, 1.4's port loop under the switch's own unlock, and the
guard that refuses `reset full`/`reset vendor` while CPUICR has TXCMD or
RXCMD set.  `R6c` appended a fourth (1.6): `vlan`, which writes the VLAN
group -- VLAN slot 8, every other VLAN and netif slot empty, PVCR0-3 and
FFCR -- through the TACI block, after verifying four words it never writes.
This tool cuts all four out of the driver UNCHANGED (from the 1.3 banner to
the end of the file) and
compiles them with the host's gcc in the kernel's dialect
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
    arch/rlx/include/asm/errno.h:98);
  * for 1.4: the switch's one read path and one guarded write path, as the
    driver writes them above the cut, over a PCRP0-PCRP8 model whose
    default is the post-`J` state (nn7F0038 on 0-4, 量 C9-SW0), with two
    faults per port -- bit 0 does not stick, or bit 3 flips on a store --
    and every PCRP access logged with whether IRQs were off and in which
    section;
  * for 1.5: a CPUICR word at 0xB8010000 that only the direct KSEG1 load
    reaches (every load logged, `C`, in the same access log), the switch
    handler's `reset` branch as the driver writes it above the cut, and a
    stub for rtl819x_sw_do_reset -- also above the cut -- that records each
    call and its recipe (`X`) and returns a scripted rc.  Any store the
    guard made would be a `W` in the log or a harness exit;
  * for 1.6: the nine ALE and VLAN registers it reads or stores, the TACI
    block (SWTACR, SWTASR, SWTAA, TCR0-7) as an engine -- a command runs for
    a scripted number of SWTACR loads, or never, then copies TCR0..TCR7 to
    the slot SWTAA names -- SWTCR0 with bit 19 reading 1 and bit 18 read/
    write (or scripted not to set, or not to clear), and the VLAN and netif
    tables behind the window at 0xBB000000, each window load logged (`T`).
    The default is the flash path (量 bench/2026-10-08b); the RAM path's
    group carries a SYNTHETIC netif slot 0.  A protocol slip -- a command
    other than 9, one started with STOP_TLU clear, a TACI store or a
    STOP_TLU clear while one runs, an SWTAA outside both tables, a store to
    a verified word -- is counted for the cases to assert, and faults are
    scripted: busy, stuck, STOP_TLU_STA never set, a corrupted or doubled
    copy, a register that does not stick, a torn window read.  The block is
    also compiled a second time with -DCONFIG_RTL_819X_SWCORE.  The access
    log holds 65,536 entries and the harness EXITS 8 when it is full, so an
    overflow fails every case of that run rather than truncating a dump.

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
  1.4, `phyif` (the write handler's fall-through and its page lines):
  K24  boot: the six lines, and 1.5's `init` line after them, byte for byte
       (rc 1: never reached, never called), and a cat reads no register
  K25  the class token absent: `phyif all`, `phyif 0` -EPERM, counted, no
       PCRP access
  K26  the token: the switch's `unlock i-mean-it`, a near miss and a doubled
       space do not open it; `unlock phyif-i-mean-it` does; `lock phyif`
       closes it
  K27  `phyif all` from the post-`J` state: exactly R pre, W pre|1, R for
       ports 0..4 in order, each port's three in one IRQs-off section of its
       own; the lines, the mark 00001F1F, the model; a second cat reads nothing
  K28  `phyif 3` alone: one port's three accesses; the previous verb's
       results do not survive into this verb's lines
  K29  ports 5, 6, 8, 9 and fifteen malformed or unknown forms -EINVAL with no
       access, each beside a permitted neighbour
  K30  bit 0 already set: one read, no store (`already`)
  K31  a word without the port's ExtPHYID: -EPROTO, no store, and `phyif all`
       stops at that port
  K32  bit 0 does not stick: -EIO (`rbfail`), and `phyif all` stops there
  K33  another bit moved on the store: -EIO although bit 0 stuck
  K34  the switch locked: the store is rtl819x_sw_wr's to refuse (-EPERM,
       `n_refused`), after the one pre-read
  K35  64 drawn pre-read words: the word stored is the word read with bit 0
       set, and nothing else differs
  K36  the lines at their widest against the block comment's figures
  1.5, `init` and the `reset` guard (1.4's handler falls through to 1.5):
  K37  the switch locked: `init` -EPERM, counted in the `init` line, no
       register read -- also with the phyif class token unlocked
  K38  `init` from the post-`J` state: R pre, W pre|1, R for ports 0..4 in
       order, each port in one IRQs-off section of its own; the phyifN
       lines, the phyif counters, the `init` line, the mark 00001F1F, no
       MDIO store and no reset; a second cat reads nothing
  K39  `init` on the vendor-set state (bit 0 set on all five): five reads,
       no store, `already` 5, mark 0000001F
  K40  a word without its port's ExtPHYID: `init` stops there (-EPROTO),
       and the results of the `phyif all` before it do not survive
  K41  a bit 0 that does not stick: `init` stops there (-EIO)
  K42  the phyif token neither needed nor enough: over (switch, phyif)
       locked/unlocked, `init` reaches the ports exactly when the switch is
       unlocked
  K43  ten malformed forms -EINVAL with no access, beside a permitted `init`
  K44  the guard: CPUICR with TXCMD, RXCMD, both (C4000000) -- `reset full`
       and `reset vendor` -EBUSY, counted, one CPUICR load each, no switch
       read, no store, rtl819x_sw_do_reset never called
  K45  the guard permits at 04000000 (after `disarm`) and at 0: one load,
       then rtl819x_sw_do_reset with the verb's recipe, its rc returned
  K46  the `init` line at its widest against the block comment's figures,
       and the page's running total through 1.2, 1.4 and 1.5
  1.6, `vlan` (1.5's handler falls through to 1.6):
  K47  the switch locked: -EPERM, counted, no access at all -- also with
       the phyif class token unlocked; a refusal after a call that stored
       shows none of that call's fields
  K48  the flash path: every access in order (the four verified words, all
       24 slots and PVCR0-3/FFCR read before any store, VLAN slot 8's table
       write step by step, PVCR0-3 and FFCR stored and read back, the
       re-read); steps (1)-(10) alone with IRQs off, in one section; 17
       stores, 81 reads, 784 window loads; the end state is the RAM path's
       group minus netif slot 0; one command, 9, under STOP_TLU
  K49  the RAM path: netif slot 0 cleared, 12 stores, nothing else stored
  K50  each verified word wrong in turn: -EPROTO after the four loads and
       nothing else, `vm` and `vr` naming it
  K51  a command that never completes: -ETIMEDOUT at (8) after 10,001
       polls, STOP_TLU cleared and read back, SWTASR read, nothing after
  K52  STOP_TLU_STA never set: -ETIMEDOUT at (3), STOP_TLU cleared and read
       back, no TCR, SWTAA or SWTACR store
  K53  a copy that differs from the entry: -EIO at (11), after the undo
  K54  bit 18 that does not clear: -EIO at (9), and the verb stops
  K55  a second `vlan`: no store, the re-read equal
  K56  -DCONFIG_RTL_819X_SWCORE: refused while locked, rc 0 unlocked, no
       access either way, the `vendor` line
  K57  the `vlan` line at its widest against the block comment's figures,
       and the page's running total through 1.6
  K58  a copy that also lands in the next slot: each slot's own read-back
       passes and the re-read refuses (-EIO, `final` 1, `at` 9)
  K59  bit 18 that does not read back set: recorded in `tlu`, not refused
  K60  the engine busy at (1): -EBUSY and nothing stored
  K61  the engine busy at the first read: -EBUSY, no window load, no store
  K62  a register store that does not stick: -EIO at (12), and the
       registers after it are not stored
  K63  slots that differ past their first word are written (all eight
       words compared)
  K64  SWTASR bit 0 set: recorded in `swtasr`, not refused
  K65  a torn window read is read again; ten torn reads are -EIO with
       nothing stored
  K66  a command busy for three polls: four polls, the same result, and no
       protocol slip
  K67  the engine busy at (4), once STOP_TLU is set: -EBUSY, STOP_TLU
       cleared and read back in the same IRQs-off section, no other store

M0..M82 then mutate a COPY of the block, one defect each, and require the case
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
answers that.  For 1.4: the switch's read and write paths and its handler's
CR/LF stripping are the harness's transcription of the driver above the cut,
not the driver's own code; and what the silicon does with bit 0 -- whether
it sticks, whether the link follows -- is the bench's.  For 1.5: the
`reset` branch of the switch's handler is transcribed, rtl819x_sw_do_reset
is a stub, and CPUICR is a variable -- nothing here says what a reset does
to a running DMA engine, or whether the NIC re-arms between the guard's
load and the reset; and /init's `init` is config/rlxfw-init.sh's, which
this tool does not read.  For 1.6: the engine is a model of the two vendor
readings the block itself was written from, so a protocol they both get
wrong passes here; whether this die takes eight TCRs or the type's size,
whether bit 18 reads back, how long a command takes and what a group with
every netif slot empty forwards are the bench's.  A mutant that removes a
bound is not run: it would hang the harness rather than turn a case red.

Needs gcc and nothing else: no toolchain, no $FWRE_WORK, no device.
    mdiocheck.py [--source PATH] [--keep DIR] [--no-mutants]
"""
import argparse
import os
import random
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
/* 1.5: the direct KSEG1 load's spelling, and three of the driver's own
 * defines from above the cut, which only the mutants use (SSIR, FULL_RST
 * and the switch window's physical base, rtl819x-switch.c:123-134). */
#define __iomem
#define KSEG1ADDR(a) ((unsigned long)(a) | 0xA0000000UL)
#define RTL819X_SW_PHYS 0x1B800000
#define RTL819X_SW_SSIR 0x4204
#define RTL819X_SW_FULL_RST (1u << 2)

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
/* 1.6: the ALE and VLAN registers `vlan` reads or stores, the TACI block and
 * the VLAN (type 6, 16 slots at 0xBB060000) and netif (type 4, 8 slots at
 * 0xBB040000) tables, 32 bytes a slot.  The registers are reached only
 * through the switch's two paths (transcribed below), the tables only
 * through the block's window load (fake_readl).  The default is the flash
 * path, 量 bench/2026-10-08b (A02, A05, A06, A08); `set vgstate 1` loads the
 * RAM path's group (量 bench/2026-09-28/M2-VV, bench/2026-10-04/PER-SW)
 * with a SYNTHETIC netif slot 0 -- valid, VID 8, MTU 1500, macMask 7,
 * address 02:00:00:00:00:01, locally administered and no unit's: the
 * loader's own words carry this unit's address and are not copied here.
 * SWTCR0 bit 19 reads 1 (量: every reading on record) and ignores stores;
 * bit 18 is read/write, or scripted not to set or not to clear.  SWTACR
 * reads the stored command while one runs and 0 once it is done (量 PER-SW:
 * 0 after the loader's table writes).  A command is done after `vgbusy`
 * more SWTACR loads, or never (`vgstuck`), and then copies TCR0..TCR7 to
 * the slot SWTAA names (`vgcorrupt` XORs word 0; `vgghost` copies to a
 * second slot too).  Counted for the cases: a command that is not 9, one
 * started with STOP_TLU clear (`nostop`), a TACI store or a STOP_TLU clear
 * while one runs (`viol`), an SWTAA outside both tables (`badaa`), and any
 * store to a verified word or to SWTASR (`illegal`, not applied). */
static u32 vg_swtcr0, vg_plitimr = 0x07FAC688u, vg_ffcr, vg_vcr0 = 0x1FFu;
static u32 vg_pbvcr0, vg_swtacr, vg_swtasr, vg_swtaa, vg_tcr[8];
static u32 vg_pvcr[5] = { 0x00010001u, 0x00010001u, 0x00010001u,
			  0x00010001u, 0x00000001u };
static u32 vg_vlan[16][8], vg_netif[8][8];
static int vg_sta = 1, vg_nostick18, vg_noclear18, vg_stuck, vg_ghost;
static int vg_running, vg_nostick_off = -1;
static long vg_busy, vg_left, vg_busy_from = -1, vg_busy_n, vg_nld, vg_tear;
static u32 vg_tearx, vg_corrupt;
static int vg_starts, vg_viol, vg_nostop, vg_badaa, vg_badcmd, vg_illegal;
static int vg_winld;

static void vg_state(int ram)
{
	int i, k;

	vg_swtcr0 = 0;
	vg_plitimr = 0x07FAC688u;
	vg_vcr0 = 0x1FFu;
	vg_pbvcr0 = vg_swtacr = vg_swtasr = vg_swtaa = 0;
	for (k = 0; k < 8; k++)
		vg_tcr[k] = 0;
	for (i = 0; i < 16; i++)
		for (k = 0; k < 8; k++)
			vg_vlan[i][k] = 0;
	for (i = 0; i < 8; i++)
		for (k = 0; k < 8; k++)
			vg_netif[i][k] = 0;
	for (i = 0; i < 4; i++)
		vg_pvcr[i] = ram ? 0x00080008u : 0x00010001u;
	vg_pvcr[4] = 1;
	vg_ffcr = ram ? 3u : 0u;
	if (ram) {
		vg_vlan[8][0] = 0x00807E3Fu;
		vg_netif[0][0] = 0x00002011u;	/* SYNTHETIC: see above */
		vg_netif[0][1] = 0x00400000u;
		vg_netif[0][2] = 0x9C000000u;
		vg_netif[0][3] = 0x000000BBu;
	}
}
static void vg_copy(u32 a, int d)
{
	unsigned int t = (a >> 16) & 0xFFu;
	int s = (int)((a & 0xFFFFu) >> 5), k;
	u32 *dst;

	if ((a & 0xFF000000u) != 0xBB000000u || (a & 0x1Fu) ||
	    !((t == 6 && s < 16) || (t == 4 && s < 8))) {
		vg_badaa++;
		return;
	}
	s += d;
	if ((t == 6 && s >= 16) || (t == 4 && s >= 8))
		return;			/* a second slot past the end: none */
	dst = t == 6 ? vg_vlan[s] : vg_netif[s];
	for (k = 0; k < 8; k++)
		dst[k] = vg_tcr[k];
	if (!d)
		dst[0] ^= vg_corrupt;
}
static u32 vg_swtacr_ld(void)
{
	long i = vg_nld++;

	if (vg_busy_from >= 0 && i >= vg_busy_from &&
	    i < vg_busy_from + vg_busy_n)
		return vg_swtacr | 1u;
	if (vg_running && !vg_stuck) {
		if (vg_left > 0) {
			vg_left--;
		} else {
			vg_running = 0;
			vg_swtacr = 0;
			vg_copy(vg_swtaa, 0);
			if (vg_ghost)
				vg_copy(vg_swtaa, vg_ghost);
		}
	}
	return vg_swtacr;
}
/* 1, and the word, if `off` is one of 1.6's registers. */
static int vg_rd(unsigned int off, u32 *v)
{
	switch (off) {
	case 0x4418:
		*v = (vg_swtcr0 & ~(1u << 19)) | (vg_sta ? 1u << 19 : 0);
		return 1;
	case 0x4420:
		*v = vg_plitimr;
		return 1;
	case 0x4428:
		*v = vg_ffcr;
		return 1;
	case 0x4A00:
		*v = vg_vcr0;
		return 1;
	case 0x4A1C:
		*v = vg_pbvcr0;
		return 1;
	case 0x4D00:
		*v = vg_swtacr_ld();
		return 1;
	case 0x4D04:
		*v = vg_swtasr;
		return 1;
	case 0x4D08:
		*v = vg_swtaa;
		return 1;
	}
	if (off >= 0x4A08 && off <= 0x4A18 && !(off & 3)) {
		*v = vg_pvcr[(off - 0x4A08) / 4];
		return 1;
	}
	if (off >= 0x4D20 && off <= 0x4D3C && !(off & 3)) {
		*v = vg_tcr[(off - 0x4D20) / 4];
		return 1;
	}
	return 0;
}
/* 1 if `off` is one of 1.6's registers, which the store then reaches. */
static int vg_wr(unsigned int off, u32 v)
{
	u32 b18;

	switch (off) {
	case 0x4418:
		b18 = v & (1u << 18);
		if (b18 && vg_nostick18)
			b18 = 0;
		if (!b18 && vg_noclear18 && (vg_swtcr0 & (1u << 18)))
			b18 = 1u << 18;
		if (!b18 && (vg_swtcr0 & (1u << 18)) && vg_running)
			vg_viol++;
		vg_swtcr0 = (v & ~(3u << 18)) | b18;
		return 1;
	case 0x4428:
		if ((int)off != vg_nostick_off)
			vg_ffcr = v;
		return 1;
	case 0x4D00:
		if (vg_running)
			vg_viol++;
		vg_swtacr = v;
		if (v & 1u) {
			vg_starts++;
			if (v != 9u)
				vg_badcmd++;
			if (!(vg_swtcr0 & (1u << 18)))
				vg_nostop++;
			vg_running = 1;
			vg_left = vg_busy;
		}
		return 1;
	case 0x4D08:
		if (vg_running)
			vg_viol++;
		vg_swtaa = v;
		return 1;
	case 0x4A00:
	case 0x4A18:
	case 0x4A1C:
	case 0x4420:
	case 0x4D04:
		vg_illegal++;		/* never stored by design: not applied */
		return 1;
	}
	if (off >= 0x4A08 && off <= 0x4A14 && !(off & 3)) {
		if ((int)off != vg_nostick_off)
			vg_pvcr[(off - 0x4A08) / 4] = v;
		return 1;
	}
	if (off >= 0x4D20 && off <= 0x4D3C && !(off & 3)) {
		if (vg_running)
			vg_viol++;
		vg_tcr[(off - 0x4D20) / 4] = v;
		return 1;
	}
	return 0;
}
/* A script's direct setting of a register's model, for a start state. */
static void vg_set(unsigned int off, u32 v)
{
	if (off == 0x4418)
		vg_swtcr0 = v;
	else if (off == 0x4420)
		vg_plitimr = v;
	else if (off == 0x4428)
		vg_ffcr = v;
	else if (off == 0x4A00)
		vg_vcr0 = v;
	else if (off == 0x4A1C)
		vg_pbvcr0 = v;
	else if (off == 0x4D04)
		vg_swtasr = v;
	else if (off >= 0x4A08 && off <= 0x4A18 && !(off & 3))
		vg_pvcr[(off - 0x4A08) / 4] = v;
	else {
		printf("HARNESS vgreg: no register %04X in the model\n", off);
		exit(3);
	}
}
/* 1.5: CPUICR, 0xB8010000, reached only by a direct KSEG1 load.  Every
 * load goes into the PCRP access log as `C`, so its order against the
 * switch's reads and stores is visible. */
static u32 cpuicr;
static int cpuicr_rd;
static void pacc_log(char k, unsigned int off, u32 v);
static u32 fake_readl(unsigned int off)
{
	if (off == 0xB8010000u) {
		cpuicr_rd++;
		pacc_log('C', off, cpuicr);
		return cpuicr;
	}
	if ((off >= 0xBB060000u && off < 0xBB060200u) ||
	    (off >= 0xBB040000u && off < 0xBB040100u)) {
		u32 v;

		if (off & 3u) {
			fprintf(stderr, "harness: unaligned table load %08X\n",
				off);
			exit(9);
		}
		v = off >= 0xBB060000u ?
		    vg_vlan[(off - 0xBB060000u) >> 5][(off >> 2) & 7u] :
		    vg_netif[(off - 0xBB040000u) >> 5][(off >> 2) & 7u];
		if (vg_tear > 0) {
			vg_tear--;
			v ^= ++vg_tearx;
		}
		vg_winld++;
		pacc_log('T', off, v);
		return v;
	}
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
/* 1.4's PCRP model: PCRP0-PCRP8 at 0x4104 + 4n, reached only through the
 * switch's own read and write paths, which the harness supplies below.  The
 * default is the post-`J` state, nn7F0038 on ports 0-4 (量 C9-SW0), with
 * PCRP6/7 as read at the prompt and PCRP5 zero.  Two faults per port: bit 0
 * does not stick, or bit 3 flips on a store. */
static u32 pcrp[9] = { 0x007F0038, 0x047F0038, 0x087F0038, 0x0C7F0038,
		       0x107F0038, 0x00000000, 0x187F0038, 0x1C7F0038, 0 };
static int pcrp_nostick[9], pcrp_flip[9];
static int pcrp_rd, pcrp_rd_insec, pcrp_wr, pcrp_wr_insec, pcrp_illegal;
static int sw_rd_calls;		/* every call of the switch's read path */
static int rtl819x_sw_unlocked;
static unsigned long sw_n_writes, sw_n_refused;
struct pa { char k; unsigned int off; u32 v; int irq; int sec; };
/* 1.6: one `vlan` makes about 900 accesses, and a scripted bound about
 * 10,000 more.  A full log EXITS rather than drop entries, so an overflow
 * fails the run's every case instead of passing with a truncated dump. */
#define PACC_MAX 65536
static struct pa pacc[PACC_MAX];
static int n_pacc, n_pacc_dumped;

static void pacc_log(char k, unsigned int off, u32 v)
{
	if (n_pacc >= PACC_MAX) {
		fprintf(stderr, "harness: the access log is full (%d)\n", n_pacc);
		exit(8);
	}
	pacc[n_pacc].k = k;
	pacc[n_pacc].off = off;
	pacc[n_pacc].v = v;
	pacc[n_pacc].irq = irq_depth > 0;
	pacc[n_pacc].sec = irq_sections;
	n_pacc++;
}

static UNUSED u32 rtl819x_sw_rd(unsigned int off)
{
	u32 v;

	sw_rd_calls++;
	if (off >= 0x4104 && off <= 0x4124 && !(off & 3)) {
		v = pcrp[(off - 0x4104) / 4];
		pcrp_rd++;
		if (irq_depth)
			pcrp_rd_insec++;
		pacc_log('R', off, v);
		return v;
	}
	if (vg_rd(off, &v)) {		/* 1.6's registers */
		pacc_log('R', off, v);
		return v;
	}
	psrp_rd++;
	if (irq_depth)
		psrp_insec++;
	if (off < 0x4128 || off > 0x4138 || (off & 3)) {
		psrp_bad++;
		return 0;
	}
	return psrp_val[(off - 0x4128) / 4];
}

/* The switch's one guarded write path, as rtl819x-switch.c:287 writes it:
 * refused, counted, while the switch is locked.  1.6's registers go to its
 * model; a store anywhere else but PCRP0-PCRP4 is counted as illegal and
 * not applied. */
static UNUSED int rtl819x_sw_wr(unsigned int off, u32 v)
{
	unsigned int p;

	if (!rtl819x_sw_unlocked) {
		sw_n_refused++;
		return -EPERM;
	}
	pacc_log('W', off, v);
	sw_n_writes++;
	if (vg_wr(off, v))		/* 1.6's registers */
		return 0;
	pcrp_wr++;
	if (irq_depth)
		pcrp_wr_insec++;
	if (off < 0x4104 || off > 0x4114 || (off & 3)) {
		pcrp_illegal++;
		return 0;
	}
	p = (off - 0x4104) / 4;
	pcrp[p] = v;
	if (pcrp_nostick[p])
		pcrp[p] &= ~1u;
	if (pcrp_flip[p])
		pcrp[p] ^= 0x8u;
	return 0;
}

/* 1.5: rtl819x_sw_do_reset is above the cut (rtl819x-switch.c:382).  The
 * stub writes nothing: it logs the call and its recipe as `X` and returns a
 * scripted rc, so what the guard lets through is visible and nothing else
 * is. */
static int n_do_reset, do_reset_rc;
static UNUSED int rtl819x_sw_do_reset(int vendor_recipe)
{
	n_do_reset++;
	pacc_log('X', 0x4204, (u32)vendor_recipe);
	return do_reset_rc;
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

/* 1.4's lines with every field at its widest (32-bit longs, as the target) */
static void set_widest14(void)
{
	int n;

	rtl819x_phyif_unlocked = INT_MIN;
	rtl819x_phyif_n_ok = rtl819x_phyif_n_stored = 0xFFFFFFFFUL;
	rtl819x_phyif_n_already = rtl819x_phyif_n_refused = 0xFFFFFFFFUL;
	rtl819x_phyif_n_idfail = rtl819x_phyif_n_rbfail = 0xFFFFFFFFUL;
	for (n = 0; n < 5; n++) {
		rtl819x_phyif_res[n].pre = rtl819x_phyif_res[n].rb = 0xFFFFFFFFu;
		rtl819x_phyif_res[n].rc = INT_MIN;
		rtl819x_phyif_res[n].st = 255;
	}
}

/* 1.5's line with every field at its widest (32-bit longs, as the target) */
static void set_widest15(void)
{
	rtl819x_sw_init_n = rtl819x_sw_init_n_ok = 0xFFFFFFFFUL;
	rtl819x_sw_init_n_refused = rtl819x_sw_rst_n_busy = 0xFFFFFFFFUL;
	rtl819x_sw_init_rc = INT_MIN;
	rtl819x_sw_init_st = rtl819x_sw_init_on = 255;
}

/* 1.6's line with every field at its widest (32-bit longs, as the target) */
static void set_widest16(void)
{
	rtl819x_vlan_n = rtl819x_vlan_n_ok = 0xFFFFFFFFUL;
	rtl819x_vlan_n_refused = 0xFFFFFFFFUL;
	rtl819x_vlan_rc = INT_MIN;
#ifndef CONFIG_RTL_819X_SWCORE
	{
		int i;

		rtl819x_vlan_n_ld = rtl819x_vlan_n_to = 0xFFFFFFFFUL;
		rtl819x_vlan_n_rb = 0xFFFFFFFFUL;
		rtl819x_vlan_sta = rtl819x_vlan_spin = 0xFFFFFFFFUL;
		rtl819x_vlan_at = rtl819x_vlan_final = INT_MIN;
		rtl819x_vlan_step = rtl819x_vlan_nw = 255;
		rtl819x_vlan_rw = rtl819x_vlan_vm = 255;
		rtl819x_vlan_vw = 0xFFFF;
		for (i = 0; i < 4; i++)
			rtl819x_vlan_vr[i] = 0xFFFFFFFFu;
		rtl819x_vlan_tlu = rtl819x_vlan_asr = 0xFFFFFFFFu;
	}
#endif
}

/* 1.6's model: the registers as a load would read them, the counters, and
 * every slot that is not eight zero words. */
static void vg_stat(void)
{
	int i, k, z;

	printf("VSTAT swtcr0=%08X ffcr=%08X pvcr=%08X,%08X,%08X,%08X,%08X "
	       "vcr0=%08X pbvcr0=%08X plitimr=%08X swtacr=%08X starts=%d "
	       "viol=%d nostop=%d badaa=%d badcmd=%d illegal=%d winld=%d\n",
	       (vg_swtcr0 & ~(1u << 19)) | (vg_sta ? 1u << 19 : 0), vg_ffcr,
	       vg_pvcr[0], vg_pvcr[1], vg_pvcr[2], vg_pvcr[3], vg_pvcr[4],
	       vg_vcr0, vg_pbvcr0, vg_plitimr, vg_swtacr, vg_starts, vg_viol,
	       vg_nostop, vg_badaa, vg_badcmd, vg_illegal, vg_winld);
	for (i = 0; i < 24; i++) {
		u32 *w = i < 16 ? vg_vlan[i] : vg_netif[i - 16];

		for (z = 1, k = 0; k < 8; k++)
			if (w[k])
				z = 0;
		if (z)
			continue;
		printf("VT %c %d", i < 16 ? 'v' : 'n', i < 16 ? i : i - 16);
		for (k = 0; k < 8; k++)
			printf(" %08X", w[k]);
		printf("\n");
	}
	printf("VT-END\n");
}

static void pstat_line(void)
{
	printf("PSTAT rd=%d rd_insec=%d wr=%d wr_insec=%d illegal=%d "
	       "sw_writes=%lu sw_refused=%lu sections=%d imbalance=%d depth=%d "
	       "marks=%d mark=%s pcrp=%08X,%08X,%08X,%08X,%08X "
	       "swrd=%d do_reset=%d cpuicr_rd=%d\n",
	       pcrp_rd, pcrp_rd_insec, pcrp_wr, pcrp_wr_insec, pcrp_illegal,
	       sw_n_writes, sw_n_refused, irq_sections, irq_imbalance,
	       irq_depth, n_marks, last_mark[0] ? last_mark : "-", pcrp[0],
	       pcrp[1], pcrp[2], pcrp[3], pcrp[4], sw_rd_calls, n_do_reset,
	       cpuicr_rd);
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
	long a, b, c, d;

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
		} else if (sscanf(line, "set swunlock %ld", &a) == 1) {
			rtl819x_sw_unlocked = (int)a;
		} else if (sscanf(line, "set pcrp %ld %li", &a, &b) == 2) {
			pcrp[a] = (u32)b;
		} else if (sscanf(line, "set nostick %ld %ld", &a, &b) == 2) {
			pcrp_nostick[a] = (int)b;
		} else if (sscanf(line, "set flip %ld %ld", &a, &b) == 2) {
			pcrp_flip[a] = (int)b;
		} else if (!strncmp(line, "v ", 2)) {
			/* what the switch's handler passes on: CR/LF stripped,
			 * count the bytes written, newline included */
			rc = rtl819x_sw_v14_write(line + 2, strlen(line + 2) + 1);
			printf("OP v %s -> %d\n", line + 2, rc);
		} else if (!strcmp(line, "l")) {
			memset(page, 0x5A, sizeof(page));
			rc = rtl819x_sw_v14_lines(page);
			page[rc < 0 ? 0 : rc] = '\0';
			printf("LINES-BEGIN\n%sLINES-END len=%d\n", page, rc);
		} else if (!strcmp(line, "pacc")) {
			for (i = n_pacc_dumped; i < n_pacc; i++)
				printf("PA %c %04X %08X irq %d sec %d\n",
				       pacc[i].k, pacc[i].off, pacc[i].v,
				       pacc[i].irq, pacc[i].sec);
			n_pacc_dumped = n_pacc;
			printf("PA-END\n");
		} else if (!strcmp(line, "pstat")) {
			pstat_line();
		} else if (!strcmp(line, "widest14")) {
			set_widest14();
		} else if (sscanf(line, "set cpuicr %li", &a) == 1) {
			cpuicr = (u32)a;
		} else if (sscanf(line, "set resetrc %ld", &a) == 1) {
			do_reset_rc = (int)a;
		} else if (!strncmp(line, "x ", 2)) {
			/* the switch handler's reset branch, as
			 * rtl819x-switch.c:636-640 writes it: two forms,
			 * the recipe from buf[6], and count on success */
			const char *b = line + 2;

			if (!strcmp(b, "reset full") ||
			    !strcmp(b, "reset vendor")) {
				rc = rtl819x_sw_v15_reset(b[6] == 'v');
				rc = rc ? rc : (int)strlen(b) + 1;
			} else {
				rc = -EINVAL;
			}
			printf("OP x %s -> %d\n", b, rc);
		} else if (!strcmp(line, "widest15")) {
			set_widest15();
		/* 1.6: every op is `set vg...`, so no older op's sscanf
		 * prefix can take one (`set nostick` would read
		 * `set nostick18 1` as port 18) */
		} else if (sscanf(line, "set vgstate %ld", &a) == 1) {
			vg_state((int)a);
		} else if (sscanf(line, "set vgregnostick %lx", &a) == 1) {
			vg_nostick_off = (int)a;
		} else if (sscanf(line, "set vgreg %lx %li", &a, &b) == 2) {
			vg_set((unsigned int)a, (u32)b);
		} else if (sscanf(line, "set vgtbl %ld %ld %ld %li", &a, &b, &c,
				  &d) == 4) {
			if (a == 6 && b >= 0 && b < 16 && c >= 0 && c < 8)
				vg_vlan[b][c] = (u32)d;
			else if (a == 4 && b >= 0 && b < 8 && c >= 0 && c < 8)
				vg_netif[b][c] = (u32)d;
			else {
				printf("HARNESS vgtbl: no slot %ld/%ld/%ld\n", a,
				       b, c);
				return 3;
			}
		} else if (sscanf(line, "set vgsta %ld", &a) == 1) {
			vg_sta = (int)a;
		} else if (sscanf(line, "set vgnostick18 %ld", &a) == 1) {
			vg_nostick18 = (int)a;
		} else if (sscanf(line, "set vgnoclear18 %ld", &a) == 1) {
			vg_noclear18 = (int)a;
		} else if (sscanf(line, "set vgbusyat %ld %ld", &a, &b) == 2) {
			vg_busy_from = a;
			vg_busy_n = b;
		} else if (sscanf(line, "set vgbusy %ld", &a) == 1) {
			vg_busy = a;
		} else if (sscanf(line, "set vgstuck %ld", &a) == 1) {
			vg_stuck = (int)a;
		} else if (sscanf(line, "set vgghost %ld", &a) == 1) {
			vg_ghost = (int)a;
		} else if (sscanf(line, "set vgcorrupt %li", &a) == 1) {
			vg_corrupt = (u32)a;
		} else if (sscanf(line, "set vgtear %ld", &a) == 1) {
			vg_tear = a;
		} else if (!strcmp(line, "vstat")) {
			vg_stat();
		} else if (!strcmp(line, "widest16")) {
			set_widest16();
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
        self.lines14, self.pacc, self.pstats = [], [], []
        self.vstats, self.vtables = [], []
        self.errno = {}
        self.bound = None
        cur = cur14 = None
        st, pa, vt = [], [], {}
        for ln in p.stdout.split("\n"):
            if cur is not None:
                m = re.match(r"PAGE-END len=(-?\d+) eof=(\d+)$", ln)
                if m:
                    self.pages.append(("".join(cur), int(m.group(1))))
                    cur = None
                else:
                    cur.append(ln + "\n")
                continue
            if cur14 is not None:
                m = re.match(r"LINES-END len=(-?\d+)$", ln)
                if m:
                    self.lines14.append(("".join(cur14), int(m.group(1))))
                    cur14 = None
                else:
                    cur14.append(ln + "\n")
                continue
            if ln == "LINES-BEGIN":
                cur14 = []
            elif ln.startswith("PA "):
                f = ln.split()
                pa.append((f[1], int(f[2], 16), int(f[3], 16), int(f[5]),
                           int(f[7])))
            elif ln == "PA-END":
                self.pacc.append(pa)
                pa = []
            elif ln.startswith("PSTAT "):
                d = {}
                for kv in ln[6:].split(" "):
                    k, _, v = kv.partition("=")
                    d[k] = v
                self.pstats.append(d)
            elif ln.startswith("VSTAT "):
                d = {}
                for kv in ln[6:].split(" "):
                    k, _, v = kv.partition("=")
                    d[k] = v
                self.vstats.append(d)
            elif ln.startswith("VT "):
                f = ln.split()
                vt[(f[1], int(f[2]))] = [int(x, 16) for x in f[3:11]]
            elif ln == "VT-END":
                self.vtables.append(vt)
                vt = {}
            elif ln == "PAGE-BEGIN":
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

    def line14(self, i, key):
        """The rest of 1.4's line starting with `key ` in the i-th render."""
        if i >= len(self.lines14):
            return None
        for ln in self.lines14[i][0].split("\n"):
            if ln.startswith(key + " "):
                return ln[len(key) + 1:]
        return None

    def pst(self, i, k):
        return self.pstats[i][k] if i < len(self.pstats) else None

    def vst(self, i, k):
        return self.vstats[i].get(k) if i < len(self.vstats) else None

    def vtab(self, i):
        return self.vtables[i] if i < len(self.vtables) else None


def rd(a, r):
    return (a << 24) | (r << 16)


def wr(a, r, v):
    return 0x80000000 | (a << 24) | (r << 16) | v


UNLOCK = "w unlock mdio-i-mean-it"
PROBED = ["init", UNLOCK, "w probe", "stores"]
PAGE1 = 0x8000		# the fake's page-1 marker bit


def boot_page(bound=10000):
    lines = ["version rtl819x-switch 1.6", "unlocked 0", "bus 0 reg_rc 1",
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


def cases(exe, block, version, exe_y=None):
    """Yield (name, ok, detail) for K1..K67 (K0 is the compile); `exe_y` is
    the block compiled with -DCONFIG_RTL_819X_SWCORE, for K56 and K57."""
    B = 10000
    dmax_seen = []

    def track(run):
        for s in run.stats:
            dmax_seen.append(int(s["dmax"]))
        return run

    # K1 boot
    r = track(Run(exe, ["init", "r", "stat"]))
    ok = (r.rc == 0 and r.op(0) == 0 and version == "rtl819x-switch 1.6"
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

    # ---------------------------------------- 1.4: the phyif write class
    for item in cases14(exe, block):
        yield item

    # ---------------------------------------- 1.6: `vlan`
    for item in cases16(exe, exe_y, block):
        yield item


# 1.4 (R6b-10).  The PCRP model's default is the post-`J` state (量 C9-SW0).
POSTJ = [0x007F0038, 0x047F0038, 0x087F0038, 0x0C7F0038, 0x107F0038]
PHYUNLOCK = "v unlock phyif-i-mean-it"
PERMIT = ["set swunlock 1", PHYUNLOCK]
# 1.5 (R6b-8 8d): the `init` line before any call (rc 1: never called).
INIT_BOOT = "calls 0 ok 0 refused 0 rc 1 stored 00 on 00 reset_busy 0"


def lines14_boot():
    """1.4's six boot lines, then the one 1.5 hooks after them and the one
    1.6 hooks after that."""
    return ("phyif unlocked 0 ok 0 stored 0 already 0 refused 0 idfail 0 "
            "rbfail 0\n" + "".join("phyif%d pre 00000000 rb 00000000 rc 1 st 0\n"
                                   % n for n in range(5))
            + "init " + INIT_BOOT + "\n" + "vlan " + vg_fields() + "\n")


def rwr(n, pre, rb=None, sec=None):
    """The accesses one stored port makes: R pre, W pre|1, R rb."""
    off = 0x4104 + 4 * n
    rb = (pre | 1) if rb is None else rb
    return [("R", off, pre), ("W", off, pre | 1), ("R", off, rb)]


def acc(run, i):
    """(kind, off, value) of the i-th pacc dump, without irq/section."""
    return [x[:3] for x in run.pacc[i]] if i < len(run.pacc) else None


def one_section(run, i, per):
    """Every access of dump i with IRQs off, `per` accesses a section, each
    group in its own section."""
    if i >= len(run.pacc):
        return False
    d = run.pacc[i]
    secs = [x[4] for x in d]
    groups = [secs[k:k + per] for k in range(0, len(secs), per)]
    return (all(x[3] == 1 for x in d) and all(len(set(g)) == 1 for g in groups)
            and len({g[0] for g in groups}) == len(groups))


def comment_figures14(block):
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in block.split("\n"))
    m = re.search(r"widest: (\d+) \+ 5 x (\d+) = (\d+) bytes", body)
    return tuple(int(g) for g in m.groups()) if m else None


def cases14(exe, block):
    """Yield (name, ok, detail) for K24..K36: 1.4's `phyif` class."""
    einval, eperm = -ERRNO["EINVAL"], -ERRNO["EPERM"]
    eproto, eio = -ERRNO["EPROTO"], -ERRNO["EIO"]

    # K24 boot, and a cat reads nothing
    r = Run(exe, ["l", "l", "pstat"])
    ok = (r.rc == 0 and len(r.lines14) == 2
          and r.lines14[0][0] == lines14_boot()
          and r.lines14[1] == r.lines14[0]
          and r.lines14[0][1] == len(r.lines14[0][0])
          and r.pst(0, "rd") == "0" and r.pst(0, "wr") == "0"
          and r.pst(0, "marks") == "0")
    yield "K24", ok, "boot lines %s, reads %s" % (
        "exact" if r.lines14 and r.lines14[0][0] == lines14_boot()
        else repr(r.lines14[:1])[:200], r.pst(0, "rd"))

    # K25 the class token absent: refused, counted, no access
    r = Run(exe, ["set swunlock 1", "v phyif all", "v phyif 0", "l", "pacc",
                  "pstat"])
    ok = (r.rc == 0 and [x[1] for x in r.ops] == [eperm, eperm]
          and r.line14(0, "phyif") == "unlocked 0 ok 0 stored 0 already 0 "
                                      "refused 2 idfail 0 rbfail 0"
          and r.line14(0, "phyif0") == "pre 00000000 rb 00000000 rc 1 st 0"
          and acc(r, 0) == [] and r.pst(0, "marks") == "0")
    yield "K25", ok, "ops %s" % [x[1] for x in r.ops]

    # K26 the token: near misses, the switch's own, then unlock and lock
    r = Run(exe, ["set swunlock 1", "v unlock i-mean-it",
                  "v unlock phyif-i-mean-it2", "v unlock  phyif-i-mean-it",
                  "l", PHYUNLOCK, "pstat", "l", "v lock phyif", "pstat", "l",
                  "v phyif 0", "pacc"])
    rcs = [x[1] for x in r.ops]
    ok = (r.rc == 0
          and rcs == [einval, einval, einval,
                      len("unlock phyif-i-mean-it\n"), len("lock phyif\n"),
                      eperm]
          and (r.line14(0, "phyif") or "").startswith("unlocked 0 ")
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF-UNLOCK"
          and (r.line14(1, "phyif") or "").startswith("unlocked 1 ")
          and r.pst(1, "mark") == "RLXFW-SW-PHYIF-LOCK"
          and (r.line14(2, "phyif") or "").startswith("unlocked 0 ")
          and acc(r, 0) == [])
    yield "K26", ok, "ops %s" % rcs

    # K27 phyif all from the post-J state: the exact accesses, one IRQs-off
    # section a port, the page, the mark, the model -- and a cat after it
    # still reads nothing
    r = Run(exe, PERMIT + ["v phyif all", "pacc", "l", "l", "pstat"])
    want = [a for n in range(5) for a in rwr(n, POSTJ[n])]
    ports = all(r.line14(0, "phyif%d" % n) ==
                "pre %08X rb %08X rc 0 st 1" % (POSTJ[n], POSTJ[n] | 1)
                for n in range(5))
    ok = (r.rc == 0 and r.op(1) == len("phyif all\n")
          and acc(r, 0) == want and one_section(r, 0, 3)
          and r.line14(0, "phyif") == "unlocked 1 ok 1 stored 5 already 0 "
                                      "refused 0 idfail 0 rbfail 0"
          and ports and len(r.lines14) == 2 and r.lines14[1] == r.lines14[0]
          and r.pst(0, "rd") == "10" and r.pst(0, "wr") == "5"
          and r.pst(0, "rd_insec") == "10" and r.pst(0, "wr_insec") == "5"
          and r.pst(0, "illegal") == "0" and r.pst(0, "sw_writes") == "5"
          and r.pst(0, "imbalance") == "0" and r.pst(0, "depth") == "0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00001F1F"
          and r.pst(0, "pcrp") == ",".join("%08X" % (v | 1) for v in POSTJ))
    yield "K27", ok, "rc %s, %d accesses, mark %s" % (
        r.op(1) if len(r.ops) > 1 else "-", len(acc(r, 0) or []),
        r.pst(0, "mark"))

    # K28 one port; the previous verb's results do not survive the next
    r = Run(exe, PERMIT + ["v phyif all"] +
            ["set pcrp %d 0x%08X" % (n, POSTJ[n]) for n in range(5)] +
            ["pacc", "v phyif 3", "pacc", "l", "pstat"])
    others = all(r.line14(0, "phyif%d" % n) ==
                 "pre 00000000 rb 00000000 rc 1 st 0" for n in (0, 1, 2, 4))
    ok = (r.rc == 0 and r.op(2) == len("phyif 3\n")
          and acc(r, 1) == rwr(3, POSTJ[3]) and one_section(r, 1, 3)
          and r.line14(0, "phyif3") == "pre %08X rb %08X rc 0 st 1"
          % (POSTJ[3], POSTJ[3] | 1)
          and others
          and r.line14(0, "phyif") == "unlocked 1 ok 2 stored 6 already 0 "
                                      "refused 0 idfail 0 rbfail 0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000808"
          and r.pst(0, "pcrp") == ",".join("%08X" % (POSTJ[n] | (n == 3))
                                           for n in range(5)))
    yield "K28", ok, "accesses %s, others reset %s" % (acc(r, 1), others)

    # K29 every other port and every malformed form refused beside a
    # permitted neighbour, with no access; unknown verbs as before 1.4
    bad = ["phyif 5", "phyif 9", "phyif 05", "phyif -1", "phyif",
           "phyif  0", "phyif 0 ", "phyif 0x", "phyif a", "phyif al",
           "phyif all ", "phyif 0 1", "phyif 6", "phyif 8", "PHYIF 0",
           "phyifall", "lock", "unlock", "bogus"]
    r = Run(exe, PERMIT + ["pacc", "v phyif 5", "v phyif 4"] +
            ["v " + b for b in bad[1:]] + ["v phyif all", "pacc", "l",
                                          "pstat"])
    rcs = [x[1] for x in r.ops][1:]
    want_rcs = [einval, len("phyif 4\n")] + [einval] * (len(bad) - 1) + \
        [len("phyif all\n")]
    want = rwr(4, POSTJ[4]) + [a for n in range(4) for a in rwr(n, POSTJ[n])] \
        + [("R", 0x4114, POSTJ[4] | 1)]
    ok = (r.rc == 0 and rcs == want_rcs and acc(r, 1) == want
          and r.line14(0, "phyif") == "unlocked 1 ok 2 stored 5 already 1 "
                                      "refused 0 idfail 0 rbfail 0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000F1F"
          and r.pst(0, "illegal") == "0")
    yield "K29", ok, "%d refusals, rcs %s" % (len(bad), rcs if rcs != want_rcs
                                             else "as written")

    # K30 already set: read, not stored
    r = Run(exe, PERMIT + ["set pcrp 3 0x0C7F0039", "v phyif 3", "pacc", "l",
                           "pstat"])
    ok = (r.rc == 0 and r.op(1) == len("phyif 3\n")
          and acc(r, 0) == [("R", 0x4110, 0x0C7F0039)]
          and r.line14(0, "phyif3") == "pre 0C7F0039 rb 00000000 rc 0 st 0"
          and r.line14(0, "phyif") == "unlocked 1 ok 1 stored 0 already 1 "
                                      "refused 0 idfail 0 rbfail 0"
          and r.pst(0, "wr") == "0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000008")
    yield "K30", ok, "accesses %s" % acc(r, 0)

    # K31 the identity check: port 2's word carries ExtPHYID 1 -- nothing
    # stored there, and `all` stops there
    r = Run(exe, PERMIT + ["set pcrp 2 0x047F0038", "v phyif all", "pacc",
                           "l", "pstat", "v phyif 2", "pacc", "pstat"])
    want = rwr(0, POSTJ[0]) + rwr(1, POSTJ[1]) + [("R", 0x410C, 0x047F0038)]
    ok = (r.rc == 0 and r.op(1) == eproto and acc(r, 0) == want
          and r.line14(0, "phyif2") == "pre 047F0038 rb 00000000 rc %d st 0"
          % eproto
          and all(r.line14(0, "phyif%d" % n) ==
                  "pre 00000000 rb 00000000 rc 1 st 0" for n in (3, 4))
          and r.line14(0, "phyif") == "unlocked 1 ok 0 stored 2 already 0 "
                                      "refused 0 idfail 1 rbfail 0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000303"
          and r.op(2) == eproto and acc(r, 1) == [("R", 0x410C, 0x047F0038)]
          and r.pst(1, "wr") == "2")
    yield "K31", ok, "rc %s, accesses %d" % (r.op(1) if len(r.ops) > 1
                                              else "-", len(acc(r, 0) or []))

    # K32 bit 0 does not stick on port 1: -EIO, and `all` stops there
    r = Run(exe, PERMIT + ["set nostick 1 1", "v phyif all", "pacc", "l",
                           "pstat"])
    want = rwr(0, POSTJ[0]) + rwr(1, POSTJ[1], rb=POSTJ[1])
    ok = (r.rc == 0 and r.op(1) == eio and acc(r, 0) == want
          and r.line14(0, "phyif1") == "pre %08X rb %08X rc %d st 1"
          % (POSTJ[1], POSTJ[1], eio)
          and r.line14(0, "phyif") == "unlocked 1 ok 0 stored 2 already 0 "
                                      "refused 0 idfail 0 rbfail 1"
          and r.line14(0, "phyif2") == "pre 00000000 rb 00000000 rc 1 st 0"
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000301")
    yield "K32", ok, "rc %s phyif1 %s" % (r.op(1) if len(r.ops) > 1 else "-",
                                         r.line14(0, "phyif1"))

    # K33 another bit moved on the store (bit 3): -EIO although bit 0 stuck
    r = Run(exe, PERMIT + ["set flip 2 1", "v phyif 2", "pacc", "l", "pstat"])
    moved = (POSTJ[2] | 1) ^ 0x8
    ok = (r.rc == 0 and r.op(1) == eio
          and acc(r, 0) == rwr(2, POSTJ[2], rb=moved)
          and r.line14(0, "phyif2") == "pre %08X rb %08X rc %d st 1"
          % (POSTJ[2], moved, eio)
          and (r.line14(0, "phyif") or "").endswith("rbfail 1")
          and r.pst(0, "mark") == "RLXFW-SW-PHYIF=00000400")
    yield "K33", ok, "rc %s phyif2 %s" % (r.op(1) if len(r.ops) > 1 else "-",
                                         r.line14(0, "phyif2"))

    # K34 the switch locked: the store is rtl819x_sw_wr's to refuse
    r = Run(exe, ["set swunlock 0", PHYUNLOCK, "v phyif 0", "pacc", "l",
                  "pstat"])
    ok = (r.rc == 0 and r.op(1) == eperm
          and acc(r, 0) == [("R", 0x4104, POSTJ[0])]
          and r.line14(0, "phyif0") == "pre %08X rb 00000000 rc %d st 0"
          % (POSTJ[0], eperm)
          and r.line14(0, "phyif") == "unlocked 1 ok 0 stored 0 already 0 "
                                      "refused 0 idfail 0 rbfail 0"
          and r.pst(0, "sw_refused") == "1" and r.pst(0, "wr") == "0")
    yield "K34", ok, "rc %s sw_refused %s" % (r.op(1) if len(r.ops) > 1
                                               else "-", r.pst(0, "sw_refused"))

    # K35 over 64 pre-read words (bit 31 and bits 25:1 drawn, ExtPHYID the
    # port's, bit 0 clear), the word stored differs from the one read in
    # bit 0 alone
    rng = random.Random(1427)
    words = []
    for i in range(64):
        n = i % 5
        w = ((rng.getrandbits(32) & 0x83FFFFFE) | (n << 26)) & ~1
        words.append((n, w))
    script = list(PERMIT)
    for n, w in words:
        script += ["set pcrp %d 0x%08X" % (n, w), "v phyif %d" % n]
    script += ["pacc", "pstat"]
    r = Run(exe, script)
    want = [a for n, w in words for a in rwr(n, w)]
    rcs = [x[1] for x in r.ops][1:]
    ok = (r.rc == 0 and rcs == [len("phyif 0\n")] * 64
          and acc(r, 0) == want and r.pst(0, "illegal") == "0")
    yield "K35", ok, "64 words, %s" % ("each stored as read with bit 0 set"
                                       if ok else "rcs/accesses differ")

    # K36 the page's lines at their widest against the comment's figures.
    # 1.4's are the first six; 1.5's line after them is K46's.
    r = Run(exe, ["widest14", "l"])
    text, n = r.lines14[0] if r.lines14 else ("", -1)
    ls = text.split("\n")[:-1]
    l14 = ls[:6]
    head = len(l14[0]) + 1 if l14 else -1
    per = {len(x) + 1 for x in l14[1:]}
    n14 = sum(len(x) + 1 for x in l14)
    fig = comment_figures14(block)
    ok = (r.rc == 0 and len(l14) == 6
          and all(x.startswith("phyif") for x in l14) and len(per) == 1
          and fig == (head, min(per) if per else -1, n14) and n == len(text))
    yield "K36", ok, "comment %s, measured %d + 5 x %s = %d" % (
        fig, head, sorted(per), n14)

    # ---------------------------------------- 1.5: `init` and the guard
    for item in cases15(exe, block):
        yield item


# 1.5 (R6b-8 8d).  The vendor-set state: bit 0 set on ports 0-4 by the
# vendor's probe (量 bench/2026-09-28/AV-P03.log:9-13).
VENDOR = [w | 1 for w in POSTJ]
SWUNLOCK = "set swunlock 1"
NINIT = len("init\n")
CPUICR = 0xB8010000


def line15(run, i):
    """The rest of 1.5's `init` line in the i-th render."""
    return run.line14(i, "init")


def ld(v):
    """The guard's CPUICR load, as the access log records it."""
    return ("C", CPUICR, v)


def rst(vendor):
    """One call of the rtl819x_sw_do_reset stub, with its recipe."""
    return ("X", 0x4204, vendor)


def comment_figures15(block):
    """(1.4's base, 1.4's total, 1.5's line, 1.5's base, 1.5's total) as the
    two block comments state them, or None."""
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in block.split("\n"))
    m4 = re.search(r"1\.2's worst case of ([\d,]+) of 4,096 becomes ([\d,]+)",
                   body)
    m5 = re.search(r"(\d+) bytes \(tools/mdiocheck\.py K46 measures it\), so "
                   r"1\.4's worst case of ([\d,]+) of 4,096 becomes ([\d,]+)",
                   body)
    if not (m4 and m5):
        return None
    return tuple(int(g.replace(",", "")) for g in m4.groups() + m5.groups())


def cases15(exe, block):
    """Yield (name, ok, detail) for K37..K46: 1.5's `init` and the guard."""
    einval, eperm, ebusy = -ERRNO["EINVAL"], -ERRNO["EPERM"], -ERRNO["EBUSY"]
    eproto, eio = -ERRNO["EPROTO"], -ERRNO["EIO"]
    full = [a for n in range(5) for a in rwr(n, POSTJ[n])]
    untried = "pre 00000000 rb 00000000 rc 1 st 0"

    # K37 the switch locked: refused before any register read, counted in
    # the `init` line and nowhere else -- and the phyif token does not open it
    r = Run(exe, ["v init", "l", "pacc", "pstat", PHYUNLOCK, "v init", "l",
                  "pacc", "pstat", "stat"])
    ok = (r.rc == 0
          and [x[1] for x in r.ops] == [eperm, len("unlock phyif-i-mean-it\n"),
                                        eperm]
          and line15(r, 0) == "calls 1 ok 0 refused 1 rc %d stored 00 on 00 "
                              "reset_busy 0" % eperm
          and line15(r, 1) == "calls 2 ok 0 refused 2 rc %d stored 00 on 00 "
                              "reset_busy 0" % eperm
          and acc(r, 0) == [] and acc(r, 1) == []
          and r.pst(0, "swrd") == "0" and r.pst(1, "swrd") == "0"
          and r.pst(1, "sw_refused") == "0" and r.pst(1, "wr") == "0"
          and r.pst(0, "marks") == "0" and r.pst(1, "marks") == "1"
          and r.pst(1, "mark") == "RLXFW-SW-PHYIF-UNLOCK"
          and (r.line14(1, "phyif") or "").startswith("unlocked 1 ")
          and all(r.line14(1, "phyif%d" % n) == untried for n in range(5))
          and r.stat(0, "nstores") == "0")
    yield "K37", ok, "ops %s, init %s" % ([x[1] for x in r.ops],
                                          line15(r, 1))

    # K38 init from the post-J state: exactly phyif all's accesses, one
    # IRQs-off section a port; phyif's own token locked throughout
    r = Run(exe, [SWUNLOCK, "v init", "pacc", "l", "l", "pstat", "stat"])
    ports = all(r.line14(0, "phyif%d" % n) ==
                "pre %08X rb %08X rc 0 st 1" % (POSTJ[n], POSTJ[n] | 1)
                for n in range(5))
    ok = (r.rc == 0 and r.op(0) == NINIT
          and acc(r, 0) == full and one_section(r, 0, 3) and ports
          and r.line14(0, "phyif") == "unlocked 0 ok 0 stored 5 already 0 "
                                      "refused 0 idfail 0 rbfail 0"
          and line15(r, 0) == "calls 1 ok 1 refused 0 rc 0 stored 1F on 1F "
                              "reset_busy 0"
          and len(r.lines14) == 2 and r.lines14[1] == r.lines14[0]
          and r.pst(0, "rd") == "10" and r.pst(0, "wr") == "5"
          and r.pst(0, "rd_insec") == "10" and r.pst(0, "wr_insec") == "5"
          and r.pst(0, "swrd") == "10" and r.pst(0, "illegal") == "0"
          and r.pst(0, "sw_writes") == "5" and r.pst(0, "imbalance") == "0"
          and r.pst(0, "depth") == "0" and r.pst(0, "do_reset") == "0"
          and r.pst(0, "cpuicr_rd") == "0" and r.pst(0, "marks") == "1"
          and r.pst(0, "mark") == "RLXFW-SW-INIT=00001F1F"
          and r.pst(0, "pcrp") == ",".join("%08X" % (v | 1) for v in POSTJ)
          and r.stat(0, "nstores") == "0")
    yield "K38", ok, "rc %s, %d accesses, mark %s" % (
        r.op(0) if r.ops else "-", len(acc(r, 0) or []), r.pst(0, "mark"))

    # K39 the vendor-set state: five reads, no store
    r = Run(exe, [SWUNLOCK] + ["set pcrp %d 0x%08X" % (n, VENDOR[n])
                               for n in range(5)]
            + ["v init", "pacc", "l", "pstat"])
    ok = (r.rc == 0 and r.op(0) == NINIT
          and acc(r, 0) == [("R", 0x4104 + 4 * n, VENDOR[n]) for n in range(5)]
          and one_section(r, 0, 1)
          and all(r.line14(0, "phyif%d" % n) ==
                  "pre %08X rb 00000000 rc 0 st 0" % VENDOR[n] for n in range(5))
          and r.line14(0, "phyif") == "unlocked 0 ok 0 stored 0 already 5 "
                                      "refused 0 idfail 0 rbfail 0"
          and line15(r, 0) == "calls 1 ok 1 refused 0 rc 0 stored 00 on 1F "
                              "reset_busy 0"
          and r.pst(0, "wr") == "0" and r.pst(0, "sw_writes") == "0"
          and r.pst(0, "mark") == "RLXFW-SW-INIT=0000001F"
          and r.pst(0, "pcrp") == ",".join("%08X" % v for v in VENDOR))
    yield "K39", ok, "accesses %s" % acc(r, 0)

    # K40 port 2's word carries port 1's ExtPHYID: init stops there, and the
    # `phyif all` before it leaves nothing in ports 3 and 4's lines
    r = Run(exe, PERMIT + ["v phyif all"]
            + ["set pcrp %d 0x%08X" % (n, POSTJ[n]) for n in range(5)]
            + ["set pcrp 2 0x047F0038", "pacc", "v init", "pacc", "l", "pstat"])
    want = rwr(0, POSTJ[0]) + rwr(1, POSTJ[1]) + [("R", 0x410C, 0x047F0038)]
    ok = (r.rc == 0 and len(r.ops) == 3 and r.op(2) == eproto
          and acc(r, 1) == want
          and r.line14(0, "phyif0") == "pre %08X rb %08X rc 0 st 1"
          % (POSTJ[0], POSTJ[0] | 1)
          and r.line14(0, "phyif2") == "pre 047F0038 rb 00000000 rc %d st 0"
          % eproto
          and all(r.line14(0, "phyif%d" % n) == untried for n in (3, 4))
          and r.line14(0, "phyif") == "unlocked 1 ok 1 stored 7 already 0 "
                                      "refused 0 idfail 1 rbfail 0"
          and line15(r, 0) == "calls 1 ok 0 refused 0 rc %d stored 03 on 03 "
                              "reset_busy 0" % eproto
          and r.pst(0, "mark") == "RLXFW-SW-INIT=00000303")
    yield "K40", ok, "rc %s, accesses %d, phyif3 %s" % (
        r.op(2) if len(r.ops) > 2 else "-", len(acc(r, 1) or []),
        r.line14(0, "phyif3"))

    # K41 bit 0 does not stick on port 1: init stops there
    r = Run(exe, [SWUNLOCK, "set nostick 1 1", "v init", "pacc", "l", "pstat"])
    want = rwr(0, POSTJ[0]) + rwr(1, POSTJ[1], rb=POSTJ[1])
    ok = (r.rc == 0 and r.op(0) == eio and acc(r, 0) == want
          and r.line14(0, "phyif1") == "pre %08X rb %08X rc %d st 1"
          % (POSTJ[1], POSTJ[1], eio)
          and all(r.line14(0, "phyif%d" % n) == untried for n in (2, 3, 4))
          and r.line14(0, "phyif") == "unlocked 0 ok 0 stored 2 already 0 "
                                      "refused 0 idfail 0 rbfail 1"
          and line15(r, 0) == "calls 1 ok 0 refused 0 rc %d stored 03 on 01 "
                              "reset_busy 0" % eio
          and r.pst(0, "mark") == "RLXFW-SW-INIT=00000301")
    yield "K41", ok, "rc %s phyif1 %s" % (r.op(0) if r.ops else "-",
                                         r.line14(0, "phyif1"))

    # K42 the phyif token is neither needed nor enough: (switch, phyif) over
    # all four, from the post-J state each time
    script = []
    for sw, ph in ((0, 0), (0, 1), (1, 0), (1, 1)):
        script += ["set swunlock %d" % sw,
                   PHYUNLOCK if ph else "v lock phyif"]
        script += ["set pcrp %d 0x%08X" % (n, POSTJ[n]) for n in range(5)]
        script += ["pacc", "v init", "pacc"]
    r = Run(exe, script + ["l"])
    inits = [x[1] for x in r.ops if x[0] == "v init"]
    ok = (r.rc == 0 and inits == [eperm, eperm, NINIT, NINIT]
          and [acc(r, i) for i in (1, 3, 5, 7)] == [[], [], full, full]
          and line15(r, 0) == "calls 4 ok 2 refused 2 rc 0 stored 1F on 1F "
                              "reset_busy 0")
    yield "K42", ok, "init rcs over (0,0) (0,1) (1,0) (1,1): %s" % inits

    # K43 malformed forms: -EINVAL, no access, not an `init` call; then the
    # permitted neighbour
    bad = ["init ", " init", "INIT", "Init", "init all", "init 0", "initx",
           "ini", "init\t", "init init"]
    r = Run(exe, [SWUNLOCK] + ["v " + b for b in bad]
            + ["pacc", "l", "v init", "pacc", "l"])
    rcs = [x[1] for x in r.ops]
    ok = (r.rc == 0 and rcs == [einval] * len(bad) + [NINIT]
          and acc(r, 0) == [] and line15(r, 0) == INIT_BOOT
          and acc(r, 1) == full
          and line15(r, 1) == "calls 1 ok 1 refused 0 rc 0 stored 1F on 1F "
                              "reset_busy 0")
    yield "K43", ok, "%d refusals, rcs %s" % (
        len(bad), rcs if rcs != [einval] * len(bad) + [NINIT] else "as written")

    # K44 the guard refuses: TXCMD, RXCMD, both (C4000000, the armed word)
    words = [0x80000000, 0x40000000, 0xC4000000]
    script = [SWUNLOCK]
    for w in words:
        script += ["set cpuicr 0x%08X" % w, "x reset full", "x reset vendor"]
    r = Run(exe, script + ["pacc", "pstat", "stat", "l"])
    ok = (r.rc == 0 and [x[1] for x in r.ops] == [ebusy] * 6
          and acc(r, 0) == [ld(w) for w in words for _ in (0, 1)]
          and r.pst(0, "do_reset") == "0" and r.pst(0, "cpuicr_rd") == "6"
          and r.pst(0, "swrd") == "0" and r.pst(0, "wr") == "0"
          and r.pst(0, "sw_writes") == "0" and r.pst(0, "sw_refused") == "0"
          and r.stat(0, "nstores") == "0"
          and line15(r, 0) == "calls 0 ok 0 refused 0 rc 1 stored 00 on 00 "
                              "reset_busy 6")
    yield "K44", ok, "rcs %s, do_reset %s, init line %s" % (
        [x[1] for x in r.ops], r.pst(0, "do_reset"), line15(r, 0))

    # K45 the guard permits: 04000000 (after `disarm`) and 0; the recipe
    # reaches rtl819x_sw_do_reset and its rc comes back
    r = Run(exe, [SWUNLOCK, "set cpuicr 0x04000000", "x reset full",
                  "x reset vendor", "set cpuicr 0", "x reset vendor",
                  "x reset full", "set resetrc -1", "set cpuicr 0x04000000",
                  "x reset vendor", "pacc", "pstat", "l"])
    want = [ld(0x04000000), rst(0), ld(0x04000000), rst(1), ld(0), rst(1),
            ld(0), rst(0), ld(0x04000000), rst(1)]
    ok = (r.rc == 0
          and [x[1] for x in r.ops] == [len("reset full\n"),
                                        len("reset vendor\n"),
                                        len("reset vendor\n"),
                                        len("reset full\n"), eperm]
          and acc(r, 0) == want
          and r.pst(0, "do_reset") == "5" and r.pst(0, "cpuicr_rd") == "5"
          and r.pst(0, "swrd") == "0"
          and line15(r, 0) == INIT_BOOT)
    yield "K45", ok, "rcs %s, accesses %s" % ([x[1] for x in r.ops],
                                              acc(r, 0))

    # K46 the `init` line at its widest against the block comment, and the
    # page's running total: 1.2's base + 1.4's measured lines = 1.4's total
    # = 1.5's base, + the measured line = 1.5's total, under the table's
    # budget (3,600) and the page (4,096)
    r = Run(exe, ["widest14", "widest15", "l"])
    text, n = r.lines14[0] if r.lines14 else ("", -1)
    ls = text.split("\n")[:-1]
    n14 = sum(len(x) + 1 for x in ls[:6])
    w15 = len(ls[6]) + 1 if len(ls) == 8 else -1     # 1.6's line is the 8th
    fig = comment_figures15(block)
    ok = (r.rc == 0 and len(ls) == 8 and n == len(text)
          and ls[6].startswith("init calls 4294967295 ok 4294967295 ")
          and fig is not None
          and fig[1] == fig[0] + n14 and fig[2] == w15
          and fig[3] == fig[1] and fig[4] == fig[3] + w15
          and fig[4] <= 3600 and fig[4] <= PAGE)
    yield "K46", ok, "comment %s, measured 1.4 %d and 1.5 %d" % (fig, n14, w15)


# 1.6 (R6c).  The model's two paths: the flash path (the default, 量
# bench/2026-10-08b) and the RAM path (`set vgstate 1`, its netif slot 0
# SYNTHETIC).  Item i is VLAN slot i below 16 and netif slot i - 16 above,
# the block's numbering.
VG_VER = [(0x4A18, 0x00000001), (0x4A00, 0x000001FF), (0x4A1C, 0x00000000),
          (0x4420, 0x07FAC688)]
VG_VR = tuple(v for _, v in VG_VER)
VG_REG = [0x4A08, 0x4A0C, 0x4A10, 0x4A14, 0x4428]
VG_RVAL = [0x00080008] * 4 + [0x00000003]
VG_FREG = [0x00010001] * 4 + [0x00000000]
ENTRY8 = [0x00807E3F] + [0] * 7
ZERO8 = [0] * 8
SYN0 = [0x00002011, 0x00400000, 0x9C000000, 0x000000BB, 0, 0, 0, 0]
STA, B18 = 1 << 19, 1 << 18
VLAN = "v vlan"
NVLAN = len("vlan\n")
SWCORE_Y = ["-DCONFIG_RTL_819X_SWCORE=1"]


def vg_fields(**kw):
    """1.6's line after `vlan `, from its fields; the defaults are a boot's."""
    f = dict(calls=0, ok=0, refused=0, rc=1, at=-1, step=0, vw=0, nw=0, rw=0,
             vm=0, vr=(0, 0, 0, 0), tlu=0, sta=0, spin=0, swtasr=0, final=-1,
             ld=0, to=0, rb=0)
    f.update(kw)
    return ("calls %(calls)d ok %(ok)d refused %(refused)d rc %(rc)d "
            "at %(at)d step %(step)d vw %(vw)04X nw %(nw)02X rw %(rw)02X "
            "vm %(vm)X " % f + "vr %08X %08X %08X %08X " % tuple(f["vr"])
            + "tlu %(tlu)08X sta %(sta)d spin %(spin)d swtasr %(swtasr)08X "
            "final %(final)d ld %(ld)d to %(to)d rb %(rb)d" % f)


def vg_addr(i):
    return 0xBB060000 + 32 * i if i < 16 else 0xBB040000 + 32 * (i - 16)


def vg_want(i):
    return ENTRY8 if i == 8 else ZERO8


def vg_start(ram):
    """item -> the eight words the model starts with."""
    cur = {i: ZERO8 for i in range(24)}
    if ram:
        cur[8], cur[16] = ENTRY8, SYN0
    return cur


def vg_read(i, words):
    """THE TABLE READ of item i agreeing at once: the idle poll, 8 + 8."""
    a = vg_addr(i)
    return ([("R", 0x4D00, 0)]
            + [("T", a + 4 * k, words[k]) for k in range(8)] * 2)


def vg_write(i, words, polls=1, sticks=True, asr=0):
    """ONE TABLE WRITE's (1)-(10) on the model, the IRQs-off part, written
    from the block comment's steps: SWTCR0's read/write bits 0 and bit 19
    read set, bit 18 setting unless `sticks` is false, the command done on
    the `polls`-th load of (8), SWTASR reading `asr`.  (11) is
    vg_read(i, words), after it."""
    s18 = B18 if sticks else 0
    return ([("R", 0x4D00, 0),                                    # (1)
             ("R", 0x4418, STA), ("W", 0x4418, STA | B18),        # (2)
             ("R", 0x4418, STA | s18),
             ("R", 0x4418, STA | s18),                            # (3)
             ("R", 0x4D00, 0)]                                    # (4)
            + [("W", 0x4D20 + 4 * k, words[k]) for k in range(7, -1, -1)]
            + [("W", 0x4D08, vg_addr(i)), ("W", 0x4D00, 9)]       # (6) (7)
            + [("R", 0x4D00, 9)] * (polls - 1) + [("R", 0x4D00, 0)]
            + [("R", 0x4418, STA | s18), ("W", 0x4418, STA),      # (9)
               ("R", 0x4418, STA), ("R", 0x4D04, asr)])           # (10)


def vg_head(cur, regs):
    """A call's accesses before its first store: the verified words, every
    slot, PVCR0-3 and FFCR."""
    seq = [("R", o, v) for o, v in VG_VER]
    for i in range(24):
        seq += vg_read(i, cur[i])
    return seq + [("R", VG_REG[r], regs[r]) for r in range(5)]


def vg_tail():
    """THE RE-READ of a group that equals its targets."""
    seq = []
    for i in range(24):
        seq += vg_read(i, vg_want(i))
    return (seq + [("R", VG_REG[r], VG_RVAL[r]) for r in range(5)]
            + [("R", o, v) for o, v in VG_VER])


def vg_full(cur, regs, writes, regw, **kw):
    """Every access of a call that runs to its end, and its IRQs-off groups:
    table writes of the items `writes` (kw to vg_write), then register
    stores of the indexes `regw`, then THE RE-READ."""
    seq, groups = vg_head(cur, regs), []
    for i in writes:
        g = vg_write(i, vg_want(i), **kw)
        groups.append(g)
        seq += g + vg_read(i, vg_want(i))
    for r in regw:
        seq += [("W", VG_REG[r], VG_RVAL[r]), ("R", VG_REG[r], VG_RVAL[r])]
    return seq + vg_tail(), groups


def vg_irq(run, i, groups):
    """Dump i's IRQs-off accesses are exactly `groups`, in order, each in a
    section of its own."""
    if i >= len(run.pacc):
        return False
    on = [x for x in run.pacc[i] if x[3] == 1]
    if [x[:3] for x in on] != [a for g in groups for a in g]:
        return False
    k, secs = 0, []
    for g in groups:
        s = {x[4] for x in on[k:k + len(g)]}
        k += len(g)
        if len(s) != 1:
            return False
        secs.append(s.pop())
    return len(set(secs)) == len(secs)


def vg_line(run, i):
    """The rest of 1.6's line in the i-th render."""
    return run.line14(i, "vlan")


def vg_end(run, i, regs=VG_RVAL, tab=None):
    """VSTAT i: PVCR0-3 and FFCR `regs`, the verified words as measured, no
    protocol slip but `nostop` (asked where it matters), and the tables:
    by default VLAN slot 8 alone, the RAM path's group minus netif slot 0."""
    tab = {("v", 8): ENTRY8} if tab is None else tab
    return (run.vst(i, "pvcr") == ",".join("%08X" % v
                                           for v in list(regs[:4]) + [1])
            and run.vst(i, "ffcr") == "%08X" % regs[4]
            and run.vst(i, "vcr0") == "000001FF"
            and run.vst(i, "pbvcr0") == "00000000"
            and run.vst(i, "plitimr") == "07FAC688"
            and all(run.vst(i, k) == "0"
                    for k in ("viol", "badaa", "badcmd", "illegal"))
            and run.vtab(i) == tab)


def first_diff(got, want):
    """Where two access lists part, for a case's detail."""
    if got is None:
        return "no dump"
    for k, (a, b) in enumerate(zip(got, want)):
        if a != b:
            return "#%d %s %04X %08X, want %s %04X %08X" % ((k,) + a + b)
    return ("none" if len(got) == len(want)
            else "lengths %d, want %d" % (len(got), len(want)))


def comment_figures16(block):
    """(1.6's line, the case that measures it, 1.5's total, 1.6's total,
    the recount's addition, the recounted page) as 1.6's comment states
    them, or None."""
    body = " ".join(re.sub(r"^\s*/?\*+/?\s?", "", ln).strip()
                    for ln in block.split("\n"))
    m = re.search(r"(\d+) bytes \(tools/mdiocheck\.py K(\d+) measures it\), "
                  r"so 1\.5's worst case of ([\d,]+) of 4,096 becomes "
                  r"([\d,]+)", body)
    m2 = re.search(r"at their types' widest they add (\d+), and the page is "
                   r"([\d,]+)", body)
    if not (m and m2):
        return None
    return tuple(int(g.replace(",", "")) for g in m.groups() + m2.groups())


def cases16(exe, exe_y, block):
    """Yield (name, ok, detail) for K47..K67: 1.6's `vlan`."""
    eperm, eproto, eio = -ERRNO["EPERM"], -ERRNO["EPROTO"], -ERRNO["EIO"]
    ebusy, etime = -ERRNO["EBUSY"], -ERRNO["ETIMEDOUT"]
    F, L = vg_start(0), vg_start(1)
    std = dict(calls=1, ok=1, rc=0, vw=0x100, rw=0x1F, vr=VG_VR,
               tlu=STA | B18, sta=1, spin=1, final=0, ld=784)

    # K47 the switch locked: refused before any access, counted -- and the
    # phyif class token does not open it; a refusal after a call that stored
    # shows that call's fields no more (only the counters and `ld` carry)
    r = Run(exe, [VLAN, "l", "pacc", "pstat", "vstat", PHYUNLOCK, VLAN, "l",
                  "pacc", "pstat", "vstat", SWUNLOCK, VLAN, "set swunlock 0",
                  VLAN, "l"])
    ok = (r.rc == 0
          and [x[1] for x in r.ops] == [eperm, len("unlock phyif-i-mean-it\n"),
                                        eperm, NVLAN, eperm]
          and vg_line(r, 0) == vg_fields(calls=1, refused=1, rc=eperm)
          and vg_line(r, 1) == vg_fields(calls=2, refused=2, rc=eperm)
          and acc(r, 0) == [] and acc(r, 1) == []
          and r.pst(1, "swrd") == "0" and r.pst(1, "sw_refused") == "0"
          and r.pst(1, "sw_writes") == "0" and r.vst(1, "winld") == "0"
          and vg_line(r, 2) == vg_fields(calls=4, ok=1, refused=3, rc=eperm,
                                         ld=784))
    yield "K47", ok, "ops %s, lines %s | %s" % ([x[1] for x in r.ops],
                                                vg_line(r, 1), vg_line(r, 2))

    # K48 the flash path, access by access: nothing stored before every
    # target is read; VLAN slot 8's (1)-(10) alone with IRQs off; the end
    # state is the RAM path's group minus netif slot 0
    r = Run(exe, [SWUNLOCK, VLAN, "pacc", "l", "pstat", "vstat", "stat"])
    want, groups = vg_full(F, VG_FREG, [8], range(5))
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_irq(r, 0, groups) and vg_line(r, 0) == vg_fields(**std)
          and r.pst(0, "sw_writes") == "17" and r.pst(0, "swrd") == "81"
          and r.pst(0, "illegal") == "0" and r.pst(0, "imbalance") == "0"
          and r.pst(0, "depth") == "0" and r.stat(0, "psrp_bad") == "0"
          and r.vst(0, "winld") == "784" and r.vst(0, "starts") == "1"
          and r.vst(0, "nostop") == "0" and r.vst(0, "swtcr0") == "00080000"
          and vg_end(r, 0))
    yield "K48", ok, "rc %s, %d accesses, first difference %s" % (
        r.op(0) if r.ops else "-", len(got or []), first_diff(got, want))

    # K49 the RAM path: netif slot 0 alone
    r = Run(exe, [SWUNLOCK, "set vgstate 1", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    want, groups = vg_full(L, VG_RVAL, [16], [])
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_irq(r, 0, groups)
          and vg_line(r, 0) == vg_fields(**dict(std, vw=0, nw=0x01, rw=0))
          and r.pst(0, "sw_writes") == "12" and r.pst(0, "swrd") == "76"
          and r.vst(0, "winld") == "784" and r.vst(0, "starts") == "1"
          and r.vst(0, "swtcr0") == "00080000" and vg_end(r, 0))
    yield "K49", ok, "rc %s, %d accesses, first difference %s" % (
        r.op(0) if r.ops else "-", len(got or []), first_diff(got, want))

    # K50 each verified word wrong in turn: refused after the four loads,
    # with no table load and no store
    bad = [0x00000002, 0x000001FE, 0x00000001, 0x07FAC689]
    oks = []
    for k, (off, _) in enumerate(VG_VER):
        r = Run(exe, [SWUNLOCK, "set vgreg %04X 0x%08X" % (off, bad[k]), VLAN,
                      "pacc", "l", "pstat", "vstat"])
        vr = list(VG_VR)
        vr[k] = bad[k]
        oks.append(r.rc == 0 and r.op(0) == eproto
                   and acc(r, 0) == [("R", o, bad[k] if o == off else v)
                                     for o, v in VG_VER]
                   and vg_line(r, 0) == vg_fields(calls=1, rc=eproto,
                                                  vm=1 << k, vr=tuple(vr))
                   and r.pst(0, "sw_writes") == "0"
                   and r.vst(0, "winld") == "0")
    yield "K50", len(oks) == 4 and all(oks), "PVCR4 VCR0 PBVCR0 PLITIMR %s" % oks

    # K51 a command that never completes: (8) gives up at the bound, and the
    # undo still runs, inside the same IRQs-off section
    r = Run(exe, [SWUNLOCK, "set vgstuck 1", VLAN, "pacc", "l", "pstat",
                  "vstat", "stat"])
    g = vg_write(8, ENTRY8)
    g = (g[:g.index(("W", 0x4D00, 9)) + 1] + [("R", 0x4D00, 9)] * 10001
         + [("R", 0x4418, STA | B18), ("W", 0x4418, STA), ("R", 0x4418, STA),
            ("R", 0x4D04, 0)])
    want = vg_head(F, VG_FREG) + g
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == etime and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=etime, at=8, step=8,
                                         vr=VG_VR, tlu=STA | B18, sta=1,
                                         spin=10001, ld=384, to=1)
          and r.vst(0, "swtcr0") == "00080000" and r.vtab(0) == {}
          and r.pst(0, "sw_writes") == "12" and r.stat(0, "dmax") == "10000")
    yield "K51", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K52 STOP_TLU_STA never set: (3) gives up, and the undo runs
    r = Run(exe, [SWUNLOCK, "set vgsta 0", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    g = ([("R", 0x4D00, 0), ("R", 0x4418, 0), ("W", 0x4418, B18),
          ("R", 0x4418, B18)] + [("R", 0x4418, B18)] * 10001
         + [("R", 0x4418, B18), ("W", 0x4418, 0), ("R", 0x4418, 0)])
    want = vg_head(F, VG_FREG) + g
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == etime and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=etime, at=8, step=3,
                                         vr=VG_VR, tlu=B18, sta=10001,
                                         ld=384, to=1)
          and r.vst(0, "swtcr0") == "00000000" and r.vst(0, "starts") == "0"
          and r.vtab(0) == {} and r.pst(0, "sw_writes") == "2")
    yield "K52", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K53 the engine stores a different word 0: the read-back refuses, the
    # undo already made, and nothing after it
    r = Run(exe, [SWUNLOCK, "set vgcorrupt 1", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    bad8 = [0x00807E3E] + [0] * 7
    g = vg_write(8, ENTRY8)
    want = vg_head(F, VG_FREG) + g + vg_read(8, bad8)
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == eio and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=eio, at=8, step=11,
                                         vr=VG_VR, tlu=STA | B18, sta=1,
                                         spin=1, ld=400, rb=1)
          and r.vst(0, "swtcr0") == "00080000"
          and r.vtab(0) == {("v", 8): bad8} and r.pst(0, "sw_writes") == "12"
          and vg_end(r, 0, regs=VG_FREG, tab={("v", 8): bad8}))
    yield "K53", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K54 bit 18 does not clear: -EIO at (9), SWTASR still read, the verb
    # stops there
    r = Run(exe, [SWUNLOCK, "set vgnoclear18 1", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    g = vg_write(8, ENTRY8)
    g[-2] = ("R", 0x4418, STA | B18)        # the undo's read-back: still set
    want = vg_head(F, VG_FREG) + g
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == eio and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=eio, at=8, step=9,
                                         vr=VG_VR, tlu=STA | B18, sta=1,
                                         spin=1, ld=384, rb=1)
          and r.vst(0, "swtcr0") == "000C0000" and r.pst(0, "sw_writes") == "12"
          and vg_end(r, 0, regs=VG_FREG))
    yield "K54", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K55 a second `vlan` on the same boot: every read again, no store --
    # so no read-back either: 768 window loads after the first call's 784
    r = Run(exe, [SWUNLOCK, VLAN, "pacc", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    cur = dict(F)
    cur[8] = ENTRY8
    want = vg_head(cur, VG_RVAL) + vg_tail()
    got = acc(r, 1)
    ok = (r.rc == 0 and [x[1] for x in r.ops] == [NVLAN, NVLAN]
          and got == want
          and vg_line(r, 0) == vg_fields(calls=2, ok=2, rc=0, vr=VG_VR,
                                         final=0, ld=784 + 768)
          and r.pst(0, "sw_writes") == "17" and r.pst(0, "swrd") == "147"
          and vg_end(r, 0))
    yield "K55", ok, "rcs %s, %d accesses, first difference %s" % (
        [x[1] for x in r.ops], len(got or []), first_diff(got, want))

    # K56 -DCONFIG_RTL_819X_SWCORE: the vendor's tables, no access at all
    if exe_y is None:
        yield "K56", False, "no SWCORE=y build"
    else:
        r = Run(exe_y, ["l", VLAN, SWUNLOCK, VLAN, "pacc", "l", "pstat",
                        "vstat"])
        ok = (r.rc == 0 and [x[1] for x in r.ops] == [eperm, NVLAN]
              and vg_line(r, 0) == "vendor calls 0 ok 0 refused 0 rc 1"
              and vg_line(r, 1) == "vendor calls 2 ok 1 refused 1 rc 0"
              and acc(r, 0) == [] and r.pst(0, "swrd") == "0"
              and r.pst(0, "sw_writes") == "0" and r.vst(0, "winld") == "0"
              and r.vst(0, "starts") == "0")
        yield "K56", ok, "rcs %s, line %s" % ([x[1] for x in r.ops],
                                             vg_line(r, 1))

    # K57 the `vlan` line at its widest against the block comment, and the
    # page's running total: 1.5's total + the measured line = 1.6's, under
    # the table's budget (3,600) and the page (4,096) -- also as recounted
    r = Run(exe, ["widest14", "widest15", "widest16", "l"])
    text, n = r.lines14[0] if r.lines14 else ("", -1)
    ls = text.split("\n")[:-1]
    w16 = len(ls[7]) + 1 if len(ls) == 8 else -1
    f15, f16 = comment_figures15(block), comment_figures16(block)
    wy = -1
    if exe_y is not None:
        ry = Run(exe_y, ["widest16", "l"])
        ty = ry.lines14[0][0].split("\n")[:-1] if ry.lines14 else []
        wy = len(ty[7]) + 1 if len(ty) == 8 else -1
    ok = (r.rc == 0 and len(ls) == 8 and n == len(text)
          and ls[7].startswith("vlan calls 4294967295 ok 4294967295 ")
          and f15 is not None and f16 is not None
          and f16[:4] == (w16, 57, f15[4], f15[4] + w16)
          and f16[5] == f16[3] + f16[4]
          and f16[3] <= 3600 and f16[5] <= 3600 and f16[5] <= PAGE
          and 0 < wy < w16)
    yield "K57", ok, "comment %s, measured %d (SWCORE=y %d)" % (f16, w16, wy)

    # K58 THE RE-READ: the engine also copies the entry into the next slot;
    # slot 8's own read-back passes and only the re-read can see slot 9
    r = Run(exe, [SWUNLOCK, "set vgghost 1", VLAN, "l", "pstat", "vstat"])
    ok = (r.rc == 0 and r.op(0) == eio
          and vg_line(r, 0) == vg_fields(**dict(std, ok=0, rc=eio, at=9,
                                                step=13, final=1, rb=1))
          and r.pst(0, "sw_writes") == "17"
          and vg_end(r, 0, tab={("v", 8): ENTRY8, ("v", 9): ENTRY8}))
    yield "K58", ok, "rc %s, line %s" % (r.op(0) if r.ops else "-",
                                         vg_line(r, 0))

    # K59 bit 18 does not read back set: recorded in `tlu`, not refused
    r = Run(exe, [SWUNLOCK, "set vgnostick18 1", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    want, groups = vg_full(F, VG_FREG, [8], range(5), sticks=False)
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_irq(r, 0, groups)
          and vg_line(r, 0) == vg_fields(**dict(std, tlu=STA))
          and r.pst(0, "sw_writes") == "17" and r.vst(0, "nostop") == "1"
          and vg_end(r, 0))
    yield "K59", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K60 the engine busy at (1): -EBUSY with nothing stored
    r = Run(exe, [SWUNLOCK, "set vgbusyat 24 10001", VLAN, "pacc", "l",
                  "pstat", "vstat"])
    g = [("R", 0x4D00, 1)] * 10001
    want = vg_head(F, VG_FREG) + g
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == ebusy and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=ebusy, at=8, step=1,
                                         vr=VG_VR, ld=384)
          and r.pst(0, "sw_writes") == "0" and r.vst(0, "starts") == "0"
          and r.vtab(0) == {})
    yield "K60", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K61 the engine busy at the first read: -EBUSY, no window load, no store
    r = Run(exe, [SWUNLOCK, "set vgbusyat 0 10001", VLAN, "pacc", "l",
                  "pstat", "vstat"])
    want = [("R", o, v) for o, v in VG_VER] + [("R", 0x4D00, 1)] * 10001
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == ebusy and got == want and vg_irq(r, 0, [])
          and vg_line(r, 0) == vg_fields(calls=1, rc=ebusy, at=0, step=0,
                                         vr=VG_VR)
          and r.pst(0, "sw_writes") == "0" and r.vst(0, "winld") == "0")
    yield "K61", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K62 PVCR2's store does not stick: -EIO at its read-back, PVCR3 and FFCR
    # never stored
    r = Run(exe, [SWUNLOCK, "set vgregnostick 4A10", VLAN, "pacc", "l",
                  "pstat", "vstat"])
    g = vg_write(8, ENTRY8)
    want = (vg_head(F, VG_FREG) + g + vg_read(8, ENTRY8)
            + [("W", 0x4A08, 0x00080008), ("R", 0x4A08, 0x00080008),
               ("W", 0x4A0C, 0x00080008), ("R", 0x4A0C, 0x00080008),
               ("W", 0x4A10, 0x00080008), ("R", 0x4A10, 0x00010001)])
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == eio and got == want
          and vg_line(r, 0) == vg_fields(calls=1, rc=eio, at=26, step=12,
                                         vw=0x100, rw=0x03, vr=VG_VR,
                                         tlu=STA | B18, sta=1, spin=1,
                                         ld=400, rb=1)
          and r.pst(0, "sw_writes") == "15"
          and vg_end(r, 0, regs=[0x00080008, 0x00080008, 0x00010001,
                                 0x00010001, 0]))
    yield "K62", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K63 slots that differ past their first word: VLAN slot 3 in word 5,
    # netif slot 6 in word 7 -- all eight words are compared
    r = Run(exe, [SWUNLOCK, "set vgtbl 6 3 5 0x00000400",
                  "set vgtbl 4 6 7 0x00000001", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    cur = dict(F)
    cur[3] = [0, 0, 0, 0, 0, 0x400, 0, 0]
    cur[22] = [0] * 7 + [1]
    want, groups = vg_full(cur, VG_FREG, [3, 8, 22], range(5))
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_irq(r, 0, groups)
          and vg_line(r, 0) == vg_fields(**dict(std, vw=0x108, nw=0x40, sta=3,
                                                spin=3, ld=816))
          and r.pst(0, "sw_writes") == "41" and vg_end(r, 0))
    yield "K63", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K64 SWTASR bit 0 set after the command: recorded, not refused
    r = Run(exe, [SWUNLOCK, "set vgreg 4D04 0x00000001", VLAN, "pacc", "l",
                  "pstat", "vstat"])
    want, groups = vg_full(F, VG_FREG, [8], range(5), asr=1)
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_line(r, 0) == vg_fields(**dict(std, swtasr=1))
          and vg_end(r, 0))
    yield "K64", ok, "rc %s, line %s" % (r.op(0) if r.ops else "-",
                                         vg_line(r, 0))

    # K65 a torn window read: one torn load is read again; ten torn double
    # reads end the call at that slot's first read, with nothing stored
    r = Run(exe, [SWUNLOCK, "set vgtear 1", VLAN, "pacc", "l",
                  "set vgtear 100000", VLAN, "pacc", "l", "pstat"])
    a0 = vg_addr(0)
    want1, _ = vg_full(F, VG_FREG, [8], range(5))
    torn = ([("R", 0x4D00, 0), ("T", a0, 1)]
            + [("T", a0 + 4 * k, 0) for k in range(1, 8)]
            + [("T", a0 + 4 * k, 0) for k in range(8)] * 3)
    want1 = want1[:4] + torn + want1[4 + 17:]
    want2 = ([("R", o, v) for o, v in VG_VER] + [("R", 0x4D00, 0)]
             + [("T", a0 + 4 * (k % 8), 2 + k) for k in range(160)])
    ok = (r.rc == 0 and [x[1] for x in r.ops] == [NVLAN, eio]
          and acc(r, 0) == want1 and acc(r, 1) == want2
          and vg_line(r, 0) == vg_fields(**dict(std, ld=800))
          and vg_line(r, 1) == vg_fields(calls=2, ok=1, rc=eio, at=0, step=0,
                                         vr=VG_VR, ld=960, rb=1)
          and r.pst(0, "sw_writes") == "17")
    yield "K65", ok, "rcs %s, line %s, first differences %s / %s" % (
        [x[1] for x in r.ops], vg_line(r, 1), first_diff(acc(r, 0), want1),
        first_diff(acc(r, 1), want2))

    # K66 a command busy for three polls: (8) polls four times, nothing is
    # stored or cleared while it runs, the result is the same
    r = Run(exe, [SWUNLOCK, "set vgbusy 3", VLAN, "pacc", "l", "pstat",
                  "vstat"])
    want, groups = vg_full(F, VG_FREG, [8], range(5), polls=4)
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == NVLAN and got == want
          and vg_irq(r, 0, groups)
          and vg_line(r, 0) == vg_fields(**dict(std, spin=4))
          and r.vst(0, "nostop") == "0" and vg_end(r, 0))
    yield "K66", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))

    # K67 the engine busy at (4), once STOP_TLU is set: -EBUSY, and the
    # undo still runs, inside the same IRQs-off section
    r = Run(exe, [SWUNLOCK, "set vgbusyat 25 10001", VLAN, "pacc", "l",
                  "pstat", "vstat"])
    g = ([("R", 0x4D00, 0),                                   # (1)
          ("R", 0x4418, STA), ("W", 0x4418, STA | B18),       # (2)
          ("R", 0x4418, STA | B18),
          ("R", 0x4418, STA | B18)]                           # (3)
         + [("R", 0x4D00, 1)] * 10001                         # (4)
         + [("R", 0x4418, STA | B18), ("W", 0x4418, STA),    # (9)
            ("R", 0x4418, STA)])
    want = vg_head(F, VG_FREG) + g
    got = acc(r, 0)
    ok = (r.rc == 0 and r.op(0) == ebusy and got == want and vg_irq(r, 0, [g])
          and vg_line(r, 0) == vg_fields(calls=1, rc=ebusy, at=8, step=4,
                                         vr=VG_VR, tlu=STA | B18, sta=1,
                                         ld=384)
          and r.vst(0, "swtcr0") == "00080000" and r.vst(0, "starts") == "0"
          and r.vtab(0) == {} and r.pst(0, "sw_writes") == "2")
    yield "K67", ok, "rc %s, line %s, first difference %s" % (
        r.op(0) if r.ops else "-", vg_line(r, 0), first_diff(got, want))


def build(block, version, work, tag, defines=()):
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
    p = subprocess.run(["gcc"] + CFLAGS + list(defines)
                       + ["-I", os.path.join(d, "include"), "-o", exe, hpath],
                       capture_output=True, text=True)
    return (exe if p.returncode == 0 else None), p.stdout + p.stderr


def evaluate(block, version, work, tag):
    """Every case over `block`, compiled twice (1.6's SWCORE=y arm is K56's
    and K57's), or (None, why) when either compile fails."""
    exe, out = build(block, version, work, tag)
    if exe is None:
        return None, out
    exe_y, out = build(block, version, work, tag + "y", SWCORE_Y)
    if exe_y is None:
        return None, out
    return {name: (ok, det)
            for name, ok, det in cases(exe, block, version, exe_y)}, ""


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
    # 1.4 (R6b-10): the phyif class
    ("M21", "phyif's own token is not asked", "K25",
     "\tif (!rtl819x_phyif_unlocked) {\n\t\trtl819x_phyif_n_refused++;\n"
     "\t\treturn -EPERM;\n\t}\n", ""),
    ("M22", "the port bound admits port 5", "K29",
     "buf[6] < '0' + RTL819X_PHYIF_NPORT",
     "buf[6] <= '0' + RTL819X_PHYIF_NPORT"),
    ("M23", "the store sets bit 1 as well", "K35",
     "\t\twant = r->pre | RTL819X_PCRP_ENPHYIF;",
     "\t\twant = r->pre | RTL819X_PCRP_ENPHYIF | 0x2u;"),
    ("M24", "the ExtPHYID identity check removed", "K31",
     "\tif (RTL819X_PCRP_EXTPHYID(r->pre) != n) {", "\tif (0) {"),
    ("M25", "the read-back is not compared", "K32",
     "\t\t\tif (r->rb != want) {", "\t\t\tif (0) {"),
    ("M26", "the read-back compares bit 0 alone", "K33",
     "\t\t\tif (r->rb != want) {",
     "\t\t\tif (!(r->rb & RTL819X_PCRP_ENPHYIF)) {"),
    ("M27", "a port already set is stored again", "K30",
     "\t} else if (r->pre & RTL819X_PCRP_ENPHYIF) {", "\t} else if (0) {"),
    ("M28", "`phyif all` goes on past a failed port", "K31",
     "\t\tif (rc)\n\t\t\tbreak;\n\t\ton |= 1u << n;",
     "\t\tif (!rc)\n\t\t\ton |= 1u << n;"),
    ("M29", "the pre-read made with IRQs on", "K27",
     "\tlocal_irq_save(flags);\n\tr->pre = rtl819x_sw_rd(off);",
     "\tr->pre = rtl819x_sw_rd(off);\n\tlocal_irq_save(flags);"),
    ("M30", "the switch's token opens the phyif class", "K26",
     "#define RTL819X_PHYIF_TOKEN\t\t\"phyif-i-mean-it\"",
     "#define RTL819X_PHYIF_TOKEN\t\t\"i-mean-it\""),
    ("M31", "a cat reads PCRP", "K24",
     "\t\tr = &rtl819x_phyif_res[n];\n",
     "\t\tr = &rtl819x_phyif_res[n];\n"
     "\t\t(void)rtl819x_sw_rd(RTL819X_SW_PCRP0 + 4 * n);\n"),
    ("M32", "a verb's results survive into the next verb's lines", "K28",
     "\t\trtl819x_phyif_res[n].rc = RTL819X_PHYIF_UNTRIED;\n", ""),
    # 1.5 (R6b-8 8d): `init` and the reset guard
    ("M33", "init without the lock check", "K37",
     "\tif (!rtl819x_sw_unlocked) {\t/* the switch's unlock, and only it */",
     "\tif (0) {"),
    ("M34", "init reads a port before refusing", "K37",
     "\trtl819x_sw_init_n++;\n\tif (!rtl819x_sw_unlocked) {",
     "\trtl819x_sw_init_n++;\n\t(void)rtl819x_sw_rd(RTL819X_SW_PCRP0);\n"
     "\tif (!rtl819x_sw_unlocked) {"),
    ("M35", "the phyif token opens init", "K42",
     "\tif (!rtl819x_sw_unlocked) {\t/* the switch's unlock, and only it */",
     "\tif (!rtl819x_sw_unlocked && !rtl819x_phyif_unlocked) {"),
    ("M36", "init asks the phyif token, not the switch's", "K42",
     "\tif (!rtl819x_sw_unlocked) {\t/* the switch's unlock, and only it */",
     "\tif (!rtl819x_phyif_unlocked) {"),
    ("M37", "init goes on past a failed port", "K40",
     "\t\tif (rc)\n\t\t\tbreak;\t\t/* the first port that fails ends it */\n"
     "\t\ton |= 1u << p;",
     "\t\tif (!rc)\n\t\t\ton |= 1u << p;"),
    ("M38", "init leaves the last verb's results in the lines", "K40",
     "\t\tr = &rtl819x_phyif_res[p];\n\t\tr->pre = r->rb = 0;\n"
     "\t\tr->rc = RTL819X_PHYIF_UNTRIED;\n\t\tr->st = 0;\n",
     "\t\tr = &rtl819x_phyif_res[p];\n\t\t(void)r;\n"),
    ("M39", "a port already set is stored again, seen by init", "K39",
     "\t} else if (r->pre & RTL819X_PCRP_ENPHYIF) {", "\t} else if (0) {"),
    ("M40", "1.4 no longer hands `init` to 1.5", "K38",
     "\t\treturn rtl819x_sw_v15_write(buf, count);\t/* 1.5 */",
     "\t\t(void)rtl819x_sw_v15_write;\n\t\treturn -EINVAL;"),
    ("M41", "the `init` line is not on the page", "K24",
     "\treturn len + rtl819x_sw_v15_lines(page + len);\t/* 1.5 */",
     "\t(void)rtl819x_sw_v15_lines;\n\treturn len;"),
    ("M42", "the guard tests TXCMD alone", "K44",
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {",
     "\tif (icr & RTL819X_CPUICR_TXCMD) {"),
    ("M43", "the guard tests RXCMD alone", "K44",
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {",
     "\tif (icr & RTL819X_CPUICR_RXCMD) {"),
    ("M44", "the guard refuses on any CPUICR bit", "K45",
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {",
     "\tif (icr) {"),
    ("M45", "the guard after a write: SSIR stored first", "K44",
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {",
     "\t(void)rtl819x_sw_wr(RTL819X_SW_SSIR, RTL819X_SW_FULL_RST);\n"
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {"),
    ("M46", "the reset entered before the guard's test", "K44",
     "\tif (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD)) {\n"
     "\t\trtl819x_sw_rst_n_busy++;\n\t\treturn -EBUSY;\n\t}\n"
     "\treturn rtl819x_sw_do_reset(vendor_recipe);",
     "\tif (!rtl819x_sw_do_reset(vendor_recipe) &&\n"
     "\t    (icr & (RTL819X_CPUICR_TXCMD | RTL819X_CPUICR_RXCMD))) {\n"
     "\t\trtl819x_sw_rst_n_busy++;\n\t\treturn -EBUSY;\n\t}\n\treturn 0;"),
    ("M47", "the guard loads CPUICR through rtl819x_sw_rd", "K44",
     "\tu32 icr = __raw_readl((void __iomem *)KSEG1ADDR(RTL819X_CPUICR_PHYS));",
     "\tu32 icr = rtl819x_sw_rd((unsigned int)RTL819X_CPUICR_PHYS -\n"
     "\t\t\t\tRTL819X_SW_PHYS);"),
    ("M48", "a refused reset is not counted", "K44",
     "\t\trtl819x_sw_rst_n_busy++;\n\t\treturn -EBUSY;", "\t\treturn -EBUSY;"),
    ("M49", "a refused init is not counted", "K37",
     "\t\trtl819x_sw_init_n_refused++;\n\t\trtl819x_sw_init_rc = -EPERM;",
     "\t\trtl819x_sw_init_rc = -EPERM;"),
    # 1.6 (R6c): `vlan`.  No mutant removes a bound: it would hang the
    # harness rather than turn a case red.
    ("M50", "vlan without the lock check", "K47",
     "\tif (!rtl819x_sw_unlocked) {\t/* before any access: nothing is read */",
     "\tif (0) {"),
    ("M51", "a refused vlan is not counted", "K47",
     "\t\trtl819x_vlan_n_refused++;\n\t\trtl819x_vlan_rc = -EPERM;",
     "\t\trtl819x_vlan_rc = -EPERM;"),
    ("M52", "TCR0 stored first, TCR7 last", "K48",
     "\tfor (k = RTL819X_VLAN_NW; k-- > 0; ) {",
     "\tfor (k = 0; k < RTL819X_VLAN_NW; k++) {"),
    ("M53", "the command is ADD (3), not force (9)", "K48",
     "\t\t\t   RTL819X_VLAN_ACTION | RTL819X_VLAN_FORCE);",
     "\t\t\t   RTL819X_VLAN_ACTION | (1u << 1));"),
    ("M54", "the registers stored last to first, FFCR first", "K48",
     "\tfor (i = 0; i < RTL819X_VLAN_NREG; i++) {\n"
     "\t\tif (reg[i] == rtl819x_vlan_rval[i])",
     "\tfor (i = RTL819X_VLAN_NREG; i-- > 0; ) {\n"
     "\t\tif (reg[i] == rtl819x_vlan_rval[i])"),
    ("M55", "STOP_TLU never set", "K48",
     "\trc = rtl819x_sw_wr(RTL819X_VLAN_SWTCR0, v | RTL819X_VLAN_STOP_TLU);",
     "\trc = rtl819x_sw_wr(RTL819X_VLAN_SWTCR0, v);"),
    ("M56", "a slot equal to its target is written anyway", "K49",
     "\t\tif (!memcmp(rtl819x_vlan_cur[i], w, sizeof(w)))\n"
     "\t\t\tcontinue;\t\t/* equal: not stored */",
     "\t\t(void)rtl819x_vlan_cur;"),
    ("M57", "PLITIMR is not verified", "K50",
     "\t\tif (rtl819x_vlan_vr[i] != rtl819x_vlan_vval[i])",
     "\t\tif (rtl819x_vlan_vr[i] != rtl819x_vlan_vval[i] && i != 3)"),
    ("M58", "a verified word refused only after the tables are read", "K50",
     "\tif (rtl819x_vlan_vm)\n\t\treturn -EPROTO;\t\t/* no table read, nothing stored */\n"
     "\tfor (i = 0; i < RTL819X_VLAN_NSLOT; i++) {\n"
     "\t\trtl819x_vlan_at = (int)i;\n"
     "\t\trc = rtl819x_vlan_read(i, rtl819x_vlan_cur[i]);\n"
     "\t\tif (rc)\n\t\t\treturn rc;\t/* step 0, nothing stored */\n\t}\n",
     "\tfor (i = 0; i < RTL819X_VLAN_NSLOT; i++) {\n"
     "\t\trtl819x_vlan_at = (int)i;\n"
     "\t\trc = rtl819x_vlan_read(i, rtl819x_vlan_cur[i]);\n"
     "\t\tif (rc)\n\t\t\treturn rc;\n\t}\n"
     "\tif (rtl819x_vlan_vm)\n\t\treturn -EPROTO;\n"),
    ("M59", "no undo after (8) gives up", "K51",
     "\t\t\trc = -ETIMEDOUT;\n\t\t\tbreak;",
     "\t\t\trc = -ETIMEDOUT;\n\t\t\tgoto out;"),
    ("M60", "no undo after (3) gives up", "K52",
     "\t\t\trc = -ETIMEDOUT;\n\t\t\tgoto undo;",
     "\t\t\trc = -ETIMEDOUT;\n\t\t\tgoto out;"),
    ("M61", "the slot's read-back is not compared", "K53",
     "\tif (!rc && memcmp(rb, w, sizeof(rb)))\n\t\trc = -EIO;",
     "\tif (0)\n\t\trc = -EIO;"),
    ("M62", "the undo's read-back is not checked", "K54",
     "\tif (rtl819x_sw_wr(RTL819X_VLAN_SWTCR0, v & ~RTL819X_VLAN_STOP_TLU) ||\n"
     "\t    (rtl819x_sw_rd(RTL819X_VLAN_SWTCR0) & RTL819X_VLAN_STOP_TLU)) {",
     "\tif (rtl819x_sw_wr(RTL819X_VLAN_SWTCR0, v & ~RTL819X_VLAN_STOP_TLU)) {"),
    ("M63", "VLAN slot 8 written whether or not it differs", "K55",
     "\t\tif (!memcmp(rtl819x_vlan_cur[i], w, sizeof(w)))\n"
     "\t\t\tcontinue;\t\t/* equal: not stored */",
     "\t\tif (!memcmp(rtl819x_vlan_cur[i], w, sizeof(w)) &&\n"
     "\t\t    i != RTL819X_VLAN_SLOT)\n\t\t\tcontinue;"),
    ("M64", "the SWCORE=y arm reads a register", "K56",
     "\trc = 0;\t\t/* the vendor's tables: nothing read or stored */",
     "\trc = (int)(rtl819x_sw_rd(0x4A08) & 0u);"),
    ("M65", "the line prints vw in eight digits", "K57",
     "\"rc %d at %d step %u vw %04X nw %02X rw %02X \"",
     "\"rc %d at %d step %u vw %08X nw %02X rw %02X \""),
    ("M66", "THE RE-READ is skipped", "K58",
     "\trtl819x_vlan_at = -1;\n\trc = rtl819x_vlan_reread();",
     "\trtl819x_vlan_at = -1;\n\trc = 0;\n\t(void)rtl819x_vlan_reread;"),
    ("M67", "a bit 18 that does not read back refuses", "K59",
     "\trtl819x_vlan_tlu = rtl819x_sw_rd(RTL819X_VLAN_SWTCR0);\t/* recorded */",
     "\trtl819x_vlan_tlu = rtl819x_sw_rd(RTL819X_VLAN_SWTCR0);\n"
     "\tif (!(rtl819x_vlan_tlu & RTL819X_VLAN_STOP_TLU)) {\n"
     "\t\trc = -EIO;\n\t\tgoto undo;\n\t}"),
    ("M68", "(1)'s idle poll removed", "K60",
     "\trtl819x_vlan_step = 1;\n\trc = rtl819x_vlan_idle();\n\tif (rc)\n"
     "\t\tgoto out;\t\t\t/* nothing stored */",
     "\trtl819x_vlan_step = 1;\n\trc = 0;"),
    ("M69", "the table read's idle poll removed", "K61",
     "\tif (rtl819x_vlan_idle())\n\t\treturn -EBUSY;\n\tfor (tries = 1; ; tries++) {",
     "\tfor (tries = 1; ; tries++) {"),
    ("M70", "a register's read-back is not compared", "K62",
     "\tif (rtl819x_sw_rd(rtl819x_vlan_roff[r]) != rtl819x_vlan_rval[r])\n"
     "\t\treturn -EIO;",
     "\t(void)rtl819x_sw_rd(rtl819x_vlan_roff[r]);"),
    ("M71", "a slot compared on its first word only", "K63",
     "\t\tif (!memcmp(rtl819x_vlan_cur[i], w, sizeof(w)))\n"
     "\t\t\tcontinue;\t\t/* equal: not stored */",
     "\t\tif (rtl819x_vlan_cur[i][0] == w[0])\n\t\t\tcontinue;"),
    ("M72", "SWTASR bit 0 refuses", "K64",
     "\tif (issued)\n\t\trtl819x_vlan_asr |= rtl819x_sw_rd(RTL819X_VLAN_SWTASR);",
     "\tif (issued) {\n\t\trtl819x_vlan_asr |= rtl819x_sw_rd(RTL819X_VLAN_SWTASR);\n"
     "\t\tif (rtl819x_vlan_asr & 1u)\n\t\t\trc = -EIO;\n\t}"),
    ("M73", "ten unequal double reads keep the second buffer", "K65",
     "\t\tif (tries >= RTL819X_VLAN_TRIES)\n\t\t\treturn -EIO;",
     "\t\tif (tries >= RTL819X_VLAN_TRIES)\n\t\t\treturn 0;"),
    ("M74", "(8) polls once and goes on", "K66",
     "\t\trtl819x_vlan_spin++;\n"
     "\t\tif (!(rtl819x_sw_rd(RTL819X_VLAN_SWTACR) & RTL819X_VLAN_ACTION))\n"
     "\t\t\tbreak;",
     "\t\trtl819x_vlan_spin++;\n\t\t(void)rtl819x_sw_rd(RTL819X_VLAN_SWTACR);\n"
     "\t\tbreak;"),
    ("M75", "the write and its read-back address slot + 1", "K48",
     "\tlocal_irq_save(flags);\n\trtl819x_vlan_step = 1;",
     "\ti++;\n\tlocal_irq_save(flags);\n\trtl819x_vlan_step = 1;"),
    # M76-M81 each change what one case alone can see: the accesses of
    # every other case stay as they were
    ("M76", "a refused call keeps the last call's fields", "K47",
     "\trtl819x_vlan_n++;\n#ifndef CONFIG_RTL_819X_SWCORE\n"
     "\trtl819x_vlan_clear();\n#endif\n"
     "\tif (!rtl819x_sw_unlocked) {\t/* before any access: nothing is read */\n"
     "\t\trtl819x_vlan_n_refused++;\n\t\trtl819x_vlan_rc = -EPERM;\n"
     "\t\treturn -EPERM;\n\t}\n",
     "\trtl819x_vlan_n++;\n\tif (!rtl819x_sw_unlocked) {\n"
     "\t\trtl819x_vlan_n_refused++;\n\t\trtl819x_vlan_rc = -EPERM;\n"
     "\t\treturn -EPERM;\n\t}\n#ifndef CONFIG_RTL_819X_SWCORE\n"
     "\trtl819x_vlan_clear();\n#endif\n"),
    ("M77", "a failed undo does not end the verb", "K54",
     "\t\trtl819x_vlan_step = 9;\n\t\trc = -EIO;",
     "\t\trtl819x_vlan_step = 9;"),
    ("M78", "the comment's line figure is a byte short", "K57",
     "): 279\n * bytes (tools/mdiocheck.py K57",
     "): 278\n * bytes (tools/mdiocheck.py K57"),
    ("M79", "THE RE-READ compares VLAN slots 0-8 only", "K58",
     "\t\tif (memcmp(w, t, sizeof(w)) && !n++)",
     "\t\tif (i <= RTL819X_VLAN_SLOT && memcmp(w, t, sizeof(w)) && !n++)"),
    ("M80", "(1)'s busy answer ignored", "K60",
     "\trtl819x_vlan_step = 1;\n\trc = rtl819x_vlan_idle();\n\tif (rc)\n"
     "\t\tgoto out;\t\t\t/* nothing stored */",
     "\trtl819x_vlan_step = 1;\n\t(void)rtl819x_vlan_idle();\n\trc = 0;"),
    ("M81", "the table read's busy answer ignored", "K61",
     "\tif (rtl819x_vlan_idle())\n\t\treturn -EBUSY;\n\tfor (tries = 1; ; tries++) {",
     "\t(void)rtl819x_vlan_idle();\n\tfor (tries = 1; ; tries++) {"),
    ("M82", "(4)'s busy answer skips the undo", "K67",
     "\trtl819x_vlan_step = 4;\n\trc = rtl819x_vlan_idle();\n\tif (rc)\n\t\tgoto undo;",
     "\trtl819x_vlan_step = 4;\n\trc = rtl819x_vlan_idle();\n\tif (rc)\n\t\tgoto out;"),
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
    print("mdiocheck 1.3")
    print("  source  %s  (block %d lines, version %r)"
          % (a.source, block.count("\n"), version))
    try:
        exe, out = build(block, version, work, "M0")
        if exe is None:
            print("  FAIL K0  the block does not compile in the harness:")
            print(out)
            return 1
        exe_y, out = build(block, version, work, "M0y", SWCORE_Y)
        if exe_y is None:
            print("  FAIL K0  the block does not compile with %s:"
                  % " ".join(SWCORE_Y))
            print(out)
            return 1
        probe = Run(exe, [])
        eok = probe.errno == ERRNO and probe.bound == 10000
        print("  %s K0  compiles with %s, and again with %s; errno %s; "
              "bound %s"
              % ("ok  " if eok else "FAIL", " ".join(CFLAGS),
                 " ".join(SWCORE_Y),
                 "= arch/rlx's" if probe.errno == ERRNO else probe.errno,
                 probe.bound))
        fails = 0 if eok else 1
        results = {}
        for name, ok, det in cases(exe, block, version, exe_y):
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
