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
#   A3  a LOADADDR change RELINKS in a build directory that already has an
#       image, instead of leaving one linked for the old address
#   A4  ...and the emitted _start really moved, so A3 is not a rebuild that
#       changed nothing
#
#   P2  probe1 builds and passes the same gate
#   V1  the sixteen victims are where probe1.c computes them: 0x400 apart, and
#       every one of them starts with the exact word the experiment patches
#   V2  rlx_fault_frame is inside .bss with room for the offset the loader's
#       do_reserved reads, so SAFE_A0 points somewhere real -- in EVERY payload,
#       because it moved to report.c on 2026-08-25
#   S1  SAFE_A0 is emitted before every CP0 instruction that could fault
#   S2  the mutation: an rlxasm.h with SAFE_A0 removed must make S1 fail
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
#   H4  rlx_do_break loads a0 before its `break` -- the one instruction in the
#       tree guaranteed by design to fault, and the one that had no guard
#   D1  a default build does not print NOT A DEVICE BUILD
#   D2  ...and a build with any qemu-only constant set does
#   X1  stub n is at rlx_cp0_stubs + 12n and encodes the rd/sel probe2.c means
#   F1  make show's flags word is the constant the image carries
#   C1  a device probe2 contains NO write to CP0 Status anywhere
#   C2  ...and a CLEAR_BEV build does, so C1 measures the gate not an absence
#   C3  rlx_isc_inv is not linked into probe2
#   C4  ...and IS linked into probe1, whose cell 4 measured it destroying DRAM
#   C5  `make P=probe2 ISC=1` still produces an image without it -- `override`
#   S3  every routine in the emitted image whose instructions can fault is
#       either guarded or on a named exemption list with a reason
#   S4  the mutation: the SAFE_A0-less build must make S3 fail
#   Q1  probe1 and probe2 run to their end markers under qemu-system-mips
#   Q2  and qemu says cell 1 is FRESH, which is the OPPOSITE of the device's
#       expected answer -- an emulator kinder than the device certifies exactly
#       the bugs the device rejects
#   Q3  qemu's own Count is running, so census row 0x48 comes back S_MOVES --
#       the two-pass census detecting a moving register, on a machine where one
#       is known to move
#
# THE FOUR MUTATIONS THAT RUN UNDER qemu, one per Must-fix
# -------------------------------------------------------
#   M1  one census stub emits `nop` instead of `mfc0`, so its destination is
#       provably not written -> that row MUST report S_NOWRITE. qemu cannot
#       exercise that state on its own: its `mfc0` always writes `rt`. Must-fix 4
#   M2  the install stores go to a scratch address -> install.bad != 0, the
#       payload REFUSES and reaches its end marker, and `break.count` never
#       appears. That branch used to be a hang. Must-fix 2
#   M3  the final copy_vec_back() is removed -> both restore legs fire
#   M5  the saved vector is taken from the handler itself, so the install
#       changes nothing -> the vacuous-read-back WARNING fires. Without this the
#       control that says "this check could not have failed" is itself unchecked
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
echo "=== A3 / A4: a LOADADDR change must RELINK in a directory that has a build ==="
# LOADADDR reaches the LINKER through --defsym and nothing downstream of the
# objects depends on it, so until 2026-08-25 a second `make` with a different
# LOADADDR into the same directory relinked nothing and left an image for the
# old address -- with `show` printing the address that had been asked for
# beside it. Same defect class as the RESULT_BASE one that was live in this
# tree, in the one knob whose drift ships an image the loader will not jump to.
# A2 above never saw it because every case here uses a fresh BUILD=.
rm -rf "$T/b8"
make -C "$RP" BUILD="$T/b8" P=probe0 payload LOADADDR=0x80500000 >/dev/null 2>&1
sha_a="$(sha256sum "$T/b8/probe0/probe0.bin" 2>/dev/null | cut -d' ' -f1)"
make -C "$RP" BUILD="$T/b8" P=probe0 payload LOADADDR=0x81000000 >/dev/null 2>&1
sha_b="$(sha256sum "$T/b8/probe0/probe0.bin" 2>/dev/null | cut -d' ' -f1)"
ck "a LOADADDR change rebuilds in the same dir" no \
   "$([ "$sha_a" = "$sha_b" ] && echo yes || echo no)"
ck "and _start moved with it"            81000000 \
   "$($NM "$T/b8/probe0/probe0.elf" 2>/dev/null | awk '$3=="_start"{print $1}')"

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
echo "=== V2: SAFE_A0's target is inside .bss and big enough, in EVERY payload ==="
# The loader's do_reserved reads offset 148 of the faulting $a0. If
# rlx_fault_frame were smaller than that, or outside the image, SAFE_A0 would be
# pointing at something no better than the integer it replaced.
#
# probe0 is in this loop as of 2026-08-25: uart.S's CP0 readers carry the guard
# now, and probe0 links uart.S. Before that the symbol was defined in probe1.c
# and probe2.c and probe0 had none -- which is why it moved to report.c.
for p in probe0 probe1; do
    FF="$($NM "$B/$p/$p.elf" | awk '$3=="rlx_fault_frame"{print $1}')"
    BS="$($NM "$B/$p/$p.elf" | awk '$3=="_bss_start"{print $1}')"
    BE="$($NM "$B/$p/$p.elf" | awk '$3=="_bss_end"{print $1}')"
    ck "$p: rlx_fault_frame is in .bss"  yes \
       "$([ -n "$FF" ] && [ $(( 0x${FF:-0} )) -ge $(( 0x${BS:-1} )) ] && [ $(( 0x${FF:-0} + 256 )) -le $(( 0x${BE:-0} )) ] && echo yes || echo no)"
    ck "$p: it is word aligned"            0 "$(( 0x${FF:-1} % 4 ))"
done

echo
echo "=== S1: SAFE_A0 is emitted before every CP0 instruction that can fault ==="
# A `lui a0` / `addiu a0` pair immediately before the CP0 write or read. Checked
# in the emitted code, not in the source, because a macro that stopped expanding
# would leave the source looking correct.
#
# The list grew on 2026-08-25 and rlx_mtc0_status left it: that routine is the
# only writer of CP0 Status in the tree and it is now compiled out of anything
# but a CLEAR_BEV build, which is C1/C2 below. uart.S's four CP0 READERS joined
# it, because Must-fix 1 ends on "widen this to every instruction that could
# fault" and three of those four read registers whose existence on this core is
# not established at all.
for fn in rlx_cctl rlx_mfc0_cctl rlx_mfc0_status rlx_mfc0_cause \
          rlx_mfc0_prid rlx_mfc0_config rlx_mfc0_config1; do
    body="$($OBJDUMP -d -m mips:3000 "$B/probe1/probe1.elf" | sed -n "/<$fn>:/,/^\$/p")"
    ck "$fn loads a0 before the CP0 op" 1 \
       "$(printf '%s\n' "$body" | grep -c 'lui.*a0,0x')"
done

echo
echo "=== S2: the mutation -- remove SAFE_A0 and S1 must fail ==="
# Without this, S1 could be passing on a `lui a0` that some unrelated edit put
# there. The mutant keeps the macro defined but makes it expand to nothing.
# It patches rlxasm.h, which is where the macro moved when exc.S needed it too.
mkdir -p "$T/mut"
cp "$RP"/*.c "$RP"/*.h "$RP"/*.S "$RP"/Makefile "$RP"/rlxprobe.lds "$T/mut/"
"${PYTHON:-python3}" - "$T/mut/rlxasm.h" <<'PY'
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
for fn in rlx_cctl rlx_mfc0_cctl rlx_mfc0_status rlx_mfc0_config1; do
    body="$($OBJDUMP -d -m mips:3000 "$T/b4/probe1/probe1.elf" 2>/dev/null | sed -n "/<$fn>:/,/^\$/p")"
    n="$(printf '%s\n' "$body" | grep -c 'lui.*a0,0x')"
    [ "$n" = "0" ] || mutbad=$((mutbad+1))
done
ck "the mutant has no a0 load in any of the four" 0 "$mutbad"
# And the mutant must still BUILD, or S2 would be passing because objdump found
# nothing rather than because the guard went away.
ck "the mutant built at all"                    yes \
   "$([ -s "$T/b4/probe1/probe1.elf" ] && echo yes || echo no)"

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
echo "=== H4: rlx_do_break loads a0 before its break ==="
# THE one instruction in the tree guaranteed by design to fault, and until
# 2026-08-25 the one without the guard. Without it, `break` on the failure
# branch reaches do_reserved with $a0 = 0 (rlx_puts always returns 0), whose
# `lw a3,148(v0)` at 0x80400C00 is a kuseg load through an uninitialised TLB --
# four bytes before its first prom_printf. The promised `Undefined Exception
# happen.` was measured to be complete silence.
body="$($OBJDUMP -d -m mips:3000 "$B/probe2/probe2.elf" | sed -n '/<rlx_do_break>:/,/^$/p')"
ck "a0 is loaded before the break"       1 \
   "$(printf '%s\n' "$body" | sed -n '1,/break/p' | grep -c 'lui.*a0,0x')"
ck "and the break is still there"        1 "$(printf '%s\n' "$body" | grep -c '	break')"
FF="$($NM "$B/probe2/probe2.elf" | awk '$3=="rlx_fault_frame"{print $1}')"
BE="$($NM "$B/probe2/probe2.elf" | awk '$3=="_bss_end"{print $1}')"
ck "probe2: the frame has room for offset 148" yes \
   "$([ -n "$FF" ] && [ $(( 0x${FF:-0} + 152 )) -le $(( 0x${BE:-0} )) ] && echo yes || echo no)"

echo
echo "=== C1 / C2: a device probe2 does not write CP0 Status ANYWHERE ==="
# probe1 cell 4 measured on 2026-08-25 that Status.IsC does not isolate on this
# core: rlx_isc_inv's `sb $0` byte stores reached DRAM and corrupted both
# victims. So probe2 must not touch Status -- and "must not" is a claim until
# something reads the emitted words. `mtc0 rt,$12` is the only shape that can,
# and the only routine in the tree that emits one is compiled out of a device
# build together with its single call site.
d2="$($OBJDUMP -d -m mips:3000 "$B/probe2/probe2.elf")"
ck "writes to CP0 Status in a device build" 0 \
   "$(printf '%s\n' "$d2" | grep -c 'mtc0.*c0_sr')"
ck "and the CCTL writes are still there"    3 \
   "$(printf '%s\n' "$d2" | grep -c 'mtc0.*\$20')"
rm -rf "$T/b9"
make -C "$RP" BUILD="$T/b9" P=probe2 payload CLEAR_BEV=1 >/dev/null 2>&1
ck "a CLEAR_BEV build DOES write Status"  yes \
   "$($OBJDUMP -d -m mips:3000 "$T/b9/probe2/probe2.elf" 2>/dev/null | grep -q 'mtc0.*c0_sr' && echo yes || echo no)"

echo
echo "=== C3 / C4 / C5: rlx_isc_inv is not linked into probe2, and cannot be ==="
ck "probe2 does not link rlx_isc_inv"       0 \
   "$($NM "$B/probe2/probe2.elf" | grep -c 'rlx_isc_inv')"
ck "probe1 DOES, so C3 measures the gate"   1 \
   "$($NM "$B/probe1/probe1.elf" | grep -c 'rlx_isc_inv')"
# `override ISC := $(ISC_$(P))` in the Makefile. A command-line variable beats a
# plain assignment; this is the case that says the override is really there.
rm -rf "$T/b10"
make -C "$RP" BUILD="$T/b10" P=probe2 payload ISC=1 >/dev/null 2>&1
ck "ISC=1 on the command line changes nothing" 0 \
   "$($NM "$T/b10/probe2/probe2.elf" 2>/dev/null | grep -c 'rlx_isc_inv')"

echo
echo "=== F1: make show's flags word is the constant the image carries ==="
# probe2.c materialises FLAGS_W into its own code; the Makefile recomputes it
# from the knobs. Two derivations, and this is where they have to agree -- a
# number printed beside an image has to come from somewhere other than the image
# or it is the image repeating itself.
fl="$(make -C "$RP" --no-print-directory BUILD="$B" P=probe2 show 2>/dev/null \
      | sed -n 's/^flags  *\([0-9a-f]*\) .*/\1/p' | head -1)"
ck "make show prints a device build's flags" 50010002 "$fl"
ck "and the image materialises its top half" yes \
   "$(printf '%s\n' "$d2" | grep -q "0x${fl:0:4}" && echo yes || echo no)"

echo
echo "=== S3: every faulting instruction is guarded, or exempt with a reason ==="
# S1 checks a LIST of routines. A list is only as good as whoever last added to
# it, and the audit's Must-fix 1 exists because `break` was not on it. This
# reads the emitted image instead: it finds every routine containing an
# instruction that can fault and asks whether $a0 was made safe first. Anything
# neither guarded nor on the exemption table below is a failure, so a NEW
# routine tomorrow is caught by construction rather than by remembering.
cat > "$T/guardscan.py" <<'PY'
import re, sys
payload = sys.argv[1]
# Exempt, and every entry is an argument rather than a suppression.
EXEMPT = {
 ("probe1", "rlx_isc_inv"):
   "entered with $a0 = the victim's address, already a real word-aligned KSEG0 "
   "address; SAFE_A0 would destroy the argument the routine needs (cache.S)",
 ("probe1", "rlx_r3k_size"):
   "same argument, and GEOM=0 keeps it out of the image entirely",
 ("probe2", "rlx_exc_entry"):
   "it IS the handler -- a fault inside it cannot be caught by anything, and "
   "its reads are CP0 13 and 14, which do_reserved itself reads",
 ("probe2", "rlx_cp0_stubs"):
   "entered through rlx_call0_primed with $a0 = the stub's own address, so the "
   "property SAFE_A0 establishes already holds; and the handler that catches a "
   "trap here was proved live by the `break` control before the census starts",
}
FAULTY = re.compile(r"\t(mfc0|mtc0|break|syscall|rfe)\b|\t\.word\t0x4[0-9a-f]{7}")
GUARD = re.compile(r"\tlui\t.*a0,0x")
cur, order, first, guard = None, [], {}, {}
for line in sys.stdin:
    m = re.match(r"^[0-9a-f]+ <([^>]+)>:", line)
    if m:
        cur = m.group(1)
        order.append(cur)
        continue
    if cur is None:
        continue
    if cur not in first and GUARD.search(line):
        guard[cur] = True
    if cur not in first and FAULTY.search(line):
        first[cur] = line.strip()
bad = 0
for fn in order:
    if fn not in first:
        continue
    if guard.get(fn):
        print("    guarded   %s" % fn)
    elif (payload, fn) in EXEMPT:
        print("    exempt    %-18s %s" % (fn, EXEMPT[(payload, fn)]))
    else:
        bad += 1
        print("    UNGUARDED %-18s %s" % (fn, first[fn]))
print("SCANNED=%d UNGUARDED=%d" % (len(first), bad))
PY
guardscan () { $OBJDUMP -d -m mips:3000 "$1" | "${PYTHON:-python3}" "$T/guardscan.py" "$2"; }
for p in probe1 probe2; do
    g="$(guardscan "$B/$p/$p.elf" "$p")"
    printf '%s\n' "$g" | grep -E 'UNGUARDED [a-z]' | sed 's/^/  /'
    ck "$p: unguarded faulting routines"  0 \
       "$(printf '%s\n' "$g" | sed -n 's/^SCANNED=[0-9]* UNGUARDED=\([0-9]*\)$/\1/p')"
    n="$(printf '%s\n' "$g" | sed -n 's/^SCANNED=\([0-9]*\) .*/\1/p')"
    ck "$p: and it had routines to scan" yes "$([ "${n:-0}" -ge 5 ] && echo yes || echo no)"
done

echo
echo "=== S4: the mutation -- the SAFE_A0-less build must make S3 fail ==="
rm -rf "$T/b11"
make -C "$T/mut" BUILD="$T/b11" P=probe2 payload HAZLINT="$HERE/hazlint" >/dev/null 2>&1
g="$(guardscan "$T/b11/probe2/probe2.elf" probe2)"
mb="$(printf '%s\n' "$g" | sed -n 's/^SCANNED=[0-9]* UNGUARDED=\([0-9]*\)$/\1/p')"
ck "the mutant has unguarded routines"  yes "$([ "${mb:-0}" -ge 5 ] && echo yes || echo no)"
ck "and rlx_do_break is one of them"      1 \
   "$(printf '%s\n' "$g" | grep -c 'UNGUARDED rlx_do_break')"

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
       "$(grep -c 't=43010000 .*vd=00000002' "$T/q-probe1.txt" 2>/dev/null | head -1)"

    # Q3. qemu's 24Kf HAS a running Count, so the two-pass census must see rd 9
    # sel 0 change between its two reads. This is the positive control on
    # S_MOVES, on a machine where a moving register is known to exist -- and it
    # is the state that answers F50b on the device without going through
    # rlx_count_delta's arithmetic at all.
    ck "census row 0x48 is S_MOVES under qemu" 1 \
       "$(grep -c '^rlxprobe: cp0 00000048 .* 00000004' "$T/q-probe2.txt" 2>/dev/null | head -1)"
    ck "and count.row48 agrees with the row"   1 \
       "$(grep -c '^rlxprobe: count.row48=00000004' "$T/q-probe2.txt" 2>/dev/null | head -1)"
    # The arithmetic on the census: every row lands in exactly one state.
    tot=0
    for f in traps values zeros nowrite moves mixed; do
        v="$(sed -n "s/^rlxprobe: $f=\([0-9a-f]*\).*/\1/p" "$T/q-probe2.txt" 2>/dev/null | head -1)"
        tot=$(( tot + 0x${v:-0} ))
    done
    ck "the six state counts sum to 256 rows" 256 "$tot"

    echo
    echo "=== M1 / M2 / M3 / M5: one mutation per Must-fix, run under qemu ==="
    # Each mutant is a full copy of the tree with ONE change, built for qemu and
    # run. They go in parallel because each is a fresh directory and qemu never
    # halts by itself, so the wall clock is one timeout rather than four.
    mkmut () {                       # mkmut <name> -> prints the tree root
        md="$T/mut-$1"; mkdir -p "$md/src"
        cp "$RP"/*.c "$RP"/*.h "$RP"/*.S "$RP"/Makefile "$RP"/rlxprobe.lds \
           "$RP"/qemu-run.sh "$md/src/"
        ln -sf "$HERE/hazlint" "$md/hazlint"     # the Makefile looks at $(HERE)../hazlint
        echo "$md"
    }
    patch_mut () {                   # patch_mut <file> <python on stdin>
        "${PYTHON:-python3}" - "$1"
    }

    m1="$(mkmut m1)"; m2="$(mkmut m2)"; m3="$(mkmut m3)"; m5="$(mkmut m5)"

    # M1 -- Must-fix 4. One census stub emits `nop`, so nothing writes its
    # destination. That row MUST come back S_NOWRITE. qemu cannot produce that
    # state on its own: its `mfc0` always writes `rt`, so without this mutation
    # the whole prime mechanism is untested by the harness.
    patch_mut "$m1/src/exc.S" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "\t.macro\tCP0STUB rd, sel\n\t.word\t0x40020000 | (\\rd << 11) | \\sel\n"
new = ("\t.macro\tCP0STUB rd, sel\n\t.if (\\rd == 0) && (\\sel == 0)\n\tnop\n"
       "\t.else\n\t.word\t0x40020000 | (\\rd << 11) | \\sel\n\t.endif\n")
assert old in s, "CP0STUB macro not found"
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
    # M2 -- Must-fix 2. The install stores land somewhere else, so the read-back
    # must catch it, the payload must REFUSE, and `break` must never run. That
    # branch used to be a hang costing one power cycle.
    patch_mut "$m2/src/probe2.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = ("\t\twr_unc(VEC_UTLB + i * 4u, rlx_exc_entry[i]);\n"
       "\t\twr_unc(VEC_GENERAL + i * 4u, rlx_exc_entry[i]);\n")
new = ("\t\twr_unc(0x80B00000u + i * 4u, rlx_exc_entry[i]);\n"
       "\t\twr_unc(0x80B00100u + i * 4u, rlx_exc_entry[i]);\n")
assert old in s, "install store loop not found"
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
    # M3 -- the restore. Remove the final copy_vec_back() and BOTH legs must
    # fire: the words no longer match the saved copy, and they still hold ours.
    patch_mut "$m3/src/probe2.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "\tcopy_vec_back();\n\n\t/* Prove the restore"
new = "\t/* MUTANT: copy_vec_back() removed. Prove the restore"
assert old in s, "the final copy_vec_back was not found"
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY
    # M5 -- the control ON the control. Save the handler's own words as the
    # "previous" vector contents, so the install changes nothing and the
    # read-back cannot fail. The payload must SAY the check was vacuous.
    patch_mut "$m5/src/probe2.c" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# The saved copy becomes the handler itself, so the install changes nothing and
# the read-back cannot fail. A block-scope `extern` because the file's own
# declaration of rlx_exc_entry comes after this function.
old = ("\tfor (i = 0; i < VEC_WORDS; i++) {\n"
       "\t\tsaved_vec[i] = rd_unc(VEC_UTLB + i * 4u);\n"
       "\t\tsaved_vec[i + VEC_WORDS] = rd_unc(VEC_GENERAL + i * 4u);\n"
       "\t}\n")
new = ("\textern u32 rlx_exc_entry[];\n"
       "\tfor (i = 0; i < VEC_WORDS; i++) {\n"
       "\t\tsaved_vec[i] = rlx_exc_entry[i];\n"
       "\t\tsaved_vec[i + VEC_WORDS] = rlx_exc_entry[i];\n"
       "\t}\n")
assert old in s, "copy_vec_out body not found"
open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))
PY

    for m in "$m1" "$m2" "$m3" "$m5"; do
        ( QEMU_OUT="$m/out" QEMU_SECONDS=14 bash "$m/src/qemu-run.sh" probe2 \
              >"$m/run.log" 2>&1 ) &
    done
    wait

    ck "M1: the nopped stub reads S_NOWRITE"  1 \
       "$(grep -c '^rlxprobe: cp0 00000000 c0de0000 d1ce0000 00000003' "$m1/out.txt" 2>/dev/null | head -1)"
    ck "M1: and the baseline row 0 was NOT"   0 \
       "$(grep -c '^rlxprobe: cp0 00000000 c0de0000 d1ce0000 00000003' "$T/q-probe2.txt" 2>/dev/null | head -1)"
    ck "M2: install.bad is non-zero"        yes \
       "$(grep -q '^rlxprobe: install.bad=00000000' "$m2/out.txt" 2>/dev/null && echo no || echo yes)"
    ck "M2: it refuses instead of breaking"   1 \
       "$(grep -c 'the handler is NOT at the vector' "$m2/out.txt" 2>/dev/null | head -1)"
    ck "M2: and break.count never appears"    0 \
       "$(grep -c 'break.count' "$m2/out.txt" 2>/dev/null | head -1)"
    ck "M2: but it still reaches its end marker" 1 \
       "$(grep -c 'rlxprobe: end' "$m2/out.txt" 2>/dev/null | head -1)"
    ck "M3: restore.mismatch fires"         yes \
       "$(grep -q '^rlxprobe: restore.mismatch=00000000' "$m3/out.txt" 2>/dev/null && echo no || echo yes)"
    ck "M3: restore.stillhandler fires"     yes \
       "$(grep -q '^rlxprobe: restore.stillhandler=00000000' "$m3/out.txt" 2>/dev/null && echo no || echo yes)"
    ck "M3: and the baseline had both at 0"   2 \
       "$(grep -c -E '^rlxprobe: restore.(mismatch|stillhandler)=00000000' "$T/q-probe2.txt" 2>/dev/null | head -1)"
    ck "M5: the vacuous read-back is announced" 1 \
       "$(grep -c 'install.changed=0 -- the vector' "$m5/out.txt" 2>/dev/null | head -1)"
    ck "M5: and the baseline says nothing"      0 \
       "$(grep -c 'install.changed=0 -- the vector' "$T/q-probe2.txt" 2>/dev/null | head -1)"
else
    sk "qemu" "no qemu-system-mips on this machine"
    sk "the four Must-fix mutations" "they run under qemu"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
