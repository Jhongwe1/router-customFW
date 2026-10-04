#!/bin/sh
# run-qemu-tests.sh -- the same sources, cross-compiled BIG-ENDIAN MIPS by the
# same rsdk gcc 3.4.6 that builds the payload, run under qemu-mips-static.
#
#   run-qemu-tests.sh <repo> <cc> <builddir> <arch flags>
#
# WHAT THIS IS A SECOND SOURCE FOR, AND WHAT IT IS NOT.
#
# It IS a second source for byte order.  A verifier that is correct
# little-endian and wrong big-endian passes every host test; SPEC-R8a.md s3 names
# that as the defect this run exists to catch, and it catches it because the ONLY
# difference from the host run is the target's endianness and the vendor
# compiler's codegen.
#
# It is NOT a statement about the device.  qemu interlocks the load delay slot
# this core exposes, it is a MIPS32 model where this die is MIPS-I with
# Config.M = 0, and `CLAUDE.md` forbids measuring the ISA or a CPU hazard under
# emulation at all.  A green run here certifies LOGIC.  It certifies no codegen
# property, no cache behaviour, no timing and nothing about the silicon.
#
# It links uClibc statically, so it is a Linux user-mode binary and not the
# payload: the payload has no libc and is tested by `make payload` plus the
# bench.  What the two share is every line of container.c, sha256b.c, ed25519.c,
# sha512.c and slots.c -- whose flash window is a 4 MiB array here, so this run
# models the window's CONTENTS and none of its behaviour.

set -e
REPO=${1:?repo}
CC=${2:?cc}
BD=${3:?builddir}
ARCH=${4:-"-EB -mabi=32 -msoft-float"}

if ! command -v qemu-mips-static >/dev/null 2>&1; then
	echo "qemu-mips-static is not installed; skipping (exit 0)"
	exit 0
fi

CWARN="-Wall -Wextra -Wundef -Wshadow"
DEFS="-DED25519_SIGN -DED25519_KEYGEN -DRLXBOOT_WANT_SEED"
mkdir -p "$BD"

# -Werror is NOT passed here and that is deliberate: gcc 3.4.6 is 19 years older
# than the host compilers and warns about things they do not, and a warning from
# it is a finding to read rather than a build to fail.  `make payload` -- the
# artefact -- IS built with -Werror.  The warning log is kept and printed.
cd "$BD"
set -x
$CC $ARCH -O2 -std=gnu99 $CWARN -Wno-sign-compare $DEFS \
    -c -o ed25519.o "$REPO/src/lib/ed25519.c"          2> w_ed.log
$CC $ARCH -O2 -std=gnu99 $CWARN -c -o sha512.o "$REPO/src/lib/sha512.c" 2> w_sha512.log
$CC $ARCH -O2 -std=gnu99 $CWARN -c -o sha256b.o "$REPO/src/rlxboot/sha256b.c" 2> w_sha256.log
$CC $ARCH -O2 -std=gnu99 $CWARN -c -o container.o "$REPO/src/rlxboot/container.c" 2> w_cont.log
$CC $ARCH -O2 -std=gnu99 $CWARN -c -o slots.o "$REPO/src/rlxboot/slots.c" 2> w_slots.log
$CC $ARCH -O2 -std=gnu99 $CWARN -DRLXBOOT_SLOTS=0 -c -o flashread_ram.o \
    "$REPO/src/rlxboot/flashread.c"                    2> w_fr0.log
$CC $ARCH -O2 -std=gnu99 $CWARN -DRLXBOOT_SLOTS=1 -c -o flashread_slots.o \
    "$REPO/src/rlxboot/flashread.c"                    2> w_fr1.log
$CC $ARCH -O2 -std=gnu99 $CWARN $DEFS -c -o t_crypto.o \
    "$REPO/src/rlxboot/test/t_crypto.c"                2> w_tc.log
$CC $ARCH -O2 -std=gnu99 $CWARN $DEFS -c -o t_container.o \
    "$REPO/src/rlxboot/test/t_container.c"             2> w_tk.log
$CC $ARCH -O2 -std=gnu99 $CWARN $DEFS -c -o t_slots.o \
    "$REPO/src/rlxboot/test/t_slots.c"                 2> w_ts.log
$CC $ARCH -static -o t_crypto t_crypto.o ed25519.o sha512.o sha256b.o
$CC $ARCH -static -o t_container t_container.o container.o flashread_ram.o \
    ed25519.o sha512.o sha256b.o
$CC $ARCH -static -o t_slots t_slots.o slots.o container.o flashread_slots.o \
    ed25519.o sha512.o sha256b.o
set +x

echo "=== gcc 3.4.6 warnings (read, not failed on)"
cat w_*.log | grep -v '^$' | sort -u | head -40 || true
echo "=== byte order of what we just built"
file t_crypto | sed 's/^/    /'
if ! file t_crypto | grep -q MSB; then
	echo "  FAIL   this is not a big-endian binary; the whole point is lost"
	exit 1
fi
echo "  ok     MSB (big-endian), which is the property this run exists for"

# Each suite's status read with no pipe on it: `| tail -8` gave tail's 0 for a
# red suite until 2026-10-05, the same defect `run-host-tests.sh` records.
for t in t_crypto t_container t_slots; do
	echo "=== $t under qemu-mips-static"
	rc=0
	qemu-mips-static "./$t" > "$t.out" 2>&1 || rc=$?
	tail -8 "$t.out"
	if [ "$rc" -ne 0 ]; then
		echo "  FAIL   $t exited $rc under qemu-mips-static:"
		grep '^FAIL' "$t.out" | head -10 | sed 's/^/         /'
		exit 1
	fi
done
echo "=== the derived public key, big-endian"
qemu-mips-static ./t_crypto devkey
echo "=== the verifier's stack depth, big-endian"
qemu-mips-static ./t_crypto stack

echo "qemu suite: PASS (logic only -- never codegen, never the ISA)"
