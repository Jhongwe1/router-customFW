#!/usr/bin/env bash
# Controls for tools/rlxprobe.
#
# The build already asserts three things about itself (raw image == every section
# that has contents, byte 0 == _start's first instruction, .bss size) and refuses
# to produce a payload unless hazlint exits 0. This file exists for the part a
# build cannot check about itself: **that the gate is closed**, and **that the
# assumptions the C code makes about the emitted layout are true of the emitted
# layout**.
#
# A gate that has never refused anything is a gate nobody has shown to be shut.
# So G2 plants P9-12's own bug -- the instruction sequence that failed on this
# physical device -- and fails if the build accepts it.
#
#   P1  probe0 builds, gated, and the build's own assertions hold
#   G1  hazlint passes the linked payload, and it scanned a non-zero population
#   G2  the gate REFUSES a planted load-use hazard, exit 1
#   G3  removing hazlint from the build breaks the build rather than skipping it
#   I1  the emitted code contains no instruction outside MIPS-I, either classifier
#   I2  no shape from the unestablished-hazard survey appears in it
#   A1  the hand-written putchar still has its nop in the load delay slot
#   A2  the entry is the first byte, at whatever LOADADDR is given
#
#   P2  probe1 builds and passes the same gate
#   V1  the sixteen victims are where probe1.c computes them: 0x400 apart, and
#       every one of them starts with the exact word the experiment patches
#   V2  rlx_fault_frame is inside .bss with room for the offset the loader's
#       do_reserved reads, so SAFE_A0 points somewhere real
#   S1  SAFE_A0 is emitted before every CP0 instruction that could fault
#   S2  the mutation: a cache.S with SAFE_A0 removed must make S1 fail
#   R1  the result block is addressed through KSEG1 as well as KSEG0
#   R2  and RESULT_BASE reaches the emitted address, so R1 is not a constant
#   Q1  GEOM is off by default and its 1 MiB-writing routine is not even linked
#   Q2  GEOM=1 links it, so Q1 measures the switch and not its absence
#
#   P3  probe2 builds and passes the same gate
#   H1  the exception handler fits in the 128 bytes the vector gives it
#   H2  a device build returns from an exception with rfe -- MIPS-I -- and has
#       no eret anywhere in it
#   H3  RET_ERET=1 swaps them, so H2 measures the knob and not a coincidence
#   D1  a default build does not print NOT A DEVICE BUILD
#   D2  ...and a build with any qemu-only constant set does
#   X1  stub n is at rlx_cp0_stubs + 12n and encodes the rd/sel probe2.c means
#   Q1  probe1 and probe2 run to their end markers under qemu-system-mips
#   Q2  and qemu says cell 1 is FRESH, which is the OPPOSITE of the device's
#       expected answer -- an emulator kinder than the device certifies exactly
#       the bugs the device rejects
#
# A1 is not decoration. The nop at 0x80406B88 is the instruction P9-12 copied
# out of the loader's putchar and discarded as padding, and two power cycles
# went to finding that out. If a future edit removes it, hazlint catches it --
# but only if hazlint is still wired in, which is G3.
#
# V1 and S1 are the two that would otherwise be checked by nothing. probe1.c
# reaches a victim as `rlx_victims + slot * 0x400` and never sees the linker's
# opinion; SAFE_A0 exists because the loader's do_reserved dereferences the
# faulting code's own $a0, and a payload that lost it would look identical.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RP="$HERE/rlxprobe"
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
# Every `make` here names the `payload` goal explicitly. The default goal is
# `all`, which recurses over BOTH payloads -- so a count-based assertion on its
# output reads 2 and looks like a duplicated section rather than a second build.
OBJDUMP=mips-linux-gnu-objdump
NM=mips-linux-gnu-nm

echo "=== P1: probe0 builds, gated, and the build's own assertions hold ==="
out="$(make -C "$RP" BUILD="$B" P=probe0 payload 2>&1)"; rc=$?
ck "make exit code"                    0 "$rc"
ck "raw image == sections with content" 1 "$(printf '%s\n' "$out" | grep -c 'ok *raw image == every section that has contents')"
ck "byte 0 is _start"                  1 "$(printf '%s\n' "$out" | grep -c "ok *byte 0 of the image is _start's first instruction")"
ck "payload exists"                  yes "$([ -s "$B/probe0/probe0.bin" ] && echo yes || echo no)"

echo
echo "=== G1: the gate ran on the linked payload, and it had something to scan ==="
g="$("$HERE/hazlint" "$B/probe0/probe0.elf" 2>&1)"; rc=$?
ck "hazlint exit code"                 0 "$rc"
ck "violations"                        0 "$(printf '%s\n' "$g" | sed -n 's/^  VIOLATIONS *\([0-9]*\).*/\1/p')"
ck "unresolved successors"             0 "$(printf '%s\n' "$g" | sed -n 's/^  successor unresolved *\([0-9]*\).*/\1/p')"
loads="$(printf '%s\n' "$g" | sed -n 's/^  loads (MIPS-I load-to-GPR, rt != \$zero) *\([0-9]*\).*/\1/p')"
ck "scanned a non-zero population"   yes "$([ "${loads:-0}" -gt 0 ] && echo yes || echo no)"
ck "scanned the executable segment"    1 "$(printf '%s\n' "$g" | grep -c 'scanned    PT_LOAD')"

echo
echo "=== G2: the gate must REFUSE a planted load-use hazard ==="
out="$(make -C "$RP" BUILD="$B" P=probe0 gate-check 2>&1)"; rc=$?
ck "gate-check exit code"              0 "$rc"
ck "the gate refused it"               1 "$(printf '%s\n' "$out" | grep -c 'ok .*the gate refused it, exit 1')"

echo
echo "=== G3: removing the gate must BREAK the build, not skip it ==="
# A gate you can get past by deleting one file is a lint. Point HAZLINT at
# something that is not there and the build must fail, not carry on.
rm -rf "$T/b2"
out="$(make -C "$RP" BUILD="$T/b2" P=probe0 payload HAZLINT=/nonexistent/hazlint 2>&1)"; rc=$?
ck "build fails without the gate"    yes "$([ "$rc" -ne 0 ] && echo yes || echo no)"
ck "and no payload was produced"     yes "$([ ! -e "$T/b2/probe0/probe0.bin" ] && echo yes || echo no)"

echo
echo "=== I1: no instruction outside MIPS-I, under either classifier ==="
for mode in "" "--loose"; do
    n="$("$HERE/hazlint" --isa $mode "$B/probe0/probe0.elf" 2>&1 \
         | sed -n 's/^  everything scanned *[0-9]* words *\([0-9]*\) hits.*/\1/p')"
    ck "isa hits ${mode:---strict}"     0 "${n:-MISSING}"
done

echo
echo "=== I2: no shape from the unestablished-hazard survey ==="
s="$("$HERE/hazlint" --survey "$B/probe0/probe0.elf" 2>&1)"
for shape in 'mult/div then mfhi/mflo' 'mtc0 then mfc0' 'a load sitting in a delay slot'; do
    n="$(printf '%s\n' "$s" | sed -n "s|^    ${shape} *\([0-9]*\).*|\1|p")"
    ck "survey: ${shape}"              0 "${n:-MISSING}"
done

echo
echo "=== A1: the nop in putchar's load delay slot is still there ==="
# lbu into t4 from the LSR, then the nop, then the andi. If the nop goes, this
# payload becomes P9-12 v1 and the console truncates at 16 bytes per iteration.
d="$($OBJDUMP -d -m mips:3000 "$B/probe0/probe0.elf" | sed -n '/<rlx_putc>:/,/^$/p')"
ck "lbu then nop then andi"            1 \
   "$(printf '%s\n' "$d" | grep -A2 'lbu.*t4,0(t2)' | grep -c 'nop')"
ck "and the andi is after the nop"     1 \
   "$(printf '%s\n' "$d" | grep -A2 'lbu.*t4,0(t2)' | grep -c 'andi.*t4,t4,0x60')"

echo
echo "=== A2: the entry is byte 0, at whatever LOADADDR is given ==="
# 0x81000000 is the address the README recommends when B3's staged copy at
# 0x80500000 must be left alone, so it is the one worth proving relocatable.
rm -rf "$T/b3"
make -C "$RP" BUILD="$T/b3" P=probe0 payload LOADADDR=0x81000000 >/dev/null 2>&1
ck "builds at 0x81000000"            yes "$([ -s "$T/b3/probe0/probe0.bin" ] && echo yes || echo no)"
if [ -s "$T/b3/probe0/probe0.bin" ]; then
    w="$($OBJDUMP -d "$T/b3/probe0/probe0.elf" \
         | awk '/^[0-9a-f]+ <_start>:/{getline; print $2; exit}')"
    b="$(od -An -tx1 -N4 "$T/b3/probe0/probe0.bin" | tr -d ' \n')"
    ck "byte 0 is _start there too"  "$w" "$b"
    # And _start really is AT the load address -- the byte-0 check alone would
    # pass on an image linked anywhere, since it compares the image against its
    # own ELF.
    ck "and _start is at LOADADDR" 81000000 \
       "$($NM "$T/b3/probe0/probe0.elf" | awk '$3=="_start"{print $1}')"
else
    # Without this branch the two cases above vanish with neither a FAIL nor a
    # skip line, and the suite prints 43 where the bench prints 45. Found
    # 2026-08-25 by tools/ci-census.py, whose arithmetic exists for exactly this
    # and which caught it the first time it was pointed at a real capture.
    ck "byte 0 is _start there too"  built "no relocated build"
    ck "and _start is at LOADADDR" 81000000 "no relocated build"
fi

echo
echo "=== P2: probe1 builds and passes the same gate ==="
out="$(make -C "$RP" BUILD="$B" P=probe1 payload 2>&1)"; rc=$?
ck "make exit code"                    0 "$rc"
ck "payload exists"                  yes "$([ -s "$B/probe1/probe1.bin" ] && echo yes || echo no)"
g1="$("$HERE/hazlint" "$B/probe1/probe1.elf" 2>&1)"; rc=$?
ck "hazlint exit code"                 0 "$rc"
ck "violations"                        0 "$(printf '%s\n' "$g1" | sed -n 's/^  VIOLATIONS *\([0-9]*\).*/\1/p')"
for mode in "" "--loose"; do
    n="$("$HERE/hazlint" --isa $mode "$B/probe1/probe1.elf" 2>&1 \
         | sed -n 's/^  everything scanned *[0-9]* words *\([0-9]*\) hits.*/\1/p')"
    ck "probe1 isa hits ${mode:---strict}" 0 "${n:-MISSING}"
done

echo
echo "=== V1: the victims are where probe1.c computes them ==="
# probe1.c reaches victim k as `rlx_victims + k * 0x400` and never consults the
# linker. If cache.S's `.align 10` stopped taking, or the section moved into
# .text's catch-all, every cell would run against whatever sits at those
# addresses -- and the payload's own run-time check would refuse the slot, which
# is the right behaviour and the wrong time to find out. This is the desk-side
# half of that check.
VS="$($NM "$B/probe1/probe1.elf" | awk '$3=="rlx_victims"{print $1}')"
VE="$($NM "$B/probe1/probe1.elf" | awk '$3=="rlx_victims_end"{print $1}')"
ck "rlx_victims is 1 KiB aligned"      0 "$(( 0x${VS:-1} % 0x400 ))"
ck "sixteen slots of 0x400"       0x4000 "$(printf '0x%x' $(( 0x${VE:-0} - 0x${VS:-0} )))"
bad=0
for k in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    a=$(( 0x${VS} + k * 0x400 ))
    w="$($OBJDUMP -d --start-address=$a --stop-address=$(( a + 4 )) \
         "$B/probe1/probe1.elf" | awk '/^ *[0-9a-f]+:/{print $2; exit}')"
    [ "$w" = "240211a1" ] || bad=$((bad+1))
done
ck "all 16 start with addiu v0,zero,0x11a1" 0 "$bad"
# The pair a cell uses is slot k and slot k+7, and the reason is that 7 KiB
# apart cannot share a cache index for any power-of-two cache size above 1 KiB.
ck "the pair gap is still 7"           7 "$(sed -n 's/^#define RLX_VICTIM_PAIR_GAP\t*\([0-9]*\).*/\1/p' "$RP/rlxdefs.h")"

echo
echo "=== V2: SAFE_A0's target is inside .bss and big enough ==="
# The loader's do_reserved reads offset 148 of the faulting $a0. If
# rlx_fault_frame were smaller than that, or outside the image, SAFE_A0 would be
# pointing at something no better than the integer it replaced.
FF="$($NM "$B/probe1/probe1.elf" | awk '$3=="rlx_fault_frame"{print $1}')"
BS="$($NM "$B/probe1/probe1.elf" | awk '$3=="_bss_start"{print $1}')"
BE="$($NM "$B/probe1/probe1.elf" | awk '$3=="_bss_end"{print $1}')"
ck "rlx_fault_frame is in .bss"      yes \
   "$([ $(( 0x${FF:-0} )) -ge $(( 0x${BS:-1} )) ] && [ $(( 0x${FF:-0} + 256 )) -le $(( 0x${BE:-0} )) ] && echo yes || echo no)"
ck "it is word aligned"                0 "$(( 0x${FF:-1} % 4 ))"

echo
echo "=== S1: SAFE_A0 is emitted before every CP0 instruction that can fault ==="
# A `lui a0` / `addiu a0` pair immediately before the CP0 write or read. Checked
# in the emitted code, not in the source, because a macro that stopped expanding
# would leave the source looking correct.
for fn in rlx_cctl rlx_mfc0_cctl rlx_mtc0_status; do
    body="$($OBJDUMP -d -m mips:3000 "$B/probe1/probe1.elf" | sed -n "/<$fn>:/,/^\$/p")"
    ck "$fn loads a0 before the CP0 op" 1 \
       "$(printf '%s\n' "$body" | grep -c 'lui.*a0,0x')"
done

echo
echo "=== S2: the mutation -- remove SAFE_A0 and S1 must fail ==="
# Without this, S1 could be passing on a `lui a0` that some unrelated edit put
# there. The mutant keeps the macro defined but makes it expand to nothing.
mkdir -p "$T/mut"
cp "$RP"/*.c "$RP"/*.h "$RP"/*.S "$RP"/Makefile "$RP"/rlxprobe.lds "$T/mut/"
"${PYTHON:-python3}" - "$T/mut/cache.S" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
lo = s.index("\t.macro\tSAFE_A0")
hi = s.index("\t.endm", lo) + len("\t.endm")
open(p, "w", encoding="utf-8", newline="\n").write(
    s[:lo] + "\t.macro\tSAFE_A0\n\t.endm" + s[hi:])
PY
rm -rf "$T/b4"
make -C "$T/mut" BUILD="$T/b4" P=probe1 payload HAZLINT="$HERE/hazlint" >/dev/null 2>&1
mutbad=0
for fn in rlx_cctl rlx_mfc0_cctl rlx_mtc0_status; do
    body="$($OBJDUMP -d -m mips:3000 "$T/b4/probe1/probe1.elf" 2>/dev/null | sed -n "/<$fn>:/,/^\$/p")"
    n="$(printf '%s\n' "$body" | grep -c 'lui.*a0,0x')"
    [ "$n" = "0" ] || mutbad=$((mutbad+1))
done
ck "the mutant has no a0 load in any of the three" 0 "$mutbad"

echo
echo "=== R1 / R2: the result block is addressed through KSEG1, and the knob reaches it ==="
# A block left in a write-back D-cache when the watchdog fires is a block the
# loader's DW will not see. RESULT_BASE 0x80A00000 must therefore appear in the
# emitted code as 0xA0A00000 as well -- the KSEG0 form is expected too, because
# that is the address the report prints and the operator types.
d1="$($OBJDUMP -d "$B/probe1/probe1.elf")"
ck "KSEG1 alias 0xa0a0 is materialised" yes \
   "$(printf '%s\n' "$d1" | grep -q 'lui.*0xa0a0' && echo yes || echo no)"
ck "KSEG0 form 0x80a0 is there too"     yes \
   "$(printf '%s\n' "$d1" | grep -q 'lui.*0x80a0' && echo yes || echo no)"
# R2, the pair: move the knob and the emitted alias must move with it. Without
# this, R1 could be passing on a constant nobody plumbed through.
rm -rf "$T/b6"
make -C "$RP" BUILD="$T/b6" P=probe1 payload RESULT_BASE=0x80B00000 >/dev/null 2>&1
d2="$($OBJDUMP -d "$T/b6/probe1/probe1.elf" 2>/dev/null)"
ck "RESULT_BASE=0x80B00000 -> 0xa0b0"   yes \
   "$(printf '%s\n' "$d2" | grep -q 'lui.*0xa0b0' && echo yes || echo no)"
ck "and 0xa0a0 is gone from that build"  no \
   "$(printf '%s\n' "$d2" | grep -q 'lui.*0xa0a0' && echo yes || echo no)"

# R3 / R4: the same knob change, into the SAME build directory. Every case above
# uses a fresh BUILD=, which is exactly why the suite never saw this: until
# 2026-08-25 no object depended on anything carrying a -D, so a second `make`
# with a different RESULT_BASE printed `Nothing to be done for 'payload'` and
# left the first binary in place, while `show` printed the RESULT_BASE that had
# been asked for beside it. The stale artefact was live in this tree.
sha_a="$(sha256sum "$T/b6/probe1/probe1.bin" | cut -d' ' -f1)"
make -C "$RP" BUILD="$T/b6" P=probe1 payload RESULT_BASE=0x80C00000 >/dev/null 2>&1
sha_b="$(sha256sum "$T/b6/probe1/probe1.bin" | cut -d' ' -f1)"
ck "a knob change rebuilds in the same dir" no \
   "$([ "$sha_a" = "$sha_b" ] && echo yes || echo no)"
ck "and the emitted alias moved to 0xa0c0"  yes \
   "$($OBJDUMP -d "$T/b6/probe1/probe1.elf" | grep -q 'lui.*0xa0c0' && echo yes || echo no)"

# R5 / R6: the word count `make show` prints must read the WHOLE result block.
# It is a Makefile constant mirroring RB_WORDS in the payload source, so it is
# recomputed here from the C rather than trusted. `88` was printed for both
# payloads until 2026-08-25 and is right for neither: for probe1 it stops three
# rows and the seal short, and probe2's block is 537 words.
rbw () { sed -n "s/^#define[[:space:]]\+$2[[:space:]]\+\([0-9]\+\)u\?.*/\1/p" "$RP/$1" | head -1; }
p1w=$(( $(rbw probe1.c RB_HDR) + $(rbw probe1.c RB_ROWS) * $(rbw probe1.c RB_ROWW) + 1 ))
p2w=$(( $(rbw probe2.c RB_HDR) + $(rbw probe2.c RB_CELLS) * $(rbw probe2.c RB_CELLW) + 1 ))
ck "show DW count == probe1 RB_WORDS"      "$p1w" \
   "$(make -C "$RP" --no-print-directory BUILD="$B" P=probe1 show 2>/dev/null | sed -n 's/^result .*DW [0-9A-Fa-f]* \([0-9]*\)$/\1/p' | head -1)"
ck "show DW count == probe2 RB_WORDS"      "$p2w" \
   "$(make -C "$RP" --no-print-directory BUILD="$B" P=probe2 show 2>/dev/null | sed -n 's/^result .*DW [0-9A-Fa-f]* \([0-9]*\)$/\1/p' | head -1)"

echo
echo "=== Q1 / Q2: the 1 MiB-writing cache-sizing walk is off by default ==="
ck "GEOM=0: rlx_r3k_size is not linked" 0 \
   "$($NM "$B/probe1/probe1.elf" | grep -c 'rlx_r3k_size')"
rm -rf "$T/b5"
make -C "$RP" BUILD="$T/b5" P=probe1 payload GEOM=1 >/dev/null 2>&1
ck "GEOM=1: it is"                     1 \
   "$($NM "$T/b5/probe1/probe1.elf" 2>/dev/null | grep -c 'rlx_r3k_size')"

echo
echo "=== P3: probe2 builds and passes the same gate ==="
out="$(make -C "$RP" BUILD="$B" P=probe2 payload 2>&1)"; rc=$?
ck "make exit code"                    0 "$rc"
ck "payload exists"                  yes "$([ -s "$B/probe2/probe2.bin" ] && echo yes || echo no)"
g2="$("$HERE/hazlint" "$B/probe2/probe2.elf" 2>&1)"; rc=$?
ck "hazlint exit code"                 0 "$rc"
ck "violations"                        0 "$(printf '%s\n' "$g2" | sed -n 's/^  VIOLATIONS *\([0-9]*\).*/\1/p')"
n="$("$HERE/hazlint" --isa "$B/probe2/probe2.elf" 2>&1 \
     | sed -n 's/^  everything scanned *[0-9]* words *\([0-9]*\) hits.*/\1/p')"
ck "probe2 isa hits --strict"          0 "${n:-MISSING}"

echo
echo "=== H1: the handler fits in the 128 bytes the vector gives it ==="
# It is COPIED to 0x80000080, and the general exception vector is 128 bytes
# before the next thing. A handler that overran would be writing over whatever
# the loader put after it, and the payload would find out by hanging.
HS="$($NM "$B/probe2/probe2.elf" | awk '$3=="rlx_exc_entry"{print $1}')"
HE="$($NM "$B/probe2/probe2.elf" | awk '$3=="rlx_exc_end"{print $1}')"
HB=$(( 0x${HE:-0} - 0x${HS:-0} ))
ck "handler bytes <= 128"            yes "$([ "$HB" -gt 0 ] && [ "$HB" -le 128 ] && echo yes || echo no)"

echo
echo "=== H2 / H3: a device build returns with rfe, and a qemu build with eret ==="
# rfe is MIPS-I; MIPS32 removed it and put eret in its place. This core is
# R3000-class -- the loader itself leaves exceptions with 0x42000010 at two
# sites and the 0x42000018 encoding appears zero times in the whole of stage 2.
# A device image containing eret would fault inside its own handler.
d2="$($OBJDUMP -d "$B/probe2/probe2.elf")"
ck "device build has rfe (0x42000010)"  yes \
   "$(printf '%s\n' "$d2" | grep -q '42000010' && echo yes || echo no)"
ck "device build has NO eret"            no \
   "$(printf '%s\n' "$d2" | grep -q '42000018' && echo yes || echo no)"
rm -rf "$T/b7"
make -C "$RP" BUILD="$T/b7" P=probe2 payload RET_ERET=1 >/dev/null 2>&1
d3="$($OBJDUMP -d "$T/b7/probe2/probe2.elf" 2>/dev/null)"
ck "RET_ERET=1 has eret"                yes \
   "$(printf '%s\n' "$d3" | grep -q '42000018' && echo yes || echo no)"
ck "and drops rfe, so H2 measures the knob" no \
   "$(printf '%s\n' "$d3" | grep -q '42000010' && echo yes || echo no)"

echo
echo "=== D1 / D2: the build says out loud when it is not a device build ==="
# Three constants exist only because qemu has no MIPS-I core, and every one of
# them would produce an image that looks right and installs a handler the device
# never reads. The pair is what makes the warning a check.
ck "a default build is quiet"             0 \
   "$(make -C "$RP" BUILD="$B" P=probe2 show 2>&1 | grep -c 'NOT A DEVICE BUILD')"
# D2 asks whether the line appears, not how many times: $(BIN)'s recipe ends by
# invoking `show` itself, so any invocation that actually rebuilds prints it twice.
ck "CLEAR_BEV=1 says so"                  yes \
   "$(make -C "$RP" BUILD="$B" P=probe2 show CLEAR_BEV=1 2>&1 | grep -q 'NOT A DEVICE BUILD' && echo yes || echo no)"

echo
echo "=== X1: stub n really is at rlx_cp0_stubs + 12n ==="
# probe2.c reaches CP0 register rd select sel as stub (rd*8+sel) at +12 bytes
# each, and never consults the linker. Checked against the emitted image.
SS="$($NM "$B/probe2/probe2.elf" | awk '$3=="rlx_cp0_stubs"{print $1}')"
SE="$($NM "$B/probe2/probe2.elf" | awk '$3=="rlx_cp0_stubs_end"{print $1}')"
ck "256 stubs of 12 bytes"           3072 "$(( 0x${SE:-0} - 0x${SS:-0} ))"
badstub=0
for n in 0 1 8 129 255; do
    a=$(( 0x${SS} + n * 12 ))
    w="$($OBJDUMP -d --start-address=$a --stop-address=$(( a + 4 )) \
         "$B/probe2/probe2.elf" | awk '/^ *[0-9a-f]+:/{print $2; exit}')"
    rd=$(( n / 8 )); sel=$(( n % 8 ))
    want="$(printf '%08x' $(( 0x40020000 | (rd << 11) | sel )))"
    [ "$w" = "$want" ] || { badstub=$((badstub+1)); echo "      stub $n: $w != $want"; }
done
ck "stubs 0,1,8,129,255 encode rd/sel"  0 "$badstub"

echo
echo "=== Q1 / Q2: both payloads reach their end marker under qemu ==="
# HARNESS ONLY. qemu interlocks the load delay slot and this core does not, so a
# pass here says the control flow is right and nothing about the silicon. It is
# worth the minute it costs because it is the only place probe1's six cells and
# probe2's 256 stubs execute at all before a power cycle is spent on them.
if command -v qemu-system-mips >/dev/null 2>&1; then
    for pay in probe1 probe2; do
        o="$T/q-$pay"
        if QEMU_OUT="$o" QEMU_SECONDS=30 bash "$RP/qemu-run.sh" "$pay" >"$T/q-$pay.log" 2>&1; then
            ck "$pay reaches 'rlxprobe: end' under qemu" yes yes
        else
            ck "$pay reaches 'rlxprobe: end' under qemu" yes no
            sed 's/^/      /' "$T/q-$pay.log" | tail -12
        fi
    done
    # And the one qemu answer that is worth reading: cell 1, the negative
    # control, must come back FRESH under qemu -- the OPPOSITE of what the
    # device is expected to say. If it came back STALE the harness would be
    # broken, not the emulator interesting.
    ck "qemu says cell 1 is FRESH (vd=02), as it must" 1 \
       "$(grep -c 't=43010000 .*vd=00000002' "$T/q-probe1.txt" 2>/dev/null || echo 0)"
else
    sk "qemu" "no qemu-system-mips on this machine"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
