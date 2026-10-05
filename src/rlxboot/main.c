/* src/rlxboot/main.c -- rlxboot's device entry.  rlxfw's own code.
 *
 * Entered by `tools/rlxprobe/start.S` after it has set up a stack and zeroed
 * .bss, which is entered by the loader's `J 81800000` -- or, for the image at
 * flash 0x010000 or 0x020000, by the stock loader's own scan, which copies it
 * to the same address.  The BOOT=ram build returns only on a refusal, and
 * start.S then arms the watchdog (RLX_RESET=1) so the board comes back to the
 * loader prompt without a power cycle -- see REFUSE_ACTION below.  The
 * BOOT=slots build never returns: it boots a slot or it halts.
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
#include "slots.h"
#include "sha256b.h"

#ifndef RLXBOOT_BUILD
#error "RLXBOOT_BUILD must be the 8-hex source digest; the Makefile computes it"
#endif

/* THE KEY THIS IMAGE TRUSTS IS CHOSEN WHEN IT IS BUILT (the R8b spec's D15).
 * KEY=prod (the Makefile's default) compiles in the public half of the
 * owner's production key from the generated `prodkey.h`; KEY=dev the
 * development key, whose seed is published in `devkey.h` -- so an image built
 * with it accepts a container anyone signed.  Whichever header is staged is a
 * BUILD_ID input, and `RLXBOOT-KEY` prints the key at boot so a capture says
 * which one an image trusts without anyone recomputing an id.  The Makefile's
 * `keycheck` refuses first; the #error below is for a build that went round
 * it. */
#ifndef RLXBOOT_KEY_PROD
#error "RLXBOOT_KEY_PROD must be 0 (KEY=dev) or 1 (KEY=prod); the Makefile sets it"
#endif
#if RLXBOOT_KEY_PROD
#include "prodkey.h"
#ifndef RLXBOOT_PRODKEY_HEX
#error "prodkey.h holds no production key: mkprodkey.py write --pubkey <64 hex>, or build KEY=dev"
#endif
#define RLXBOOT_PUBKEY     rlxboot_prodkey
#define RLXBOOT_KEY_LINE   "RLXBOOT-KEY prod " RLXBOOT_PRODKEY_HEX
#else
#include "devkey.h"
#define RLXBOOT_PUBKEY     rlxboot_devkey
#define RLXBOOT_KEY_LINE   "RLXBOOT-KEY dev " RLXBOOT_DEVKEY_HEX
#endif

/* WHERE THE CONTAINER COMES FROM IS DECIDED WHEN THE IMAGE IS BUILT, NEVER WHEN
 * IT RUNS.  The Makefile's BOOT= sets this and also decides whether `slots.c`
 * is linked, so the two builds differ in BUILD_ID as well as in behaviour.
 *   1  (BOOT=slots, the default and the artefact)  R8b: read flash slot A and
 *      slot B, verify each in its own buffer, boot per the R8b spec's D4, and
 *      HALT when neither verifies.
 *   0  (BOOT=ram)  R8a: verify the container the loader's TFTP staged at
 *      0x81000000.
 * There is no build that tries one and then the other.  `MEM-17`: DRAM
 * survives a power cycle, so a "RAM first" path would let a stale container --
 * from any earlier seating -- win over both slots without anyone typing a
 * thing. */
#ifndef RLXBOOT_SLOTS
#error "RLXBOOT_SLOTS must be 0 (BOOT=ram) or 1 (BOOT=slots); the Makefile sets it"
#endif

/* 1: on a refusal, return to start.S, which arms the watchdog and the board is
 * back at the loader prompt in 41.9 ms..41.9 s depending on OVSEL -- costing no
 * power cycle, so one seating can drive the accept case and every reject case.
 * 0: spin forever, which is what SPEC-R8a s4's word "stops" says literally and
 * costs one power cycle per case.  The default is 1 and the reason is arithmetic:
 * seven reject cases at one power cycle each is seven power cycles on a project
 * with one device and no spare.  Either way NO UNVERIFIED IMAGE IS ENTERED --
 * `rlxboot_jump` is called from exactly one place and only after
 * `rlxu_verify` has returned RLXU_OK.
 *
 * BOOT=ram ONLY.  The slots build always halts (D4: "HALT (spin), no reset
 * loop"): a reset there would come straight back through the stock loader's
 * scan to this same rlxboot and the same two slots, forever.  讀
 * `docs/loader-command-semantics.md`: the loader's only two `WDTCNR` writes
 * are its own deliberate reboots, so nothing arms the watchdog under a spin
 * that this payload did not arm itself. */
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

/* ----------------------------------------------------------------- boot --- */

/* The one path into a payload, shared by both builds.  `r` is a verdict of
 * RLXU_OK and `body` is the first payload byte OF THE BYTES THAT VERDICT WAS
 * ABOUT: the staged container (BOOT=ram) or the winning slot's own buffer
 * (BOOT=slots) -- never flash, and never a second copy. */
static void boot_verified(const struct rlxu *r, const unsigned char *body)
	__attribute__((noreturn));

static void boot_verified(const struct rlxu *r, const unsigned char *body)
{
	/* Verified.  Only now does one byte move. */
	rlx_memcpy((void *)r->load_addr, (const void *)body, r->payload_len);

	/* Write back the D side, THEN invalidate the I side, both entered
	 * through KSEG1.  See the file header for the argument; the order is
	 * the argument. */
	rlx_call2_uncached((u32)(unsigned long)rlx_cctl, CCTL_DWBINVAL, 0);
	rlx_call2_uncached((u32)(unsigned long)rlx_cctl, CCTL_IINVAL, 0);

	rlx_puts("RLXBOOT-BOOT load=");
	rlx_puthex32((u32)r->load_addr);
	rlx_puts(" entry=");
	rlx_puthex32((u32)r->entry_addr);
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

	rlxboot_jump(r->entry_addr);
}

#if RLXBOOT_SLOTS
/* The two slots, in .bss: zeroed by start.S, so a field this file forgets to
 * set reads 0 rather than whatever the vendor kernel left there. */
static struct rlxb_slot slot_a, slot_b;

static const struct rlxb_io console = { rlx_putc };

/* D28: `RLXBOOT-FROM <8 hex>`, the loader's word saying which candidate it
 * accepted (rlxboot.h).  INFORMATIONAL ONLY, BY CONSTRUCTION: the word is
 * loaded inside the argument list of `rlx_puthex32` (report.c: prints eight
 * nibbles, stores nothing), into no variable, in this one function that
 * returns nothing -- so no decision in this file or in `slots.c` can see it.
 *
 * THROUGH KSEG0, ON PURPOSE: the loader wrote it with an ordinary cached
 * store and the D side is write-back, so if the loader jumped here without
 * writing that line back, DRAM is stale and only a cached load sees what it
 * last wrote; a KSEG0 load hits the dirty line or fills from DRAM, right
 * either way.  A KSEG1 load would be right only if the write-back happened,
 * which nothing has measured -- `flashread.c`'s argument for the RAM counter.
 * Word aligned and inside stage 2's window, or this does not compile: an
 * unaligned `lw` is an AdEL on this core, and a typo must not read elsewhere. */
typedef char rlxb_from_in_loader[
	(RLXB_LDR_FROM >= RLXB_LDR_BASE && RLXB_LDR_FROM + 4UL <= RLXB_LDR_END
	 && (RLXB_LDR_FROM & 3UL) == 0) ? 1 : -1];

static void print_from(void)
{
	rlx_puts("RLXBOOT-FROM ");
	rlx_puthex32(*(volatile const u32 *)RLXB_LDR_FROM);
	nl();
}
#endif

/* ----------------------------------------------------------------- main --- */

void rlxprobe_main(void)
{
	struct rlxu_env env;
	int malformed = 0;
#if RLXBOOT_SLOTS
	struct rlxb_slot *win;
#else
	struct rlxu r;
	int from_ram;
#endif

	rlx_puts("RLXBOOT-V1 build=");
	rlx_puthex32(RLXBOOT_BUILD);
	nl();
#if RLXBOOT_SLOTS
	print_from();           /* D28; the BOOT=ram build prints no FROM line */
#endif
	rlx_puts(RLXBOOT_KEY_LINE);
	nl();

	/* The counter is read BEFORE the container is verified, and that is
	 * safe in a way the rest of this file is careful about: reading it
	 * touches only addresses rlxboot chose (0xBD3F0000, and in BOOT=ram
	 * 0x81700000), none of which comes out of the header.  Nothing an
	 * attacker controls influences what is read.  It is read early so
	 * `RLXBOOT-CTRSRC` is on the console before the ~1 s of silence that
	 * Ed25519 and a 3 MiB SHA-256 cost -- if the flash window is not
	 * decoded at 0xBD3F0000 at the prompt, the hang is here and the console
	 * says so.
	 *
	 * D21: the slots build has ONE source, the flash bitmap, and its RAM
	 * path is not compiled (`flashread.c` says why), so the line is a
	 * constant there.  BOOT=ram keeps R8a's RAM-first order and says which
	 * source decided. */
#if RLXBOOT_SLOTS
	(void)rlxboot_read_counter_bitmap(ctr_bitmap);
	rlx_puts("RLXBOOT-CTRSRC flash");
#else
	from_ram = rlxboot_read_counter_bitmap(ctr_bitmap);
	rlx_puts(from_ram ? "RLXBOOT-CTRSRC ram" : "RLXBOOT-CTRSRC flash");
#endif
	nl();

	env.ram_base  = RLXB_RAM_BASE;
	env.ram_end   = RLXB_RAM_END;
	env.self_base = (unsigned long)_rlxboot_start;
	env.self_end  = (unsigned long)_stack_top;
#if RLXBOOT_SLOTS
	/* No buffer here: `slots.c` gives each slot its own window, and an
	 * empty one is what a forgotten window would refuse against.  It also
	 * keeps 0x81700000 -- RLXB_CONTAINER_LIMIT is the RAM counter's
	 * address -- out of this image entirely, which the payload gate
	 * checks (D21). */
	env.buf_base  = 0;
	env.buf_limit = 0;
#else
	env.buf_base  = RLXB_CONTAINER;
	env.buf_limit = RLXB_CONTAINER_LIMIT;
#endif
	env.ldr_base  = RLXB_LDR_BASE;
	env.ldr_end   = RLXB_LDR_END;
	/* rlxboot's boot path writes no flash byte, so it declares no write and
	 * the container's signed `flash_at` is compared against nothing.  It is
	 * still CHECKED: a container declaring the loader region or H601 is
	 * refused as `flash_dst` here too, in a path that writes nothing.
	 * `R8b`'s install path is what will set this to a real offset.  (The
	 * slots build replaces the buffer and these two per slot, in
	 * `slots.c`, and says why there.) */
	env.write_at   = RLXU_FLASH_NONE;
	env.write_form = RLXU_FORM_NONE;
	ctr_value     = rlxu_counter_from_bitmap(ctr_bitmap, &malformed);
	env.counter   = ctr_value;
	env.pk        = RLXBOOT_PUBKEY;

	if (malformed)
		rlx_puts("ctr-bitmap malformed: using the total zero count\r\n");

#if RLXBOOT_SLOTS
	slot_a.name      = 'A';
	slot_a.flash_off = RLXB_SLOT_A_FLASH;
	slot_a.size      = RLXB_SLOT_SIZE;
	slot_a.buf_addr  = RLXB_SLOT_A_BUF;
	slot_a.src = (const volatile unsigned int *)(RLXB_FLASH_WIN + RLXB_SLOT_A_FLASH);
	slot_a.buf = (unsigned int *)RLXB_SLOT_A_BUF;
	slot_b.name      = 'B';
	slot_b.flash_off = RLXB_SLOT_B_FLASH;
	slot_b.size      = RLXB_SLOT_SIZE;
	slot_b.buf_addr  = RLXB_SLOT_B_BUF;
	slot_b.src = (const volatile unsigned int *)(RLXB_FLASH_WIN + RLXB_SLOT_B_FLASH);
	slot_b.buf = (unsigned int *)RLXB_SLOT_B_BUF;

	win = rlxb_select(&slot_a, &slot_b, &env, report, &console);
	if (!win) {
		/* `rlxb_select` has printed both reasons.  No reset: see
		 * RLXBOOT_REFUSE_RESET above for why this build never loops. */
		rlx_puts("refuse-action halt\r\n");
		for (;;)
			;
	}
	boot_verified(&win->r, rlxb_boot_body(win));
#else
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
	boot_verified(&r, (const unsigned char *)(RLXB_CONTAINER + RLXU_BODY_OFF));
#endif
}
