/* spictl.c -- the client layer spictl.h declares.  Single-threaded callers
 * (SPEC-R7 § 2), no allocation, no stdio stream: every buffer is on the stack
 * and bounded by a constant in spictl.h.
 *
 * ---------------------------------------------------------------------------
 * WHY EACH CALL OPENS AND CLOSES ITS OWN FILE
 * ---------------------------------------------------------------------------
 *
 * The /proc files keep no per-open state: write_proc ignores the offset and
 * read_proc regenerates the whole page on every call.  Holding an fd across
 * calls would buy nothing and would hand a forked child a descriptor it did not
 * ask for, so every call is open, one operation, close -- which is also what
 * makes "exactly one write(2) per verb" a property of one function body rather
 * than of every caller's discipline.
 *
 * ---------------------------------------------------------------------------
 * THE READ GUARD RUNS BEFORE ANYTHING ELSE
 * ---------------------------------------------------------------------------
 *
 * spictl_flash_read() refuses a range touching [0, SPICTL_GUARD_HI) before it
 * opens the device, before it looks at alignment and before it looks at the
 * caller's pointers, so no sequence of other checks can reach past it.  The
 * driver itself has no such rule for READS (rtl819x_spi_mtd_read takes any
 * aligned in-chip range); this is the userspace half of SPEC-S144-U § 5's
 * "never read [0, 0x10000) of flash from userspace".  An access starting
 * below the floor is refused even when it is empty: being stricter than the
 * set arithmetic costs nothing here and removes the empty-range special case.
 *
 * lseek + read, not pread: cfg.c's reason (uClibc 0.9.30 is the target libc,
 * and a loop written here is one fewer thing to be surprised by), and the fd
 * is this call's own, so there is no shared offset for pread to protect.
 */

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/file.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include "spictl.h"

const struct spictl_paths spictl_dev = {
	"/proc/rtl819x-spi",
	"/proc/rtl819x-spi-img",
	"/run/rlxfw-flash.lock",
	"/dev/mtd2ro",
	"/proc/rtl819x-spi-inst"
};

/* ------------------------------------------------------------------------- */
/* The lock                                                                  */
/* ------------------------------------------------------------------------- */

/* 100 ms, restarted on EINTR with what is left. */
static void spictl_nap(void)
{
	struct timespec ts, rem;

	ts.tv_sec = 0;
	ts.tv_nsec = (long)SPICTL_LOCK_STEP_MS * 1000000L;
	while (nanosleep(&ts, &rem) != 0 && errno == EINTR)
		ts = rem;
}

int spictl_lock(const struct spictl_paths *p, unsigned timeout_s)
{
	unsigned long tries, i;
	int fd, e;

	if (p == NULL || p->lock == NULL)
		return -EINVAL;
	if (timeout_s > SPICTL_LOCK_MAX_S)
		timeout_s = SPICTL_LOCK_MAX_S;
	tries = (unsigned long)timeout_s * (1000ul / SPICTL_LOCK_STEP_MS);

	/* 0600: every writer is root (PID 1 mounts /run 0755, src/init/mounts.c),
	 * and a caller that is not root gets EACCES here, which is the refusal it
	 * should get -- it could not write /proc/rtl819x-spi either. */
	fd = open(p->lock, O_RDWR | O_CREAT, 0600);
	if (fd < 0)
		return -errno;
	/* A child forked while this is held must not carry the descriptor into
	 * an exec: the lock belongs to the open file description, and a
	 * long-lived inheritor would hold it long after this process let go. */
	(void)fcntl(fd, F_SETFD, FD_CLOEXEC);

	for (i = 0;; i++) {
		if (flock(fd, LOCK_EX | LOCK_NB) == 0)
			return fd;
		e = errno;
		/* EWOULDBLOCK (flock(2)'s word for "held"; EAGAIN on Linux) is
		 * someone else holding it; EINTR is counted as an attempt so that
		 * a signal storm cannot make this unbounded.  Everything else --
		 * ENOSYS above all, a kernel built without CONFIG_FILE_LOCKING --
		 * is final: waiting cannot change it. */
		if (e != EWOULDBLOCK && e != EINTR) {
			(void)close(fd);
			return -e;
		}
		if (i >= tries) {
			(void)close(fd);
			return -ETIMEDOUT;
		}
		spictl_nap();
	}
}

void spictl_unlock(int fd)
{
	if (fd < 0)
		return;
	/* Explicitly, before the close: a descriptor duplicated into a child
	 * that has not exec'd yet must not keep the lock alive. */
	(void)flock(fd, LOCK_UN);
	(void)close(fd);
}

const char *spictl_lock_why(int rc)
{
	static char other[48];

	if (rc == -ENOSYS)
		return "flock: ENOSYS, the kernel has no CONFIG_FILE_LOCKING";
	if (rc == -ETIMEDOUT)
		return "flock: held by another writer past the timeout";
	if (rc == -EACCES)
		return "lock file: EACCES (not root?)";
	(void)snprintf(other, sizeof other, "lock: errno %d", rc < 0 ? -rc : rc);
	return other;
}

/* ------------------------------------------------------------------------- */
/* Verbs and staging                                                         */
/* ------------------------------------------------------------------------- */

int spictl_verb(const struct spictl_paths *p, const char *line)
{
	size_t n;
	ssize_t w;
	int fd, e;

	if (p == NULL || p->proc == NULL || line == NULL)
		return -EINVAL;
	n = strlen(line);
	if (n == 0)
		return -EINVAL;		/* no verb is empty; refused before the open */

	fd = open(p->proc, O_WRONLY);
	if (fd < 0)
		return -errno;
	w = write(fd, line, n);
	e = errno;
	/* close(2) on procfs cannot report the verb's result -- the verb ran
	 * inside write(2) -- so its return is not the verdict. */
	(void)close(fd);
	if (w < 0)
		return -e;
	if ((size_t)w != n)
		return -EIO;		/* the handler answers all or nothing */
	return 0;
}

int spictl_stage(const struct spictl_paths *p, const void *buf, size_t len)
{
	const unsigned char *b = (const unsigned char *)buf;
	size_t done = 0;
	int fd, e;

	if (p == NULL || p->img == NULL || buf == NULL || len == 0)
		return -EINVAL;

	/* O_WRONLY and nothing else: the driver appends whatever the offset says,
	 * and O_WRONLY on a write_proc file is what init's /proc verbs measure on
	 * the device (src/init/main.c write_verbs). */
	fd = open(p->img, O_WRONLY);
	if (fd < 0)
		return -errno;
	while (done < len) {
		size_t n = len - done;
		ssize_t w;

		if (n > SPICTL_STAGE_CHUNK)
			n = SPICTL_STAGE_CHUNK;
		w = write(fd, b + done, n);
		if (w < 0) {
			e = errno;
			(void)close(fd);
			return -e;
		}
		if ((size_t)w != n) {
			/* A partial append is not retried: what is staged is
			 * now a prefix, and only `img reset` can say so. */
			(void)close(fd);
			return -EIO;
		}
		done += n;
	}
	(void)close(fd);
	return 0;
}

/* ------------------------------------------------------------------------- */
/* Fields                                                                    */
/* ------------------------------------------------------------------------- */

int spictl_field(const struct spictl_paths *p, const char *key, char *out,
		 size_t cap)
{
	char page[SPICTL_PAGE_MAX + 1];
	size_t klen, i, ls;
	ssize_t n;
	int fd, e;

	if (out != NULL && cap > 0)
		out[0] = '\0';
	if (p == NULL || p->state == NULL || key == NULL || out == NULL ||
	    cap == 0)
		return -EINVAL;
	klen = strlen(key);
	if (klen == 0)
		return -EINVAL;
	for (i = 0; i < klen; i++)
		if (key[i] == ' ' || key[i] == '\n' || key[i] == '\r')
			return -EINVAL;

	/* p->state, never p->proc: the verbs' page is longer than one read. */
	fd = open(p->state, O_RDONLY);
	if (fd < 0)
		return -errno;
	n = read(fd, page, (size_t)SPICTL_PAGE_MAX);
	e = errno;
	(void)close(fd);
	if (n < 0)
		return -e;

	/* Complete lines only: page[ls .. i) with page[i] == '\n'.  A key
	 * matches its whole first token, so `img` never matches `img_len 4096`
	 * and `n_write` never matches `n_writes 5`; the value is the rest of the
	 * line after the one space. */
	ls = 0;
	for (i = 0; i < (size_t)n; i++) {
		size_t vlen;

		if (page[i] != '\n')
			continue;
		if (i - ls > klen && page[ls + klen] == ' ' &&
		    memcmp(page + ls, key, klen) == 0) {
			vlen = i - (ls + klen + 1);
			if (vlen + 1 > cap)
				return -E2BIG;
			memcpy(out, page + ls + klen + 1, vlen);
			out[vlen] = '\0';
			return 0;
		}
		ls = i + 1;
	}
	return -ENOENT;
}

/* Strict unsigned decimal, as every counter in the page prints (%u, %lu):
 * no sign, no space, no leading zero unless the value is "0", overflow
 * refused rather than wrapped. */
int spictl_field_u32(const struct spictl_paths *p, const char *key, uint32_t *v)
{
	char s[SPICTL_U32_TEXT];
	uint32_t x = 0;
	size_t i, n;
	int rc;

	if (v == NULL)
		return -EINVAL;
	rc = spictl_field(p, key, s, sizeof s);
	if (rc != 0)
		return rc;
	n = strlen(s);
	if (n == 0 || n > 10 || (s[0] == '0' && n > 1))
		return -EINVAL;
	for (i = 0; i < n; i++) {
		uint32_t d;

		if (s[i] < '0' || s[i] > '9')
			return -EINVAL;
		d = (uint32_t)(s[i] - '0');
		if (x > (0xFFFFFFFFu - d) / 10u)
			return -ERANGE;
		x = x * 10u + d;
	}
	*v = x;
	return 0;
}

/* ------------------------------------------------------------------------- */
/* The flash read                                                            */
/* ------------------------------------------------------------------------- */

int spictl_flash_read(const struct spictl_paths *p, uint32_t off, void *buf,
		      size_t len)
{
	unsigned char *b = (unsigned char *)buf;
	size_t done = 0;
	int fd, e;

	/* THE GUARD, first: nothing below touches the device until it passed.
	 * `len > 0xFFFFFFFF - off` is the wrap test written so that it cannot
	 * itself wrap, and it also refuses a size_t above 32 bits on a 64-bit
	 * host before the cast below. */
	if (off < SPICTL_GUARD_HI)
		return -EPERM;
	if (len > (size_t)(0xFFFFFFFFu - off))
		return -EPERM;
	if (((off | (uint32_t)len) & 3u) != 0u)
		return -EINVAL;
	if (p == NULL || p->flash == NULL || (b == NULL && len != 0))
		return -EINVAL;

	fd = open(p->flash, O_RDONLY);
	if (fd < 0)
		return -errno;
	if (lseek(fd, (off_t)off, SEEK_SET) == (off_t)-1) {
		e = errno;
		(void)close(fd);
		return -e;
	}
	while (done < len) {
		ssize_t r = read(fd, b + done, len - done);

		if (r < 0) {
			if (errno == EINTR)
				continue;
			e = errno;
			(void)close(fd);
			return -e;
		}
		if (r == 0)
			break;			/* past the end: short */
		done += (size_t)r;
	}
	(void)close(fd);
	return (done == len) ? 0 : -EIO;
}
