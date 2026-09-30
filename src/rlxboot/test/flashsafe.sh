#!/bin/sh
# flashsafe.sh -- run flashscan.py over the linked payload, and over a planted
# flash-write so the scan is shown REFUSING as well as permitting.
#
#   flashsafe.sh <objdump> <elf> <cc> <asflags> <builddir>
#
# The vendor objdump and gcc are used, so the whole `make` this is called from
# belongs under `tools/vendor-tripwire.sh`.

set -e
OBJDUMP=${1:?objdump}
ELF=${2:?elf}
CC=${3:?cc}
ASFLAGS=${4:?asflags}
BD=${5:?builddir}
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-/usr/bin/python3}

mkdir -p "$BD"

echo '--- flashsafe: the counter window against tools/flashwin.py ---'
# THREE levels up, not two: HERE is <repo>/src/rlxboot/test.  Two gave <repo>/src
# and `ctrwin` refused with "No module named 'flashwin'" rather than reporting a
# clean window -- which is the refusal working.
REPO=$(cd "$HERE/../../.." && pwd)
"$PY" "$HERE/ctrwin.py" "$REPO" || exit 1

echo '--- flashsafe: the payload must form no SPI controller address ---'
"$OBJDUMP" -d "$ELF" > "$BD/flashsafe.dis"
if ! "$PY" "$HERE/flashscan.py" < "$BD/flashsafe.dis"; then
	echo "  FAIL   the payload forms an address in the SPI controller block"
	exit 1
fi

echo '--- flashsafe control: a planted flash write must be REFUSED ---'
cat > "$BD/planted_flw.S" <<'EOF'
	.set	noreorder
	.set	nomacro
	.text
	.globl	_planted_flw
_planted_flw:
	lui	$8,0xb800
	ori	$8,$8,0x1200
	sw	$0,0($8)
	jr	$31
	nop
EOF
# shellcheck disable=SC2086
(cd "$BD" && $CC $ASFLAGS -c -o planted_flw.o planted_flw.S)
"$OBJDUMP" -d "$BD/planted_flw.o" > "$BD/planted_flw.dis"
if "$PY" "$HERE/flashscan.py" --quiet < "$BD/planted_flw.dis" > "$BD/planted_flw.log" 2>&1; then
	echo "  FAIL   the scan ACCEPTED a store to 0xB8001200 -- it proves nothing"
	sed 's/^/         /' "$BD/planted_flw.log"
	exit 1
fi
echo "  ok     the scan refused the planted write:"
grep REFUSED "$BD/planted_flw.log" | sed 's/^/         /'

# And the other direction on the control: the same planted object with the
# offset moved OUT of the block must pass, so the refusal is about the address
# and not about the shape of the instruction.
sed 's/0x1200/0x2000/' "$BD/planted_flw.S" > "$BD/planted_ok.S"
# shellcheck disable=SC2086
(cd "$BD" && $CC $ASFLAGS -c -o planted_ok.o planted_ok.S)
"$OBJDUMP" -d "$BD/planted_ok.o" > "$BD/planted_ok.dis"
if "$PY" "$HERE/flashscan.py" --quiet < "$BD/planted_ok.dis" >/dev/null 2>&1; then
	echo "  ok     the same store to 0xB8002000 is permitted (positive control)"
else
	echo "  FAIL   the scan refuses a store outside the block; it is not"
	echo "         discriminating on the address"
	exit 1
fi
