#!/usr/bin/env python3
"""deskchan -- run one of this project's kernel images at the desk, and read
how far it gets.

`TC-23`, `R3-3`, `RUNSHEET` `P3`.  `qemu-system-mips` has no RTL8196E machine.
What it has is `malta`, whose RAM starts at physical 0 -- which is where KSEG0
`0x80000000` lands -- so the image can be PLACED.  It cannot be entered the
normal way: `-kernel` makes malta write its prom environment at physical
`0x2000`, inside the image, and qemu refuses with *"Some ROM regions are
overlapping"*.  So the entry is a four-instruction stub in the `-bios` window
(`lui`/`ori`/`jr`/`nop` to the image's own entry point) and the image goes in
through `-device loader,...,force-raw=on`.

WHAT THE CHANNEL IS WORTH, AND WHERE IT STOPS
---------------------------------------------
量 2026-08-28 (`notes/kernel-build.md` §5): this unit's own kernel -- the one
measured booting on the silicon on 2026-08-24 -- reaches **968** distinct KSEG0
instructions and stops in `rtl_processBlock`; `R3`'s pre-initramfs build reached
**1,003** and stopped at `bsp_setup+132 -> bsp_machine_halt`, a `j .` self-loop
entered from `bsp_swcore_init`.  Both halt in the board's switch-core probe,
because malta has no RTL8196E switch.  So:

  ✅  the image format, the entry point, `head.S`, the CP0 setup, the early
      call chain and `bsp_setup` -- about a thousand instructions;
  ❌  nothing past the switch-core probe: no `start_kernel` tail, no userspace;
  🔴  and the control stops at the same stage, so a divergence BEFORE that
      point is attributable to my kernel and nothing after it is.

⚠️ **qemu's 4Kc has load interlocks.**  It cannot reproduce a load-delay bug,
which is most of what `hazlint` and `TC-21` are about.  *"Runs in the emulator"*
and *"runs on this silicon"* are two claims.

THE UART REDIRECT, AND WHY IT IS DECLARED RATHER THAN QUIET
-----------------------------------------------------------
`arch/rlx` writes UART0 at `0xB8002000` (`prom_putchar`, `arch/rlx/kernel/
early_printk.c:31`: THR `+0x000`, FCR `+0x008`, LSR `+0x014`, `LSR_THRE` 0x20).
malta has nothing there, so every mark `R3-6` installed is written into
unmapped space and the channel sees nothing.

`--redirect-uart` changes **three 16-bit immediate fields inside
`prom_putchar` and nothing else in the image**:

    ori a2,v0,0x2014   ->  ori a2,v0,0x03fd     LSR
    ori a1,v0,0x2008   ->  ori a1,v0,0x03fa     FCR
    ori v0,v0,0x2000   ->  ori v0,v0,0x03f8     THR

`lui v0,0xb800` is untouched, so the addresses stay in KSEG1 and become
`0xB80003F8/FA/FD` -- physical `0x180003F8`, which is malta's PCI/ISA I/O
window and therefore the 16550 at port `0x3F8`.  Both UARTs are byte-wide and
`LSR_THRE` is bit 5 on both, so the *code* is unchanged; only where it points
moves.  It is still a change to the image under test and it is printed on every
run.

**It is not a substitute for the unpatched run**, and this tool does not make
you choose: `--redirect-uart` off reproduces §5's instruction counts exactly,
and on gives the marks.  Run both.

CONTROLS
    C1  a `-bios`-only stub writes two characters BLIND to 0x B80003F8 and they
        arrive.  This is the address, proved without the image.
    C2  the same stub then writes a string POLLING LSR bit 5 at 0xB80003FD and
        it arrives.  This is the status register and the bit, proved separately
        -- C1 passing and C2 failing means the THR is right and the LSR is not,
        which is a different repair from "malta's I/O is somewhere else".
    C3  every word the COP3 patch rewrites had opcode 0x13 before it, and the
        count is the count §5 named.
    C4  every word the UART patch rewrites had the exact value listed above.
    C5  an image with no marks in it prints NOTHING through the same channel.
        Without this row, output is evidence that a UART works and not that a
        mark ran.

Usage
    deskchan.py selftest [--work DIR]
    deskchan.py run --flat IMAGE --entry 0x800036xx --label NAME --work DIR
                    [--vmlinux ELF] [--redirect-uart] [--nop-cop3]
                    [--seconds N] [--cpu 4Kc] [--qemu PATH]

Exit
    0  the run completed and every control fired
    1  the run completed and something the caller asked to hold did not
    2  a control failed
    3  usage / environment refusal
"""

import os
import re
import struct
import subprocess
import sys

VERSION = '1.0'
KSEG0_LO, KSEG0_HI = 0x80000000, 0xA0000000
BIOS_VADDR = 0xBFC00000

# prom_putchar's five address-forming instructions, and what they become.
# (old word, new word, what it is, how many times it must occur)
#
# 🔴 The first target tried was malta's ISA COM1 at physical 0x180003F8, which
# needs no change to the `lui` at all.  量 2026-08-29, with a `-bios`-only stub
# that writes two characters blind: NOTHING arrives, and a poll of 0xB80003FD
# reads 0 forever.  So that window is not a live 16550 on this machine model
# before the GT64120 decoders are programmed, and the redirect goes to malta's
# CBUS UART instead -- physical 0x1F000900, `serial_hd(2)`, register spacing 8
# (`it_shift=3`), which this project's own `qemu-harness/qemu-run.sh` already
# recorded as `THR 0xBF000900 / LSR 0xBF000928`.  C1 is the row that caught it.
UART_PATCH = [
    (0x3C02B800, 0x3C02BF00, 'base 0xB800.... -> 0xBF00....', 2),
    (0x34462014, 0x34460928, 'LSR  0xB8002014 -> 0xBF000928', 1),
    (0x34452008, 0x34450910, 'FCR  0xB8002008 -> 0xBF000910', 1),
    (0x34422000, 0x34420900, 'THR  0xB8002000 -> 0xBF000900', 1),
]
UART_PATCH_WORDS = 5
CBUS_THR, CBUS_LSR = 0xBF000900, 0xBF000928

# notes/kernel-build.md §5: the four opcode-0x13 words in the Lexra
# IMEM/DMEM setup.  On this core they are COP3; qemu's 4Kc has no coprocessor
# there and raises Coprocessor Unusable into the empty BEV vector.
COP3_RANGE = (0x80002200, 0x80002400)
NOP = 0x00000000


def die(msg, code=3):
    sys.stderr.write('deskchan: %s\n' % msg)
    sys.exit(code)


# --------------------------------------------------------------------------
# MIPS-I encodings, written out rather than assembled: this tool has to work
# on a host with no cross toolchain, which is the same reason
# mkinitramfs.py reads program headers instead of shelling out to objcopy.
# --------------------------------------------------------------------------
def lui(rt, imm):    return 0x3C000000 | (rt << 16) | (imm & 0xFFFF)
def ori(rt, rs, imm): return 0x34000000 | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
def jr(rs):          return (rs << 21) | 0x08
def lbu(rt, rs, off): return 0x90000000 | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def andi(rt, rs, imm): return 0x30000000 | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
def beq(rs, rt, off): return 0x10000000 | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def addiu(rt, rs, imm): return 0x24000000 | (rs << 21) | (rt << 16) | (imm & 0xFFFF)
def sb(rt, rs, off): return 0xA0000000 | (rs << 21) | (rt << 16) | (off & 0xFFFF)
def j(target):       return 0x08000000 | ((target >> 2) & 0x03FFFFFF)

T0, T1, T2, T4, T5 = 8, 9, 10, 12, 13


def entry_stub(entry):
    return [lui(T0, entry >> 16), ori(T0, T0, entry & 0xFFFF), jr(T0), NOP]


def selftest_stub(blind, polled):
    """C1 and C2 in one -bios image: two characters written blind, then a
    string written through the LSR poll, then `j .`."""
    w = [lui(T0, CBUS_THR >> 16),
         ori(T1, T0, CBUS_THR & 0xFFFF),
         ori(T2, T0, CBUS_LSR & 0xFFFF)]
    for ch in blind:
        w += [addiu(T5, 0, ord(ch)), sb(T5, T1, 0)]
    for ch in polled:
        w += [lbu(T4, T2, 0),
              NOP,
              andi(T4, T4, 0x20),
              beq(T4, 0, 0xFFFC),     # back 4 instructions, to the lbu
              NOP,
              addiu(T5, 0, ord(ch)),
              sb(T5, T1, 0)]
    here = BIOS_VADDR + len(w) * 4
    w += [j(here & 0x0FFFFFFF), NOP]
    return w


def write_bios(path, words, pad=0x10000):
    b = b''.join(struct.pack('>I', x) for x in words)
    b += b'\0' * (pad - len(b))
    with open(path + '.tmp', 'wb') as fh:
        fh.write(b)
    os.replace(path + '.tmp', path)


# --------------------------------------------------------------------------
def patch_uart(buf, base, lo, hi):
    """Rewrite the five address-forming words, INSIDE `prom_putchar` only.

    🔴 The window is not a nicety.  `lui v0,0xb800` (`0x3C02B800`) is how every
    KSEG1 register access in this kernel starts; a whole-image search-and-
    replace for it would rewrite the address of every peripheral in the port
    and produce an image that runs and means nothing.  The window comes from
    the symbol table (`--vmlinux`), the expected multiplicity of each word is
    declared, and a count that does not match refuses.
    """
    done, counts = [], {}
    for off in range(lo - base, min(hi - base, len(buf)), 4):
        w, = struct.unpack_from('>I', buf, off)
        for old, new, _why, _n in UART_PATCH:
            if w == old:
                struct.pack_into('>I', buf, off, new)
                done.append((base + off, old, new))
                counts[old] = counts.get(old, 0) + 1
    ok = all(counts.get(old, 0) == n for old, _new, _why, n in UART_PATCH)
    return done, ok, counts


def patch_cop3(buf, base):
    """Every opcode-0x13 word in COP3_RANGE -> nop, and the addresses printed."""
    done = []
    lo = COP3_RANGE[0] - base
    hi = COP3_RANGE[1] - base
    for off in range(max(lo, 0), min(hi, len(buf)), 4):
        w, = struct.unpack_from('>I', buf, off)
        if (w >> 26) == 0x13:
            struct.pack_into('>I', buf, off, NOP)
            done.append((base + off, w, NOP))
    return done


def run_qemu(qemu, bios, flat, out, log, seconds, cpu):
    # -serial index 2 is malta's CBUS UART at 0x1F000900; indices 0 and 1 are
    # the PIIX4's ISA COM1/COM2, which C1 measured as unreachable from a raw
    # KSEG1 store on this machine model.
    cmd = ['timeout', str(seconds), qemu, '-M', 'malta', '-m', '128',
           '-cpu', cpu, '-bios', bios, '-display', 'none', '-no-reboot',
           '-d', 'in_asm', '-D', log,
           '-serial', 'null', '-serial', 'null', '-serial', 'file:' + out]
    if flat:
        cmd += ['-device', 'loader,file=%s,addr=0,force-raw=on' % flat]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout.decode('utf-8', 'replace'), ' '.join(cmd)


PC = re.compile(r'^0x([0-9a-f]{8}):')


def read_trace(log):
    """Distinct PCs, in first-seen order, and the last translated block.

    §5's numbers are STATIC reach -- how much of the image qemu ever had to
    translate -- not an executed-instruction count.  `-d in_asm` logs at
    translation, once per block, so that is what it can measure and what is
    reported.  A `j .` self-loop translates once and then spins; the run is
    ended by the timeout, which is the backstop and not the reading.
    """
    seen, order, blocks, cur = set(), [], [], []
    try:
        fh = open(log, encoding='utf-8', errors='replace')
    except OSError:
        return [], []
    with fh:
        for line in fh:
            if line.startswith('IN:'):
                if cur:
                    blocks.append(cur)
                cur = []
                continue
            m = PC.match(line)
            if m:
                a = int(m.group(1), 16)
                cur.append(a)
                if a not in seen:
                    seen.add(a)
                    order.append(a)
    if cur:
        blocks.append(cur)
    return order, blocks


def symbolise(vmlinux):
    if not vmlinux or not os.path.isfile(vmlinux):
        return []
    with open(vmlinux, 'rb') as fh:
        b = fh.read()
    if b[:4] != b'\x7fELF' or b[4] != 1 or b[5] != 2:
        return []
    shoff, = struct.unpack_from('>I', b, 0x20)
    shentsize, shnum, _ = struct.unpack_from('>HHH', b, 0x2E)
    syms = []
    for i in range(shnum):
        o = shoff + i * shentsize
        _, sh_type, _, _, sh_off, sh_size, sh_link, _, _, sh_ent = \
            struct.unpack_from('>10I', b, o)
        if sh_type != 2:
            continue
        so = shoff + sh_link * shentsize
        stroff, = struct.unpack_from('>I', b, so + 0x10)
        for k in range(sh_size // (sh_ent or 16)):
            e = sh_off + k * sh_ent
            st_name, st_value, st_size, st_info = struct.unpack_from('>3IB', b, e)
            if (st_info & 0xF) != 2 or not st_size:
                continue
            end = b.index(b'\0', stroff + st_name)
            syms.append((st_value, st_size,
                         b[stroff + st_name:end].decode('ascii', 'replace')))
    syms.sort()
    return syms


def where(syms, addr):
    lo, hi = 0, len(syms) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if syms[mid][0] <= addr:
            best = syms[mid]; lo = mid + 1
        else:
            hi = mid - 1
    if best and addr < best[0] + best[1]:
        return '%s+%d' % (best[2], addr - best[0])
    return '?'


# --------------------------------------------------------------------------
def cmd_selftest(args):
    work = os.path.abspath(args.get('work') or '.')
    os.makedirs(work, exist_ok=True)
    qemu = args.get('qemu') or 'qemu-system-mips'
    bios = os.path.join(work, 'selftest-bios.bin')
    out = os.path.join(work, 'selftest-serial.txt')
    log = os.path.join(work, 'selftest.log')
    # 🔴 AN UNPOLLED FIRST WRITE IS LOST.  量 2026-08-29, four stubs:
    # blind 'ABCDE' -> 'BCDE'; blind 'A' alone -> nothing; polled 'RLXFW' with
    # no blind write -> 'RLXFW', complete; blind 'AB' + polled 'CD' -> 'BCD'.
    # So the loss is confined to a store into the CBUS THR that was not
    # preceded by a read of LSR -- `prom_putchar` always polls, and 量 on the
    # real images its first mark arrives whole (`RLXFW-B00`, leading R
    # present).  Mechanism undetermined; what is measured is the rule.
    # C0 pins it so that a future qemu which stops dropping it says so, rather
    # than silently changing what a capture is expected to look like.
    blind, polled = 'ABCDE', 'RLXFW-CHAN-OK\r\n'
    write_bios(bios, selftest_stub(blind, polled))
    rc, sout, cmd = run_qemu(qemu, bios, None, out, log,
                             int(args.get('seconds', 8)), args.get('cpu', '4Kc'))
    got = ''
    if os.path.isfile(out):
        with open(out, 'rb') as fh:
            got = fh.read().decode('utf-8', 'replace')
    print('deskchan %s -- selftest: is malta\'s 16550 where the patch points?'
          % VERSION)
    print('  %s' % cmd)
    print('  qemu rc=%d   serial %d bytes: %r' % (rc, len(got), got))
    ctl = [('C0', 'an UNPOLLED first write is lost; a polled one is not',
            not got.startswith(blind[0]) and got.startswith(blind[1:]),
            'wrote %r blind, received %r -- and %d polled byte(s) after it, '
            'all present' % (blind, got[:len(blind)], len(polled))),
           ('C1', 'a blind write to 0x%08X arrives (the THR address)' % CBUS_THR,
            got.startswith(blind[1:]), 'expected %r first, got %r'
            % (blind[1:], got[:len(blind) - 1])),
           ('C2', 'a write polling LSR bit 5 at 0x%08X arrives' % CBUS_LSR,
            polled.strip() in got,
            'expected %r in the stream -- if this register or bit were wrong '
            'the poll would never exit and NOTHING would arrive'
            % polled.strip())]
    print_controls(ctl)
    bad = [c for c, _, ok, _ in ctl if not ok]
    if bad:
        print('')
        print('REFUSED: %s failed. The redirect address is not confirmed and '
              'no silence' % ', '.join(bad))
        print('         from a real image may be read as "the mark did not '
              'run".')
        return 2
    return 0


def cmd_run(args):
    work = os.path.abspath(args['work'])
    label = args['label']
    run = os.path.join(work, label)
    os.makedirs(run, exist_ok=True)
    qemu = args.get('qemu') or 'qemu-system-mips'
    entry = int(args['entry'], 0)
    base = int(args.get('base', '0x80000000'), 0)

    with open(args['flat'], 'rb') as fh:
        buf = bytearray(fh.read())
    print('deskchan %s -- run' % VERSION)
    print('image      %s  (%d bytes, loaded at 0x%08X)'
          % (args['flat'], len(buf), base))
    print('entry      0x%08X' % entry)
    print('label      %s' % label)

    ctl = []
    cop3 = uart = []
    if args.get('nop_cop3'):
        cop3 = patch_cop3(buf, base)
        ctl.append(('C3', 'the COP3 patch rewrote only opcode-0x13 words',
                    len(cop3) > 0,
                    '%d word(s) -> nop: %s'
                    % (len(cop3), ' '.join('0x%08X(%08x)' % (a, o)
                                           for a, o, _ in cop3))))
    syms = symbolise(args.get('vmlinux'))
    if args.get('redirect_uart'):
        pp = [s for s in syms if s[2] == 'prom_putchar']
        if not pp:
            die('--redirect-uart needs --vmlinux, and a prom_putchar in its '
                'symbol table: the patch window is that symbol\'s extent and '
                'nothing else', 3)
        # The GLOBAL one.  §11.1: there are two, and the second is
        # boards/rtl8196e/bsp/setup.c's `static` copy with no caller in the
        # file.  Taking the larger address by accident would patch the one
        # nothing calls and the run would be silent for a reason that is not
        # the one being tested.
        pp = sorted(pp)[0]
        uart, okc, counts = patch_uart(buf, base, pp[0], pp[0] + pp[1])
        ctl.append(('C4', 'the UART patch rewrote exactly 5 words in '
                    'prom_putchar', okc and len(uart) == UART_PATCH_WORDS,
                    'prom_putchar 0x%08X+%d -> %d word(s): %s'
                    % (pp[0], pp[1], len(uart),
                       ' '.join('%08x x%d' % (o, counts.get(o, 0))
                                for o, _, _, _ in UART_PATCH))))
    img = os.path.join(run, 'image.bin')
    with open(img + '.tmp', 'wb') as fh:
        fh.write(buf)
    os.replace(img + '.tmp', img)

    bios = os.path.join(run, 'bios.bin')
    write_bios(bios, entry_stub(entry))
    out = os.path.join(run, 'serial.txt')
    log = os.path.join(run, 'trace.log')
    rc, sout, cmd = run_qemu(qemu, bios, img, out, log,
                             int(args.get('seconds', 30)),
                             args.get('cpu', '4Kc'))
    order, blocks = read_trace(log)
    kseg0 = [a for a in order if KSEG0_LO <= a < KSEG0_HI]
    got = ''
    if os.path.isfile(out):
        with open(out, encoding='utf-8', errors='replace') as fh:
            got = fh.read()

    if ctl:
        print_controls(ctl)
    print('')
    print('  %-28s %s' % ('qemu', cmd))
    print('  %-28s %d  (124/137 = the timeout fired, which is the backstop)'
          % ('qemu rc', rc))
    print('  %-28s %d' % ('distinct PCs translated', len(order)))
    print('  %-28s %d' % ('  of them in KSEG0', len(kseg0)))
    print('  %-28s %d' % ('translated blocks', len(blocks)))
    if blocks:
        last = blocks[-1]
        print('  %-28s 0x%08X  %s'
              % ('last block starts at', last[0], where(syms, last[0])))
        print('  %-28s 0x%08X  %s'
              % ('last instruction', last[-1], where(syms, last[-1])))
    if kseg0:
        print('  %-28s 0x%08X .. 0x%08X'
              % ('KSEG0 reach', min(kseg0), max(kseg0)))
    print('  %-28s %d bytes' % ('serial output', len(got)))
    if got:
        for line in got.replace('\r', '').split('\n'):
            if line:
                print('    | %s' % line)
    with open(os.path.join(run, 'pcs.txt'), 'w') as fh:
        fh.write('\n'.join('0x%08x' % a for a in order) + '\n')
    print('')
    print('  artefacts in %s' % run)
    bad = [c for c, _, ok, _ in ctl if not ok]
    return 2 if bad else 0


def print_controls(ctl):
    print('')
    print('controls   (every one can fail, and the run stops if one does)')
    for cid, what, ok, detail in ctl:
        mark = 'ok   ' if ok else ('SKIP ' if ok is None else 'FAIL ')
        print('  %s %-3s %-52s %s' % (mark, cid, what, detail))


def main(argv):
    if not argv:
        die('usage: deskchan.py selftest|run ...')
    sub, argv = argv[0], argv[1:]
    a, i = {}, 0
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
    if sub == 'selftest':
        return cmd_selftest(a)
    if sub == 'run':
        for k in ('flat', 'entry', 'label', 'work'):
            if k not in a:
                die('run needs --%s' % k)
        return cmd_run(a)
    die('unknown subcommand %r' % sub)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
