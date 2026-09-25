/*
 * rtl819x-nic-tx.h -- rtl819x-nic 1.5 (R6b-2): the TX policy's declarations
 * and every part of 1.5 that decides something without touching hardware.
 * THIS FILE IS NOT REALTEK'S.
 *
 * Included once, by rtl819x-nic.c, on 1.4's blank line 217, so that no line
 * of 1.4 moves (the 72 citations into that file stay where they are).  What
 * is here takes every input as an argument: tools/nic15check.py compiles
 * this file UNCHANGED with the host's gcc, beside a generated driver that
 * defines NIC15_HOST and the five hooks declared at the end, and drives the
 * parsers, the gate table, the length policy, the classifier, the sweep's
 * bookkeeping (registration, retries, the record key, the mark values), the
 * frame's expected bytes, the verb dispatcher and both page formatters.  The
 * kernel and the harness therefore run the same table and the same formats.
 *
 * NIC_* macros are defined AFTER line 217, so nothing here uses them;
 * NIC15_TXD is checked against NIC_TX_DESC by a BUILD_BUG_ON in nic15_init.
 *
 * WHAT 1.5 IS, IN FIVE LINES (the reasons: notes/nic-driver.md, R6b-2):
 *   txlen    which TX length fields the two writers store (default 1.4's)
 *   txoff    the TX copy's buffer offset, 2 (1.4) or 0
 *   txrb     descriptor read-backs and their load-matched controls
 *   sweep    re-arm; frame a at L; probe b -- once per length, in the kernel;
 *            LOOPBACK unless the command ends in ` wire`
 *   swclear  forget the sweep's records (they are otherwise never erased)
 * Each behaviour verb is refused while the engine is on, rlx0 is up or a
 * sweep runs, and marks the policy dirty; `engine on` (and `ifconfig rlx0
 * up`) then refuses (-ESTALE) until `arm` has run, so no frame is ever sent
 * under a new policy from a ring the old one left.  A boot that types no 1.5
 * verb runs 1.4's stores in 1.4's order.
 */
#ifndef RTL819X_NIC_TX_H
#define RTL819X_NIC_TX_H

#define NIC15_TXD		4	/* == NIC_TX_DESC, BUILD_BUG_ON'd */
#define NIC15_PAGE		4096	/* what read_proc is handed */

/* ------------------------------------------------------------------ txlen
 * m_len = F + 4 - d; m_extsize = F + 4 when ext_ph, else 1.4's constant
 * (2,046, passed in by the call site as the literal 1.4 expression).  ph_len
 * is F + 4 in every setting, F = max(L, 60), and nic_xmit's zero-fill to 60
 * stays: padding content is not a length field.  `vendor` is the vendor's
 * and the loader's LENGTHS (讀 rtl865xc_swNic.c:713-721, NET-122), not their
 * bytes -- neither pads.  mlen and ext name which of the two fields matters;
 * d1..d3 grade m_len so that M1-cover8 makes a prediction (182 * d bad
 * lengths) no other surviving rule makes.  They are nobody's convention. */
#define NIC15_LEN_RLXFW		0
#define NIC15_LEN_MLEN		1
#define NIC15_LEN_EXT		2
#define NIC15_LEN_VENDOR	3
#define NIC15_LEN_D1		4
#define NIC15_LEN_D2		5
#define NIC15_LEN_D3		6
#define NIC15_LEN_N		7

struct nic15_len_row {
	const char *name;
	unsigned char d;	/* ph_len - m_len */
	unsigned char ext_ph;	/* 1: m_extsize = ph_len */
};

static const struct nic15_len_row nic15_len_tab[NIC15_LEN_N] = {
	{ "rlxfw",  4, 0 },	/* 1.4                                 */
	{ "mlen",   0, 0 },
	{ "ext",    4, 1 },
	{ "vendor", 0, 1 },	/* _swNic_send; the loader, NET-122    */
	{ "d1",     1, 0 },
	{ "d2",     2, 0 },
	{ "d3",     3, 0 },
};

/* The policy.  One struct so that the pure setter below can be driven on the
 * host; 1.4's lines read its fields.  `dirty` is set by EVERY accepted
 * behaviour verb, the same value re-typed included: both A/B arms type their
 * txlen and so both pass through the dirty-clearing arm (F11). */
struct nic15_pol {
	int txlen;
	int txoff;
	int txrb;
	int dirty;
};

static inline const char *nic15_len_name(int pol)
{
	return (pol >= 0 && pol < NIC15_LEN_N) ? nic15_len_tab[pol].name : "?";
}

/* THE DEFAULT ARM FIRST, AND IT IS 1.4's VALUE LITERALLY: at pol 0 (and at any
 * value this table does not hold) m_len is the F the caller passed and
 * m_extsize is the 1.4 expression the caller passed.  nic15check drives both
 * over F = 0..2,047. */
static inline u32 nic15_mlen(u32 f, int pol)
{
	if (pol <= NIC15_LEN_RLXFW || pol >= NIC15_LEN_N)
		return f;
	return f + 4 - nic15_len_tab[pol].d;
}

static inline u32 nic15_ext(u32 f, int pol, u32 ext14)
{
	if (pol <= NIC15_LEN_RLXFW || pol >= NIC15_LEN_N ||
	    !nic15_len_tab[pol].ext_ph)
		return ext14;
	return f + 4;
}

/* ------------------------------------------------------------------- txrb
 * A mask.  Bits 2 and 3 are the controls for bits 0 and 1: the same count of
 * uncached loads at the same position, of words the engine never owns
 * (nic_idle_ph, nic_idle_ring -- carved by every alloc), into a sink the CPU
 * alone reads.  So a bit-0 fix that bit 2 does not reproduce is about WHICH
 * words were read, not about the time or the bus traffic the loads cost.
 * 推, not established for the RLX4181: whether an uncached load waits for the
 * write buffer to drain.  A read-back that returns the written value does not
 * prove the store reached DRAM; Q records what the load returned. */
#define NIC15_RB_FIELDS		0x1	/* 12 slot words into Q, before OWN      */
#define NIC15_RB_RING		0x2	/* the ring word into Q, before TXFD     */
#define NIC15_RB_IDLE12		0x4	/* 12 loads of nic_idle_ph at bit 0's    */
#define NIC15_RB_IDLE1		0x8	/* 1 load of nic_idle_ring at bit 1's    */
#define NIC15_RB_MAX		0xF

/* ------------------------------------------------------------------ verbs */
#define NIC15_V_NONE		0
#define NIC15_V_TXLEN		1
#define NIC15_V_TXOFF		2
#define NIC15_V_TXRB		3
#define NIC15_V_ENGINE		4	/* engine on, ndo_open: :2307, :1665 */
#define NIC15_V_SWEEP		5
#define NIC15_V_SWSHOW		6
#define NIC15_V_SWCLEAR		7
#define NIC15_V_N		8

static const char *const nic15_vname[NIC15_V_N] = {
	"-", "txlen", "txoff", "txrb", "engine", "sweep", "swshow", "swclear"
};

/* The seven bits the gate reads.  128 states. */
#define NIC15_S_ENGINE		0x01	/* nic_engine_on    */
#define NIC15_S_UP		0x02	/* nic_ndev_up      */
#define NIC15_S_DIRTY		0x04	/* nic15_pol.dirty  */
#define NIC15_S_UNLOCK		0x08	/* nic_unlocked     */
#define NIC15_S_ALLOC		0x10	/* nic_allocated    */
#define NIC15_S_ARMED		0x20	/* nic_armed        */
#define NIC15_S_SWEEP		0x40	/* a sweep runs, and the caller is not it */
#define NIC15_S_ALL		0x7F

/* THE REFUSAL TABLE, ONE FUNCTION, run by the kernel and by nic15check.
 * Rows in precedence order; 0 permits.
 *
 *   txlen/txoff/txrb  engine on OR rlx0 up OR a sweep  -EBUSY  (F4: the
 *                                                  kernel tests this inside
 *                                                  spin_lock_irqsave)
 *   engine            a sweep (not the sweep's own)  -EBUSY
 *                     dirty                          -ESTALE  (1.4's own
 *                                                  -ENXIO and -EPERM are 1.4's
 *                                                  code, around :2307)
 *   sweep             a sweep, or rlx0 up            -EBUSY
 *                     locked                         -EPERM
 *                     not allocated or not armed     -ENXIO
 *                     (dirty is allowed: a sweep's first act is an arm)
 *                     then nic15_sweep_gate's bound: a WIRE sweep over more
 *                     than one length at any txlen but vendor  -EPERM
 *   swshow            nothing: it touches no hardware
 *   swclear           a sweep                        -EBUSY
 *
 * `ndo_open` asks the engine row at :1665, BEFORE napi_enable and
 * nic_ndev_up, so `ifconfig rlx0 up` over a dirty policy or a running sweep
 * changes nothing.  Parse errors (-EINVAL) are the parsers', before this is
 * asked; a sweep's record-key refusal (-EEXIST) is nic15_keycheck's, after. */
static inline int nic15_gate(int verb, unsigned int st)
{
	switch (verb) {
	case NIC15_V_TXLEN:
	case NIC15_V_TXOFF:
	case NIC15_V_TXRB:
		return (st & (NIC15_S_ENGINE | NIC15_S_UP | NIC15_S_SWEEP)) ?
			-EBUSY : 0;
	case NIC15_V_ENGINE:
		if (st & NIC15_S_SWEEP)
			return -EBUSY;
		return (st & NIC15_S_DIRTY) ? -ESTALE : 0;
	case NIC15_V_SWEEP:
		if (st & (NIC15_S_SWEEP | NIC15_S_UP))
			return -EBUSY;
		if (!(st & NIC15_S_UNLOCK))
			return -EPERM;
		if (!(st & NIC15_S_ALLOC) || !(st & NIC15_S_ARMED))
			return -ENXIO;
		return 0;
	case NIC15_V_SWSHOW:
		return 0;
	case NIC15_V_SWCLEAR:
		return (st & NIC15_S_SWEEP) ? -EBUSY : 0;
	}
	return -EINVAL;
}

/* A sweep's whole gate: the table's row, then THE OWNER'S BOUND.  The owner
 * allowed a wire sweep at 1.4's settings only BOUNDED, because at every
 * txlen but `vendor` about half the lengths are predicted to put a mis-sent
 * frame on the CPU port.  So a WIRE sweep over more than one length (from !=
 * to) is permitted only at txlen vendor, the setting both surviving rules
 * predict clean; at rlxfw, mlen, ext and d1..d3 a wire sweep is `sweep L L p
 * wire`, one length per command, and a card has to type every one.  -EPERM:
 * the operation is one the owner did not permit.  Loopback is unaffected. */
static inline int nic15_sweep_gate(unsigned int st, int wire, u32 from,
				   u32 to, int txlen)
{
	int rc = nic15_gate(NIC15_V_SWEEP, st);

	if (rc)
		return rc;
	if (wire && from != to && txlen != NIC15_LEN_VENDOR)
		return -EPERM;
	return 0;
}

/* A behaviour verb's whole effect, given the state: gate, set, mark dirty.
 * The kernel calls it under nic_lock with interrupts off; the host calls it
 * bare.  A refusal leaves the policy untouched. */
static inline int nic15_set(struct nic15_pol *p, int v, int val,
			    unsigned int st)
{
	int rc = nic15_gate(v, st);

	if (rc)
		return rc;
	if (v == NIC15_V_TXLEN)
		p->txlen = val;
	else if (v == NIC15_V_TXOFF)
		p->txoff = val;
	else if (v == NIC15_V_TXRB)
		p->txrb = val;
	else
		return -EINVAL;
	p->dirty = 1;
	return 0;
}

/* ---------------------------------------------------------------- parsers
 * 1.4's write handler has already stripped trailing CR, LF and space
 * (:2624-2629), so `txlen vendor ` arrives as `txlen vendor` and no refusal
 * can rest on a trailing space.  Numbers are canonical decimal: digits only,
 * no sign, no leading zero except "0" itself, at most four digits. */
#define NIC15_LMIN		60
#define NIC15_LMAX		1514
#define NIC15_NLEN		(NIC15_LMAX - NIC15_LMIN + 1)	/* 1,455 */

static inline long nic15_dec(const char *s, const char **end)
{
	long v = 0;
	int n = 0;

	while (s[n] >= '0' && s[n] <= '9') {
		if (n == 4)
			return -1;
		v = v * 10 + (s[n] - '0');
		n++;
	}
	if (!n || (n > 1 && s[0] == '0'))
		return -1;
	*end = s + n;
	return v;
}

static inline int nic15_parse_txlen(const char *a)
{
	int p;

	for (p = 0; p < NIC15_LEN_N; p++)
		if (!strcmp(a, nic15_len_tab[p].name))
			return p;
	return -EINVAL;
}

static inline int nic15_parse_txoff(const char *a)
{
	if (!strcmp(a, "2"))
		return 2;
	if (!strcmp(a, "0"))
		return 0;
	return -EINVAL;		/* 1 and 3: nobody's; 4 and 6 overstate 2,046 */
}

static inline int nic15_parse_txrb(const char *a)
{
	const char *e = a;
	long v = nic15_dec(a, &e);

	if (v < 0 || v > NIC15_RB_MAX || *e)
		return -EINVAL;
	return (int)v;
}

/* `sweep <from> <to> <probe>` is a LOOPBACK sweep: the sweep sets LBMODE
 * itself after every `engine on` (which writes CPUICR with `=`, :2308), so
 * the register's state before the verb decides nothing.  `sweep <from> <to>
 * <probe> wire` -- that word, once, last -- is the only way to put the
 * sweep's frames on the wire, so a wire sweep cannot happen by accident, and
 * nic15_sweep_gate bounds it (one length, except at txlen vendor).
 * 60 <= from <= to <= 1,514; probe 0 (the second frame is L again: block
 * 46's protocol) or
 * 60..1,514.  `sweep L L p` is one length. */
static inline int nic15_parse_sweep(const char *a, u32 *from, u32 *to,
				    u32 *probe, int *wire)
{
	const char *e = a;
	long f, t, p;
	int w;

	f = nic15_dec(a, &e);
	if (f < 0 || *e != ' ')
		return -EINVAL;
	t = nic15_dec(e + 1, &e);
	if (t < 0 || *e != ' ')
		return -EINVAL;
	p = nic15_dec(e + 1, &e);
	if (p < 0)
		return -EINVAL;
	if (!*e)
		w = 0;
	else if (!strcmp(e, " wire"))
		w = 1;
	else
		return -EINVAL;
	if (f < NIC15_LMIN || t > NIC15_LMAX || f > t)
		return -EINVAL;
	if (p && (p < NIC15_LMIN || p > NIC15_LMAX))
		return -EINVAL;
	*from = (u32)f;
	*to = (u32)t;
	*probe = (u32)p;
	*wire = w;
	return 0;
}

static inline int nic15_parse_swshow(const char *a, u32 *l)
{
	const char *e = a;
	long v = nic15_dec(a, &e);

	if (v < NIC15_LMIN || v > NIC15_LMAX || *e)
		return -EINVAL;
	*l = (u32)v;
	return 0;
}

/* ------------------------------------------------------ the frame, as sent
 * What nic_do_tx writes at frame offset j (讀 :2226-2244): a broadcast
 * destination, 02:52:4C:58:46:57, EtherType 0x88B5, "RLXFW-NIC ", the digit
 * '0' + n_tx % 10 taken before the call, then filler 0x40 + (k & 0x3F) where
 * k = j - 14.  A frame is OURS when bytes 6..13 (the source and the
 * EtherType) match; the digit at byte 24 then says WHICH of our frames came
 * back.  The sweep compares [0, F) one __raw_readb at a time (the RX buffer
 * is 2 mod 4, so memcmp's word loads could fault). */
static inline u8 nic15_txbyte(u32 j, u32 digit)
{
	static const u8 hdr[14] = {
		0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
		0x02, 0x52, 0x4C, 0x58, 0x46, 0x57,
		0x88, 0xB5
	};
	static const char tag[] = "RLXFW-NIC ";
	u32 k;

	if (j < 14)
		return hdr[j];
	k = j - 14;
	if (k < 10)
		return (u8)tag[k];
	if (k == 10)
		return (u8)('0' + digit % 10);
	return (u8)(0x40 + (k & 0x3F));
}

/* The digit an OURS frame carried, against the one it should carry and the
 * one the frame sent just before it carried: 0 its own, 1 the previous
 * frame's (a REPEAT: for b, frame a came back again), 2 any other. */
static inline int nic15_digit_state(u8 got, u32 digit, u32 prev)
{
	if (got == (u8)('0' + digit % 10))
		return 0;
	if (got == (u8)('0' + prev % 10))
		return 1;
	return 2;
}

/* id[0..7] are the looped frame's bytes 6..13, id[8] its byte 24.  OURS is
 * decided by bytes 6..13 alone -- a wrong digit is never FOREIGN -- and then
 * *dig says which of our frames it is. */
static inline int nic15_identify(const u8 *id, u32 digit, u32 prev, int *dig)
{
	u32 k;

	for (k = 0; k < 8; k++)
		if (id[k] != nic15_txbyte(6 + k, digit))
			return 0;
	*dig = nic15_digit_state(id[8], digit, prev);
	return 1;
}

/* ---------------------------------------------------------------- classes
 * One nibble per frame.  Loopback scores a frame by what came back; wire mode
 * only by whether its slot retired (SENT).  VOID is a unit whose frames were
 * FOREIGN twice: not scored.  SKEW is the instrument failing to resolve the
 * mbuf: not scored either, and never a bad frame. */
#define NIC15_C_NONE		0	/* not reached: b after a bad a    */
#define NIC15_C_RIGHT		1	/* ours, delta = delta0, [0,F) ok  */
#define NIC15_C_LONG		2	/* ours, delta > delta0            */
#define NIC15_C_SHORT		3	/* ours, delta < delta0            */
#define NIC15_C_CONTENT		4	/* ours, length right, bytes not   */
#define NIC15_C_ALIEN		5	/* not ours, ph < 64 or > 1,522    */
#define NIC15_C_FOREIGN		6	/* not ours, 64..1,522: retry once */
#define NIC15_C_SKEW		7	/* the mbuf did not resolve (F14)  */
#define NIC15_C_TIMEOUT		8	/* slot did not retire / no frame  */
#define NIC15_C_FAILTX		9	/* nic_do_tx refused               */
#define NIC15_C_SENT		10	/* wire mode: the slot retired     */
#define NIC15_C_VOID		11	/* FOREIGN twice                   */
#define NIC15_C_REPEAT		12	/* ours, the previous frame's digit */
#define NIC15_C_DIGIT		13	/* ours, any other wrong digit     */
#define NIC15_C_N		14

static const char *const nic15_cname[NIC15_C_N] = {
	"none", "right", "long", "short", "content", "alien", "foreign",
	"skew", "timeout", "failtx", "sent", "void", "repeat", "digit"
};

/* st: 0, or TIMEOUT / FAILTX / SKEW, which decide before anything is read.
 * ours: bytes 6..13 matched; dig: nic15_digit_state (only when ours).
 * delta = ph_len - (F + 4); delta0 is the registered one. */
static inline int nic15_classify(int st, int ours, int dig, int content_ok,
				 long delta, long delta0, u32 ph)
{
	if (st)
		return st;
	if (!ours)
		return (ph < 64 || ph > 1522) ? NIC15_C_ALIEN : NIC15_C_FOREIGN;
	if (dig == 1)
		return NIC15_C_REPEAT;
	if (dig)
		return NIC15_C_DIGIT;
	if (delta > delta0)
		return NIC15_C_LONG;
	if (delta < delta0)
		return NIC15_C_SHORT;
	return content_ok ? NIC15_C_RIGHT : NIC15_C_CONTENT;
}

/* A class that says the frame went wrong.  NONE, VOID, SKEW and the two good
 * ones are not. */
static inline int nic15_bad(int c)
{
	return c != NIC15_C_NONE && c != NIC15_C_RIGHT &&
	       c != NIC15_C_SENT && c != NIC15_C_VOID && c != NIC15_C_SKEW;
}

/* ------------------------------------------------- the sweep's bookkeeping
 * REGISTRATION.  The first unit's frame a sets delta0 = ph_len - (F + 4).  It
 * must be RIGHT and delta0 must be 0 (1.4's measured ph_len = F + 4, 11 of 11)
 * or 4 (the engine appending a CRC under mlen/vendor, F7); anything else is a
 * finding about the setting and the sweep refuses -EPROTO. */
static inline int nic15_register(int cls, long delta)
{
	if (cls != NIC15_C_RIGHT)
		return -EPROTO;
	return (delta == 0 || delta == 4) ? 0 : -EPROTO;
}

/* RETRIES.  After a unit's try: DONE (record it), RETRY (once, counted once),
 * VOID (FOREIGN on the retry as well), or NOREG (FOREIGN twice while delta0
 * is not yet registered: the sweep refuses -EPROTO, as registration says). */
#define NIC15_ACT_DONE		0
#define NIC15_ACT_RETRY		1
#define NIC15_ACT_VOID		2
#define NIC15_ACT_NOREG		3

static inline int nic15_try_act(int tries, int foreign, int reg)
{
	if (!foreign)
		return NIC15_ACT_DONE;
	if (!tries)
		return NIC15_ACT_RETRY;
	return reg ? NIC15_ACT_VOID : NIC15_ACT_NOREG;
}

/* 6 bytes per length, 8,730 in all.  Records ACCUMULATE across sweeps under
 * one key and are NEVER erased by a sweep: a unit that completes overwrites
 * its own length, an aborted sweep leaves every other record as it was, and
 * a sweep under a different key is refused (-EEXIST) while records exist --
 * `swclear` is the only eraser.  The map reads each length as one of six
 * codes, and 0 is a code of its own, so an unswept length never reads clean:
 *   0  no record (never swept under this key)
 *   1  scored, neither frame bad
 *   2  bad b   (a right, b not)
 *   3  bad a   (b is not sent after a bad a, so 2 and 3 cannot both hold)
 *   4  VOID    (FOREIGN twice: not scored)
 *   5  SKEW    (the mbuf did not resolve: not scored, not bad) */
struct nic15_rec {
	u16 ph_a, ph_b;		/* the looped ph_len of a and of b, 0 if none */
	u8 cls;			/* a << 4 | b */
	u8 extra;		/* CPU-owned mbufs the unit's last frame left */
};

#define NIC15_M_NONE		0
#define NIC15_M_CLEAN		1
#define NIC15_M_BADB		2
#define NIC15_M_BADA		3
#define NIC15_M_VOID		4
#define NIC15_M_SKEW		5
#define NIC15_M_N		6

static inline int nic15_code(const struct nic15_rec *r, int recorded)
{
	int ca = r->cls >> 4, cb = r->cls & 0xF;

	if (!recorded)
		return NIC15_M_NONE;
	if (ca == NIC15_C_VOID)
		return NIC15_M_VOID;
	if (ca == NIC15_C_SKEW || cb == NIC15_C_SKEW)
		return NIC15_M_SKEW;
	if (nic15_bad(ca))
		return NIC15_M_BADA;
	if (nic15_bad(cb))
		return NIC15_M_BADB;
	return NIC15_M_CLEAN;
}

/* The key the records are written under.  nic_tx_rings is in it: the idle
 * rings change what the engine walks. */
struct nic15_key {
	int txlen, txoff, txrb, wire;
	u32 probe, rings;
};

static inline int nic15_keycheck(const struct nic15_key *have, u32 n_rec,
				 const struct nic15_key *want)
{
	if (!n_rec)
		return 0;
	if (have->txlen != want->txlen || have->txoff != want->txoff ||
	    have->txrb != want->txrb || have->wire != want->wire ||
	    have->probe != want->probe || have->rings != want->rings)
		return -EEXIST;
	return 0;
}

/* THE MARKS.  A refused sweep prints neither.  Every sweep that printed
 *   RLXFW-N-SWEEP=MMFFFTTT   MM 4C loopback / 57 wire, FFF from, TTT to (hex)
 * closes with
 *   RLXFW-N-SWSUM=SSSSVVVV   units scored, units VOID (this sweep)
 *   RLXFW-N-SWEND=AAAABBBB   bad a, bad b -- or the negative errno
 * A sweep that scored nothing ends -ENODATA, never 00000000: a clean sweep
 * reads SWSUM with S > 0 and SWEND 00000000. */
static inline u32 nic15_swbegin_val(int wire, u32 from, u32 to)
{
	return ((u32)(wire ? 0x57 : 0x4C) << 24) | ((from & 0xFFF) << 12) |
	       (to & 0xFFF);
}

static inline u32 nic15_swsum_val(u32 scored, u32 voids)
{
	return ((scored & 0xFFFF) << 16) | (voids & 0xFFFF);
}

static inline u32 nic15_swend_val(int rc, u32 bad_a, u32 bad_b)
{
	if (rc)
		return (u32)rc;
	return ((bad_a & 0xFFFF) << 16) | (bad_b & 0xFFFF);
}

static inline int nic15_sweep_rc(int rc, u32 scored)
{
	if (rc)
		return rc;
	return scored ? 0 : -ENODATA;
}

#define NIC15_SW_NEVER		0
#define NIC15_SW_RUN		1
#define NIC15_SW_DONE		2
#define NIC15_SW_FAIL		3
#define NIC15_SW_INTR		4	/* a signal: the loop stopped, -EINTR */
#define NIC15_SW_N		5

static const char *const nic15_swname[NIC15_SW_N] = {
	"never", "run", "done", "fail", "intr"
};

/* This sweep's counts are u16: none can pass 2 x 1,455 x 2 (drained, which
 * can, is u32). */
struct nic15_sum {
	int state, rc, wire;
	u32 from, to, probe, bufs;
	int reg, delta0;		/* delta0 valid when reg */
	int noreg_cls;			/* -EPROTO: frame a's class, else 0 */
	u32 noreg_ph;
	int noreg_delta;
	u16 units, scored, voids, skews, retries, foreign, alien;
	u16 timeouts, cycles, bad_a, bad_b;
	u32 drained, j0, j1;
	u32 last_l;
	struct nic15_rec last;
	struct nic15_key key;		/* what the records were written under */
	u32 n_rec;			/* how many lengths hold a record */
};

/* ----------------------------------------------------------- the formatters
 * Every line goes through nic15_pf: checked against the soft cap BEFORE it is
 * written, exactly as 1.4's loops are (`truncated 1` then stops the page),
 * and written with vsnprintf bounded by the hard size, so no line can store
 * past the page whatever it holds.  nic15check measures the whole page with
 * every counter at its widest value. */
struct nic15_pg {
	char *buf;
	int len, size, cap, trunc;
};

static void nic15_pf(struct nic15_pg *pg, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));

static void nic15_pf(struct nic15_pg *pg, const char *fmt, ...)
{
	va_list ap;
	int room, n;

	if (pg->trunc)
		return;
	room = pg->size - pg->len;
	if (room <= 1)
		return;
	if (pg->len > pg->cap) {
		pg->trunc = 1;
		n = snprintf(pg->buf + pg->len, room, "truncated 1\n");
	} else {
		va_start(ap, fmt);
		n = vsnprintf(pg->buf + pg->len, room, fmt, ap);
		va_end(ap);
	}
	if (n < 0)
		n = 0;
	if (n > room - 1)
		n = room - 1;
	pg->len += n;
}

/* The one line 1.5 adds to /proc/rtl819x-nic, on 1.4's blank :2571, before
 * the 1.4 tail (rx_len .. rx_ph4 [rx_bytes]), so frozen cards' terminators on
 * rx_ph4 still match.  At most size - 1 bytes and always ending in a newline,
 * whatever the fields hold; the main dump passes 64. */
static inline int nic15_fmt_tx15(char *buf, int size,
				 const struct nic15_pol *p, int p15)
{
	struct nic15_pg pg;

	pg.buf = buf;
	pg.len = 0;
	pg.size = size;
	pg.cap = size;
	pg.trunc = 0;
	nic15_pf(&pg, "tx15 txlen %s txoff %d txrb %d dirty %d p15 %d\n",
		 nic15_len_name(p->txlen), p->txoff, p->txrb, p->dirty, p15);
	if (pg.len > 0 && buf[pg.len - 1] != '\n')
		buf[pg.len - 1] = '\n';
	return pg.len;
}

/* W: what a writer queued in a slot at its last fill. */
struct nic15_w {
	u32 f;			/* the F it stored             */
	u32 n;			/* the fill number (n_txq)     */
	u8 pol, off, rb, path;	/* path 0 none, 1 xmit, 2 tx   */
};

static const char *const nic15_pathname[3] = { "-", "xmit", "tx" };

/* Everything /proc/rtl819x-nic-tx prints, gathered by the caller.  R is read
 * uncached by the kernel at page time; no looped byte and no RX-buffer byte
 * is here -- TX descriptor words, lengths, classes and counts only. */
struct nic15_view {
	const char *version;
	const struct nic15_pol *pol;
	int p15, last_v, last_rc, allocated;
	u32 n_ok, n_refused, n_txq, n_arm15;
	const struct nic15_w *w;		/* [NIC15_TXD]            */
	u32 r[NIC15_TXD][13];			/* ring, ph w0-5, mb w0-5 */
	u32 (*q)[13];				/* [NIC15_TXD][13]        */
	const u8 *qv;				/* [NIC15_TXD]            */
	u32 rb_chk, rb_bad, rb_n, rb_i, rb_w, rb_got, rb_want;
	const struct nic15_sum *sw;
	const struct nic15_rec *rec;		/* [NIC15_NLEN]           */
	const u8 *recd;				/* bitmap over the same   */
	u32 show;
};

#define NIC15_RECD(recd, i)	((recd)[(i) >> 3] & (0x80 >> ((i) & 7)))
#define NIC15_HB		16	/* histogram bins */

/* The map's alphabet: one character per PAIR of lengths, 6 x first + second
 * code, so a line of 64 still covers 128 lengths and the page is no longer
 * than with two-bit codes.  '0' two unswept, '7' two clean, 'E' two bad b,
 * 'L' two bad a, 'S' two VOID, 'Z' two SKEW; '0'..'5' a pair whose FIRST
 * length was never swept.  nic15check decodes it with a decoder of its own. */
static const char nic15_alph[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

static inline const char *nic15_mode_name(int wire)
{
	return wire ? "wire" : "loop";
}

/* The page.  Its layout, line by line:
 *   version, tx15, v15 (last verb, its rc, the counters)
 *   w0..w3   W: F, policy, writer and fill number of each slot's last fill
 *   r0..r3   R: ring word, ph w0-w5, mb w0-w5, as memory holds them now
 *   q0..q3   Q: the same 13 words as the txrb loads returned; only slots
 *            whose last fill loaded, and v says which (1 fields, 2 ring)
 *   rb       Q's check against what the fill meant to write
 *   sw ...   the LAST sweep: state, mode, args, rc; the key the records are
 *            under; its counts (scored, bad a, bad b, VOID, SKEW, ...);
 *            delta0; its last unit; why it refused, if it did
 *   mt       the RECORDS, all sweeps under the key: how many of each code
 *   m00..m11 the map, one character per pair of lengths (nic15_alph)
 *   hb       ph_b over the bad-b lengths: ph:count:first-last, 16 bins, and
 *            the VOID lengths the histogram cannot contain
 *   ww       32 lengths from `swshow`: ph:classes(a b):extra, where ph is
 *            ph_b, or ph_a when a went wrong; `-` no record, `v` VOID */
static int nic15_format(char *buf, int size, int cap,
			const struct nic15_view *v)
{
	const struct nic15_sum *s = v->sw;
	struct nic15_pg pg;
	u32 hph[NIC15_HB], hn[NIC15_HB], hf[NIC15_HB], hl[NIC15_HB];
	u32 mt[NIC15_M_N];
	u32 nb = 0, other = 0, i, k, l0, start;
	char tx15[64];

	pg.buf = buf;
	pg.len = 0;
	pg.size = size;
	pg.cap = cap;
	pg.trunc = 0;

	nic15_pf(&pg, "version %s\n", v->version);
	nic15_fmt_tx15(tx15, sizeof(tx15), v->pol, v->p15);
	nic15_pf(&pg, "%s", tx15);
	nic15_pf(&pg, "v15 last %s %d ok %u refused %u txq %u arm15 %u\n",
		 nic15_vname[(v->last_v >= 0 && v->last_v < NIC15_V_N) ?
			     v->last_v : 0],
		 v->last_rc, v->n_ok, v->n_refused, v->n_txq, v->n_arm15);
	for (i = 0; i < NIC15_TXD; i++)
		nic15_pf(&pg, "w%u F %u pol %s off %u rb %u path %s n %u\n",
			 i, v->w[i].f, nic15_len_name(v->w[i].pol),
			 v->w[i].off, v->w[i].rb,
			 nic15_pathname[v->w[i].path < 3 ? v->w[i].path : 0],
			 v->w[i].n);
	for (i = 0; i < NIC15_TXD; i++) {
		if (!v->allocated) {
			nic15_pf(&pg, "r%u -\n", i);
			continue;
		}
		nic15_pf(&pg, "r%u %08X %08X %08X %08X %08X %08X %08X "
			 "%08X %08X %08X %08X %08X %08X\n", i,
			 v->r[i][0], v->r[i][1], v->r[i][2], v->r[i][3],
			 v->r[i][4], v->r[i][5], v->r[i][6], v->r[i][7],
			 v->r[i][8], v->r[i][9], v->r[i][10], v->r[i][11],
			 v->r[i][12]);
	}
	for (i = 0; i < NIC15_TXD; i++) {
		if (!v->qv[i])
			continue;
		nic15_pf(&pg, "q%u v%X %08X %08X %08X %08X %08X %08X %08X "
			 "%08X %08X %08X %08X %08X %08X\n", i, v->qv[i] & 0xF,
			 v->q[i][0], v->q[i][1], v->q[i][2], v->q[i][3],
			 v->q[i][4], v->q[i][5], v->q[i][6], v->q[i][7],
			 v->q[i][8], v->q[i][9], v->q[i][10], v->q[i][11],
			 v->q[i][12]);
	}
	nic15_pf(&pg, "rb chk %u bad %u first n %u slot %u word %u "
		 "got %08X want %08X\n", v->rb_chk, v->rb_bad, v->rb_n,
		 v->rb_i, v->rb_w, v->rb_got, v->rb_want);

	nic15_pf(&pg, "sw %s mode %s from %u to %u probe %u rc %d bufs %08X\n",
		 nic15_swname[(s->state >= 0 && s->state < NIC15_SW_N) ?
			      s->state : 0], nic15_mode_name(s->wire),
		 s->from, s->to, s->probe, s->rc, s->bufs);
	nic15_pf(&pg, "sw key txlen %s txoff %d txrb %d mode %s probe %u "
		 "rings %u rec %u\n", nic15_len_name(s->key.txlen),
		 s->key.txoff, s->key.txrb, nic15_mode_name(s->key.wire),
		 s->key.probe, s->key.rings, s->n_rec);
	nic15_pf(&pg, "sw scored %u bad_a %u bad_b %u void %u skew %u "
		 "retry %u foreign %u alien %u\n", s->scored, s->bad_a,
		 s->bad_b, s->voids, s->skews, s->retries, s->foreign,
		 s->alien);
	nic15_pf(&pg, "sw delta0 %d reg %d units %u timeout %u cycles %u "
		 "drained %u j0 %u j1 %u\n", s->delta0, s->reg, s->units,
		 s->timeouts, s->cycles, s->drained, s->j0, s->j1);
	nic15_pf(&pg, "sw last %u a %u %X b %u %X x %u\n", s->last_l,
		 s->last.ph_a, s->last.cls >> 4, s->last.ph_b,
		 s->last.cls & 0xF, s->last.extra);
	if (s->noreg_cls)
		nic15_pf(&pg, "sw noreg %s ph %u delta %d\n",
			 nic15_cname[(s->noreg_cls > 0 &&
				      s->noreg_cls < NIC15_C_N) ?
				     s->noreg_cls : 0],
			 s->noreg_ph, s->noreg_delta);

	/* the records, counted by code */
	for (k = 0; k < NIC15_M_N; k++)
		mt[k] = 0;
	for (i = 0; i < NIC15_NLEN; i++)
		mt[nic15_code(&v->rec[i], NIC15_RECD(v->recd, i) != 0)]++;
	nic15_pf(&pg, "mt none %u clean %u bad_b %u bad_a %u void %u "
		 "skew %u\n", mt[NIC15_M_NONE], mt[NIC15_M_CLEAN],
		 mt[NIC15_M_BADB], mt[NIC15_M_BADA], mt[NIC15_M_VOID],
		 mt[NIC15_M_SKEW]);

	/* the map: 12 lines x 64 characters x 2 lengths */
	for (k = 0; k < 12; k++) {
		char line[65];
		u32 d;

		for (d = 0; d < 64; d++) {
			u32 l = NIC15_LMIN + 128 * k + 2 * d, c[2], b;

			for (b = 0; b < 2; b++, l++)
				c[b] = (l <= NIC15_LMAX) ?
					(u32)nic15_code(&v->rec[l - NIC15_LMIN],
						NIC15_RECD(v->recd,
							   l - NIC15_LMIN) != 0)
					: NIC15_M_NONE;
			line[d] = nic15_alph[c[0] * NIC15_M_N + c[1]];
		}
		line[64] = '\0';
		nic15_pf(&pg, "m%02u %s\n", k, line);
	}

	/* ph_b over the bad-b lengths, first seen first */
	for (i = 0; i < NIC15_NLEN; i++) {
		u32 ph;

		if (nic15_code(&v->rec[i], NIC15_RECD(v->recd, i) != 0) !=
		    NIC15_M_BADB)
			continue;
		ph = v->rec[i].ph_b;
		for (k = 0; k < nb; k++)
			if (hph[k] == ph)
				break;
		if (k == nb) {
			if (nb == NIC15_HB) {
				other++;
				continue;
			}
			hph[nb] = ph;
			hn[nb] = 0;
			hf[nb] = i + NIC15_LMIN;
			nb++;
		}
		hn[k]++;
		hl[k] = i + NIC15_LMIN;
	}
	nic15_pf(&pg, "hb n %u other %u void %u\n", nb, other,
		 mt[NIC15_M_VOID]);
	for (k = 0; k < nb; k += 4) {
		char line[128];
		struct nic15_pg lp;
		u32 j;

		lp.buf = line;
		lp.len = 0;
		lp.size = sizeof(line);
		lp.cap = sizeof(line);
		lp.trunc = 0;
		nic15_pf(&lp, "hb");
		for (j = k; j < k + 4 && j < nb; j++)
			nic15_pf(&lp, " %u:%u:%u-%u", hph[j], hn[j], hf[j],
				 hl[j]);
		nic15_pf(&pg, "%s\n", line);
	}

	/* the window */
	start = v->show;
	if (start < NIC15_LMIN)
		start = NIC15_LMIN;
	if (start > NIC15_LMAX - 31)
		start = NIC15_LMAX - 31;
	for (l0 = start; l0 < start + 32; l0 += 8) {
		char line[160];
		struct nic15_pg lp;
		u32 l;

		lp.buf = line;
		lp.len = 0;
		lp.size = sizeof(line);
		lp.cap = sizeof(line);
		lp.trunc = 0;
		nic15_pf(&lp, "ww %u", l0);
		for (l = l0; l < l0 + 8; l++) {
			const struct nic15_rec *r = &v->rec[l - NIC15_LMIN];
			int c = nic15_code(r, NIC15_RECD(v->recd,
							l - NIC15_LMIN) != 0);

			if (c == NIC15_M_NONE)
				nic15_pf(&lp, " -");
			else if (c == NIC15_M_VOID)
				nic15_pf(&lp, " v");
			else
				nic15_pf(&lp, " %u:%X%X:%u",
					 c == NIC15_M_BADA ? r->ph_a : r->ph_b,
					 r->cls >> 4, r->cls & 0xF, r->extra);
		}
		nic15_pf(&pg, "%s\n", line);
	}
	return pg.len;
}

/* ------------------------------------------------------------- the verbs
 * Reached only at 1.4's final `return -EINVAL` (:3027), so every 1.4 verb
 * parses exactly as before.  No 1.4 prefix captures a 1.5 verb: `tx ` needs
 * a space third, `txrings `/`txmode `/`txstall ` their own spellings, `poll`
 * four letters no 1.5 verb starts with.  A verb word is matched whole: bare,
 * or followed by exactly one space.  Every accepted verb returns `count`
 * (F9: a write_proc that returns 0 is re-issued by stdio, and a sweep would
 * run again); a refusal returns its errno and is recorded in v15_last. */
#define NIC15_PROC_NAME		"rtl819x-nic-tx"

static inline int nic15_verb(const char *buf, const char **arg)
{
	int v;
	size_t n;

	for (v = NIC15_V_TXLEN; v < NIC15_V_N; v++) {
		if (v == NIC15_V_ENGINE)
			continue;
		n = strlen(nic15_vname[v]);
		if (strncmp(buf, nic15_vname[v], n))
			continue;
		if (buf[n] == '\0') {
			*arg = NULL;
			return v;
		}
		if (buf[n] == ' ') {
			*arg = buf + n + 1;
			return v;
		}
	}
	return NIC15_V_NONE;
}

/* The includer's five hooks.  In the kernel: nic15_apply takes nic_lock and
 * calls nic15_set on the live state; nic15_sweep_run asks the gate and the
 * key and runs the sweep; nic15_swclear_run asks the gate and forgets the
 * records; nic15_ret records v15_last and counts. */
static int nic15_apply(int v, int val);
static int nic15_sweep_run(u32 from, u32 to, u32 probe, int wire);
static void nic15_swshow_set(u32 l);
static int nic15_swclear_run(void);
static int nic15_ret(int v, int rc);

static int nic15_write(const char *buf, unsigned long count)
{
	const char *a = NULL;
	int v, val, rc, w = 0;
	u32 x = 0, y = 0, z = 0;

	v = nic15_verb(buf, &a);
	if (v == NIC15_V_NONE)
		return -EINVAL;		/* 1.4's answer to an unknown verb */
	switch (v) {
	case NIC15_V_TXLEN:
	case NIC15_V_TXOFF:
	case NIC15_V_TXRB:
		if (!a)
			val = -EINVAL;
		else if (v == NIC15_V_TXLEN)
			val = nic15_parse_txlen(a);
		else if (v == NIC15_V_TXOFF)
			val = nic15_parse_txoff(a);
		else
			val = nic15_parse_txrb(a);
		if (val < 0)
			return nic15_ret(v, val);
		rc = nic15_apply(v, val);
		break;
	case NIC15_V_SWEEP:
		if (!a || nic15_parse_sweep(a, &x, &y, &z, &w))
			return nic15_ret(v, -EINVAL);
		rc = nic15_sweep_run(x, y, z, w);
		break;
	case NIC15_V_SWCLEAR:
		if (a)
			return nic15_ret(v, -EINVAL);
		rc = nic15_swclear_run();
		break;
	default:				/* NIC15_V_SWSHOW */
		if (!a || nic15_parse_swshow(a, &x))
			return nic15_ret(v, -EINVAL);
		nic15_swshow_set(x);
		rc = 0;
		break;
	}
	return nic15_ret(v, rc ? rc : (int)count);
}

#ifndef NIC15_HOST
#include <linux/sched.h>	/* cond_resched(), signal_pending() */

/* 1.4's lines reach these before the definitions appended after :3113.  The
 * policy is a tentative definition (C99 6.9.2); its initialiser is there. */
static struct nic15_pol nic15_pol;

static void nic15_rb_pre_own(unsigned int i);
static void nic15_rb_pre_bell(unsigned int i);
static void nic15_note(unsigned int i, u32 f, int path);
static int nic15_engine_gate(void);
static void nic15_armed(void);
static int nic15_line(char *page, int *len);
static void nic15_init(void);
#endif

#endif /* RTL819X_NIC_TX_H */
