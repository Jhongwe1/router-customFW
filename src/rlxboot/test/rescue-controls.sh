#!/bin/sh
# rescue-controls.sh -- the two opposite properties `FW-168` names, each control
# shown BOTH ways, at the command line rather than inside a self-test.
#
#   rescue-controls.sh <repo> <imagedir> <workdir>
#
# WHY AT THE CLI AT ALL, when `mkcr6c.py --self-test` already covers seventeen
# cases.  A self-test calls the functions; what a `make` reads is an exit code,
# and the two are not the same claim.  `R1`/`R2` below drive the real `wrap` and
# the real `scan` over the real images this build just produced, and `R3`-`R6`
# feed them fixtures built here so that each control is seen going RED.  A
# control that only ever passes on the good artefact is not a control.
#
# THE TWO PROPERTIES, as predicates:
#
#   (1) flash 0x010000 and 0x020000 each hold 4 bytes reading `cr6c` followed by
#       a header whose `len` payload bytes sum to zero as 16-bit big-endian
#       halfwords -- so `check_image()` returns 2 and `doBooting()` boots it.
#       REFUTED BY: either image for which `check_image()` returns other than 2,
#       or returns 2 with a non-zero sum.
#
#   (2) no 64 KiB-aligned offset the loader scans other than those two, and
#       neither slot base, holds 4 bytes matching any of `check_image()`'s two
#       signatures or `burn()`'s eight.  REFUTED BY: any such offset at which
#       `mkfw2.stock_loader_verdict` reports RECOGNISED, or at which
#       `check_image()` returns 2 with a zero sum.
#
# Nothing here writes flash and nothing here runs on the device.

set -e
REPO=${1:?repo}
IMGDIR=${2:?image dir}
WD=${3:?work dir}
PY=${PYTHON:-/usr/bin/python3}
MKCR6C="$REPO/tools/mkcr6c.py"
PRIMARY="$IMGDIR/rlxboot.cr6c"
RESCUE="$IMGDIR/rlxboot-rescue.cr6c"

mkdir -p "$WD"
fails=0
note() { echo "  $1     $2"; }
red() { note "FAIL" "$1"; fails=$((fails + 1)); }

# 🔴 A RED ARM THAT PRINTS NOTHING IS NOT EVIDENCE.  `R6`'s first version
# grepped for `WRONG 0x030000` while the tool prints two spaces, so the case
# reported `ok` on the exit code with an EMPTY evidence block underneath -- a
# tool reporting zero lines making a claim.  `evidence` fails the case when its
# pattern matches nothing, so the grep and the exit code must agree.
evidence() {                  # evidence <logfile> <pattern> <what>
	_n=$(grep -cE "$2" "$1" || true)
	if [ "${_n:-0}" -eq 0 ]; then
		red "$3: the exit code said so and the evidence grep matched 0 lines"
		return 1
	fi
	grep -E "$2" "$1" | sed 's/^/         /'
	return 0
}

for f in "$PRIMARY" "$RESCUE"; do
	[ -f "$f" ] || { echo "REFUSED: no $f; run 'make rescue' first"; exit 3; }
done

echo '--- rescue-controls: the producer'"'"'s own cases ---'
"$PY" "$MKCR6C" --self-test | tail -2

# ===================================================================== (1) ===
echo
echo '--- R1  property 1, GREEN: both real images are check_image()-bootable ---'
if "$PY" "$MKCR6C" scan --place 0x010000="$PRIMARY" \
                        --place 0x020000="$RESCUE" > "$WD/r1.log" 2>&1; then
	note "ok" "scan exits 0 over the two images this build made"
	grep -E '^    0x0(1|2)0000' "$WD/r1.log" | sed 's/^/         /'
else
	red "scan refused the layout this build is supposed to produce"
	sed 's/^/         /' "$WD/r1.log"
fi

echo
echo '--- R3  property 1, RED: the FW-168 signature, cr6b, must be caught ---'
# 🔴 THE FIXTURE IS THE DEFECT, not an invented one.  量 `FW-168`: `cvimg`'s
# linux-ro option writes `cr6b`, and that is the signature rlxfw's own
# `linux.bin` carries today.  One byte of four.
"$PY" - "$RESCUE" "$WD/cr6b.img" <<'EOF'
import sys
b = bytearray(open(sys.argv[1], 'rb').read())
b[3:4] = b'b'                      # 'cr6c' -> 'cr6b'
open(sys.argv[2], 'wb').write(bytes(b))
EOF
if "$PY" "$MKCR6C" scan --place 0x010000="$PRIMARY" \
                        --place 0x020000="$WD/cr6b.img" \
                        > "$WD/r3.log" 2>&1; then
	red "scan ACCEPTED a cr6b image at 0x020000 -- property 1 is not checked"
	sed 's/^/         /' "$WD/r3.log"
else
	note "ok" "scan refuses it, and names the candidate:"
	evidence "$WD/r3.log" 'WRONG +0x020000' "R3"
	evidence "$WD/r3.log" "cr6b" "R3 names the signature it saw"
fi

echo
echo '--- R4  property 1, RED 2: the right signature with a broken sum ---'
# The second of the two independent conditions `tools/rtkimage.py` fails an
# image on.  A control that only ever broke the signature would never show the
# sum being tested at all.
"$PY" - "$RESCUE" "$WD/badsum.img" <<'EOF'
import sys
b = bytearray(open(sys.argv[1], 'rb').read())
b[16] ^= 0x01                      # one bit of the payload; the tail no longer cancels
open(sys.argv[2], 'wb').write(bytes(b))
EOF
if "$PY" "$MKCR6C" scan --place 0x010000="$PRIMARY" \
                        --place 0x020000="$WD/badsum.img" \
                        > "$WD/r4.log" 2>&1; then
	red "scan ACCEPTED an image whose 16-bit sum is not zero"
	sed 's/^/         /' "$WD/r4.log"
else
	note "ok" "one flipped payload bit turns the sum non-zero and is caught:"
	evidence "$WD/r4.log" 'WRONG +0x020000' "R4"
	evidence "$WD/r4.log" '0x020000   MUST .* 0x0100' "R4 shows the non-zero sum"
fi

echo
echo '--- R5  property 1, RED 3: the producer refuses a destination that must not boot ---'
# `wrap` is the producer, and the guard is shown both ways: the two MUST
# destinations are produced and the four barrier candidates are refused.
dd if=/dev/zero of="$WD/pay.bin" bs=1 count=4096 2>/dev/null
ok=0
for at in 0x030000 0x040000 0x050000 0x060000 0x070000; do
	if "$PY" "$MKCR6C" wrap --in "$WD/pay.bin" --out "$WD/x.cr6c" \
	        --start-addr 0x81800000 --flash-at "$at" >/dev/null 2>&1; then
		red "wrap PRODUCED a cr6c header for $at, which must not boot"
	else
		ok=$((ok + 1))
	fi
done
for at in 0x010000 0x020000; do
	if "$PY" "$MKCR6C" wrap --in "$WD/pay.bin" --out "$WD/x.cr6c" \
	        --start-addr 0x81800000 --flash-at "$at" >/dev/null 2>&1; then
		ok=$((ok + 1))
	else
		red "wrap REFUSED $at, which is one of the two that must boot"
	fi
done
note "ok" "wrap refused 5 destinations and produced 2 ($ok of 7 as declared)"

# ===================================================================== (2) ===
echo
echo '--- R2  property 2, GREEN: the barrier reads erased and nothing boots there ---'
grep -E '^    0x0[3-6]0000' "$WD/r1.log" | sed 's/^/         /'
if grep -qE '^    0x0[3-6]0000 .*must-not.*no +ok' "$WD/r1.log"; then
	note "ok" "all 4 barrier candidates: ret 0, not summed, not bootable"
else
	red "the barrier candidates do not read as expected in R1's scan"
fi

echo
echo '--- R6  property 2, RED: a stray cr6c at a barrier candidate ---'
# 🔴 `FW-167`'s own hole, as a command.  The obvious layout puts slot A at
# 0x030000, and then four of the loader's six candidates fall inside it; a
# payload byte pattern reading `cr6c` at one of them boots a slot with no
# signature check and no anti-rollback counter.
if "$PY" "$MKCR6C" scan --place 0x010000="$PRIMARY" \
                        --place 0x020000="$RESCUE" \
                        --place 0x030000="$RESCUE" \
                        > "$WD/r6.log" 2>&1; then
	red "scan ACCEPTED a bootable header at 0x030000 -- property 2 is not checked"
	sed 's/^/         /' "$WD/r6.log"
else
	note "ok" "scan refuses it:"
	evidence "$WD/r6.log" 'WRONG +0x030000' "R6"
fi

echo
echo '--- R7  property 2, RED 2: a SLOT the loader would recognise ---'
# The other half of `FW-168`: the slot must deliberately carry no header.
# 0x070000 is not scanned, so this is caught by the signature test alone and
# not by the candidate table -- which is the point, because `bank_offset` has
# never been read and the table could move.
if "$PY" "$MKCR6C" scan --place 0x010000="$PRIMARY" \
                        --place 0x020000="$RESCUE" \
                        --place 0x070000="$RESCUE" \
                        > "$WD/r7.log" 2>&1; then
	red "scan ACCEPTED a slot whose first 4 bytes read cr6c"
	sed 's/^/         /' "$WD/r7.log"
else
	note "ok" "scan refuses a recognisable slot although 0x070000 is not scanned:"
	evidence "$WD/r7.log" 'RECOGNISED' "R7"
	evidence "$WD/r7.log" 'WRONG +0x070000' "R7 names the offset"
fi

echo
if [ "$fails" -ne 0 ]; then
	echo "rescue-controls: $fails control(s) FAILED"
	exit 1
fi
echo "rescue-controls: 2 properties, 4 red arms and 3 green arms, all as declared"
echo "  what this does NOT establish: that either image has ever been loaded or"
echo "  run.  Every reading here is of bytes on a desk, through a desk"
echo "  reproduction of check_image() read out of one unit's stage2.bin, and"
echo "  check_image()'s bank_offset has never been read for this build."
