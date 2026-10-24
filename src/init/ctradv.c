/* ctradv.c -- see ctradv.h.  notes/self-update.md § 5 is the design; the
 * verb's own order (§ 2.4.2) is the kernel's.
 *
 * ---------------------------------------------------------------------------
 * THE ORDER, AND WHY EACH STEP IS WHERE IT IS
 * ---------------------------------------------------------------------------
 *
 *   1  "up" first: brokerd answers a STATUS as root.  Not up in 60 s ->
 *      nothing is written and the older slot stays bootable, the availability
 *      half of P6r-11's "only after up".
 *   2  /proc/rlxfw-boot, one read.  `none` -> nothing is written: the kernel's
 *      handoff tie (§ 2.4.5) would refuse anyway, and a refused verb is still
 *      an attempt in /proc and a line on the console.  Anything that is not
 *      `slot X ver N` -> nothing is written either.
 *   3  the flash lock, because `ctr` ends disarmed like every write verb
 *      (rtl819x-spi.c, rtl819x_spi_verb_inst) and must not land inside
 *      another writer's arm -> install pair (§ 3.2 step 1).
 *   4  ctr_attempts, ctr_done, ctr_refused and ctr_failed read from
 *      /proc/rtl819x-spi-inst BEFORE the verb.  The fields read after it are
 *      this verb's only if ctr_attempts moved by exactly one, and the class is
 *      whichever of the other three moved: a reason name alone cannot tell a
 *      refused ENGINE (the bitmap's first read) from a failed one.
 *   5  ONE spictl_verb(): one write(2), never retried.  Its return is the
 *      kernel's errno and is printed; the decision is read from the node.
 *   6  the fields after it, read while the lock is still held; the release;
 *      one console line.
 *
 * Every path prints exactly one line beginning "rlxfw: ctr ".  A card gates on
 * /proc/rtl819x-spi-inst (SPEC.md FW-47), never on this line.
 *
 * WHAT THIS DOES NOT DO.  It does not check the version against the bitmap,
 * the range or the tie: the kernel does all three and names the one that
 * refused.  It does not retry.  It cannot keep out a writer that types verbs
 * without the flash lock (a bench shell's `echo ctr 6 >`); the ctr_attempts
 * check is what makes such an interleaving read as UNKNOWN instead of as this
 * verb's result.  The fields are read one spictl_field() call each, so each is
 * its own read of the node; under the lock only a writer that ignores it can
 * change them between two reads.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "client.h"
#include "ctradv.h"

/* Tries of STATUS at most: 1 + 60,000 / 500.  A second bound beside the clock,
 * so a clock that does not move cannot make the wait endless. */
#define CTR_UP_TRIES	(1L + CTR_UP_BUDGET_MS / CTR_UP_STEP_MS)

#define CTR_BOOT_UNREAD	(-2)	/* ctr_read_boot only: open or read failed */

/* ------------------------------------------------------------------------- */
/* /proc/rlxfw-boot                                                          */
/* ------------------------------------------------------------------------- */

int ctr_parse_boot(const char *b, size_t n, char *slot, uint32_t *ver)
{
	uint32_t v = 0u;
	size_t i;

	if (b == NULL || slot == NULL || ver == NULL)
		return CTR_BOOT_BAD;
	if (n == 5u && memcmp(b, "none\n", 5u) == 0)
		return CTR_BOOT_NONE;
	/* "slot " X " ver " then 1..10 digits then '\n': 13..22 bytes, the
	 * node's own `slot %c ver %u\n` and nothing else. */
	if (n < 13u || n > 22u)
		return CTR_BOOT_BAD;
	if (memcmp(b, "slot ", 5u) != 0 || (b[5] != 'A' && b[5] != 'B') ||
	    memcmp(b + 6, " ver ", 5u) != 0 || b[n - 1u] != '\n' ||
	    b[11] == '0')
		return CTR_BOOT_BAD;
	for (i = 11u; i < n - 1u; i++) {
		uint32_t d;

		if (b[i] < '0' || b[i] > '9')
			return CTR_BOOT_BAD;
		d = (uint32_t)(b[i] - '0');
		if (v > (0xFFFFFFFFu - d) / 10u)
			return CTR_BOOT_BAD;
		v = v * 10u + d;
	}
	if (v == 0xFFFFFFFFu)
		return CTR_BOOT_BAD;	/* the handoff's versions end at 0xFFFFFFFE */
	*slot = b[5];
	*ver = v;
	return CTR_BOOT_SLOT;
}

/* One read: the node is at most 22 bytes and renders the whole text from
 * offset 0 (rlxfw-boot.c), so a 64-byte buffer either holds all of it or holds
 * something that is not the node -- and that fails the parse. */
static int ctr_read_boot(const char *path, char *slot, uint32_t *ver, int *err)
{
	char buf[64];
	ssize_t n;
	int fd;

	*err = 0;
	if (path == NULL) {
		*err = EINVAL;
		return CTR_BOOT_UNREAD;
	}
	fd = open(path, O_RDONLY);
	if (fd < 0) {
		*err = errno;
		return CTR_BOOT_UNREAD;
	}
	do
		n = read(fd, buf, sizeof buf);
	while (n < 0 && errno == EINTR);
	if (n < 0)
		*err = errno;
	(void)close(fd);
	if (n < 0)
		return CTR_BOOT_UNREAD;
	return ctr_parse_boot(buf, (size_t)n, slot, ver);
}

/* ------------------------------------------------------------------------- */
/* Up                                                                        */
/* ------------------------------------------------------------------------- */

int ctr_wait_up(const struct ctr_env *e)
{
	long t0 = e->now_ms(e->ctx);
	long k;

	for (k = 1;; k++) {
		if (e->broker_up(e->ctx) == 1)
			return 1;
		if (e->now_ms(e->ctx) - t0 >= CTR_UP_BUDGET_MS ||
		    k >= CTR_UP_TRIES)
			return 0;
		e->sleep_ms(e->ctx, CTR_UP_STEP_MS);
	}
}

int ctr_broker_status(const char *sock)
{
	struct bk_req rq;
	struct bk_resp rs;

	memset(&rq, 0, sizeof rq);
	rq.op = OP_STATUS;	/* no body; all-zero tokens, so no session */
	bk_set_timeouts(CTR_BK_CONNECT_S, CTR_BK_IO_S);
	if (bk_call(sock, &rq, &rs) != 0)
		return 0;
	return rs.status == ST_OK ? 1 : 0;
}

/* ------------------------------------------------------------------------- */
/* The node                                                                  */
/* ------------------------------------------------------------------------- */

/* The four counters rtl819x_spi_ctr_run() moves, by the names
 * rlxfw_spi_inst_emit_ctr() prints (rtl819x-spi-install.h 1.2). */
struct ctr_count {
	uint32_t attempts, done, refused, failed;
};

/* The last attempt's verdict, by the same names. */
struct ctr_verdict {
	char reason[CTR_REASON_MAX];
	uint32_t cur, newv, read, pp;
};

static int ctr_counts(const struct spictl_paths *sp, struct ctr_count *c)
{
	int rc;

	rc = spictl_field_u32(sp, "ctr_attempts", &c->attempts);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_done", &c->done);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_refused", &c->refused);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_failed", &c->failed);
	return rc;
}

static int ctr_fields(const struct spictl_paths *sp, struct ctr_verdict *v)
{
	int rc;

	rc = spictl_field(sp, "ctr_reason", v->reason, sizeof v->reason);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_cur", &v->cur);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_new", &v->newv);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_read", &v->read);
	if (rc == 0)
		rc = spictl_field_u32(sp, "ctr_pp", &v->pp);
	return rc;
}

/* A reason as the install header spells them: [A-Z0-9_]+.  Nothing else from
 * the node reaches the console. */
static int ctr_reason_ok(const char *s)
{
	size_t i;

	for (i = 0; s[i] != '\0'; i++)
		if (!((s[i] >= 'A' && s[i] <= 'Z') ||
		      (s[i] >= '0' && s[i] <= '9') || s[i] == '_'))
			return 0;
	return i > 0u;
}

/* ------------------------------------------------------------------------- */
/* The helper                                                                */
/* ------------------------------------------------------------------------- */

static int ctr_judge(const struct ctr_env *e, int rc, int wrc, uint32_t ver,
		     const struct ctr_count *a, const struct ctr_count *b,
		     const struct ctr_verdict *v)
{
	char line[CTR_LINE_MAX];
	uint32_t dn = b->attempts - a->attempts;
	uint32_t dd = b->done - a->done;
	uint32_t dr = b->refused - a->refused;
	uint32_t df = b->failed - a->failed;
	int res;

	if (rc != 0) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr verdict unknown: "
			       "/proc/rtl819x-spi-inst unreadable after the "
			       "verb (%d; write %d)", rc, wrc);
		res = CTR_R_UNKNOWN;
	} else if (dn == 0u) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: the "
			       "verb did not reach the counter (ctr_attempts "
			       "unchanged; write %d)", wrc);
		res = CTR_R_UNRAN;
	} else if (dn != 1u || dd + dr + df != 1u || !ctr_reason_ok(v->reason)) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr verdict unknown: "
			       "ctr_attempts +%lu done +%lu refused +%lu "
			       "failed +%lu", (unsigned long)dn,
			       (unsigned long)dd, (unsigned long)dr,
			       (unsigned long)df);
		res = CTR_R_UNKNOWN;
	} else if (dd == 1u && wrc == 0 && strcmp(v->reason, "OK") == 0 &&
		   v->newv == ver && v->read == ver) {
		if (v->pp == 0u) {
			(void)snprintf(line, sizeof line,
				       "rlxfw: ctr %lu -> %lu SAME pp=0",
				       (unsigned long)v->cur,
				       (unsigned long)v->newv);
			res = CTR_R_SAME;
		} else {
			(void)snprintf(line, sizeof line,
				       "rlxfw: ctr %lu -> %lu OK pp=%lu",
				       (unsigned long)v->cur,
				       (unsigned long)v->newv,
				       (unsigned long)v->pp);
			res = CTR_R_OK;
		}
	} else if (dr == 1u && wrc < 0) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: %s "
			       "ver=%lu cur=%lu new=%lu errno=%d", v->reason,
			       (unsigned long)ver, (unsigned long)v->cur,
			       (unsigned long)v->newv, -wrc);
		res = CTR_R_REFUSED;
	} else if (df == 1u && wrc < 0) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr FAILED: %s ver=%lu "
			       "cur=%lu new=%lu read=%lu pp=%lu errno=%d",
			       v->reason, (unsigned long)ver,
			       (unsigned long)v->cur, (unsigned long)v->newv,
			       (unsigned long)v->read, (unsigned long)v->pp,
			       -wrc);
		res = CTR_R_FAILED;
	} else {
		(void)snprintf(line, sizeof line, "rlxfw: ctr verdict unknown: "
			       "%s done +%lu refused +%lu failed +%lu new=%lu "
			       "read=%lu write %d", v->reason, (unsigned long)dd,
			       (unsigned long)dr, (unsigned long)df,
			       (unsigned long)v->newv, (unsigned long)v->read,
			       wrc);
		res = CTR_R_UNKNOWN;
	}
	e->say(e->ctx, line);
	return res;
}

int ctr_advance(const struct ctr_env *e)
{
	struct ctr_count a, b;
	struct ctr_verdict v;
	char line[CTR_LINE_MAX], verb[24], slot = '?';
	uint32_t ver = 0u;
	int h, err = 0, lk, rc, wrc;

	if (e == NULL || e->sp == NULL || e->broker_up == NULL ||
	    e->now_ms == NULL || e->sleep_ms == NULL || e->say == NULL)
		return CTR_R_UNKNOWN;

	/* 1: up */
	if (!ctr_wait_up(e)) {
		e->say(e->ctx, "rlxfw: ctr not advanced: brokerd did not answer "
			       "STATUS in 60 s");
		return CTR_R_NOBROKER;
	}

	/* 2: the handoff */
	h = ctr_read_boot(e->boot_path, &slot, &ver, &err);
	if (h == CTR_BOOT_NONE) {
		e->say(e->ctx, "rlxfw: ctr not advanced: no handoff (not started "
			       "by rlxboot)");
		return CTR_R_NOHANDOFF;
	}
	if (h != CTR_BOOT_SLOT) {
		if (h == CTR_BOOT_UNREAD)
			(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: "
				       "/proc/rlxfw-boot unreadable (errno=%d)",
				       err);
		else
			(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: "
				       "/proc/rlxfw-boot is neither `none` nor "
				       "`slot X ver N`");
		e->say(e->ctx, line);
		return CTR_R_BOOTREAD;
	}

	/* 3: the flash lock */
	lk = spictl_lock(e->sp, e->lock_s);
	if (lk < 0) {
		(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: %s",
			       spictl_lock_why(lk));
		e->say(e->ctx, line);
		return CTR_R_LOCK;
	}

	/* 4: the counters before */
	rc = ctr_counts(e->sp, &a);
	if (rc != 0) {
		spictl_unlock(lk);
		(void)snprintf(line, sizeof line, "rlxfw: ctr not advanced: "
			       "/proc/rtl819x-spi-inst unreadable before the "
			       "verb (%d)", rc);
		e->say(e->ctx, line);
		return CTR_R_STATE;
	}

	/* 5: ONE verb.  The version as rlxboot handed it over, decimal; the
	 * kernel's parser takes 1..4 digits and refuses the rest itself. */
	(void)snprintf(verb, sizeof verb, "ctr %lu", (unsigned long)ver);
	wrc = spictl_verb(e->sp, verb);

	/* 6: the verdict, under the lock; then the release */
	memset(&v, 0, sizeof v);
	rc = ctr_counts(e->sp, &b);
	if (rc == 0)
		rc = ctr_fields(e->sp, &v);
	spictl_unlock(lk);
	return ctr_judge(e, rc, wrc, ver, &a, &b, &v);
}

/* ------------------------------------------------------------------------- */
/* When PID 1 forks it                                                       */
/* ------------------------------------------------------------------------- */

int ctr_fork_due(const struct sv_set *s, int lan_said_up)
{
	int i;

	if (!lan_said_up)
		return CTR_FORK_NOLAN;
	if (s == NULL)
		return CTR_FORK_NOBROKER;
	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++) {
		const struct sv_child *c = &s->c[i];

		if (strcmp(c->name, "brokerd") != 0)
			continue;
		/* Neither ever starts: SV_OFF is a config "no", SV_ABSENT a
		 * binary the image does not carry (main.c add_child). */
		if (c->state == SV_OFF || c->state == SV_ABSENT)
			return CTR_FORK_NOBROKER;
		return c->starts > 0u ? 1 : 0;
	}
	return CTR_FORK_NOBROKER;
}

const char *ctr_fork_why(int due)
{
	if (due == CTR_FORK_NOLAN)
		return "rlxfw: ctr not advanced: no `lan up` on this boot";
	if (due == CTR_FORK_NOBROKER)
		return "rlxfw: ctr not advanced: no brokerd in the child table";
	return "";
}

/* ------------------------------------------------------------------------- */
/* The device's environment                                                  */
/* ------------------------------------------------------------------------- */

static int ctr_dev_up(void *ctx)
{
	(void)ctx;
	return ctr_broker_status(CTR_BROKER_SOCK);
}

static long ctr_dev_now(void *ctx)
{
	struct timespec ts;

	(void)ctx;
	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;	/* CTR_UP_TRIES still ends the wait */
	return (long)ts.tv_sec * 1000L + (long)(ts.tv_nsec / 1000000L);
}

static void ctr_dev_sleep(void *ctx, long ms)
{
	struct timespec ts, rem;

	(void)ctx;
	if (ms <= 0)
		return;
	ts.tv_sec = (time_t)(ms / 1000L);
	ts.tv_nsec = (ms % 1000L) * 1000000L;
	while (nanosleep(&ts, &rem) != 0 && errno == EINTR)
		ts = rem;
}

/* The line and its '\n' in ONE write(2), so a daemon's own line cannot land
 * between them. */
static void ctr_dev_say(void *ctx, const char *s)
{
	char b[CTR_LINE_MAX + 1];
	size_t n = strlen(s);
	ssize_t w;

	(void)ctx;
	if (n > (size_t)CTR_LINE_MAX - 1u)
		n = (size_t)CTR_LINE_MAX - 1u;
	memcpy(b, s, n);
	b[n++] = '\n';
	w = write(1, b, n);
	(void)w;	/* a console that cannot be written is not a reason to stop */
}

void ctr_env_dev(struct ctr_env *e)
{
	memset(e, 0, sizeof *e);
	e->sp = &spictl_dev;
	e->boot_path = CTR_BOOT_PATH;
	e->broker_up = ctr_dev_up;
	e->now_ms = ctr_dev_now;
	e->sleep_ms = ctr_dev_sleep;
	e->say = ctr_dev_say;
	e->ctx = NULL;
	e->lock_s = CTR_LOCK_S;
}
