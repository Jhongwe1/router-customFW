/* tools/uspacescan-fixtures/pos.c -- the planted positive for R7's
 * system()/popen() gate.
 *
 * It really does call system(), with an argument the compiler cannot fold away,
 * so the call survives -Os and the linker really pulls `system.os` out of
 * `libc.a`.  Both of `tools/uspacescan.py`'s sources must go red on it:
 * source (1) must find system's code in the linked ELF AND in the stripped
 * binary, and source (2) must find `system` as an SHN_UNDEF reference in pos.o.
 * If either comes back clean, the instrument is broken and the tool refuses to
 * report on anything else.
 *
 * This file is never installed, never runs and never reaches the image.  It
 * lives under tools/ rather than under config/rlxfw-user/ for that reason:
 * everything under config/rlxfw-user/ is a program that ships, and a file whose
 * whole purpose is to contain the one call R7 forbids must not sit in that
 * population where `imgprocs`/`mkinitramfs` could ever pick it up.  It sits
 * beside the tool that compiles it, the way tools/rlxprobe/ holds the payload
 * sources for tools/rlxprobe.
 *
 * `uspacescan.py --self-test` compiles THIS file when it is present and an
 * identical built-in copy when it is not, and says which it used, so the
 * controls still run from a checkout that has the tool and nothing else.
 */
#include <stdlib.h>

int main(int argc, char **argv)
{
	(void)argc;
	return system(argv[1]);
}
