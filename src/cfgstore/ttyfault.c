/* ttyfault.c -- test-only: tcsetattr(), wrapped (-Wl,--wrap=tcsetattr) into
 * cfgstore-tty, so that test_cli can show cmd_passwd's echo guard REFUSING
 * (notes/self-update.md § 6.4).  No target build links it.
 *
 *   CFGSTORE_TTYFAULT=fail  every call fails EIO
 *   CFGSTORE_TTYFAULT=keep  the call is made with ECHO set again: it answers 0
 *                           and leaves echo on, the partial change POSIX
 *                           allows and that no pty makes by itself
 *   unset                   the real call; test_cli runs this binary
 *                           permitting as well
 */

#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>

int __real_tcsetattr(int fd, int act, const struct termios *t);
int __wrap_tcsetattr(int fd, int act, const struct termios *t);

int __wrap_tcsetattr(int fd, int act, const struct termios *t)
{
	const char *m = getenv("CFGSTORE_TTYFAULT");
	struct termios k;

	if (m != NULL && strcmp(m, "fail") == 0) {
		errno = EIO;
		return -1;
	}
	if (m != NULL && strcmp(m, "keep") == 0) {
		k = *t;
		k.c_lflag |= (tcflag_t)ECHO;
		return __real_tcsetattr(fd, act, &k);
	}
	return __real_tcsetattr(fd, act, t);
}
