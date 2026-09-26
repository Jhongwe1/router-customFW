#!/usr/bin/env bash
# The suite for tools/ethcensus.py (R6b-8 8a): the census that decides D8's
# "no vendor Ethernet code in vmlinux".
#
# Four layers, because a green census is only a claim about its controls:
#
#   * the command line: usage and refusal exit codes, no traceback
#   * the self-test, run as a process and read from a file.  Its cases are
#     synthetic kbuild trees assembled with the host binutils (a vendor-
#     present reference, a vendor-free tree with the seam, and one mutant
#     each: an eleventh vendor name in the seam, a seam name defined twice,
#     an empty population, a surviving MIPS16 vendor function, the
#     segment-113 parser against nm in both modes, and one tree per census
#     and per guard on which only that census or guard decides)
#   * the same trees through the real process (`self-test --keep`), so the
#     exit codes a CI step reads are the ones tested
#   * mutations of ethcensus.py itself: each must turn the self-test case it
#     names red, and the unmutated copy must pass through the same path
#
# The reference layer needs r6b6q2's build tree ($FWRE_WORK, the desk only).
# Without it the block prints ONE skip line standing for its cases; CI has
# no build tree.  It needs binutils-mips-linux-gnu and declares no skip for
# it: without the binutils the self-test REFUSES and this suite goes red.
#
# 🔴 The self-test's case lines carry the same two leading spaces as this
# suite's, so they are captured to a file and never echoed: ci-census reads
# `.out` files by line and would add them to this suite's total.
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EC="$HERE/ethcensus.py"
FX="$HERE/ethcensus-population.txt"
PY="${PYTHON:-/usr/bin/python3}"
REF="${ETHCENSUS_REF:-/home/key/fwre-work/rebuild/r3-4/cells/r6b6q2/top/linux-2.6.30}"
SEAM=drivers/net/rlxfw-seam.o
export PYTHONDONTWRITEBYTECODE=1

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then
        printf '  ok     %-58s %s\n' "$1" "$3"; pass=$((pass+1))
    else
        printf '  FAIL   %s  expected %s, got %s\n' "$1" "$2" "$3"
        fail=$((fail+1))
    fi
}
run () { # outfile tool args...
    local out="$1" tool="$2"; shift 2
    set +o errexit
    "$PY" "$tool" "$@" > "$out" 2>&1
    rc=$?
    set -o errexit
}
has () { grep -qF -- "$2" "$1" && echo 1 || echo 0; }
notrace () { grep -q 'Traceback' "$1" && echo 0 || echo 1; }
# The line a self-test prints for one case: "ok" or "FAIL" (or "none").
verdict () { # outfile label
    local v
    v="$(sed -n "s/^  \(ok\|FAIL\) *$2 .*/\1/p" "$1" | head -1)"
    echo "${v:-none}"
}

# --- the command line -------------------------------------------------------
run "$T/u1.out" "$EC"
ck "no mode is a usage error"                          3 "$rc"
run "$T/u2.out" "$EC" census --build x
ck "an unknown mode is a usage error"                  3 "$rc"
run "$T/u3.out" "$EC" check --build x --image y
ck "check without --seam is a usage error"             3 "$rc"
mkdir -p "$T/notatree"
run "$T/u4.out" "$EC" check --build "$T/notatree" --image "$T/u1.out" \
    --seam "$SEAM"
ck "a tree with no vmlinux is REFUSED"                 2 "$rc"
ck "  ... with a reason, not a traceback"              11 \
   "$(has "$T/u4.out" 'REFUSED:')$(notrace "$T/u4.out")"
printf 'not a fixture\n' > "$T/bad.fx"
run "$T/u5.out" "$EC" check --build "$T/notatree" --image "$T/u1.out" \
    --seam "$SEAM" --fixture "$T/bad.fx"
ck "a malformed fixture is REFUSED before anything is read" 2 "$rc"
mkdir -p "$T/alone"
cp "$EC" "$T/alone/"
run "$T/u6.out" "$T/alone/ethcensus.py" check --build "$T/notatree" \
    --image "$T/u1.out" --seam "$SEAM"
ck "without imgprocs.py beside it: REFUSED, exit 2, no traceback" "2 1 1" \
   "$rc $(has "$T/u6.out" 'REFUSED: imgprocs.py not found') $(notrace "$T/u6.out")"

# --- the self-test, as a process --------------------------------------------
run "$T/st.out" "$EC" self-test --keep "$T/keep"
ck "self-test exits 0"                                 0 "$rc"
n_ok="$(grep -cE '^  ok ' "$T/st.out" || true)"
n_all="$(grep -cE '^  (ok|FAIL) ' "$T/st.out" || true)"
ck "self-test: every case ok, and more than 30 of them" 1 \
   "$([ "$n_ok" = "$n_all" ] && [ "$n_all" -gt 30 ] && echo 1 || echo 0)"
for m in M1 M2 M3a M3b M4 M5 M5c M5v M8 M9; do
    ck "self-test mutant $m is killed (its case ok)"   ok "$(verdict "$T/st.out" "$m")"
done
ck "self-test control: the reference reads RED"        ok "$(verdict "$T/st.out" C1)"
ck "self-test: the vendor-free tree reads GREEN"       ok "$(verdict "$T/st.out" G1)"

# --- the kept synthetic trees through the real process ----------------------
K="$T/keep"
run "$T/k1.out" "$EC" check --build "$K/good" --image "$K/good/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: the vendor-free tree exits 0, GREEN"      "0 1" \
   "$rc $(has "$T/k1.out" 'GREEN:')"
run "$T/k2.out" "$EC" check --build "$K/eleventh" --image "$K/eleventh/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: an eleventh vendor name in the seam exits 1" 1 "$rc"
run "$T/k3.out" "$EC" check --build "$K/second" --image "$K/second/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: a seam name defined twice exits 1"        1 "$rc"
run "$T/k4.out" "$EC" check --build "$K/mips16" --image "$K/mips16/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: a surviving MIPS16 vendor function exits 1, named" "1 1" \
   "$rc $(has "$T/k4.out" 'swNic_receive [MIPS16]')"
run "$T/k7.out" "$EC" check --build "$K/newobj" --image "$K/newobj/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: a new in-scope leaf alone exits 1, by the object census" "1 1" \
   "$rc $(grep -qxF 'RED: 1 in-scope leaves are linked' "$T/k7.out" && echo 1 || echo 0)"
cp -a "$K/good" "$T/nomap"
rm "$T/nomap/System.map"
run "$T/k8.out" "$EC" check --build "$T/nomap" --image "$T/nomap/flat" \
    --seam "$SEAM" --fixture "$K/ref.fixture"
ck "process: check without System.map exits 2, REFUSED" "2 1" \
   "$rc $(has "$T/k8.out" 'REFUSED: no System.map')"
grep '^#' "$K/ref.fixture" | sed 's/^# population [0-9]*/# population 0/' \
    > "$T/empty.fx"
run "$T/k5.out" "$EC" check --build "$K/good" --image "$K/good/flat" \
    --seam "$SEAM" --fixture "$T/empty.fx"
ck "process: an empty population exits 2, REFUSED"     "2 1" \
   "$rc $(has "$T/k5.out" 'empty population')"
run "$T/k6.out" "$EC" population --build "$K/ref" --out "$T/again.fx"
# The kept tree was built under another path, which the `# build` line names.
grep -v '^# build ' "$T/again.fx" > "$T/again.cmp" || true
grep -v '^# build ' "$K/ref.fixture" > "$T/kept.cmp" || true
ck "process: population exits 0 and is deterministic"  "0 1" \
   "$rc $(cmp -s "$T/again.cmp" "$T/kept.cmp" && [ -s "$T/kept.cmp" ] && echo 1 || echo 0)"

# --- mutations of the tool: each must turn its named case red ---------------
# Every anchor must occur exactly once; M0 runs the unmutated copy through the
# same path, so a broken path cannot pass as a killed mutant.
mkdir -p "$T/mut"
"$PY" - "$EC" "$T/mut" > "$T/mut/anchors" <<'PYEOF'
import os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
MUT = [
    ("M0", None, None),
    ("X1", '        if rest[0].startswith("["):\n',
     '        if rest[0].startswith("["):\n            continue\n'
     '        if rest[0].startswith("["):\n'),
    ("X2", "    return diff\n", "    return []\n"),
    ("X3", "    return p.startswith(SCOPE_DIR) or p == SCOPE_OBJ\n",
     "    return p.startswith(SCOPE_DIR)\n"),
    ("X4", "           if seam_obj is None or defs.get(n, set()) != {seam_obj}]\n",
     "           if seam_obj is None]\n"),
    ("X5", "    if derived != given:\n", "    if False:\n"),
    ("X6", '        red.append("%d vendor-unique /proc name(s) in the image" % len(on))\n',
     "        pass\n"),
    ("X7", '    fo = [s for s in vend if s.type in ("FUNC", "OBJECT")]\n',
     '    fo = [s for s in vend if s.type in ("FUNC",)]\n'),
    ("X8", '        red.append("%d in-scope leaves are linked" % len(scope))\n',
     "        pass\n"),
    ("X9", "    refuse_on(diff, \"this build's leaves\")\n", "    pass\n"),
    ("X10", '    refuse_on(vdiff, "vmlinux")\n', "    pass\n"),
    ("X11", "    if not any(not in_scope(m) for m in hit.get(SANITY, [])):\n",
     "    if False:\n"),
    ("X12", "    if hit.get(ABSENT):\n", "    if False:\n"),
    ("X13", "    if not unique:\n", "    if False:\n"),
    ("X14", "    if len(seams) > 1:\n", "    if False:\n"),
    ("X15", "    if lost:\n", "    if False:\n"),
    ("X16", "            if head != EMPTY_AR:\n", "            if False:\n"),
    ("X17", '        raise Refusal("no System.map in %s -- check reads the symbol table "\n'
            '                      "a second time through it, as population does" % tree)\n',
     "        smap = set()\n"),
]
for label, old, new in MUT:
    d = os.path.join(dst, label)
    os.makedirs(d)
    shutil.copy(os.path.join(os.path.dirname(src), "imgprocs.py"), d)
    n = 1 if old is None else text.count(old)
    body = text if old is None else text.replace(old, new)
    open(os.path.join(d, "ethcensus.py"), "w").write(body)
    print(label, n)
PYEOF
while read -r label n; do
    ck "mutation $label: its anchor occurs exactly once"   1 "$n"
done < "$T/mut/anchors"
mut () { # label case-it-must-kill
    run "$T/mut/$1.out" "$T/mut/$1/ethcensus.py" self-test
    ck "mutation $1 turns $2 red (self-test exit non-zero)" "FAIL 1" \
       "$(verdict "$T/mut/$1.out" "$2") $([ "$rc" != 0 ] && echo 1 || echo 0)"
}
run "$T/mut/M0.out" "$T/mut/M0/ethcensus.py" self-test
ck "mutation M0 (unmutated, same path) passes"         0 "$rc"
mut X1 P1      # st_other lines skipped: the segment-113 drop
mut X2 P9      # the two parsers never disagree
mut X3 M6      # rtk_vlan.o out of the scope
mut X4 M2      # a seam name may have a second definer
mut X5 R1      # any image accepted
mut X6 M7      # a surviving /proc literal is not red
mut X7 T1      # OBJECT names out of the population
mut X8 M8      # the object census never adds a RED
mut X9 M5c     # check's nm cross-check of the leaves gone
mut X10 M5v    # check's nm cross-check of vmlinux gone
mut X11 T6     # population's SANITY control gone
mut X12 T7     # population's ABSENT control gone
mut X13 T8     # a reference with no vendor-unique /proc name accepted
mut X14 R9     # a basename --seam matching two leaves takes the first
mut X15 M9     # a seam name missing from vmlinux is not red
mut X16 R10    # a built-in.o with no .cmd walked as a leaf
mut X17 R8     # check runs without System.map, on one reading

# Without the host binutils the self-test must REFUSE, never pass or skip.
mkdir -p "$T/mut/NB"
cp "$HERE/imgprocs.py" "$T/mut/NB/"
sed 's|^BIN = "/usr/bin"$|BIN = "/nonexistent-bin"|' "$EC" \
    > "$T/mut/NB/ethcensus.py"
run "$T/mut/NB.out" "$T/mut/NB/ethcensus.py" self-test
ck "without the host binutils the self-test is REFUSED" "2 1" \
   "$rc $(has "$T/mut/NB.out" 'missing host binutils')"

# --- the reference build: desk only -----------------------------------------
if [ ! -f "$REF/.vmlinux.cmd" ] || [ ! -f "$REF/vmlinux" ]; then
    printf '  skip   %-52s %s\n' "reference build" \
        "no r6b6q2 build tree at $REF (covers 8)"
else
    run "$T/d1.out" "$EC" population --build "$REF" --out "$T/ref.fx"
    ck "reference: population exits 0"                  0 "$rc"
    ck "reference: it reproduces the committed fixture byte for byte" 1 \
       "$(cmp -s "$T/ref.fx" "$FX" && echo 1 || echo 0)"
    /usr/bin/mips-linux-gnu-objcopy -O binary "$REF/vmlinux" "$T/ref.flat"
    run "$T/d2.out" "$EC" check --build "$REF" --image "$T/ref.flat" \
        --seam "$SEAM"
    ck "reference control: check exits 1 (RED)"         1 "$rc"
    ck "reference control: object census 22"            1 \
       "$(has "$T/d2.out" '1 object  22 of 627 leaves')"
    ck "reference control: symbol census 898 of 899, System.map agrees" 1 \
       "$(has "$T/d2.out" '2 symbol  898 of 899 population names in vmlinux (898 by System.map)')"
    ck "reference control: string census 6 of 6"        1 \
       "$(has "$T/d2.out" '3 string  6 of 6 vendor-unique')"
    # The staged tree carries the vendor DROP's own flat kernel under the
    # name a flat image goes by; a census of it would read the vendor's
    # image as this build's.
    run "$T/d3.out" "$EC" check --build "$REF" \
        --image "$REF/rtkload/vmlinux_img" --seam "$SEAM"
    ck "reference: the drop's rtkload/vmlinux_img is REFUSED" "2 1" \
       "$rc $(has "$T/d3.out" "not this build's flat image")"
    # The segment-113 parser on the real tree: nm must catch every line it
    # drops, and the refusal must name a MIPS16 and the hex-sized name.
    # 43 = 39 `[MIPS16]` symbol lines + 4 hex sizes over the 627 leaves,
    # counted 2026-09-27 by a split-based scan that shares no code with this
    # tool; 14 in scope = 907 - 893, this tool's names against the design's.
    sed 's/        r = PARSE_READELF(run(/        r = old_parse(run(/' \
        "$T/mut/M0/ethcensus.py" > "$T/mut/M0/old.py"
    run "$T/d4.out" "$T/mut/M0/old.py" population --build "$REF" \
        --out "$T/old.fx"
    ck "reference: the segment-113 parser is REFUSED by nm, naming what it drops" \
       "2 1 1 1" "$rc $(has "$T/d4.out" 'swNic_receive') $(has "$T/d4.out" 'eth_skb_buf') $(has "$T/d4.out" 'disagree on 43 symbol(s) of the reference'"'"'s leaves, 14 of them in scope')"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"
    exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
