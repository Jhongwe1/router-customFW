/* linkprobe.c -- R6b-6: calls the three ethtool ops `rtl819x-nic` has carried
 * since 1.3 and that nothing has ever called.
 *
 * ---------------------------------------------------------------------------
 * WHY IT EXISTS
 * ---------------------------------------------------------------------------
 *
 * `nic_et_drvinfo`, `nic_et_get_link` and `nic_et_ringparam` were written in
 * `rtl819x-nic` 1.3 (`2aae301`).  量 on all 217 committed NIC dumps:
 * `n_et_link 0` and `et_link_last FFFFFFFF` -- the ops have never run, because
 * this image has no `ethtool` binary and busybox carries no applet that issues
 * `SIOCETHTOOL`.  This program is the missing caller, and nothing else.
 *
 * It issues exactly three requests, all reads: ETHTOOL_GDRVINFO, ETHTOOL_GLINK
 * and ETHTOOL_GRINGPARAM, through SIOCETHTOOL on an AF_INET datagram socket.
 * The request table below is a compile-time `const` and it names no
 * ETHTOOL_S* at all; `tools/linkprobecheck.py` refuses a source that does.
 *
 * ---------------------------------------------------------------------------
 * THE CONTROLS ARE IN THE SAME INVOCATION
 * ---------------------------------------------------------------------------
 *
 *   linkprobe get rlx0 lo eth4 nosuch0
 *
 * makes twelve calls, and each interface is a control for the others (讀, the
 * staged 2.6.30 tree, byte-identical to the drop):
 *
 *   rlx0     rlxfw's ops: three rc 0 lines.
 *   lo       `loopback_ethtool_ops` has only `.get_link = always_on`
 *            (drivers/net/loopback.c:118-124): drv and ring refuse with
 *            -EOPNOTSUPP, link reads 1 THROUGH A DIFFERENT DRIVER.
 *   eth4     the vendor tree sets no ethtool_ops, so dev_ethtool returns
 *            -EOPNOTSUPP before it reads the command (net/core/ethtool.c:
 *            907-908): three refusals.
 *   nosuch0  no device: -ENODEV (:904-905), three refusals.
 *
 * EOPNOTSUPP is 122 on this ABI and not the 95 a PC prints (toolchain
 * asm/errno.h:76 and the kernel's arch/rlx/include/asm/errno.h:76 agree).
 * This program prints the number the kernel returned and never names it, so a
 * wrong expectation is the card's error and not something this file can hide.
 *
 * AGAINST "A PROBE THAT CAN ONLY PRINT 1":
 *   (a) `lo` prints 1 through a driver that is not rlxfw's;
 *   (b) before every call the whole buffer except `cmd` is filled with 0xA5,
 *       and every line prints `can <k>`: how many bytes past `cmd` still hold
 *       0xA5 after the call.  A call that returns 0 WITHOUT WRITING prints
 *       `data A5A5A5A5 can 4`, never `data 00000001`.  (`can` counts bytes
 *       that EQUAL the canary, so it is an upper bound on bytes untouched: a
 *       driver that wrote 0xA5 would read as not having written it.)
 *   (c) the build refuses (gate G5) if the linked ELF holds the bytes
 *       `rtl819x`, so a driver name this program prints came from the kernel;
 *   (d) the value 0 comes from the cable, on the card.
 *
 * ---------------------------------------------------------------------------
 * OUTPUT (write(2) only; one line per call, `\n`, the tty adds the `\r`)
 * ---------------------------------------------------------------------------
 *
 *   LP0 linkprobe 1 build <16 hex>
 *   LP drv <if> rc 0 driver "<s>" version "<s>" fw "<s>" bus "<s>" can <k>
 *   LP link <if> rc 0 data <8 hex> can <k>
 *   LP ring <if> rc 0 rx <p>/<max> mini <p>/<max> jumbo <p>/<max> tx <p>/<max> can <k>
 *   LP <req> <if> rc <errno> can <k>                  (any refused call)
 *   LP9 calls <n> ok <n> refused <n> nowrite <n>
 *
 * `nowrite` counts rc 0 calls whose `can` equals the whole region -- a call
 * that succeeded and wrote nothing.  On a working kernel it is 0.
 * A string field prints printable ASCII only (anything else, and `"` and `\`,
 * as `\xHH`), and a 32-byte field with no NUL in it prints `nonul` in place of
 * the string.
 *
 *   linkprobe watch <if> <ms> <s>        10 <= ms <= 10000, 1 <= s <= 600
 *
 *   LPW start <if> v <x> rc <r>                 the first sample, at once:
 *                                               tells running from never started
 *   LPW t <ms> i <n> v <x> rc <r>               each change of v or rc
 *   LPW end n <n> ms <el> ones <a> zeros <b> other <o> err <e> nowrite <w> trans <k>
 *
 * `v` is GLINK's data in decimal; n = ones + zeros + other + err + nowrite.
 * Time is CLOCK_MONOTONIC through syscall(), so no -lrt.  讀 .config: HZ 100
 * and no HIGH_RES_TIMERS, so the achieved period is 10-20 ms (推).  The hard
 * bound is n <= floor(s*1000/ms) + 1 and it is enforced here by a schedule
 * counter, not only by the clock: a sleep that returned early could not raise
 * it.
 *
 * Refusals print `LPE <reason>` and exit 2; a socket() failure prints
 * `LPE socket rc <errno>` and exits 3.  Every mode prints LP0 first, so every
 * capture names the build.
 *
 * ---------------------------------------------------------------------------
 * HOUSE RULES (config/rlxfw-user/isaprobe/ucost.c's, and for its reasons)
 * ---------------------------------------------------------------------------
 *
 *   - write(2) only, no stdio.
 *   - NO DIVISION anywhere, by a constant or a runtime value: gcc emits a
 *     `break 7` divide check and gate G1 counts `break` by opcode.  Decimal is
 *     produced by subtracting powers of ten; milliseconds are printed by
 *     dropping six digits from a nanosecond count.
 *   - No asm, so no `.set noreorder` question.
 *
 * LP_HOST (tools/linkprobecheck.py only) swaps the four system shims --
 * lp_open, lp_ioctl, lp_now_ns and lp_sleep_ms -- for a scripted fake and a
 * fake clock.  The logic is the same bytes; the ABI is not, and is gate G6's
 * and the board's.
 */

#include <stddef.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <net/if.h>
#include <linux/sockios.h>
#include <linux/ethtool.h>

#ifndef LP_BUILD_ID
#define LP_BUILD_ID "0000000000000000"
#endif
#define LP_VERSION "1"

typedef unsigned int u32;
typedef unsigned long long u64;

/* The ABI, asserted at compile time on BOTH compilers.  Sizes and offsets are
 * 讀 from the staged kernel's include/linux/ethtool.h:51-65, :77-80 and
 * :196-215; gate G6 separately requires the toolchain's copy of the three
 * struct regions to be byte-identical to the kernel's.  A header that drifted
 * fails here rather than producing a line whose fields are shifted. */
#define LP_ASSERT(name, cond) typedef char lp_assert_##name[(cond) ? 1 : -1]
LP_ASSERT(drv_size, sizeof(struct ethtool_drvinfo) == 196);
LP_ASSERT(val_size, sizeof(struct ethtool_value) == 8);
LP_ASSERT(ring_size, sizeof(struct ethtool_ringparam) == 36);
LP_ASSERT(drv_driver, offsetof(struct ethtool_drvinfo, driver) == 4);
LP_ASSERT(drv_version, offsetof(struct ethtool_drvinfo, version) == 36);
LP_ASSERT(drv_fw, offsetof(struct ethtool_drvinfo, fw_version) == 68);
LP_ASSERT(drv_bus, offsetof(struct ethtool_drvinfo, bus_info) == 100);
LP_ASSERT(val_data, offsetof(struct ethtool_value, data) == 4);
LP_ASSERT(ring_tx, offsetof(struct ethtool_ringparam, tx_pending) == 32);
LP_ASSERT(cmd_drv, ETHTOOL_GDRVINFO == 0x3);
LP_ASSERT(cmd_link, ETHTOOL_GLINK == 0xa);
LP_ASSERT(cmd_ring, ETHTOOL_GRINGPARAM == 0x10);
LP_ASSERT(siocethtool, SIOCETHTOOL == 0x8946);
LP_ASSERT(ifnamsiz, IFNAMSIZ == 16);
#ifndef LP_HOST
/* 讀 toolchain asm/unistd.h:284 and arch/rlx/include/asm/unistd.h:284, both
 * `(__NR_Linux + 263)` with __NR_Linux 4000 at :20. */
LP_ASSERT(nr_clock_gettime, SYS_clock_gettime == 4263);
#endif

/* ---------------------------------------------------------------------------
 * Output
 * ------------------------------------------------------------------------- */

static void lp_write(const char *s, unsigned n)
{
	unsigned done = 0u;

	while (done < n) {
		int k = (int)write(1, s + done, n - done);

		if (k <= 0)
			return;		/* a closed console is not a finding */
		done += (unsigned)k;
	}
}

static void lp_puts(const char *s)
{
	unsigned n = 0u;

	while (s[n] != '\0')
		n++;
	lp_write(s, n);
}

static const char lp_hx[] = "0123456789ABCDEF";

static void lp_hex32(u32 v)
{
	char b[8];
	int i;

	for (i = 7; i >= 0; i--) {
		b[i] = lp_hx[v & 0xfu];
		v >>= 4;
	}
	lp_write(b, 8u);
}

/* Decimal by subtraction.  `drop` removes that many low digits (6 turns a
 * nanosecond count into milliseconds, truncating), which is how this file
 * divides without dividing. */
static const u64 lp_p10[20] = {
	10000000000000000000ull, 1000000000000000000ull, 100000000000000000ull,
	10000000000000000ull, 1000000000000000ull, 100000000000000ull,
	10000000000000ull, 1000000000000ull, 100000000000ull, 10000000000ull,
	1000000000ull, 100000000ull, 10000000ull, 1000000ull, 100000ull,
	10000ull, 1000ull, 100ull, 10ull, 1ull
};

static void lp_dec_drop(u64 v, unsigned drop)
{
	char b[20];
	unsigned i, n = 0u;
	int started = 0;

	for (i = 0u; i + drop < 20u; i++) {
		char d = '0';

		while (v >= lp_p10[i]) {
			v -= lp_p10[i];
			d++;
		}
		if (d != '0' || started || i + drop == 19u) {
			b[n++] = d;
			started = 1;
		}
	}
	lp_write(b, n);
}

static void lp_dec(u64 v)
{
	lp_dec_drop(v, 0u);
}

/* A kernel string field: printable ASCII, `\xHH` for anything else and for
 * `"` and `\`; `nonul` when the field has no NUL in its `n` bytes. */
static void lp_field(const char *key, const unsigned char *f, unsigned n)
{
	unsigned i, len = n;
	char e[4];

	lp_puts(" ");
	lp_puts(key);
	for (i = 0u; i < n; i++)
		if (f[i] == 0u) {
			len = i;
			break;
		}
	if (len == n) {
		lp_puts(" nonul");
		return;
	}
	lp_puts(" \"");
	for (i = 0u; i < len; i++) {
		unsigned char c = f[i];

		if (c >= 0x20u && c <= 0x7eu && c != '"' && c != '\\') {
			lp_write((const char *)&f[i], 1u);
		} else {
			e[0] = '\\';
			e[1] = 'x';
			e[2] = lp_hx[(c >> 4) & 0xfu];
			e[3] = lp_hx[c & 0xfu];
			lp_write(e, 4u);
		}
	}
	lp_puts("\"");
}

/* ---------------------------------------------------------------------------
 * The system shims.  Everything that reaches the kernel goes through one of
 * these (and lp_open, below), which is what lets LP_HOST replace exactly
 * them.
 * ------------------------------------------------------------------------- */

#ifdef LP_HOST
extern int lp_fake_socket(void);
extern int lp_fake_ioctl(int fd, unsigned long req, struct ifreq *ifr);
extern u64 lp_fake_now_ns(void);
extern void lp_fake_sleep_ms(u32 ms);
#endif

/* -> 0, or the positive errno. */
static int lp_ioctl(int fd, struct ifreq *ifr)
{
#ifdef LP_HOST
	return lp_fake_ioctl(fd, (unsigned long)SIOCETHTOOL, ifr);
#else
	if (ioctl(fd, SIOCETHTOOL, ifr) == 0)
		return 0;
	return errno > 0 ? errno : 255;
#endif
}

static u64 lp_now_ns(void)
{
#ifdef LP_HOST
	return lp_fake_now_ns();
#else
	struct timespec ts;

	ts.tv_sec = 0;
	ts.tv_nsec = 0;
	if (syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &ts) != 0)
		return 0ull;	/* the capture's .timing rows are the fallback */
	return (u64)(unsigned long)ts.tv_sec * 1000000000ull +
	       (u64)(unsigned long)ts.tv_nsec;
#endif
}

static void lp_sleep_ms(u32 ms)
{
#ifdef LP_HOST
	lp_fake_sleep_ms(ms);
#else
	struct timespec req;
	u32 s = 0u;

	while (ms >= 1000u) {		/* at most ten turns: ms <= 10,000 */
		ms -= 1000u;
		s++;
	}
	req.tv_sec = (time_t)s;
	req.tv_nsec = (long)ms * 1000000L;
	(void)nanosleep(&req, 0);
#endif
}

/* ---------------------------------------------------------------------------
 * The request table.  Three reads; no set.
 * ------------------------------------------------------------------------- */

#define LP_CANARY 0xA5u

union lp_buf {
	struct ethtool_drvinfo drv;
	struct ethtool_value val;
	struct ethtool_ringparam ring;
	unsigned char b[sizeof(struct ethtool_drvinfo)];
};

struct lp_req {
	const char *name;
	u32 cmd;
	unsigned size;
};

static const struct lp_req lp_reqs[3] = {
	{ "drv",  ETHTOOL_GDRVINFO,   sizeof(struct ethtool_drvinfo) },
	{ "link", ETHTOOL_GLINK,      sizeof(struct ethtool_value) },
	{ "ring", ETHTOOL_GRINGPARAM, sizeof(struct ethtool_ringparam) },
};

#define LP_REQ_LINK 1u

static union lp_buf lp_b;
static u32 lp_n_calls, lp_n_ok, lp_n_refused, lp_n_nowrite;

static unsigned lp_strlen(const char *s)
{
	unsigned n = 0u;

	while (s[n] != '\0')
		n++;
	return n;
}

/* One call.  -> rc (0 or errno); `*can` gets the canary bytes left past
 * `cmd`.  The buffer is filled BEFORE every call, so a stale value from the
 * previous call can never be read as this one's. */
static int lp_call(int fd, const char *ifname, const struct lp_req *r,
		   unsigned *can)
{
	struct ifreq ifr;
	unsigned i, n;
	int rc;

	for (i = 0u; i < sizeof(lp_b.b); i++)
		lp_b.b[i] = (unsigned char)LP_CANARY;
	lp_b.val.cmd = r->cmd;		/* cmd is the first word of all three */

	for (i = 0u; i < sizeof(ifr); i++)
		((unsigned char *)&ifr)[i] = 0u;
	n = lp_strlen(ifname);		/* < IFNAMSIZ: checked by the caller */
	for (i = 0u; i < n; i++)
		ifr.ifr_name[i] = ifname[i];
	ifr.ifr_data = (void *)&lp_b;

	rc = lp_ioctl(fd, &ifr);

	n = 0u;
	for (i = 4u; i < r->size; i++)
		if (lp_b.b[i] == (unsigned char)LP_CANARY)
			n++;
	*can = n;

	lp_n_calls++;
	if (rc == 0) {
		lp_n_ok++;
		if (n == r->size - 4u)
			lp_n_nowrite++;
	} else {
		lp_n_refused++;
	}
	return rc;
}

static void lp_pair(const char *k, u32 pending, u32 max)
{
	lp_puts(" ");
	lp_puts(k);
	lp_puts(" ");
	lp_dec(pending);
	lp_puts("/");
	lp_dec(max);
}

static void lp_line(const char *ifname, const struct lp_req *r, int rc,
		    unsigned can)
{
	lp_puts("LP ");
	lp_puts(r->name);
	lp_puts(" ");
	lp_puts(ifname);
	lp_puts(" rc ");
	lp_dec((u32)rc);
	if (rc == 0) {
		if (r->cmd == ETHTOOL_GDRVINFO) {
			lp_field("driver", (const unsigned char *)lp_b.drv.driver, 32u);
			lp_field("version", (const unsigned char *)lp_b.drv.version, 32u);
			lp_field("fw", (const unsigned char *)lp_b.drv.fw_version, 32u);
			lp_field("bus", (const unsigned char *)lp_b.drv.bus_info, 32u);
		} else if (r->cmd == ETHTOOL_GLINK) {
			lp_puts(" data ");
			lp_hex32(lp_b.val.data);
		} else {
			lp_pair("rx", lp_b.ring.rx_pending, lp_b.ring.rx_max_pending);
			lp_pair("mini", lp_b.ring.rx_mini_pending,
				lp_b.ring.rx_mini_max_pending);
			lp_pair("jumbo", lp_b.ring.rx_jumbo_pending,
				lp_b.ring.rx_jumbo_max_pending);
			lp_pair("tx", lp_b.ring.tx_pending, lp_b.ring.tx_max_pending);
		}
	}
	lp_puts(" can ");
	lp_dec(can);
	lp_puts("\n");
}

/* ---------------------------------------------------------------------------
 * Arguments
 * ------------------------------------------------------------------------- */

static int lp_refuse(const char *why)
{
	lp_puts("LPE ");
	lp_puts(why);
	lp_puts("\n");
	return 2;
}

/* Decimal, by hand: `atoi` on a string that is not a number is undefined.
 * -> 0 and *out, or -1 for anything that is not 1-9 digits. */
static int lp_num(const char *s, u32 *out)
{
	u32 v = 0u;
	unsigned k;

	if (s == 0 || s[0] == '\0')
		return -1;
	for (k = 0u; s[k] != '\0'; k++) {
		if (k >= 9u || s[k] < '0' || s[k] > '9')
			return -1;
		v = v * 10u + (u32)(s[k] - '0');
	}
	*out = v;
	return 0;
}

static int lp_ifname_ok(const char *s)
{
	unsigned n = lp_strlen(s);

	return n >= 1u && n < (unsigned)IFNAMSIZ;
}

static int lp_open(void)
{
#ifdef LP_HOST
	return lp_fake_socket();
#else
	return socket(AF_INET, SOCK_DGRAM, 0);
#endif
}

#define LP_GET_MAX_IF	8
#define LP_MS_MIN	10u
#define LP_MS_MAX	10000u
#define LP_S_MIN	1u
#define LP_S_MAX	600u

static int lp_get(int argc, char **argv)
{
	int i, fd;
	unsigned q, can;

	if (argc < 3 || argc > 2 + LP_GET_MAX_IF)
		return lp_refuse("get takes 1 to 8 interface names");
	for (i = 2; i < argc; i++)
		if (!lp_ifname_ok(argv[i]))
			return lp_refuse("ifname must be 1 to 15 characters");
	fd = lp_open();
	if (fd < 0) {
		lp_puts("LPE socket rc ");
		lp_dec((u32)errno);
		lp_puts("\n");
		return 3;
	}
	for (i = 2; i < argc; i++)
		for (q = 0u; q < 3u; q++) {
			int rc = lp_call(fd, argv[i], &lp_reqs[q], &can);

			lp_line(argv[i], &lp_reqs[q], rc, can);
		}
	lp_puts("LP9 calls ");
	lp_dec(lp_n_calls);
	lp_puts(" ok ");
	lp_dec(lp_n_ok);
	lp_puts(" refused ");
	lp_dec(lp_n_refused);
	lp_puts(" nowrite ");
	lp_dec(lp_n_nowrite);
	lp_puts("\n");
	return 0;
}

/* One GLINK sample -> its class: 0 err, 1 nowrite, 2 zero, 3 one, 4 other. */
static unsigned lp_sample(int fd, const char *ifname, int *rc, u32 *v)
{
	unsigned can;

	*rc = lp_call(fd, ifname, &lp_reqs[LP_REQ_LINK], &can);
	*v = lp_b.val.data;
	if (*rc != 0)
		return 0u;
	if (can == 4u)
		return 1u;
	if (*v == 0u)
		return 2u;
	if (*v == 1u)
		return 3u;
	return 4u;
}

static void lp_wv(u32 v, int rc)
{
	lp_puts(" v ");
	lp_dec(v);
	lp_puts(" rc ");
	lp_dec((u32)rc);
}

static int lp_watch(int argc, char **argv)
{
	u32 ms, s, cls_n[5], v, v0, n, trans;
	u64 t0, total_ns, sched, el;
	int fd, rc, rc0;
	unsigned c, k;

	if (argc != 5)
		return lp_refuse("watch takes <if> <ms> <s>");
	if (!lp_ifname_ok(argv[2]))
		return lp_refuse("ifname must be 1 to 15 characters");
	if (lp_num(argv[3], &ms) != 0 || ms < LP_MS_MIN || ms > LP_MS_MAX)
		return lp_refuse("ms must be 10 to 10000");
	if (lp_num(argv[4], &s) != 0 || s < LP_S_MIN || s > LP_S_MAX)
		return lp_refuse("s must be 1 to 600");
	fd = lp_open();
	if (fd < 0) {
		lp_puts("LPE socket rc ");
		lp_dec((u32)errno);
		lp_puts("\n");
		return 3;
	}
	for (k = 0u; k < 5u; k++)
		cls_n[k] = 0u;
	total_ns = (u64)s * 1000000000ull;
	t0 = lp_now_ns();
	c = lp_sample(fd, argv[2], &rc0, &v0);
	cls_n[c]++;
	n = 1u;
	trans = 0u;
	lp_puts("LPW start ");
	lp_puts(argv[2]);
	lp_wv(v0, rc0);
	lp_puts("\n");
	sched = 0ull;
	for (;;) {
		/* The schedule counter: sample k is taken only if k*ms <= s*1000,
		 * so n <= floor(s*1000/ms) + 1 whatever the clock does. */
		sched += (u64)ms * 1000000ull;
		if (sched > total_ns)
			break;
		el = lp_now_ns() - t0;
		if (el >= total_ns)
			break;
		lp_sleep_ms(ms);
		c = lp_sample(fd, argv[2], &rc, &v);
		cls_n[c]++;
		if (rc != rc0 || (rc == 0 && v != v0)) {
			trans++;
			lp_puts("LPW t ");
			lp_dec_drop(lp_now_ns() - t0, 6u);
			lp_puts(" i ");
			lp_dec(n);
			lp_wv(v, rc);
			lp_puts("\n");
			rc0 = rc;
			v0 = v;
		}
		n++;
	}
	el = lp_now_ns() - t0;
	lp_puts("LPW end n ");
	lp_dec(n);
	lp_puts(" ms ");
	lp_dec_drop(el, 6u);
	lp_puts(" ones ");
	lp_dec(cls_n[3]);
	lp_puts(" zeros ");
	lp_dec(cls_n[2]);
	lp_puts(" other ");
	lp_dec(cls_n[4]);
	lp_puts(" err ");
	lp_dec(cls_n[0]);
	lp_puts(" nowrite ");
	lp_dec(cls_n[1]);
	lp_puts(" trans ");
	lp_dec(trans);
	lp_puts("\n");
	return 0;
}

int main(int argc, char **argv)
{
	const char *m;

	lp_puts("LP0 linkprobe " LP_VERSION " build " LP_BUILD_ID "\n");
	if (argc < 2)
		return lp_refuse("usage: linkprobe get <if>... | watch <if> <ms> <s>");
	m = argv[1];
	if (m[0] == 'g' && m[1] == 'e' && m[2] == 't' && m[3] == '\0')
		return lp_get(argc, argv);
	if (m[0] == 'w' && m[1] == 'a' && m[2] == 't' && m[3] == 'c' &&
	    m[4] == 'h' && m[5] == '\0')
		return lp_watch(argc, argv);
	return lp_refuse("unknown mode");
}
