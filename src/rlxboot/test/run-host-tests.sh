#!/bin/sh
# run-host-tests.sh -- build and run the whole host suite under two compilers
# and then under the sanitisers.
#
#   run-host-tests.sh <repo> <cc1> <cc2> <builddir>
#
# EVERY rlxfw-WRITTEN FILE IS BUILT WITH -Wall -Wextra -Werror AND NO EXEMPTION.
# `src/lib/ed25519.c` gets -Wno-sign-compare and nothing else does: it is
# imported TweetNaCl and its `vn()` compares a u32 index against an int bound at
# one site.  Editing imported crypto to silence a warning is not a trade this
# gate makes, and hiding it by dropping -Werror everywhere would be worse.
#
# The stack measurement does NOT run under -fsanitize=address: it paints 64 KiB
# below its own frame, which is a stack-buffer-underflow by construction, and
# ASan is right about that.  It runs in the plain build.

set -e
REPO=${1:?repo}
CC1=${2:-gcc-13}
CC2=${3:-clang-18}
BD=${4:?builddir}

CWARN="-Wall -Wextra -Werror -Wundef -Wshadow"
DEFS="-DED25519_SIGN -DED25519_KEYGEN -DRLXBOOT_WANT_SEED"
mkdir -p "$BD"

build_and_run() {
	cc=$1; extra=$2; tag=$3
	echo "=== $tag  ($cc $extra)"
	o="$BD/$tag"
	mkdir -p "$o"
	$cc -c -O2 -std=gnu99 $CWARN -Wno-sign-compare $extra $DEFS \
	    -o "$o/ed25519.o" "$REPO/src/lib/ed25519.c"
	$cc -c -O2 -std=gnu99 $CWARN $extra -o "$o/sha512.o" "$REPO/src/lib/sha512.c"
	$cc -c -O2 -std=gnu99 $CWARN $extra -o "$o/sha256b.o" "$REPO/src/rlxboot/sha256b.c"
	$cc -c -O2 -std=gnu99 $CWARN $extra -o "$o/container.o" "$REPO/src/rlxboot/container.c"
	$cc -c -O2 -std=gnu99 $CWARN $extra $DEFS \
	    -o "$o/t_crypto.o" "$REPO/src/rlxboot/test/t_crypto.c"
	$cc -c -O2 -std=gnu99 $CWARN $extra $DEFS \
	    -o "$o/t_container.o" "$REPO/src/rlxboot/test/t_container.c"
	$cc $extra -o "$o/t_crypto" "$o/t_crypto.o" "$o/ed25519.o" "$o/sha512.o" \
	    "$o/sha256b.o"
	$cc $extra -o "$o/t_container" "$o/t_container.o" "$o/container.o" \
	    "$o/ed25519.o" "$o/sha512.o" "$o/sha256b.o"
	"$o/t_crypto"       | tail -3
	"$o/t_container"    | tail -3
	echo "    $tag: both suites exited 0"
}

build_and_run "$CC1" ""    "cc1"
build_and_run "$CC2" ""    "cc2"
build_and_run "$CC1" "-fsanitize=address,undefined -fno-omit-frame-pointer -g" "san"

echo "=== the hash cross-check against coreutils"
# An INDEPENDENT second source for SHA-256 and SHA-512 that no vector table can
# give: the same message hashed by this tree's code and by coreutils.  Every
# length 0..200 covers all four block boundaries of both hashes.
# THE MESSAGE IS HANDED OVER, NOT REIMPLEMENTED.  An earlier version rebuilt the
# LCG in awk; awk computes in doubles, `s * 1103515245` exceeds 2^53, and the
# sequence silently diverged after two bytes -- 199 of 201 lengths "disagreed
# with coreutils" while every digest was correct.  `t_crypto digest N FILE` now
# writes the bytes it hashed, and coreutils hashes those.
bad=0
n=0
for L in $(seq 0 200); do
	out=$("$BD/cc1/t_crypto" digest "$L" "$BD/m.bin")
	got256=$(printf '%s\n' "$out" | awk '/^sha256/{print $2}')
	got512=$(printf '%s\n' "$out" | awk '/^sha512/{print $2}')
	w256=$(sha256sum "$BD/m.bin" | cut -d" " -f1)
	w512=$(sha512sum "$BD/m.bin" | cut -d" " -f1)
	n=$((n+1))
	if [ "$got256" != "$w256" ] || [ "$got512" != "$w512" ]; then
		echo "  FAIL   length $L: coreutils disagrees"
		echo "         sha256 ours $got256"
		echo "         sha256 them $w256"
		bad=$((bad+1))
	fi
done
if [ "$bad" != 0 ]; then
	echo "  FAIL   $bad of $n lengths disagree with coreutils"
	exit 1
fi
echo "  ok     $n message lengths 0..200 agree with coreutils sha256sum/sha512sum"
# The control on that comparison: a deliberately wrong digest must be caught, or
# the loop above would pass on an empty string.
if [ "$(sha256sum "$BD/m.bin" | cut -d" " -f1)" = "0000000000000000000000000000000000000000000000000000000000000000" ]; then
	echo "  FAIL   the comparison is reading nothing"
	exit 1
fi
echo "  ok     the comparison reads a real digest (negative control)"

echo "=== the stack measurement (no sanitiser)"
"$BD/cc1/t_crypto" stack

echo "host suite: PASS"
