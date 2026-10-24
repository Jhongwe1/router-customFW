/* ctradv.h -- the counter advance after "up" (notes/self-update.md § 5;
 * PROGRESS.md P6r-11).  PID 1 forks ONE helper per boot that runs
 * ctr_advance(); src/init/main.c decides when (ctr_fork_due), this file what.
 *
 * Everything the helper touches comes in through struct ctr_env -- the five
 * spictl paths, the handoff node, the broker probe, the clock, the sleep and
 * the console -- so src/init/test_ctradv.c drives it against scratch files, a
 * broker stand-in and a clock that moves only when the code sleeps.
 * ctr_env_dev() fills in the device's.
 */
#ifndef RLXFW_INIT_CTRADV_H
#define RLXFW_INIT_CTRADV_H

#include <stddef.h>
#include <stdint.h>

#include "spictl.h"
#include "supervise.h"

/* "Up" is brokerd answering a STATUS, tried every CTR_UP_STEP_MS for up to
 * CTR_UP_BUDGET_MS (the design's 500 ms and 60 s): 1 + 60,000 / 500 = 121
 * tries at most, the last at 60 s. */
#define CTR_UP_STEP_MS		500L
#define CTR_UP_BUDGET_MS	60000L
/* The flash lock's wait: the store's own (CFG_FLASH_LOCK_S, src/lib/cfg.h). */
#define CTR_LOCK_S		30u
/* bk_call's two timeouts for one STATUS, seconds: one stalled try costs at
 * most this much of the 60 s, not the client's default 15 s. */
#define CTR_BK_CONNECT_S	1
#define CTR_BK_IO_S		2

/* The handoff node (kernel/linux-2.6.30/arch/rlx/kernel/rlxfw-boot.c):
 * `slot B ver 6\n` or `none\n`, at most 22 bytes. */
#define CTR_BOOT_PATH		"/proc/rlxfw-boot"
/* brokerd's socket, as PID 1 sees it.  The one definition is BK_SOCK_PATH in
 * src/brokerd/brokerd.h; init does not include brokerd's state header, and
 * test_ctradv.c holds the two strings equal. */
#define CTR_BROKER_SOCK		"/srv/www/run/broker.sock"

#define CTR_LINE_MAX		200	/* one console line, NUL included */
#define CTR_REASON_MAX		32	/* a reason name of the install header */

/* What ctr_advance() did.  Only CTR_R_OK changed the flash; CTR_R_FAILED may
 * have (after the kernel's first program).  Every other result wrote no verb,
 * or wrote one the kernel refused before its first program. */
enum ctr_result {
	CTR_R_OK = 0,		/* advanced: `rlxfw: ctr <c> -> <n> OK pp=<k>` */
	CTR_R_SAME,		/* the counter already read <n>: nothing programmed */
	CTR_R_NOBROKER,		/* no STATUS answer in 60 s: no verb */
	CTR_R_NOHANDOFF,	/* /proc/rlxfw-boot reads `none`: no verb */
	CTR_R_BOOTREAD,		/* /proc/rlxfw-boot unreadable or malformed: no verb */
	CTR_R_LOCK,		/* the flash lock was not taken: no verb */
	CTR_R_STATE,		/* the node unreadable before the verb: no verb */
	CTR_R_UNRAN,		/* the verb never reached the counter code */
	CTR_R_REFUSED,		/* the kernel refused before its first program */
	CTR_R_FAILED,		/* the kernel failed after programming */
	CTR_R_UNKNOWN		/* the node after the verb did not add up */
};

struct ctr_env {
	const struct spictl_paths *sp;	/* verbs to sp->proc, fields from sp->state */
	const char *boot_path;		/* CTR_BOOT_PATH */
	int  (*broker_up)(void *ctx);	/* 1: STATUS answered ST_OK; 0: not (yet) */
	long (*now_ms)(void *ctx);	/* monotonic milliseconds */
	void (*sleep_ms)(void *ctx, long ms);
	void (*say)(void *ctx, const char *line);	/* one line, no '\n' */
	void *ctx;
	unsigned lock_s;		/* spictl_lock's timeout, CTR_LOCK_S */
};

/* The device's: spictl_dev, CTR_BOOT_PATH, ctr_broker_status(CTR_BROKER_SOCK),
 * CLOCK_MONOTONIC, nanosleep, one write(2) of the line and '\n' to fd 1. */
void ctr_env_dev(struct ctr_env *e);

/* The whole helper: up, the handoff, the lock, ONE `ctr <version>`, the
 * fields, the release, one console line beginning "rlxfw: ctr ".  Returns a
 * CTR_R_*. */
int ctr_advance(const struct ctr_env *e);

/* 1 once e->broker_up answered, 0 when CTR_UP_BUDGET_MS passed without. */
int ctr_wait_up(const struct ctr_env *e);

/* /proc/rlxfw-boot's text, exactly: CTR_BOOT_SLOT with *slot 'A' or 'B' and
 * *ver 1..0xFFFFFFFE (decimal, no leading zero), CTR_BOOT_NONE, or
 * CTR_BOOT_BAD for anything else -- a missing newline, a trailing byte, slot
 * C, version 0 or 06.  Nothing is set unless CTR_BOOT_SLOT. */
#define CTR_BOOT_SLOT	1
#define CTR_BOOT_NONE	0
#define CTR_BOOT_BAD	(-1)
int ctr_parse_boot(const char *buf, size_t n, char *slot, uint32_t *ver);

/* One STATUS as root through bk_call (src/lib/client.c), timeouts
 * CTR_BK_CONNECT_S and CTR_BK_IO_S: 1 when a response frame came back with
 * ST_OK, else 0. */
int ctr_broker_status(const char *sock);

/* When PID 1 forks the helper, decided on its child table: 1 now (brokerd has
 * been started at least once), 0 not yet, CTR_FORK_NOLAN when `lan up` was
 * not printed, CTR_FORK_NOBROKER when the table has no brokerd that can ever
 * start (no row, SV_OFF, SV_ABSENT).  ctr_fork_why() is the console line for a
 * negative answer. */
#define CTR_FORK_NOLAN		(-1)
#define CTR_FORK_NOBROKER	(-2)
int ctr_fork_due(const struct sv_set *s, int lan_said_up);
const char *ctr_fork_why(int due);

#endif /* RLXFW_INIT_CTRADV_H */
