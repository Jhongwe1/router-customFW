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

echo "=== rlxboot BOOT=ram, built for Malta (NOT A DEVICE BUILD)"
# The make's status is read, not a `tail`'s: with `| tail -6` a failed build
# exited 0 and the `cp` below picked up whatever ELF an earlier run left.
rm -f "$BD/stage/build/rlxboot.elf"
rc=0
make -s -C "$REPO/src/rlxboot" BOOT=ram KEY=dev STAGE="$BD/stage" OUT="$BD/out" \
	CFLAGS_EXTRA="$QUART" qemu-elf > "$BD/make-ram.log" 2>&1 || rc=$?
tail -6 "$BD/make-ram.log"
[ "$rc" -eq 0 ] || { echo "  FAIL  the BOOT=ram qemu build exited $rc"; exit 1; }
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

# ============================================================ BOOT=slots ===
#
# R8b's path, end to end: the real payload reads two slots through its flash
# window, verifies each in its own buffer, prints its verdicts, and boots the
# winner or halts.  Malta decodes nothing at 0x1D000000, so this build moves
# the window to physical 0x00C00000 (KSEG1 0xA0C00000) -- below slot A's
# buffer at 0x01000000, above the fixture's 0x00500000, inside -m 32 -- and
# a 4 MiB image built here, 0xFF except where a case places a container, is
# loaded there.  THE WINDOW'S CONTENTS ARE MODELLED AND NONE OF ITS
# BEHAVIOUR: a load from emulated RAM is not a transaction to an SPI
# controller, its timing is nothing like 2.075 us, and whether the device
# decodes 0xBD070000-0xBD2AFFFF at the loader prompt is not touched here.
#
# The payload booted from slot B is the fixture with `RLXPAY-OK` patched to
# `RLXPAY-OB`, so the line the BOOTED code prints says which slot's bytes ran
# -- a reading of the jump, not of rlxboot's own claim about it.
QWIN=0xA0C00000
QWIN_PHYS=0x00C00000
PY=${PYTHON:-/usr/bin/python3}

echo
echo "=== rlxboot BOOT=slots, built for Malta, window at $QWIN (NOT A DEVICE BUILD)"
rm -f "$BD/stage-slots/build/rlxboot.elf"
rc=0
make -s -C "$REPO/src/rlxboot" BOOT=slots KEY=dev STAGE="$BD/stage-slots" \
	OUT="$BD/out-slots" CFLAGS_EXTRA="$QUART -DRLXB_FLASH_WIN=${QWIN}UL" \
	qemu-elf > "$BD/make-slots.log" 2>&1 || rc=$?
tail -6 "$BD/make-slots.log"
[ "$rc" -eq 0 ] || { echo "  FAIL  the BOOT=slots qemu build exited $rc"; exit 1; }
cp "$BD/stage-slots/build/rlxboot.elf" "$BD/rlxboot-slots-qemu.elf"

echo "=== the slot fixtures"
"$PY" - "$BD/qemupay.bin" "$BD/qemupayB.bin" <<'EOF'
import sys
b = open(sys.argv[1], 'rb').read()
if b.count(b'RLXPAY-OK') != 1:
    sys.exit("qemupay.bin does not hold RLXPAY-OK exactly once")
open(sys.argv[2], 'wb').write(b.replace(b'RLXPAY-OK', b'RLXPAY-OB'))
EOF
"$BD/mkfixture" container "$BD/sA7.bin"  "$BD/qemupay.bin"  7 80500000 80500000 AABBCCDD 070000 whole
"$BD/mkfixture" container "$BD/sB8.bin"  "$BD/qemupayB.bin" 8 80500000 80500000 AABBCCDD 190000 whole
"$BD/mkfixture" container "$BD/sB7.bin"  "$BD/qemupayB.bin" 7 80500000 80500000 AABBCCDD 190000 whole
"$BD/mkfixture" flip      "$BD/sB8flip.bin" "$BD/sB8.bin" 200 5
"$BD/mkfixture" container "$BD/sAforB.bin" "$BD/qemupay.bin" 9 80500000 80500000 AABBCCDD 190000 whole

# mkflash OUT [A=FILE] [B=FILE] [tornA]: 4 MiB of 0xFF, containers at the slot
# bases, and `tornA` erases slot A's first 256-byte page -- D5's state after a
# cut that fell before the header page was programmed.
mkflash() {
	"$PY" - "$@" <<'EOF'
import sys
img = bytearray(b'\xff' * 0x400000)
for arg in sys.argv[2:]:
    k, _, v = arg.partition('=')
    if k in ('A', 'B'):
        off = 0x070000 if k == 'A' else 0x190000
        c = open(v, 'rb').read()
        img[off:off + len(c)] = c
    elif k == 'tornA':
        img[0x070000:0x070100] = b'\xff' * 256
    else:
        sys.exit('mkflash: unknown argument %r' % arg)
open(sys.argv[1], 'wb').write(bytes(img))
EOF
}
mkflash "$BD/f_a_only.bin"   A="$BD/sA7.bin"
mkflash "$BD/f_b_higher.bin" A="$BD/sA7.bin" B="$BD/sB8.bin"
mkflash "$BD/f_tie.bin"      A="$BD/sA7.bin" B="$BD/sB7.bin"
mkflash "$BD/f_none.bin"     A="$BD/sA7.bin" B="$BD/sB8flip.bin" tornA
mkflash "$BD/f_wrong.bin"    A="$BD/sAforB.bin"

# ============================================================ KEY=prod ===
#
# D15's production path, with a THROWAWAY key made for this run: a random seed
# in $BD -- never in the repository -- whose public half `mkprodkey.py` writes
# to a header in $BD that the build reads through PRODKEY_H, one container
# signed with it by `tools/mkfw2.py`, and the seed deleted before any image
# runs.  First the refusal: a KEY=prod build against a header that holds no
# key must stop before anything is compiled, and say why.
echo
echo "=== KEY=prod against a header holding no key: must REFUSE"
"$PY" -B "$REPO/src/rlxboot/mkprodkey.py" none --out "$BD/prodkey-none.h"
rm -rf "$BD/stage-none"
rc=0
make -s -C "$REPO/src/rlxboot" BOOT=slots KEY=prod PRODKEY_H="$BD/prodkey-none.h" \
	STAGE="$BD/stage-none" OUT="$BD/out-none" CFLAGS_EXTRA="$QUART" \
	qemu-elf > "$BD/make-none.log" 2>&1 || rc=$?
sed 's/^/    /' "$BD/make-none.log" | head -4
if [ "$rc" -ne 0 ] && grep -q 'holds NO production key' "$BD/make-none.log" \
   && [ ! -f "$BD/stage-none/build/rlxboot.elf" ]; then
	echo "  ok    refused (make exit $rc), named the reason, and built nothing"
else
	echo "  FAIL  KEY=prod with no key: make exit $rc, or no reason, or an ELF"
	fail=1
fi

echo "=== KEY=prod with a throwaway key"
TS="$BD/throwaway.seed"
rm -f "$TS"
head -c 32 /dev/urandom > "$TS"
TPUB=$("$PY" -B "$REPO/tools/rlxsign.py" pubkey --seed-file "$TS")
"$PY" -B "$REPO/src/rlxboot/mkprodkey.py" write --pubkey "$TPUB" \
	--out "$BD/prodkey-throwaway.h"
rc=0
"$PY" -B "$REPO/tools/mkfw2.py" build --payload "$BD/qemupay.bin" \
	--out "$BD/pA7.bin" --version 7 --load-addr 0x80500000 \
	--entry-addr 0x80500000 --recipe-id AABBCCDD --flash-at 0x070000 \
	--flash-form whole --seed-file "$TS" > "$BD/pA7.log" 2>&1 || rc=$?
rm -f "$TS"
[ "$rc" -eq 0 ] || { echo "  FAIL  mkfw2 build with the throwaway seed exited $rc"; exit 1; }
[ ! -e "$TS" ] || { echo "  FAIL  the throwaway seed is still on disk"; exit 1; }
rm -f "$BD/stage-prod/build/rlxboot.elf"
rc=0
make -s -C "$REPO/src/rlxboot" BOOT=slots KEY=prod \
	PRODKEY_H="$BD/prodkey-throwaway.h" STAGE="$BD/stage-prod" \
	OUT="$BD/out-prod" CFLAGS_EXTRA="$QUART -DRLXB_FLASH_WIN=${QWIN}UL" \
	qemu-elf > "$BD/make-prod.log" 2>&1 || rc=$?
tail -3 "$BD/make-prod.log"
[ "$rc" -eq 0 ] || { echo "  FAIL  the KEY=prod qemu build exited $rc"; exit 1; }
cp "$BD/stage-prod/build/rlxboot.elf" "$BD/rlxboot-prod-qemu.elf"
# Slot A signed with the throwaway key, slot B dev-signed at a HIGHER version:
# each image must take the slot signed with its own key and refuse the other.
mkflash "$BD/f_prod.bin" A="$BD/pA7.bin" B="$BD/sB8.bin"

# The runs go side by side: each is bounded by `timeout` and none's status is
# read (the verdict is the capture), so nothing waits on a status it needs.
srun() {     # srun <case> <flash image> [elf] [RCNT block for 0x81700000]
	rm -f "$BD/$1.txt"
	timeout "$SEC" qemu-system-mips -M malta -m 32 -nographic -monitor none \
		-kernel "${3:-$BD/rlxboot-slots-qemu.elf}" \
		-device loader,file="$2",addr=$QWIN_PHYS \
		${4:+-device} ${4:+loader,file=$4,addr=0x01700000} \
		-serial file:"$BD/$1.txt" </dev/null >/dev/null 2>&1 || true
}
# D21: a valid RCNT block (count 9) staged where R8a's bench put one.  The
# RAM image honours exactly this block in `rollback` above (ctr=9, refused);
# the slots image must not read it at all.
srun s_rcnt     "$BD/f_a_only.bin" "$BD/rlxboot-slots-qemu.elf" "$BD/rcnt9.bin" &
srun s_a_only   "$BD/f_a_only.bin" &
srun s_b_higher "$BD/f_b_higher.bin" &
srun s_tie      "$BD/f_tie.bin" &
srun s_none     "$BD/f_none.bin" &
srun s_wrong    "$BD/f_wrong.bin" &
srun p_prod     "$BD/f_prod.bin" "$BD/rlxboot-prod-qemu.elf" &
srun p_devimg   "$BD/f_prod.bin" &
wait
for name in s_rcnt s_a_only s_b_higher s_tie s_none s_wrong p_prod p_devimg; do
	echo "--- $name"
	tr -d '\r' < "$BD/$name.txt" \
	    | grep -E '^(RLXBOOT-|RLXPAY-|refuse-action|ctr-bitmap)' \
	    | sed 's/^/    /' || echo "    (no recognised output)"
done

# n= is the container's length rounded up to a word; under 64 KiB, no dots.
nA=$(( ($(wc -c < "$BD/sA7.bin") + 3) / 4 * 4 ))
nB=$(( ($(wc -c < "$BD/sB8.bin") + 3) / 4 * 4 ))
nono() {   # nono <case> <pattern>: the pattern must NOT appear
	if tr -d '\r' < "$BD/$1.txt" | grep -q "$2"; then
		echo "  FAIL  $1 contains '$2'"
		fail=1
	else
		echo "  ok    $1 does not contain '$2'"
	fi
}
echo
echo "=== slot verdicts"
chk s_a_only   '^RLXBOOT-CTRSRC flash$'
chk s_a_only   "^RLXBOOT-READ A flash=00070000 buf=81000000 n=$nA\$"
chk s_a_only   '^RLXBOOT-READ B flash=00190000 buf=81200000 n=160$'
chk s_a_only   '^RLXBOOT-VERDICT A ok ver=7$'
chk s_a_only   '^RLXBOOT-VERDICT B bad=magic$'
chk s_a_only   '^RLXBOOT-SLOT A$'
chk s_a_only   '^RLXBOOT-BOOT load=80500000 entry=80500000$'
chk s_a_only   '^RLXPAY-OK$'
chk s_b_higher "^RLXBOOT-READ B flash=00190000 buf=81200000 n=$nB\$"
chk s_b_higher '^RLXBOOT-VERDICT A ok ver=7$'
chk s_b_higher '^RLXBOOT-VERDICT B ok ver=8$'
chk s_b_higher '^RLXBOOT-SLOT B$'
chk s_b_higher '^RLXPAY-OB$'
nono s_b_higher 'RLXPAY-OK'
chk s_tie      '^RLXBOOT-VERDICT A ok ver=7$'
chk s_tie      '^RLXBOOT-VERDICT B ok ver=7$'
chk s_tie      '^RLXBOOT-SLOT A$'
chk s_tie      '^RLXPAY-OK$'
nono s_tie     'RLXPAY-OB'
chk s_none     '^RLXBOOT-VERDICT A bad=magic$'
chk s_none     '^RLXBOOT-VERDICT B bad=digest$'
chk s_none     '^RLXBOOT-HALT A=magic B=digest$'
chk s_none     '^refuse-action halt$'
nono s_none    'RLXPAY-'
nono s_none    'RLXBOOT-BOOT'
nono s_none    'RLXBOOT-SLOT'
chk s_wrong    '^RLXBOOT-VERDICT A bad=flash_match$'
chk s_wrong    '^RLXBOOT-HALT A=flash_match B=magic$'
nono s_wrong   'RLXPAY-'
echo
echo "=== D21: the RAM counter, both builds"
chk rollback   '^RLXBOOT-CTRSRC ram$'
chk rollback   '^RLXBOOT-VER cur=7 ctr=9 bad$'
chk s_rcnt     '^RLXBOOT-CTRSRC flash$'
nono s_rcnt    'RLXBOOT-CTRSRC ram'
chk s_rcnt     '^RLXBOOT-VER cur=7 ctr=0 ok$'
chk s_rcnt     '^RLXBOOT-SLOT A$'
chk s_rcnt     '^RLXPAY-OK$'
echo
echo "=== key verdicts"
DEVHEX=$(grep -o '[0-9a-f]\{64\}' "$REPO/src/rlxboot/devkey.h" | head -1)
chk accept     "^RLXBOOT-KEY dev $DEVHEX\$"
chk s_a_only   "^RLXBOOT-KEY dev $DEVHEX\$"
chk p_prod     "^RLXBOOT-KEY prod $TPUB\$"
chk p_prod     '^RLXBOOT-VERDICT A ok ver=7$'
chk p_prod     '^RLXBOOT-VERDICT B bad=sig$'
chk p_prod     '^RLXBOOT-SLOT A$'
chk p_prod     '^RLXPAY-OK$'
nono p_prod    'RLXPAY-OB'
chk p_devimg   "^RLXBOOT-KEY dev $DEVHEX\$"
chk p_devimg   '^RLXBOOT-VERDICT A bad=sig$'
chk p_devimg   '^RLXBOOT-VERDICT B ok ver=8$'
chk p_devimg   '^RLXBOOT-SLOT B$'
chk p_devimg   '^RLXPAY-OB$'
nono p_devimg  'RLXPAY-OK'
# One banner per run: a halt that reset would print it again.
for name in s_rcnt s_a_only s_b_higher s_tie s_none s_wrong p_prod p_devimg; do
	nb=$(tr -d '\r' < "$BD/$name.txt" | grep -c '^RLXBOOT-V1 ' || true)
	if [ "$nb" = 1 ]; then
		echo "  ok    $name printed the banner once"
	else
		echo "  FAIL  $name printed the banner $nb times"
		fail=1
	fi
done
[ "$fail" = 0 ] || exit 1
echo "qemu payload run: PASS (logic only -- never codegen, never the ISA, and"
echo "CP0 20 is XContext on this model, so the cache writes were not cache ops)"
