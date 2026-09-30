/* test_mounts.c -- R7 host test for PID 1's mount table.
 *
 * The cases fall into two kinds, and the second kind is the interesting one:
 *
 *   * behaviour -- EBUSY is success, EEXIST on the mkdir is success, a required
 *     row failing raises the degraded count AND the rows after it are still
 *     attempted (nothing aborts the boot).
 *   * policy as an assertion -- the real table carries no row whose target is
 *     /dev (the devtmpfs decision), every row is MS_NOSUID|MS_NODEV, and no row
 *     passes a `size=` option, because ramfs silently ignores it on this kernel
 *     and an option that reads like a limit and is none is worse than none.
 *
 * A policy written only in a comment is a policy that the next edit deletes.
 */

#include "mounts.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

#define MF_MAX 16

struct mfake {
	int n_mkdir, n_mount;
	char mkdir_path[MF_MAX][32];
	unsigned mkdir_mode[MF_MAX];
	char mount_target[MF_MAX][32];
	char mount_fs[MF_MAX][16];
	unsigned long mount_flags[MF_MAX];
	char mount_data[MF_MAX][32];
	/* injected: a target whose mount fails, and with what */
	const char *fail_target;
	int fail_errno;
	const char *mkdir_fail_target;
	int mkdir_errno;
};

static void cpy(char *d, size_t n, const char *s)
{
	size_t i;

	for (i = 0; i + 1 < n && s != NULL && s[i] != '\0'; i++)
		d[i] = s[i];
	d[s == NULL ? 0 : i] = '\0';
}

static int f_mkdir(void *ctx, const char *path, unsigned mode)
{
	struct mfake *f = (struct mfake *)ctx;

	if (f->n_mkdir < MF_MAX) {
		cpy(f->mkdir_path[f->n_mkdir], 32, path);
		f->mkdir_mode[f->n_mkdir] = mode;
	}
	f->n_mkdir++;
	if (f->mkdir_fail_target != NULL &&
	    strcmp(path, f->mkdir_fail_target) == 0) {
		errno = f->mkdir_errno;
		return -1;
	}
	errno = EEXIST;   /* the usual case: the initramfs already has it */
	return -1;
}

static int f_mount(void *ctx, const char *src, const char *target,
		   const char *fstype, unsigned long flags, const void *data)
{
	struct mfake *f = (struct mfake *)ctx;

	(void)src;
	if (f->n_mount < MF_MAX) {
		cpy(f->mount_target[f->n_mount], 32, target);
		cpy(f->mount_fs[f->n_mount], 16, fstype);
		f->mount_flags[f->n_mount] = flags;
		cpy(f->mount_data[f->n_mount], 32, (const char *)data);
	}
	f->n_mount++;
	if (f->fail_target != NULL && strcmp(target, f->fail_target) == 0) {
		errno = f->fail_errno;
		return -1;
	}
	return 0;
}

static void mfake_init(struct mfake *f, struct mnt_ops *o)
{
	memset(f, 0, sizeof(*f));
	o->do_mkdir = f_mkdir;
	o->do_mount = f_mount;
	o->ctx = f;
}

/* ------------------------------------------------------- the table's policy */

static void t_policy(void)
{
	const struct mnt_row *rows;
	int n, i;

	rows = mnt_table(&n);
	CK(rows != NULL);
	CK(n > 0 && n <= MNT_MAX);

	/* /proc is first: everything after it may want to read a /proc file, and
	 * the bench-shell decision reads /proc/cmdline. */
	CK(strcmp(rows[0].target, "/proc") == 0);
	CK(rows[0].required == 1);

	for (i = 0; i < n; i++) {
		/* No devtmpfs on 2.6.30, so /dev is the initramfs's static set
		 * and mounting anything over it would hide the console node. */
		CK(strcmp(rows[i].target, "/dev") != 0);
		CK(strncmp(rows[i].target, "/dev/", 5) != 0);
		/* Absolute targets only; nothing relative, nothing empty. */
		CK(rows[i].target[0] == '/');
		CK(rows[i].src != NULL && rows[i].src[0] != '\0');
		CK(rows[i].fstype != NULL && rows[i].fstype[0] != '\0');
		/* Every mount is nosuid and nodev.  These are VFS superblock
		 * flags, so unlike `size=` they are honoured whatever the
		 * filesystem turns out to be. */
		CK((rows[i].flags & (unsigned long)MS_NOSUID) != 0);
		CK((rows[i].flags & (unsigned long)MS_NODEV) != 0);
		/* 🔴 No `size=`: ramfs's option table is `mode=%o` and its
		 * switch has no default, so `size=` is SILENTLY IGNORED and
		 * would read as a limit that does not exist. */
		if (rows[i].opts != NULL)
			CK(strstr(rows[i].opts, "size=") == NULL);
		/* Nothing read-only, and nothing bound or moved: the table is
		 * six fresh mounts and no remount. */
		CK((rows[i].flags & (unsigned long)MS_RDONLY) == 0);
		CK((rows[i].flags & (unsigned long)MS_REMOUNT) == 0);
		CK((rows[i].flags & (unsigned long)MS_BIND) == 0);
	}
	/* The four paths SPEC § 3 needs are all mounted or under something that
	 * is: /var/lib/cfg.bin, /run/wan.dns, /run/dnsfwd.pid,
	 * /srv/www/run/broker.sock. */
	{
		int have_var = 0, have_run = 0, have_srv = 0;

		for (i = 0; i < n; i++) {
			if (strcmp(rows[i].target, "/var") == 0)
				have_var = 1;
			if (strcmp(rows[i].target, "/run") == 0)
				have_run = 1;
			if (strcmp(rows[i].target, "/srv/www/run") == 0)
				have_srv = 1;
		}
		CK(have_var && have_run && have_srv);
	}
}

/* ------------------------------------------------------------- the behaviour */

static void t_all_ok(void)
{
	struct mfake f;
	struct mnt_ops o;
	struct mnt_status st[MNT_MAX];
	const struct mnt_row *rows;
	int n, i;

	mfake_init(&f, &o);
	rows = mnt_table(&n);
	CK(mnt_apply(rows, n, &o, st) == 0);
	CK(f.n_mount == n);
	for (i = 0; i < n; i++) {
		CK(st[i].rc == 0);
		CK(st[i].err == 0);
		/* EEXIST on the mkdir is not recorded as an error. */
		CK(st[i].mkdir_err == 0);
		/* The row reached mount() in order, with its own flags. */
		CK(strcmp(f.mount_target[i], rows[i].target) == 0);
		CK(f.mount_flags[i] == rows[i].flags);
	}
}

static void t_ebusy_is_ok(void)
{
	struct mfake f;
	struct mnt_ops o;
	struct mnt_status st[MNT_MAX];
	const struct mnt_row *rows;
	int n;

	mfake_init(&f, &o);
	f.fail_target = "/proc";
	f.fail_errno = EBUSY;
	rows = mnt_table(&n);
	/* /proc is `required`, but EBUSY means it is already there. */
	CK(mnt_apply(rows, n, &o, st) == 0);
	CK(st[0].rc == 1);
	CK(st[0].err == EBUSY);
	CK(f.n_mount == n);
}

static void t_required_failure_does_not_abort(void)
{
	struct mfake f;
	struct mnt_ops o;
	struct mnt_status st[MNT_MAX];
	const struct mnt_row *rows;
	int n, i;

	mfake_init(&f, &o);
	f.fail_target = "/var";      /* required */
	f.fail_errno = ENODEV;
	rows = mnt_table(&n);
	CK(mnt_apply(rows, n, &o, st) == 1);
	/* THE property: every row after the failure was still attempted. */
	CK(f.n_mount == n);
	for (i = 0; i < n; i++) {
		if (strcmp(rows[i].target, "/var") == 0) {
			CK(st[i].rc == -1);
			CK(st[i].err == ENODEV);
		} else {
			CK(st[i].rc == 0);
		}
	}

	/* An OPTIONAL row failing raises no degraded count at all. */
	mfake_init(&f, &o);
	f.fail_target = "/tmp";
	f.fail_errno = ENODEV;
	CK(mnt_apply(rows, n, &o, st) == 0);
	CK(f.n_mount == n);
}

static void t_mkdir_errors(void)
{
	static const char *const paths[] = { "/a", "/b", "/c" };
	static const unsigned modes[] = { 0700, 0755, 01777 };
	struct mfake f;
	struct mnt_ops o;
	struct mnt_status st[MNT_MAX];
	const struct mnt_row *rows;
	int n;

	/* EEXIST is not a failure; anything else is counted. */
	mfake_init(&f, &o);
	CK(mnt_mkdirs(paths, modes, 3, &o) == 0);
	CK(f.n_mkdir == 3);
	CK(strcmp(f.mkdir_path[0], "/a") == 0);
	CK(f.mkdir_mode[0] == 0700);
	CK(f.mkdir_mode[2] == 01777);

	mfake_init(&f, &o);
	f.mkdir_fail_target = "/b";
	f.mkdir_errno = EROFS;
	CK(mnt_mkdirs(paths, modes, 3, &o) == 1);
	CK(f.n_mkdir == 3);   /* and it kept going */

	/* A mkdir that fails for a real reason is recorded but does not stop the
	 * mount from being attempted: the directory may exist as something the
	 * mkdir cannot see. */
	mfake_init(&f, &o);
	f.mkdir_fail_target = "/proc";
	f.mkdir_errno = EACCES;
	rows = mnt_table(&n);
	CK(mnt_apply(rows, n, &o, st) == 0);
	CK(st[0].mkdir_err == EACCES);
	CK(st[0].rc == 0);

	CK(mnt_mkdirs(NULL, modes, 3, &o) == -1);
	CK(mnt_mkdirs(paths, NULL, 3, &o) == -1);
	CK(mnt_mkdirs(paths, modes, 3, NULL) == -1);
	CK(mnt_apply(NULL, 1, &o, st) == -1);
	CK(mnt_apply(rows, -1, &o, st) == -1);
	CK(mnt_apply(rows, n, NULL, st) == -1);
	CK(mnt_apply(rows, n, &o, NULL) == -1);
}

int main(void)
{
	t_policy();
	t_all_ok();
	t_ebusy_is_ok();
	t_required_failure_does_not_abort();
	t_mkdir_errors();
	printf("test_mounts: %d checks, %d failures\n", checks, fails);
	return fails == 0 ? 0 : 1;
}
