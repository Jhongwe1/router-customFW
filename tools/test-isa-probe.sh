#!/usr/bin/env bash
# Controls for tools/isa-probe.sh.
#
# The instrument's whole value is that a `.` means "the assembler was asked and
# said no". Everything that could make a `.` mean something else is a case here,
# and each one is exercised with a stub assembler so that it runs on a machine
# with no vendor toolchain at all.
#
#   A1  no assembler        -> exit 3, and NOT ONE table row on stdout.
#                              This is the case that matters most: the failure
#                              this repository keeps meeting is a tool that
#                              reports when it cannot see.
#   A2  stub accepts all    -> NEG daddu passes, so -march is being ignored ->
#                              exit 2, refused.
#   A3  stub rejects all    -> POS addu fails -> exit 2, refused.
#   A4  stub with a known   -> the printed table must be exactly what the stub
#       accept-list            was told to accept. Proves the rows come from the
#                              assembler and are not baked into the script.
#   A5  --archs is honoured -> one arch in, one column out.
#   B*  the real rsdk       -> each row must match the table measured on
#                              2026-08-27 and recorded in
#                              notes/vendor-kernel-isa.md §6. Skipped where the
#                              vendor toolchain is not on disk.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROBE="$HERE/isa-probe.sh"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail=0; pass=0; skipped=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-34s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-34s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-34s %s\n' "$1" "$2"; skipped=$((skipped+1)); }

# A stub assembler. $STUB_OK is a space-separated list of mnemonics it accepts;
# anything else it rejects. $STUB_DEAD_ARCH, if set, makes it reject EVERYTHING
# for that one -march, which is how A6 builds a column that cannot assemble.
#
# ⚠️ The comment here used to claim the stub "records that it was called, so a
# case can tell rejected from never asked". It did not, and no case used it.
# What actually distinguishes the two is A4/A5's accept-list, which now covers
# every row -- see A4's note.
mkstub () { # path  accept-list
    cat > "$1" <<'STUB'
#!/usr/bin/env bash
src=""; arch=""
for a in "$@"; do
    case "$a" in -march=*) arch="${a#-march=}" ;; -*|*.o) ;; *) src="$a" ;; esac
done
if [ -n "${STUB_DEAD_ARCH:-}" ] && [ "$arch" = "$STUB_DEAD_ARCH" ]; then exit 1; fi
m="$(awk 'NF && $1 !~ /^\./ {print $1; exit}' "$src")"
for ok in $STUB_OK; do [ "$m" = "$ok" ] && exit 0; done
exit 1
STUB
    chmod +x "$1"
}

echo "=== A1: no assembler -> exit 3, and no table ==="
out="$("$PROBE" --as "$T/does-not-exist" 2>/dev/null)"; rc=$?
ck "A1 exit code"            3 "$rc"
ck "A1 rows printed"         0 "$(printf '%s' "$out" | grep -cE '^(lwl|ll|cache|movz) ' || true)"
err="$("$PROBE" --as "$T/does-not-exist" 2>&1 >/dev/null)"
ck "A1 says why"             1 "$(printf '%s' "$err" | grep -c 'SKIPPED' || true)"

echo
echo "=== A2: a stub that accepts everything -> NEG daddu fires -> refused ==="
mkstub "$T/as-all" ""
cat > "$T/as-all" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
chmod +x "$T/as-all"
out="$("$PROBE" --as "$T/as-all" 2>"$T/e2")"; rc=$?
ck "A2 exit code"            2 "$rc"
ck "A2 names the NEG control" 1 "$(grep -c 'NEG daddu ACCEPTED' "$T/e2" || true)"
ck "A2 prints no table"      0 "$(printf '%s' "$out" | grep -cE '^lwl ' || true)"

echo
echo "=== A3: a stub that rejects everything -> POS addu fires -> refused ==="
cat > "$T/as-none" <<'STUB'
#!/usr/bin/env bash
exit 1
STUB
chmod +x "$T/as-none"
out="$("$PROBE" --as "$T/as-none" 2>"$T/e3")"; rc=$?
ck "A3 exit code"            2 "$rc"
ck "A3 names the POS control" 1 "$(grep -c 'POS addu rejected' "$T/e3" || true)"
ck "A3 prints no table"      0 "$(printf '%s' "$out" | grep -cE '^lwl ' || true)"

echo
echo "=== A4: a stub with a known accept-list -> the table is that list ==="
# 2026-08-28: `pref`, `madd`, `rdhwr` and `lwc3` were added to the accept-list
# out of the adversarial review. They are all-dots in every column of the real
# table, and the first version of A4 excluded them -- so three published rows
# could be hardcoded to `.` without the assembler ever being asked, and the
# suite stayed 40/40. A suite with no positive control on a row cannot certify
# that row's zeros.
mkstub "$T/as-known"
export STUB_OK="addu lwl lwr cache movz pref madd rdhwr lwc3"
out="$("$PROBE" --as "$T/as-known" --archs "rlx4181" --quiet 2>/dev/null)"; rc=$?
ck "A4 exit code"            0 "$rc"
ck "A4 lwl accepted"    "lwl y" "$(printf '%s\n' "$out" | awk '$1=="lwl"{print $1, $2}')"
ck "A4 lwr accepted"    "lwr y" "$(printf '%s\n' "$out" | awk '$1=="lwr"{print $1, $2}')"
ck "A4 swl rejected"    "swl ." "$(printf '%s\n' "$out" | awk '$1=="swl"{print $1, $2}')"
ck "A4 ll  rejected"    "ll ."  "$(printf '%s\n' "$out" | awk '$1=="ll"{print $1, $2}')"
ck "A4 cache accepted"  "cache y" "$(printf '%s\n' "$out" | awk '$1=="cache"{print $1, $2}')"
ck "A4 movz accepted"   "movz y" "$(printf '%s\n' "$out" | awk '$1=="movz"{print $1, $2}')"
ck "A4 movn rejected"   "movn ." "$(printf '%s\n' "$out" | awk '$1=="movn"{print $1, $2}')"
# The four rows that are all-dots in the real table, asserted ACCEPTING here so
# that "asked and refused" is distinguishable from "never asked".
ck "A4 pref accepted"   "pref y"  "$(printf '%s\n' "$out" | awk '$1=="pref"{print $1, $2}')"
ck "A4 madd accepted"   "madd y"  "$(printf '%s\n' "$out" | awk '$1=="madd"{print $1, $2}')"
ck "A4 rdhwr accepted"  "rdhwr y" "$(printf '%s\n' "$out" | awk '$1=="rdhwr"{print $1, $2}')"
ck "A4 lwc3 accepted"   "lwc3 y"  "$(printf '%s\n' "$out" | awk '$1=="lwc3"{print $1, $2}')"
ck "A4 row count"           20 "$(printf '%s\n' "$out" | grep -c . || true)"
unset STUB_OK

echo
echo "=== A5: --archs is honoured ==="
export STUB_OK="addu"
one="$("$PROBE" --as "$T/as-known" --archs "rlx4181" --quiet 2>/dev/null | awk '$1=="lwl"{print NF}')"
three="$("$PROBE" --as "$T/as-known" --archs "rlx4181 mips1 mips2" --quiet 2>/dev/null | awk '$1=="lwl"{print NF}')"
ck "A5 one arch -> 2 fields"  2 "$one"
ck "A5 three archs -> 4 fields" 4 "$three"
unset STUB_OK

echo
echo "=== A6: one dead column must refuse the whole table, not print dots ==="
# Out of the adversarial review. Running the POS/NEG controls on the first
# column only passed 40/40, and the mutant then printed the certification line
# "POS addu accepted in all columns" over an rlx5281 column that could not
# assemble at all -- twenty dots, exit 0. A2/A3's accept-all and reject-all
# stubs cannot see that, because they break every column at once.
mkstub "$T/as-dead"
export STUB_OK="addu lwl lwr cache movz"
export STUB_DEAD_ARCH="rlx5281"
out="$("$PROBE" --as "$T/as-dead" --archs "rlx4181 rlx5281 mips1" 2>"$T/e6")"; rc=$?
ck "A6 exit code"                   2 "$rc"
ck "A6 names the dead column"       1 "$(grep -c 'POS addu rejected by:.*rlx5281' "$T/e6" || true)"
ck "A6 does NOT name a live one"    0 "$(grep -c 'POS addu rejected by:.*rlx4181' "$T/e6" || true)"
ck "A6 prints no table"             0 "$(printf '%s' "$out" | grep -cE '^lwl ' || true)"
unset STUB_OK STUB_DEAD_ARCH

echo
echo "=== B: the real rsdk assembler, against the table of 2026-08-27 ==="
# notes/vendor-kernel-isa.md §6. Columns: lx4180 rlx4181 rlx5181 lx5280
# rlx5281 rlx4281 mips1 mips2.
read -r -d '' EXPECT <<'TBL' || true
lwl   y y y y y y y y
lwr   y y y y y y y y
swl   y y y y y y y y
swr   y y y y y y y y
ll    . y y . y y . y
sc    . y y . y y . y
sync  . . . . y y . y
cache . y y . y y . .
pref  . . . . . . . .
mfc3  y y y y y y y y
mtc3  y y y y y y y y
lwc3  y y y y y y y y
movz  . y y y y y . .
movn  . y y y y y . .
beql  . . . . . . . y
madd  . . . . . . . .
rdhwr . . . . . . . .
mfc1  y y y y y y y y
lwc1  y y y y y y y y
jalx  y y y y y y y y
TBL

# Branch on the EXIT CODE, not on truthiness. 3 is "no assembler" and is the
# only thing that may become a skip; 2 is REFUSED -- a toolchain that is present
# but whose -march is being ignored, which is precisely what the NEG control
# exists to catch. The first version of this branch turned that into "no working
# rsdk assembler", and the census then scored it as the expected skip.
"$PROBE" --quiet > "$T/real.txt" 2>"$T/ereal"; rc=$?
case "$rc" in
0)
    while read -r name rest; do
        [ -z "$name" ] && continue
        got="$(awk -v k="$name" '$1==k {$1=""; print}' "$T/real.txt" | tr -s ' ' | sed 's/^ //;s/ $//')"
        want="$(printf '%s' "$rest" | tr -s ' ' | sed 's/^ //;s/ $//')"
        ck "B $name" "$want" "$got"
    done <<< "$EXPECT"
    ;;
3)
    # The label is what `tools/ci-expected.tsv` keys on, and it has to match the
    # row there exactly or the census reports UNEXPECTED-SKIP -- which is how
    # this line got its name rather than the one it had first.
    sk "the vendor toolchains" "20 rows: no working rsdk assembler under \$FWRE_WORK. A1 is the control that makes this a skip and not a zero"
    ;;
*)
    printf '  FAIL   %-34s isa-probe exited %s, which is neither 0 (table) nor 3 (no assembler)\n' \
        "B (20 rows)" "$rc"
    sed 's/^/           /' "$T/ereal" | head -4
    fail=$((fail+1))
    ;;
esac

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skip line(s)\n' "$pass" "$fail" "$skipped"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skip line(s)\n' "$pass" "$skipped"
