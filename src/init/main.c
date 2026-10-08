/* main.c -- R7: rlxfw's PID 1.  It replaces the four-line
 * `config/rlxfw-init.sh` that every seating since R3 rung 1 has booted.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT DOES, IN ORDER
 * ---------------------------------------------------------------------------
 *
 *   1  stdio onto /dev/console, whether or not the kernel got there first
 *   2  the rung-1 discriminator, which has to be the first line
 *   3  the mount table (mounts.c), then the directories under it
 *   4  the config store, read by linking cfg.c -- never by exec'ing cfgstore
 *   5  hostname, then the five /proc verbs, then the LAN by ioctl
 *   6  /var/udhcpd.conf, written from integers
 *   7  the child table, then the loop: reap, restart, poll
 *
 * ---------------------------------------------------------------------------
 * NO SHELL, AND WHAT THAT COSTS
 * ---------------------------------------------------------------------------
 *
 * There is no `system`, `popen`, `execl*`, `execvp` or `/bin/sh -c` in this
 * file.  Six children exist and each one is `fork` plus `execve` with an argv
 * of string literals and a fixed three-entry environment; not one argv byte
 * comes from the config store, from a lease, or from the kernel command line.
 * The five /proc writes that bring the switch core up are `write(2)` of a
 * compile-time literal to a compile-time path -- they are what the old script's
 * `echo … >` did, minus the interpreter.
 *
 * What that costs: the vendor's `/etc/inittab` semantics (respawn levels,
 * `askfirst`, `sysinit` ordering) are gone, and so is any notion of a service
 * DEPENDING on another.  Children start in table order and nothing waits for
 * anything -- brokerd may not have its socket up when httpd first tries it, and
 * httpd's client code has to cope.  That is a real limitation, recorded in
 * notes/init.md 8 rather than papered over with a sleep.
 *
 * ---------------------------------------------------------------------------
 * PID 1 NEVER EXITS
 * ---------------------------------------------------------------------------
 *
 * Every failure below is reported and survived.  The kernel's answer to PID 1
 * exiting is `Attempted to kill init`, so "abort the boot" can only mean a
 * panic, and a console with a loud line on it beats a panic every time.
 */

#include "init.h"
#include "mounts.h"
#include "supervise.h"
#include "../lib/netutil.h"
#include "cfg.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <sys/wait.h>
#include <unistd.h>

/* ==========================================================================
 * A bounded line builder.  No stdio, and no format string is ever assembled
 * from an input: the caller names each piece, so there is no path by which a
 * config value or a lease value becomes a conversion specifier.
 * ========================================================================== */

#define LB_MAX 240

struct lbuf {
	char b[LB_MAX + 2];
	size_t n;
	int truncated;
};

static void lb_reset(struct lbuf *l)
{
	l->n = 0;
	l->truncated = 0;
	l->b[0] = '\0';
}

static void lb_c(struct lbuf *l, char c)
{
	if (l->n >= LB_MAX) {
		l->truncated = 1;
		return;
	}
	l->b[l->n++] = c;
}

static void lb_s(struct lbuf *l, const char *s)
{
	size_t i;

	if (s == NULL)
		s = "(null)";
	for (i = 0; i < LB_MAX && s[i] != '\0'; i++)
		lb_c(l, s[i]);
}

static void lb_u(struct lbuf *l, unsigned long v)
{
	char t[24];
	int k = 0;

	if (v == 0) {
		lb_c(l, '0');
		return;
	}
	while (v > 0 && k < (int)sizeof(t)) {
		t[k++] = (char)('0' + (int)(v % 10ul));
		v /= 10ul;
	}
	while (k-- > 0)
		lb_c(l, t[k]);
}

static void lb_ip(struct lbuf *l, uint32_t ip)
{
	char q[NU_QUAD_BUF];

	if (nu_format_ipv4(ip, q, sizeof(q)) < 0)
		lb_s(l, "?.?.?.?");
	else
		lb_s(l, q);
}

static int console_fd = 2;

static void lb_out(struct lbuf *l)
{
	ssize_t w;

	if (l->truncated)
		lb_s(l, " [truncated]");
	l->b[l->n++] = '\n';
	w = write(console_fd, l->b, l->n);
	(void)w;   /* a console we cannot write to is not a reason to stop */
	lb_reset(l);
}

/* The two shapes almost every line here has. */
static void say(const char *a)
{
	struct lbuf l;

	lb_reset(&l);
	lb_s(&l, "rlxfw: init: ");
	lb_s(&l, a);
	lb_out(&l);
}

static void say2(const char *a, const char *b)
{
	struct lbuf l;

	lb_reset(&l);
	lb_s(&l, "rlxfw: init: ");
	lb_s(&l, a);
	lb_s(&l, b);
	lb_out(&l);
}

static void say_errno(const char *a, const char *b, int e)
{
	struct lbuf l;

	lb_reset(&l);
	lb_s(&l, "rlxfw: init: ");
	lb_s(&l, a);
	lb_s(&l, b);
	lb_s(&l, " errno=");
	lb_u(&l, (unsigned long)e);
	lb_out(&l);
}

/* ==========================================================================
 * The clock.
 *
 * `clock_gettime(CLOCK_MONOTONIC)` and NOT `times()`.  讀 the toolchain:
 * `clock_gettime` is in `libc.a` itself (member `clock_gettime.os`, a bare
 * `__NR_clock_gettime` = 4263 syscall), so a static uClibc 0.9.30 link needs no
 * `-lrt`; and `CLOCK_MONOTONIC` is 1 in `bits/time.h`.
 *
 * `times()` was the first choice and it is WRONG here: its return value carries
 * the kernel's INITIAL_JIFFIES offset of `-300 * HZ`
 * (`include/linux/jiffies.h:171`), so it starts near -30000 and crosses zero at
 * 300 s of uptime -- and it legitimately returns -1 at about 299.99 s, which the
 * usual `if (c == (clock_t)-1)` error check would read as a failure.  Only
 * DIFFERENCES of `times()` are usable, and a supervisor compares absolute
 * deadlines.
 *
 * Granularity is 10 ms: the clocksource is `jiffies` at HZ = 100, with no
 * hrtimers and no NOHZ in this .config.  Every constant in supervise.h is a
 * multiple of 50 ms, so the grid is not a problem; SV_TERM_STEP_MS is 50.
 * ========================================================================== */

static long now_ms(void)
{
	struct timespec ts;

	if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
		return 0;
	return (long)ts.tv_sec * 1000l + (long)(ts.tv_nsec / 1000000l);
}

/* ==========================================================================
 * Signals, through a self-pipe: the handler writes one byte and nothing else,
 * so everything that reacts to a signal runs in the loop with no reentrancy.
 * ========================================================================== */

static int sigpipe_fd[2] = { -1, -1 };

static void sig_handler(int s)
{
	unsigned char b = (unsigned char)s;
	ssize_t w = write(sigpipe_fd[1], &b, 1);

	(void)w;
}

static int install(int sig, void (*fn)(int))
{
	struct sigaction sa;

	memset(&sa, 0, sizeof(sa));
	sa.sa_handler = fn;
	sigemptyset(&sa.sa_mask);
	sa.sa_flags = SA_RESTART | (sig == SIGCHLD ? SA_NOCLDSTOP : 0);
	return sigaction(sig, &sa, NULL);
}

/* ==========================================================================
 * The syscall layer `supervise.c` is given.
 * ========================================================================== */

/* A fixed environment.  Three literals; nothing is inherited and nothing is
 * built.  PATH exists because the bench shell is unusable without one. */
static char *const child_env[] = {
	(char *)"PATH=/bin:/sbin:/usr/bin:/usr/sbin",
	(char *)"HOME=/",
	(char *)"TERM=vt102",
	NULL
};

static pid_t sys_spawn(void *ctx, const struct sv_child *c)
{
	char *av[SV_ARGV_MAX];
	pid_t pid;
	int i, fd;

	(void)ctx;
	pid = fork();
	if (pid != 0)
		return pid;   /* parent, or -1 which sv_start_due handles */

	/* --- child ------------------------------------------------------- */
	/* Default dispositions back: a child must not inherit PID 1's handlers
	 * or PID 1's ignored SIGPIPE. */
	(void)signal(SIGCHLD, SIG_DFL);
	(void)signal(SIGTERM, SIG_DFL);
	(void)signal(SIGINT, SIG_DFL);
	(void)signal(SIGUSR1, SIG_DFL);
	(void)signal(SIGHUP, SIG_DFL);
	(void)signal(SIGPIPE, SIG_DFL);
	if (sigpipe_fd[0] >= 0)
		(void)close(sigpipe_fd[0]);
	if (sigpipe_fd[1] >= 0)
		(void)close(sigpipe_fd[1]);

	if (c->console) {
		/* Its own session, with a real controlling tty, so that the
		 * shell gets job control and a ^C reaches the shell instead of
		 * going nowhere (today's `exec /bin/sh` from a script has no
		 * ctty at all, so ^C does nothing).
		 *
		 * /dev/ttyS0 FIRST, /dev/console second.  `CONFIG_CMDLINE` is
		 * "console=ttyS0,38400", so ttyS0 is the real device and
		 * /dev/console is the redirector; TIOCSCTTY on the redirector is
		 * not something this kernel has been shown to honour.
		 *
		 * 🔄 `R7-8`: this said /dev/ttyS0 was NOT in the image and that
		 * the open would therefore fall back to /dev/console.  It IS in
		 * the image now -- `nod /dev/ttyS0 c:4:64 0600`,
		 * config/rlxfw-initramfs.tsv -- so the first open is expected to
		 * succeed and the fallback becomes the untaken branch.  Which
		 * branch runs is 未定 until a boot says so: nothing has opened
		 * this node on the device.
		 *
		 * 🔴 This changes bytes a tool depends on: `looprun.py`'s
		 * DEFAULT_BOOT_UNTIL is "job control turned off[^#]{1,2}# ", and
		 * a shell WITH a ctty never prints that (量 `R7-8`: the string
		 * "can't access tty; job control turned off" is in this image's
		 * busybox exactly once, so its absence from a capture is the
		 * shell HAVING a ctty and not the string being unbuilt).  Pass
		 * --boot-until; `R7-8`'s report gives the pattern.
		 */
		(void)setsid();
		fd = open("/dev/ttyS0", O_RDWR);
		if (fd < 0)
			fd = open(PATH_CONSOLE, O_RDWR);
		if (fd >= 0) {
			(void)ioctl(fd, TIOCSCTTY, 0);
			(void)dup2(fd, 0);
			(void)dup2(fd, 1);
			(void)dup2(fd, 2);
			if (fd > 2)
				(void)close(fd);
		}
	} else {
		/* A daemon reads nothing.  stdout and stderr stay on the
		 * console: this is R7's first boot and a daemon's complaint is
		 * the whole point of having a console. */
		fd = open("/dev/null", O_RDWR);
		if (fd >= 0) {
			(void)dup2(fd, 0);
			if (fd > 2)
				(void)close(fd);
		}
	}

	for (i = 0; i < SV_ARGV_MAX; i++)
		av[i] = (char *)c->argv[i];   /* literals; NULL-terminated */
	av[SV_ARGV_MAX - 1] = NULL;
	(void)execve(c->path, av, child_env);
	_exit(127);   /* the only exit code that means "execve failed" here */
}

static int sys_send(void *ctx, pid_t pid, int sig)
{
	(void)ctx;
	return kill(pid, sig);
}

static pid_t sys_reap(void *ctx, int *wstatus)
{
	(void)ctx;
	return waitpid(-1, wstatus, WNOHANG);
}

static long sys_now(void *ctx)
{
	(void)ctx;
	return now_ms();
}

static void sys_wait(void *ctx, long ms)
{
	struct pollfd p;

	(void)ctx;
	p.fd = sigpipe_fd[0];
	p.events = POLLIN;
	p.revents = 0;
	(void)poll(&p, 1, (int)ms);
}

static void sys_sync(void *ctx)
{
	(void)ctx;
	sync();
}

/* 讀 `arch/rlx/bsp/setup.c`, and this matters at the bench:
 *
 *   RB_AUTOBOOT    -> kernel_restart -> bsp_machine_restart, which sets
 *                     BSP_WDTCNR = 0 and spins: a watchdog bite.  量 (SPEC.md
 *                     FW-37): `busybox reboot -f` resets this board and reaches
 *                     the loader prompt in 2.407 s.  This is the path that works.
 *   RB_POWER_OFF   -> bsp_machine_power_off, which is `while (1);`
 *   RB_HALT_SYSTEM -> bsp_machine_halt,      which is `while (1);`
 *
 * THIS SoC CANNOT POWER ITSELF OFF.  `pm_power_off` is set, so there is not even
 * the usual degrade-to-halt; both spin with interrupts off and no watchdog
 * armed, which on a console looks exactly like a crash.  So the poweroff path
 * says what it is about to do before it does it, and the board then needs a hand
 * on the power. */
static int sys_reboot(void *ctx, int how)
{
	(void)ctx;
	switch (how) {
	case SV_POWEROFF:
		say("reboot(RB_POWER_OFF): this SoC has no power control -- "
		    "bsp_machine_power_off is `while(1);`.  PULL THE POWER.");
		return reboot(RB_POWER_OFF);
	case SV_HALT:
		say("reboot(RB_HALT_SYSTEM): bsp_machine_halt is `while(1);`.  "
		    "PULL THE POWER.");
		return reboot(RB_HALT_SYSTEM);
	default:
		/* The watchdog bite. */
		return reboot(RB_AUTOBOOT);
	}
}

static void sys_log(void *ctx, const struct sv_child *c, const char *what)
{
	struct lbuf l;

	(void)ctx;
	lb_reset(&l);
	lb_s(&l, "rlxfw: init: ");
	lb_s(&l, c->name);
	lb_c(&l, ' ');
	lb_s(&l, what);
	if (c->pid > 0) {
		lb_s(&l, " pid=");
		lb_u(&l, (unsigned long)c->pid);
	}
	if (c->exited) {
		lb_s(&l, " exit=");
		lb_u(&l, (unsigned long)c->exit_code);
	} else if (c->signo != 0) {
		lb_s(&l, " signal=");
		lb_u(&l, (unsigned long)c->signo);
	}
	if (c->state == SV_WAIT && c->backoff_ms > 0) {
		lb_s(&l, " retry_in_ms=");
		lb_u(&l, (unsigned long)c->backoff_ms);
		lb_s(&l, " fails=");
		lb_u(&l, (unsigned long)c->fails);
	}
	if (c->state == SV_GIVENUP) {
		lb_s(&l, " after=");
		lb_u(&l, (unsigned long)c->fails);
		lb_s(&l, " consecutive fast failures; NOT RESTARTING");
	}
	lb_out(&l);
}

static const struct sv_sys sysops = {
	sys_spawn, sys_send, sys_reap, sys_now, sys_wait,
	sys_sync, sys_reboot, sys_log, NULL
};

/* ==========================================================================
 * Step 1: stdio.
 * ========================================================================== */

static void stdio_init(void)
{
	int fd = open(PATH_CONSOLE, O_RDWR | O_NOCTTY);

	if (fd < 0)
		fd = open("/dev/null", O_RDWR);
	if (fd < 0)
		return;   /* fd 0-2 are whatever the kernel left; console_fd = 2 */
	if (fd != 0)
		(void)dup2(fd, 0);
	(void)dup2(0, 1);
	(void)dup2(0, 2);
	if (fd > 2)
		(void)close(fd);
	console_fd = 1;
}

/* ==========================================================================
 * /proc/cmdline, tokenised with a fixed bound.  Used for one thing only:
 * turning the bench shell off.
 * ========================================================================== */

static int cmdline_has(const char *tok)
{
	char buf[513];
	ssize_t got;
	size_t i, start;
	int fd = open("/proc/cmdline", O_RDONLY);

	if (fd < 0)
		return 0;
	got = read(fd, buf, sizeof(buf) - 1);
	(void)close(fd);
	if (got <= 0)
		return 0;
	buf[got] = '\0';
	for (start = 0, i = 0; i <= (size_t)got; i++) {
		if (buf[i] != ' ' && buf[i] != '\t' && buf[i] != '\n' &&
		    buf[i] != '\0')
			continue;
		if (i > start) {
			buf[i] = '\0';
			if (strcmp(buf + start, tok) == 0)
				return 1;
		}
		start = i + 1;
	}
	return 0;
}

/* ==========================================================================
 * Steps 3 and 5: mounts, directories, /proc verbs, the LAN.
 * ========================================================================== */

static void do_mounts(int *degraded)
{
	static const char *const dirs[] = {
		"/var/lib", "/srv", "/srv/www", "/usr", "/usr/sbin", "/sbin"
	};
	static const unsigned modes[] = { 0700, 0755, 0755, 0755, 0755, 0755 };
	struct mnt_status st[MNT_MAX];
	const struct mnt_row *rows;
	int n, i, bad;

	rows = mnt_table(&n);
	if (n > MNT_MAX)
		n = MNT_MAX;
	*degraded = mnt_apply(rows, n, mnt_ops_real(), st);
	for (i = 0; i < n; i++) {
		if (st[i].rc == 0)
			say2("mounted ", rows[i].target);
		else if (st[i].rc == 1)
			say2("already mounted ", rows[i].target);
		else
			say_errno(rows[i].required ? "MOUNT FAILED (required) "
						   : "mount failed ",
				  rows[i].target, st[i].err);
	}
	/* /var/lib after /var is a tmpfs, or it would be created on the
	 * initramfs and then hidden by the mount. */
	bad = mnt_mkdirs(dirs, modes, (int)(sizeof(dirs) / sizeof(dirs[0])),
			 mnt_ops_real());
	if (bad > 0) {
		struct lbuf l;

		lb_reset(&l);
		lb_s(&l, "rlxfw: init: mkdir failed for ");
		lb_u(&l, (unsigned long)bad);
		lb_s(&l, " of 6 runtime directories");
		lb_out(&l);
	}
	if (*degraded > 0) {
		struct lbuf l;

		lb_reset(&l);
		lb_s(&l, "rlxfw: init: DEGRADED BOOT: ");
		lb_u(&l, (unsigned long)*degraded);
		lb_s(&l, " required mount(s) failed; continuing");
		lb_out(&l);
	}
}

/* config/rlxfw-init.sh's six verbs in its order, the switch core first (B43:
 * rlx0 carries nothing without it); a failed one prints and the next runs. */
struct procverb {
	const char *path;
	const char *data;
};

#if RLXFW_SWITCH_BRINGUP
static const struct procverb lan_verbs[] = {
	{ "/proc/rtl819x-switch", "unlock i-mean-it\n" },
	{ "/proc/rtl819x-switch", "init\n" },
	{ "/proc/rtl819x-switch", "vlan\n" },
	{ "/proc/rtl819x-switch", "start\n" },
	{ "/proc/rtl819x-nic", "unlock\n" },
	{ "/proc/rtl819x-nic", "netdev on\n" }
};

static void write_verbs(void)
{
	size_t k;

	for (k = 0; k < sizeof(lan_verbs) / sizeof(lan_verbs[0]); k++) {
		size_t len = strlen(lan_verbs[k].data);
		int fd = open(lan_verbs[k].path, O_WRONLY);
		ssize_t w;

		if (fd < 0) {
			say_errno("cannot open ", lan_verbs[k].path, errno);
			continue;
		}
		w = write(fd, lan_verbs[k].data, len);
		if (w != (ssize_t)len)
			say_errno("short write to ", lan_verbs[k].path, errno);
		(void)close(fd);
	}
}

static void lan_up(uint32_t ip, uint32_t mask)
{
	struct nu_net net;
	struct lbuf l;
	int rc;

	rc = nu_net_open(&net, nu_ops_real());
	if (rc != 0) {
		say_errno("no AF_INET socket: ", nu_strerror(rc), net.last_errno);
		return;
	}
	/* Address before netmask: SIOCSIFADDR resets the mask to the class
	 * default, so a mask written first would be silently thrown away. */
	rc = nu_if_set_addr(&net, RLXFW_LAN_IF, ip);
	if (rc != 0)
		say_errno("SIOCSIFADDR " RLXFW_LAN_IF " ", nu_strerror(rc),
			  nu_errno(&net));
	rc = nu_if_set_mask(&net, RLXFW_LAN_IF, mask);
	if (rc != 0)
		say_errno("SIOCSIFNETMASK " RLXFW_LAN_IF " ", nu_strerror(rc),
			  nu_errno(&net));
	rc = nu_if_set_flags(&net, RLXFW_LAN_IF, 1);
	if (rc != 0)
		say_errno("SIOCSIFFLAGS " RLXFW_LAN_IF " ", nu_strerror(rc),
			  nu_errno(&net));
	nu_net_close(&net);

	lb_reset(&l);
	lb_s(&l, "rlxfw: lan up, " RLXFW_LAN_IF " ");
	lb_ip(&l, ip);
	lb_c(&l, '/');
	lb_u(&l, (unsigned long)(nu_mask_prefix(mask) < 0
					 ? 0
					 : nu_mask_prefix(mask)));
	lb_out(&l);
}
#endif /* RLXFW_SWITCH_BRINGUP */

/* ==========================================================================
 * Step 4: the config store, and the typed reads on top of it.
 * ========================================================================== */

static uint32_t cfg_ipv4(const struct cfg *c, uint16_t id, uint32_t fallback)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;

	if (cfg_get(c, id, v, &len) != 0 || len != 4)
		return fallback;
	return ((uint32_t)v[0] << 24) | ((uint32_t)v[1] << 16) |
	       ((uint32_t)v[2] << 8) | (uint32_t)v[3];
}

static unsigned cfg_u8(const struct cfg *c, uint16_t id, unsigned fallback)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;

	if (cfg_get(c, id, v, &len) != 0 || len != 1)
		return fallback;
	return v[0];
}

static unsigned long cfg_u32(const struct cfg *c, uint16_t id,
			     unsigned long fallback)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;

	if (cfg_get(c, id, v, &len) != 0 || len != 4)
		return fallback;
	return ((unsigned long)v[0] << 24) | ((unsigned long)v[1] << 16) |
	       ((unsigned long)v[2] << 8) | (unsigned long)v[3];
}

/* `sys.hostname` re-validated here even though agent B validates it on load:
 * `sethostname` is a syscall and the charset rule is one line. */
static void set_hostname(const struct cfg *c)
{
	uint8_t v[CFG_VAL_MAX];
	uint16_t len = 0;
	char name[33];
	uint16_t i;

	if (cfg_get(c, CFGID_SYS_HOSTNAME, v, &len) != 0)
		return;
	if (len < 1 || len > 32)
		return;
	for (i = 0; i < len; i++) {
		char ch = (char)v[i];

		if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z') ||
		    (ch >= '0' && ch <= '9') || ch == '-')
			continue;
		say("hostname refused: charset");
		return;
	}
	if (v[0] == '-' || v[len - 1] == '-') {
		say("hostname refused: leading or trailing '-'");
		return;
	}
	memcpy(name, v, len);
	name[len] = '\0';
	if (sethostname(name, len) < 0)
		say_errno("sethostname ", name, errno);
	else
		say2("hostname ", name);
}

/* ==========================================================================
 * Step 6: /var/udhcpd.conf.
 *
 * Every byte of this file is either a literal from this function or the decimal
 * form of a `uint32_t` -- no config STRING reaches it, so there is nothing in
 * it that a SET could turn into a udhcpd directive.  The buffer is built whole
 * and written once.
 * ========================================================================== */

static void lb_kv_ip(struct lbuf *l, const char *k, uint32_t ip)
{
	lb_s(l, k);
	lb_ip(l, ip);
	lb_c(l, '\n');
}

static int write_udhcpd_conf(uint32_t lan, uint32_t mask, uint32_t start,
			     uint32_t end, uint32_t dns, unsigned long lease)
{
	struct lbuf l;
	unsigned long span;
	int fd;
	ssize_t w;

	lb_reset(&l);
	lb_s(&l, "# generated by rlxfw init; do not edit\n");
	lb_s(&l, "interface " RLXFW_LAN_IF "\n");
	lb_kv_ip(&l, "start ", start);
	lb_kv_ip(&l, "end ", end);
	lb_kv_ip(&l, "opt subnet ", mask);
	lb_kv_ip(&l, "opt router ", lan);
	lb_kv_ip(&l, "opt dns ", dns);
	lb_s(&l, "opt lease ");
	lb_u(&l, lease);
	lb_c(&l, '\n');
	span = end >= start ? (unsigned long)(end - start) + 1ul : 1ul;
	if (span > 254ul)
		span = 254ul;
	lb_s(&l, "max_leases ");
	lb_u(&l, span);
	lb_c(&l, '\n');
	lb_s(&l, "lease_file " PATH_UDHCPD_LEASES "\n");
	lb_s(&l, "pidfile /run/udhcpd.pid\n");
	if (l.truncated)
		return -1;   /* refuse a half-written config outright */

	fd = open(PATH_UDHCPD_CONF, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0) {
		say_errno("cannot write ", PATH_UDHCPD_CONF, errno);
		return -1;
	}
	w = write(fd, l.b, l.n);
	(void)close(fd);
	if (w != (ssize_t)l.n) {
		say_errno("short write ", PATH_UDHCPD_CONF, errno);
		return -1;
	}
	return 0;
}

/* ==========================================================================
 * Step 7: the child table.
 * ========================================================================== */

static void add_child(struct sv_set *s, const char *name, const char *path,
		      const char *a0, const char *a1, const char *a2,
		      const char *a3, const char *a4, const char *a5,
		      int console, int enabled, const char *why_off)
{
	struct sv_child *c;
	size_t nl;

	if (s->n >= SV_MAX_CHILD) {
		say2("child table full, dropped ", name);
		return;
	}
	c = &s->c[s->n];
	memset(c, 0, sizeof(*c));
	nl = strlen(name);
	if (nl > (size_t)(SV_NAME_MAX - 1))
		nl = (size_t)(SV_NAME_MAX - 1);
	memcpy(c->name, name, nl);
	c->path = path;
	c->argv[0] = a0;
	c->argv[1] = a1;
	c->argv[2] = a2;
	c->argv[3] = a3;
	c->argv[4] = a4;
	c->argv[5] = a5;
	c->argv[6] = NULL;
	c->argv[7] = NULL;
	c->console = console;
	s->n++;

	if (!enabled) {
		c->state = SV_OFF;
		say2(name, why_off);
		return;
	}
	/* One `access` before the first start.  Without it a binary that is not
	 * on the image costs SV_FAIL_MAX `execve` failures and eight console
	 * lines; with it, one line, and the crash-loop cap stays for the case it
	 * is actually for -- a daemon that starts and then dies. */
	if (access(path, X_OK) != 0) {
		c->state = SV_ABSENT;
		say_errno(name, ": binary not executable, NOT STARTED: ", errno);
		say2("  missing: ", path);
		return;
	}
	sv_arm(c, now_ms());
}

static void build_table(struct sv_set *s, const struct cfg *c, int shell_on)
{
	unsigned dhcpd = cfg_u8(c, CFGID_DHCPD_ENABLE, 1);
	unsigned wanmode = cfg_u8(c, CFGID_WAN_MODE, 0);

	s->n = 0;
	add_child(s, "brokerd", "/usr/sbin/brokerd", "brokerd", NULL, NULL,
		  NULL, NULL, NULL, 0, 1, "");
	add_child(s, "httpd", "/usr/sbin/httpd", "httpd", NULL, NULL, NULL,
		  NULL, NULL, 0, 1, "");
	add_child(s, "dnsfwd", "/usr/sbin/dnsfwd", "dnsfwd", NULL, NULL, NULL,
		  NULL, NULL, 0, 1, "");
	/* `-f`: busybox udhcpd and udhcpc both background themselves without
	 * it, and a supervisor handed an immediately-exiting parent counts a
	 * fast failure every time.  SPEC § 3's argv is missing it. */
	add_child(s, "udhcpd", PATH_BUSYBOX, "udhcpd", "-f", PATH_UDHCPD_CONF,
		  NULL, NULL, NULL, 0, dhcpd == 1,
		  ": not started (dhcpd.enable = 0)");
	add_child(s, "udhcpc", PATH_BUSYBOX, "udhcpc", "-f", "-i",
		  RLXFW_WAN_IF, "-s", PATH_IFUPD, 0, wanmode == 1,
		  ": not started (wan.mode is not dhcp)");
	add_child(s, "shell", PATH_SHELL, "sh", NULL, NULL, NULL, NULL, NULL,
		  1, shell_on, ": console shell DISABLED in this build");
}

/* ==========================================================================
 * main
 * ========================================================================== */

int main(int argc, char **argv)
{
	struct sv_set set;
	struct cfg cfg;
	struct pollfd pfd;
	uint32_t lan_ip, lan_mask;
	int degraded = 0, shell_on, rc, mask_rc;
	volatile int want_reboot = 0, want_poweroff = 0, want_reload = 0;

	(void)argc;
	(void)argv;

	stdio_init();
	/* Step 2.  This exact string, first, byte for byte: tools/bootbytes.py
	 * and RUNSHEET.md B5/P6 both depend on it. */
	{
		struct lbuf l;

		lb_reset(&l);
		lb_s(&l, RLXFW_RUNG1_LINE);
		lb_out(&l);
	}
	say("compiled PID 1 (R7).  No shell is exec'd except the bench shell below.");

	if (pipe(sigpipe_fd) == 0) {
		(void)fcntl(sigpipe_fd[0], F_SETFL, O_NONBLOCK);
		(void)fcntl(sigpipe_fd[1], F_SETFL, O_NONBLOCK);
	} else {
		say_errno("pipe() failed, signals will be polled: ", "", errno);
	}
	(void)signal(SIGPIPE, SIG_IGN);
	if (install(SIGCHLD, sig_handler) != 0 ||
	    install(SIGTERM, sig_handler) != 0 ||
	    install(SIGINT, sig_handler) != 0 ||
	    install(SIGUSR1, sig_handler) != 0 ||
	    install(SIGHUP, sig_handler) != 0)
		say("WARNING: a signal handler could not be installed");

	do_mounts(&degraded);

	/* Step 4. */
	rc = cfg_load(PATH_CFG, &cfg);
	if (rc != 0) {
		(void)cfg_defaults(&cfg);
		say("config store absent or invalid: DEFAULTS, source=0 "
		    "(no admin.pwhash, so no web login until one is set)");
	} else {
		struct lbuf l;

		lb_reset(&l);
		lb_s(&l, "rlxfw: init: config store slot ");
		lb_u(&l, (unsigned long)cfg.source);
		lb_s(&l, " seq ");
		lb_u(&l, (unsigned long)cfg.seq);
		lb_out(&l);
	}

	/* Step 5. */
	set_hostname(&cfg);
	lan_ip = cfg_ipv4(&cfg, CFGID_LAN_IPADDR, 0x0A010101u);   /* 10.1.1.1 */
	lan_mask = cfg_ipv4(&cfg, CFGID_LAN_NETMASK, 0xFFFFFF00u);
	mask_rc = nu_mask_ok(lan_mask, 8, 30);
	if (mask_rc != 0 || !nu_is_unicast(lan_ip) ||
	    nu_is_net_or_bcast(lan_ip, lan_mask)) {
		say2("lan.ipaddr/lan.netmask refused: ",
		     mask_rc != 0 ? nu_strerror(mask_rc) : "not a host address");
		say("  falling back to 10.1.1.1/24 so the bench keeps a LAN");
		lan_ip = 0x0A010101u;
		lan_mask = 0xFFFFFF00u;
	}
#if RLXFW_SWITCH_BRINGUP
	say("lan bring-up");
	write_verbs();
	lan_up(lan_ip, lan_mask);
#else
	say("lan bring-up SKIPPED (built with RLXFW_SWITCH_BRINGUP=0); "
	    "no /proc verb written and no interface opened");
#endif

	/* Step 6. */
	if (cfg_u8(&cfg, CFGID_DHCPD_ENABLE, 1) == 1 &&
	    write_udhcpd_conf(lan_ip, lan_mask,
			      cfg_ipv4(&cfg, CFGID_DHCPD_START, 0x0A010164u),
			      cfg_ipv4(&cfg, CFGID_DHCPD_END, 0x0A0101C7u),
			      cfg_ipv4(&cfg, CFGID_DNS_UPSTREAM, 0x0A010102u),
			      cfg_u32(&cfg, CFGID_DHCPD_LEASE, 86400ul)) == 0)
		say("wrote " PATH_UDHCPD_CONF);

	/* Step 7.  The bench shell, and the one line that has to be loud. */
	shell_on = RLXFW_BENCH_SHELL ? 1 : 0;
	if (shell_on && cmdline_has(CMDLINE_NOSHELL)) {
		shell_on = 0;
		say("bench shell suppressed by '" CMDLINE_NOSHELL
		    "' on the kernel command line");
	}
	if (shell_on) {
		say("*** BENCH PROFILE: A ROOT SHELL IS ENABLED ON "
		    PATH_CONSOLE " ***");
		say("*** build with BENCH_SHELL=0, or boot with '"
		    CMDLINE_NOSHELL "', to remove it ***");
	} else {
		say("bench profile OFF: no shell on " PATH_CONSOLE);
	}
	build_table(&set, &cfg, shell_on);

	pfd.fd = sigpipe_fd[0];
	pfd.events = POLLIN;

	for (;;) {
		long now = now_ms();
		long d;
		unsigned char sb[64];
		ssize_t got;
		int i;

		(void)sv_reap_all(&set, &sysops, now);

		if (want_reboot || want_poweroff) {
			say(want_poweroff ? "POWEROFF requested"
					  : "REBOOT requested");
			(void)sv_shutdown(&set, &sysops,
					  want_poweroff ? SV_POWEROFF
							: SV_REBOOT);
			/* reboot(2) returned, which on this SoC is 未定 --
			 * nothing has run on the device yet.  Say so and keep
			 * reaping rather than exiting. */
			say("reboot(2) RETURNED; PID 1 is still here");
			want_reboot = 0;
			want_poweroff = 0;
			continue;
		}
		if (want_reload) {
			want_reload = 0;
			say("SIGHUP: re-reading the config store");
			if (cfg_load(PATH_CFG, &cfg) != 0)
				(void)cfg_defaults(&cfg);
			for (i = 0; i < set.n; i++)
				if (set.c[i].state == SV_GIVENUP) {
					say2("re-arming ", set.c[i].name);
					sv_arm(&set.c[i], now_ms());
				}
		}

		(void)sv_start_due(&set, &sysops, now_ms());

		d = sv_next_due(&set, now_ms());
		if (pfd.fd < 0) {
			/* No self-pipe: poll cannot block on nothing, so fall
			 * back to a 200 ms tick.  Signals still arrive; they
			 * are just noticed a tick late. */
			sys_wait(NULL, 200);
		} else {
			(void)poll(&pfd, 1, d < 0 ? 1000 : (int)d);
			got = read(pfd.fd, sb, sizeof(sb));
			for (i = 0; i < (int)got; i++) {
				switch ((int)sb[i]) {
				case SIGTERM:
				case SIGINT:
					want_reboot = 1;
					break;
				case SIGUSR1:
					want_poweroff = 1;
					break;
				case SIGHUP:
					want_reload = 1;
					break;
				default:
					break;   /* SIGCHLD: the wake is the message */
				}
			}
		}
	}
	/* not reached */
}
