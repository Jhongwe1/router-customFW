#!/usr/bin/env bash
# Controls for tools/hazlint -- and controls on those controls.
#
# hazlint already runs five or eight controls of its own before it will report
# on anything.  This file exists because that is not enough: a control that
# lives inside the tool it checks passes whenever the tool is broken in a way
# that also breaks the control.  So everything below MUTATES the tool and
# demands that it notices.
#
#   P1  the three acceptance numbers, on the real artefacts
#         stage2.bin        -> 1474 loads / 646 nop / 0 violations, exit 0
#         P9-12 v1 (148 B)  -> 2 violations at 0x1c and 0x2c,       exit 1
#         P9-12 v2 (156 B)  -> 0 violations,                        exit 0
#   P2  the embedded fixtures are byte-identical to the copies in $FWRE_WORK
#         (skipped off the bench machine -- and it says so rather than passing)
#   M1  take the population count away, three ways, and the tool must refuse
#   M2  blind the scanner (no loads recognised) and it must refuse
#   M3  drop the `rt != $zero` rule and the population moves to 1475/647,
#         which K4 must catch
#   M4  make `reads()` return nothing and the negative control must go quiet,
#         which K1 and K2 must catch
#   M5  the exit-code contract, because a gate is only as good as its codes
#   M6  a file with no loads at all is refused, not passed
#   E1  an assembled .o with a planted hazard is found through ELF section
#         headers -- the path rlxprobe's build will actually use
#   E2  `-march=mips1` vs `-march=mips32` on the same C, through --isa
#         (this is DAY-ZERO's 2026-08-24 desk measurement, re-run as a control)
#
# M1 is the DoD clause: "take the positive control's population count away and
# the whole thing refuses to output."  It is tested three ways because there
# are three ways to lose it -- a wrong expectation, a missing file, and an
# operator waiving it.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HAZ="$HERE/hazlint"
PY="${PYTHON:-python3}"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0; skip=0
ck () {  # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-46s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-46s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-46s %s\n' "$1" "$2"; skip=$((skip+1)); }

# Field extractors.  Deliberately crude: they read the printed report, which is
# what a human reads, so a change that breaks the report breaks the test too.
num () { sed -n "s/^  $1 *\([0-9]*\).*/\1/p" | head -1; }

V1="$T/v1.bin"; V2="$T/v2.bin"
"$PY" - "$V1" "$V2" <<'PY'
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
V1 = ("041100010000000027f000603c08b80035092014350820000200882192240000"
      "1080000b26310001240b198c912a0000314a006015400003256bffff1560fffb"
      "00000000a10400001000fff4000000003c0c0800258cffff1580fffe00000000"
      "1000ffed000000000d0a2a2a2a204e31353052542052414d424f4f542050392d"
      "3132203462616565353137202a2a2a0d0a000000")
V2 = ("041100010000000027f000683c08b80035092014350820000200882192240000"
      "000000001080000c26310001240b198c912a000000000000314a006015400003"
      "256bffff1560fffa00000000a10400001000fff2000000003c0c0800258cffff"
      "1580fffe000000001000ffeb000000000d0a2a2a2a204e31353052542052414d"
      "424f4f542050392d3132203462616565353137202a2a2a0d0a000000")
for path, hx in ((sys.argv[1], V1), (sys.argv[2], V2)):
    open(path, 'wb').write(bytes(bytearray(
        int(hx[i:i+2], 16) for i in range(0, len(hx), 2))))
PY

STAGE2=""
for c in "$WORK/stage2.bin" "$WORK/rebuild/work-item4/stage2.bin"; do
    [ -f "$c" ] && STAGE2="$c" && break
done

echo "=== P1: the three acceptance numbers, on the real artefacts ==="
if [ -n "$STAGE2" ]; then
    out="$("$PY" "$HAZ" "$STAGE2" --raw --base 0x80400000 2>&1)"; rc=$?
    ck "stage2 loads"        1474 "$(printf '%s\n' "$out" | num 'loads (MIPS-I load-to-GPR, rt != \$zero)')"
    ck "stage2 nop-after"     646 "$(printf '%s\n' "$out" | num 'followed by an explicit nop')"
    ck "stage2 violations"      0 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
    ck "stage2 exit code"       0 "$rc"
else
    sk "stage2.bin population" "not found under $WORK"
fi

out="$("$PY" "$HAZ" "$V1" --raw --base 0x80500000 2>&1)"; rc=$?
ck "P9-12 v1 loads"            2 "$(printf '%s\n' "$out" | num 'loads (MIPS-I load-to-GPR, rt != \$zero)')"
ck "P9-12 v1 violations"       2 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
ck "P9-12 v1 exit code"        1 "$rc"
ck "P9-12 v1 offset 0x1c named" 1 "$(printf '%s\n' "$out" | grep -c 'file 0x1c ')"
ck "P9-12 v1 offset 0x2c named" 1 "$(printf '%s\n' "$out" | grep -c 'file 0x2c ')"

out="$("$PY" "$HAZ" "$V2" --raw --base 0x80500000 2>&1)"; rc=$?
ck "P9-12 v2 violations"       0 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
ck "P9-12 v2 nop-after"        2 "$(printf '%s\n' "$out" | num 'followed by an explicit nop')"
ck "P9-12 v2 exit code"        0 "$rc"

echo
echo "=== P2: the embedded fixtures against the copies in \$FWRE_WORK ==="
# The bytes are carried inside hazlint because mkramboot.py can no longer
# produce the broken one and *.bin is gitignored.  Where the originals ARE
# present, they are the second source, and this is where that is checked.
for pair in "w08-ramboot-v1-truncating.bin:$V1" "w08-ramboot.bin:$V2"; do
    orig="$WORK/${pair%%:*}"; emb="${pair##*:}"
    if [ -f "$orig" ]; then
        if cmp -s "$orig" "$emb"; then
            ck "embedded == $(basename "$orig")" same same
        else
            ck "embedded == $(basename "$orig")" same differs
        fi
    else
        sk "embedded == $(basename "$orig")" "$orig not present"
    fi
done

echo
echo "=== M1: take the population count away, and the tool must refuse ==="
# (a) a wrong expectation -- the control fires
sed 's/^STAGE2_LOADS = 1474$/STAGE2_LOADS = 1473/' "$HAZ" > "$T/m1a"
if [ -n "$STAGE2" ]; then
    "$PY" "$T/m1a" "$V2" --raw --base 0x80500000 >/dev/null 2>&1
    ck "M1a wrong population -> refuse"  2 "$?"
    # and the mutation must actually have landed
    ck "M1a mutation landed"  1 "$(grep -c 'STAGE2_LOADS = 1473' "$T/m1a")"
else
    sk "M1a wrong population" "needs stage2.bin"
fi
# (b) the fixture is not reachable at all -- the fresh-clone case, simulated by
#     pointing $FWRE_WORK at an empty directory
mkdir -p "$T/empty"
FWRE_WORK="$T/empty" "$PY" "$HAZ" "$V2" --raw --base 0x80500000 >/dev/null 2>&1
ck "M1b unreachable fixture -> refuse"  2 "$?"
# (c) an operator waives it: a CLEAN file must still not certify
FWRE_WORK="$T/empty" "$PY" "$HAZ" "$V2" --raw --base 0x80500000 \
      --no-population-control >/dev/null 2>&1
ck "M1c waived, clean file -> still 2"  2 "$?"
# ... and a waived run must SAY so, not just exit quietly
FWRE_WORK="$T/empty" "$PY" "$HAZ" "$V2" --raw --base 0x80500000 \
      --no-population-control 2>&1 | grep -q 'POPULATION CONTROL NOT RUN'
ck "M1c waived run says so"             0 "$?"
# (d) and a --stage2 that does not exist must NOT quietly fall back to
#     $FWRE_WORK. It did, until this case was written.
"$PY" "$HAZ" "$V2" --raw --base 0x80500000 --stage2 "$T/nope.bin" >/dev/null 2>&1
ck "M1d named-but-absent fixture -> error" 3 "$?"

echo
echo "=== M2: blind the scanner, and it must refuse ==="
# A tool that recognises no loads reports 0 violations on everything.  That is
# the exact failure mode the population control exists for.
sed "s/^LOADS = {0x20: 'lb'.*$/LOADS = {}/" "$HAZ" | \
    sed "s/^         0x24: 'lbu'.*$//;s/^         0x24.*$//" > "$T/m2"
sed -i "s/^         0x24: 'lbu', 0x25: 'lhu', 0x26: 'lwr'}$//" "$T/m2"
ck "M2 mutation landed"  1 "$(grep -c '^LOADS = {}' "$T/m2")"
"$PY" "$T/m2" "$V1" --raw --base 0x80500000 >/dev/null 2>&1
ck "M2 blinded scanner -> refuse"       2 "$?"

echo
echo "=== M3: drop the rt != \$zero rule; the population must move ==="
sed 's/    if op in LOADS and rt_of(w) != 0:/    if op in LOADS:  # MUTATED/' \
    "$HAZ" > "$T/m3"
ck "M3 mutation landed"  1 "$(grep -c '# MUTATED' "$T/m3")"
if [ -n "$STAGE2" ]; then
    "$PY" "$T/m3" "$V2" --raw --base 0x80500000 >/dev/null 2>&1
    ck "M3 rt-rule dropped -> refuse"    2 "$?"
    # 1665, not 1474: `lb zero,…` and `lwr zero,…` decoded out of the loader's
    # string and table region are what the rt rule was excluding, and they are
    # the 191 words the population control is protected by.
    got="$("$PY" "$T/m3" --self-test 2>&1 | sed -n 's/.*K4.*  \([0-9]*\) loads.*/\1/p')"
    ck "M3 moves the population to 1665" 1665 "$got"
else
    sk "M3 rt-rule dropped" "needs stage2.bin"
fi

echo
echo "=== M4: make reads() return nothing; the negative control must catch it ==="
"$PY" - "$HAZ" "$T/m4" <<'PY'
import sys, re
src = open(sys.argv[1]).read()
# Replace the body of reads() with a constant empty set, leaving everything
# else -- including the load counter -- intact.  This is the "it counts but it
# does not judge" mutation, and K2 is what must notice.
src = src.replace('''    op = w >> 26
    rs, rt, rd, f = rs_of(w), rt_of(w), rd_of(w), w & 0x3F

    if op == 0x00:                                  # SPECIAL''',
                  '''    return set()
    op = w >> 26
    rs, rt, rd, f = rs_of(w), rt_of(w), rd_of(w), w & 0x3F

    if op == 0x00:                                  # SPECIAL''', 1)
open(sys.argv[2], 'w').write(src)
PY
ck "M4 mutation landed"  1 "$(grep -c '^    return set()$' "$T/m4")"
"$PY" "$T/m4" "$V1" --raw --base 0x80500000 >/dev/null 2>&1
ck "M4 blinded judge -> refuse"         2 "$?"

echo
echo "=== M5: the exit-code contract ==="
"$PY" "$HAZ" "$T/does-not-exist" --raw >/dev/null 2>&1
ck "missing file -> 3"                  3 "$?"
"$PY" "$HAZ" --raw --frobnicate >/dev/null 2>&1
ck "unknown option -> 3"                3 "$?"
"$PY" "$HAZ" --self-test >/dev/null 2>&1
if [ -n "$STAGE2" ]; then ck "self-test -> 0" 0 "$?"; else ck "self-test (no stage2) -> 2" 2 "$?"; fi

echo
echo "=== M6: a file with no loads is refused, not passed ==="
printf '\x00\x00\x00\x00%.0s' 1 2 3 4 > "$T/zeros.bin"
"$PY" "$HAZ" "$T/zeros.bin" --raw >/dev/null 2>&1
ck "no loads at all -> refuse"          2 "$?"
"$PY" "$HAZ" "$T/zeros.bin" --raw --allow-zero-loads >/dev/null 2>&1
ck "no loads, explicitly allowed -> 0"  0 "$?"

echo
echo "=== E1: an assembled .o, through ELF section headers ==="
if command -v mips-linux-gnu-as >/dev/null 2>&1; then
    cat > "$T/haz.s" <<'ASM'
	.set noreorder
	.text
	.globl _start
_start:
	lw	$t0, 0($t1)
	addu	$t2, $t0, $t3	# VIOLATION: reads t0 in the load delay slot
	lw	$t4, 4($t1)
	nop
	addu	$t5, $t4, $t3	# fine
	jr	$ra
	nop
ASM
    cat > "$T/clean.s" <<'ASM'
	.set noreorder
	.text
	.globl _start
_start:
	lw	$t0, 0($t1)
	nop
	addu	$t2, $t0, $t3
	jr	$ra
	nop
ASM
    mips-linux-gnu-as -march=mips1 -EB -o "$T/haz.o" "$T/haz.s" 2>/dev/null
    mips-linux-gnu-as -march=mips1 -EB -o "$T/clean.o" "$T/clean.s" 2>/dev/null
    out="$("$PY" "$HAZ" "$T/haz.o" 2>&1)"; rc=$?
    ck "planted hazard in a .o -> 1 violation" 1 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
    ck "planted hazard exit code"              1 "$rc"
    ck "found the .text section"               1 "$(printf '%s\n' "$out" | grep -c 'scanned    .text')"
    out="$("$PY" "$HAZ" "$T/clean.o" 2>&1)"; rc=$?
    ck "clean .o -> 0 violations"              0 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
    ck "clean .o exit code"                    0 "$rc"
else
    sk "assembled .o path" "no mips-linux-gnu-as on this machine"
fi

echo
echo "=== E2: -march=mips1 vs -march=mips32 on the same C, through --isa ==="
# DAY-ZERO records this as a desk measurement made 2026-08-24: gcc-12 respects
# the load delay slot under -march=mips1 and emits no movz/movn, while the same
# C under -march=mips32 emits one.  Re-run here so the claim has a control that
# fires rather than a sentence that ages.
CC=""
for c in mips-linux-gnu-gcc-12 mips-linux-gnu-gcc; do
    command -v "$c" >/dev/null 2>&1 && CC="$c" && break
done
if [ -n "$CC" ]; then
    cat > "$T/cmov.c" <<'C'
int pick(int a, int b, int c) { return c ? a : b; }
unsigned sum(const unsigned char *p, int n)
{ unsigned s = 0; while (n-- > 0) s += *p++; return s; }
C
    # -msoft-float is not decoration.  Measured 2026-08-24 on gcc 12.4.0:
    # `-march=mips1` alone is REJECTED -- "'-march=mips1' requires '-mfp32'" --
    # so the build line DAY-ZERO item 6 records does not compile on this host.
    # -msoft-float satisfies it and is the honest flag for a core with no FPU.
    for m in mips1 mips32; do
        "$CC" -march=$m -mabi=32 -msoft-float -EB -O2 -nostdlib -ffreestanding \
              -fno-pic -c -o "$T/cmov-$m.o" "$T/cmov.c" 2>/dev/null
    done
    # The control on this control: a count of 0 taken from a compile that never
    # ran is a tool reporting 0 while not looking, which is the whole subject of
    # this file.  So the object must exist before its count is believed.
    ck "mips1 object was produced"  yes "$([ -s "$T/cmov-mips1.o" ] && echo yes || echo no)"
    ck "mips32 object was produced" yes "$([ -s "$T/cmov-mips32.o" ] && echo yes || echo no)"
    if [ -s "$T/cmov-mips1.o" ] && [ -s "$T/cmov-mips32.o" ]; then
        n1="$("$PY" "$HAZ" --isa "$T/cmov-mips1.o" 2>&1 | grep -cE '^      (movz|movn) ')"
        n32="$("$PY" "$HAZ" --isa "$T/cmov-mips32.o" 2>&1 | grep -cE '^      (movz|movn) ')"
        ck "-march=mips1 emits no movz/movn"   0 "$n1"
        ck "-march=mips32 does (the positive control)" \
           yes "$([ "$n32" -gt 0 ] && echo yes || echo no)"
        # And the load delay slot itself: the mips1 object must pass the gate,
        # which is the claim rlxprobe's whole toolchain choice rests on.
        "$PY" "$HAZ" "$T/cmov-mips1.o" >/dev/null 2>&1
        ck "-march=mips1 object passes the gate"   0 "$?"
    else
        sk "-march comparison" "an object did not build; the counts above are void"
    fi
else
    sk "-march comparison" "no mips-linux-gnu-gcc on this machine"
fi

echo
echo "=== M7-M9: the 2026-08-24 fixes must each have a control that fails ==="
# The adversarial review's finding 6 was that K1-K6 constrained none of the
# decoder defects: the patched tool and the shipped tool were indistinguishable
# to the suite. These three mutations undo one fix each and demand a refusal.
mut () {   # mut <name> <python-mutation> <label>
    "$PY" - "$HAZ" "$T/$1" <<'INNERPY'
import sys
src = open(sys.argv[1]).read()
import os
which = os.path.basename(sys.argv[2])
if which == 'm7':          # the lwl/lwr exemption swallows the base register again
    src = src.replace("and rs_of(w2) != rt:", "and True:", 1)
elif which == 'm8':        # control_flow forgets the REGIMM branch-likely forms
    src = src.replace("                             0x02, 0x03, 0x12, 0x13):",
                      "                             ):", 1)
elif which == 'm9':        # reads() forgets that lwl/lwr merge into rt
    src = src.replace("""        # Found by the adversarial review, 2026-08-24.
        return {rs, rt}""",
                      """        # MUTATED: the merge read of rt is gone
        return {rs}""", 1)
open(sys.argv[2], 'w').write(src)
INNERPY
}
mut m7; mut m8; mut m9
ck "M7 mutation landed"  0 "$(grep -c 'and rs_of(w2) != rt:' "$T/m7")"
ck "M8 mutation landed"  0 "$(grep -c '0x02, 0x03, 0x12, 0x13' "$T/m8")"
ck "M9 mutation landed"  1 "$(grep -c 'MUTATED: the merge read' "$T/m9")"
for m in m7 m8 m9; do
    "$PY" "$T/$m" --self-test >/dev/null 2>&1
    ck "$m self-test must refuse"  2 "$?"
done

echo
echo "=== U1: an unchecked successor fails the gate ==="
# Finding 14: the "unresolved -> exit 1" contract had zero coverage. A file
# whose last word is a load has a successor that is not in the file at all.
printf '\x8d\x28\x00\x00' > "$T/tail-load.bin"
out="$("$PY" "$HAZ" "$T/tail-load.bin" --raw --base 0x80500000 2>&1)"; rc=$?
ck "one load, no successor -> exit 1"     1 "$rc"
ck "and it says why"                      1 "$(printf '%s\n' "$out" | grep -c 'last word of')"
ck "with 0 violations, not a fake one"    0 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"

echo
echo "=== U2: two executable sections in one .o must not be read across ==="
if command -v mips-linux-gnu-as >/dev/null 2>&1; then
    cat > "$T/two.s" <<'ASM'
	.set noreorder
	.set nomacro
	.section .text.a,"ax",@progbits
	.globl _a
_a:
	lw	$t0, 0($t1)		# the LAST word of section a
	.section .text.b,"ax",@progbits
	.globl _b
_b:
	addu	$t2, $t0, $zero		# the FIRST word of section b, reads t0
	jr	$ra
	nop
ASM
    mips-linux-gnu-as -EB -march=mips1 -o "$T/two.o" "$T/two.s" 2>/dev/null
    out="$("$PY" "$HAZ" "$T/two.o" 2>&1)"; rc=$?
    ck "no violation across the section seam" 0 "$(printf '%s\n' "$out" | num 'VIOLATIONS')"
    ck "the seam is reported, not silent"     1 \
       "$(printf '%s\n' "$out" | grep -c 'last word of .text.a')"
    ck "both sections were scanned"           2 \
       "$(printf '%s\n' "$out" | grep -c '^scanned    .text.')"
    ck "and the addresses are flagged synthetic" 2 \
       "$(printf '%s\n' "$out" | grep -c 'ADDRESSES ARE SYNTHETIC')"
    ck "exit 1, because a successor is unknown" 1 "$rc"
else
    sk "two-section .o" "no mips-linux-gnu-as"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
