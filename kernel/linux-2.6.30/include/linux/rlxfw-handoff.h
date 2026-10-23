/*
 * rlxfw-handoff -- the boot handoff rlxboot leaves in a0..a3 and rtkload
 * carries to kernel_entry, which stores it in fw_arg0..fw_arg3.
 *
 * THIS FILE IS NOT REALTEK'S.  P6r-10, 2026-10-23 (144th segment).  Pure, no
 * #include of its own: the includer supplies u32.  Included by
 * arch/rlx/kernel/rlxfw-boot.c, by drivers/mtd/devices/rtl819x-spi.c and by
 * the host tests.  The design is notes/self-update.md § 1.4.
 */
#ifndef _LINUX_RLXFW_HANDOFF_H
#define _LINUX_RLXFW_HANDOFF_H

/* src/rlxboot/handoff.h's three constants, restated; a host test compares
 * them with that file. */
#define RLXFW_HANDOFF_MAGIC	0x524C5848u	/* "RLXH" */
#define RLXFW_HANDOFF_SLOT_A	0x41u		/* 'A', what RLXBOOT-SLOT prints */
#define RLXFW_HANDOFF_SLOT_B	0x42u

enum { RLXFW_HO_OK = 0, RLXFW_HO_MAGIC, RLXFW_HO_CHECK, RLXFW_HO_SLOT, RLXFW_HO_VERSION };

/* The checks in this order; the first that fails is the reason.  The version
 * range is RLXU_VER_MIN..RLXU_VER_MAX (src/rlxboot/container.h). */
static inline int rlxfw_handoff_parse(u32 a0, u32 a1, u32 a2, u32 a3, u32 *slot, u32 *ver)
{
	if (a0 != RLXFW_HANDOFF_MAGIC)
		return RLXFW_HO_MAGIC;
	if (a3 != ~(a0 ^ a1 ^ a2))
		return RLXFW_HO_CHECK;
	if (a1 != RLXFW_HANDOFF_SLOT_A && a1 != RLXFW_HANDOFF_SLOT_B)
		return RLXFW_HO_SLOT;
	if (a2 < 1u || a2 > 0xFFFFFFFEu)
		return RLXFW_HO_VERSION;
	*slot = a1;
	*ver = a2;
	return RLXFW_HO_OK;
}

/* Defined in arch/rlx/kernel/rlxfw-boot.c.  0, with *slot (RLXFW_HANDOFF_SLOT_A
 * or _B) and *ver set, when the handoff latched at boot was valid; -ENOENT,
 * with neither touched, otherwise -- a handoff that failed a check, or a call
 * before the latch.  The callers are the install path's counter tie and its
 * running-slot fence (notes/self-update.md §§ 2.4.5, 2.5). */
int rlxfw_boot_handoff(u32 *slot, u32 *ver);

#endif
