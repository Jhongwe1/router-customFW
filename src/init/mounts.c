/* mounts.c -- R7: what PID 1 mounts, and what it deliberately does not.
 *
 * ---------------------------------------------------------------------------
 * THERE IS NO devtmpfs ON THIS KERNEL, AND "tmpfs" HERE IS ramfs
 * ---------------------------------------------------------------------------
 *
 * 讀, and measured at the desk against a positive control (Linux 5.4.27 in
 * `src-vendor/shibajee-linux-rtl8196e`, which has all of it):
 *
 *   * devtmpfs was merged in 2.6.32.  `drivers/base/devtmpfs.c` does not exist
 *     in this 2.6.30 drop, `CONFIG_DEVTMPFS` is not a symbol anywhere in its
 *     Kconfig, and the built `System.map` and `strings vmlinux` hold zero
 *     `devtmpfs` lines.  So /dev is the static set declared in
 *     `config/rlxfw-initramfs.tsv` and **nothing is mounted on /dev**.  That is
 *     a decision, not an omission: a filesystem mounted over /dev would hide the
 *     declared nodes and the boot would lose its console.
 *   * `# CONFIG_TMPFS is not set` and `# CONFIG_SHMEM is not set`, yet
 *     `mount -t tmpfs` still works: `mm/shmem.c`'s `#else !CONFIG_SHMEM` branch
 *     registers a `tmpfs_fs_type` whose `get_sb` is `ramfs_get_sb`.  Confirmed
 *     in the built artefact by dumping the struct out of `vmlinux`'s `.data`.
 *   * 🔴 SO THERE IS NO SIZE LIMIT.  `fs/ramfs/inode.c`'s option table holds
 *     `mode=%o` and nothing else, and its `switch` has no `default:` -- every
 *     other option is SILENTLY IGNORED.  A `size=512k` here would read like a
 *     limit and be none, so it is not written: the rows below pass `mode=` only.
 *     Every one of these mounts can grow until the board is out of RAM (~26 MB),
 *     and `simple_statfs` means `df` cannot even show it.  Bounding them needs
 *     CONFIG_TMPFS and CONFIG_SHMEM, which is a kernel change and not this
 *     file's to make; it is recorded in notes/init.md 3 as what this does not
 *     establish.
 *
 * ---------------------------------------------------------------------------
 * NO MOUNT FAILURE ABORTS THE BOOT
 * ---------------------------------------------------------------------------
 *
 * PID 1 cannot exit -- the kernel panics with "Attempted to kill init" -- so
 * "abort the boot" would mean a panic, and a panic is strictly less useful than
 * a console with a loud line on it.  `required` therefore selects the loudness
 * and sets a bit in the degraded mask; it never stops the sequence.  A boot
 * that failed to mount /var still starts brokerd, which fails closed on a
 * missing config store (SPEC § 5: source = 0, no `admin.pwhash`, no login).
 */

#include "mounts.h"

#include <errno.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>

/* MS_NOSUID and MS_NODEV are VFS superblock flags, so they are honoured whatever
 * the filesystem is -- unlike `size=`, they are real here.  /tmp keeps MS_NOSUID
 * and MS_NODEV but not MS_NOEXEC: iperf3 needs `mkstemp` + `mmap` there. */
static const struct mnt_row mnt_rows[] = {
	/* src      target          fs       opts            flags                              mkdir  req */
	{ "proc",   "/proc",        "proc",  NULL,           MS_NOSUID | MS_NODEV | MS_NOEXEC,  0755,  1 },
	{ "sysfs",  "/sys",         "sysfs", NULL,           MS_NOSUID | MS_NODEV | MS_NOEXEC,  0755,  0 },
	{ "tmpfs",  "/var",         "tmpfs", "mode=0755",    MS_NOSUID | MS_NODEV,              0755,  1 },
	{ "tmpfs",  "/run",         "tmpfs", "mode=0755",    MS_NOSUID | MS_NODEV,              0755,  1 },
	{ "tmpfs",  "/tmp",         "tmpfs", "mode=1777",    MS_NOSUID | MS_NODEV,              01777, 0 },
	{ "tmpfs",  "/srv/www/run", "tmpfs", "mode=0755",    MS_NOSUID | MS_NODEV,              0755,  0 }
};

const struct mnt_row *mnt_table(int *n)
{
	if (n != NULL)
		*n = (int)(sizeof(mnt_rows) / sizeof(mnt_rows[0]));
	return mnt_rows;
}

static int real_mkdir(void *ctx, const char *path, unsigned mode)
{
	(void)ctx;
	return mkdir(path, (mode_t)mode);
}

static int real_mount(void *ctx, const char *src, const char *target,
		      const char *fstype, unsigned long flags, const void *data)
{
	(void)ctx;
	return mount(src, target, fstype, flags, data);
}

const struct mnt_ops *mnt_ops_real(void)
{
	static const struct mnt_ops ops = { real_mkdir, real_mount, NULL };
	return &ops;
}

int mnt_apply(const struct mnt_row *rows, int n, const struct mnt_ops *ops,
	      struct mnt_status *st)
{
	int i, degraded = 0;

	if (rows == NULL || ops == NULL || st == NULL || n < 0)
		return -1;

	for (i = 0; i < n; i++) {
		st[i].rc = -1;
		st[i].err = 0;
		st[i].mkdir_err = 0;

		if (rows[i].mkdir_mode != 0) {
			errno = 0;
			if (ops->do_mkdir(ops->ctx, rows[i].target,
					  rows[i].mkdir_mode) < 0 &&
			    errno != EEXIST)
				st[i].mkdir_err = errno;
		}
		errno = 0;
		if (ops->do_mount(ops->ctx, rows[i].src, rows[i].target,
				  rows[i].fstype, rows[i].flags,
				  rows[i].opts) == 0) {
			st[i].rc = 0;
			continue;
		}
		st[i].err = errno;
		/* Already mounted is not a failure.  It happens when PID 1
		 * re-runs the table on SIGHUP, and it would happen if a future
		 * kernel mounted /proc for us. */
		if (errno == EBUSY) {
			st[i].rc = 1;
			continue;
		}
		if (rows[i].required)
			degraded++;
	}
	return degraded;
}

int mnt_mkdirs(const char *const *paths, const unsigned *modes, int n,
	       const struct mnt_ops *ops)
{
	int i, bad = 0;

	if (paths == NULL || modes == NULL || ops == NULL)
		return -1;
	for (i = 0; i < n; i++) {
		errno = 0;
		if (ops->do_mkdir(ops->ctx, paths[i], modes[i]) < 0 &&
		    errno != EEXIST)
			bad++;
	}
	return bad;
}
