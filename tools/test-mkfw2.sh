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
#   M1-M2  **the mutation controls.**  M1 breaks flashguard's lower bound so it
#          compares only the start address; M2 removes the nfjrom/boot.img name
#          refusal.  Each must turn a named case RED.  A suite whose mutants
#          all survive is decoration, and CLAUDE.md requires the unmutated
#          suite to pass before a mutation run is trusted -- A1-A3 above are
#          that precondition and M1/M2 run last.
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
sk ()   { printf '  (skipped: %s -- %s)\n' "$1" "$2"; skip=$((skip+1)); }
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
      --recipe-id 3685a3a4 --dev-seed >/dev/null 2>&1
if cmp -s "$T/fixture.rlxu" "$T/rebuilt.rlxu"; then a5=same; else a5=DIFFERS; fi
ck "A5  the committed container rebuilds byte for byte" same "$a5"
ck "A6  the committed container verifies" 0 \
   "$(rc "$PY" "$MKFW" verify "$T/fixture.rlxu" --dev-seed)"

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

# --------------------------------------------------------------- C1-C6
ck "C1  build REFUSES --flash-at 0x000000 (loader)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x000000)"
ck "C1b build REFUSES --flash-at 0x006000 (H601)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x006000)"
ck "C1c build REFUSES --flash-at 0x020000 (rescue)" 3 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/x.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x020000)"
ck "C2  build PERMITS --flash-at 0x030000" 0 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/ok.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed --flash-at 0x030000)"
mkdir -p "$T/outs"
for bad in nfjrom boot.img NFJROM Boot.IMG; do
  ck "C3  build REFUSES --out $bad" 3 \
     "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/outs/$bad" \
         --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
         --recipe-id 3685a3a4 --dev-seed)"
  if [ -e "$T/outs/$bad" ]; then w=WROTE; else w=absent; fi
  ck "C3b it did not create $bad" absent "$w"
done
ck "C3c build PERMITS --out nfjrom.rlxu (a near miss)" 0 \
   "$(rc "$PY" "$MKFW" build --payload "$T/payload.bin" --out "$T/outs/nfjrom.rlxu" \
       --version 1 --load-addr 0x80500000 --entry-addr 0x80500000 \
       --recipe-id 3685a3a4 --dev-seed)"
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
           "$MKFW --self-test" "$MKFW" \
           "$MKFW verify $T/ok.rlxu --dev-seed --stock-loader"; do
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
     --recipe-id zz --dev-seed)
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

echo "  $pass passed, $fail failed, $skip skipped"
[ "$fail" -eq 0 ] || exit 1
exit 0
