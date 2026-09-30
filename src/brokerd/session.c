/* src/brokerd/session.c -- clock, constant-time compare, entropy gate,
 * randomness, the four sessions and the sixteen rate-limit buckets.
 *
 * ENTROPY IS FAIL-CLOSED, AND THAT IS NOT A HYPOTHETICAL ON THIS BOARD.
 * 量 2026-09-30 on the r6b8i image: /proc/sys/kernel/random/entropy_avail read
 * 0 at 768.26 s of uptime (bench/2026-09-30/SB-ENT.log) and 0 again at
 * 1613.27 s (SB-RT1.log), with poolsize 4096.  So with today's kernel this
 * file's gate NEVER opens and LOGIN/PWSET answer NOENTROPY forever.  That is
 * the correct behaviour of the two available ones: the alternative is to issue
 * 16-byte session tokens out of a pool the kernel says holds no entropy, which
 * is a predictable-token bug shipped to hide a kernel gap.  Feeding the pool is
 * a kernel-side item and is not fixed here.
 *
 * Tokens are never passed to bk_log().  No printf in this file takes one.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "brokerd.h"

void bk_log(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	(void)vfprintf(stderr, fmt, ap);
	va_end(ap);
	(void)fputc('\n', stderr);
}

void bk_init(struct broker *bk)
{
	if (bk == 0)
		return;
	memset(bk, 0, sizeof(*bk));
	bk->cfg_path      = BK_CFG_PATH;
	bk->entropy_path  = BK_ENTROPY_PATH;
	bk->random_path   = BK_RANDOM_PATH;
	bk->uptime_path   = "/proc/uptime";
	bk->loadavg_path  = "/proc/loadavg";
	bk->meminfo_path  = "/proc/meminfo";
	bk->ping_bin      = BK_PING_BIN;
	bk->ping_timeout_s = BK_PING_TIMEOUT;
	bk->use_fake_clock = 0;
	bk->fake_now = 0;
	(void)cfg_defaults(&bk->cfg);
}

long bk_now(const struct broker *bk)
{
	struct timespec ts;

	if (bk != 0 && bk->use_fake_clock)
		return bk->fake_now;
	/* CLOCK_MONOTONIC, so a settimeofday cannot shorten a lock or extend a
	 * session.  It is also why the TTL survives an NTP step. */
	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;
	return (long)ts.tv_sec;
}

long long bk_now_ms(const struct broker *bk)
{
	struct timespec ts;

	if (bk != 0 && bk->use_fake_clock)
		return (long long)bk->fake_now * 1000;
	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;
	return (long long)ts.tv_sec * 1000 + (long long)(ts.tv_nsec / 1000000);
}

int bk_ct_eq(const void *a, const void *b, size_t n)
{
	const volatile unsigned char *p = (const volatile unsigned char *)a;
	const volatile unsigned char *q = (const volatile unsigned char *)b;
	unsigned char d = 0;
	size_t i;

	if (a == 0 || b == 0)
		return 0;
	/* No early exit: every byte is read whatever the first one said, so the
	 * time taken does not depend on how long a common prefix was.  The
	 * volatile qualifiers stop the compiler turning this into memcmp. */
	for (i = 0; i < n; i++)
		d = (unsigned char)(d | (unsigned char)(p[i] ^ q[i]));
	return d == 0;
}

/* ------------------------------------------------------- small file reads */

/* O_CLOEXEC does not exist in uClibc 0.9.30's fcntl.h (the kernel has had the
 * flag since 2.6.23; the header predates it), so every open in brokerd goes
 * through this: open, then set FD_CLOEXEC.  The extra syscall costs nothing and
 * there is no race to lose -- brokerd is single-threaded and the only fork is
 * inside op_ping, which opens nothing. */
static int open_cloexec(const char *path, int flags)
{
	int fd = open(path, flags);

	if (fd >= 0)
		(void)fcntl(fd, F_SETFD, FD_CLOEXEC);
	return fd;
}

/* Read at most cap-1 bytes of a file into buf and NUL-terminate.  Bounded,
 * EINTR-retried, no allocation.  Returns bytes read or -1. */
static int slurp(const char *path, char *buf, size_t cap)
{
	int fd;
	size_t off = 0;

	if (path == 0 || buf == 0 || cap < 2)
		return -1;
	fd = open_cloexec(path, O_RDONLY);
	if (fd < 0)
		return -1;
	while (off + 1 < cap) {
		ssize_t r = read(fd, buf + off, cap - 1 - off);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			(void)close(fd);
			return -1;
		}
		if (r == 0)
			break;
		off += (size_t)r;
	}
	buf[off] = '\0';
	(void)close(fd);
	return (int)off;
}

/* Decimal at the head of s, saturating.  No strtoul: this must not accept a
 * sign, a prefix or whitespace-then-digits from a /proc file we are treating
 * as data. */
static uint32_t dec_head(const char *s, const char **end)
{
	uint32_t v = 0;
	int any = 0;

	while (*s >= '0' && *s <= '9') {
		uint32_t d = (uint32_t)(*s - '0');

		any = 1;
		if (v > (0xFFFFFFFFu - d) / 10u)
			v = 0xFFFFFFFFu;
		else
			v = v * 10u + d;
		s++;
	}
	if (end != 0)
		*end = s;
	return any ? v : 0;
}

/* ------------------------------------------------------------- entropy */

int bk_entropy_ready(struct broker *bk)
{
	char buf[32];

	if (bk == 0)
		return 0;
	if (bk->auth_ready)
		return 1;                   /* sticky, per SPEC § 6 */
	if (slurp(bk->entropy_path, buf, sizeof(buf)) < 0) {
		/* Cannot read the file -> not ready.  Fail closed: an unreadable
		 * /proc is not permission to hand out tokens. */
		bk->entropy_last = 0;
		return 0;
	}
	bk->entropy_last = dec_head(buf, 0);
	if (bk->entropy_last >= BK_ENTROPY_MIN)
		bk->auth_ready = 1;
	return bk->auth_ready;
}

int bk_random(struct broker *bk, uint8_t *p, size_t n)
{
	int fd;
	size_t off = 0;
	const char *path = (bk != 0 && bk->random_path != 0)
	                 ? bk->random_path : BK_RANDOM_PATH;

	if (p == 0 || n == 0)
		return -1;
	/* getrandom(2) does not exist in 2.6.30 and its wrapper is not in
	 * uClibc 0.9.30 either, so /dev/urandom is the source.  The entropy
	 * gate above is what makes reading it defensible. */
	fd = open_cloexec(path, O_RDONLY);
	if (fd < 0)
		return -1;
	while (off < n) {
		ssize_t r = read(fd, p + off, n - off);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			(void)close(fd);
			return -1;
		}
		if (r == 0) {               /* short read: refuse, do not pad */
			(void)close(fd);
			return -1;
		}
		off += (size_t)r;
	}
	(void)close(fd);
	return 0;
}

/* ------------------------------------------------------------ sessions */

void bk_sess_expire(struct broker *bk)
{
	long now;
	int i;

	if (bk == 0)
		return;
	now = bk_now(bk);
	for (i = 0; i < BK_NSESS; i++) {
		if (!bk->sess[i].used)
			continue;
		/* Idle TTL: valid while (now - last) < TTL, expired at >= TTL.
		 * The boundary is pinned by test_session.c: 899 valid, 900 not. */
		if (now - bk->sess[i].last >= BK_SESS_TTL)
			bk_sess_drop(&bk->sess[i]);
	}
}

struct bk_sess *bk_sess_find(struct broker *bk, const uint8_t tok[PROTO_TOK_LEN])
{
	struct bk_sess *hit = 0;
	int i;

	if (bk == 0 || tok == 0)
		return 0;
	bk_sess_expire(bk);
	/* Every slot is compared, with no early return, so the loop's duration
	 * does not say which slot matched or how far a near-miss got. */
	for (i = 0; i < BK_NSESS; i++) {
		if (!bk->sess[i].used)
			continue;
		if (bk_ct_eq(bk->sess[i].tok, tok, PROTO_TOK_LEN))
			hit = &bk->sess[i];
	}
	return hit;
}

struct bk_sess *bk_sess_new(struct broker *bk)
{
	struct bk_sess *slot = 0;
	int i;

	if (bk == 0)
		return 0;
	bk_sess_expire(bk);
	for (i = 0; i < BK_NSESS; i++) {
		if (!bk->sess[i].used) {
			slot = &bk->sess[i];
			break;
		}
	}
	if (slot == 0) {
		/* LRU: the smallest ->last, and the smallest ->born breaks a tie
		 * (two sessions used in the same second). */
		slot = &bk->sess[0];
		for (i = 1; i < BK_NSESS; i++) {
			if (bk->sess[i].last < slot->last ||
			    (bk->sess[i].last == slot->last &&
			     bk->sess[i].born < slot->born))
				slot = &bk->sess[i];
		}
	}
	if (bk_random(bk, slot->tok, PROTO_TOK_LEN) != 0)
		return 0;
	if (bk_random(bk, slot->csrf, PROTO_TOK_LEN) != 0) {
		/* Do not leave a session whose CSRF token is zeroes. */
		bk_sess_drop(slot);
		return 0;
	}
	slot->used = 1;
	slot->last = bk_now(bk);
	slot->born = ++bk->sess_seq;
	return slot;
}

void bk_sess_drop(struct bk_sess *s)
{
	if (s == 0)
		return;
	/* Wipe rather than clear a flag: the bytes are secrets and this object
	 * is reused. */
	memset(s, 0, sizeof(*s));
}

void bk_sess_drop_all(struct broker *bk)
{
	int i;

	if (bk == 0)
		return;
	for (i = 0; i < BK_NSESS; i++)
		bk_sess_drop(&bk->sess[i]);
}

int bk_sess_count(const struct broker *bk)
{
	int i, n = 0;

	if (bk == 0)
		return 0;
	for (i = 0; i < BK_NSESS; i++)
		if (bk->sess[i].used)
			n++;
	return n;
}

/* ---------------------------------------------------------- rate limit */

struct bk_rl *bk_rl_peek(struct broker *bk, uint32_t ip)
{
	int i;

	if (bk == 0)
		return 0;
	for (i = 0; i < BK_NRL; i++)
		if (bk->rl[i].used && bk->rl[i].ip == ip)
			return &bk->rl[i];
	return 0;
}

/* Find or make the bucket for ip.
 *
 * EVICTION IS WHERE A NAIVE TABLE LEAKS.  A 16-entry table with "evict the
 * oldest" lets an attacker who is locked out clear their own lock by
 * connecting from sixteen other addresses.  So: a LOCKED bucket is never
 * evicted.  Free slots first, then an unlocked bucket (the one seen longest
 * ago).  If all sixteen are locked, this returns 0 and bk_rl_check answers
 * LOCKED with the shortest remaining lock -- fail closed, at the cost of
 * refusing logins from new addresses while the table is saturated. */
static struct bk_rl *rl_slot(struct broker *bk, uint32_t ip)
{
	struct bk_rl *victim = 0;
	long now = bk_now(bk);
	int i;

	for (i = 0; i < BK_NRL; i++)
		if (bk->rl[i].used && bk->rl[i].ip == ip)
			return &bk->rl[i];
	for (i = 0; i < BK_NRL; i++)
		if (!bk->rl[i].used) {
			memset(&bk->rl[i], 0, sizeof(bk->rl[i]));
			bk->rl[i].used = 1;
			bk->rl[i].ip = ip;
			bk->rl[i].seen = now;
			return &bk->rl[i];
		}
	for (i = 0; i < BK_NRL; i++) {
		if (bk->rl[i].lock_until > now)
			continue;                      /* locked: untouchable */
		if (victim == 0 || bk->rl[i].seen < victim->seen)
			victim = &bk->rl[i];
	}
	if (victim == 0)
		return 0;
	memset(victim, 0, sizeof(*victim));
	victim->used = 1;
	victim->ip = ip;
	victim->seen = now;
	return victim;
}

int bk_rl_check(struct broker *bk, uint32_t ip, uint32_t *secs)
{
	struct bk_rl *e;
	long now;

	if (secs != 0)
		*secs = 0;
	if (bk == 0)
		return 1;
	now = bk_now(bk);
	e = rl_slot(bk, ip);
	if (e == 0) {
		/* Table saturated with locks.  Report the shortest wait so the
		 * answer is still actionable. */
		long best = -1;
		int i;

		for (i = 0; i < BK_NRL; i++) {
			long left = bk->rl[i].lock_until - now;

			if (left > 0 && (best < 0 || left < best))
				best = left;
		}
		if (secs != 0)
			*secs = (uint32_t)(best > 0 ? best : 1);
		return 1;
	}
	e->seen = now;
	if (e->lock_until > now) {
		if (secs != 0)
			*secs = (uint32_t)(e->lock_until - now);
		return 1;
	}
	if (e->lock_until != 0) {
		/* The lock just expired.  The failure count resets so the next
		 * five attempts are the ones that re-lock; ->lock_s is kept, so
		 * the doubling does not restart at 60 s. */
		e->lock_until = 0;
		e->fails = 0;
	}
	return 0;
}

void bk_rl_fail(struct broker *bk, uint32_t ip)
{
	struct bk_rl *e;

	if (bk == 0)
		return;
	e = rl_slot(bk, ip);
	if (e == 0)
		return;
	e->seen = bk_now(bk);
	if (e->fails < 255)
		e->fails++;
	if (e->fails < BK_RL_FAILS)
		return;
	if (e->lock_s == 0)
		e->lock_s = BK_RL_LOCK0;
	else if (e->lock_s < BK_RL_LOCKCAP) {
		uint32_t n = e->lock_s * 2u;

		e->lock_s = (n > BK_RL_LOCKCAP || n < e->lock_s)
		          ? BK_RL_LOCKCAP : n;
	}
	e->lock_until = bk_now(bk) + (long)e->lock_s;
	e->fails = 0;                    /* the next five re-lock, longer */
	bk_log("brokerd: login locked for %u s", (unsigned)e->lock_s);
}

void bk_rl_ok(struct broker *bk, uint32_t ip)
{
	struct bk_rl *e;

	if (bk == 0)
		return;
	e = rl_slot(bk, ip);
	if (e == 0)
		return;
	/* A success clears the consecutive count and the escalation.  It cannot
	 * clear a lock: bk_rl_check runs first, so a locked IP never reaches a
	 * KDF and never reaches here. */
	e->fails = 0;
	e->lock_s = 0;
	e->lock_until = 0;
	e->seen = bk_now(bk);
}

/* /proc readers used by STATUS.  Kept here because they share slurp(). */

uint32_t bk_proc_uptime(struct broker *bk)
{
	char buf[64];

	if (bk == 0 || slurp(bk->uptime_path, buf, sizeof(buf)) < 0)
		return 0;
	return dec_head(buf, 0);                /* whole seconds, first field */
}

uint32_t bk_proc_load1x100(struct broker *bk)
{
	char buf[128];
	const char *p = buf;
	uint32_t whole, frac = 0, scale = 1;

	if (bk == 0 || slurp(bk->loadavg_path, buf, sizeof(buf)) < 0)
		return 0;
	whole = dec_head(p, &p);
	if (*p == '.') {
		const char *q = p + 1;

		frac = dec_head(q, &q);
		while (q > p + 1) { scale *= 10u; q--; }
	}
	if (whole > 42000000u)
		return 0xFFFFFFFFu;
	return whole * 100u + (scale != 0 ? (frac * 100u) / scale : 0);
}

uint32_t bk_proc_memfree_kb(struct broker *bk)
{
	char buf[1024];
	const char *p;

	if (bk == 0 || slurp(bk->meminfo_path, buf, sizeof(buf)) < 0)
		return 0;
	p = strstr(buf, "MemFree:");
	if (p == 0)
		return 0;
	p += 8;
	while (*p == ' ' || *p == '\t')
		p++;
	return dec_head(p, 0);
}
