#!/usr/bin/env bash
# Controls for tools/rtkimage.py -- and mutations that must break them.
#
# `rtkimage check` says three things a bench session will act on: what the
# loader will find at 0x80500000, how big the decompressed image is, and
# whether it is under the ceiling.  Each of those is a number that would look
# exactly the same if the tool were reading the wrong bytes, so the cases here
# are mostly about making it read the wrong bytes on purpose.
#
#   S1  sum16 is the rule C-4 states, and one flipped bit moves it
#   S2  a hand-built cr6c header parses to the fields it was built from
#   S3  the exit contract: no subcommand 3, unknown 3, check with no --nfjrom
#       3, check with no --memload 3 (and it says why, because __vmlinux_start
#       comes out of the ELF and not out of a scan)
#   S4  elf_symbols finds a planted __vmlinux_start in a synthetic ELF
#   B1  the drop's own nfjrom checks out and reproduces §3.2's four numbers
#   B2  --expect-img pointed at the wrong file exits 1 rather than 0
#   B3  a truncated payload is REFUSED -- it decodes partially without raising,
#       so "smaller image" is the shape this had to be stopped from printing
#   M1  R1's expectation moved; the tool must refuse and report nothing
#   M2  sum16 forced to 0; R2 must go red
#
# S1-S4 run anywhere.  B1-B3 and M1-M2 need the GPL drop under
# $FWRE_WORK/rebuild/src-vendor, which cannot be committed, and they SKIP
# rather than pass without it.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$HERE/rtkimage.py"
PY="${PYTHON:-python3}"
WORK="${FWRE_WORK:-/home/key/fwre-work}"
DROP="$WORK/rebuild/src-vendor/rtl819x-toolchain"
if [ -n "${TESTTMP:-}" ]; then T="$TESTTMP"; mkdir -p "$T"
else T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT; fi

pass=0; fail=0; skip=0
ck ()   { if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
          else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }
ckin () { if grep -qF -- "$2" "$3"; then printf '  ok     %-52s %s\n' "$1" "found"; pass=$((pass+1))
          else printf '  FAIL   %-52s %s not in output\n' "$1" "$2"; fail=$((fail+1)); fi }
sk ()   { printf '  skip   %-52s %s\n' "$1" "$2"; skip=$((skip+1)); }

[ -f "$TOOL" ] || { echo "no $TOOL"; exit 3; }

echo "== tools/test-rtkimage.sh"
echo

# ----------------------------------------------------------------- S1, S2, S4
"$PY" - "$TOOL" "$T" > "$T/s.out" 2>&1 <<'PYEOF'
import importlib.util, os, struct, sys
spec = importlib.util.spec_from_file_location('r', sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
T = sys.argv[2]
out = []

# S1 -- sum16, and a bit that has to move it
p = bytes([0x12, 0x34, 0xED, 0xCC])          # 0x1234 + 0xEDCC = 0x10000 -> 0
out.append(('S1a  sum16 of a zero-summing payload', '0', '%d' % r.sum16(p)))
bad = bytearray(p); bad[0] ^= 0x01
out.append(('S1b  one flipped bit moves it', 'True', str(r.sum16(bytes(bad)) != 0)))
out.append(('S1c  odd length is padded, not rejected', '0x1234',
            '0x%04X' % r.sum16(b'\x12\x34')))

# S2 -- a hand-built cr6c header
body = b'\xAA' * 64
hdr = b'cr6c' + struct.pack('>3I', 0x80500000, 0x30000, len(body) + 2)
tail = struct.pack('>H', (-r.sum16(body)) & 0xFFFF)
path = os.path.join(T, 'lx.bin')
open(path, 'wb').write(hdr + body + tail)
d = r.parse_linuxbin(path)
out.append(('S2a  signature',    "b'cr6c'", repr(d['signature'])))
out.append(('S2b  start address', '0x80500000', '0x%08X' % d['start']))
out.append(('S2c  flash offset',  '0x00030000', '0x%08X' % d['flash_offset']))
out.append(('S2d  length field',  '66', str(d['length'])))
out.append(('S2e  the tail makes the payload sum to zero', '0x0000',
            '0x%04X' % d['sum16']))

# S4 -- a synthetic ELF with __vmlinux_start / __vmlinux_end
def mkelf(path, syms):
    shstr = b'\0.shstrtab\0.symtab\0.strtab\0'
    strtab = b'\0'
    symtab = b'\0' * 16
    for n, v in syms:
        symtab += struct.pack('>3IBBH', len(strtab), v, 0, (1 << 4) | 1, 0, 1)
        strtab += n.encode() + b'\0'
    eh, se = 52, 40
    o1 = eh; o2 = o1 + len(shstr); o3 = o2 + len(symtab); o4 = o3 + len(strtab)
    osh = (o4 + 3) & ~3
    sh = [(0,)*10,
          (1, 3, 0, 0, o1, len(shstr), 0, 0, 1, 0),
          (11, 2, 0, 0, o2, len(symtab), 3, 1, 4, 16),
          (19, 3, 0, 0, o3, len(strtab), 0, 0, 1, 0)]
    b = bytearray(b'\x7fELF\x01\x02\x01' + b'\0' * 9)
    b += struct.pack('>HHIIIIIHHHHHH', 2, 8, 1, 0, 0, osh, 0, eh, 0, 0, se,
                     len(sh), 1)
    b += shstr + symtab + strtab
    b += b'\0' * (osh - len(b))
    for s in sh:
        b += struct.pack('>10I', *s)
    open(path, 'wb').write(bytes(b))

e = os.path.join(T, 'ml.elf')
mkelf(e, [('__vmlinux_start', 0x80502C00), ('__vmlinux_end', 0x805D07E4)])
s = r.elf_symbols(e)
out.append(('S4a  __vmlinux_start', '0x80502C00', '0x%08X' % s['__vmlinux_start'][0]))
out.append(('S4b  __vmlinux_end',   '0x805D07E4', '0x%08X' % s['__vmlinux_end'][0]))
out.append(('S4c  a file that is not an ELF returns None', 'None',
            str(r.elf_symbols(os.path.join(T, 'lx.bin')))))
for lbl, exp, got in out:
    print('%s\t%s\t%s' % (lbl, exp, got))
PYEOF
if [ -s "$T/s.out" ] && grep -q 'S1a' "$T/s.out"; then
    while IFS=$'\t' read -r lbl exp got; do ck "$lbl" "$exp" "$got"; done < "$T/s.out"
else
    printf '  FAIL   %-52s %s\n' "S1-S4 the in-process block" "$(head -3 "$T/s.out" | tr '\n' ' ')"
    fail=$((fail+1))
fi

# ------------------------------------------------------------------------- S3
"$PY" "$TOOL" >/dev/null 2>&1;                      ck "S3a no subcommand" 3 "$?"
"$PY" "$TOOL" frobnicate >/dev/null 2>&1;           ck "S3b unknown subcommand" 3 "$?"
"$PY" "$TOOL" check >/dev/null 2>&1;                ck "S3c check with no --nfjrom" 3 "$?"

# --------------------------------------------------------------- B1, B2, B3, M
NF="$DROP/boards/rtl8196e/image/nfjrom"
ML="$DROP/linux-2.6.30/rtkload/memload-full"
IMG="$DROP/linux-2.6.30/rtkload/vmlinux_img"
LB="$DROP/boards/rtl8196e/image/linux.bin"
if [ -f "$NF" ] && [ -f "$ML" ] && [ -f "$IMG" ]; then
    "$PY" "$TOOL" check --nfjrom "$NF" >/dev/null 2>&1
    ck "S3d check with no --memload" 3 "$?"

    "$PY" "$TOOL" check --nfjrom "$NF" --memload "$ML" --linuxbin "$LB" \
          --expect-img "$IMG" > "$T/b1.out" 2>&1
    ck   "B1  the drop's own nfjrom: exit" 0 "$?"
    ckin "B1a R1 fired" "ok    R1" "$T/b1.out"
    ckin "B1b R2 fired" "ok    R2" "$T/b1.out"
    ckin "B1c R3 fired" "ok    R3" "$T/b1.out"
    ckin "B1d pending_len 1"          "pending_len                1" "$T/b1.out"
    ckin "B1e kernelStartAddr"        "0x80003600" "$T/b1.out"
    ckin "B1f decompressed 2,953,660" "decompressed bytes         2953660" "$T/b1.out"
    ckin "B1g 56.3% of the ceiling"   "56.3% used" "$T/b1.out"
    ckin "B1h the round trip holds"   "byte-identical           True" "$T/b1.out"

    head -c 100000 "$IMG" > "$T/wrong.img"
    "$PY" "$TOOL" check --nfjrom "$NF" --memload "$ML" --expect-img "$T/wrong.img" \
          > "$T/b2.out" 2>&1
    ck "B2  --expect-img pointed at the wrong file" 1 "$?"

    head -c 600000 "$NF" > "$T/trunc.bin"
    "$PY" "$TOOL" check --nfjrom "$T/trunc.bin" --memload "$ML" > "$T/b3.out" 2>&1
    ck   "B3  a truncated payload is refused, not reported" 1 "$?"
    ckin "B3b and it says TRUNCATED" "TRUNCATED" "$T/b3.out"

    cp "$TOOL" "$T/m1.py"
    sed -i "s/'decompressed': 2953660/'decompressed': 2953661/" "$T/m1.py"
    "$PY" "$T/m1.py" check --nfjrom "$NF" --memload "$ML" > "$T/m1.out" 2>&1
    ck   "M1  R1's expectation moved: refuses" 2 "$?"
    ckin "M1b and it is R1"    "FAIL  R1" "$T/m1.out"
    ckin "M1c and nothing is reported" "Nothing is reported about this image" "$T/m1.out"

    cp "$TOOL" "$T/m2.py"
    sed -i 's/^def sum16(b):/def sum16(b):\n    return 0/' "$T/m2.py"
    "$PY" "$T/m2.py" check --nfjrom "$NF" --memload "$ML" > "$T/m2.out" 2>&1
    ck   "M2  sum16 forced to 0: refuses" 2 "$?"
    ckin "M2b and it is R2" "FAIL  R2" "$T/m2.out"
else
    # ONE skip line standing for eighteen cases, and the label is the one
    # `tools/ci-expected.tsv` carries. The first version printed eighteen
    # separate lines with eighteen labels: the census reported every one of
    # them as an UNEXPECTED-SKIP and then a CENSUS-MISMATCH, which is that
    # gate working -- a skip LINE is not a skipped CASE, and the table owns
    # the arithmetic.
    sk "the GPL drop" \
       "$DROP absent -- 18 cases (S3d, B1-B1h, B2, B3, B3b, M1-M1c, M2, M2b); the drop's nfjrom, memload-full and vmlinux_img are someone else's property and cannot be committed"
fi

echo
if [ "$fail" -eq 0 ]; then
    printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"; exit 0
fi
printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
exit 1
