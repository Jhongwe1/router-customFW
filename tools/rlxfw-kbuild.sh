#!/usr/bin/env bash
# Stage a kernel tree from src-vendor and build it.   R3-4's build driver.
#
#   rlxfw-kbuild.sh <cellname> [options]
#     --config FILE      .config to install VERBATIM.  Without it the
#                        .config is DERIVED from the board template plus
#                        config/rlxfw-kernel.delta -- see CFG-1 below.
#     --variant V        quiet | loud, the delta's two variants.  Required
#                        when deriving; refused together with --config.
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
#     --id-scope S       where -DRLXFW_SRC_ID goes: `global` (every C
#                        object, the default and what every measurement so
#                        far used) or `main` (init/main.o alone, where the
#                        only consumer is).  See INC-1 by the make line.
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
# CLAUDE.md: every bench command runs /usr/bin/python3 and never `python3`.
# 量 2026-09-02: `python3` resolves to ~/.venvs/thermal in a LOGIN shell and
# to /usr/bin elsewhere, so the same script works one way and not the other.
PY=${RLXFW_PYTHON:-/usr/bin/python3}
RSDK="toolchain/rsdk-1.3.6-4181-EB-2.6.30-0.9.30"

CELL=${1:?usage: rlxfw-kbuild.sh <cellname> [options]}
shift
CONFIG=""
VARIANT=""
OLDCONFIG=devnull
CFLAGS_KERNEL=""
INITRAMFS=""
TARGET=vmlinux
JOBS=$(nproc)
KEEP=0
MARKS=0
ID_SCOPE=global
NOCFLAGS=0
CFLAGS_GIVEN=0
NOSTAMP=0
DRYRUN=0
# 🔴 `napplied` has TWO writers -- the host-compat loop and the marks block --
# and the second silently shadows the first.  Nothing read it after the fact
# until the manifest below did, so it was harmless and invisible; the manifest
# is the first reader and it would have recorded the marks count under the
# patch count's name.  量 2026-09-04.  Separate names, same printed lines.
N_PATCHES=0
N_MARKS=0
while [ $# -gt 0 ]; do
    case "$1" in
        --config)        CONFIG="$2"; shift 2 ;;
        --variant)       VARIANT="$2"; shift 2 ;;
        --oldconfig)     OLDCONFIG="$2"; shift 2 ;;
        --cflags-kernel) CFLAGS_KERNEL="$2"; CFLAGS_GIVEN=1; shift 2 ;;
        --initramfs)     INITRAMFS="$2"; shift 2 ;;
        --target)        TARGET="$2"; shift 2 ;;
        --jobs)          JOBS="$2"; shift 2 ;;
        --keep)          KEEP=1; shift ;;
        --marks)         MARKS=1; shift ;;
        --id-scope)      ID_SCOPE=$2; shift 2 ;;
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

# 🔴 --id-scope is validated HERE for exactly that reason, and its first
# version was not: the `case` that rejects an unknown value sat beside the make
# invocation, so `--id-scope typo` would have staged 480 MB, run oldconfig and
# built 592 objects before saying the word was wrong.  Found on 2026-09-02 by
# reading this file's own comment above, in the same session that added the
# flag.
case "$ID_SCOPE" in
    global|main) ;;
    *) echo "$CELL: unknown --id-scope '$ID_SCOPE' (global|main)" >&2
       echo "  global -- -DRLXFW_SRC_ID on every C object (the default, and" >&2
       echo "            what every measurement so far was taken under)" >&2
       echo "  main   -- on init/main.o alone, where the only consumer is" >&2
       exit 3 ;;
esac

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
# 🔴 CFG-1's guard sits ABOVE THE STAGE and BELOW the two guards above it,
# and both halves of that are deliberate.
#
# Above the stage, for the reason the CFLAGS paragraph gives: lower down a
# refusal costs a 480 MB copy before it fires.  The .config is not written
# until much later, but WHICH SOURCE it comes from is decided by these
# lines and can be decided now, so --dry-run exercises them.
#
# 🔴 Below the cflags and stamp guards because it was first written above
# them, and 量: that made THIRTEEN cases of test-kbuild-cflags fail --
# every one named for a refusal this guard had started preempting
# (`C2 and it names --no-cflags in the refusal`, `S1 and it names
# --no-stamp`, ...).  A case that no longer reaches the guard it is named
# for has stopped testing what it says, and a new guard must not quietly
# take that over.  There is a reason beyond not breaking them: those two
# are about a DECLARED INPUT being missing or empty, which is a defect in
# the declaration; this one is about the CALLER not choosing between two
# variants the declaration offers.  The declaration is checked first.
if [ -n "$CONFIG" ] && [ -n "$VARIANT" ]; then
    echo "$CELL: --config and --variant are two sources for one file." >&2
    echo "  --config FILE takes the file as given; --variant derives it from" >&2
    echo "  the board template plus config/rlxfw-kernel.delta. Pick one." >&2
    exit 3
fi
if [ -z "$CONFIG" ] && [ -z "$VARIANT" ]; then
    echo "$CELL: no --config and no --variant." >&2
    echo "  With no --config the .config is DERIVED from the board template" >&2
    echo "  plus config/rlxfw-kernel.delta (CFG-1), and that delta declares" >&2
    echo "  two variants. Pass --variant quiet or --variant loud." >&2
    echo "  There is no default: they differ by CONFIG_PRINTK, so a silent" >&2
    echo "  choice between them is a silent choice of which image booted." >&2
    exit 3
fi
case "${VARIANT:-quiet}" in
    quiet|loud) ;;
    *) echo "$CELL: unknown --variant '$VARIANT' (quiet|loud)" >&2
       echo "  These are config/rlxfw-kernel.delta's own two names; " >&2
       echo "  kconfig-delta.py refuses an undeclared one rather than" >&2
       echo "  falling through to 'no variant', and so does this." >&2
       exit 3 ;;
esac


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

# ------------------------------------------- the initramfs, declared by CONTENT
# A spec names paths, modes and owners; gen_init_cpio reads the CONTENTS at
# build time.  mkinitramfs writes <name>.manifest.tsv beside each <name>.spec,
# and a spec with no such record is refused here, where --dry-run reaches it.
# What each digest covers and does not: the format-2 notes above write_manifest.
IRFS_MANIFEST=""
if [ -n "$INITRAMFS" ]; then
    [ -f "$INITRAMFS" ] || { echo "$CELL: no initramfs spec at $INITRAMFS" >&2; exit 3; }
    case "$INITRAMFS" in
        *.spec) IRFS_MANIFEST="${INITRAMFS%.spec}.manifest.tsv" ;;
        *) echo "$CELL: --initramfs $INITRAMFS is not <name>.spec, so no <name>.manifest.tsv records its contents" >&2; exit 3 ;;
    esac
    [ -f "$IRFS_MANIFEST" ] || { echo "$CELL: no $IRFS_MANIFEST beside the spec: nothing records which file CONTENTS this initramfs carries -- mkinitramfs.py build writes it" >&2; exit 3; }
    echo "== $CELL: initramfs contents <- $IRFS_MANIFEST"
fi

# --dry-run answers "what would this build be" without copying anything.  It
# exists so every guard above it is testable for free, and it is the only exit
# in this script that reports success without producing an image.
if [ "$DRYRUN" = 1 ]; then
    echo "== $CELL: --dry-run, nothing staged and nothing built"
    exit 0
fi

# ------------------------------------ what the two post-build gates read
# CFG-3 / TC-i, 2026-09-23 (P2-2).  Both gates were on no path until now: 量
# 2026-09-08, an undeclared CONFIG_GPIO_SYSFS rode three images (SPEC.md TC-47).
# Each reads the SAME file its generator half applies -- one variable per
# declaration, so the generator and the auditor cannot be pointed apart.
DELTA_FILE="$REPO/config/rlxfw-kernel.delta"
MARKS_DECL="$REPO/config/rlxfw-marks.tsv"
KDELTA="$REPO/tools/kconfig-delta.py"
MARKSPY="$HERE/rlxfw-marks.py"
# `verify`'s --absent inputs.  Under tools/, not config/: config/ is what
# RECIPE_ID digests, and this list changes no byte of any image (its header).
ABSENT_DECL="$REPO/tools/rlxfw-marks-absent.tsv"
ABSENT_FILES=(); ABSENT_SHAS=(); ABSENT_NAMES=()

# absent_refs -- check every row of $ABSENT_DECL against the file on disk; fill
# ABSENT_FILES/_SHAS/_NAMES in order and return 0, or name EVERY problem and
# return 3.  Called above the stage and again by run_gates at the point of use.
# 🔴 A missing or changed reference is a REFUSAL, never a skipped gate.
absent_refs() {
    local rows ln name rel bytes want p size got bad=0
    ABSENT_FILES=(); ABSENT_SHAS=(); ABSENT_NAMES=()
    if [ ! -f "$ABSENT_DECL" ]; then
        echo "$CELL: no $ABSENT_DECL." >&2
        echo "  It declares the vendor kernels rlxfw-marks verify reads as" >&2
        echo "  --absent. Without it the gate has nothing to be absent from," >&2
        echo "  and 'present in mine' alone is a label, not a discriminator." >&2
        return 3
    fi
    # awk checks the SHAPE of every row; the files are checked below.  -F'\t'
    # and not `read`: tab is IFS whitespace to `read`, so two tabs collapse
    # into one and an empty field would vanish instead of being refused.
    rows="$(awk -F'\t' '
        { sub(/\r$/, "") }
        /^#/ || /^[ \t]*$/ { next }
        NF != 5 { printf "BAD\tline %d: %d tab-separated field(s), expected 5 (name, relpath, bytes, sha256, role)\n", NR, NF; next }
        $1 == "" || $2 == "" || $3 == "" || $4 == "" || $5 == "" { printf "BAD\tline %d: an empty field\n", NR; next }
        $2 ~ /^\// || $2 ~ /(^|\/)\.\.(\/|$)/ { printf "BAD\tline %d: relpath %s is not a path under $FWRE_WORK\n", NR, $2; next }
        $3 !~ /^[0-9]+$/ { printf "BAD\tline %d: bytes %s is not a decimal count\n", NR, $3; next }
        length($4) != 64 || $4 !~ /^[0-9a-f]+$/ { printf "BAD\tline %d: sha256 %s is not 64 lower-case hex digits\n", NR, $4; next }
        ($1 in nm) { printf "BAD\tline %d: name %s is already used on line %d\n", NR, $1, nm[$1]; next }
        ($4 in dg) { printf "BAD\tline %d: its sha256 is also on line %d -- one artefact counted twice\n", NR, dg[$4]; next }
        { nm[$1] = NR; dg[$4] = NR; printf "ROW\t%s\t%s\t%s\t%s\n", $1, $2, $3, $4 }
    ' "$ABSENT_DECL")"
    while IFS= read -r ln; do
        case "$ln" in
            BAD$'\t'*)
                echo "$CELL: $ABSENT_DECL ${ln#BAD$'\t'}" >&2
                bad=$((bad+1)) ;;
            ROW$'\t'*)
                IFS=$'\t' read -r _ name rel bytes want <<< "$ln"
                p="$FWRE_WORK/$rel"
                if [ ! -f "$p" ]; then
                    echo "$CELL: $name: no file at \$FWRE_WORK/$rel" >&2
                    bad=$((bad+1)); continue
                fi
                size="$(stat -c %s "$p")"
                if [ "$size" != "$bytes" ]; then
                    echo "$CELL: $name: \$FWRE_WORK/$rel is $size bytes, the declaration says $bytes" >&2
                    bad=$((bad+1)); continue
                fi
                got="$(sha256sum "$p" | cut -d' ' -f1)"
                if [ "$got" != "$want" ]; then
                    echo "$CELL: $name: \$FWRE_WORK/$rel has sha256 ${got:0:16}..., the declaration says ${want:0:16}..." >&2
                    bad=$((bad+1)); continue
                fi
                ABSENT_FILES+=("$p"); ABSENT_SHAS+=("$got"); ABSENT_NAMES+=("$name") ;;
        esac
    done <<< "$rows"
    if [ "$bad" -ne 0 ]; then
        echo "  $bad problem(s) in the declared --absent inputs: the build is refused" >&2
        echo "  here -- verify neither runs on an undeclared input nor is skipped." >&2
        ABSENT_FILES=(); ABSENT_SHAS=(); ABSENT_NAMES=()
        return 3
    fi
    if [ "${#ABSENT_FILES[@]}" -eq 0 ]; then
        echo "$CELL: $ABSENT_DECL declares no reference image. verify with no" >&2
        echo "  --absent reports 'present in mine' and nothing else." >&2
        return 3
    fi
    return 0
}

# 🔴 BELOW --dry-run, unlike the other guards: the references live in
# $FWRE_WORK, which a CI runner lacks, so above the exit this would refuse every
# --dry-run case there.  Still ABOVE THE STAGE; the suite drives it with a fake
# $FWRE_WORK (A1-A10).  --target none builds nothing, so there is nothing to
# guard, and a refusal there would teach the reader to feed it something.
if [ "$TARGET" = none ]; then
    echo "== $CELL: --target none: nothing is built, so no gate runs and no reference is read"
else
    absent_refs || exit 3
    refs="$(for i in "${!ABSENT_NAMES[@]}"; do printf ' %s %s' "${ABSENT_NAMES[$i]}" "${ABSENT_SHAS[$i]:0:16}"; done)"
    echo "== $CELL: --absent references verified <- ${ABSENT_DECL#"$REPO"/}:$refs"
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
    N_PATCHES=$napplied
fi

# --------------------------------------------------------- rlxfw's boot marks
# R3-6.  The first lines of Realtek's source this project changes, declared one
# row at a time in config/rlxfw-marks.tsv with a reason each.  Applied to the
# STAGED tree, never to src-vendor (rlxfw-marks.py refuses a path under it).
# Off by default so that every measurement made before R3-6 can still be
# reproduced by the same driver.
if [ "$MARKS" = 1 ]; then
    # 🔴 --keep + --marks could not run at all until 2026-09-02 (R5-0), and
    # the failure did not read as a refusal: `apply` walks into A4 ("already
    # in this file; this tree is not clean") and the driver reports
    # `rlxfw-marks apply FAILED`. That combination is what INC-1 has to
    # measure, so --keep now asks for the idempotent path. It is NOT passed
    # on a fresh stage: a freshly staged tree must be clean, and a tool that
    # tolerates a dirty one there would hide a bad drop.
    MARKS_IF_NEEDED=""
    [ "$KEEP" = 1 ] && MARKS_IF_NEEDED="--if-needed"
    if ! "$PY" "$MARKSPY" apply \
            --decl "$MARKS_DECL" \
            --tree "$top" --src "$REPO/config/rlxfw-src" $MARKS_IF_NEEDED \
            > "$log.marks.log" 2>&1
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
    # 🔄 The pattern matched `mark(s) applied` until 2026-09-02. With
    # --if-needed the tool correctly says `already present` when it inserted
    # nothing, and the narrower pattern would have left $napplied empty and
    # killed the build -- a message getting MORE honest must not break its
    # reader.  The verb is captured too, so this line reports what happened
    # rather than always saying "applied".
    nline="$(sed -e 's/\x1b\[[0-9;]*m//g' "$log.marks.log" \
             | sed -n 's/^RESULT: \([0-9][0-9]*\) mark(s) \(.*\) and read back.*/\1 \2/p')"
    napplied="${nline%% *}"
    nverb="${nline#* }"
    [ -n "$napplied" ] || {
        echo "$CELL: rlxfw-marks printed no RESULT count" >&2
        tail -5 "$log.marks.log" >&2
        exit 3; }
    echo "== $CELL: $napplied declared row(s) from config/rlxfw-marks.tsv $nverb"
    N_MARKS=$napplied
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
#
# 🔄 CFG-1, 2026-09-04.  The default used to be the BARE board template, and
# that made a build's identity depend on whether the caller remembered to pass
# --config.  It is now the template with config/rlxfw-kernel.delta APPLIED --
# which is what every rlxfw image has actually been built from.
#
# WHY DERIVE RATHER THAN COMMIT THE RESOLVED FILE.  CFG-1 was opened saying
# "commit r51quiet.config-installed into config/".  That would make the
# repository hold two owners of one piece of state: the delta (a declaration,
# 35 rules with a reason each, against a baseline pinned by sha256) and a
# 26,931-byte artefact derived from it.  House rule 1 says one owner.
#
# 量 2026-09-04, before this was written: `kconfig-delta.py apply` on the
# pinned baseline (44f781de..., 26,548 bytes) produces a file BYTE-IDENTICAL
# to r51quiet.config-installed -- sha256 e6cdc47d9343001d..., 26,931 bytes,
# 15 set rules applied and 21 derive rules left to kconfig.  So the resolved
# config is a function of things already committed, and the fix is to compute
# it rather than to store it.
#
# ⚠️ THIS IS A BEHAVIOUR CHANGE AND IT IS MEASURED, NOT ASSUMED.  A plain
# invocation with no --config used to build 15 CONFIG symbols differently:
# BLK_DEV_INITRD, INITRAMFS_SOURCE/_ROOT_UID/_ROOT_GID/_COMPRESSION_{NONE,GZIP,
# BZIP2,LZMA}, MTD_CHAR, CMDLINE, DECOMPRESS_GZIP, PROBE_INITRD_HEADER,
# RD_GZIP, RD_BZIP2, RD_LZMA -- every one of them a row in the delta.  So the
# change makes the default agree with the declaration; it introduces no
# difference the declaration does not already carry.
#
# --variant is REQUIRED when deriving, and is refused when --config is given.
# The delta declares `quiet` and `loud`, and today no row is tagged @quiet --
# so omitting the flag and passing `quiet` produce the same bytes, and a
# default would be right by coincidence.  kconfig-delta's own C24 refuses a
# variant nobody declared for exactly this reason one layer down.
if [ -n "$CONFIG" ]; then
    cp "$CONFIG" "$DIR_LINUX/.config" || exit 3
    echo "== $CELL: .config <- $CONFIG"
else
    "$PY" "$KDELTA" apply \
        --baseline "$TEMPLATE" \
        --delta "$DELTA_FILE" \
        --variant "$VARIANT" \
        --out "$DIR_LINUX/.config" || {
        echo "$CELL: kconfig-delta apply FAILED" >&2; exit 3; }
    echo "== $CELL: .config <- board template + config/rlxfw-kernel.delta" \
         "[$VARIANT]"
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
    # The CONTENT record, copied beside the spec so the cell's own record holds
    # both; write_manifest digests this copy (initramfs_manifest_sha256).
    cp "$IRFS_MANIFEST" "$log.initramfs.manifest.tsv" || exit 3
    echo "== $CELL: contents sha256 $(sha256sum "$log.initramfs.manifest.tsv" | cut -c1-16)"
fi
# Without --initramfs, no initramfs record of an earlier build of this cell
# name may stand beside this one's .config.
[ -n "$INITRAMFS" ] || rm -f "$log.initramfs.spec" "$log.initramfs.spec.sha256" \
                             "$log.initramfs.manifest.tsv"

cd "$scratch" || exit 3

run() {          # run() <logsuffix> <cmd...>
    local sfx="$1"; shift
    bash "$TRIPWIRE" --quiet -- "$@" > "$log.$sfx.log" 2>&1
    local rc=$?
    echo "   $sfx rc=$rc"
    return $rc
}

# ------------------------------------------------------------- the manifest
# RECIPE-1, 2026-09-04.  `RLXFW-ID0` is a digest over `config/` and NOTHING
# ELSE, so two images built from one frozen `config/` with different `--config`
# print the same id.  量 the same day: `r51quiet` and `r51loud`, both
# `229d2983`, `.config-installed` e6cdc47d… against a49c254d…, `vmlinux`
# 2b0d1618… against 271ad13e….  (The pair this repository named until today
# was `r51a`/`r51quiet`, and that pair does NOT collide -- `r51a` compiled
# `078bb2b4`.)
#
# This file is the PROVENANCE record: what content went in, and -- since
# format 2, CFG-3 -- what the two declaration gates said about what came out.
# It is not the upload pin: `looprun --image-sha256` is, because a pin has to
# run on the desk beside the file about to be uploaded, and this file lives
# wherever the build happened.  What joins the two is `rtkimage.py build`'s
# record, which names this manifest's vmlinux digest and the nfjrom digest a
# card pins.
#
# 🔴 `config_sha256` digests `<cell>.config-installed`, the file that was
# COPIED IN, and never `<cell>.config-built`.  量 2026-09-04: two builds whose
# images are byte-identical have different `config-built` digests, because
# kconfig writes a wall-clock comment on line 4.  A manifest keyed on the
# post-oldconfig file would report every rebuild as a different recipe.
#
# Format 2 (2026-09-23) appends, never reorders:
#   variant              quiet | loud | -   (- is a --config build)
#   build_rc             the build step's status as vendor-tripwire.sh
#                        returns it: 1 make failed, 2/5 a vendor tree was
#                        touched, 4 one was dirty before make ran
#   kconfig_check        green | red | refused      (gate_verdict, below)
#   kconfig_check_rc     the tool's exit status, or - if it was not run
#   kconfig_check_result its RESULT line, SGR escapes removed; for `refused`,
#                        why, and the tool's last line if it ran
#   marks_verify, marks_verify_rc, marks_verify_result    the same three
#   marks_verify_absent  name=sha256 of every --absent file verify was given
#   initramfs_manifest_sha256  sha256 of <cell>.initramfs.manifest.tsv, the
#                        copy of mkinitramfs's content record for the spec
#                        (<name>.spec -> <name>.manifest.tsv); - without
#                        --initramfs; `missing` if given and not recorded
#   verdict              green, or not-green -- overall_verdict, the one rule
#                        that also decides the exit status and whether the
#                        `manifest ->` line is printed
#
# 🔴 WHAT THE TWO INITRAMFS DIGESTS COVER, 2026-09-23.  `initramfs_sha256` is
# the SPEC's digest: its text -- each entry's path, mode and owner and the
# source path gen_init_cpio will read -- and NOT any file's contents, which
# gen_init_cpio reads at build time.  量 the same day: _irfs-s100a and _irfs-p2
# hold byte-identical specs (7130245fbcd92afc) whose /init differ, 988 bytes
# e871efdd... against 2,153 bytes ef2c8797..., and this key said nothing.
# `initramfs_manifest_sha256` is the content-level digest: every file's bytes
# and sha256 as mkinitramfs read them (3a8bf014... against 51ea1604... for
# those two).  It is only as good as that read, made when the spec was
# written: a source changed between mkinitramfs and this build is in the
# image and not in the record, and nothing here re-reads the sources.  Its
# header also names the unit tree and the repository by absolute path, so the
# same contents recorded from another clone digest differently.
write_manifest() {          # write_manifest <vmlinux path>
    local vm="$1" m="$log.manifest" irm=-
    # `missing`, not `-`, when --initramfs was given and its record is not
    # here: an absent record must not read as "no initramfs".
    if [ -n "$INITRAMFS" ]; then
        irm=missing
        [ -f "$log.initramfs.manifest.tsv" ] && \
            irm="$(sha256sum "$log.initramfs.manifest.tsv" | cut -d' ' -f1)"
    fi
    {
        printf 'rlxfw-build-manifest\t2\n'
        printf 'cell\t%s\n'             "$CELL"
        printf 'recipe_id\t%s\n'        "$RECIPE_ID"
        printf 'config_sha256\t%s\n'    "$(sha256sum "$log.config-installed" | cut -d' ' -f1)"
        printf 'config_source\t%s\n'    "${CONFIG:-board-template}"
        if [ -n "$INITRAMFS" ]; then
            printf 'initramfs_sha256\t%s\n'  "$(cat "$log.initramfs.spec.sha256")"
            printf 'initramfs_source\t%s\n'  "$INITRAMFS"
        else
            printf 'initramfs_sha256\t-\n'
            printf 'initramfs_source\t-\n'
        fi
        printf 'cflags_kernel\t%s\n'    "$CFLAGS_KERNEL"
        printf 'id_scope\t%s\n'         "$ID_SCOPE"
        printf 'oldconfig\t%s\n'        "$OLDCONFIG"
        printf 'target\t%s\n'           "$TARGET"
        printf 'jobs\t%s\n'             "$JOBS"
        printf 'keep\t%s\n'             "$KEEP"
        printf 'stamp_epoch\t%s\n'      "${STAMP_EPOCH:--}"
        printf 'host_compat_patches\t%s\n' "$N_PATCHES"
        printf 'marks\t%s\n'            "$N_MARKS"
        printf 'drop\t%s\n'             "$(basename "$DROP")"
        printf 'vmlinux_sha256\t%s\n'   "$(sha256sum "$vm" | cut -d' ' -f1)"
        printf 'vmlinux_bytes\t%s\n'    "$(stat -c %s "$vm")"
        printf 'variant\t%s\n'              "${VARIANT:--}"
        printf 'build_rc\t%s\n'             "${BUILD_RC:--}"
        printf 'kconfig_check\t%s\n'        "${KCHECK_VERDICT:--}"
        printf 'kconfig_check_rc\t%s\n'     "${KCHECK_RC:--}"
        printf 'kconfig_check_result\t%s\n' "${KCHECK_RESULT:--}"
        printf 'marks_verify\t%s\n'         "${MVERIFY_VERDICT:--}"
        printf 'marks_verify_rc\t%s\n'      "${MVERIFY_RC:--}"
        printf 'marks_verify_result\t%s\n'  "${MVERIFY_RESULT:--}"
        printf 'marks_verify_absent\t%s\n'  "${MVERIFY_ABSENT:--}"
        printf 'initramfs_manifest_sha256\t%s\n' "$irm"
        printf 'verdict\t%s\n'              "$(overall_verdict)"
    } > "$m"
}

# ------------------------------------------------ the two declaration gates
# CFG-3 / TC-i.  "A build whose declaration was never checked must not reach
# a bench."  Both gates run after every build that leaves a vmlinux, their
# verdicts go into the manifest, and a build whose gates are not BOTH green
#
#   * exits 6, or the build step's own status if that was not 0 -- not 4,
#     because vendor-tripwire.sh already returns 1-5 for the build step and
#     its 4 means "a vendor tree was dirty"; and
#   * does NOT print `== <cell>: manifest -> <path>` -- it prints a
#     NOT FOR UPLOAD line that looprun's MANIFEST_RX does not match.
#
# 🔴 FAIL, NOT RECORD-ONLY, and the reason is the state CFG-3 was opened
# for.  Nothing reads these verdicts yet: looprun's S2 reads the exit status
# and the `manifest ->` line and nothing else, and a card pins an nfjrom.  A
# red verdict that only lands in a file is a gate on no path again -- the
# shape that carried CONFIG_GPIO_SYSFS through three images.  Failing puts it
# on the one path that exists: S2 refuses a non-zero exit, and no S3 means
# no nfjrom for a card to pin.  The manifest is STILL WRITTEN, red verdicts
# and all, because a red build is a result and its record is evidence; it
# overwrites any older manifest of the same cell name, so the file at
# <cell>.manifest always describes this run.
#
# What this does NOT establish:
#   * that the UPLOADED bytes carry the marks.  verify reads the linked ELF;
#     the nfjrom is assembled later by rtkimage (LZMA, where a count is 0 for
#     every image), and RUNSHEET P10's flat-image leg is not automated.
#   * anything about a --config build's variant.  --config and --variant are
#     refused together, so a --config build is checked against the rows
#     common to every variant: the loud .config given as --config is RED
#     here, and that is the declaration saying it does not know the file.
#   * anything about code generation.  A --no-cflags image, seven load-use
#     violations and all (TC-25), passes both gates; that is hazlint's
#     question.
# And a build without --marks is red by construction: its image carries none
# of the declared marks, verify says so, and it exits 6.  Such a build is for
# reproducing a pre-R3-6 measurement at the desk, never for a bench.

# gate_verdict <rc> <log>  ->  "<verdict><TAB><text>" on stdout.
#
# 🔴 A VERDICT NEEDS ITS RESULT LINE.  A Python traceback exits 1, which is
# also both tools' "red" status, so the status alone would file a crashed
# checker as a red build -- and a checker that exits 0 without saying what it
# found would be filed green.  So: green is status 0 with exactly one RESULT
# line, red is status 1 with exactly one, and everything else is `refused`
# (kconfig-delta: 2 when its own controls fail, 3 for die(); rlxfw-marks: 3).
# Tabs in the text become spaces, so a RESULT line cannot split a TSV row.
gate_verdict() {
    local rc="$1" lg="$2" clean n res
    clean="$(sed -e 's/\x1b\[[0-9;]*m//g' -e 's/\r$//' -e 's/\t/ /g' "$lg" 2>/dev/null)"
    n="$(printf '%s\n' "$clean" | grep -c '^RESULT: ')"
    res="$(printf '%s\n' "$clean" | grep '^RESULT: ' | tail -n 1)"
    if [ "$n" = 1 ] && [ "$rc" = 0 ]; then
        printf 'green\t%s\n' "$res"
    elif [ "$n" = 1 ] && [ "$rc" = 1 ]; then
        printf 'red\t%s\n' "$res"
    else
        res="$(printf '%s\n' "$clean" | grep -v '^[[:space:]]*$' | tail -n 1)"
        printf 'refused\t%d RESULT line(s) at rc=%s; last line: %s\n' "$n" "$rc" "${res:--}"
    fi
}

# run_gates -- sets KCHECK_* and MVERIFY_* for write_manifest.  Each gate's
# whole output goes to <cell>.kconfig-check.log / <cell>.marks-verify.log.
# An input that is missing is `refused` with the reason and the tool is not
# run: a traceback is not a verdict.
run_gates() {
    local kargs margs line pairs i
    KCHECK_RC=-;  KCHECK_VERDICT=refused;  KCHECK_RESULT=-
    MVERIFY_RC=-; MVERIFY_VERDICT=refused; MVERIFY_RESULT=-; MVERIFY_ABSENT=-
    # The .config the build USED, not the one copied in (kconfig-delta's C6).
    if [ ! -f "$log.config-built" ]; then
        KCHECK_RESULT="not run: there is no $log.config-built"
    else
        kargs=(check --baseline "$TEMPLATE" --delta "$DELTA_FILE"
               --built "$log.config-built")
        [ -n "$VARIANT" ] && kargs+=(--variant "$VARIANT")
        "$PY" "$KDELTA" "${kargs[@]}" > "$log.kconfig-check.log" 2>&1
        KCHECK_RC=$?
        line="$(gate_verdict "$KCHECK_RC" "$log.kconfig-check.log")"
        KCHECK_VERDICT="${line%%$'\t'*}"; KCHECK_RESULT="${line#*$'\t'}"
    fi
    echo "== $CELL: kconfig-delta check [${VARIANT:-no variant}] $KCHECK_VERDICT (rc=$KCHECK_RC): $KCHECK_RESULT"
    # The artefact, not the tree (rlxfw-marks.py's own header: `check` is the
    # weak question).  The references are re-checked HERE, at the point of
    # use, because the pre-stage check ran before a build that took minutes.
    if [ ! -f "$log.vmlinux.elf" ] || [ ! -f "$log.System.map" ]; then
        MVERIFY_RESULT="not run: there is no $log.vmlinux.elf or no $log.System.map"
    elif ! absent_refs; then
        MVERIFY_RESULT="not run: the declared --absent inputs no longer verify (see above)"
    else
        margs=(verify --decl "$MARKS_DECL" --image "$log.vmlinux.elf"
               --map "$log.System.map")
        pairs=""
        for i in "${!ABSENT_FILES[@]}"; do
            margs+=(--absent "${ABSENT_FILES[$i]}")
            pairs="$pairs${pairs:+,}${ABSENT_NAMES[$i]}=${ABSENT_SHAS[$i]}"
        done
        MVERIFY_ABSENT="$pairs"
        "$PY" "$MARKSPY" "${margs[@]}" > "$log.marks-verify.log" 2>&1
        MVERIFY_RC=$?
        line="$(gate_verdict "$MVERIFY_RC" "$log.marks-verify.log")"
        MVERIFY_VERDICT="${line%%$'\t'*}"; MVERIFY_RESULT="${line#*$'\t'}"
    fi
    echo "== $CELL: rlxfw-marks verify $MVERIFY_VERDICT (rc=$MVERIFY_RC): $MVERIFY_RESULT"
}

# overall_verdict -- the ONE rule.  The manifest's `verdict`, the exit status
# and the `manifest ->` line all come from here, so they cannot disagree.
overall_verdict() {
    if [ "${BUILD_RC:-}" = 0 ] && [ "${KCHECK_VERDICT:-}" = green ] \
       && [ "${MVERIFY_VERDICT:-}" = green ]; then
        echo green
    else
        echo not-green
    fi
}

# finish_build -- print the line looprun reads, or one it cannot mistake for
# it, and return the exit status.
finish_build() {
    local m="$log.manifest"
    if [ "$(overall_verdict)" = green ]; then
        echo "== $CELL: manifest -> $m"
        return 0
    fi
    echo "== $CELL: NOT FOR UPLOAD -- build rc=${BUILD_RC:--}," \
         "kconfig-delta check ${KCHECK_VERDICT:--}," \
         "rlxfw-marks verify ${MVERIFY_VERDICT:--}; the record is $m"
    [ "${KCHECK_VERDICT:-}" = green ] || [ ! -f "$log.kconfig-check.log" ] \
        || tail -n 12 "$log.kconfig-check.log" >&2
    [ "${MVERIFY_VERDICT:-}" = green ] || [ ! -f "$log.marks-verify.log" ] \
        || tail -n 12 "$log.marks-verify.log" >&2
    if [ "${BUILD_RC:-1}" != 0 ]; then
        return "${BUILD_RC:-1}"
    fi
    return 6
}

# Every file the gates and the manifest read is THIS run's.  A previous build
# of the same cell name left .config-built, .vmlinux.elf, .System.map and
# .manifest here, and the map is copied below with `2>/dev/null`: without
# this, a build that produced no System.map would be verified against the
# last one, and a build that failed would leave the last manifest standing.
rm -f "$log.config-built" "$log.vmlinux.elf" "$log.System.map" \
      "$log.manifest" "$log.kconfig-check.log" "$log.marks-verify.log"

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
#
# 🔴 AND REACHING EVERY OBJECT IS WHAT MAKES AN INCREMENTAL R5 ITERATION COST
# A FULL BUILD.  量 2026-09-02 (INC-1, R5-0): editing one file under
# config/rlxfw-src/ moves RECIPE_ID, which moves 592 command lines, and
# kbuild's arg-check -- working since 0004 -- rebuilds all of them: 592 CC /
# 32.58 s against 3 CC / 11.75 s for the SAME edit made where RECIPE_ID does
# not move.  The identity string, not the build system, is the cost.
#
# --id-scope main passes it to init/main.o alone, which is where the sole
# consumer lives (grep over the staged tree: one hit, init/main.c:576).
# `global` stays the default because it is what every measurement so far was
# taken under; changing a default silently is how a reproducibility claim
# stops meaning anything.
# The value was validated above the stage; this dispatch is total by
# construction and does not repeat the refusal -- a second copy of the allowed
# set is a second owner of it.
case "$ID_SCOPE" in
    global) set -- "$@" "KCPPFLAGS=-DRLXFW_SRC_ID=0x$RECIPE_ID" ;;
    main)   set -- "$@" "CFLAGS_main.o=-DRLXFW_SRC_ID=0x$RECIPE_ID" ;;
esac
echo "== $CELL: $*"
run build "$@" < /dev/null
rc=$?

out="$DIR_LINUX/vmlinux"
if [ -f "$out" ]; then
    cp "$out" "$log.vmlinux.elf"
    cp "$DIR_LINUX/System.map" "$log.System.map" 2>/dev/null
    echo "== OUTPUT $(stat -c %s "$out") bytes  sha256 $(sha256sum "$out" | cut -c1-16)"
    BUILD_RC=$rc
    run_gates
    write_manifest "$out"
    finish_build
    rc=$?
else
    echo "== NO vmlinux"
    [ "$rc" -eq 0 ] && rc=9
fi
exit $rc
