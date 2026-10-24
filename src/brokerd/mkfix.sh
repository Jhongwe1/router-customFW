#!/bin/sh
# src/brokerd/mkfix.sh -- the containers test_update and test_e2e read.
#
#   mkfix.sh <repo> <outdir>
#
# Every container but two is made by tools/mkfw2.py, the format's producer,
# signed with the development seed (`--dev-seed`, devkey.h's 32 x 0x42) except
# `b6key`, signed with a seed of 32 x 0x43 that no build here trusts: on the
# host that is § 4.6's "the development key" row (a key the build does not
# trust; the host build trusts the development key, as rlxboot's host suite
# does).  Each is declared for its slot, form whole, as an installed slot must
# be (src/rlxboot/slots.c's DECISION).  The 4 MiB flash images are the tests'
# own: mkfw2.py has no image verb, so each test writes these containers at
# 0x070000 / 0x190000 of simkern's 4 MiB file and the counter's bitmap at
# 0x3F0000.
#
# `big` is 1,108,992 payload bytes, a 1,109,152-byte container: `FW-246`'s
# length, so the accepted install's n_writes is the measured 4,621.
#
# The exit code is the first failing step's; nothing is left half-written
# (each container is mkfw2's own tmp-then-rename).
set -eu
REPO=${1:?repo}
OUT=${2:?outdir}
PY=${PYTHON:-/usr/bin/python3}
MK="$REPO/tools/mkfw2.py"

mkdir -p "$OUT"
"$PY" -B -c '
import sys
def put(path, n, k):
    data = bytes(((i * k + 5) ^ (i >> 7)) & 0xFF for i in range(n))
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    import os
    os.replace(path + ".tmp", path)
put(sys.argv[1], 3000, 13)
put(sys.argv[2], 1108992, 29)
' "$OUT/p_small.bin" "$OUT/p_big.bin"

one() {
	# name payload version flash_at [seed args...]
	name=$1; pay=$2; ver=$3; at=$4; shift 4
	"$PY" -B "$MK" build --payload "$OUT/$pay" --out "$OUT/$name.rlxu" \
	    --version "$ver" --load-addr 0x80500000 --entry-addr 0x80500000 \
	    --recipe-id 3685a3a4 --flash-at "$at" --flash-form whole "$@" \
	    > "$OUT/$name.log"
}

one a5    p_small.bin 5 0x070000 --dev-seed
one a6    p_small.bin 6 0x070000 --dev-seed
one a7    p_small.bin 7 0x070000 --dev-seed
one b5    p_small.bin 5 0x190000 --dev-seed
one b6    p_small.bin 6 0x190000 --dev-seed
one b7    p_small.bin 7 0x190000 --dev-seed
one b6big p_big.bin   6 0x190000 --dev-seed
one b6key p_small.bin 6 0x190000 \
    --seed-hex 4343434343434343434343434343434343434343434343434343434343434343

# The environment's cases: containers whose load address rlxboot's own
# environment refuses -- slot B's RAM buffer (dst_buf) and stage 2's window
# (dst_loader), which mkfw2.py builds, and rlxboot's own range (dst_self),
# which mkfw2.py REFUSES to emit (its verify checks 0x81800000-0x818FFFFF).
# Those two come from src/rlxboot/test/mkfixture.c, rlxboot's own fixture
# builder, development key, no checks: an independent second producer.
mkf_load() {
	# name payload version load flash_at
	name=$1; pay=$2; ver=$3; la=$4; at=$5
	"$PY" -B "$MK" build --payload "$OUT/$pay" --out "$OUT/$name.rlxu" \
	    --version "$ver" --load-addr "$la" --entry-addr "$la" \
	    --recipe-id 3685a3a4 --flash-at "$at" --flash-form whole --dev-seed \
	    > "$OUT/$name.log"
}
mkf_load b6buf p_small.bin 6 0x81200000 0x190000
mkf_load b6ldr p_small.bin 6 0x80400000 0x190000

CC=${HOSTCC:-gcc-13}
W="-std=gnu99 -O1 -Wall -Wextra -Werror"
D="-DED25519_SIGN -DED25519_KEYGEN -DRLXBOOT_WANT_SEED"
"$CC" $W -Wno-sign-compare $D -c -o "$OUT/mkfixture-ed25519.o" "$REPO/src/lib/ed25519.c"
"$CC" $W $D -o "$OUT/mkfixture" "$REPO/src/rlxboot/test/mkfixture.c" \
    "$REPO/src/rlxboot/sha256b.c" "$REPO/src/lib/sha512.c" "$OUT/mkfixture-ed25519.o"
"$OUT/mkfixture" container "$OUT/b6self.rlxu" "$OUT/p_small.bin" 6 81800000 \
    81800000 3685a3a4 190000 whole > "$OUT/b6self.log"
"$OUT/mkfixture" container "$OUT/b6selfhi.rlxu" "$OUT/p_small.bin" 6 818FF000 \
    818FF000 3685a3a4 190000 whole > "$OUT/b6selfhi.log"
# mkfixture's container must be the format mkfw2.py's verify reads: the same
# bytes but the load address, so check its b6 twin verifies under mkfw2.py
"$OUT/mkfixture" container "$OUT/b6mkf.rlxu" "$OUT/p_small.bin" 6 80500000 \
    80500000 3685a3a4 190000 whole > "$OUT/b6mkf.log"
cmp -s "$OUT/b6mkf.rlxu" "$OUT/b6.rlxu" || {
	echo "mkfix: REFUSED: mkfixture's B6 is not mkfw2.py's B6 byte for byte"; exit 1; }
rm -f "$OUT/b6mkf.rlxu"

n=$(ls "$OUT"/*.rlxu | wc -l)
[ "$n" = 12 ] || { echo "mkfix: REFUSED: $n containers in $OUT, want 12"; exit 1; }
echo "mkfix: 12 containers in $OUT (mkfixture's B6 equals mkfw2.py's byte for byte)"
