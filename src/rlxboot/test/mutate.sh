#!/bin/sh
# mutate.sh -- the mutation controls.  A green suite is a claim about its
# controls; this is what tests them.
#
#   mutate.sh <repo> <cc> <builddir>
#
# BEFORE TRUSTING A MUTATION RUN, CONFIRM THE UNMUTATED SUITE PASSES.  That is
# step 0 below and it is not decoration: a mutation run against a suite that was
# already red says nothing at all.
#
# Two mutations, and they are chosen because they are the two ways this design
# could be wrong that no vector set would notice.
#
#   M1  the digest comparison tests only the first byte.
#       EXPECTED: the bit-flip sweep goes red.  A flipped payload bit changes
#       the SHA-256 everywhere, so 255 in 256 flips would still be caught by
#       byte 0 -- the sweep is 8,192 payload flips, so the ~32 that leave byte 0
#       unchanged are what turn it red.  If this mutation passed, the sweep would
#       be testing SHA-256 and not the comparison.
#
#   M2  verification is reordered so the payload is hashed BEFORE the signature
#       is checked -- exactly the defect this unit's own stage 2 has
#       (`check_image()` copies to a header-supplied address before checksumming).
#       EXPECTED: no accept/reject verdict changes anywhere, so no functional
#       case catches it.  What catches it is the ORDER test: `r.trace` and
#       `r.hashed`.  This is reported honestly either way -- if neither goes red,
#       the test list is incomplete and that is the finding.

set -e
REPO=${1:?repo}
CC=${2:-gcc-13}
BD=${3:?builddir}

CWARN="-Wall -Wextra -Wundef -Wshadow"
DEFS="-DED25519_SIGN -DED25519_KEYGEN -DRLXBOOT_WANT_SEED"
mkdir -p "$BD"

mkclone() {
	rm -rf "$BD/tree"
	mkdir -p "$BD/tree/src/lib" "$BD/tree/src/rlxboot/test"
	cp "$REPO"/src/lib/*.c "$REPO"/src/lib/*.h "$BD/tree/src/lib/"
	cp "$REPO"/src/rlxboot/*.c "$REPO"/src/rlxboot/*.h "$BD/tree/src/rlxboot/"
	cp "$REPO"/src/rlxboot/test/*.c "$REPO"/src/rlxboot/test/*.h \
	   "$BD/tree/src/rlxboot/test/"
}

buildrun() {
	t="$BD/tree"
	o="$BD/obj"
	rm -rf "$o"; mkdir -p "$o"
	$CC -c -O2 -std=gnu99 $CWARN -Wno-sign-compare $DEFS -o "$o/ed.o" "$t/src/lib/ed25519.c"
	$CC -c -O2 -std=gnu99 $CWARN -o "$o/s5.o" "$t/src/lib/sha512.c"
	$CC -c -O2 -std=gnu99 $CWARN -o "$o/s2.o" "$t/src/rlxboot/sha256b.c"
	$CC -c -O2 -std=gnu99 $CWARN -o "$o/co.o" "$t/src/rlxboot/container.c"
	$CC -c -O2 -std=gnu99 $CWARN $DEFS -o "$o/tk.o" "$t/src/rlxboot/test/t_container.c"
	$CC -o "$o/t" "$o/tk.o" "$o/co.o" "$o/ed.o" "$o/s5.o" "$o/s2.o"
	"$o/t" > "$BD/out.txt" 2>&1 || true
	grep -c '^FAIL' "$BD/out.txt" || true
}

echo '=== step 0: the UNMUTATED suite must pass, or the run means nothing'
mkclone
n=$(buildrun)
if [ "$n" != "0" ]; then
	echo "  REFUSED  the unmutated suite already has $n failures"
	grep '^FAIL' "$BD/out.txt" | head -5 | sed 's/^/           /'
	exit 2
fi
echo "  ok       unmutated: 0 failures"

echo '=== M1: the digest comparison tests only the first byte'
mkclone
# `ct_eq32` loops i = 0..31.  Make it stop after the first byte.  Anchored on
# the function's own text, and checked below -- a mutation that silently fails
# to apply is the one way a mutation run lies.
perl -0pi -e 's/(static int ct_eq32\(const unsigned char \*a, const unsigned char \*b\)\s*\{\s*unsigned long d = 0;\s*int i;\s*\n\s*for \(i = 0; i < )32(; i\+\+\))/${1}1${2}/s' \
	"$BD/tree/src/rlxboot/container.c"
if ! grep -q 'i < 1; i++' "$BD/tree/src/rlxboot/container.c"; then
	echo "  REFUSED  the mutation did not apply; ct_eq32 no longer has the"
	echo "           shape this script edits.  A mutation that silently does"
	echo "           nothing reports the suite as robust when it was untested."
	exit 2
fi
n=$(buildrun)
if [ "$n" = "0" ]; then
	echo "  FAIL     M1 applied and the suite still passed: the bit-flip sweep"
	echo "           is not testing the digest comparison"
	exit 1
fi
echo "  ok       M1 turned the suite red ($n failures):"
grep '^FAIL' "$BD/out.txt" | head -4 | sed 's/^/           /'

echo '=== M2: hash the payload BEFORE checking the signature'
mkclone
# Move the whole digest block above the signature check by swapping the two
# blocks' order with a marker-driven rewrite.  The blocks are delimited by the
# step comments in container.c, so the edit is anchored on text that exists for
# the reader and not on line numbers.
perl -0pi -e '
  my $sig = qr/(\ttrace\(r, RLXU_T_SIG\);.*?\tpassed\(r, rep, RLXU_T_SIG\);\n)/s;
  my $dig = qr/(\ttrace\(r, RLXU_T_DIGEST\);.*?\tpassed\(r, rep, RLXU_T_DIGEST\);\n)/s;
  if (/$sig/ and /$dig/) {
    my ($s) = /$sig/; my ($d) = /$dig/;
    s/$sig//; s/$dig/$d$s/;
  }
' "$BD/tree/src/rlxboot/container.c"
# Did it apply?  The digest block must now come first.
si=$(grep -n 'trace(r, RLXU_T_SIG)' "$BD/tree/src/rlxboot/container.c" | head -1 | cut -d: -f1)
di=$(grep -n 'trace(r, RLXU_T_DIGEST)' "$BD/tree/src/rlxboot/container.c" | head -1 | cut -d: -f1)
if [ -z "$si" ] || [ -z "$di" ] || [ "$di" -gt "$si" ]; then
	echo "  REFUSED  the reorder did not apply (sig at $si, digest at $di)"
	exit 2
fi
echo "  ok       reorder applied: digest block now at line $di, signature at $si"
n=$(buildrun)
if [ "$n" = "0" ]; then
	echo "  FINDING  M2 applied and EVERY test still passed."
	echo "           No functional case can see this reordering, which is the"
	echo "           honest answer -- and it means the test list needs the"
	echo "           order test to be present, not just the verdict tests."
	exit 1
fi
echo "  ok       M2 turned the suite red ($n failures) -- caught by:"
grep '^FAIL' "$BD/out.txt" | head -6 | sed 's/^/           /'

echo 'mutate: both mutations were applied and both were caught'
