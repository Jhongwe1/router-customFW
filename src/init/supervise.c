/* supervise.c -- R7: see supervise.h for the policy and its four constants. */

#include "supervise.h"

#include <signal.h>
#include <sys/wait.h>

void sv_arm(struct sv_child *c, long now_ms)
{
	if (c == NULL)
		return;
	c->state = SV_WAIT;
	c->pid = 0;
	c->fails = 0;
	c->backoff_ms = 0;
	c->due_ms = now_ms;
	c->started_ms = 0;
	c->exited = 0;
	c->exit_code = 0;
	c->signo = 0;
	c->ran_ms = 0;
}

void sv_on_start(struct sv_child *c, pid_t pid, long now_ms)
{
	if (c == NULL)
		return;
	c->pid = pid;
	c->state = SV_RUNNING;
	c->started_ms = now_ms;
	c->starts++;
}

/* The backoff for the `fails`-th consecutive fast failure: 250 ms doubling to
 * SV_BACKOFF_MAX_MS.  The shift is bounded before it is taken, so this cannot
 * shift a 32-bit value by 32 whatever `fails` reaches. */
static unsigned backoff_for(unsigned fails)
{
	unsigned b = SV_BACKOFF_MS;
	unsigned i;

	if (fails == 0)
		return 0;
	for (i = 1; i < fails; i++) {
		if (b >= (unsigned)SV_BACKOFF_MAX_MS)
			return (unsigned)SV_BACKOFF_MAX_MS;
		b *= 2u;
	}
	return b > (unsigned)SV_BACKOFF_MAX_MS ? (unsigned)SV_BACKOFF_MAX_MS : b;
}

/* The common tail of "this child is not running any more and it failed fast".
 * `sv_on_exit` and `sv_on_spawn_fail` share it so that a fork that fails and a
 * daemon that dies at once cannot get different caps. */
static int count_fast_failure(struct sv_child *c, long now_ms)
{
	if (c->fails < 0xFFFFFFFFu)
		c->fails++;
	if (c->fails >= (unsigned)SV_FAIL_MAX) {
		c->state = SV_GIVENUP;
		c->backoff_ms = 0;
		c->due_ms = 0;
		c->pid = 0;
		return c->state;
	}
	c->backoff_ms = backoff_for(c->fails);
	c->due_ms = now_ms + (long)c->backoff_ms;
	c->state = SV_WAIT;
	c->pid = 0;
	return c->state;
}

int sv_on_exit(struct sv_child *c, int wstatus, long now_ms)
{
	long ran;

	if (c == NULL)
		return SV_OFF;

	c->exited = WIFEXITED(wstatus) ? 1 : 0;
	c->exit_code = WIFEXITED(wstatus) ? WEXITSTATUS(wstatus) : 0;
	c->signo = WIFSIGNALED(wstatus) ? WTERMSIG(wstatus) : 0;

	/* A child told to stop stays stopped. */
	if (c->state == SV_STOPPING) {
		c->state = SV_OFF;
		c->pid = 0;
		return c->state;
	}

	ran = c->started_ms > 0 ? now_ms - c->started_ms : 0;
	if (ran < 0)
		ran = 0;         /* a clock that went backwards is not a credit */
	c->ran_ms = ran;

	if (ran >= SV_RUNOK_MS) {
		/* Healthy: the failure count and the backoff both reset, so a
		 * daemon that has been up for a day and then crashes twice is
		 * not one step from the cap. */
		c->fails = 0;
		c->backoff_ms = 0;
		c->due_ms = now_ms;
		c->state = SV_WAIT;
		c->pid = 0;
		return c->state;
	}
	return count_fast_failure(c, now_ms);
}

int sv_on_spawn_fail(struct sv_child *c, long now_ms)
{
	if (c == NULL)
		return SV_OFF;
	c->exited = 0;
	c->exit_code = 0;
	c->signo = 0;
	c->ran_ms = 0;
	c->started_ms = 0;
	return count_fast_failure(c, now_ms);
}

long sv_next_due(const struct sv_set *s, long now_ms)
{
	long best = -1;
	int i;

	if (s == NULL)
		return -1;
	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++) {
		long d;

		if (s->c[i].state != SV_WAIT)
			continue;
		d = s->c[i].due_ms - now_ms;
		if (d < 0)
			d = 0;
		if (best < 0 || d < best)
			best = d;
	}
	return best;
}

int sv_due(const struct sv_set *s, long now_ms, int *idx, int max)
{
	int i, n = 0;

	if (s == NULL || idx == NULL || max <= 0)
		return 0;
	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++) {
		if (s->c[i].state != SV_WAIT)
			continue;
		if (s->c[i].due_ms > now_ms)
			continue;
		if (n >= max)
			break;
		idx[n++] = i;
	}
	return n;
}

struct sv_child *sv_by_pid(struct sv_set *s, pid_t pid)
{
	int i;

	if (s == NULL || pid <= 0)
		return NULL;
	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++)
		if (s->c[i].pid == pid &&
		    (s->c[i].state == SV_RUNNING || s->c[i].state == SV_STOPPING))
			return &s->c[i];
	return NULL;
}

int sv_start_due(struct sv_set *s, const struct sv_sys *sys, long now_ms)
{
	int idx[SV_MAX_CHILD];
	int n, i, started = 0;

	if (s == NULL || sys == NULL)
		return 0;
	n = sv_due(s, now_ms, idx, SV_MAX_CHILD);
	for (i = 0; i < n; i++) {
		struct sv_child *c = &s->c[idx[i]];
		pid_t pid = sys->spawn(sys->ctx, c);

		if (pid > 0) {
			sv_on_start(c, pid, now_ms);
			sys->log(sys->ctx, c, "started");
			started++;
			continue;
		}
		if (sv_on_spawn_fail(c, now_ms) == SV_GIVENUP)
			sys->log(sys->ctx, c, "GIVEN UP: cannot start");
		else
			sys->log(sys->ctx, c, "start failed");
	}
	return started;
}

int sv_reap_all(struct sv_set *s, const struct sv_sys *sys, long now_ms)
{
	int handled = 0;

	if (s == NULL || sys == NULL)
		return 0;
	for (;;) {
		int wstatus = 0;
		pid_t pid = sys->reap(sys->ctx, &wstatus);
		struct sv_child *c;
		int st;

		if (pid <= 0)
			break;
		handled++;
		c = sv_by_pid(s, pid);
		if (c == NULL)
			continue; /* an orphan the kernel reparented to PID 1:
				   * reaped, and that is the whole job. */
		st = sv_on_exit(c, wstatus, now_ms);
		if (st == SV_GIVENUP)
			sys->log(sys->ctx, c, "GIVEN UP: crash loop");
		else if (st == SV_OFF)
			sys->log(sys->ctx, c, "stopped");
		else
			sys->log(sys->ctx, c, "exited");
	}
	return handled;
}

int sv_shutdown(struct sv_set *s, const struct sv_sys *sys, int how)
{
	long t0, now;
	int i, alive;

	if (s == NULL || sys == NULL)
		return -1;

	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++) {
		if (s->c[i].state != SV_RUNNING)
			continue;
		s->c[i].state = SV_STOPPING;
		sys->send(sys->ctx, s->c[i].pid, SIGTERM);
		sys->log(sys->ctx, &s->c[i], "SIGTERM");
	}

	t0 = sys->now_ms(sys->ctx);
	for (;;) {
		now = sys->now_ms(sys->ctx);
		sv_reap_all(s, sys, now);
		alive = 0;
		for (i = 0; i < s->n && i < SV_MAX_CHILD; i++)
			if (s->c[i].state == SV_STOPPING)
				alive++;
		if (alive == 0)
			break;
		if (now - t0 >= SV_TERM_MS)
			break;
		sys->wait_ms(sys->ctx, SV_TERM_STEP_MS);
	}

	for (i = 0; i < s->n && i < SV_MAX_CHILD; i++) {
		if (s->c[i].state != SV_STOPPING)
			continue;
		sys->send(sys->ctx, s->c[i].pid, SIGKILL);
		sys->log(sys->ctx, &s->c[i], "SIGKILL");
	}
	sv_reap_all(s, sys, sys->now_ms(sys->ctx));

	/* `sync` and then `reboot`, in that order and with nothing between
	 * them.  On this device /var and /run are tmpfs and the config store is
	 * in RAM, so `sync` has nothing of ours to flush -- it is here because
	 * R8 puts the store on an MTD partition and the ordering is the thing
	 * that has to be right before that, not after. */
	sys->do_sync(sys->ctx);
	return sys->do_reboot(sys->ctx, how);
}
