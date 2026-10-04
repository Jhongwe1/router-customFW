/* src/rlxboot/slots.c -- R8b: verify slot A and slot B, and choose one.
 * rlxfw's own code.  `slots.h` states the rule; this file carries the reasons
 * for the mechanics.
 *
 * ONE BUFFER PER SLOT, AND THAT IS WHAT "VERIFY THE BYTES YOU BOOT" COSTS.
 * With one buffer, verifying B overwrites A's verified copy, and a tie (or A
 * winning) would need A read from flash again -- a second copy, verified or
 * not, of bytes that were already judged.  Two buffers 2 MiB apart cost
 * nothing on a 32 MiB part, so every slot's verdict is about the bytes that
 * stay in its buffer, and `main.c` boots the winner out of that buffer.
 *
 * THE COPY IS SIZED BY THE HEADER IN RAM AND BOUNDED BY THE SLOT.  The first
 * 160 bytes are copied; if they begin `RLXU` and their `payload_len` fits the
 * slot, the rest of the container follows, else nothing more does.  That
 * length is read from the copy, not from flash, and it is the same field
 * `rlxu_verify` then reads from the same copy -- so the bytes verified and the
 * bytes copied cannot disagree about how many there are.  `copied` is passed
 * as `avail` and `buf_limit` is the buffer's end, so `rlxu_verify` refuses a
 * container that did not fit (`truncated`, or `payload_len` past 3 MiB) with
 * the reason it already has.  The untrusted field decides only how long a copy
 * into a fixed buffer runs, never where anything goes -- the opposite of the
 * stock loader's `check_image()` (see `container.c`).  What it saves: an erased
 * or torn slot costs a 160-byte read, not 1,179,648 bytes at ~2 us a word.
 *
 * DECISION (not in the R8b spec): each slot is verified with `write_at` = the
 * slot's own base and `write_form` = WHOL.  `container.c` then requires the
 * container's SIGNED declaration to name the place it was read from, in the
 * form that puts a header at that place -- so a container signed for slot B
 * and found in slot A, an undeclared one (`flash_at` none), or a PAYL one is
 * refused as `flash_match`.  The field's name says "write"; the question it
 * answers is "is this where the signer said it goes", which is the same
 * question whether the caller is about to write it or has just read it.
 * D13's containers are each signed for their slot and the R8b installer
 * refuses any other (D7), so for a correctly installed slot this changes
 * nothing; for a slot written by any other route it is the second fence.
 */

#include "rlxboot.h"
#include "container.h"
#include "slots.h"

/* Every word this file reads or writes is 32 bits, on the host as well. */
typedef char rlxb_word_is_32_bits[(sizeof(unsigned int) == 4) ? 1 : -1];

/* D1's layout as arithmetic the compiler refuses to get wrong.  Both slots lie
 * in [0x070000, 0x3F0000): above rlxboot, the rescue and the barrier (so
 * nothing below 0x070000 -- and in particular nothing in 0x000000-0x00FFFF --
 * is nameable here), below the anti-rollback page, 64 KiB aligned (D11), and
 * apart.  The buffers lie in RAM above the stage-2 loader's window, apart,
 * word aligned, and below the RAM counter -- and so below rlxboot itself. */
typedef char rlxb_a_above_barrier[(RLXB_SLOT_A_FLASH >= 0x070000UL) ? 1 : -1];
typedef char rlxb_b_above_barrier[(RLXB_SLOT_B_FLASH >= 0x070000UL) ? 1 : -1];
typedef char rlxb_a_below_state[
	(RLXB_SLOT_A_FLASH + RLXB_SLOT_SIZE <= RLXB_CTR_FLASH) ? 1 : -1];
typedef char rlxb_b_below_state[
	(RLXB_SLOT_B_FLASH + RLXB_SLOT_SIZE <= RLXB_CTR_FLASH) ? 1 : -1];
typedef char rlxb_slots_apart[
	(RLXB_SLOT_A_FLASH + RLXB_SLOT_SIZE <= RLXB_SLOT_B_FLASH) ? 1 : -1];
typedef char rlxb_slots_64k[
	(((RLXB_SLOT_A_FLASH | RLXB_SLOT_B_FLASH | RLXB_SLOT_SIZE)
	  & (RLXB_TICK_BYTES - 1UL)) == 0) ? 1 : -1];
typedef char rlxb_slot_holds_header[(RLXB_SLOT_SIZE > RLXU_BODY_OFF) ? 1 : -1];
typedef char rlxb_buf_a_above_loader[(RLXB_SLOT_A_BUF >= RLXB_LDR_END) ? 1 : -1];
typedef char rlxb_bufs_apart[
	(RLXB_SLOT_A_BUF + RLXB_SLOT_SIZE <= RLXB_SLOT_B_BUF) ? 1 : -1];
typedef char rlxb_buf_b_below_ctr[
	(RLXB_SLOT_B_BUF + RLXB_SLOT_SIZE <= RLXB_CTR_RAM) ? 1 : -1];
typedef char rlxb_ctr_below_self[(RLXB_CTR_RAM < RLXB_SELF) ? 1 : -1];
typedef char rlxb_bufs_aligned[
	(((RLXB_SLOT_A_BUF | RLXB_SLOT_B_BUF) & 3UL) == 0) ? 1 : -1];

/* ---------------------------------------------------------------- output */

/* Lower-case hex, as `rlx_puthex32` prints the build id and the BOOT line. */
static void out_s(const struct rlxb_io *io, const char *s)
{
	while (*s)
		io->emit(*s++);
}

static void out_nl(const struct rlxb_io *io)
{
	io->emit('\r');
	io->emit('\n');
}

static void out_hex8(const struct rlxb_io *io, unsigned long v)
{
	static const char digits[] = "0123456789abcdef";
	int i;

	for (i = 28; i >= 0; i -= 4)
		io->emit(digits[(v >> i) & 0xFUL]);
}

static void out_dec(const struct rlxb_io *io, unsigned long v)
{
	char d[12];
	int i = 0;

	v &= 0xFFFFFFFFUL;
	do {
		d[i++] = (char)('0' + (int)(v % 10UL));
		v /= 10UL;
	} while (v);
	while (i--)
		io->emit(d[i]);
}

/* ------------------------------------------------------------------ copy */

/* Copy words [from, to) of slot `s` into its buffer, `to` rounded up to a
 * word and capped at the slot; returns the byte count now in the buffer.
 *
 * WORD LOADS.  量 `FLS-11`: the window serves each uncached load as its own
 * transaction, 2.075 us at stride 4 and at stride 1,024 alike -- so the
 * transaction and not the byte is the unit of cost, and a byte loop would pay
 * it up to four times a word (推: probe3 timed `lw`, never `lbu`).  Every
 * load is aligned: the slot bases are 64 KiB aligned, `from` is 0 or a value
 * this function returned, and an unaligned `lw` on this core is an AdEL, not
 * a slow path (`CPU-75`).  Big-endian load, big-endian store: the bytes land
 * in flash order, and on the little-endian host the same holds for the same
 * reason.  `volatile` so that each load is a load of the part.
 *
 * One dot per 64 KiB, so a copy that has stopped is dots that stopped: the
 * bench operator's way to tell slow from hung without a timer this payload
 * would have to trust. */
static unsigned long copy_words(struct rlxb_slot *s, unsigned long from,
                                unsigned long to, const struct rlxb_io *io)
{
	unsigned long w = from >> 2;
	unsigned long end = (to + 3UL) >> 2;
	unsigned long cap = s->size >> 2;

	if (end > cap)
		end = cap;
	for (; w < end; w++) {
		s->buf[w] = s->src[w];
		if (((w + 1UL) & ((RLXB_TICK_BYTES >> 2) - 1UL)) == 0)
			io->emit('.');
	}
	return w << 2;
}

/* ------------------------------------------------------------------- run */

/* The READ line is the bench operator's account of the copy, in this order:
 *
 *   RLXBOOT-READ A flash=00070000 buf=81000000       before the first load,
 *                                                    so a hang in the very
 *                                                    first read of the part
 *                                                    ends the console here
 *    n=1114272                                       after the 160-byte
 *                                                    prefix: how many bytes
 *                                                    this read will cover
 *    .................                               one per 64 KiB, as they
 *                                                    are copied; absent when
 *                                                    n is under 64 KiB
 *
 * so the finished line reads `... n=1114272 .................` and a parser
 * that wants the count matches up to the dots. */
int rlxb_slot_run(struct rlxb_slot *s, const struct rlxu_env *e,
                  rlxu_report_fn rep, const struct rlxb_io *io)
{
	struct rlxu_env se;
	const unsigned char *b = (const unsigned char *)s->buf;
	unsigned long want = RLXU_BODY_OFF, planned;

	se = *e;
	se.buf_base   = s->buf_addr;
	se.buf_limit  = s->buf_addr + s->size;
	se.write_at   = s->flash_off;        /* DECISION: see the file header */
	se.write_form = RLXU_FORM_WHOLE;

	out_s(io, "RLXBOOT-READ ");
	io->emit(s->name);
	out_s(io, " flash=");
	out_hex8(io, s->flash_off);
	out_s(io, " buf=");
	out_hex8(io, s->buf_addr);

	s->copied = copy_words(s, 0, RLXU_BODY_OFF, io);
	if (s->copied >= RLXU_BODY_OFF && rlxu_be32(b) == RLXU_MAGIC) {
		unsigned long plen = rlxu_be32(b + 12);

		if (plen <= s->size - RLXU_BODY_OFF)
			want = RLXU_BODY_OFF + plen;
	}
	/* What `copy_words` will return, computed the way it computes it. */
	planned = (want + 3UL) >> 2;
	if (planned > (s->size >> 2))
		planned = s->size >> 2;
	planned <<= 2;
	out_s(io, " n=");
	out_dec(io, planned);
	if (planned >= RLXB_TICK_BYTES)
		io->emit(' ');
	s->copied = copy_words(s, s->copied, want, io);
	out_nl(io);

	/* The COPY is verified -- `b`, never `s->src`. */
	s->reason = rlxu_verify(b, s->copied, &se, &s->r, rep);

	out_s(io, "RLXBOOT-VERDICT ");
	io->emit(s->name);
	if (s->reason == RLXU_OK) {
		out_s(io, " ok ver=");
		out_dec(io, s->r.version);
	} else {
		out_s(io, " bad=");
		out_s(io, rlxu_reason_name(s->reason));
	}
	out_nl(io);
	return s->reason;
}

/* ---------------------------------------------------------------- choose */

/* D4.  An unverified slot never wins, whatever version its header claims --
 * before `rlxu_verify` returns RLXU_OK the version is an unauthenticated
 * 32-bit field.  Between two verified slots the higher version wins, and on
 * equal versions the FIRST argument wins, which `rlxb_select` makes A. */
struct rlxb_slot *rlxb_choose(struct rlxb_slot *a, struct rlxb_slot *b)
{
	int ok_a = (a->reason == RLXU_OK);
	int ok_b = (b->reason == RLXU_OK);

	if (ok_a && ok_b)
		return (b->r.version > a->r.version) ? b : a;
	if (ok_a)
		return a;
	if (ok_b)
		return b;
	return 0;
}

struct rlxb_slot *rlxb_select(struct rlxb_slot *a, struct rlxb_slot *b,
                              const struct rlxu_env *e, rlxu_report_fn rep,
                              const struct rlxb_io *io)
{
	struct rlxb_slot *w;

	rlxb_slot_run(a, e, rep, io);
	rlxb_slot_run(b, e, rep, io);
	w = rlxb_choose(a, b);
	if (w) {
		out_s(io, "RLXBOOT-SLOT ");
		io->emit(w->name);
		out_nl(io);
	} else {
		out_s(io, "RLXBOOT-HALT ");
		io->emit(a->name);
		io->emit('=');
		out_s(io, rlxu_reason_name(a->reason));
		io->emit(' ');
		io->emit(b->name);
		io->emit('=');
		out_s(io, rlxu_reason_name(b->reason));
		out_nl(io);
	}
	return w;
}

const unsigned char *rlxb_boot_body(const struct rlxb_slot *s)
{
	return (const unsigned char *)s->buf + RLXU_BODY_OFF;
}
