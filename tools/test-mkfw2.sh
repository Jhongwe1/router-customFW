#!/usr/bin/env bash
# Controls for mkfw2.py, flashguard.py and rlxsign.py -- and the mutations that
# must break them.
#
# The three tools' own `--self-test` cases live inside them and are run here as
# A1-A3.  What this file adds is everything a self-test cannot honestly do:
#
#   A4-A6  the committed fixtures.  A tool checked only against itself agrees
#          with itself; `tools/fixtures/mkfw2/dev-key.tsv` holds the derived
#          public key as a CONSTANT outside the implementation, and
#          `sample-v3.rlxu.hex` is a byte-exact container.  If the format or
#          the key derivation drifts, these are what say so.
#   B1-B4  flashguard through its CLI, refusing and PERMITTING.  A guard shown
#          only refusing is not shown to be a guard (plan R8 precondition 3).
#   B5-B8  the 2026-10-04 RULING, through `flashguard licence`: 0x020000 is
#          refused with no owner-yes, PERMITTED under the owner's dated row,
#          refused again when one field of that row is changed -- and STILL
#          refused for the loader region and H601 even with a row that names
#          them exactly.  Three arms, and the third is the containment one.
#   G1-G2  the C fence against the Python one.  RLXU_FLASH_KEEPOUT_END and
#          RLXU_CHIP_SIZE are read OUT of src/rlxboot/container.h and must
#          equal what flashguard.check_unrecoverable enforces -- which is
#          PROBED, not grepped for a literal.  G2 is G1's control: a planted
#          wrong value must make the same comparison fail.
#   N1-N8  format 2's signed destination AND landing form.  The declaration
#          is required and so is the form (N1, N2, N7); the two committed
#          fixtures differ in the 8 declaration bytes and the 64 signature
#          bytes and NOWHERE else (N3), which in format 1 was 0 bytes;
#          `verify --write-at/--write-form` accepts a match and refuses a
#          mismatched base, a mismatched FORM and an undeclared container
#          (N4, N5, N8); and a container whose format word says 1 is refused
#          at step 1 (N6).  N8 is the one that fails if the form is signed
#          but not compared -- the writer, not the signer, then decides
#          whether the 160-byte prefix is stripped, and that decides whether
#          a rescue slot can boot at all (FW-168).
#   C1-C6  mkfw2's three build refusals and the stock-loader proof, through the
#          CLI, including `rtkimage.py`'s independent cr6c parser as a second
#          source over the same container.
#   D1-D2  one flipped bit, at the CLI, rejected -- and the unflipped container
#          accepted in the same shape, because a `verify` that always exits 1
#          would pass D1 alone.
#   X1-X4  **no tool here emits FLW, EW, EB or a non-zero AUTOBURN.**  Nothing
#          in R8a writes flash.  X1 sweeps every command's stdout+stderr, X2
#          sweeps the sources for a print of one, X3 is X1's control (a string
#          that IS present is found, so the sweep is known to look), and X4
#          checks the one permitted form `AUTOBURN 0` is not emitted either --
#          these tools have no business typing anything at the loader.
#   E1-E4  every refusal is one line with a reason and NEVER a traceback.
#   M1-M6  **the mutation controls.**  M1 breaks flashguard's lower bound so it
#          compares only the start address; M2 removes the nfjrom/boot.img name
#          refusal; M3 compares one digest byte; M4 lets a licence be read for
#          a range nothing can license; M5 makes the signed destination match
#          anything; M6 empties LICENSABLE so the licensed arm can never open.
#          Each must turn a named case RED.  A suite whose mutants
#          all survive is decoration, and CLAUDE.md requires the unmutated
#          suite to pass before a mutation run is trusted -- A1-A3 above are
#          that precondition and M1-M6 run last.
#
# Everything here runs at the desk with no device and no vendor drop.  C6 needs
# the s116 rlxfw build under $FWRE_WORK and SKIPs without it; the skip is
# printed, because a silent skip reads as a pass.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-/usr/bin/python3}"
MKFW="$HERE/mkfw2.py"
GUARD="$HERE/flashguard.py"
SIGN="$HERE/rlxsign.py"
FIX="$HERE/fixtures/mkfw2"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
RTK="$WORK/rebuild/s116/rtk/r6b8i/rlxfw/kroot/rtkload"
if [ -n "${TESTTMP:-}" ]; then T="$TESTTMP"; mkdir -p "$T"
else T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT; fi

pass=0; fail=0; skip=0
ck ()   { if [ "$2" = "$3" ]; then printf '  ok     %-56s %s\n' "$1" "$3"; pass=$((pass+1))
          else printf '  FAIL   %-56s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }
sk ()   { printf '  skip   %-56s %s\n' "$1" "$2"; skip=$((skip+1)); }
# 🔴 `_out`/`_err`, not `o`/`e`: the first version of this file used `$T/o` for
# both the captured stdout AND the directory C3 writes into, and the collision
# made `mkdir -p` fail and C3c report a refusal the tool never made.
rc ()   { "$@" >"$T/_out" 2>"$T/_err"; echo $?; }

echo "test-mkfw2 -- controls for mkfw2 / flashguard / rlxsign"

# --------------------------------------------------------------- A1-A3
ck "A1  rlxsign --self-test exits 0"     0 "$(rc "$PY" "$SIGN"  --self-test)"
ck "A2  flashguard --self-test exits 0"  0 "$(rc "$PY" "$GUARD" --self-test)"
ck "A3  mkfw2 --self-test exits 0"       0 "$(rc "$PY" "$MKFW"  --self-test)"

# --------------------------------------------------------------- A4-A6
WANT_PUB="$(awk -F'\t' '$1=="dev_public_key_hex"{print $2}' "$FIX/dev-key.tsv")"
GOT_PUB="$("$PY" "$SIGN" pubkey --dev-seed)"
ck "A4  derived public key == the committed fixture" "$WANT_PUB" "$GOT_PUB"

grep -v '^#' "$FIX/sample-payload.hex" | tr -d '\n' > "$T/p.hex"
"$PY" -c "import sys;open(sys.argv[2],'wb').write(bytes.fromhex(open(sys.argv[1]).read()))" \
      "$T/p.hex" "$T/payload.bin"
grep -v '^#' "$FIX/sample-v3.rlxu.hex" | tr -d '\n' > "$T/c.hex"
"$PY" -c "import sys;open(sys.argv[2],'wb').write(bytes.fromhex(open(sys.argv[1]).read()))" \
      "$T/c.hex" "$T/fixture.rlxu"
"$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/rebuilt.rlxu" \
      --version 3 --load-addr 0x80500000 --entry-addr 0x80500000 \
      --recipe-id 3685a3a4 --dev-seed --not-for-flash >/dev/null 2>&1
if cmp -s "$T/fixture.rlxu" "$T/rebuilt.rlxu"; then a5=same; else a5=DIFFERS; fi
ck "A5  the committed container rebuilds byte for byte" same "$a5"
ck "A6  the committed container verifies" 0 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture.rlxu" --dev-seed)"
# A7-A8 -- the SECOND committed fixture, the same payload declared for
# 0x030000.  It exists because A5 alone cannot see whether the destination is
# inside the signed bytes: in format 1 these two builds were byte-identical.
grep -v '^#' "$FIX/sample-v3-at030000.rlxu.hex" | tr -d '\n' > "$T/ca.hex"
"$PY" -c "import sys;open(sys.argv[2],'wb').write(bytes.fromhex(open(sys.argv[1]).read()))" \
      "$T/ca.hex" "$T/fixture-at.rlxu"
"$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/rebuilt-at.rlxu" \
      --version 3 --load-addr 0x80500000 --entry-addr 0x80500000 \
      --recipe-id 3685a3a4 --dev-seed --flash-at 0x030000 \
      --flash-form whole >/dev/null 2>&1
if cmp -s "$T/fixture-at.rlxu" "$T/rebuilt-at.rlxu"; then a7=same; else a7=DIFFERS; fi
ck "A7  the committed 0x030000 container rebuilds byte for byte" same "$a7"
ck "A8  and it verifies" 0 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed)"

# --------------------------------------------------------------- B1-B4
for spec in "0x000000 0x1000 loader" "0x005FFF 0x1 loader" \
            "0x006000 0x1000 H601" "0x007FFF 0x1 H601" \
            "0x020000 0x1000 rescue" "0x02FFFF 0x1 rescue"; do
  set -- $spec
  ck "B1  flashguard REFUSES $1+$2 ($3)" 1 "$(rc "$PY" "$GUARD" check --at "$1" --bytes "$2")"
done
# 🔴 B2 is the positive control plan precondition 3 names.  Without it, a guard
# that refuses every address in the chip passes B1 six times.
for spec in "0x008000 0x1000" "0x010000 0x1000" "0x01F000 0x1000" \
            "0x030000 0x1000" "0x060000 0x10000" "0x3F0000 0x200" \
            "0x3FF000 0x1000" "0x030000 0x110000"; do
  set -- $spec
  ck "B2  flashguard PERMITS $1+$2" 0 "$(rc "$PY" "$GUARD" check --at "$1" --bytes "$2")"
done
"$PY" "$GUARD" table > "$T/tbl" 2>&1
n=$(grep -c '^  0x0' "$T/tbl"); ck "B3  table lists 3 forbidden ranges" 3 "$n"
n=$(grep -c '^  PERMIT' "$T/tbl"); ck "B3b table shows permitted neighbours" 6 "$n"
ck "B4  a zero-length range is refused, not answered" 3 \
   "$(rc "$PY" "$GUARD" check --at 0x030000 --bytes 0)"

# --------------------------------------------------------------- B5-B8
# THE RULING, through the CLI, in all three directions.  The licence row is
# generated by flashguard's own `licence_payload`, so this block cannot drift
# from the spelling the tool demands -- and B6's permit is what makes B5 a
# guard rather than a wall.
PSHA="$("$PY" -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$T/payload.bin")"
# 🔴 THE LANDING LENGTH, not the container length.  The rescue slot is
# written in `payload` form, so 256 bytes land and not 416 -- and the row the
# owner signs names what is programmed.  Using the container length here was
# the defect the item-5 agent found in the first draft of this gate.
NB=256
ROW="$("$PY" -c "
import sys
sys.path.insert(0, sys.argv[1])
import flashguard as g
print('2026-10-04\t' + g.licence_payload(int(sys.argv[2], 0), int(sys.argv[3]),
                                         sys.argv[4], sys.argv[5]))" \
      "$HERE" 0x020000 "$NB" rescue "$PSHA")"
printf '# the owner looked at this payload for this slot\n\n```owner-yes\n%s\n```\n' \
       "$ROW" > "$T/licence.md"
ck "B5  flashguard licence REFUSES 0x020000 with no owner-yes" 1 \
   "$(rc "$PY" "$GUARD" licence --at 0x020000 --bytes "$NB" --sha256 "$PSHA")"
ck "B6  and PERMITS it with the owner's dated row" 0 \
   "$(rc "$PY" "$GUARD" licence --at 0x020000 --bytes "$NB" --sha256 "$PSHA" \
       --owner-yes "$T/licence.md")"
"$PY" "$GUARD" licence --at 0x020000 --bytes "$NB" --sha256 "$PSHA" \
      --owner-yes "$T/licence.md" > "$T/lic.out" 2>&1
if grep -q 'under the owner.s yes of 2026-10-04' "$T/lic.out"; then b6=dated; else b6=UNDATED; fi
ck "B6b and the permit names the date it was given" dated "$b6"
# 🔴 B7: the same licence, one byte more.  A row that covers a different
# length is not this row.
ck "B7  that row does not cover one byte more" 1 \
   "$(rc "$PY" "$GUARD" licence --at 0x020000 --bytes $((NB + 1)) --sha256 "$PSHA" \
       --owner-yes "$T/licence.md")"
# 🔴 B8 IS THE CONTAINMENT ARM.  A row written for the loader region and for
# H601, with the right digest and a real date, must open nothing at all.
for spec in "0x000000 loader" "0x005FFF loader" "0x006000 H601" "0x007FFF H601"; do
  set -- $spec
  r8row="$("$PY" -c "
import sys
sys.path.insert(0, sys.argv[1])
import flashguard as g
print('2026-10-04\t' + g.licence_payload(int(sys.argv[2], 0), 1, sys.argv[3],
                                         sys.argv[4]))" \
        "$HERE" "$1" "$2" "$PSHA")"
  printf '```owner-yes\n%s\n```\n' "$r8row" > "$T/bad-licence.md"
  ck "B8  a licence naming $1 ($2) opens nothing" 1 \
     "$(rc "$PY" "$GUARD" licence --at "$1" --bytes 1 --sha256 "$PSHA" \
         --owner-yes "$T/bad-licence.md")"
done

# --------------------------------------------------------------- G1-G2
# The C fence and the Python one.  `container.h` states the two bounds the
# DEVICE enforces; flashguard enforces the same two on the host.  Neither is
# read from the other at run time, so this is the case that goes red on drift.
# The Python side is PROBED -- the first offset check_unrecoverable permits --
# rather than read as a constant, because a pre-flight guard tests the real
# value and not a grep for a literal.
HDR="$HERE/../src/rlxboot/container.h"
KEEP="$(awk '$2=="RLXU_FLASH_KEEPOUT_END"{print $3}' "$HDR")"
CHIP="$(awk '$2=="RLXU_CHIP_SIZE"{print $3}' "$HDR")"
WANT="$(printf '0x%08X 0x%08X' $((${KEEP%UL})) $((${CHIP%UL})))"
GOT="$("$PY" -c "
import sys
sys.path.insert(0, sys.argv[1])
import flashguard as g
k = 0
while k < g.CHIP_SIZE and g.check_unrecoverable(k, 1) is not None:
    k += 1
print('0x%08X 0x%08X' % (k, g.CHIP_SIZE))" "$HERE")"
ck "G1  container.h's keepout and chip size equal flashguard's" "$WANT" "$GOT"
# G2 is G1's control: the same comparison against a planted wrong keepout must
# NOT match, or G1 is a comparison that cannot fail.
BAD="$(printf '0x%08X 0x%08X' $((0x9000)) $((${CHIP%UL})))"
ck "G2  and the same comparison rejects a planted wrong keepout" differ \
   "$([ "$BAD" != "$GOT" ] && echo differ || echo SAME)"

# --------------------------------------------------------------- C1-C6
ck "C1  build REFUSES --flash-at 0x000000 (loader)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x000000 \
       --flash-form whole)"
ck "C1b build REFUSES --flash-at 0x006000 (H601)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x006000 \
       --flash-form whole)"
ck "C1c build REFUSES --flash-at 0x020000 (rescue)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x020000 \
       --flash-form payload)"
# 🔴 C1d IS THE LICENSED ARM OF THE RULING, through the producer.  C1c above
# is the same command without `--owner-yes` and it is still refused 3.
ck "C1d build PERMITS --flash-at 0x020000 WITH the owner-yes" 0 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/resc.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x020000 \
       --flash-form payload --owner-yes "$T/licence.md")"
f=$("$PY" -c "import sys;print(open(sys.argv[1],'rb').read()[64:72].hex())" "$T/resc.rlxu")
ck "C1e and the container it built SIGNS 0x00020000 and 'PAYL' at 64..71" \
   000200005041594c "$f"
# the digest arm, through the CLI: the same licence, a different payload
head -c 128 "$T/payload.bin" > "$T/other.bin"
ck "C1f that licence does not cover a different payload" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/other.bin" --out "$T/resc2.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x020000 \
       --flash-form payload --owner-yes "$T/licence.md")"
# 🔴 C1g: the SAME licence does not cover the WHOLE-container landing at the
# same base -- 160 more bytes land, so it is a different write.
ck "C1g that licence does not cover the whole-container landing" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/resc3.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x020000 \
       --flash-form whole --owner-yes "$T/licence.md")"
ck "C2  build PERMITS --flash-at 0x030000" 0 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/ok.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x030000 \
       --flash-form whole)"
mkdir -p "$T/outs"
# 🔴 `--not-for-flash` is on every one of these: without a declaration the
# refusal would be the DECLARATION's and not the name's, and C3 would pass
# while testing nothing.  C3c, which expects 0, is what would have caught it.
for bad in nfjrom boot.img NFJROM Boot.IMG; do
  ck "C3  build REFUSES --out $bad" 3 \
     "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/outs/$bad" \
         --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
         --recipe-id 3685a3a4 --dev-seed --not-for-flash)"
  if grep -q 'AUTO-EXECUTE' "$T/_err"; then w2=name; else w2=OTHER; fi
  ck "C3d and the refusal is the NAME's, not the declaration's" name "$w2"
  if [ -e "$T/outs/$bad" ]; then w=WROTE; else w=absent; fi
  ck "C3b it did not create $bad" absent "$w"
done
ck "C3c build PERMITS --out nfjrom.rlxu (a near miss)" 0 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/outs/nfjrom.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --not-for-flash)"
"$PY" "$MKFW" verify "$T/ok.rlxu" --dev-seed --stock-loader > "$T/sl" 2>&1
ck "C4  verify --stock-loader exits 0 on a good container" 0 "$(rc "$PY" "$MKFW" \
   verify "$T/ok.rlxu" --dev-seed --stock-loader)"
if grep -q 'stock loader verdict: NOT AN IMAGE' "$T/sl"; then v=NOTIMAGE; else v=MISSING; fi
ck "C5  the stock loader does NOT recognise it" NOTIMAGE "$v"
# C6 -- the second source: rtkimage.py's own cr6c header parser, which is not
# this code, over the same container.  It must report a signature that is not
# cr6c AND a non-zero sum16: two independent reasons check_image() fails.
if [ -f "$RTK/nfjrom" ] && [ -f "$RTK/memload-full" ]; then
  "$PY" "$HERE/rtkimage.py" check --nfjrom "$RTK/nfjrom" \
        --memload "$RTK/memload-full" --linuxbin "$T/ok.rlxu" \
        --label RLXU > "$T/rt" 2>&1
  # 🔴 TWO defects this line had, both caught by running it.  (1) `grep -qv`
  # is true whenever ANY line fails to match, so it was true every run.  (2)
  # grepping the WHOLE capture read `rtkimage`'s own control R2, which prints
  # `sum16 0x0000 -> 0xFFFF` about a DIFFERENT image -- so the assertion about
  # this container was answered by a line about the vendor's.  The block the
  # verdict lives in is `  linux.bin` to the end, and nothing else is read.
  sed -n '/^  linux.bin$/,$p' "$T/rt" > "$T/rt.lb"
  c6=UNEXPECTED
  if grep -q "signature  *b'RLXU'" "$T/rt.lb" \
     && grep -qE 'sum16 +0x[0-9A-F]{4}' "$T/rt.lb" \
     && ! grep -qE 'sum16 +0x0000' "$T/rt.lb"; then c6=rejected; fi
  # C6c is (2)'s control: the scoped block must be SHORTER than the capture, or
  # the sed matched nothing and the scoping did not happen.
  ck "C6c the verdict block is scoped, not the whole capture" yes \
     "$([ "$(wc -l < "$T/rt.lb")" -lt "$(wc -l < "$T/rt")" ] \
        && [ -s "$T/rt.lb" ] && echo yes || echo NO)"
  ck "C6  rtkimage's independent cr6c parser rejects it" rejected "$c6"
  ck "C6b and rtkimage exits non-zero on it" 1 \
     "$(rc "$PY" "$HERE/rtkimage.py" check --nfjrom "$RTK/nfjrom" \
         --memload "$RTK/memload-full" --linuxbin "$T/ok.rlxu" --label RLXU)"
else
  sk "C6" "no rlxfw build at $RTK -- the second-source parser has no image"
fi

# --------------------------------------------------------------- N1-N6
# Format 2: the declaration is required, it is signed, and it is compared.
ck "N1  build with NEITHER declaration is refused" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/n1.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed)"
if grep -q 'exactly one of' "$T/_err"; then n1=declaration; else n1=OTHER; fi
ck "N1b and the reason is the missing declaration" declaration "$n1"
if [ -e "$T/n1.rlxu" ]; then n1c=WROTE; else n1c=absent; fi
ck "N1c and it wrote no container" absent "$n1c"
ck "N2  build with BOTH declarations is refused" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/n2.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x030000 --not-for-flash)"
# 🔴 N3 is the measurement format 1 could not pass: the two committed
# fixtures carry the same payload and must differ in the 4 destination bytes
# and the 64 signature bytes and in NOTHING else.  In format 1 the same two
# builds differed in 0 bytes.
n3="$("$PY" -c "
import sys
a = open(sys.argv[1], 'rb').read()
b = open(sys.argv[2], 'rb').read()
d = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
print('%d %d %d %d' % (len(d), len([i for i in d if 64 <= i < 72]),
                       len([i for i in d if 96 <= i < 160]),
                       len([i for i in d if i < 64 or 72 <= i < 96 or i >= 160])))" \
      "$T/fixture.rlxu" "$T/fixture-at.rlxu")"
ck "N3  the two fixtures differ in the 8 declaration bytes and the \
signature only" "72 8 64 0" "$n3"
ck "N4  verify --write-at 0x030000 whole ACCEPTS the container declared for \
it" 0 "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed \
       --write-at 0x030000 --write-form whole)"
ck "N4b and REFUSES the same container against 0x020000" 1 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed \
       --write-at 0x020000 --write-form whole)"
ck "N5  an UNDECLARED container is refused against any write" 1 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture.rlxu" --dev-seed \
       --write-at 0x030000 --write-form whole)"
"$PY" "$MKFW" verify "$T/fixture.rlxu" --dev-seed --write-at 0x030000 \
      --write-form whole > "$T/n5" 2>&1
if grep -q 'REJECT step 2 flash_match' "$T/n5"; then n5=by_name; else n5=OTHER; fi
ck "N5b and the refusal is flash_match, by name" by_name "$n5"
# N7: the FORM is required with --flash-at, and refused without it.
ck "N7  --flash-at without --flash-form is refused" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/n7.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x030000)"
if grep -q 'needs --flash-form' "$T/_err"; then n7=form; else n7=OTHER; fi
ck "N7b and the reason is the missing form" form "$n7"
ck "N7c --flash-form without --flash-at is refused" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/n7c.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-form whole)"
# 🔴 N8 IS THE FOURTH DECISION'S CASE.  The base agrees and only the FORM
# differs, so this is what goes green on a signature that covers the form and
# red on a verifier that does not compare it.  量 2026-10-04: a container over
# a cr6c-headed payload reads RLXU at offset 0 and cr6c at offset 160, so the
# form decides whether the stock loader can boot what landed at 0x020000.
ck "N8  the 0x030000 WHOLE container is ACCEPTED against a whole write" 0 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed \
       --write-at 0x030000 --write-form whole)"
ck "N8b and REFUSED against a PAYLOAD write to the same base" 1 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed \
       --write-at 0x030000 --write-form payload)"
ck "N8c and REFUSED against a caller that names no form at all" 1 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed \
       --write-at 0x030000)"
"$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed --write-at 0x030000 \
      --write-form payload > "$T/n8" 2>&1
if grep -q 'REJECT step 2 flash_match' "$T/n8"; then n8=by_name; else n8=OTHER; fi
ck "N8d and that refusal is flash_match, by name" by_name "$n8"
# N8e: the landing report, in both directions, over the two fixtures.
"$PY" "$MKFW" verify "$T/fixture-at.rlxu" --dev-seed > "$T/n8e" 2>&1
if grep -q "landing bytes      b'RLXU' at 0x030000" "$T/n8e" \
   && grep -q 'landing scanned    0x030000 IS one of' "$T/n8e"; then
  n8e=reported
else n8e=MISSING; fi
ck "N8e verify reports what lands and whether that base is scanned" reported "$n8e"
"$PY" "$MKFW" verify "$T/fixture.rlxu" --dev-seed > "$T/n8f" 2>&1
if grep -q 'landing            nothing' "$T/n8f"; then n8f=nothing; else n8f=MISSING; fi
ck "N8f and reports no landing at all for the undeclared one" nothing "$n8f"

# N6: the format word patched to 1, NOT re-signed -- step 1 runs before step 3,
# so the old format number is what must refuse it.
"$PY" -c "import sys
b = bytearray(open(sys.argv[1], 'rb').read())
b[4] = 0; b[5] = 1
open(sys.argv[2], 'wb').write(bytes(b))" "$T/fixture.rlxu" "$T/f1.rlxu"
ck "N6  a container whose format word says 1 is refused" 1 \
   "$(rc "$PY" "$MKFW" verify "$T/f1.rlxu" --dev-seed)"
"$PY" "$MKFW" verify "$T/f1.rlxu" --dev-seed > "$T/n6" 2>&1
if grep -q 'REJECT step 1 format' "$T/n6"; then n6=by_name; else n6=OTHER; fi
ck "N6b and the refusal is step 1 format, before the signature" by_name "$n6"

# --------------------------------------------------------------- D1-D2
ck "D2  the unflipped container is ACCEPTED (D1's control)" 0 \
   "$(rc "$PY" "$MKFW" verify "$T/ok.rlxu" --dev-seed)"
d1=ok
for off in 0 4 8 12 16 20 24 28 60 64 95 96 130 159 160 300; do
  cp "$T/ok.rlxu" "$T/flip.rlxu"
  "$PY" -c "import sys
p,o=sys.argv[1],int(sys.argv[2])
b=bytearray(open(p,'rb').read()); b[o]^=1; open(p,'wb').write(bytes(b))" \
        "$T/flip.rlxu" "$off"
  r=$(rc "$PY" "$MKFW" verify "$T/flip.rlxu" --dev-seed)
  [ "$r" = 1 ] || d1="ACCEPTED at offset $off"
done
ck "D1  one flipped bit at each of 16 offsets is REJECTED" ok "$d1"

# --------------------------------------------------------------- X1-X4
# Every command of every tool, stdout and stderr together, swept for the four
# verbs that can write flash.  `\b` is not portable here, so the patterns are
# anchored on the shapes a command would take.
: > "$T/allout"
for cmd in "$SIGN --self-test" "$SIGN pubkey --dev-seed" "$SIGN" \
           "$GUARD --self-test" "$GUARD table" "$GUARD check --at 0x030000 --bytes 0x1000" \
           "$GUARD check --at 0x000000 --bytes 0x1000" "$GUARD" \
           "$GUARD licence --at 0x030000 --bytes 0x1000 --sha256 $PSHA" \
           "$GUARD licence --at 0x020000 --bytes $NB --sha256 $PSHA" \
           "$GUARD licence --at 0x020000 --bytes $NB --sha256 $PSHA --owner-yes $T/licence.md" \
           "$MKFW --self-test" "$MKFW" \
           "$MKFW verify $T/ok.rlxu --dev-seed --stock-loader" \
           "$MKFW verify $T/fixture-at.rlxu --dev-seed --write-at 0x030000 --write-form whole" \
           "$MKFW verify $T/fixture-at.rlxu --dev-seed --write-at 0x030000 --write-form payload" \
           "$MKFW verify $T/fixture-at.rlxu --dev-seed --write-at 0x020000 --write-form whole"; do
  "$PY" $cmd >> "$T/allout" 2>> "$T/allout" || true
done
bad=$(grep -oE '(FLW|AUTOBURN|\bEW\b|\bEB\b)[^a-zA-Z]' "$T/allout" | sort -u | tr '\n' ' ')
ck "X1  no FLW / EW / EB / AUTOBURN in any command's output" "" "$bad"
# X3 is X1's control: the sweep must find a string that IS there, or "none
# found" only means the sweep does not look.
if grep -q 'RLXU' "$T/allout"; then x3=found; else x3=BLIND; fi
ck "X3  X1's sweep does find a string that IS present" found "$x3"
# X2 looks for a verb inside a string literal ON a print line and followed by
# a space -- the shape a COMMAND takes.  Naming a verb in prose is not emitting
# one, and an X2 that fired on prose is an X2 nobody will keep.
bad=$(grep -nE "print\(.*[\"'](FLW|EW|EB|AUTOBURN) " "$MKFW" "$GUARD" "$SIGN" \
      | tr '\n' ' ')
ck "X2  no source line prints one of the four verbs as a command" "" "$bad"
# X2b is X2's control: the same pattern applied to a line that DOES look like a
# command must match, or X2 is a grep that cannot fire.
echo 'print("FLW 0 0 0")' > "$T/decoy.py"
n=$(grep -cE "print\(.*[\"'](FLW|EW|EB|AUTOBURN) " "$T/decoy.py")
ck "X2b the same pattern DOES match a planted command" 1 "$n"
bad=$(grep -oE 'AUTOBURN +[0-9]' "$T/allout" | sort -u | tr '\n' ' ')
ck "X4  not even AUTOBURN 0 is emitted" "" "$bad"

# --------------------------------------------------------------- E1-E4
tb () { if grep -q Traceback "$T/_err" "$T/_out"; then echo TRACEBACK
        elif [ "$(wc -l < "$T/_err")" -le 2 ]; then echo "1-line"
        else echo "$(wc -l < "$T/_err")-lines"; fi; }
r=$(rc "$PY" "$MKFW");            ck "E1  mkfw2 with no subcommand: rc 3, one line" "3 1-line" "$r $(tb)"
r=$(rc "$PY" "$GUARD");           ck "E2  flashguard with no subcommand: rc 3" "3 1-line" "$r $(tb)"
r=$(rc "$PY" "$SIGN");            ck "E3  rlxsign with no subcommand: rc 2" "2 1-line" "$r $(tb)"
r=$(rc "$PY" "$MKFW" verify "$T/nope.rlxu" --dev-seed)
ck "E4  mkfw2 verify on a missing file: rc 3, no traceback" "3 1-line" "$r $(tb)"
r=$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/z.rlxu" \
     --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
     --recipe-id zz --dev-seed --not-for-flash)
ck "E4b a bad --recipe-id: rc 3, no traceback" "3 1-line" "$r $(tb)"

# --------------------------------------------------------------- M1-M2
# 🔴 The mutation controls.  A1-A3 above are the precondition CLAUDE.md names:
# an unmutated suite that does not pass makes a mutation run meaningless, and
# the two `ck` calls just above this line are where that would have shown.
#
# Each mutant is applied to a COPY of the tools in $T/m/, never to the tree.
mut () {   # $1 label  $2 sed program  $3 file to mutate  $4 tool to run
  rm -rf "$T/m"; mkdir -p "$T/m"
  # 🔴 EVERY tools/*.py, not the four this suite names.  The first version
  # copied four files and left out `flashwin.py`, which `flashguard.py`
  # imports; all three mutants then died on the import with rc 1 and were
  # scored SURVIVED.  A mutation harness that cannot run the mutant reports
  # the same thing as a mutant that is not caught.
  cp "$HERE"/*.py "$T/m/"
  cp -r "$HERE/fixtures" "$T/m/fixtures"
  sed -i "$2" "$T/m/$3"
  if cmp -s "$HERE/$3" "$T/m/$3"; then
    printf '  FAIL   %-56s the sed changed NOTHING\n' "$1"; fail=$((fail+1))
    echo 99; return
  fi
  "$PY" "$T/m/$4" --self-test >"$T/mo" 2>&1
  echo $?
}

r=$(mut "M1  flashguard lower bound broken -> a case goes red" \
        's|if at < hi and end > lo:|if lo <= at < hi:|' \
        flashguard.py flashguard.py)
if [ "$r" = 2 ] && grep -q 'FAIL' "$T/mo"; then
  m1="red: $(grep -m3 -oE 'FAIL +[A-Z0-9]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m1="SURVIVED (rc $r)"; fi
ck "M1  a start-address-only compare turns cases RED" "red:" "${m1%%:*}:"
printf '         %s\n' "$m1"

r=$(mut "M2  nfjrom name refusal removed -> a case goes red" \
        's|^AUTOEXEC_NAMES = .*|AUTOEXEC_NAMES = ()|' \
        mkfw2.py mkfw2.py)
if [ "$r" = 2 ] && grep -q 'FAIL  *C17' "$T/mo"; then m2="red: C17"
else m2="SURVIVED (rc $r)"; fi
ck "M2  removing the nfjrom refusal turns C17 RED" "red:" "${m2%%:*}:"
printf '         %s\n' "$m2"

# A third mutant, because M1 and M2 both hit a refusal and neither touches the
# container format: break the digest comparison to one byte and the bit-flip
# sweep must go red.
r=$(mut "M3  digest compared on one byte -> the flip sweep goes red" \
        's|got == f\["digest"\]|got[:1] == f["digest"][:1]|' \
        mkfw2.py mkfw2.py)
if [ "$r" = 2 ] && grep -qE 'FAIL +C5b' "$T/mo"; then
  m3="red: $(grep -m3 -oE 'FAIL +[A-Z0-9b]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m3="SURVIVED (rc $r)"; fi
ck "M3  a one-byte digest compare turns cases RED" "red:" "${m3%%:*}:"
printf '         %s\n' "$m3"

# 🔴 M4 IS THE MUTANT FOR THE CONTAINMENT RULE.  `if False` makes
# `check_licensed` read a licence for EVERY forbidden range, so a row naming
# the loader region opens it -- which is precisely what L4 and L6 exist to
# refuse.  If this mutant survives, the ruling has no guard behind it.
r=$(mut "M4  a licence read for an unrecoverable range -> L4/L6 red" \
        's|if r.rid not in LICENSABLE:|if False:|' \
        flashguard.py flashguard.py)
if [ "$r" = 2 ] && grep -qE 'FAIL +L(4|6)' "$T/mo"; then
  m4="red: $(grep -m4 -oE 'FAIL +[A-Z0-9b]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m4="SURVIVED (rc $r)"; fi
ck "M4  opening the licence for every range turns cases RED" "red:" "${m4%%:*}:"
printf '         %s\n' "$m4"

# M5: the signed destination compared against nothing.  C23b/C24 are what
# must notice, and C25 -- the permitting arm -- must stay green, or the
# mutant would be caught by a case that proves nothing about the comparison.
r=$(mut "M5  flash_match always true -> C23b/C24 red" \
        's|fa == write_at|True|' mkfw2.py mkfw2.py)
if [ "$r" = 2 ] && grep -qE 'FAIL +C2(3b|4)' "$T/mo"; then
  m5="red: $(grep -m4 -oE 'FAIL +[A-Z0-9b]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m5="SURVIVED (rc $r)"; fi
ck "M5  a destination that matches anything turns cases RED" "red:" "${m5%%:*}:"
printf '         %s\n' "$m5"

# M6: the other direction on the ruling.  With LICENSABLE empty the licensed
# arm can never open, so L2 and the mkfw2 cases that build for 0x020000 go
# red -- the control that B6/C1d/L2 are not passing for some other reason.
r=$(mut "M6  LICENSABLE emptied -> L2 red" \
        's|^LICENSABLE = .*|LICENSABLE = ()|' flashguard.py flashguard.py)
if [ "$r" = 2 ] && grep -qE 'FAIL +L(2|11)' "$T/mo"; then
  m6="red: $(grep -m4 -oE 'FAIL +[A-Z0-9b]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m6="SURVIVED (rc $r)"; fi
ck "M6  an empty LICENSABLE turns the licensed arm RED" "red:" "${m6%%:*}:"
printf '         %s\n' "$m6"

# 🔴 M7 IS THE MUTANT FOR THE FOURTH DECISION.  Comparing only the offset is
# exactly the verifier the item-5 agent's reading would have let through: the
# writer then chooses whether to strip the 160-byte prefix, and that choice is
# whether `rlxboot-rescue` boots.  C25b is what must notice.
r=$(mut "M7  flash_match compares the offset only -> C25b red" \
        's|fa == write_at and fo == wf|fa == write_at|' mkfw2.py mkfw2.py)
if [ "$r" = 2 ] && grep -qE 'FAIL +C25b' "$T/mo"; then
  m7="red: $(grep -m4 -oE 'FAIL +[A-Z0-9b]+' "$T/mo" | awk '{print $2}' | tr '\n' ',')"
else m7="SURVIVED (rc $r)"; fi
ck "M7  comparing the offset but not the form turns C25b RED" "red:" "${m7%%:*}:"
printf '         %s\n' "$m7"

echo "  $pass passed, $fail failed, $skip skipped"
[ "$fail" -eq 0 ] || exit 1
exit 0
