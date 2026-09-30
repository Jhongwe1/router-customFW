/* src/httpd/rl.h -- token buckets, and the reason they live in the PARENT.
 *
 * plan D8 v6 ruling 2: "the rate limiter runs BEFORE the KDF, and it blocks on
 * the httpd side, so the request never reaches brokerd".  Ruling 1 makes the
 * parameter choice a budget: concurrent KDF evaluations x memory per evaluation
 * must stay under a cap written down first.  Neither is satisfiable by a limiter
 * that lives in the connection handler, because httpd forks per connection and
 * the design has no shared memory on purpose (D7: MIPS-I has no atomic
 * read-modify-write, so the architecture is processes, not threads, and then
 * there is nothing to lock).
 *
 * So the buckets live in the parent, which is the only process that sees every
 * connection, and a child that is about to spend a KDF evaluation ASKS for it
 * over the socketpair it was forked with.  One writer, no locks, no shared page,
 * and the answer arrives before the request is forwarded.  A child that is
 * refused answers 429 itself.
 *
 * Time is milliseconds from CLOCK_MONOTONIC.  The arithmetic is in milli-tokens
 * so a refill slower than one token per second is expressible: the login bucket
 * refills one token per four seconds, which is 250 milli-tokens per second.
 *
 * WHAT THIS DOES NOT ESTABLISH.  Nothing here bounds an attacker who can spend
 * eight concurrent connections on slow header writes; that is what the 5 s header
 * timeout and HTTP_CONN_MAX are for.  And a per-IP bucket is not a bound on a
 * LAN attacker who rotates source addresses -- on a LAN they own their stack --
 * which is why the GLOBAL login bucket exists and is the one the budget is
 * computed from.  The per-IP bucket only keeps one honest client from locking the
 * global one by accident.
 */
#ifndef RLXFW_HTTPD_RL_H
#define RLXFW_HTTPD_RL_H

#include <stdint.h>

struct rl_bucket {
	uint32_t cap_milli;     /* burst, in milli-tokens */
	uint32_t rate_milli;    /* refill, milli-tokens per second */
	uint32_t tokens_milli;
	uint32_t last_ms;
	uint8_t  started;
};

void rl_init(struct rl_bucket *b, uint32_t burst, uint32_t milli_per_s);
/* 1 = one token taken, 0 = refused.  Never blocks. */
int  rl_take(struct rl_bucket *b, uint32_t now_ms);
/* Seconds until one token exists.  0 when a token is available now; at least 1
 * when it is not, so a Retry-After never says "retry immediately". */
uint32_t rl_retry_s(const struct rl_bucket *b);

#define RL_IPS 16

struct rl_table {
	uint32_t burst;
	uint32_t rate_milli;
	struct {
		uint32_t ip;
		uint32_t last_ms;
		uint8_t  used;
		struct rl_bucket b;
	} e[RL_IPS];
};

void rl_table_init(struct rl_table *t, uint32_t burst, uint32_t milli_per_s);
/* 1 = taken, 0 = refused.  A full table evicts the least recently used entry,
 * which is the only behaviour available with a fixed table: it means an attacker
 * who cycles more than RL_IPS addresses resets his own per-IP bucket, and the
 * global bucket is what actually holds. */
int  rl_table_take(struct rl_table *t, uint32_t ip, uint32_t now_ms);
uint32_t rl_table_retry_s(struct rl_table *t, uint32_t ip);
/* Put one token back into `ip`'s bucket, never above the burst, and do nothing
 * at all for an address that has no bucket.  It exists for one caller: a taker
 * that has to consult TWO buckets and finds the second one refusing, which
 * would otherwise charge one refusal to both.  It is not a general credit. */
void rl_table_refund(struct rl_table *t, uint32_t ip);

/* ------ the numbers, and every one of them is in notes/httpd.md's budget ---- */

/* Connections: enough for a page load (index.html, style.css, app.js and a
 * couple of /api/status polls) several times over. */
#define RL_CONN_BURST        32
#define RL_CONN_RATE_MILLI 16000   /* 16 connections per second */
#define RL_CONN_IP_BURST     16
#define RL_CONN_IP_RATE    8000

/* Logins, and these are the budget's numbers: 3 immediate, then one every 4 s
 * globally.  With one evaluation in flight at a time and a per-evaluation figure
 * of ~0.6 s (推, notes/httpd.md), the sustained share of brokerd an attacker can
 * occupy with KDF work is 0.25 x 0.6 = 15 %. */
#define RL_KDF_BURST         3
#define RL_KDF_RATE_MILLI  250     /* one token per 4 s */
#define RL_KDF_IP_BURST      3
#define RL_KDF_IP_RATE     100     /* one token per 10 s, per address */

#endif /* RLXFW_HTTPD_RL_H */
