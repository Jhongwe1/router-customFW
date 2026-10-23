#!/usr/bin/env bash
# test-spi-install -- R8b Gap A's install path, on the host, then prove the
# suites can fail.
#
# Two suites, four builds, one runner:
#   test-spi-install.c       the DECISIONS: rtl819x-spi-install.h compiled
#                            unchanged (region table, verbs, arm agreement,
#                            staging, payload headers, the write ORDER, D11's
#                            erased range at both candidate sizes, the cuts;
#                            1.1: the store's regions, the counter, its loop,
#                            repeat= and the fence), built TWICE -- `pure`
#                            with the provisioning table
#                            (-DCONFIG_MTD_RTL819X_PROVISION) and `pure0`
#                            with the SHIPPED table, which names nothing
#                            below slot A
#   test-spi-install-glue.c  the GLUE: the block between rtl819x-spi.c's
#                            `R8b GAP A` banner and its `END OF R8b GAP A`
#                            line, and the driver's /proc write handler,
#                            both extracted from the driver and run against
#                            stub kernel APIs and a simulated NOR part; built
#                            TWICE as well -- `glue` (provisioning table) and
#                            `glue0` (the SHIPPED table, the one the device
#                            runs), each the other's control
#
# The payload fixtures are PRODUCED here by tools/mkfw2.py's build() and
# tools/mkcr6c.py's build_image()/gate_image(), with the development seed, so
# the installer is tested against what the producers emit.  The typed digests
# come from Python's hashlib; the glue hashes with src/lib/sha256.c; the
# kernel will hash with crypto/sha256_generic.c -- three implementations.
#
# THE ORDER IS THE POINT.  Both unmutated suites run FIRST and must pass; only
# then are the mutations trusted (CLAUDE.md).  Every mutation must COMPILE
# and then FAIL: a mutation that does not compile is not a kill.
#
# What a green run does NOT say: anything about the silicon, the kernel's own
# APIs, rlxfw_boot_handoff() (a stub here; arch/rlx/kernel/rlxfw-boot.c is not
# compiled), the verbs write_proc reaches outside the block (stubs), the rest
# of read_proc (its length enters as a swept prefix), or the init that creates
# /proc/rtl819x-spi-img -- none of those are in the extracted code.
#
# Exit 0 green; 1 a case or a mutation went the wrong way; 3 an input is
# missing or a producer refused (never a silent skip).
set -u

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(dirname -- "$here")
dev="$repo/kernel/linux-2.6.30/drivers/mtd/devices"
drv="$dev/rtl819x-spi.c"
wtu="$dev/rtl819x-spi-write.c"
ihdr="$dev/rtl819x-spi-install.h"
khdr="$repo/kernel/linux-2.6.30/include/linux/rlxfw-handoff.h"
PY=${PY:-/usr/bin/python3}
CC=${CC:-cc}
out=$(mktemp -d "${TMPDIR:-/tmp}/rlxfw-spi-install.XXXXXX") || exit 3
trap 'rm -rf "$out"' EXIT

kinc="$repo/kernel/linux-2.6.30/include"
for f in "$drv" "$wtu" "$ihdr" "$dev/rtl819x-spi-wrpolicy.h" \
         "$kinc/linux/rlxfw-handoff.h" \
         "$repo/src/rlxboot/container.h" "$repo/src/lib/sha256.c" \
         "$khdr" "$repo/src/rlxboot/handoff.h" \
         "$repo/src/lib/sha256.h" "$here/mkfw2.py" "$here/mkcr6c.py" \
         "$here/test-spi-install.c" "$here/test-spi-install-glue.c"; do
    if [ ! -f "$f" ]; then
        echo "test-spi-install: $f is not there; this runner compiles the" >&2
        echo "  driver's own files, never a copy." >&2
        exit 3
    fi
done

rc=0
red () { echo "  FAIL  $*"; rc=1; }

# No compiler sees both translation units' views of a cross-TU function, so a
# prototype mismatch links silently.  These two are the install path's.
echo "--- drift: functions declared in one TU and defined in the other"
if grep -Fq 'extern void rtl819x_spi_note_write(int erase);' "$wtu" &&
   grep -Fq 'void rtl819x_spi_note_write(int erase)' "$drv"; then
    echo "  ok    rtl819x_spi_note_write: both say (int erase)"
else
    red "rtl819x_spi_note_write: rtl819x-spi-write.c and rtl819x-spi.c disagree"
fi
if grep -Fq 'int rtl819x_spi_wr_get_arm(struct rlxfw_spi_wr_arm *out)' "$wtu" &&
   grep -Fq 'extern int rtl819x_spi_wr_get_arm(struct rlxfw_spi_wr_arm *out);' "$drv"; then
    echo "  ok    rtl819x_spi_wr_get_arm: both say (struct rlxfw_spi_wr_arm *out)"
else
    red "rtl819x_spi_wr_get_arm: rtl819x-spi-write.c and rtl819x-spi.c disagree"
fi
# The glue suite restates four of the driver's constants that live outside
# the extracted block; each must still be the driver's.
for name in RTL819X_SPI_CHUNK RTL819X_SPI_PROC_BUDGET RTL819X_SPI_CMD_SE \
            RTL819X_SPI_WIP_SPINS; do
    dv=$(awk -v n="$name" '$1 == "#define" && $2 == n { print $3; exit }' "$drv")
    tv=$(awk -v n="$name" '$1 == "#define" && $2 == n { print $3; exit }' \
         "$here/test-spi-install-glue.c")
    if [ -n "$dv" ] && [ "$dv" = "$tv" ]; then
        echo "  ok    $name: the glue suite's $tv is the driver's"
    else
        red "$name: the driver says [$dv], the glue suite [$tv]"
    fi
done
# /proc/rtl819x-spi-inst prints n_writes in the main page's own format: the
# same statement twice in the driver, the main page's and the node's.
n=$(grep -cF 'len += sprintf(page + len, "n_writes %lu\n", rtl819x_spi_n_writes);' "$drv")
if [ "$n" = 2 ]; then
    echo "  ok    n_writes: one format, on the main page and on the node"
else
    red "n_writes: the driver prints it with that statement $n time(s), not 2"
fi
# ... and the page the install blocks are measured against ends with this
# statement, whose widest the glue suite adds (PROC_TAIL): the first one after
# the call, past comments and preprocessor lines.
nx=$(awk 'f && !/^[ \t]*(\/\*|\*|#|$)/ { print; exit }
          index($0, "len += rtl819x_spi_inst_proc(page + len, len);") { f = 1 }' "$drv")
case "$nx" in
    *'len += sprintf(page + len, "proc_bytes_before_this_line %d\n", len);'*)
        echo "  ok    read_proc: after the install blocks, only its self-measuring line" ;;
    *) red "read_proc: the statement after rtl819x_spi_inst_proc() is [$nx], not the one the glue suite budgets" ;;
esac
# 1.2: the widest prefix read_proc's comments allow (the glue suite's
# THEORY_PREFIX, 2,323) is the sum of six allowances; each must still be what
# its comment or format says, or the sum is stale.
for pair in "$drv|could already produce is 1,101 bytes" \
            "$drv|add at most 340" \
            "$drv|bytes is 128 against" \
            "$wtu|round number above 714" \
            "$drv|len += sprintf(page + len, \"wr_truncated 0\\n\");" \
            "$drv|len += sprintf(page + len, \"n_wip_timeout %lu\\n\","; do
    f=${pair%%|*}; t=${pair#*|}
    if [ "$(grep -cF "$t" "$f")" -ge 1 ]; then
        echo "  ok    THEORY_PREFIX: [$t] still in $(basename "$f")"
    else
        red "THEORY_PREFIX: [$t] is gone from $(basename "$f"); re-derive the glue suite's widest prefix"
    fi
done

echo "--- extract the driver's Gap A block"
b=$(grep -n 'R8b GAP A -- THE INSTALL PATH' "$drv" | cut -d: -f1)
e=$(grep -n 'END OF R8b GAP A' "$drv" | cut -d: -f1)
if [ "$(printf '%s\n' "$b" | grep -c .)" != 1 ] ||
   [ "$(printf '%s\n' "$e" | grep -c .)" != 1 ]; then
    echo "test-spi-install: the banner or the end marker is not in $drv exactly once" >&2
    exit 3
fi
start=$((b - 1)); end=$((e + 1))
case "$(sed -n "${start}p" "$drv")" in
    '/* ===='*) ;;
    *) echo "test-spi-install: the line above the banner is not its opening rule" >&2; exit 3 ;;
esac
sed -n "${start},${end}p" "$drv" > "$out/gapA.inc"
echo "  lines $start-$end of rtl819x-spi.c, $(wc -l < "$out/gapA.inc") lines"
# The /proc write handler: its dispatcher is what hands `ctr` and `ctrloop`
# lines to the install parser by prefix (notes/self-update.md § 2.4.2).
w=$(grep -n '^static int rtl819x_spi_write_proc(struct file \*file, const char __user \*buffer,$' "$drv" | cut -d: -f1)
if [ "$(printf '%s\n' "$w" | grep -c .)" != 1 ]; then
    echo "test-spi-install: rtl819x_spi_write_proc's first line is not in $drv exactly once" >&2
    exit 3
fi
we=$(awk -v s="$w" 'NR > s && /^}$/ { print NR; exit }' "$drv")
sed -n "${w},${we}p" "$drv" > "$out/writeproc.inc"
if ! grep -q 'ret = rtl819x_spi_verb_inst(buf);' "$out/writeproc.inc"; then
    echo "test-spi-install: the extracted write handler never calls rtl819x_spi_verb_inst" >&2
    exit 3
fi
echo "  write handler: lines $w-$we of rtl819x-spi.c, $(wc -l < "$out/writeproc.inc") lines"
mkdir -p "$out/inc/linux"
: > "$out/inc/linux/vmalloc.h"
: > "$out/inc/linux/delay.h"

echo "--- fixtures from the producers (dev seed)"
mkdir -p "$out/fx"
if ! "$PY" - "$here" "$out/fx" "$ihdr" > "$out/fx.log" 2>&1 <<'PY'
import hashlib, os, re, sys
tools, out, hdr = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, tools)
import mkfw2, mkcr6c, rlxsign

def stream(n, tag):
    b = bytearray()
    i = 0
    while len(b) < n:
        b += hashlib.sha256(tag + b"-%d" % i).digest()
        i += 1
    return bytes(b[:n])

rid = b"\x12\x34\x56\x78"
def cont(name, payload, at, form):
    blob = mkfw2.build(payload, 3, 0x80500000, 0x80500000, rid,
                       rlxsign.DEV_SEED, at, form)
    open(os.path.join(out, name), "wb").write(blob)
    print("  %-16s %8d bytes  flash_at %08X form %08X" % (name, len(blob), at, form))

cont("slotA.rlxu", stream(140000, b"A"), 0x070000, mkfw2.FORM_WHOLE)
cont("slotA-full.rlxu", stream(1179648 - 160, b"F"), 0x070000, mkfw2.FORM_WHOLE)
cont("slotB.rlxu", stream(140000, b"B"), 0x190000, mkfw2.FORM_WHOLE)
cont("slotA-payl.rlxu", stream(140000, b"A"), 0x070000, mkfw2.FORM_PAYLOAD)
cont("nff.rlxu", stream(140000, b"A"), mkfw2.FLASH_NONE, mkfw2.FORM_NONE)
for name, at, n in (("rlxboot.cs6c", 0x010000, 30000),
                    ("rescue.cs6c", 0x020000, 65536 - 18)):
    img = mkcr6c.build_image(stream(n, name.encode()), 0x81800000, at)
    mkcr6c.gate_image(img, at)
    open(os.path.join(out, name), "wb").write(img)
    print("  %-16s %8d bytes  burnAddr %08X" % (name, len(img), at))
    # FW-241's fixture: the same image as mkcr6c 1.0 wrote it, `cr6c`, its sum
    # intact -- the bytes s124 produced and the guard must now refuse.  The
    # producer refuses to make it, so it is made here from the producer's own
    # output, and that refusal is checked too.
    legacy = mkcr6c.CR6C + img[4:]
    try:
        mkcr6c.gate_image(legacy, at)
        sys.exit("mkcr6c.gate_image accepted a cr6c image for %06X" % at)
    except ValueError:
        pass
    lname = name.replace(".cs6c", ".cr6c")
    open(os.path.join(out, lname), "wb").write(legacy)
    print("  %-16s %8d bytes  burnAddr %08X (1.0's signature)" % (lname, len(legacy), at))
with open(os.path.join(out, "digests"), "w") as fh:
    for name in sorted(os.listdir(out)):
        if name != "digests":
            d = hashlib.sha256(open(os.path.join(out, name), "rb").read())
            fh.write("%s %s\n" % (name, d.hexdigest()))

# The region table against the producer's scan policy -- a second source.
txt = open(hdr).read()
v = {}
for name, kind, val in re.findall(
        r"#define\s+RLXFW_SPI_INST_(\w+?)_(BASE|SIZE)\s+(0x[0-9A-Fa-f]+)u", txt):
    v[(name, kind)] = int(val, 16)
bad = []
if tuple(mkcr6c.MUST_BOOT) != (v[("RLXBOOT", "BASE")], v[("RESCUE", "BASE")]):
    bad.append("rlxboot/rescue bases != mkcr6c.MUST_BOOT")
lo, hi = v[("BARRIER", "BASE")], v[("BARRIER", "BASE")] + v[("BARRIER", "SIZE")]
if (min(mkcr6c.MUST_NOT_BOOT) != lo or
        max(mkcr6c.MUST_NOT_BOOT) + mkcr6c.REGION_BYTES != hi):
    bad.append("the barrier is not exactly mkcr6c.MUST_NOT_BOOT's blocks")
for s in ("SLOTA", "SLOTB", "CFG0", "CFG1", "PROBE"):
    b0, b1 = v[(s, "BASE")], v[(s, "BASE")] + v[(s, "SIZE")]
    if any(b0 <= c < b1 for c in mkcr6c.scan_candidates()):
        bad.append("%s holds a loader scan candidate" % s)
# FW-241: why the rlxboot/rescue regions take cs6c and refuse cr6c.  Every
# rootfs candidate a cr6c header sends the locator to lies inside slot A, so
# once slot A holds a container none is a rootfs.  If the layout ever moved so
# that one fell outside, the refusal's stated reason would no longer be true.
a0, a1 = v[("SLOTA", "BASE")], v[("SLOTA", "BASE")] + v[("SLOTA", "SIZE")]
if not all(a0 <= c < a1 for c in mkcr6c.rootfs_candidates()):
    bad.append("a cr6c rootfs candidate lies outside slot A")
# D19's block: after slot B, ending where the state block (0x3F0000) begins
p0, p1 = v[("PROBE", "BASE")], v[("PROBE", "BASE")] + v[("PROBE", "SIZE")]
if not (v[("SLOTB", "BASE")] + v[("SLOTB", "SIZE")] <= p0 and p1 == 0x3F0000):
    bad.append("the probe block is not the last free 64 KiB before 0x3F0000")
print("  region table vs mkcr6c: %s" % ("agree" if not bad else "; ".join(bad)))
sys.exit(1 if bad else 0)
PY
then
    sed 's/^/    /' "$out/fx.log"
    if grep -q 'region table vs mkcr6c:' "$out/fx.log"; then
        red "the region table disagrees with tools/mkcr6c.py (above)"
    else
        echo "test-spi-install: a producer refused; nothing to test against" >&2
        exit 3
    fi
else
    cat "$out/fx.log"
fi

# P6r-10: the store's slot images, from the store's own producer -- src/cfgstore
# built for the host -- so K_CFG is tested against what the store writes, as the
# containers are against mkfw2.  seq 1 lands in slot 0 (both empty), seq 2 in
# slot 1 (the slot not selected).
echo "--- the store's slot images, from src/cfgstore's host build"
if ! make -s -C "$repo/src/cfgstore" host O="$out/cs" > "$out/cs.log" 2>&1; then
    sed 's/^/    /' "$out/cs.log"
    echo "test-spi-install: src/cfgstore's host build failed; no producer for the store's fixtures" >&2
    exit 3
fi
cs="$out/cs/host/cfgstore"
if ! "$cs" --file "$out/fx/store.bin" init --force > "$out/cs-init.log" 2>&1 ||
   ! "$cs" --file "$out/fx/store.bin" set sys.hostname=tsi1 > "$out/cs-set.log" 2>&1; then
    cat "$out/cs-init.log" "$out/cs-set.log"
    echo "test-spi-install: cfgstore refused to write the fixture store" >&2
    exit 3
fi
head -c 4096 "$out/fx/store.bin" > "$out/fx/cfg-seq1.bin"
tail -c +4097 "$out/fx/store.bin" > "$out/fx/cfg-seq2.bin"
echo "  store.bin $(wc -c < "$out/fx/store.bin") bytes -> cfg-seq1.bin $(wc -c < "$out/fx/cfg-seq1.bin"), cfg-seq2.bin $(wc -c < "$out/fx/cfg-seq2.bin")"
# The glue suite types digests for these too, so they join the digest list
# (hashlib's), with two refusals derived from the producer's own output: seq 0
# (HDR_SEQ) and one byte too many (HDR_LEN).  Each derivation is checked to
# have changed exactly what it says.
if ! "$PY" - "$out/fx" > "$out/cfgfx.log" 2>&1 <<'PY'
import hashlib, os, sys
fx = sys.argv[1]
s1 = open(os.path.join(fx, "cfg-seq1.bin"), "rb").read()
if len(s1) != 4096 or s1[:4] != b"RLXC" or s1[8:12] != b"\x00\x00\x00\x01":
    sys.exit("cfg-seq1.bin is not a 4,096-byte RLXC slot image with seq 1")
s0 = s1[:8] + b"\x00\x00\x00\x00" + s1[12:]
open(os.path.join(fx, "cfg-seq0.bin"), "wb").write(s0)
open(os.path.join(fx, "cfg-4097.bin"), "wb").write(s1 + b"\xff")
with open(os.path.join(fx, "digests"), "a") as fh:
    for name in ("cfg-seq0.bin", "cfg-seq1.bin", "cfg-seq2.bin", "cfg-4097.bin"):
        d = hashlib.sha256(open(os.path.join(fx, name), "rb").read())
        fh.write("%s %s\n" % (name, d.hexdigest()))
print("  cfg-seq0.bin (seq 0) and cfg-4097.bin derived; 4 store digests listed")
PY
then
    cat "$out/cfgfx.log"
    echo "test-spi-install: the store's derived fixtures could not be made" >&2
    exit 3
fi
cat "$out/cfgfx.log"

echo "--- compile"
W="-std=gnu89 -Wall -Wextra -Werror -Wdeclaration-after-statement -Wstrict-prototypes -O2"
# The counter's second source is rlxboot's own decode, linked, with what
# container.c links against (run-host-tests.sh's set).
for f in src/rlxboot/container.c src/rlxboot/sha256b.c src/lib/ed25519.c src/lib/sha512.c; do
    o="$out/2s-$(basename "$f" .c).o"
    "$CC" -std=gnu99 -O2 -Wno-sign-compare -c -o "$o" "$repo/$f" 2> "$o.err" ||
        { cat "$o.err"; exit 3; }
done
build_pure () {   # build_pure OUT PROVISION(0|1) [EXTRA-INCLUDE-DIR]
    local pdef=
    [ "$2" = 1 ] && pdef=-DCONFIG_MTD_RTL819X_PROVISION
    # shellcheck disable=SC2086
    $CC $W -DWITH_CONTAINER_H -DWITH_CFG_H -DWITH_CONTAINER_C $pdef \
        ${3:+-I "$3"} -I "$dev" -I "$repo/src/rlxboot" -I "$repo/src/lib" \
        -I "$repo/kernel/linux-2.6.30/include/linux" \
        -o "$1" "$here/test-spi-install.c" "$out"/2s-*.o 2> "$1.err"
}
"$CC" -std=gnu99 -O2 -c -o "$out/sha256.o" "$repo/src/lib/sha256.c" 2> "$out/sha.err" ||
    { cat "$out/sha.err"; exit 3; }
build_glue () {   # build_glue OUT INCDIR PROVISION(0|1)
    # INCDIR holds a mutated gapA.inc or writeproc.inc, if any; $out holds
    # both as extracted, so whichever one is not mutated is found there.
    # <linux/rlxfw-handoff.h> is the repository's own (kernel/linux-2.6.30/
    # include/), searched after the empty vmalloc.h/delay.h stand-ins.
    local pdef=
    [ "$3" = 1 ] && pdef=-DCONFIG_MTD_RTL819X_PROVISION
    # shellcheck disable=SC2086
    $CC $W -Wno-unused-parameter $pdef \
        -I "$2" -I "$out" -I "$out/inc" -I "$dev" -I "$repo/src/lib" \
        -I "$kinc" -o "$1" "$here/test-spi-install-glue.c" "$out/sha256.o" \
        2> "$1.err"
}
if ! build_pure "$out/pure" 1; then cat "$out/pure.err"; exit 3; fi
if ! build_pure "$out/pure0" 0; then cat "$out/pure0.err"; exit 3; fi
if ! build_glue "$out/glue" "$out" 1; then cat "$out/glue.err"; exit 3; fi
if ! build_glue "$out/glue0" "$out" 0; then cat "$out/glue0.err"; exit 3; fi
echo "  all four built with: $W"

echo "--- arm 1 of 3: the suites as declared (must PASS)"
"$out/pure" --fixtures "$out/fx" > "$out/pure.out"; prc=$?
"$out/pure0" --fixtures "$out/fx" > "$out/pure0.out"; p0rc=$?
"$out/glue" --fixtures "$out/fx" > "$out/glue.out"; grc=$?
"$out/glue0" --fixtures "$out/fx" > "$out/glue0.out"; g0rc=$?
grep -v '^  ok ' "$out/pure.out"
grep -v '^  ok ' "$out/pure0.out"
grep -v '^  ok ' "$out/glue.out"
grep -v '^  ok ' "$out/glue0.out"
echo "  pure suite exit $prc, shipped-table pure suite exit $p0rc, glue suite exit $grc, shipped-table glue suite exit $g0rc"
if [ "$prc" != 0 ] || [ "$p0rc" != 0 ] || [ "$grc" != 0 ] || [ "$g0rc" != 0 ]; then
    echo "test-spi-install: an unmutated suite FAILED; the mutations below would prove nothing" >&2
    exit 1
fi

echo "--- arm 2 of 3: expectation flips (each must FAIL)"
idx () { sed -n "s/^  ok  *\([0-9][0-9]*\) $2.*/\1/p" "$1" | head -n 1; }
for spec in "pure|install slotA sha=<64 lower>" \
            "pure|a PAYL-form container for slotA" \
            "pure|D11 control: a 64 KiB step" \
            "pure|ctr 6" \
            "pure|I a cut after k programs" \
            "pure0|shipped: install rlxboot is not nameable" \
            "pure0|M decode == rlxboot's rlxu_counter_from_bitmap" \
            "pure|M handoff slot and version wrong (own check): SLOT first" \
            "pure0|M round trip: rlxboot's magic, slot, version and check word" \
            "glue|grain 4096 pace 0: install slotA -> OK" \
            "glue|not armed -> UNARMED" \
            "glue|rlxboot.cs6c on rlxboot at a 64 KiB grain" \
            "glue|ctr 6 on an erased counter" \
            "glue|handoff names A: install slotA -> RUNNING_SLOT" \
            "glue|ctrloop 2 under the probe arm -> OK" \
            "glue|the node at the widest state is exactly" \
            "glue0|one read(2) of the node, through generic.c's loop" \
            "glue0|grain 4096 pace 0: install slotA -> OK" \
            "glue0|shipped: install rlxboot is not nameable" \
            "glue0|shipped: across the whole run the lowest address" \
            "pure|K 1.2's widest state: se_us and pp_us at ten digits" \
            "pure|K RLXFW_SPI_INST_PROC_MAX is the MEASURED widest block" \
            "pure|K RLXFW_SPI_INST_CTR_PROC_MAX is the MEASURED widest block" \
            "pure|L ctr_addr(base, b) is base + b" \
            "pure|L a show whose read failed records its errno" \
            "glue|every block that printed fit the budget" \
            "glue|at the widest prefix read_proc's comments allow" \
            "glue0|ctrloop show with no memory: ENOMEM"; do
    s=${spec%%|*}; name=${spec#*|}
    n=$(idx "$out/$s.out" "$name")
    if [ -z "$n" ]; then red "no case named '$name' in the $s suite"; continue; fi
    if "$out/$s" --fixtures "$out/fx" --mutate "$n" > /dev/null 2>&1; then
        red "$s case $n ($name) inverted and the suite still PASSED"
    else
        echo "  ok    $s case $n inverted -> red ($name)"
    fi
done

echo "--- arm 3 of 3: source mutations (each must compile, then FAIL)"
mutate () {   # mutate LABEL SUITE FILE SED-EXPR
    local label=$1 suite=$2 file=$3 expr=$4 d="$out/m-$1" n
    mkdir -p "$d"
    sed -e "$expr" "$file" > "$d/$(basename "$file")"
    n=$(diff "$file" "$d/$(basename "$file")" | grep -c '^>')
    if [ "$n" -lt 1 ]; then red "mutation $label changed nothing -- fix the runner"; return; fi
    if [ "$suite" = pure ] || [ "$suite" = pure0 ]; then
        build_pure "$d/bin" "$([ "$suite" = pure ] && echo 1 || echo 0)" "$d" ||
            { red "mutation $label did not compile (not a kill)"; return; }
    else
        build_glue "$d/bin" "$d" "$([ "$suite" = glue ] && echo 1 || echo 0)" ||
            { red "mutation $label did not compile (not a kill)"; return; }
    fi
    if "$d/bin" --fixtures "$out/fx" > "$d/out" 2>&1; then
        red "mutation $label ($n line(s)) PASSED -- the suite cannot see it"
    else
        echo "  ok    $label -> red ($(grep -c '^  FAIL' "$d/out") failing case(s))"
    fi
}
mutate H1-arm-window   pure "$ihdr" 's/if (a->lo != rg->base || a->hi != rg->base + rg->size)/if (0)/'
mutate H2-flash-at     pure "$ihdr" 's/if (rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_RLXU_FLASH_OFF) != base)/if (rlxfw_spi_inst_be32(img + RLXFW_SPI_INST_RLXU_FLASH_OFF) != base \&\& 0)/'
mutate H3-header-first pure "$ihdr" 's/k = (j + 1u < pl->np) ? j + 1u : 0u;/k = j;/'
mutate H4-no-sum16     pure "$ihdr" 's/if ((sum & 0xFFFFu) != 0u)/if (0)/'
mutate H5-overflow     pure "$ihdr" 's/if (count > (unsigned long)(RLXFW_SPI_INST_IMG_CAP - im->len)) {/if (count > (unsigned long)(RLXFW_SPI_INST_IMG_CAP - im->len) + 1ul) {/'
mutate H6-pace-ceiling pure "$ihdr" 's/v == 0u || v > RLXFW_SPI_INST_PACE_MAX)/v == 0u || v > RLXFW_SPI_INST_PACE_MAX + 1u)/'
mutate H6b-pace-20s    pure "$ihdr" 's/^#define RLXFW_SPI_INST_PACE_MAX\t\t30000u$/#define RLXFW_SPI_INST_PACE_MAX\t\t10000u/'
mutate H7-half-erase   pure "$ihdr" 's|pl->ne = rg->size / grain;|pl->ne = rg->size / grain / 2u;|'
mutate B1-no-disarm    glue "$out/gapA.inc" 's/^\trtl819x_spi_wr_do_disarm();$//'
mutate B2-no-sha       glue "$out/gapA.inc" 's/if (!r->sha_ok) {/if (0) {/'
mutate B3-no-cmp       glue "$out/gapA.inc" 's/if (r->cmp_diff) {/if (0) {/'
mutate B4-wrong-src    glue "$out/gapA.inc" 's/rtl819x_spi_img + op.off);/rtl819x_spi_img);/'
mutate B5-no-arm-check glue "$out/gapA.inc" 's/why = rlxfw_spi_inst_chk_arm(&arm, rg);/why = 0;/'
mutate B6-no-policy    glue "$out/gapA.inc" 's/if (r->policy) {/if (0) {/g'
mutate B7-ignore-getter glue "$out/gapA.inc" 's/if (rtl819x_spi_wr_get_arm(&arm))/if (rtl819x_spi_wr_get_arm(\&arm) \&\& 0)/'
mutate B8-probe-dirty  glue "$out/gapA.inc" 's/if (!ff) {/if (0) {/'
mutate B9-stale-clean  glue "$out/gapA.inc" 's/^\t\tp->clean_known = 0;$//'
mutate H9-size-table   pure "$ihdr" 's/^\t\treturn 4096;$/\t\treturn 32768;/'
mutate H10-anomaly-raw pure "$ihdr" 's/^\t\treturn 0x1000u;$/\t\treturn 0u;/'
mutate H11-verdict     pure "$ihdr" 's/if (clean != 1)/if (clean == 0)/'
mutate H12-cr6c-magic  pure "$ihdr" 's/^#define RLXFW_SPI_INST_CR6C_MAGIC\t0x63733663u/#define RLXFW_SPI_INST_CR6C_MAGIC\t0x63723663u/'
# 1.1, P6r-10 and P6r-11
mutate H13-ctr-two-bits pure "$ihdr" 's/return (u8)(0xFFu >> ((b & 7u) + 1u));/return (u8)(0xFFu >> ((b \& 7u) + 2u));/'
mutate H14-ctr-lead-only pure "$ihdr" 's/return bad ? total : lead;/return lead;/'
mutate H15-ctr-no-below pure "$ihdr" 's/if (n < \*cur)/if (0)/'
mutate H16-ctr-weak-tie pure "$ihdr" 's/if (!ho_ok || ho_ver != n)/if (!ho_ok \&\& ho_ver != n)/'
mutate H17-no-fence    pure "$ihdr" 's/return RLXFW_SPI_INST_R_RUNNING_SLOT;/return RLXFW_SPI_INST_OK;/'
mutate H18-cfg-seq0    pure "$ihdr" 's/if (seq == 0u || seq > RLXFW_SPI_INST_CFG_SEQ_MAX)/if (seq > RLXFW_SPI_INST_CFG_SEQ_MAX)/'
mutate H19-repeat-any  pure "$ihdr" 's/return RLXFW_SPI_INST_R_REPEAT_ONLY_SLOT;/(void)0;/'
mutate H20-shipped-floor pure0 "$ihdr" 's/{ "slotA",   RLXFW_SPI_INST_SLOTA_BASE,/{ "slotA",   RLXFW_SPI_INST_RLXBOOT_BASE,/'
mutate H21-cfg-not-erasable pure "$ihdr" 's/rg->kind != RLXFW_SPI_INST_K_CFG)/1)/'
mutate H22-loop-ops    pure "$ihdr" 's/^#define RLXFW_SPI_INST_LOOP_OPS\t(RLXFW_SPI_INST_CTR_BITS + 1u)/#define RLXFW_SPI_INST_LOOP_OPS\t(RLXFW_SPI_INST_CTR_BITS + 2u)/'
mutate H23-no-ctrloop  pure "$ihdr" 's/if (rlxfw_spi_inst_tokeq(s, n, "ctrloop"))/if (0)/'
mutate H24-ctr-prefix  pure "$ihdr" 's/if (rlxfw_spi_inst_tokeq(s, n, "ctr"))/if (rlxfw_spi_inst_prefix(s, n, "ctr"))/'
# 1.1's glue (notes/self-update.md §§ 2.4-2.7): the counter, its loop, the
# fence, repeat= and the dispatcher, each mutated in the driver's own text
mutate B10-ctr-se      glue "$out/gapA.inc" 's/^\trlxfw_spi_inst_fmt_ctr_go(say, c->cur, c->newv);$/\t(void)rtl819x_spi_se_block(RLXFW_SPI_INST_STATE); rlxfw_spi_inst_fmt_ctr_go(say, c->cur, c->newv);/'
mutate B11-ctr-no-tie  glue "$out/gapA.inc" 's/why = rlxfw_spi_inst_ctr_tie(rq->ctr_n, ho_ok, ho_ver);/why = rlxfw_spi_inst_ctr_tie(rq->ctr_n, ho_ok, ho_ver) \&\& 0;/'
mutate B12-no-fence    glue "$out/gapA.inc" 's/why = rlxfw_spi_inst_fence(rg, rtl819x_spi_handoff(&ho_ver));/why = rlxfw_spi_inst_fence(rg, rtl819x_spi_handoff(\&ho_ver)) \&\& 0;/'
mutate B12b-no-fence-shipped glue0 "$out/gapA.inc" 's/why = rlxfw_spi_inst_fence(rg, rtl819x_spi_handoff(&ho_ver));/why = rlxfw_spi_inst_fence(rg, rtl819x_spi_handoff(\&ho_ver)) \&\& 0;/'
mutate B13-ctr-two-bits glue "$out/gapA.inc" 's/rlxfw_spi_inst_ctr_value(b), &rc);/(u8)(rlxfw_spi_inst_ctr_value(b) >> 1), \&rc);/'
mutate B14-ctr-no-readback glue "$out/gapA.inc" 's/why = rlxfw_spi_inst_ctr_verify(rb, rq->ctr_n);/why = RLXFW_SPI_INST_OK;/'
mutate B15-repeat-once glue "$out/gapA.inc" 's/nrep = rq.repeat ? rq.repeat : 1u;/nrep = 1u;/'
mutate B16-loop-no-final-se glue "$out/gapA.inc" 's/nops = rlxfw_spi_inst_loop_nops(rq->loops);/nops = rlxfw_spi_inst_loop_nops(rq->loops) - 1u;/'
mutate B17-ctr-no-nwrites glue "$out/gapA.inc" 's/^\trtl819x_spi_note_write(0);\t\/\* n_writes: one per bit cleared \*\/$//'
mutate B18-no-ctr-dispatch glue "$out/writeproc.inc" 's/!strncmp(buf, "ctr", 3))$/0)/'
mutate B19-no-ctr-proc glue "$out/gapA.inc" 's/len += rlxfw_spi_inst_emit_ctr(page, &rtl819x_spi_ctr_st);/(void)0;/'
# 1.2: ctr_addr(), the scratch reading in /proc, the blocks measured whole,
# the counter's block first
mutate H25-ctr-addr    pure "$ihdr" 's/return base + (b >> 3);/return base + (b >> 2);/'
mutate H26-scratch-on-failure pure "$ihdr" 's/^\tif (rc != 0)$/\tif (0)/'
mutate H27-max-without-line pure "$ihdr" 's/^#define RLXFW_SPI_INST_PROC_MAX\t\t1183$/#define RLXFW_SPI_INST_PROC_MAX\t\t1166/'
mutate H27b-max-without-line-glue glue "$ihdr" 's/^#define RLXFW_SPI_INST_PROC_MAX\t\t1183$/#define RLXFW_SPI_INST_PROC_MAX\t\t1166/'
mutate H28-ctr-max     pure "$ihdr" 's/^#define RLXFW_SPI_INST_CTR_PROC_MAX\t501$/#define RLXFW_SPI_INST_CTR_PROC_MAX\t500/'
mutate H29-no-inst-line pure "$ihdr" 's/^\tlen += sprintf(p + len, "inst_truncated 0\\n");$/\t(void)0;/'
mutate B20-show-unrecorded glue "$out/gapA.inc" 's/rlxfw_spi_inst_scratch_note(c, rc, buf, RTL819X_SPI_CHUNK);/(void)0;/'
mutate B21-inst-block-first glue "$out/gapA.inc" 's/if (used + RLXFW_SPI_INST_CTR_PROC_MAX <= RTL819X_SPI_PROC_BUDGET)/if (used + RLXFW_SPI_INST_PROC_MAX + RLXFW_SPI_INST_CTR_PROC_MAX <= RTL819X_SPI_PROC_BUDGET)/'
mutate B22-glue-own-addr glue "$out/gapA.inc" 's/rlxfw_spi_inst_ctr_addr(RLXFW_SPI_INST_STATE, b),/RLXFW_SPI_INST_STATE + (b >> 2),/'
# P6r-10: the boot handoff's parse, include/linux/rlxfw-handoff.h (group M)
mutate HO1-no-check   pure "$khdr" 's/if (a3 != ~(a0 ^ a1 ^ a2))/if (a3 != ~(a0 ^ a1 ^ a2) \&\& 0)/'
mutate HO2-slot-after-version pure "$khdr" '/a1 != RLXFW_HANDOFF_SLOT_A/{N;h;d};/return RLXFW_HO_VERSION;/G'
mutate HO3-ver-ceiling pure "$khdr" 's/a2 > 0xFFFFFFFEu/a2 > 0xFFFFFFFFu/'
mutate HO4-magic-off  pure "$khdr" 's/^#define RLXFW_HANDOFF_MAGIC\t0x524C5848u/#define RLXFW_HANDOFF_MAGIC\t0x524C5849u/'
# /proc/rtl819x-spi-inst
mutate B23-node-no-nwrites glue "$out/gapA.inc" 's/^\tlen += sprintf(page + len, "n_writes %lu\\n", rtl819x_spi_n_writes);$/\t(void)0;/'

# The one check here where NOT compiling is the expected result, so it is a
# refusal check and not a kill: the node's one-read assert must stop a build
# whose widest node would not fit one read(2).  The plant is an over-long
# counter block (2,000 bytes: 20 + 1,183 + 2,000 = 3,203 > 3,072); its
# control, the same build with the header copied unplanted, must compile.
echo "--- compile refusal: a node over one read(2) must NOT build"
d="$out/r-node"; mkdir -p "$d/plant" "$d/copy"
sed -e 's/^#define RLXFW_SPI_INST_CTR_PROC_MAX\t501$/#define RLXFW_SPI_INST_CTR_PROC_MAX\t2000/' \
    "$ihdr" > "$d/plant/rtl819x-spi-install.h"
cp "$ihdr" "$d/copy/rtl819x-spi-install.h"
if cmp -s "$ihdr" "$d/plant/rtl819x-spi-install.h"; then
    red "R1: the plant changed nothing -- fix the runner"
elif ! build_glue "$d/copy/bin" "$d/copy" 1; then
    red "R1 control: the unplanted copy did not compile, so a refusal would prove nothing"
    cat "$d/copy/bin.err"
elif build_glue "$d/plant/bin" "$d/plant" 1; then
    red "R1: a node of 3,203 bytes COMPILED -- the one-read assert does not hold"
elif grep -q 'rlxfw_spi_inst_assert_node_one_read' "$d/plant/bin.err"; then
    echo "  ok    R1 control: the same build, header unplanted, compiles"
    echo "  ok    R1 a planted 2,000-byte counter block (a 3,203-byte node) refuses to compile, at the node_one_read assert"
else
    red "R1: the planted build failed, but not at the node_one_read assert"
    cat "$d/plant/bin.err"
fi

if [ "$rc" -ne 0 ]; then
    echo "test-spi-install: FAILED (see FAIL lines above)" >&2
    exit 1
fi
echo "test-spi-install: ok ($(grep -c '^  ok ' "$out/pure.out") pure + $(grep -c '^  ok ' "$out/pure0.out") shipped-table pure + $(grep -c '^  ok ' "$out/glue.out") glue + $(grep -c '^  ok ' "$out/glue0.out") shipped-table glue cases green; every flip and mutation red)"
exit 0
