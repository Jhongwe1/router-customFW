/* firstpw.h -- the console first-password step of notes/self-update.md § 3.8
 * (PROGRESS.md P6r-10), for the image built with BENCH_SHELL=0.  PID 1 forks
 * it once per boot when the store it loaded holds no admin.pwhash
 * (src/init/main.c); fp_run() is the whole step.
 *
 * Everything it touches comes in through struct fp_env: the console's two
 * descriptors, the store's path, the entropy reading, the salt and the sleep,
 * so src/init/test_firstpw.c drives it with a pipe or a pty, a file-backend
 * store in a scratch directory and an entropy pool that fills on cue.
 * fp_env_dev() fills in the device's.
 */
#ifndef RLXFW_INIT_FIRSTPW_H
#define RLXFW_INIT_FIRSTPW_H

#include <stdint.h>

#include "cfg.h"

/* The password's bounds: cfgstore passwd's (src/cfgstore/main.c, 8 and
 * CFGSTORE_PW_MAX 64) and PWSET's (src/brokerd/ops.c, newlen 8..64), so a
 * password one of them takes the others take. */
#define FP_PW_MIN	8
#define FP_PW_MAX	64

/* While the pool is short: one salt attempt a second, and one console line
 * on the first and then every 30th. */
#define FP_WAIT_STEP_MS		1000L
#define FP_WAIT_SAY_EVERY	30

#define FP_LINE_MAX	200	/* one console line, NUL included */

enum fp_result {
	FP_R_SET_STORE = 0,	/* the hash added to the valid record: cfg_store */
	FP_R_SET_FRESH,		/* defaults + the hash: cfg_store_fresh */
	FP_R_HASHED,		/* the store already holds a hash: nothing written */
	FP_R_EOF,		/* the console's input ended: nothing written */
	FP_R_TTY,		/* echo could not be turned off: nothing read */
	FP_R_KDF,		/* no salt or no hash: nothing written */
	FP_R_IO			/* the store could not be read, or the write failed */
};

struct fp_env {
	int in_fd;			/* the console, read one byte at a time */
	int out_fd;			/* the console, written one line at a time */
	const char *store;		/* CFG_FLASH_DEV on the device */
	int  (*entropy)(void *ctx);	/* kdf_entropy_avail(): the reading */
	int  (*salt)(void *ctx, uint8_t salt[16]);	/* pwhash_salt() */
	void (*sleep_ms)(void *ctx, long ms);
	void *ctx;
};

/* The device's seams around the given descriptors and store: kdf.c's
 * kdf_entropy_avail and pwhash_salt, nanosleep. */
void fp_env_dev(struct fp_env *e, int in_fd, int out_fd, const char *store);

/* Whether PID 1 offers the step, on the store as it loaded it at boot:
 * FP_OFFER_YES when cfg_load returned 0 and the record (or the defaults it
 * fell back to) holds no admin.pwhash; FP_OFFER_NO when it holds one;
 * FP_OFFER_UNREADABLE when cfg_load failed -- a store that cannot be read is
 * never written over. */
#define FP_OFFER_YES		1
#define FP_OFFER_NO		0
#define FP_OFFER_UNREADABLE	(-1)
int fp_offer(int load_rc, const struct cfg *c);

/* The step: the password twice with echo off, the salt once the pool allows
 * it, scrypt with kdf.h's KDF_LOG2N/KDF_R/KDF_P, and ONE store write chosen on
 * the store as it reads at that moment -- cfg_store when it holds a valid
 * record without a hash, cfg_store_fresh when neither slot holds a valid
 * record, nothing when it holds a hash or cannot be read.  A short, long or
 * mismatched entry writes nothing and asks again.  Returns an FP_R_*. */
int fp_run(const struct fp_env *e);

#endif /* RLXFW_INIT_FIRSTPW_H */
