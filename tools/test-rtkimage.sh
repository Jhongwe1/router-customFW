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
#   P1-P6  `build`'s record (TC-i): its digests equal a recomputation of the
#       files it names, one flipped byte breaks that comparison, and no record
#       is written for a make that left no nfjrom or changed its input
#   T, V, W, C, E  `build` runs make through vendor-tripwire.sh: one case per
#       exit status it can give, its verdict line read and never assumed, and
#       the argv, stdin, cwd and existence check that allow no other way
#   P7  `build` with a missing --vmlinux refuses (3), not a traceback
#
# S1-S4, P1-P7 and T/V/W/C/E run anywhere.  B1-B3 and M1-M2 need the GPL drop under
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

# ---------------------------------------------------------------------- P1-P7
# TC-i, 2026-09-23.  `build` writes rtkimage-record.tsv: which vmlinux became
# which nfjrom, by full sha256.  A card pins the nfjrom and the build manifest
# records the vmlinux and the gate verdicts; this record is the only link.
#
# 🔄 The same day `build` began running make THROUGH vendor-tripwire.sh, as
# rlxfw-kbuild.sh does.  One case per exit status the tripwire can give: 0 is
# P1h, 1 is P6/P6b (tolerated) and T1b (not), and 2, 5, 4 and 3 are T2, T5, T4
# and T3a/T3b.  V1-V3 are its verdict line read rather than assumed; W, W2, C
# and E are what keep make from being spawned any other way.
#
# cmd_build runs IN PROCESS against a fake cell and a fake drop, with
# subprocess.run replaced by a fake TRIPWIRE: it records what it was asked to
# spawn, plays make's part (writing the artefacts), and prints the verdict
# line each scenario asks for.  Neither the tripwire nor any vendor binary
# runs -- a real `build` executes the drop's lzma and cvimg -- so these run
# anywhere, and what they test is the bookkeeping: the record's digests must
# equal a recomputation of the files it NAMES, and no record may exist for a
# make the tripwire did not certify.
"$PY" - "$TOOL" "$T" > "$T/p.out" 2>&1 <<'PYEOF'
import contextlib, hashlib, importlib.util, io, os, sys, types
spec = importlib.util.spec_from_file_location('r', sys.argv[1])
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
T = sys.argv[2]
out = []
seen = []
CLEAN0 = 'VENDOR-TRIPWIRE: CLEAN  cmd-rc=0  6 tree(s) watched'

def sha(p):
    with open(p, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()

def write(p, b):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(b)

cell = os.path.join(T, 'pcell'); kcell = os.path.join(cell, 'linux-2.6.30')
write(os.path.join(kcell, 'include/linux/autoconf.h'), b'/* fake */\n')
write(os.path.join(kcell, '.config'), b'CONFIG_FAKE=y\n')
write(os.path.join(cell, '.config'), b'CONFIG_SDK_FAKE=y\n')
write(os.path.join(cell, 'toolchain/bin/rsdk-linux-gcc'), b'')
r.DROP = os.path.join(T, 'pdrop')
write(os.path.join(r.DROP, 'linux-2.6.30/rtkload/Makefile'), b'# fake\n')
vm = os.path.join(T, 'pvmlinux')
write(vm, b'\x7fELF a fake vmlinux ' + bytes(range(256)))

def fake_tripwire(make=True, make_rc=0, nfjrom=True, touch_input=False,
                  tail=b'', pre=b'', line=None, rc=None):
    """`bash vendor-tripwire.sh --quiet -- make -C <rtk>`, faked.

    line=None prints the CLEAN line for `make_rc` and rc=None takes the exit
    status the real tripwire would give it (0, or 1 when make failed); line=''
    prints no verdict line at all.  make=False is the tripwire refusing
    before the command runs.  The spawned command is found after `--` when
    there is one and taken whole when there is not, so a cmd_build that
    spawned make directly would still build -- and W alone would catch it.
    """
    if line is None:
        line = 'VENDOR-TRIPWIRE: CLEAN  cmd-rc=%d  6 tree(s) watched' % make_rc
    if rc is None:
        rc = 0 if make_rc == 0 else 1

    def run(argv, env=None, cwd=None, stdin=None, stdout=None, stderr=None):
        seen.append({'argv': list(argv), 'cwd': cwd, 'stdin': stdin})
        cmd = argv[argv.index('--') + 1:] if '--' in argv else list(argv)
        rtk = cmd[cmd.index('-C') + 1]
        if make:
            for f in ('vmlinux-stripped', 'vmlinux_img', 'memload-full', 'linux.bin'):
                write(os.path.join(rtk, f), f.encode())
            if nfjrom:
                with open(os.path.join(rtk, '..', 'vmlinux'), 'rb') as fh:
                    write(os.path.join(rtk, 'nfjrom'), b'NFJROM' + fh.read()[::-1])
            if touch_input:
                with open(os.path.join(rtk, '..', 'vmlinux'), 'ab') as fh:
                    fh.write(b'!')
            stdout.write(pre + b'Generate image successfully\n' + tail)
        if line:
            stdout.write(line.encode() + b'\n')
        return types.SimpleNamespace(returncode=rc)
    return run

def build(label, **kw):
    del seen[:]
    r.subprocess = types.SimpleNamespace(run=fake_tripwire(**kw), STDOUT=-2,
                                         DEVNULL=-3)
    # stderr is captured too: die() writes its refusal there, and this block's
    # own stderr is merged into the file the reader below parses -- an
    # uncaptured refusal became a stray line there, which the first version of
    # E turned into a phantom `ok`.
    buf, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = r.cmd_build({'cell': cell, 'vmlinux': vm, 'label': label,
                              'work': os.path.join(T, 'pwork'),
                              'kconfig': os.path.join(kcell, '.config'),
                              'sdkconfig': os.path.join(cell, '.config')})
    except SystemExit as e:
        rc = 'exit %s' % e.code
    return (rc, buf.getvalue() + err.getvalue(),
            os.path.join(T, 'pwork', label, r.RECORD_NAME))

def record(path):
    with open(path, encoding='utf-8') as fh:
        return [tuple(l.rstrip('\n').split('\t', 1)) for l in fh]

rc, txt, rp = build('ok')
first = [dict(s) for s in seen]
rows = record(rp) if os.path.isfile(rp) else []
rec = dict(rows)
out.append(('P1a build writes a record', '0 True', '%s %s' % (rc, os.path.isfile(rp))))
out.append(('P1h and it says the make was watched, CLEAN, cmd-rc=0', CLEAN0,
            rec.get('tripwire_verdict', '-')))
out.append(('P1b its first row is the format', "('rlxfw-rtkimage-record', '1')",
            repr(rows[0]) if rows else '-'))
out.append(('P1c vmlinux_sha256 == sha256 of the vmlinux it names', 'True',
            str(bool(rec) and rec['vmlinux_sha256'] == sha(rec['vmlinux']))))
out.append(('P1d and that is the file given, not only the copy', 'True',
            str(bool(rec) and rec['vmlinux'] == os.path.abspath(vm)
                and rec['vmlinux_sha256'] == sha(vm))))
out.append(('P1e nfjrom_sha256 == sha256 of the nfjrom it names', 'True',
            str(bool(rec) and rec['nfjrom_sha256'] == sha(rec['nfjrom']))))
out.append(('P1f both byte counts are the files\' sizes', 'True',
            str(bool(rec) and int(rec['vmlinux_bytes']) == os.path.getsize(vm)
                and int(rec['nfjrom_bytes']) == os.path.getsize(rec['nfjrom']))))
out.append(('P1g and the run says where the record is', '1',
            str(txt.count('record -> %s' % rp))))
out.append(('P2  no .tmp is left beside it', 'False', str(os.path.exists(rp + '.tmp'))))
# P3 -- the NEGATIVE control on P1c/P1e: the comparison they make can fail.
if rec:
    with open(rec['nfjrom'], 'r+b') as fh:
        b0 = fh.read(1); fh.seek(0); fh.write(bytes([b0[0] ^ 1]))
out.append(('P3  one flipped nfjrom byte breaks the comparison', 'False',
            str(bool(rec) and rec['nfjrom_sha256'] == sha(rec['nfjrom']))))
# P4 -- make "succeeds" and writes no nfjrom.  Same label as P1, so the record
# P1 left must be GONE rather than left standing beside a failed run.
rc, txt, rp = build('ok', nfjrom=False)
out.append(('P4  no nfjrom -> 1 and no record, not even the old one', '1 False',
            '%s %s' % (rc, os.path.exists(rp))))
out.append(('P4b and it says why', '1', str(txt.count('wrote no nfjrom'))))
rc, txt, rp = build('touched', touch_input=True)
out.append(('P5  make changed its input copy -> 1 and no record', '1 False',
            '%s %s' % (rc, os.path.exists(rp))))
# P6 is T1a: the tripwire exits 1 because make did, the CLEAN line carries
# make's own status, and B1's evidence is what tolerates it -- still.
rc, txt, rp = build('tolerated', make_rc=2, tail=b'Usage: cvimg <option>\n')
rec = dict(record(rp)) if os.path.isfile(rp) else {}
out.append(('P6  the one tolerated make failure is recorded as such', "0 2 True",
            '%s %s %s' % (rc, rec.get('make_rc'),
                          rec.get('make_tolerated', '-') != '-')))
out.append(('P6b make_rc is cmd-rc from the CLEAN line, not the tripwire\'s 1',
            'VENDOR-TRIPWIRE: CLEAN  cmd-rc=2  6 tree(s) watched',
            rec.get('tripwire_verdict', '-')))

def refused(label, word, **kw):
    """rc, whether any record (or its .tmp) exists, and whether `word` was said."""
    rc, txt, rp = build(label, **kw)
    return '%s %s %s' % (rc, os.path.exists(rp) or os.path.exists(rp + '.tmp'),
                         word in txt)

# T1b -- the same make failure WITHOUT B1's evidence is a failure, not a
# tolerance: the tripwire being CLEAN says nothing about make succeeding.
out.append(('T1b CLEAN cmd-rc=2 without B1 evidence -> 1, no record', '1 False True',
            refused('t1b', 'rc=2', make_rc=2)))
out.append(('T2  TRIPPED -> 2, no record, and it says TRIPPED', '2 False True',
            refused('t2', 'TRIPPED', rc=2,
                    line='VENDOR-TRIPWIRE: TRIPPED  cmd-rc=0  a watched tree changed')))
out.append(('T5  TOUCHED -> 2, no record, and it says TOUCHED', '2 False True',
            refused('t5', 'TOUCHED', rc=5,
                    line='VENDOR-TRIPWIRE: TOUCHED  cmd-rc=0  git sees no change, '
                         'but files moved past the stamp')))
out.append(('T4  a tree dirty before, make not run -> 2, no record', '2 False True',
            refused('t4', 'ALREADY dirty', rc=4, make=False,
                    line='VENDOR-TRIPWIRE: REFUSED  a watched tree is already '
                         'dirty; a diff taken against dirt cannot be attributed.')))
out.append(('T3a no tree to watch, make not run -> 3, no record', '3 False True',
            refused('t3a', 'SKIPPED', rc=3, make=False,
                    line='VENDOR-TRIPWIRE: SKIPPED  not a git repository: /x/tree')))
# T3b -- the same exit status as T3a, and a different answer: make RAN, and
# nothing certified what it wrote.  That is a control failing, not an
# environment that was not ready.
out.append(('T3b git unreadable AFTER make ran -> 2, no record', '2 False True',
            refused('t3b', 'nothing certifies it', rc=3,
                    line='VENDOR-TRIPWIRE: REFUSED  cmd-rc=0  git could not read '
                         'a watched tree AFTER the command ran.')))
out.append(('V1  exit 0 and NO verdict line -> 2, no record', '2 False True',
            refused('v1', 'never read as CLEAN', rc=0, line='')))
out.append(('V2  exit 0 with a TRIPPED line: they disagree -> 2', '2 False True',
            refused('v2', 'disagree', rc=0,
                    line='VENDOR-TRIPWIRE: TRIPPED  cmd-rc=0  a watched tree changed')))
# V3 -- the verdict is the LAST such line.  make's own output carrying an
# earlier one must not decide: here it says TRIPPED and the real verdict,
# printed after make returned, is CLEAN.
rc, txt, rp = build('v3', pre=b'VENDOR-TRIPWIRE: TRIPPED  cmd-rc=0  echoed by a recipe\n')
out.append(('V3  an earlier line in make\'s output does not decide', '0 True',
            '%s %s' % (rc, os.path.isfile(rp))))
# W, W2, C -- how the first build above spawned its command.
# The expected tripwire is spelt from the TOOL's own path, not read back out of
# the module, so W also fails if TRIPWIRE stops being the one beside it.
out.append(('W   make is spawned only through the tripwire, after --',
            repr(['bash', os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])),
                                       'vendor-tripwire.sh'),
                  '--quiet', '--', 'make', '-C',
                  os.path.join(T, 'pwork', 'ok', 'kroot', 'rtkload')]),
            repr(first[0]['argv']) if first else '-'))
out.append(('W2  and with stdin at /dev/null', '-3',
            str(first[0]['stdin']) if first else '-'))
out.append(('C   and from <work>/<label>, never the caller\'s cwd', 'True',
            str(bool(first) and first[0]['cwd'] == os.path.join(T, 'pwork', 'ok')
                and os.path.commonpath([first[0]['cwd'], os.path.join(T, 'pwork')])
                == os.path.join(T, 'pwork'))))
# E -- no tripwire: refused before anything is copied or spawned.
saved = r.TRIPWIRE
r.TRIPWIRE = os.path.join(T, 'no-such-tripwire.sh')
rc, txt, rp = build('e-none')
r.TRIPWIRE = saved
out.append(('E   no tripwire -> 3, nothing spawned, nothing under --work', 'exit 3 0 False True',
            '%s %d %s %s' % (rc, len(seen),
                             os.path.exists(os.path.join(T, 'pwork', 'e-none')),
                             'no tripwire at' in txt)))
for lbl, exp, got in out:
    print('%s\t%s\t%s' % (lbl, exp, got))
PYEOF
# 🔴 Only well-formed rows are cases.  A line without two tabs is not a case
# that passed: `read` would hand ck an empty expected and an empty got, and ck
# would print `ok`.  量 2026-09-23, the first run of E: an uncaptured stderr
# line became exactly that phantom `ok`.  Any such line is one FAIL here.
if [ -s "$T/p.out" ] && grep -q 'P1a' "$T/p.out" && ! grep -q 'Traceback' "$T/p.out"; then
    stray="$(awk -F'\t' 'NF != 3' "$T/p.out" | head -1)"
    [ -z "$stray" ] || { printf '  FAIL   %-52s %s\n' "a stray line in the in-process block" "$stray"; fail=$((fail+1)); }
    while IFS=$'\t' read -r lbl exp got; do ck "$lbl" "$exp" "$got"; done \
        < <(awk -F'\t' 'NF == 3' "$T/p.out")
else
    printf '  FAIL   %-52s %s\n' "the in-process block (P, T, V, W, C, E)" "$(tail -3 "$T/p.out" | tr '\n' ' ')"
    fail=$((fail+1))
fi
# P7 -- a missing --vmlinux is a refusal with a reason.  Until 2026-09-23 the
# size print ran before the existence check and this was a traceback, exit 1.
mkdir -p "$T/p7cell/linux-2.6.30"
"$PY" "$TOOL" build --cell "$T/p7cell" --vmlinux "$T/no-such-vmlinux" \
      --label p7 --work "$T/p7work" > "$T/p7.out" 2>&1
ck "P7  build with a missing --vmlinux -> 3" 3 "$?"
ck "P7b and it is a refusal, not a traceback" "1/0" \
   "$(grep -c 'no-such-vmlinux: not found' "$T/p7.out")/$(grep -c 'Traceback' "$T/p7.out")"

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
