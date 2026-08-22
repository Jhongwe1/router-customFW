#!/usr/bin/env bash
# Guard suite for .gitignore -- 13 cases.
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

# MUST be tracked. Without these, a .gitignore of `*` would score 7/7.
KEEP="SOURCES.json .gitignore refs/README.md tools/fetch-sources.sh docs/threat-model.md dumps/MANIFEST.json"

# MUST be ignored, one per reason:
#   plan/     planning material, may address the author directly
#   refs/     vendor documentation, not ours to redistribute
#   src-vendor/  cloned GPL drops, re-fetchable from SOURCES.json
#   build/    build output
#   dumps/    per-unit artefacts -- MACs and radio calibration
#   *.img *.squashfs  images anywhere
DROP="plan/router-rebuild-plan.md refs/RTL8196E-VEx-CG_Datasheet_1.1.pdf src-vendor/x.c build/vmlinux dumps/flash.bin work.img rootfs.squashfs"

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
echo "=== what a first commit would actually contain ==="
git add -A .
git diff --cached --name-only | sort | sed 's/^/  /'

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
