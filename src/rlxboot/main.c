/* src/rlxboot/main.c -- rlxboot's device entry.  rlxfw's own code.
 *
 * Entered by `tools/rlxprobe/start.S` after it has set up a stack and zeroed
 * .bss, which is entered by the loader's `J 81800000`.  Returns only on a
 * refusal, and start.S then arms the watchdog (RLX_RESET=1) so the board comes
 * back to the loader prompt without a power cycle -- see REFUSE_ACTION below.
 *
 * THE CACHE, AND HOW I CONVINCED MYSELF IT IS RIGHT.
 *
 * rlxboot writes instructions into DRAM with ordinary stores and then jumps to
 * them.  Three facts decide what has to happen in between, and all three are in
 * `notes/cache-model.md`:
 *
 *   1. There is no coherence between the I and D sides.  This is an R3000-class
 *      core; the I-cache does not snoop D-side writes.
 *   2. The D side is write-back.  A store to a line that IS resident leaves the
 *      line dirty and DRAM stale.  (It is write-back WITHOUT write-allocate, so
 *      a store to a line that is not resident goes straight to memory -- which
 *      is why getting this wrong sometimes appears to work, and why "it booted"
 *      is not evidence that the flush is unnecessary.)
 *   3. CP0 register 20 is `CCTL`, edge-triggered 0 -> 1, and the two commands
 *      this file issues are the two with a name from a source and a value from
 *      two files: 0x200 `DWB_Inval` (write back and invalidate the D side) and
 *      0x002 `IInval` (invalidate the I side).  `rlx_cctl` in
 *      `tools/rlxprobe/cache.S` writes them with the clear/write/clear idiom
 *      both this unit's own bootcode and the vendor's `c-r3k.c` use.
 *
 * So: WRITE BACK D, THEN INVALIDATE I, THEN JUMP.  The order is not
 * interchangeable -- invalidating I first would let the I side refill from a
 * DRAM line the D side still holds dirty, which is the failure that looks
 * exactly like a bad signature: the digest verified over the bytes the D cache
 * holds, and the core executed the bytes DRAM holds.
 *
 * Both are issued THROUGH THE KSEG1 ALIAS, with `rlx_call2_uncached`.  Two
 * reasons, and the second is the one that is easy to miss: invalidating the
 * I-cache while fetching out of it is the classic way to fetch garbage, and this
 * unit's own loader does not take that risk either (at 0x804004a8 it ORs
 * 0xA0000000 into its own next address and jumps).  `rlx_cctl` entered at its
 * KSEG0 address is not a compile error and is not checked at run time; entering
 * it uncached is the caller's decision and this is the caller making it.
 *
 * WHAT I DID NOT DO, and why.  No flush at entry: rlxboot's own code arrived in
 * DRAM by the same route probe0..probe6 arrive by, and if the I-cache held stale
 * lines for 0x81800000 this function would never have printed its banner -- so a
 * flush here could only affect instructions after it, and nothing between here
 * and the copy is self-modified.  No `Status.IsC` path: probe1 cell 4 MEASURED
 * that this core does not isolate and that the byte stores of that method reach
 * DRAM (`CPU-35`), corrupting both victims 7 KiB apart.  `rlx_isc_inv` is
 * therefore not linked into this payload at all (RLX_ISC=0).
 *
 * ⚠️ AND WHAT IS STILL 推.  That `CCTL 0x002` is sufficient for this case is
 * 量 for probe1's victims -- a two-word patch inside the payload's own image --
 * and this is a copy of up to 3 MiB to an address 19 MiB away.  Nothing has
 * measured the D-side writeback of 0x200 on this die at all: `notes/cache-model.md`
 * marks 0x100 `DWB` as a value whose effect no source records and which cell
 * `c-F` exists to measure.  The refutation condition is on the bench and it is
 * cheap: a payload that boots and prints its own banner has been fetched
 * through the I side after the invalidate, and a payload whose first
 * instruction word is read back with `DW` and equals the container's is one
 * whose copy reached DRAM.  Until that seating, "the caches were handled
 * correctly" is an argument, not a reading.
 */

#include "rlxdefs.h"            /* tools/rlxprobe: CCTL_*, RLX_UART_LSR */
#include "rlxprobe.h"           /* tools/rlxprobe: rlx_putc/puts/puthex32,
                                 * rlx_cctl, rlx_call2_uncached -- reused */
#include "rlxboot.h"
#include "container.h"
#include "sha256b.h"
#include "devkey.h"

#ifndef RLXBOOT_BUILD
#error "RLXBOOT_BUILD must be the 8-hex source digest; the Makefile computes it"
#endif

/* 1: on a refusal, return to start.S, which arms the watchdog and the board is
 * back at the loader prompt in 41.9 ms..41.9 s depending on OVSEL -- costing no
 * power cycle, so one seating can drive the accept case and every reject case.
 * 0: spin forever, which is what SPEC-R8a s4's word "stops" says literally and
 * costs one power cycle per case.  The default is 1 and the reason is arithmetic:
 * seven reject cases at one power cycle each is seven power cycles on a project
 * with one device and no spare.  Either way NO UNVERIFIED IMAGE IS ENTERED --
 * `rlxboot_jump` is called from exactly one place and only after
 * `rlxu_verify` has returned RLXU_OK. */
#ifndef RLXBOOT_REFUSE_RESET
#define RLXBOOT_REFUSE_RESET 1
#endif

/* The linker script's own symbols: rlxboot's image and the top of its stack.
 * The self range is derived from them and not written down twice -- a payload
 * that grew past a hard-coded self_end would be a payload that permits a
 * destination on top of its own .bss. */
extern u32 _rlxboot_start[];
extern u32 _stack_top[];

static unsigned char ctr_bitmap[RLXU_CTR_BYTES];
/* ONE counter value, computed once.  `report` printed it by recomputing at
 * first, which is the shape of defect this repository has a rule about: the
 * number on the console has to be the number the comparison used, and two calls
 * to a pure function is an argument that they are, not a guarantee. */
static unsigned long ctr_value;

/* --------------------------------------------------------------- output --- */

/* CRLF.  `docs/isa-payload.md` records that device lines arrive CR CR LF and
 * the emulator's CR LF; every capture in this tree is stripped of CR before a
 * field is compared, so what matters here is that a line ENDS and that the
 * terminator is the one a serial terminal expects. */
static void nl(void)
{
	rlx_putc('\r');
	rlx_putc('\n');
}

static void putdec(u32 v)
{
	char b[12];
	int i = 0;

	if (v == 0) {
		rlx_putc('0');
		return;
	}
	while (v) {
		b[i++] = (char)('0' + (v % 10));
		v /= 10;
	}
	while (i--)
		rlx_putc(b[i]);
}

/* The per-stage reporter.  `RLXBOOT-HDR` covers two stages -- the spec's
 * steps 1 and 2 -- so the `ok` form is printed once, when the second passes. */
static void report(const struct rlxu *r, int stage, int reason)
{
	switch (stage) {
	case RLXU_T_HDR:
		if (reason != RLXU_OK) {
			rlx_puts("RLXBOOT-HDR bad=");
			rlx_puts(rlxu_reason_name(reason));
			nl();
		}
		break;
	case RLXU_T_BOUND:
		rlx_puts("RLXBOOT-HDR ");
		if (reason == RLXU_OK) {
			rlx_puts("ok");
		} else {
			rlx_puts("bad=");
			rlx_puts(rlxu_reason_name(reason));
		}
		nl();
		break;
	case RLXU_T_SIG:
		rlx_puts(reason == RLXU_OK ? "RLXBOOT-SIG ok" : "RLXBOOT-SIG bad");
		nl();
		break;
	case RLXU_T_DIGEST:
		rlx_puts(reason == RLXU_OK ? "RLXBOOT-DIGEST ok"
		                           : "RLXBOOT-DIGEST bad");
		nl();
		break;
	case RLXU_T_VER:
		rlx_puts("RLXBOOT-VER cur=");
		putdec((u32)r->version);
		rlx_puts(" ctr=");
		putdec((u32)ctr_value);
		rlx_puts(reason == RLXU_OK ? " ok" : " bad");
		nl();
		break;
	default:
		break;
	}
}

/* ----------------------------------------------------------------- main --- */

void rlxprobe_main(void)
{
	struct rlxu_env env;
	struct rlxu r;
	int from_ram, malformed = 0;

	rlx_puts("RLXBOOT-V1 build=");
	rlx_puthex32(RLXBOOT_BUILD);
	nl();

	/* The counter is read BEFORE the container is verified, and that is
	 * safe in a way the rest of this file is careful about: reading it
	 * touches only two addresses rlxboot chose (0x81700000 and
	 * 0xBD3F0000), neither of which comes out of the header.  Nothing an
	 * attacker controls influences what is read.  It is read early so
	 * `RLXBOOT-CTRSRC` is on the console before the ~1 s of silence that
	 * Ed25519 and a 3 MiB SHA-256 cost -- if the flash window is not
	 * decoded at 0xBD3F0000 at the prompt, the hang is here and the console
	 * says so. */
	from_ram = rlxboot_read_counter_bitmap(ctr_bitmap);
	rlx_puts(from_ram ? "RLXBOOT-CTRSRC ram" : "RLXBOOT-CTRSRC flash");
	nl();

	env.ram_base  = RLXB_RAM_BASE;
	env.ram_end   = RLXB_RAM_END;
	env.self_base = (unsigned long)_rlxboot_start;
	env.self_end  = (unsigned long)_stack_top;
	env.buf_base  = RLXB_CONTAINER;
	env.buf_limit = RLXB_CONTAINER_LIMIT;
	env.ldr_base  = RLXB_LDR_BASE;
	env.ldr_end   = RLXB_LDR_END;
	/* rlxboot's boot path writes no flash byte, so it declares no write and
	 * the container's signed `flash_at` is compared against nothing.  It is
	 * still CHECKED: a container declaring the loader region or H601 is
	 * refused as `flash_dst` here too, in a path that writes nothing.
	 * `R8b`'s install path is what will set this to a real offset. */
	env.write_at   = RLXU_FLASH_NONE;
	env.write_form = RLXU_FORM_NONE;
	ctr_value     = rlxu_counter_from_bitmap(ctr_bitmap, &malformed);
	env.counter   = ctr_value;
	env.pk        = rlxboot_devkey;

	if (malformed)
		rlx_puts("ctr-bitmap malformed: using the total zero count\r\n");

	if (rlxu_verify((const unsigned char *)RLXB_CONTAINER,
	                RLXB_CONTAINER_LIMIT - RLXB_CONTAINER,
	                &env, &r, report) != RLXU_OK) {
		rlx_puts("RLXBOOT-REFUSE ");
		rlx_puts(rlxu_reason_name(r.reason));
		nl();
#if RLXBOOT_REFUSE_RESET
		rlx_puts("refuse-action reset\r\n");
		return;                 /* start.S arms the watchdog */
#else
		rlx_puts("refuse-action halt\r\n");
		for (;;)
			;
#endif
	}

	/* Verified.  Only now does one byte move. */
	rlx_memcpy((void *)r.load_addr,
	           (const void *)(RLXB_CONTAINER + RLXU_BODY_OFF),
	           r.payload_len);

	/* Write back the D side, THEN invalidate the I side, both entered
	 * through KSEG1.  See the file header for the argument; the order is
	 * the argument. */
	rlx_call2_uncached((u32)(unsigned long)rlx_cctl, CCTL_DWBINVAL, 0);
	rlx_call2_uncached((u32)(unsigned long)rlx_cctl, CCTL_IINVAL, 0);

	rlx_puts("RLXBOOT-BOOT load=");
	rlx_puthex32((u32)r.load_addr);
	rlx_puts(" entry=");
	rlx_puthex32((u32)r.entry_addr);
	nl();

	/* Drain the UART before the jump.  The payload may reprogram the 16550
	 * or reset the board; a line still in the FIFO is a line the capture
	 * never sees, and this is the one line that says the boot happened.
	 * The bound is the loader's own 6540 iterations, copied by uart.S. */
	{
		volatile const unsigned char *lsr =
			(volatile const unsigned char *)RLX_UART_LSR;
		u32 spin = 6540;
		while (spin-- && !(*lsr & 0x40))
			;
	}

	rlxboot_jump(r.entry_addr);
}
