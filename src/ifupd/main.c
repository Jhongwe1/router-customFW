/* main.c -- R7: `ifupd`, the compiled replacement for busybox `udhcpc`'s
 * default `-s` shell script.
 *
 * ---------------------------------------------------------------------------
 * WHAT IT REPLACES
 * ---------------------------------------------------------------------------
 *
 * `udhcpc` has no opinion about what happens with a lease: it `execve`s the
 * program named by `-s` with the event as `argv[1]` and the lease in the
 * environment, and busybox ships a `/usr/share/udhcpc/default.script` for the
 * job.  That script is a shell script, which makes it the direct conflict with
 * R7's "no shell" condition -- and it is a shell script whose inputs come from
 * a DHCP server on the WAN.  This program is the same interface with no
 * interpreter behind it.
 *
 *   usage: /sbin/ifupd <deconfig|bound|renew|nak|leasefail>
 *   env:   interface ip subnet router dns    (nothing else is read)
 *   exit:  0 applied, 1 applied in part, 2 refused, 3 usage
 *
 * Everything decided is decided in `netcfg.c`, which is a pure function of the
 * environment and the injected syscall layer; this file supplies `getenv`, the
 * real socket, the real file, and the console line.  It executes nothing --
 * there is no `system`, `popen`, `execl*`, `execvp` or `fork` in either file.
 */

#include "netcfg.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* The same bounded builder PID 1 uses.  It is duplicated rather than shared
 * because `src/lib/` is another agent's ground and a log formatter is not
 * network utility code; it is 40 lines and it has no state. */
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
		return;
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

static void lb_out(struct lbuf *l)
{
	ssize_t w;

	if (l->truncated)
		lb_s(l, " [truncated]");
	l->b[l->n++] = '\n';
	w = write(2, l->b, l->n);   /* stderr: udhcpc inherits PID 1's console */
	(void)w;
	lb_reset(l);
}

/* -------------------------------------------------------------- the real ops */

static const char *real_getenv(void *ctx, const char *name)
{
	(void)ctx;
	return getenv(name);
}

static int real_write_dns(void *ctx, const uint32_t *v, int n)
{
	(void)ctx;
	return ifu_write_dns_to(PATH_WAN_DNS, v, n);
}

static const char *const ev_name[] = {
	"deconfig", "bound", "renew", "nak", "leasefail", "unknown"
};

int main(int argc, char **argv)
{
	struct nu_net net;
	struct ifu_ops io;
	struct ifu_result r;
	struct lbuf l;
	int rc, i;

	lb_reset(&l);

	/* argv[1] and nothing else.  udhcpc passes exactly one argument; more
	 * than that means something other than udhcpc called this. */
	if (argc != 2) {
		lb_s(&l, "ifupd: usage: ifupd <deconfig|bound|renew|nak|leasefail>");
		lb_out(&l);
		return 3;
	}

	io.write_dns = real_write_dns;
	io.ctx = NULL;

	rc = nu_net_open(&net, nu_ops_real());
	if (rc != 0) {
		lb_s(&l, "ifupd: refused: no-socket ");
		lb_s(&l, nu_strerror(rc));
		lb_out(&l);
		return 2;
	}

	rc = ifu_run(argv[1], real_getenv, NULL, &net, &io, &r);
	nu_net_close(&net);

	/* One line, always, whatever happened: a lease that was refused and a
	 * lease that was applied must be equally visible in a boot capture. */
	lb_s(&l, "ifupd: ");
	lb_s(&l, ev_name[r.event <= IFU_EV_UNKNOWN ? r.event : IFU_EV_UNKNOWN]);
	lb_s(&l, r.rc == IFU_OK ? " ok" : (r.rc == IFU_PARTIAL ? " PARTIAL" : " REFUSED"));
	lb_s(&l, " reason=");
	lb_s(&l, r.reason);
	if (r.detail != NULL && r.detail[0] != '\0') {
		lb_s(&l, " detail=");
		lb_s(&l, r.detail);
	}
	if (r.ifname[0] != '\0') {
		lb_s(&l, " if=");
		lb_s(&l, r.ifname);
	}
	if (r.did_addr) {
		lb_s(&l, " ip=");
		lb_ip(&l, r.ip);
	}
	if (r.did_mask) {
		lb_c(&l, '/');
		lb_u(&l, (unsigned long)(nu_mask_prefix(r.mask) < 0
						 ? 0
						 : nu_mask_prefix(r.mask)));
	}
	if (r.did_route_add) {
		lb_s(&l, " gw=");
		lb_ip(&l, r.gw);
	}
	if (r.did_dns) {
		lb_s(&l, " dns=");
		lb_u(&l, (unsigned long)r.n_dns);
	}
	for (i = 0; i < r.n_note; i++) {
		lb_c(&l, ' ');
		lb_s(&l, r.note[i]);
	}
	lb_out(&l);

	return r.rc;
}
