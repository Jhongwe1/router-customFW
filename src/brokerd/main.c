/* src/brokerd/main.c -- argv, the socket, and the loop.
 *
 * The loop itself is loop.c (bk_loop_step), so that a host test can drive it
 * pass by pass and adopt a socket with the uid its test names.  main() is the
 * only caller that accepts: every connection here gets its uid from
 * SO_PEERCRED and from nowhere else.  The concurrency model, what still blocks
 * and why the reboot and the install wait for the reply are written there.
 */
#define _GNU_SOURCE 1

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "brokerd.h"

static volatile sig_atomic_t want_stop;

static void on_term(int sig)
{
	(void)sig;
	want_stop = 1;
}

static void usage(void)
{
	(void)fprintf(stderr,
	  "brokerd [-s SOCK] [-c CFG] [-m MODE] [-g GID]\n"
	  "  -s  unix socket path   (default " BK_SOCK_PATH ")\n"
	  "  -c  config store path  (default " BK_CFG_PATH ")\n"
	  "  -m  socket mode, octal (default 0666; see notes/broker.md)\n"
	  "  -g  socket group gid   (default: leave as root)\n"
	  "There is deliberately no option for the entropy file, the random\n"
	  "source, the ping binary or the update path's files: each would be a\n"
	  "runtime bypass.\n");
}

int main(int argc, char **argv)
{
	struct broker bk;
	struct bk_loop loop;
	const char *sock_path = BK_SOCK_PATH;
	const char *cfg_path = BK_CFG_PATH;
	mode_t mode = 0666;
	gid_t gid = (gid_t)-1;
	int lfd, opt;

	/* SIGPIPE ignored: a peer that vanishes between our read and our write
	 * must give us EPIPE, not kill the only privileged process on the box --
	 * and EPIPE is how END's OK learns it was not delivered (loop.c).
	 * SIGCHLD is left at SIG_DFL on purpose -- SIG_IGN would make PING's
	 * waitpid() fail with ECHILD and lose the exit status. */
	(void)signal(SIGPIPE, SIG_IGN);
	(void)signal(SIGTERM, on_term);
	(void)signal(SIGINT, on_term);

	while ((opt = getopt(argc, argv, "s:c:m:g:h")) != -1) {
		switch (opt) {
		case 's': sock_path = optarg; break;
		case 'c': cfg_path = optarg; break;
		case 'm': mode = (mode_t)strtoul(optarg, 0, 8); break;
		case 'g': gid = (gid_t)strtoul(optarg, 0, 10); break;
		case 'h': usage(); return 0;
		default:  usage(); return 2;
		}
	}

	bk_init(&bk);
	bk.cfg_path = cfg_path;
	/* Fail-closed, per SPEC § 5: defaults, source = 0, and with no
	 * admin.pwhash no login is possible until one is set.  This load only
	 * makes the start-up log say what the store held: bk_dispatch() loads it
	 * again before every request (`FW-184`). */
	(void)bk_cfg_reload(&bk);
	(void)bk_entropy_ready(&bk);
	bk_log("brokerd: entropy_avail=%lu auth_ready=%d",
	       (unsigned long)bk.entropy_last, bk.auth_ready);
	if (!bk.auth_ready)
		bk_log("brokerd: LOGIN and PWSET will answer NOENTROPY until "
		       "entropy_avail reaches %d at least once", BK_ENTROPY_MIN);

	lfd = bk_bind_socket(sock_path, mode, gid);
	if (lfd < 0)
		return 1;
	bk_loop_init(&loop);
	bk_log("brokerd: listening on %s mode %04o", sock_path, (unsigned)mode);

	while (!want_stop)
		if (bk_loop_step(&bk, &loop, lfd, 1000) != 0)
			break;

	bk_loop_close_all(&bk, &loop);
	(void)close(lfd);
	(void)unlink(sock_path);
	bk_sess_drop_all(&bk);
	bk_upd_discard(&bk);
	bk_log("brokerd: stopped");
	return 0;
}
