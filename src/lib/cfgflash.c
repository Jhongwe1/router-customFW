/* cfgflash.c -- the config store's flash backend: a slot read through
 * /dev/mtd2ro, a slot written through rtl819x-spi's install path.  The design
 * is notes/self-update.md §§ 3.1-3.3; every byte that reaches /proc or /dev
 * goes through src/lib/spictl.c.
 *
 * ---------------------------------------------------------------------------
 * THE WRITE, AND WHY EACH CHECK IS WHERE IT IS
 * ---------------------------------------------------------------------------
 *
 * The verbs are spelled as rtl819x-spi.c's write_proc and the install
 * header's parser read them (`disarm`, `img reset`, `arm <lo> <hi> <budget>`
 * with simple_strtoul base 0, `install <region> sha=<64 hex>`, single spaces,
 * nothing trailing), and the region names are the table's, `cfg0` and `cfg1`.
 *
 *   disarm, img reset    no arm and no staged byte from an earlier writer
 *                        survives into this one (the lock is held, so no
 *                        writer is mid-sequence)
 *   stage 4,096          spictl_stage: one write(2) here, at the chunk size
 *   img_len, img_err     read AFTER the stage, each from its own read of
 *                        /proc/rtl819x-spi-inst (spictl_dev.state, the node
 *                        that fits one read): a staging the kernel did not
 *                        take whole stops
 *                        the sequence before anything is armed
 *   n_writes             noted after the stage and before the arm, so the
 *                        delta below spans exactly the install
 *   arm, install         the arm is the region exactly (the kernel refuses
 *                        anything else, ARM_WINDOW); the digest is this
 *                        writer's sha256 of its own buffer, so a staging that
 *                        is not that buffer is the kernel's SHA refusal
 *   inst_*, n_writes     the kernel's own verdict, re-read: OK, the read-back
 *                        compare ran clean, and 32 flash operations (16 SE + 16
 *                        PP, the install header's plan for 4,096 bytes in a
 *                        64 KiB region), not 31 and not 33
 *   img reset            frees the staging buffer
 *
 * A deviation anywhere is -CFGE_IO with the step and the reason logged, and is
 * followed by ONE verb, `img reset`, and nothing else: no arm after a bad
 * staging, no second install, no retry.  What the cleanup cannot undo it does
 * not try to: an install that failed after its first erase has erased the
 * slot, which then reads as absent or corrupt, and cfg_store wrote it only
 * because it was not the slot holding the selected record.
 *
 * The one residue: if `arm` succeeded and the install line never reached the
 * handler (its own open(2) failed), the arm stays in force until the next
 * writer's first verb, which is `disarm`.  An install needs an arm equal to
 * the region and staged bytes matching a typed digest, so a stale arm is not
 * a write; it is recorded here rather than covered by a second cleanup verb.
 */

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "cfg.h"
#include "sha256.h"
#include "spictl.h"

/* "<step>: <detail>" of the last deviation, or "" (cfg_flash_why). */
static char cf_reason[192];

const char *cfg_flash_why(void)
{
	return cf_reason;
}

static uint32_t cf_base(int s)
{
	return (s == 0) ? CFG_FLASH_OFF0 : CFG_FLASH_OFF1;
}

/* Records the deviation and puts one line on fd 2, which is the console for
 * every caller this has (init's stdio_init, brokerd's and cfgstore's
 * stderr).  No stdio stream: snprintf into a buffer and one write(2). */
static int cf_fail(int s, const char *step, const char *detail)
{
	char line[sizeof cf_reason + 40];
	ssize_t w;
	int n;

	(void)snprintf(cf_reason, sizeof cf_reason, "%s: %s", step, detail);
	if (s == 0 || s == 1)
		n = snprintf(line, sizeof line, "rlxfw: cfgflash: cfg%d: %s\n",
			     s, cf_reason);
	else
		n = snprintf(line, sizeof line, "rlxfw: cfgflash: %s\n",
			     cf_reason);
	if (n > 0) {
		size_t len = ((size_t)n < sizeof line) ? (size_t)n
							: sizeof line - 1;

		w = write(2, line, len);
		(void)w;
	}
	return -CFGE_IO;
}

static int cf_fail_errno(int s, const char *step, int rc)
{
	char d[32];

	(void)snprintf(d, sizeof d, "errno %d", (rc < 0) ? -rc : rc);
	return cf_fail(s, step, d);
}

/* After the lock is held and a verb may have been sent: the deviation, then
 * the one cleanup verb.  Its own failure is logged and changes nothing. */
static int cf_abort(int s, const char *step, const char *detail)
{
	int rc;

	(void)cf_fail(s, step, detail);
	rc = spictl_verb(&spictl_dev, "img reset");
	if (rc != 0) {
		char line[64];
		ssize_t w;
		int n = snprintf(line, sizeof line,
				 "rlxfw: cfgflash: cleanup img reset: errno %d\n",
				 -rc);

		if (n > 0 && (size_t)n < sizeof line) {
			w = write(2, line, (size_t)n);
			(void)w;
		}
	}
	return -CFGE_IO;
}

static int cf_abort_errno(int s, const char *step, int rc)
{
	char d[32];

	(void)snprintf(d, sizeof d, "errno %d", (rc < 0) ? -rc : rc);
	return cf_abort(s, step, d);
}

/* ------------------------------------------------------------------------- */

int cfg_flash_read_slot(int s, uint8_t *buf, size_t *got)
{
	size_t i;
	int rc;

	if (got != NULL)
		*got = 0;
	if (buf == NULL || got == NULL)
		return -CFGE_SPACE;
	if (s != 0 && s != 1)
		return cf_fail(s, "read", "no such slot");
	rc = spictl_flash_read(&spictl_dev, cf_base(s), buf,
			       (size_t)CFG_SLOT_SIZE);
	if (rc != 0)
		return cf_fail_errno(s, "read", rc);
	/* § 3.1: an erased slot is absent, not a record that failed its CRC. */
	for (i = 0; i < (size_t)CFG_SLOT_SIZE; i++)
		if (buf[i] != CFG_FILL)
			break;
	*got = (i == (size_t)CFG_SLOT_SIZE) ? 0 : (size_t)CFG_SLOT_SIZE;
	return 0;
}

int cfg_flash_lock(void)
{
	int fd;

	cf_reason[0] = '\0';
	fd = spictl_lock(&spictl_dev, CFG_FLASH_LOCK_S);
	if (fd < 0)
		return cf_fail(-1, "lock", spictl_lock_why(fd));
	return fd;
}

void cfg_flash_unlock(int fd)
{
	spictl_unlock(fd);
}

int cfg_flash_write_slot_locked(int s, const uint8_t *img)
{
	static const char hx[] = "0123456789abcdef";
	const struct spictl_paths *p = &spictl_dev;
	char line[128], v[32], d[64];
	uint8_t md[SHA256_DIGEST_LEN];
	uint32_t base, ilen = 0, nw0 = 0, nw1 = 0, x = 0;
	int rc, i, n;

	cf_reason[0] = '\0';
	if ((s != 0 && s != 1) || img == NULL)
		return cf_fail(s, "args", "slot 0 or 1 and an image");
	base = cf_base(s);

	/* 2 */
	rc = spictl_verb(p, "disarm");
	if (rc != 0)
		return cf_abort_errno(s, "disarm", rc);
	rc = spictl_verb(p, "img reset");
	if (rc != 0)
		return cf_abort_errno(s, "img reset", rc);

	/* 3 */
	rc = spictl_stage(p, img, (size_t)CFG_SLOT_SIZE);
	if (rc != 0)
		return cf_abort_errno(s, "stage", rc);

	/* 4: each field from its own read, after the step it reports on. */
	rc = spictl_field_u32(p, "img_len", &ilen);
	if (rc != 0)
		return cf_abort_errno(s, "img_len", rc);
	if (ilen != (uint32_t)CFG_SLOT_SIZE) {
		(void)snprintf(d, sizeof d, "%lu staged, want %d",
			       (unsigned long)ilen, CFG_SLOT_SIZE);
		return cf_abort(s, "img_len", d);
	}
	rc = spictl_field(p, "img_err", v, sizeof v);
	if (rc != 0)
		return cf_abort_errno(s, "img_err", rc);
	if (strcmp(v, "none") != 0)
		return cf_abort(s, "img_err", v);
	rc = spictl_field_u32(p, "n_writes", &nw0);
	if (rc != 0)
		return cf_abort_errno(s, "n_writes", rc);

	/* 5: the region exactly, budget its size. */
	n = snprintf(line, sizeof line, "arm 0x%lx 0x%lx 0x%lx",
		     (unsigned long)base,
		     (unsigned long)(base + CFG_FLASH_REGION),
		     (unsigned long)CFG_FLASH_REGION);
	if (n <= 0 || (size_t)n >= sizeof line)
		return cf_abort(s, "arm", "line");
	rc = spictl_verb(p, line);
	if (rc != 0)
		return cf_abort_errno(s, "arm", rc);

	/* 6: this writer's digest of this writer's buffer, lower-case hex. */
	if (sha256(img, (size_t)CFG_SLOT_SIZE, md) != 0)
		return cf_abort(s, "sha256", "the digest failed");
	n = snprintf(line, sizeof line, "install cfg%d sha=", s);
	if (n <= 0 || (size_t)n + 2u * SHA256_DIGEST_LEN >= sizeof line)
		return cf_abort(s, "install", "line");
	for (i = 0; i < SHA256_DIGEST_LEN; i++) {
		line[n + 2 * i] = hx[(md[i] >> 4) & 0x0Fu];
		line[n + 2 * i + 1] = hx[md[i] & 0x0Fu];
	}
	line[n + 2 * SHA256_DIGEST_LEN] = '\0';
	rc = spictl_verb(p, line);
	if (rc != 0) {
		/* The kernel's refusal or failure; its reason is in the node. */
		if (spictl_field(p, "inst_reason", v, sizeof v) != 0)
			(void)snprintf(v, sizeof v, "?");
		(void)snprintf(d, sizeof d, "errno %d, inst_reason %s", -rc, v);
		return cf_abort(s, "install", d);
	}

	/* 7: the kernel's verdict, re-read. */
	rc = spictl_field(p, "inst_reason", v, sizeof v);
	if (rc != 0)
		return cf_abort_errno(s, "inst_reason", rc);
	if (strcmp(v, "OK") != 0)
		return cf_abort(s, "inst_reason", v);
	rc = spictl_field_u32(p, "inst_cmp_ok", &x);
	if (rc != 0)
		return cf_abort_errno(s, "inst_cmp_ok", rc);
	if (x != 1u)
		return cf_abort(s, "inst_cmp_ok", "the read-back compare did not pass");
	rc = spictl_field_u32(p, "inst_cmp_diff", &x);
	if (rc != 0)
		return cf_abort_errno(s, "inst_cmp_diff", rc);
	if (x != 0u) {
		(void)snprintf(d, sizeof d, "%lu bytes differ", (unsigned long)x);
		return cf_abort(s, "inst_cmp_diff", d);
	}
	rc = spictl_field_u32(p, "n_writes", &nw1);
	if (rc != 0)
		return cf_abort_errno(s, "n_writes", rc);
	if ((uint32_t)(nw1 - nw0) != CFG_FLASH_NWRITES) {
		(void)snprintf(d, sizeof d, "moved by %lu, want %lu",
			       (unsigned long)(uint32_t)(nw1 - nw0),
			       (unsigned long)CFG_FLASH_NWRITES);
		return cf_abort(s, "n_writes", d);
	}

	/* 8: the staging buffer freed.  Its failure is the last deviation there
	 * can be, and it is not followed by anything. */
	rc = spictl_verb(p, "img reset");
	if (rc != 0)
		return cf_fail_errno(s, "img reset (last)", rc);
	return 0;
}

int cfg_flash_write_slot(int s, const uint8_t *img)
{
	int fd, rc;

	fd = cfg_flash_lock();
	if (fd < 0)
		return -CFGE_IO;
	rc = cfg_flash_write_slot_locked(s, img);
	cfg_flash_unlock(fd);
	return rc;
}
