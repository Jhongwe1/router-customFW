#!/usr/bin/env bash
# reproduce-l2.sh -- layer 2 of REPRODUCE.md: layer 1, run inside a container
# whose base image is named by digest and whose packages come from one dated
# snapshot at exact versions, with no network and every input read-only.
#
#   reproduce-l2.sh image [--engine podman|docker]
#   reproduce-l2.sh build --assets DIR --release-json FILE --drop DIR
#                         --ref-drop DIR --out DIR [--release-vmlinux FILE]
#                         [--tmpfs SIZE] [--engine podman|docker]
#                         [--control-withhold-drop]
#
# `image` builds tools/reproduce-l2.Containerfile -- the only step that uses
# the network -- from an empty context, tags it rlxfw-reproduce-l2:<the first
# 12 hex digits of the file's sha256>, and then, with no network, reads back
# the installed version of every package the file pins; a mismatch refuses.
#
# `build` runs `tools/reproduce-l1.sh build --iperf3-in-place` in that image:
#   * with --network=none;
#   * with read-only mounts of exactly this repository (the scripts, the pins
#     and the tag layer 0 reads), --assets, --release-json, --drop, --ref-drop
#     and, if given, --release-vmlinux;
#   * with one writable mount, DIR/result under --out, which must be empty and
#     which the build user cannot write: the container's root copies the
#     results into it after layer 1 exits;
#   * with the build directory on the container's own filesystem (overlay), or
#     with --tmpfs SIZE on a tmpfs of that size, iperf3's directory then on a
#     second tmpfs: tmpfs lists a directory in another order than ext4 does,
#     and the run prints the order each gave;
#   * as a user named as the released kernel banner names its builder, on a
#     host named as it names the host: a first run of the same image, with no
#     network, reads the banner out of the released image (tools/relimage.py
#     info), and the names are passed to the build run as its user and its
#     --hostname.  The drop's scripts/mkcompile_h reads `whoami` and
#     `hostname`; nothing here types either name.
# The rebuilt image's sha256 is compared with the manifest's entry twice: by
# layer 1 inside the container, and here, on the copy in --out.
#
# --control-withhold-drop mounts an empty directory in the drop's place.  The
# run must then stop at layer 1's pin check, exit 3 and name the drop, with no
# traceback: no other copy of it is reachable from inside.
#
# EXIT
#   0  the rebuilt image equals the manifest's entry; with the control, the
#      control fired
#   1  rebuilt and different; with the control, it did not fire
#   3  refused: an input, the engine or the image failed a check
#   4  the container run ended in neither verdict
#
# WHAT IT DOES NOT ESTABLISH
#   * That the image can be built next year: the base digest and the snapshot
#     are pinned, but third parties serve both.
#   * That the container image is itself reproducible: its ID changes with
#     every build; the pins fix the packages it holds, which `image` checks.
#   * Docker: the commands are written for both CLIs; only rootless podman
#     has run them.
#   * Independence from directory order beyond the two orders one run pair
#     measures, or anything layer 1 does not establish.
set -o nounset

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
REPO="$(cd "$(dirname "$SELF")/.." && pwd)"
CF=$REPO/tools/reproduce-l2.Containerfile
BUID=10001   # the build user's uid and gid in the container; the banner holds its name only
DROP_NAME=rtl819x-toolchain

say()    { printf '%s\n' "$*"; }
refuse() { say "REFUSED: $*" >&2; exit 3; }
failed() { say "FAILED: $*" >&2; exit 4; }

# ------------------------------------------------------- inside the container
# Run by the container's root.  `names` prints what the build run needs to be
# given; `run` creates the build user and the two directories, runs layer 1 as
# that user, reports what the filesystem did and copies the results out.
in_names() {
    local img
    img=$(awk '$2 ~ /\.img$/ { print $2 }' /l2/assets/SHA256SUMS)
    [ "$(printf '%s\n' "$img" | grep -c .)" = 1 ] || refuse "the manifest lists no single image"
    printf 'banner\t%s\n' "$(/usr/bin/python3 -I /l2/repo/tools/relimage.py info --image "/l2/assets/$img" | sed -n 's/^banner *//p')"
    printf 'iperf3dir\t%s\n' "$(bash /l2/repo/tools/reproduce-l1.sh iperf3-dir --assets /l2/assets)"
}

listing() {   # listing DIR -> one line: path count, sha256 of the listing in readdir order, and sorted
    local d=$1
    [ -d "$d" ] || { say "  listing ${d#/l2/build/root/}: absent"; return 0; }
    find "$d" -path '*/.git' -prune -o -print > /tmp/l2-list
    say "  listing ${d#/l2/build/root/}: $(grep -c . /tmp/l2-list) paths; sha256 as find read them $(sha256sum < /tmp/l2-list | cut -c1-16), sorted $(LC_ALL=C sort /tmp/l2-list | sha256sum | cut -c1-16)"
}

in_run() {
    local u="" h="" fs="" vm=0 d got who rc n
    while [ $# -gt 0 ]; do
        case "$1" in
            --user) u=$2; shift 2 ;;
            --host) h=$2; shift 2 ;;
            --fs) fs=$2; shift 2 ;;
            --release-vmlinux) vm=1; shift ;;
            *) refuse "in-container run: unknown argument $1" ;;
        esac
    done
    [ -n "$u" ] && [ -n "$h" ] && [ -n "$fs" ] || refuse "in-container run needs --user, --host and --fs"
    [ "$(id -u)" = 0 ] || refuse "the in-container step runs as the container's root, which creates the build user"
    umask 022
    for p in /l2/repo/tools/reproduce-l1.sh /l2/assets/SHA256SUMS /l2/release.json /l2/ref-drop /l2/out; do
        [ -e "$p" ] || refuse "$p is not mounted"
    done
    [ -z "$(ls -A /l2/out)" ] || refuse "/l2/out is not empty"
    say "container: $(uname -srm); $(grep -c . /usr/share/rlxfw-l2/dpkg.tsv) packages installed, their list's sha256 $(sha256sum < /usr/share/rlxfw-l2/dpkg.tsv | cut -c1-64)"
    say "network interfaces: $(ls /sys/class/net | tr '\n' ' ')"

    getent passwd "$u" > /dev/null && refuse "the image already has a user named $u"
    getent passwd "$BUID" > /dev/null && refuse "the image already has uid $BUID"
    groupadd -g "$BUID" "$u" && useradd -M -N -g "$BUID" -u "$BUID" -d /nonexistent -s /bin/bash "$u" \
        || refuse "could not create the build user"

    d=$(bash /l2/repo/tools/reproduce-l1.sh iperf3-dir --assets /l2/assets) || refuse "could not read iperf3's directory: $d"
    if [ "$fs" = tmpfs ]; then
        [ "$(stat -f -c %T "$d" 2>/dev/null)" = tmpfs ] || refuse "iperf3's directory is not on the tmpfs the driver mounted"
    else
        [ -e "$d" ] && refuse "the image already holds iperf3's directory"
        mkdir -p "$d" || refuse "could not create iperf3's directory"
    fi
    [ -z "$(ls -A "$d")" ] || refuse "iperf3's directory is not empty"
    chown "$BUID:$BUID" "$d" && chmod 0755 "$d" || refuse "could not hand iperf3's directory to the build user"
    mkdir -p /l2/build && chown "$BUID:$BUID" /l2/build && chmod 0755 /l2/build || refuse "could not create /l2/build"
    got=$(stat -f -c %T /l2/build)
    case "$fs" in
        tmpfs) [ "$got" = tmpfs ] || refuse "the build directory is on $got, not the tmpfs the driver mounted" ;;
        container) ;;   # whatever the engine's storage gives: overlay here, other drivers elsewhere
        *) refuse "--fs is tmpfs or container" ;;
    esac
    for m in /l2/build "$d"; do
        awk -v m="$m" '$2 == m { print $4 }' /proc/mounts | grep -q noexec \
            && refuse "$m is mounted noexec, and the build runs programs from it"
    done
    say "build directory on $got; iperf3's directory on $(stat -f -c %T "$d")"

    # The order this filesystem lists a directory in: 13 names created in one order.
    mkdir /l2/build/.probe
    for n in 07 03 11 01 09 05 13 02 12 04 10 06 08; do : > "/l2/build/.probe/f$n"; done
    say "  readdir order of f07 f03 f11 f01 f09 f05 f13 f02 f12 f04 f10 f06 f08, created in that order: $(ls -f /l2/build/.probe | grep -v '^\.' | tr '\n' ' ')"
    rm -rf /l2/build/.probe

    who=$(setpriv --reuid="$BUID" --regid="$BUID" --init-groups -- /bin/sh -c 'printf "%s@%s" "$(whoami)" "$(hostname)"')
    [ "$who" = "$u@$h" ] || refuse "the build user reads its names as $who, not as the banner gives them"
    say "the build user's whoami@hostname equals the released banner's names"

    set -- build --assets /l2/assets --release-json /l2/release.json --drop /l2/drop --ref-drop /l2/ref-drop \
        --root /l2/build/root --iperf3-in-place
    [ "$vm" = 1 ] && set -- "$@" --release-vmlinux /l2/release-vmlinux.elf
    setpriv --reuid="$BUID" --regid="$BUID" --init-groups -- /bin/bash /l2/repo/tools/reproduce-l1.sh "$@"
    rc=$?
    say "== layer 1 exited $rc"

    say "what the filesystem did:"
    listing /l2/build/root/src
    listing /l2/build/root/work/rebuild/src-vendor/rtl819x-toolchain/linux-2.6.30
    n=$(du -sk /l2/build/root 2>/dev/null | cut -f1)
    say "  footprint: the build directory ${n:-?} KiB, iperf3's directory $(du -sk "$d" | cut -f1) KiB"

    mkdir -p /l2/out/log
    [ -d /l2/build/root/log ] && cp -r /l2/build/root/log/. /l2/out/log/
    for f in /l2/build/root/out/rebuilt.img /l2/build/root/out/irfs-diff.txt \
             /l2/build/root/work/rebuild/r3-4/out/v10-recipient.vmlinux.elf \
             /l2/build/root/work/rebuild/r3-4/out/v10-recipient.manifest; do
        [ -f "$f" ] && cp "$f" /l2/out/
    done
    exit "$rc"
}

# --------------------------------------------------------------- the host side
ENGINE=""; ASSETS=""; RJSON=""; DROP=""; REFDROP=""; OUT=""; RELVM=""; TMPFS=""; CTL=0
VERB=${1:-}; [ $# -gt 0 ] && shift
case "$VERB" in
    in-container)
        sub=${1:-}; [ $# -gt 0 ] && shift
        case "$sub" in
            names) in_names; exit 0 ;;
            run) in_run "$@" ;;
            *) refuse "in-container: names or run" ;;
        esac ;;
    image|build) ;;
    *) say "usage: reproduce-l2.sh image [--engine podman|docker]"
       say "       reproduce-l2.sh build --assets DIR --release-json FILE --drop DIR --ref-drop DIR --out DIR [--release-vmlinux FILE] [--tmpfs SIZE] [--engine podman|docker] [--control-withhold-drop]"
       exit 3 ;;
esac
while [ $# -gt 0 ]; do
    if [ "$1" = --control-withhold-drop ]; then CTL=1; shift; continue; fi
    [ $# -ge 2 ] || refuse "$1 needs a value"
    case "$1" in
        --engine)          ENGINE=$2 ;;
        --assets)          ASSETS=$2 ;;
        --release-json)    RJSON=$2 ;;
        --drop)            DROP=$2 ;;
        --ref-drop)        REFDROP=$2 ;;
        --out)             OUT=$2 ;;
        --release-vmlinux) RELVM=$2 ;;
        --tmpfs)           TMPFS=$2 ;;
        *) refuse "unknown argument $1" ;;
    esac
    shift 2
done

if [ -z "$ENGINE" ]; then
    if command -v podman > /dev/null; then ENGINE=podman
    elif command -v docker > /dev/null; then ENGINE=docker
    else refuse "no container engine: podman or docker"; fi
fi
case "$ENGINE" in podman|docker) ;; *) refuse "--engine is podman or docker" ;; esac
command -v "$ENGINE" > /dev/null || refuse "no $ENGINE on PATH"
[ -f "$CF" ] || refuse "no $CF"
TAG=rlxfw-reproduce-l2:$(sha256sum "$CF" | cut -c1-12)
BASE=$(awk '$1 == "FROM" { print $2 }' "$CF")
SNAP=$(grep -oE 'https://snapshot\.ubuntu\.com/ubuntu/[0-9]{8}T[0-9]{6}Z/' "$CF" | head -1)
PINS=$(grep -oE '^ +[a-z0-9][a-z0-9.+-]*=[^ ]+' "$CF" | tr -d ' ')
case "$BASE" in *@sha256:????????????????????????????????????????????????????????????????) ;;
    *) refuse "the Containerfile's FROM is not a digest: $BASE" ;; esac
[ -n "$SNAP" ] || refuse "the Containerfile names no dated snapshot"

if [ "$VERB" = image ]; then
    say "engine: $($ENGINE --version)"
    say "base: $BASE"
    say "snapshot: $SNAP"
    ctx=$(mktemp -d) || refuse "mktemp"
    "$ENGINE" build -f "$CF" -t "$TAG" "$ctx" || { rmdir "$ctx"; failed "$ENGINE build"; }
    rmdir "$ctx"
    id=$("$ENGINE" image inspect --format '{{.Id}}' "$TAG") || failed "no image $TAG after the build"
    # shellcheck disable=SC2086  # PINS is one name=version word per line
    got=$("$ENGINE" run --rm --network=none "$TAG" dpkg-query -W -f '${Package}=${Version}\n' $(printf '%s\n' $PINS | cut -d= -f1))
    n=0; bad=0
    for p in $PINS; do
        n=$((n + 1))
        printf '%s\n' "$got" | grep -qxF "$p" || { say "  PIN NOT HELD $p (installed: $(printf '%s\n' "$got" | grep "^${p%%=*}=" || echo none))"; bad=$((bad + 1)); }
    done
    [ "$bad" = 0 ] || refuse "$bad of $n pinned packages are not installed at their pinned version"
    say "pins: $n of $n named packages installed at the pinned version"
    say "image: $TAG, ID $id"
    exit 0
fi

# build
[ -n "$ASSETS" ] && [ -n "$RJSON" ] && [ -n "$REFDROP" ] && [ -n "$OUT" ] || refuse "build needs --assets, --release-json, --ref-drop and --out"
[ -n "$DROP" ] || [ "$CTL" = 1 ] || refuse "no --drop: the vendor drop $DROP_NAME at its pin is an input this run cannot reach otherwise (no network, nothing in the image)"
for v in ASSETS RJSON DROP REFDROP OUT RELVM; do
    p=${!v}; [ -z "$p" ] && continue
    case "$p" in /*) ;; *) refuse "$p is not an absolute path: every path argument must be" ;; esac
    case "$p" in *:*|*,*) refuse "$p holds ':' or ',', which a mount option cannot carry" ;; esac
done
[ -f "$ASSETS/SHA256SUMS" ] || refuse "no SHA256SUMS in --assets $ASSETS"
[ -f "$RJSON" ] || refuse "no --release-json $RJSON"
[ "$CTL" = 1 ] || [ -e "$DROP/.git" ] || refuse "--drop $DROP is not a checkout of $DROP_NAME"
[ -d "$REFDROP" ] || refuse "no --ref-drop $REFDROP"
[ -z "$RELVM" ] || [ -f "$RELVM" ] || refuse "no --release-vmlinux $RELVM"
if [ -n "$TMPFS" ]; then
    printf '%s' "$TMPFS" | grep -qE '^[0-9]+[kmg]$' || refuse "--tmpfs takes a size such as 3g"
fi
if [ -e "$OUT" ]; then
    [ -d "$OUT" ] && [ -z "$(ls -A "$OUT")" ] || refuse "--out $OUT exists and is not an empty directory"
else
    mkdir "$OUT" || refuse "cannot create $OUT"
fi
mkdir "$OUT/result" || refuse "cannot create $OUT/result"
id=$("$ENGINE" image inspect --format '{{.Id}}' "$TAG" 2>/dev/null) || refuse "no image $TAG: run \`reproduce-l2.sh image\` first"
exec > >(tee -a "$OUT/reproduce-l2.log") 2>&1
say "== $(date -u '+%F %T') UTC layer 2 starts"
say "engine: $($ENGINE --version); image $TAG, ID $id"
say "base: $BASE"
say "snapshot: $SNAP; $(printf '%s\n' $PINS | grep -c .) packages pinned by version"
say "repository: $(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo 'not a git checkout'), $(git -C "$REPO" status --porcelain 2>/dev/null | grep -c .) uncommitted path(s)"

ro=(-v "$REPO:/l2/repo:ro" -v "$ASSETS:/l2/assets:ro")
names=$("$ENGINE" run --rm --network=none "${ro[@]}" "$TAG" /bin/bash /l2/repo/tools/reproduce-l2.sh in-container names) \
    || refuse "the first run could not read the released image"
banner=$(printf '%s\n' "$names" | awk -F'\t' '$1 == "banner" { print $2 }')
idir=$(printf '%s\n' "$names" | awk -F'\t' '$1 == "iperf3dir" { print $2 }')
buser=$(printf '%s\n' "$banner" | sed -n 's/^Linux version [^ ]* (\([^@ ()]*\)@\([^@ ()]*\)) .*/\1/p')
bhost=$(printf '%s\n' "$banner" | sed -n 's/^Linux version [^ ]* (\([^@ ()]*\)@\([^@ ()]*\)) .*/\2/p')
say "the released banner: $banner"
printf '%s' "$buser" | grep -qE '^[a-z_][a-z0-9_-]{0,31}$' || refuse "the banner's user name is not one useradd takes: '$buser'"
printf '%s' "$bhost" | grep -qE '^[A-Za-z0-9][A-Za-z0-9.-]{0,62}$' || refuse "the banner's host name is not one a container takes: '$bhost'"
case "$idir" in /?*) ;; *) refuse "no directory for iperf3 read from the released image" ;; esac
case "$idir" in *:*|*,*) refuse "iperf3's directory holds ':' or ',', which a mount option cannot carry" ;; esac
say "read from the released image: the banner's user and host names, and iperf3's directory (${#idir} characters)"

if [ "$CTL" = 1 ]; then
    mkdir "$OUT/withheld-drop" || refuse "cannot create the empty stand-in"
    DROP=$OUT/withheld-drop
    say "CONTROL: the drop is withheld; an empty directory is mounted in its place"
fi
mounts=("${ro[@]}" -v "$RJSON:/l2/release.json:ro" -v "$DROP:/l2/drop:ro" -v "$REFDROP:/l2/ref-drop:ro"
        -v "$OUT/result:/l2/out")
[ -n "$RELVM" ] && mounts+=(-v "$RELVM:/l2/release-vmlinux.elf:ro")
fs=container; where="the container's own filesystem"
if [ -n "$TMPFS" ]; then
    fs=tmpfs; where="a tmpfs of $TMPFS"
    # exec: docker documents noexec as its --tmpfs default (podman 4.9.3 mounts
    # without it), and the toolchain runs from under --root
    mounts+=(--tmpfs "/l2/build:rw,exec,size=$TMPFS,mode=0755" --tmpfs "$idir:rw,exec,size=256m,mode=0755")
fi
args=(in-container run --user "$buser" --host "$bhost" --fs "$fs")
[ -n "$RELVM" ] && args+=(--release-vmlinux)
say "== $(date -u +%T) the build run: --network=none, the build directory on $where, $(( ${#mounts[@]} / 2 )) mounts"
# Its output is also kept whole in build-run.log, which the verdicts below read.
"$ENGINE" run --rm --network=none --hostname "$bhost" "${mounts[@]}" "$TAG" /bin/bash /l2/repo/tools/reproduce-l2.sh "${args[@]}" 2>&1 \
    | tee "$OUT/build-run.log"
rc=${PIPESTATUS[0]}
say "== $(date -u '+%F %T') UTC the build run exited $rc"

if [ "$CTL" = 1 ]; then
    if [ "$rc" = 3 ] && grep -aq "^PIN $DROP_NAME: /l2/drop is not a git checkout" "$OUT/build-run.log" \
       && grep -aq '^REFUSED: --drop is not the pinned tree' "$OUT/build-run.log" \
       && ! grep -aq 'Traceback' "$OUT/build-run.log" && [ ! -e "$OUT/result/rebuilt.img" ]; then
        say "CONTROL: FIRED -- with the drop withheld the run stopped at the pin check, exit 3, naming $DROP_NAME, with no traceback and no image"
        exit 0
    fi
    say "CONTROL: DID NOT FIRE -- exit $rc"
    exit 1
fi
want=$(awk '$2 ~ /\.img$/ { print $1 }' "$ASSETS/SHA256SUMS")
[ -f "$OUT/result/rebuilt.img" ] || { say "RESULT: NO IMAGE -- layer 1 exited $rc"; [ "$rc" = 3 ] && exit 3; exit 4; }
got=$(sha256sum "$OUT/result/rebuilt.img" | cut -c1-64)
say "outside the container: the rebuilt image's sha256 $got; the manifest's entry $want"
if [ "$got" = "$want" ] && [ "$rc" = 0 ]; then
    say "RESULT: EQUAL -- inside a container from $TAG, with no network and read-only inputs, the build directory on $where, the image is the released one, byte for byte"
    exit 0
fi
say "RESULT: DIFFERENT -- layer 1 exited $rc; locate it with tools/repdiff.py on $OUT/result/v10-recipient.vmlinux.elf"
exit 1
