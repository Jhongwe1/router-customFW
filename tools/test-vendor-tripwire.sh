#!/usr/bin/env bash
# Controls for tools/vendor-tripwire.sh.
#
# A tripwire that cannot fire proves nothing, and a tripwire that fires on
# everything is a broken smoke alarm nobody looks at. So the cases come in
# pairs: for every way the tool must fire there is a neighbouring case where it
# must stay silent, and the two differ by one thing.
#
#   T1  clean command                -> exit 0, CLEAN
#   T2  command that FAILS but does  -> exit 1, still CLEAN, and the command's
#       not write                       own status appears on the verdict. This
#                                       is the pair that keeps "the build broke"
#                                       distinguishable from "the tree broke".
#   T3  untracked file appears       -> exit 2, path named
#   T4  tracked file modified        -> exit 2, reported as M
#   T5  tracked file DELETED         -> exit 2, reported as D. This is the
#                                       incident's actual shape: 2,580 deletions.
#   T6  IGNORED file appears         -> exit 2, AND the same damage read through
#                                       a plain `git status --porcelain` is zero
#                                       lines. Seventeen of the incident's files
#                                       were ignored; without `--ignored` the
#                                       tool would have called that tree clean.
#   T7  mtime-only write             -> exit 5 TOUCHED, and with --no-mtime the
#                                       identical write is exit 0 CLEAN. Both
#                                       directions, because a detector that
#                                       cannot be switched off has not been
#                                       shown to be the thing that fired.
#   T8  not a git repository         -> exit 3, refused
#   T9  tree already dirty           -> exit 4, refused, and the command is NOT
#                                       run -- checked by the absence of the
#                                       cmd-rc field it would otherwise print.
#   T11 git itself fails            -> exit 3 REFUSED. An unreadable tree gives
#                                      two empty snapshots that compare equal,
#                                      so this used to certify CLEAN.
#   T12 --check                     -> 0 on a clean tree, 4 on a dirty one. A
#                                      documented mode with no case before this.
#   T13 default tree discovery      -> the documented invocation. Every other
#                                      case passes --tree explicitly, so a mutant
#                                      that watched one tree instead of all of
#                                      them passed the entire suite.
#   T10 the incident's own binary    -> `rsdk-linux-config --version` must trip
#                                       it. Needs --live: the case damages and
#                                       then restores 2,580 files, which is not
#                                       a thing to do on every CI run.
#
# Every case that damages the subject tree restores it, and the EXIT trap
# restores it again in case a case died halfway. The suite refuses to start on a
# tree that is already dirty -- testing a tripwire on dirt measures nothing.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ME="$HERE/vendor-tripwire.sh"
ROOT="${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor"
LIVE=0
[ "${1:-}" = "--live" ] && LIVE=1

fail=0; pass=0; skipped=0
ck () { if [ "$2" = "$3" ]; then printf '  ok     %-42s %s\n' "$1" "$3"; pass=$((pass+1))
        else printf '  FAIL   %-42s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }
sk () { printf '  skip   %-42s %s\n' "$1" "$2"; skipped=$((skipped+1)); }

# --- pick a subject -----------------------------------------------------------
# The ignored-file control needs a path that some .gitignore in that tree
# actually matches. A tree with no ignore rules cannot exercise T6, and passing
# T6 there by silence would be the exact class of false green this project keeps
# finding in its own tools.
SUBJ=""; IGN=""
for d in "$ROOT"/*/; do
    [ -d "$d/.git" ] || continue
    for cand in linux-2.6.30/rlxfw-tripwire-probe.o rtl819x/linux-2.6.30/rlxfw-tripwire-probe.o \
                rlxfw-tripwire-probe.o; do
        base="${cand%/*}"; [ "$base" = "$cand" ] && base="."
        [ -d "${d%/}/$base" ] || continue
        if git -C "${d%/}" check-ignore -q "$cand" 2>/dev/null; then
            SUBJ="${d%/}"; IGN="$cand"; break
        fi
    done
    [ -n "$SUBJ" ] && break
done

# 🔴 No vendor tree is NOT a reason to run nothing. Until 2026-08-28 this suite
# printed one skip line and `0 passed, 0 failed` on any machine without the GPL
# drops -- which is every CI runner -- so the step went green even if
# `vendor-tripwire.sh` had been deleted outright. Every case except T10 works on
# ANY git repository with an ignore rule in it, so build one.
SYNTHETIC=0
if [ -z "$SUBJ" ]; then
    SUBJ="$(mktemp -d)/subject"; SYNTHETIC=1
    mkdir -p "$SUBJ"
    git -C "$SUBJ" init -q 2>/dev/null
    git -C "$SUBJ" config user.email t@t; git -C "$SUBJ" config user.name t
    printf 'one\n' > "$SUBJ/a.txt"
    printf 'two\n' > "$SUBJ/b.txt"
    printf '*.o\n' > "$SUBJ/.gitignore"
    git -C "$SUBJ" add -A >/dev/null 2>&1
    git -C "$SUBJ" commit -qm init >/dev/null 2>&1
    IGN="rlxfw-tripwire-probe.o"
    if ! git -C "$SUBJ" check-ignore -q "$IGN" 2>/dev/null; then
        sk "the vendor trees" "32 cases: no vendor tree, and the synthetic subject could not be built either"
        printf 'RESULT: \033[32m0 passed, 0 failed\033[0m, %d skip line(s)\n' "$skipped"
        exit 0
    fi
fi
if [ -n "$(git -C "$SUBJ" status --porcelain=v1 --ignored=matching)" ]; then
    sk "the vendor trees" "32 cases: the subject tree is already dirty, and a tripwire tested on dirt measures nothing"
    printf 'RESULT: \033[32m0 passed, 0 failed\033[0m, %d skip line(s)\n' "$skipped"
    exit 0
fi

W="$(mktemp -d)"
cleanup () {
    rm -f "$SUBJ/$IGN" "$SUBJ/rlxfw-tripwire-untracked" 2>/dev/null
    git -C "$SUBJ" checkout -- . 2>/dev/null
    rm -rf "$W"
}
trap cleanup EXIT

# A tracked regular file to modify and to delete. Taken from the tree rather
# than named, so this does not rot when the pin moves.
VICTIM="$(git -C "$SUBJ" ls-files -- '*.README' '*.txt' '*.c' '*.h' 2>/dev/null | head -1)"
[ -z "$VICTIM" ] && VICTIM="$(git -C "$SUBJ" ls-files | head -1)"

echo "=== subject      $SUBJ$( [ "$SYNTHETIC" = 1 ] && echo '   (SYNTHETIC -- no vendor drop on this machine; every case but T10 still runs)' )"
echo "=== ignorable    $IGN"
echo "=== victim       $VICTIM"
echo
echo "=== T1 / T2: a clean run, and a FAILING command that writes nothing ==="
"$ME" --tree "$SUBJ" -- true >"$W/o1" 2>&1; ck "T1 clean cmd -> exit 0" 0 "$?"
ck "T1 verdict says CLEAN"          1 "$(grep -c 'CLEAN' "$W/o1" || true)"
"$ME" --tree "$SUBJ" -- sh -c 'exit 7' >"$W/o2" 2>&1; ck "T2 failing cmd -> exit 1" 1 "$?"
ck "T2 tree still called CLEAN"     1 "$(grep -c 'CLEAN' "$W/o2" || true)"
ck "T2 verdict carries cmd-rc=7"    1 "$(grep -c 'cmd-rc=7' "$W/o2" || true)"

echo
echo "=== T3: an untracked file appears -> TRIPPED ==="
"$ME" --tree "$SUBJ" -- sh -c "touch '$SUBJ/rlxfw-tripwire-untracked'" >"$W/o3" 2>&1
ck "T3 exit 2"                      2 "$?"
ck "T3 names the path"              1 "$(grep -c 'rlxfw-tripwire-untracked' "$W/o3" || true)"
rm -f "$SUBJ/rlxfw-tripwire-untracked"

echo
echo "=== T4: a tracked file is modified -> TRIPPED ==="
"$ME" --tree "$SUBJ" -- sh -c "printf 'x' >> '$SUBJ/$VICTIM'" >"$W/o4" 2>&1
ck "T4 exit 2"                      2 "$?"
ck "T4 reports it as M"             1 "$(grep -cE '^ +M ' "$W/o4" || true)"
git -C "$SUBJ" checkout -- .

echo
echo "=== T5: a tracked file is DELETED -> TRIPPED   (the incident's shape) ==="
"$ME" --tree "$SUBJ" -- sh -c "rm -f '$SUBJ/$VICTIM'" >"$W/o5" 2>&1
ck "T5 exit 2"                      2 "$?"
ck "T5 reports it as D"             1 "$(grep -cE '^ +D ' "$W/o5" || true)"
git -C "$SUBJ" checkout -- .

echo
echo "=== T6: an IGNORED file appears -> TRIPPED, and plain git status is blind ==="
"$ME" --tree "$SUBJ" -- sh -c "touch '$SUBJ/$IGN'" >"$W/o6" 2>&1
ck "T6 exit 2"                      2 "$?"
touch "$SUBJ/$IGN"
ck "T6 plain git status: 0 lines"   0 "$(git -C "$SUBJ" status --porcelain=v1 | wc -l | tr -d ' ')"
ck "T6 with --ignored: 1 line"      1 "$(git -C "$SUBJ" status --porcelain=v1 --ignored=matching | wc -l | tr -d ' ')"
rm -f "$SUBJ/$IGN"

echo
echo "=== T7: mtime-only write -> TOUCHED, and --no-mtime turns that detector off ==="
"$ME" --tree "$SUBJ" -- sh -c "touch '$SUBJ/$VICTIM'" >"$W/o7" 2>&1
ck "T7 exit 5"                      5 "$?"
ck "T7 verdict says TOUCHED"        1 "$(grep -c 'TOUCHED' "$W/o7" || true)"
ck "T7 git alone saw nothing"       0 "$(git -C "$SUBJ" status --porcelain=v1 --ignored=matching | wc -l | tr -d ' ')"
"$ME" --tree "$SUBJ" --no-mtime -- sh -c "touch '$SUBJ/$VICTIM'" >"$W/o7b" 2>&1
ck "T7 --no-mtime -> exit 0"        0 "$?"
ck "T7 --no-mtime says CLEAN"       1 "$(grep -c 'CLEAN' "$W/o7b" || true)"

echo
echo "=== T8 / T9: the two refusals ==="
mkdir -p "$W/notgit"
"$ME" --tree "$W/notgit" -- true >"$W/o8" 2>&1; ck "T8 not a git repo -> exit 3" 3 "$?"
touch "$SUBJ/rlxfw-tripwire-untracked"
"$ME" --tree "$SUBJ" -- true >"$W/o9" 2>&1;      ck "T9 already dirty -> exit 4" 4 "$?"
ck "T9 the command was NOT run"     0 "$(grep -c 'cmd-rc' "$W/o9" || true)"
rm -f "$SUBJ/rlxfw-tripwire-untracked"

echo
echo "=== T11: git itself fails -> REFUSED, not CLEAN ==="
# A directory that has a .git but is not a repository. `git status` fails, writes
# nothing, and two empty snapshots compare equal -- so before 2026-08-28 this
# certified an unreadable tree as CLEAN.
mkdir -p "$W/fakegit/.git"
"$ME" --tree "$W/fakegit" -- true >"$W/o11" 2>&1
ck "T11 exit 3 (refused)"           3 "$?"
ck "T11 never says CLEAN"           0 "$(grep -c 'CLEAN' "$W/o11" || true)"

echo
echo "=== T12: --check, both directions ==="
"$ME" --tree "$SUBJ" --check >"$W/o12" 2>&1
ck "T12 clean tree -> exit 0"       0 "$?"
ck "T12 says CLEAN"                 1 "$(grep -c 'CLEAN' "$W/o12" || true)"
touch "$SUBJ/rlxfw-tripwire-untracked"
"$ME" --tree "$SUBJ" --check >"$W/o12b" 2>&1
ck "T12 dirty tree -> exit 4"       4 "$?"
ck "T12 says DIRTY"                 1 "$(grep -c 'DIRTY' "$W/o12b" || true)"
rm -f "$SUBJ/rlxfw-tripwire-untracked"

echo
echo "=== T13: the default tree discovery, which every case above bypassed ==="
if [ "$SYNTHETIC" = 1 ]; then
    sk "T13 default discovery" "2 cases: the default path reads \$FWRE_WORK/rebuild/src-vendor, and this run has a synthetic subject instead"
else
# Every T1-T12 passes --tree explicitly, so a mutant that discovered one tree
# instead of all of them passed the whole suite. This is the documented default
# invocation and it had no case at all.
"$ME" --check >"$W/o13" 2>&1
ck "T13 default discovery -> exit 0" 0 "$?"
ntrees=$(sed -n 's/.*CLEAN *\([0-9]*\) tree(s).*/\1/p' "$W/o13")
ndisk=$(find "$ROOT" -mindepth 2 -maxdepth 2 -name .git -type d 2>/dev/null | wc -l | tr -d ' ')
ck "T13 watches every git tree on disk" "$ndisk" "${ntrees:-0}"
fi

echo
echo "=== T10: the incident's own binary ==="
LIVEBIN="$(ls "$ROOT"/*/toolchain/*/bin/rsdk-linux-config 2>/dev/null | head -1)"
if [ "$LIVE" -eq 1 ] && [ -x "$LIVEBIN" ]; then
    "$ME" --tree "$SUBJ" -- "$LIVEBIN" --version >"$W/o10" 2>&1
    ck "T10 rsdk-linux-config --version -> exit 2" 2 "$?"
    git -C "$SUBJ" checkout -- . 2>/dev/null
    git -C "$SUBJ" clean -fdX -q 2>/dev/null
    ck "T10 tree restored afterwards"  0 "$(git -C "$SUBJ" status --porcelain=v1 --ignored=matching | wc -l | tr -d ' ')"
elif [ -x "$LIVEBIN" ]; then
    sk "T10 the incident's own binary" "2 cases: needs --live; it damages and restores 2,580 files"
else
    sk "T10 the incident's own binary" "2 cases: no rsdk-linux-config under \$FWRE_WORK"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skip line(s)\n' "$pass" "$fail" "$skipped"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skip line(s)\n' "$pass" "$skipped"
