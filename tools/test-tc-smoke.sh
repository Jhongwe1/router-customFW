#!/usr/bin/env bash
# Controls for tools/tc-smoke.sh.
#
# The ladder's whole value is that each rung is a separate claim. So every case
# here breaks exactly one rung and checks that the rung below it still reads ok
# and the rung above it does NOT read ok. A harness that reported the same
# verdict for a broken assembler and a broken emulator would have four rungs
# and one bit of information.
#
#   S1  no toolchain at all        -> exit 3, and not one table row. The failure
#                                     this repository keeps meeting is a tool
#                                     that reports when it cannot see.
#   S2  `as` will not start        -> L1 FAIL, and L2/L3/L4 must read '-'.
#                                     This is the shape of the real 2026-08-28
#                                     finding: seventeen binutils down on one
#                                     missing library while gcc --version was
#                                     still green.
#   S3  the driver accepts a       -> NEG control fires, exit 2, REFUSED. If a
#       binutils -march spelling      driver takes `rlx4181` then -march is
#                                     being ignored and every per-arch number
#                                     is one column repeated.
#   S4  the link produces a        -> L2 FAIL. Checks that L2 READS the ELF
#       little-endian ELF             header instead of trusting the linker.
#   S5  `as` exits 0 and emits     -> L3 FAIL. This is the case that separates
#       the wrong bytes               "accepted the mnemonic" from "emitted the
#                                     instruction".
#   S6  no MIPS emulator           -> L4 reads `noqemu`, never `ok`, AND the
#                                     tool exits 4 rather than 0. Not reached is
#                                     a third answer beside pass and fail, and it
#                                     had the same exit code as pass until the
#                                     2026-08-28 review pointed at it.
#   S7  the emulator prints the    -> L4 FAIL. The program linked and ran and
#       wrong answer                  computed the wrong number.
#   B   the real rsdk toolchains   -> L1..L4 all ok. Skipped where the vendor
#                                     toolchain is not on disk.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SMOKE="$HERE/tc-smoke.sh"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail=0; pass=0; skipped=0
ck () { if [ "$2" = "$3" ]; then printf '  ok     %-44s %s\n' "$1" "$3"; pass=$((pass+1))
        else printf '  FAIL   %-44s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }
sk () { printf '  skip   %-44s %s\n' "$1" "$2"; skipped=$((skipped+1)); }

# The 48 bytes tc-smoke requires from feat.S, and a wrong version of them,
# carried as base64. They were hex at first and that was a bug: bash `printf`
# with a NUL in the format truncates, so the stub emitted 132 bytes instead of
# 48 and every case downstream failed for a reason that had nothing to do with
# the thing being tested. base64 has no escape layer.
#   GOOD -> sha256 298d5f2a...  the bytes all three real rsdk releases emit
#   BAD  -> the same file with the `cache` word zeroed, so `as` succeeds and
#           emits something that is not the instruction
GOOD_B64='iKgAAJioAAOoiAAAuIgAA0yAAABMgAgAvJEAAAPgAAgAAAAAAAAAAAAAAAAAAAAA'
BAD_B64='iKgAAJioAAOoiAAAuIgAA0yAAABMgAgAAAAAAAPgAAgAAAAAAAAAAAAAAAAAAAAA'

# Build a stub toolchain. $1 dir, $2 knob:
#   good        everything works
#   deadas      mips-linux-as exits 1 with a loader-style message
#   loosemarch  the driver accepts a binutils -march spelling
#   littleend   readelf reports little endian
#   badbytes    as exits 0 and objcopy emits the wrong .text
mkstub () {
    local d="$1" knob="$2"
    mkdir -p "$d/bin"
    cat > "$d/bin/mips-linux-gcc" <<STUB
#!/usr/bin/env bash
knob="$knob"
STUB
    cat >> "$d/bin/mips-linux-gcc" <<'STUB'
out=""; want_o=0; march=""
for a in "$@"; do
    if [ "$want_o" = 1 ]; then out="$a"; want_o=0; continue; fi
    case "$a" in -o) want_o=1 ;; --version) echo "stub-gcc 0.0"; exit 0 ;;
                 -march=*) march="${a#-march=}" ;; esac
done
case "$march" in
    lx4180|rlx4181|rlx5281)
        if [ "$knob" != loosemarch ]; then echo "bad value ($march) for -march" >&2; exit 1; fi ;;
    4180|4181|5181|5280|5281|4281|"") ;;
    *) echo "bad value ($march) for -march" >&2; exit 1 ;;
esac
[ -n "$out" ] && printf 'STUBOUT\n' > "$out"
exit 0
STUB
    chmod +x "$d/bin/mips-linux-gcc"

    cat > "$d/bin/mips-linux-as" <<STUB
#!/usr/bin/env bash
knob="$knob"
STUB
    cat >> "$d/bin/mips-linux-as" <<'STUB'
if [ "$knob" = deadas ]; then
    echo "mips-linux-as: error while loading shared libraries: libz.so.1: cannot open shared object file" >&2
    exit 127
fi
out=""; want_o=0
for a in "$@"; do
    if [ "$want_o" = 1 ]; then out="$a"; want_o=0; continue; fi
    case "$a" in -o) want_o=1 ;; --version) echo "stub-as 0.0"; exit 0 ;; esac
done
[ -n "$out" ] && printf 'STUBOBJ\n' > "$out"
exit 0
STUB
    chmod +x "$d/bin/mips-linux-as"

    cat > "$d/bin/mips-linux-readelf" <<STUB
#!/usr/bin/env bash
knob="$knob"
STUB
    cat >> "$d/bin/mips-linux-readelf" <<'STUB'
case "${1:-}" in --version) echo "stub-readelf 0.0"; exit 0 ;; esac
if [ "$knob" = littleend ]; then echo "  Data: 2's complement, little endian"
else echo "  Data: 2's complement, big endian"; fi
echo "  Type: EXEC (Executable file)"
echo "  Machine: MIPS R3000"
exit 0
STUB
    chmod +x "$d/bin/mips-linux-readelf"

    cat > "$d/bin/mips-linux-objcopy" <<STUB
#!/usr/bin/env bash
knob="$knob"
GOOD_B64="$GOOD_B64"
BAD_B64="$BAD_B64"
STUB
    cat >> "$d/bin/mips-linux-objcopy" <<'STUB'
case "${1:-}" in --version) echo "stub-objcopy 0.0"; exit 0 ;; esac
dst=""
for a in "$@"; do dst="$a"; done
b="$GOOD_B64"; [ "$knob" = badbytes ] && b="$BAD_B64"
printf '%s' "$b" | base64 -d > "$dst"
exit 0
STUB
    chmod +x "$d/bin/mips-linux-objcopy"

    for p in ld ar ranlib nm objdump size strip; do
        printf '#!/usr/bin/env bash\ncase "${1:-}" in --version) echo "stub-%s 0.0"; exit 0;; esac\nexit 0\n' "$p" > "$d/bin/mips-linux-$p"
        chmod +x "$d/bin/mips-linux-$p"
    done
    ln -sf mips-linux-gcc "$d/bin/rsdk-linux-gcc"
}

# A stub emulator. $1 dir, $2 what it prints.
mkqemu () { printf '#!/usr/bin/env bash\necho "%s"\n' "$2" > "$1"; chmod +x "$1"; }
QOK="$T/qemu-ok"; mkqemu "$QOK" "rlxfw-smoke 338350"
QBAD="$T/qemu-bad"; mkqemu "$QBAD" "rlxfw-smoke 0"

# The cell in column `rung` of the first data row. The header is found by NAME,
# not by line number: the tool prints a title and a blank line first, and an awk
# that assumed "row 2 is the header" read the header back as the answer -- which
# is why every case below passed its exit code and failed its cell on the first
# run of this suite.
cell () { # output rung -> the cell in that column, first data row
    awk -v c="$2" 'seen && NF { print $(c+1); exit } /^TOOLCHAIN /{seen=1}' <<< "$1"
}


echo "=== S1: no toolchain -> exit 3, and no table row ==="
mkdir -p "$T/nope"        # exists, but holds no compiler driver
out="$("$SMOKE" --tc "$T/nope" 2>/dev/null)"; rc=$?
ck "S1 exit 3"                    3 "$rc"
ck "S1 no toolchain row"          0 "$(printf '%s' "$out" | grep -c 'ok\|FAIL' || true)"
err="$("$SMOKE" --tc "$T/nope" 2>&1 >/dev/null)"
ck "S1 says why"                  1 "$(printf '%s' "$err" | grep -c 'SKIPPED' || true)"

echo
echo "=== S2: as will not start -> L1 FAIL, rungs above it not reached ==="
mkstub "$T/deadas" deadas
out="$("$SMOKE" --tc "$T/deadas" --qemu "$QOK" 2>&1)"; rc=$?
ck "S2 exit 1"                    1 "$rc"
ck "S2 L1 FAIL"                   FAIL "$(cell "$out" 1)"
ck "S2 L2 not reached"            "-"  "$(cell "$out" 2)"
ck "S2 L4 not reached"            "-"  "$(cell "$out" 4)"
ck "S2 names the library"         1 "$(printf '%s' "$out" | grep -c 'libz' || true)"

echo
echo "=== S3: driver accepts a binutils -march spelling -> NEG fires, REFUSED ==="
mkstub "$T/loose" loosemarch
out="$("$SMOKE" --tc "$T/loose" --qemu "$QOK" 2>&1)"; rc=$?
ck "S3 exit 2 (refused)"          2 "$rc"
# three spellings offered, this stub takes all three, so three lines
ck "S3 says -march is ignored"    3 "$(printf '%s' "$out" | grep -c 'being ignored' || true)"
ck "S3 certifies nothing"         1 "$(printf '%s' "$out" | grep -c 'nothing certified' || true)"

echo
echo "=== S4: link produces a little-endian ELF -> L2 FAIL ==="
mkstub "$T/le" littleend
out="$("$SMOKE" --tc "$T/le" --qemu "$QOK" 2>&1)"; rc=$?
ck "S4 exit 1"                    1 "$rc"
ck "S4 L1 still ok"               ok "$(cell "$out" 1)"
ck "S4 L2 FAIL"                   FAIL "$(cell "$out" 2)"
# monotonicity, from outside the tool: the rungs above a FAILed one must read
# `-`, never `ok`. Until 2026-08-28 the POS control was a printf and this was
# asserted nowhere; a mutant that let them read ok kept the suite green.
ck "S4 L3 not reached"            "-"  "$(cell "$out" 3)"
ck "S4 L4 not reached"            "-"  "$(cell "$out" 4)"
ck "S4 POS control still holds"   1 "$(printf '%s' "$out" | grep -c 'ok    POS' || true)"
ck "S4 says not-big-endian"       1 "$(printf '%s' "$out" | grep -c 'not-big-endian' || true)"

echo
echo "=== S5: as exits 0 and emits the WRONG bytes -> L3 FAIL ==="
mkstub "$T/badb" badbytes
out="$("$SMOKE" --tc "$T/badb" --qemu "$QOK" 2>&1)"; rc=$?
ck "S5 exit 1"                    1 "$rc"
ck "S5 L2 still ok"               ok "$(cell "$out" 2)"
ck "S5 L3 FAIL"                   FAIL "$(cell "$out" 3)"
ck "S5 reports the sha it got"    1 "$(printf '%s' "$out" | grep -c 'text-sha' || true)"

echo
echo "=== S6/S7: the emulator rung ==="
mkstub "$T/good" good
out="$("$SMOKE" --tc "$T/good" --qemu "$T/no-such-qemu" 2>&1)"; rc=$?
ck "S6 L4 reads noqemu"           noqemu "$(cell "$out" 4)"
ck "S6 L4 is never ok"            0 "$(printf '%s' "$out" | grep -c 'ok *ok *ok *ok' || true)"
# The rung was NOT REACHED. That is neither a pass nor a failure, and until
# 2026-08-28 it exited 0 and printed the verdict that says every toolchain
# reached L4 -- the tool certifying a rung it never ran.
ck "S6 exit 4, not 0"             4 "$rc"
ck "S6 certifies nothing above L3" 0 "$(printf '%s' "$out" | grep -c 'every toolchain reached L4' || true)"
out="$("$SMOKE" --tc "$T/good" --qemu "$QBAD" 2>&1)"; rc=$?
ck "S7 exit 1"                    1 "$rc"
ck "S7 L3 still ok"               ok "$(cell "$out" 3)"
ck "S7 L4 FAIL"                   FAIL "$(cell "$out" 4)"
out="$("$SMOKE" --tc "$T/good" --qemu "$QOK" 2>&1)"; rc=$?
ck "S7 control: a good stub is 0" 0 "$rc"
ck "S7 control: L4 ok"            ok "$(cell "$out" 4)"

echo
echo "=== B: the real rsdk toolchains ==="
"$SMOKE" --quiet > "$T/real.txt" 2>"$T/ereal"; rc=$?
case "$rc" in
0)
    ck "B every toolchain reached L4" 0 "$rc"
    ck "B three releases, deduplicated" 3 "$(grep -c '^rsdk-' "$T/real.txt" || true)"
    ck "B no FAIL cell"               0 "$(grep -c 'FAIL' "$T/real.txt" || true)"
    ck "B the 4181 release reports cfg-march=4181" 1 \
       "$(grep -c '^rsdk-1.3.6-4181.*cfg-march=4181' "$T/real.txt" || true)"
    ck "B both 5281 releases report cfg-march=5281" 2 \
       "$(grep -c '^rsdk-.*-5281-.*cfg-march=5281' "$T/real.txt" || true)"
    ;;
3)
    sk "B the vendor toolchains" "5 cases: no rsdk under \$FWRE_WORK. S1 is the control that makes this a skip and not a zero"
    ;;
4)
    # A machine that HAS the toolchains but no MIPS emulator reaches L3 and
    # stops. That is not a failed toolchain and must not be scored as one.
    # tc-smoke exits 4 for exactly this. ⚠️ This arm was written as `1)` when the
    # noqemu path still exited 0-or-1, and the fix that made it exit 4 turned a
    # false green into a false RED -- the run fell through to the default arm and
    # printed FAIL. Caught by the same review that asked for the fix.
    sk "B qemu-mips" "5 cases: the toolchains are here and a MIPS user-mode emulator is not, so L4 was not reached. S6 is the control that makes this a skip and not a pass"
    ;;
*)
    printf '  FAIL   %-44s tc-smoke exited %s, which is neither 0 nor 3\n' "B (5 cases)" "$rc"
    sed 's/^/           /' "$T/ereal" | head -4
    fail=$((fail+1))
    ;;
esac

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skip line(s)\n' "$pass" "$fail" "$skipped"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skip line(s)\n' "$pass" "$skipped"
