/* tools/uspacescan-fixtures/allowed.c -- the allowed-call control.
 *
 * A guard that has only been shown refusing has not been shown working.  This
 * fixture is the other half: `execve` with a typed argv array, an absolute path
 * from the caller and no PATH search is exactly the shape R7 permits (SPEC-R7
 * § 2, and the broker's PING op is built this way), so `tools/uspacescan.py`
 * must report it CLEAN of every FORBIDDEN name while COUNTING `execve` on both
 * sources -- before and after `mips-linux-strip`.
 *
 * A clean answer here that did not also count execve would mean the scanner had
 * simply stopped seeing things, which is the failure mode this file exists to
 * exclude.  Never installed, never runs; see pos.c for why it lives here.
 */
#include <unistd.h>

int main(int argc, char **argv)
{
	char *const av[] = { "busybox", "true", (char *)0 };
	char *const ev[] = { (char *)0 };

	(void)argc;
	return execve(argv[1], av, ev);
}
