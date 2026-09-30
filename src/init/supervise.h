/* supervise.h -- R7: PID 1's child table and the respawn state machine.
 *
 * ---------------------------------------------------------------------------
 * THE STATE MACHINE IS A PURE FUNCTION OF (child, wstatus, now_ms)
 * ---------------------------------------------------------------------------
 *
 * `sv_on_exit`, `sv_next_due` and `sv_due` touch no clock, no signal and no
 * process: they are given `now_ms` and they return what to do.  That is what
 * lets `test_supervise.c` drive a crash loop of eight failures in microseconds,
 * with no fork, and assert the exact backoff sequence -- and it is why the
 * crash-loop cap is testable at all.  The loop in `main.c` supplies the clock,
 * the `waitpid` and the `fork`/`execve`.
 *
 * ---------------------------------------------------------------------------
 * THE POLICY, AND THE FOUR CONSTANTS IT IS MADE OF
 * ---------------------------------------------------------------------------
 *
 *   SV_RUNOK_MS      10000   a child that stayed up this long is healthy:
 *                            its consecutive-failure count and its backoff
 *                            both reset.  Anything shorter is a fast failure.
 *   SV_BACKOFF_MS      250   the first fast failure waits this long
 *   SV_BACKOFF_MAX_MS 16000  and the wait doubles to here and stops
 *   SV_FAIL_MAX            8 consecutive fast failures and the child moves to
 *                            SV_GIVENUP: never restarted, one loud console
 *                            line, and the rest of the system keeps running
 *
 * The sequence is therefore 250, 500, 1000, 2000, 4000, 8000, 16000, 16000 ms
 * and then a stop -- about 32 s of trying before a broken daemon is left alone.
 * Without the cap, a missing binary is an `execve` that fails every 16 s for as
 * long as the board is powered, and the console it prints on is the console the
 * bench needs.  `test_supervise.c` `T-CAP` and the mutation control in
 * `notes/init.md` 6 are both about this.
 *
 * A child that exits 0 is still a fast failure if it ran for less than
 * SV_RUNOK_MS: a daemon's job is to stay up, and exit(0) at once is the shape
 * of a daemon that cannot parse its own config.  What differs is the record --
 * `exited`/`exit_code`/`signo` -- and the console word, so a capture says which
 * of the three happened.
 */

#ifndef RLXFW_INIT_SUPERVISE_H
#define RLXFW_INIT_SUPERVISE_H

#include <stddef.h>
#include <sys/types.h>

#define SV_MAX_CHILD 8
#define SV_ARGV_MAX 8
#define SV_NAME_MAX 12

#define SV_RUNOK_MS 10000
#define SV_BACKOFF_MS 250
#define SV_BACKOFF_MAX_MS 16000
#define SV_FAIL_MAX 8
#define SV_TERM_MS 2000   /* how long shutdown waits after SIGTERM */
#define SV_TERM_STEP_MS 50

enum sv_state {
	SV_OFF = 0,     /* its config key says no; never started */
	SV_ABSENT,      /* its binary is not on the image; never started */
	SV_WAIT,        /* a start is due at `due_ms` */
	SV_RUNNING,
	SV_GIVENUP,     /* SV_FAIL_MAX consecutive fast failures */
	SV_STOPPING     /* SIGTERM sent, waiting for the exit */
};

enum sv_how { SV_REBOOT = 0, SV_POWEROFF = 1, SV_HALT = 2 };

struct sv_child {
	char name[SV_NAME_MAX];
	const char *path;
	const char *argv[SV_ARGV_MAX]; /* fixed literals, NULL-terminated */
	int console;                   /* 1 = new session + controlling tty */

	int state;
	pid_t pid;
	unsigned starts;
	unsigned fails;          /* consecutive fast failures */
	unsigned backoff_ms;
	long due_ms;
	long started_ms;
	/* the last exit, recorded for the console and for the tests */
	int exited;              /* 1 = WIFEXITED */
	int exit_code;
	int signo;               /* WTERMSIG, or 0 */
	long ran_ms;
};

struct sv_set {
	struct sv_child c[SV_MAX_CHILD];
	int n;
};

/* The injectable side.  `spawn` returns a pid > 0 or -1; the real one is
 * fork + execve.  `reap` is waitpid(-1, st, WNOHANG)-shaped: > 0 a pid, 0
 * nothing ready, -1 no children.  Every pointer must be non-NULL. */
struct sv_sys {
	pid_t (*spawn)(void *ctx, const struct sv_child *c);
	int (*send)(void *ctx, pid_t pid, int sig);
	pid_t (*reap)(void *ctx, int *wstatus);
	long (*now_ms)(void *ctx);
	void (*wait_ms)(void *ctx, long ms);
	void (*do_sync)(void *ctx);
	int (*do_reboot)(void *ctx, int how);   /* how is enum sv_how */
	void (*log)(void *ctx, const struct sv_child *c, const char *what);
	void *ctx;
};

/* ------------------------------------------------------------ pure machine */

/* Arm a child for its first start at `now_ms` (state SV_WAIT, due now). */
void sv_arm(struct sv_child *c, long now_ms);

/* Record an exit.  Chooses the next state and, for SV_WAIT, `due_ms`.
 * Returns the new state. */
int sv_on_exit(struct sv_child *c, int wstatus, long now_ms);

/* Note that a start happened (state SV_RUNNING, `pid`, `started_ms`). */
void sv_on_start(struct sv_child *c, pid_t pid, long now_ms);

/* Note that a start could not happen (spawn failed): treated as a fast
 * failure, so a fork that fails cannot spin. */
int sv_on_spawn_fail(struct sv_child *c, long now_ms);

/* Milliseconds until the earliest due start, 0 if one is due now, or -1 when
 * nothing is waiting (the loop then blocks until a signal). */
long sv_next_due(const struct sv_set *s, long now_ms);

/* Indices of the children due to start at `now_ms`, into `idx[0..max-1]`.
 * Returns how many. */
int sv_due(const struct sv_set *s, long now_ms, int *idx, int max);

/* The child with this pid, or NULL. */
struct sv_child *sv_by_pid(struct sv_set *s, pid_t pid);

/* ----------------------------------------------------------- the impure bits */

/* Start every due child through `sys->spawn`.  Returns how many started. */
int sv_start_due(struct sv_set *s, const struct sv_sys *sys, long now_ms);

/* Reap everything ready and feed each exit to `sv_on_exit`.  Returns how many
 * exits were processed. */
int sv_reap_all(struct sv_set *s, const struct sv_sys *sys, long now_ms);

/* SIGTERM everything running, wait up to SV_TERM_MS reaping, SIGKILL the rest,
 * `sync`, then `reboot`.  Returns `do_reboot`'s value; it is not expected to
 * return at all on the device. */
int sv_shutdown(struct sv_set *s, const struct sv_sys *sys, int how);

#endif /* RLXFW_INIT_SUPERVISE_H */
