#!/bin/sh
# test-spi-wrpolicy -- compile and run the flash write path's policy on the
# host, then prove the suite can fail.
#
# R8b item 4, 2026-10-04.  It is the ONLY desk control over any of item 4's
# four decisions, and it covers exactly one of them (W3's refusals).  What has
# no desk control is listed in notes/spi-mtd-driver.md § 12.4 and in
# i4/controls.md; the short version is everything that touches the controller.
#
# THE ORDER IS THE POINT.  The unmutated suite runs FIRST and must pass; only
# then are the mutations trusted, because a mutation run against an already
# red suite says nothing (CLAUDE.md: "Before trusting a mutation run, confirm
# the unmutated suite passes").
set -e

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(dirname -- "$here")
hdr="$repo/config/rlxfw-src/linux-2.6.30/drivers/mtd/devices"
out=${TMPDIR:-/tmp}/rlxfw-wrpolicy.$$

if [ ! -f "$hdr/rtl819x-spi-wrpolicy.h" ]; then
	echo "test-spi-wrpolicy: $hdr/rtl819x-spi-wrpolicy.h is not there." >&2
	echo "  This test compiles the DRIVER's header, not a copy of it." >&2
	exit 3
fi

CC=${CC:-cc}
# -Wall -Wextra -Werror, and -std=gnu89 because that is the dialect gcc 3.4.6
# compiles the kernel TU in, so a C99-ism the host accepts is caught here.
# NOT -std=c89, which has no `inline` keyword at all and rejects the header
# outright -- the first run of this script did exactly that, which is the
# cheapest possible reminder that this header is compiled twice.
# -Wextra is load-bearing: -Wmissing-field-initializers caught two table
# rows one field short, which would have read as mtd_erasesize = 0 and
# turned two permitting cases into GEOM refusals -- a suite greener than
# the code deserved.
"$CC" -std=gnu89 -Wall -Wextra -Werror -O2 \
	-I "$hdr" -o "$out" "$here/test-spi-wrpolicy.c"

rc=0
echo "--- arm 1 of 2: the suite as declared (must PASS)"
if "$out"; then
	echo "    PASS"
else
	echo "    the unmutated suite FAILED; mutations below prove nothing" >&2
	rm -f "$out"
	exit 1
fi

# Two mutations, one over a REFUSING case and one over a PERMITTING case, so
# the control covers both directions of the guard.  Case 0 is `prog offset 0,
# armed` (forbidden) and the permitting one is found by name rather than by
# index, because an index into a table someone will extend is a citation that
# rots.
perm=$("$out" 2>/dev/null | sed -n 's/^permitted \([0-9]*\) of.*/\1/p')
echo "--- arm 2 of 2: two mutations (each must FAIL); $perm permitting case(s)"
for m in 0 6; do
	if "$out" --mutate "$m" >/dev/null 2>&1; then
		echo "    MUTATION $m PASSED -- the suite cannot fail on it" >&2
		rc=1
	else
		echo "    mutation $m: red, as required"
	fi
done

rm -f "$out"
if [ "$rc" -ne 0 ]; then
	echo "test-spi-wrpolicy: FAILED (a mutation did not go red)" >&2
	exit 1
fi
echo "test-spi-wrpolicy: ok (suite green, both mutations red)"
exit 0
