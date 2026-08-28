#!/usr/bin/env bash
# Controls for tools/deskchan.py -- and mutations that must break them.
#
# `deskchan` decides one thing that a bench session will be planned around:
# whether a mark that did not appear means the code never reached it or the
# instrument never carried it.  So the cases below are all about the second
# half -- an instrument that cannot be shown to carry anything is not evidence
# of anything.
#
#   D1  the selftest passes: the CBUS THR and LSR are where the redirect
#       points, and an unpolled first write is lost while a polled one is not
#   D2  END TO END on a hand-built image with no vendor material in it: a
#       twelve-instruction payload loaded at physical 0 and entered through the
#       -bios stub prints a string, and deskchan reads it back.  This is the
#       case that says the loader path, the entry stub and the trace parser all
#       work, on a machine with no GPL drop on it
#   D3  --nop-cop3 rewrites exactly the opcode-0x13 words in range and names
#       their addresses; an image with none of them makes C3 refuse
#   D4  --redirect-uart without --vmlinux refuses rather than guessing a window
#   D5  the exit contract: no subcommand 3, unknown subcommand 3, run without
#       --flat 3
#   M1  CBUS_THR moved one register along; the selftest must go red
#   M3  the trace parser made to return nothing; D2's reach must collapse
#
# qemu-system-mips is required for D1/D2/D3 and they SKIP without it -- and the
# skip is a skip and not a pass, because every one of them is about what the
# emulator does.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$HERE/deskchan.py"
PY="${PYTHON:-python3}"
QEMU="${QEMU_MIPS:-qemu-system-mips}"
if [ -n "${TESTTMP:-}" ]; then T="$TESTTMP"; mkdir -p "$T"
else T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT; fi

pass=0; fail=0; skip=0
ck ()   { if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
          else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }
ckin () { if grep -qF -- "$2" "$3"; then printf '  ok     %-52s %s\n' "$1" "found"; pass=$((pass+1))
          else printf '  FAIL   %-52s %s not in output\n' "$1" "$2"; fail=$((fail+1)); fi }
sk ()   { printf '  skip   %-52s %s\n' "$1" "$2"; skip=$((skip+1)); }

[ -f "$TOOL" ] || { echo "no $TOOL"; exit 3; }
HAVE_QEMU=0; command -v "$QEMU" >/dev/null 2>&1 && HAVE_QEMU=1

echo "== tools/test-deskchan.sh"
echo

# ------------------------------------------------------------------ D5, D4
"$PY" "$TOOL" >/dev/null 2>&1;                  ck "D5  no subcommand" 3 "$?"
"$PY" "$TOOL" frobnicate >/dev/null 2>&1;       ck "D5b unknown subcommand" 3 "$?"
"$PY" "$TOOL" run --label x --work "$T" >/dev/null 2>&1; ck "D5c run without --flat" 3 "$?"

# a flat image that writes "RLXFW-D2-OK" through the CBUS UART, polling LSR,
# then loops.  Built here so this case needs no drop and no cross toolchain.
"$PY" - "$T/d2.bin" <<'PYEOF'
import struct, sys
def lui(rt, i):      return 0x3C000000 | (rt << 16) | (i & 0xFFFF)
def ori(rt, rs, i):  return 0x34000000 | (rs << 21) | (rt << 16) | (i & 0xFFFF)
def lbu(rt, rs, o):  return 0x90000000 | (rs << 21) | (rt << 16) | (o & 0xFFFF)
def andi(rt, rs, i): return 0x30000000 | (rs << 21) | (rt << 16) | (i & 0xFFFF)
def beq(rs, rt, o):  return 0x10000000 | (rs << 21) | (rt << 16) | (o & 0xFFFF)
def addiu(rt, rs, i):return 0x24000000 | (rs << 21) | (rt << 16) | (i & 0xFFFF)
def sb(rt, rs, o):   return 0xA0000000 | (rs << 21) | (rt << 16) | (o & 0xFFFF)
def j(t):            return 0x08000000 | ((t >> 2) & 0x03FFFFFF)
T0, T1, T2, T4, T5 = 8, 9, 10, 12, 13
w = [lui(T0, 0xBF00), ori(T1, T0, 0x0900), ori(T2, T0, 0x0928)]
for ch in 'XRLXFW-D2-OK\r\n':          # X is eaten: an unpolled channel drops
    w += [lbu(T4, T2, 0), 0, andi(T4, T4, 0x20), beq(T4, 0, 0xFFFC), 0,
          addiu(T5, 0, ord(ch)), sb(T5, T1, 0)]
here = 0x80000000 + len(w) * 4
w += [j(here & 0x0FFFFFFF), 0]
open(sys.argv[1], 'wb').write(b''.join(struct.pack('>I', x) for x in w))
PYEOF

if [ "$HAVE_QEMU" = 1 ]; then
    "$PY" "$TOOL" selftest --work "$T" --seconds 8 > "$T/self.out" 2>&1
    ck   "D1  selftest exit" 0 "$?"
    ckin "D1b C0 the unpolled first write is lost" "ok    C0" "$T/self.out"
    ckin "D1c C1 the THR address"                  "ok    C1" "$T/self.out"
    ckin "D1d C2 the LSR address and bit"          "ok    C2" "$T/self.out"

    "$PY" "$TOOL" run --flat "$T/d2.bin" --entry 0x80000000 --label d2 \
          --work "$T" --seconds 10 > "$T/d2.out" 2>&1
    ck   "D2  a hand-built image runs and speaks: exit" 0 "$?"
    ckin "D2b and the string comes back"    "RLXFW-D2-OK" "$T/d2.out"
    ckin "D2c and the reach is reported"    "of them in KSEG0" "$T/d2.out"

    # D3 -- four opcode-0x13 words planted in [0x80002200, 0x80002400)
    "$PY" - "$T/cop3.bin" <<'PYEOF'
import struct, sys
n = 0x2400 // 4
w = [0] * n
for i, off in enumerate((0x2210, 0x2220, 0x2230, 0x2240)):
    w[off // 4] = 0x4C880000 | (i << 11)
w[0] = 0x08000000 | ((0x80002400 >> 2) & 0x03FFFFFF)   # j past the words
open(sys.argv[1], 'wb').write(b''.join(struct.pack('>I', x) for x in w))
PYEOF
    "$PY" "$TOOL" run --flat "$T/cop3.bin" --entry 0x80000000 --label cop3 \
          --work "$T" --seconds 8 --nop-cop3 > "$T/c3.out" 2>&1
    ckin "D3  C3 finds exactly the four planted words" "4 word(s) -> nop" "$T/c3.out"
    ckin "D3b and names one of them"                   "0x80002210" "$T/c3.out"

    "$PY" "$TOOL" run --flat "$T/d2.bin" --entry 0x80000000 --label nocop3 \
          --work "$T" --seconds 8 --nop-cop3 > "$T/c3b.out" 2>&1
    ck   "D3c an image with no COP3 word in range: refuses" 2 "$?"
    ckin "D3d and it is C3"                                 "FAIL  C3" "$T/c3b.out"
else
    sk "D1  selftest"                      "no $QEMU"
    sk "D1b C0"                            "no $QEMU"
    sk "D1c C1"                            "no $QEMU"
    sk "D1d C2"                            "no $QEMU"
    sk "D2  hand-built image"              "no $QEMU"
    sk "D2b string"                        "no $QEMU"
    sk "D2c reach"                         "no $QEMU"
    sk "D3  C3 four words"                 "no $QEMU"
    sk "D3b address"                       "no $QEMU"
    sk "D3c refusal"                       "no $QEMU"
    sk "D3d C3 named"                      "no $QEMU"
fi

"$PY" "$TOOL" run --flat "$T/d2.bin" --entry 0x80000000 --label d4 \
      --work "$T" --seconds 5 --redirect-uart > "$T/d4.out" 2>&1
ck   "D4  --redirect-uart with no --vmlinux refuses" 3 "$?"
ckin "D4b and says why"  "patch window" "$T/d4.out"

# ------------------------------------------------------------------ mutations
mut () {
    cp "$TOOL" "$T/mut.py"; sed -i "$2" "$T/mut.py"
    if cmp -s "$TOOL" "$T/mut.py"; then
        echo "  FAIL   mutation $1 changed nothing"; fail=$((fail+1)); return 1; fi
    return 0
}

if [ "$HAVE_QEMU" = 1 ]; then
    if mut M1 's/^CBUS_THR, CBUS_LSR = 0xBF000900, 0xBF000928/CBUS_THR, CBUS_LSR = 0xBF000908, 0xBF000928/'; then
        "$PY" "$T/mut.py" selftest --work "$T/m1" --seconds 8 > "$T/m1.out" 2>&1
        ck   "M1  CBUS_THR moved one register: selftest refuses" 2 "$?"
    fi
    if mut M3 's/^    seen, order, blocks, cur = set(), \[\], \[\], \[\]/    seen, order, blocks, cur = set(), [], [], []\n    return [], []/'; then
        "$PY" "$T/mut.py" run --flat "$T/d2.bin" --entry 0x80000000 \
              --label m3 --work "$T" --seconds 8 > "$T/m3.out" 2>&1
        ckin "M3  a blind trace parser reports zero reach" "of them in KSEG0           0" "$T/m3.out"
    fi
else
    sk "M1  CBUS_THR moved" "no $QEMU"
    sk "M3  blind trace parser" "no $QEMU"
fi

echo
if [ "$fail" -eq 0 ]; then
    printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"; exit 0
fi
printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
exit 1
