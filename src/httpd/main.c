/* src/httpd/main.c -- rlxfw's web server: argv, then three calls into serve.c.
 *
 * What the program is, in the order it happens:
 *   1. bind TCP :80 as root -- the only thing root is used for;
 *   2. chroot("/srv/www"), chdir("/"), setgroups(0), setgid(100), setuid(100),
 *      each verified, and then setuid(0) and setgid(0) proved to fail;
 *   3. accept, fork a child per connection (at most eight live), parse the request
 *      inside the child, and turn every privileged action into one typed op on
 *      /run/broker.sock -- which is /srv/www/run/broker.sock from outside the
 *      chroot, the only door out of the web root.
 *
 * There is no `system()`, no `popen()`, no `exec` of anything, and no shell in
 * the tree this process can see: `make -C src/httpd chrootcheck ROOT=srv/www`
 * refuses the build if an ELF, a symlink, a setuid bit or a device node appears
 * under the web root.
 *
 * There is no flag that skips the privilege drop.  A binary with a
 * --no-chroot switch is a binary that will one day be started with it, so the
 * host tests exercise srv_conn() on a socketpair instead and main() has no such
 * path: it refuses to run at all unless it is root and every step of the drop
 * holds.
 *
 * WHAT THIS DOES NOT ESTABLISH.  No TLS: HTTP only, and SPEC-R7 puts R7g outside
 * this gate, so every password on this port crosses the LAN in clear.  Nothing
 * here has run on the device.
 */

#include "http.h"
#include "routes.h"
#include "serve.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define DEF_ROOT  "/srv/www"
#define DEF_SOCK  "/run/broker.sock"   /* as seen from INSIDE the chroot */
#define DEF_PORT  80
#define DEF_UID   100
#define DEF_GID   100
#define DEF_PROOF "index.html"         /* must exist inside the new root */

static void usage(void)
{
	(void)fprintf(stderr,
		"usage: httpd [--root DIR] [--sock PATH] [--port N]\n"
		"             [--uid N] [--gid N] [--proof NAME]\n"
		"  --root   directory to chroot into (default " DEF_ROOT ")\n"
		"  --sock   broker socket, as seen inside the chroot (default "
		DEF_SOCK ")\n"
		"  --port   TCP port to bind as root (default 80)\n"
		"  --proof  a file that must exist inside --root, proving the\n"
		"           chroot landed where it was meant to\n");
}

/* strtoul with the whole string consumed, a range, and no atoi(). */
static int arg_u32(const char *s, unsigned long lo, unsigned long hi,
		   unsigned long *out)
{
	char *end = NULL;
	unsigned long v;

	if (s == NULL || *s == '\0')
		return -1;
	v = strtoul(s, &end, 10);
	if (end == NULL || *end != '\0')
		return -1;
	if (v < lo || v > hi)
		return -1;
	*out = v;
	return 0;
}

int main(int argc, char **argv)
{
	const char *root = DEF_ROOT;
	const char *sock = DEF_SOCK;
	const char *proof = DEF_PROOF;
	unsigned long port = DEF_PORT;
	unsigned long uid = DEF_UID;
	unsigned long gid = DEF_GID;
	int lfd;
	int i;

	for (i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;

		if (strcmp(a, "--root") == 0 && v != NULL) {
			root = v;
			i++;
		} else if (strcmp(a, "--sock") == 0 && v != NULL) {
			sock = v;
			i++;
		} else if (strcmp(a, "--proof") == 0 && v != NULL) {
			proof = v;
			i++;
		} else if (strcmp(a, "--port") == 0 &&
			   arg_u32(v, 1, 65535, &port) == 0) {
			i++;
		} else if (strcmp(a, "--uid") == 0 &&
			   arg_u32(v, 1, 65533, &uid) == 0) {
			i++;
		} else if (strcmp(a, "--gid") == 0 &&
			   arg_u32(v, 1, 65533, &gid) == 0) {
			i++;
		} else {
			usage();
			return 2;
		}
	}

	lfd = srv_listen((uint16_t)port, HTTP_CONN_MAX * 2);
	if (lfd < 0) {
		(void)fprintf(stderr, "httpd: cannot bind port %lu\n", port);
		return 1;
	}

	/* srv_drop() does not return on any failure: it prints the step that
	 * failed and _exit(1)s, so there is no path from here that serves a
	 * request with privilege it should not have. */
	(void)srv_drop(root, (uint32_t)uid, (uint32_t)gid, proof);

	(void)fprintf(stderr,
		      "httpd: uid=%lu gid=%lu root=%s sock=%s port=%lu conn=%d\n",
		      (unsigned long)getuid(), (unsigned long)getgid(),
		      root, sock, port, HTTP_CONN_MAX);
	(void)fflush(stderr);

	return srv_loop(lfd, sock) == 0 ? 0 : 1;
}
