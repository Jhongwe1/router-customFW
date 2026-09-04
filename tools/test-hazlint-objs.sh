#!/usr/bin/env bash
# Controls for tools/hazlint-objs.py -- and mutations that must break them.
#
# `hazlint-objs` runs eleven controls of its own before it reports.  This file
# exists because a control that lives inside the tool it checks passes whenever
# the tool is broken in a way that also breaks the control.  So everything
# below either FEEDS the tool a tree whose answer is known, or MUTATES the tool
# and demands that one named control goes red.
#
#   A1  a tree whose bsp/ objects are unreachable by plain `find` is swept
#       anyway -- Q1 green, and the six extra objects are named
#   A2  the same tree with the bsp symlink REMOVED -- Q1 red, exit 2, and
#       nothing is reported about the tree.  This is notes/kernel-build.md §10
#       landing on P2, and it is the case P2 was written wrong for
#   A3  a planted load-use hazard in one object is found and the object named
#   A4  an object with no loads is retried with --allow-zero-loads, reported
#       as zero-loads, and does not sink the run
#   A5  a data-only object is skipped as NO CODE and Q7b confirms it against
#       the section headers rather than against hazlint's prose
#   A6  the --out artefact carries the control block, not just the table
#   A7  --expect-vmlinux that does not match refuses
#   A8  the exit contract: no --tree 3, absent tree 3, clean tree 0,
#       violation 1, failed control 2
#   M1  `find -L` -> `find` in the enumerator; Q1 must go red
#   M2  a stub -march=5281 that carries no hazard; the tool must refuse rather than
#       report a 0 it cannot show a 1 against
#   M3  make the stub assembler emit the SAFE object for both Q3 and Q4;
#       Q3 must go red
#   M4  exec_section_bytes() forced to 0; Q7b must go red on a real object
#   M5  the violation count parsed as always 0; A3 must stop finding it
#
# The tree is synthetic and so are the objects: this suite builds 32-bit
# big-endian MIPS ET_REL files itself, so it needs no cross toolchain and runs
# on a stock runner.  The stub `rsdk-linux-as` and `rsdk-linux-gcc` are the
# same shape `test-isa-probe.sh` and `test-tc-smoke.sh` already use.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$HERE/hazlint-objs.py"
HAZ="$HERE/hazlint"
PY="${PYTHON:-python3}"
# TESTTMP keeps the fixtures for inspection; without it they go to mktemp and
# are removed.  A suite whose fixtures cannot be looked at is a suite whose
# failures have to be reproduced by guesswork.
if [ -n "${TESTTMP:-}" ]; then T="$TESTTMP"; mkdir -p "$T"
else T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT; fi

pass=0; fail=0; skip=0
ck () {
    if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}
ckin () {   # label needle haystack-file
    if grep -qF -- "$2" "$3"; then printf '  ok     %-52s %s\n' "$1" "found"; pass=$((pass+1))
    else printf '  FAIL   %-52s %s not in output\n' "$1" "$2"; fail=$((fail+1)); fi
}
cknot () {
    if grep -qF -- "$2" "$3"; then printf '  FAIL   %-52s %s present\n' "$1" "$2"; fail=$((fail+1))
    else printf '  ok     %-52s %s\n' "$1" "absent"; pass=$((pass+1)); fi
}
sk () { printf '  skip   %-52s %s\n' "$1" "$2"; skip=$((skip+1)); }

[ -f "$TOOL" ] || { echo "no $TOOL"; exit 3; }

# --------------------------------------------------------------------- fixtures
cat > "$T/mkobj.py" <<'PYEOF'
"""Write a 32-bit big-endian MIPS ET_REL object with one .text section.

Enough of an ELF for hazlint to read: header, .text (PROGBITS|ALLOC|EXECINSTR
or ALLOC only), .shstrtab, .symtab, .strtab with one STT_FUNC symbol.  Nothing
here is a general ELF writer; it exists so this suite needs no toolchain.
"""
import struct, sys

def build(path, words, exec_flag=True, symname='f', symsize=None):
    text = b''.join(struct.pack('>I', w) for w in words)
    shstr = b'\0.text\0.shstrtab\0.symtab\0.strtab\0'
    names = {'.text': 1, '.shstrtab': 7, '.symtab': 17, '.strtab': 25}
    strtab = b'\0' + symname.encode() + b'\0'
    nsym = 2
    sym = b'\0' * 16
    sym += struct.pack('>IIIBBH', 1, 0, symsize if symsize is not None else len(text),
                       (1 << 4) | 2, 0, 1)          # GLOBAL STT_FUNC, shndx 1
    ehsize, shentsize = 52, 40
    off = ehsize
    o_text = off; off += len(text)
    o_shstr = off; off += len(shstr)
    o_sym = off; off += len(sym)
    o_str = off; off += len(strtab)
    o_sh = (off + 3) & ~3
    flags = 0x6 if exec_flag else 0x2               # ALLOC|EXECINSTR or ALLOC
    sh = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
          (names['.text'], 1, flags, 0, o_text, len(text), 0, 0, 4, 0),
          (names['.shstrtab'], 3, 0, 0, o_shstr, len(shstr), 0, 0, 1, 0),
          (names['.symtab'], 2, 0, 0, o_sym, len(sym), 4, 1, 4, 16),
          (names['.strtab'], 3, 0, 0, o_str, len(strtab), 0, 0, 1, 0)]
    b = bytearray()
    b += b'\x7fELF\x01\x02\x01' + b'\0' * 9
    b += struct.pack('>HHIIIIIHHHHHH', 1, 8, 1, 0, 0, o_sh, 0,
                     ehsize, 0, 0, shentsize, len(sh), 2)
    b += text + shstr + sym + strtab
    b += b'\0' * (o_sh - len(b))
    for s in sh:
        b += struct.pack('>10I', *s)
    with open(path + '.tmp', 'wb') as fh:
        fh.write(bytes(b))
    import os
    os.replace(path + '.tmp', path)

LW_T0   = 0x8C880000        # lw   t0,0(a0)
ADDU    = 0x01084821        # addu t1,t0,t0     <- reads t0
NOP     = 0x00000000
JR_RA   = 0x03E00008
ORI     = 0x34090001        # ori  t1,zero,1    (no load, no use)

HAZARD = [LW_T0, ADDU, JR_RA, NOP]
SAFE   = [LW_T0, NOP, ADDU, JR_RA, NOP]
NOLOAD = [ORI, ORI, JR_RA, NOP]

if __name__ == '__main__':
    what, path = sys.argv[1], sys.argv[2]
    if what == 'hazard':  build(path, HAZARD)
    elif what == 'safe':  build(path, SAFE)
    elif what == 'noload': build(path, NOLOAD)
    elif what == 'nocode': build(path, [], exec_flag=False)
    elif what == 'allocnotexec': build(path, SAFE, exec_flag=False)
    else: raise SystemExit('unknown %r' % what)
PYEOF

# a staged tree: top/linux-2.6.30/arch/rlx/{kernel,lib}, plus arch/rlx/bsp as a
# symlink into top/boards/rtl8196e/bsp -- the exact shape rlxfw-kbuild.sh makes
mktree () {   # mktree <dir> <with-bsp-symlink 0|1>
    local D="$1" B="$2"
    rm -rf "$D"; mkdir -p "$D/linux-2.6.30/arch/rlx/kernel" \
                          "$D/linux-2.6.30/arch/rlx/lib" \
                          "$D/boards/rtl8196e/bsp" "$D/toolchain/rsdk/bin"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/kernel/entry.o"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/kernel/genex.o"
    "$PY" "$T/mkobj.py" noload "$D/linux-2.6.30/arch/rlx/kernel/head.o"
    "$PY" "$T/mkobj.py" nocode "$D/linux-2.6.30/arch/rlx/kernel/init_task.o"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/lib/strlen_user.o"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/lib/strnlen_user.o"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/lib/strncpy_user.o"
    "$PY" "$T/mkobj.py" safe   "$D/linux-2.6.30/arch/rlx/kernel/scall32-o32.o"
    "$PY" "$T/mkobj.py" safe   "$D/boards/rtl8196e/bsp/setup.o"
    "$PY" "$T/mkobj.py" safe   "$D/boards/rtl8196e/bsp/prom.o"
    ln -sf boards/rtl8196e "$D/target"
    if [ "$B" = 1 ]; then
        ln -sf ../../../target/bsp "$D/linux-2.6.30/arch/rlx/bsp"
    fi
    # kbuild .cmd files, so Q5 has a command line to reuse
    for f in kernel/entry kernel/genex kernel/scall32-o32 \
             lib/strlen_user lib/strnlen_user lib/strncpy_user; do
        d="$(dirname "$f")"; b="$(basename "$f")"
        printf 'cmd_arch/rlx/%s.o := rsdk-linux-gcc -c -o arch/rlx/%s.o arch/rlx/%s.S\n' \
               "$f" "$f" "$f" > "$D/linux-2.6.30/arch/rlx/$d/.$b.o.cmd"
    done
    # stub toolchain: `as` picks its answer from the source it is handed,
    # `gcc` from the -o path, so Q3/Q4/Q5 each get the object their claim needs
    # The stub keys on the OUTPUT name, not on the source text: hazlint-objs'
    # Q3 fixture ends in `jr $31 / nop`, so a stub that looked for the string
    # `nop` answered `safe` to both questions and Q3 failed for a reason that
    # had nothing to do with the tool.  量, first run of this suite.
    cat > "$D/toolchain/rsdk/bin/rsdk-linux-as" <<STUB
#!/usr/bin/env bash
out=""
while [ \$# -gt 0 ]; do
  case "\$1" in -o) out="\$2"; shift 2;; *) shift;; esac
done
case "\$out" in *q3.o) k=hazard;; *) k=safe;; esac
$PY "$T/mkobj.py" \$k "\$out"
STUB
    cat > "$D/toolchain/rsdk/bin/rsdk-linux-gcc" <<STUB
#!/usr/bin/env bash
out=""
while [ \$# -gt 0 ]; do
  case "\$1" in -o) out="\$2"; shift 2;; *) shift;; esac
done
case "\$out" in
  *entry*)          n=5;;
  *genex*)          n=1;;
  *strlen_user*)    n=2;;
  *strnlen_user*)   n=2;;
  *strncpy_user*)   n=1;;
  *)                n=0;;
esac
$PY - "\$out" "\$n" <<'PY2'
import sys, importlib.util
spec = importlib.util.spec_from_file_location('m', '$T/mkobj.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
n = int(sys.argv[2])
w = []
for _ in range(n):
    w += [m.LW_T0, m.ADDU]
w += [m.LW_T0, m.NOP, m.ADDU, m.JR_RA, m.NOP]
m.build(sys.argv[1], w)
PY2
STUB
    chmod +x "$D/toolchain/rsdk/bin/rsdk-linux-as" \
             "$D/toolchain/rsdk/bin/rsdk-linux-gcc"
}

run () {   # run <tree> [extra args...]; sets RC and writes $T/out
    local D="$1"; shift
    "$PY" "$TOOL" --tree "$D" --hazlint "$1" --jobs 4 "${@:2}" > "$T/out" 2>&1
    RC=$?
}

echo "== tools/test-hazlint-objs.sh"
echo

# ------------------------------------------------------------------- A1, A8
mktree "$T/tree" 1
run "$T/tree" "$HAZ" --no-arch-control
ck  "A1  a tree with bsp reachable only through -L: exit" 0 "$RC"
ckin "A1b Q1 green and names the six bsp objects" "bsp/setup.o" "$T/out"
ckin "A1c the sweep total counts the bsp objects"  "bsp/setup.o" "$T/out"

# ------------------------------------------------------------------- A2, the §10 case
mktree "$T/nobsp" 0
run "$T/nobsp" "$HAZ" --no-arch-control
ck  "A2  bsp symlink removed: the tool REFUSES" 2 "$RC"
ckin "A2b and it names the control" "Q1" "$T/out"
cknot "A2c and reports nothing about the tree" "TOTAL (leaf objects only)" "$T/out"

# ------------------------------------------------------------------- A3
mktree "$T/bad" 1
"$PY" "$T/mkobj.py" hazard "$T/bad/linux-2.6.30/arch/rlx/kernel/traps.o"
run "$T/bad" "$HAZ" --no-arch-control
ck  "A3  a planted hazard is found: exit" 1 "$RC"
ckin "A3b and the object is named" "kernel/traps.o" "$T/out"

# ------------------------------------------------------------------- A4, A5
run "$T/tree" "$HAZ" --no-arch-control
ckin "A4  an object with no loads is reported zero-loads" "zero-loads" "$T/out"
ckin "A5  a data-only object is skipped as NO CODE" "NO CODE" "$T/out"
ckin "A5b Q7b confirms it against the section headers" "Q7b" "$T/out"

# ------------------------------------------------------------------- A6
run "$T/tree" "$HAZ" --no-arch-control --out "$T/art.txt"
ckin "A6  the --out artefact carries the control block" "  ok    Q1 " "$T/art.txt"
ckin "A6b and the table"                                "TOTAL (leaf" "$T/art.txt"

# ------------------------------------------------------------------- A7
run "$T/tree" "$HAZ" --no-arch-control --expect-vmlinux deadbeefdeadbeef
ck  "A7  --expect-vmlinux mismatch refuses" 2 "$RC"

# ------------------------------------------------------------------- A8
"$PY" "$TOOL" > "$T/out" 2>&1; ck "A8  no --tree" 3 "$?"
"$PY" "$TOOL" --tree "$T/nowhere" > "$T/out" 2>&1; ck "A8b absent tree" 3 "$?"

# ------------------------------------------------------------------- A9 (Q5)
run "$T/tree" "$HAZ"
ck  "A9  Q5 runs against the stub toolchain: exit" 0 "$RC"
ckin "A9b and reads 11, which is TC-21's number" "= 11 (TC-21 says 11)" "$T/out"

# ------------------------------------------------------- A10..A14  HAZ-1, --also
# The population is a claim.  Before --also existed, a sweep of arch/rlx over a
# tree carrying a driver under drivers/ reported 0 violations and never opened
# it -- which is what HAZ-1 records and what A11 pins by making that driver a
# HAZARD.  A10 is the negative half: without --also the hazard is invisible and
# the tool exits 0.
mktree "$T/drv" 1
mkdir -p "$T/drv/linux-2.6.30/drivers/clocksource"
"$PY" "$T/mkobj.py" hazard "$T/drv/linux-2.6.30/drivers/clocksource/rtl819x-timer.o"

run "$T/drv" "$HAZ" --no-arch-control
ck   "A10 a driver hazard under drivers/ is INVISIBLE without --also" 0 "$RC"
cknot "A10b and the object is not in the sweep" "rtl819x-timer.o" "$T/out"
ckin "A10c Q1b says the population is arch/rlx alone" "no --also given" "$T/out"

run "$T/drv" "$HAZ" --no-arch-control --also drivers/clocksource
ck   "A11 --also drivers/clocksource: the same hazard is FOUND" 1 "$RC"
ckin "A11b and the object is named" "rtl819x-timer.o" "$T/out"
ckin "A11c and the header says what was swept" "population arch/rlx + drivers/clocksource" "$T/out"

# A12 -- the positive control.  A --also that adds nothing must refuse, not
# sweep past: a green run over a population that silently excludes what the
# caller named is the state --also exists to remove.
run "$T/drv" "$HAZ" --no-arch-control --also drivers/spi
ck   "A12 --also naming a directory that is not there: REFUSES" 2 "$RC"
ckin "A12b and it is Q1b" "FAIL  Q1b:drivers/spi" "$T/out"
cknot "A12c and reports nothing about the tree" "TOTAL (leaf objects only)" "$T/out"

# A13 -- a directory that EXISTS and holds no object is the same refusal, and
# it is a different code path from A12 (isdir true, added zero).
mkdir -p "$T/drv/linux-2.6.30/drivers/empty"
run "$T/drv" "$HAZ" --no-arch-control --also drivers/empty
ck   "A13 --also on an existing but empty directory: REFUSES" 2 "$RC"
ckin "A13b and it is Q1b" "FAIL  Q1b:drivers/empty" "$T/out"

# A14 -- and naming arch/rlx again adds nothing, so it refuses too.  This is
# the case that keeps Q1b from being satisfiable by a redundant argument.
run "$T/tree" "$HAZ" --no-arch-control --also arch/rlx
ck   "A14 --also arch/rlx (already swept) adds nothing: REFUSES" 2 "$RC"
ckin "A14b and it is Q1b" "FAIL  Q1b:arch/rlx" "$T/out"

# ---------------------------------------------------------------- mutations
mut () {   # mut <name> <sed-expr>
    cp "$TOOL" "$T/mut.py"
    sed -i "$2" "$T/mut.py"
    if cmp -s "$TOOL" "$T/mut.py"; then
        echo "  FAIL   mutation $1 changed nothing"; fail=$((fail+1)); return 1
    fi
    return 0
}
mrun () { "$PY" "$T/mut.py" --tree "$1" --hazlint "$HAZ" --jobs 4 "${@:2}" \
              > "$T/mout" 2>&1; MRC=$?; }

if mut M1 's/cmd = \[.find.\]/cmd = ["find"]; follow = False/'; then
    mrun "$T/tree" --no-arch-control
    ck  "M1  find -L becomes find: the tool refuses"           2 "$MRC"
    ckin "M1b and it is Q1 that says so" "FAIL  Q1" "$T/mout"
fi

# M2 -- Q5's control is what turns "0 violations" into a measurement, so the
# mutation is the one that takes the 11 away.  The first version of this case
# edited TC21_EXPECT to `{} or {...}`, which is the SAME dict in Python and
# therefore not a mutation at all: it passed, and a case that cannot fail was
# about to certify the control that certifies everything else.
cp "$T/tree/toolchain/rsdk/bin/rsdk-linux-gcc" "$T/gcc.orig"
cat > "$T/tree/toolchain/rsdk/bin/rsdk-linux-gcc" <<STUB
#!/usr/bin/env bash
out=""
while [ \$# -gt 0 ]; do case "\$1" in -o) out="\$2"; shift 2;; *) shift;; esac; done
$PY "$T/mkobj.py" safe "\$out"
STUB
chmod +x "$T/tree/toolchain/rsdk/bin/rsdk-linux-gcc"
run "$T/tree" "$HAZ"
ck  "M2  a -march=5281 that carries NO hazard: refuses"      2 "$RC"
ckin "M2b and it is Q5" "FAIL  Q5" "$T/out"
cp "$T/gcc.orig" "$T/tree/toolchain/rsdk/bin/rsdk-linux-gcc"
chmod +x "$T/tree/toolchain/rsdk/bin/rsdk-linux-gcc"

cp "$T/tree/toolchain/rsdk/bin/rsdk-linux-as" "$T/as.orig"
cat > "$T/tree/toolchain/rsdk/bin/rsdk-linux-as" <<STUB
#!/usr/bin/env bash
out=""
while [ \$# -gt 0 ]; do case "\$1" in -o) out="\$2"; shift 2;; *) shift;; esac; done
$PY "$T/mkobj.py" safe "\$out"
STUB
chmod +x "$T/tree/toolchain/rsdk/bin/rsdk-linux-as"
run "$T/tree" "$HAZ" --no-arch-control
ck  "M3  an assembler that cannot produce a hazard: refuses" 2 "$RC"
ckin "M3b and it is Q3" "FAIL  Q3" "$T/out"
cp "$T/as.orig" "$T/tree/toolchain/rsdk/bin/rsdk-linux-as"
chmod +x "$T/tree/toolchain/rsdk/bin/rsdk-linux-as"

if mut M4 's/^def exec_section_bytes(path):/def exec_section_bytes(path):\n    return 0/'; then
    mrun "$T/tree" --no-arch-control
    ck  "M4  exec_section_bytes() forced to 0: refuses"      2 "$MRC"
    ckin "M4b and it is Q7b" "FAIL  Q7b" "$T/mout"
fi

if mut M5 's/            r.viol = int(m.group(1)); continue/            r.viol = 0; continue/'; then
    mrun "$T/bad" --no-arch-control
    ck  "M5  the violation count blinded: Q3 catches it" 2 "$MRC"
    ckin "M5b and it is Q3" "FAIL  Q3" "$T/mout"
fi

echo
if [ "$fail" -eq 0 ]; then
    printf 'RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped\n' "$pass" "$skip"
    exit 0
fi
printf 'RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped\n' "$pass" "$fail" "$skip"
exit 1
