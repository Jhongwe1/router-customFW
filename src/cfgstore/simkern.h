/* simkern.h -- a simulated rtl819x-spi for the flash backend's host tests.
 *
 * Linked ONLY into test programs (test_flash, cfgstore-sim), with
 * -Wl,--wrap=open,--wrap=close,--wrap=write,--wrap=flock,--wrap=nanosleep,
 * --wrap=lseek.  The code under test is the product's own: src/lib/spictl.c,
 * cfgflash.c and cfg.c, opening the five real device paths of spictl_dev.
 * The wrappers map exactly those strings (and the other spellings of the
 * image's flash nodes) and pass every other path through:
 *
 *   /proc/rtl819x-spi      write: one verb per write(2), decided by the
 *                          install header the kernel compiles
 *                          (rtl819x-spi-install.h: the parser, the arm
 *                          agreement, the payload check, the plan, the
 *                          read-back compare) and by rtl819x-spi-wrpolicy.h's
 *                          arm check; read: a page with NO field, so a field
 *                          read from it instead of the node finds nothing
 *   /proc/rtl819x-spi-inst read only: n_writes, then the header's own install
 *                          and counter emits, regenerated on every open, and
 *                          refused if it would not fit one read (3,072)
 *   /proc/rtl819x-spi-img  appends, admitted by the header's img_admit
 *   /run/rlxfw-flash.lock  a real file in the scratch directory, real flock(2)
 *   /dev/mtd2ro            a real 4 MiB file in the scratch directory, O_RDONLY
 *                          only (EACCES otherwise, as the 0400 odd-minor node)
 *   /dev/mtd0ro, /dev/mtd1ro, //dev/mtd2ro, /dev/./mtd2ro
 *                          /dev/zero: a character device, O_RDONLY only
 *
 * Every write to the two writable /proc files, every lock and unlock of the
 * lock file, every lseek on the flash file ('s') and on one of the other
 * nodes ('c') is an event, kept in order in memory and appended to
 * <dir>/writes.log.  nanosleep sleeps nothing and adds the time it was asked
 * for to a counter, so a 30 s lock timeout runs in microseconds and is still
 * measured as 30 s of asked-for sleep.
 *
 * Faults are the kernel misbehaving on purpose, one at a time: the node
 * reporting a value the step did not produce, or a verb refused.
 */
#ifndef RLXFW_SIMKERN_H
#define RLXFW_SIMKERN_H

#include <stddef.h>
#include <stdint.h>

#define SIMK_CHIP	0x00400000u	/* the 4 MiB part */

enum {
	SIMK_NONE = 0,
	SIMK_IMGLEN_SHORT,	/* the page says img_len one byte short */
	SIMK_IMGERR,		/* the page says img_err POISONED */
	SIMK_STAGE_EFBIG,	/* the staging write is refused EFBIG, and poisons */
	SIMK_INST_REASON,	/* install answers success; the page says CMP */
	SIMK_INST_SHA,		/* install refused SHA: the digest check fails */
	SIMK_CMP_DIFF,		/* the page says inst_cmp_diff 1 */
	SIMK_CMP_OK0,		/* the page says inst_cmp_ok 0 */
	SIMK_NW_MINUS1,		/* the install moves n_writes by 31 */
	SIMK_NW_PLUS1,		/* ... by 33 */
	SIMK_LOCK_ENOSYS,	/* flock(2) is ENOSYS: no CONFIG_FILE_LOCKING */
	SIMK_DISARM_EIO,	/* `disarm` refused EIO */
	SIMK_ARM_EPERM,		/* `arm` refused EPERM */
	SIMK_NFAULT
};

/* One event.  kind: 'v' a verb line, 'i' a staging write of len bytes,
 * 'L' the lock taken, 'U' the lock released, 's' an lseek on the flash file,
 * 'c' an lseek on another flash node (a read the file backend must not do).
 * err is the errno the simulated kernel answered with, 0 for success. */
struct simk_ev {
	char kind;
	char text[140];
	size_t len;
	int err;
	uint32_t off;
};

/* Points the four paths at dir and creates a fresh 4 MiB flash file: the low
 * 64 KiB a pattern that is never all 0xFF (the loader and H601 stand-in),
 * every other byte 0xFF.  0 or -1. */
int simk_init(const char *dir);
/* Points the paths at dir and creates nothing: a child of the test that must
 * see the flash file the parent built (cfgstore-sim does this from
 * RLXFW_SIMKERN_DIR at its first wrapped call). */
int simk_attach(const char *dir);

void simk_fault(int f);			/* SIMK_*; SIMK_NONE clears */
void simk_reset(void);			/* events, sleep counter, n_writes kept */
int  simk_nev(void);
const struct simk_ev *simk_ev(int i);
unsigned long simk_slept_ms(void);
unsigned long simk_nwrites(void);

/* A second holder of the lock file, through the real flock: 1 takes it, 0
 * lets it go.  0 or -1. */
int simk_hold_lock(int on);

const char *simk_flash_file(void);	/* the 4 MiB file's path */
const char *simk_dir(void);
/* The staged bytes of the last install the simulated kernel accepted for its
 * digest check, saved to this file (for an independent digest). */
const char *simk_staged_file(void);

#endif /* RLXFW_SIMKERN_H */
