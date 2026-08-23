#!/usr/bin/env bash
# Controls for tools/rlxprobe.
#
# The build already asserts two things about itself (raw image == linked image,
# byte 0 == _start's first instruction) and refuses to produce a payload unless
# hazlint exits 0. This file exists for the part a build cannot check about
# itself: **that the gate is closed**.
#
# A gate that has never refused anything is a gate nobody has shown to be shut.
# So G2 plants P9-12's own bug -- the instruction sequence that failed on this
# physical device -- and fails if the build accepts it.
#
#   P1  the payload builds, gated, and the build's own assertions hold
#   G1  hazlint passes the linked payload, and it scanned a non-zero population
#   G2  the gate REFUSES a planted load-use hazard, exit 1
#   G3  removing hazlint from the build breaks the build rather than skipping it
#   I1  the emitted code contains no instruction outside MIPS-I, either classifier
#   I2  no shape from the unestablished-hazard survey appears in it
#   A1  the hand-written putchar still has its nop in the load delay slot
#   A2  the entry is the first byte, at whatever LOADADDR is given
#
# A1 is not decoration. The nop at 0x80406B88 is the instruction P9-12 copied
# out of the loader's putchar and discarded as padding, and two power cycles
# went to finding that out. If a future edit removes it, hazlint catches it --
# but only if hazlint is still wired in, which is G3.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RP="$HERE/rlxprobe"
PY="${PYTHON:-python3}"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0; skip=0
ck () {
    if [ "$2" = "$3" ]; then printf '  ok     %-46s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-46s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-46s %s\n' "$1" "$2"; skip=$((skip+1)); }

if ! command -v mips-linux-gnu-gcc >/dev/null 2>&1; then
    sk "everything" "no mips-linux-gnu-gcc on this machine"
    printf 'RESULT: 0 passed, 0 failed, 1 skipped\n'; exit 0
fi

B="$T/build"
MAKE="make -C $RP BUILD=$B"

echo "=== P1: the payload builds, gated, and the build's own assertions hold ==="
out="$($MAKE 2>&1)"; rc=$?
ck "make exit code"                    0 "$rc"
ck "raw image == linked image"         1 "$(printf '%s\n' "$out" | grep -c 'ok *raw image == linked image')"
ck "byte 0 is _start"                  1 "$(printf '%s\n' "$out" | grep -c "ok *byte 0 of the image is _start's first instruction")"
ck "payload exists"                  yes "$([ -s "$B/probe0.bin" ] && echo yes || echo no)"

echo
echo "=== G1: the gate ran on the linked payload, and it had something to scan ==="
g="$("$HERE/hazlint" "$B/probe0.elf" 2>&1)"; rc=$?
ck "hazlint exit code"                 0 "$rc"
ck "violations"                        0 "$(printf '%s\n' "$g" | sed -n 's/^  VIOLATIONS *\([0-9]*\).*/\1/p')"
ck "unresolved successors"             0 "$(printf '%s\n' "$g" | sed -n 's/^  successor unresolved *\([0-9]*\).*/\1/p')"
loads="$(printf '%s\n' "$g" | sed -n 's/^  loads (MIPS-I load-to-GPR, rt != \$zero) *\([0-9]*\).*/\1/p')"
ck "scanned a non-zero population"   yes "$([ "${loads:-0}" -gt 0 ] && echo yes || echo no)"
ck "scanned the executable segment"    1 "$(printf '%s\n' "$g" | grep -c 'scanned    PT_LOAD')"

echo
echo "=== G2: the gate must REFUSE a planted load-use hazard ==="
out="$($MAKE gate-check 2>&1)"; rc=$?
ck "gate-check exit code"              0 "$rc"
ck "the gate refused it"               1 "$(printf '%s\n' "$out" | grep -c 'ok .*the gate refused it, exit 1')"

echo
echo "=== G3: removing the gate must BREAK the build, not skip it ==="
# A gate you can get past by deleting one file is a lint. Point HAZLINT at
# something that is not there and the build must fail, not carry on.
rm -rf "$T/b2"
out="$(make -C "$RP" BUILD="$T/b2" HAZLINT=/nonexistent/hazlint 2>&1)"; rc=$?
ck "build fails without the gate"    yes "$([ "$rc" -ne 0 ] && echo yes || echo no)"
ck "and no payload was produced"     yes "$([ ! -e "$T/b2/probe0.bin" ] && echo yes || echo no)"

echo
echo "=== I1: no instruction outside MIPS-I, under either classifier ==="
for mode in "" "--loose"; do
    n="$("$HERE/hazlint" --isa $mode "$B/probe0.elf" 2>&1 \
         | sed -n 's/^  everything scanned *[0-9]* words *\([0-9]*\) hits.*/\1/p')"
    ck "isa hits ${mode:---strict}"     0 "${n:-MISSING}"
done

echo
echo "=== I2: no shape from the unestablished-hazard survey ==="
s="$("$HERE/hazlint" --survey "$B/probe0.elf" 2>&1)"
for shape in 'mult/div then mfhi/mflo' 'mtc0 then mfc0' 'a load sitting in a delay slot'; do
    n="$(printf '%s\n' "$s" | sed -n "s|^    ${shape} *\([0-9]*\).*|\1|p")"
    ck "survey: ${shape}"              0 "${n:-MISSING}"
done

echo
echo "=== A1: the nop in putchar's load delay slot is still there ==="
# lbu into t4 from the LSR, then the nop, then the andi. If the nop goes, this
# payload becomes P9-12 v1 and the console truncates at 16 bytes per iteration.
d="$(mips-linux-gnu-objdump -d -m mips:3000 "$B/probe0.elf" \
     | sed -n '/<rlx_putc>:/,/^$/p')"
ck "lbu then nop then andi"            1 \
   "$(printf '%s\n' "$d" | grep -A2 'lbu.*t4,0(t2)' | grep -c 'nop')"
ck "and the andi is after the nop"     1 \
   "$(printf '%s\n' "$d" | grep -A2 'lbu.*t4,0(t2)' | grep -c 'andi.*t4,t4,0x60')"

echo
echo "=== A2: the entry is byte 0, at whatever LOADADDR is given ==="
# 0x81000000 is the address the README recommends when B3's staged copy at
# 0x80500000 must be left alone, so it is the one worth proving relocatable.
rm -rf "$T/b3"
make -C "$RP" BUILD="$T/b3" LOADADDR=0x81000000 >/dev/null 2>&1
ck "builds at 0x81000000"            yes "$([ -s "$T/b3/probe0.bin" ] && echo yes || echo no)"
if [ -s "$T/b3/probe0.bin" ]; then
    w="$(mips-linux-gnu-objdump -d "$T/b3/probe0.elf" \
         | awk '/^[0-9a-f]+ <_start>:/{getline; print $2; exit}')"
    b="$(od -An -tx1 -N4 "$T/b3/probe0.bin" | tr -d ' \n')"
    ck "byte 0 is _start there too"  "$w" "$b"
    ck "and it moved with LOADADDR"  3c1d8100 "$b"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
