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
 *   0x81700000                 the RAM-staged counter: "RCNT" then 512 bytes
 *   0x81800000                 rlxboot itself, load and entry
 *   0xBD000000                 the flash MMIO read window (SPEC.md FLS-11)
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
 * and unbuffered; a cached read of an MMIO window is not a reading of it. */
#define RLXB_FLASH_WIN    0xBD000000UL
#define RLXB_CTR_FLASH    0x003F0000UL   /* offset into the flash */

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
/* Read the 512-byte counter bitmap into `out`.  Returns 1 when the RAM-staged
 * bitmap at 0x81700000 was used (its magic word read "RCNT"), 0 when the flash
 * window was.  READS ONLY.  There is no program or erase path in this payload;
 * `test/flashsafe.sh` is what proves that from the emitted image. */
int rlxboot_read_counter_bitmap(unsigned char *out);

/* jump.S */
/* Jump to `entry` with a0..a3 zeroed.  Does not return.  Every delay slot
 * filled by hand under `.set noreorder`. */
void rlxboot_jump(unsigned long entry) __attribute__((noreturn));

#endif /* RLXBOOT_H */
