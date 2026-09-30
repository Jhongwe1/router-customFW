/* mounts.h -- R7: the filesystem table PID 1 brings up, as data.
 *
 * The table is a compile-time `const` and `mnt_apply` walks it: nothing here
 * takes a path or an option string from the config store, from the kernel
 * command line, or from any other input.  That is the point -- `mount(2)`'s
 * fifth argument is parsed by the filesystem, so the only safe way to keep it
 * out of reach of a config value is for it never to be built at runtime.
 *
 * `struct mnt_ops` makes the two syscalls injectable so the host test can walk
 * the real table without root.
 */

#ifndef RLXFW_INIT_MOUNTS_H
#define RLXFW_INIT_MOUNTS_H

/* For NULL.  gcc 3.4.6's <sys/mount.h> chain does not pull it in, and a
 * `NULL` that is undeclared inside a static initialiser fails as "initializer
 * element is not constant", which names the wrong problem. */
#include <stddef.h>

#define MNT_MAX 8

struct mnt_row {
	const char *src;
	const char *target;
	const char *fstype;
	const char *opts;      /* mount(2) data; NULL for proc and sysfs */
	unsigned long flags;
	unsigned mkdir_mode;   /* 0 = do not create the mount point */
	int required;          /* 1 = a failure is loud and marks the boot degraded */
};

struct mnt_ops {
	int (*do_mkdir)(void *ctx, const char *path, unsigned mode);
	int (*do_mount)(void *ctx, const char *src, const char *target,
			const char *fstype, unsigned long flags, const void *data);
	void *ctx;
};

/* rc: 0 mounted, 1 was already mounted (EBUSY), -1 failed.  `err` is errno. */
struct mnt_status {
	int rc;
	int err;
	int mkdir_err;  /* errno of the mkdir, or 0; EEXIST is not recorded */
};

const struct mnt_row *mnt_table(int *n);
const struct mnt_ops *mnt_ops_real(void);

/* Walks `rows`, filling `st[0..n-1]`.  Returns the number of rows marked
 * `required` that failed -- the degraded count.  Never aborts: a mount failure
 * on this device must still reach a console, because a boot that cannot mount
 * /proc is exactly the boot that needs looking at. */
int mnt_apply(const struct mnt_row *rows, int n, const struct mnt_ops *ops,
	      struct mnt_status *st);

/* mkdir every path in order, ignoring EEXIST.  Returns the count that failed
 * for any other reason. */
int mnt_mkdirs(const char *const *paths, const unsigned *modes, int n,
	       const struct mnt_ops *ops);

#endif /* RLXFW_INIT_MOUNTS_H */
