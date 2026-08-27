#!/usr/bin/env bash
# Controls for tools/binsim.py.
#
# binsim's own `--self-test` runs twenty-four controls and refuses to report if one
# of them fails. This suite exists because that sentence is unfalsifiable on its
# own: a control nobody has seen go red is a control nobody has shown is
# looking. So the middle of this file breaks binsim twelve different ways and
# requires a NAMED control to go red each time -- and requires a DIFFERENT named
# control to stay green, because "exit 2" only says that something failed, and a
# mutation that reddened the wrong control would look identical.
#
# `mutate` refuses when its target string does not appear exactly once, so a sed
# that quietly matched nothing cannot produce a passing case. That is the
# control on the controls, and this suite has no value without it.
#
# Sections:
#   P   binsim as shipped: the self-test, the CLI contract, the report, determinism
#   M   twelve mutations, each naming the control it must redden and one it must not
#   X   the corpus machinery end to end, on synthetic corpora built here, so the
#       manifest reader / matrix / void verdict / BASE / FLOOR all run in CI
#       rather than only on the one machine that has $FWRE_WORK. TWO of those
#       corpora exist to put the floor verdict on either side of CROSS: until
#       2026-08-27 the REFUTED branch fired only on the real six trees, and the
#       day R2a/b/d-1 moved @floor above CROSS it would have had no test at all
#   R   the real six trees. Skipped where they are absent, which is everywhere
#       but the bench machine: the bytes are someone else's property and one of
#       the six is this unit's own flash dump.
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HERE/binsim.py"
export BINSIM_DIR="$HERE"
PY="${PYTHON:-python3}"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0
ck () { # label expected actual
    if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
cknot () { # label notexpected actual
    if [ "$2" != "$3" ]; then printf '  ok     %-52s %s (not %s)\n' "$1" "$3" "$2"; pass=$((pass+1))
    else printf '  FAIL   %-52s got %s, which it must not\n' "$1" "$3"; fail=$((fail+1)); fi
}
skip () { printf '  skip   %-52s %s\n' "$1" "$2"; }

rc () { # run, echo exit status, keep stdout in $T/out
    set +o errexit
    "$@" > "$T/out" 2>"$T/err"
    local s=$?
    set -o errexit
    echo "$s"
}

# ---------------------------------------------------------------------------
echo "=== P1: binsim as shipped ==="

s=$(rc "$PY" "$BIN" --self-test)
ck "self-test exit" 0 "$s"
ck "self-test says nothing failed" 1 "$(grep -c '^  24 control(s), 0 failed$' "$T/out")"
ck "twenty-four control lines, no more no less" 24 "$(grep -c '^  \(ok\|FAIL\) ' "$T/out")"
# A control that vanished would leave the count at 24 only if another appeared,
# so the ids are pinned too. This is what caught nothing yet and is here because
# ci-census exists for exactly this failure on the suite one level up.
ck "every control id present" "A1 A2 A3 A4 B1 B2 B3 C1 C2 C3 C4 C5 C6 C7 C8 C9 C10 C11 C12 D1 D2 D3 D4 D5" \
   "$(grep -o '^  \(ok\|FAIL\)     [A-D][0-9]*b\?' "$T/out" | awk '{print $2}' | tr '\n' ' ' | sed 's/ $//')"

echo
echo "=== P2: the CLI contract, including the exit codes a gate would read ==="
ck "--help exits 0"                0 "$(rc "$PY" "$BIN" --help)"
ck "unknown flag exits 3"          3 "$(rc "$PY" "$BIN" --nonsense)"
ck "one file exits 3"              3 "$(rc "$PY" "$BIN" "$BIN")"
ck "-k 0 exits 3"                  3 "$(rc "$PY" "$BIN" -k 0 --self-test)"
# Long enough to get past the length check, so the refusal that fires is the
# magic one. The first draft of this case used an 18-byte file and asserted a
# message the tool had no reason to print.
head -c 512 /dev/zero | tr '\0' 'x' > "$T/plain"
ck "a non-ELF pair exits 2"        2 "$(rc "$PY" "$BIN" "$T/plain" "$T/plain")"
ck "refusal names the reason"      1 "$(grep -c 'no ELF magic' "$T/err")"

echo
echo "=== P3: the report, re-read from what it printed ==="
"$PY" - "$T" <<'PY'
import sys, os
sys.path.insert(0, os.environ['BINSIM_DIR'])
import binsim as B
T = sys.argv[1]
w = B._plausible_code(6000, seed=3)
open(os.path.join(T, 'a.elf'), 'wb').write(B.synth_elf(w))
open(os.path.join(T, 'b.elf'), 'wb').write(B.synth_elf(w[:3000] + B._plausible_code(3000, seed=4)))
PY
s=$(rc "$PY" "$BIN" "$T/a.elf" "$T/a.elf" --sweep)
ck "a file against itself exits 0" 0 "$s"
ck "... and reports 1.0000 on both measures" 1 \
   "$(grep -c '^  code           1.0000     1.0000' "$T/out")"
ck "... and 0 fingerprint fields differ" 1 "$(grep -c '^  0 of 10 fingerprint field(s) differ$' "$T/out")"
ck "... and the k sweep printed every k" 16 "$(sed -n '/k sweep/,$p' "$T/out" | grep -c '^  *[0-9]* *[01]\.[0-9]')"
s=$(rc "$PY" "$BIN" "$T/a.elf" "$T/b.elf")
ck "a half-shared pair exits 0" 0 "$s"
half=$(awk '/^  code /{print $2}' "$T/out")
cknot "... and does not score 1.0000" "1.0000" "$half"
cknot "... and does not score 0.0000" "0.0000" "$half"

echo
echo "=== P3b: --fingerprint, which had no control at all until it was read ==="
# It shipped printing `squashfs-root` as the label for every row of the corpus,
# and an unpadded table nobody could line up. A mode with no case is a mode
# nobody has looked at.
s=$(rc "$PY" "$BIN" --fingerprint "$T/a.elf" "$T/a.elf")
ck "--fingerprint on two copies exits 0" 0 "$s"
ck "... and reports 0 fields differing" 1 \
   "$(grep -c '^  0 of 10 field(s) differ across 2 file(s)' "$T/out")"
ck "... and marks nothing with a star" 0 "$(grep -c '^\* ' "$T/out")"
"$PY" - "$T" <<'PY'
import sys, os
sys.path.insert(0, os.environ['BINSIM_DIR'])
import binsim as B
T = sys.argv[1]
w = B._plausible_code(6000, seed=3)
d = os.path.join(T, 'root', 'tree-x', 'squashfs-root', 'bin')
os.makedirs(d, exist_ok=True)
with open(os.path.join(d, 'boa'), 'wb') as fh:
    fh.write(B.synth_elf(w, flags=0x1005, nphdr_extra=2))
PY
s=$(rc "$PY" "$BIN" --fingerprint "$T/a.elf" "$T/root/tree-x/squashfs-root/bin/boa")
ck "--fingerprint on two different builds exits 0" 0 "$s"
ck "... and e_flags is one of the fields marked differing" 1 \
   "$(grep -c '^\* e_flags' "$T/out")"
ck "... and the corpus label is the TREE, not squashfs-root" 1 \
   "$(grep -c 'tree-x/boa' "$T/out")"
cknot "... and squashfs-root is not used as a label" "1" \
   "$(grep -c '  squashfs-root ' "$T/out" || true)"

echo
echo "=== P4: determinism -- the same input twice must print the same bytes ==="
# A set iteration order or a randomised hash leaking into a number would show
# up here and nowhere else, and it would show up as a matrix that moved between
# two runs of the same build.
"$PY" "$BIN" --self-test > "$T/d1" 2>&1
"$PY" "$BIN" --self-test > "$T/d2" 2>&1
if cmp -s "$T/d1" "$T/d2"; then ck "two self-test runs are byte-identical" 0 0
else ck "two self-test runs are byte-identical" 0 1; fi
"$PY" "$BIN" "$T/a.elf" "$T/b.elf" --sweep > "$T/d3" 2>&1
"$PY" "$BIN" "$T/a.elf" "$T/b.elf" --sweep > "$T/d4" 2>&1
if cmp -s "$T/d3" "$T/d4"; then ck "two pair runs are byte-identical" 0 0
else ck "two pair runs are byte-identical" 0 1; fi

# ---------------------------------------------------------------------------
mutate () { # dst old new
    MUT_OLD="$2" MUT_NEW="$3" "$PY" - "$BIN" "$1" <<'PY'
import os, sys
src, dst = sys.argv[1], sys.argv[2]
old, new = os.environ['MUT_OLD'], os.environ['MUT_NEW']
with open(src, encoding='utf-8') as fh:
    s = fh.read()
n = s.count(old)
if n != 1:
    sys.stderr.write('mutation target appears %d times, not once\n' % n)
    sys.exit(9)
t = s.replace(old, new)
tmp = dst + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(t)
os.replace(tmp, dst)
PY
}

mcase () { # label old new must_redden must_stay_green
    local label="$1" old="$2" new="$3" red="$4" green="$5"
    local m="$T/mut.py"
    rm -f "$m"
    if ! mutate "$m" "$old" "$new"; then
        printf '  FAIL   %-52s mutation did not apply\n' "$label"; fail=$((fail+1))
        printf '  FAIL   %-52s (skipped, no mutant)\n' "$label (specificity)"; fail=$((fail+1))
        return
    fi
    local s; s=$(rc "$PY" "$m" --self-test)
    if [ "$s" = 2 ] && grep -q "^  FAIL   $red" "$T/out"; then
        printf '  ok     %-52s exit 2, %s red\n' "$label" "$red"; pass=$((pass+1))
    else
        printf '  FAIL   %-52s exit %s, %s not red\n' "$label" "$s" "$red"; fail=$((fail+1))
    fi
    if grep -q "^  ok     $green" "$T/out"; then
        printf '  ok     %-52s %s stayed green\n' "$label (specificity)" "$green"; pass=$((pass+1))
    else
        printf '  FAIL   %-52s %s did not stay green\n' "$label (specificity)" "$green"; fail=$((fail+1))
    fi
}

echo
echo "=== M: twelve mutations, each naming the control it must redden ==="

mcase "M1  containment over max instead of min" \
      "    return (inter / min(len(a), len(b))," \
      "    return (inter / max(len(a), len(b))," \
      "C6" "C1"

mcase "M2  every k-gram becomes a 1-gram" \
      "        for j in range(i, i + k):" \
      "        for j in range(i, i + 1):" \
      "C5" "C1"

# C6 is NOT the specificity partner here: sorting the window also flattens the
# truncation control, so it reddens too. A1 does not touch kgrams at all.
mcase "M3  the k-gram is order-blind" \
      "    add = out.add" \
      "    add = out.add; toks = sorted(toks)" \
      "C5" "A1"

mcase "M4  nop collapses into sll" \
      "        return TOK_NOP" \
      "        return TOK_SPECIAL" \
      "B1" "A1"

mcase "M5  a COPz rs field is read as a register" \
      "        fsel = rs if rs < 8 else (7 if rs == 8 else 8)" \
      "        fsel = rs & 7" \
      "B1" "B3"

mcase "M6  the code window starts at file offset 0" \
      "        off = self.v2o(init)" \
      "        off = 0" \
      "A1" "B1"

mcase "M7  DT_FINI below DT_INIT is accepted" \
      "        if fini <= init:" \
      "        if False:" \
      "A2" "A1"

mcase "M8  the k-gram hash prime changes" \
      "FNV_PRIME = 0x100000001B3" \
      "FNV_PRIME = 0x100000001B5" \
      "B3" "B1"

# Asymmetric jaccard reddens C6 first -- it asserts a jaccard value -- so the
# mutation that isolates C8 is an asymmetric CONTAINMENT, which leaves C6's
# assertion untouched because C6's smaller set is already the numerator's.
mcase "M9  containment becomes asymmetric" \
      "    return (inter / min(len(a), len(b))," \
      "    return (inter / len(a)," \
      "C8" "C6"

mcase "M10 the strings channel takes runs of one byte" \
      "            if len(run) >= minlen:" \
      "            if len(run) >= 1:" \
      "C9" "C1"

# M11 exists because of what R2a/b/d-1 did on 2026-08-27: it moved @floor above
# CROSS, so the real corpus stopped exercising the REFUTED branch. A verdict
# that no longer fires anywhere is not a verdict, which is the same rule acltd
# earns its place in the corpus under. D3 is the specificity partner because it
# is the OTHER verdict in the same function group and this mutation must not
# touch it.
mcase "M11 the floor verdict is inverted" \
      "    return floor_v < cross_v" \
      "    return floor_v > cross_v" \
      "D5" "D3"

# M12 is the mutant an adversarial reviewer BUILT rather than reasoned about,
# and it survived the first version of D5: a verdict that ignores its second
# argument and hard-codes the corpus's CROSS. Every control and all 69 runner
# cases stayed green under it, because D5 passed the same 0.1581 three times.
# D5 varies cross_v now, so this reddens.
mcase "M12 the floor verdict ignores CROSS and pins it" \
      "    return floor_v < cross_v" \
      "    return floor_v < 0.1581" \
      "D5" "D3"

# ---------------------------------------------------------------------------
echo
echo "=== X: the corpus machinery, on a corpus built here ==="
# Without this the manifest reader, the matrices, the void verdict and the
# BASE/FLOOR selection would only ever run on the one machine that holds the six
# vendor trees -- which is the shape of untested code this project keeps finding.
"$PY" - "$T" <<'PY'
import hashlib, os, sys
sys.path.insert(0, os.environ['BINSIM_DIR'])
import binsim as B

T = sys.argv[1]


def write(root, tree, prog, words):
    d = os.path.join(root, tree, 'squashfs-root', 'bin')
    os.makedirs(d, exist_ok=True)
    blob = B.synth_elf(words)
    p = os.path.join(d, prog)
    with open(p + '.tmp', 'wb') as fh:
        fh.write(blob)
    os.replace(p + '.tmp', p)
    return len(blob), hashlib.sha256(blob).hexdigest()


def manifest(path, rows, base, floor):
    out = ['@base\t' + '\t'.join(base), '@floor\t' + '\t'.join(floor)]
    for r in rows:
        out.append('\t'.join(str(x) for x in r))
    text = '\n'.join(out) + '\n'
    with open(path + '.tmp', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    os.replace(path + '.tmp', path)


# progA and progB are both subjects and share almost no code, so CROSS is near
# zero and FLOOR sits ABOVE it -- the branch the real corpus does NOT take,
# which is exactly why it needs a fixture. progC is the identity anchor, and its
# three copies differ only in a tag OUTSIDE the code window, which is the shape
# of the eight-byte busybox pair and the only thing that can exercise E2b.
a = B._plausible_code(9000, seed=21)
A = {'t1': a,
     't2': a[:8600] + B._plausible_code(400, seed=22),
     't3': a[:4500] + B._plausible_code(4500, seed=23)}
b = B._plausible_code(9000, seed=41)
Bp = {'t1': b,
      't2': b[:8600] + B._plausible_code(400, seed=42),
      't3': b[:4500] + B._plausible_code(4500, seed=43)}
c = B._plausible_code(2000, seed=61)

root = os.path.join(T, 'corpus')
rows = []
for prog, trees in (('progA', A), ('progB', Bp)):
    for i, t in enumerate(('t1', 't2', 't3')):
        n, h = write(root, t, prog, trees[t])
        rows.append((t, '2020-01-0%d' % (i + 1), prog, 'bin/' + prog, n, h, 'subject'))
for i, t in enumerate(('t1', 't2', 't3')):
    d = os.path.join(root, t, 'squashfs-root', 'bin')
    os.makedirs(d, exist_ok=True)
    blob = B.synth_elf(c, tag=b'tree-is-%s\x00' % t.encode())
    p = os.path.join(d, 'progC')
    with open(p + '.tmp', 'wb') as fh:
        fh.write(blob)
    os.replace(p + '.tmp', p)
    rows.append((t, '2020-01-0%d' % (i + 1), 'progC', 'bin/progC',
                 len(blob), hashlib.sha256(blob).hexdigest(), 'identity'))
manifest(os.path.join(T, 'ok.tsv'), rows,
         ('progA', 't1', 't2'), ('progA', 't1', 't3'))

bad = [list(r) for r in rows]
bad[0][5] = '0' * 64
manifest(os.path.join(T, 'badsha.tsv'), bad, ('progA', 't1', 't2'), ('progA', 't1', 't3'))
manifest(os.path.join(T, 'badcell.tsv'), rows,
         ('progA', 't1', 'nosuchtree'), ('progA', 't1', 't3'))

# three identical trees: the void verdict must fire end to end
root2 = os.path.join(T, 'void')
rows2 = []
for i, t in enumerate(('t1', 't2', 't3')):
    n, h = write(root2, t, 'progA', a)
    rows2.append((t, '2020-01-0%d' % (i + 1), 'progA', 'bin/progA', n, h, 'subject'))
manifest(os.path.join(T, 'void.tsv'), rows2, ('progA', 't1', 't2'), ('progA', 't1', 't3'))

# A corpus whose named FLOOR sits BELOW CROSS, so the REFUTED branch fires here
# rather than only on the six vendor trees. Until R2a/b/d-1 moved the real
# @floor above CROSS on 2026-08-27, those trees were the only thing that took
# this branch -- and the day they stopped, it would have had no test anywhere.
# progD shares a 3,000-word prefix with progA, which is what lifts CROSS;
# progA's t3 shares nothing with t1, which is what drops FLOOR. progD's own
# three cells are deliberately NOT all alike, or the void verdict would fire on
# progD and set the same exit status for a different reason.
root3 = os.path.join(T, 'refuted')
d1 = B._plausible_code(6000, seed=90)
D = {'t1': a[:3000] + d1,
     't2': a[:3000] + d1[:5700] + B._plausible_code(300, seed=91),
     't3': a[:3000] + B._plausible_code(6000, seed=93)}
A3 = {'t1': a,
      't2': a[:8600] + B._plausible_code(400, seed=22),
      't3': B._plausible_code(9000, seed=77)}
rows3 = []
for prog, trees in (('progA', A3), ('progD', D)):
    for i, t in enumerate(('t1', 't2', 't3')):
        n, h = write(root3, t, prog, trees[t])
        rows3.append((t, '2020-01-0%d' % (i + 1), prog, 'bin/' + prog, n, h, 'subject'))
# progC again, for the same reason it is in ok.tsv: E2 needs at least one pair
# with byte-identical code windows and E2b needs those two files to differ
# outside the window, or both go red on a corpus that is otherwise fine. The
# first draft of this fixture omitted it and E2 reddened -- correctly.
for i, t in enumerate(('t1', 't2', 't3')):
    d = os.path.join(root3, t, 'squashfs-root', 'bin')
    os.makedirs(d, exist_ok=True)
    blob = B.synth_elf(c, tag=b'tree-is-%s\x00' % t.encode())
    p = os.path.join(d, 'progC')
    with open(p + '.tmp', 'wb') as fh:
        fh.write(blob)
    os.replace(p + '.tmp', p)
    rows3.append((t, '2020-01-0%d' % (i + 1), 'progC', 'bin/progC',
                  len(blob), hashlib.sha256(blob).hexdigest(), 'identity'))
manifest(os.path.join(T, 'refuted.tsv'), rows3,
         ('progA', 't1', 't2'), ('progA', 't1', 't3'))
PY

s=$(rc "$PY" "$BIN" --corpus "$T/ok.tsv" --root "$T/corpus")
ck "a synthetic corpus with FLOOR above CROSS exits 0" 0 "$s"
ck "... and says the metric discriminates" 1 "$(grep -c 'the metric discriminates on progA' "$T/out")"
ck "... and FLOOR is reported above CROSS" 1 "$(grep -c 'FLOOR is above CROSS' "$T/out")"
ck "... and BASE is above FLOOR" 1 \
   "$("$PY" -c 'import re,sys
t=open(sys.argv[1],encoding="utf-8").read()
b=float(re.search(r"BASE.*= ([0-9.]+)",t).group(1))
f=float(re.search(r"FLOOR.*= ([0-9.]+)",t).group(1))
print(1 if b>f else 0)' "$T/out")"
ck "a manifest sha256 that does not match exits 2" 2 \
   "$(rc "$PY" "$BIN" --corpus "$T/badsha.tsv" --root "$T/corpus")"
ck "... and the refusal names sha256"     1 "$(grep -c 'manifest sha256' "$T/err")"
ck "a @base naming a missing tree exits 2" 2 \
   "$(rc "$PY" "$BIN" --corpus "$T/badcell.tsv" --root "$T/corpus")"
# A corpus that mixes ISAs. The parser already refuses a little-endian file, so
# the case that matters is one that PARSES and is still the wrong part: a
# big-endian MIPS32r2 sample among MIPS-I ones. Without E0 it would score, and
# it would move FLOOR.
"$PY" - "$T" <<'PY'
import hashlib, os, sys
sys.path.insert(0, os.environ['BINSIM_DIR'])
import binsim as B
T = sys.argv[1]
root = os.path.join(T, 'mixed')
rows = ['@base\tprogA\tt1\tt2', '@floor\tprogA\tt1\tt3']
a = B._plausible_code(9000, seed=21)
for i, t in enumerate(('t1', 't2', 't3')):
    d = os.path.join(root, t, 'squashfs-root', 'bin')
    os.makedirs(d, exist_ok=True)
    flags = 0x70001007 if t == 't3' else 0x1007      # t3 is MIPS32r2
    blob = B.synth_elf(a if t == 't1' else a[:4500] + B._plausible_code(4500, seed=30 + i),
                       flags=flags)
    p = os.path.join(d, 'progA')
    with open(p + '.tmp', 'wb') as fh:
        fh.write(blob)
    os.replace(p + '.tmp', p)
    rows.append('\t'.join((t, '2020-01-0%d' % (i + 1), 'progA', 'bin/progA',
                           str(len(blob)), hashlib.sha256(blob).hexdigest(), 'subject')))
text = '\n'.join(rows) + '\n'
with open(os.path.join(T, 'mixed.tsv.tmp'), 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(text)
os.replace(os.path.join(T, 'mixed.tsv.tmp'), os.path.join(T, 'mixed.tsv'))
PY
ck "a corpus mixing MIPS-I and MIPS32r2 exits 2" 2 \
   "$(rc "$PY" "$BIN" --corpus "$T/mixed.tsv" --root "$T/mixed")"
ck "... and E0 is the control that reddened" 1 \
   "$(grep -c '^  FAIL   E0  every sample in the corpus is the same ISA' "$T/out")"

# A corpus file truncated in its BODY -- the commonest way a manifest hash
# fails. It used to die inside tokenize() with an uncaught struct.error, which
# main's `except Refused` does not catch, so it exited 1 -- the code the
# docstring assigns to "reported, but a result is void". A crashed parse and a
# legitimate void verdict were the same exit status.
cp "$T/corpus/t1/squashfs-root/bin/progA" "$T/corpus/t1/squashfs-root/bin/progA.keep"
head -c 4096 "$T/corpus/t1/squashfs-root/bin/progA.keep" > "$T/corpus/t1/squashfs-root/bin/progA"
ck "a corpus file truncated in its body exits 2, not 1" 2 \
   "$(rc "$PY" "$BIN" --corpus "$T/ok.tsv" --root "$T/corpus")"
ck "... and the refusal is about the manifest, before any parse" 1 \
   "$(grep -c 'manifest says .* bytes, file is' "$T/err")"
mv "$T/corpus/t1/squashfs-root/bin/progA.keep" "$T/corpus/t1/squashfs-root/bin/progA"

# The committed manifest, parsed and validated with no vendor byte in sight.
# Until --check-manifest existed, tools/binsim-corpus.tsv was opened by no code
# path a runner could reach: its only reader was --corpus, which needs the six
# trees. A typo in @floor would have been found on one machine, months later.
ck "the committed manifest parses and validates" 0 \
   "$(rc "$PY" "$BIN" --check-manifest "$HERE/binsim-corpus.tsv")"
ck "... and it carries twenty-one rows" 1 "$(grep -c '21 row(s), 5 program(s)' "$T/out")"
ck "... and @base/@floor name trees it has" 1 \
   "$(grep -c 'every @base/@floor cell names a tree the manifest carries' "$T/out")"
sed 's/^@floor\tboa\tunit-2018\tbusybox\tunit-2018$/@floor\tboa\tunit-2018\tbusybox\tnosuchtree/' \
    "$HERE/binsim-corpus.tsv" > "$T/badfloor.tsv"
ck "a @floor naming a tree the manifest lacks is refused" 2 \
   "$(rc "$PY" "$BIN" --check-manifest "$T/badfloor.tsv")"
# The @floor row moved twice on 2026-08-27 -- boa/v3.4.0 to busybox/v3.4.0, then
# to the five-field cross-program form -- and the sed above had to move with it
# each time. A sed that matched nothing would leave the manifest valid and this
# case would read 0, which is why it asserts 2 rather than "not 0", and why the
# committed manifest is checked for the exact row the sed targets.
ck "... and the manifest really carries the row that sed targets" 1 \
   "$(grep -c '^@floor	boa	unit-2018	busybox	unit-2018$' "$HERE/binsim-corpus.tsv")"
# The five-field form is what let @floor name a cell no matrix holds. The
# four-field form still has to work, or every corpus written before today would
# stop parsing.
ck "... and @model is carried too" 1 \
   "$(grep -c '^@model	pppd	unit-2018	pppd	v3.4.0$' "$HERE/binsim-corpus.tsv")"
printf '@base\tprogA\tt1\tt2\n@floor\tprogA\tt1\tprogA\tt1\n' > "$T/selfcell.tsv"
ck "a @floor naming one binary against itself is refused" 2 \
   "$(rc "$PY" "$BIN" --check-manifest "$T/selfcell.tsv")"
ck "... and the refusal says so" 1 "$(grep -c 'names one binary against itself' "$T/err")"

s=$(rc "$PY" "$BIN" --corpus "$T/void.tsv" --root "$T/void")
ck "three identical trees exit 1, VOID" 1 "$s"
ck "... and the void verdict is printed" 1 "$(grep -c "^  VOID  the plan's failure condition fired" "$T/out")"

s=$(rc "$PY" "$BIN" --corpus "$T/refuted.tsv" --root "$T/refuted")
ck "a synthetic corpus with FLOOR below CROSS exits 1" 1 "$s"
ck "... and the REFUTED verdict is printed" 1 \
   "$(grep -c '^  REFUTED: FLOOR is below CROSS' "$T/out")"
# exit 1 is also what VOID returns, so without this the case above would pass
# on the wrong verdict.
ck "... and it is the floor verdict that fired, not the void one" 0 \
   "$(grep -c '^  VOID' "$T/out")"

# ---------------------------------------------------------------------------
echo
echo "=== R: the real six trees ==="
if [ ! -d "$WORK/extracted/unit-2018/squashfs-root/bin" ]; then
    skip "the six vendor trees" "\$FWRE_WORK/extracted absent -- 22 cases; the bytes are someone else's property and one of the six is this unit's own flash dump, so they cannot be committed"
else
    s=$(rc env FWRE_WORK="$WORK" "$PY" "$BIN" --corpus)
    ck "the real corpus exits 0 (FLOOR stands)" 0 "$s"
    ck "every corpus control green" 11 "$(grep -c '^  ok     E' "$T/out")"
    ck "no corpus control red"      0 "$(grep -c '^  FAIL   E' "$T/out")"
    # The real corpus is the one that can exercise all seven. A n-a line here
    # would mean a control that only ever runs on the machine that has the
    # material had quietly stopped running there too.
    ck "no corpus control not-applicable" 0 "$(grep -c '^  n-a' "$T/out")"
    ck "BASE"  "0.9818" "$(sed -n 's/^  BASE   binsim.*= \([0-9.]*\)   denominator.*$/\1/p' "$T/out")"
    ck "FLOOR" "0.1581" "$(sed -n 's/^  FLOOR  binsim.*= \([0-9.]*\)   denominator.*$/\1/p' "$T/out")"
    ck "CROSS" "0.1581" "$(sed -n 's/^  CROSS  = \([0-9.]*\) .*/\1/p' "$T/out")"
    # The floor is the CROSS cell itself. That is not a coincidence and not a
    # tautology: it is the finding. Nothing in the corpus sits above the
    # no-shared-source level and below BASE, so the tightest correct floor IS
    # that level -- see notes/which-drop.md §1.
    ck "the FLOOR cell is the cross-program one" 1 \
       "$(grep -c '^  FLOOR  binsim(boa/unit-2018, busybox/unit-2018)' "$T/out")"
    # A threshold read at one denominator and applied at another is the defect
    # that sank this step's first floor, so the two are pinned equal here.
    ck "... and BASE and FLOOR share a denominator" 1 \
       "$(grep -E '^  (BASE|FLOOR) ' "$T/out" \
          | sed -n 's/.*denominator \([0-9]*\) grams$/\1/p' | sort -u | wc -l)"
    ck "... and that denominator is this unit's boa" "28887" \
       "$(sed -n 's/^  FLOOR .*denominator \([0-9]*\) grams$/\1/p' "$T/out")"
    ck "FLOOR is reported as the CROSS cell itself" 1 \
       "$(grep -c '^  FLOOR is the CROSS cell itself' "$T/out")"
    ck "no FLOOR refutation is printed" 0 \
       "$(grep -c '^  REFUTED: FLOOR is below CROSS' "$T/out")"
    # E7: the floor is the top of a POPULATION at one denominator, not one
    # pair's number. Three programs, and the case pins the count -- a corpus
    # that lost pppd and wscd would turn E7 n-a and this would catch it.
    ck "the no-shared-source population has three members" 3 \
       "$(sed -n '/^  reference boa\/unit-2018/,/^  CROSS/p' "$T/out" | grep -c '^    vs ')"
    ck "... and busybox is its top" 1 \
       "$(grep -c '^    vs busybox    unit-2018      0.1581' "$T/out")"
    ck "... and the other two are below it" 1 \
       "$(grep -cE '^    vs (pppd|wscd) ' "$T/out" | awk '{print ($1==2)?1:0}')"
    # E8 is the precondition's whole justification: one source, two compilation
    # models, at a denominator within 1 % of the floor's own.
    ck "the model-change reading is printed" 1 \
       "$(grep -c '^    pppd unit-2018 / v3.4.0 = 0.1212' "$T/out")"
    ck "... and it is at or below the floor" 1 \
       "$(grep -c '^  That is AT OR BELOW the floor' "$T/out")"
    # The named cell has to stay the top of its population as k moves. Both
    # halves, because a sweep that said "stands" everywhere would be a sweep
    # that could not fail: k=1 is where another program overtakes it.
    ck "the named cell stays the top of its population above the pin" 10 \
       "$(sed -n '/Does the named cell stay the top/,/^  The reference is/p' "$T/out" | grep -c 'stands$')"
    ck "... and is overtaken at k=1, where the reference also flips" 1 \
       "$(sed -n '/Does the named cell stay the top/,/^  The reference is/p' "$T/out" | grep -c '^       1 .*busybox/unit-2018  pppd       REFUTED')"
    # The floor cell is only a floor because the SOURCE is held constant across
    # it: same upstream BusyBox in both trees, so the cell isolates the
    # compilation-model change. That is a premise of the choice, not a
    # consequence of it, so it is measured here rather than asserted in prose.
    ck "one BusyBox version across all six trees" 1 \
       "$(for t in v2.1.2 n300rt-2.1.6 unit-2018 n200re-3.2.0 n300rt-3.4.0 v3.4.0; do
              strings -a "$WORK/extracted/$t/squashfs-root/bin/busybox" \
                | grep -m1 -oE 'BusyBox v[0-9][0-9.]*'
          done | sort -u | wc -l)"
    ck "... and it is 1.13.4" "BusyBox v1.13.4" \
       "$(strings -a "$WORK/extracted/unit-2018/squashfs-root/bin/busybox" \
            | grep -m1 -oE 'BusyBox v[0-9][0-9.]*')"
    # boa's banner agrees across all six too, which is what makes the boa
    # version of the same cell the WRONG floor: same version, different code,
    # so the version string is not what moved -- the vendor's own source is.
    ck "one boa version across all six trees" 1 \
       "$(for t in v2.1.2 n300rt-2.1.6 unit-2018 n200re-3.2.0 n300rt-3.4.0 v3.4.0; do
              strings -a "$WORK/extracted/$t/squashfs-root/bin/boa" \
                | grep -m1 -oE 'Boa/[0-9][0-9.a-z]*'
          done | sort -u | wc -l)"
fi

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
