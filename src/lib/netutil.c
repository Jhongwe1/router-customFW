/* netutil.c -- R7: see netutil.h for why this exists.
 *
 * ---------------------------------------------------------------------------
 * WHAT THE PARSER REFUSES, AND WHY EACH REFUSAL IS SEPARATE
 * ---------------------------------------------------------------------------
 *
 * `inet_aton` accepts "1.2.3", "0x7f.1", "017.1.1.1" and "1.2.3.4 " -- four
 * shapes that mean different things to different resolvers, which is how a
 * lease value ends up meaning one address to `ifupd` and another to whatever
 * reads the file it wrote.  This parser accepts exactly four decimal octets of
 * one to three digits with no leading zero, separated by single dots, with
 * nothing before and nothing after.  Every other shape gets its own NU_E_*
 * code, because a test that only asserts "refused" cannot tell a refusal for
 * the right reason from one for the wrong reason.
 */

#include "netutil.h"

#include <errno.h>
#include <string.h>

#include <sys/ioctl.h>
#include <sys/socket.h>
#include <net/if.h>
#include <net/route.h>
#include <netinet/in.h>
#include <unistd.h>

static const char *const nu_err_tok[NU_E_MAX] = {
	"ok", "empty", "too-long", "bad-char", "octet-too-long",
	"leading-zero", "octet-over-255", "not-four-octets", "misplaced-dot",
	"mask-not-contiguous", "prefix-out-of-range", "no-room",
	"bad-ifname", "socket-failed", "ioctl-failed", "net-not-open"
};

const char *nu_strerror(int rc)
{
	int e = rc < 0 ? -rc : rc;
	if (e < 0 || e >= NU_E_MAX)
		return "unknown";
	return nu_err_tok[e];
}

/* ------------------------------------------------------------------ parsing */

int nu_parse_ipv4_n(const char *s, size_t n, uint32_t *out)
{
	uint32_t acc = 0;
	size_t i = 0;
	int oct;

	if (out == NULL || s == NULL)
		return -NU_E_EMPTY;
	if (n == 0)
		return -NU_E_EMPTY;
	if (n > NU_QUAD_MAX)
		return -NU_E_LONG;

	for (oct = 0; oct < 4; oct++) {
		unsigned v = 0;
		int digits = 0;

		if (oct > 0) {
			if (i >= n)
				return -NU_E_FIELDS; /* ran out: "1.2.3" */
			if (s[i] != '.')
				return -NU_E_DOT;
			i++;
		}
		if (i >= n)
			return -NU_E_FIELDS;
		/* A dot or any non-digit where a digit is due.  The ordering
		 * matters: '.' is reported as a misplaced dot and everything
		 * else (space, '+', '-', NUL, a letter) as a bad character. */
		if (s[i] == '.')
			return -NU_E_DOT;
		if (s[i] < '0' || s[i] > '9')
			return -NU_E_CHAR;
		if (s[i] == '0' && i + 1 < n && s[i + 1] >= '0' && s[i + 1] <= '9')
			return -NU_E_LEADZERO;
		while (i < n && s[i] >= '0' && s[i] <= '9') {
			if (++digits > 3)
				return -NU_E_OCTLEN;
			v = v * 10u + (unsigned)(s[i] - '0');
			i++;
		}
		if (v > 255u)
			return -NU_E_RANGE;
		/* The byte that stopped the digit run must be a dot, and only
		 * between octets.  Anything else is a bad character. */
		if (i < n && s[i] != '.')
			return -NU_E_CHAR;
		acc = (acc << 8) | v;
	}
	if (i != n)
		return -NU_E_FIELDS; /* a fifth octet: "1.2.3.4.5" */
	*out = acc;
	return 0;
}

int nu_parse_ipv4(const char *s, uint32_t *out)
{
	size_t n;

	if (s == NULL)
		return -NU_E_EMPTY;
	/* Bounded look for the NUL: a 4 KB value costs 16 reads and NU_E_LONG. */
	for (n = 0; n <= NU_QUAD_MAX; n++)
		if (s[n] == '\0')
			return nu_parse_ipv4_n(s, n, out);
	return -NU_E_LONG;
}

int nu_format_ipv4(uint32_t ip, char *out, size_t n)
{
	char buf[NU_QUAD_BUF];
	size_t len = 0;
	int oct;

	if (out == NULL || n == 0)
		return -NU_E_SPACE;
	for (oct = 3; oct >= 0; oct--) {
		unsigned v = (ip >> (8 * oct)) & 0xFFu;
		if (oct != 3)
			buf[len++] = '.';
		if (v >= 100u)
			buf[len++] = (char)('0' + v / 100u);
		if (v >= 10u)
			buf[len++] = (char)('0' + (v / 10u) % 10u);
		buf[len++] = (char)('0' + v % 10u);
	}
	if (len + 1 > n)
		return -NU_E_SPACE;
	memcpy(out, buf, len);
	out[len] = '\0';
	return (int)len;
}

/* ----------------------------------------------------------------- netmasks */

int nu_mask_prefix(uint32_t mask)
{
	int p = 0;
	uint32_t bit = 0x80000000u;

	while (p < 32 && (mask & bit) != 0) {
		p++;
		bit >>= 1;
	}
	if (p < 32) {
		/* p < 32, so the shift is 0..31 and defined. */
		if ((mask & (0xFFFFFFFFu >> p)) != 0)
			return -NU_E_MASK;
	}
	return p;
}

int nu_mask_ok(uint32_t mask, int lo, int hi)
{
	int p = nu_mask_prefix(mask);

	if (p < 0)
		return p;
	if (p < lo || p > hi)
		return -NU_E_PREFIX;
	return 0;
}

int nu_is_unicast(uint32_t ip)
{
	if (ip == 0u || ip == 0xFFFFFFFFu)
		return 0;
	if ((ip >> 24) == 127u)
		return 0;
	if ((ip >> 28) >= 0xEu)  /* 224/4 multicast and 240/4 class E */
		return 0;
	return 1;
}

int nu_is_net_or_bcast(uint32_t ip, uint32_t mask)
{
	uint32_t host = ip & ~mask;

	if (mask == 0xFFFFFFFFu)
		return 0; /* /32: the address is the subnet */
	return host == 0u || host == (~mask & 0xFFFFFFFFu);
}

int nu_ifname_ok(const char *name)
{
	size_t i;

	if (name == NULL || name[0] == '\0')
		return -NU_E_IFNAME;
	for (i = 0; i < (size_t)NU_IFNAME_MAX; i++) {
		char c = name[i];
		if (c == '\0')
			return 0;
		if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
		    (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-')
			continue;
		return -NU_E_IFNAME;
	}
	/* NU_IFNAME_MAX legal bytes; the next one must be the NUL. */
	return name[NU_IFNAME_MAX] == '\0' ? 0 : -NU_E_IFNAME;
}

/* ------------------------------------------------------- the syscall layer */

static int real_open(void *ctx)
{
	(void)ctx;
	return socket(AF_INET, SOCK_DGRAM, 0);
}

static int real_close(void *ctx, int fd)
{
	(void)ctx;
	return close(fd);
}

static int real_ioctl(void *ctx, int fd, unsigned long req, void *arg)
{
	(void)ctx;
	return ioctl(fd, req, arg);
}

const struct nu_ops *nu_ops_real(void)
{
	static const struct nu_ops ops = { real_open, real_close, real_ioctl, NULL };
	return &ops;
}

int nu_net_open(struct nu_net *n, const struct nu_ops *ops)
{
	int fd;

	if (n == NULL || ops == NULL)
		return -NU_E_SOCK;
	n->ops = ops;
	n->open = 0;
	n->fd = -1;
	n->last_errno = 0;
	fd = ops->sock_open(ops->ctx);
	if (fd < 0) {
		n->last_errno = errno;
		return -NU_E_SOCK;
	}
	n->fd = fd;
	n->open = 1;
	return 0;
}

void nu_net_close(struct nu_net *n)
{
	if (n == NULL || !n->open)
		return;
	n->ops->sock_close(n->ops->ctx, n->fd);
	n->open = 0;
	n->fd = -1;
}

int nu_errno(const struct nu_net *n)
{
	return n == NULL ? 0 : n->last_errno;
}

/* Fill an ifreq's name and its sockaddr_in payload.  `struct ifreq` is memset
 * whole: the kernel reads the union past the address on some requests, and a
 * stack-residue byte there would be an uninitialised read the sanitiser is
 * right to complain about. */
static int ifreq_prep(struct ifreq *r, const char *ifname)
{
	int rc = nu_ifname_ok(ifname);
	size_t len;

	if (rc != 0)
		return rc;
	memset(r, 0, sizeof(*r));
	len = strlen(ifname);
	memcpy(r->ifr_name, ifname, len); /* len <= 15, ifr_name is 16 */
	return 0;
}

static void sin_set(struct sockaddr *sa, uint32_t ip)
{
	struct sockaddr_in sin;

	memset(&sin, 0, sizeof(sin));
	sin.sin_family = AF_INET;
	sin.sin_port = 0;
	/* Explicit shifts, never a memcpy of a host-order word: this file is
	 * compiled for a big-endian target and tested on a little-endian host. */
	sin.sin_addr.s_addr = htonl(ip);
	memcpy(sa, &sin, sizeof(sin));
}

static int do_ioctl(struct nu_net *n, unsigned long req, void *arg)
{
	if (n == NULL || !n->open)
		return -NU_E_NOTOPEN;
	if (n->ops->sock_ioctl(n->ops->ctx, n->fd, req, arg) < 0) {
		n->last_errno = errno;
		return -NU_E_IOCTL;
	}
	return 0;
}

int nu_if_set_addr(struct nu_net *n, const char *ifname, uint32_t ip)
{
	struct ifreq r;
	int rc = ifreq_prep(&r, ifname);

	if (rc != 0)
		return rc;
	sin_set(&r.ifr_addr, ip);
	return do_ioctl(n, SIOCSIFADDR, &r);
}

int nu_if_set_mask(struct nu_net *n, const char *ifname, uint32_t mask)
{
	struct ifreq r;
	int rc = ifreq_prep(&r, ifname);

	if (rc != 0)
		return rc;
	/* `ifr_addr` and not `ifr_netmask`: they are the same union member and
	 * the same offset, the kernel's `devinet_ioctl` reads that offset for
	 * SIOCSIFNETMASK, and uClibc 0.9.30's `net/if.h` is not guaranteed to
	 * carry the `ifr_netmask` alias. */
	sin_set(&r.ifr_addr, mask);
	return do_ioctl(n, SIOCSIFNETMASK, &r);
}

int nu_if_set_flags(struct nu_net *n, const char *ifname, int up)
{
	struct ifreq r;
	int rc = ifreq_prep(&r, ifname);

	if (rc != 0)
		return rc;
	/* Read-modify-write: clobbering the whole word would clear IFF_MULTICAST
	 * and IFF_BROADCAST, which the driver set at registration. */
	rc = do_ioctl(n, SIOCGIFFLAGS, &r);
	if (rc != 0)
		return rc;
	/* IFF_UP only.  IFF_RUNNING is the driver's to set (it follows carrier),
	 * and `dev_change_flags` would ignore it anyway. */
	if (up)
		r.ifr_flags = (short)(r.ifr_flags | IFF_UP);
	else
		r.ifr_flags = (short)(r.ifr_flags & ~IFF_UP);
	return do_ioctl(n, SIOCSIFFLAGS, &r);
}

int nu_if_get_flags(struct nu_net *n, const char *ifname, unsigned *flags)
{
	struct ifreq r;
	int rc = ifreq_prep(&r, ifname);

	if (rc != 0)
		return rc;
	rc = do_ioctl(n, SIOCGIFFLAGS, &r);
	if (rc != 0)
		return rc;
	if (flags != NULL)
		*flags = (unsigned)(unsigned short)r.ifr_flags;
	return 0;
}

static int route_prep(struct rtentry *rt, char *devbuf, size_t devn,
		      const char *ifname, uint32_t gw)
{
	int rc = nu_ifname_ok(ifname);
	size_t len;

	if (rc != 0)
		return rc;
	len = strlen(ifname);
	if (len + 1 > devn)
		return -NU_E_IFNAME;
	memset(rt, 0, sizeof(*rt));
	memset(devbuf, 0, devn);
	memcpy(devbuf, ifname, len);
	sin_set(&rt->rt_dst, 0u);      /* 0.0.0.0 ... */
	sin_set(&rt->rt_genmask, 0u);  /* ... /0 */
	sin_set(&rt->rt_gateway, gw);
	rt->rt_flags = RTF_UP | RTF_GATEWAY;
	rt->rt_dev = devbuf;
	rt->rt_metric = 0;
	return 0;
}

int nu_route_default_add(struct nu_net *n, const char *ifname, uint32_t gw)
{
	struct rtentry rt;
	char dev[NU_IFNAME_MAX + 1];
	int rc = route_prep(&rt, dev, sizeof(dev), ifname, gw);

	if (rc != 0)
		return rc;
	return do_ioctl(n, SIOCADDRT, &rt);
}

int nu_route_default_del(struct nu_net *n, const char *ifname, uint32_t gw)
{
	struct rtentry rt;
	char dev[NU_IFNAME_MAX + 1];
	int rc = route_prep(&rt, dev, sizeof(dev), ifname, gw);

	if (rc != 0)
		return rc;
	rc = do_ioctl(n, SIOCDELRT, &rt);
	/* Deleting a route that is not there is the normal case for the first
	 * `deconfig` of a boot, and it is not a failure. */
	if (rc == -NU_E_IOCTL &&
	    (n->last_errno == ESRCH || n->last_errno == ENOENT))
		return 0;
	return rc;
}
