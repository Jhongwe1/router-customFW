#!/usr/bin/env bash
# Controls for tools/opcount.py.
#
# The fixture's machine code is hardcoded here rather than assembled, so the
# test runs on a machine with no MIPS cross-assembler. When one IS present the
# test additionally re-derives the fixture from source and checks that the
# hardcoded words still match -- a control on the control.
#
# Three cases:
#   P1  known counts must be reproduced exactly
#   N1  reading the fixture little-endian must NOT give the same answer
#   N2  scanning from a 2-byte offset must NOT give the same answer
#
# N1 and N2 exist because P1 alone cannot fail for the two mistakes most likely
# to be made here. A counter that read the wrong endianness, or that ignored
# alignment, would still be a counter -- it would just be wrong, quietly.
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPC="$HERE/opcount.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

# 24 words. Assembled from fixture.s (below) with
#   mips-linux-gnu-as -march=mips32 -EB
WORDS="89280000 896a0001 89ac0002 99280003 996a0003 a9280000 b9280003 b96a0003
b9ac0003 b9ee0003 c12a0000 e12a0000 bd300000 bd310004 0000000f 5109ffff
00000000 712a4002 c5200000 cd200000 25280001 8d280000 ad280000 00000000"

cat > "$T/fixture.s" <<'ASM'
	.set noreorder
	.text
	.globl _start
_start:
	lwl	$t0, 0($t1)
	lwl	$t2, 1($t3)
	lwl	$t4, 2($t5)
	lwr	$t0, 3($t1)
	lwr	$t2, 3($t3)
	swl	$t0, 0($t1)
	swr	$t0, 3($t1)
	swr	$t2, 3($t3)
	swr	$t4, 3($t5)
	swr	$t6, 3($t7)
	ll	$t2, 0($t1)
	sc	$t2, 0($t1)
	cache	0x10, 0($t1)
	cache	0x11, 4($t1)
	sync
	beql	$t0, $t1, _start
	nop
	mul	$t0, $t1, $t2
	lwc1	$f0, 0($t1)
	pref	0, 0($t1)
	addiu	$t0, $t1, 1
	lw	$t0, 0($t1)
	sw	$t0, 0($t1)
	nop
ASM

echo "$WORDS" | tr -s ' \n' '\n' | grep . | while read -r w; do printf '%b' \
  "\x${w:0:2}\x${w:2:2}\x${w:4:2}\x${w:6:2}"; done > "$T/fx.bin"

count () { "$OPC" "$1" --base 0 | sed -n "s/^  0x$2 .* \([0-9]\+\) .*/\1/p" | head -1; }
field () { "$OPC" "$1" --base 0 | awk -v k="$2" '$0 ~ "^  0x" k " " {print $3; exit}'; }

fail=0; pass=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-28s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-28s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}

echo "=== P1: known fixture, exact counts ==="
ck "lwl  (0x22)"      3 "$(field "$T/fx.bin" 22)"
ck "lwr  (0x26)"      2 "$(field "$T/fx.bin" 26)"
ck "swl  (0x2a)"      1 "$(field "$T/fx.bin" 2a)"
ck "swr  (0x2e)"      4 "$(field "$T/fx.bin" 2e)"
ck "cache (0x2f)"     2 "$(field "$T/fx.bin" 2f)"
ck "ll   (0x30)"      1 "$(field "$T/fx.bin" 30)"
ck "sc   (0x38)"      1 "$(field "$T/fx.bin" 38)"
ck "beql (0x14)"      1 "$(field "$T/fx.bin" 14)"
ck "SPECIAL2 (0x1c)"  1 "$(field "$T/fx.bin" 1c)"
ck "lwc1 (0x31)"      1 "$(field "$T/fx.bin" 31)"
# The fixture is assembled `-march=mips32`, where these 32 bits are `pref`.
# On this core the same word is `lwc3`, which is what opcount names it since
# 2026-08-27 -- the histogram is keyed on the opcode, so only the label
# moved. That the two ISAs disagree about one opcode is the point of the
# row, not a defect in the fixture.
ck "lwc3/pref (0x33)" 1 "$(field "$T/fx.bin" 33)"
ck "unaligned total"  10 "$("$OPC" "$T/fx.bin" --base 0 | sed -n 's/.*swr = \([0-9]*\).*/\1/p')"

echo
echo "=== N1: the same bytes read little-endian must give a different answer ==="
python3 - "$T/fx.bin" "$T/le.bin" <<'PY'
import sys, struct
b = open(sys.argv[1],'rb').read()
out = b''.join(struct.pack('>I', struct.unpack_from('<I', b, i)[0]) for i in range(0,len(b),4))
open(sys.argv[2],'wb').write(out)
PY
n1="$("$OPC" "$T/le.bin" --base 0 | sed -n 's/.*swr = \([0-9]*\).*/\1/p')"
if [ "$n1" != "10" ]; then printf '  ok     %-28s %s (not 10)\n' "byte-swapped total" "$n1"; pass=$((pass+1))
else printf '  FAIL   %-28s got 10 -- endianness is not being read\n' "byte-swapped total"; fail=$((fail+1)); fi

echo
echo "=== N2: scanning from a 2-byte offset must give a different answer ==="
tail -c +3 "$T/fx.bin" > "$T/off.bin"
n2="$("$OPC" "$T/off.bin" --base 0 | sed -n 's/.*swr = \([0-9]*\).*/\1/p')"
if [ "$n2" != "10" ]; then printf '  ok     %-28s %s (not 10)\n' "2-byte shifted total" "$n2"; pass=$((pass+1))
else printf '  FAIL   %-28s got 10 -- alignment is not being respected\n' "2-byte shifted total"; fail=$((fail+1)); fi

echo
echo "=== control on the control: are the hardcoded words still what the assembler emits? ==="
if command -v mips-linux-gnu-as >/dev/null 2>&1; then
    mips-linux-gnu-as -march=mips32 -EB -o "$T/fx.o" "$T/fixture.s"
    mips-linux-gnu-objcopy -O binary --only-section=.text "$T/fx.o" "$T/fx2.bin"
    if cmp -s "$T/fx.bin" "$T/fx2.bin"; then
        printf '  ok     %-28s assembler agrees\n' "hardcoded fixture"; pass=$((pass+1))
    else
        printf '  FAIL   %-28s assembler disagrees with the hardcoded words\n' "hardcoded fixture"; fail=$((fail+1))
    fi
else
    printf '  skip   %-28s no mips-linux-gnu-as on this machine\n' "hardcoded fixture"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
