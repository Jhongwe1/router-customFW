#!/usr/bin/env bash
# Which instructions does the vendor's own assembler accept for each Lexra core?
#
# Realtek's rsdk ships a patched binutils whose opcode table names six Lexra
# architectures -- the same six that `arch/rlx/Kconfig` names. That table is a
# machine description written by the people who integrated the core, so
# assembling one instruction at a time against each `-march` is a direct read of
# it. It is the only per-core ISA statement in this project that does not come
# from a datasheet or from guessing at a binary.
#
# What it is NOT: a statement about silicon. The table says what Realtek's
# toolchain believes; `boards/*/config.in` says what Realtek's kernel believes
# about one SoC; and those two disagree about `ll`/`sc` on `rlx4181`. Both are
# recorded in `notes/vendor-kernel-isa.md` §6. Only `R1a` measures the die.
#
# Two controls run before anything is printed, and a failure of either refuses
# the report rather than annotating it:
#
#   POS  `addu` must be accepted in EVERY column. A column that fails here did
#        not assemble for a reason that has nothing to do with the row being
#        probed -- a missing runtime library, a bad -march spelling -- and every
#        `.` below it would be a false negative.
#   NEG  `daddu` must be rejected in EVERY column. It is a 64-bit instruction
#        and no 32-bit architecture may take it. If it is accepted, `-march` is
#        being ignored and the whole table is one column repeated.
#
# And the failure mode this repository keeps meeting: **a tool that cannot see
# still reports.** With no assembler this exits 3 and prints nothing that could
# be read as a table of absences. `.` here always means "the assembler was
# asked and said no", never "nobody asked".
#
# Usage
#     isa-probe.sh [--as PATH] [--archs "a b c"] [--quiet]
#
#     --as      the assembler. Default: search $FWRE_WORK/rebuild/src-vendor
#               for rsdk-linux-as, newest rsdk first.
#     --archs   override the -march list.
#     --quiet   print only the table body, for diffing.
#
# Exit
#     0  table printed, both controls held
#     2  a control failed -- nothing certified
#     3  no assembler found, or one that will not run
set -o nounset

AS=""
ARCHS="lx4180 rlx4181 rlx5181 lx5280 rlx5281 rlx4281 mips1 mips2"
QUIET=0

while [ $# -gt 0 ]; do
    case "$1" in
        --as)     AS="$2"; shift 2 ;;
        --archs)  ARCHS="$2"; shift 2 ;;
        --quiet)  QUIET=1; shift ;;
        *) echo "isa-probe.sh: unknown option $1" >&2; exit 3 ;;
    esac
done

SMOKE="$(mktemp -d)"
printf '\t.set noreorder\n\taddu $2,$3,$4\n' > "$SMOKE/s.s"

if [ -z "$AS" ]; then
    # Pick the first candidate that can actually assemble, not the first that
    # exists. 量 2026-08-27: rsdk-1.5.5's `as` is present and executable and
    # dies on a missing 32-bit libz.so.1, so a search that stopped at `-x`
    # selected a binary that rejects every instruction -- which the POS control
    # then reported as eight columns of `.`. The control was right and the
    # search was wrong; both are fixed, and the control stays.
    ROOT="${FWRE_WORK:-/home/key/fwre-work}/rebuild/src-vendor"
    for cand in "$ROOT"/*/toolchain/*/bin/rsdk-linux-as \
                "$ROOT"/*/*/toolchain/*/bin/rsdk-linux-as; do
        [ -x "$cand" ] || continue
        if "$cand" -march=mips1 "$SMOKE/s.s" -o "$SMOKE/s.o" 2>/dev/null; then
            AS="$cand"; break
        fi
    done
fi
rm -rf "$SMOKE"

if [ -z "$AS" ] || [ ! -x "$AS" ]; then
    echo "isa-probe.sh: SKIPPED -- no rsdk assembler found." >&2
    echo "  Looked under \$FWRE_WORK/rebuild/src-vendor/*/toolchain/*/bin/." >&2
    echo "  The vendor toolchains are part of the GPL drops and are not in a" >&2
    echo "  clone. Pass --as PATH to point at one." >&2
    echo "  Nothing was probed, so nothing is reported: an empty table and a" >&2
    echo "  table of rejections are different answers." >&2
    exit 3
fi

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

# Returns 0 if the assembler took the instruction for that -march.
try () { # arch insn
    printf '\t.set noreorder\n\t%s\n' "$2" > "$T/i.s"
    "$AS" -march="$1" "$T/i.s" -o "$T/i.o" 2>/dev/null
}

row () { # label insn
    printf "%-12s" "$1"
    for a in $ARCHS; do
        if try "$a" "$2"; then printf " %-9s" "y"; else printf " %-9s" "."; fi
    done
    echo
}

# --- controls, before the table ------------------------------------------
bad_pos=""
bad_neg=""
for a in $ARCHS; do
    try "$a" 'addu $2,$3,$4'  || bad_pos="$bad_pos $a"
    try "$a" 'daddu $2,$3,$4' && bad_neg="$bad_neg $a"
done

if [ -n "$bad_pos" ] || [ -n "$bad_neg" ]; then
    echo "isa-probe.sh: REFUSED -- a control failed, so no row below it would mean anything." >&2
    [ -n "$bad_pos" ] && echo "  POS addu rejected by:$bad_pos   (that column cannot assemble at all)" >&2
    [ -n "$bad_neg" ] && echo "  NEG daddu ACCEPTED by:$bad_neg   (-march is being ignored)" >&2
    exit 2
fi

if [ "$QUIET" -eq 0 ]; then
    echo "assembler   $AS"
    "$AS" --version 2>/dev/null | head -1 | sed 's/^/version     /'
    echo "controls    POS addu accepted in all columns; NEG daddu rejected in all columns"
    echo
    printf "%-12s" "instr"
    for a in $ARCHS; do printf " %-9s" "$a"; done
    echo
    printf "%-12s" "-----"
    for a in $ARCHS; do printf " %-9s" "---------"; done
    echo
fi

row "lwl"   'lwl $2,0($4)'
row "lwr"   'lwr $2,3($4)'
row "swl"   'swl $2,0($4)'
row "swr"   'swr $2,3($4)'
row "ll"    'll $2,0($4)'
row "sc"    'sc $2,0($4)'
row "sync"  'sync'
row "cache" 'cache 0x11,0($4)'
row "pref"  'pref 0,0($4)'
row "mfc3"  'mfc3 $2,$0'
row "mtc3"  'mtc3 $2,$0'
row "lwc3"  'lwc3 $2,0($4)'
row "movz"  'movz $2,$3,$4'
row "movn"  'movn $2,$3,$4'
row "beql"  'beql $2,$3,.'
row "madd"  'madd $2,$3'
row "rdhwr" 'rdhwr $2,$29'
row "mfc1"  'mfc1 $2,$f0'
row "lwc1"  'lwc1 $f0,0($4)'
row "jalx"  'jalx 0x400000'
exit 0
