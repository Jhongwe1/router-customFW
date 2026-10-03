/* src/brokerd/brokerd.h -- the broker's state and its seams.
 *
 * ONE struct holds everything mutable.  There are no globals in ops.c or
 * session.c, because every seam a test has to drive -- the clock, the entropy
 * file, the random source, the ping binary and its timeout -- is a field here,
 * set by bk_init() to the production value and overridden only by a test.
 * Nothing on the command line can move them: an option that repointed
 * ->entropy_path would be a runtime bypass of the fail-closed rule, and
 * "do not build the bypass" is cheaper than auditing who may use it.
 */
#ifndef RLXFW_BROKERD_H
#define RLXFW_BROKERD_H

#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

#include "cfg.h"
#include "proto.h"
#include "schema.h"	/* the CFGID_* ids and CFG_PWHASH_LEN; `R7-8` */
#include "kdf.h"		/* KDF_LOG2N/R/P, the one owner of the parameters */

#define BK_SOCK_PATH   "/srv/www/run/broker.sock"
#define BK_CFG_PATH    "/var/lib/cfg.bin"
#define BK_ENTROPY_PATH "/proc/sys/kernel/random/entropy_avail"
#define BK_RANDOM_PATH "/dev/urandom"
#define BK_PING_BIN    "/bin/busybox"
#define BK_VERSION_STR "rlxfw-brokerd-1"

#define BK_UID_ROOT   0
#define BK_UID_HTTPD  100
#define BK_UID_DNSFWD 101

#define BK_NSESS        4        /* SPEC § 6: at most 4, LRU eviction */
#define BK_SESS_TTL     900      /* seconds of idle; >= TTL is expired */
#define BK_NRL          16       /* SPEC § 6: 16-entry token bucket table */
#define BK_RL_FAILS     5        /* consecutive failures that lock */
#define BK_RL_LOCK0     60       /* first lock, seconds */
#define BK_RL_LOCKCAP   3600     /* doubling stops here */
#define BK_ENTROPY_MIN  128      /* entropy_avail seen once at or above this */
#define BK_PING_TIMEOUT 10       /* seconds; the mechanism that ends a ping */
#define BK_PING_OUT_MAX 2048
#define BK_GET_MAX_KEYS 64

/* KDF parameters brokerd writes into a NEW admin.pwhash.  From plan § D8's
 * anti-DoS budget: 1 evaluation in flight x 128*N*r bytes <= 4 MiB, r = 8, so
 * N <= 4096 and log2N = 12 -- 4 MiB exactly.  A hash already on disk is
 * verified with ITS OWN parameters, read out of bytes [1..5]; these three only
 * decide what a PWSET writes.  Time on the device: 未定 (agent D's row). */
/* 🔴 `R7-8`: this said `BK_KDF_R 8`.  src/lib/kdf.h's ruling is r = 7, and
 * kdf_scrypt REFUSES any parameter set whose peak exceeds KDF_PEAK_CAP
 * (4,194,304 B); (12, 8, 1) peaks at 4,197,376, so PWSET would have failed
 * -KDFE_NOMEM on every call and a blob already carrying r = 8 could not be
 * verified either.  Aliased to the one owner rather than re-typed. */
#define BK_KDF_LOG2N KDF_LOG2N
#define BK_KDF_R     KDF_R
#define BK_KDF_P     KDF_P
#define BK_PWHASH_LEN CFG_PWHASH_LEN	/* 56, owned by src/lib/schema.h */

struct bk_sess {
	int      used;
	uint8_t  tok[PROTO_TOK_LEN];
	uint8_t  csrf[PROTO_TOK_LEN];
	long     last;        /* bk_now() at the last accepted use */
	unsigned long born;   /* insertion order, the LRU tie-break */
};

struct bk_rl {
	int      used;
	uint32_t ip;
	uint8_t  fails;       /* consecutive */
	uint32_t lock_s;      /* length of the NEXT lock; 0 = never locked yet */
	long     lock_until;  /* bk_now() past which the lock is gone */
	long     seen;        /* bk_now() at the last touch, for eviction */
};

/* What the last bk_cfg_reload() found, kept so that a change is logged once
 * and not once per request (`FW-184`). */
#define BK_CFG_OK      0	/* a valid record, or no store yet */
#define BK_CFG_IO      1	/* the store could not be opened or read */
#define BK_CFG_INVALID 2	/* bytes, and no valid record in either slot */

struct broker {
	struct cfg cfg;
	const char *cfg_path;
	int cfg_state;              /* BK_CFG_*; 0 from bk_init() */

	struct bk_sess sess[BK_NSESS];
	unsigned long  sess_seq;

	struct bk_rl rl[BK_NRL];

	int      auth_ready;        /* sticky: entropy_avail >= 128 seen once */
	uint32_t entropy_last;      /* what the last read said, for STATUS */
	int      kdf_busy;          /* the global "1 scrypt in flight" latch */
	int      pending_reboot;    /* main() acts on this AFTER the reply */

	/* seams: production values from bk_init(), moved only by tests */
	const char *entropy_path;
	const char *random_path;
	const char *uptime_path;
	const char *loadavg_path;
	const char *meminfo_path;
	const char *ping_bin;
	int  ping_timeout_s;
	int  use_fake_clock;
	long fake_now;
};

void bk_init(struct broker *bk);
long bk_now(const struct broker *bk);
/* Monotonic milliseconds.  A whole-second deadline is coarse in the wrong
 * direction: floor()ing the start means `now + 2` can fall only 1.01 s later,
 * so a "10 s" PING timeout would be anywhere in [9, 10].  Every deadline that
 * is measured against a wall clock uses this. */
long long bk_now_ms(const struct broker *bk);

/* Constant-time equality.  1 when equal, 0 when not.  Written once and used
 * for every token, CSRF and password-hash comparison in this program; there is
 * no other comparison of a secret anywhere in brokerd. */
int bk_ct_eq(const void *a, const void *b, size_t n);

/* ---- entropy and randomness ------------------------------------------ */
int  bk_entropy_ready(struct broker *bk);   /* 1 ready, 0 not.  Sticky. */
int  bk_random(struct broker *bk, uint8_t *p, size_t n);  /* 0 or -1 */

/* ---- sessions -------------------------------------------------------- */
void bk_sess_expire(struct broker *bk);
struct bk_sess *bk_sess_find(struct broker *bk, const uint8_t tok[PROTO_TOK_LEN]);
struct bk_sess *bk_sess_new(struct broker *bk);
void bk_sess_drop(struct bk_sess *s);
void bk_sess_drop_all(struct broker *bk);
int  bk_sess_count(const struct broker *bk);

/* ---- LOGIN rate limit ------------------------------------------------ */
/* 0 = may proceed to the KDF; 1 = locked, *secs holds how long is left. */
int  bk_rl_check(struct broker *bk, uint32_t ip, uint32_t *secs);
void bk_rl_fail(struct broker *bk, uint32_t ip);
void bk_rl_ok(struct broker *bk, uint32_t ip);
struct bk_rl *bk_rl_peek(struct broker *bk, uint32_t ip);   /* tests only */

/* ---- the authorisation table (ops.c) --------------------------------- */
struct bk_op_rule {
	uint8_t     op;
	const char *name;
	uint8_t     supported;      /* 0 -> NOTSUP, whoever asks */
	uint8_t     allow_100;      /* httpd may call it at all */
	uint8_t     allow_101;      /* dnsfwd may call it at all */
	uint8_t     need_session;   /* non-root needs a live session */
	uint8_t     need_csrf;      /* ... and a matching CSRF token */
	uint8_t     rw_only;        /* non-root may only touch WEB_RW keys */
};

const struct bk_op_rule *bk_op_rule(uint8_t op);
int bk_op_count(void);
const struct bk_op_rule *bk_op_at(int i);

/* dnsfwd's two keys, by id.  The list, not a pair of ifs. */
int bk_dnsfwd_may_read(uint16_t id);

/* The dispatcher.  Fills rs (status, body, body_len) and returns 0; a negative
 * return means it could not even form a response, which main() turns into a
 * bare ST_IO reply. */
int bk_dispatch(struct broker *bk, const struct proto_req *rq, uid_t peer_uid,
                struct proto_resp *rs);

/* `FW-184`: re-read the store into bk->cfg.  bk_dispatch() calls it before
 * every request it has not already refused, and main() once at start-up; the
 * argument for why that is enough, and how it fails closed, is above it in
 * ops.c.  0 when bk->cfg is a record from the store or the store does not
 * exist yet; -1 when it is the defaults over a store that could not be used. */
int bk_cfg_reload(struct broker *bk);

/* STATUS TLV types (SPEC § 6). */
#define BKS_UPTIME   0x8001
#define BKS_LOAD1    0x8002
#define BKS_MEMFREE  0x8003
#define BKS_CFGSRC   0x8004
#define BKS_CFGSEQ   0x8005
#define BKS_VERSION  0x8006
#define BKS_ENTROPY  0x8007
#define BKS_AUTHRDY  0x8008

/* /proc readers STATUS uses; bounded, no allocation (session.c). */
uint32_t bk_proc_uptime(struct broker *bk);
uint32_t bk_proc_load1x100(struct broker *bk);
uint32_t bk_proc_memfree_kb(struct broker *bk);

void bk_log(const char *fmt, ...);

#endif /* RLXFW_BROKERD_H */
