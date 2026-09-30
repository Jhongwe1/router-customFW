/* test_ifupd.c -- R7 host test for src/ifupd/netcfg.c.
 *
 * ---------------------------------------------------------------------------
 * WHAT IS BEING TESTED, AND WHAT THE FAKE IS
 * ---------------------------------------------------------------------------
 *
 * The fake `nu_ops` decodes the same `struct ifreq` and `struct rtentry` the
 * kernel would, so what these cases check is the bytes `netcfg.c` hands to
 * `ioctl` -- the address in network order, the mask at the union offset, the
 * route's dst/genmask/gateway/dev -- and not a mock of an interface I wrote.
 * That is why the test needs no root and no network and still says something.
 *
 * The table's second half is the hostile set.  Each row states what must
 * happen: applied, applied in part with a named reason, or refused with nothing
 * applied at all.  A refusal that still issued an ioctl is a failure here, and
 * `n_ioctl` is asserted for exactly that.  Run under
 * -fsanitize=address,undefined, "none crashing" is the third assertion every
 * row makes for free.
 */

#include "netcfg.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <net/if.h>
#include <net/route.h>
#include <netinet/in.h>
#include <sys/ioctl.h>
#include <sys/socket.h>

static int checks, fails;

#define CK(cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); \
	} \
} while (0)

#define CKN(name, cond) do { \
	checks++; \
	if (!(cond)) { \
		fails++; \
		printf("FAIL [%s] %s:%d  %s\n", name, __FILE__, __LINE__, #cond); \
	} \
} while (0)

/* ------------------------------------------------------------------ the fake */

struct fake {
	int n_ioctl;
	int n_addr, n_mask, n_getfl, n_setfl, n_add, n_del;
	char addr_if[IFNAMSIZ + 1];
	char mask_if[IFNAMSIZ + 1];
	uint32_t addr, mask;
	unsigned flags;
	uint32_t rt_dst, rt_mask, rt_gw;
	char rt_dev[IFNAMSIZ + 1];
	unsigned short rt_flags;
	/* injected failures */
	unsigned long fail_req;
	int fail_errno;
	int del_esrch;
	/* what write_dns saw */
	int dns_calls, dns_n;
	uint32_t dns[IFU_DNS_MAX];
};

static uint32_t sin_of(const struct sockaddr *sa)
{
	struct sockaddr_in sin;

	memcpy(&sin, sa, sizeof(sin));
	return ntohl(sin.sin_addr.s_addr);
}

static void name_of(char *dst, size_t n, const char *src)
{
	size_t i;

	for (i = 0; i + 1 < n && i < IFNAMSIZ && src[i] != '\0'; i++)
		dst[i] = src[i];
	dst[i] = '\0';
}

static int fake_open(void *ctx)
{
	(void)ctx;
	return 7;   /* any non-negative handle */
}

static int fake_close(void *ctx, int fd)
{
	(void)ctx;
	(void)fd;
	return 0;
}

static int fake_ioctl(void *ctx, int fd, unsigned long req, void *arg)
{
	struct fake *f = (struct fake *)ctx;

	(void)fd;
	f->n_ioctl++;
	if (f->fail_req == req) {
		errno = f->fail_errno;
		return -1;
	}
	switch (req) {
	case SIOCSIFADDR: {
		struct ifreq *r = (struct ifreq *)arg;

		f->n_addr++;
		name_of(f->addr_if, sizeof(f->addr_if), r->ifr_name);
		f->addr = sin_of(&r->ifr_addr);
		/* The kernel resets the mask to the class default here, which
		 * is why netcfg.c writes the address first. */
		return 0;
	}
	case SIOCSIFNETMASK: {
		struct ifreq *r = (struct ifreq *)arg;

		f->n_mask++;
		name_of(f->mask_if, sizeof(f->mask_if), r->ifr_name);
		f->mask = sin_of(&r->ifr_addr);
		return 0;
	}
	case SIOCGIFFLAGS: {
		struct ifreq *r = (struct ifreq *)arg;

		f->n_getfl++;
		r->ifr_flags = (short)f->flags;
		return 0;
	}
	case SIOCSIFFLAGS: {
		struct ifreq *r = (struct ifreq *)arg;

		f->n_setfl++;
		f->flags = (unsigned)(unsigned short)r->ifr_flags;
		return 0;
	}
	case SIOCADDRT:
	case SIOCDELRT: {
		struct rtentry *rt = (struct rtentry *)arg;

		if (req == SIOCDELRT) {
			f->n_del++;
			if (f->del_esrch) {
				errno = ESRCH;
				return -1;
			}
		} else {
			f->n_add++;
		}
		f->rt_dst = sin_of(&rt->rt_dst);
		f->rt_mask = sin_of(&rt->rt_genmask);
		f->rt_gw = sin_of(&rt->rt_gateway);
		f->rt_flags = rt->rt_flags;
		name_of(f->rt_dev, sizeof(f->rt_dev),
			rt->rt_dev == NULL ? "" : rt->rt_dev);
		return 0;
	}
	default:
		errno = EINVAL;
		return -1;
	}
}

static int fake_write_dns(void *ctx, const uint32_t *v, int n)
{
	struct fake *f = (struct fake *)ctx;
	int i;

	f->dns_calls++;
	f->dns_n = n;
	for (i = 0; i < n && i < IFU_DNS_MAX; i++)
		f->dns[i] = v[i];
	return 0;
}

/* --------------------------------------------------------- the environment */

#define ENV_MAX 8

struct env {
	const char *k[ENV_MAX];
	const char *v[ENV_MAX];
	int n;
};

static const char *env_get(void *ctx, const char *name)
{
	struct env *e = (struct env *)ctx;
	int i;

	for (i = 0; i < e->n; i++)
		if (strcmp(e->k[i], name) == 0)
			return e->v[i];
	return NULL;
}

static void env_put(struct env *e, const char *k, const char *v)
{
	if (v == NULL || e->n >= ENV_MAX)
		return;
	e->k[e->n] = k;
	e->v[e->n] = v;
	e->n++;
}

/* --------------------------------------------------------------- the table */

struct tcase {
	const char *name;
	const char *event;
	const char *interface;
	const char *ip;
	const char *subnet;
	const char *router;
	const char *dns;
	int want_rc;
	const char *want_reason;
	int want_ioctl_zero;   /* 1 = the refusal must have touched nothing */
	int want_addr_set;
	uint32_t want_addr;
	int want_route;
	uint32_t want_gw;
	int want_dns_n;
};

/* 4 KB and 64-byte hostile values, built once. */
static char big4k[4096];
static char big64[65];
static char ten_dns[256];
static char long_router[64];

static void build_big(void)
{
	memset(big4k, '9', sizeof(big4k) - 1);
	big4k[sizeof(big4k) - 1] = '\0';
	memset(big64, '7', sizeof(big64) - 1);
	big64[sizeof(big64) - 1] = '\0';
	/* Ten valid resolvers: only the first three may survive. */
	(void)snprintf(ten_dns, sizeof(ten_dns),
		       "1.1.1.1 2.2.2.2 3.3.3.3 4.4.4.4 5.5.5.5 "
		       "6.6.6.6 7.7.7.7 8.8.8.8 9.9.9.9 10.10.10.10");
	(void)snprintf(long_router, sizeof(long_router),
		       "192.168.1.1 192.168.1.2 192.168.1.3");
}

static const struct tcase cases[] = {
/*   name                     event        if      ip               subnet            router          dns                   rc            reason                        0io  a  addr        rt gw           dns */
	{ "bound-good",           "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  "8.8.8.8 8.8.4.4",    IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 2 },
	{ "renew-good",           "renew",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  "8.8.8.8",            IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 1 },
	{ "bound-slash30",        "bound",     "eth4", "10.0.0.1",      "255.255.255.252","10.0.0.2",     "1.1.1.1",            IFU_OK,       "ok",                          0, 1, 0x0A000001u, 1, 0x0A000002u, 1 },
	{ "bound-no-router",      "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  NULL,           "8.8.8.8",            IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 0, 0u,          1 },
	{ "bound-no-dns",         "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  NULL,                 IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 0 },
	{ "deconfig",             "deconfig",  "eth4", NULL,            NULL,             NULL,           NULL,                 IFU_OK,       "ok",                          0, 1, 0u,          0, 0u,          0 },
	{ "nak",                  "nak",       "eth4", "1.2.3.4",       "255.255.255.0",  "1.2.3.1",      "8.8.8.8",            IFU_OK,       "ok",                          0, 1, 0u,          0, 0u,          0 },
	{ "leasefail",            "leasefail", "eth4", NULL,            NULL,             NULL,           NULL,                 IFU_OK,       "ok",                          0, 1, 0u,          0, 0u,          0 },

	/* ---------------------------- the hostile set -------------------------------------------------------------------------------------------------------------- */
	{ "unknown-event",        "explode",   "eth4", "1.2.3.4",       "255.255.255.0",  "1.2.3.1",      "8.8.8.8",            IFU_REFUSED,  "unknown-event",               1, 0, 0u,          0, 0u,          0 },
	{ "event-empty",          "",          "eth4", "1.2.3.4",       "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "unknown-event",               1, 0, 0u,          0, 0u,          0 },
	{ "event-shell",          "bound;id",  "eth4", "1.2.3.4",       "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "unknown-event",               1, 0, 0u,          0, 0u,          0 },
	{ "no-interface",         "bound",     NULL,   "1.2.3.4",       "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "no-interface",                1, 0, 0u,          0, 0u,          0 },
	{ "interface-16-bytes",   "bound",     "1234567890123456", "1.2.3.4", "255.255.255.0", NULL,      NULL,                 IFU_REFUSED,  "interface-too-long",          1, 0, 0u,          0, 0u,          0 },
	{ "interface-shell",      "bound",     "eth0;id", "1.2.3.4",    "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "bad-ifname",                  1, 0, 0u,          0, 0u,          0 },
	{ "interface-traversal",  "deconfig",  "../../etc", NULL,       NULL,             NULL,           NULL,                 IFU_REFUSED,  "bad-ifname",                  1, 0, 0u,          0, 0u,          0 },
	{ "no-ip",                "bound",     "eth4", NULL,            "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "no-ip",                       1, 0, 0u,          0, 0u,          0 },
	{ "ip-nonnumeric",        "bound",     "eth4", "gateway",       "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "bad-ip",                      1, 0, 0u,          0, 0u,          0 },
	{ "ip-256",               "bound",     "eth4", "256.1.1.1",     "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "bad-ip",                      1, 0, 0u,          0, 0u,          0 },
	{ "ip-three-octets",      "bound",     "eth4", "192.168.1",     "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "bad-ip",                      1, 0, 0u,          0, 0u,          0 },
	{ "ip-zero",              "bound",     "eth4", "0.0.0.0",       "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-not-unicast",              1, 0, 0u,          0, 0u,          0 },
	{ "ip-loopback",          "bound",     "eth4", "127.0.0.1",     "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-not-unicast",              1, 0, 0u,          0, 0u,          0 },
	{ "ip-multicast",         "bound",     "eth4", "224.0.0.1",     "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-not-unicast",              1, 0, 0u,          0, 0u,          0 },
	{ "ip-is-network",        "bound",     "eth4", "192.168.1.0",   "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-is-network-or-broadcast",  1, 0, 0u,          0, 0u,          0 },
	{ "ip-is-broadcast",      "bound",     "eth4", "192.168.1.255", "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-is-network-or-broadcast",  1, 0, 0u,          0, 0u,          0 },
	{ "no-subnet",            "bound",     "eth4", "192.168.1.50",  NULL,             NULL,           NULL,                 IFU_REFUSED,  "no-subnet",                   1, 0, 0u,          0, 0u,          0 },
	{ "subnet-noncontiguous", "bound",     "eth4", "192.168.1.50",  "255.0.255.0",    NULL,           NULL,                 IFU_REFUSED,  "bad-netmask",                 1, 0, 0u,          0, 0u,          0 },
	{ "subnet-slash31",       "bound",     "eth4", "192.168.1.50",  "255.255.255.254",NULL,           NULL,                 IFU_REFUSED,  "bad-netmask",                 1, 0, 0u,          0, 0u,          0 },
	{ "subnet-slash32",       "bound",     "eth4", "192.168.1.50",  "255.255.255.255",NULL,           NULL,                 IFU_REFUSED,  "bad-netmask",                 1, 0, 0u,          0, 0u,          0 },
	{ "subnet-zero",          "bound",     "eth4", "192.168.1.50",  "0.0.0.0",        NULL,           NULL,                 IFU_REFUSED,  "bad-netmask",                 1, 0, 0u,          0, 0u,          0 },
	{ "subnet-nonnumeric",    "bound",     "eth4", "192.168.1.50",  "yes",            NULL,           NULL,                 IFU_REFUSED,  "bad-subnet",                  1, 0, 0u,          0, 0u,          0 },

	/* --- applied in part: the address is good, the router is not -------------------------------------------------------------------------------------------- */
	{ "router-off-subnet",    "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "10.9.9.9",     "8.8.8.8",            IFU_PARTIAL,  "gw-off-subnet",               0, 1, 0xC0A80132u, 0, 0u,          1 },
	{ "router-is-self",       "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.50", NULL,                 IFU_PARTIAL,  "gw-is-self",                  0, 1, 0xC0A80132u, 0, 0u,          0 },
	{ "router-zero",          "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "0.0.0.0",      NULL,                 IFU_PARTIAL,  "gw-not-unicast",              0, 1, 0xC0A80132u, 0, 0u,          0 },
	{ "router-nonnumeric",    "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "default",      NULL,                 IFU_PARTIAL,  "bad-router",                  0, 1, 0xC0A80132u, 0, 0u,          0 },
	{ "router-broadcast",     "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "255.255.255.255", NULL,              IFU_PARTIAL,  "gw-not-unicast",              0, 1, 0xC0A80132u, 0, 0u,          0 },

	/* --- accepted with a note ------------------------------------------------------------------------------------------------------------------------------- */
	{ "router-list",          "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  NULL /*long*/,  NULL,                 IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 0 },
	{ "dns-ten-entries",      "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  NULL /*ten*/,         IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 3 },
	{ "dns-4k-garbage",       "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  NULL /*big4k*/,       IFU_OK,       "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 0 },
	{ "dns-one-bad",          "bound",     "eth4", "192.168.1.50",  "255.255.255.0",  "192.168.1.1",  "8.8.8.8 nope 1.1.1.1", IFU_OK,     "ok",                          0, 1, 0xC0A80132u, 1, 0xC0A80101u, 2 },

	/* --- 4 KB and 64-byte mandatory values ---------------------------------------------------------------------------------------------------------------- */
	{ "subnet-4k",            "bound",     "eth4", "192.168.1.50",  NULL /*big4k*/,   NULL,           NULL,                 IFU_REFUSED,  "subnet-too-long",             1, 0, 0u,          0, 0u,          0 },
	{ "ip-64-digits",         "bound",     "eth4", NULL /*big64*/,  "255.255.255.0",  NULL,           NULL,                 IFU_REFUSED,  "ip-too-long",                 1, 0, 0u,          0, 0u,          0 },
	{ "interface-4k",         "bound",     NULL /*big4k*/, "192.168.1.50", "255.255.255.0", NULL,      NULL,                IFU_REFUSED,  "interface-too-long",          1, 0, 0u,          0, 0u,          0 },
	{ "everything-4k",        "bound",     NULL /*big4k*/, NULL /*big4k*/, NULL /*big4k*/, NULL /*big4k*/, NULL /*big4k*/,  IFU_REFUSED,  "interface-too-long",          1, 0, 0u,          0, 0u,          0 }
};

/* The rows whose value is a runtime buffer, patched in by name. */
static const char *patch(const char *tname, const char *field, const char *v)
{
	if (v != NULL)
		return v;
	if (strcmp(tname, "router-list") == 0 && strcmp(field, "router") == 0)
		return long_router;
	if (strcmp(tname, "dns-ten-entries") == 0 && strcmp(field, "dns") == 0)
		return ten_dns;
	if (strcmp(tname, "dns-4k-garbage") == 0 && strcmp(field, "dns") == 0)
		return big4k;
	if (strcmp(tname, "subnet-4k") == 0 && strcmp(field, "subnet") == 0)
		return big4k;
	if (strcmp(tname, "ip-64-digits") == 0 && strcmp(field, "ip") == 0)
		return big64;
	if (strcmp(tname, "interface-4k") == 0 && strcmp(field, "interface") == 0)
		return big4k;
	if (strcmp(tname, "everything-4k") == 0)
		return big4k;
	return NULL;
}

static void run_table(void)
{
	size_t k;

	for (k = 0; k < sizeof(cases) / sizeof(cases[0]); k++) {
		const struct tcase *t = &cases[k];
		struct fake f;
		struct env e;
		struct nu_ops ops;
		struct nu_net net;
		struct ifu_ops io;
		struct ifu_result r;
		int rc;

		memset(&f, 0, sizeof(f));
		memset(&e, 0, sizeof(e));
		f.flags = IFF_BROADCAST | IFF_MULTICAST;
		ops.sock_open = fake_open;
		ops.sock_close = fake_close;
		ops.sock_ioctl = fake_ioctl;
		ops.ctx = &f;
		io.write_dns = fake_write_dns;
		io.ctx = &f;

		env_put(&e, "interface", patch(t->name, "interface", t->interface));
		env_put(&e, "ip", patch(t->name, "ip", t->ip));
		env_put(&e, "subnet", patch(t->name, "subnet", t->subnet));
		env_put(&e, "router", patch(t->name, "router", t->router));
		env_put(&e, "dns", patch(t->name, "dns", t->dns));
		/* Values ifupd must never read, all of them poisonous. */
		env_put(&e, "mtu", "$(reboot)");
		env_put(&e, "domain", "`id`");
		env_put(&e, "lease", "; rm -rf /");

		CK(nu_net_open(&net, &ops) == 0);
		rc = ifu_run(t->event, env_get, &e, &net, &io, &r);
		nu_net_close(&net);

		CKN(t->name, rc == t->want_rc);
		CKN(t->name, r.rc == t->want_rc);
		CKN(t->name, r.reason != NULL &&
			     strcmp(r.reason, t->want_reason) == 0);
		if (r.reason == NULL || strcmp(r.reason, t->want_reason) != 0)
			printf("      [%s] reason=\"%s\" want=\"%s\" detail=\"%s\"\n",
			       t->name, r.reason == NULL ? "(null)" : r.reason,
			       t->want_reason, r.detail);

		/* A refusal must not have touched the interface at all. */
		if (t->want_ioctl_zero)
			CKN(t->name, f.n_ioctl == 0);

		CKN(t->name, f.n_addr == (t->want_addr_set ? 1 : 0));
		if (t->want_addr_set) {
			CKN(t->name, f.addr == t->want_addr);
			CKN(t->name, strcmp(f.addr_if, t->interface == NULL
							       ? ""
							       : t->interface) == 0);
			/* IFF_UP was set and the driver's own flags survived. */
			CKN(t->name, (f.flags & IFF_UP) != 0);
			CKN(t->name, (f.flags & IFF_BROADCAST) != 0);
		}
		CKN(t->name, f.n_add == (t->want_route ? 1 : 0));
		if (t->want_route) {
			CKN(t->name, f.rt_gw == t->want_gw);
			CKN(t->name, f.rt_dst == 0u);
			CKN(t->name, f.rt_mask == 0u);
			CKN(t->name, (f.rt_flags & (RTF_UP | RTF_GATEWAY)) ==
					     (RTF_UP | RTF_GATEWAY));
			CKN(t->name, strcmp(f.rt_dev, t->interface) == 0);
			/* Delete before add, so a renew cannot leave two. */
			CKN(t->name, f.n_del == 1);
		}
		if (t->want_rc != IFU_REFUSED) {
			CKN(t->name, f.dns_calls == 1);
			CKN(t->name, f.dns_n == t->want_dns_n);
		} else {
			CKN(t->name, f.dns_calls == 0);
		}
		/* Whatever happened, a reason was named and nothing was left
		 * pointing at a NULL. */
		CKN(t->name, r.detail != NULL);
		CKN(t->name, r.n_note >= 0 && r.n_note <= IFU_NOTE_MAX);
	}
}

/* An ioctl that fails is a partial, not a crash and not a silent success. */
static void t_ioctl_failure(void)
{
	static const unsigned long reqs[] = { SIOCSIFADDR, SIOCSIFNETMASK,
					      SIOCSIFFLAGS, SIOCADDRT };
	static const char *const want[] = { "addr-ioctl-failed",
					    "mask-ioctl-failed", "ok",
					    "route-ioctl-failed" };
	size_t k;

	for (k = 0; k < sizeof(reqs) / sizeof(reqs[0]); k++) {
		struct fake f;
		struct env e;
		struct nu_ops ops;
		struct nu_net net;
		struct ifu_ops io;
		struct ifu_result r;

		memset(&f, 0, sizeof(f));
		memset(&e, 0, sizeof(e));
		f.fail_req = reqs[k];
		f.fail_errno = EPERM;
		ops.sock_open = fake_open;
		ops.sock_close = fake_close;
		ops.sock_ioctl = fake_ioctl;
		ops.ctx = &f;
		io.write_dns = fake_write_dns;
		io.ctx = &f;
		env_put(&e, "interface", "eth4");
		env_put(&e, "ip", "192.168.1.50");
		env_put(&e, "subnet", "255.255.255.0");
		env_put(&e, "router", "192.168.1.1");
		CK(nu_net_open(&net, &ops) == 0);
		(void)ifu_run("bound", env_get, &e, &net, &io, &r);
		nu_net_close(&net);
		/* A failing SIOCSIFFLAGS is only a note: the address is set and
		 * the interface may already be up. */
		CK(strcmp(r.reason, want[k]) == 0);
		CK(r.rc == (strcmp(want[k], "ok") == 0 ? IFU_OK : IFU_PARTIAL));
	}
	/* SIOCDELRT returning ESRCH -- a first `bound` of the boot -- must not
	 * stop the add. */
	{
		struct fake f;
		struct env e;
		struct nu_ops ops;
		struct nu_net net;
		struct ifu_ops io;
		struct ifu_result r;

		memset(&f, 0, sizeof(f));
		memset(&e, 0, sizeof(e));
		f.del_esrch = 1;
		ops.sock_open = fake_open;
		ops.sock_close = fake_close;
		ops.sock_ioctl = fake_ioctl;
		ops.ctx = &f;
		io.write_dns = fake_write_dns;
		io.ctx = &f;
		env_put(&e, "interface", "eth4");
		env_put(&e, "ip", "192.168.1.50");
		env_put(&e, "subnet", "255.255.255.0");
		env_put(&e, "router", "192.168.1.1");
		CK(nu_net_open(&net, &ops) == 0);
		CK(ifu_run("bound", env_get, &e, &net, &io, &r) == IFU_OK);
		nu_net_close(&net);
		CK(f.n_add == 1);
	}
}

static void t_dns_list(void)
{
	uint32_t v[IFU_DNS_MAX];
	int more, bad, n;

	n = ifu_dns_list("8.8.8.8 8.8.4.4 1.1.1.1", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 3 && more == 0 && bad == 0);
	CK(v[0] == 0x08080808u && v[1] == 0x08080404u && v[2] == 0x01010101u);

	n = ifu_dns_list(ten_dns, v, IFU_DNS_MAX, &more, &bad);
	CK(n == 3 && more == 1 && bad == 0);
	CK(v[0] == 0x01010101u);

	n = ifu_dns_list("", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 0 && bad == 0);
	n = ifu_dns_list(NULL, v, IFU_DNS_MAX, &more, &bad);
	CK(n == 0);
	n = ifu_dns_list("   ", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 0 && bad == 0);
	n = ifu_dns_list("0.0.0.0 127.0.0.1 224.0.0.1", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 0 && bad == 3);
	n = ifu_dns_list("8.8.8.8;reboot 1.1.1.1", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 1 && bad == 1 && v[0] == 0x01010101u);
	n = ifu_dns_list(big4k, v, IFU_DNS_MAX, &more, &bad);
	CK(n == 0 && bad == 1);   /* one unterminated token inside the scan bound */
	/* An embedded NUL truncates the list, and nothing is read past it. */
	n = ifu_dns_list("1.1.1.1\0" "2.2.2.2", v, IFU_DNS_MAX, &more, &bad);
	CK(n == 1 && v[0] == 0x01010101u);
	/* max = 0 and max = 1 are both honoured. */
	n = ifu_dns_list("1.1.1.1 2.2.2.2", v, 1, &more, &bad);
	CK(n == 1 && more == 1);
}

/* /run/wan.dns must be data.  Its whole alphabet is [0-9.\n]: that is what
 * makes "never writes a shell-readable script" a property rather than a hope. */
static void t_wan_dns_bytes(void)
{
	static const uint32_t v[3] = { 0x08080808u, 0x08080404u, 0xC0A80101u };
	const char *path = "./test_wan_dns.tmp";
	char buf[128];
	FILE *fp;
	size_t got, i;
	int lines = 0;

	CK(ifu_write_dns_to(path, v, 3) == 0);
	fp = fopen(path, "rb");
	CK(fp != NULL);
	if (fp == NULL)
		return;
	got = fread(buf, 1, sizeof(buf), fp);
	(void)fclose(fp);
	CK(got == strlen("8.8.8.8\n8.8.4.4\n192.168.1.1\n"));
	for (i = 0; i < got; i++) {
		int c = (unsigned char)buf[i];

		CK((c >= '0' && c <= '9') || c == '.' || c == '\n');
		if (c == '\n')
			lines++;
	}
	CK(lines == 3);
	CK(memcmp(buf, "8.8.8.8\n8.8.4.4\n192.168.1.1\n", got) == 0);

	/* n = 0 leaves an empty file, not a missing one: a reader must be able
	 * to tell "no resolvers" from "ifupd never ran". */
	CK(ifu_write_dns_to(path, NULL, 0) == 0);
	fp = fopen(path, "rb");
	CK(fp != NULL);
	if (fp != NULL) {
		CK(fread(buf, 1, sizeof(buf), fp) == 0);
		(void)fclose(fp);
	}
	CK(ifu_write_dns_to(path, v, IFU_DNS_MAX + 1) == -1);
	CK(ifu_write_dns_to(NULL, v, 1) == -1);
	(void)unlink(path);
	(void)unlink("./test_wan_dns.tmp.tmp");
}

static void t_event_names(void)
{
	CK(ifu_event_of("deconfig") == IFU_EV_DECONFIG);
	CK(ifu_event_of("bound") == IFU_EV_BOUND);
	CK(ifu_event_of("renew") == IFU_EV_RENEW);
	CK(ifu_event_of("nak") == IFU_EV_NAK);
	CK(ifu_event_of("leasefail") == IFU_EV_LEASEFAIL);
	CK(ifu_event_of("BOUND") == IFU_EV_UNKNOWN);
	CK(ifu_event_of("bound ") == IFU_EV_UNKNOWN);
	CK(ifu_event_of("") == IFU_EV_UNKNOWN);
	CK(ifu_event_of(NULL) == IFU_EV_UNKNOWN);
}

int main(void)
{
	build_big();
	t_event_names();
	t_dns_list();
	run_table();
	t_ioctl_failure();
	t_wan_dns_bytes();
	printf("test_ifupd: %d checks, %d failures, %d table rows\n", checks,
	       fails, (int)(sizeof(cases) / sizeof(cases[0])));
	return fails == 0 ? 0 : 1;
}
