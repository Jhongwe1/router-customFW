/* test_supervise.c -- R7 host test for PID 1's respawn state machine.
 *
 * Nothing here forks.  `sv_on_exit`, `sv_due` and `sv_next_due` are pure
 * functions of (child, wstatus, now_ms), so a crash loop of eight failures runs
 * in microseconds and the exact backoff sequence can be asserted rather than
 * waited for.  The `sv_shutdown` case drives an injected syscall layer that
 * records an ORDERED event log, which is how "sync before reboot" becomes a
 * test instead of a comment.
 *
 * T-CAP-TERMINATES is the mutation target: M1 in notes/init.md 6 removes the
 * crash-loop cap, and that case is written as a BOUNDED loop so the mutant
 * FAILS in finite time instead of hanging a suite.  A hang is not a test result.
 */

#include "supervise.h"

#include <signal.h>
#include <stdio.h>
#include <string.h>

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

#define CKN(name, cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL [%s] %s:%d  %s\n", name, __FILE__, __LINE__, #cond); \
	} \
} while (0)

/* Linux wait status encodings, built here rather than borrowed, so the test
 * does not depend on a <sys/wait.h> macro to CONSTRUCT what it then asks the
 * same header to decode. */
static int st_exit(int code)
{
	return (code & 0xFF) << 8;
}

static int st_signal(int sig)
{
	return sig & 0x7F;
}

/* ------------------------------------------------------- an injected system */

#define EV_MAX 64

struct sysfake {
	long now;
	int n_ev;
	char ev[EV_MAX][48];
	/* a queue of exits for `reap` */
	pid_t q_pid[EV_MAX];
	int q_st[EV_MAX];
	int q_head, q_tail;
	/* pids that ignore SIGTERM until `stubborn_until` */
	pid_t stubborn;
	long stubborn_until;
	pid_t next_pid;
	int spawn_fail;
};

static void ev(struct sysfake *f, const char *a, const char *b, long v)
{
	char *p;
	size_t n = 0;

	if (f->n_ev >= EV_MAX)
		return;
	p = f->ev[f->n_ev++];
	while (*a != '\0' && n < 40)
		p[n++] = *a++;
	if (b != NULL) {
		p[n++] = ' ';
		while (*b != '\0' && n < 44)
			p[n++] = *b++;
	}
	if (v >= 0) {
		p[n++] = ' ';
		if (v >= 10)
			p[n++] = (char)('0' + (int)((v / 10) % 10));
		p[n++] = (char)('0' + (int)(v % 10));
	}
	p[n] = '\0';
}

static pid_t f_spawn(void *ctx, const struct sv_child *c)
{
	struct sysfake *f = (struct sysfake *)ctx;

	if (f->spawn_fail) {
		ev(f, "spawnfail", c->name, -1);
		return -1;
	}
	ev(f, "spawn", c->name, -1);
	return f->next_pid++;
}

static int f_send(void *ctx, pid_t pid, int sig)
{
	struct sysfake *f = (struct sysfake *)ctx;

	ev(f, sig == SIGTERM ? "TERM" : (sig == SIGKILL ? "KILL" : "SIG"),
	   NULL, (long)pid);
	/* A stubborn child does not die on SIGTERM; it dies on SIGKILL. */
	if (sig == SIGKILL || pid != f->stubborn) {
		if (f->q_tail < EV_MAX) {
			f->q_pid[f->q_tail] = pid;
			f->q_st[f->q_tail] = st_signal(sig);
			f->q_tail++;
		}
	}
	return 0;
}

static pid_t f_reap(void *ctx, int *wstatus)
{
	struct sysfake *f = (struct sysfake *)ctx;

	if (f->q_head >= f->q_tail)
		return 0;
	*wstatus = f->q_st[f->q_head];
	return f->q_pid[f->q_head++];
}

static long f_now(void *ctx)
{
	return ((struct sysfake *)ctx)->now;
}

static void f_wait(void *ctx, long ms)
{
	struct sysfake *f = (struct sysfake *)ctx;

	f->now += ms;
	/* Past its deadline the stubborn child gives in, which is what lets the
	 * SIGKILL branch and the "it died in time" branch both be exercised. */
	if (f->stubborn > 0 && f->now >= f->stubborn_until)
		f->stubborn = -1;
}

static void f_sync(void *ctx)
{
	ev((struct sysfake *)ctx, "sync", NULL, -1);
}

static int f_reboot(void *ctx, int how)
{
	ev((struct sysfake *)ctx, "reboot", NULL, (long)how);
	return 0;
}

static void f_log(void *ctx, const struct sv_child *c, const char *what)
{
	(void)c;
	(void)what;
	(void)ctx;
}

static void sysfake_init(struct sysfake *f, struct sv_sys *s)
{
	memset(f, 0, sizeof(*f));
	f->next_pid = 100;
	f->stubborn = -1;
	s->spawn = f_spawn;
	s->send = f_send;
	s->reap = f_reap;
	s->now_ms = f_now;
	s->wait_ms = f_wait;
	s->do_sync = f_sync;
	s->do_reboot = f_reboot;
	s->log = f_log;
	s->ctx = f;
}

static void mkchild(struct sv_child *c, const char *name)
{
	memset(c, 0, sizeof(*c));
	memcpy(c->name, name, strlen(name) < SV_NAME_MAX - 1
				      ? strlen(name)
				      : (size_t)(SV_NAME_MAX - 1));
	c->path = "/usr/sbin/x";
	c->argv[0] = "x";
}

/* ==========================================================================
 * T-BACKOFF: the sequence, and only that sequence.
 * ========================================================================== */
static void t_backoff(void)
{
	static const unsigned want[] = { 250, 500, 1000, 2000, 4000, 8000, 16000 };
	struct sv_child c;
	long t = 1000;
	size_t k;

	mkchild(&c, "d");
	sv_arm(&c, t);
	CK(c.state == SV_WAIT);
	CK(c.due_ms == t);
	CK(c.fails == 0);

	for (k = 0; k < sizeof(want) / sizeof(want[0]); k++) {
		int st;

		sv_on_start(&c, 200 + (pid_t)k, t);
		CK(c.state == SV_RUNNING);
		t += 5;   /* it lived 5 ms: a fast failure */
		st = sv_on_exit(&c, st_exit(1), t);
		CK(st == SV_WAIT);
		CK(c.fails == (unsigned)(k + 1));
		CK(c.backoff_ms == want[k]);
		CK(c.due_ms == t + (long)want[k]);
		CK(c.pid == 0);
		t += (long)want[k];
	}
	/* The eighth consecutive fast failure is the cap. */
	sv_on_start(&c, 999, t);
	t += 5;
	CK(sv_on_exit(&c, st_exit(1), t) == SV_GIVENUP);
	CK(c.fails == (unsigned)SV_FAIL_MAX);
	CK(c.state == SV_GIVENUP);
	/* The total time spent trying, which is the number that matters at the
	 * bench: 250+500+1000+2000+4000+8000+16000 = 31,750 ms of backoff. */
	CK(250 + 500 + 1000 + 2000 + 4000 + 8000 + 16000 == 31750);
}

/* ==========================================================================
 * T-CAP: once given up, nothing makes it due again -- not time, not a poll.
 * T-CAP-TERMINATES: and the loop that gets there is finite.  M1's target.
 * ========================================================================== */
static void t_cap(void)
{
	struct sv_set s;
	int idx[SV_MAX_CHILD];
	int i, guard;

	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "d");
	s.n = 1;
	sv_arm(&s.c[0], 0);

	/* Bounded: 1,000 iterations is 125x the cap.  With the cap removed this
	 * exits on the guard and the assertion below goes red -- a FAILURE in
	 * finite time, which is what a mutation control has to be. */
	guard = 0;
	while (s.c[0].state != SV_GIVENUP && guard < 1000) {
		sv_on_start(&s.c[0], 500, (long)guard * 10);
		sv_on_exit(&s.c[0], st_exit(1), (long)guard * 10 + 1);
		guard++;
	}
	CK(guard < 1000);                       /* M1 makes this red */
	CK(s.c[0].state == SV_GIVENUP);         /* and this */
	CK(guard == SV_FAIL_MAX);               /* and this */

	/* Nothing brings it back on its own. */
	for (i = 0; i < 4; i++) {
		long t = 1000000l * (i + 1);

		CK(sv_due(&s, t, idx, SV_MAX_CHILD) == 0);
		CK(sv_next_due(&s, t) == -1);
	}
	/* Only an explicit re-arm does -- what SIGHUP uses. */
	sv_arm(&s.c[0], 7);
	CK(s.c[0].state == SV_WAIT);
	CK(sv_due(&s, 7, idx, SV_MAX_CHILD) == 1);
}

/* ==========================================================================
 * T-HEALTHY: SV_RUNOK_MS resets both counters, and does so at the boundary.
 * ========================================================================== */
static void t_healthy(void)
{
	struct sv_child c;
	int k;

	mkchild(&c, "d");
	sv_arm(&c, 0);
	/* Five fast failures, then one that lives exactly SV_RUNOK_MS. */
	for (k = 0; k < 5; k++) {
		sv_on_start(&c, 1, (long)k * 100);
		sv_on_exit(&c, st_exit(1), (long)k * 100 + 1);
	}
	CK(c.fails == 5);
	CK(c.backoff_ms == 4000);

	sv_on_start(&c, 2, 100000);
	CK(sv_on_exit(&c, st_exit(0), 100000 + SV_RUNOK_MS) == SV_WAIT);
	CK(c.fails == 0);
	CK(c.backoff_ms == 0);
	CK(c.due_ms == 100000 + SV_RUNOK_MS);   /* restarted at once */
	CK(c.ran_ms == SV_RUNOK_MS);

	/* One millisecond short of the boundary is still a fast failure, and it
	 * starts the sequence from the beginning because the count was reset. */
	sv_on_start(&c, 3, 200000);
	CK(sv_on_exit(&c, st_exit(1), 200000 + SV_RUNOK_MS - 1) == SV_WAIT);
	CK(c.fails == 1);
	CK(c.backoff_ms == SV_BACKOFF_MS);

	/* A clock that went backwards is not credited as uptime. */
	sv_on_start(&c, 4, 500000);
	CK(sv_on_exit(&c, st_exit(1), 400000) == SV_WAIT);
	CK(c.ran_ms == 0);
	CK(c.fails == 2);
}

/* ==========================================================================
 * T-EXIT0-VS-SIGNAL: the record differs, the policy does not.
 * ========================================================================== */
static void t_exit_vs_signal(void)
{
	struct sv_child a, b;

	mkchild(&a, "a");
	mkchild(&b, "b");
	sv_arm(&a, 0);
	sv_arm(&b, 0);

	sv_on_start(&a, 10, 0);
	CK(sv_on_exit(&a, st_exit(0), 3) == SV_WAIT);
	CK(a.exited == 1);
	CK(a.exit_code == 0);
	CK(a.signo == 0);

	sv_on_start(&b, 11, 0);
	CK(sv_on_exit(&b, st_signal(SIGSEGV), 3) == SV_WAIT);
	CK(b.exited == 0);
	CK(b.signo == SIGSEGV);
	CK(b.exit_code == 0);

	/* Identical policy: a daemon's job is to stay up, and exit(0) at once is
	 * a daemon that could not parse its own config. */
	CK(a.fails == b.fails);
	CK(a.backoff_ms == b.backoff_ms);
	CK(a.due_ms == b.due_ms);

	/* A non-zero exit records its code. */
	sv_on_start(&a, 12, 100);
	CK(sv_on_exit(&a, st_exit(127), 103) == SV_WAIT);
	CK(a.exited == 1 && a.exit_code == 127);   /* 127 = execve failed */
}

/* ==========================================================================
 * T-TWO-AT-ONCE: two children die in the same wake, each keeps its own state.
 * ========================================================================== */
static void t_two_at_once(void)
{
	struct sv_set s;
	struct sv_sys sys;
	struct sysfake f;
	int idx[SV_MAX_CHILD];
	int n;

	sysfake_init(&f, &sys);
	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "a");
	mkchild(&s.c[1], "b");
	mkchild(&s.c[2], "c");
	s.n = 3;
	sv_arm(&s.c[0], 0);
	sv_arm(&s.c[1], 0);
	sv_arm(&s.c[2], 0);

	f.now = 0;
	CK(sv_start_due(&s, &sys, 0) == 3);
	CK(s.c[0].pid == 100 && s.c[1].pid == 101 && s.c[2].pid == 102);

	/* a and b die together; c stays up.  b has already failed twice, so the
	 * two must come out of this wake with DIFFERENT backoffs -- a shared
	 * counter would make them equal and the test would not see it. */
	s.c[1].fails = 2;
	f.q_pid[f.q_tail] = 100; f.q_st[f.q_tail++] = st_exit(1);
	f.q_pid[f.q_tail] = 101; f.q_st[f.q_tail++] = st_signal(SIGKILL);
	CK(sv_reap_all(&s, &sys, 5) == 2);

	CK(s.c[0].state == SV_WAIT && s.c[0].fails == 1);
	CK(s.c[1].state == SV_WAIT && s.c[1].fails == 3);
	CK(s.c[2].state == SV_RUNNING && s.c[2].pid == 102);
	CK(s.c[0].backoff_ms == 250);
	CK(s.c[1].backoff_ms == 1000);
	CK(s.c[0].backoff_ms != s.c[1].backoff_ms);

	/* sv_next_due picks the EARLIEST, and sv_due hands back only what is due. */
	CK(sv_next_due(&s, 5) == 250);
	CK(sv_due(&s, 5, idx, SV_MAX_CHILD) == 0);
	n = sv_due(&s, 5 + 250, idx, SV_MAX_CHILD);
	CK(n == 1 && idx[0] == 0);
	n = sv_due(&s, 5 + 1000, idx, SV_MAX_CHILD);
	CK(n == 2 && idx[0] == 0 && idx[1] == 1);
	/* And `max` is honoured. */
	CK(sv_due(&s, 5 + 1000, idx, 1) == 1);

	/* Nothing waiting at all: the loop must be told to block, not to spin. */
	s.c[0].state = SV_RUNNING;
	s.c[1].state = SV_GIVENUP;
	CK(sv_next_due(&s, 99999) == -1);
}

/* An exit from a pid PID 1 never started -- an orphan the kernel reparented --
 * is reaped and otherwise ignored.  PID 1 leaving a zombie is the bug this is
 * about. */
static void t_orphan(void)
{
	struct sv_set s;
	struct sv_sys sys;
	struct sysfake f;

	sysfake_init(&f, &sys);
	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "a");
	s.n = 1;
	sv_arm(&s.c[0], 0);
	CK(sv_start_due(&s, &sys, 0) == 1);

	f.q_pid[f.q_tail] = 31337; f.q_st[f.q_tail++] = st_exit(0);
	f.q_pid[f.q_tail] = 31338; f.q_st[f.q_tail++] = st_signal(SIGPIPE);
	CK(sv_reap_all(&s, &sys, 10) == 2);
	CK(s.c[0].state == SV_RUNNING);
	CK(s.c[0].fails == 0);
	CK(sv_by_pid(&s, 31337) == NULL);
	CK(sv_by_pid(&s, 100) == &s.c[0]);
	CK(sv_by_pid(&s, 0) == NULL);
	CK(sv_by_pid(&s, -1) == NULL);
}

/* A child in SV_STOPPING that exits stays stopped: shutdown must not race the
 * respawn logic into restarting what it just killed. */
static void t_stopping(void)
{
	struct sv_child c;

	mkchild(&c, "a");
	sv_arm(&c, 0);
	sv_on_start(&c, 5, 0);
	c.state = SV_STOPPING;
	CK(sv_on_exit(&c, st_signal(SIGTERM), 1) == SV_OFF);
	CK(c.pid == 0);
	CK(c.fails == 0);
}

/* A fork that fails is a fast failure, so it cannot spin either. */
static void t_spawn_fail(void)
{
	struct sv_set s;
	struct sv_sys sys;
	struct sysfake f;
	int k;

	sysfake_init(&f, &sys);
	f.spawn_fail = 1;
	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "a");
	s.n = 1;
	sv_arm(&s.c[0], 0);

	for (k = 0; k < SV_FAIL_MAX; k++) {
		long t = (long)k * 100000;

		s.c[0].due_ms = t;
		CK(sv_start_due(&s, &sys, t) == 0);
		CK(s.c[0].pid == 0);
	}
	CK(s.c[0].state == SV_GIVENUP);
	CK(s.c[0].starts == 0);
}

/* ==========================================================================
 * T-REBOOT-ORDER: sync before reboot, reboot last, TERM before both.
 * ========================================================================== */
static int ev_index(const struct sysfake *f, const char *what)
{
	int i;

	for (i = 0; i < f->n_ev; i++)
		if (strncmp(f->ev[i], what, strlen(what)) == 0)
			return i;
	return -1;
}

static int ev_count(const struct sysfake *f, const char *what)
{
	int i, n = 0;

	for (i = 0; i < f->n_ev; i++)
		if (strncmp(f->ev[i], what, strlen(what)) == 0)
			n++;
	return n;
}

static void t_reboot_order(void)
{
	struct sv_set s;
	struct sv_sys sys;
	struct sysfake f;
	int i_sync, i_reboot, i_term;

	sysfake_init(&f, &sys);
	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "brokerd");
	mkchild(&s.c[1], "httpd");
	mkchild(&s.c[2], "off");
	s.n = 3;
	sv_arm(&s.c[0], 0);
	sv_arm(&s.c[1], 0);
	s.c[2].state = SV_OFF;
	CK(sv_start_due(&s, &sys, 0) == 2);

	CK(sv_shutdown(&s, &sys, SV_REBOOT) == 0);

	i_term = ev_index(&f, "TERM");
	i_sync = ev_index(&f, "sync");
	i_reboot = ev_index(&f, "reboot");
	CK(i_term >= 0);
	CK(i_sync >= 0);
	CK(i_reboot >= 0);
	CK(ev_count(&f, "sync") == 1);
	CK(ev_count(&f, "reboot") == 1);
	CK(ev_count(&f, "TERM") == 2);              /* not the SV_OFF child */
	CK(i_term < i_sync);                        /* children first */
	CK(i_sync < i_reboot);                      /* THE ordering */
	CK(i_reboot == f.n_ev - 1);                 /* and nothing after it */
	CK(ev_count(&f, "KILL") == 0);              /* they went quietly */
	CK(s.c[0].state == SV_OFF && s.c[1].state == SV_OFF);
	if (i_sync >= 0 && i_reboot >= 0 && i_sync >= i_reboot)
		printf("      event log: sync at %d, reboot at %d\n", i_sync,
		       i_reboot);

	/* A child that ignores SIGTERM: SIGKILL after SV_TERM_MS, and `sync`
	 * still comes after every kill and before the reboot. */
	sysfake_init(&f, &sys);
	memset(&s, 0, sizeof(s));
	mkchild(&s.c[0], "stubborn");
	s.n = 1;
	sv_arm(&s.c[0], 0);
	CK(sv_start_due(&s, &sys, 0) == 1);
	f.stubborn = s.c[0].pid;
	f.stubborn_until = 1000000l;   /* never gives in */
	CK(sv_shutdown(&s, &sys, SV_POWEROFF) == 0);
	CK(ev_count(&f, "KILL") == 1);
	CK(ev_index(&f, "KILL") < ev_index(&f, "sync"));
	CK(ev_index(&f, "sync") < ev_index(&f, "reboot"));
	CK(f.now >= SV_TERM_MS);       /* it waited, and it stopped waiting */
	CK(f.now <= SV_TERM_MS + SV_TERM_STEP_MS);
	/* The `how` reached reboot() unchanged. */
	CK(strcmp(f.ev[f.n_ev - 1], "reboot 01") == 0 ||
	   strcmp(f.ev[f.n_ev - 1], "reboot 1") == 0);

	/* Nothing running at all still syncs and still reboots. */
	sysfake_init(&f, &sys);
	memset(&s, 0, sizeof(s));
	s.n = 0;
	CK(sv_shutdown(&s, &sys, SV_REBOOT) == 0);
	CK(ev_count(&f, "sync") == 1);
	CK(ev_count(&f, "reboot") == 1);
	CK(ev_index(&f, "sync") < ev_index(&f, "reboot"));
}

/* Every entry point survives a NULL rather than dereferencing it: PID 1 must
 * not be the process that segfaults. */
static void t_nulls(void)
{
	struct sv_child c;
	int idx[2];

	mkchild(&c, "a");
	sv_arm(NULL, 0);
	sv_on_start(NULL, 1, 0);
	CK(sv_on_exit(NULL, 0, 0) == SV_OFF);
	CK(sv_on_spawn_fail(NULL, 0) == SV_OFF);
	CK(sv_next_due(NULL, 0) == -1);
	CK(sv_due(NULL, 0, idx, 2) == 0);
	CK(sv_by_pid(NULL, 1) == NULL);
	CK(sv_start_due(NULL, NULL, 0) == 0);
	CK(sv_reap_all(NULL, NULL, 0) == 0);
	CK(sv_shutdown(NULL, NULL, 0) == -1);
}

int main(void)
{
	t_backoff();
	t_cap();
	t_healthy();
	t_exit_vs_signal();
	t_two_at_once();
	t_orphan();
	t_stopping();
	t_spawn_fail();
	t_reboot_order();
	t_nulls();
	printf("test_supervise: %d checks, %d failures\n", checks, fails);
	return fails == 0 ? 0 : 1;
}
