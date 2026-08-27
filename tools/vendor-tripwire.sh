#!/usr/bin/env bash
# Did running that vendor binary write into the vendor source trees?
#
# 量 2026-08-28, and the tool exists because of it: a census that ran every
# executable in the three rsdk `bin/` directories with `--version` was not a
# read-only operation. `rsdk-linux-config` is not a program that prints a
# version -- it is a statically linked i386 ELF that runs `make` inside the
# tree it lives in. Sixteen seconds of `--version` deleted **2,580 tracked files** from a pinned vendor clone -- and the first
# version of this header called them "2,580 tracked symlinks under
# `config/uclibc/include/bits/`", which is impossible: 讀 the index, that
# directory holds **93** tracked symlinks per tree and the whole of
# `config/uclibc` holds **132**. The 2,580 are overwhelmingly regular files
# across `libc/`, `libm/`, `include/` and `lib/`; at most 264 of them (every
# tracked symlink under `config/uclibc` in both 1.3.6 trees) can be symlinks.
# The characterisation was generalised from the first forty lines of a
# `git status` that had 2,584.
# It also rewrote four tracked files and left seventeen ignored build products
# (量: the seventeen paths were listed with their mtimes at the time; a later
# reproduction under different starting state counted differently, which is
# recorded in `LOG.md` rather than reconciled). Nothing warned. The damage was found
# only because `git status` was run afterwards on a hunch, and it was
# recoverable only because the tree is a clone pinned at a known sha.
#
# The trees under `src-vendor/` are the material this project reads. A silent
# write into one of them does not announce itself later; it comes back as a
# measurement that disagrees with a measurement taken last week, with no way to
# tell which one was taken on the real thing.
#
# So: wrap the command, snapshot before and after, and refuse to certify
# anything you cannot attribute.
#
# TWO INDEPENDENT DETECTORS, because either alone has a blind spot:
#
#   git    `git status --porcelain=v1 --ignored=matching` per tree. `--ignored`
#          is load-bearing and not decoration: seventeen of the files the
#          incident created were ignored by a nested `.gitignore`, and a plain
#          `git status --porcelain` reports exactly zero of them. `T6` in
#          `test-vendor-tripwire.sh` pins that, in both directions.
#   mtime  A stamp file is created outside the tree immediately before the
#          command runs, and `find -newer` looks for anything that moved past
#          it. This catches the write git cannot see: the incident also touched
#          `lib/libc.so` and `lib/libpthread.so` -- same bytes, new mtime -- and
#          git called both of them unmodified, correctly and uselessly.
#
# WHERE IT FAILS, and none of these is hypothetical:
#   - It DETECTS. It does not prevent. By the time it fires, the write happened.
#   - A writer that restores both content and mtime defeats both detectors.
#     Nothing here would see it.
#   - It snapshots the moment the guarded command RETURNS. A command that
#     backgrounds a writer and exits is certified before that writer runs.
#     Nothing here waits for orphans, and the vendor build system does start
#     background jobs.
#   - It watches the declared trees only. A vendor binary that writes to $HOME,
#     to /tmp, or into `$FWRE_WORK/extracted/` is invisible to it. This is a
#     vendor-source tripwire, not a sandbox.
#   - Changes under `.git/` are deliberately not reported. `git status` writes
#     its own index; a tripwire that fires on its own detector is noise.
#   - On a tree that is ALREADY dirty it exits 4 and does not run the command,
#     because a diff taken against dirt cannot be attributed to anything. That
#     refusal is the point, not an inconvenience.
#
# Usage
#     vendor-tripwire.sh [OPTIONS] -- <command> [args...]
#     vendor-tripwire.sh [OPTIONS] --check
#
#     --tree DIR   a tree to watch. Repeatable. Default: every git repository
#                  directly under $FWRE_WORK/rebuild/src-vendor/.
#     --no-mtime   disable the second detector (git only).
#     --check      report cleanliness and exit; run no command.
#     --quiet      verdict line only. The verdict ALWAYS prints; --quiet drops
#                  the per-file detail under it.
#
# Exit
#     0  trees clean before and after; the command exited 0
#     1  trees clean; the command exited non-zero (its status is on the verdict)
#     2  TRIPPED -- a tree changed in a way git can see
#     3  refused -- no tree found, or a named tree is not a git repository
#     4  refused -- a tree was already dirty before the command ran
#     5  TOUCHED -- git sees no change, but a file's mtime advanced past the stamp
set -o nounset

TREES=()
DO_MTIME=1
MODE="run"
QUIET=0

while [ $# -gt 0 ]; do
    case "$1" in
        # Strip a trailing slash: `--tree /x/` makes the prune path `/x//.git`,
        # which `find -path` does not match, and the tool then trips on its own
        # detector writing the git index. Found by review, 2026-08-28.
        --tree)     TREES+=("${2%/}"); shift 2 ;;
        --no-mtime) DO_MTIME=0; shift ;;
        --check)    MODE="check"; shift ;;
        --quiet)    QUIET=1; shift ;;
        --)         shift; break ;;
        *) echo "vendor-tripwire.sh: unknown option $1" >&2; exit 3 ;;
    esac
done

# `--quiet` is documented as "verdict line only". It did the opposite: the
# verdicts went through `say` (suppressed) while the per-file detail was raw
# printf (kept). So the invocation this repository's own guidance prescribes
# printed everything except the answer. `verdict` always prints; `detail` is
# what --quiet drops.
verdict () { printf '%s\n' "$*"; }
detail () { [ "$QUIET" -eq 1 ] || printf '%s\n' "$*"; }

if [ ${#TREES[@]} -eq 0 ]; then
    ROOT="${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor"
    for d in "$ROOT"/*/; do
        [ -d "$d/.git" ] || continue
        TREES+=("${d%/}")
    done
fi

if [ ${#TREES[@]} -eq 0 ]; then
    echo "VENDOR-TRIPWIRE: SKIPPED  no git repository under \${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor" >&2
    exit 3
fi
for t in "${TREES[@]}"; do
    if [ ! -d "$t/.git" ]; then
        echo "VENDOR-TRIPWIRE: SKIPPED  not a git repository: $t" >&2
        exit 3
    fi
done

# One file per tree holding the porcelain lines. Written to $WORK, never into
# the tree being watched -- a tripwire that wrote inside its own subject would
# trip itself, which is a bug this nearly had.
# A failing `git status` writes an empty file, and two empty files compare
# equal -- so a tripwire that ignores git's exit status certifies a filthy tree
# as clean, silently, exactly when git is the thing that broke. Read the status.
snapshot () { # dest-dir  -> 0 ok, 1 a git invocation failed
    local dest="$1" t i=0 bad=0
    for t in "${TREES[@]}"; do
        if ! git -C "$t" status --porcelain=v1 --ignored=matching > "$dest/$i.txt" 2>"$dest/$i.err"; then
            bad=1
            printf 'VENDOR-TRIPWIRE: git status failed in %s: %s\n' \
                "$t" "$(head -1 "$dest/$i.err")" >&2
        fi
        i=$((i+1))
    done
    return "$bad"
}

report_tree_diff () { # before-dir after-dir
    local before="$1" after="$2" t i=0 n
    for t in "${TREES[@]}"; do
        n=$(diff "$before/$i.txt" "$after/$i.txt" 2>/dev/null | grep -c '^>' || true)
        if [ "$n" -gt 0 ]; then
            printf '  %s\n' "$t"
            diff "$before/$i.txt" "$after/$i.txt" 2>/dev/null | grep '^>' | sed 's/^> /    /' | head -12
            [ "$n" -gt 12 ] && printf '    ... and %d more\n' "$((n-12))"
            printf '    restore:  git -C %s checkout -- . && git -C %s clean -fdX\n' "$t" "$t"
        fi
        i=$((i+1))
    done
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/before" "$WORK/after"

if ! snapshot "$WORK/before"; then
    echo "VENDOR-TRIPWIRE: REFUSED  git could not read a watched tree; nothing can be attributed." >&2
    exit 3
fi
DIRTY=0
for f in "$WORK"/before/*.txt; do [ -s "$f" ] && DIRTY=1; done

if [ "$MODE" = "check" ]; then
    if [ "$DIRTY" -eq 1 ]; then
        verdict "VENDOR-TRIPWIRE: DIRTY  ${#TREES[@]} tree(s) watched"
        i=0; for t in "${TREES[@]}"; do
            n=$(wc -l < "$WORK/before/$i.txt" | tr -d ' ')
            [ "$n" -gt 0 ] && { detail "  $t  $n line(s)"; [ "$QUIET" -eq 1 ] || head -8 "$WORK/before/$i.txt" | sed 's/^/    /'; }
            i=$((i+1))
        done
        exit 4
    fi
    verdict "VENDOR-TRIPWIRE: CLEAN  ${#TREES[@]} tree(s) watched, 0 lines"
    exit 0
fi

if [ "$DIRTY" -eq 1 ]; then
    echo "VENDOR-TRIPWIRE: REFUSED  a watched tree is already dirty; a diff taken against dirt cannot be attributed." >&2
    i=0; for t in "${TREES[@]}"; do
        n=$(wc -l < "$WORK/before/$i.txt" | tr -d ' ')
        [ "$n" -gt 0 ] && { printf '  %s  %s line(s)\n' "$t" "$n" >&2; head -8 "$WORK/before/$i.txt" | sed 's/^/    /' >&2; }
        i=$((i+1))
    done
    echo "  the command was NOT run." >&2
    exit 4
fi

[ $# -eq 0 ] && { echo "vendor-tripwire.sh: nothing to run; use -- <command>" >&2; exit 3; }

STAMP="$WORK/stamp"
touch "$STAMP"
# One second, so that a filesystem or a program with coarse timestamps cannot
# produce a write that fails to be strictly newer than the stamp. Paid once per
# guarded command, not per case.
sleep 1

"$@"
CMDRC=$?

if ! snapshot "$WORK/after"; then
    echo "VENDOR-TRIPWIRE: REFUSED  cmd-rc=$CMDRC  git could not read a watched tree AFTER the command ran." >&2
    echo "  That is itself a change worth looking at. Nothing is certified." >&2
    exit 3
fi

CHANGED=0
i=0
for t in "${TREES[@]}"; do
    if ! cmp -s "$WORK/before/$i.txt" "$WORK/after/$i.txt"; then CHANGED=1; fi
    i=$((i+1))
done

if [ "$CHANGED" -eq 1 ]; then
    echo "VENDOR-TRIPWIRE: TRIPPED  cmd-rc=$CMDRC  a watched tree changed"
    report_tree_diff "$WORK/before" "$WORK/after"
    exit 2
fi

if [ "$DO_MTIME" -eq 1 ]; then
    TOUCHED=""
    for t in "${TREES[@]}"; do
        n=$(find "$t" -path "$t/.git" -prune -o -newer "$STAMP" -print 2>/dev/null | head -20)
        [ -n "$n" ] && TOUCHED="$TOUCHED$n"$'\n'
    done
    if [ -n "$TOUCHED" ]; then
        echo "VENDOR-TRIPWIRE: TOUCHED  cmd-rc=$CMDRC  git sees no change, but files moved past the stamp"
        printf '%s' "$TOUCHED" | sed 's/^/    /' | head -20
        exit 5
    fi
fi

verdict "VENDOR-TRIPWIRE: CLEAN  cmd-rc=$CMDRC  ${#TREES[@]} tree(s) watched"
[ "$CMDRC" -eq 0 ] && exit 0
exit 1
