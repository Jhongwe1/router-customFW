/* main.c -- dnsfwd: rlxfw's DNS forwarder for the LAN.  R7, plan s R7f item 3.
 *
 * ---------------------------------------------------------------------------
 * WHY IT EXISTS
 * ---------------------------------------------------------------------------
 *
 * 讀 SPEC.md FW-20: the vendor rootfs ships `bin/dnsmasq`, and it imports
 * `popen`.  R7's pass condition is that the shipped rootfs imports `system`
 * and `popen` zero times, so keeping dnsmasq would fail the gate on its own.
 * The plan's ruling is to write the forwarder instead: UDP only, forward only,
 * a bounded parser, refuses recursion.
 *
 * ---------------------------------------------------------------------------
 * WHAT THIS FILE IS, AND WHAT IT IS NOT
 * ---------------------------------------------------------------------------
 *
 * This file is the syscalls and nothing else: two sockets, the privilege drop,
 * the broker fetch, the signal flags, the select loop, and the `--decode` mode
 * that lets one parser case run on the target ELF under qemu.  Every decision
 * about a byte on the wire is in dns.c, behind an injectable `struct dns_io`,
 * so the host tests exercise the whole forwarder without opening a socket --
 * the bench owns this machine's interfaces and the tests must not touch them.
 *
 * It contains no `system`, no `popen`, no `exec*` and no `fork`: dnsfwd never
 * starts another process at all.
 */

#include "dns.h"

/* `R7-8`: this was a #ifdef DNSFWD_STUB_CLIENT pair selecting between
 * src/dnsfwd/stub/client.h and ../lib/client.h.  The stub is deleted and the
 * Makefile refuses without the real header, so there is one include -- and it
 * is a bare name, because the target build stages every source flat onto ext4
 * and compiles with -I. there, where "../lib/client.h" does not exist. */
#include "client.h"

#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/* SPEC-R7 s 3: dnsfwd runs as uid/gid 101 after binding :53 as root. */
#define DNSFWD_UID 101
#define DNSFWD_GID 101

/* SPEC-R7 s 4 key ids. */
#define K_LAN_IPADDR   0x0010
#define K_LAN_NETMASK  0x0011
#define K_DNS_UPSTREAM 0x0030

#define BROKER_SOCK_DEFAULT "/srv/www/run/broker.sock"
#define PIDFILE_DEFAULT     "/run/dnsfwd.pid"

/* SPEC-R7 s 4 default for lan.netmask, used only when the broker refuses to
 * hand `lan.netmask` to uid 101; see cfg_fetch(). */
#define LAN_MASK_FALLBACK 0xFFFFFF00u

static volatile sig_atomic_t g_hup;
static volatile sig_atomic_t g_quit;

struct io_ctx {
	int cs;        /* the :53 socket */
	int us;        /* the upstream socket */
	int urand;     /* /dev/urandom, opened as root and kept open */
};

/* ------------------------------------------------------------------------ */
/* Console                                                                  */
/* ------------------------------------------------------------------------ */

static void say(const char *fmt, ...)
#if defined(__GNUC__)
	__attribute__((format(printf, 1, 2)))
#endif
;

#include <stdarg.h>

static void say(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	(void)fputs("dnsfwd: ", stderr);
	(void)vfprintf(stderr, fmt, ap);
	(void)fputc('\n', stderr);
	va_end(ap);
	(void)fflush(stderr);
}

static void on_sig(int s)
{
	if (s == SIGHUP) g_hup = 1;
	else             g_quit = 1;
}

/* ------------------------------------------------------------------------ */
/* The I/O vtable                                                           */
/* ------------------------------------------------------------------------ */

static int io_send(void *c, int which, const uint8_t *buf, size_t n,
                   uint32_t addr, uint16_t port)
{
	struct io_ctx     *x = (struct io_ctx *)c;
	struct sockaddr_in sa;
	ssize_t            w;
	int                fd = (which == DNS_SOCK_UPSTREAM) ? x->us : x->cs;

	memset(&sa, 0, sizeof sa);
	sa.sin_family      = AF_INET;
	sa.sin_port        = htons(port);
	sa.sin_addr.s_addr = htonl(addr);
	for (;;) {
		w = sendto(fd, buf, n, 0, (struct sockaddr *)&sa, sizeof sa);
		if (w >= 0) return (int)w;
		if (errno == EINTR) continue;
		/* A connect()ed UDP socket reports a previous ICMP port-unreachable
		 * here.  It is information about the upstream, not a reason to die. */
		return -errno;
	}
}

static int io_rand16(void *c, uint16_t *out)
{
	struct io_ctx *x = (struct io_ctx *)c;
	uint8_t        b[2];
	size_t         off = 0;

	while (off < sizeof b) {
		ssize_t r = read(x->urand, b + off, sizeof b - off);
		if (r < 0) {
			if (errno == EINTR) continue;
			return -errno;
		}
		if (r == 0) return -EIO;
		off += (size_t)r;
	}
	*out = dns_get16(b);
	return 0;
}

static uint32_t io_now_ms(void *c)
{
	(void)c;
#ifdef DNSFWD_NO_CLOCK_GETTIME
	{
		struct timeval tv;

		if (gettimeofday(&tv, 0) != 0) return 0;
		return (uint32_t)tv.tv_sec * 1000u + (uint32_t)(tv.tv_usec / 1000);
	}
#else
	{
		struct timespec ts;

		if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
		return (uint32_t)ts.tv_sec * 1000u + (uint32_t)(ts.tv_nsec / 1000000);
	}
#endif
}

static void io_logline(void *c, const char *msg)
{
	(void)c;
	say("%s", msg);
}

/* ------------------------------------------------------------------------ */
/* Config, from the broker only                                             */
/* ------------------------------------------------------------------------ */

/* Reads the TLV body SPEC-R7 s 6 GET returns: type u16 BE, len u16 BE, value.
 * Returns 1 and the 4-byte IPV4 value in host order, or 0 when the id is
 * absent.  Bounded: never reads past body_len. */
static int tlv_ipv4(const uint8_t *b, uint32_t n, uint16_t id, uint32_t *out)
{
	uint32_t off = 0;

	while (off + 4 <= n) {
		uint16_t t = dns_get16(b + off);
		uint16_t l = dns_get16(b + off + 2);

		if ((uint32_t)off + 4 + l > n) return 0;   /* malformed: stop */
		if (t == id) {
			if (l != 4) return 0;
			*out = dns_get32(b + off + 4);
			return 1;
		}
		off += 4u + l;
	}
	return 0;
}

struct cfg_wire { uint32_t lan_ip, lan_mask, upstream; };

/* Fail closed: any failure leaves *c untouched and returns < 0.  There is no
 * hard-coded resolver anywhere in this program -- grep it -- so a dnsfwd that
 * cannot reach the broker does not forward, it says so and exits. */
static int cfg_fetch(const char *sock, struct cfg_wire *c)
{
	static const uint16_t want3[3] = { K_LAN_IPADDR, K_LAN_NETMASK,
	                                   K_DNS_UPSTREAM };
	static const uint16_t want2[2] = { K_LAN_IPADDR, K_DNS_UPSTREAM };
	uint8_t         body[8];
	struct bk_req   rq;
	struct bk_resp  rs;
	uint32_t        ip = 0, mask = 0, up = 0;
	int             pass, rc, nk;

	/* SPEC DEVIATION: s 6 allows uid 101 exactly two keys, `dns.upstream` and
	 * `lan.ipaddr`, but the brief's off-LAN check needs `lan.ipaddr` AND a
	 * netmask.  So: ask for all three; if the broker answers PERM, ask again
	 * for the two it allows and use the schema's own default netmask with a
	 * console line.  /24 is narrower than any class-based guess would be, and
	 * narrower is the safe direction here -- a too-wide mask turns dnsfwd into
	 * an open forwarder, a too-narrow one only refuses local clients. */
	for (pass = 0; pass < 2; pass++) {
		const uint16_t *want = pass == 0 ? want3 : want2;
		int             i;

		nk = pass == 0 ? 3 : 2;
		for (i = 0; i < nk; i++) dns_put16(body + i * 2, want[i]);

		memset(&rq, 0, sizeof rq);
		rq.op       = BK_OP_GET;
		rq.body     = body;
		rq.body_len = (uint32_t)(nk * 2);
		rc = bk_call(sock, &rq, &rs);
		if (rc != 0) {
			say("broker unreachable at %s: %s -- FAILING CLOSED, "
			    "no resolver is forwarded to", sock, strerror(-rc));
			return rc;
		}
		if (rs.status == BK_PERM && pass == 0) {
			say("broker refused lan.netmask to uid %d (PERM); retrying with "
			    "the two keys SPEC-R7 s 6 allows", (int)DNSFWD_UID);
			continue;
		}
		if (rs.status != BK_OK) {
			say("broker GET status %u -- FAILING CLOSED",
			    (unsigned)rs.status);
			return -EACCES;
		}
		break;
	}

	if (!tlv_ipv4(rs.body, rs.body_len, K_LAN_IPADDR, &ip) ||
	    !tlv_ipv4(rs.body, rs.body_len, K_DNS_UPSTREAM, &up)) {
		say("broker reply lacks lan.ipaddr or dns.upstream -- FAILING CLOSED");
		return -ENOENT;
	}
	if (!tlv_ipv4(rs.body, rs.body_len, K_LAN_NETMASK, &mask)) {
		mask = LAN_MASK_FALLBACK;
		say("lan.netmask not available to uid %d; using the schema default "
		    "255.255.255.0 for the off-LAN check", (int)DNSFWD_UID);
	}
	/* A mask that is not contiguous, or /0, would widen the accept set; refuse
	 * rather than narrow it silently. */
	if (mask == 0 || (uint32_t)(~mask & (uint32_t)(~mask + 1u)) != 0) {
		say("lan.netmask %08lx is not a contiguous non-zero prefix -- "
		    "FAILING CLOSED", (unsigned long)mask);
		return -EINVAL;
	}
	if (up == 0 || (up >> 24) == 127 || (up >> 28) == 0xE) {
		say("dns.upstream %lu.%lu.%lu.%lu is not a usable unicast address -- "
		    "FAILING CLOSED", (unsigned long)(up >> 24) & 0xFF,
		    (unsigned long)(up >> 16) & 0xFF, (unsigned long)(up >> 8) & 0xFF,
		    (unsigned long)up & 0xFF);
		return -EINVAL;
	}
	c->lan_ip   = ip;
	c->lan_mask = mask;
	c->upstream = up;
	return 0;
}

/* ------------------------------------------------------------------------ */
/* Sockets and privileges                                                   */
/* ------------------------------------------------------------------------ */

static int udp_bind(uint32_t addr, uint16_t port)
{
	struct sockaddr_in sa;
	int                fd = socket(AF_INET, SOCK_DGRAM, 0);

	if (fd < 0) return -errno;
	memset(&sa, 0, sizeof sa);
	sa.sin_family      = AF_INET;
	sa.sin_port        = htons(port);
	sa.sin_addr.s_addr = htonl(addr);
	if (bind(fd, (struct sockaddr *)&sa, sizeof sa) < 0) {
		int e = -errno;
		(void)close(fd);
		return e;
	}
	return fd;
}

/* connect() the upstream socket so the kernel itself drops datagrams from
 * anywhere but the upstream -- a second source for the address half of the
 * Kaminsky check, never a replacement for dnsfwd's own test.
 *
 * It MUST be redone when dns.upstream changes on SIGHUP: a socket left
 * connected to the old address would have the kernel silently discard every
 * reply from the new one, and dnsfwd would time out every query while its own
 * source check looked fine. */
static void upstream_connect(int fd, uint32_t addr)
{
	struct sockaddr_in sa;

	memset(&sa, 0, sizeof sa);
	sa.sin_family      = AF_INET;
	sa.sin_port        = htons(DNS_PORT);
	sa.sin_addr.s_addr = htonl(addr);
	if (connect(fd, (struct sockaddr *)&sa, sizeof sa) < 0)
		say("connect(upstream): %s -- continuing with dnsfwd's own source "
		    "check only", strerror(errno));
}

/* Drops to 101:101 and then PROVES it: the group first (setgid after setuid
 * would fail), the supplementary list emptied, every id read back, and finally
 * setuid(0) attempted and REQUIRED to fail.  A privilege drop that is not
 * verified is a comment. */
static int drop_privs(void)
{
	if (geteuid() != 0) {
		say("not root at the privilege drop (euid %ld) -- refusing to run "
		    "with an unknown privilege level", (long)geteuid());
		return -1;
	}
	if (setgroups(0, 0) != 0) {
		say("setgroups(0): %s", strerror(errno));
		return -1;
	}
	if (setgid(DNSFWD_GID) != 0) {
		say("setgid(%d): %s", DNSFWD_GID, strerror(errno));
		return -1;
	}
	if (setuid(DNSFWD_UID) != 0) {
		say("setuid(%d): %s", DNSFWD_UID, strerror(errno));
		return -1;
	}
	if (getuid() != DNSFWD_UID || geteuid() != DNSFWD_UID ||
	    getgid() != DNSFWD_GID || getegid() != DNSFWD_GID) {
		say("privilege drop did not take: uid %ld/%ld gid %ld/%ld",
		    (long)getuid(), (long)geteuid(), (long)getgid(), (long)getegid());
		return -1;
	}
	if (setuid(0) == 0) {
		say("setuid(0) SUCCEEDED after dropping to %d -- this process can "
		    "regain root and must not serve the network", DNSFWD_UID);
		return -1;
	}
	if (errno != EPERM)
		say("note: setuid(0) failed with %s, not EPERM", strerror(errno));
	say("running as uid %ld gid %ld; setuid(0) refused (%s)",
	    (long)getuid(), (long)getgid(), strerror(EPERM));
	return 0;
}

/* ------------------------------------------------------------------------ */
/* --decode: one parser case, runnable on the target ELF under qemu          */
/* ------------------------------------------------------------------------ */

static void name_text(const uint8_t *nm, uint8_t nl, char *out, size_t cap)
{
	size_t i = 0, o = 0;

	if (cap == 0) return;
	if (nl == 1 && nm[0] == 0) {
		if (cap > 1) { out[0] = '.'; out[1] = 0; } else out[0] = 0;
		return;
	}
	while (i < nl && nm[i] != 0) {
		uint8_t  l = nm[i];
		unsigned k;

		if ((size_t)i + 1 + l > nl) break;
		for (k = 0; k < l; k++) {
			uint8_t ch = nm[i + 1 + k];

			if (o + 2 >= cap) { out[o] = 0; return; }
			out[o++] = (ch >= 33 && ch <= 126 && ch != '.' && ch != '\\')
			           ? (char)ch : '?';
		}
		if (o + 2 >= cap) break;
		out[o++] = '.';
		i += 1u + l;
	}
	out[o < cap ? o : cap - 1] = 0;
}

static int decode_file(const char *path)
{
	uint8_t           buf[DNS_MSG_MAX + 8];
	char              txt[600];
	struct dns_query  q;
	struct dns_reply  r;
	size_t            n = 0;
	int               fd, rc;

	fd = open(path, O_RDONLY);
	if (fd < 0) { say("%s: %s", path, strerror(errno)); return 2; }
	for (;;) {
		ssize_t k = read(fd, buf + n, sizeof buf - n);
		if (k < 0) { if (errno == EINTR) continue; break; }
		if (k == 0) break;
		n += (size_t)k;
		if (n == sizeof buf) break;
	}
	(void)close(fd);

	printf("bytes %lu\n", (unsigned long)n);
	printf("get16 %04X get32 %08lX\n",
	       (unsigned)dns_get16((const uint8_t *)"\x12\x34"),
	       (unsigned long)dns_get32((const uint8_t *)"\xDE\xAD\xBE\xEF"));

	rc = dns_parse_query(buf, n, &q);
	printf("query rc %d %s", rc, dns_strerr(rc));
	if (rc == 0) {
		name_text(q.q.name, q.q.nlen, txt, sizeof txt);
		printf(" id %04X name %s nlen %u qtype %u qclass %u",
		       q.h.id, txt, (unsigned)q.q.nlen, q.q.qtype, q.q.qclass);
	}
	printf("\n");

	rc = dns_parse_reply(buf, n, &r);
	printf("reply rc %d %s", rc, dns_strerr(rc));
	if (rc == 0) {
		unsigned i;

		name_text(r.q.name, r.q.nlen, txt, sizeof txt);
		printf(" id %04X rcode %u qname %s an %u walked %u",
		       r.h.id, (unsigned)(r.h.flags & DNS_F_RCMASK), txt,
		       (unsigned)r.n_an, (unsigned)r.n_walked);
		for (i = 0; i < r.n_an; i++) {
			name_text(r.an[i].name, r.an[i].nlen, txt, sizeof txt);
			printf(" | rr %s type %u ttl %lu rdlen %u rdoff %u", txt,
			       r.an[i].type, (unsigned long)r.an[i].ttl,
			       r.an[i].rdlen, r.an[i].rdoff);
		}
	}
	printf("\n");
	return 0;
}

/* ------------------------------------------------------------------------ */
/* main                                                                     */
/* ------------------------------------------------------------------------ */

static void usage(void)
{
	(void)fputs("usage: dnsfwd [-s BROKER_SOCK] [-p PIDFILE] [-f]\n"
	            "       dnsfwd --decode FILE\n", stderr);
}

int main(int argc, char **argv)
{
	const char     *sock = BROKER_SOCK_DEFAULT;
	const char     *pidf = PIDFILE_DEFAULT;
	struct io_ctx   ctx;
	struct dns_io   io;
	struct dnsfwd   d;
	struct cfg_wire cfg;
	int             i, rc;

	for (i = 1; i < argc; i++) {
		if (strcmp(argv[i], "--decode") == 0 && i + 1 < argc)
			return decode_file(argv[++i]);
		else if (strcmp(argv[i], "-s") == 0 && i + 1 < argc) sock = argv[++i];
		else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) pidf = argv[++i];
		else if (strcmp(argv[i], "-f") == 0) ;   /* foreground is the only mode */
		else { usage(); return 2; }
	}

	rc = cfg_fetch(sock, &cfg);
	if (rc != 0) return 1;
	say("lan %lu.%lu.%lu.%lu mask %08lX upstream %lu.%lu.%lu.%lu",
	    (unsigned long)(cfg.lan_ip >> 24) & 0xFF,
	    (unsigned long)(cfg.lan_ip >> 16) & 0xFF,
	    (unsigned long)(cfg.lan_ip >> 8) & 0xFF,
	    (unsigned long)cfg.lan_ip & 0xFF, (unsigned long)cfg.lan_mask,
	    (unsigned long)(cfg.upstream >> 24) & 0xFF,
	    (unsigned long)(cfg.upstream >> 16) & 0xFF,
	    (unsigned long)(cfg.upstream >> 8) & 0xFF,
	    (unsigned long)cfg.upstream & 0xFF);

	ctx.urand = open("/dev/urandom", O_RDONLY);
	if (ctx.urand < 0) {
		say("/dev/urandom: %s -- no query IDs, FAILING CLOSED",
		    strerror(errno));
		return 1;
	}
	/* :53 on the LAN address only, never INADDR_ANY: a forwarder that also
	 * listens on the WAN address is the open forwarder the LAN check exists to
	 * prevent, and binding narrowly means the kernel refuses those datagrams
	 * before dnsfwd sees them. */
	rc = udp_bind(cfg.lan_ip, DNS_PORT);
	if (rc < 0) {
		say("bind :53 on the LAN address: %s", strerror(-rc));
		return 1;
	}
	ctx.cs = rc;
	/* The upstream socket gets its ephemeral port from the kernel while we are
	 * still root, so the port is fixed for the process lifetime.  It is
	 * per-process, NOT per-query: see notes/dnsfwd.md on what that costs. */
	rc = udp_bind(0, 0);
	if (rc < 0) {
		say("upstream socket: %s", strerror(-rc));
		return 1;
	}
	ctx.us = rc;
	upstream_connect(ctx.us, cfg.upstream);

	{
		FILE *f = fopen(pidf, "w");

		if (f != 0) {
			(void)fprintf(f, "%ld\n", (long)getpid());
			(void)fclose(f);
		} else {
			say("%s: %s (continuing)", pidf, strerror(errno));
		}
	}

	if (drop_privs() != 0) return 1;

	(void)signal(SIGHUP, on_sig);
	(void)signal(SIGTERM, on_sig);
	(void)signal(SIGINT, on_sig);
	(void)signal(SIGPIPE, SIG_IGN);

	io.send    = io_send;
	io.rand16  = io_rand16;
	io.now_ms  = io_now_ms;
	io.logline = io_logline;
	io.ctx     = &ctx;
	dnsfwd_init(&d, &io);
	dnsfwd_config(&d, cfg.lan_ip, cfg.lan_mask, cfg.upstream);
	say("forwarding; inflight cap %d, upstream timeout %d ms, "
	    "rate %d q/s burst %d", DNS_INFLIGHT_MAX, DNS_TIMEOUT_MS,
	    DNS_RATE_FILL_M * 1000 / DNS_RATE_COST_M,
	    DNS_RATE_CAP_M / DNS_RATE_COST_M);

	while (!g_quit) {
		fd_set         rfds;
		struct timeval tv;
		int            nfds = (ctx.cs > ctx.us ? ctx.cs : ctx.us) + 1;

		if (g_hup) {
			struct cfg_wire nc;

			g_hup = 0;
			if (cfg_fetch(sock, &nc) == 0) {
				if (nc.upstream != cfg.upstream)
					upstream_connect(ctx.us, nc.upstream);
				if (nc.lan_ip != cfg.lan_ip)
					say("SIGHUP: lan.ipaddr changed but :53 is still bound to "
					    "the old address and rebinding needs root we have "
					    "dropped -- restart dnsfwd (PID 1 respawns it)");
				cfg = nc;
				dnsfwd_config(&d, cfg.lan_ip, cfg.lan_mask, cfg.upstream);
				say("SIGHUP: config reloaded");
			} else {
				/* Keep the last values that were known good.  Exiting here
				 * would hand a denial of service to anything able to make the
				 * broker briefly unavailable; the startup path is the one that
				 * fails closed, and no hard-coded resolver exists either way. */
				say("SIGHUP: broker refused; keeping the previous config");
			}
		}

		FD_ZERO(&rfds);
		FD_SET(ctx.cs, &rfds);
		FD_SET(ctx.us, &rfds);
		tv.tv_sec  = 0;
		tv.tv_usec = 500000;
		rc = select(nfds, &rfds, 0, 0, &tv);
		if (rc < 0) {
			if (errno == EINTR) continue;
			say("select: %s", strerror(errno));
			break;
		}
		if (rc > 0) {
			int which;

			for (which = 0; which < 2; which++) {
				uint8_t            buf[DNS_MSG_MAX];
				struct sockaddr_in sa;
				socklen_t          sl = sizeof sa;
				int                fd = which == 0 ? ctx.cs : ctx.us;
				ssize_t            k;

				if (!FD_ISSET(fd, &rfds)) continue;
				memset(&sa, 0, sizeof sa);
				/* A 512-byte buffer with MSG_TRUNC set: a longer datagram is
				 * reported at its true length and therefore refused by
				 * dns_parse_* as DNSE_LONG, instead of being silently
				 * truncated into something that happens to parse. */
				k = recvfrom(fd, buf, sizeof buf, MSG_TRUNC,
				             (struct sockaddr *)&sa, &sl);
				if (k < 0) {
					if (errno == EINTR || errno == EAGAIN) continue;
					say("recvfrom(%d): %s", which, strerror(errno));
					continue;
				}
				/* MSG_TRUNC reports the datagram's TRUE length, which can
				 * exceed what was copied in.  Drop it here rather than hand a
				 * length past the end of `buf` to a parser and rely on that
				 * parser's own 512-byte bound to save us. */
				if ((size_t)k > sizeof buf) {
					d.st.d_parse++;
					continue;
				}
				if (sl < (socklen_t)sizeof sa || sa.sin_family != AF_INET)
					continue;
				if (which == 0)
					(void)dnsfwd_on_client(&d, buf, (size_t)k,
					                       ntohl(sa.sin_addr.s_addr),
					                       ntohs(sa.sin_port));
				else
					(void)dnsfwd_on_upstream(&d, buf, (size_t)k,
					                         ntohl(sa.sin_addr.s_addr),
					                         ntohs(sa.sin_port));
			}
		}
		(void)dnsfwd_tick(&d);
	}

	say("stopping: in %u fwd %u replies %u; dropped off-LAN %u rate %u "
	    "parse %u full %u spoof %u; timed out %u",
	    d.st.q_in, d.st.q_fwd, d.st.r_out, d.st.d_offlan, d.st.d_rate,
	    d.st.d_parse, d.st.d_full, d.st.d_spoof, d.st.t_expired);
	return 0;
}
