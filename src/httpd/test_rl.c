/* src/httpd/test_rl.c -- the token buckets, and the controls that make the
 * numbers mean something.
 *
 * Every case here is arithmetic on a clock the test supplies, so there is no
 * sleep and no wall-clock dependence.  The two controls matter more than the
 * cases: a bucket that never refuses would make every "refused as expected" line
 * below vacuous, so one case shows a bucket refusing and another shows the same
 * bucket permitting after exactly the time the rate says.
 */

#include "rl.h"
#include "testlib.h"

int main(void)
{
	struct rl_bucket b;
	struct rl_table t;
	unsigned i;
	int taken;

	/* burst 3, one token per 4 s: the login bucket of notes/httpd.md */
	rl_init(&b, RL_KDF_BURST, RL_KDF_RATE_MILLI);
	taken = 0;
	for (i = 0; i < 10; i++)
		taken += rl_take(&b, 0);
	t_okf(taken == 3, "burst of 3 at t=0", taken, 3);

	t_okf(rl_take(&b, 3999) == 0, "still empty at 3.999 s", 0, 0);
	t_okf(rl_take(&b, 4000) == 1, "one token at 4.000 s", 1, 1);
	t_okf(rl_take(&b, 4001) == 0, "and only one", 0, 0);
	t_okf(rl_take(&b, 12000) == 1, "another after 8 more seconds", 1, 1);

	/* saturation at the burst, not above it */
	rl_init(&b, RL_KDF_BURST, RL_KDF_RATE_MILLI);
	(void)rl_take(&b, 0);
	(void)rl_take(&b, 0);
	(void)rl_take(&b, 0);
	taken = 0;
	for (i = 0; i < 10; i++)
		taken += rl_take(&b, 1000000);
	t_okf(taken == 3, "a long idle refills to the burst and no further",
	      taken, 3);

	/* Retry-After never says "now" when there is nothing to take. */
	rl_init(&b, 1, RL_KDF_RATE_MILLI);
	(void)rl_take(&b, 0);
	t_ok(rl_retry_s(&b) >= 1, "retry_s is at least one second", NULL);
	rl_init(&b, 1, RL_KDF_RATE_MILLI);
	t_okf(rl_retry_s(&b) == 0, "retry_s is zero while a token is there",
	      (long)rl_retry_s(&b), 0);

	/* A clock that goes backwards must not refill.  A 32-bit millisecond
	 * counter wraps every 49.7 days and this box is meant to outlive that. */
	rl_init(&b, 2, RL_KDF_RATE_MILLI);
	(void)rl_take(&b, 4000000);
	(void)rl_take(&b, 4000000);
	t_okf(rl_take(&b, 10) == 0, "a backwards clock grants nothing", 0, 0);

	/* A rate of zero is a hard cap: burst and then never again. */
	rl_init(&b, 2, 0);
	t_okf(rl_take(&b, 0) + rl_take(&b, 0) == 2, "a zero rate gives its burst",
	      2, 2);
	t_okf(rl_take(&b, 1000000000u) == 0, "and nothing after it", 0, 0);

	/* ------------------------------------------------ the per-address table */
	rl_table_init(&t, 2, RL_KDF_RATE_MILLI);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) == 1, "first address, first token",
	      1, 1);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) == 1, "and its second", 1, 1);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) == 0, "and no third", 0, 0);
	t_okf(rl_table_take(&t, 0x0a010165u, 0) == 1,
	      "a different address has its own bucket", 1, 1);

	/* Sixteen addresses each keep a bucket; the seventeenth evicts one.  That
	 * is the honest limit of a fixed table, and it is why the GLOBAL bucket is
	 * the one the anti-DoS budget is computed from: an attacker who cycles
	 * seventeen source addresses resets his own per-address bucket. */
	rl_table_init(&t, 1, 0);
	for (i = 0; i < RL_IPS; i++)
		(void)rl_table_take(&t, 0x0a010100u + i, (uint32_t)i);
	taken = 0;
	for (i = 0; i < RL_IPS; i++)
		taken += rl_table_take(&t, 0x0a010100u + i, 100);
	t_okf(taken == 0, "sixteen addresses all held their empty buckets", taken,
	      0);
	t_okf(rl_table_take(&t, 0x0a0102ffu, 200) == 1,
	      "the seventeenth address evicts the least recent and is granted",
	      1, 1);
	t_okf(rl_table_take(&t, 0x0a010100u, 300) == 1,
	      "the evicted address comes back with a fresh bucket (the limit)",
	      1, 1);

	/* The control on every line above: if rl_take could not refuse, none of
	 * them would mean anything.  Here it is refusing, and here it is
	 * permitting, in the same two lines. */
	rl_init(&b, 1, 0);
	t_okf(rl_take(&b, 0) == 1, "control: the bucket can permit", 1, 1);
	t_okf(rl_take(&b, 0) == 0, "control: the bucket can refuse", 0, 0);

	/* 2026-09-30, image r78a: POST /api/login answered `429 retry_s 2` across
	 * a 20 s idle gap and then a 90 s one.  Neither login bucket here can do
	 * that, and these are the cases that say so -- the 429 came from the
	 * parent's grant marker in serve.c, not from this arithmetic.
	 *
	 * The refutation condition, written first: if a single (tokens, last_ms)
	 * state existed from which a 90 s gap with no call in it left the bucket
	 * refusing, rl.c would be a candidate and this case would go red. */
	{
		uint32_t tok;
		int refused = 0, granted = 0;

		for (tok = 0; tok <= (uint32_t)RL_KDF_BURST * 1000u; tok += 250u) {
			struct rl_bucket q;

			rl_init(&q, RL_KDF_BURST, RL_KDF_RATE_MILLI);
			q.started = 1;
			q.tokens_milli = tok;
			q.last_ms = 640000u;
			if (rl_take(&q, 640000u + 90000u))
				granted++;
			else
				refused++;
		}
		t_okf(refused == 0, "a 90 s idle gap refills a login bucket from"
		      " every state it can be in", refused, 0);
		t_okf(granted == 13, "and the sweep ran its thirteen states",
		      granted, 13);
	}
	rl_init(&b, RL_KDF_BURST, RL_KDF_RATE_MILLI);
	b.tokens_milli = 0;
	t_okf(rl_retry_s(&b) == 5u, "an empty global login bucket names 5 s",
	      (long)rl_retry_s(&b), 5);
	rl_init(&b, RL_KDF_IP_BURST, RL_KDF_IP_RATE);
	b.tokens_milli = 0;
	t_okf(rl_retry_s(&b) == 11u, "an empty per-address login bucket names"
	      " 11 s -- neither of them can name 2", (long)rl_retry_s(&b), 11);

	/* rl_table_refund(): exactly one token back, never above the burst, and
	 * nothing at all for an address that has no bucket. */
	rl_table_init(&t, 2, RL_KDF_RATE_MILLI);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) +
	      rl_table_take(&t, 0x0a010164u, 0) == 2, "two tokens taken", 2, 2);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) == 0, "and the third refused", 0,
	      0);
	rl_table_refund(&t, 0x0a010164u);
	t_okf(rl_table_take(&t, 0x0a010164u, 0) == 1, "a refund gives one back",
	      1, 1);
	rl_table_refund(&t, 0x0a010164u);
	rl_table_refund(&t, 0x0a010164u);
	rl_table_refund(&t, 0x0a010164u);
	taken = 0;
	for (i = 0; i < 5; i++)
		taken += rl_table_take(&t, 0x0a010164u, 0);
	t_okf(taken == 2, "three refunds cannot push it past the burst", taken, 2);
	rl_table_refund(&t, 0x0aff00ffu);
	taken = 0;
	for (i = 0; i < 5; i++)
		taken += rl_table_take(&t, 0x0aff00ffu, 0);
	t_okf(taken == 2, "a refund for an address with no bucket creates none",
	      taken, 2);

	return t_done(29);
}
