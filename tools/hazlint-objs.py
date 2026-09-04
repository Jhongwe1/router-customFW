#!/usr/bin/env python3
"""hazlint-objs -- run `hazlint` over every object a kernel build produced
under `arch/rlx`, and assert `TC-21` while doing it.

RUNSHEET `P2`.  Why this is not the same check as `P1`
-----------------------------------------------------
`P1` runs `hazlint` over the linked `vmlinux` and reports 0 violations.  That
is a stronger statement about the bytes that will execute and a WEAKER one
about why they are safe, because it cannot separate two claims that happen to
coincide:

  * the author of `arch/rlx`'s hand-written assembly filled the delay slots;
  * `gas`, handed its own default `-march` by the gcc driver (`TC-14`), filled
    eleven of them for him.

`TC-21` says it is the second.  The instrument that decides it is one `as`
invocation per file with `-march` moved and nothing else moved, and the
objects are where that lands -- a linked image is the same code after both
have already happened.

So this tool does two things in one pass:

  the SWEEP     every `.o` the build produced -> 0 violations expected
  the CONTROL   the same six `.S` files, re-assembled from the build's own
                recorded command line with `-Wa,-march=5281` appended and
                NOTHING else changed -> the eleven violations must appear

A sweep that reports 0 and cannot show what a 1 looks like on the same
material is not a measurement.  `Q5` is that showing, and it refuses.

The enumeration is itself a control, and it has already been wrong here
-----------------------------------------------------------------------
`notes/kernel-build.md` §10: `arch/rlx/bsp` is a SYMLINK (-> `../../../target/bsp`
-> `boards/rtl8196e/bsp`), so `find arch/rlx -name '*.o'` never enters it.
量 on this project's four `R3` trees: plain `find` returns 57/58 objects and
`find -L` returns 63/64.  The six it cannot see are `bsp/setup.o`, `prom.o`,
`serial.o`, `timer.o`, `irq.o` and `bsp/built-in.o` -- the board.  `bsp_setup()`,
`bsp_serial_init()` and the call to `bsp_swcore_init()` whose return value
`RLXFW-B07` prints are all in `setup.o`.  A `P2` written with plain `find`
would have swept the architecture and skipped the machine, and reported 0.

`Q1` refuses on exactly that: `bsp/setup.o` must be in the swept list.
§10.3 is why `-L` is used HERE and not everywhere -- inside `arch/rlx` nothing
leaves the tree; at a drop root `-R`/`-L` inflates a census by 19.2% and
imports the host's `/var/tmp`.

What this tool CANNOT tell you, printed with every run
------------------------------------------------------
1.  **Branch targets in a `.o` are unresolved and are reported, not followed.**
    Relocations have not been applied, section addresses are 0, and `hazlint`
    gives every section a synthetic base with `addressed=False`.  A load in a
    delay slot whose branch target is in another section is counted in
    `unresolved`, not in `VIOLATIONS`.  That is a false-negative channel and
    it is the reason `P1` exists as well as `P2`.  The `unresolved` total is
    printed for every object.

2.  **`TC-m`: on an `ET_REL` object the MIPS16 excision is PRINTED and does not
    happen.**  The holes are computed from `st_value`, which is
    section-relative in a relocatable object, while the spans carry a
    synthetic base -- so they never intersect and `_cut` cuts nothing, while
    `print_spans` still says `EXCISED BY NAME`.  The error is CONSERVATIVE:
    those bytes are scanned as 32-bit code rather than skipped, so it can
    manufacture a violation and cannot hide one.  **A 0 from this sweep is
    therefore not weakened by `TC-m`; a non-zero from it is suspect until the
    site is read.**  Objects whose report claims an excision are counted and
    named in the summary as `TC-m exposed`, and `TC-m` is not fixed here --
    it is carried in `PROGRESS.md`.

3.  It reads the objects a build LEFT BEHIND.  It does not rebuild them, and
    it cannot tell you that the tree it is reading is the tree that produced
    the `vmlinux` you are about to upload.  `--expect-vmlinux` pins that by
    sha256 and is the only thing here that does.

Usage
    hazlint-objs.py --tree <staged top>            # the dir holding linux-2.6.30/
                    [--also DIR]...                # HAZ-1; repeatable, relative
                                                   # to linux-2.6.30/
                    [--label NAME] [--jobs N]
                    [--hazlint PATH] [--out FILE]
                    [--expect-vmlinux SHA256]
                    [--no-arch-control]            # skip Q5. Says so, loudly.

`--also` and why a sweep's own population is a claim  (HAZ-1)
-------------------------------------------------------------
The population above is `arch/rlx`, and every one of `R5`'s six drivers is
under `drivers/`.  量 2026-09-03: `R5-1` produced
`drivers/clocksource/rtl819x-timer.o`, and this tool could not see it -- so
`P2` would have reported **0 violations over a population containing no
driver of mine**, and that 0 reads to a later reader as *the drivers were
swept too*.  `--also drivers/clocksource` puts the directory in.

`Q1b` is its positive control and it is one row per `--also`: the directory
must ADD objects, measured as the count with it against the count without.
A `--also` naming a directory that contributes nothing REFUSES, because a
green sweep over a population that silently excludes what the caller named is
the failure this option exists to remove -- not a smaller version of it.

Exit
    0  every object clean and every control fired
    1  at least one object reports a violation
    2  a control failed, or refused -- NOTHING is reported about the tree
    3  usage / environment refusal
"""

import concurrent.futures
import os
import re
import shlex
import subprocess
import sys
import hashlib

VERSION = '1.0'

# The six files TC-21 names, and the violation count each must produce when the
# assembler is handed a core WITH load interlocks.  notes/kernel-build.md §2.
# `relocate_kernel.S` is in the table and NOT in this dict: CONFIG_KEXEC=n, the
# file is not built for this board, and a control that expects an object the
# build does not produce is a control that fails for the wrong reason.
TC21_EXPECT = {
    'arch/rlx/kernel/entry.o':        5,
    'arch/rlx/kernel/genex.o':        1,
    'arch/rlx/lib/strlen_user.o':     2,
    'arch/rlx/lib/strnlen_user.o':    2,
    'arch/rlx/lib/strncpy_user.o':    1,
    # `differs, no hazard exposed` -- gas emits an extra nop and every later
    # offset shifts, and hazlint reads 0 at both -march values.  It is in the
    # control because a control that only contains cells expected to fire
    # cannot show that the tool is reading the -march and not the filename.
    'arch/rlx/kernel/scall32-o32.o':  0,
}
TC21_TOTAL = 11

HAZ_VIOL = re.compile(r'^\s+VIOLATIONS\s+(\d+)\s*$')
HAZ_LOAD = re.compile(r'^\s+loads \(MIPS-I load-to-GPR, rt != \$zero\)\s+(\d+)\s*$')
HAZ_NOP = re.compile(r'^\s+followed by an explicit nop\s+(\d+)\s')
HAZ_UNRES = re.compile(r'^\s+successor unresolved\s+(\d+)\s*$')
HAZ_COV = re.compile(r'^coverage\s+(\d+) bytes scanned; (\d+) bytes named')
HAZ_WORDS = re.compile(r'^words\s+(\d+)\s*$')
HAZ_SITE = re.compile(r'^\s*\d+\.\s+0x([0-9a-fA-F]{8})\s')


class Row(object):
    def __init__(self, path, rel):
        self.path, self.rel = path, rel
        self.rc = None
        self.viol = self.loads = self.nop = self.unres = 0
        self.scanned = self.notscanned = self.words = 0
        self.excise_claimed = False
        self.zero_loads = False      # refused for 0 loads, re-run with the flag
        self.no_code = False         # no PROGBITS+EXECINSTR section at all
        self.sites = []
        self.raw = ''


def exec_section_bytes(path):
    """Bytes of PROGBITS+EXECINSTR in a 32-bit big-endian ELF, read here.

    A SECOND source for the two things the sweep has to decide about an object
    it cannot get a verdict on: does it hold code at all, and is `0 loads` a
    statement about an empty file.  `hazlint` says both in prose; a sweep that
    believed the prose would have one owner for the fact and no way to notice
    it drifting.  Returns None if the file is not an ELF this tool can read.
    """
    import struct
    try:
        with open(path, 'rb') as fh:
            b = fh.read()
    except OSError:
        return None
    if b[:4] != b'\x7fELF' or b[4] != 1 or b[5] != 2:
        return None
    try:
        shoff, = struct.unpack_from('>I', b, 0x20)
        shentsize, shnum = struct.unpack_from('>HH', b, 0x2E)
        total = 0
        for i in range(shnum):
            o = shoff + i * shentsize
            _, sh_type, sh_flags, _, _, sh_size = struct.unpack_from('>6I', b, o)
            if sh_type == 1 and (sh_flags & 0x4):
                total += sh_size
        return total
    except struct.error:
        return None


def die(msg, code=3):
    sys.stderr.write('hazlint-objs: %s\n' % msg)
    sys.exit(code)


def run_hazlint(hazlint, path, rel, extra=()):
    """One hazlint invocation, with its own live control block.

    TWO refusals are expected on a per-object sweep and neither is a defect:

      `REFUSED: N words scanned and not one load`   an object that really has
          no loads -- `head.o`, `ashldi3.o`.  Re-run once with
          `--allow-zero-loads`, and the re-run must still report 0 loads on a
          non-zero number of words: the flag lifts the refusal, it does not
          change the reading.  If the re-run finds loads, the first run was
          not what this branch thinks it was and Q7a fails.

      `no executable section in this ELF`            a data-only object --
          `init_task.o`.  Confirmed independently against the section headers
          before it is skipped (Q7b), because "there is nothing to scan here"
          is exactly the sentence a broken sweep would also print.
    """
    r = Row(path, rel)
    p = subprocess.run([sys.executable, hazlint] + list(extra) + [path],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    r.rc = p.returncode
    r.raw = p.stdout.decode('utf-8', 'replace')
    if 'no executable section in this ELF' in r.raw:
        r.no_code = True
        return r
    if 'REFUSED:' in r.raw and 'not one load' in r.raw \
            and '--allow-zero-loads' not in extra:
        r2 = run_hazlint(hazlint, path, rel, tuple(extra) + ('--allow-zero-loads',))
        r2.zero_loads = True
        return r2
    for line in r.raw.split('\n'):
        m = HAZ_VIOL.match(line)
        if m:
            r.viol = int(m.group(1)); continue
        m = HAZ_LOAD.match(line)
        if m:
            r.loads = int(m.group(1)); continue
        m = HAZ_NOP.match(line)
        if m:
            r.nop = int(m.group(1)); continue
        m = HAZ_UNRES.match(line)
        if m:
            r.unres = int(m.group(1)); continue
        m = HAZ_COV.match(line)
        if m:
            r.scanned, r.notscanned = int(m.group(1)), int(m.group(2)); continue
        m = HAZ_WORDS.match(line)
        if m:
            r.words = int(m.group(1)); continue
        if line.startswith('EXCISED BY NAME'):
            r.excise_claimed = True; continue
        m = HAZ_SITE.match(line)
        if m:
            r.sites.append('0x' + m.group(1))
    return r


def sweep(hazlint, objs, jobs):
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(run_hazlint, hazlint, p, rel) for p, rel in objs]
        for f in concurrent.futures.as_completed(futs):
            rows.append(f.result())
    rows.sort(key=lambda r: r.rel)
    return rows


def enumerate_objs(kdir, also=()):
    """Every .o under arch/rlx and under each `also` directory, FOLLOWING
    symlinks, plus the plain-find list so the difference can be printed rather
    than assumed.

    `also` is `HAZ-1`.  The population was `arch/rlx` alone, and `R5`'s six
    drivers are all under `drivers/` -- so `P2` would have reported 0
    violations over a population containing no driver, and that 0 reads like
    "the drivers were swept too".  量 2026-09-03: `R5-1`'s product is
    `drivers/clocksource/rtl819x-timer.o`, which this function could not see.

    The per-directory counts are returned so `Q1b` can require that each
    `--also` actually ADDED objects: a directory that contributes nothing is
    refused rather than swept past, because a sweep that silently covers less
    than its caller asked for is the defect this argument exists to close.
    """
    pre = os.path.join(kdir, '')
    rel = lambda p: p[len(pre):] if p.startswith(pre) else p

    def find(root, follow):
        cmd = ['find']
        if follow:
            cmd.append('-L')
        cmd += [root, '-name', '*.o']
        out = subprocess.run(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL).stdout.decode()
        return sorted(x for x in out.split('\n') if x)

    roots = [('arch/rlx', os.path.join(kdir, 'arch/rlx'))]
    for d in also:
        roots.append((d, os.path.join(kdir, d)))

    plain, deref, per_root, seen = [], [], [], set()
    for name, root in roots:
        p, d = find(root, False), find(root, True)
        plain += p
        added = [x for x in d if rel(x) not in seen]
        seen.update(rel(x) for x in added)
        deref += added
        per_root.append((name, root, len(added), os.path.isdir(root)))

    deref = sorted(set(deref))
    return ([(p, rel(p)) for p in deref], set(rel(p) for p in plain),
            set(rel(p) for p in deref), per_root)


# --------------------------------------------------------------------------
# Q3/Q4 -- the synthetic pair, assembled by the tree's OWN as
# --------------------------------------------------------------------------
HAZ_S = """\t.set noreorder
\t.text
\t.globl q3
q3:
\tlw\t$8,0($4)
\taddu\t$9,$8,$8
\tjr\t$31
\tnop
"""
SAFE_S = """\t.set noreorder
\t.text
\t.globl q4
q4:
\tlw\t$8,0($4)
\tnop
\taddu\t$9,$8,$8
\tjr\t$31
\tnop
"""


def assemble(as_bin, src_text, out_o, workdir, extra=()):
    s = os.path.join(workdir, os.path.basename(out_o) + '.s')
    with open(s + '.tmp', 'w') as fh:
        fh.write(src_text)
    os.replace(s + '.tmp', s)
    cmd = [as_bin, '-EB', '-O0'] + list(extra) + ['-o', out_o, s]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       cwd=workdir)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), ' '.join(cmd)


# --------------------------------------------------------------------------
# Q5 -- TC-21.  The build's own recorded command line, one token added.
# --------------------------------------------------------------------------
def cmd_for(kdir, rel_o):
    """The gcc line kbuild recorded for this object, verbatim.

    Read out of `.<name>.o.cmd` rather than reconstructed.  A reconstructed
    command line is a second owner of the build's flags and it goes stale
    silently; this one cannot, because if it is wrong the object it produces
    does not match the one on disk and Q5b says so.
    """
    d, b = os.path.split(rel_o)
    cmdf = os.path.join(kdir, d, '.' + b + '.cmd')
    if not os.path.isfile(cmdf):
        return None
    with open(cmdf, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if line.startswith('cmd_') and ':=' in line:
                return line.split(':=', 1)[1].strip()
    return None


def rebuild_with_march(kdir, rel_o, march, out_o, env):
    cmd = cmd_for(kdir, rel_o)
    if cmd is None:
        return None, 'no .cmd file for %s' % rel_o
    argv = shlex.split(cmd)
    # replace the output path, keep everything else byte for byte
    for i, a in enumerate(argv):
        if a == '-o':
            argv[i + 1] = out_o
            break
    else:
        return None, 'no -o in the recorded command for %s' % rel_o
    argv.append('-Wa,-march=%s' % march)
    try:
        p = subprocess.run(argv, cwd=kdir, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as e:
        return None, '%s: %s' % (argv[0], e)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def parse_args(argv):
    a = {'tree': None, 'label': None, 'jobs': 4, 'hazlint': None, 'out': None,
         'arch_control': True, 'expect_vmlinux': None, 'also': []}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x == '--tree':
            a['tree'] = argv[i + 1]; i += 2
        elif x == '--also':
            # Repeatable, and relative to linux-2.6.30/ so it reads the same
            # way `arch/rlx` does in this file's own prose.
            a['also'].append(argv[i + 1].strip('/')); i += 2
        elif x == '--label':
            a['label'] = argv[i + 1]; i += 2
        elif x == '--jobs':
            a['jobs'] = int(argv[i + 1]); i += 2
        elif x == '--hazlint':
            a['hazlint'] = argv[i + 1]; i += 2
        elif x == '--out':
            a['out'] = argv[i + 1]; i += 2
        elif x == '--expect-vmlinux':
            a['expect_vmlinux'] = argv[i + 1]; i += 2
        elif x == '--no-arch-control':
            a['arch_control'] = False; i += 1
        else:
            die('unknown option %s' % x)
    if not a['tree']:
        die('--tree is required (the staged top, the directory holding '
            'linux-2.6.30/)')
    return a


def main(argv):
    args = parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    hazlint = args['hazlint'] or os.path.join(here, 'hazlint')
    top = os.path.abspath(args['tree'])
    kdir = os.path.join(top, 'linux-2.6.30')
    label = args['label'] or os.path.basename(top.rstrip('/'))

    print('hazlint-objs %s -- RUNSHEET P2: the objects, not the image' % VERSION)
    print('the claim under test is TC-21: eleven load-use hazards in')
    print("hand-written arch/rlx assembly are prevented by the assembler's")
    print('default -march and not by the author.')
    print('')
    print('tree       %s' % top)
    print('label      %s' % label)
    print('population arch/rlx%s'
          % ''.join(' + ' + d for d in args['also']))

    if not os.path.isdir(kdir):
        die('%s: no linux-2.6.30 under the tree' % kdir)
    if not os.path.isfile(hazlint):
        die('%s: no hazlint' % hazlint)

    failed = []
    ctl = []

    def ck(cid, what, ok, detail):
        ctl.append((cid, what, ok, detail))
        if not ok:
            failed.append(cid)

    # ---------------------------------------------------------------- Q0
    vm = os.path.join(kdir, 'vmlinux')
    vmsha = ''
    if os.path.isfile(vm):
        h = hashlib.sha256()
        with open(vm, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''):
                h.update(chunk)
        vmsha = h.hexdigest()
    if args['expect_vmlinux']:
        ck('Q0', 'the tree is the one that produced the named vmlinux',
           vmsha.startswith(args['expect_vmlinux'].lower()),
           'vmlinux sha256 %s vs --expect-vmlinux %s'
           % (vmsha[:16] or '(absent)', args['expect_vmlinux'][:16]))
    else:
        ctl.append(('Q0', 'the tree is the one that produced the named vmlinux',
                    None, 'NOT PINNED -- no --expect-vmlinux given; the '
                          'vmlinux on disk is %s' % (vmsha[:16] or '(absent)')))

    # ---------------------------------------------------------------- Q1/Q2
    objs, plain, deref, per_root = enumerate_objs(kdir, args['also'])
    blind = sorted(deref - plain)
    ck('Q1', 'the sweep enters arch/rlx/bsp (notes/kernel-build.md §10)',
       any(r.endswith('arch/rlx/bsp/setup.o') for _, r in objs),
       'find=%d  find -L=%d  the %d only -L reaches: %s'
       % (len(plain), len(deref), len(blind),
          ', '.join(b.replace('arch/rlx/', '') for b in blind) or 'none'))
    ck('Q2', 'there is something to sweep', len(objs) > 0,
       '%d object(s)' % len(objs))

    # Q1b -- HAZ-1's positive control, one row per --also.  The claim an
    # `--also` makes is "this directory is in the population"; the reading that
    # settles it is that DROPPING it lowers the count.  A directory that adds
    # nothing is refused, because a green sweep over a population that quietly
    # excludes the thing you named is exactly the state HAZ-1 was opened on.
    base_n = per_root[0][2]
    for name, root, added, exists in per_root[1:]:
        ck('Q1b:%s' % name, 'the --also directory ADDS objects to the sweep',
           exists and added > 0,
           'arch/rlx alone=%d, +%s=%d (%s%s)'
           % (base_n, name, base_n + added,
              '' if exists else 'NO SUCH DIRECTORY under linux-2.6.30/; ',
              '%+d' % added))
        base_n += added
    if not args['also']:
        ctl.append(('Q1b', 'the --also directory ADDS objects to the sweep',
                    None, 'no --also given -- the population is arch/rlx '
                          'alone, which contains none of R5\'s drivers '
                          '(HAZ-1)'))
    if failed:
        print_controls(ctl)
        print('REFUSED: %d control(s) failed before the tree was read.'
              % len(failed))
        return 2

    # ---------------------------------------------------------------- Q3/Q4
    # followlinks=True is load-bearing and is the same defect as Q1: the staged
    # tree's `toolchain/rsdk-...` is a SYMLINK into the drop (rlxfw-kbuild.sh
    # links it rather than copying 480 MB), and an os.walk that does not follow
    # symlinks walks an empty directory and reports "no assembler" on a tree
    # that has one.
    rsdk = None
    for root, dirs, files in os.walk(os.path.join(top, 'toolchain'),
                                     followlinks=True):
        if 'rsdk-linux-as' in files:
            rsdk = root
            break
    work = os.path.join(top, '.hazlint-objs')
    os.makedirs(work, exist_ok=True)
    if rsdk:
        as_bin = os.path.join(rsdk, 'rsdk-linux-as')
        rc1, o1, c1 = assemble(as_bin, HAZ_S, os.path.join(work, 'q3.o'), work)
        rc2, o2, c2 = assemble(as_bin, SAFE_S, os.path.join(work, 'q4.o'), work)
        r3 = run_hazlint(hazlint, os.path.join(work, 'q3.o'), 'q3.o') \
            if rc1 == 0 else None
        r4 = run_hazlint(hazlint, os.path.join(work, 'q4.o'), 'q4.o') \
            if rc2 == 0 else None
        ck('Q3', "a load-use hazard assembled by THIS tree's own as is caught",
           r3 is not None and r3.viol >= 1,
           'lw $8 / addu $9,$8,$8 under .set noreorder -> %s violation(s)'
           % (r3.viol if r3 else 'as rc=%d' % rc1))
        ck('Q4', 'the same sequence with the nop is not caught',
           r4 is not None and r4.viol == 0,
           'lw $8 / nop / addu -> %s violation(s)'
           % (r4.viol if r4 else 'as rc=%d' % rc2))
    else:
        ck('Q3', "a load-use hazard assembled by THIS tree's own as is caught",
           False, 'no rsdk-linux-as under %s/toolchain' % top)
        ck('Q4', 'the same sequence with the nop is not caught', False, 'idem')

    # ---------------------------------------------------------------- Q5
    if args['arch_control']:
        env = dict(os.environ)
        env['PATH'] = (rsdk + os.pathsep + env.get('PATH', '')) if rsdk \
            else env.get('PATH', '')
        got, notes = {}, []
        for rel_o, want in sorted(TC21_EXPECT.items()):
            if not os.path.isfile(os.path.join(kdir, rel_o)):
                notes.append('%s NOT BUILT' % rel_o)
                continue
            out_o = os.path.join(work, '5281-' +
                                 rel_o.replace('/', '_'))
            rc, out = rebuild_with_march(kdir, rel_o, '5281', out_o, env)
            if rc is None or rc != 0:
                notes.append('%s rc=%s %s' % (rel_o, rc, out.strip()[:120]))
                continue
            r = run_hazlint(hazlint, out_o, rel_o)
            got[rel_o] = r.viol
        total = sum(got.values())
        exact = all(got.get(k) == v for k, v in TC21_EXPECT.items()
                    if os.path.isfile(os.path.join(kdir, k)))
        ck('Q5', 'TC-21: the same sources at -march=5281 DO carry the hazards',
           bool(got) and total >= 1 and exact,
           '%s = %d (TC-21 says %d)%s'
           % (' '.join('%s:%d' % (k.split('/')[-1], v)
                       for k, v in sorted(got.items())),
              total, TC21_TOTAL, ('  ' + '; '.join(notes)) if notes else ''))
    else:
        ctl.append(('Q5', 'TC-21: the same sources at -march=5281 DO carry '
                    'the hazards', None,
                    'SKIPPED by --no-arch-control -- the 0 below is then a '
                    'reading with no demonstration that a 1 was reachable'))

    if failed:
        print_controls(ctl)
        print('')
        print('REFUSED: %d control(s) failed. Nothing is reported about this '
              'tree' % len(failed))
        print('         until the sweep itself is trusted.')
        return 2

    # ------------------------------------------------------------- the sweep
    rows = sweep(hazlint, objs, args['jobs'])

    # ---------------------------------------------------------------- Q6
    leaves = [r for r in rows if not r.rel.endswith('built-in.o')]
    aggs = [r for r in rows if r.rel.endswith('built-in.o')]
    leafsites = set()
    for r in leaves:
        leafsites.add(r.rel)
    agg_bad = [r.rel for r in aggs if r.viol and not leaves]
    ck('Q6', 'built-in.o aggregates are counted separately from their leaves',
       not agg_bad,
       '%d leaf object(s), %d built-in.o aggregate(s); the aggregates are '
       'reported and NOT added to the leaf totals'
       % (len(leaves), len(aggs)))

    zl = [r for r in rows if r.zero_loads]
    nc = [r for r in rows if r.no_code]
    scanned_rows = [r for r in rows if not r.no_code]
    refused = [r for r in scanned_rows if r.rc not in (0, 1)]
    ck('Q7', 'every object holding code produced a verdict', not refused,
       '%d of %d scanned; %d refusal(s)%s'
       % (len(scanned_rows), len(rows), len(refused),
          (': ' + ', '.join(r.rel for r in refused[:4])) if refused else ''))
    # Q7a -- the zero-loads retry lifts a refusal, it does not move a number.
    bad_zl = [r.rel for r in zl if r.loads != 0 or r.words == 0]
    ck('Q7a', '--allow-zero-loads re-runs report 0 loads on non-zero words',
       not bad_zl,
       '%d object(s) really have no load: %s%s'
       % (len(zl), ', '.join(r.rel.split('/')[-1] for r in zl[:6]),
          ('  BAD: ' + ', '.join(bad_zl)) if bad_zl else ''))
    # Q7b -- "no executable section" is confirmed against the section headers
    # here, not taken from hazlint's prose.
    bad_nc = [r.rel for r in nc if (exec_section_bytes(r.path) or 0) != 0]
    also = [r.rel for r in scanned_rows
            if (exec_section_bytes(r.path) or 0) == 0]
    ck('Q7b', 'objects skipped as code-free hold 0 EXECINSTR bytes (2nd source)',
       not bad_nc and not also,
       '%d skipped: %s%s%s'
       % (len(nc), ', '.join(r.rel.split('/')[-1] for r in nc[:6]),
          ('  WRONGLY SKIPPED: ' + ', '.join(bad_nc)) if bad_nc else '',
          ('  WRONGLY SCANNED: ' + ', '.join(also)) if also else ''))

    # Q8 -- TC-m, measured on this material instead of asserted from the source.
    # If the excision an ET_REL report CLAIMS had actually happened, `scanned`
    # would be less than the EXECINSTR bytes.  Equality is the reading that
    # says the bytes were scanned, which is the conservative direction and is
    # the whole reason a 0 here survives TC-m.
    tcm_rows = [r for r in rows if r.excise_claimed]
    mismatch = []
    for r in tcm_rows:
        ex = exec_section_bytes(r.path)
        if ex is None:
            mismatch.append('%s (unreadable)' % r.rel); continue
        if r.scanned > ex or ex - r.scanned >= 4:
            mismatch.append('%s scanned %d of %d' % (r.rel, r.scanned, ex))
    ck('Q8', 'TC-m: the claimed excision removed nothing (scanned == EXECINSTR)',
       not mismatch,
       '%d object(s) claim an excision; %d scanned fewer bytes than they hold%s'
       % (len(tcm_rows), len(mismatch),
          ('  ' + '; '.join(mismatch[:4])) if mismatch else ''))

    print_controls(ctl)
    if failed:
        print('')
        print('REFUSED: %d control(s) failed after the sweep.' % len(failed))
        return 2

    # ------------------------------------------------------------- report
    lines = []
    lines.append('')
    lines.append('%-46s %7s %7s %7s %7s %9s' %
                 ('object', 'loads', 'nop', 'unres', 'VIOL', 'scanned'))
    for r in rows:
        flag = ''
        if r.excise_claimed:
            flag += ' TC-m'
        if r.zero_loads:
            flag += ' zero-loads'
        if r.no_code:
            flag += ' NO CODE (%d EXECINSTR bytes)' % (exec_section_bytes(r.path) or 0)
        if r.viol:
            flag += ' <<<'
        lines.append('%-46s %7d %7d %7d %7d %9d%s'
                     % (r.rel.replace('arch/rlx/', ''), r.loads, r.nop,
                        r.unres, r.viol, r.scanned, flag))
    tl = sum(r.loads for r in leaves)
    tn = sum(r.nop for r in leaves)
    tu = sum(r.unres for r in leaves)
    tv = sum(r.viol for r in leaves)
    ts = sum(r.scanned for r in leaves)
    lines.append('%-46s %7d %7d %7d %7d %9d' %
                 ('TOTAL (leaf objects only)', tl, tn, tu, tv, ts))
    al = sum(r.loads for r in aggs)
    av = sum(r.viol for r in aggs)
    lines.append('%-46s %7d %7s %7s %7d %9d' %
                 ('  built-in.o aggregates, not added', al, '-', '-', av,
                  sum(r.scanned for r in aggs)))
    lines.append('')
    tcm = [r.rel for r in rows if r.excise_claimed]
    lines.append('TC-m exposed   %d object(s) whose report claims an excision '
                 'that an ET_REL' % len(tcm))
    lines.append('               scan does not perform. The error is '
                 'conservative -- those bytes')
    lines.append('               are SCANNED, not skipped -- so it cannot hide '
                 'a violation.')
    if tcm:
        lines.append('               %s' % ', '.join(tcm[:8]))
    lines.append('unresolved     %d successor(s) not followed across the leaf '
                 'objects: a .o' % tu)
    lines.append('               carries no applied relocations, so a load in '
                 'a delay slot whose')
    lines.append('               target is elsewhere is reported and not '
                 'checked. This is the')
    lines.append('               false-negative channel P1 exists to close.')
    lines.append('')
    if tv:
        lines.append('RESULT: \033[31m%d violation(s)\033[0m in %d of %d leaf '
                     'objects' % (tv, sum(1 for r in leaves if r.viol),
                                  len(leaves)))
        for r in leaves:
            if r.viol:
                lines.append('   %s  %s' % (r.rel, ' '.join(r.sites[:8])))
    else:
        lines.append('RESULT: \033[32m0 violations\033[0m in %d loads across '
                     '%d leaf objects (%d bytes),' % (tl, len(leaves), ts))
        lines.append('        and Q5 shows that the same sources at '
                     '-march=5281 carry %d.' % TC21_TOTAL)
    out = '\n'.join(lines)
    print(out)
    if args['out']:
        # The control block goes into the SAVED artefact too.  A file holding
        # a table of zeros and no record that the controls fired is the shape
        # this repository keeps refusing to accept from itself.
        head = ['tree %s' % top, 'label %s' % label, 'vmlinux %s' % vmsha,
                'hazlint-objs %s' % VERSION, '',
                'controls   (every one can fail, and the run stops if one does)']
        for cid, what, ok, detail in ctl:
            mark = 'ok   ' if ok else ('SKIP ' if ok is None else 'FAIL ')
            head.append('  %s %-22s %-58s %s' % (mark, cid, what, detail))
        body = '\n'.join(head) + re.sub(r'\033\[[0-9;]*m', '', out) + '\n'
        with open(args['out'] + '.tmp', 'w', encoding='utf-8') as fh:
            fh.write(body)
        os.replace(args['out'] + '.tmp', args['out'])
    return 1 if tv else 0


def print_controls(ctl):
    print('')
    print('controls   (every one can fail, and the run stops if one does)')
    for cid, what, ok, detail in ctl:
        mark = 'ok   ' if ok else ('SKIP ' if ok is None else 'FAIL ')
        print('  %s %-22s %-58s %s' % (mark, cid, what, detail))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
