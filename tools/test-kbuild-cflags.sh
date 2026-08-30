#!/usr/bin/env bash
# Does rlxfw-kbuild.sh's CFLAGS_KERNEL guard actually gate?   R3-9, 2026-08-30.
#
# WHY IT EXISTS.  量 2026-08-30: `quietm` -- the image that booted on the
# silicon -- could not be rebuilt from its own recorded configuration.  Same
# pinned drop, same `.config-built` to the line, same 599 translation units,
# same symbol set, and `.text` 2,444,228 against 2,427,448.  The whole
# difference was `-fno-if-conversion` (SPEC.md TC-25), the flag that takes
# `hazlint` from SEVEN load-use violations to ZERO -- and it lived nowhere
# except the operator's shell.  `config/rlxfw-cflags` declares it now and this
# suite is what says the declaration is load-bearing.
#
# WHERE THE GUARD SITS IS PART OF THE CLAIM.  It runs BEFORE the tree is staged
# and before the drop is checked for, so four of these five cases need no vendor
# material at all: a refusal that costs a 480 MB copy is a refusal nobody
# exercises.  C1 is the one that stages, and it stands down without a drop.
#
# Usage:  tools/test-kbuild-cflags.sh
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
K="$HERE/rlxfw-kbuild.sh"
CF="$REPO/config/rlxfw-cflags"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
DROP="$WORK/rebuild/src-vendor/rtl819x-toolchain"

pass=0; fail=0; skip=0
ck () {  # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-52s %s\n' "$1" "$2"; skip=$((skip+1)); }

[ -f "$CF" ] || { echo "no $CF" >&2; exit 3; }
[ -x "$K" ] || { echo "no $K" >&2; exit 3; }

# C4 and C5 move and rewrite the file under test.  A suite that leaves a
# declaration file damaged would be worse than no suite, so its digest is taken
# before anything touches it and asserted at the end -- byte for byte, rather
# than a grep for a string the file's own comment block also contains, which is
# what the first version did and what it reported 2 for.
CF_SHA0="$(sha256sum "$CF" | cut -d' ' -f1)"

# 🔴 C1's label is written ONCE and used three times: to print the case, to
# print the skip, and to assert against `tools/ci-expected.tsv`.  It is a
# variable because the first version spelled it one way in the suite and
# another way in the table, and CI went red on
# `UNEXPECTED-SKIP 'C1 the declared flags reach the build'`.
#
# WHY THE BENCH COULD NOT SEE THAT.  `ci-census` matches a printed skip label
# against the table's allowed-skip column; on this machine `$FWRE_WORK` holds
# the GPL drop, so C1 RUNS and prints no skip line at all, so the label is never
# compared.  A pre-push census here is structurally blind to a mismatch in a
# skip that only happens on a runner.  `C7` closes that: it reads the table.
C1_LABEL="C1 the declared flags reach the build"
EXPECTED_TSV="$HERE/ci-expected.tsv"

# A cell name no build will ever use, so a stray stage is obvious.
run () {  # args... -> sets $rc and $out
    out="$(bash "$K" "$@" --target none 2>&1)"; rc=$?
}

echo "=== the guard, above the stage: four cases that need no vendor drop ==="

# C2 -- an explicitly EMPTY --cflags-kernel is NOT the same request as
# --no-cflags.  The first version of the guard tested `[ -n "$CFLAGS_KERNEL" ]`
# and could not tell them apart, so `--cflags-kernel ""` fell through to the
# declared file: the one request this file exists to refuse.  Same distinction
# console-capture's N20 pins.
run gcf-c2 --cflags-kernel ""
ck "C2 an empty --cflags-kernel is refused"  3 "$rc"
ck "C2 and it names --no-cflags in the refusal" 1 \
   "$(printf '%s\n' "$out" | grep -c -- '--no-cflags')"

# C4 -- the declaration file missing is a REFUSAL, not a silent empty build.
mv "$CF" "$CF.t4"
run gcf-c4
mv "$CF.t4" "$CF"
ck "C4 no declaration file -> refuse"        3 "$rc"
ck "C4 and it says what an empty one costs"  1 \
   "$(printf '%s\n' "$out" | grep -c 'SEVEN load-use')"

# C5 -- a declaration holding only comments is refused too.  "No flags" has to
# be asked for by name and can never be arrived at.
cp "$CF" "$CF.t5"
printf '# only a comment\n\n' > "$CF"
run gcf-c5
cp "$CF.t5" "$CF"; rm -f "$CF.t5"
ck "C5 a comments-only declaration -> refuse" 3 "$rc"

# C6 -- --no-cflags is ACCEPTED and says so, which is what stops C2/C4/C5 being
# passed by a guard that refuses everything.  It reaches the drop check, so
# without a drop it exits 3 with a DIFFERENT message; the assertion is on the
# message the guard printed, not on the exit code.
run gcf-c6 --no-cflags
ck "C6 --no-cflags is accepted by the guard"  1 \
   "$(printf '%s\n' "$out" | grep -c 'deliberately empty')"
ck "C6 and it did NOT read the declaration"   0 \
   "$(printf '%s\n' "$out" | grep -c 'rlxfw-cflags')"

echo
echo "=== C1: the declared file is what a real build uses ==="
if [ -d "$DROP/linux-2.6.30" ]; then
    run gcf-c1 --config "$DROP/boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW"
    ck "$C1_LABEL"  1 \
       "$(printf '%s\n' "$out" | grep -c 'CFLAGS_KERNEL=\[-fno-if-conversion\]')"
    rm -rf "$WORK/rebuild/r3-4/cells/gcf-c1"
else
    sk "$C1_LABEL" "no GPL drop under \$FWRE_WORK"
fi

echo
echo "=== C7: the skip this suite prints is the skip the census expects ==="
# 🔴 This case exists because CI went red on
# `UNEXPECTED-SKIP 'C1 the declared flags reach the build'` while the same
# suite was 9/9 green here. `ci-census` counts a skip only when its printed
# label appears in the allowed-skip column of `tools/ci-expected.tsv`; a label
# that does not match is counted as a case that vanished, and the build fails
# on arithmetic that never mentions the label.
#
# On this machine C1 RUNS -- `$FWRE_WORK` holds the GPL drop -- so no skip line
# is printed and no label is ever compared. The bench is structurally blind to
# this class. Reading the table is the only check that works in both
# configurations, and it needs no vendor material.
if [ -f "$EXPECTED_TSV" ]; then
    tsv_skip="$(awk -F'\t' '$1 == "test-kbuild-cflags" { print $3 }' "$EXPECTED_TSV")"
    ck "C7 ci-expected.tsv's allowed skip is this suite's label" \
       "$C1_LABEL" "$tsv_skip"
else
    sk "$C1_LABEL" "no ci-expected.tsv beside this suite"
fi

echo
echo "=== the declaration is back, byte for byte ==="
ck "the file under test is unmodified" "$CF_SHA0" "$(sha256sum "$CF" | cut -d' ' -f1)"

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
