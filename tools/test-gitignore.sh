#!/usr/bin/env bash
# Guard suite for .gitignore -- 21 cases, one of which skips on a filesystem
# that cannot make symlinks.
#
# 18 -> 21 on 2026-08-30: `ci-out/` had never been ignored, and the pre-push
# step CLAUDE.md mandates -- rebuild it locally, run the census -- is what
# creates it. Three cases, because one line is not one claim: the directory
# itself, a file inside it, and `ci-out.md` NOT ignored, which is what tells a
# trailing-slash pattern from a bare prefix.
#
# Why this exists rather than "just read the file"
# ------------------------------------------------
# The first version of this repository's .gitignore contained the line
#
#     src-vendor/          # cloned GPL drops -- SOURCES.json says how to re-fetch
#
# and it ignored nothing. `.gitignore` has no trailing-comment syntax: `#` only
# starts a comment at the beginning of a line, so the whole string -- spaces,
# em-dash and all -- was one pattern, matching no path that has ever existed.
#
# Reading the file does not catch that. Neither does any amount of care. The
# only thing that catches it is showing the file to the consumer that will
# actually judge it, which is what this does: a throwaway repository, real
# files, `git check-ignore`.
#
# It has a positive control as well as a negative one. A .gitignore consisting
# of the single line `*` would pass every "must be ignored" case and is
# obviously wrong, so six files that MUST survive are checked too.
#
# Usage:  tools/test-gitignore.sh
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GI="$HERE/.gitignore"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

[ -f "$GI" ] || { echo "no .gitignore at $GI" >&2; exit 1; }

skip=0

# MUST be tracked. Without these, a .gitignore of `*` would score 7/7.
KEEP="SOURCES.json .gitignore refs/README.md tools/fetch-sources.sh docs/threat-model.md dumps/MANIFEST.json ci-out.md"

# MUST be ignored, one per reason:
#   plan/     planning material, may address the author directly
#   study/    teaching notes, same reason
#   refs/     vendor documentation, not ours to redistribute
#   src-vendor/  cloned GPL drops, re-fetchable from SOURCES.json
#   build/    build output
#   dumps/    per-unit artefacts -- MACs and radio calibration
#   *.img *.squashfs  images anywhere
#   ci-out/   the CI capture directory, which the pre-push census creates here
DROP="plan/router-rebuild-plan.md study/20260823-study.md refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf src-vendor/x.c build/vmlinux dumps/flash.bin work.img rootfs.squashfs ci-out/spec-check.out ci-out/deeper/x.out"

cd "$T"
cp "$GI" .gitignore
git init -q .
git config user.email t@example.invalid
git config user.name t

for f in $KEEP $DROP; do
    [ "$f" = ".gitignore" ] && continue      # never truncate the file under test
    mkdir -p "$(dirname "$f")"
    : > "$f"
done

fail=0
pass=0

echo "=== must be TRACKED (positive control) ==="
for f in $KEEP; do
    if git check-ignore -q "$f"; then
        printf '  FAIL   %s  <- ignored, but this file must be committed\n' "$f"
        fail=$((fail + 1))
    else
        printf '  ok     %s\n' "$f"
        pass=$((pass + 1))
    fi
done

echo
echo "=== must be IGNORED ==="
for f in $DROP; do
    if git check-ignore -q "$f"; then
        printf '  ok     %s\n' "$f"
        pass=$((pass + 1))
    else
        printf '  FAIL   %s  <- would be committed\n' "$f"
        fail=$((fail + 1))
    fi
done

echo
echo "=== a SYMLINK named src-vendor must be ignored too ==="
# On this machine src-vendor is a symlink into ext4, not a directory: NTFS is
# case-insensitive and the vendor kernel trees carry paths that differ only in
# case. A .gitignore pattern ending in / matches directories only, so it would
# have let the symlink itself be committed.
rm -rf src-vendor
# MSYS/Git Bash has no symlinks: `ln -s` to a nonexistent target fails outright,
# and with errexit that killed this script before it printed RESULT -- on the one
# machine the push actually happens from. Skipped rather than failed, because the
# case is about .gitignore's pattern and not about the filesystem; Linux and WSL
# both still run it. `tools/ci-expected.tsv` carries the label.
if ! ln -s /nonexistent/elsewhere src-vendor 2>/dev/null; then
    printf '  skip   %-46s %s\n' "src-vendor (symlink)" \
           "this filesystem cannot make symlinks"
    skip=$((skip + 1))
elif git check-ignore -q src-vendor; then
    printf '  ok     %s
' "src-vendor (symlink)"
    pass=$((pass + 1))
else
    printf '  FAIL   %s  <- symlink would be committed
' "src-vendor (symlink)"
    fail=$((fail + 1))
fi
rm -f src-vendor

echo
echo "=== rlxfw's own source mirror is NOT swallowed by linux-*/ ==="
# 2026-08-28: `linux-*/` is there to keep vendor kernel trees out, and it also
# matched config/rlxfw-src/linux-2.6.30/ -- rlxfw's own two files, laid out the
# way the staged tree is laid out so tools/rlxfw-marks.py needs no path mapping.
# MEASURED: `git add -A` staged every other file of that session and left these
# two out in silence, which would have committed a build driver and a
# declaration that both name sources the repository does not contain.
#
# Both halves are asserted, because the negation only works if the DIRECTORY is
# un-ignored first: git does not descend into an excluded directory, so a
# `!.../**` on its own does nothing and this case would pass on a .gitignore
# that still drops the files.
for f in config/rlxfw-src/linux-2.6.30/arch/rlx/kernel/rlxfw_mark.c \
         config/rlxfw-src/linux-2.6.30/include/linux/rlxfw-mark.h; do
    # This suite runs inside a throwaway repository, so the paths are created
    # here rather than read out of the real tree: what is under test is the
    # PATTERN, and a case that depended on the real files existing would go red
    # for the wrong reason the day one of them is renamed.
    mkdir -p "$(dirname "$f")"
    : > "$f"
    if git check-ignore -q "$f"; then
        printf '  FAIL   %-46s %s\n' "$(basename "$f")" \
               "<- ignored; it would be missing from the commit"
        fail=$((fail + 1))
    else
        printf '  ok     %-46s %s\n' "$(basename "$f")" "tracked"
        pass=$((pass + 1))
    fi
done

# And the negative control: a vendor tree at the same depth must STILL be
# ignored, or the fix above turned the rule off rather than narrowing it.
mkdir -p .gitignore-probe/linux-2.6.30/arch
: > .gitignore-probe/linux-2.6.30/arch/probe.c
if git check-ignore -q .gitignore-probe/linux-2.6.30/arch/probe.c; then
    printf '  ok     %-46s %s\n' "linux-*/ still ignores a vendor tree" "ignored"
    pass=$((pass + 1))
else
    printf '  FAIL   %-46s %s\n' "linux-*/ still ignores a vendor tree" \
           "<- the negation widened the rule instead of narrowing it"
    fail=$((fail + 1))
fi
rm -rf .gitignore-probe

echo
echo "=== what a first commit would actually contain ==="
git add -A .
git diff --cached --name-only | sort | sed 's/^/  /'

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
