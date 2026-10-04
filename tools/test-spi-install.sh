#!/usr/bin/env bash
# test-spi-install -- R8b Gap A's install path, on the host, then prove the
# suites can fail.
#
# Two suites, one runner:
#   test-spi-install.c       the DECISIONS: rtl819x-spi-install.h compiled
#                            unchanged (region table, verbs, arm agreement,
#                            staging, payload headers, the write ORDER, D11's
#                            erased range at both candidate sizes, the cuts)
#   test-spi-install-glue.c  the GLUE: the block between rtl819x-spi.c's
#                            `R8b GAP A` banner and its `END OF R8b GAP A`
#                            line, extracted from the driver and run against
#                            stub kernel APIs and a simulated NOR part
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
# APIs, the dispatcher in rtl819x_spi_write_proc, or the init that creates
# /proc/rtl819x-spi-img -- none of those are in the extracted block.
#
# Exit 0 green; 1 a case or a mutation went the wrong way; 3 an input is
# missing or a producer refused (never a silent skip).
set -u

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(dirname -- "$here")
dev="$repo/config/rlxfw-src/linux-2.6.30/drivers/mtd/devices"
drv="$dev/rtl819x-spi.c"
wtu="$dev/rtl819x-spi-write.c"
ihdr="$dev/rtl819x-spi-install.h"
PY=${PY:-/usr/bin/python3}
CC=${CC:-cc}
out=$(mktemp -d "${TMPDIR:-/tmp}/rlxfw-spi-install.XXXXXX") || exit 3
trap 'rm -rf "$out"' EXIT

for f in "$drv" "$wtu" "$ihdr" "$dev/rtl819x-spi-wrpolicy.h" \
         "$repo/src/rlxboot/container.h" "$repo/src/lib/sha256.c" \
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
for name, at, n in (("rlxboot.cr6c", 0x010000, 30000),
                    ("rescue.cr6c", 0x020000, 65536 - 18)):
    img = mkcr6c.build_image(stream(n, name.encode()), 0x81800000, at)
    mkcr6c.gate_image(img, at)
    open(os.path.join(out, name), "wb").write(img)
    print("  %-16s %8d bytes  burnAddr %08X" % (name, len(img), at))
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
for s in ("SLOTA", "SLOTB", "PROBE"):
    b0, b1 = v[(s, "BASE")], v[(s, "BASE")] + v[(s, "SIZE")]
    if any(b0 <= c < b1 for c in mkcr6c.scan_candidates()):
        bad.append("%s holds a loader scan candidate" % s)
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

echo "--- compile"
W="-std=gnu89 -Wall -Wextra -Werror -Wdeclaration-after-statement -Wstrict-prototypes -O2"
build_pure () {   # build_pure OUT [EXTRA-INCLUDE-DIR]
    # shellcheck disable=SC2086
    $CC $W -DWITH_CONTAINER_H ${2:+-I "$2"} -I "$dev" -I "$repo/src/rlxboot" \
        -o "$1" "$here/test-spi-install.c" 2> "$1.err"
}
"$CC" -std=gnu99 -O2 -c -o "$out/sha256.o" "$repo/src/lib/sha256.c" 2> "$out/sha.err" ||
    { cat "$out/sha.err"; exit 3; }
build_glue () {   # build_glue OUT INCDIR-WITH-gapA.inc [EXTRA-INCLUDE-DIR]
    # shellcheck disable=SC2086
    $CC $W -Wno-unused-parameter ${3:+-I "$3"} -I "$2" -I "$out/inc" -I "$dev" \
        -I "$repo/src/lib" -o "$1" "$here/test-spi-install-glue.c" "$out/sha256.o" \
        2> "$1.err"
}
if ! build_pure "$out/pure"; then cat "$out/pure.err"; exit 3; fi
if ! build_glue "$out/glue" "$out"; then cat "$out/glue.err"; exit 3; fi
echo "  both built with: $W"

echo "--- arm 1 of 3: the suites as declared (must PASS)"
"$out/pure" --fixtures "$out/fx" > "$out/pure.out"; prc=$?
"$out/glue" --fixtures "$out/fx" > "$out/glue.out"; grc=$?
grep -v '^  ok ' "$out/pure.out"
grep -v '^  ok ' "$out/glue.out"
echo "  pure suite exit $prc, glue suite exit $grc"
if [ "$prc" != 0 ] || [ "$grc" != 0 ]; then
    echo "test-spi-install: an unmutated suite FAILED; the mutations below would prove nothing" >&2
    exit 1
fi

echo "--- arm 2 of 3: expectation flips (each must FAIL)"
idx () { sed -n "s/^  ok  *\([0-9][0-9]*\) $2.*/\1/p" "$1" | head -n 1; }
for spec in "pure|install slotA sha=<64 lower>" \
            "pure|a PAYL-form container for slotA" \
            "pure|D11 control: a 64 KiB step" \
            "glue|grain 4096 pace 0: install slotA -> OK" \
            "glue|not armed -> UNARMED"; do
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
    if [ "$suite" = pure ]; then
        build_pure "$d/bin" "$d" || { red "mutation $label did not compile (not a kill)"; return; }
    else
        build_glue "$d/bin" "$d" || { red "mutation $label did not compile (not a kill)"; return; }
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

if [ "$rc" -ne 0 ]; then
    echo "test-spi-install: FAILED (see FAIL lines above)" >&2
    exit 1
fi
echo "test-spi-install: ok ($(grep -c '^  ok ' "$out/pure.out") pure + $(grep -c '^  ok ' "$out/glue.out") glue cases green; every flip and mutation red)"
exit 0
