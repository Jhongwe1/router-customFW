#!/usr/bin/env bash
# Stage a kernel tree from src-vendor and build it.   R3-4's build driver.
#
#   rlxfw-kbuild.sh <cellname> [options]
#     --config FILE      .config to install (default: the board template)
#     --oldconfig MODE   how `make oldconfig` gets its stdin:
#                          none      -- do not run oldconfig at all
#                          devnull   -- < /dev/null            (default)
#                          empty     -- yes '' |               (the banned one)
#                          no        -- yes n |
#                          yes       -- yes y |
#     --cflags-kernel S  passed as CFLAGS_KERNEL=S to the kernel make
#     --initramfs F     gen_init_cpio spec, staged to usr/rlxfw-initramfs.spec
#                       (the path CONFIG_INITRAMFS_SOURCE names, relative
#                       to the kernel directory, so nothing depends on
#                       where the scratch tree happens to live)
#     --target T         make target inside linux-2.6.30 (default: vmlinux)
#     --jobs N           -j (default: nproc)
#     --keep             do not re-stage if the cell already exists   [TESTING ONLY]
#     --no-cflags        build with an EMPTY CFLAGS_KERNEL, deliberately.
#                        Without it the flags come from config/rlxfw-cflags
#                        and an empty flag set is REFUSED -- see below.
#     --marks            apply config/rlxfw-marks.tsv to the staged tree
#                        (R3-6's boot ladder; off by default so every
#                        pre-R3-6 measurement stays reproducible here)
#     --no-stamp         build with the WALL CLOCK, deliberately.  Without it
#                        the stamp comes from config/rlxfw-build-stamp and a
#                        declaration with no epoch is REFUSED -- see below.
#                        A --no-stamp build is not reproducible and says so.
#     --dry-run          print the declared inputs -- flags, stamp, recipe id
#                        -- and exit 0 BEFORE staging anything.  Every guard
#                        above the stage is testable through it.
#
# WHY THE TREE IS RE-STAGED EVERY TIME AND NOT `rm vmlinux`.
# `r2ab-build.sh` learned this on userspace and it is worse here: a kernel
# build that failed with the wrong flags leaves .o files newer than their .c,
# and kbuild's .cmd files make the next run believe they were built with the
# flags now in force.  `make clean` does not remove include/config/auto.conf or
# .config, which is exactly the state R3-4 is measuring.  Only a fresh copy is
# single-variable.
#
# WHY cwd IS A SCRATCH DIRECTORY.
# `rsdk-linux-*` is a wrapper that writes `offset.tmp` into the current
# directory.  On 2026-08-28 one landed in the repository root, which no
# vendor-tree check watches.
set -o nounset

FWRE_WORK=${FWRE_WORK:-/home/key/fwre-work}
SV="$FWRE_WORK/rebuild/src-vendor"
DROP="$SV/rtl819x-toolchain"
R="$FWRE_WORK/rebuild/r3-4"
# The repository this script lives in, not a path typed into it.  Until
# 2026-08-28 this file was not in the repository at all, while two committed
# files (notes/kernel-build.md 8 and SPEC.md TC-26) asserted that "the build
# driver stops if a patch does not apply" -- a build-time gate with no
# implementation anyone could read.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${RLXFW_REPO:-$(cd "$HERE/.." && pwd)}"
TRIPWIRE="$HERE/vendor-tripwire.sh"
RSDK="toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30"

CELL=${1:?usage: rlxfw-kbuild.sh <cellname> [options]}
shift
CONFIG=""
OLDCONFIG=devnull
CFLAGS_KERNEL=""
INITRAMFS=""
TARGET=vmlinux
JOBS=$(nproc)
KEEP=0
MARKS=0
NOCFLAGS=0
CFLAGS_GIVEN=0
NOSTAMP=0
DRYRUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --config)        CONFIG="$2"; shift 2 ;;
        --oldconfig)     OLDCONFIG="$2"; shift 2 ;;
        --cflags-kernel) CFLAGS_KERNEL="$2"; CFLAGS_GIVEN=1; shift 2 ;;
        --initramfs)     INITRAMFS="$2"; shift 2 ;;
        --target)        TARGET="$2"; shift 2 ;;
        --jobs)          JOBS="$2"; shift 2 ;;
        --keep)          KEEP=1; shift ;;
        --marks)         MARKS=1; shift ;;
        --no-cflags)     NOCFLAGS=1; shift ;;
        --no-stamp)      NOSTAMP=1; shift ;;
        --dry-run)       DRYRUN=1; shift ;;
        *) echo "unknown option $1" >&2; exit 3 ;;
    esac
done

# --------------------------------------------------- CFLAGS_KERNEL, declared
# 🔴 R3-9, 2026-08-30.  `quietm` -- the image that booted -- could not be
# rebuilt from its own recorded configuration, and the whole difference was
# `-fno-if-conversion` (SPEC.md TC-25), which takes hazlint from SEVEN load-use
# violations to ZERO.  It reached the 2026-08-28 build as a flag typed at a
# shell: no committed file carried it and this script did not record it either.
# 量 the same day: the flagless rebuild has 7 violations and every gate in the
# repository stayed green.
#
# So the flags are a declared input now, an empty set has to be ASKED for, and
# the effective value is written beside <cell>.config-built.
#
# THE GUARD IS HERE, above the stage, on purpose.  Below it a refusal costs a
# 480 MB copy before it fires, and a refusal nobody can afford to test is one
# nobody tests.
CFLAGS_FILE="$REPO/config/rlxfw-cflags"
# 🔴 The first version of this guard tested `[ -n "$CFLAGS_KERNEL" ]`, so
# `--cflags-kernel ""` fell through to the declared file and was accepted -- the
# one request the file exists to refuse. Found by its own C2 control on the
# first run. It is the same distinction console-capture's N20 pins: a flag GIVEN
# with an empty value is not the flag being absent.
if [ "$CFLAGS_GIVEN" = 1 ]; then
    [ -n "$CFLAGS_KERNEL" ] || {
        echo "$CELL: --cflags-kernel was given an EMPTY value. If an empty" >&2
        echo "  CFLAGS_KERNEL is what you want, say --no-cflags: it is the" >&2
        echo "  same build and a different sentence in the log." >&2
        exit 3; }
    CFLAGS_SRC="--cflags-kernel"
elif [ "$NOCFLAGS" = 1 ]; then
    CFLAGS_SRC="--no-cflags (deliberately empty)"
else
    [ -f "$CFLAGS_FILE" ] || {
        echo "$CELL: no $CFLAGS_FILE, no --cflags-kernel and no --no-cflags." >&2
        echo "  An image built with an empty CFLAGS_KERNEL has SEVEN load-use" >&2
        echo "  violations in it (量 2026-08-30) and looks identical to a good" >&2
        echo "  one everywhere except hazlint. Ask for it, or declare it." >&2
        exit 3; }
    CFLAGS_KERNEL="$(sed -e 's/#.*//' "$CFLAGS_FILE" | tr '\n' ' ' \
                     | tr -s ' ' | sed -e 's/^ //' -e 's/ $//')"
    CFLAGS_SRC="$CFLAGS_FILE"
    [ -n "$CFLAGS_KERNEL" ] || {
        echo "$CELL: $CFLAGS_FILE declares no flags. That is not the same" >&2
        echo "  request as --no-cflags, and it is refused rather than guessed." >&2
        exit 3; }
fi
echo "== $CELL: CFLAGS_KERNEL=[$CFLAGS_KERNEL]  <- $CFLAGS_SRC"

# ------------------------------------------------- the build stamp, declared
# P4a, 2026-09-01.  Same shape as the CFLAGS block above and for the same
# reason: 量 the same day, two back-to-back builds of one tree differ in 84 of
# 3,935,472 bytes, and every one of those bytes is a clock reading.  Six are
# the kernel's own UTS_VERSION and 78 are gen_init_cpio's; one declared epoch
# settles both, which is why they are read from ONE file here rather than set
# in two places.
#
# The RENDERING is done here and not in the declaration.  `date` output carries
# a timezone name and a locale, so the same epoch reads `CST` on this machine
# and `UTC` on another; pinning LC_ALL and TZ is what makes the stamp a
# property of the declaration instead of a property of the desk.
STAMP_FILE="$REPO/config/rlxfw-build-stamp"
STAMP_EPOCH=""
if [ "$NOSTAMP" = 1 ]; then
    STAMP_SRC="--no-stamp (the wall clock, deliberately)"
else
    [ -f "$STAMP_FILE" ] || {
        echo "$CELL: no $STAMP_FILE and no --no-stamp." >&2
        echo "  Without a declared stamp this build embeds the wall clock in" >&2
        echo "  84 bytes (量 2026-09-01) and two builds of one tree do not" >&2
        echo "  match. Ask for the clock, or declare an epoch." >&2
        exit 3; }
    STAMP_EPOCH="$(sed -e 's/#.*//' "$STAMP_FILE" | tr -d ' \t' \
                   | grep -xE '[0-9]+' | head -1)"
    [ -n "$STAMP_EPOCH" ] || {
        echo "$CELL: $STAMP_FILE declares no epoch. That is not the same" >&2
        echo "  request as --no-stamp, and it is refused rather than guessed." >&2
        exit 3; }
    STAMP_SRC="$STAMP_FILE"
fi

# ------------------------------------------------------ the recipe's identity
# What `ID0` prints on the console, and it is derived rather than typed.  The
# anti-DoD's build-stamp leg loses its "WHICH of my builds" role the moment the
# stamp is frozen; this replaces it with a string computed from the declaration
# files themselves, so it moves when the recipe moves and needs no remembering.
#
# Paths are hashed RELATIVE to the repository root.  `sha256sum` prints the
# path beside the digest, and an absolute path would make the id a function of
# where the clone happens to live.
RECIPE_ID="$(cd "$REPO" && find config -type f -print0 | LC_ALL=C sort -z \
             | xargs -0 sha256sum | sha256sum | cut -c1-8)"

# 🔴 THE RENDERING HAPPENS HERE, ABOVE THE STAGE, AND THE PLACEMENT IS PART OF
# THE CLAIM.  It sat in the environment block until 2026-09-01, which is after
# a 480 MB tree copy -- so the one line that makes this stamp machine-
# independent could not be checked without paying for a stage, and it had no
# test at all.  Same lesson as console-capture's terminator guard: a refusal,
# or a claim, that costs a copy is one nobody exercises.
STAMP_RENDERED=""
[ -n "$STAMP_EPOCH" ] && \
    STAMP_RENDERED="$(LC_ALL=C TZ=UTC date -u -d "@$STAMP_EPOCH")"
echo "== $CELL: stamp=$STAMP_EPOCH [$STAMP_RENDERED] recipe=$RECIPE_ID  <- $STAMP_SRC"

# --dry-run answers "what would this build be" without copying anything.  It
# exists so every guard above it is testable for free, and it is the only exit
# in this script that reports success without producing an image.
if [ "$DRYRUN" = 1 ]; then
    echo "== $CELL: --dry-run, nothing staged and nothing built"
    exit 0
fi

cell="$R/cells/$CELL"
top="$cell/top"
scratch="$R/scratch/$CELL"
log="$R/out/$CELL"
mkdir -p "$R/cells" "$R/out" "$scratch"

[ -x "$TRIPWIRE" ] || { echo "no tripwire at $TRIPWIRE" >&2; exit 3; }
[ -d "$DROP/linux-2.6.30" ] || { echo "no drop at $DROP" >&2; exit 3; }

# ------------------------------------------------------------------ stage
if [ "$KEEP" = 1 ] && [ -d "$top/linux-2.6.30" ]; then
    echo "== $CELL: REUSING existing tree (--keep)"
else
    rm -rf "${cell:?}"
    mkdir -p "$top"
    cp -a "$DROP/linux-2.6.30" "$top/linux-2.6.30" || exit 3
    cp -a "$DROP/boards"       "$top/boards"       || exit 3
    mkdir -p "$top/toolchain"
    ln -s "$DROP/$RSDK" "$top/$RSDK" || exit 3
    ln -s boards/rtl8196e "$top/target" || exit 3
    mkdir -p "$top/target/romfs" "$top/target/tmpfs" "$top/target/image"
    # The TOP-LEVEL .config, which arch/rlx/bsp/Makefile:10 and
    # net/rtl/fastpath/Makefile both `include`.  Without it the build stops at
    # net/rtl/fastpath with "No rule to make target '<top>/.config'".  It is
    # normally written by config/mconf, a curses program; rlxfw states the
    # selections in config/rlxfw-sdk.config instead so the build has no step
    # that only a human at a terminal can perform.
    cp "$REPO/config/rlxfw-sdk.config" "$top/.config" || exit 3
    echo "== $CELL: staged from $DROP"
fi

TEMPLATE="$top/boards/rtl8196e/config.linux-2.6.30.RTL8196E_88E_GW"
[ -f "$TEMPLATE" ] || { echo "no board template" >&2; exit 3; }

# ------------------------------------------------- declared host-compat patches
# The build that was on disk on 2026-08-28 carried an UNDECLARED change to
# `kernel/timeconst.pl`.  Reproducing it needed a patch nothing in the repo
# named.  Every source change to the vendor tree now lives in
# config/host-compat/, is applied here, and a patch that does not apply stops
# the build rather than being skipped -- a partially patched tree builds, and
# what it builds is not what the patch list describes.
PATCHDIR="$REPO/config/host-compat"
if [ "$KEEP" != 1 ]; then
    napplied=0
    for pf in "$PATCHDIR"/*.patch; do
        [ -e "$pf" ] || continue
        if ! (cd "$top/linux-2.6.30" && patch -p1 --forward --silent < "$pf"); then
            echo "$CELL: host-compat patch FAILED: $pf" >&2
            exit 3
        fi
        napplied=$((napplied+1))
    done
    echo "== $CELL: applied $napplied declared host-compat patch(es)"
fi

# --------------------------------------------------------- rlxfw's boot marks
# R3-6.  The first lines of Realtek's source this project changes, declared one
# row at a time in config/rlxfw-marks.tsv with a reason each.  Applied to the
# STAGED tree, never to src-vendor (rlxfw-marks.py refuses a path under it).
# Off by default so that every measurement made before R3-6 can still be
# reproduced by the same driver.
if [ "$MARKS" = 1 ]; then
    if ! python3 "$HERE/rlxfw-marks.py" apply \
            --decl "$REPO/config/rlxfw-marks.tsv" \
            --tree "$top" --src "$REPO/config/rlxfw-src" > "$log.marks.log" 2>&1
    then
        echo "$CELL: rlxfw-marks apply FAILED" >&2
        tail -20 "$log.marks.log" >&2
        exit 3
    fi
    # 🔴 This counted `^  B\|^  MK\|^  IN` until 2026-09-01, which made this
    # line a SECOND owner of a number rlxfw-marks.py already prints -- and
    # `ID0` matches none of the three, so it would have reported 15 while 16
    # rows were applied. Read the tool's own RESULT, and refuse rather than
    # print an empty count: a blank where a number belongs reads as zero.
    napplied="$(sed -e 's/\x1b\[[0-9;]*m//g' "$log.marks.log" \
                | sed -n 's/^RESULT: \([0-9][0-9]*\) mark(s) applied.*/\1/p')"
    [ -n "$napplied" ] || {
        echo "$CELL: rlxfw-marks printed no RESULT count" >&2
        tail -5 "$log.marks.log" >&2
        exit 3; }
    echo "== $CELL: applied $napplied declared row(s) from config/rlxfw-marks.tsv"
fi

# ------------------------------------------------------------- environment
export DIR_ROOT="$top"
export DIR_RSDK="$DIR_ROOT/$RSDK"
export DIR_BOARD="$DIR_ROOT/target"
export DIR_ROMFS="$DIR_ROOT/target/romfs"
export DIR_TMPFS="$DIR_ROOT/target/tmpfs"
export DIR_IMAGE="$DIR_ROOT/target/image"
export DIR_LINUX="$DIR_ROOT/linux-2.6.30"
export PATH="$DIR_RSDK/bin:$PATH"
export CROSS_COMPILE=rsdk-linux-
if [ -n "$STAMP_EPOCH" ]; then
    # 讀 scripts/mkcompile_h:38 -- KBUILD_BUILD_TIMESTAMP replaces `date`.
    # host-compat/0002 -- RLXFW_CPIO_MTIME replaces gen_init_cpio's time(NULL).
    export KBUILD_BUILD_TIMESTAMP="$STAMP_RENDERED"
    export RLXFW_CPIO_MTIME="$STAMP_EPOCH"
    echo "== $CELL: KBUILD_BUILD_TIMESTAMP=[$KBUILD_BUILD_TIMESTAMP]"
else
    echo "== $CELL: NO declared stamp -- this build is NOT reproducible"
fi
[ -x "$DIR_RSDK/bin/rsdk-linux-gcc" ] || {
    echo "no rsdk-linux-gcc under $DIR_RSDK" >&2; exit 3; }

# ---------------------------------------------------------------- .config
if [ -n "$CONFIG" ]; then
    cp "$CONFIG" "$DIR_LINUX/.config" || exit 3
    echo "== $CELL: .config <- $CONFIG"
else
    cp "$TEMPLATE" "$DIR_LINUX/.config" || exit 3
    echo "== $CELL: .config <- board template"
fi
cp "$DIR_LINUX/.config" "$log.config-installed"

if [ -n "$INITRAMFS" ]; then
    [ -f "$INITRAMFS" ] || { echo "$CELL: no initramfs spec at $INITRAMFS" >&2; exit 3; }
    cp "$INITRAMFS" "$DIR_LINUX/usr/rlxfw-initramfs.spec" || exit 3
    # 🔄 2026-08-28, corrected by the adversarial pass: a MISSING spec file
    # does NOT fall back to `-d`.  讀 gen_initramfs_list.sh:197-222 --
    # input_file() ends "Cannot open" / exit 1, so the build fails loudly.
    # What falls back to `-d` -- an image holding one empty directory -- is
    # CONFIG_INITRAMFS_SOURCE="", because usr/Makefile:31 tests the STRING
    # and not the file.  That is the case this check catches: a .config whose
    # INITRAMFS_SOURCE is empty or points somewhere else builds a kernel that
    # panics "No init found" for a reason nothing to do with the contents.
    if grep -q '^CONFIG_INITRAMFS_SOURCE=' "$DIR_LINUX/.config"; then
        want='CONFIG_INITRAMFS_SOURCE="usr/rlxfw-initramfs.spec"'
        grep -qxF "$want" "$DIR_LINUX/.config" || {
            echo "$CELL: CONFIG_INITRAMFS_SOURCE is not $want" >&2
            grep '^CONFIG_INITRAMFS_SOURCE=' "$DIR_LINUX/.config" >&2
            exit 3; }
    else
        echo "$CELL: --initramfs given but the .config does not set CONFIG_INITRAMFS_SOURCE" >&2
        exit 3
    fi
    echo "== $CELL: initramfs spec <- $INITRAMFS ($(grep -c . "$INITRAMFS") entries)"
    # R3-9, 2026-08-30.  The build records the .config it used and, until now,
    # nothing about the initramfs -- so an image could be built from a spec that
    # no file in the repository still describes and nothing could say so.  The
    # spec and its digest go beside <cell>.config-built, which is what lets
    # `mkinitramfs verify` distinguish "this image is stale" from "the
    # declaration changed after it was built".
    cp "$INITRAMFS" "$log.initramfs.spec"
    sha256sum "$INITRAMFS" | cut -d" " -f1 > "$log.initramfs.spec.sha256"
    echo "== $CELL: spec sha256 $(cut -c1-16 < "$log.initramfs.spec.sha256")"
fi

cd "$scratch" || exit 3

run() {          # run() <logsuffix> <cmd...>
    local sfx="$1"; shift
    bash "$TRIPWIRE" --quiet -- "$@" > "$log.$sfx.log" 2>&1
    local rc=$?
    echo "   $sfx rc=$rc"
    return $rc
}

# ------------------------------------------------------------- oldconfig
case "$OLDCONFIG" in
    none) echo "== $CELL: oldconfig SKIPPED" ;;
    devnull)
        run oldconfig make -C "$DIR_LINUX" oldconfig < /dev/null ;;
    empty|no|yes)
        case "$OLDCONFIG" in
            empty) ans="" ;;
            no)    ans="n" ;;
            yes)   ans="y" ;;
        esac
        yes "$ans" | bash "$TRIPWIRE" --quiet -- \
            make -C "$DIR_LINUX" oldconfig > "$log.oldconfig.log" 2>&1
        echo "   oldconfig(yes '$ans') rc=$?" ;;
    *) echo "unknown --oldconfig $OLDCONFIG" >&2; exit 3 ;;
esac
[ -f "$DIR_LINUX/.config" ] && cp "$DIR_LINUX/.config" "$log.config-built"
# The build records what it COMPILED with, not only what it configured
# with. Until 2026-08-30 the second was recorded and the first was not.
printf '%s\n' "$CFLAGS_KERNEL" > "$log.cflags"

# ------------------------------------------------------------------ build
if [ "$TARGET" = "none" ]; then
    echo "== $CELL: build SKIPPED"
    exit 0
fi
set -- make -C "$DIR_LINUX" -j"$JOBS" "$TARGET"
[ -n "$CFLAGS_KERNEL" ] && set -- "$@" "CFLAGS_KERNEL=$CFLAGS_KERNEL"
# 讀 Makefile:572 -- KCPPFLAGS is appended to KBUILD_CPPFLAGS, so this reaches
# every C object.  `ID0` in config/rlxfw-marks.tsv is the only consumer, and a
# --marks build without this define does not compile: a build failure rather
# than an image whose identity string is wrong.
set -- "$@" "KCPPFLAGS=-DRLXFW_SRC_ID=0x$RECIPE_ID"
echo "== $CELL: $*"
run build "$@" < /dev/null
rc=$?

out="$DIR_LINUX/vmlinux"
if [ -f "$out" ]; then
    cp "$out" "$log.vmlinux.elf"
    cp "$DIR_LINUX/System.map" "$log.System.map" 2>/dev/null
    echo "== OUTPUT $(stat -c %s "$out") bytes  sha256 $(sha256sum "$out" | cut -c1-16)"
else
    echo "== NO vmlinux"
    [ "$rc" -eq 0 ] && rc=9
fi
exit $rc
