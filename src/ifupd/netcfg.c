/* netcfg.c -- R7: see netcfg.h for the input model and the rules. */

#include "netcfg.h"

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>     /* rename() only */
#include <string.h>
#include <unistd.h>

static void note(struct ifu_result *r, const char *t)
{
	if (r->n_note < IFU_NOTE_MAX)
		r->note[r->n_note++] = t;
}

static int refuse(struct ifu_result *r, const char *reason, const char *detail)
{
	r->rc = IFU_REFUSED;
	r->reason = reason;
	r->detail = detail;
	return r->rc;
}

int ifu_event_of(const char *name)
{
	static const struct {
		const char *n;
		int e;
	} tab[] = {
		{ "deconfig", IFU_EV_DECONFIG },
		{ "bound", IFU_EV_BOUND },
		{ "renew", IFU_EV_RENEW },
		{ "nak", IFU_EV_NAK },
		/* busybox sends this one too, and a firmware that treats an
		 * unknown event as fatal would log a refusal on every failed
		 * DISCOVER.  It means the same as deconfig. */
		{ "leasefail", IFU_EV_LEASEFAIL }
	};
	size_t i;

	if (name == NULL)
		return IFU_EV_UNKNOWN;
	for (i = 0; i < sizeof(tab) / sizeof(tab[0]); i++)
		if (strcmp(name, tab[i].n) == 0)
			return tab[i].e;
	return IFU_EV_UNKNOWN;
}

/* Read a value and refuse it before looking at it if there is no NUL within
 * `max` bytes.  Returns the string, or NULL with *toolong set. */
static const char *get_bounded(ifu_getenv_fn get, void *ctx, const char *name,
			       size_t max, int *toolong)
{
	const char *v = get(ctx, name);
	size_t i;

	*toolong = 0;
	if (v == NULL)
		return NULL;
	for (i = 0; i <= max; i++)
		if (v[i] == '\0')
			return i == 0 ? NULL : v;   /* empty means absent */
	*toolong = 1;
	return NULL;
}

int ifu_dns_list(const char *s, uint32_t *out, int max, int *more, int *bad)
{
	size_t i = 0;
	int n = 0;

	*more = 0;
	*bad = 0;
	if (s == NULL || out == NULL || max <= 0)
		return 0;
	while (i < (size_t)IFU_DNS_SCAN && s[i] != '\0') {
		size_t start;
		uint32_t v;

		if (s[i] == ' ' || s[i] == '\t' || s[i] == ',') {
			i++;
			continue;
		}
		start = i;
		while (i < (size_t)IFU_DNS_SCAN && s[i] != '\0' &&
		       s[i] != ' ' && s[i] != '\t' && s[i] != ',')
			i++;
		/* A token longer than a dotted quad can be, or one that does
		 * not parse, or one that is not a usable resolver address: each
		 * is counted and skipped, never fatal.  A lease with one bad
		 * resolver and two good ones should leave two working. */
		if (i - start > (size_t)NU_QUAD_MAX ||
		    nu_parse_ipv4_n(s + start, i - start, &v) != 0 ||
		    !nu_is_unicast(v)) {
			(*bad)++;
			continue;
		}
		if (n >= max) {
			*more = 1;
			continue;
		}
		out[n++] = v;
	}
	return n;
}

int ifu_write_dns_to(const char *path, const uint32_t *v, int n)
{
	/* IFU_DNS_MAX lines of at most NU_QUAD_MAX + 1 bytes. */
	char buf[IFU_DNS_MAX * (NU_QUAD_MAX + 1) + 1];
	char tmp[64];
	size_t len = 0, pl;
	int i, fd;
	ssize_t w;

	if (path == NULL || n < 0 || n > IFU_DNS_MAX)
		return -1;
	for (i = 0; i < n; i++) {
		int k = nu_format_ipv4(v[i], buf + len, sizeof(buf) - len);

		if (k < 0)
			return -1;
		len += (size_t)k;
		buf[len++] = '\n';
	}
	/* Write a temporary and rename: a reader must never see a half-written
	 * resolver list, and rename(2) on the same tmpfs is atomic. */
	pl = strlen(path);
	if (pl + 5 >= sizeof(tmp))
		return -1;
	memcpy(tmp, path, pl);
	memcpy(tmp + pl, ".tmp", 5);
	fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
	if (fd < 0)
		return -1;
	w = len == 0 ? 0 : write(fd, buf, len);
	if (close(fd) != 0 || w != (ssize_t)len) {
		(void)unlink(tmp);
		return -1;
	}
	if (rename(tmp, path) != 0) {
		(void)unlink(tmp);
		return -1;
	}
	return 0;
}

/* ------------------------------------------------------------------ the run */

static int do_deconfig(struct ifu_result *r, struct nu_net *net,
		       const struct ifu_ops *io)
{
	int rc;

	/* Up first: udhcpc cannot send a DISCOVER on an interface that is down,
	 * and `deconfig` is exactly what runs before the first DISCOVER. */
	rc = nu_if_set_flags(net, r->ifname, 1);
	if (rc == 0)
		r->did_up = 1;
	else
		note(r, "up-failed");

	/* 0.0.0.0 removes the address and, with it, every route through it --
	 * including the default route, which is why no explicit delete is
	 * needed here and why one is issued anyway on `renew`. */
	rc = nu_if_set_addr(net, r->ifname, 0u);
	if (rc == 0) {
		r->did_addr = 1;
	} else {
		note(r, "addr-clear-failed");
		r->rc = IFU_PARTIAL;
		r->reason = "addr-clear-failed";
		r->detail = nu_strerror(rc);
	}
	if (io->write_dns(io->ctx, NULL, 0) == 0)
		r->did_dns = 1;
	else
		note(r, "wan-dns-write-failed");
	return r->rc;
}

static int do_bound(struct ifu_result *r, ifu_getenv_fn get, void *gctx,
		    struct nu_net *net, const struct ifu_ops *io)
{
	const char *s;
	int toolong, rc, more = 0, bad = 0;
	uint32_t v;

	/* --- parse and validate everything mandatory, applying nothing ---- */
	s = get_bounded(get, gctx, "ip", NU_QUAD_MAX, &toolong);
	if (toolong)
		return refuse(r, "ip-too-long", "too-long");
	if (s == NULL)
		return refuse(r, "no-ip", "");
	rc = nu_parse_ipv4(s, &r->ip);
	if (rc != 0)
		return refuse(r, "bad-ip", nu_strerror(rc));

	s = get_bounded(get, gctx, "subnet", NU_QUAD_MAX, &toolong);
	if (toolong)
		return refuse(r, "subnet-too-long", "too-long");
	if (s == NULL)
		return refuse(r, "no-subnet", "");
	rc = nu_parse_ipv4(s, &r->mask);
	if (rc != 0)
		return refuse(r, "bad-subnet", nu_strerror(rc));
	rc = nu_mask_ok(r->mask, 8, 30);
	if (rc != 0)
		return refuse(r, "bad-netmask", nu_strerror(rc));

	if (!nu_is_unicast(r->ip))
		return refuse(r, "ip-not-unicast", "");
	if (nu_is_net_or_bcast(r->ip, r->mask))
		return refuse(r, "ip-is-network-or-broadcast", "");

	/* --- from here on the interface is touched ------------------------ */
	rc = nu_if_set_addr(net, r->ifname, r->ip);
	if (rc != 0) {
		r->rc = IFU_PARTIAL;
		r->reason = "addr-ioctl-failed";
		r->detail = nu_strerror(rc);
		return r->rc;   /* no point setting a mask on no address */
	}
	r->did_addr = 1;
	rc = nu_if_set_mask(net, r->ifname, r->mask);
	if (rc == 0) {
		r->did_mask = 1;
	} else {
		note(r, "mask-ioctl-failed");
		r->rc = IFU_PARTIAL;
		r->reason = "mask-ioctl-failed";
		r->detail = nu_strerror(rc);
	}
	rc = nu_if_set_flags(net, r->ifname, 1);
	if (rc == 0)
		r->did_up = 1;
	else
		note(r, "up-failed");

	/* --- the router, whose refusal is partial and not fatal ----------- */
	s = get_bounded(get, gctx, "router", NU_QUAD_MAX, &toolong);
	if (toolong) {
		/* udhcpc joins several routers with a space, so a long value is
		 * usually a list rather than an attack.  Take the first token,
		 * bounded, and say that the rest was dropped. */
		const char *raw = get(gctx, "router");
		size_t k = 0;

		note(r, "router-list-truncated");
		/* <= NU_QUAD_MAX so that a legal 15-byte first token followed by
		 * a space is accepted; a 16th byte before the separator is not. */
		while (k <= (size_t)NU_QUAD_MAX && raw[k] != '\0' &&
		       raw[k] != ' ' && raw[k] != '\t')
			k++;
		if (k == 0 || k > (size_t)NU_QUAD_MAX ||
		    nu_parse_ipv4_n(raw, k, &v) != 0) {
			note(r, "router-unparsable");
			r->rc = IFU_PARTIAL;
			r->reason = "router-unparsable";
			s = NULL;
		} else {
			r->gw = v;
			s = "";   /* parsed out of band; skip the parse below */
		}
	} else if (s != NULL) {
		rc = nu_parse_ipv4(s, &r->gw);
		if (rc != 0) {
			note(r, "router-unparsable");
			r->rc = IFU_PARTIAL;
			r->reason = "bad-router";
			r->detail = nu_strerror(rc);
			s = NULL;
		}
	}

	if (s == NULL) {
		if (r->rc == IFU_OK)
			note(r, "no-router-no-default-route");
	} else if (!nu_is_unicast(r->gw)) {
		note(r, "gw-not-unicast");
		r->rc = IFU_PARTIAL;
		r->reason = "gw-not-unicast";
	} else if ((r->gw & r->mask) != (r->ip & r->mask)) {
		/* The interesting hostile case.  A gateway off the subnet is
		 * unreachable without a classless-static-route option this
		 * firmware does not implement, and installing it would make
		 * the kernel refuse with ENETUNREACH anyway.  Refuse it here,
		 * by name, and keep the address that is perfectly good. */
		note(r, "gw-off-subnet");
		r->rc = IFU_PARTIAL;
		r->reason = "gw-off-subnet";
	} else if (r->gw == r->ip) {
		note(r, "gw-is-self");
		r->rc = IFU_PARTIAL;
		r->reason = "gw-is-self";
	} else {
		/* Delete before add, so a `renew` that moved the gateway does
		 * not leave two default routes. */
		if (nu_route_default_del(net, r->ifname, r->gw) == 0)
			r->did_route_del = 1;
		rc = nu_route_default_add(net, r->ifname, r->gw);
		if (rc == 0) {
			r->did_route_add = 1;
		} else {
			note(r, "route-ioctl-failed");
			r->rc = IFU_PARTIAL;
			r->reason = "route-ioctl-failed";
			r->detail = nu_strerror(rc);
		}
	}

	/* --- the resolvers ------------------------------------------------ */
	s = get(gctx, "dns");
	r->n_dns = ifu_dns_list(s, r->dns, IFU_DNS_MAX, &more, &bad);
	if (more)
		note(r, "dns-truncated");
	if (bad > 0)
		note(r, "dns-entry-refused");
	if (io->write_dns(io->ctx, r->dns, r->n_dns) == 0)
		r->did_dns = 1;
	else
		note(r, "wan-dns-write-failed");
	return r->rc;
}

int ifu_run(const char *event, ifu_getenv_fn get, void *gctx,
	    struct nu_net *net, const struct ifu_ops *io, struct ifu_result *r)
{
	const char *s;
	int toolong;
	size_t l;

	if (r == NULL)
		return IFU_REFUSED;
	memset(r, 0, sizeof(*r));
	r->rc = IFU_OK;
	r->reason = "ok";
	r->detail = "";
	r->event = IFU_EV_UNKNOWN;
	if (get == NULL || net == NULL || io == NULL)
		return refuse(r, "internal-null", "");

	r->event = ifu_event_of(event);
	if (r->event == IFU_EV_UNKNOWN)
		return refuse(r, "unknown-event", "");

	s = get_bounded(get, gctx, "interface", NU_IFNAME_MAX, &toolong);
	if (toolong)
		return refuse(r, "interface-too-long", "too-long");
	if (s == NULL)
		return refuse(r, "no-interface", "");
	if (nu_ifname_ok(s) != 0)
		return refuse(r, "bad-ifname", nu_strerror(-NU_E_IFNAME));
	l = strlen(s);
	memcpy(r->ifname, s, l);
	r->ifname[l] = '\0';

	switch (r->event) {
	case IFU_EV_BOUND:
	case IFU_EV_RENEW:
		return do_bound(r, get, gctx, net, io);
	case IFU_EV_DECONFIG:
	case IFU_EV_NAK:
	case IFU_EV_LEASEFAIL:
		return do_deconfig(r, net, io);
	default:
		return refuse(r, "unknown-event", "");
	}
}
