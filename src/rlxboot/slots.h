/* src/rlxboot/slots.h -- R8b: boot from flash slot A or slot B.
 * rlxfw's own code.
 *
 * THE RULE (the R8b spec's D4, not chosen here): verify slot A and slot B,
 * boot the valid one with the higher container version, boot A on a tie, and
 * VERIFY THE BYTES THAT ARE BOOTED -- each slot is copied into a RAM buffer of
 * its own, verified there, and the winner is booted from its buffer.  Nothing
 * is read from flash after a slot's verdict, so there is no second copy whose
 * bytes could differ from the ones that were checked.  No valid slot: each
 * slot's refusal is printed and the caller halts.
 *
 * Like `container.c`, nothing in `slots.c` touches hardware: the flash window,
 * the buffers and the console arrive in the structures below, so the same
 * translation unit runs on the host against a 4 MiB array standing in for the
 * part (`test/t_slots.c`), under qemu-mips-static big-endian, and on the
 * device.  What the host cannot reach is `main.c`'s halt and jump.
 */
#ifndef RLXBOOT_SLOTS_H
#define RLXBOOT_SLOTS_H

#include "container.h"

/* One progress dot per 64 KiB copied: 16,384 word loads through the window,
 * ~34 ms at `FLS-11`'s 2.075 us a load (推 for this loop -- that figure is
 * probe3's), so a copy that has stopped shows as dots that stopped. */
#define RLXB_TICK_BYTES   0x10000UL

struct rlxb_slot {
	char name;                        /* 'A' or 'B' -- what the console says */
	/* DEVICE numbers: what the console prints and what `rlxu_env` compares.
	 * On the host they stay the device's, exactly as `t_container.c` keeps
	 * `buf_base` at 0x81000000 while it verifies a host array. */
	unsigned long flash_off;          /* the slot's base, an offset into the part */
	unsigned long size;               /* bytes it spans; a multiple of 4 */
	unsigned long buf_addr;           /* its RAM buffer's address */
	/* The pointers actually read and written.  32-bit words: `unsigned int`
	 * is 32 bits under both ABIs this file is built for, and `slots.c`
	 * refuses to compile where it is not. */
	const volatile unsigned int *src; /* the slot's first word, through the window */
	unsigned int *buf;                /* the buffer's first word */
	/* What happened.  `copied` bounds everything `rlxu_verify` may read. */
	unsigned long copied;
	int reason;                       /* RLXU_OK, or the refusal */
	struct rlxu r;                    /* rlxu_verify's parse of the COPY */
};

/* The console, one byte at a time.  The device passes `rlx_putc`. */
struct rlxb_io {
	void (*emit)(int c);
};

/* Copy one slot into its buffer and verify the copy.  `e` supplies everything
 * but the buffer window and the flash comparison, which come from `s`.
 * Prints the slot's READ line and its VERDICT line; `rep` is passed through
 * to `rlxu_verify` for the per-stage lines.  Returns s->reason. */
int rlxb_slot_run(struct rlxb_slot *s, const struct rlxu_env *e,
                  rlxu_report_fn rep, const struct rlxb_io *io);

/* D4's choice over two slots that have run.  `a` wins a tie.  0 when neither
 * verified.  Pure: reads only the two verdicts and the two versions. */
struct rlxb_slot *rlxb_choose(struct rlxb_slot *a, struct rlxb_slot *b);

/* Run `a`, then `b`, choose, and print `RLXBOOT-SLOT <name>` or, when neither
 * verified, `RLXBOOT-HALT A=<reason> B=<reason>`.  Returns the winner or 0;
 * halting is the caller's. */
struct rlxb_slot *rlxb_select(struct rlxb_slot *a, struct rlxb_slot *b,
                              const struct rlxu_env *e, rlxu_report_fn rep,
                              const struct rlxb_io *io);

/* The first payload byte the boot copies from: inside the winner's own
 * buffer, which is where `rlxu_verify` hashed it. */
const unsigned char *rlxb_boot_body(const struct rlxb_slot *s);

#endif /* RLXBOOT_SLOTS_H */
