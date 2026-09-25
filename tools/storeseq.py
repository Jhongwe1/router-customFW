#!/usr/bin/env python3
"""storeseq -- the store sequence of two builds' TX writers, read off the objects.

WHY (R6b-2, review F12)
-----------------------
`rtl819x-nic` 1.5 claims that at its default settings `nic_xmit` and
`nic_do_tx` perform 1.4's stores in 1.4's order.  The header half of 1.5 is
checked on the host (`tools/nic15check.py`), but a host compiler says nothing
about the object that runs.  This tool reads the RSDK-built vmlinux of each
image with `mips-linux-gnu-objdump -d` and compares, per function, the
sequence of memory stores -- (opcode, the address it stores to) -- where the
address is evaluated symbolically from the instructions before it:

    sw  [nic_tx_mb]+?+12        mb w3 of the slot `?`
    sb  [nic_bufs]+?+16386      a TX buffer byte at offset 2 of slot 8+?
    sw  &nic_tx_idx             a global

`[x]` is the value loaded from symbol x, `&x` its address, `?` any value the
evaluator does not follow (a loop index, an argument).  Symbol addresses come
from the ELF's own symbol table, so a global that MOVED between the two images
still reads as the same store.  A load from a `nic15_*` symbol reads that
symbol's INITIAL value out of the ELF -- which is what "at the default
settings" means -- so 1.5's `nic15_pol.txoff` folds into the constant 2 that
1.4 wrote as NIC_RX_OFFSET.

VERDICT, per function
---------------------
GREEN when (1) the non-stack store sequences are equal and (2) every
instruction the new function has and the old does not is one of: a load from
a `nic15_*` symbol, a call to a `nic15_*` function, a branch, a nop, a
register-only instruction, or a stack save/restore.  A new store, a new load
from anything else, or a new call to anything else is RED.  Stores to the
stack (`sp`-based) are register allocation, not the device's memory, and are
reported but not compared.  The default list is every function 1.5 hooks on
the paths a default boot runs -- nic_xmit, nic_do_tx, nic_do_engine,
nic_do_arm, nic_ndo_open -- and two it must leave alone, nic_recov_fn and
nic_poll.

When the new ELF has `nic15_pol` and the old one does not (1.4 against 1.5),
two more checks run and must hold:
  IDENTITY  every driver function (`nic_*`, `rtl819x_nic*`) in both ELFs that
            TOUCHED below does not name is instruction-for-instruction the same:
            mnemonic, registers, immediates, relative branch targets, and
            every address rendered by symbol, so a function that only moved
            reads the same.  A function named in TOUCHED that is identical is
            RED too: the declaration is stale.  A function in one ELF only must
            be `nic15_*` or named in NEW_ONLY.
  DEFAULTS  the ELF's initial words: nic15_pol = {txlen 0, txoff 2, txrb 0,
            dirty 0} and nic15_show = 60.

`nic_do_tx` is inlined into `nic_write_proc` in 1.4's images (one call site,
-Os) and out of line in 1.5's (two).  When a function exists in one ELF and
not the other, its store sequence is looked for as a CONTIGUOUS run in the
named container (`nic_do_tx@nic_write_proc`), and must occur there exactly
once; the instruction check then runs over the matched region.  When it is out
of line in NEITHER ELF (1.4 against 1.4), the two containers are compared
whole -- stricter than the spec, so a RED there can come from anywhere in the
container -- and a body with no store is refused: an empty run is found
everywhere and proves nothing.

WHAT IT CANNOT SEE
------------------
Values held in registers: that the word stored at mb w2 is m_len = F and not
F + 4 is nic15check's K4, not this.  Timing: 1.5 adds loads, a branch and a
call between 1.4's stores, and "same stores" is not "same cycles".  Control
flow: the evaluator reads the listing in address order and does not merge
paths, so an address formed on one path and used on another can print as `?`
-- the same way in both builds, which is why it is compared rather than
trusted.  A RED from this tool is a difference in the objects, to be read.

    storeseq.py --old OLD.elf --new NEW.elf [--func F[@CONTAINER]]... [--show]
    storeseq.py --self-test
"""
import argparse
import difflib
import os
import re
import shutil
import struct
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

OBJDUMP = "mips-linux-gnu-objdump"
NM = "mips-linux-gnu-nm"
READELF = "mips-linux-gnu-readelf"
DEFAULT_FUNCS = ["nic_xmit", "nic_do_tx@nic_write_proc", "nic_do_engine",
                 "nic_do_arm", "nic_ndo_open", "nic_recov_fn", "nic_poll"]

# 1.5 changes these, by name and why; everything else of the driver must be
# identical.  A name here whose function IS identical is a stale declaration.
TOUCHED = {
    "nic_xmit": "the txrb and W hooks, the policy's fields (store-compared)",
    "nic_write_proc": "the 1.5 dispatcher at :3027; 1.4 inlined nic_do_tx",
    "nic_read_proc": "the tx15 line at :2571",
    "nic_do_engine": "the engine gate at :2307 (store-compared)",
    "nic_do_arm": "nic15_armed at :2096 (store-compared)",
    "nic_ndo_open": "the engine gate at :1665 (store-compared)",
    "rtl819x_nic_init": "nic15_init at :3109",
    "nic_et_drvinfo": "ethtool's version is RTL819X_NIC_VERSION, :218 1.4 -> 1.5",
}
NEW_ONLY = {"nic_do_tx": "out of line in 1.5, inlined into nic_write_proc in 1.4"}
DRIVER = re.compile(r"^(nic_|rtl819x_nic)")
DEFAULT_WORDS = {"nic15_pol": [0, 2, 0, 0], "nic15_show": [60]}

STORES = {"sb", "sh", "sw", "swl", "swr", "sc", "sd", "swc1", "sdc1"}
LOADS = {"lb", "lbu", "lh", "lhu", "lw", "lwl", "lwr", "ll", "ld", "lwc1",
         "ldc1"}
CALLS = {"jal", "jalr", "bal", "bgezal", "bltzal"}
BRANCH = re.compile(r"^(b|beq|bne|beqz|bnez|bgez|bgtz|blez|bltz|beql|bnel|"
                    r"beqzl|bnezl|j|jr|bc0f|bc0t|bc1f|bc1t|bnel)$")
CLOBBER = ["at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3",
           "t4", "t5", "t6", "t7", "t8", "t9", "ra"]
LINE = re.compile(r"^\s*([0-9a-f]+):\s+([a-z][a-z0-9.]*)\s*(.*?)\s*$")


class Refused(Exception):
    pass


# ---------------------------------------------------------------- symbols
class Syms:
    """Address <-> symbol for one ELF, and the initial word at an address."""

    def __init__(self, rows, data=None, anon=None):
        # rows: [(addr, size, type, name)]
        self.rows = sorted(rows)
        self.by_name = {n: (a, s, t) for a, s, t, n in rows}
        self.data = data or (lambda addr, n: None)
        # anon(addr): an address no symbol names, rendered by what is there
        # -- a C string's content, else its section -- or None outside the
        # ELF's sections (an I/O register)
        self.anon = anon or (lambda addr: None)

    def name(self, addr):
        """-> "sym+off" for an address inside a sized data/text symbol."""
        best = None
        for a, s, t, n in self.rows:
            if a <= addr < a + max(s, 1):
                if best is None or a > best[0]:
                    best = (a, n)
            if a > addr:
                break
        if best is None:
            return None
        off = addr - best[0]
        return best[1] if not off else "%s+%d" % (best[1], off)

    @classmethod
    def from_elf(cls, elf):
        p = subprocess.run([NM, "-S", "-n", elf], capture_output=True,
                           encoding="utf-8", errors="replace")
        if p.returncode:
            raise Refused("%s failed on %s: %s" % (NM, elf, p.stderr.strip()))
        rows = []
        for ln in p.stdout.splitlines():
            f = ln.split()
            if len(f) == 4:
                rows.append((int(f[0], 16), int(f[1], 16), f[2], f[3]))
            elif len(f) == 3:
                rows.append((int(f[0], 16), 0, f[1], f[2]))
        secs = []
        p = subprocess.run([READELF, "-S", "-W", elf], capture_output=True,
                           encoding="utf-8", errors="replace")
        for ln in p.stdout.splitlines():
            m = re.match(r"\s*\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]{8})\s+"
                         r"([0-9a-f]{6,8})\s+([0-9a-f]+)", ln)
            if m:
                secs.append((m.group(1), m.group(2), int(m.group(3), 16),
                             int(m.group(4), 16), int(m.group(5), 16)))
        blob = open(elf, "rb").read()

        def data(addr, n=4):
            for name, typ, a, off, size in secs:
                if a <= addr < a + size and a:
                    if typ == "NOBITS":
                        return 0
                    o = off + addr - a
                    return struct.unpack(">I", blob[o:o + 4])[0] \
                        if n == 4 else blob[o]
            return None

        def anon(addr):
            for name, typ, a, off, size in secs:
                if a <= addr < a + size and a:
                    if typ == "NOBITS":
                        return "anon:%s" % name
                    o = off + addr - a
                    s = blob[o:o + 64].split(b"\0")[0]
                    if s and all(32 <= c < 127 or c in (9, 10) for c in s):
                        return "str:%r" % s.decode("ascii")
                    return "anon:%s" % name
            return None
        return cls(rows, data, anon)


# --------------------------------------------------------------- listing
def listing(elf, func):
    p = subprocess.run([OBJDUMP, "-d", "--no-show-raw-insn",
                        "--disassemble=" + func, elf], capture_output=True,
                       encoding="utf-8", errors="replace")
    if p.returncode:
        raise Refused("%s failed on %s: %s" % (OBJDUMP, elf,
                                               p.stderr.strip()[:200]))
    ins = parse(p.stdout)
    return ins


def parse(text):
    """objdump -d text -> [(addr, mnem, [ops], comment)]."""
    out = []
    for ln in text.splitlines():
        m = LINE.match(ln)
        if not m:
            continue
        ops_raw = m.group(3)
        comment = ""
        if "<" in ops_raw:
            comment = ops_raw[ops_raw.index("<") + 1:ops_raw.rindex(">")] \
                if ">" in ops_raw else ""
            ops_raw = ops_raw[:ops_raw.index("<")].strip()
        ops = [o.strip() for o in ops_raw.split(",")] if ops_raw else []
        out.append((int(m.group(1), 16), m.group(2), ops, comment))
    return out


# ------------------------------------------------------------ the evaluator
def _imm(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith(("0x", "-0x")) else int(s)


def _add(a, b, k=1):
    r = dict(a)
    for t, c in b.items():
        r[t] = r.get(t, 0) + k * c
        if not r[t]:
            del r[t]
    return r


def _scale(a, k):
    return {t: c * k for t, c in a.items() if c * k}


class Eval:
    """Symbolic values of registers, as a forward dataflow over the listing's
    control-flow graph (delay slots included): a register keeps a value at a
    join only if every path into the join agrees on it.  An unknown value is
    named by the instruction and register that made it, so the fixpoint is
    stable; every unknown renders as `?`."""

    def __init__(self, syms, subst_prefix="nic15_"):
        self.syms = syms
        self.subst = subst_prefix
        self.reg = {}
        self.site = 0

    def get(self, r):
        if r == "zero":
            return {}
        if r not in self.reg:
            self.reg[r] = {"?%d.%s.in" % (self.site, r): 1}
        return self.reg[r]

    def unknown(self, r):
        if r == "zero":
            return
        self.reg[r] = {"?%d.%s" % (self.site, r): 1}

    def addr(self, opnd):
        m = re.match(r"^(-?(?:0x)?[0-9a-fA-F]*)\((\w+)\)$", opnd)
        if not m:
            return None
        off = _imm(m.group(1)) if m.group(1) else 0
        return _add(self.get(m.group(2)), {"1": off})

    def render(self, e):
        """An expression, layout-independent: symbols by name, unknowns `?`."""
        if e is None:
            return "?"
        parts = []
        unk = False
        for t, c in sorted(e.items()):
            if t == "1":
                continue
            if t.startswith("?"):
                unk = True
            elif t.startswith("$"):
                parts.append(t if c == 1 else "%d*%s" % (c, t))
            else:
                parts.append(t if c == 1 else "%d*%s" % (c, t))
        const = e.get("1", 0) & 0xFFFFFFFF
        if unk:
            parts.append("?")
        if const:
            nm = self.syms.name(const) if const >= 0x80000000 else None
            if nm:
                parts.append("&" + nm)
            elif const >= 0xFFFF0000:
                parts.append(str(const - (1 << 32)))
            elif const >= 0x80000000:
                parts.append("0x%08X" % const)     # KSEG0/1: an address
            else:
                parts.append(str(const))
        return "+".join(parts) if parts else "0"

    def loadval(self, e):
        """The value of a load from a constant address: [sym], or, for a
        nic15_* symbol, its initial value in the ELF."""
        if e is None or set(e) - {"1"}:
            return None
        a = e.get("1", 0) & 0xFFFFFFFF
        nm = self.syms.name(a)
        if nm is None:
            return None
        if nm.startswith(self.subst):
            v = self.syms.data(a, 4)
            if v is not None:
                return {"1": v} if v else {}
        return {"[%s]" % nm: 1}

    def step(self, mn, ops):
        """-> (kind, target-string or None).  kind: store, sstore (stack),
        load, sload, call, branch, nop, alu."""
        if mn == "nop":
            return "nop", None
        if mn in STORES:
            e = self.addr(ops[1]) if len(ops) > 1 else None
            s = self.render(e)
            return ("sstore" if "$sp" in s else "store"), s
        if mn in LOADS:
            e = self.addr(ops[1]) if len(ops) > 1 else None
            s = self.render(e)
            v = self.loadval(e)
            if v is None:
                self.unknown(ops[0])
            else:
                self.reg[ops[0]] = v
            return ("sload" if "$sp" in s else "load"), s
        if mn in CALLS:
            return "call", None         # annotate clobbers after the slot
        if BRANCH.match(mn):
            return "branch", None
        d = ops[0] if ops else None
        try:
            if mn == "lui":
                self.reg[d] = {"1": (_imm(ops[1]) & 0xFFFF) << 16}
            elif mn in ("addiu", "addi"):
                self.reg[d] = _add(self.get(ops[1]), {"1": _imm(ops[2])})
            elif mn == "li":
                self.reg[d] = {"1": _imm(ops[1])} if _imm(ops[1]) else {}
            elif mn == "move":
                self.reg[d] = dict(self.get(ops[1]))
            elif mn in ("addu", "add"):
                self.reg[d] = _add(self.get(ops[1]), self.get(ops[2]))
            elif mn in ("subu", "sub"):
                self.reg[d] = _add(self.get(ops[1]), self.get(ops[2]), -1)
            elif mn == "negu":
                self.reg[d] = _scale(self.get(ops[1]), -1)
            elif mn == "sll":
                self.reg[d] = _scale(self.get(ops[1]), 1 << _imm(ops[2]))
            elif mn == "ori" and set(self.get(ops[1])) <= {"1"} and \
                    not (self.get(ops[1]).get("1", 0) & 0xFFFF):
                self.reg[d] = _add(self.get(ops[1]), {"1": _imm(ops[2])})
            elif mn == "or" and "zero" in ops[1:3]:
                other = ops[2] if ops[1] == "zero" else ops[1]
                self.reg[d] = dict(self.get(other))
            elif d and re.match(r"^[a-z][a-z0-9]$|^s8$|^fp$", d):
                self.unknown(d)
        except (ValueError, IndexError):
            if d:
                self.unknown(d)
        return "alu", None


def _target(ins, k):
    """The listing index a branch at k goes to, or None (outside, computed)."""
    ops = ins[k][2]
    if not ops:
        return None
    t = ops[-1]
    try:
        a = int(t, 16)
    except ValueError:
        return None
    for i, x in enumerate(ins):
        if x[0] == a:
            return i
    return None


def successors(ins):
    """succ[k] for every instruction, delay slots modelled: a branch at k
    goes to k + 1 (its slot), and the slot goes where the branch goes."""
    n = len(ins)
    succ = []
    for k in range(n):
        pm = ins[k - 1][1] if k else None
        if pm and (BRANCH.match(pm) or pm in CALLS):
            if pm in CALLS:
                s = [k + 1]
            elif pm in ("j", "b"):
                t = _target(ins, k - 1)
                s = [t] if t is not None else []
            elif pm == "jr":
                s = []
            else:
                t = _target(ins, k - 1)
                s = [k + 1] + ([t] if t is not None else [])
        else:
            s = [k + 1]
        succ.append([x for x in s if x is not None and x < n])
    return succ


def _meet(a, b):
    return {r: v for r, v in a.items() if b.get(r) == v}


def annotate(ins, syms):
    """-> [(addr, mnem, kind, target, norm, idn)] where norm is the text the
    instruction diff aligns on: mnemonic, plus the target for memory ops and
    the callee for calls -- never a register or an address -- and idn is the
    identity check's: registers and immediates too, branch targets relative,
    and an address only by symbol."""
    n = len(ins)
    succ = successors(ins)
    ev = Eval(syms)
    start = {"sp": {"$sp": 1}, "gp": {"$gp": 1}}
    state_in = [None] * n
    if n:
        state_in[0] = dict(start)
    work = [0] if n else []
    guard = 0
    while work:
        guard += 1
        if guard > 200000:
            raise Refused("the dataflow over %d instructions did not settle"
                          % n)
        k = work.pop(0)
        ev.reg = dict(state_in[k])
        ev.site = k
        ev.step(ins[k][1], ins[k][2])
        out = ev.reg
        if k and ins[k - 1][1] in CALLS:        # the call's slot has run
            for r in CLOBBER:
                ev.site = k
                ev.unknown(r)
            out = ev.reg
        for s in succ[k]:
            new = dict(out) if state_in[s] is None else _meet(state_in[s], out)
            if state_in[s] is None or new != state_in[s]:
                state_in[s] = new
                if s not in work:
                    work.append(s)
    res = []
    for k, (addr, mn, ops, cmt) in enumerate(ins):
        ev.reg = dict(state_in[k] or start)
        ev.site = k
        kind, tgt = ev.step(mn, ops)
        if kind == "call":
            callee = cmt.split("+")[0] if cmt else "?"
            tgt = callee
            norm = "%s %s" % (mn, callee)
        elif tgt is not None:
            norm = "%s %s" % (mn, tgt)
        else:
            norm = mn
        res.append((addr, mn, kind, tgt, norm,
                    _idn(ins, k, kind, tgt, ev)))
    return res


def _idn(ins, k, kind, tgt, ev):
    """The identity text of instruction k, after ev has stepped it."""
    _addr, mn, ops, cmt = ins[k]
    if kind == "call":
        return "%s %s" % (mn, cmt.split("+")[0] if cmt else ",".join(ops))
    if kind in ("store", "sstore", "load", "sload"):
        if tgt and re.fullmatch(r"0x[0-9A-F]{8}", tgt):
            tgt = ev.syms.anon(int(tgt, 16)) or tgt
        return "%s %s %s" % (mn, ops[0] if ops else "", tgt)
    if kind == "branch":
        t = _target(ins, k)
        if t is not None:
            dest = "@%+d" % (t - k)
        elif cmt:
            dest = "<%s>" % cmt
        else:
            dest = ops[-1] if ops else ""
        regs = ops[:-1] if (t is not None or cmt) else ops
        return "%s %s %s" % (mn, ",".join(regs), dest)
    if kind == "nop":
        return "nop"
    d = ops[0] if ops else None
    if mn == "lui" and len(ops) > 1:
        try:
            imm = _imm(ops[1]) & 0xFFFF
        except ValueError:
            return "%s %s" % (mn, ",".join(ops))
        return "lui %s %s" % (d, "HI" if imm >= 0x8000 else "0x%x" % imm)
    val = ev.reg.get(d) if d else None
    if (val is not None and set(val) <= {"1"} and
            (val.get("1", 0) & 0xFFFFFFFF) >= 0x80000000):
        c = val.get("1", 0) & 0xFFFFFFFF
        if not c & 0xFFFF:
            return "%s %s HI" % (mn, d)         # a high half, as lui's
        r = ev.render(val)
        if r.startswith("0x"):
            r = ev.syms.anon(c) or r
        return "%s %s %s" % (mn, d, r)
    return "%s %s" % (mn, ",".join(ops))


def stores(ann):
    return [(i, "%s %s" % (a[1], a[3])) for i, a in enumerate(ann)
            if a[2] == "store"]


def find_run(hay, needle):
    """Every index where `needle` occurs as a contiguous run of `hay`."""
    n = len(needle)
    return [i for i in range(len(hay) - n + 1) if hay[i:i + n] == needle]


# --------------------------------------------------------------- compare
ALLOWED = ("nic15-load", "nic15-call", "global-load", "branch", "nop", "alu",
           "stack")


def classify_extra(a):
    """A new-only instruction.  A load from a symbol's own address is a
    CACHED read of kernel data (KSEG0) -- a global the compiler reloads after
    a new call, say -- and touches neither the engine nor a descriptor, so it
    is allowed and counted.  A load through a computed address can be a
    descriptor or a register (KSEG1) and is not."""
    _addr, mn, kind, tgt = a[:4]
    if kind in ("sstore", "sload"):
        return "stack"
    if kind == "load":
        if tgt and ("nic15_" in tgt):
            return "nic15-load"
        if tgt and re.fullmatch(r"&[A-Za-z_][\w.]*(\+\d+)?", tgt):
            return "global-load"
        return "LOAD"
    if kind == "store":
        return "STORE"
    if kind == "call":
        return "nic15-call" if tgt and tgt.startswith("nic15_") else "CALL"
    return kind


def compare(old_ann, new_ann, label):
    """-> (green, lines)"""
    lines = []
    so = [s for _, s in stores(old_ann)]
    sn = [s for _, s in stores(new_ann)]
    same = so == sn
    lines.append("%s: %d stores old, %d new: %s" % (
        label, len(so), len(sn), "EQUAL" if same else "DIFFERENT"))
    if not same:
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                a=so, b=sn, autojunk=False).get_opcodes():
            if tag != "equal":
                lines.append("    %s old[%d:%d] %s  new[%d:%d] %s" % (
                    tag, i1, i2, so[i1:i2][:4], j1, j2, sn[j1:j2][:4]))
    # What the new function does that the old does not, as MULTISETS of
    # memory operations and calls (by kind and rendered target or callee),
    # so that a moved block or a renamed register is not read as a new
    # instruction.  Register-only instructions, branches and nops are
    # counted, not compared: they touch no memory.
    def census(ann):
        mem, other = {}, {}
        for a in ann:
            key = (a[2], a[4])
            if a[2] in ("load", "store", "call", "sload", "sstore"):
                mem[key] = mem.get(key, 0) + 1
            else:
                other[a[2]] = other.get(a[2], 0) + 1
        return mem, other
    mo, oo = census(old_ann)
    mn_, on = census(new_ann)
    extra, bad, gone = {}, [], []
    rep = {(a[2], a[4]): a for a in new_ann}
    for key, cnt in sorted(mn_.items()):
        d = cnt - mo.get(key, 0)
        if d <= 0:
            continue
        c = classify_extra(rep[key])
        extra[c] = extra.get(c, 0) + d
        if c not in ALLOWED:
            bad.append("%d x %s" % (d, key[1]))
    for key, cnt in sorted(mo.items()):
        d = cnt - mn_.get(key, 0)
        if d > 0 and key[0] not in ("sload", "sstore"):
            gone.append("%d x %s" % (d, key[1]))
    for k in sorted(set(oo) | set(on)):
        d = on.get(k, 0) - oo.get(k, 0)
        if d:
            extra["%s(net)" % k] = d
    lines.append("    new memory ops and calls: %s" % (
        ", ".join("%s %d" % kv for kv in sorted(extra.items())) or "none"))
    for b in bad[:12]:
        lines.append("    FORBIDDEN %s" % b)
    for g in gone[:6]:
        lines.append("    old-only (reported): %s" % g)
    sp_o = sum(1 for a in old_ann if a[2] == "sstore")
    sp_n = sum(1 for a in new_ann if a[2] == "sstore")
    lines.append("    stack stores (not compared): old %d, new %d" % (sp_o, sp_n))
    return same and not bad, lines


def region(ann, run_start, n):
    idx = [i for i, a in enumerate(ann) if a[2] == "store"]
    first, last = idx[run_start], idx[run_start + n - 1]
    return ann[first:last + 1]


def compare_func(spec, old, new, osyms, nsyms, lister=listing):
    """spec 'f' or 'f@container'.  -> (green, lines)."""
    f, _, cont = spec.partition("@")
    lo, ln = lister(old, f), lister(new, f)
    if lo and ln:
        return compare(annotate(lo, osyms), annotate(ln, nsyms), f)
    if not cont:
        raise Refused("%s is missing from %s and no container was named"
                      % (f, "the old ELF" if not lo else "the new ELF"))
    if not lo and not ln:
        # inlined in BOTH: there is no body to search for, so the containers
        # are compared whole, and the output says so
        co, cn = lister(old, cont), lister(new, cont)
        if not co or not cn:
            raise Refused("%s is out of line in neither ELF and %s is missing "
                          "from the %s ELF" % (f, cont,
                                               "old" if not co else "new"))
        green, more = compare(annotate(co, osyms), annotate(cn, nsyms),
                              "%s (whole)" % cont)
        return green, ["%s: out of line in neither ELF; compared as its whole "
                       "container %s" % (f, cont)] + more
    # one side has it out of line: find its stores in the other's container
    if ln:
        ref, refsyms, other, osy, side = ln, nsyms, lister(old, cont), osyms, \
            "old"
    else:
        ref, refsyms, other, osy, side = lo, osyms, lister(new, cont), nsyms, \
            "new"
    if not other:
        raise Refused("neither %s nor %s is in the %s ELF" % (f, cont, side))
    ra, oa = annotate(ref, refsyms), annotate(other, osy)
    needle = [s for _, s in stores(ra)]
    hay = [s for _, s in stores(oa)]
    if not needle:
        raise Refused("%s has no store in the %s ELF: an empty run is found "
                      "at every index and proves nothing"
                      % (f, "new" if ln else "old"))
    hits = find_run(hay, needle)
    lines = ["%s: %d stores out of line in the %s ELF, searched as one run in "
             "%s's %d in the %s ELF: found %d time(s)"
             % (f, len(needle), "new" if ln else "old", cont, len(hay), side,
                len(hits))]
    if len(hits) != 1:
        best = difflib.SequenceMatcher(a=hay, b=needle, autojunk=False)
        m = best.find_longest_match(0, len(hay), 0, len(needle))
        lines.append("    longest common run %d of %d, at %s[%d] and %s[%d]"
                     % (m.size, len(needle), cont, m.a, f, m.b))
        if m.b + m.size < len(needle):
            lines.append("    first store after it: %s has %r, %s has %r" % (
                f, needle[m.b + m.size], cont,
                hay[m.a + m.size] if m.a + m.size < len(hay) else None))
        return False, lines
    sub = region(oa, hits[0], len(needle))
    own = region(ra, 0, len(needle)) if needle else ra
    old_r, new_r = (sub, own) if ln else (own, sub)
    green, more = compare(old_r, new_r, "%s (region)" % f)
    return green, lines + more


# ------------------------------------------------- identity and defaults
def driver_funcs(syms):
    return {n for a, s, t, n in syms.rows if t in "tT" and DRIVER.match(n)}


def identity(old, new, osyms, nsyms, lister=listing, funcs=None):
    """-> {name: (status, detail)}, status one of same, differ, old-only,
    new-only."""
    fo = driver_funcs(osyms) if funcs is None else funcs[0]
    fn = driver_funcs(nsyms) if funcs is None else funcs[1]
    res = {}
    for f in sorted(fo | fn):
        if f not in fn:
            res[f] = ("old-only", "")
            continue
        if f not in fo:
            res[f] = ("new-only", "")
            continue
        a = [x[5] for x in annotate(lister(old, f), osyms)]
        b = [x[5] for x in annotate(lister(new, f), nsyms)]
        if a == b:
            res[f] = ("same", "%d instructions" % len(a))
            continue
        i = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]),
                 min(len(a), len(b)))
        res[f] = ("differ", "%d vs %d instructions; first at %d: %r / %r" % (
            len(a), len(b), i, a[i] if i < len(a) else None,
            b[i] if i < len(b) else None))
    return res


def identity_verdict(res, touched=None, new_only=None):
    """-> (green, lines).  Swept both ways: an untouched function that
    differs is RED, and so is a TOUCHED one that does not."""
    touched = TOUCHED if touched is None else touched
    new_only = NEW_ONLY if new_only is None else new_only
    lines, green, same = [], True, 0
    for f, (st, det) in sorted(res.items()):
        if st == "same" and f not in touched:
            same += 1
            continue
        if st == "same":
            ok, why = False, "declared TOUCHED but identical: stale"
        elif st == "differ":
            ok = f in touched
            why = ("touched: %s" % touched[f]) if ok else "NOT declared: " + det
        elif st == "new-only":
            ok = f.startswith("nic15_") or f in new_only
            why = new_only.get(f, "1.5's own") if ok else "new and not declared"
        else:
            ok, why = False, "gone from the new ELF"
        green &= ok
        lines.append("    %-5s %-18s %s" % ("ok" if ok else "RED", f, why))
    for f in sorted(set(touched) - set(res)):
        green = False
        lines.append("    RED   %-18s declared TOUCHED but in neither ELF" % f)
    lines.insert(0, "identity: %d driver function(s) identical, %d accounted "
                 "for below" % (same, len(lines)))
    return green, lines


def defaults_check(nsyms, want=None):
    """-> (green, lines): the new ELF's initial words."""
    want = DEFAULT_WORDS if want is None else want
    lines, green = [], True
    for name, words in sorted(want.items()):
        if name not in nsyms.by_name:
            green = False
            lines.append("    RED   %s is not in the new ELF" % name)
            continue
        a = nsyms.by_name[name][0]
        got = [nsyms.data(a + 4 * i, 4) for i in range(len(words))]
        ok = got == words
        green &= ok
        lines.append("    %-5s %s = %s%s" % ("ok" if ok else "RED", name, got,
                                              "" if ok else " != %s" % words))
    lines.insert(0, "defaults: the ELF's initial words")
    return green, lines


# -------------------------------------------------------------- self-test
SYN_SYMS = Syms([(0x803D0000, 4, "b", "nic_tx_ring"),
                 (0x803D0004, 4, "b", "nic_tx_mb"),
                 (0x803D0008, 4, "b", "nic_tx_ph"),
                 (0x803D000C, 4, "b", "nic_tx_idx"),
                 (0x803D0010, 4, "b", "nic_bufs"),
                 (0x803D0014, 4, "b", "other_global"),
                 (0x802B0000, 16, "d", "nic15_pol")],
                data=lambda a, n=4: {0x802B0004: 2}.get(a, 0))
SYN_SYMS0 = Syms(SYN_SYMS.rows, data=lambda a, n=4: 0)

SYN_OLD = """\
80000000:\taddiu\tsp,sp,-24
80000004:\tsw\tra,16(sp)
80000008:\tlui\tv1,0x803d
8000000c:\tlw\tv0,4(v1)
80000010:\tsll\ta0,s0,0x3
80000014:\taddu\tv0,v0,a0
80000018:\tsw\ta2,12(v0)
8000001c:\tsw\ta2,16(v0)
80000020:\tlw\tv0,16(v1)
80000024:\tsll\ta1,s0,0xb
80000028:\taddu\tv0,v0,a1
8000002c:\taddiu\ta2,v0,16386
80000030:\tsb\tt1,0(a2)
80000034:\tlw\tv0,8(v1)
80000038:\tsw\tt2,4(v0)
8000003c:\tjal\t80001000 <nic_wr>
80000040:\tnop
80000044:\tlui\ta0,0x803d
80000048:\tsw\tt3,12(a0)
8000004c:\tlw\tra,16(sp)
80000050:\tjr\tra
80000054:\taddiu\tsp,sp,24
"""


def _syn(text, repl=()):
    for a, b in repl:
        assert text.count(a) == 1, a
        text = text.replace(a, b)
    return parse(text)


def self_test():
    rows = []

    def ck(cid, cond, note):
        rows.append((cid, bool(cond), note))

    old = _syn(SYN_OLD)
    oa = annotate(old, SYN_SYMS)
    st = [s for _, s in stores(oa)]
    ck("S0", len(old) == 22 and st == [
        "sw [nic_tx_mb]+?+12", "sw [nic_tx_mb]+?+16", "sb [nic_bufs]+?+16386",
        "sw [nic_tx_ph]+4", "sw &nic_tx_idx"],
       "the parser reads 22 instructions and the evaluator names 5 stores: %s"
       % st)
    g, _ = compare(oa, annotate(_syn(SYN_OLD), SYN_SYMS), "same")
    ck("S1", g, "an identical listing is GREEN")
    sw = _syn(SYN_OLD, [("80000018:\tsw\ta2,12(v0)", "80000018:\tsw\ta2,16(v0)"),
                        ("8000001c:\tsw\ta2,16(v0)", "8000001c:\tsw\ta2,12(v0)")])
    g, _ = compare(oa, annotate(sw, SYN_SYMS), "swap")
    ck("S2", not g, "two stores swapped is RED")
    de = _syn(SYN_OLD, [("80000038:\tsw\tt2,4(v0)\n", "")])
    g, _ = compare(oa, annotate(de, SYN_SYMS), "del")
    ck("S3", not g, "a store deleted is RED")
    ad = _syn(SYN_OLD, [("80000040:\tnop\n", "80000040:\tnop\n"
                         "80000042:\tsw\tt4,20(a0)\n")])
    g, _ = compare(oa, annotate(ad, SYN_SYMS), "add")
    ck("S4", not g, "a store to another global added is RED")
    rn = SYN_OLD.replace("v0", "t7").replace("a2", "t8")
    g, _ = compare(oa, annotate(parse(rn), SYN_SYMS), "rename")
    ck("S5", g, "registers renamed throughout is GREEN (the normalisation "
                "is a positive control)")
    hk = _syn(SYN_OLD, [("80000044:\tlui\ta0,0x803d\n",
                         "80000044:\tlui\ta0,0x803d\n"
                         "80000045:\tlui\tt0,0x802b\n"
                         "80000046:\tlw\tt0,8(t0)\n"
                         "80000047:\tbeqz\tt0,80000049 <x+0x49>\n"
                         "80000048:\tnop\n"
                         "80000049:\tjal\t80002000 <nic15_note>\n"
                         "8000004a:\tmove\ta0,s0\n"
                         "8000004b:\tlui\ta0,0x803d\n")])
    ha = annotate(hk, SYN_SYMS)
    g, ln_ = compare(oa, ha, "hooks")
    ck("S6", g and any("nic15-load 1" in x and "nic15-call 1" in x
                       for x in ln_),
       "a nic15 load, a branch and a call to nic15_note are GREEN and named")
    ul = _syn(SYN_OLD, [("80000044:\tlui\ta0,0x803d\n",
                         "80000044:\tlui\ta0,0x803d\n"
                         "80000045:\tlw\tt6,0(a3)\n")])
    g, _ = compare(oa, annotate(ul, SYN_SYMS), "load")
    ck("S7", not g, "a new load from a computed address is RED")
    cl = _syn(SYN_OLD, [("80000044:\tlui\ta0,0x803d\n",
                         "80000044:\tlui\ta0,0x803d\n"
                         "80000045:\tjal\t80003000 <printk>\n")])
    g, _ = compare(oa, annotate(cl, SYN_SYMS), "call")
    ck("S8", not g, "a new call to a non-nic15 function is RED")
    # container search: the old has the body inlined among other stores
    cont = ("7ffffff0:\tlui\tv1,0x803d\n7ffffff4:\tsw\tzero,20(v1)\n" +
            SYN_OLD + "80000058:\tsw\tzero,20(v1)\n")
    lister = {("old", "f"): [], ("old", "c"): parse(cont),
              ("new", "f"): _syn(SYN_OLD), ("new", "c"): []}
    g, ln_ = compare_func("f@c", "old", "new", SYN_SYMS, SYN_SYMS,
                          lister=lambda e, fn: lister[(e, fn)])
    ck("S9", g and "found 1 time" in ln_[0],
       "a body inlined in its container is found once, and GREEN")
    lister[("new", "f")] = _syn(SYN_OLD, [("80000038:\tsw\tt2,4(v0)",
                                           "80000038:\tsw\tt2,8(v0)")])
    g, ln_ = compare_func("f@c", "old", "new", SYN_SYMS, SYN_SYMS,
                          lister=lambda e, fn: lister[(e, fn)])
    ck("S10", not g and "found 0 time" in ln_[0],
       "the same with one store's word changed is not found, and RED")
    # the default substitution: 1.5 adds nic15_pol.txoff where 1.4 had 2
    sub = _syn(SYN_OLD, [("8000002c:\taddiu\ta2,v0,16386",
                          "8000002c:\taddiu\ta2,v0,16384\n"
                          "8000002d:\tlui\tt9,0x802b\n"
                          "8000002e:\tlw\tt9,4(t9)\n"
                          "8000002f:\taddu\ta2,a2,t9")])
    g1, _ = compare(oa, annotate(sub, SYN_SYMS), "subst2")
    g0, _ = compare(oa, annotate(sub, SYN_SYMS0), "subst0")
    ck("S11", g1 and not g0, "a nic15 load folds to its initial value: GREEN "
                             "at 2, RED at 0")
    # inlined in BOTH: the containers are compared whole
    lb = {("old", "f"): [], ("new", "f"): [], ("old", "c"): parse(cont),
          ("new", "c"): parse(cont)}
    try:
        g, ln_ = compare_func("f@c", "old", "new", SYN_SYMS, SYN_SYMS,
                              lister=lambda e, fn: lb[(e, fn)])
    except Refused as e:
        g, ln_ = False, ["REFUSED: %s" % e]
    ck("S12", g and "neither" in ln_[0],
       "a body inlined in BOTH is compared as the whole container, and an "
       "identical one is GREEN")
    lb[("new", "c")] = parse(cont.replace("80000038:\tsw\tt2,4(v0)",
                                          "80000038:\tsw\tt2,8(v0)"))
    try:
        g, ln_ = compare_func("f@c", "old", "new", SYN_SYMS, SYN_SYMS,
                              lister=lambda e, fn: lb[(e, fn)])
    except Refused as e:
        g, ln_ = None, ["REFUSED: %s" % e]
    ck("S13", g is False and "neither" in ln_[0],
       "the same with one store's word changed in the new container is RED")
    le = {("old", "f"): [], ("new", "f"): parse(
        "80000000:\taddiu\tsp,sp,-8\n80000004:\tjr\tra\n"
        "80000008:\taddiu\tsp,sp,8\n"), ("old", "c"): parse(cont),
        ("new", "c"): []}
    try:
        compare_func("f@c", "old", "new", SYN_SYMS, SYN_SYMS,
                     lister=lambda e, fn: le[(e, fn)])
        s14 = False
    except Refused:
        s14 = True
    ck("S14", s14, "a body with no store is REFUSED, not searched as an "
                   "empty run")
    # identity: a global that only MOVED reads the same; a renamed register
    # does not (the store sequence, S5, is blind to it -- this is stricter)
    moved_syms = Syms([(a + 0x100, s, t, n) for a, s, t, n in SYN_SYMS.rows],
                      data=lambda a, n=4: 0)
    moved = SYN_OLD
    for o, n_ in (("lw\tv0,4(v1)", "lw\tv0,260(v1)"),
                  ("lw\tv0,16(v1)", "lw\tv0,272(v1)"),
                  ("lw\tv0,8(v1)", "lw\tv0,264(v1)"),
                  ("sw\tt3,12(a0)", "sw\tt3,268(a0)")):
        assert moved.count(o) == 1, o
        moved = moved.replace(o, n_)
    lid = {("o", "f"): parse(SYN_OLD), ("n", "f"): parse(moved)}
    r1 = identity("o", "n", SYN_SYMS, moved_syms,
                  lister=lambda e, fn: lid[(e, fn)], funcs=({"f"}, {"f"}))
    lid[("n", "f")] = parse(SYN_OLD.replace("80000010:\tsll\ta0,s0,0x3",
                                            "80000010:\tsll\ta1,s0,0x3"))
    r2 = identity("o", "n", SYN_SYMS, SYN_SYMS,
                  lister=lambda e, fn: lid[(e, fn)], funcs=({"f"}, {"f"}))
    form = ("%x:\tlui\ta0,0x803d\n%x:\taddiu\ta0,a0,%d\n"
            "%x:\tbeqz\ta1,%x <g+0x10>\n%x:\tnop\n"
            "%x:\tjal\t80001000 <nic_wr>\n%x:\tnop\n"
            "%x:\tjr\tra\n%x:\tnop\n")

    def at(base, imm):
        a = [base + 4 * i for i in range(8)]
        return form % (a[0], a[1], imm, a[2], a[4], a[3], a[4], a[5], a[6],
                       a[7])
    lid[("o", "g")] = parse(at(0x80000000, 12))
    lid[("n", "g")] = parse(at(0x80000140, 268))
    r3 = identity("o", "n", SYN_SYMS, moved_syms,
                  lister=lambda e, fn: lid[(e, fn)], funcs=({"g"}, {"g"}))
    lid[("n", "g")] = parse(at(0x80000000, 16))
    r4 = identity("o", "n", SYN_SYMS, SYN_SYMS,
                  lister=lambda e, fn: lid[(e, fn)], funcs=({"g"}, {"g"}))
    # an anonymous literal that moved, and a copied high half
    lit = ("80000000:\tlui\ta0,0x8029\n80000004:\taddiu\ta0,a0,%d\n"
           "80000008:\tlui\tv1,0x803f\n8000000c:\tmove\tt2,v1\n"
           "80000010:\tjr\tra\n80000014:\tnop\n")
    s_o = Syms([(0x803E0000, 0x20000, "b", "big")],
               anon=lambda a: {0x80292EB4: 'str:"RLXFW-N-ALLOC="',
                               0x80292EC4: 'str:"RLXFW-N-ARM="'}.get(a))
    s_n = Syms([(0x803E4000, 0x20000, "b", "big")],
               anon=lambda a: {0x80293070: 'str:"RLXFW-N-ALLOC="',
                               0x80293080: 'str:"RLXFW-N-ARM="'}.get(a))
    lid[("o", "h")] = parse(lit % 0x2EB4)
    lid[("n", "h")] = parse(lit % 0x3070)
    r5 = identity("o", "n", s_o, s_n, lister=lambda e, fn: lid[(e, fn)],
                  funcs=({"h"}, {"h"}))
    lid[("n", "h")] = parse(lit % 0x3080)
    r6 = identity("o", "n", s_o, s_n, lister=lambda e, fn: lid[(e, fn)],
                  funcs=({"h"}, {"h"}))
    ck("S15", r1["f"][0] == "same" and r2["f"][0] == "differ" and
       r3["g"][0] == "same" and r4["g"][0] == "differ" and
       r5["h"][0] == "same" and r6["h"][0] == "differ",
       "identity: a listing whose globals only moved -- loads, an address "
       "formed by lui/addiu, an anonymous literal (by content), a copied high "
       "half -- is the same; one register renamed, another global's address "
       "or another literal differs")
    t = {"g": "hooked"}
    g_a, _ = identity_verdict({"f": ("same", ""), "g": ("differ", "")}, t, {})
    g_b, _ = identity_verdict({"f": ("differ", "x"), "g": ("differ", "")}, t, {})
    g_c, _ = identity_verdict({"f": ("same", ""), "g": ("same", "")}, t, {})
    g_d, _ = identity_verdict({"f": ("same", ""), "g": ("differ", ""),
                               "h": ("new-only", "")}, t, {})
    g_e, _ = identity_verdict({"f": ("same", ""), "g": ("differ", ""),
                               "nic15_x": ("new-only", "")}, t, {})
    ck("S16", g_a and not g_b and not g_c and not g_d and g_e,
       "identity verdict, both ways: an undeclared difference, a stale "
       "declaration and an undeclared new function are RED")
    wsyms = Syms([(0x802B0000, 16, "d", "nic15_pol"),
                  (0x802B0010, 4, "d", "nic15_show")],
                 data=lambda a, n=4: {0x802B0004: 2, 0x802B0010: 60}.get(a, 0))
    bsyms = Syms(wsyms.rows,
                 data=lambda a, n=4: {0x802B0010: 60}.get(a, 0))
    ck("S17", defaults_check(wsyms)[0] and not defaults_check(bsyms)[0] and
       not defaults_check(SYN_SYMS)[0],
       "defaults: {0, 2, 0, 0} and 60 are GREEN; txoff 0 is RED; a missing "
       "nic15_show is RED")
    ck("S18", "nic_do_engine" in DEFAULT_FUNCS and "nic_ndo_open" in
       DEFAULT_FUNCS and "nic_recov_fn" in DEFAULT_FUNCS and "nic_poll" in
       DEFAULT_FUNCS and set(TOUCHED) & set(DEFAULT_FUNCS) >= {
           "nic_xmit", "nic_do_engine", "nic_do_arm", "nic_ndo_open"},
       "the default list carries the review's functions, and every hooked "
       "function on the default path is store-compared")
    fails = 0
    for cid, ok, note in rows:
        print("  %-4s %-4s %s" % ("ok" if ok else "FAIL", cid, note))
        fails += 0 if ok else 1
    print("RESULT: %d passed, %d failed" % (len(rows) - fails, fails))
    return 1 if fails else 0


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--func", action="append")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    try:
        if not a.old or not a.new:
            raise Refused("give --old ELF and --new ELF, or --self-test")
        for tool in (OBJDUMP, NM, READELF):
            if not shutil.which(tool):
                raise Refused("no %s on PATH (binutils-mips-linux-gnu)" % tool)
        for p in (a.old, a.new):
            if not os.path.isfile(p):
                raise Refused("no ELF at %s" % p)
        osyms, nsyms = Syms.from_elf(a.old), Syms.from_elf(a.new)
        green_all = True
        for spec in a.func or DEFAULT_FUNCS:
            g, lines = compare_func(spec, a.old, a.new, osyms, nsyms)
            green_all &= g
            for x in lines:
                print(x)
            print("  %s %s" % ("GREEN" if g else "RED  ", spec))
        if "nic15_pol" in nsyms.by_name and "nic15_pol" not in osyms.by_name:
            for label, (g, lines) in (
                    ("defaults", defaults_check(nsyms)),
                    ("identity", identity_verdict(identity(
                        a.old, a.new, osyms, nsyms)))):
                green_all &= g
                for x in lines:
                    print(x)
                print("  %s %s" % ("GREEN" if g else "RED  ", label))
        else:
            print("identity, defaults: not run -- only for 1.4 (no nic15_pol) "
                  "against 1.5")
    except Refused as e:
        print("storeseq: REFUSED: %s" % e)
        return 2
    except (OSError, subprocess.SubprocessError) as e:
        print("storeseq: REFUSED: %s: %s" % (type(e).__name__, e))
        return 2
    print("RESULT: %s -- %s against %s" % (
        "GREEN" if green_all else "RED", os.path.basename(a.new),
        os.path.basename(a.old)))
    return 0 if green_all else 1


if __name__ == "__main__":
    sys.exit(main())
