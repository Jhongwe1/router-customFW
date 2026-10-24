/* firstpw.c -- see firstpw.h.
 *
 * ---------------------------------------------------------------------------
 * WHY IT EXISTS
 * ---------------------------------------------------------------------------
 *
 * notes/self-update.md § 3.8: the shipped image has no root shell, so
 * `cfgstore passwd` cannot be typed; admin.pwhash has no default
 * (src/lib/schema.c); with no hash every LOGIN answers AUTH and PWSET is
 * root-only (src/brokerd/ops.c op_login, op_pwset), so no browser can set the
 * first one.  Without this step a shell-less image could never get a password.
 *
 * ---------------------------------------------------------------------------
 * THE WRITE, CHOSEN ON THE STORE AS IT READS JUST BEFORE IT
 * ---------------------------------------------------------------------------
 *
 *   valid record, no hash   cfg_set + cfg_store: the ordinary write, so every
 *                           other key of the record survives and seq moves by
 *                           exactly one.
 *   no valid record         cfg_store_fresh with the defaults and the hash.
 *                           cfgstore passwd loads strictly and refuses a store
 *                           that holds bytes and no valid record
 *                           (src/cfgstore/main.c load_or_die); a shell-less
 *                           image has no `cfgstore init --force` to type, so
 *                           without this path a corrupt store would block the
 *                           first password for good.  cfg_store_fresh bases
 *                           nothing on the corrupt bytes and refuses
 *                           (-CFGE_SEQ) if a valid record appeared meanwhile.
 *   a hash                  nothing.  "Holds a hash" is the key being present
 *                           (cfg_present), whatever its bytes: stricter than
 *                           PWSET's have_hash, which also wants the alg byte 1.
 *   unreadable              nothing: whether it holds a record is unknown.
 *
 * The decision and the write are not under one hold of the flash lock --
 * cfg_store and cfg_store_fresh take it themselves, and flock(2) from a second
 * descriptor of the same file would wait on this one.  What is left between
 * the re-read and the write is a window of one function call; the only other
 * writers of a store with no hash are root processes (PWSET with no hash is
 * root-only), and a shell-less image runs none that writes the store.
 *
 * ---------------------------------------------------------------------------
 * THE SAME HASH AS THE OTHER TWO WRITERS
 * ---------------------------------------------------------------------------
 *
 * pwhash_make (src/lib/kdf.c) with KDF_LOG2N, KDF_R and KDF_P: what cfgstore
 * passwd calls, and what PWSET's BK_KDF_* alias (src/brokerd/brokerd.h).  The
 * bytes hashed are the bytes typed, trailing CRs stripped as cfgstore's
 * read_line strips them, 8..64 of them as both require.  test_firstpw.c
 * verifies the stored blob with pwhash_verify and holds its parameter bytes
 * equal to BK_KDF_*.
 *
 * ---------------------------------------------------------------------------
 * ENTROPY: WAIT, NEVER FAIL, NEVER WEAKEN
 * ---------------------------------------------------------------------------
 *
 * The salt is pwhash_salt's, which reads entropy_avail and refuses below
 * KDF_ENTROPY_MIN -- 128, brokerd's login-gate threshold (BK_ENTROPY_MIN) --
 * and never returns a weak salt.  Where cfgstore passwd gives up on that
 * refusal, this waits: one attempt a second for as long as it takes, the
 * reading on the console on the first and every 30th.  It is not brokerd's
 * sticky latch: the reading is taken again at the draw, which can only make it
 * wait longer.  On this board the pool is fed by the NIC (SPEC.md FW-179), so
 * at first boot it fills when traffic arrives.
 *
 * ---------------------------------------------------------------------------
 * ECHO
 * ---------------------------------------------------------------------------
 *
 * ECHO, ECHOE, ECHOK and ECHONL are cleared for both entries, with TCSAFLUSH
 * (what was typed before the prompt is dropped), and the mode is READ BACK
 * before the first byte is read: tcsetattr() returns 0 when any one of the
 * requested changes took (POSIX), so its return is not the proof.  If echo
 * cannot be shown off, no password is read.  A descriptor that is not a tty --
 * the host test's pipe -- echoes nothing and is read as it is.
 */

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#include "firstpw.h"
#include "kdf.h"
#include "schema.h"

#define FP_LINE_OK	0
#define FP_LINE_EOF	(-1)
#define FP_LINE_LONG	(-2)

static void fp_wipe(void *p, size_t n)
{
	volatile unsigned char *q = (volatile unsigned char *)p;

	while (n > 0) {
		*q = 0;
		q++;
		n--;
	}
}

/* One write(2) per line, so a daemon's own line cannot split it. */
static void fp_put(const struct fp_env *e, const char *s, int nl)
{
	char b[FP_LINE_MAX + 1];
	size_t n = strlen(s);
	ssize_t w;

	if (n > (size_t)FP_LINE_MAX - 1u)
		n = (size_t)FP_LINE_MAX - 1u;
	memcpy(b, s, n);
	if (nl)
		b[n++] = '\n';
	if (n == 0)
		return;
	w = write(e->out_fd, b, n);
	(void)w;	/* a console that cannot be written is not a reason to stop */
}

static void fp_say(const struct fp_env *e, const char *s)
{
	fp_put(e, s, 1);
}

/* ------------------------------------------------------------------------- */
/* The console                                                               */
/* ------------------------------------------------------------------------- */

static int fp_echo_off(int fd, struct termios *saved, int *tty)
{
	struct termios t;

	*tty = isatty(fd) ? 1 : 0;
	if (!*tty)
		return 0;
	if (tcgetattr(fd, saved) != 0)
		return -1;
	t = *saved;
	t.c_lflag &= ~(tcflag_t)(ECHO | ECHOE | ECHOK | ECHONL);
	t.c_lflag |= (tcflag_t)ICANON;
	if (tcsetattr(fd, TCSAFLUSH, &t) != 0)
		goto undo;
	if (tcgetattr(fd, &t) != 0 || (t.c_lflag & (tcflag_t)ECHO) != 0)
		goto undo;
	return 0;
undo:
	(void)tcsetattr(fd, TCSANOW, saved);
	return -1;
}

static void fp_echo_restore(int fd, const struct termios *saved, int tty)
{
	if (tty)
		(void)tcsetattr(fd, TCSANOW, saved);
}

/* One line, one byte per read(2), so nothing past its '\n' is consumed.  At
 * most cap bytes are kept; a longer line is read to its end and is LONG.
 * Trailing CRs are stripped, as cfgstore's read_line does, so a password set
 * here and one set there from the same keys hash the same bytes. */
static int fp_read_line(int fd, char *buf, size_t cap, size_t *len)
{
	size_t i = 0;
	int over = 0;
	ssize_t r;
	char ch;

	*len = 0;
	for (;;) {
		r = read(fd, &ch, 1);
		if (r < 0 && errno == EINTR)
			continue;
		if (r != 1)
			return FP_LINE_EOF;	/* the console is gone */
		if (ch == '\n')
			break;
		if (i < cap)
			buf[i++] = ch;
		else
			over = 1;
	}
	while (i > 0 && buf[i - 1] == '\r')
		i--;
	*len = i;
	return over ? FP_LINE_LONG : FP_LINE_OK;
}

/* ------------------------------------------------------------------------- */
/* The store                                                                 */
/* ------------------------------------------------------------------------- */

static int fp_has_hash(const struct cfg *c)
{
	return cfg_present(c, CFGID_ADMIN_PWHASH) == 1;
}

int fp_offer(int load_rc, const struct cfg *c)
{
	if (load_rc != 0 || c == NULL)
		return FP_OFFER_UNREADABLE;
	return fp_has_hash(c) ? FP_OFFER_NO : FP_OFFER_YES;
}

static const char *fp_why(const char *store)
{
	const char *w = cfg_is_flash(store) ? cfg_flash_why() : cfg_file_why();

	return w != NULL ? w : "";
}

static int fp_store(const struct fp_env *e, const uint8_t blob[PWHASH_LEN])
{
	struct cfg cur;
	struct cfg_store_info info;
	char line[FP_LINE_MAX];
	unsigned long was_seq;
	int rc, was_slot;

	rc = cfg_load_info(e->store, &cur, &info);
	if (rc != 0) {
		(void)snprintf(line, sizeof line, "rlxfw: firstpw: FAILED: the "
			       "store could not be read (%s%s%s); nothing written",
			       cfg_strerror(rc), *fp_why(e->store) ? ": " : "",
			       fp_why(e->store));
		fp_say(e, line);
		return FP_R_IO;
	}

	if (info.selected != 0) {
		was_slot = cur.source - 1;
		was_seq = (unsigned long)cur.seq;
		if (fp_has_hash(&cur)) {
			(void)snprintf(line, sizeof line, "rlxfw: firstpw: a "
				       "password is already set (slot %d, seq %lu); "
				       "nothing written", was_slot, was_seq);
			fp_say(e, line);
			return FP_R_HASHED;
		}
		rc = cfg_set(&cur, CFGID_ADMIN_PWHASH, blob, PWHASH_LEN);
		if (rc == 0)
			rc = cfg_store(e->store, &cur);
		if (rc != 0) {
			fp_wipe(&cur, sizeof cur);
			(void)snprintf(line, sizeof line, "rlxfw: firstpw: FAILED: "
				       "cfg_store: %s%s%s", cfg_strerror(rc),
				       *fp_why(e->store) ? ": " : "",
				       fp_why(e->store));
			fp_say(e, line);
			return FP_R_IO;
		}
		(void)snprintf(line, sizeof line, "rlxfw: firstpw: admin.pwhash "
			       "set through cfg_store: the record of slot %d seq "
			       "%lu, the hash added, written as slot %d seq %lu",
			       was_slot, was_seq, cur.source - 1,
			       (unsigned long)cur.seq);
		fp_wipe(&cur, sizeof cur);
		fp_say(e, line);
		return FP_R_SET_STORE;
	}

	/* Neither slot holds a valid record. */
	rc = cfg_defaults(&cur);
	if (rc == 0)
		rc = cfg_set(&cur, CFGID_ADMIN_PWHASH, blob, PWHASH_LEN);
	if (rc == 0)
		rc = cfg_store_fresh(e->store, &cur);
	if (rc != 0) {
		fp_wipe(&cur, sizeof cur);
		(void)snprintf(line, sizeof line, "rlxfw: firstpw: FAILED: "
			       "cfg_store_fresh: %s%s%s", cfg_strerror(rc),
			       *fp_why(e->store) ? ": " : "", fp_why(e->store));
		fp_say(e, line);
		return FP_R_IO;
	}
	(void)snprintf(line, sizeof line, "rlxfw: firstpw: admin.pwhash set "
		       "through cfg_store_fresh: the defaults and the hash written "
		       "as slot %d seq %lu; the store held %s", cur.source - 1,
		       (unsigned long)cur.seq,
		       info.file_bytes == 0 ? "no record"
					    : "bytes but no valid record");
	fp_wipe(&cur, sizeof cur);
	fp_say(e, line);
	return FP_R_SET_FRESH;
}

/* ------------------------------------------------------------------------- */
/* The step                                                                  */
/* ------------------------------------------------------------------------- */

int fp_run(const struct fp_env *e)
{
	char pw[FP_PW_MAX + 1], pw2[FP_PW_MAX + 1], line[FP_LINE_MAX];
	uint8_t salt[KDF_SALT_LEN], blob[PWHASH_LEN];
	struct termios saved;
	size_t n1 = 0, n2 = 0;
	int tty = 0, r1, r2, rc;
	long k;

	if (e == NULL || e->store == NULL || e->entropy == NULL ||
	    e->salt == NULL || e->sleep_ms == NULL)
		return FP_R_IO;
	memset(&saved, 0, sizeof saved);
	(void)snprintf(line, sizeof line, "rlxfw: firstpw: no admin password is "
		       "set; set one on this console (%d..%d bytes, not echoed)",
		       FP_PW_MIN, FP_PW_MAX);
	fp_say(e, line);

	/* The password, twice, with echo off across both entries: turning it
	 * back on between them would echo a second entry typed ahead. */
	for (;;) {
		if (fp_echo_off(e->in_fd, &saved, &tty) != 0) {
			fp_say(e, "rlxfw: firstpw: REFUSED: the console's echo "
				  "could not be turned off, so no password is "
				  "read; nothing written");
			return FP_R_TTY;
		}
		fp_put(e, "rlxfw: firstpw: new password: ", 0);
		r1 = fp_read_line(e->in_fd, pw, FP_PW_MAX, &n1);
		fp_put(e, "", 1);	/* the Enter was not echoed */
		r2 = FP_LINE_OK;
		n2 = 0;
		if (r1 == FP_LINE_OK && n1 >= FP_PW_MIN) {
			fp_put(e, "rlxfw: firstpw: the same again: ", 0);
			r2 = fp_read_line(e->in_fd, pw2, FP_PW_MAX, &n2);
			fp_put(e, "", 1);
		}
		fp_echo_restore(e->in_fd, &saved, tty);

		if (r1 == FP_LINE_EOF || r2 == FP_LINE_EOF) {
			fp_wipe(pw, sizeof pw);
			fp_wipe(pw2, sizeof pw2);
			fp_say(e, "rlxfw: firstpw: the console's input ended; "
				  "nothing written");
			return FP_R_EOF;
		}
		if (r1 == FP_LINE_LONG || r2 == FP_LINE_LONG) {
			fp_say(e, "rlxfw: firstpw: longer than 64 bytes; nothing "
				  "written, asking again");
		} else if (n1 < FP_PW_MIN) {
			fp_say(e, "rlxfw: firstpw: fewer than 8 bytes; nothing "
				  "written, asking again");
		} else if (n1 != n2 || memcmp(pw, pw2, n1) != 0) {
			fp_say(e, "rlxfw: firstpw: the two entries differ; "
				  "nothing written, asking again");
		} else {
			break;
		}
		fp_wipe(pw, sizeof pw);
		fp_wipe(pw2, sizeof pw2);
	}
	fp_wipe(pw2, sizeof pw2);

	/* The salt: pwhash_salt refuses a short pool; wait it out. */
	for (k = 0;; k++) {
		rc = e->salt(e->ctx, salt);
		if (rc == 0)
			break;
		if (rc != -KDFE_ENTROPY) {
			fp_wipe(pw, sizeof pw);
			(void)snprintf(line, sizeof line, "rlxfw: firstpw: FAILED: "
				       "no salt (%s); nothing written",
				       rc == -KDFE_IO ? "/dev/urandom or "
							"entropy_avail unreadable"
						      : "the KDF's own error");
			fp_say(e, line);
			return FP_R_KDF;
		}
		if (k % FP_WAIT_SAY_EVERY == 0) {
			(void)snprintf(line, sizeof line, "rlxfw: firstpw: waiting "
				       "for entropy before the salt is drawn: "
				       "entropy_avail=%d, %d needed",
				       e->entropy(e->ctx), KDF_ENTROPY_MIN);
			fp_say(e, line);
		}
		e->sleep_ms(e->ctx, FP_WAIT_STEP_MS);
	}

	(void)snprintf(line, sizeof line, "rlxfw: firstpw: deriving the hash "
		       "(scrypt log2N=%d r=%d p=%d)", KDF_LOG2N, KDF_R, KDF_P);
	fp_say(e, line);
	rc = pwhash_make((const uint8_t *)pw, n1, KDF_LOG2N, KDF_R, KDF_P, salt,
			 blob);
	fp_wipe(pw, sizeof pw);
	fp_wipe(salt, sizeof salt);
	if (rc != 0) {
		fp_wipe(blob, sizeof blob);
		(void)snprintf(line, sizeof line, "rlxfw: firstpw: FAILED: the KDF "
			       "refused (-%d); nothing written", -rc);
		fp_say(e, line);
		return FP_R_KDF;
	}
	rc = fp_store(e, blob);
	fp_wipe(blob, sizeof blob);
	return rc;
}

/* ------------------------------------------------------------------------- */
/* The device's environment                                                  */
/* ------------------------------------------------------------------------- */

static int fp_dev_entropy(void *ctx)
{
	(void)ctx;
	return kdf_entropy_avail();
}

static int fp_dev_salt(void *ctx, uint8_t salt[16])
{
	(void)ctx;
	return pwhash_salt(salt);
}

static void fp_dev_sleep(void *ctx, long ms)
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

void fp_env_dev(struct fp_env *e, int in_fd, int out_fd, const char *store)
{
	memset(e, 0, sizeof *e);
	e->in_fd = in_fd;
	e->out_fd = out_fd;
	e->store = store;
	e->entropy = fp_dev_entropy;
	e->salt = fp_dev_salt;
	e->sleep_ms = fp_dev_sleep;
	e->ctx = NULL;
}
