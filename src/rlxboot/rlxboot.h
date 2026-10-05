/* src/rlxboot/rlxboot.h -- rlxboot's own declarations and the R8a memory map.
 *
 * THE MAP IS SPEC-R8a.md s4's, and every address here is pinned there rather
 * than chosen here.  A number in this file that disagrees with that spec is a
 * bug in this file.
 *
 *   0x80000000 .. 0x81FFFFFF   RAM, 32 MiB (SPEC s4)
 *   0x80400000 .. 0x8041FFFF   stage 2's code and data -- not a destination
 *   0x80500000                 where a normal payload's load_addr points
 *   0x81000000                 the container, staged by the loader's TFTP
 *                              (BOOT=ram); slot A's buffer (BOOT=slots)
 *   0x81200000                 slot B's buffer (BOOT=slots; R8b, not SPEC-R8a)
 *   0x81700000                 the RAM-staged counter: "RCNT" then 512 bytes
 *   0x81800000                 rlxboot itself, load and entry
 *   0xBD000000                 the flash MMIO read window (SPEC.md FLS-11)
 *   0xBD070000, 0xBD190000     slots A and B through it (BOOT=slots)
 *   0xBD3F0000                 the 512-byte anti-rollback bitmap
 *
 * ⚠️ 0x81000000 IS THE ONE ADDRESS IN RAM THIS PROJECT HAS MEASURED BEING
 * REWRITTEN.  `MEM-14`: word 1 of 0x81000000 is rewritten to 0x00000144 on every
 * boot, three times reproduced -- which is `tools/rlxprobe/Makefile`'s reason for
 * putting probe1's result block at 0x80A00000 instead.  Word 1 of a container is
 * `format` and `header_len`, so a boot between the upload and the `J` corrupts
 * the container into `RLXBOOT-HDR bad=format`.  That is not a defect in rlxboot
 * and it is not silent -- but it is a constraint on the card: upload the
 * container AFTER the prompt is reached and do not let the board reset between
 * the upload and the jump.  Named here because the spec pins the address and the
 * next reader of this file is the one who will be surprised.
 */
#ifndef RLXBOOT_H
#define RLXBOOT_H

#define RLXB_RAM_BASE     0x80000000UL
#define RLXB_RAM_END      0x82000000UL
#define RLXB_LDR_BASE     0x80400000UL
#define RLXB_LDR_END      0x80420000UL
#define RLXB_CONTAINER    0x81000000UL
#define RLXB_CTR_RAM      0x81700000UL
#define RLXB_SELF         0x81800000UL

/* The container may occupy everything from its base up to the RAM counter.
 * 7 MiB, which is more than the 3 MiB + 160 the format allows -- the bound that
 * matters is `payload_len <= RLXU_PAYLOAD_MAX`, and this one only says where
 * rlxboot is willing to read from. */
#define RLXB_CONTAINER_LIMIT  RLXB_CTR_RAM

/* The flash MMIO read window.  量, `SPEC.md` `FLS-11`: 1,024 uncached loads
 * through 0xBD000000 at the loader prompt from a bare-metal payload (`probe3`
 * Group F, seating 8), and independently the whole 4,194,304 bytes under Linux
 * byte-for-byte equal to the PIO path (`D3`, seating 16).  KSEG1, so uncached
 * and unbuffered; a cached read of an MMIO window is not a reading of it.
 *
 * `#ifndef` for ONE caller: `test/run-qemu-payload.sh` moves the window into
 * emulated RAM (Malta decodes nothing at 0x1D000000), the same way it moves the
 * UART, and that build prints NOT A DEVICE BUILD.  The device recipe passes no
 * such flag. */
#ifndef RLXB_FLASH_WIN
#define RLXB_FLASH_WIN    0xBD000000UL
#endif
#define RLXB_CTR_FLASH    0x003F0000UL   /* offset into the flash */

/* R8b: THE TWO SLOTS (the R8b spec's D1, `notes/update-chain.md` s 6).  Flash
 * offsets, and the RAM buffer each slot is copied into before it is verified.
 * Nothing in this file names 0x000000-0x00FFFF, and `slots.c` refuses at
 * compile time a slot that leaves [0x070000, 0x3F0000) or two that overlap.
 *
 *   0x070000 .. 0x18FFFF   slot A, 1,179,648 bytes
 *   0x190000 .. 0x2AFFFF   slot B, 1,179,648 bytes
 *   0x81000000             slot A's buffer (= RLXB_CONTAINER, which the
 *                          slots build never reads as a staged container)
 *   0x81200000             slot B's buffer -- its own, so the slot that wins
 *                          is booted from the bytes that were verified and
 *                          nothing is read from flash a second time */
#define RLXB_SLOT_A_FLASH 0x00070000UL
#define RLXB_SLOT_B_FLASH 0x00190000UL
#define RLXB_SLOT_SIZE    0x00120000UL
#define RLXB_SLOT_A_BUF   0x81000000UL
#define RLXB_SLOT_B_BUF   0x81200000UL

/* R8b's D28: the stock loader's own record of which flash candidate it
 * accepted -- the global its image locator writes on every candidate it tries
 * (`sw a0,-8900(s0)` at 0x804080C0), so after the scan it holds the one that
 * booted.  讀 only: `docs/loader-command-semantics.md` s a and s 8 row 1 (which
 * also predicts the value is the offset biased by 0x05000000), and
 * `PROGRESS.md` `C-1`.  A RAM address inside stage 2's data, NOT a flash
 * offset.  BOOT=slots prints it and nothing reads it for any decision. */
#define RLXB_LDR_FROM     0x8040DD3CUL

/* --- from tools/rlxprobe, reused unmodified ------------------------------- */
/* `rlxprobe.h` is included by the payload for the real prototypes; these
 * comments record WHICH pieces rlxboot depends on, so a change there that
 * breaks rlxboot is findable from this side:
 *   start.S   the entry, the stack, the .bss zeroing, and RLX_RESET
 *   uart.S    rlx_putc, rlx_reset
 *   report.c  rlx_puts, rlx_puthex32, rlx_fault_frame
 *   cache.S   rlx_cctl, rlx_call2_uncached
 * exc.S is NOT linked: rlxboot installs no exception handler, so a fault in it
 * lands in the loader's `do_reserved` and hangs, costing one power cycle.  That
 * is the same exposure probe0 and probe1 ran with. */

/* --- rlxboot's own ------------------------------------------------------- */

/* klib.c -- freestanding, and the only reason they exist is that there is no
 * libc.  `-fno-builtin` stops gcc calling them behind our back; providing them
 * anyway means a call gcc emits regardless links to code in this tree. */
void *rlx_memcpy(void *d, const void *s, unsigned long n);
void *rlx_memset(void *d, int c, unsigned long n);
int rlx_memcmp(const void *a, const void *b, unsigned long n);

/* flashread.c */
/* Read the 512-byte counter bitmap into `out`.  BOOT=ram: returns 1 when the
 * RAM-staged bitmap at 0x81700000 was used (its magic word read "RCNT"), 0
 * when the flash window was.  BOOT=slots: the flash window only, always 0 --
 * the RAM source is not compiled (D21).  READS ONLY.  There is no program or
 * erase path in this payload; `test/flashsafe.sh` is what proves that from the
 * emitted image. */
int rlxboot_read_counter_bitmap(unsigned char *out);
/* The same with both sources as pointers, for the host suites: `ram` is the
 * staged block (magic word, then the bitmap), `flash` the bitmap itself.  In
 * BOOT=slots `ram` is never read. */
int rlxb_counter_read(unsigned char *out, const volatile unsigned int *ram,
                      const volatile unsigned char *flash);

/* jump.S */
/* Jump to `entry` with a0..a3 zeroed.  Does not return.  Every delay slot
 * filled by hand under `.set noreorder`. */
void rlxboot_jump(unsigned long entry) __attribute__((noreturn));

#endif /* RLXBOOT_H */
