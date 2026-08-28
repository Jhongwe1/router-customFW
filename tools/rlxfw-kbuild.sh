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
#     --marks            apply config/rlxfw-marks.tsv to the staged tree
#                        (R3-6's boot ladder; off by default so every
#                        pre-R3-6 measurement stays reproducible here)
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
while [ $# -gt 0 ]; do
    case "$1" in
        --config)        CONFIG="$2"; shift 2 ;;
        --oldconfig)     OLDCONFIG="$2"; shift 2 ;;
        --cflags-kernel) CFLAGS_KERNEL="$2"; shift 2 ;;
        --initramfs)     INITRAMFS="$2"; shift 2 ;;
        --target)        TARGET="$2"; shift 2 ;;
        --jobs)          JOBS="$2"; shift 2 ;;
        --keep)          KEEP=1; shift ;;
        --marks)         MARKS=1; shift ;;
        *) echo "unknown option $1" >&2; exit 3 ;;
    esac
done

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
    echo "== $CELL: applied $(grep -c '^  B\|^  MK\|^  IN' "$log.marks.log") declared boot mark row(s)"
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

# ------------------------------------------------------------------ build
if [ "$TARGET" = "none" ]; then
    echo "== $CELL: build SKIPPED"
    exit 0
fi
set -- make -C "$DIR_LINUX" -j"$JOBS" "$TARGET"
[ -n "$CFLAGS_KERNEL" ] && set -- "$@" "CFLAGS_KERNEL=$CFLAGS_KERNEL"
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
