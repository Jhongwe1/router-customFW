/* src/rlxboot/handoff.h -- P6r-10: what a slot boot hands the kernel, in
 * a0..a3, through rtkload.  rlxfw's own code.
 *
 * Asm-safe: #defines only, no suffix on the constants, so jump.S can include
 * it; `RLXB_HANDOFF_CHECK` is for C.  A BUILD_ID input (MY_HDR).  The kernel
 * restates the three constants in include/linux/rlxfw-handoff.h and a host
 * test compares the two.  The design is notes/self-update.md § 1.
 */
#ifndef RLXBOOT_HANDOFF_H
#define RLXBOOT_HANDOFF_H

#define RLXB_HANDOFF_MAGIC   0x524C5848     /* "RLXH"                        */
#define RLXB_HANDOFF_SLOT_A  0x41           /* 'A', what RLXBOOT-SLOT prints */
#define RLXB_HANDOFF_SLOT_B  0x42
/* C only: the check word.  Not cryptographic -- notes/self-update.md § 1.6. */
#define RLXB_HANDOFF_CHECK(slot, ver) \
	((~(RLXB_HANDOFF_MAGIC ^ (unsigned long)(slot) ^ (unsigned long)(ver))) & 0xFFFFFFFFUL)

#endif
