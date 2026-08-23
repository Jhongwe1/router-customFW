#!/usr/bin/env bash
# Every tracked program must be recorded executable, and nothing else may be.
#
# Why this exists rather than being obvious: this repository lives on /mnt/c,
# DrvFs reports every file as 777, git responds by setting core.fileMode=false,
# and from then on it cannot see a mode change at all. So a new tool is recorded
# with whatever mode `git add` happened to capture, nobody is told, and nothing
# ever corrects it. Seven of the first ten files in tools/ drifted to 100644
# this way while the three oldest stayed 100755.
#
# The bit is not load-bearing today -- every invocation in the documentation
# goes through `python3` or `bash`. It becomes load-bearing the moment DAY-ZERO
# item 6 builds a container, and a `Permission denied` from a shebang file is a
# confusing half hour. This check is cheap enough to run at every session close.
#
# It reads THE INDEX, not the working tree, because the working tree is exactly
# what DrvFs lies about. `git ls-files -s` prints what would be committed.
#
# Two directions, because a check that only looks one way would pass a repo in
# which every file is executable:
#   a file starting with `#!`  MUST be 100755
#   a file that does not       MUST NOT be 100755
#
# The control builds a synthetic repository with core.fileMode=false -- the same
# blindness this machine has -- containing one violation of each direction and
# one correct file of each kind, and requires the scan to report exactly the two
# violations. A scan that reported nothing there could not be trusted here.
set -o errexit
set -o nounset

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Print "<mode> <path>" for every tracked blob whose recorded mode disagrees
# with whether the file begins with a shebang. Blobs only: 120000 is a symlink
# (src-vendor points into WSL and may not even resolve from here) and 160000 is
# the pinned upstream submodule.
scan () {
    local repo="$1" mode hash stage path head2
    git -C "$repo" ls-files -s | while read -r mode hash stage path; do
        case "$mode" in 100644|100755) ;; *) continue ;; esac
        [ -f "$repo/$path" ] || continue
        head2="$(head -c2 "$repo/$path" 2>/dev/null || true)"
        if [ "$head2" = '#!' ] && [ "$mode" = 100644 ]; then
            echo "not-executable $path"
        elif [ "$head2" != '#!' ] && [ "$mode" = 100755 ]; then
            echo "executable-but-not-a-program $path"
        fi
    done
}

pass=0; fail=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-40s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-40s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}

echo "=== CONTROL: a synthetic repo, blind to modes the way this one is ==="
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
git -C "$T" init -q
git -C "$T" config core.fileMode false
git -C "$T" config core.autocrlf false   # or git warns about line endings it is not being asked about
git -C "$T" config user.email t@t; git -C "$T" config user.name t

printf '#!/bin/sh\necho hi\n' > "$T/drifted.sh"     # shebang, recorded 644 -- a violation
printf '# just a note\n'      > "$T/marked.md"      # no shebang, recorded 755 -- a violation
printf '#!/bin/sh\necho ok\n' > "$T/correct.sh"     # shebang, recorded 755 -- fine
printf '# another note\n'     > "$T/plain.md"       # no shebang, recorded 644 -- fine
git -C "$T" add -A
git -C "$T" update-index --chmod=-x drifted.sh
git -C "$T" update-index --chmod=+x marked.md
git -C "$T" update-index --chmod=+x correct.sh
git -C "$T" update-index --chmod=-x plain.md

ctl="$(scan "$T" | sort | tr '\n' ' ')"
ck "both violations reported, nothing else" \
   "executable-but-not-a-program marked.md not-executable drifted.sh " "$ctl"
ck "the correct files are not reported" \
   "0" "$(scan "$T" | grep -c -e correct.sh -e plain.md || true)"

echo
echo "=== THIS REPOSITORY ==="
found="$(scan "$ROOT" || true)"
if [ -n "$found" ]; then
    echo "$found" | while read -r why path; do printf '  FAIL   %-40s %s\n' "$why" "$path"; done
    fail=$((fail + $(echo "$found" | grep -c .)))
else
    n="$(git -C "$ROOT" ls-files -s | grep -c '^100755' || true)"
    printf '  ok     %-40s %s recorded executable\n' "every tracked program is 100755" "$n"
    pass=$((pass+1))
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"
    printf '        fix with: git update-index --chmod=+x <path>\n'
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
