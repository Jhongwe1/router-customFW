#!/usr/bin/env bash
#
# Verify one copy of the S0a backup set against the reference copy, byte for
# byte, every file.
#
# Why this exists.  S0a made three copies and read two of them back.  "The
# upload reported success" and "what is sitting there is what was sent" are
# different claims, and only reading it back settles the second.  That is C-10.
#
# Why it hashes everything rather than reading CIPHERTEXT-SHA256.txt.  That
# manifest lists the seven .age archives.  The set also contains four par2
# recovery volumes, two public keys, RESTORE.md and two .deb files -- and the
# par2 volumes are the entire reason a copy left in a drawer is *repairable*
# rather than merely checkable.  age authenticates every 64 KiB chunk, so it
# detects rot; it cannot repair it.  Nothing was checking the thing that can.
#
# Usage
#   verify-backup-copy.sh <reference-dir> <copy-dir>
#   verify-backup-copy.sh --self-test <reference-dir>
#
# Exit 0 only when every file in the copy matches the reference and no file is
# missing or extra.

set -u

manifest() {   # manifest <dir> -> "<sha256>  <relative path>" lines, sorted
    ( cd "$1" && find . -type f -printf '%P\n' | LC_ALL=C sort \
        | while IFS= read -r f; do printf '%s  %s\n' "$(sha256sum -b -- "$f" | cut -d' ' -f1)" "$f"; done )
}

compare() {    # compare <ref> <copy> -> prints findings, returns count
    local ref=$1 copy=$2 n=0
    local rm cm
    rm=$(mktemp) cm=$(mktemp)
    manifest "$ref"  > "$rm"
    manifest "$copy" > "$cm"

    while IFS= read -r line; do
        local h=${line%%  *} f=${line#*  }
        local other
        other=$(grep -F -- "  $f" "$cm" | head -1)
        if [ -z "$other" ]; then
            printf 'MISSING   %s\n' "$f"; n=$((n+1))
        elif [ "${other%%  *}" != "$h" ]; then
            printf 'DIFFERS   %s\n    reference %s\n    copy      %s\n' "$f" "$h" "${other%%  *}"; n=$((n+1))
        fi
    done < "$rm"

    while IFS= read -r line; do
        local f=${line#*  }
        grep -qF -- "  $f" "$rm" || { printf 'EXTRA     %s\n' "$f"; n=$((n+1)); }
    done < "$cm"

    rm -f "$rm" "$cm"
    return $n
}

self_test() {  # the tool must be able to fail, in three distinct ways
    local ref=$1 tmp rc pass=0 fail=0
    tmp=$(mktemp -d)
    cp -a "$ref/." "$tmp/copy"  2>/dev/null || { mkdir -p "$tmp/copy"; cp -a "$ref/." "$tmp/copy/"; }

    check() {  # check <name> <expected-findings>
        local name=$1 want=$2 got
        compare "$ref" "$tmp/copy" >/dev/null 2>&1; got=$?
        if [ "$got" = "$want" ]; then printf '  ok    %-28s %s findings\n' "$name" "$got"; pass=$((pass+1))
        else printf '  FAIL  %-28s expected %s, got %s\n' "$name" "$want" "$got"; fail=$((fail+1)); fi
    }

    # C0 is the negative control: an untouched copy must report nothing.  On its
    # own it proves nothing, which is why C1-C3 follow.
    check "C0 untouched copy" 0

    local victim
    victim=$(cd "$tmp/copy" && find . -type f -printf '%P\n' | LC_ALL=C sort | head -1)
    printf '%s' x | dd of="$tmp/copy/$victim" bs=1 seek=0 conv=notrunc status=none
    check "C1 one flipped byte" 1

    cp -a "$ref/." "$tmp/copy/" 2>/dev/null
    rm -f "$tmp/copy/$victim"
    check "C2 one file removed" 1

    cp -a "$ref/." "$tmp/copy/" 2>/dev/null
    : > "$tmp/copy/an-extra-file"
    check "C3 one file added" 1

    rm -rf "$tmp"
    printf '\n%s passed, %s failed\n' "$pass" "$fail"
    [ "$fail" = 0 ]
}

case "${1:-}" in
    --self-test)
        [ $# -eq 2 ] || { echo "usage: $0 --self-test <reference-dir>" >&2; exit 2; }
        echo "self-test: the checker must report exactly one finding for each single defect"
        self_test "$2" ;;
    "")
        echo "usage: $0 <reference-dir> <copy-dir>" >&2
        echo "       $0 --self-test <reference-dir>" >&2
        exit 2 ;;
    *)
        [ $# -eq 2 ] || { echo "usage: $0 <reference-dir> <copy-dir>" >&2; exit 2; }
        [ -d "$1" ] || { echo "no such reference dir: $1" >&2; exit 2; }
        [ -d "$2" ] || { echo "no such copy dir: $2" >&2; exit 2; }
        echo "reference $1"
        echo "copy      $2"
        compare "$1" "$2"
        n=$?
        if [ "$n" = 0 ]; then
            echo "ok  every file in the copy matches the reference, none missing, none extra"
        else
            echo "$n finding(s).  A copy fetched as a server-made .zip and a copy fetched"
            echo "file by file are two different reads; if exactly one file differs, fetch"
            echo "that one on its own before concluding the stored bytes are wrong."
        fi
        exit $n ;;
esac
