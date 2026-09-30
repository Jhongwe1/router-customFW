/* src/httpd/rl.c -- the token buckets declared in rl.h.
 *
 * All arithmetic is unsigned 32-bit and every product is bounded before it is
 * taken: `elapsed_ms * rate_milli` would overflow for an elapsed time of a few
 * days at the connection rate, so elapsed is clamped first and the refill is
 * saturated at the burst.  A monotonic clock that goes backwards (it should not,
 * but a counter wrap on a 32-bit millisecond field happens every 49.7 days and
 * this box is meant to run for longer than that) refills nothing rather than
 * refilling everything: the bucket's `last_ms` is simply moved forward.
 *
 * WHAT IT DOES NOT ESTABLISH.  That the rate is right.  The rate is an argument,
 * written in notes/httpd.md against a budget; this file only implements it.
 */

#include "rl.h"

void rl_init(struct rl_bucket *b, uint32_t burst, uint32_t milli_per_s)
{
	b->cap_milli = burst * 1000u;
	b->rate_milli = milli_per_s;
	b->tokens_milli = b->cap_milli;
	b->last_ms = 0;
	b->started = 0;
}

static void rl_refill(struct rl_bucket *b, uint32_t now_ms)
{
	uint32_t dt, add;

	if (!b->started) {
		b->started = 1;
		b->last_ms = now_ms;
		return;
	}
	if (now_ms < b->last_ms) {          /* wrap, or a clock that moved back */
		b->last_ms = now_ms;
		return;
	}
	/* A rate of zero is a hard cap: the burst, and then never again.  Without
	 * this line the saturating branch below would refill it to full after a
	 * long enough gap, which is the opposite of what a zero rate means.  量 by
	 * test_rl.c's zero-rate case, which is why that case exists. */
	if (b->rate_milli == 0) {
		b->last_ms = now_ms;
		return;
	}
	dt = now_ms - b->last_ms;
	if (dt == 0)
		return;
	/* Clamp before multiplying: at the highest rate here (16,000 milli/s)
	 * dt must stay under 268,435 ms for dt*rate to fit in 32 bits.  A longer
	 * gap can only mean "full", so clamp and saturate. */
	if (dt > 200000u) {
		b->tokens_milli = b->cap_milli;
		b->last_ms = now_ms;
		return;
	}
	add = (dt * b->rate_milli) / 1000u;
	if (add == 0)
		return;                      /* keep last_ms: the remainder accrues */
	/* Advance the clock only by the time the granted tokens actually cost, so
	 * the truncated remainder is not thrown away.  Dropping it would make the
	 * bucket drift slower than its declared rate -- safe, but it would mean the
	 * rate in notes/httpd.md is not the rate the code implements, and the
	 * budget is computed from that number. */
	b->last_ms += (add * 1000u) / b->rate_milli;
	if (b->cap_milli - b->tokens_milli <= add)
		b->tokens_milli = b->cap_milli;
	else
		b->tokens_milli += add;
}

int rl_take(struct rl_bucket *b, uint32_t now_ms)
{
	rl_refill(b, now_ms);
	if (b->tokens_milli < 1000u)
		return 0;
	b->tokens_milli -= 1000u;
	return 1;
}

uint32_t rl_retry_s(const struct rl_bucket *b)
{
	uint32_t need;

	if (b->tokens_milli >= 1000u)
		return 0;
	if (b->rate_milli == 0)
		return 3600u;
	need = 1000u - b->tokens_milli;
	/* round up, and never say zero */
	return (need + b->rate_milli - 1u) / b->rate_milli + 1u;
}

void rl_table_init(struct rl_table *t, uint32_t burst, uint32_t milli_per_s)
{
	unsigned i;

	t->burst = burst;
	t->rate_milli = milli_per_s;
	for (i = 0; i < RL_IPS; i++) {
		t->e[i].ip = 0;
		t->e[i].last_ms = 0;
		t->e[i].used = 0;
		rl_init(&t->e[i].b, burst, milli_per_s);
	}
}

static unsigned rl_table_slot(struct rl_table *t, uint32_t ip, uint32_t now_ms)
{
	unsigned i, lru = 0;
	uint32_t oldest = 0;
	int have_oldest = 0;

	for (i = 0; i < RL_IPS; i++) {
		if (t->e[i].used && t->e[i].ip == ip) {
			t->e[i].last_ms = now_ms;
			return i;
		}
	}
	for (i = 0; i < RL_IPS; i++) {
		if (!t->e[i].used) {
			t->e[i].used = 1;
			t->e[i].ip = ip;
			t->e[i].last_ms = now_ms;
			rl_init(&t->e[i].b, t->burst, t->rate_milli);
			return i;
		}
	}
	for (i = 0; i < RL_IPS; i++) {
		if (!have_oldest || t->e[i].last_ms < oldest) {
			oldest = t->e[i].last_ms;
			lru = i;
			have_oldest = 1;
		}
	}
	t->e[lru].ip = ip;
	t->e[lru].last_ms = now_ms;
	rl_init(&t->e[lru].b, t->burst, t->rate_milli);
	return lru;
}

int rl_table_take(struct rl_table *t, uint32_t ip, uint32_t now_ms)
{
	unsigned s = rl_table_slot(t, ip, now_ms);

	return rl_take(&t->e[s].b, now_ms);
}

void rl_table_refund(struct rl_table *t, uint32_t ip)
{
	unsigned i;

	for (i = 0; i < RL_IPS; i++) {
		if (t->e[i].used && t->e[i].ip == ip) {
			struct rl_bucket *b = &t->e[i].b;

			if (b->cap_milli - b->tokens_milli <= 1000u)
				b->tokens_milli = b->cap_milli;
			else
				b->tokens_milli += 1000u;
			return;
		}
	}
}

uint32_t rl_table_retry_s(struct rl_table *t, uint32_t ip)
{
	unsigned i;

	for (i = 0; i < RL_IPS; i++) {
		if (t->e[i].used && t->e[i].ip == ip)
			return rl_retry_s(&t->e[i].b);
	}
	return 1u;
}
