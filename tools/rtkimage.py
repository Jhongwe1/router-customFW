#!/usr/bin/env python3
"""rtkimage -- run Realtek's `rtkload` pipeline, and read what it produced.

`R3-2`.  `TC-d` part one.  The pipeline, out of `linux-2.6.30/rtkload/Makefile`
and `boards/rtl8196e/Makefile:178`:

    vmlinux --strip--> vmlinux-stripped --objcopy -Obinary--> vmlinux_img
            --lzma e--> vmlinux_img.gz  --cvimg vmlinuxhdr--> +8 bytes
            --objcopy --add-section .vmlinux--> vmlinux_img.o
            --ld -T ld.script @ LOAD_START_ADDR--> memload-full
            --objcopy -Obinary--> nfjrom
            --cvimg linux-ro--> linux.bin

`nfjrom` is what goes to RAM at `0x80500000` and gets jumped to.  `linux.bin`
is `nfjrom` with a 16-byte `cr6c` flash header and a 2-byte checksum tail, and
this project does not write flash -- it is produced because the vendor shipped
one to compare against, not because anything will use it.

WHY THE CONTROL IS THE VENDOR'S OWN OUTPUT AND WHY IT COMES FIRST
-----------------------------------------------------------------
The drop ships `boards/rtl8196e/image/nfjrom` (854,016 bytes) and `linux.bin`
(854,034) beside the `image/vmlinux.elf` (3,441,133) they were made from, and
it also left three intermediates behind: `rtkload/vmlinux-stripped` (3,001,168),
`rtkload/vmlinux_img` (2,953,660) and `rtkload/memload-full` (944,997, an ELF
with its symbol table).  So every stage has a vendor-made reference, not just
the last one.  **A pipeline that cannot reproduce the vendor's own output is
not an instrument**, and until it has, a byte count printed about one of my own
images is a number with nothing behind it.

⚠️ A byte difference against a prebuilt vendor artefact is NOT automatically a
defect -- a build stamp is enough to move one.  So `check` compares STRUCTURE
(header fields, the compressed payload, the decompressed image) as well as
bytes, and says which of the two it is.

THE THREE THINGS THIS TOOL CANNOT TELL YOU
------------------------------------------
1.  That the image will boot.  It reads format, not behaviour.  The only desk
    execution channel is `TC-23`, it runs a different core, and it stops at the
    switch-core probe.
2.  That `lzma-26` is the compressor the vendor used.  `rtkload/lzma` is a
    two-branch shell script keyed on `uname -r | grep 2.4`; on any modern host
    it selects `lzma-26`.  If the vendor built on a 2.4 kernel it selected
    `lzma-24` instead.  Reproducing the shipped bytes is what decides it, and
    that is `C3` below -- it is a RESULT of this tool, never an assumption in it.
3.  Anything about flash.  `linux.bin`'s `cr6c` header is `check_image()`'s
    input on the FLASH boot path (`C-4`, `LDR-18`).  On the RAM path the loader
    takes the payload and a `cr6c` header would be 16 bytes of junk at
    `0x80500000` (`RUNSHEET` `P5`).

Usage
    rtkimage.py build --cell TOP --vmlinux ELF --label NAME --work DIR
                      [--kconfig FILE] [--sdkconfig FILE] [--jobs N]
    rtkimage.py check --nfjrom FILE [--memload ELF] [--linuxbin FILE]
                      [--expect-img FILE] [--ceiling N] [--label NAME]

Exit
    0  built / checked, and every control fired
    1  a comparison the caller asked for did not hold
    2  a control failed -- nothing is reported
    3  usage / environment refusal
"""

import hashlib
import lzma
import os
import shutil
import struct
import subprocess
import sys

VERSION = '1.0'
LOAD_START_ADDR = 0x80500000
CEILING = 5242880            # notes/kernel-build.md §3.4: 0x80500000 - 0x80000000

DROP = os.environ.get('RLXFW_DROP') or os.path.join(
    os.environ.get('FWRE_WORK', '/home/key/fwre-work'),
    'rebuild/src-vendor/rtl819x-toolchain')

# The vendor's own artefacts, and the numbers notes/kernel-build.md §3.1/§3.2
# already read off them.  Every `check` re-derives these before it says
# anything about the file it was given.
CTL_NFJROM = os.path.join(DROP, 'boards/rtl8196e/image/nfjrom')
CTL_MEMLOAD = os.path.join(DROP, 'linux-2.6.30/rtkload/memload-full')
CTL_IMG = os.path.join(DROP, 'linux-2.6.30/rtkload/vmlinux_img')
CTL_LINUXBIN = os.path.join(DROP, 'boards/rtl8196e/image/linux.bin')
CTL_EXPECT = {'pending_len': 1, 'kernel_start': 0x80003600,
              'decompressed': 2953660, 'vmlinux_start_off': 0x2C00}


def die(msg, code=3):
    sys.stderr.write('rtkimage: %s\n' % msg)
    sys.exit(code)


def sha(path_or_bytes):
    h = hashlib.sha256()
    if isinstance(path_or_bytes, bytes):
        h.update(path_or_bytes)
    else:
        with open(path_or_bytes, 'rb') as fh:
            for c in iter(lambda: fh.read(1 << 20), b''):
                h.update(c)
    return h.hexdigest()


def sum16(b):
    """The 16-bit big-endian sum `check_image()` requires to be zero (C-4).

    Odd-length input is padded with one zero byte; the images this runs on are
    even, and the pad is here so the function has one behaviour rather than an
    exception.
    """
    if len(b) % 2:
        b = b + b'\0'
    s = 0
    for i in range(0, len(b), 2):
        s = (s + ((b[i] << 8) | b[i + 1])) & 0xFFFF
    return s


# --------------------------------------------------------------------------
# reading an image
# --------------------------------------------------------------------------
def elf_symbols(path):
    """{name: (value, size)} out of a 32-bit big-endian MIPS ELF's .symtab."""
    with open(path, 'rb') as fh:
        b = fh.read()
    if b[:4] != b'\x7fELF' or b[4] != 1 or b[5] != 2:
        return None
    shoff, = struct.unpack_from('>I', b, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from('>HHH', b, 0x2E)
    out = {}
    for i in range(shnum):
        o = shoff + i * shentsize
        _, sh_type, _, _, sh_off, sh_size, sh_link, _, _, sh_entsize = \
            struct.unpack_from('>10I', b, o)
        if sh_type != 2:                       # SHT_SYMTAB
            continue
        so = shoff + sh_link * shentsize
        stroff, = struct.unpack_from('>I', b, so + 0x10)
        n = sh_size // (sh_entsize or 16)
        for j in range(n):
            e = sh_off + j * sh_entsize
            st_name, st_value, st_size = struct.unpack_from('>3I', b, e)
            end = b.index(b'\0', stroff + st_name)
            nm = b[stroff + st_name:end].decode('ascii', 'replace')
            if nm:
                out[nm] = (st_value, st_size)
    return out


class Image(object):
    """The `.vmlinux` payload inside an `nfjrom`, read rather than scanned for.

    §3.2 located it with a 1024-aligned LZMA scan because it had only the raw
    file.  Here the linked ELF is on hand for both the vendor's image and mine,
    so `__vmlinux_start` / `__vmlinux_end` come out of the symbol table and the
    locator has no failure mode to control for.  The scan stays in §3.2 as the
    reading that did not need the ELF.
    """

    def __init__(self, nfjrom, memload):
        with open(nfjrom, 'rb') as fh:
            self.raw = fh.read()
        self.nfjrom, self.memload = nfjrom, memload
        syms = elf_symbols(memload)
        if not syms or '__vmlinux_start' not in syms:
            raise ValueError('%s: no __vmlinux_start symbol' % memload)
        self.vstart = syms['__vmlinux_start'][0] - LOAD_START_ADDR
        self.vend = syms['__vmlinux_end'][0] - LOAD_START_ADDR
        sec = self.raw[self.vstart:self.vend]
        self.pending_len, self.kernel_start = struct.unpack_from('>II', sec, 0)
        # misc.c:304-312 -- 8 bytes of cvimg header, then the LZMA `alone`
        # stream: 5 bytes of properties, 8 bytes of little-endian size.
        self.stream = sec[8:len(sec) - self.pending_len]
        self.props = self.stream[:5]
        self.declared, self.declared_hi = struct.unpack_from('<II',
                                                             self.stream, 5)
        self.plain = None
        self.error = None
        try:
            d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
            self.plain = d.decompress(self.stream)
            # 🔴 A TRUNCATED STREAM DOES NOT RAISE.  `LZMADecompressor` returns
            # whatever it managed to decode and reports no error, so an image
            # cut short reads as a SMALLER image rather than as a broken one --
            # and "smaller" is the direction that looks like good news on a
            # ceiling check.  量, `test-rtkimage.sh` `B3`, on the drop's own
            # nfjrom cut to 600,000 bytes: 2,953,660 declared, far fewer
            # decoded, exit 0, no message.  Both halves are required now: the
            # decoder must say it reached the end of the stream, and the length
            # must equal the one the LZMA header declares.
            if not d.eof:
                self.error = ('the stream ends without an end marker: %d byte(s) '
                              'decoded, %d declared -- TRUNCATED'
                              % (len(self.plain), self.declared))
                self.plain = None
            elif len(self.plain) != self.declared:
                self.error = ('%d byte(s) decoded, %d declared in the LZMA '
                              'header' % (len(self.plain), self.declared))
                self.plain = None
        except lzma.LZMAError as e:
            self.error = str(e)

    def rows(self):
        r = [('nfjrom bytes', len(self.raw)),
             ('.vmlinux at file offset', '0x%X .. 0x%X' % (self.vstart, self.vend)),
             ('pending_len', self.pending_len),
             ('kernelStartAddr', '0x%08X' % self.kernel_start),
             ('LZMA properties', self.props.hex()),
             ('declared uncompressed', self.declared),
             ('compressed stream bytes', len(self.stream))]
        if self.plain is not None:
            r.append(('decompressed bytes', len(self.plain)))
            r.append(('decompressed sha256', sha(self.plain)[:16]))
            r.append(('ceiling %d' % CEILING,
                      '%d free, %.1f%% used'
                      % (CEILING - len(self.plain),
                         100.0 * len(self.plain) / CEILING)))
        else:
            r.append(('decompressed bytes', 'LZMA ERROR: %s' % self.error))
        return r


def parse_linuxbin(path):
    with open(path, 'rb') as fh:
        b = fh.read()
    sig = b[:4]
    start, flashoff, length = struct.unpack_from('>3I', b, 4)
    return {'raw': b, 'signature': sig, 'start': start, 'flash_offset': flashoff,
            'length': length, 'payload': b[16:], 'sum16': sum16(b[16:])}


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------
def controls_for_check():
    """R1-R3.  The vendor's own artefact, parsed by the same code, every run."""
    ctl = []

    def add(cid, what, ok, detail):
        ctl.append((cid, what, ok, detail))

    for p in (CTL_NFJROM, CTL_MEMLOAD, CTL_IMG):
        if not os.path.isfile(p):
            add('R1', "the drop's own nfjrom parses to the numbers §3.2 read",
                False, 'missing %s' % p)
            return ctl
    try:
        v = Image(CTL_NFJROM, CTL_MEMLOAD)
    except ValueError as e:
        add('R1', "the drop's own nfjrom parses to the numbers §3.2 read",
            False, str(e))
        return ctl
    with open(CTL_IMG, 'rb') as fh:
        ref = fh.read()
    ok = (v.pending_len == CTL_EXPECT['pending_len']
          and v.kernel_start == CTL_EXPECT['kernel_start']
          and v.vstart == CTL_EXPECT['vmlinux_start_off']
          and v.plain is not None
          and len(v.plain) == CTL_EXPECT['decompressed']
          and v.plain == ref)
    add('R1', "the drop's own nfjrom parses to the numbers §3.2 read", ok,
        'pending_len=%s start=0x%08X off=0x%X -> %s bytes, byte-identical to '
        'rtkload/vmlinux_img: %s'
        % (v.pending_len, v.kernel_start, v.vstart,
           len(v.plain) if v.plain is not None else 'ERROR',
           v.plain == ref if v.plain is not None else False))

    # R2 -- one bit.  A checker that cannot fail proves nothing.
    lb = parse_linuxbin(CTL_LINUXBIN)
    bad = bytearray(lb['payload'])
    bad[len(bad) // 2] ^= 0x01
    dec_ok = True
    try:
        badsec = bytearray(v.raw)
        badsec[v.vstart + 8 + 200] ^= 0x01
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        out = d.decompress(bytes(badsec[v.vstart + 8:
                                        v.vend - v.pending_len]))
        dec_ok = (out == ref)
    except lzma.LZMAError:
        dec_ok = False
    add('R2', 'one flipped bit breaks both the checksum and the payload',
        sum16(bytes(bad)) != 0 and not dec_ok,
        'sum16 0x0000 -> 0x%04X; decompressed still identical: %s'
        % (sum16(bytes(bad)), dec_ok))

    # R3 -- the LZMA header's declared size against the actual length.
    add('R3', 'the size in the LZMA header equals the length decoded',
        v.plain is not None and v.declared == len(v.plain),
        'declared %d, decoded %s' % (v.declared,
                                     len(v.plain) if v.plain is not None
                                     else 'ERROR'))
    return ctl


def cmd_check(args):
    label = args.get('label') or os.path.basename(args['nfjrom'])
    print('rtkimage %s -- check' % VERSION)
    print('image      %s' % args['nfjrom'])
    print('label      %s' % label)
    ctl = controls_for_check()
    print_controls(ctl)
    if any(ok is False for _, _, ok, _ in ctl):
        print('')
        print('REFUSED: a control failed. Nothing is reported about this image.')
        return 2

    memload = args.get('memload')
    if not memload:
        die('--memload is required: __vmlinux_start comes out of the linked '
            'ELF, not out of a scan')
    img = Image(args['nfjrom'], memload)
    print('')
    for k, v in img.rows():
        print('  %-26s %s' % (k, v))
    print('  %-26s %s' % ('nfjrom sha256', sha(args['nfjrom'])[:16]))

    bad = 0
    if img.plain is None:
        print('')
        print('  THE PAYLOAD DID NOT DECODE: %s' % img.error)
        print('  Nothing below this line is a statement about a loadable '
              'image.')
        bad += 1
    if args.get('linuxbin'):
        lb = parse_linuxbin(args['linuxbin'])
        print('')
        print('  linux.bin')
        print('    %-24s %r' % ('signature', lb['signature']))
        print('    %-24s 0x%08X' % ('start address', lb['start']))
        print('    %-24s 0x%08X' % ('flash offset', lb['flash_offset']))
        print('    %-24s %d  (nfjrom %d + %d)'
              % ('length field', lb['length'], len(img.raw),
                 lb['length'] - len(img.raw)))
        print('    %-24s 0x%04X   (C-4 requires 0)' % ('sum16', lb['sum16']))
        print('    %-24s %s' % ('body == nfjrom',
                                lb['payload'][:len(img.raw)] == img.raw))
        if lb['signature'] != b'cr6c' or lb['sum16'] != 0:
            bad += 1

    if args.get('expect_img'):
        with open(args['expect_img'], 'rb') as fh:
            ref = fh.read()
        same = img.plain == ref
        print('')
        print('  round trip vs %s' % args['expect_img'])
        print('    %-24s %s' % ('byte-identical', same))
        if not same:
            print('    %-24s %d vs %d' % ('sizes', len(img.plain or b''),
                                          len(ref)))
            bad += 1

    if img.plain is not None and len(img.plain) >= CEILING:
        print('')
        print('  OVER THE CEILING: %d >= %d -- the decompressor writes to '
              '0x80000000 and' % (len(img.plain), CEILING))
        print('  reads from 0x80500000; over this it overwrites its own input '
              '(FW-23)')
        bad += 1
    return 1 if bad else 0


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def cmd_build(args):
    cell = os.path.abspath(args['cell'])
    kcell = os.path.join(cell, 'linux-2.6.30')
    label = args['label']
    work = os.path.abspath(args['work'])
    run = os.path.join(work, label)
    kroot = os.path.join(run, 'kroot')
    rtk = os.path.join(kroot, 'rtkload')

    print('rtkimage %s -- build' % VERSION)
    print('cell       %s' % cell)
    print('vmlinux    %s  (%d bytes, sha256 %s)'
          % (args['vmlinux'], os.path.getsize(args['vmlinux']),
             sha(args['vmlinux'])[:16]))
    print('work       %s' % run)

    for p in (kcell, args['vmlinux']):
        if not os.path.exists(p):
            die('%s: not found' % p)
    if not os.path.isfile(os.path.join(kcell, 'include/linux/autoconf.h')):
        die('%s has no include/linux/autoconf.h -- rtkload\'s sources include '
            'it (cache.c, hfload.c, misc.c, prom_printf.c, read_memory.c, '
            'start.S), so an unconfigured tree cannot build the loader stub'
            % kcell)

    shutil.rmtree(run, ignore_errors=True)
    os.makedirs(kroot)
    # KERNEL_ROOT is `..` from rtkload/, and the Makefile reads `../.config`
    # and `../../.config`.  Those four links plus two files are the whole of
    # what the loader stub's build sees of a kernel tree; the tree itself is
    # 480 MB and is not copied.
    for d in ('include', 'arch', 'lib'):
        os.symlink(os.path.join(kcell, d), os.path.join(kroot, d))
    shutil.copy2(args['vmlinux'], os.path.join(kroot, 'vmlinux'))
    shutil.copy2(args['kconfig'], os.path.join(kroot, '.config'))
    shutil.copy2(args['sdkconfig'], os.path.join(run, '.config'))
    shutil.copytree(os.path.join(DROP, 'linux-2.6.30/rtkload'), rtk)

    rsdk = None
    for root, _, files in os.walk(os.path.join(cell, 'toolchain'),
                                  followlinks=True):
        if 'rsdk-linux-gcc' in files:
            rsdk = root
            break
    if rsdk is None:
        die('no rsdk-linux-gcc under %s/toolchain' % cell)
    env = dict(os.environ)
    env['PATH'] = rsdk + os.pathsep + env.get('PATH', '')
    env['CROSS_COMPILE'] = 'rsdk-linux-'

    log = os.path.join(run, 'make.log')
    with open(log, 'wb') as fh:
        p = subprocess.run(['make', '-C', rtk], env=env,
                           stdout=fh, stderr=subprocess.STDOUT)
    print('make       rc=%d   (%s)' % (p.returncode, log))
    with open(log, encoding='utf-8', errors='replace') as fh:
        logtext = fh.read()
    if p.returncode != 0:
        # B1 -- ONE make failure is known, named, and happens after every
        # artefact has been written.  量 2026-08-29: with the vendor's own
        # board config (CONFIG_BLK_DEV_INITRD not set, CONFIG_RTL_FLASH_MAPPING_ENABLE=y)
        # the last recipe line is `cvimg flash_size_chk linux.bin`, and the
        # `cvimg` this drop ships -- Version 1.1 -- does not implement that
        # subcommand: it prints its usage and exits non-zero.  The drop's own
        # build system cannot run to completion with the drop's own tool.
        # Anything else is a real failure and is not tolerated.
        # The recipe line is `@$(CVIMG) flash_size_chk linux.bin`, and the `@`
        # means the command itself never reaches the log -- so the string
        # `flash_size_chk` is NOT what identifies it.  What identifies it is
        # cvimg's usage banner appearing AFTER the last successful image
        # generation, with every artefact already on disk.  量, by running the
        # subcommand directly: `./cvimg flash_size_chk linux.bin` prints the
        # banner and exits 1.
        gen = logtext.rfind('Generate image successfully')
        use = logtext.rfind('Usage: cvimg <option>')
        known = (gen >= 0 and use > gen
                 and all(os.path.isfile(os.path.join(rtk, f))
                         for f in ('nfjrom', 'linux.bin', 'memload-full')))
        if not known:
            print('\n'.join('   | ' + t
                            for t in logtext.strip().split('\n')[-25:]))
            return 1
        print('           TOLERATED, named: `cvimg flash_size_chk` is the '
              'last recipe line and')
        print('           this drop\'s cvimg 1.1 does not implement it. Every '
              'artefact below was')
        print('           written before it ran, and no later line produces '
              'one.')

    print('')
    print('  %-24s %10s  %s' % ('artefact', 'bytes', 'sha256'))
    outs = ['vmlinux-stripped', 'vmlinux_img', 'vmlinux_img.gz',
            'vmlinux_img.o', 'memload-full', 'nfjrom', 'linux.bin']
    for o in outs:
        p2 = os.path.join(rtk, o)
        if os.path.isfile(p2):
            print('  %-24s %10d  %s'
                  % (o, os.path.getsize(p2), sha(p2)[:16]))
        else:
            print('  %-24s %10s' % (o, 'ABSENT'))
    print('')
    print('  outputs are in %s' % rtk)

    if args.get('compare_vendor'):
        print('')
        print('  against the artefacts this drop SHIPS -- the R3-2 positive '
              'control')
        print('  %-18s %10s %-18s %10s %-18s %s'
              % ('artefact', 'mine', 'sha256', 'vendor', 'sha256', ''))
        pairs = [('vmlinux-stripped', os.path.join(DROP, 'linux-2.6.30/rtkload/vmlinux-stripped')),
                 ('vmlinux_img', CTL_IMG),
                 ('memload-full', CTL_MEMLOAD),
                 ('nfjrom', CTL_NFJROM),
                 ('linux.bin', CTL_LINUXBIN)]
        ndiff = 0
        for name, ref in pairs:
            mine = os.path.join(rtk, name)
            if not (os.path.isfile(mine) and os.path.isfile(ref)):
                print('  %-18s MISSING' % name); ndiff += 1; continue
            sa, sb = sha(mine), sha(ref)
            same = sa == sb
            if not same:
                ndiff += 1
            print('  %-18s %10d %-18s %10d %-18s %s'
                  % (name, os.path.getsize(mine), sa[:16],
                     os.path.getsize(ref), sb[:16],
                     'IDENTICAL' if same else 'DIFFERS'))
        print('')
        print('  %d of %d differ. A difference here is not automatically a '
              'defect -- a build' % (ndiff, len(pairs)))
        print('  stamp moves an ELF and not the bytes that load. `nfjrom` is '
              'the one that is')
        print('  uploaded and jumped to; it is the row to read first.')
        print('')
        print('  量 2026-08-29, and both differences are accounted for:')
        print('    memload-full  492 bytes of DWARF, all of it DW_AT_comp_dir '
              '(101 chars vs 58,')
        print('                  ten translation units, +43 each). No '
              'allocated section moves.')
        print('    linux.bin     ONE byte: the signature. The Makefile picks '
              '`linux-ro` for this')
        print('                  board (CONFIG_SQUASHFS=y) and this cvimg '
              'writes `cr6b` for it,')
        print('                  while the shipped image is `cr6c`. '
              '`cvimg signature <in> <out>')
        print('                  0x80500000 0x30000 cr6c` reproduces the '
              'shipped file exactly --')
        print('                  so the tool can write it and the option '
              'logic does not ask for it.')
    return 0


def print_controls(ctl):
    print('')
    print('controls   (every one can fail, and the run stops if one does)')
    for cid, what, ok, detail in ctl:
        mark = 'ok   ' if ok else ('SKIP ' if ok is None else 'FAIL ')
        print('  %s %-3s %-52s %s' % (mark, cid, what, detail))


def main(argv):
    if not argv:
        die(__doc__.split('Usage')[1].strip())
    sub, argv = argv[0], argv[1:]
    a = {}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x.startswith('--'):
            k = x[2:].replace('-', '_')
            if i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                a[k] = argv[i + 1]; i += 2
            else:
                a[k] = True; i += 1
        else:
            die('unexpected argument %s' % x)
    if sub == 'build':
        for k in ('cell', 'vmlinux', 'label', 'work'):
            if k not in a:
                die('build needs --%s' % k)
        a.setdefault('kconfig', os.path.join(a['cell'], 'linux-2.6.30/.config'))
        a.setdefault('sdkconfig', os.path.join(a['cell'], '.config'))
        return cmd_build(a)
    if sub == 'check':
        if 'nfjrom' not in a:
            die('check needs --nfjrom')
        return cmd_check(a)
    die('unknown subcommand %r' % sub)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
