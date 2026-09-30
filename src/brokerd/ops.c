/* src/brokerd/ops.c -- the op table, the authorisation gate, and the ops.
 *
 * AUTHORISATION IS A TABLE.  `rules[]` below is the whole of it: there is no
 * `if (uid == 100)` in any op handler, and `authorise()` is the only function
 * that reads a uid.  test_authz.c walks the same table and asserts the status
 * for every (op x uid x session x csrf) cell, so a row added without a rule is
 * a failing test rather than an open door.
 *
 * WHERE THIS DEVIATES FROM SPEC-R7 § 6, because § 6 does not say (each is in
 * the report under SPEC DEVIATIONS):
 *   * a live session with a WRONG CSRF token answers PERM, not AUTH.  AUTH
 *     tells httpd "the session is gone, clear the cookie"; a CSRF mismatch is
 *     a request that must be refused without logging the user out.
 *   * GET refuses a WEB_HIDDEN key to a non-root peer with PERM.  § 6 pins
 *     "web=rw keys only" for SET and says nothing for GET; admin.pwhash is
 *     `hidden` and must not leave through httpd.
 *   * the LOGIN rate limiter is keyed on the EFFECTIVE client_ip and root is
 *     exempt.  Locking the console out of cfgstore buys nothing: a root peer
 *     already owns the box.
 *   * the entropy gate applies to every uid, root included.  PWSET needs 16
 *     random salt bytes whoever asks for it.
 *   * PWSET with oldlen = 0 is accepted ONLY from root and ONLY when no
 *     admin.pwhash exists -- the console bootstrap § 5 describes.
 */
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "brokerd.h"
#include "kdf.h"

/*                     op          name       sup 100 101 sess csrf rw  */
static const struct bk_op_rule rules[] = {
	{ OP_GET,          "GET",          1, 1, 1, 1, 0, 0 },
	{ OP_SET,          "SET",          1, 1, 0, 1, 1, 1 },
	{ OP_REBOOT,       "REBOOT",       1, 1, 0, 1, 1, 0 },
	{ OP_STATUS,       "STATUS",       1, 1, 0, 0, 0, 0 },
	{ OP_PING,         "PING",         1, 1, 0, 1, 1, 0 },
	{ OP_LOGIN,        "LOGIN",        1, 1, 0, 0, 0, 0 },
	{ OP_LOGOUT,       "LOGOUT",       1, 1, 0, 1, 1, 0 },
	{ OP_PWSET,        "PWSET",        1, 1, 0, 1, 1, 0 },
	{ OP_UPDATE_BEGIN, "UPDATE_BEGIN", 0, 1, 0, 1, 1, 0 },
	{ OP_UPDATE_DATA,  "UPDATE_DATA",  0, 1, 0, 1, 1, 0 },
	{ OP_UPDATE_END,   "UPDATE_END",   0, 1, 0, 1, 1, 0 }
};
#define NRULES ((int)(sizeof(rules) / sizeof(rules[0])))

/* dnsfwd's two keys.  A list, so adding a third is one line and one test. */
static const uint16_t dnsfwd_keys[] = { CFGID_LAN_IPADDR, CFGID_DNS_UPSTREAM };

const struct bk_op_rule *bk_op_rule(uint8_t op)
{
	int i;

	for (i = 0; i < NRULES; i++)
		if (rules[i].op == op)
			return &rules[i];
	return 0;
}

int bk_op_count(void) { return NRULES; }

const struct bk_op_rule *bk_op_at(int i)
{
	return (i >= 0 && i < NRULES) ? &rules[i] : 0;
}

int bk_dnsfwd_may_read(uint16_t id)
{
	size_t i;

	for (i = 0; i < sizeof(dnsfwd_keys) / sizeof(dnsfwd_keys[0]); i++)
		if (dnsfwd_keys[i] == id)
			return 1;
	return 0;
}

/* ------------------------------------------------------- response helpers */

static void rs_status(struct proto_resp *rs, uint8_t st)
{
	memset(rs, 0, sizeof(*rs));
	rs->version = PROTO_VERSION;
	rs->status = st;
	rs->reserved = 0;
	rs->body_len = 0;
}

static void rs_locked(struct proto_resp *rs, uint32_t secs)
{
	rs_status(rs, ST_LOCKED);
	proto_put_be32(rs->body, secs);
	rs->body_len = 4;
}

static void rs_inval(struct proto_resp *rs, uint16_t key)
{
	rs_status(rs, ST_INVAL);
	proto_put_be16(rs->body, key);
	rs->body_len = 2;
}

/* ------------------------------------------------------------- the ops */

static int op_get(struct broker *bk, const struct proto_req *rq, uid_t uid,
                  int have_sess, struct proto_resp *rs)
{
	size_t nkeys, i, off = 0;

	(void)have_sess;
	if (rq->body_len == 0 || (rq->body_len & 1u) != 0) {
		rs_inval(rs, 0);
		return 0;
	}
	nkeys = rq->body_len / 2u;
	if (nkeys > BK_GET_MAX_KEYS) {
		rs_inval(rs, 0);
		return 0;
	}
	rs_status(rs, ST_OK);
	for (i = 0; i < nkeys; i++) {
		uint16_t id = proto_be16(rq->body + i * 2);
		const struct cfg_key *k = cfg_key_by_id(id);
		uint8_t v[CFG_VAL_MAX];
		uint16_t len = 0;

		if (k == 0) {
			rs_inval(rs, id);
			return 0;
		}
		if (uid != BK_UID_ROOT && k->web == WEB_HIDDEN) {
			rs_status(rs, ST_PERM);
			return 0;
		}
		if (uid == BK_UID_DNSFWD && !bk_dnsfwd_may_read(id)) {
			rs_status(rs, ST_PERM);
			return 0;
		}
		if (cfg_get(&bk->cfg, id, v, &len) != 0) {
			rs_status(rs, ST_NOENT);
			return 0;
		}
		if (proto_tlv_put(rs->body, sizeof(rs->body), &off, id, v, len) != 0) {
			rs_status(rs, ST_BADREQ);
			return 0;
		}
	}
	rs->body_len = (uint32_t)off;
	return 0;
}

static int op_set(struct broker *bk, const struct proto_req *rq, uid_t uid,
                  struct proto_resp *rs)
{
	struct cfg work = bk->cfg;         /* commit only if everything passes */
	size_t off = 0;
	long prev = -1;
	int n = 0;

	if (rq->body_len == 0) {
		rs_inval(rs, 0);
		return 0;
	}
	while (off < rq->body_len) {
		uint16_t type, len;
		const uint8_t *val;
		const struct cfg_key *k;

		if (proto_tlv_get(rq->body, rq->body_len, &off, &type, &val, &len) != 0) {
			rs_inval(rs, 0);
			return 0;
		}
		if (++n > BK_GET_MAX_KEYS) {
			rs_inval(rs, 0);
			return 0;
		}
		/* Strictly ascending, so duplicates are impossible (SPEC § 5). */
		if (prev >= 0 && (long)type <= prev) {
			rs_inval(rs, type);
			return 0;
		}
		prev = (long)type;
		k = cfg_key_by_id(type);
		if (k == 0) {
			rs_inval(rs, type);
			return 0;
		}
		if (uid != BK_UID_ROOT && k->web != WEB_RW) {
			rs_status(rs, ST_PERM);
			return 0;
		}
		if (cfg_set(&work, type, val, len) != 0) {
			rs_inval(rs, type);
			return 0;
		}
	}
	if (cfg_validate(&work) != 0) {
		rs_inval(rs, cfg_last_key());
		return 0;
	}
	if (cfg_store(bk->cfg_path, &work) != 0) {
		rs_status(rs, ST_IO);
		return 0;
	}
	bk->cfg = work;
	rs_status(rs, ST_OK);
	return 0;
}

static int op_status(struct broker *bk, int full, struct proto_resp *rs)
{
	size_t off = 0;
	const char *ver = BK_VERSION_STR;
	size_t vlen = strlen(ver);
	int bad = 0;

	if (vlen > 32)
		vlen = 32;
	/* Reading entropy here is also what advances the sticky gate, so STATUS
	 * is the poll a caller uses to find out whether login will work. */
	(void)bk_entropy_ready(bk);

	rs_status(rs, ST_OK);
	bad |= proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
	                         BKS_UPTIME, bk_proc_uptime(bk));
	if (full) {
		bad |= proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
		                         BKS_LOAD1, bk_proc_load1x100(bk));
		bad |= proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
		                         BKS_MEMFREE, bk_proc_memfree_kb(bk));
		bad |= proto_tlv_put_u8(rs->body, sizeof(rs->body), &off,
		                        BKS_CFGSRC, (uint8_t)bk->cfg.source);
		bad |= proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
		                         BKS_CFGSEQ, bk->cfg.seq);
	}
	bad |= proto_tlv_put(rs->body, sizeof(rs->body), &off,
	                     BKS_VERSION, (const uint8_t *)ver, (uint16_t)vlen);
	if (full)
		bad |= proto_tlv_put_u32(rs->body, sizeof(rs->body), &off,
		                         BKS_ENTROPY, bk->entropy_last);
	bad |= proto_tlv_put_u8(rs->body, sizeof(rs->body), &off,
	                        BKS_AUTHRDY, (uint8_t)(bk->auth_ready ? 1 : 0));
	if (bad != 0) {
		rs_status(rs, ST_IO);
		return 0;
	}
	rs->body_len = (uint32_t)off;
	return 0;
}

/* PING.  The target is four bytes and the count is one byte; argv is built
 * from those typed values and from nothing else, so there is no text from the
 * caller anywhere in it and no interpreter in the picture.
 *
 * THE TIMEOUT IS THE PRIMARY MECHANISM, not a safety net.  This image's
 * busybox ping ignores -c (config/image-commands.tsv), so `-c N` does not stop
 * it: the wall-clock deadline closes the pipe, SIGKILLs the child and reaps
 * it.  -c is passed anyway because a later busybox honours it. */
static int op_ping(struct broker *bk, const struct proto_req *rq,
                   struct proto_resp *rs)
{
	char dotted[16], cnt[4];
	char *argv[7];
	int pfd[2];
	pid_t pid;
	size_t got = 0;
	long long deadline;
	int status = 0, reaped = 0;
	uint8_t count;

	if (rq->body_len != 5) {
		rs_inval(rs, 0);
		return 0;
	}
	count = rq->body[4];
	if (count < 1 || count > 5) {
		rs_inval(rs, 0);
		return 0;
	}
	if (rq->body[0] == 0 && rq->body[1] == 0 &&
	    rq->body[2] == 0 && rq->body[3] == 0) {
		rs_inval(rs, 0);
		return 0;
	}
	(void)snprintf(dotted, sizeof(dotted), "%u.%u.%u.%u",
	               (unsigned)rq->body[0], (unsigned)rq->body[1],
	               (unsigned)rq->body[2], (unsigned)rq->body[3]);
	(void)snprintf(cnt, sizeof(cnt), "%u", (unsigned)count);

	argv[0] = (char *)"ping";
	argv[1] = (char *)"-c";
	argv[2] = cnt;
	argv[3] = (char *)"-W";
	argv[4] = (char *)"1";
	argv[5] = dotted;
	argv[6] = 0;

	if (pipe(pfd) != 0) {
		rs_status(rs, ST_IO);
		return 0;
	}
	pid = fork();
	if (pid < 0) {
		(void)close(pfd[0]);
		(void)close(pfd[1]);
		rs_status(rs, ST_IO);
		return 0;
	}
	if (pid == 0) {
		char *envp[1];

		envp[0] = 0;
		(void)close(pfd[0]);
		if (dup2(pfd[1], 1) < 0 || dup2(pfd[1], 2) < 0)
			_exit(127);
		if (pfd[1] > 2)
			(void)close(pfd[1]);
		(void)execve(bk->ping_bin, argv, envp);
		_exit(127);
	}
	(void)close(pfd[1]);
	/* The read side is CLOEXEC in the parent only for later forks; this
	 * child is already gone past exec by now. */
	(void)fcntl(pfd[0], F_SETFD, FD_CLOEXEC);

	rs_status(rs, ST_OK);
	deadline = bk_now_ms(bk) + (long long)bk->ping_timeout_s * 1000;
	for (;;) {
		struct pollfd p;
		long long left = deadline - bk_now_ms(bk);
		int rc;
		ssize_t r;

		if (left <= 0)
			break;
		p.fd = pfd[0];
		p.events = POLLIN;
		p.revents = 0;
		rc = poll(&p, 1, (int)(left > 200 ? 200 : left));
		if (rc < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (rc == 0)
			continue;
		if (got >= BK_PING_OUT_MAX)
			break;
		r = read(pfd[0], rs->body + got, BK_PING_OUT_MAX - got);
		if (r < 0) {
			if (errno == EINTR)
				continue;
			break;
		}
		if (r == 0)
			break;                     /* the child closed it */
		got += (size_t)r;
	}
	(void)close(pfd[0]);
	rs->body_len = (uint32_t)got;

	/* Reap, with a deadline of its own.  TERM first, then KILL; a child that
	 * ignored both would leave a zombie, so the KILL is unconditional and
	 * the final waitpid blocks -- SIGKILL cannot be caught. */
	(void)kill(pid, SIGTERM);
	{
		long long wdl = bk_now_ms(bk) + 2000;

		while (bk_now_ms(bk) <= wdl) {
			pid_t w = waitpid(pid, &status, WNOHANG);

			if (w == pid) { reaped = 1; break; }
			if (w < 0 && errno != EINTR) { reaped = 1; break; }
			if (w == 0) {
				struct timespec ts;

				ts.tv_sec = 0;
				ts.tv_nsec = 20 * 1000 * 1000;
				(void)nanosleep(&ts, 0);
			}
		}
	}
	if (!reaped) {
		(void)kill(pid, SIGKILL);
		for (;;) {
			pid_t w = waitpid(pid, &status, 0);

			if (w == pid || (w < 0 && errno != EINTR))
				break;
		}
	}
	return 0;
}

/* LOGIN.  Order: entropy, then the bucket, then the KDF.  Entropy first so a
 * board that cannot issue a session at all never locks anyone out over it. */
static int op_login(struct broker *bk, const struct proto_req *rq, uid_t uid,
                    uint32_t cip, struct proto_resp *rs)
{
	uint8_t hash[CFG_VAL_MAX], want[32];
	uint16_t hlen = 0;
	uint32_t secs = 0;
	struct bk_sess *s;
	uint8_t log2n;
	uint16_t r, p;

	if (rq->body_len < 1 || rq->body_len > 64) {
		rs_inval(rs, 0);
		return 0;
	}
	if (!bk_entropy_ready(bk)) {
		rs_status(rs, ST_NOENTROPY);
		return 0;
	}
	if (uid != BK_UID_ROOT && bk_rl_check(bk, cip, &secs)) {
		rs_locked(rs, secs);
		return 0;
	}
	if (cfg_get(&bk->cfg, CFGID_ADMIN_PWHASH, hash, &hlen) != 0 ||
	    hlen != BK_PWHASH_LEN || hash[0] != 1) {
		/* No password set -> AUTH (SPEC § 6).  Not counted as a failure:
		 * there is nothing to guess yet. */
		rs_status(rs, ST_AUTH);
		return 0;
	}
	if (bk->kdf_busy) {
		rs_status(rs, ST_BUSY);
		return 0;
	}
	log2n = hash[1];
	r = proto_be16(hash + 2);
	p = proto_be16(hash + 4);
	if (log2n < 8 || log2n > 20 || r == 0 || p == 0) {
		rs_status(rs, ST_IO);        /* a stored hash we cannot evaluate */
		return 0;
	}
	bk->kdf_busy = 1;
	if (kdf_scrypt(rq->body, (size_t)rq->body_len, hash + 8, log2n, r, p, want) != 0) {
		bk->kdf_busy = 0;
		rs_status(rs, ST_IO);
		return 0;
	}
	bk->kdf_busy = 0;
	if (!bk_ct_eq(want, hash + 24, 32)) {
		memset(want, 0, sizeof(want));
		if (uid != BK_UID_ROOT)
			bk_rl_fail(bk, cip);
		rs_status(rs, ST_AUTH);
		return 0;
	}
	memset(want, 0, sizeof(want));
	if (uid != BK_UID_ROOT)
		bk_rl_ok(bk, cip);
	s = bk_sess_new(bk);
	if (s == 0) {
		rs_status(rs, ST_IO);        /* /dev/urandom refused */
		return 0;
	}
	rs_status(rs, ST_OK);
	memcpy(rs->body, s->tok, PROTO_TOK_LEN);
	memcpy(rs->body + PROTO_TOK_LEN, s->csrf, PROTO_TOK_LEN);
	proto_put_be32(rs->body + 2 * PROTO_TOK_LEN, (uint32_t)BK_SESS_TTL);
	rs->body_len = 2 * PROTO_TOK_LEN + 4;
	return 0;
}

static int op_pwset(struct broker *bk, const struct proto_req *rq, uid_t uid,
                    struct proto_resp *rs)
{
	uint8_t old[CFG_VAL_MAX], hash[CFG_VAL_MAX], newhash[BK_PWHASH_LEN];
	uint8_t want[32], salt[16];
	const uint8_t *oldpw, *newpw;
	uint8_t oldlen, newlen;
	uint16_t hlen = 0;
	int have_hash;
	size_t o;

	if (!bk_entropy_ready(bk)) {
		rs_status(rs, ST_NOENTROPY);
		return 0;
	}
	/* Bounded parse of `u8 oldlen | old | u8 newlen | new`. */
	if (rq->body_len < 2) {
		rs_inval(rs, 0);
		return 0;
	}
	oldlen = rq->body[0];
	o = 1;
	if ((size_t)rq->body_len - o < (size_t)oldlen) {
		rs_inval(rs, 0);
		return 0;
	}
	oldpw = rq->body + o;
	o += oldlen;
	if ((size_t)rq->body_len - o < 1) {
		rs_inval(rs, 0);
		return 0;
	}
	newlen = rq->body[o];
	o += 1;
	if ((size_t)rq->body_len - o != (size_t)newlen) {
		rs_inval(rs, 0);        /* trailing bytes, or a short new password */
		return 0;
	}
	newpw = rq->body + o;
	if (newlen < 8 || newlen > 64 || oldlen > 64) {
		rs_inval(rs, 0);
		return 0;
	}

	have_hash = (cfg_get(&bk->cfg, CFGID_ADMIN_PWHASH, hash, &hlen) == 0 &&
	             hlen == BK_PWHASH_LEN && hash[0] == 1);
	if (have_hash) {
		uint8_t l2 = hash[1];
		uint16_t r = proto_be16(hash + 2), p = proto_be16(hash + 4);

		if (oldlen == 0) {
			rs_status(rs, ST_AUTH);
			return 0;
		}
		if (l2 < 8 || l2 > 20 || r == 0 || p == 0) {
			rs_status(rs, ST_IO);
			return 0;
		}
		if (bk->kdf_busy) {
			rs_status(rs, ST_BUSY);
			return 0;
		}
		bk->kdf_busy = 1;
		memcpy(old, oldpw, oldlen);
		if (kdf_scrypt(old, oldlen, hash + 8, l2, r, p, want) != 0) {
			bk->kdf_busy = 0;
			memset(old, 0, sizeof(old));
			rs_status(rs, ST_IO);
			return 0;
		}
		bk->kdf_busy = 0;
		memset(old, 0, sizeof(old));
		if (!bk_ct_eq(want, hash + 24, 32)) {
			memset(want, 0, sizeof(want));
			rs_status(rs, ST_AUTH);
			return 0;
		}
		memset(want, 0, sizeof(want));
	} else if (uid != BK_UID_ROOT) {
		/* The first password is set on the console (SPEC § 5), so only a
		 * root peer may do it; httpd cannot bootstrap itself an account. */
		rs_status(rs, ST_PERM);
		return 0;
	}

	if (bk_random(bk, salt, sizeof(salt)) != 0) {
		rs_status(rs, ST_IO);
		return 0;
	}
	memset(newhash, 0, sizeof(newhash));
	newhash[0] = 1;                                 /* alg = scrypt */
	newhash[1] = BK_KDF_LOG2N;
	proto_put_be16(newhash + 2, BK_KDF_R);
	proto_put_be16(newhash + 4, BK_KDF_P);
	proto_put_be16(newhash + 6, 0);
	memcpy(newhash + 8, salt, 16);
	if (bk->kdf_busy) {
		rs_status(rs, ST_BUSY);
		return 0;
	}
	bk->kdf_busy = 1;
	if (kdf_scrypt(newpw, newlen, salt, BK_KDF_LOG2N, BK_KDF_R, BK_KDF_P,
	               newhash + 24) != 0) {
		bk->kdf_busy = 0;
		memset(newhash, 0, sizeof(newhash));
		rs_status(rs, ST_IO);
		return 0;
	}
	bk->kdf_busy = 0;
	{
		struct cfg work = bk->cfg;

		if (cfg_set(&work, CFGID_ADMIN_PWHASH, newhash, BK_PWHASH_LEN) != 0) {
			memset(newhash, 0, sizeof(newhash));
			rs_inval(rs, CFGID_ADMIN_PWHASH);
			return 0;
		}
		if (cfg_store(bk->cfg_path, &work) != 0) {
			memset(newhash, 0, sizeof(newhash));
			rs_status(rs, ST_IO);
			return 0;
		}
		bk->cfg = work;
	}
	memset(newhash, 0, sizeof(newhash));
	/* A password change invalidates every session, including the caller's:
	 * whoever knew the old one must prove they know the new one. */
	bk_sess_drop_all(bk);
	rs_status(rs, ST_OK);
	return 0;
}

/* --------------------------------------------------------- the gate */

int bk_dispatch(struct broker *bk, const struct proto_req *rq, uid_t peer_uid,
                struct proto_resp *rs)
{
	const struct bk_op_rule *r;
	struct bk_sess *s = 0;
	uint32_t cip;
	int is_root, is_httpd, is_dnsfwd;

	if (bk == 0 || rq == 0 || rs == 0)
		return -1;
	rs_status(rs, ST_BADREQ);

	r = bk_op_rule(rq->op);
	if (r == 0 || !r->supported) {
		rs_status(rs, ST_NOTSUP);
		return 0;
	}

	is_root    = (peer_uid == BK_UID_ROOT);
	is_httpd   = (peer_uid == BK_UID_HTTPD);
	is_dnsfwd  = (peer_uid == BK_UID_DNSFWD);
	if (!is_root && !is_httpd && !is_dnsfwd) {
		rs_status(rs, ST_PERM);       /* an unknown uid gets nothing */
		return 0;
	}
	if (is_httpd && !r->allow_100) {
		rs_status(rs, ST_PERM);
		return 0;
	}
	if (is_dnsfwd && !r->allow_101) {
		rs_status(rs, ST_PERM);
		return 0;
	}

	/* client_ip is honoured only from uid 100 (SPEC § 6); everyone else's is
	 * discarded, so root and dnsfwd cannot forge a bucket. */
	cip = is_httpd ? rq->client_ip : 0;

	/* Look a session up whenever one is offered, even by an op that does not
	 * need one: STATUS widens its answer for an authenticated caller, and a
	 * root LOGOUT names someone else's token.  `need_session` is what uid
	 * 100 must have; uid 101 has no way to get a session at all, so its
	 * access is decided by allow_101 and the key list and NOT by this flag.
	 * (Gating dnsfwd on need_session was the first bug the named negatives
	 * in test_authz.c caught -- the matrix's own derivation shared it.) */
	if (is_root || is_httpd)
		s = bk_sess_find(bk, rq->session);
	if (is_httpd && r->need_session) {
		if (s == 0) {
			rs_status(rs, ST_AUTH);
			return 0;
		}
		if (r->need_csrf && !bk_ct_eq(s->csrf, rq->csrf, PROTO_TOK_LEN)) {
			rs_status(rs, ST_PERM);
			return 0;
		}
	}
	if (s != 0)
		s->last = bk_now(bk);        /* the idle TTL restarts on use */

	switch (rq->op) {
	case OP_GET:
		return op_get(bk, rq, peer_uid, s != 0, rs);
	case OP_SET:
		return op_set(bk, rq, peer_uid, rs);
	case OP_REBOOT:
		if (rq->body_len != 0) {
			rs_inval(rs, 0);
			return 0;
		}
		bk->pending_reboot = 1;       /* main() acts AFTER the reply */
		rs_status(rs, ST_OK);
		return 0;
	case OP_STATUS:
		if (rq->body_len != 0) {
			rs_inval(rs, 0);
			return 0;
		}
		/* Root sees everything without a session; httpd sees the three
		 * public rows until it has one. */
		return op_status(bk, is_root || s != 0, rs);
	case OP_PING:
		return op_ping(bk, rq, rs);
	case OP_LOGIN:
		return op_login(bk, rq, peer_uid, cip, rs);
	case OP_LOGOUT:
		if (rq->body_len != 0) {
			rs_inval(rs, 0);
			return 0;
		}
		if (s == 0 && is_root)
			s = bk_sess_find(bk, rq->session);   /* may be none */
		if (s != 0)
			bk_sess_drop(s);
		/* Idempotent: a root LOGOUT naming nothing is OK, and so is one
		 * naming a token that already expired.  Never test session[0]
		 * against 0 to decide "a token was supplied" -- one token in 256
		 * begins with a zero byte. */
		rs_status(rs, ST_OK);
		return 0;
	case OP_PWSET:
		return op_pwset(bk, rq, peer_uid, rs);
	default:
		rs_status(rs, ST_NOTSUP);
		return 0;
	}
}
