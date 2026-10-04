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
# 🔄 2026-09-23 (P2-2, CFG-3 / TC-i): the driver now runs `kconfig-delta check`
# and `rlxfw-marks verify` after every build and fails one that is not green.
# A1-A10 are the declared --absent inputs, refused above the stage; G1-G8 the
# rule that turns a tool's exit status and RESULT line into a verdict; R0-R8
# the two gates with the real tools on synthetic inputs, down to the line
# looprun's S2 reads; I1-I10 the initramfs recorded by CONTENT, not by spec
# text.  All of them run anywhere bash and python3 do.
# 🔄 2026-10-05 (R8b, FW-228): X1-X12d, `--expect-present ROW-ID` -- its
# refusals above the stage, and the four cells of its truth table through the
# gate, mainline and armed, with and without the flag.  Same: no drop needed.
# 🔄 2026-10-05 (GPL-2.0 § 3, P4b): Y1-Y7b and Z0-Z7, `--recipient` -- the
# build a recipient of the corresponding source runs: the --absent rows the
# driver's UNIT_REFS names are not read, nothing else is skipped, and the
# verdict is `recipient` with exit 7, never green.  Same: no drop needed.
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
# Format 2 (CFG-3) writes `verdict` through overall_verdict, the one rule
# the exit status also comes from, so the harness sources both.
sed -n '/^overall_verdict() {/,/^}$/p' "$K" >> "$MTMP/fn.sh"

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
# C15 -- CFG-3's negative control at the level of the record: a manifest
# written when NO gate ran must not be able to read green.  Every verdict
# field is `-`, and `verdict` says not-green rather than inheriting a default.
ck "C15 no gate run -> the manifest's verdict is not-green, never green" \
   "not-green/-/-" \
   "$(field verdict)/$(field kconfig_check)/$(field marks_verify)"
ck "C16 the manifest says format 2" "2" \
   "$(awk -F'\t' '$1 == "rlxfw-build-manifest" { print $2 }' "$MTMP/c.manifest")"
rm -rf "$MTMP"

echo
echo "=== A1-A10: the declared --absent inputs, checked above the stage (CFG-3) ==="
# rlxfw-marks verify reads vendor kernels as --absent, and until P2-2 nothing
# declared which: the path lived in a runsheet row and in the operator's
# shell.  tools/rlxfw-marks-absent.tsv declares them by path, size and sha256,
# and the driver refuses a build whose references do not verify -- before the
# stage, so a refusal costs no 480 MB copy.
#
# Everything here is synthetic: a fake $FWRE_WORK holding two small files and
# a fake repository (RLXFW_REPO) holding the two declarations the guards above
# need plus a test declaration.  With no drop under the fake $FWRE_WORK, a run
# that gets PAST the guard stops at the next refusal, `no drop at` -- which is
# what A7 asserts, the way C6 asserts on a later message.
AT="$(mktemp -d)"
FW="$AT/work"; RP="$AT/repo"
mkdir -p "$FW/rebuild/ref" "$RP/config" "$RP/tools"
cp "$CF" "$RP/config/rlxfw-cflags"
cp "$SF" "$RP/config/rlxfw-build-stamp"
AD="$RP/tools/rlxfw-marks-absent.tsv"
printf 'the first synthetic vendor kernel\n' > "$FW/rebuild/ref/a.bin"
printf 'the second one, a different kernel\n' > "$FW/rebuild/ref/b.bin"
cp "$FW/rebuild/ref/a.bin" "$AT/a.orig"
SA="$(sha256sum "$FW/rebuild/ref/a.bin" | cut -d' ' -f1)"; NA="$(stat -c %s "$FW/rebuild/ref/a.bin")"
SB="$(sha256sum "$FW/rebuild/ref/b.bin" | cut -d' ' -f1)"; NB="$(stat -c %s "$FW/rebuild/ref/b.bin")"
good_decl () {
    printf '# a test declaration\n# name\trelpath\tbytes\tsha256\trole\n'
    printf 'ref-a\trebuild/ref/a.bin\t%s\t%s\tthe first\n' "$NA" "$SA"
    printf 'ref-b\trebuild/ref/b.bin\t%s\t%s\tthe second\n' "$NB" "$SB"
}
arun () {   # the real driver, the default --target, the fake inputs
    out="$(FWRE_WORK="$FW" RLXFW_REPO="$RP" bash "$K" "$@" 2>&1)"; rc=$?
}
has () { printf '%s\n' "$out" | grep -c -- "$1"; }

arun gcf-a1 --variant quiet
ck "A1 no declaration file -> refuse"                     3 "$rc"
ck "A1b and it says what the file is for"                 1 "$(has 'It declares the vendor kernels')"
ck "A1c and it stopped there, not at the drop check"      0 "$(has 'no drop at')"

good_decl > "$AD"; rm "$FW/rebuild/ref/b.bin"
arun gcf-a2 --variant quiet
ck "A2 a declared file missing -> refuse, naming it"      "3/1/0" "$rc/$(has 'ref-b: no file at \$FWRE_WORK/rebuild/ref/b.bin')/$(has 'no drop at')"
printf 'the second one, a different kernel\n' > "$FW/rebuild/ref/b.bin"

# One byte changed, same size: only the digest can see it.
printf 'The first synthetic vendor kernel\n' > "$FW/rebuild/ref/a.bin"
arun gcf-a3 --variant quiet
ck "A3 one byte changed, same size -> refuse on sha256"   "3/1/0" "$rc/$(has 'ref-a: .* has sha256 ')/$(has 'no drop at')"
printf 'the first synthetic vendor kernel\nX' > "$FW/rebuild/ref/a.bin"
arun gcf-a4 --variant quiet
ck "A4 another size -> refuse on bytes"                   "3/1/0" "$rc/$(has "is $((NA+1)) bytes, the declaration says $NA")/$(has 'no drop at')"
cp "$AT/a.orig" "$FW/rebuild/ref/a.bin"

printf '# only a comment\n\n' > "$AD"
arun gcf-a5 --variant quiet
ck "A5 a comments-only declaration -> refuse"             "3/1/0" "$rc/$(has 'declares no reference image')/$(has 'no drop at')"
{ good_decl; printf 'ref-c\trebuild/ref/c.bin\t12\t%s\n' "$SA"; } > "$AD"
arun gcf-a5b --variant quiet
ck "A5b a four-field row is refused, not skipped"         "3/1/0" "$rc/$(has '4 tab-separated field(s), expected 5')/$(has 'no drop at')"
# A5c -- relpaths are relative to $FWRE_WORK and stay under it.  An absolute
# path makes the declaration a fact about one desk, and `..` can reach into
# a tree the vendor-bytes rules keep this list out of.
{ good_decl
  printf 'ref-d\t/etc/hostname\t1\t%s\tabsolute\n' "$(printf '%064d' 1)"
  printf 'ref-e\trebuild/../../x.bin\t1\t%s\tclimbs\n' "$(printf '%064d' 2)"; } > "$AD"
arun gcf-a5c --variant quiet
ck "A5c an absolute or climbing relpath is refused"        "3/2/0" "$rc/$(has 'is not a path under')/$(has 'no drop at')"

# 🔴 P6 counted one kernel twice for a day (2026-08-28/29): two of its three
# "vendor artefacts" were the same bytes.  A second row with the first row's
# digest is refused, whatever it is called and wherever it lives.
cp "$FW/rebuild/ref/a.bin" "$FW/rebuild/ref/a-copy.bin"
{ good_decl; printf 'ref-c\trebuild/ref/a-copy.bin\t%s\t%s\ta copy\n' "$NA" "$SA"; } > "$AD"
arun gcf-a6 --variant quiet
ck "A6 two rows with one digest -> refuse"                "3/1/0" "$rc/$(has 'one artefact counted twice')/$(has 'no drop at')"

# A9 before A7 and A8, which do get past the guard: every refusal above fired
# before the driver created anything.
ck "A9 the refusals created nothing under \$FWRE_WORK"    "absent" \
   "$( [ -e "$FW/rebuild/r3-4" ] && echo present || echo absent )"

# A8 -- the placement control.  --target none builds nothing, so there is no
# gate to feed; the guard must not fire even with NO declaration at all.
rm -f "$AD"
arun gcf-a8 --variant quiet --target none
ck "A8 --target none with no declaration is not refused by this guard" \
   "3/0/1/1" "$rc/$(has 'It declares the vendor kernels')/$(has 'nothing is built, so no gate runs')/$(has 'no drop at')"

# A7 -- the positive control.  Without it A1-A6 would pass against a guard
# that refused everything.
good_decl > "$AD"
arun gcf-a7 --variant quiet
ck "A7 a declaration that verifies gets past the guard"   "1/1/0" \
   "$(has '--absent references verified')/$(has 'no drop at')/$(has 'problem(s) in the declared')"
ck "A7b and it names each reference by digest"            1 \
   "$(has "ref-a ${SA:0:16} ref-b ${SB:0:16}")"

# A10 -- the COMMITTED declaration parses to its two rows.  Under this empty
# $FWRE_WORK both are missing, so the refusal names both relpaths -- which is
# a statement about the file's shape that needs no vendor byte and runs on a
# runner.  Whether the files on the desk match it is what every real build
# now checks.
cp "$REPO/tools/rlxfw-marks-absent.tsv" "$AD"
arun gcf-a10 --variant quiet
ck "A10 the committed declaration: two rows, both named"  "3/2/1/1" \
   "$rc/$(has 'no file at')/$(has 'unit-kernel: no file at \$FWRE_WORK/rebuild/b4c-desk/vmlinux-rederived.bin')/$(has 'drop-kernel: no file at \$FWRE_WORK/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/vmlinux_img')"
rm -rf "$AT"

echo
echo "=== G1-G8: gate_verdict -- a verdict needs its RESULT line ==="
# Both gate tools exit 1 for red, and so does an uncaught Python exception.
# Status alone would file a crashed checker as a red build and a silent exit 0
# as green.
GT="$(mktemp -d)"
sed -n '/^gate_verdict() {/,/^}$/p' "$K" > "$GT/fn.sh"
gv () {   # gv <rc> <file> -> "<verdict>|<text>"
    ( . "$GT/fn.sh"; gate_verdict "$1" "$2" | tr '\t' '|' )
}
printf 'controls\n  ok  C1\n\nRESULT: \033[32mall 12 mark(s) present\033[0m\n' > "$GT/green"
ck "G1 rc 0 and one RESULT -> green, SGR escapes removed" \
   "green|RESULT: all 12 mark(s) present" "$(gv 0 "$GT/green")"
printf 'RESULT: \033[31mREFUSED\033[0m -- 2 undeclared, 0 mismatched, 0 not applied.\n' > "$GT/red"
ck "G2 rc 1 and one RESULT -> red" \
   "red|RESULT: REFUSED -- 2 undeclared, 0 mismatched, 0 not applied." "$(gv 1 "$GT/red")"
printf 'kconfig-delta: --baseline x hashes 1234 and the delta declares 5678\n' > "$GT/die"
ck "G3 rc 3 and no RESULT -> refused, with the tool's last line" \
   "refused|0 RESULT line(s) at rc=3; last line: kconfig-delta: --baseline x hashes 1234 and the delta declares 5678" \
   "$(gv 3 "$GT/die")"
printf 'Traceback (most recent call last):\n  File "x", line 1\nFileNotFoundError: [Errno 2] No such file\n' > "$GT/tb"
ck "G4 rc 1 with no RESULT (a traceback) -> refused, NOT red" \
   "refused" "$(gv 1 "$GT/tb" | cut -d'|' -f1)"
printf 'said nothing\n' > "$GT/silent"
ck "G5 rc 0 with no RESULT -> refused, NOT green" \
   "refused" "$(gv 0 "$GT/silent" | cut -d'|' -f1)"
printf 'RESULT: one\nRESULT: two\n' > "$GT/two"
ck "G6 rc 0 with two RESULT lines -> refused" \
   "refused" "$(gv 0 "$GT/two" | cut -d'|' -f1)"
printf 'RESULT: a\tb\r\n' > "$GT/tab"
ck "G7 a tab and a CR in the RESULT line do not reach the manifest" \
   "green|RESULT: a b" "$(gv 0 "$GT/tab")"
ck "G8 a missing log is refused, not a crash" \
   "refused" "$(gv 0 "$GT/nonexistent" | cut -d'|' -f1)"
rm -rf "$GT"

echo
echo "=== R1-R8: the two gates with the REAL tools, on synthetic inputs ==="
# run_gates, write_manifest and finish_build are extracted and sourced -- the
# C8 reason: a build is 35 s -- but the gate tools are the real
# tools/kconfig-delta.py and tools/rlxfw-marks.py, so a RESULT line that
# changed shape, or an exit status that moved, turns these red.  Every input
# is a few bytes written here: a baseline whose sha256 the delta declares, a
# one-row marks declaration, an "image" holding the mark once, and a fake
# $FWRE_WORK holding one reference.
RT="$(mktemp -d)"
for f in absent_refs gate_verdict run_gates overall_verdict write_manifest finish_build; do
    sed -n "/^$f() {/,/^}\$/p" "$K" >> "$RT/fns.sh"
done
ck "R0 the six functions are extractable" "6" "$(grep -c '^}$' "$RT/fns.sh")"
printf '#\n# synthetic baseline\n#\nCONFIG_A=y\n# CONFIG_B is not set\n' > "$RT/base.config"
BSHA="$(sha256sum "$RT/base.config" | cut -d' ' -f1)"
{ printf '# baseline-sha256: %s\n' "$BSHA"
  printf 'set\tCONFIG_B\tn\ty\t-\trlxfw turns B on\n'
  printf 'set@loud\tCONFIG_L\t-\ty\t-\tthe loud image only\n'; } > "$RT/delta"
printf 'CONFIG_A=y\nCONFIG_B=y\n'             > "$RT/built-quiet"
printf 'CONFIG_A=y\nCONFIG_B=y\nCONFIG_L=y\n' > "$RT/built-loud"
printf 'CONFIG_A=y\nCONFIG_B=y\nCONFIG_X=y\n' > "$RT/built-undeclared"
printf '# id\tfile\tposition\tanchor\tinsert\twitness\treason\nB00\tinit/main.c\tafter\tstart_kernel();\trlxfw_mark("B00");\t\tthe first mark\n' > "$RT/marks.tsv"
printf 'head RLXFW-B00\n tail' > "$RT/marked.elf"
printf 'head, and no mark\n'   > "$RT/unmarked.elf"
printf '80000000 T _text\n'    > "$RT/System.map"
mkdir -p "$RT/work/rebuild/ref"
refdecl () {   # refdecl <file under $RT/work> <declaration out>
    printf 'vendor\t%s\t%s\t%s\ta synthetic vendor kernel\n' "$1" \
        "$(stat -c %s "$RT/work/$1")" "$(sha256sum "$RT/work/$1" | cut -d' ' -f1)" > "$2"
}
printf 'a vendor kernel\n'            > "$RT/work/rebuild/ref/vendor.bin"
printf 'a vendor kernel RLXFW-B00\n'  > "$RT/work/rebuild/ref/dirty.bin"
refdecl rebuild/ref/vendor.bin "$RT/absent.tsv"
refdecl rebuild/ref/dirty.bin  "$RT/absent-dirty.tsv"
PY3=/usr/bin/python3
gates () {   # gates <built|-> <image> <variant> <absent decl> <build rc> [hook]
    rm -f "$RT"/c.* "$RT"/fin.*
    (
        log="$RT/c"; CELL=rcell; RECIPE_ID=deadbeef; CONFIG=""; VARIANT="$3"
        INITRAMFS=""; CFLAGS_KERNEL=-fno-if-conversion; ID_SCOPE=global
        OLDCONFIG=devnull; TARGET=vmlinux; JOBS=4; KEEP=0; STAMP_EPOCH=1788220800
        N_PATCHES=7; N_MARKS=25; DROP=/x/rtl819x-toolchain; PY="$PY3"
        TEMPLATE="$RT/base.config"; DELTA_FILE="$RT/delta"; MARKS_DECL="$RT/marks.tsv"
        KDELTA="$REPO/tools/kconfig-delta.py"; MARKSPY="$REPO/tools/rlxfw-marks.py"
        FWRE_WORK="$RT/work"; ABSENT_DECL="$4"; RECIPIENT=0
        ABSENT_FILES=(); ABSENT_SHAS=(); ABSENT_NAMES=()
        [ "$1" = - ] || cp "$1" "$log.config-built"
        cp "$2" "$log.vmlinux.elf"; cp "$RT/System.map" "$log.System.map"
        printf 'INSTALLED\n' > "$log.config-installed"
        . "$RT/fns.sh"
        [ -n "${6:-}" ] && eval "$6"
        BUILD_RC="$5"
        run_gates > "$RT/fin.gates" 2>&1
        write_manifest "$log.vmlinux.elf"
        finish_build > "$RT/fin.out" 2> "$RT/fin.err"
        echo "$?" > "$RT/fin.rc"
    )
}
mf () { awk -F'\t' -v k="$1" '$1 == k { print $2 }' "$RT/c.manifest"; }
# looprun's OWN regex, read out of looprun.py rather than restated here: a
# copy would be a second owner of what S2 accepts.
mrx () {
    "$PY3" - "$REPO/tools/looprun.py" "$RT/fin.out" <<'PYEOF'
import re, sys
rx = [l for l in open(sys.argv[1], encoding="utf-8").read().splitlines()
      if l.startswith("MANIFEST_RX = ")]
if len(rx) != 1:
    print("no MANIFEST_RX in looprun.py"); sys.exit(0)
ns = {"re": re}
exec(rx[0], ns)
print(1 if ns["MANIFEST_RX"].search(open(sys.argv[2], encoding="utf-8").read()) else 0)
PYEOF
}
fin () { cat "$RT/fin.rc"; }

gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent.tsv" 0
ck "R1 both gates green -> green/0, green/0, verdict green" \
   "green/0/green/0/green" \
   "$(mf kconfig_check)/$(mf kconfig_check_rc)/$(mf marks_verify)/$(mf marks_verify_rc)/$(mf verdict)"
ck "R1b and the driver exits 0 with a line looprun's MANIFEST_RX reads" \
   "0/1" "$(fin)/$(mrx)"
ck "R1c each RESULT line is recorded, escapes removed" \
   "RESULT: every difference between the vendor template and the .config this build used is on the list" \
   "$(mf kconfig_check_result)"
ck "R1d verify's RESULT names the one reference it was given" 1 \
   "$(mf marks_verify_result | grep -c 'absent from 1 vendor artefact(s)$')"
ck "R1e marks_verify_absent is name=sha256 of that reference" \
   "vendor=$(sha256sum "$RT/work/rebuild/ref/vendor.bin" | cut -d' ' -f1)" \
   "$(mf marks_verify_absent)"

gates "$RT/built-undeclared" "$RT/marked.elf" quiet "$RT/absent.tsv" 0
ck "R2 an undeclared .config difference -> kconfig_check red, rc 1" \
   "red/1/not-green" "$(mf kconfig_check)/$(mf kconfig_check_rc)/$(mf verdict)"
ck "R2b and its RESULT line is the tool's, verbatim" \
   "RESULT: REFUSED -- 1 undeclared, 0 mismatched, 0 not applied." "$(mf kconfig_check_result)"
ck "R2c exit 6, NO line MANIFEST_RX reads, and the red record is kept" \
   "6/0/present" "$(fin)/$(mrx)/$( [ -f "$RT/c.manifest" ] && echo present || echo absent )"

gates "$RT/built-quiet" "$RT/unmarked.elf" quiet "$RT/absent.tsv" 0
ck "R3 the mark missing from the image -> marks_verify red, exit 6" \
   "red/1/6/0" "$(mf marks_verify)/$(mf marks_verify_rc)/$(fin)/$(mrx)"

gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-dirty.tsv" 0
ck "R4 the mark present in the reference -> marks_verify red" \
   "red/6" "$(mf marks_verify)/$(fin)"

# R5 -- --variant reaches the check.  The delta has a @loud row, so the loud
# .config is green under loud and RED with no variant (a --config build).
gates "$RT/built-loud" "$RT/marked.elf" loud "$RT/absent.tsv" 0
ck "R5 --variant loud: the loud .config is green, variant recorded" \
   "green/loud" "$(mf kconfig_check)/$(mf variant)"
gates "$RT/built-loud" "$RT/marked.elf" "" "$RT/absent.tsv" 0
ck "R5b no variant (a --config build): the same file is red, variant -" \
   "red/-" "$(mf kconfig_check)/$(mf variant)"

gates - "$RT/marked.elf" quiet "$RT/absent.tsv" 0
ck "R6 no .config-built -> refused, rc -, and the tool was not run" \
   "refused/-/absent" \
   "$(mf kconfig_check)/$(mf kconfig_check_rc)/$( [ -f "$RT/c.kconfig-check.log" ] && echo present || echo absent )"

# R7 -- the point-of-use check.  The reference changes after the declaration
# was written (the hook runs just before run_gates), so verify is refused
# rather than run against bytes nobody declared.
cp "$RT/work/rebuild/ref/vendor.bin" "$RT/vendor.orig"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent.tsv" 0 \
      'printf "a vendor kernel, edited\n" > "$RT/work/rebuild/ref/vendor.bin"'
ck "R7 a reference changed before use -> marks_verify refused, rc -" \
   "refused/-/6" "$(mf marks_verify)/$(mf marks_verify_rc)/$(fin)"
cp "$RT/vendor.orig" "$RT/work/rebuild/ref/vendor.bin"

gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent.tsv" 2
ck "R8 build step not 0 (rc 2), both gates green -> exit 2, no line" \
   "green/green/not-green/2/0" \
   "$(mf kconfig_check)/$(mf marks_verify)/$(mf verdict)/$(fin)/$(mrx)"

echo
echo "=== X1-X12d: --expect-present ROW-ID (R8b, FW-228) -- forwarded, never derived ==="
# R8b's armed image flips config/rlxfw-kernel.delta's CONFIG_MTD_RTL819X_WRITE
# to y, so rtl819x_spi_write_page is in its System.map and MK5's `absent:` goes
# RED, correctly.  rlxfw-marks.py's `--expect-present ROW` inverts that one row
# for one run (its own W17a-W17d); the driver forwards the flag verbatim when
# it is given and never otherwise.  X1-X8b are the flag's refusals and their
# positive control, above the stage through --dry-run -- every one of them
# carries --dry-run, so a refusal that stopped firing exits at the dry-run and
# stages nothing.  X9-X12d are the four cells of the truth table END TO END
# through the extracted gate (run_gates, write_manifest, finish_build) with the
# REAL rlxfw-marks.py, down to the exit status and the line looprun's
# MANIFEST_RX reads.  The two REDS are the half that matters: a flag shown only
# where it passes is a flag that cannot fail.
xrun () { out="$(bash "$K" "$@" 2>&1)"; rc=$?; }
xhas () { printf '%s\n' "$out" | grep -c -- "$1"; }
xrun gcf-x1 --variant quiet --dry-run --expect-present
ck "X1 --expect-present with nothing after it -> 3, a reason" \
   "3/1/0" "$rc/$(xhas 'was given no ROW-ID')/$(xhas 'unbound variable')"
xrun gcf-x2 --variant quiet --dry-run --expect-present ""
ck "X2 an EMPTY row id -> 3, the same reason" "3/1" "$rc/$(xhas 'was given no ROW-ID')"
# The flag swallows the first --dry-run; the second is the one in force, so a
# guard that stopped firing would end at the dry-run instead of staging.
xrun gcf-x3 --variant quiet --expect-present --dry-run --dry-run
ck "X3 an option taken as the row id -> 3, before the dry-run exit" "3/1/0" \
   "$rc/$(xhas "'--dry-run': that is an option")/$(xhas 'nothing staged and nothing built')"
# X4-X6 -- which ids are valid is the TOOL's to say, above the stage: each
# refusal carries rlxfw-marks' own sentence and the driver keeps no list.
xrun gcf-x4 --variant quiet --dry-run --expect-present MK55
ck "X4 an unknown row id -> 3 in rlxfw-marks' words, before the dry-run" "3/1/1/0" \
   "$rc/$(xhas 'rlxfw-marks refused the exemption, above the stage')/$(xhas 'MK55: .* declares no such row')/$(xhas 'nothing staged and nothing built')"
xrun gcf-x5 --variant quiet --dry-run --expect-present MK4
ck "X5 an unconditional row (MK4, obj-y) -> 3, it has nothing to invert" "3/1" \
   "$rc/$(xhas 'which is not a conditional Kbuild line')"
xrun gcf-x6 --variant quiet --dry-run --expect-present MK5 --expect-present MK5
ck "X6 the same row id twice -> 3, refused by the tool" "3/1" "$rc/$(xhas 'MK5 was given twice')"
xrun gcf-x7 --variant quiet --dry-run --target none --expect-present MK5
ck "X7 with --target none -> 3: no gate runs, so nothing to exempt" "3/1" \
   "$rc/$(xhas 'with --target none')"
# X8 -- the positive control: a guard that refused everything would pass X1-X7.
# X8b -- and without the flag the output does not mention it at all.
xrun gcf-x8 --variant quiet --dry-run --expect-present MK5
ck "X8 --expect-present MK5 is accepted, printed, and the dry-run reached" "0/1/1" \
   "$rc/$(xhas '--expect-present MK5 <- argv, this run only')/$(xhas 'nothing staged and nothing built')"
xrun gcf-x8b --variant quiet --dry-run
ck "X8b no flag: not one line of the output mentions it" "0/0" "$rc/$(xhas 'expect-present')"

# X9-X12d -- one declaration holding a mark and an MK5-shaped conditional row,
# two maps that differ in that one symbol, and the exemption set the way the
# argument loop sets it, as EXPECT_PRESENT, through `gates`' hook.
{ printf '# id\tfile\tposition\tanchor\tinsert\twitness\treason\n'
  printf 'B00\tinit/main.c\tafter\tstart_kernel();\trlxfw_mark("B00");\t\tthe first mark\n'
  printf 'MK5\tdrivers/mtd/devices/Makefile\tafter\tobj-y += rtl819x-spi.o\tobj-$(CONFIG_MTD_RTL819X_WRITE) += rtl819x-spi-write.o\tabsent:rtl819x_spi_write_page\tdeclared, conditional\n'
} > "$RT/marks-cond.tsv"
printf '80000000 T _text\n80100000 T rtl819x_spi_read_page\n'  > "$RT/map-mainline"
printf '80000000 T _text\n801a8a20 T rtl819x_spi_write_page\n' > "$RT/map-armed"
cell () {   # cell <map> [row id] -- the exemption is in force iff a row id is given
    local hook='MARKS_DECL="$RT/marks-cond.tsv"; cp "$RT/'"$1"'" "$log.System.map"'
    [ -z "${2:-}" ] || hook="$hook; EXPECT_PRESENT=($2)"
    gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent.tsv" 0 "$hook"
}
vlog () { sed 's/\x1b\[[0-9;]*m//g' "$RT/c.marks-verify.log"; }
vline () { grep '^== rcell: rlxfw-marks verify ' "$RT/fin.gates"; }
lastrow () { tail -n 1 "$RT/c.manifest" | tr '\t' ' '; }

cell map-mainline
ck "X9 mainline, no flag: GREEN, exit 0, a line MANIFEST_RX reads" \
   "green/0/green/0/1" "$(mf marks_verify)/$(mf marks_verify_rc)/$(mf verdict)/$(fin)/$(mrx)"
ck "X9b and no trace of the flag: tool argv, verdict line, last line, manifest" \
   "0/0/0/30" "$(vlog | grep -c 'expect-present')/$(vline | grep -c 'expect-present')/$(grep -c 'expect-present' "$RT/fin.out")/$(wc -l < "$RT/c.manifest" | tr -d ' ')"
cell map-mainline MK5
ck "X10 mainline + --expect-present MK5: RED, exit 6, no MANIFEST_RX line" \
   "red/1/not-green/6/0" "$(mf marks_verify)/$(mf marks_verify_rc)/$(mf verdict)/$(fin)/$(mrx)"
ck "X10b the tool got the flag; the verdict, last line and manifest name it" \
   "1/1/1/marks_verify_expect_present MK5" \
   "$(vlog | grep -c '^expect *--expect-present MK5')/$(vline | grep -c 'verify \[--expect-present MK5\] red (rc=1)')/$(grep -c 'rlxfw-marks verify red under --expect-present MK5; the record is' "$RT/fin.out")/$(lastrow)"
cell map-armed
ck "X11 armed, no flag: RED, exit 6 -- the exemption is never derived" \
   "red/1/not-green/6/0" "$(mf marks_verify)/$(mf marks_verify_rc)/$(mf verdict)/$(fin)/$(mrx)"
ck "X11b and the red row is MK5, its symbol found where it must not be" 1 \
   "$(vlog | grep -cE '^  MK5 +absent: +rtl819x_spi_write_page +mine:1 .*must be 0 here')"
cell map-armed MK5
ck "X12 armed + --expect-present MK5: GREEN, exit 0, a line MANIFEST_RX reads" \
   "green/0/green/0/1" "$(mf marks_verify)/$(mf marks_verify_rc)/$(mf verdict)/$(fin)/$(mrx)"
ck "X12b the verdict line names it, and so does the line before the manifest" "1/1" \
   "$(vline | grep -c 'verify \[--expect-present MK5\] green (rc=0)')/$(sed -n 1p "$RT/fin.out" | grep -c 'green UNDER --expect-present MK5')"
ck "X12c the manifest records it last, after the same thirty lines" \
   "31/marks_verify_expect_present MK5" "$(wc -l < "$RT/c.manifest" | tr -d ' ')/$(lastrow)"
ck "X12d and verify's own RESULT says one row was confirmed PRESENT" 1 \
   "$(mf marks_verify_result | grep -c '1 confirmed PRESENT under --expect-present')"

echo
echo "=== Y1-Y7b: --recipient above the stage (GPL-2.0 § 3) -- only UNIT_REFS is skipped ==="
# 量 2026-10-05: with the committed declaration the driver exits 3 unless BOTH
# --absent references are on the desk, and `unit-kernel` is this unit's own
# vendor kernel, which no recipient of the corresponding source can hold.
# --recipient skips the rows the driver's UNIT_REFS names and nothing else.
# The A-block's shape: the real driver, a fake $FWRE_WORK and repository, and a
# run that gets past the reference guard stops at `no drop at`.  The four cells
# the flag has -- refs present or missing, flag or not -- are Y1/Y2/Y3/Y4 here
# and Z1/Z2/Z3/Z4 through the gate below.
YT="$(mktemp -d)"
YW="$YT/work"; YR="$YT/repo"; YD="$YR/tools/rlxfw-marks-absent.tsv"
mkdir -p "$YW/rebuild/desk" "$YW/rebuild/src-vendor/drop" "$YR/config" "$YR/tools" "$YT/empty"
cp "$CF" "$YR/config/rlxfw-cflags"; cp "$SF" "$YR/config/rlxfw-build-stamp"
printf 'a synthetic unit kernel\n' > "$YW/rebuild/desk/unit.bin"
printf 'a synthetic drop kernel\n' > "$YW/rebuild/src-vendor/drop/vmlinux_img"
cp "$YW/rebuild/desk/unit.bin" "$YT/unit.orig"
yrow () {   # yrow <name> <relpath under $YW>
    printf '%s\t%s\t%s\t%s\tsynthetic\n' "$1" "$2" \
        "$(stat -c %s "$YW/$2")" "$(sha256sum "$YW/$2" | cut -d' ' -f1)"
}
UROW="$(yrow unit-kernel rebuild/desk/unit.bin)"
DROW="$(yrow drop-kernel rebuild/src-vendor/drop/vmlinux_img)"
SU="$(sha256sum "$YW/rebuild/desk/unit.bin" | cut -c1-16)"
SD="$(sha256sum "$YW/rebuild/src-vendor/drop/vmlinux_img" | cut -c1-16)"
printf '%s\n%s\n' "$UROW" "$DROW" > "$YD"
yrun () { out="$(FWRE_WORK="$YW" RLXFW_REPO="$YR" bash "$K" "$@" 2>&1)"; rc=$?; }
yhas () { printf '%s\n' "$out" | grep -c -- "$1"; }
# The wording is pinned here as a literal, not read from the driver: the docs
# and a recipient's own scripts grep for it.
RB='RECIPIENT BUILD -- unit-specific checks not run: unit-kernel'
VERIFIED_D="references verified <- tools/rlxfw-marks-absent.tsv: drop-kernel $SD\$"

yrun gcf-y1 --variant quiet
ck "Y1 refs present, no flag: both verified, no word of the flag" "3/1/1/0" \
   "$rc/$(yhas "references verified <- tools/rlxfw-marks-absent.tsv: unit-kernel $SU drop-kernel $SD\$")/$(yhas 'no drop at')/$(printf '%s\n' "$out" | grep -ci 'recipient')"
mv "$YW/rebuild/desk/unit.bin" "$YT/unit.away"
yrun gcf-y2 --variant quiet
ck "Y2 unit ref missing, no flag: 3, named, the refusal names --recipient" "3/1/1/0/0" \
   "$rc/$(yhas 'unit-kernel: no file at')/$(yhas '  --recipient, which skips the checks that read it and nothing else.')/$(yhas "$RB")/$(yhas 'no drop at')"
mv "$YT/unit.away" "$YW/rebuild/desk/unit.bin"
# Y2b -- the offer is about the unit-specific row only: the flag cannot help a
# missing drop kernel, so offering it there would be a wrong instruction.
mv "$YW/rebuild/src-vendor/drop/vmlinux_img" "$YT/drop.away"
yrun gcf-y2b --variant quiet
ck "Y2b drop ref missing, no flag: 3, and --recipient is NOT offered" "3/1/0" \
   "$rc/$(yhas 'drop-kernel: no file at')/$(printf '%s\n' "$out" | grep -ci 'recipient')"
mv "$YT/drop.away" "$YW/rebuild/src-vendor/drop/vmlinux_img"

mv "$YW/rebuild/desk/unit.bin" "$YT/unit.away"
yrun gcf-y3 --variant quiet --recipient
ck "Y3 unit ref missing + --recipient: past the guard on the drop ref alone" "3/1/1/0" \
   "$rc/$(yhas "$VERIFIED_D")/$(yhas 'no drop at')/$(yhas 'problem(s) in the declared')"
ck "Y3b and line 3 is the banner, before any reference is read" \
   "== gcf-y3: $RB; not for upload to this project's unit" "$(printf '%s\n' "$out" | sed -n 3p)"
mv "$YW/rebuild/src-vendor/drop/vmlinux_img" "$YT/drop.away"
yrun gcf-y3c --variant quiet --recipient
ck "Y3c and with the drop ref missing too: 3 on drop-kernel -- nothing else skipped" "3/1/0/0" \
   "$rc/$(yhas 'drop-kernel: no file at')/$(yhas 'unit-kernel: ')/$(yhas 'no drop at')"
mv "$YT/drop.away" "$YW/rebuild/src-vendor/drop/vmlinux_img"
mv "$YT/unit.away" "$YW/rebuild/desk/unit.bin"

# Y4 -- refs PRESENT + --recipient is allowed, and the unit row is still not
# read: what the flag does is a property of argv, not of the desk.
yrun gcf-y4 --variant quiet --recipient
ck "Y4 refs present + --recipient: allowed, the unit ref not listed" "3/1/1/0" \
   "$rc/$(yhas "$VERIFIED_D")/$(yhas 'no drop at')/$(yhas "$SU")"
# Y4b -- "not read" rather than "read and forgiven": a CHANGED unit file passes
# under the flag and is refused on its digest without it -- and a changed file
# is a desk defect, so that refusal does not offer the flag.
printf 'A synthetic unit kernel\n' > "$YW/rebuild/desk/unit.bin"
yrun gcf-y4b --variant quiet --recipient; y4r="$rc/$(yhas 'no drop at')"
yrun gcf-y4c --variant quiet; y4n="$rc/$(yhas 'unit-kernel: .* has sha256 ')/$(printf '%s\n' "$out" | grep -ci 'recipient')"
ck "Y4b a CHANGED unit ref: unread under the flag, refused (no offer) without" \
   "3/1 3/1/0" "$y4r $y4n"
cp "$YT/unit.orig" "$YW/rebuild/desk/unit.bin"

# Y5 -- the exemption is by NAME, so a declaration without that name makes the
# flag skip nothing: refused.  Y5b -- and with the unit row the only row, verify
# would get no --absent at all: refused.
printf '%s\n' "$DROW" > "$YD"
yrun gcf-y5 --variant quiet --recipient
ck "Y5 --recipient, no unit-kernel row: 3, it would skip nothing" "3/1/0" \
   "$rc/$(yhas 'declares no row of that name')/$(yhas 'no drop at')"
printf '%s\n' "$UROW" > "$YD"
yrun gcf-y5b --variant quiet --recipient
ck "Y5b --recipient, the unit row alone: 3, verify never runs with no --absent" "3/1/0" \
   "$rc/$(yhas 'declares no reference image besides the row(s)')/$(yhas 'no drop at')"
printf '%s\n%s\n' "$UROW" "$DROW" > "$YD"
yrun gcf-y6 --variant quiet --recipient --dry-run
ck "Y6 --recipient --dry-run: 0, the banner, the dry-run reached" "0/1/1" \
   "$rc/$(yhas "== gcf-y6: $RB; not for upload")/$(yhas 'nothing staged and nothing built')"

# Y7 -- the COMMITTED declaration, under an empty $FWRE_WORK, in both
# directions: with the flag only drop-kernel is required, and without it both
# are, the refusal offering the flag once.  A third row a recipient cannot hold
# would turn Y7 red rather than slip into what --recipient still reads.
cp "$REPO/tools/rlxfw-marks-absent.tsv" "$YD"
out="$(FWRE_WORK="$YT/empty" RLXFW_REPO="$YR" bash "$K" gcf-y7 --variant quiet --recipient 2>&1)"; rc=$?
ck "Y7 committed declaration + --recipient: drop-kernel alone is required" "3/1/1/0" \
   "$rc/$(yhas 'no file at')/$(yhas 'drop-kernel: no file at \$FWRE_WORK/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30/rtkload/vmlinux_img')/$(yhas 'unit-kernel: ')"
out="$(FWRE_WORK="$YT/empty" RLXFW_REPO="$YR" bash "$K" gcf-y7b --variant quiet 2>&1)"; rc=$?
ck "Y7b and without it: both required, the flag offered once" "3/2/1" \
   "$rc/$(yhas 'no file at')/$(yhas 'a recipient builds with')"
rm -rf "$YT"

echo
echo "=== Z0-Z7: --recipient through the gate -- its own verdict, never green ==="
# The X-block's harness and the real rlxfw-marks.py.  A unit reference that
# HOLDS a mark string is the discriminator for "not read": without the flag it
# turns verify red; with it, verify never sees it.
eval "$(sed -n -e '/^UNIT_REFS=/p' -e '/^RECIPIENT_NOTE=/p' "$K")"
ck "Z0 the driver's UNIT_REFS and its note, as the docs quote them" \
   "unit-kernel|unit-specific checks not run: unit-kernel" "${UNIT_REFS-}|${RECIPIENT_NOTE-}"
mkdir -p "$RT/work/rebuild/desk"
printf "this unit's vendor kernel\n"         > "$RT/work/rebuild/desk/unit.bin"
printf 'a unit kernel holding RLXFW-B00\n' > "$RT/work/rebuild/desk/unit-dirty.bin"
urow () {
    printf 'unit-kernel\t%s\t%s\t%s\tthis unit, synthetic\n' "$1" \
        "$(stat -c %s "$RT/work/$1")" "$(sha256sum "$RT/work/$1" | cut -d' ' -f1)"
}
{ urow rebuild/desk/unit.bin;       cat "$RT/absent.tsv"; } > "$RT/absent-u.tsv"
{ urow rebuild/desk/unit-dirty.bin; cat "$RT/absent.tsv"; } > "$RT/absent-ud.tsv"
UNIT_AWAY='mv "$RT/work/rebuild/desk/unit.bin" "$RT/unit.away"'
any_recipient () { cat "$RT/fin.gates" "$RT/fin.out" "$RT/c.manifest" | grep -ci 'recipient'; }

gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-u.tsv" 0
ck "Z1 refs present, no flag: green, exit 0, MANIFEST_RX, both refs to verify" \
   "green/0/1/2/0/30" \
   "$(mf verdict)/$(fin)/$(mrx)/$(mf marks_verify_absent | tr ',' '\n' | grep -c .)/$(any_recipient)/$(wc -l < "$RT/c.manifest" | tr -d ' ')"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-u.tsv" 0 "$UNIT_AWAY"
mv "$RT/unit.away" "$RT/work/rebuild/desk/unit.bin"
ck "Z2 unit ref missing, no flag: verify refused, exit 6, the flag offered" \
   "refused/not-green/6/0/1" \
   "$(mf marks_verify)/$(mf verdict)/$(fin)/$(mrx)/$(grep -c 'a recipient builds with' "$RT/fin.gates")"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-u.tsv" 0 "$UNIT_AWAY; RECIPIENT=1"
mv "$RT/unit.away" "$RT/work/rebuild/desk/unit.bin"
ck "Z3 unit ref missing + --recipient: verdict recipient, exit 7, no MANIFEST_RX" \
   "green/recipient/7/0" "$(mf marks_verify)/$(mf verdict)/$(fin)/$(mrx)"
ck "Z3b the verify line, the last line and the manifest's last row carry it" \
   "1/1/recipient $RECIPIENT_NOTE/31" \
   "$(grep -c "verify \[RECIPIENT BUILD -- $RECIPIENT_NOTE\] green (rc=0)" "$RT/fin.gates")/$(grep -c "^== rcell: RECIPIENT BUILD -- $RECIPIENT_NOTE; build rc=0, .*not for upload to this project's unit; the record is " "$RT/fin.out")/$(lastrow)/$(wc -l < "$RT/c.manifest" | tr -d ' ')"
ck "Z3c verify got the other reference alone, and its RESULT counts one" \
   "vendor=$(sha256sum "$RT/work/rebuild/ref/vendor.bin" | cut -d' ' -f1)/1" \
   "$(mf marks_verify_absent)/$(mf marks_verify_result | grep -c 'absent from 1 vendor artefact(s)$')"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-ud.tsv" 0
z4="$(mf marks_verify)/$(fin)"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-ud.tsv" 0 'RECIPIENT=1'
ck "Z4 refs PRESENT, a mark in the unit ref: red/6 without the flag, recipient/7 with" \
   "red/6 recipient/7/0" "$z4 $(mf verdict)/$(fin)/$(mrx)"
gates "$RT/built-quiet" "$RT/unmarked.elf" quiet "$RT/absent-u.tsv" 0 'RECIPIENT=1'
ck "Z5 --recipient over a RED verify: not-green, exit 6, NOT FOR UPLOAD names it" \
   "not-green/6/0/1" \
   "$(mf verdict)/$(fin)/$(mrx)/$(grep -c "NOT FOR UPLOAD -- .*rlxfw-marks verify red; RECIPIENT BUILD -- $RECIPIENT_NOTE; the record is " "$RT/fin.out")"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-u.tsv" 0 \
      'MARKS_DECL="$RT/marks-cond.tsv"; cp "$RT/map-armed" "$log.System.map"; EXPECT_PRESENT=(MK5); RECIPIENT=1'
ck "Z6 + --expect-present MK5, armed: recipient/7, no MANIFEST_RX, no green UNDER" \
   "green/recipient/7/0/0" \
   "$(mf marks_verify)/$(mf verdict)/$(fin)/$(mrx)/$(grep -c 'green UNDER' "$RT/fin.out")"
ck "Z6b and the manifest ends with both rows, the exemption first" \
   "marks_verify_expect_present MK5|recipient $RECIPIENT_NOTE" \
   "$(tail -n 2 "$RT/c.manifest" | tr '\t' ' ' | paste -sd'|')"
gates "$RT/built-quiet" "$RT/marked.elf" quiet "$RT/absent-u.tsv" 2 'RECIPIENT=1'
ck "Z7 --recipient with the build step at rc 2: exit 2, never 7" "not-green/2/0" \
   "$(mf verdict)/$(fin)/$(mrx)"
rm -rf "$RT"

echo
echo "=== I1-I10: the initramfs, recorded by CONTENT (2026-09-23) ==="
# 量 2026-09-23: `initramfs_sha256` digests the spec -- paths, modes, owners --
# and _irfs-s100a and _irfs-p2 hold byte-identical specs whose /init differ
# (988 against 2,153 bytes).  mkinitramfs writes the content record beside
# each spec, <name>.spec -> <name>.manifest.tsv; the driver now refuses a spec
# without one ABOVE --dry-run, copies it beside the cell's copied spec, and
# digests the copy as `initramfs_manifest_sha256`.  All synthetic: the guard
# is reached by --dry-run, the key by the write_manifest harness, and the copy
# by one run against a fake drop (--oldconfig none, --target none) whose only
# "toolchain" is a file nothing executes.
IT="$(mktemp -d)"
mkdir -p "$IT/ok" "$IT/bare" "$IT/cellrec" "$IT/mixed"
spec_text () { printf 'dir /bin 0755 0 0\nfile /init %s 0755 0 0\n' "$1"; }
spec_text /src/init > "$IT/ok/rlxfw-initramfs.spec"
printf '# path\tkind\tbytes\tsha256\towner\tsource\n/init\tfile\t988\t%064d\trlxfw\t$REPO/init\n' 1 \
    > "$IT/ok/rlxfw-initramfs.manifest.tsv"
spec_text /src/init > "$IT/bare/rlxfw-initramfs.spec"
spec_text /src/init > "$IT/cellrec/c9.initramfs.spec"
cp "$IT/ok/rlxfw-initramfs.manifest.tsv" "$IT/cellrec/c9.initramfs.manifest.tsv"
spec_text /src/init > "$IT/mixed/c9.initramfs.spec"
cp "$IT/ok/rlxfw-initramfs.manifest.tsv" "$IT/mixed/rlxfw-initramfs.manifest.tsv"
spec_text /src/init > "$IT/ok/spec-without-suffix"

run gcf-i1 --variant quiet --initramfs "$IT/ok/rlxfw-initramfs.spec" --dry-run
ck "I1 a spec with its content record beside it passes" "0/1" \
   "$rc/$(printf '%s\n' "$out" | grep -c -- "initramfs contents <- $IT/ok/rlxfw-initramfs.manifest.tsv")"
run gcf-i2 --variant quiet --initramfs "$IT/bare/rlxfw-initramfs.spec" --dry-run
ck "I2 no record beside the spec -> 3, before the dry-run exit" "3/1/0" \
   "$rc/$(printf '%s\n' "$out" | grep -c -- "no $IT/bare/rlxfw-initramfs.manifest.tsv beside the spec")/$(printf '%s\n' "$out" | grep -c 'nothing staged and nothing built')"
run gcf-i3 --variant quiet --initramfs "$IT/nowhere/rlxfw-initramfs.spec" --dry-run
ck "I3 no spec at all -> 3, and it says the SPEC is missing" "3/1" \
   "$rc/$(printf '%s\n' "$out" | grep -c 'no initramfs spec at')"
run gcf-i4 --variant quiet --initramfs "$IT/ok/spec-without-suffix" --dry-run
ck "I4 a spec not named <name>.spec -> 3" "3/1" \
   "$rc/$(printf '%s\n' "$out" | grep -c 'is not <name>.spec')"
# I5 -- the record is paired with the spec by NAME, which is what lets a cell's
# own recorded pair be an input again: <cell>.initramfs.spec beside the
# <cell>.initramfs.manifest.tsv this driver now writes.  I5b is its negative: a
# record under another name in the same directory does not count, or one record
# could vouch for every spec beside it.
run gcf-i5 --variant quiet --initramfs "$IT/cellrec/c9.initramfs.spec" --dry-run
ck "I5 a cell's recorded pair (<cell>.initramfs.*) is a valid input" "0" "$rc"
run gcf-i5b --variant quiet --initramfs "$IT/mixed/c9.initramfs.spec" --dry-run
ck "I5b and a record under ANOTHER name beside it is not" "3" "$rc"

# I6-I9 -- the key, through the extracted write_manifest.
sed -n '/^write_manifest() {/,/^}$/p;/^overall_verdict() {/,/^}$/p' "$K" > "$IT/fn.sh"
irman () {   # irman <spec or ''> <record copy or ''> -> $IT/c.manifest
    rm -f "$IT"/c.*
    printf 'INSTALLED\n' > "$IT/c.config-installed"
    printf 'ELF\n' > "$IT/vm"
    if [ -n "$1" ]; then sha256sum "$1" | cut -d' ' -f1 > "$IT/c.initramfs.spec.sha256"; fi
    if [ -n "$2" ]; then cp "$2" "$IT/c.initramfs.manifest.tsv"; fi
    (
        log="$IT/c"; CELL=cell; RECIPE_ID=deadbeef; CONFIG=""; INITRAMFS="$1"
        CFLAGS_KERNEL=-fno-if-conversion; ID_SCOPE=global; OLDCONFIG=devnull
        TARGET=vmlinux; JOBS=4; KEEP=0; STAMP_EPOCH=1788220800; N_PATCHES=7
        N_MARKS=25; DROP=/x/rtl819x-toolchain
        . "$IT/fn.sh"
        write_manifest "$IT/vm"
    )
}
imf () { awk -F'\t' -v k="$1" '$1 == k { print $2 }' "$IT/c.manifest"; }
irman "$IT/ok/rlxfw-initramfs.spec" "$IT/ok/rlxfw-initramfs.manifest.tsv"
ck "I6 initramfs_manifest_sha256 is the digest of the record's copy" \
   "$(sha256sum "$IT/ok/rlxfw-initramfs.manifest.tsv" | cut -d' ' -f1)" \
   "$(imf initramfs_manifest_sha256)"
irman "" ""
ck "I7 no --initramfs -> a dash" "-" "$(imf initramfs_manifest_sha256)"
irman "$IT/ok/rlxfw-initramfs.spec" ""
ck "I8 --initramfs with no record copy -> missing, not a dash" \
   "missing" "$(imf initramfs_manifest_sha256)"
# I9 -- the finding itself, as a control.  Two specs identical in text, two
# records differing in one file's contents: the spec digest cannot tell them
# apart and the content digest must.
sed 's/\t988\t[0-9]*\t/\t2153\t0000000000000000000000000000000000000000000000000000000000000002\t/' \
    "$IT/ok/rlxfw-initramfs.manifest.tsv" > "$IT/other.manifest.tsv"
irman "$IT/ok/rlxfw-initramfs.spec" "$IT/ok/rlxfw-initramfs.manifest.tsv"
i9s1="$(imf initramfs_sha256)"; i9m1="$(imf initramfs_manifest_sha256)"
irman "$IT/bare/rlxfw-initramfs.spec" "$IT/other.manifest.tsv"
i9s2="$(imf initramfs_sha256)"; i9m2="$(imf initramfs_manifest_sha256)"
ck "I9 identical spec text, different contents: only the content digest moves" \
   "spec-same/contents-differ" \
   "$( [ "$i9s1" = "$i9s2" ] && echo spec-same || echo spec-differ )/$( [ "$i9m1" != "$i9m2" ] && echo contents-differ || echo contents-same )"

# I10 -- the copy, made by the driver's own main flow, against a fake drop.
FWI="$IT/work"; RPI="$IT/repo"
DRI="$FWI/rebuild/src-vendor/rtl819x-toolchain"
mkdir -p "$DRI/linux-2.6.30/usr" "$DRI/boards/rtl8196e" \
         "$DRI/toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/bin" "$RPI/config"
printf '# a fake board template\n' > "$DRI/boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW"
printf '#!/bin/sh\nexit 1\n' > "$DRI/toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/bin/rsdk-linux-gcc"
chmod +x "$DRI/toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30/bin/rsdk-linux-gcc"
cp "$CF" "$RPI/config/rlxfw-cflags"; cp "$SF" "$RPI/config/rlxfw-build-stamp"
printf '# a fake SDK config\n' > "$RPI/config/rlxfw-sdk.config"
printf 'CONFIG_BLK_DEV_INITRD=y\nCONFIG_INITRAMFS_SOURCE="usr/rlxfw-initramfs.spec"\n' > "$IT/fake.config"
irun () { out="$(FWRE_WORK="$FWI" RLXFW_REPO="$RPI" bash "$K" "$@" --oldconfig none --target none 2>&1)"; rc=$?; }
IOUT="$FWI/rebuild/r3-4/out/gcf-i10"
irun gcf-i10 --config "$IT/fake.config" --initramfs "$IT/ok/rlxfw-initramfs.spec"
ck "I10 the build copies the record beside the copied spec" "0/same" \
   "$rc/$(cmp -s "$IT/ok/rlxfw-initramfs.manifest.tsv" "$IOUT.initramfs.manifest.tsv" && echo same || echo differs)"
irun gcf-i10 --config "$IT/fake.config"
ck "I10b rebuilt without --initramfs: no earlier initramfs record stands" "0/0" \
   "$rc/$(ls "$IOUT".initramfs.* 2>/dev/null | wc -l)"
rm -rf "$IT"

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
# 🔴 There is no default. 🔄 Since R6b-8 8g (2026-09-28) the delta declares
# quiet, loud and quiet-swcore and its SWCORE rows are `@quiet,loud`, so no two
# names give the same bytes, and omitting the flag reads the untagged rows --
# quiet-swcore's set by coincidence, and never the mainline. kconfig-delta's own
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

# V7/V8 -- R6b-8 8g's vocabulary. quiet-swcore (the SWCORE=y image) is taken;
# 8b's quiet-noswcore is refused ABOVE the stage and says what replaced it,
# because the two names are two letters apart and mean opposite images.
run gcf-v7 --variant quiet-swcore --dry-run
ck "V7 --variant quiet-swcore is accepted"          0 "$rc"
run gcf-v8 --variant quiet-noswcore --dry-run
ck "V8 the retired quiet-noswcore is REFUSED"       3 "$rc"
ck "V8b and it names what replaced it"              1 \
   "$(printf '%s\n' "$out" | grep -c "retired.*SWCORE=n is 'quiet' now.*'quiet-swcore'")"


echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
