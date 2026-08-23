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

/* --- probe0.c ----------------------------------------------------------- */

void rlx_puts(const char *s);
void rlx_puthex32(u32 v);
void rlxprobe_main(void);

#endif /* RLXPROBE_H */
