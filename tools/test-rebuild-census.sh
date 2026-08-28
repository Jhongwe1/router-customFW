#!/usr/bin/env bash
# Controls for tools/rebuild-census.py.
#
# What this tool claims is narrow and every claim is a case here:
#
#   * it hands opcount and hazlint the SAME window binsim scores, so a
#     disagreement between channels is a disagreement about the file and not
#     about where the code is                                      -- A1, A2
#   * it applies notes/which-drop.md section 6's rule mechanically, and the
#     container test comes FIRST -- a perfect score with a changed container is
#     VOID, not pass                                               -- A3, M3, M4
#   * it says whether anything in the run could have made channel 3's zero
#     fire, because a zero from a tool nothing exercised is not a reading
#                                                                  -- A6, A7
#   * it refuses rather than substituting a comparand               -- A8
#
# M* are MUTATIONS: the tool's source with one line changed, run through its own
# controls. A mutation that the controls do not catch is a control that is not
# guarding what it says it guards -- which is the defect an adversarial review
# found in tools/binsim.py's D5 and the reason every case below has one.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$HERE/rebuild-census.py"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail=0; pass=0; skipped=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-46s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-46s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
sk () { printf '  skip   %-46s %s\n' "$1" "$2"; skipped=$((skipped+1)); }

PY=python3
command -v "$PY" >/dev/null 2>&1 || { echo "no python3"; exit 2; }

# ---------------------------------------------------------------- A: the tool
"$PY" "$TOOL" --self-test > "$T/self.out" 2>&1
ck "A0  --self-test exits 0" 0 "$?"
ck "A0b every control line says ok" 0 "$(grep -c '^  FAIL' "$T/self.out")"
ck "A0c the control count is the one this suite knows" 8 \
   "$(sed -n 's/^  \([0-9]*\) control(s).*/\1/p' "$T/self.out")"

for c in W1 W2 V1 V2 V3 C1 C2 S1; do
    ck "A1  control $c ran and passed" 1 "$(grep -c "^  ok     $c " "$T/self.out")"
done

ck "A2  the window line reports a word count" 1 \
   "$(grep -c 'W1 .*words' "$T/self.out")"

ck "A3  S1 asserts the window did not move" 1 \
   "$(grep -c 'S1 .*window identical' "$T/self.out")"

"$PY" "$TOOL" --badflag > "$T/usage.out" 2>&1
ck "A4  an unknown flag is a usage error" 3 "$?"

"$PY" "$TOOL" > "$T/noargs.out" 2>&1
ck "A5  no comparand is a usage error" 3 "$?"

"$PY" "$TOOL" --against "$T/does-not-exist" "$TOOL" > "$T/missing.out" 2>&1
ck "A6  a missing comparand is refused, not substituted" 3 "$?"
ck "A6b and it says so in those words" 1 \
   "$(grep -c 'will not substitute another' "$T/missing.out")"

# ------------------------------------------------------- A7/A8: real material
FW="${FWRE_WORK:-/home/key/fwre-work}"
REF="$FW/extracted/unit-2018/squashfs-root/bin/boa"
REB="$FW/rebuild/r2ab/out/bin"
if [ -f "$REF" ] && [ -d "$REB" ]; then
    "$PY" "$TOOL" --against "$REF" "$REB"/boa.rtl819x__t136-4181 \
        > "$T/real1.out" 2>&1
    ck "A7  a 1.3.6 rebuild is VOID on the container" 1 \
       "$(grep -c 'VOID   phnum,needed' "$T/real1.out")"
    ck "A7b with no violation anywhere, the zero is called NOT LOOKED FOR" 1 \
       "$(grep -c 'NOT LOOKED FOR' "$T/real1.out")"

    "$PY" "$TOOL" --against "$REF" "$REB"/boa.rtl819x__t155-5281 \
        > "$T/real2.out" 2>&1
    ck "A8  a -march=5281 rebuild supplies the positive control" 1 \
       "$(grep -c 'DID report violations' "$T/real2.out")"
    ck "A8b the comparand scored against itself is 1.0000 and passes" 1 \
       "$(grep -cE '^boa +1\.0000 +1\.0000 +1\.0000 +pass' "$T/real2.out")"
else
    sk "A7 real-material cases" "no \$FWRE_WORK corpus (covers 4)"
fi

# ------------------------------------------------------------- M: mutations
mut () { # label  sed-expression  expect-failed-control
    sed "$2" "$TOOL" > "$T/mut.py"
    if cmp -s "$TOOL" "$T/mut.py"; then
        printf '  FAIL   %-46s mutation changed nothing\n' "$1"; fail=$((fail+1)); return
    fi
    # PYTHONPATH, because the mutant lives outside tools/ and its own
    # `sys.path.insert(0, HERE)` then points at the temp directory. Without it
    # every mutant dies on `import binsim` with rc=1 and this harness would
    # score that as "the mutation was caught" -- a mutation test that passes
    # because nothing ran.
    PYTHONPATH="$HERE" "$PY" "$T/mut.py" --self-test > "$T/mut.out" 2>&1
    rc=$?
    got="$(grep -c "^  FAIL   $3" "$T/mut.out")"
    if [ "$rc" = "2" ] && [ "$got" = "1" ]; then
        printf '  ok     %-46s caught by %s\n' "$1" "$3"; pass=$((pass+1))
    else
        printf '  FAIL   %-46s rc=%s, %s flagged=%s\n' "$1" "$rc" "$3" "$got"
        fail=$((fail+1))
    fi
}

mut "M1  window handed off as the whole file"   's/return sample.off, sample.off + sample.size, sample.vaddr - sample.off/return 0, len(sample.blob), sample.vaddr - sample.off/' "W1"
mut "M2  --base left at zero"                   's/return sample.off, sample.off + sample.size, sample.vaddr - sample.off/return sample.off, sample.off + sample.size, 0/' "W2"
mut "M3  container test moved after the score"  's/^    if container_differs:/    if False and container_differs:/' "V1"
mut "M4  FLOOR treated as exclusive"            's/    if containment <= floor:/    if containment < floor:/' "V1"
mut "M5  the manifest cell check re-pointed"    's/WANT_FLOOR = ("boa", "unit-2018", "busybox", "unit-2018")/WANT_FLOOR = ("boa", "unit-2018", "pppd", "v3.4.0")/' "V3"

# M6 is the one that matters most: a mutant that ignores the container argument
# entirely still gets every SCORE right, and only V2 can see it.
mut "M6  verdict ignores its container argument" 's/^def verdict(containment, container_differs, base=BASE, floor=FLOOR):/def verdict(containment, container_differs=False, base=BASE, floor=FLOOR):\n    container_differs = False/' "V2"

printf '\n  %d passed, %d failed, %d skipped\n' "$pass" "$fail" "$skipped"
[ "$fail" -eq 0 ]
