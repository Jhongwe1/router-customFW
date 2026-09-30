#!/usr/bin/env bash
# mkbusybox.sh -- build rlxfw's own busybox 1.13.4 for the RTL8196E.   R7.
#
# Until this existed, config/rlxfw-initramfs.tsv's /bin/busybox row was tagged
# `unit`: THIS DEVICE's own vendor binary, 273,332 bytes, v1.13.4, with eleven
# symlinks pointing at it.  That single row is why docs/KNOWN-ISSUES.md cannot
# say the userspace is rlxfw's.  This script builds the same version from the
# vendor GPL drop's own source with the 4181 toolchain, and the applet set it
# installs is a DECLARATION (config/rlxfw-busybox.config), not a leftover.
#
# The shape is tools/rlxfw-kbuild.sh's, and that file owns the reasons this one
# repeats without restating: why the tree is re-staged rather than cleaned (a
# failed build leaves .o files newer than their .c and kbuild's .cmd files make
# the next run believe they were built with the flags now in force), why cwd is
# a scratch directory (rsdk-linux-* writes offset.tmp into the current
# directory, and one landed in the repository root on 2026-08-28), and why a
# patch that does not apply STOPS the build instead of being skipped.
#
#   mkbusybox.sh [options]
#     --config FILE   the .config to install VERBATIM.
#                     default: config/rlxfw-busybox.config
#     --out DIR       where busybox, busybox.unstripped and the record go.
#                     default: $FWRE_WORK/rebuild/rlxfw-user/busybox/out
#     --stage DIR     staging root.  default: $FWRE_WORK/rebuild/rlxfw-user/busybox
#     --drop NAME     which src-vendor tree to take the source from.
#                     default: rtl819x-toolchain (SOURCES.json role `base`)
#     --ref NAME      the SECOND drop the staged source is diffed against.
#                     default: saturn49-wecb.  `--ref none` REFUSES: see G1.
#     --jobs N        -j (default: 4 -- one build at a time on this desk)
#     --keep          reuse an existing staged tree             [TESTING ONLY]
#     --dry-run       print the declared inputs and exit 0 BEFORE staging
#
# WHY THERE IS A SECOND DROP AND NOT A sha256 LIST (G1).
# busybox-1.13 ships in THREE of the trees under src-vendor/.  量 2026-09-30:
# their SOURCE is byte-identical (`diff -rq`, 0 differences); the only
# difference is that the `base` drop has been BUILT IN PLACE at some point and
# carries fourteen build products (.config, .config.old, include/autoconf.h,
# include/applet_tables.h, include/bbconfigopts.h, include/usage_compressed.h,
# include/config/, docs/BusyBox.{1,html}, docs/busybox.net/BusyBox.html,
# scripts/basic/{docproc,fixdep,split-include}, scripts/kconfig/conf).  So the
# stage deletes those fourteen and then proves the remainder EQUALS a different
# drop.  That is stronger than a digest list this script would also own: a
# digest list can be edited to match whatever is on disk, and two independent
# clones agreeing cannot.
# 🔴 It is also the guard against the worst failure mode here: a stale
# include/autoconf.h from the vendor's own build would silently decide the
# applet set, and the .config installed below would say nothing.
#
# WHAT THIS DOES NOT ESTABLISH.  Nothing about codegen on the die.  qemu
# certifies logic; hazlint certifies one hazard class over the words it can
# reach; neither is the silicon.  And the applet TABLE holding a name does not
# mean the applet works or that any option of it works -- SPEC.md FW-42
# measured `grep` present and `grep -E` absent on the vendor build.
set -o nounset

FWRE_WORK=${FWRE_WORK:-/home/key/fwre-work}
SV="$FWRE_WORK/rebuild/src-vendor"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${RLXFW_REPO:-$(cd "$HERE/.." && pwd)}"
TRIPWIRE="$HERE/vendor-tripwire.sh"
PY=${RLXFW_PYTHON:-/usr/bin/python3}
TCROOT="$SV/rtl819x-toolchain/toolchain"
TC=${TC:-rsdk-1.3.6-4181-EB-2.6.30-0.9.30}
TCBIN="$TCROOT/$TC/bin"

CONFIG="$REPO/config/rlxfw-busybox.config"
STAGE="$FWRE_WORK/rebuild/rlxfw-user/busybox"
OUT=""
DROP=rtl819x-toolchain
REF=saturn49-wecb
JOBS=4
KEEP=0
DRYRUN=0

# The subdirectory each drop keeps busybox-1.13 under.  Two shapes, because the
# toolchain drop has no rtl819x/ level and the two SDK drops do.
drop_src () { # <drop name> -> the busybox source directory, or empty
    local d="$SV/$1"
    [ -d "$d/users/busybox-1.13" ] && { printf '%s\n' "$d/users/busybox-1.13"; return 0; }
    [ -d "$d/rtl819x/users/busybox-1.13" ] && { printf '%s\n' "$d/rtl819x/users/busybox-1.13"; return 0; }
    return 1
}

# The fourteen build products the base drop carries.  Listed, never globbed: a
# glob would also delete a source file whose name happened to match, and this
# list is the thing G1 then proves complete.
PRODUCTS=(
    .config .config.old
    docs/BusyBox.1 docs/BusyBox.html docs/busybox.net/BusyBox.html
    include/applet_tables.h include/autoconf.h include/bbconfigopts.h
    include/usage_compressed.h
    scripts/basic/docproc scripts/basic/fixdep scripts/basic/split-include
    scripts/kconfig/conf
)
PRODUCT_DIRS=( include/config )

# gcc 13 compiles kconfig's gperf-generated zconf.hash.c, where
# `kconf_id_lookup` is a bare `__inline` definition.  Under C99 inline
# semantics -- gcc's default since 5.x -- a bare `inline` definition emits NO
# external symbol, so `HOSTLD scripts/kconfig/conf` dies with
# "undefined reference to `kconf_id_lookup'".  量 2026-09-30, this host's gcc
# 13.3.0.  -fgnu89-inline restores the semantics the file was written for.
# This is a HOST flag: it reaches no target byte.  It is here and not in a
# patch because the source is correct for its own era and a patch would have
# to be carried for every host gcc after this one.
HOSTCFLAGS_RLXFW='-Wall -Wstrict-prototypes -Os -fomit-frame-pointer -fgnu89-inline'

# SPEC-R7 § 2, userspace target flags, and NO -march: the rsdk wrapper's
# default is the 4181 core, and -march=mips32 miscompiles the exposed load
# delay slot silently.  busybox's own Makefile.flags already supplies
# -std=gnu99, -Os (CONFIG_DEBUG=n) and -static (CONFIG_STATIC=y), which G4
# checks rather than assumes; EXTRA_CFLAGS carries what it does not.
# 讀 scripts/Makefile.lib:89 -- `_c_flags = $(CFLAGS) $(EXTRA_CFLAGS)
# $(CFLAGS_$(*F).o)`, so a command-line EXTRA_CFLAGS reaches every object.
EXTRA_CFLAGS_RLXFW='-fno-builtin -fno-strict-aliasing -fno-common'

# The forbidden imports.  `system` and `popen` are SPEC-R7 § 2's ban; `execl`,
# `execlp` and `execvp` are the brief's, and each is a real hazard and not a
# style rule: execl/execle are variadic (an argv assembled at a call site
# rather than declared), execlp/execvp search PATH.  uClibc 0.9.30's system()
# is itself `execl("/bin/sh", "sh", "-c", line, NULL)`, which is why removing
# one call site removes two names.
FORBIDDEN=( system popen pclose execl execlp execvp )
# EXEMPT BY NAME, with the control that goes red when the exemption stops
# being needed (CLAUDE.md).  networking/udhcp/script.c's udhcp_run_script()
# is `execle(client_config.script, client_config.script, name, NULL, envp)`:
# a two-element argv built from a typed path and one of four literal event
# names, no shell and no PATH.  SPEC-R7 § 3 depends on it -- udhcpc runs
# `/sbin/ifupd`.  G6 refuses if ANY other object reaches for it.
EXEMPT_SYM=execle
EXEMPT_OBJ=networking/udhcp/script.o

while [ $# -gt 0 ]; do
    case "$1" in
        --config)  CONFIG="$2"; shift 2 ;;
        --out)     OUT="$2"; shift 2 ;;
        --stage)   STAGE="$2"; shift 2 ;;
        --drop)    DROP="$2"; shift 2 ;;
        --ref)     REF="$2"; shift 2 ;;
        --jobs)    JOBS="$2"; shift 2 ;;
        --keep)    KEEP=1; shift ;;
        --dry-run) DRYRUN=1; shift ;;
        *) echo "mkbusybox.sh: unknown option $1" >&2; exit 3 ;;
    esac
done
[ -n "$OUT" ] || OUT="$STAGE/out"

die () { echo "mkbusybox: $*" >&2; exit 3; }

# ---------------------------------------------------------- guards above the
# stage.  A refusal below this point costs a 9 MB copy and a four-minute
# build first, and a refusal nobody can afford to test is one nobody tests.
[ -x "$TRIPWIRE" ] || die "no vendor-tripwire.sh at $TRIPWIRE"
[ -x "$TCBIN/mips-linux-gcc" ] || die "no mips-linux-gcc under $TCBIN"
[ -f "$CONFIG" ] || die "no .config at $CONFIG"
[ -x "$REPO/tools/hazlint" ] || die "no tools/hazlint at $REPO/tools/hazlint"

SRC_DROP="$(drop_src "$DROP")" || die "no busybox-1.13 under \$FWRE_WORK/rebuild/src-vendor/$DROP"
if [ "$REF" = none ]; then
    echo "mkbusybox: --ref none is REFUSED.  G1 proves the staged source is" >&2
    echo "  pristine by diffing it against a SECOND drop; without one, a stale" >&2
    echo "  include/autoconf.h in the base drop would decide the applet set and" >&2
    echo "  the installed .config would say nothing.  Name a drop." >&2
    exit 3
fi
[ "$REF" != "$DROP" ] || die "--ref $REF is --drop: one tree compared with itself proves nothing"
SRC_REF="$(drop_src "$REF")" || die "no busybox-1.13 under \$FWRE_WORK/rebuild/src-vendor/$REF"

# The .config is a DECLARATION, so the two facts the target build rests on are
# read out of it here, above the stage, rather than trusted later.
grep -qx 'CONFIG_STATIC=y' "$CONFIG" \
  || die "$CONFIG does not set CONFIG_STATIC=y; this image has no dynamic loader for a busybox of mine"
XPREFIX="$(sed -n 's/^CONFIG_CROSS_COMPILER_PREFIX="\(.*\)"$/\1/p' "$CONFIG")"
[ "$XPREFIX" = "mips-linux-" ] \
  || die "$CONFIG declares CROSS_COMPILER_PREFIX='$XPREFIX'; this build needs mips-linux- (the 4181 rsdk)"
# G4a, and it tests the real value rather than grepping for a literal: no
# -march reaches the compiler from anywhere this script controls.
case " $EXTRA_CFLAGS_RLXFW " in *" -march"*)
    die "EXTRA_CFLAGS carries a -march; this build takes the rsdk driver's 4181 default" ;;
esac
if grep -q '^CONFIG_EXTRA_CFLAGS=.*-march' "$CONFIG" 2>/dev/null; then
    die "$CONFIG smuggles a -march through CONFIG_EXTRA_CFLAGS"
fi

PATCHDIR="$REPO/config/busybox-patches"
N_PATCH_DECL=0
if [ -d "$PATCHDIR" ]; then
    for pf in "$PATCHDIR"/*.patch; do [ -e "$pf" ] && N_PATCH_DECL=$((N_PATCH_DECL+1)); done
fi

CFG_SHA="$($PY -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$CONFIG")"
echo "== mkbusybox: source   $SRC_DROP   (--drop $DROP)"
echo "== mkbusybox: witness  $SRC_REF   (--ref $REF)"
echo "== mkbusybox: toolchain $TC   (gcc $("$TCBIN/mips-linux-gcc" -dumpversion 2>/dev/null || echo '?'))"
echo "== mkbusybox: .config  $CONFIG   sha256 ${CFG_SHA:0:16}"
echo "== mkbusybox: patches  $N_PATCH_DECL declared in config/busybox-patches/"
echo "== mkbusybox: flags    EXTRA_CFLAGS=[$EXTRA_CFLAGS_RLXFW]  (no -march)"
echo "== mkbusybox: stage    $STAGE     out $OUT"

if [ "$DRYRUN" = 1 ]; then
    echo "== mkbusybox: --dry-run, nothing staged and nothing built"
    exit 0
fi

SRC="$STAGE/src"
SCRATCH="$STAGE/scratch"
LOG="$STAGE/log"
STAMP="$STAGE/.staged"          # written LAST; its absence means "partial"
mkdir -p "$STAGE" "$SCRATCH" "$LOG" "$OUT" || die "cannot create $STAGE"

# ------------------------------------------------------------------- G0 stage
# 🔴 A PARTIALLY STAGED TREE IS REFUSED, NOT REPAIRED.  The stamp file carries
# the source path and the patch count it was staged with, and it is written
# only after the last patch applies.  So an interrupted stage -- a killed cp, a
# patch that failed -- leaves $SRC present and $STAMP absent, and --keep on
# that tree refuses instead of building something whose provenance nobody can
# state.  Without --keep the tree is deleted and re-staged, which is the only
# single-variable answer.
if [ "$KEEP" = 1 ]; then
    [ -d "$SRC" ] || die "--keep but there is no staged tree at $SRC"
    [ -f "$STAMP" ] || die "--keep but $SRC has no $STAMP: the tree is PARTIALLY STAGED (an interrupted cp, or a patch that failed). Re-run without --keep; this script does not repair a tree it cannot describe."
    echo "== mkbusybox: REUSING $SRC  [$(cat "$STAMP")]"
else
    if [ -d "$SRC" ] && [ ! -f "$STAMP" ]; then
        echo "== mkbusybox: $SRC is partially staged (no $STAMP); deleting it"
    fi
    rm -f "$STAMP"
    rm -rf "${SRC:?}"
    mkdir -p "$(dirname "$SRC")"
    cp -a "$SRC_DROP" "$SRC" || die "cp -a $SRC_DROP failed"

    # --- delete the base drop's in-place build products, by name
    n_removed=0
    for p in "${PRODUCTS[@]}"; do
        [ -e "$SRC/$p" ] && { rm -f "$SRC/$p" && n_removed=$((n_removed+1)); }
    done
    for p in "${PRODUCT_DIRS[@]}"; do
        [ -e "$SRC/$p" ] && { rm -rf "$SRC/$p" && n_removed=$((n_removed+1)); }
    done
    echo "== mkbusybox: removed $n_removed in-place build product(s) from the staged copy"

    # --- G1: the staged source EQUALS a second, independent drop
    if ! diff -rq "$SRC" "$SRC_REF" > "$LOG/g1.diff" 2>&1; then
        echo "== mkbusybox: G1 FAILED -- the staged source is not $REF's:" >&2
        head -20 "$LOG/g1.diff" >&2
        echo "  Either a product this script does not name is still in the tree," >&2
        echo "  or the two drops genuinely differ and which one is 1.13.4 is now" >&2
        echo "  an open question.  Nothing is built." >&2
        exit 3
    fi
    # A comparison that cannot fail is not a comparison.  Show it seeing one.
    printf 'rlxfw G1 control\n' > "$SRC/.rlxfw-g1-control"
    if diff -rq "$SRC" "$SRC_REF" > /dev/null 2>&1; then
        rm -f "$SRC/.rlxfw-g1-control"
        die "G1's comparison cannot see an added file; it proves nothing"
    fi
    rm -f "$SRC/.rlxfw-g1-control"
    echo "== mkbusybox: G1 staged source == $REF's byte for byte (and the diff was shown finding a planted file)"

    # --- G2: every declared patch applies, in name order, or the build stops
    n_applied=0
    if [ -d "$PATCHDIR" ]; then
        for pf in "$PATCHDIR"/*.patch; do
            [ -e "$pf" ] || continue
            if ! (cd "$SRC" && patch -p1 --forward --silent < "$pf"); then
                echo "== mkbusybox: G2 FAILED -- patch did not apply: $pf" >&2
                echo "  A partially patched tree builds, and what it builds is not" >&2
                echo "  what config/busybox-patches/ describes.  Nothing is built." >&2
                exit 3
            fi
            n_applied=$((n_applied+1))
        done
    fi
    [ "$n_applied" = "$N_PATCH_DECL" ] \
      || die "G2: $n_applied of $N_PATCH_DECL declared patches applied"
    echo "== mkbusybox: G2 applied $n_applied of $N_PATCH_DECL declared patch(es)"
    printf 'src=%s ref=%s patches=%d config=%s\n' \
        "$SRC_DROP" "$SRC_REF" "$n_applied" "$CFG_SHA" > "$STAMP"
fi

# ------------------------------------------------------------------ .config
cp "$CONFIG" "$SRC/.config" || die "cannot install $CONFIG"
cp "$CONFIG" "$LOG/config-installed"

export PATH="$TCBIN:$PATH"
cd "$SCRATCH" || die "cannot cd $SCRATCH"

run () { # run <logname> <cmd...>
    local sfx="$1"; shift
    bash "$TRIPWIRE" --quiet -- "$@" > "$LOG/$sfx.log" 2>&1
    local rc=$?
    echo "   $sfx rc=$rc"
    return $rc
}

# G3: `make oldconfig` must not change the declaration.  kconfig rewrites line
# 4 with the wall clock on every run (量 2026-09-30: two consecutive oldconfig
# runs differ in that line and nothing else), so the comparison excludes the
# leading comment block and is shown refusing a real change first.
run oldconfig make -C "$SRC" oldconfig HOSTCC=gcc HOSTCFLAGS="$HOSTCFLAGS_RLXFW" \
  || die "make oldconfig failed; see $LOG/oldconfig.log"
body () { grep -v '^#' "$1" | grep -v '^$'; }
if ! diff <(body "$CONFIG") <(body "$SRC/.config") > "$LOG/g3.diff"; then
    echo "== mkbusybox: G3 FAILED -- oldconfig changed the declaration:" >&2
    head -30 "$LOG/g3.diff" >&2
    echo "  config/rlxfw-busybox.config must be a RESOLVED .config: a symbol" >&2
    echo "  kconfig has to decide is a symbol this repository has not declared." >&2
    exit 3
fi
if diff <(body "$CONFIG") <(printf 'CONFIG_RLXFW_G3_CONTROL=y\n'; body "$CONFIG") > /dev/null; then
    die "G3's comparison cannot see an added symbol; it proves nothing"
fi
echo "== mkbusybox: G3 oldconfig changed no declared symbol (and the comparison was shown seeing a planted one)"

# ------------------------------------------------------------- the build stamp
# 🔴 量 2026-09-30, two back-to-back runs of this script: the stripped binaries
# are the same 456,344 bytes and differ in EXACTLY ONE BYTE, at offset 444087 --
# the seconds digit of `BusyBox v1.13.4 (2026-09-30 09:28:29 CST)`.  讀
# libbb/messages.c:17, `BB_EXTRA_VERSION BB_BT`, and Makefile.flags,
# `-DBB_BT=AUTOCONF_TIMESTAMP`: kconfig writes AUTOCONF_TIMESTAMP into
# include/autoconf.h from the wall clock, so busybox's banner is a clock
# reading.  Same defect P4a found in the kernel (84 bytes there), same fix:
# one declared epoch, rendered with LC_ALL and TZ pinned so the stamp is a
# property of the declaration and not of the desk.
#
# The rewrite is to a GENERATED FILE in the staged tree -- include/autoconf.h
# is kconfig's output, not vendor source -- which is why it is not a patch.  It
# happens AFTER oldconfig so autoconf.h is newer than .config and the build
# does not regenerate it; G7 below reads the artefact rather than trusting that.
STAMP_FILE="$REPO/config/rlxfw-build-stamp"
[ -f "$STAMP_FILE" ] || die "no $STAMP_FILE: without a declared epoch this build embeds the wall clock and two builds of one tree do not match"
STAMP_EPOCH="$(sed -e 's/#.*//' "$STAMP_FILE" | tr -d ' \t' | grep -xE '[0-9]+' | head -1)"
[ -n "$STAMP_EPOCH" ] || die "$STAMP_FILE declares no epoch; it is refused rather than guessed"
STAMP_RENDERED="$(LC_ALL=C TZ=UTC date -u -d "@$STAMP_EPOCH" '+%Y-%m-%d %H:%M:%S UTC')"
run autoconf make -C "$SRC" include/autoconf.h HOSTCC=gcc HOSTCFLAGS="$HOSTCFLAGS_RLXFW" \
  || die "could not generate include/autoconf.h"
AC="$SRC/include/autoconf.h"
[ -f "$AC" ] || die "no $AC after the autoconf step"
n_ts=$(grep -c '^#define AUTOCONF_TIMESTAMP ' "$AC" || true)
[ "$n_ts" = 1 ] || die "expected exactly one AUTOCONF_TIMESTAMP line in $AC, found $n_ts"
sed -i "s|^#define AUTOCONF_TIMESTAMP .*|#define AUTOCONF_TIMESTAMP \"$STAMP_RENDERED\"|" "$AC"
grep -qxF "#define AUTOCONF_TIMESTAMP \"$STAMP_RENDERED\"" "$AC" \
  || die "the AUTOCONF_TIMESTAMP rewrite did not take"
touch "$AC"
echo "== mkbusybox: stamp $STAMP_EPOCH [$STAMP_RENDERED]  <- ${STAMP_FILE#"$REPO"/}"

# --------------------------------------------------------------------- build
run build make -C "$SRC" -j"$JOBS" busybox \
    HOSTCC=gcc HOSTCFLAGS="$HOSTCFLAGS_RLXFW" EXTRA_CFLAGS="$EXTRA_CFLAGS_RLXFW"
BUILD_RC=$?
ELF="$SRC/busybox_unstripped"
BIN="$SRC/busybox"
[ "$BUILD_RC" = 0 ] || { tail -30 "$LOG/build.log" >&2; die "the build failed (rc=$BUILD_RC)"; }
[ -f "$ELF" ] && [ -f "$BIN" ] || die "the build reported success and left no busybox"

# G4b: the flags the .config was trusted for actually reached the link.  讀
# busybox Makefile.flags: CONFIG_STATIC=y adds -static to CFLAGS_busybox, so a
# PT_INTERP here means the declaration and the artefact disagree.
NINTERP=$("$TCBIN/mips-linux-readelf" -l "$ELF" | grep -c INTERP || true)
[ "$NINTERP" = 0 ] || die "G4b: a PT_INTERP in a build declaring CONFIG_STATIC=y"
EFLAGS=$("$TCBIN/mips-linux-readelf" -h "$ELF" | sed -n 's/^ *Flags: *//p')
case "$EFLAGS" in *mips1*) ;; *) die "G4b: e_flags [$EFLAGS] do not say mips1" ;; esac
ENDIAN=$("$TCBIN/mips-linux-readelf" -h "$ELF" | awk -F': *' '/^ *Data:/{print $2}')
case "$ENDIAN" in *"big endian"*) ;; *) die "G4b: not big endian ($ENDIAN)" ;; esac
echo "== mkbusybox: G4 static, no PT_INTERP, big-endian, e_flags [$EFLAGS]"

# G5: hazlint over the linked ELF.  0 violations, and hazlint's own controls
# are what make the 0 a claim rather than a silence.
echo '--- G5: hazlint ---'
HAZLINT_CHILD=1 "$PY" "$REPO/tools/hazlint" "$ELF" > "$LOG/hazlint.log" 2>&1
HAZ_RC=$?
sed -e 's/\x1b\[[0-9;]*m//g' "$LOG/hazlint.log" | grep -E '^(RESULT|  VIOLATIONS|  loads)' || true
[ "$HAZ_RC" = 0 ] || { tail -20 "$LOG/hazlint.log" >&2; die "G5: hazlint refused the linked ELF"; }

# G6: the forbidden imports, from the symbol table of the unstripped link, and
# the exemption swept BOTH WAYS.
echo '--- G6: forbidden imports ---'
"$TCBIN/mips-linux-nm" "$ELF" > "$LOG/nm.txt" 2>&1 || die "G6: nm failed on $ELF"
# The positive control FIRST: the same nm on the same libc.a must SHOW these
# names, or a clean report means only that nm stopped working.
CTRL_LIB="$TCROOT/$TC/lib/libc.a"
[ -f "$CTRL_LIB" ] || die "G6: no $CTRL_LIB to run the positive control against"
"$TCBIN/mips-linux-nm" "$CTRL_LIB" > "$LOG/nm-libc.txt" 2>&1 || die "G6: nm failed on libc.a"
for s in "${FORBIDDEN[@]}"; do
    n=$(awk -v s="$s" '$NF==s && $(NF-1)!="U"' "$LOG/nm-libc.txt" | wc -l)
    [ "$n" -gt 0 ] || die "G6: the control cannot see '$s' even in libc.a; the scan proves nothing"
done
echo "   control: all ${#FORBIDDEN[@]} forbidden names ARE visible in $TC's libc.a"
bad=0
for s in "${FORBIDDEN[@]}"; do
    hits=$(awk -v s="$s" '$NF==s' "$LOG/nm.txt")
    n=$(printf '%s' "$hits" | grep -c . || true)
    if [ "$n" -gt 0 ]; then
        echo "   FORBIDDEN  $s:"; printf '%s\n' "$hits" | sed 's/^/     /'
        bad=$((bad+1))
    else
        echo "   clean      $s"
    fi
done
[ "$bad" = 0 ] || die "G6: $bad forbidden import(s) in the linked ELF"
# The named exemption, and its control: execle is admitted ONLY as
# networking/udhcp/script.o's.  A second user, or none at all, is a refusal --
# swept both ways, so the exemption cannot outlive its reason.
users=$(find "$SRC" -name '*.o' -print0 \
        | xargs -0 -r "$TCBIN/mips-linux-nm" -A -u 2>/dev/null \
        | awk -v s="$EXEMPT_SYM" '$NF==s{print $1}' \
        | sed -e "s|^$SRC/||" -e 's/:$//' | sort -u)
echo "   exempt     $EXEMPT_SYM referenced by: ${users:-<nothing>}"
if [ -z "$users" ]; then
    die "G6: nothing references $EXEMPT_SYM any more -- the exemption has outlived its reason and must be deleted from this script"
fi
if [ "$users" != "$EXEMPT_OBJ" ]; then
    die "G6: $EXEMPT_SYM is reached from more than $EXEMPT_OBJ: [$users]"
fi

# G7: the DECLARED stamp is in the artefact, and the host's clock is not.  The
# banner is the only place BB_BT reaches in this applet set (讀 libbb/messages.c;
# fsck.c and vi.c also print it and neither applet is built), so this is the
# whole of what makes two builds of one declaration byte-identical.
echo '--- G7: the declared stamp reached the binary ---'
WANT_BANNER="BusyBox v1.13.4 ($STAMP_RENDERED)"
n=$(strings -a "$BIN" | grep -cxF "$WANT_BANNER" || true)
[ "$n" = 1 ] || die "G7: the stripped binary does not carry [$WANT_BANNER] exactly once (found $n)"
# and the control: the same counter must see a string that IS there, and must
# NOT see today's date -- a stamp check that cannot fail is not a check.
TODAY="$(LC_ALL=C TZ=UTC date -u '+%Y-%m-%d')"
if [ "$TODAY" != "${STAMP_RENDERED%% *}" ]; then
    n=$(strings -a "$BIN" | grep -cF "BusyBox v1.13.4 ($TODAY" || true)
    [ "$n" = 0 ] || die "G7: the binary carries a banner dated today ($TODAY); the rewrite did not reach the link"
fi
echo "   banner [$WANT_BANNER], and no banner dated $TODAY"

# ------------------------------------------------------------------- install
cp -f "$ELF" "$OUT/busybox.unstripped"
cp -f "$BIN" "$OUT/busybox"
SZ_S=$(stat -c %s "$OUT/busybox")
SZ_U=$(stat -c %s "$OUT/busybox.unstripped")
SHA=$(sha256sum "$OUT/busybox" | cut -d' ' -f1)
{
    printf 'rlxfw-busybox-build\t1\n'
    printf 'version\t%s\n'        "$(sed -n 's/^SUBLEVEL = /1.13./p' "$SRC/Makefile" | head -1)"
    printf 'drop\t%s\n'           "$DROP"
    printf 'ref_drop\t%s\n'       "$REF"
    printf 'toolchain\t%s\n'      "$TC"
    printf 'config_sha256\t%s\n'  "$CFG_SHA"
    printf 'patches\t%s\n'        "$N_PATCH_DECL"
    printf 'stamp_epoch\t%s\n'    "$STAMP_EPOCH"
    printf 'banner\t%s\n'         "$WANT_BANNER"
    printf 'extra_cflags\t%s\n'   "$EXTRA_CFLAGS_RLXFW"
    printf 'bytes_stripped\t%s\n' "$SZ_S"
    printf 'bytes_unstripped\t%s\n' "$SZ_U"
    printf 'sha256\t%s\n'         "$SHA"
    printf 'e_flags\t%s\n'        "$EFLAGS"
    printf 'hazlint\t%s\n'        "$(sed -e 's/\x1b\[[0-9;]*m//g' "$LOG/hazlint.log" | sed -n 's/^RESULT: //p')"
    printf 'exempt\t%s=%s\n'      "$EXEMPT_SYM" "$EXEMPT_OBJ"
} > "$OUT/busybox.build"
echo "== mkbusybox: $OUT/busybox  $SZ_S bytes stripped ($SZ_U unstripped)"
echo "== mkbusybox: sha256 $SHA"
echo "== mkbusybox: record -> $OUT/busybox.build"
exit 0
