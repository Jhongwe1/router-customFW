/* netcfg.h -- R7: what `ifupd` does with a DHCP lease, as one testable function.
 *
 * ---------------------------------------------------------------------------
 * THE INPUT IS HOSTILE
 * ---------------------------------------------------------------------------
 *
 * busybox `udhcpc` `execve`s its `-s` script with the lease in the environment.
 * Whoever answers the DISCOVER on the WAN chooses `ip`, `subnet`, `router` and
 * `dns`; `udhcpc` copies option bytes into the environment with very little
 * opinion about them.  So every value here is an attacker's string, and the
 * vendor's answer -- a `/usr/share/udhcpc/default.script` that `eval`s some of
 * it and hands the rest to `ifconfig` and `route` -- is the single largest
 * reason this gate exists.
 *
 * The rules, all of them:
 *   * exactly five names are read: event, interface, ip, subnet, router, dns.
 *     `mtu`, `lease`, `domain`, `hostname`, `serverid` and everything else are
 *     never looked at, so they cannot be mis-parsed.
 *   * every read is length-bounded BEFORE the value is examined, so a 4 KB
 *     `subnet` costs sixteen byte reads and a named refusal.
 *   * every value that survives is a `uint32_t` from then on.  Nothing that
 *     reaches an `ioctl` or a file is a copy of an environment byte.
 *   * ip, subnet and interface are all validated before the first `ioctl`, so a
 *     refusal leaves the interface exactly as it was.
 *   * the one deliberate partial: a bad `router` does not throw away a good
 *     address.  The address is applied, the route is refused by name, and the
 *     result is IFU_PARTIAL.
 *   * nothing is executed.  `/run/wan.dns` is written from `nu_format_ipv4`, so
 *     its byte alphabet is [0-9.\n] by construction -- it cannot be a script
 *     even if something later reads it with the wrong tool.
 */

#ifndef RLXFW_IFUPD_NETCFG_H
#define RLXFW_IFUPD_NETCFG_H

#include <stdint.h>

#include "../lib/netutil.h"

#define IFU_DNS_MAX 3        /* SPEC § 3: /run/wan.dns is at most 3 lines */
#define IFU_NOTE_MAX 8
#define IFU_DNS_SCAN 256     /* bytes of `dns` ever read; the rest is ignored */
#define PATH_WAN_DNS "/run/wan.dns"

enum ifu_rc { IFU_OK = 0, IFU_PARTIAL = 1, IFU_REFUSED = 2 };

enum ifu_event {
	IFU_EV_DECONFIG = 0,
	IFU_EV_BOUND,
	IFU_EV_RENEW,
	IFU_EV_NAK,
	IFU_EV_LEASEFAIL,
	IFU_EV_UNKNOWN
};

struct ifu_ops {
	/* Replace /run/wan.dns with `n` (0..IFU_DNS_MAX) host-order addresses,
	 * one dotted quad per line.  0 or -1. */
	int (*write_dns)(void *ctx, const uint32_t *v, int n);
	void *ctx;
};

struct ifu_result {
	int rc;               /* enum ifu_rc */
	const char *reason;   /* the decisive named token; never NULL */
	const char *detail;   /* nu_strerror of the parse that failed, or "" */
	int event;            /* enum ifu_event */

	int did_addr, did_mask, did_up, did_route_add, did_route_del, did_dns;

	uint32_t ip, mask, gw;
	uint32_t dns[IFU_DNS_MAX];
	int n_dns;
	char ifname[NU_IFNAME_MAX + 1];

	int n_note;
	const char *note[IFU_NOTE_MAX];   /* static tokens only */
};

/* A getenv-shaped hook, so the test drives a table and `main` drives getenv. */
typedef const char *(*ifu_getenv_fn)(void *ctx, const char *name);

int ifu_event_of(const char *name);

/* Parse up to `max` resolvers out of a space-separated list, reading at most
 * IFU_DNS_SCAN bytes.  Returns how many were accepted; sets *more when a valid
 * token was dropped for want of room, and *bad to the count refused. */
int ifu_dns_list(const char *s, uint32_t *out, int max, int *more, int *bad);

/* The whole program, minus the environment and the console. */
int ifu_run(const char *event, ifu_getenv_fn get, void *gctx,
	    struct nu_net *net, const struct ifu_ops *io, struct ifu_result *r);

/* The real /run/wan.dns writer (used by main.c; exposed so the test can check
 * the byte alphabet it produces against a temporary path). */
int ifu_write_dns_to(const char *path, const uint32_t *v, int n);

#endif /* RLXFW_IFUPD_NETCFG_H */
