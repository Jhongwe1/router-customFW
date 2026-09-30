#!/bin/sh
# run-qemu-payload.sh -- drive the ACTUAL payload end to end under
# qemu-system-mips: stage a container and a counter bitmap in emulated RAM, boot
# rlxboot, and read the RLXBOOT- lines off the emulated serial port.
#
#   run-qemu-payload.sh <repo> <cc> <objcopy> <builddir> <arch flags> <stage2>
#
# WHAT THIS IS WORTH, AND WHAT IT IS NOT.
#
# It is the only place before the bench where the EXACT output lines are read off
# a serial port rather than read off this script's expectations, and the only
# place the copy, the cache writes and the jump all run in sequence.  Every
# reject case costs nothing here and a power cycle there, so every reject case
# runs here first.
#
# It is NOT a device reading and it never will be.  `tools/rlxprobe/qemu-run.sh`
# says why and this inherits all of it: qemu-system-mips's Malta board is a 24Kf,
# a MIPS32 part, where this die is MIPS-I with Config.M = 0 量; qemu interlocks
# the load delay slot this core exposes; and CP0 register 20 is `XContext` there,
# not `CCTL`, so THE CACHE WRITES ARE EXERCISED AS INSTRUCTIONS AND NOT AS CACHE
# OPERATIONS -- they cannot fail here and they can on the die.  The build is
# also marked NOT A DEVICE BUILD: the UART is moved to Malta's 0xB80003F8.
#
# `tools/rlxprobe/qemu-run.sh` itself cannot host this payload: it rebuilds
# through `tools/rlxprobe/Makefile` with `P=<payload>` and gates the capture on
# `rlxprobe: end`.  This script is that harness's shape, with rlxboot's Makefile
# and rlxboot's own gate pattern.

set -e
REPO=${1:?repo}
CC=${2:?cc}
OBJCOPY=${3:?objcopy}
BD=${4:?builddir}
ARCH=${5:-"-EB -mabi=32 -msoft-float -G0 -mno-abicalls -fno-pic"}
STAGE2=${6:-}

if ! command -v qemu-system-mips >/dev/null 2>&1; then
	echo "qemu-system-mips is not installed; skipping (exit 0)"
	exit 0
fi
mkdir -p "$BD"
SEC=${QEMU_SECONDS:-25}

# Malta's 16550: one-byte register spacing, so LSR is THR + 5.  The device's are
# four bytes apart with the value in the top byte -- `tools/rlxprobe/rlxdefs.h`
# owns that difference and this is the only thing that ever overrides it.
QUART="-DRLX_UART_THR=0xB80003F8 -DRLX_UART_LSR=0xB80003FD"

echo "=== the fixture payload rlxboot will boot (linked at 0x80500000)"
$CC $ARCH $QUART -I"$REPO/tools/rlxprobe" \
    -c -o "$BD/qemupay.o" "$REPO/src/rlxboot/test/qemupay.S"
$CC $ARCH -nostdlib -nostartfiles -static \
    -Wl,--defsym,LOAD_ADDR=0x80500000 -Wl,--defsym,STACK_SIZE=0x100 \
    -Wl,-T,"$REPO/src/rlxboot/rlxboot.lds" -o "$BD/qemupay.elf" "$BD/qemupay.o"
$OBJCOPY -O binary "$BD/qemupay.elf" "$BD/qemupay.bin"
ls -l "$BD/qemupay.bin" | sed 's/^/    /'

echo "=== mkfixture, on the host"
HOSTCC=${HOSTCC:-gcc-13}
$HOSTCC -O2 -std=gnu99 -Wall -Wextra -Werror -Wno-sign-compare \
    -DED25519_SIGN -DED25519_KEYGEN -DRLXBOOT_WANT_SEED \
    -o "$BD/mkfixture" \
    "$REPO/src/rlxboot/test/mkfixture.c" "$REPO/src/rlxboot/sha256b.c" \
    "$REPO/src/lib/ed25519.c" "$REPO/src/lib/sha512.c"

echo "=== the fixtures"
"$BD/mkfixture" container "$BD/good.bin"  "$BD/qemupay.bin" 7 80500000 80500000 AABBCCDD
"$BD/mkfixture" rcnt      "$BD/rcnt5.bin" 5
"$BD/mkfixture" rcnt      "$BD/rcnt9.bin" 9
"$BD/mkfixture" flip      "$BD/flipsig.bin" "$BD/good.bin" 100 3
# Byte 5 is the low half of `format`, so this flip is refused at the HEADER
# stage and names the field.  It was byte 30 first -- inside the digest field,
# which the signature covers -- so the console said `RLXBOOT-SIG bad` and the
# case proved nothing about the header checks it was named for.
"$BD/mkfixture" flip      "$BD/fliphdr.bin" "$BD/good.bin" 5 0
# Byte 200 is inside the payload: the container is 160 + 112 = 272 bytes, so
# 400 was past the end and mkfixture refused -- which is the refusal working.
"$BD/mkfixture" flip      "$BD/flippay.bin" "$BD/good.bin" 200 5

run() {
	name=$1; ctr=$2; con=$3
	out="$BD/$name.txt"
	rm -f "$out"
	# KSEG0 0x81000000 -> physical 0x01000000; 0x81700000 -> 0x01700000.
	timeout "$SEC" qemu-system-mips -M malta -m 32 -nographic -monitor none \
		-kernel "$BD/rlxboot-qemu.elf" \
		-device loader,file="$con",addr=0x01000000 \
		${ctr:+-device} ${ctr:+loader,file=$ctr,addr=0x01700000} \
		-serial file:"$out" </dev/null >/dev/null 2>&1 || true
	echo "--- $name"
	tr -d '\r' < "$out" | grep -E '^(RLXBOOT-|RLXPAY-|refuse-action|ctr-bitmap)' \
	    | sed 's/^/    /' || echo "    (no recognised output)"
}

echo "=== rlxboot, built for Malta (NOT A DEVICE BUILD)"
make -s -C "$REPO/src/rlxboot" STAGE="$BD/stage" OUT="$BD/out" \
	CFLAGS_EXTRA="$QUART" qemu-elf 2>&1 | tail -6
cp "$BD/stage/build/rlxboot.elf" "$BD/rlxboot-qemu.elf"

run accept     "$BD/rcnt5.bin"  "$BD/good.bin"
run reject_sig "$BD/rcnt5.bin"  "$BD/flipsig.bin"
run reject_hdr "$BD/rcnt5.bin"  "$BD/fliphdr.bin"
run reject_pay "$BD/rcnt5.bin"  "$BD/flippay.bin"
run rollback   "$BD/rcnt9.bin"  "$BD/good.bin"
run ctr_flash  ""               "$BD/good.bin"

echo
echo "=== verdicts"
fail=0
chk() {
	f="$BD/$1.txt"; pat=$2
	if tr -d '\r' < "$f" | grep -q "$pat"; then
		echo "  ok    $1 contains '$pat'"
	else
		echo "  FAIL  $1 does not contain '$pat'"
		fail=1
	fi
}
chk accept     '^RLXBOOT-SIG ok$'
chk accept     '^RLXBOOT-DIGEST ok$'
chk accept     '^RLXBOOT-VER cur=7 ctr=5 ok$'
chk accept     '^RLXBOOT-BOOT load=80500000 entry=80500000$'
chk accept     '^RLXPAY-OK$'
chk accept     '^RLXBOOT-CTRSRC ram$'
chk reject_sig '^RLXBOOT-SIG bad$'
chk reject_sig '^RLXBOOT-REFUSE sig$'
chk reject_hdr '^RLXBOOT-HDR bad=format$'
chk reject_hdr '^RLXBOOT-REFUSE format$'
chk reject_pay '^RLXBOOT-DIGEST bad$'
chk reject_pay '^RLXBOOT-REFUSE digest$'
chk rollback   '^RLXBOOT-VER cur=7 ctr=9 bad$'
chk rollback   '^RLXBOOT-REFUSE rollback$'
chk ctr_flash  '^RLXBOOT-CTRSRC flash$'
# The negative controls on the accept case: a rejected container must NOT boot.
for r in reject_sig reject_hdr reject_pay rollback; do
	if tr -d '\r' < "$BD/$r.txt" | grep -q 'RLXPAY-OK'; then
		echo "  FAIL  $r BOOTED the payload"
		fail=1
	else
		echo "  ok    $r did not boot the payload"
	fi
done
[ "$fail" = 0 ] || exit 1
echo "qemu payload run: PASS (logic only -- never codegen, never the ISA, and"
echo "CP0 20 is XContext on this model, so the cache writes were not cache ops)"
