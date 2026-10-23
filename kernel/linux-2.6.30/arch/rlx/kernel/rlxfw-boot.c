/*
 * rlxfw-boot -- the kernel side of the boot handoff.   P6r-10.
 *
 * THIS FILE IS NOT REALTEK'S.  It is staged into arch/rlx/kernel/ from kernel/
 * by tools/rlxfw-marks.py, and config/rlxfw-marks.tsv's MK14 is the Kbuild
 * line that links it.  The design is notes/self-update.md § 1.4.
 *
 * WHAT IT IS.  rlxboot leaves magic, slot, version and a check word in a0..a3
 * when it boots a flash slot (src/rlxboot/handoff.h), rtkload carries them to
 * kernel_entry, and head.S stores them in fw_arg0..fw_arg3 after the .bss
 * clear (READ: the drop's arch/rlx/kernel/head.S:141-144).  This file is the
 * one reader.  An arch_initcall reads the four words once, parses them with
 * rlxfw_handoff_parse() (include/linux/rlxfw-handoff.h), latches the verdict
 * and the raw a0, prints ONE line through rlxfw_puts, and only then creates
 * /proc/rlxfw-boot, so no reader can see the node before the latch:
 *
 *     handoff valid   RLXFW-HANDOFF slot=B ver=6                 slot B ver 6
 *     anything else   RLXFW-HANDOFF none why=magic a0=00000000   none
 *
 * The console line is rlxboot's `RLXBOOT-HANDOFF slot=B ver=6` seen from the
 * kernel, and its name keeps it apart from the boot ladder's RLXFW-B00..B10.
 *
 * The console line, the node and rlxfw_boot_handoff() all branch on one
 * predicate, rlxfw_boot_valid(), over a latch nothing writes twice.  A gate
 * reads the node, never the console line.
 *
 * WHAT IT IS NOT.  Not evidence that rlxboot booted this image: the check
 * word catches registers that are not a handoff, not an attacker, and code
 * typed at the loader's prompt can set any four values (the note's § 1.6).
 * Not a writer: no register, no flash, no fw_arg.  Not a PROM reader: READ,
 * nothing in the built kernel reads fw_arg0..3 as an argument vector, and
 * the kernel build refuses a System.map holding prom_argc or _prom_argv
 * (tools/rlxfw-kbuild.sh, fwarg_check).
 *
 * WHY arch_initcall (3).  READ init/main.c: proc_root_init() runs inside
 * start_kernel, before rest_init() and so before every initcall.  The
 * callers are the install path in rtl819x-spi.c, a late_initcall (7) driver
 * whose verbs arrive as /proc writes after boot, so the latch is in place
 * before the first of them.  No EXPORT_SYMBOL: the callers are built in and
 * link against the global symbol, and with CONFIG_MODULES unset (the board
 * template) the macro is empty (include/linux/module.h).
 *
 * WHAT A GREEN HOST TEST SAYS.  tools/test-spi-install.c's group M drives
 * rlxfw_handoff_parse refusing and permitting and holds its constants and
 * check word equal to rlxboot's.  It does not compile this file: the
 * initcall, the two formats, the /proc handler and the latch are read here
 * and nowhere tested, and nothing on the host says what a0..a3 hold at kernel
 * entry on the die -- the first slot boot's /proc/rlxfw-boot is that reading.
 */

#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/proc_fs.h>
#include <linux/rlxfw-mark.h>
#include <linux/rlxfw-handoff.h>
#include <asm/bootinfo.h>		/* fw_arg0..fw_arg3, the vendor's own */

/*
 * The node is the reading every gate takes (notes/self-update.md § 1.4), and
 * CONFIG_PROC_FS=y comes from the vendor's board template, which rlxfw does
 * not change -- so, as rlxfw_mark.c does for CONFIG_EARLY_PRINTK, the
 * dependency is asserted where it is used rather than left to fail silently.
 */
#ifndef CONFIG_PROC_FS
#error "rlxfw-boot creates /proc/rlxfw-boot, which every gate reads. \
CONFIG_PROC_FS is =y in the vendor board template and rlxfw does not change \
it; without it the node would be silently absent, so this build stops."
#endif

/* The node's name.  Not MK14's witness: the userspace that reads the node
 * carries this string too, so MK14 witnesses sym:rlxfw_boot_handoff. */
#define RLXFW_BOOT_PROC_NAME	"rlxfw-boot"

/*
 * The latch.  Written once, by rlxfw_boot_init, before the node exists, and
 * never again.  INFERRED: CONFIG_SMP is unset, so these plain stores are
 * seen by every later reader without a barrier.
 */
static int rlxfw_boot_latched;
static int rlxfw_boot_why;	/* RLXFW_HO_*: the parse's verdict */
static u32 rlxfw_boot_a0;	/* the raw a0, for the none line */
static u32 rlxfw_boot_slot;	/* RLXFW_HANDOFF_SLOT_A or _B, iff valid */
static u32 rlxfw_boot_ver;	/* 1 .. 0xFFFFFFFE, iff valid */

/* The one predicate the console line, the node and the accessor read. */
static int rlxfw_boot_valid(void)
{
	return rlxfw_boot_latched && rlxfw_boot_why == RLXFW_HO_OK;
}

/*
 * The contract is include/linux/rlxfw-handoff.h's: 0 with *slot and *ver set
 * when the latched handoff was valid; -ENOENT, touching neither, otherwise --
 * a failed check, or a call before the latch.  Latched statics only: no
 * sleep, no allocation, no lock, so it is callable under the SPI driver's.
 */
int rlxfw_boot_handoff(u32 *slot, u32 *ver)
{
	if (!rlxfw_boot_valid())
		return -ENOENT;
	*slot = rlxfw_boot_slot;
	*ver = rlxfw_boot_ver;
	return 0;
}

static const char *rlxfw_boot_why_name(int why)
{
	switch (why) {
	case RLXFW_HO_MAGIC:
		return "magic";
	case RLXFW_HO_CHECK:
		return "check";
	case RLXFW_HO_SLOT:
		return "slot";
	case RLXFW_HO_VERSION:
		return "version";
	}
	return "?";	/* unreachable: the parse returns one of the five */
}

/*
 * 2.6.30's read_proc_t in the shape the project's other nodes use
 * (rlxfw-entropy.c, rtl819x-spi.c): the whole text from offset 0, *start
 * left NULL, *eof set -- at most 22 bytes ("slot B ver 4294967294\n"), far
 * inside the one page.  One `cat` is two calls (SPEC.md FW-64): READ
 * fs/proc/generic.c, the second arrives with off at the first call's length,
 * and this returns 0 there itself rather than leaving the subtraction to
 * proc_file_read.  The text is rendered from the latch, which never changes,
 * so the two calls render the same bytes and FW-64's grown-by-one-digit case
 * cannot arise; a partial read at 0 < off < len gets the rest, sliced by
 * proc_file_read from the same text.
 */
static int rlxfw_boot_read_proc(char *page, char **start, off_t off,
				int count, int *eof, void *data)
{
	int len;

	if (rlxfw_boot_valid())
		len = sprintf(page, "slot %c ver %u\n", (int)rlxfw_boot_slot,
			      rlxfw_boot_ver);
	else
		len = sprintf(page, "none\n");
	*eof = 1;
	if (off >= len)
		return 0;
	return len;
}

static int __init rlxfw_boot_init(void)
{
	struct proc_dir_entry *pde;
	char line[64];
	u32 a0, a1, a2, a3;
	u32 slot = 0, ver = 0;
	int why;

	/* The only read of fw_arg0..3, each word once. */
	a0 = (u32)fw_arg0;
	a1 = (u32)fw_arg1;
	a2 = (u32)fw_arg2;
	a3 = (u32)fw_arg3;
	why = rlxfw_handoff_parse(a0, a1, a2, a3, &slot, &ver);

	rlxfw_boot_a0 = a0;
	rlxfw_boot_why = why;
	if (why == RLXFW_HO_OK) {
		rlxfw_boot_slot = slot;
		rlxfw_boot_ver = ver;
	}
	rlxfw_boot_latched = 1;

	/* One line per boot, from the latch, through prom_putchar. */
	if (rlxfw_boot_valid())
		snprintf(line, sizeof(line), "RLXFW-HANDOFF slot=%c ver=%u\n",
			 (int)rlxfw_boot_slot, rlxfw_boot_ver);
	else
		snprintf(line, sizeof(line), "RLXFW-HANDOFF none why=%s a0=%08x\n",
			 rlxfw_boot_why_name(rlxfw_boot_why), rlxfw_boot_a0);
	rlxfw_puts(line);

	/* Last, so the node never shows a state the latch was not in.  On
	 * failure the accessor still answers from the latch and every gate
	 * reads no node, which fails closed. */
	pde = create_proc_entry(RLXFW_BOOT_PROC_NAME, 0444, NULL);
	if (!pde)
		return -ENOMEM;
	pde->read_proc = rlxfw_boot_read_proc;
	return 0;
}
arch_initcall(rlxfw_boot_init);
