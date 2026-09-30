#!/usr/bin/env bash
# Controls for tools/uspacescan.py -- and controls on those controls.
#
# `uspacescan.py --self-test` already runs thirty controls of its own before it
# will report on anything, fourteen of them on synthetic ELFs it builds in
# process and sixteen on binaries the target toolchain really compiles.  This
# file exists because that is not enough, for the reason this repository keeps
# writing down: a control that lives inside the tool it checks passes whenever
# the tool is broken in a way that also breaks the control.  So everything
# below MUTATES the tool and demands that it notices.
#
#   B0  the UNMUTATED copy in the scratch tree passes.  Without this, every
#       mutation below could be failing for a reason that has nothing to do
#       with the mutation -- CLAUDE.md: "before trusting a mutation run,
#       confirm the unmutated suite passes"
#   B1  the real self-test, on the real tool, in this checkout
#   E1  the exit-code contract: 0 clean, 1 a finding, 2 disagreement,
#       3 refused -- and never a traceback on any of them
#   F1  the tracked fixtures are the files that get compiled, not the copies
#       built into the tool
#   M1  take the BYTE-LEVEL path away (fp_search returns nothing) and the
#       STRIPPED control must go red.  This is the whole point of the rewrite:
#       without 1c there is nothing to read in a stripped static ELF, and the
#       old instrument answered 0 there
#   M2  blind source (2)'s undefined-symbol test and its planted positive must
#       go red
#   M3  remove the anti-vacuity refusal and a stripped ELF with no fingerprint
#       must stop being refused -- which C4 must catch
#   M4  move `execve` to FORBIDDEN in a COPY of the name table and the verdict
#       on the very same ELF must flip.  That is what makes the table data
#   M5  lower --fp-distinct until the degenerate `vfork` fingerprint is used,
#       and T7 must catch it
#   M6  make the two-source disagreement a vote instead of an error and T9
#       must catch it
#   M7  make the planted positive not plant anything, and the tool must refuse
#       rather than report a clean run
#   P1  the four rlxfw target binaries, both sources, real numbers
#   V1  the vendor census reproduces FW-20's 31 (string scan) and upstream's
#       28 (import walk) on the same name set, and names the three files that
#       are the difference
#   X1  the toolchain's own `mips-linux-nm -u` agrees with source (2)
#
# M1 is the DoD clause: remove the byte-level path and --self-test must exit
# non-zero.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$HERE/uspacescan.py"
TABLE="$HERE/uspacescan-names.tsv"
TRIP="$HERE/vendor-tripwire.sh"
PY="${PYTHON:-/usr/bin/python3}"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
TC="${TC:-$WORK/rebuild/src-vendor/rtl819x-toolchain/toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30}"
ROOTFS="${ROOTFS:-$WORK/extracted/unit-2018/squashfs-root}"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0; skip=0
ck () {  # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-54s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-54s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-54s %s\n' "$1" "$2"; skip=$((skip+1)); }

# A mutated copy of the whole tool directory, so the copy finds its own table
# and its own fixtures and a mutation cannot be masked by reading the real ones.
mutant () {  # name sed-expr...
    local name="$1"; shift
    local d="$T/$name"
    mkdir -p "$d"
    cp "$TOOL" "$d/uspacescan.py"
    cp "$TABLE" "$d/uspacescan-names.tsv"
    [ -d "$HERE/uspacescan-fixtures" ] && cp -r "$HERE/uspacescan-fixtures" "$d/"
    local e
    for e in "$@"; do sed -i "$e" "$d/uspacescan.py"; done
    printf '%s\n' "$d/uspacescan.py"
}

# Did the sed actually change anything?  A mutation that silently matched
# nothing makes the tool look robust when the test never ran.
bit () {  # mutant-path
    cmp -s "$TOOL" "$1" && echo no || echo yes
}

selftest () {  # tool-path [extra args...]
    local t="$1"; shift
    "$PY" "$t" --self-test --tc "$TC" --trip "$TRIP" "$@" \
        > "$T/out.txt" 2>"$T/err.txt"
    echo $?
}

echo "=== B0/B1: the unmutated tool, in this checkout and in the scratch copy ==="
if [ ! -f "$TOOL" ]; then
    echo "  FAIL   no tool at $TOOL"; exit 1
fi
if [ ! -x "$TOOL" ]; then
    printf '  note   %s is not executable in the working tree (DrvFs); the\n' "$TOOL"
    printf '         recorded mode is what tools/test-file-modes.sh reads.\n'
fi
HAVE_CC=no; [ -x "$TC/bin/mips-linux-gcc" ] && [ -f "$TC/lib/libc.a" ] && HAVE_CC=yes
rc="$(selftest "$TOOL")"
ck "B1 --self-test on the real tool" 0 "$rc"
ck "B1b and it says how many controls ran" yes \
   "$(grep -qE '^  [0-9]+ passed, 0 failed' "$T/out.txt" && echo yes || echo no)"
ck "B1c the synthetic half ran" 1 "$(grep -c 'SELF-TEST, PART 1' "$T/out.txt")"
ck "B1d the toolchain half ran (T1 present)" 1 \
   "$(grep -c '^  ok     T1 ' "$T/out.txt")"
nctl="$(sed -n 's/^  \([0-9]*\) passed, 0 failed.*/\1/p' "$T/out.txt" | head -1)"
ck "B1e the number of controls is not zero" yes \
   "$([ "${nctl:-0}" -gt 20 ] && echo yes || echo no)"
base="$(mutant base)"
ck "B0 the unmutated scratch copy passes too" 0 "$(selftest "$base")"

echo
echo "=== E1: the exit-code contract, and never a traceback ==="
"$PY" "$TOOL" scan --elf /nonexistent/file --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
ck "E1a a missing --elf refuses" 3 "$rc"
ck "E1b with a one-line reason on stderr" 1 "$(grep -c '^REFUSED: ' "$T/e")"
ck "E1c and no traceback" 0 "$(grep -c 'Traceback' "$T/e")"
"$PY" "$TOOL" --vendor-census /nonexistent/dir --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
ck "E1d a missing census root refuses" 3 "$rc"
ck "E1e and still no traceback" 0 "$(grep -c 'Traceback' "$T/e")"
"$PY" "$TOOL" scan --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
ck "E1f scan with nothing to scan refuses" 3 "$rc"
head -c 200 /dev/urandom > "$T/garbage"
"$PY" "$TOOL" scan --elf "$T/garbage" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
ck "E1g a non-ELF refuses, no traceback" "3 0" \
   "$rc $(grep -c 'Traceback' "$T/e")"
"$PY" "$TOOL" scan --elf "$TOOL" --objdir "$T" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
ck "E1h a text file offered as an ELF refuses" 3 "$rc"
printf 'x\ty\tz\n' > "$T/bad.tsv"
"$PY" "$TOOL" --self-test --table "$T/bad.tsv" >"$T/o" 2>"$T/e"; rc=$?
ck "E1i a malformed name table refuses, no traceback" "3 0" \
   "$rc $(grep -c 'Traceback' "$T/e")"

echo
echo "=== F1: the fixtures that are compiled are the tracked ones ==="
if [ "$HAVE_CC" = no ]; then
    sk "F1 which fixture was compiled" "no cross compiler at $TC"
else
    selftest "$TOOL" > /dev/null
    ck "F1 pos.c came from tools/uspacescan-fixtures/" 1 \
       "$(grep -c 'fixture pos.c .*uspacescan-fixtures/pos.c' "$T/out.txt")"
    ck "F1b allowed.c likewise" 1 \
       "$(grep -c 'fixture allowed.c .*uspacescan-fixtures/allowed.c' "$T/out.txt")"
    ck "F1c and pos.c really contains the forbidden call" 1 \
       "$(grep -c 'return system(argv\[1\]);' "$HERE/uspacescan-fixtures/pos.c")"
    ck "F1d and allowed.c really contains execve" 1 \
       "$(grep -c 'return execve(argv\[1\], av, ev);' "$HERE/uspacescan-fixtures/allowed.c")"
fi

echo
echo "=== M1: take the BYTE-LEVEL path away; the stripped control must go red ==="
m1="$(mutant m1 's/^    hits = \[\]$/    hits = []\n    return hits/')"
ck "M1 the mutation bit" yes "$(bit "$m1")"
rc="$(selftest "$m1")"
ck "M1a --self-test exits non-zero" nonzero \
   "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
ck "M1b C5b (the fingerprint finds the relocated copy) fails" 1 \
   "$(grep -c '^  FAIL   C5b ' "$T/out.txt")"
if [ "$HAVE_CC" = yes ]; then
    ck "M1c T2 (the STRIPPED planted positive) fails" 1 \
       "$(grep -c '^  FAIL   T2 ' "$T/out.txt")"
    ck "M1d and T1 (the UNSTRIPPED one) still passes -- so M1 removed 1c only" 1 \
       "$(grep -c '^  ok     T1 ' "$T/out.txt")"
else
    sk "M1c/M1d the stripped control" "no cross compiler"
fi

echo
echo "=== M2: blind source (2); its planted positive must go red ==="
m2="$(mutant m2 's/s\["bind"\] in (STB_GLOBAL, STB_WEAK):/s["bind"] in ():/')"
ck "M2 the mutation bit" yes "$(bit "$m2")"
rc="$(selftest "$m2")"
ck "M2a --self-test exits non-zero" nonzero \
   "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
ck "M2b C6 (an object's UND system) fails" 1 \
   "$(grep -c '^  FAIL   C6 ' "$T/out.txt")"
ck "M2c and source (1) is untouched -- C1 still passes" 1 \
   "$(grep -c '^  ok     C1 ' "$T/out.txt")"

echo
echo "=== M3: remove the anti-vacuity refusal ==="
m3="$(mutant m3 's/if not has_dyn and not has_sym and not usable_fp:/if False:/')"
ck "M3 the mutation bit" yes "$(bit "$m3")"
rc="$(selftest "$m3")"
ck "M3a --self-test exits non-zero" nonzero \
   "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
ck "M3b C4 (a stripped static ELF is refused) fails" 1 \
   "$(grep -c '^  FAIL   C4 ' "$T/out.txt")"

echo
echo "=== M4: the name table is DATA -- move execve to FORBIDDEN ==="
sed 's/^execve\tALLOWED\t/execve\tFORBIDDEN\t/' "$TABLE" > "$T/flip.tsv"
ck "M4 the table edit bit" yes \
   "$(cmp -s "$TABLE" "$T/flip.tsv" && echo no || echo yes)"
if [ "$HAVE_CC" = no ]; then
    sk "M4a-c the verdict flip" "no cross compiler"
else
    rc="$(selftest "$TOOL" --table "$T/flip.tsv")"
    ck "M4a --self-test exits non-zero on the flipped table" nonzero \
       "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
    ck "M4b T4 (the execve fixture is clean) now FAILS" 1 \
       "$(grep -c '^  FAIL   T4 ' "$T/out.txt")"
    ck "M4c on the SAME ELF, with no change to the tool" 1 \
       "$(grep -c 'fixture allowed.c' "$T/out.txt")"
fi

echo
echo "=== M5: use the degenerate fingerprint; T7 must catch it ==="
if [ "$HAVE_CC" = no ]; then
    sk "M5 the degenerate fingerprint" "needs libc.a at $TC/lib"
else
    rc="$(selftest "$TOOL" --fp-distinct 1)"
    ck "M5a --self-test exits non-zero at --fp-distinct 1" nonzero \
       "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
    ck "M5b T7 (the degenerate fingerprint is named) fails" 1 \
       "$(grep -c '^  FAIL   T7 ' "$T/out.txt")"
    ck "M5c and C5d fails too -- a 3-word fingerprint is no longer WEAK" 1 \
       "$(grep -c '^  FAIL   C5d ' "$T/out.txt")"
fi

echo
echo "=== M6: make disagreement a vote ==="
m6="$(mutant m6 's/^        st = "DISAGREE"$/        st = "CLEAN"/')"
ck "M6 the mutation bit" yes "$(bit "$m6")"
if [ "$HAVE_CC" = no ]; then
    sk "M6a/M6b the disagreement rule" "no cross compiler"
else
    rc="$(selftest "$m6")"
    ck "M6a --self-test exits non-zero" nonzero \
       "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
    ck "M6b T9 (clean + dirty is DISAGREE) fails" 1 \
       "$(grep -c '^  FAIL   T9 ' "$T/out.txt")"
fi

echo
echo "=== M7: a planted positive that plants nothing must be refused ==="
mkdir -p "$T/m7/uspacescan-fixtures"
cp "$TOOL" "$T/m7/uspacescan.py"
cp "$TABLE" "$T/m7/uspacescan-names.tsv"
cp "$HERE/uspacescan-fixtures/allowed.c" "$T/m7/uspacescan-fixtures/"
printf 'int main(void)\n{\n\treturn 0;\n}\n' > "$T/m7/uspacescan-fixtures/pos.c"
if [ "$HAVE_CC" = no ]; then
    sk "M7 the gutted planted positive" "no cross compiler"
else
    rc="$(selftest "$T/m7/uspacescan.py")"
    ck "M7a --self-test exits non-zero" nonzero \
       "$([ "$rc" != 0 ] && echo nonzero || echo 0)"
    ck "M7b and says the planted positive plants nothing" 1 \
       "$(grep -c 'planted positive that plants nothing' "$T/err.txt")"
fi

echo
echo "=== the planted positive, end to end through the scan verb ==="
if [ "$HAVE_CC" = no ]; then
    sk 'S1-S4 the planted positive through the scan verb' "no cross compiler"
else
    S="$T/s"; mkdir -p "$S"
    cp "$HERE/uspacescan-fixtures/pos.c" "$S/pos.c"
    cp "$HERE/uspacescan-fixtures/allowed.c" "$S/allowed.c"
    CF="-Os -std=gnu99 -static -fno-builtin -fno-strict-aliasing -fno-common"
    # One tripwire bracket around the whole build, for the reason
    # uspacescan.py's tc_build() states: a bracket costs a second of sleep and
    # two six-tree `git status --ignored` runs, and six of them dominate this
    # suite's wall clock.  Everything vendor still runs inside a bracket.
    cat > "$S/build.sh" <<EOF
set -e
cd "$S"
"$TC/bin/mips-linux-gcc" $CF -c pos.c -o pos.o
"$TC/bin/mips-linux-gcc" -static -o pos.elf pos.o
cp pos.elf pos.stripped
"$TC/bin/mips-linux-strip" pos.stripped
"$TC/bin/mips-linux-gcc" $CF -c allowed.c -o allowed.o
"$TC/bin/mips-linux-gcc" -static -o allowed.elf allowed.o
EOF
    ( cd "$S" && bash "$TRIP" --quiet -- /bin/sh "$S/build.sh" ) \
        > "$T/build.log" 2>&1
    ck "S0 the fixtures built" yes "$([ -f "$S/pos.stripped" ] && echo yes || echo no)"
    mkdir -p "$S/pos.obj"; cp "$S/pos.o" "$S/pos.obj/"
    mkdir -p "$S/allowed.obj"; cp "$S/allowed.o" "$S/allowed.obj/"
    "$PY" "$TOOL" scan --elf "$S/pos.stripped" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "S1 source (1) alone flags the STRIPPED planted positive" 1 "$rc"
    ck "S1b and names system as the finding" 1 \
       "$(grep -c '^  FINDING   (1) .*system' "$T/o")"
    ck "S1c and says nothing was paired, rather than claiming agreement" 1 \
       "$(grep -c '^  UNPAIRED ' "$T/o")"
    "$PY" "$TOOL" scan --objdir "$S/pos.obj" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "S2 source (2) alone flags the planted object" 1 "$rc"
    "$PY" "$TOOL" scan --elf "$S/allowed.elf" --objdir "$S/allowed.obj" \
        --pair "$S/allowed.elf=$S/allowed.obj" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "S3 the execve fixture is permitted by both sources" 0 "$rc"
    ck "S3b and execve is COUNTED in the same run" 1 \
       "$(grep -c 'ALLOWED, counted not flagged: execve' "$T/o")"
    "$PY" "$TOOL" scan --elf "$S/allowed.elf" --objdir "$S/pos.obj" \
        --pair "$S/allowed.elf=$S/pos.obj" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "S4 a mismatched pair is DISAGREE, exit 2" 2 "$rc"
    ck "S4b and the VERDICT section names the file" 1 \
       "$(sed -n '/=== VERDICT ===/,$p' "$T/o" | grep -c '^  DISAGREE ')"
fi

echo
echo "=== P1: the rlxfw target binaries ==="
# `build/` is gitignored, so a fresh clone has none of the installed copies and
# only the staging tree under $FWRE_WORK carries the ELFs.  Both populations are
# looked at, and the DISCOVERED count is printed beside the verdict -- a check
# written against a fixed 4 would pass vacuously in a clone and be a lie about
# what ran.
ELVES=""; n_elf=0
for p in "$HERE/../build/rlxfw-user/isaprobe/uprobe" \
         "$HERE/../build/rlxfw-user/isaprobe/ucost" \
         "$HERE/../build/rlxfw-user/iperf3/iperf3" \
         "$HERE/../build/rlxfw-user/linkprobe/linkprobe" \
         "$WORK/rebuild/rlxfw-user/isaprobe/build/uprobe" \
         "$WORK/rebuild/rlxfw-user/ucost/build/ucost" \
         "$WORK/rebuild/rlxfw-user/iperf3/build/iperf3" \
         "$WORK/rebuild/rlxfw-user/linkprobe/build/linkprobe"; do
    if [ -f "$p" ]; then ELVES="$ELVES --elf $p"; n_elf=$((n_elf+1)); fi
done
if [ "$n_elf" -eq 0 ] || [ "$HAVE_CC" = no ]; then
    sk "P1 the rlxfw binaries" "none built, or no libc.a for the fingerprints"
else
    # shellcheck disable=SC2086
    "$PY" "$TOOL" scan $ELVES --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "P1a every built rlxfw ELF is clean of all six ($n_elf found)" 0 "$rc"
    ck "P1b the population really was scanned, not skipped" "$n_elf" \
       "$(grep -c '^ELF  ' "$T/o")"
    ck "P1c each one is static and stripped" "$n_elf" \
       "$(grep -c 'shape=static stripped=True' "$T/o")"
    ck "P1d the verdict line says how many were scanned" 1 \
       "$(grep -c "CLEAN: $n_elf ELF" "$T/o")"
    ck "P1e and every one of the six FORBIDDEN names was really looked for" \
       "$((n_elf * 6))" "$(grep -cE '^     [a-z_]+ +FORBIDDEN ' "$T/o")"
    ck "P1f fork is counted, not flagged, wherever it is linked in" 1 \
       "$(grep -c '^  ALLOWED, counted not flagged: fork' "$T/o")"
fi

echo
echo "=== V1: the vendor baseline, reproduced on the same name set ==="
if [ ! -d "$ROOTFS" ]; then
    sk "V1 the vendor census" "no extracted rootfs at $ROOTFS"
else
    "$PY" "$TOOL" --vendor-census "$ROOTFS" --only system,popen --tc "$TC" \
        >"$T/o" 2>"$T/e"; rc=$?
    ck "V1a the census runs" 0 "$rc"
    ck "V1b 161 regular files" 161 \
       "$(sed -n 's/^  regular files[^0-9]*\([0-9]*\)$/\1/p' "$T/o" | head -1)"
    ck "V1b2 55 ELFs among them" 55 \
       "$(sed -n 's/^  ELF files[^0-9]*\([0-9]*\)$/\1/p' "$T/o" | head -1)"
    ck "V1c the STRING scan reproduces FW-20's 31" 31 \
       "$(sed -n 's/^  ELFs matched by the STRING scan *\([0-9]*\).*/\1/p' "$T/o")"
    ck "V1d the IMPORT walk reproduces upstream's 28" 28 \
       "$(sed -n 's/^  ELFs matched by the IMPORT walk *\([0-9]*\).*/\1/p' "$T/o")"
    ck "V1e and the 3 that are the difference are named" 3 \
       "$(sed -n '/string-only/,/import-only/p' "$T/o" | grep -c '^    [a-z]')"
    ck "V1f one of them is static, so the import walk is BLIND to it" 1 \
       "$(sed -n '/string-only/,/import-only/p' "$T/o" | grep -c 'static')"
    "$PY" "$TOOL" --vendor-census "$ROOTFS" --tc "$TC" >"$T/o2" 2>"$T/e"
    ck "V1g the six-name table is a DIFFERENT number, and says so" 2 \
       "$(grep -c 'NOT comparable' "$T/o2")"
fi

echo
echo "=== X1: the toolchain's own nm agrees with source (2) ==="
if [ "$HAVE_CC" = no ] || [ ! -d "$WORK/rebuild/rlxfw-user/linkprobe/build" ]; then
    sk "X1 the nm cross-check" "no cross compiler, or no built objects"
else
    "$PY" "$TOOL" scan --objdir "$WORK/rebuild/rlxfw-user/linkprobe/build" \
        --nm "$TC/bin/mips-linux-nm" --trip "$TRIP" --tc "$TC" \
        >"$T/o" 2>"$T/e"; rc=$?
    ck "X1a the cross-check runs and agrees" 0 "$rc"
    ck "X1b and says so" 1 "$(grep -c 'nm cross-check: agrees' "$T/o")"
    # A cross-check that reports nothing agrees with 0 for free.  /bin/true
    # prints no undefined symbol at all, so if the tool called that agreement,
    # `--nm` would be decoration.  It must refuse instead.
    "$PY" "$TOOL" scan --objdir "$WORK/rebuild/rlxfw-user/linkprobe/build" \
        --nm /bin/true --trip "$TRIP" --tc "$TC" >"$T/o" 2>"$T/e"; rc=$?
    ck "X1c an nm that reports nothing is NOT taken as agreement" 3 "$rc"
    ck "X1d and the refusal says why" 1 \
       "$(grep -c 'agrees with 0 for free' "$T/e")"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
