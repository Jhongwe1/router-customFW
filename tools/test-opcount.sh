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
echo "=== P2: --pairs, the unaligned idiom rather than the opcode ==="
# The fixture is a discriminating one and that is why it is reused here. Its
# `lwl $t0,0($t1)` and `lwr $t0,3($t1)` are three words apart with the same rt,
# the same base and offsets 0 and 3 -- a pair. Its `lwl $t2,1($t3)` and
# `lwr $t2,3($t3)` have offsets 1 and 3 -- NOT a pair, because two apart is not
# three. A matcher that only looked at rt and base would report three.
pf () { "$OPC" "$T/fx.bin" --base 0 --pairs | sed -n "s/^  $1 *\(.*\)$/\1/p" | head -1; }
ck "P2 paired sites"     "2      lwl/lwr 1   swl/swr 1" "$(pf 'paired sites')"
ck "P2 orientation"      "BE 2   LE 0"                  "$(pf orientation)"
ck "P2 unpaired halves"  "6      lwl 2  lwr 1  swl 0  swr 3" "$(pf 'unpaired halves')"

echo
echo "=== N3/N4: the pair matcher must not survive endianness or alignment either ==="
n3="$("$OPC" "$T/le.bin" --base 0 --pairs | sed -n 's/^  paired sites *\([0-9]*\).*/\1/p')"
if [ "$n3" != "2" ]; then printf '  ok     %-28s %s (not 2)\n' "N3 byte-swapped pairs" "$n3"; pass=$((pass+1))
else printf '  FAIL   %-28s got 2\n' "N3 byte-swapped pairs"; fail=$((fail+1)); fi
n4="$("$OPC" "$T/off.bin" --base 0 --pairs | sed -n 's/^  paired sites *\([0-9]*\).*/\1/p')"
if [ "$n4" != "2" ]; then printf '  ok     %-28s %s (not 2)\n' "N4 2-byte shifted pairs" "$n4"; pass=$((pass+1))
else printf '  FAIL   %-28s got 2\n' "N4 2-byte shifted pairs"; fail=$((fail+1)); fi

echo "=== P3-P5: --mips16, the precondition every count above it stands on ==="
# Added 2026-08-27, because until then opcount's docstring promised that a
# linear scan cannot miss an instruction, and this unit's own kernel is a
# counter-example. See notes/vendor-kernel-isa.md §4.2.
#
# P3 is the control ON the control: 24 words carry no jal, so the instrument
# cannot be shown to fire, and it must say NOT ESTABLISHED rather than "clean".
ck "P3 too small to control on" "NOT ESTABLISHED" \
   "$("$OPC" "$T/fx.bin" --base 0 --mips16 | sed -n 's/.*VERDICT *\(NOT ESTABLISHED\).*/\1/p')"

python3 - "$T/m16.bin" "$T/nom16.bin" <<'PY'
import struct, sys
# 300 words of plausible 32-bit code at 0x80000000: `addiu $t0,$t1,1` fills it,
# 40 `jal`s land inside the image so the control fires, and ONE `jalx` lands
# inside too. The second file is identical except that the jalx is a jal, so
# the pair is a single-variable experiment on the detector.
N = 300
base, words = 0x80000000, [0x25280001] * N
for k in range(20, 260, 6):
    words[k] = 0x0C000000 | ((k + 3) & 0x03FFFFFF)      # jal -> 4*(k+3), in range
m16 = list(words)
m16[150] = 0x74000000 | 0x80                            # jalx -> 0x80000200
open(sys.argv[1], 'wb').write(struct.pack('>%dI' % N, *m16))
open(sys.argv[2], 'wb').write(struct.pack('>%dI' % N, *words))
PY
v4="$("$OPC" "$T/m16.bin"   --base 0x80000000 --mips16 | sed -n 's/.*VERDICT *\([A-Z0-9 ]*\).*/\1/p' | head -1)"
v5="$("$OPC" "$T/nom16.bin" --base 0x80000000 --mips16 | sed -n 's/.*VERDICT *\(no MIPS16\).*/\1/p')"
ck "P4 one jalx in range"  "MIPS16 REACHED " "$v4"
ck "P5 the same file, jal" "no MIPS16"       "$v5"
ck "P4 cluster count"      1 "$("$OPC" "$T/m16.bin" --base 0x80000000 --mips16 | sed -n 's/.*in \([0-9]*\) cluster.*/\1/p')"

# P6-P8, added 2026-08-28 out of the adversarial review. Each one is a mutation
# the suite could not previously see.
#
# P6/P7: until this commit the "control did not fire" guard sat inside the
# `if not inr:` branch, so it gated the ZERO and not the POSITIVE -- a wrong
# base produced the tool's strongest claim on an artefact whose control landed
# nothing. Both directions are asserted now, on the SAME two fixtures at a base
# that is wrong for them, so the pair is a single-variable experiment on the
# guard.
#
# P8: P4/P5's fixture is 100 % plausible code, so the codeness filter is never
# load-bearing in them -- deleting it left the suite green while `stage2.bin`,
# the artefact this project certifies clean, flipped to MIPS16 REACHED. P8 is a
# data island with an in-range jalx-shaped word in it, which is what that filter
# exists for.
ck "P6 REACHED fixture, wrong base" "NOT ESTABLISHED" \
   "$("$OPC" "$T/m16.bin" --base 0x81000000 --mips16 | sed -n 's/.*VERDICT *\(NOT ESTABLISHED\).*/\1/p')"
ck "P7 clean fixture, wrong base"   "NOT ESTABLISHED" \
   "$("$OPC" "$T/nom16.bin" --base 0x81000000 --mips16 | sed -n 's/.*VERDICT *\(NOT ESTABLISHED\).*/\1/p')"

python3 - "$T/island.bin" <<'PY'
import struct, sys
# 300 words of plausible code with a firing jal control, plus a 128-word data
# island whose middle word is a jalx pointing back into the image. The island's
# words are small integers and 0x80-prefixed pointers -- the two shapes that
# actually occur in these artefacts and that _plausible() is built to reject.
N = 300
words = [0x25280001] * N
for k in range(20, 260, 6):
    words[k] = 0x0C000000 | ((k + 3) & 0x03FFFFFF)
island = [0x000009c5, 0x000007c7, 0x00000632, 0x800014cc, 0x8000fea8] * 25
island = island[:128]
island[64] = 0x74000000 | 0x80        # jalx -> 0x80000200, inside the image
open(sys.argv[1], 'wb').write(struct.pack('>%dI' % (N + len(island)), *(words + island)))
PY
ck "P8 jalx inside a data island"   "no MIPS16" \
   "$("$OPC" "$T/island.bin" --base 0x80000000 --mips16 | sed -n 's/.*VERDICT *\(no MIPS16\).*/\1/p')"

# P9 is the one that pins the ASYMMETRY rather than the threshold, and P6/P7 do
# not: at a wrong base the jalx targets fall out of range too, so `inr` is empty
# and a guard that only covers the zero branch still fires. This fixture keeps a
# jalx target INSIDE the range while every jal target lands outside it -- the
# exact shape where a half-guarded tool announces MIPS16 REACHED on an artefact
# it cannot be shown to be reading correctly. Built after the first three
# mutants were run and the third survived.
python3 - "$T/nofire.bin" <<'PY'
import struct, sys
N = 300
words = [0x25280001] * N
for k in range(20, 260, 6):
    words[k] = 0x0C000000 | 0x03C00000     # jal -> 0x8F000000, far outside
words[150] = 0x74000000 | 0x80             # jalx -> 0x80000200, inside
open(sys.argv[1], 'wb').write(struct.pack('>%dI' % N, *words))
PY
ck "P9 jalx in range, control not firing" "NOT ESTABLISHED" \
   "$("$OPC" "$T/nofire.bin" --base 0x80000000 --mips16 | sed -n 's/.*VERDICT *\(NOT ESTABLISHED\).*/\1/p')"
ck "P9 and it says how many jalx it is withholding" 1 \
   "$("$OPC" "$T/nofire.bin" --base 0x80000000 --mips16 | grep -c 'jalx target(s) found here')"

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
