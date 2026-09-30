/* netutil.h -- R7: dotted-quad parsing and formatting, netmask validation, and
 * the `ioctl` calls that set an interface address and a default route.
 *
 * ---------------------------------------------------------------------------
 * WHY IT EXISTS
 * ---------------------------------------------------------------------------
 *
 * Two programs need to configure an interface without a shell: `init` (the LAN,
 * from the config store) and `ifupd` (the WAN, from a DHCP lease).  `ifconfig`
 * and `route` are busybox applets, so using them would mean exec'ing a
 * multi-call binary with an argv assembled from a DHCP server's bytes.  These
 * functions replace them with `SIOCSIFADDR`, `SIOCSIFNETMASK`, `SIOCSIFFLAGS`,
 * `SIOCADDRT` and `SIOCDELRT`.
 *
 * The parser is the security boundary.  `ifupd`'s inputs come from a DHCP
 * server on the WAN, which is to say from whoever is upstream; every value is
 * length-bounded before it is looked at, and every value that reaches a file or
 * an `ioctl` has been through `nu_parse_ipv4*` and is carried from there on as
 * a `uint32_t`, never as text.  Nothing in this file allocates, recurses, or
 * calls `strcpy`, `sprintf`, `atoi`, `strtol` or `inet_addr`.
 *
 * ---------------------------------------------------------------------------
 * THE SYSCALL LAYER IS INJECTABLE
 * ---------------------------------------------------------------------------
 *
 * `struct nu_ops` is the only way this file reaches the kernel, so the host
 * tests run the real `struct ifreq` / `struct rtentry` filling code without
 * root and without a network.  `nu_ops_real()` is the production one.  The
 * fake is in `src/ifupd/test_ifupd.c`: it decodes the same structures the
 * kernel would and records the interface state they describe, so what the test
 * checks is the bytes handed to `ioctl`, not a mock of this interface.
 */

#ifndef RLXFW_NETUTIL_H
#define RLXFW_NETUTIL_H

#include <stddef.h>
#include <stdint.h>

/* Named reasons.  Every function returns 0 / a count on success or -NU_E_* on
 * failure; `nu_strerror` maps one to a short stable token that goes on the
 * console and into the tests' expectations.  Never NULL, never a sentence. */
enum {
	NU_E_OK = 0,
	NU_E_EMPTY = 1,   /* zero-length input */
	NU_E_LONG,        /* input longer than the field's maximum */
	NU_E_CHAR,        /* a byte outside [0-9.] (space, sign, NUL, letter) */
	NU_E_OCTLEN,      /* an octet of more than 3 digits */
	NU_E_LEADZERO,    /* an octet with a leading zero ("01", "007") */
	NU_E_RANGE,       /* an octet above 255 */
	NU_E_FIELDS,      /* not exactly four octets */
	NU_E_DOT,         /* a dot where a digit was due, or a trailing dot */
	NU_E_MASK,        /* netmask bits are not contiguous */
	NU_E_PREFIX,      /* prefix length outside the caller's range */
	NU_E_SPACE,       /* output buffer too small */
	NU_E_IFNAME,      /* interface name empty, too long, or bad charset */
	NU_E_SOCK,        /* socket() failed */
	NU_E_IOCTL,       /* the ioctl failed; nu_errno() carries errno */
	NU_E_NOTOPEN,     /* nu_net used before nu_net_open */
	NU_E_MAX
};

const char *nu_strerror(int rc); /* accepts 0, NU_E_*, or -NU_E_* */

/* strlen("255.255.255.255"); NU_QUAD_BUF is that plus the NUL. */
#define NU_QUAD_MAX 15
#define NU_QUAD_BUF 16

/* IFNAMSIZ is 16 in the kernel; the name plus its NUL must fit. */
#define NU_IFNAME_MAX 15

/* ---------------------------------------------------------------- parsing */

/* Parse exactly `n` bytes as a dotted quad.  `s` needs no NUL and is never
 * read past `n`; a NUL inside `n` is NU_E_CHAR, not a terminator.  On success
 * `*out` is the address in HOST byte order and the return is 0. */
int nu_parse_ipv4_n(const char *s, size_t n, uint32_t *out);

/* Same, for a NUL-terminated string.  Refuses before parsing if there is no
 * NUL within NU_QUAD_MAX+1 bytes (NU_E_LONG), so a 4 KB environment value
 * costs 16 byte reads. */
int nu_parse_ipv4(const char *s, uint32_t *out);

/* Write the dotted form of a host-order address.  Returns the number of bytes
 * written excluding the NUL, or -NU_E_SPACE.  The output alphabet is exactly
 * [0-9.] -- this is what lets /run/wan.dns be data rather than a script. */
int nu_format_ipv4(uint32_t ip, char *out, size_t n);

/* ---------------------------------------------------------------- netmasks */

/* Prefix length 0..32 of a contiguous mask, or -NU_E_MASK.  255.0.255.0 is
 * -NU_E_MASK; 0.0.0.0 is 0 and 255.255.255.255 is 32. */
int nu_mask_prefix(uint32_t mask);

/* Contiguity plus a prefix range, both ends inclusive (the schema's LAN rule
 * is nu_mask_ok(m, 8, 30)).  0 on success, -NU_E_MASK or -NU_E_PREFIX. */
int nu_mask_ok(uint32_t mask, int lo, int hi);

/* 1 when `ip` is a plausible host address: not 0.0.0.0, not 127/8, not
 * 224/4 or above (multicast and class E), not 255.255.255.255. */
int nu_is_unicast(uint32_t ip);

/* 1 when `ip` is the network or the all-ones broadcast address of its own
 * subnet.  Both are refused as host addresses. */
int nu_is_net_or_bcast(uint32_t ip, uint32_t mask);

/* 0 when `name` is 1..NU_IFNAME_MAX bytes of [A-Za-z0-9._-] with no NUL
 * inside, else -NU_E_IFNAME.  Bounded: never reads past NU_IFNAME_MAX+1. */
int nu_ifname_ok(const char *name);

/* ------------------------------------------------------- the syscall layer */

struct nu_ops {
	/* An AF_INET SOCK_DGRAM handle, or -1.  Any non-negative value is
	 * opaque to this file. */
	int (*sock_open)(void *ctx);
	int (*sock_close)(void *ctx, int fd);
	/* Exactly ioctl(fd, req, arg); -1 on failure with errno set. */
	int (*sock_ioctl)(void *ctx, int fd, unsigned long req, void *arg);
	void *ctx;
};

const struct nu_ops *nu_ops_real(void);

struct nu_net {
	const struct nu_ops *ops;
	int fd;
	int open;
	int last_errno; /* errno of the most recent failing ioctl */
};

int nu_net_open(struct nu_net *n, const struct nu_ops *ops);
void nu_net_close(struct nu_net *n);
int nu_errno(const struct nu_net *n);

/* Each of these validates `ifname` first and returns 0 or -NU_E_*. */
int nu_if_set_addr(struct nu_net *n, const char *ifname, uint32_t ip);
int nu_if_set_mask(struct nu_net *n, const char *ifname, uint32_t mask);
int nu_if_set_flags(struct nu_net *n, const char *ifname, int up);
int nu_if_get_flags(struct nu_net *n, const char *ifname, unsigned *flags);

/* Default route (0.0.0.0/0) through `gw` on `ifname`.  The caller has already
 * checked that `gw` is reachable: this issues the ioctl and nothing else.
 * `nu_route_default_del` treats "no such route" (ESRCH/ENOENT) as success, so
 * a `deconfig` before any `bound` is not an error. */
int nu_route_default_add(struct nu_net *n, const char *ifname, uint32_t gw);
int nu_route_default_del(struct nu_net *n, const char *ifname, uint32_t gw);

#endif /* RLXFW_NETUTIL_H */
