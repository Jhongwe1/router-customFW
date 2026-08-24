/* rlxprobe -- bare-metal probe for the Lexra-family core in the RTL8196E.
 *
 * There is no libc here and there will not be one.  Everything this header
 * declares is either in `uart.S`, where the instruction order is load-bearing
 * and must not be rescheduled, or in `probe0.c`.
 */
#ifndef RLXPROBE_H
#define RLXPROBE_H

typedef unsigned int u32;

/* --- uart.S ------------------------------------------------------------- */

/* One character out of the 16550 at 0xB8002000.  Structure copied from this
 * unit's own putchar at 0x80406B88 -- including the `nop` in the load delay
 * slot, which is the instruction P9-12 discarded as padding and paid for. */
void rlx_putc(int c);

/* The address of the instruction after the call.  This is the payload proving
 * where it is ACTUALLY running, which is a different claim from `LOADADDR`
 * echoing what it was told. */
u32 rlx_pc(void);

/* CP0 reads.  One function per register because the register number is an
 * instruction field, not a runtime value.  Each leaves two `nop`s after the
 * `mfc0`: the CP0 read hazard on this core is C-9 and is NOT established, so
 * the spacing is deliberate rather than incidental. */
u32 rlx_mfc0_status(void);      /* $12 */
u32 rlx_mfc0_cause(void);       /* $13 */
u32 rlx_mfc0_prid(void);        /* $15 -- CPU-04: RLX4181 or RLX5281 */
u32 rlx_mfc0_config(void);      /* $16 -- Config.M decides whether $16.1 exists */
u32 rlx_mfc0_config1(void);     /* $16 select 1, emitted as a raw word */

/* Arm the watchdog and spin, after draining the UART.  This is the loader's
 * own idiom from 0x804092E8, and it is what makes a payload cost no physical
 * power cycle. */
void rlx_reset(void) __attribute__((noreturn));

/* --- cache.S ------------------------------------------------------------ */
/* Only probe1 links these.  Every one of them either writes a CP0 register
 * whose behaviour on this core is unestablished, or calls an address -- so the
 * comments in cache.S are part of the interface, not decoration. */

/* CP0 register 20, Lexra's, called CCTL by inference.  Clear / write / clear,
 * which is the idiom both sources use. */
void rlx_cctl(u32 cmd);

/* The read side of the same register.  NOBODY HAS READ IT on this part -- both
 * sources only ever write it -- so this may return anything, including a
 * fault.  probe1 calls it after every cache cell is already recorded. */
u32 rlx_mfc0_cctl(void);

/* Status's write side.  Three `nop`s after the `mtc0`: the CP0 write hazard on
 * this core is C-9 and is NOT established. */
void rlx_mtc0_status(u32 v);

/* c-r3k.c's r3k_flush_icache_range(), reproduced: isolate and swap the caches,
 * byte-store across the range, restore Status.  MUST be entered through KSEG1
 * -- use rlx_call2_uncached() -- because what instruction fetch does while the
 * caches are swapped is undocumented for this core. */
void rlx_isc_inv(u32 base, u32 len);

#if RLX_GEOM
/* c-r3k.c's r3k_cache_size(), reproduced.  Returns bytes, or 0 when the core
 * does not answer.  DANGEROUS -- see cache.S -- and off unless RLX_GEOM=1. */
u32 rlx_r3k_size(u32 base, u32 ca_flags);
#endif

/* Call an address and return $v0.  The `_uncached` form ORs KSEG1 in first. */
u32 rlx_call0(u32 fn);
u32 rlx_call2_uncached(u32 fn, u32 arg0, u32 arg1);

/* --- exc.S -------------------------------------------------------------- */
/* Only probe2 links these. */

/* The handler, assembled here and COPIED to 0x80000080 and 0x80000000. Nothing
 * in it depends on the address it was linked at. `rlx_exc_end - rlx_exc_entry`
 * is its length in words, and probe2 refuses to install if that exceeds 128
 * bytes. */
extern u32 rlx_exc_entry[];
extern u32 rlx_exc_end[];

/* The handler's record, written THROUGH KSEG1: [0] exceptions taken, [1] Cause,
 * [2] EPC. Every C access to it must be uncached too. */
extern u32 rlx_exc_rec[4];

/* `break`. Traps on every MIPS ever built, which is what makes it the positive
 * control on the handler rather than a question about this core. */
void rlx_do_break(void);

/* CP0 Count read twice around `spins` iterations of a two-instruction loop.
 * Zero is a result: R3000-class CP0s have no Count. */
u32 rlx_count_delta(u32 spins);

/* 256 stubs, 3 words each, rd 0..31 x sel 0..7: stub n is at
 * `rlx_cp0_stubs + n * 12`. */
extern u32 rlx_cp0_stubs[];
extern u32 rlx_cp0_stubs_end[];

/* --- report.c ----------------------------------------------------------- */

void rlx_puts(const char *s);
void rlx_puthex32(u32 v);

/* --- probe0.c / probe1.c ------------------------------------------------ */
/* One per payload, and exactly one is linked into any image. */

void rlxprobe_main(void);

#endif /* RLXPROBE_H */
