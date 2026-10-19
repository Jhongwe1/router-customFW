#!/usr/bin/env bash
# reproduce-l1.sh -- layer 1 of REPRODUCE.md: rebuild a release's image from its
# corresponding-source archive in an empty directory, and compare it with the
# image the release published.
#
#   reproduce-l1.sh pincheck --name NAME --tree DIR
#   reproduce-l1.sh build --assets DIR --release-json FILE --drop DIR
#                         --ref-drop DIR --root DIR [--release-vmlinux FILE]
#                         [--control-iperf3-path]
#
# `pincheck` answers one question: is DIR the tree REPRODUCE.md pins as NAME --
# HEAD the pinned commit, and `git status` empty, ignored files included?  A
# tree at the right commit with a file deleted or a build product left in it
# is not the pinned tree, and is refused.
#
# `build` takes four inputs and nothing else:
#   --assets, --release-json   the release's files and GitHub's description of
#                  them, as `tools/reproduce-l0.py fetch` wrote them; layer 0 is
#                  re-run on them first, controls included, and must pass.
#   --drop         a checkout of the vendor drop `rtl819x-toolchain` (the kernel,
#                  busybox and the toolchain), checked by `pincheck`.
#   --ref-drop     a checkout of `saturn49-wecb`, checked by `pincheck`.  No byte
#                  of it reaches the image: the archive's `tools/mkbusybox.sh`
#                  refuses to build busybox unless the staged source equals a
#                  second drop's copy (its gate G1), and the archive carries one.
# and --root, a directory that must not exist or must be empty, on a
# filesystem that keeps file modes.  Everything is written under --root.
#
# The environment is cleared: the script re-executes itself under `env -i`
# with exactly HOME (an empty directory under --root), PATH
# (/usr/sbin:/usr/bin:/sbin:/bin), LC_ALL=C, TZ=UTC, TMPDIR (under --root),
# PYTHONDONTWRITEBYTECODE=1 and FWRE_WORK (under --root), plus its own marker.
#
# The build is the archive's own tools, run as the release build ran them, with
# the steps the archive does not supply written here.  Each such step is a gap
# in the archive, and REPRODUCE.md lists them.  Every vendor binary runs under
# the archive's `tools/vendor-tripwire.sh`, from a scratch directory, at -j4.
#
# iperf3 embeds its absolute source directory in three assert() strings, so it
# is rebuilt at that directory, which is read out of the released image's own
# /bin/iperf3 (`tools/relimage.py srcdir`), never typed.  The build runs in a
# private mount namespace (`unshare --user --map-root-user --mount`) in which
# the staged tree is bind-mounted over that directory; outside the namespace
# the directory is not written, and if it holds files their digest is compared
# before and after.  The directory has to exist on this host to be a mount
# point: where it does not, the build refuses and says so.
#
# TWO CONTROLS, because an equal digest is a claim about the comparison too.
#   * Before anything is built, no file under the unpacked archive or the two
#     checkouts may already hold the bytes of one of the released initramfs's
#     ELF programs: a copy would compare equal without having been rebuilt.
#   * --control-iperf3-path builds iperf3 in the staged tree's own directory,
#     without the namespace.  The run must then come out DIFFERENT, in
#     /bin/iperf3 alone among the initramfs files: that shows the comparison
#     can fail and that the directory is the input that decides it.
#
# EXIT
#   0  the rebuilt image's sha256 equals the manifest's entry for the image;
#      with --control-iperf3-path, the control fired as predicted
#   1  it was rebuilt and differs (the comparison that locates the difference
#      is printed); with --control-iperf3-path, the control did not fire
#   3  refused before building: an input failed its check
#   4  a build step failed
#   5  the kernel build's verdict was not `recipient` (exit 7 and its line)
#
# WHAT IT DOES NOT ESTABLISH
#   * A rebuild on another machine or by another user: the kernel banner
#     carries the builder's user and host names (`P4A-1`), and this script
#     passes the host's through.  Layer 2 is where they are set.
#   * That the archive alone suffices: the drop supplies the toolchain and the
#     files the archive leaves out, and the second drop serves G1.
#   * The provenance of the toolchain, trusted by its pin.
#   * Anything about the device.
set -o nounset

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
REPO="$(cd "$(dirname "$SELF")/.." && pwd)"
PIN_DOC="$REPO/REPRODUCE.md"
PY=/usr/bin/python3
CELL=v10-recipient
TCN=rsdk-1.3.6-4181-EB-2.6.30-0.9.30

say()    { printf '%s\n' "$*"; }
refuse() { say "REFUSED: $*" >&2; exit 3; }
failed() { say "FAILED: $*" >&2; exit 4; }
step()   { say "== $(date -u +%T) $*"; }

# --------------------------------------------------------------- the pins
# REPRODUCE.md states each pin as a line `pin <name> <40 hex>`, and the
# repository's SOURCES.json must state the same value: two files saying one
# thing, read here so that neither can drift alone.
pin_of() {   # pin_of NAME -> the commit
    local name=$1 a b
    [ -f "$PIN_DOC" ] || refuse "no $PIN_DOC to read the pins from"
    a=$(awk -v n="$name" '$1 == "pin" && $2 == n && $3 ~ /^[0-9a-f]{40}$/ { print $3 }' "$PIN_DOC")
    [ "$(printf '%s' "$a" | grep -c .)" = 1 ] || refuse "REPRODUCE.md states $(printf '%s' "$a" | grep -c .) pin line(s) for $name, not 1"
    b=$("$PY" -I - "$REPO/SOURCES.json" "$name" <<'PYEOF'
import json, sys
def walk(o):
    if isinstance(o, dict):
        if o.get("id") == sys.argv[2] and "pin" in o:
            yield o["pin"]
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)
pins = list(walk(json.load(open(sys.argv[1]))))
print(pins[0] if len(pins) == 1 else "")
PYEOF
)
    [ "$a" = "$b" ] || refuse "REPRODUCE.md pins $name at ${a:-nothing}, SOURCES.json at ${b:-nothing}"
    printf '%s\n' "$a"
}

pincheck() {   # pincheck NAME DIR -> 0, or a refusal naming what differs
    local name=$1 dir=$2 want head st n
    want=$(pin_of "$name") || exit 3
    git -C "$dir" rev-parse --git-dir > /dev/null 2>&1 || { say "PIN $name: $dir is not a git checkout"; return 1; }
    head=$(git -C "$dir" rev-parse HEAD 2>/dev/null)
    if [ "$head" != "$want" ]; then
        say "PIN $name: $dir is at ${head:-no commit}, not the pin $want"; return 1
    fi
    st=$(git -C "$dir" status --porcelain=v1 --ignored=matching --untracked-files=all 2>&1)
    n=$(printf '%s' "$st" | grep -c .)
    if [ "$n" != 0 ]; then
        say "PIN $name: $dir is at the pin and its status is not clean: $n line(s)"
        printf '%s\n' "$st" | head -5 | sed 's/^/    /'
        return 1
    fi
    say "PIN $name: $dir is at $want, status clean (ignored files included)"
    return 0
}

usage() { say "usage: reproduce-l1.sh pincheck --name NAME --tree DIR"
          say "       reproduce-l1.sh build --assets DIR --release-json FILE --drop DIR --ref-drop DIR --root DIR [--release-vmlinux FILE] [--control-iperf3-path]"
          exit 3; }

VERB=${1:-}; [ $# -gt 0 ] && shift
NAME=""; TREE=""; ASSETS=""; RJSON=""; DROP=""; REFDROP=""; ROOT=""; RELVM=""; CTL_IPERF=0
ARGS=("$@")
while [ $# -gt 0 ]; do
    if [ "$1" = --control-iperf3-path ]; then CTL_IPERF=1; shift; continue; fi
    [ $# -ge 2 ] || usage
    case "$1" in
        --name)            NAME=$2 ;;
        --tree)            TREE=$2 ;;
        --assets)          ASSETS=$2 ;;
        --release-json)    RJSON=$2 ;;
        --drop)            DROP=$2 ;;
        --ref-drop)        REFDROP=$2 ;;
        --root)            ROOT=$2 ;;
        --release-vmlinux) RELVM=$2 ;;
        *) usage ;;
    esac
    shift 2
done

case "$VERB" in
    pincheck)
        [ -n "$NAME" ] && [ -n "$TREE" ] || usage
        pincheck "$NAME" "$TREE"; exit $? ;;
    build) ;;
    *) usage ;;
esac

[ -n "$ASSETS" ] && [ -n "$RJSON" ] && [ -n "$DROP" ] && [ -n "$REFDROP" ] && [ -n "$ROOT" ] || usage
for v in ASSETS RJSON DROP REFDROP ROOT RELVM; do
    p=${!v}; [ -z "$p" ] && continue
    case "$p" in /*) ;; *) refuse "$p is not an absolute path: every path argument must be" ;; esac
done

# ------------------------------------------------- the environment, cleared
if [ "${RLXFW_L1_INNER:-}" != 1 ]; then
    case "$ROOT" in /mnt/*) refuse "--root $ROOT is on DrvFs, which reports every file 0777" ;; esac
    if [ -e "$ROOT" ]; then
        [ -d "$ROOT" ] && [ -z "$(ls -A "$ROOT")" ] || refuse "--root $ROOT exists and is not an empty directory"
    else
        [ -d "$(dirname "$ROOT")" ] || refuse "the parent of --root $ROOT does not exist"
        mkdir "$ROOT" || refuse "cannot create $ROOT"
    fi
    mkdir "$ROOT/home" "$ROOT/tmp" || refuse "cannot create $ROOT/home and $ROOT/tmp"
    exec env -i HOME="$ROOT/home" PATH=/usr/sbin:/usr/bin:/sbin:/bin LC_ALL=C TZ=UTC \
        TMPDIR="$ROOT/tmp" PYTHONDONTWRITEBYTECODE=1 FWRE_WORK="$ROOT/work" \
        RLXFW_L1_INNER=1 /bin/bash "$SELF" build "${ARGS[@]}"
fi

[ "$(find "$ROOT" -mindepth 1 | LC_ALL=C sort | tr '\n' ' ')" = "$ROOT/home $ROOT/tmp " ] \
    || refuse "$ROOT holds more than the empty home/ and tmp/ this script made"
L=$ROOT/log; O=$ROOT/out; SC=$ROOT/scratch; SV=$FWRE_WORK/rebuild/src-vendor
mkdir -p "$L" "$O" "$SC" "$SV" "$ROOT/src" "$ROOT/unit"
exec > >(tee -a "$L/reproduce-l1.log") 2>&1
step "layer 1 starts at $(date -u '+%F %T') UTC in $ROOT"
say "environment: $(env | cut -d= -f1 | sort | tr '\n' ' ')"
say "host: $(uname -srm); $(git --version); $(make --version | head -1); $($PY --version 2>&1); gcc $(gcc -dumpfullversion 2>/dev/null)"
t=$ROOT/tmp/mode-probe; : > "$t"; chmod 0644 "$t"
[ "$(stat -c %a "$t")" = 644 ] || refuse "$ROOT does not keep file modes (0644 reads back $(stat -c %a "$t"))"; rm -f "$t"
o=$(pgrep -af 'mips-linux-gcc|rlxfw-kbuild|rtkimage.py build|mkbusybox|rsdk-linux-gcc|make -C .*linux-2.6.30' | grep -v -e pgrep -e reproduce-l1)
[ -z "$o" ] || refuse "another build is running (one at a time): $(printf '%s' "$o" | head -1 | cut -c1-120)"

# ------------------------------------------------------------ L1-1 layer 0
step "L1-1 layer 0 on the release's files"
"$PY" -I "$REPO/tools/reproduce-l0.py" check --assets "$ASSETS" --release-json "$RJSON" --repo "$REPO" > "$L/layer0.log" 2>&1
rc=$?; tail -3 "$L/layer0.log"
[ $rc = 0 ] || refuse "layer 0 exited $rc on $ASSETS (log $L/layer0.log)"
SUMS=$ASSETS/SHA256SUMS
ARCH=$(awk '$2 ~ /^rlxfw-src-[0-9a-f]+\.tar\.xz$/ { print $2 }' "$SUMS")
IMG=$(awk '$2 ~ /\.img$/ { print $2 }' "$SUMS")
[ "$(printf '%s\n' "$ARCH" | grep -c .)" = 1 ] || refuse "the manifest lists $(printf '%s\n' "$ARCH" | grep -c .) archives, not 1"
[ "$(printf '%s\n' "$IMG" | grep -c .)" = 1 ] || refuse "the manifest lists $(printf '%s\n' "$IMG" | grep -c .) images, not 1"
IMG_SHA=$(awk -v n="$IMG" '$2 == n { print $1 }' "$SUMS")
BASE=${ARCH%.tar.xz}
say "archive $ARCH; image $IMG, the manifest's sha256 $IMG_SHA"

# --------------------------------------------------------------- L1-2 pins
step "L1-2 the two drops against REPRODUCE.md's pins"
pincheck rtl819x-toolchain "$DROP" || refuse "--drop is not the pinned tree"
pincheck saturn49-wecb "$REFDROP" || refuse "--ref-drop is not the pinned tree"
PIN_D=$(pin_of rtl819x-toolchain); PIN_R=$(pin_of saturn49-wecb)

# ----------------------------------------------------------- L1-3 unpack
step "L1-3 the archive, unpacked and read back by its own tool"
tar -xJf "$ASSETS/$ARCH" -C "$ROOT/src" || failed "tar could not unpack $ARCH"
[ "$(find "$ROOT/src" -mindepth 1 -maxdepth 1 | grep -c .)" = 1 ] || failed "the archive does not unpack to one directory"
R=$(find "$ROOT/src" -mindepth 1 -maxdepth 1)
"$PY" "$R/tools/srcarchive.py" verify --archive "$ASSETS/$ARCH" --sums "$ASSETS/$BASE.SHA256SUMS" > "$L/srcarchive-verify.log" 2>&1 \
    || { tail -5 "$L/srcarchive-verify.log"; failed "srcarchive.py verify refused the archive"; }
tail -1 "$L/srcarchive-verify.log"
for n in rtl819x-toolchain saturn49-wecb; do
    got=$("$PY" -I - "$R/SOURCES.json" "$n" <<'PYEOF'
import json, sys
def walk(o):
    if isinstance(o, dict):
        if o.get("id") == sys.argv[2] and "pin" in o:
            yield o["pin"]
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)
p = list(walk(json.load(open(sys.argv[1]))))
print(p[0] if len(p) == 1 else "")
PYEOF
)
    [ "$got" = "$(pin_of "$n")" ] || refuse "the archive's SOURCES.json pins $n at ${got:-nothing}, REPRODUCE.md at $(pin_of "$n")"
done
grep -qP "^# tree\trtl819x-toolchain\t$PIN_D\t" "$R/CORRESPONDING-SOURCE.tsv" \
    || refuse "the archive's CORRESPONDING-SOURCE.tsv does not name rtl819x-toolchain at $PIN_D"
say "the archive's SOURCES.json and CORRESPONDING-SOURCE.tsv name the same pins"

# ------------------------------------------------- L1-4 the drops, in --root
# Sparse checkouts, the parts the build reads: the release build's drop copy
# held boards/, linux-2.6.30/ and the 4181 toolchain; busybox adds its source.
step "L1-4 the drops, checked out at their pins under \$FWRE_WORK"
sparse_clone() {   # sparse_clone SRC DEST PIN pattern...
    local src=$1 dest=$2 pin=$3; shift 3
    git clone -q --no-checkout --no-hardlinks "$src" "$dest" || return 1
    git -C "$dest" cat-file -e "$pin^{commit}" || { say "$src holds no commit $pin"; return 1; }
    git -C "$dest" config core.sparseCheckout true
    git -C "$dest" config core.sparseCheckoutCone true
    printf '%s\n' "$@" > "$dest/.git/info/sparse-checkout"
    git -C "$dest" checkout -q --detach "$pin" || return 1
}
sparse_clone "$DROP" "$SV/rtl819x-toolchain" "$PIN_D" '/*' '!/*/' '/boards/' '/linux-2.6.30/' \
    '/toolchain/' '!/toolchain/*/' "/toolchain/$TCN/" '/users/' '!/users/*/' '/users/busybox-1.13/' \
    || failed "could not check out rtl819x-toolchain at $PIN_D"
sparse_clone "$REFDROP" "$SV/saturn49-wecb" "$PIN_R" '/*' '!/*/' '/rtl819x/' '!/rtl819x/*/' \
    '/rtl819x/users/' '!/rtl819x/users/*/' '/rtl819x/users/busybox-1.13/' \
    || failed "could not check out saturn49-wecb at $PIN_R"
# The archive's own copy of the drop's files goes over the checkout: what is
# compiled is the archive's bytes, and the checkout staying clean is git's
# proof that each of them is the pinned file.
nv=$(cd "$R/src-vendor/rtl819x-toolchain" && find . ! -type d | grep -c .)
cp -a "$R/src-vendor/rtl819x-toolchain/." "$SV/rtl819x-toolchain/" || failed "could not overlay the archive's drop files"
say "overlaid $nv of the archive's drop file(s) and symlink(s) on the checkout"
pincheck rtl819x-toolchain "$SV/rtl819x-toolchain" || refuse "the archive's drop files are not the pinned ones"
pincheck saturn49-wecb "$SV/saturn49-wecb" || refuse "the saturn49-wecb checkout is not clean"
TC=$SV/rtl819x-toolchain/toolchain/$TCN
TW=$R/tools/vendor-tripwire.sh
(cd "$SC" && bash "$TW" --check) | tail -1
"$PY" -I "$REPO/tools/relimage.py" files --image "$ASSETS/$IMG" > "$O/released-files.tsv" || failed "relimage files"
"$PY" -I - "$O/released-files.tsv" "$R" "$SV" <<'PYEOF' || refuse "the inputs already hold a released program's bytes"
import hashlib, os, sys
want = {}
for ln in open(sys.argv[1]):
    p, n, s = ln.rstrip("\n").split("\t")
    want.setdefault(int(n), {})[s] = p
hits, seen = [], 0
for top in sys.argv[2:]:
    for d, dirs, files in os.walk(top):
        dirs[:] = [x for x in dirs if x != ".git"]
        for f in files:
            q = os.path.join(d, f)
            if os.path.islink(q) or not os.path.isfile(q):
                continue
            n = os.path.getsize(q)
            if n not in want:
                continue
            seen += 1
            with open(q, "rb") as fh:
                b = fh.read()
            s = hashlib.sha256(b).hexdigest()
            if s in want[n]:
                hits.append((want[n][s], q[len(top) + 1:], b[:4] == b"\x7fELF"))
elf = [h for h in hits if h[2]]
print("  independence: %d file(s) of a released initramfs file's size, %d with its sha256 (%s); ELF programs among them: %d"
      % (seen, len(hits), ", ".join(sorted(set(h[0] for h in hits))) or "none", len(elf)))
for h in elf:
    print("  ALREADY PRESENT %s as %s" % (h[0], h[1]))
sys.exit(1 if elf else 0)
PYEOF

# ------------------------------------------------- L1-5 the six programs
step "L1-5 the six programs (src/Makefile target, install)"
(cd "$SC" && make -C "$R/src" target O="$O/user" TC="$TC" TRIP="$TW") > "$L/user-target.log" 2>&1 \
    || { tail -15 "$L/user-target.log"; failed "make -C src target"; }
make -C "$R/src" install O="$O/user" > "$L/user-install.log" 2>&1 || failed "make -C src install"
grep -c 'VENDOR-TRIPWIRE: CLEAN' "$L/user-target.log" | sed 's/^/  tripwire CLEAN lines: /'

# ------------------------------------------------------------ L1-6 busybox
step "L1-6 busybox (tools/mkbusybox.sh --drop rtl819x-toolchain --ref saturn49-wecb)"
(cd "$SC" && bash "$R/tools/mkbusybox.sh" --config "$R/config/rlxfw-busybox.config" --drop rtl819x-toolchain \
    --ref saturn49-wecb --stage "$O/bb" --out "$O/bb/out" --jobs 4) > "$L/busybox.log" 2>&1 \
    || { tail -15 "$L/busybox.log"; failed "mkbusybox.sh"; }
mkdir -p "$R/build/rlxfw-user/busybox"
cp "$O/bb/out/busybox" "$R/build/rlxfw-user/busybox/busybox" && chmod 0755 "$R/build/rlxfw-user/busybox/busybox"

# ------------------------------------------------------------- L1-7 probes
step "L1-7 uprobe, ucost, linkprobe (their committed Makefiles)"
(cd "$SC" && bash "$TW" -- make -f "$R/config/rlxfw-user/isaprobe/Makefile" -j1 TCROOT="$SV/rtl819x-toolchain/toolchain" \
    TC="$TCN" STAGE="$O/isaprobe" INSTALL="$R/build/rlxfw-user/isaprobe" UC_STAGE="$O/ucost" \
    UC_INSTALL="$R/build/rlxfw-user/isaprobe" PYTHON="$PY" show ucost-show) > "$L/isaprobe.log" 2>&1 \
    || { tail -15 "$L/isaprobe.log"; failed "isaprobe"; }
(cd "$SC" && bash "$TW" -- make -f "$R/config/rlxfw-user/linkprobe/Makefile" -j1 TCROOT="$SV/rtl819x-toolchain/toolchain" \
    TC="$TCN" KTREE="$SV/rtl819x-toolchain/linux-2.6.30" UPROBE_ELF="$O/isaprobe/build/uprobe.elf" \
    STAGE="$O/linkprobe" INSTALL="$R/build/rlxfw-user/linkprobe" PYTHON="$PY" show) > "$L/linkprobe.log" 2>&1 \
    || { tail -15 "$L/linkprobe.log"; failed "linkprobe"; }

# ------------------------------------------------------------- L1-8 iperf3
step "L1-8 iperf3, from the pinned tarball, at the directory the released bytes name"
TGZ=$R/refs/iperf-3.1.3.tar.gz
want=$(awk -F'\t' '$1 == "# imported" && $2 == "iperf3" { print $3 }' "$R/CORRESPONDING-SOURCE.tsv")
[ -n "$want" ] && [ "$(sha256sum "$TGZ" | cut -c1-64)" = "$want" ] || failed "refs/iperf-3.1.3.tar.gz is not the sha256 the archive declares"
mkdir -p "$O/iperf3-tree"
tar -xzf "$TGZ" -C "$O/iperf3-tree" --no-same-owner || failed "could not unpack the iperf3 tarball"
T=$O/iperf3-tree/iperf-3.1.3
# config/rlxfw-user/iperf3/build.sh's step 1, which stages into a fixed path
# of its own: the two generated headers, written here into the staged tree.
tr -d '\r' < "$R/config/rlxfw-user/iperf3/iperf_config.h" > "$T/src/iperf_config.h" || failed "iperf_config.h"
sed 's/@PACKAGE_VERSION@/3.1.3/' "$T/src/version.h.in" > "$T/src/version.h" || failed "version.h"
if [ "$CTL_IPERF" = 1 ]; then
    say "  CONTROL: iperf3 is built in the staged tree's own directory, without the namespace"
    (cd "$SC" && bash "$TW" -- make -f "$R/config/rlxfw-user/iperf3/Makefile" -j4 TC="$TC" SRC="$T/src" \
        STAGE="$O/iperf3" INSTALL="$R/build/rlxfw-user/iperf3" show) > "$L/iperf3.log" 2>&1 \
        || { tail -15 "$L/iperf3.log"; failed "the iperf3 build"; }
    grep -a 'VENDOR-TRIPWIRE' "$L/iperf3.log" | sed 's/^/  /'
else
    SRCDIR=$("$PY" -I "$REPO/tools/relimage.py" srcdir --image "$ASSETS/$IMG" --member /bin/iperf3 \
             --names net.c,tcp_window_size.c,units.c) || failed "relimage could not read iperf3's source directory: $SRCDIR"
    say "the released /bin/iperf3 was compiled from a directory of $(printf '%s' "$SRCDIR" | wc -c) characters (read from its assert strings)"
    [ -d "$SRCDIR" ] || failed "that directory does not exist on this host, so it cannot be a mount point here: layer 2 creates it"
    digest_dir() { (cd "$1" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 -r sha256sum | sha256sum | cut -c1-16); }
    before=$(digest_dir "$SRCDIR")
    marker="rlxfw-bind-$$-$(date +%s%N)"
    printf '%s\n' "$marker" > "$T/src/.rlxfw-bind-marker"
    unshare --user --map-root-user --mount bash -c '
        set -u
        mount --bind "$1" "$2" || { echo "NS: bind failed"; exit 7; }
        [ "$(cat "$2/.rlxfw-bind-marker" 2>/dev/null)" = "$3" ] || { echo "NS: the directory does not show the staged tree"; exit 7; }
        rm -f "$2/.rlxfw-bind-marker"
        echo "NS: the staged tree is mounted at the directory (marker seen, then removed)"
        shift 3
        cd "$1" || exit 7
        shift
        exec bash "$@"
    ' _ "$T/src" "$SRCDIR" "$marker" "$SC" "$TW" -- make -f "$R/config/rlxfw-user/iperf3/Makefile" -j4 \
        TC="$TC" SRC="$SRCDIR" STAGE="$O/iperf3" INSTALL="$R/build/rlxfw-user/iperf3" show > "$L/iperf3.log" 2>&1
    rc=$?
    grep -a '^NS:\|VENDOR-TRIPWIRE' "$L/iperf3.log" | sed 's/^/  /'
    [ $rc != 7 ] || failed "the private mount namespace did not show the staged tree at the directory"
    [ ! -e "$T/src/.rlxfw-bind-marker" ] || failed "the marker is still in the staged tree: the bind was not in effect"
    [ "$(digest_dir "$SRCDIR")" = "$before" ] || failed "the directory's content changed outside the namespace"
    say "  outside the namespace the directory's content digest is unchanged ($before)"
    [ $rc = 0 ] || { tail -15 "$L/iperf3.log"; failed "the iperf3 build (rc $rc)"; }
fi

# ---------------------------------------------------------- L1-9 initramfs
step "L1-9 the initramfs (tools/mkinitramfs.py build)"
# The declaration tags seven directories `unit`: they exist in this unit's flash
# dump, which no recipient holds, and mkinitramfs checks them against it.  They
# carry no content, so an empty directory holding the seven stands in for it.
awk -F'\t' '$5 == "unit" && $1 != "dir" { bad = 1 } END { exit bad }' "$R/config/rlxfw-initramfs.tsv" \
    || failed "the declaration takes a file or link from the unit's dump: no recipient can supply it"
awk -F'\t' '$1 == "dir" && $5 == "unit" { print $2 }' "$R/config/rlxfw-initramfs.tsv" | while read -r d; do mkdir -p "$ROOT/unit$d"; done
say "unit stand-in: $(cd "$ROOT/unit" && find . -mindepth 1 | sort | tr '\n' ' ')"
"$PY" "$R/tools/mkinitramfs.py" build --decl "$R/config/rlxfw-initramfs.tsv" --unit "$ROOT/unit" --repo "$R" \
    --out "$O/irfs" > "$L/irfs.log" 2>&1 || { tail -8 "$L/irfs.log"; failed "mkinitramfs build"; }
SPEC=$O/irfs/rlxfw-initramfs.spec
# The second source for what relimage read: docs/sbom.md, an asset of the
# release, lists the same files' sha256 in its Appendix A.
"$PY" -I - "$O/released-files.tsv" "$ASSETS/sbom.md" "$O/irfs/rlxfw-initramfs.manifest.tsv" "$O/irfs-diff.txt" <<'PYEOF' || failed "the initramfs comparison"
import re, sys
rel = {}
for ln in open(sys.argv[1]):
    p, n, s = ln.rstrip("\n").split("\t")
    rel[p] = (int(n), s)
sb = {}
for m in re.finditer(r"^\| `(/[^`]+)` \| ([0-9,]+) \| `([0-9a-f]{64})` \|", open(sys.argv[2]).read(), re.M):
    sb[m.group(1)] = (int(m.group(2).replace(",", "")), m.group(3))
new = {}
for ln in open(sys.argv[3]):
    if ln.startswith("#"):
        continue
    f = ln.rstrip("\n").split("\t")
    if len(f) > 3 and f[1] == "file":
        new[f[0]] = (int(f[2]), f[3])
same_sb = sum(1 for p in rel if sb.get(p) == rel[p])
print("  the released image's cpio holds %d file(s); %d of them match sbom.md's Appendix A (%d rows)"
      % (len(rel), same_sb, len(sb)))
if same_sb != len(rel) or len(sb) != len(rel):
    print("  the image reader and the release's SBOM disagree: nothing below is evidence")
    sys.exit(1)
diff = sorted(p for p in set(rel) | set(new) if rel.get(p) != new.get(p))
print("  rebuilt: %d file(s); %d of %d equal to the released bytes" % (len(new), len(rel) - len(diff), len(rel)))
for p in diff:
    print("  DIFF %-26s released %s  rebuilt %s" % (p, rel.get(p), new.get(p)))
with open(sys.argv[4], "w") as fh:
    fh.write("".join(p + "\n" for p in diff))
PYEOF

# ------------------------------------------------------------- L1-10 kernel
step "L1-10 the kernel (tools/rlxfw-kbuild.sh --recipient, -j4)"
(cd "$SC" && bash "$R/tools/rlxfw-kbuild.sh" "$CELL" --variant quiet --marks --jobs 4 --initramfs "$SPEC" --recipient) \
    > "$L/kbuild.log" 2>&1
krc=$?
last=$(tail -1 "$L/kbuild.log")
say "  kbuild exit $krc; last line: $(printf '%s' "$last" | cut -c1-160)"
KO=$FWRE_WORK/rebuild/r3-4/out
[ -f "$KO/$CELL.vmlinux.elf" ] || { tail -15 "$L/kbuild.log"; failed "the kernel build left no vmlinux"; }
case "$last" in "== $CELL: RECIPIENT BUILD -- unit-specific checks not run: unit-kernel"*) kline=1 ;; *) kline=0 ;; esac
if [ $krc != 7 ] || [ $kline != 1 ]; then
    tail -15 "$L/kbuild.log"; say "FAILED: the kernel build's verdict is not recipient (exit 7 and its line)"; exit 5
fi
grep -P '^(verdict|recipient|recipe_id|vmlinux_sha256)\t' "$KO/$CELL.manifest" | sed 's/^/  manifest  /'

# ----------------------------------------------------------- L1-11 rtkimage
step "L1-11 the image (tools/rtkimage.py build)"
(cd "$SC" && "$PY" "$R/tools/rtkimage.py" build --cell "$FWRE_WORK/rebuild/r3-4/cells/$CELL/top" \
    --vmlinux "$KO/$CELL.vmlinux.elf" --label "$CELL" --work "$O/img") > "$L/rtkimage.log" 2>&1 \
    || { tail -15 "$L/rtkimage.log"; failed "rtkimage.py build"; }
NFJ=$O/img/$CELL/kroot/rtkload/nfjrom
[ -f "$NFJ" ] || failed "rtkimage wrote no $NFJ"
cp "$NFJ" "$O/rebuilt.img"

# ------------------------------------------------------------ L1-12 verdict
step "L1-12 the comparison"
GOT=$(sha256sum "$O/rebuilt.img" | cut -c1-64)
say "  released $IMG  $(stat -c %s "$ASSETS/$IMG") bytes  sha256 $IMG_SHA  (the manifest's entry)"
say "  rebuilt  $(stat -c %s "$O/rebuilt.img") bytes  sha256 $GOT"
TP=$(tail -c +161 "$ASSETS/T.rlxu" | sha256sum | cut -c1-64)
say "  T.rlxu's payload (after its 160-byte header and signature) sha256 $TP"
if [ -n "$RELVM" ]; then
    "$PY" -I "$REPO/tools/repdiff.py" "$RELVM" "$KO/$CELL.vmlinux.elf" > "$L/repdiff.log" 2>&1
    say "  repdiff, the release build's vmlinux against this one: exit $? ($(grep -m1 -i 'differ\|identical' "$L/repdiff.log" | cut -c1-120))"
fi
"$PY" -I "$REPO/tools/relimage.py" info --image "$O/rebuilt.img" | grep -E '^(vmlinux_img|banner|cpio)' | sed 's/^/  rebuilt  /'
"$PY" -I "$REPO/tools/relimage.py" info --image "$ASSETS/$IMG" | grep -E '^(vmlinux_img|banner|cpio)' | sed 's/^/  released /'
say "== $(date -u +%T) layer 1 ends"
if [ "$CTL_IPERF" = 1 ]; then
    if [ "$GOT" != "$IMG_SHA" ] && [ "$(cat "$O/irfs-diff.txt")" = /bin/iperf3 ]; then
        say "CONTROL: FIRED -- with iperf3 built elsewhere the image differs, and /bin/iperf3 is the one initramfs file that does"
        exit 0
    fi
    say "CONTROL: DID NOT FIRE -- the image is $( [ "$GOT" = "$IMG_SHA" ] && echo equal || echo different), initramfs files differing: $(tr '\n' ' ' < "$O/irfs-diff.txt")"
    exit 1
fi
if [ "$GOT" = "$IMG_SHA" ]; then
    say "RESULT: EQUAL -- the image rebuilt from $ARCH is the released $IMG, byte for byte"
    exit 0
fi
say "RESULT: DIFFERENT -- see the comparisons above; repdiff locates a kernel difference"
exit 1
