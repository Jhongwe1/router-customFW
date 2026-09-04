#!/usr/bin/env bash
# Do rlxfw-kbuild.sh's DECLARED-INPUT guards actually gate?
#   R3-9, 2026-08-30 (CFLAGS_KERNEL) and P4a, 2026-09-01 (the build stamp).
#
# ⚠️ The file's NAME says cflags and its contents are wider now. Renaming
# it would move this suite's row in ci-expected.tsv AND its allowed-skip label
# in ci.yml, and an allowed-skip label edited in one place and not the other is
# exactly what put CI red on 2026-08-31 (run 33410057391, three commits). The
# rename is carried forward next to the config/host-compat one, which has the
# same shape and the same reason for not being done in the same session as the
# change that widened it.
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

# C8 -- --id-scope, R5-0 2026-09-02.  It is here rather than beside the flag
# because the property being tested is the one this file exists for: a refusal
# must fire ABOVE the stage.  The flag's first version validated its value in
# the `case` beside the make invocation, so `--id-scope typo` would have
# staged 480 MB, run oldconfig and built 592 objects before saying the word was
# wrong -- and rlxfw-kbuild.sh's own comment says why that is the wrong place.
run gcf-c8 --id-scope typo
ck "C8 an unknown --id-scope is refused"      3 "$rc"
ck "C8 and it names the two allowed values"   1 \
   "$(printf '%s\n' "$out" | grep -c 'global|main')"
# The one that makes it a guard ABOVE the stage rather than a message: the
# refusal must arrive before the CFLAGS declaration is even read, which is the
# first thing below it.
ck "C8 and it fires before the cflags block"  0 \
   "$(printf '%s\n' "$out" | grep -c 'CFLAGS_KERNEL=')"
# C8b -- the negative control.  A guard that refuses every value would pass
# C8, so an ALLOWED value must get past it; --dry-run stops before staging so
# this costs nothing and needs no drop.
run gcf-c8b --id-scope main --variant quiet --dry-run
ck "C8b an allowed --id-scope is accepted"    0 "$rc"
ck "C8b and it reached the dry-run report"    1 \
   "$(printf '%s\n' "$out" | grep -c 'nothing staged and nothing built')"

echo
echo "=== the build stamp, P4a 2026-09-01: same guard shape, same reasons ==="
# 量 2026-09-01: two back-to-back builds of one tree differ in 84 of 3,935,472
# bytes, all of them clock readings -- 6 the kernel's UTS_VERSION and 78
# gen_init_cpio's.  config/rlxfw-build-stamp declares one epoch for both.  These
# run through --dry-run, which exits 0 above the stage, so none of them pays for
# a 480 MB copy.
SF="$REPO/config/rlxfw-build-stamp"
SF_SHA0="$(sha256sum "$SF" | cut -d' ' -f1)"

# S1 -- the declaration missing is a REFUSAL, not a silent fall-back to the
# clock.  Same distinction as C4: the difference between an unreproducible
# build and a reproducible one has to be asked for by name.
mv "$SF" "$SF.s1"
run gcf-s1 --dry-run
mv "$SF.s1" "$SF"
ck "S1 no stamp declaration -> refuse"         3 "$rc"
ck "S1 and it names --no-stamp"                1 \
   "$(printf '%s\n' "$out" | grep -c -- '--no-stamp')"

# S2 -- comments only is refused too, and refused with a DIFFERENT sentence
# from S1: "declares no epoch" is not "there is no file".
cp "$SF" "$SF.s2"
printf '# only a comment\n\n' > "$SF"
run gcf-s2 --dry-run
cp "$SF.s2" "$SF"; rm -f "$SF.s2"
ck "S2 a comments-only declaration -> refuse"  3 "$rc"
ck "S2 and it says that is not --no-stamp"     1 \
   "$(printf '%s\n' "$out" | grep -c 'not the same')"

# S3 -- --no-stamp is ACCEPTED, which is what stops S1/S2 being passed by a
# guard that refuses everything, and it leaves the stamp EMPTY rather than
# quietly substituting one.
run gcf-s3 --no-stamp --variant quiet --dry-run
ck "S3 --no-stamp is accepted"                 0 "$rc"
ck "S3 and it says the clock is deliberate"    1 \
   "$(printf '%s\n' "$out" | grep -c 'wall clock, deliberately')"
ck "S3 and the stamp is empty, not substituted" 1 \
   "$(printf '%s\n' "$out" | grep -c 'stamp= \[\]')"

# S4 -- the declared epoch is read.
run gcf-s4 --variant quiet --dry-run
ck "S4 the declared epoch is read"             1 \
   "$(printf '%s\n' "$out" | grep -c 'stamp=1788220800')"

# 🔴 S5. THE FIRST VERSION OF THIS CASE COULD NOT FAIL, and it was caught by
# measuring the two variables it varied rather than by running it.  It compared
# the driver under TZ=Asia/Taipei against TZ=UTC and asserted they matched.
# 量 2026-09-01:
#
#   date    -d @1788220800  ->  Tue Sep  1 08:00:00 CST 2026
#   date -u -d @1788220800  ->  Tue Sep  1 00:00:00 UTC 2026
#   TZ=Asia/Taipei date -u  ->  Tue Sep  1 00:00:00 UTC 2026   <- TZ does nothing
#   LC_ALL=zh_TW.UTF-8      ->  identical; `locale -a` on this host is C,
#                               C.utf8 and POSIX and nothing else
#
# So `-u` is what makes the rendering timezone-independent, `TZ=UTC` in the
# driver is belt-and-braces on top of it, and the locale cannot be varied here
# at all.  A case that varies two things neither of which can move the output
# is green for the same reason an empty probe list is green.
#
# S5a is the real one: the stamp the driver prints must be the UTC rendering
# and must NOT be the local one.  Drop `-u` from the driver and it goes red.
E=1788220800
UTC_RENDER="$(date -u -d "@$E")"
run gcf-s5 --variant quiet --dry-run
DRIVER_RENDER="$(printf '%s\n' "$out" | sed -n 's/.*stamp=[0-9]* \[\([^]]*\)\].*/\1/p')"
ck "S5a the driver renders the UTC form"       "$UTC_RENDER" "$DRIVER_RENDER"

# 🔴 S5b's FIRST version skipped when the host's own TZ was already UTC, and
# that is how CI went red on run 33424495422: on this desk TZ is +0800 so the
# case RAN and printed no skip line, so its label was never compared against
# ci-expected.tsv -- structurally the same blindness that put three commits red
# on 2026-08-31, one tool over. A case that only runs where it was written is
# worse than no case.
#
# So it does not depend on the host's zone at all: it runs the DRIVER under a
# pinned non-UTC zone and requires the same string out. If the driver stopped
# pinning TZ *and* stopped passing -u, this goes red on any host, UTC included.
# ⚠️ Nothing can distinguish losing ONLY `-u` from losing only `TZ=UTC`,
# because either one alone still produces UTC. They are belt-and-braces by
# design, S5c is the assertion that both are present, and saying which case
# covers which half is the point of writing all three down.
o_tz="$(TZ=Asia/Taipei LC_ALL=C bash "$K" gcf-s5b --variant quiet --dry-run --target none 2>&1 \
        | sed -n 's/.*stamp=[0-9]* \[\([^]]*\)\].*/\1/p')"
ck "S5b a non-UTC TZ does not move the rendering" "$UTC_RENDER" "$o_tz"

# 🔴 S5c is a SOURCE assertion and is weaker than the two above, and that is
# stated rather than hidden.  `date`'s default format comes from the locale's
# D_T_FMT, so LC_ALL=C is load-bearing on a host that has another locale
# installed -- and this host has none, so no run-time case here can distinguish
# a driver that pins it from one that does not.  This is what is left.
ck "S5c the driver pins LC_ALL and TZ in the rendering" 1 \
   "$(grep -c 'LC_ALL=C TZ=UTC date -u -d' "$K")"

# S6 -- S1 and S2 move and rewrite the declaration.  Byte for byte at the end,
# for the reason C4/C5's digest check already gives.
ck "S6 the stamp declaration is byte-identical" "$SF_SHA0" \
   "$(sha256sum "$SF" | cut -d' ' -f1)"

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
echo "=== C8-C11: the build manifest (RECIPE-1, 2026-09-04) ==="
# WHY.  RLXFW-ID0 is a digest over config/ and NOTHING else, so `--config` and
# `--initramfs` -- the two inputs that decide what the image IS -- are outside
# it.  量 2026-09-04: `r51quiet` and `r51loud` both compile 229d2983 from
# different .config files and produce different vmlinux.  write_manifest is the
# provenance record that closes that; `looprun --image-sha256` is the gate.
#
# The function is EXTRACTED and sourced rather than exercised through a build,
# because a build is 35 s and a guard that costs 35 s is a guard nobody runs --
# the same reason C2-C6 above sit above the stage.
MTMP="$(mktemp -d)"
sed -n '/^write_manifest() {/,/^}$/p' "$K" > "$MTMP/fn.sh"
ck "C8 write_manifest is extractable as one function" \
   "1" "$(grep -c '^}$' "$MTMP/fn.sh")"

printf 'INSTALLED-BYTES\n'  > "$MTMP/c.config-installed"
printf 'BUILT-BYTES-DIFFER\n' > "$MTMP/c.config-built"
printf 'spec\n'             > "$MTMP/c.initramfs.spec"
printf 'aaaa\n'             > "$MTMP/c.initramfs.spec.sha256"
printf 'ELF\n'              > "$MTMP/vm"
run_manifest () {           # run_manifest -> writes $MTMP/c.manifest
    (
        # shellcheck disable=SC1090
        log="$MTMP/c"; CELL=cell; RECIPE_ID=deadbeef
        CONFIG="${1:-/some/path}"; INITRAMFS="${2:-}"
        CFLAGS_KERNEL=-fno-if-conversion; ID_SCOPE=global; OLDCONFIG=devnull
        TARGET=vmlinux; JOBS=4; KEEP=0; STAMP_EPOCH=1788220800
        N_PATCHES="${3:-4}"; N_MARKS="${4:-17}"; DROP=/x/rtl819x-toolchain
        . "$MTMP/fn.sh"
        write_manifest "$MTMP/vm" > /dev/null
    )
}
field () { awk -F'\t' -v k="$1" '$1 == k { print $2 }' "$MTMP/c.manifest"; }

run_manifest
INST_SHA="$(sha256sum "$MTMP/c.config-installed" | cut -d' ' -f1)"
BUILT_SHA="$(sha256sum "$MTMP/c.config-built" | cut -d' ' -f1)"
ck "C9 config_sha256 is the digest of config-INSTALLED" \
   "$INST_SHA" "$(field config_sha256)"
# 🔴 C10 is the case this whole block exists for.  量 2026-09-04: two builds
# whose images are BYTE-IDENTICAL have different `.config-built` digests,
# because kconfig writes a wall-clock comment on line 4.  A manifest keyed on
# the post-oldconfig file would report every rebuild as a different recipe.
ck "C10 and NOT of config-built, which carries a wall-clock comment" \
   "differ" "$( [ "$(field config_sha256)" = "$BUILT_SHA" ] && echo same || echo differ )"

# C11: the positive control.  A digest that never moves is not a digest.
printf 'INSTALLED-BYTES-CHANGED\n' > "$MTMP/c.config-installed"
run_manifest
ck "C11 one byte of the installed .config moves the digest" \
   "moved" "$( [ "$(field config_sha256)" = "$INST_SHA" ] && echo same || echo moved )"

# C12: `napplied` had TWO writers in this driver -- the host-compat loop and the
# marks block -- and the second shadowed the first.  Nothing read it until the
# manifest did.  Distinct values in, distinct values out.
run_manifest /p "" 3 11
ck "C12 host_compat_patches and marks are separate counters" \
   "3/11" "$(field host_compat_patches)/$(field marks)"
ck "C13 no --initramfs records a dash, not an empty field" \
   "-/-" "$(field initramfs_sha256)/$(field initramfs_source)"
run_manifest /p "$MTMP/c.initramfs.spec" 3 11
ck "C14 and with one, the digest comes from the driver's own .sha256 file" \
   "aaaa" "$(field initramfs_sha256)"
rm -rf "$MTMP"

echo
echo "=== the declaration is back, byte for byte ==="
ck "the file under test is unmodified" "$CF_SHA0" "$(sha256sum "$CF" | cut -d' ' -f1)"
# ---------------------------------------------------------------- CFG-1
# V1..V5 -- the guard that made the five edits above necessary.
#
# Until 2026-09-04 a run with no --config silently used the BARE board
# template, and 量 that is 15 CONFIG symbols away from what every rlxfw image
# has actually been built from -- BLK_DEV_INITRD, INITRAMFS_*, MTD_CHAR,
# CMDLINE among them, every one of them a row in config/rlxfw-kernel.delta.
# So the .config is DERIVED now, and the variant has to be chosen.
#
# 🔴 There is no default. The delta declares `quiet` and `loud`, and today NO
# row is tagged @quiet -- so omitting the flag and passing `quiet` produce the
# same bytes, and a default would be right by coincidence. kconfig-delta's own
# C24 refuses an undeclared variant one layer down for the same reason.
run gcf-v1 --dry-run
ck "V1 neither --config nor --variant is REFUSED"   3 "$rc"
ck "V1b and it names both flags"                    1 \
   "$(printf '%s\n' "$out" | grep -c 'no --config and no --variant')"

run gcf-v2 --config /dev/null --variant quiet --dry-run
ck "V2 --config AND --variant is REFUSED"           3 "$rc"
ck "V2b and it says why: two sources for one file"  1 \
   "$(printf '%s\n' "$out" | grep -c 'two sources for one file')"

run gcf-v3 --variant quiett --dry-run
ck "V3 an undeclared variant is REFUSED"            3 "$rc"
ck "V3b and it names the two that are declared"     1 \
   "$(printf '%s\n' "$out" | grep -c "unknown --variant 'quiett'")"

# V4/V5 -- the negative controls. A guard that refused everything would pass
# V1..V3 and prove nothing, so BOTH accepted forms must get through.
run gcf-v4 --variant quiet --dry-run
ck "V4 --variant quiet is accepted"                 0 "$rc"
run gcf-v5 --variant loud --dry-run
ck "V5 --variant loud is accepted too"              0 "$rc"
run gcf-v6 --config /dev/null --dry-run
ck "V6 --config alone is accepted"                  0 "$rc"


echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
