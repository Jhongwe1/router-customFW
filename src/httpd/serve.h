/* src/httpd/serve.h -- the listening socket, the privilege drop and the loop.
 *
 * main.c reads argv and calls exactly three of these in order.  They are separate
 * from main() so the tests can call the connection handler on a socketpair
 * without a listening socket, a fork or a root process.
 */
#ifndef RLXFW_HTTPD_SERVE_H
#define RLXFW_HTTPD_SERVE_H

#include <stdint.h>

#include "routes.h"

/* Bind and listen on TCP port `port` as root.  Returns the fd or -1. */
int srv_listen(uint16_t port, int backlog);

/* chroot(root) -> chdir("/") -> setgroups(0) -> setgid(gid) -> setuid(uid), each
 * verified, then the two refusals (setuid(0) and setgid(0) must fail).  Returns 0
 * only when every step succeeded and every check held; on any failure it writes
 * one line naming the step to stderr and returns a negative step number.  It
 * never continues with partial privilege. */
int srv_drop(const char *root, uint32_t uid, uint32_t gid, const char *proof);

/* Serve exactly one request on `fd` and return.  Does not close fd.  Returns the
 * HTTP status sent, or -1 if nothing was sent (peer closed first). */
int srv_conn(int fd, const struct route_env *env);

/* The accept loop.  Forks one child per connection, at most HTTP_CONN_MAX live,
 * at most SRV_PER_IP from one address; owns the login token buckets and answers
 * the children's grant requests.  Returns only on a fatal error. */
int srv_loop(int lfd, const char *sock_path);

#define SRV_PER_IP 4

/* The Retry-After a second asker is told while one KDF evaluation is in flight.
 * It is a constant and no bucket in rl.h can produce it for more than two
 * seconds, so a device that answers `retry_s: 2` across a long idle gap is
 * answering from the holder branch and not from a bucket.  That is how the
 * 2026-09-30 defect was located; notes/httpd.md section 11 has the numbers. */
#define SRV_KDF_BUSY_S 2

/* The parent's KDF grant arbitration.  srv_loop() owns the state and calls
 * exactly these three, so a test of them is a test of the deployed decision
 * rather than of a second implementation of it -- which is the whole lesson of
 * the 2026-09-30 defect.  The clock is an argument: no test sleeps.
 *
 * WHAT THEY DO NOT ESTABLISH.  Nothing here covers the socketpair itself, the
 * five-byte encoding of the answer, or select()'s ordering against SIGCHLD.  A
 * child that is never reaped and never closes its channel still holds the grant,
 * correctly, and the bound on that is the child's own alarm(), not this. */
void srv_kdf_reset(void);
/* 1 = `slot` now holds the one grant, *retry_s = 0.  0 = refused, and *retry_s
 * says when to come back, never 0. */
int  srv_kdf_ask(unsigned slot, uint32_t ip, uint32_t t_ms,
		 uint32_t *retry_s);
/* The child in `slot` no longer holds the grant, for any reason: it released it,
 * its channel closed, or it exited and was reaped.  All three call sites must
 * reach this one function; a second marker that only some of them update is the
 * defect this interface exists to prevent. */
void srv_kdf_gone(unsigned slot);

/* The bytes on the parent/child channel.  One byte out, five bytes back. */
#define SRV_ASK   'L'
#define SRV_REL   'R'
#define SRV_YES   'Y'
#define SRV_NO    'N'

#endif /* RLXFW_HTTPD_SERVE_H */
