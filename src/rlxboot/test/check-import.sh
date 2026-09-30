#!/bin/sh
# check-import.sh -- the control on the provenance claim.
#
#   check-import.sh <repo> [upstream tweetnacl.c]
#
# `src/lib/ed25519.c` and `src/lib/sha512.c` say in their headers that the text
# between their IMPORTED markers is TweetNaCl 20140427, unaltered.  That is an
# assertion.  This is the instrument.
#
# With the upstream file: `mk-import.sh` regenerates both files and they must be
# byte-identical to what is in the tree.  That is the strong form and it is what
# the segment that wrote them ran.
#
# Without it (no network, or the file was not kept -- it is NOT committed): the
# sha256 of each file's IMPORTED regions is compared with the value recorded
# below.  That catches an edit to imported code, which is what the check is for;
# it does not re-prove the upstream origin, and it says so.
#
# The recorded digests are of the concatenated IMPORTED regions only -- the
# comments, the wrapper and the `#include`s are excluded, so rlxfw can edit its
# own half of either file without touching this.

set -e
REPO=${1:?repo}
UP=${2:-}
HERE=$(cd "$(dirname "$0")" && pwd)

UPSTREAM_SHA=02e65bc3013ff2168983365e55906bc783c4c7e0a60d8100f17bb303a17175c4
ED_REGION_SHA=54caecd85e5be9b1ef7c7aa3ee8eb87d2daac96034acfb8491d75c7d29760d60
S5_REGION_SHA=f3aba5cc1af8adfb09db61fd33156994191ce91faa636eb2c9c94099a34a5052

regions() {
	awk '/----- BEGIN IMPORTED/{p=1;next} /----- END IMPORTED/{p=0;next} p' "$1"
}

echo "upstream  https://tweetnacl.cr.yp.to/20140427/tweetnacl.c"
echo "          sha256 $UPSTREAM_SHA  (public domain)"

if [ -n "$UP" ]; then
	echo '--- strong form: regenerate from upstream and diff ---'
	got=$(sha256sum "$UP" | cut -d' ' -f1)
	if [ "$got" != "$UPSTREAM_SHA" ]; then
		echo "  REFUSED  $UP is sha256 $got, not the pinned upstream"
		exit 2
	fi
	tmp=$(mktemp -d)
	trap 'rm -rf "$tmp"' EXIT
	sh "$HERE/mk-import.sh" "$UP" "$tmp" >/dev/null
	rc=0
	for f in ed25519.c sha512.c; do
		if cmp -s "$tmp/$f" "$REPO/src/lib/$f"; then
			echo "  ok       src/lib/$f is byte-identical to the regeneration"
		else
			echo "  FAIL     src/lib/$f differs from the regeneration:"
			diff -u "$tmp/$f" "$REPO/src/lib/$f" | head -20 | sed 's/^/           /'
			rc=1
		fi
	done
	exit $rc
fi

echo '--- weak form: the IMPORTED regions digest ---'
ed=$(regions "$REPO/src/lib/ed25519.c" | sha256sum | cut -d' ' -f1)
s5=$(regions "$REPO/src/lib/sha512.c" | sha256sum | cut -d' ' -f1)
rc=0
if [ "$ED_REGION_SHA" = "__ED_REGION_SHA__" ]; then
	echo "  ed25519.c imported regions: $ed"
	echo "  sha512.c  imported regions: $s5"
	echo "  REFUSED  the expected digests are not recorded in this script yet."
	echo "           Paste the two values above into ED_REGION_SHA and"
	echo "           S5_REGION_SHA.  Refusing rather than passing: a check with"
	echo "           no expected value is a check that cannot fail."
	exit 2
fi
if [ "$ed" = "$ED_REGION_SHA" ]; then
	echo "  ok       ed25519.c imported regions unaltered ($ed)"
else
	echo "  FAIL     ed25519.c imported regions changed"
	echo "           want $ED_REGION_SHA"
	echo "           got  $ed"
	rc=1
fi
if [ "$s5" = "$S5_REGION_SHA" ]; then
	echo "  ok       sha512.c imported regions unaltered ($s5)"
else
	echo "  FAIL     sha512.c imported regions changed"
	echo "           want $S5_REGION_SHA"
	echo "           got  $s5"
	rc=1
fi
exit $rc
