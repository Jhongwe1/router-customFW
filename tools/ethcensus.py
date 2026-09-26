#!/usr/bin/env python3
"""ethcensus -- is any of the vendor's Ethernet driver left in a vmlinux?

WHY THIS EXISTS
---------------
`R6b-8`'s definition of done (`PROGRESS.md`) is `ping` both ways "with no
vendor Ethernet code in `vmlinux` (a symbol census)".  A census that reads 0
is making a claim, so this is three censuses, two of which share no parsing,
and each has a control that must read non-zero on a vendor-present build:

  1. object census -- the leaf objects the link names, found by walking the
     `ld -r` chains from `.vmlinux.cmd` down through every `built-in.o`'s
     `.cmd`: 0 in scope.  A `built-in.o` with no `ld -r` `.cmd` must be
     kbuild's empty archive, or the run REFUSES: its objects would be
     counted under its own path.
  2. symbol census -- the FUNC and OBJECT names (global and local) that the
     reference build's in-scope objects define, looked up in the new
     `vmlinux`'s symbol table: exactly the ten seam names, each defined by the
     seam object and by no other leaf.
  3. string census -- `imgprocs`' NUL-bounded search, inverted, on the flat
     image: 0 of the vendor-unique `/proc/rtl865x/` names, while rlxfw's own
     `rtl819x-switch` is present and a synthetic name is not.

SCOPE -- the owner's ruling, 2026-09-26
---------------------------------------
Vendor Ethernet code = every object under `drivers/net/rtl819x/` plus
`drivers/net/rtk_vlan.o`.  The vendor code that STAYS -- the IPv4 fast path,
the feature glue, the WLAN driver and `rtl_gpio.c` (which writes
`PIN_MUX_SEL`) -- is printed by every run with its leaf count in the build
read, so nobody reads the census wider than it is.  The ten seam names
(`SEAM_NAMES`, R6b-8 design section 1.2) are where that code meets the tree
that leaves.

THE PARSE, AND WHY TWO
----------------------
The design's first population (segment 113) read `readelf -sW` with a regex
that assumed `Vis` is followed by `Ndx`.  A MIPS16 function carries
`[MIPS16]` between them, so its line did not match and was dropped without a
word, and a size above 99,999 prints in hex (`0x19f80`), which a `\\d+` size
field also drops.  Here:
  * every readelf symbol line must parse, field by field, or the run REFUSES;
    `st_other` is taken as a bracket group of one or more tokens
    (`[MIPS16]`, `[<other>: 88]`), never assumed absent;
  * the result is compared, symbol by symbol on seven fields (object or
    archive member, name, binding, type, value, size, section name), with
    `nm -f sysv`, which reads the same file through BFD rather than
    readelf's own ELF reader.  Any disagreement is printed and REFUSED: the
    population is frozen only where the two agree;
  * `check` also reads the population names through `System.map`, kbuild's
    own `nm` listing of vmlinux, and REFUSES without one, as `population`
    does.
The binaries are the host's `binutils-mips-linux-gnu` under /usr/bin, never
the vendor's toolchain.

量 2026-09-27, `r6b6q2` (recipe `acf8ed3d`, vmlinux `9e0ff326`): 627 leaves
through 89 `ld -r` links, 22 in scope; the parsers agree on all 13,897
defined symbols of the leaves; 907 FUNC/OBJECT names in scope (512 global or
weak), 13 of them MIPS16; 8 excluded; a population of 899, of which 898 are
in `System.map` (`__exitcall_re865x_exit` is not).  The segment-113 regex
read 893 and 886: it dropped the 13 MIPS16 names and `eth_skb_buf`, whose
size prints in hex, and so could not see that `rtk_dequeue` collides with
the WLAN driver's.  Of the 42 registered `/proc` names, 6 are carried by a
vendor object only and 7 by retained code too, the same 7 as
`imgprocs.SHARED`.

THE FIXTURE
-----------
`population` writes the reference population as a sorted name list under a
header naming the build, its vmlinux's sha256 and every count, and `check`
reads it (default `tools/ethcensus-population.txt`), so a census of a new
build needs no reference tree.  Names ALSO defined by an object outside scope
are excluded from the population BY NAME in the header -- present in any
vmlinux, they could not discriminate -- and a name the new build defines
outside scope that the reference did not is a RED, not an exclusion.

WHAT IT CANNOT SEE
------------------
Vendor code under another path (the scope is a path rule); a vendor function
the compiler inlined into an out-of-scope object (it leaves no symbol); a
NOTYPE label (counted and printed, not in the population); and whether the
image is the one the board boots -- `RLXFW-ID0` is the bench's half.  A name
absent is a name no symbol table entry carries, not proof no byte of vendor
code survives.

usage
    ethcensus.py population --build TREE --out FIXTURE
    ethcensus.py check --build TREE --image FLAT --seam OBJ [--fixture FIXTURE]
    ethcensus.py self-test [--keep DIR]

exit: 0 green / fixture written, 1 red, 2 refused, 3 usage.
"""
import collections
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:  # the NUL-bounded method, OWN and SHARED; exit 2, never a traceback
    import imgprocs  # noqa: E402
except ImportError as _e:
    if isinstance(_e, ModuleNotFoundError) and _e.name == "imgprocs":
        print("REFUSED: imgprocs.py not found beside ethcensus.py (%s)"
              % HERE)
    else:
        print("REFUSED: imgprocs.py beside ethcensus.py does not import: "
              "%s: %s" % (type(_e).__name__, _e))
    sys.exit(2)
_lack = [a for a in ("OWN", "SHARED", "parse_names", "count")
         if not hasattr(imgprocs, a)]
if _lack:
    print("REFUSED: imgprocs.py beside ethcensus.py lacks %s"
          % ", ".join(_lack))
    sys.exit(2)

VERSION = "ethcensus 1.0"
BIN = "/usr/bin"
READELF = os.path.join(BIN, "mips-linux-gnu-readelf")
NM = os.path.join(BIN, "mips-linux-gnu-nm")
OBJCOPY = os.path.join(BIN, "mips-linux-gnu-objcopy")
AS = os.path.join(BIN, "mips-linux-gnu-as")
LD = os.path.join(BIN, "mips-linux-gnu-ld")
AR = os.path.join(BIN, "mips-linux-gnu-ar")

SCOPE_DIR = "drivers/net/rtl819x/"
SCOPE_OBJ = "drivers/net/rtk_vlan.o"
SCOPE_TEXT = ("vendor Ethernet code = every object under %s plus %s "
              "(the owner's ruling, 2026-09-26)" % (SCOPE_DIR, SCOPE_OBJ))

#: The vendor code that stays in the image, printed by every run.
KEPT = (("net/rtl/fastpath/", "the vendor IPv4 fast path"),
        ("net/rtl/features/", "the vendor feature glue"),
        ("drivers/net/wireless/rtl8192cd/", "the vendor WLAN driver"),
        ("drivers/char/rtl_gpio.o",
         "the vendor GPIO driver, which writes PIN_MUX_SEL"))

#: R6b-8 design section 1.2: the ten names the kept code takes from the tree
#: that leaves, which rlxfw's seam object provides.
SEAM_NAMES = ("bsp_swcore_init", "rtl865x_setNetifType",
              "rtl_get_hw_fdb_age", "igmp_delete_init_netlink",
              "cached_dev", "cached_dev2", "cached_eth_addr",
              "cached_eth_addr2", "update_hw_l2table", "rtl865x_curOpMode")

PROC_SRC = "drivers/net/rtl819x/rtl865x_proc_debug.c"
SANITY = imgprocs.OWN             # rlxfw's own /proc entry: must be present
ABSENT = "zzzz-not-a-name"        # must be absent
FIXTURE = os.path.join(HERE, "ethcensus-population.txt")
MAGIC = "# ethcensus-population 1"

TYPES = {"NOTYPE", "OBJECT", "FUNC", "SECTION", "FILE", "COMMON", "TLS",
         "GNU_IFUNC"}
BINDS = {"LOCAL", "GLOBAL", "WEAK", "UNIQUE"}
VISES = {"DEFAULT", "INTERNAL", "HIDDEN", "PROTECTED"}


class Refusal(Exception):
    pass


Sym = collections.namedtuple(
    "Sym", "member name bind type value size section mips16")


# --------------------------------------------------------------------- paths

def in_scope(path):
    p = os.path.normpath(path.split("[", 1)[0])
    return p.startswith(SCOPE_DIR) or p == SCOPE_OBJ


def container(member):
    """`lib/lib.a[ctype.o]` -> `lib/lib.a`; a plain object is itself."""
    return member.split("[", 1)[0]


def read_cmd(tree, rel):
    """The kbuild command that produced `rel`, or None."""
    d, b = os.path.split(rel)
    p = os.path.join(tree, d, "." + b + ".cmd")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("cmd_") and ":=" in line:
                return line.split(":=", 1)[1]
    return None


def link_inputs(tokens):
    """The .o/.a inputs of a link command, the output excluded."""
    out = tokens[tokens.index("-o") + 1] if "-o" in tokens else None
    return [t for t in tokens if t.endswith((".o", ".a")) and t != out]


#: kbuild's `built-in.o` for a directory that builds nothing: `ar rcs` of no
#: member.  Any other `built-in.o` is an `ld -r` link.
EMPTY_AR = b"!<arch>\n"


def walk(tree):
    """(leaves, number of ld -r links): every object the vmlinux link reads,
    followed down every `ld -r` to the objects that are not links.  A
    `built-in.o` reached as a leaf must be kbuild's empty archive: one that
    is not is a link whose `.cmd` is missing, and the objects it holds --
    under any path -- would be counted as its own out-of-scope path."""
    top = read_cmd(tree, "vmlinux")
    if top is None:
        raise Refusal("no .vmlinux.cmd in %s -- not a built kernel tree"
                      % tree)
    toks = top.split()
    if "-o" not in toks:
        raise Refusal(".vmlinux.cmd has no -o: %s" % top.strip()[:120])
    stack = list(reversed(link_inputs(toks)))
    if not stack:
        raise Refusal(".vmlinux.cmd names no object")
    leaves, seen, links = [], set(), 0
    while stack:
        rel = os.path.normpath(stack.pop())
        if rel in seen:
            continue
        seen.add(rel)
        if not os.path.isfile(os.path.join(tree, rel)):
            raise Refusal("the link names %s and the tree has no such file"
                          % rel)
        cmd = read_cmd(tree, rel) if rel.endswith(".o") else None
        if cmd is not None:
            t = cmd.split()
            if "-r" in t and "-o" in t:
                links += 1
                stack.extend(reversed(link_inputs(t)))
                continue
        if os.path.basename(rel) == "built-in.o":
            with open(os.path.join(tree, rel), "rb") as fh:
                head = fh.read(len(EMPTY_AR) + 1)
            if head != EMPTY_AR:
                raise Refusal(
                    "%s is reached as a leaf but is not an empty archive: a "
                    "built-in.o is an ld -r link, so its .cmd is %s, and the "
                    "objects it links are invisible to the object census"
                    % (rel, "missing" if cmd is None else "not an ld -r"))
        leaves.append(rel)
    return leaves, links


# ------------------------------------------------------------------- parsing

SYM_LINE = re.compile(r"^\s*\d+:\s")
SEC_LINE = re.compile(r"^\s*\[\s*(\d+)\]\s?(.*)$")
HEX = re.compile(r"^[0-9a-f]+$")


def parse_readelf(text, first):
    """Every defined, named symbol that is not SECTION or FILE, from
    `readelf -W -S -s` over one or more files.  A symbol line that does not
    parse is a refusal, never a skip."""
    member, secs, out = first, {}, []
    for line in text.splitlines():
        if line.startswith("File: "):
            m = line[6:].strip()
            a = re.match(r"^(.*)\((.*)\)$", m)
            member = "%s[%s]" % a.groups() if a else m
            secs = {}
            continue
        s = SEC_LINE.match(line)
        if s:
            idx, rest = int(s.group(1)), s.group(2).split()
            secs[idx] = "" if idx == 0 or not rest else rest[0]
            continue
        if not SYM_LINE.match(line):
            continue
        f = line.split()
        if len(f) < 7:
            raise Refusal("readelf line not understood (%s): %r"
                          % (member, line))
        val, size, typ, bind, vis = f[1:6]
        rest = f[6:]
        other = ""
        if rest[0].startswith("["):
            # st_other: `[MIPS16]`, or `[<other>: 88]` across two tokens.
            j = 0
            while j < len(rest) and not rest[j].endswith("]"):
                j += 1
            if j == len(rest):
                raise Refusal("readelf st_other bracket never closes (%s): "
                              "%r" % (member, line))
            other, rest = " ".join(rest[:j + 1]), rest[j + 1:]
        if not rest or len(rest) > 2:
            raise Refusal("readelf line not understood -- %s after Vis "
                          "(%s): %r" % ("no Ndx" if not rest
                                        else "more than Ndx and a name",
                                        member, line))
        ndx, name = rest[0], (rest[1] if len(rest) > 1 else "")
        size_ok = size.isdigit() or re.match(r"^0x[0-9a-f]+$", size)
        if (not HEX.match(val) or not size_ok or typ not in TYPES
                or bind not in BINDS or vis not in VISES
                or not (ndx in ("UND", "ABS", "COM") or ndx.isdigit())):
            raise Refusal("readelf line not understood (%s): %r"
                          % (member, line))
        if typ in ("SECTION", "FILE") or ndx == "UND" or not name:
            continue
        if ndx.isdigit() and int(ndx) not in secs:
            raise Refusal("symbol %s in %s names section %s, which readelf "
                          "-S did not list" % (name, member, ndx))
        sec = {"ABS": "*ABS*", "COM": "*COM*"}.get(ndx) or secs[int(ndx)]
        out.append(Sym(member, name, bind, typ, int(val, 16),
                       int(size, 16) if size.startswith("0x") else int(size),
                       sec, "MIPS16" in other))
    return out


def parse_nm(text, first):
    """The same population from `nm -f sysv`, as comparable tuples."""
    member, out = first, []
    for line in text.splitlines():
        if line.startswith("Symbols from ") and line.endswith(":"):
            member = line[len("Symbols from "):-1]
            continue
        if "|" not in line:
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 7:
            raise Refusal("nm line not understood (%s): %r" % (member, line))
        name, val, cls, typ, size, _line, sec = p
        if sec == "*UND*":
            continue
        if not name or not HEX.match(val) or len(cls) != 1:
            raise Refusal("nm line not understood (%s): %r" % (member, line))
        if cls in "WwVv":
            bind = "WEAK"
        elif cls == "u":
            bind = "UNIQUE"
        elif cls.islower():
            bind = "LOCAL"
        else:
            bind = "GLOBAL"
        out.append((member, name, bind, typ, int(val, 16),
                    int(size, 16) if size else 0, sec))
    return out


def key(s):
    return (s.member, s.name, s.bind, s.type, s.value, s.size, s.section)


def compare(r_syms, n_tuples):
    """Lines describing every disagreement; empty when they agree."""
    r = collections.Counter(key(s) for s in r_syms)
    n = collections.Counter(n_tuples)
    diff = []
    for t in sorted((r - n).elements()):
        diff.append("readelf only: %s %s %s %s value %x size %d %s" % t)
    for t in sorted((n - r).elements()):
        diff.append("nm only:      %s %s %s %s value %x size %d %s" % t)
    return diff


def run(argv, cwd):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise Refusal("%s exited %d: %s" % (os.path.basename(argv[0]),
                                            p.returncode,
                                            p.stderr.strip()[:300]))
    return p.stdout


#: The readelf parser `symbols()` uses; the self-test swaps in the old one.
PARSE_READELF = parse_readelf


def symbols(tree, rels, batch=64):
    """(syms, disagreements) over the files `rels`, each read twice."""
    need(READELF, NM)
    syms, diff = [], []
    for i in range(0, len(rels), batch):
        chunk = rels[i:i + batch]
        r = PARSE_READELF(run([READELF, "-W", "-S", "-s"] + chunk, tree),
                          chunk[0])
        n = parse_nm(run([NM, "-f", "sysv"] + chunk, tree), chunk[0])
        syms.extend(r)
        diff.extend(compare(r, n))
    return syms, diff


def refuse_on(diff, what):
    """Print every disagreement, in-scope ones first, and refuse."""
    if diff:
        # "readelf only: <member> ..." / "nm only:      <member> ..."
        diff = sorted(diff, key=lambda d: (not in_scope(d.split()[2]), d))
        ins = sum(1 for d in diff if in_scope(d.split()[2]))
        for d in diff[:30]:
            print("    " + d)
        if len(diff) > 30:
            print("    ... and %d more" % (len(diff) - 30))
        raise Refusal("readelf and nm disagree on %d symbol(s) of %s, %d of "
                      "them in scope -- the population is frozen only where "
                      "the two parsers agree" % (len(diff), what, ins))


def need(*paths):
    missing = [p for p in paths if not os.access(p, os.X_OK)]
    if missing:
        raise Refusal("missing host binutils: %s (binutils-mips-linux-gnu)"
                      % ", ".join(missing))


# ------------------------------------------------------------- string search

def elf_alloc(data, where):
    """The bytes of every SHF_ALLOC, non-NOBITS section, NUL-separated."""
    import struct
    if data[:4] != b"\x7fELF":
        raise Refusal("%s is not ELF" % where)
    e = ">" if data[5] == 2 else "<"
    if data[4] == 1:
        shoff, = struct.unpack_from(e + "I", data, 0x20)
        shentsize, shnum = struct.unpack_from(e + "HH", data, 0x2E)
        fmt = e + "IIIIIIIIII"
    else:
        shoff, = struct.unpack_from(e + "Q", data, 0x28)
        shentsize, shnum = struct.unpack_from(e + "HH", data, 0x3A)
        fmt = e + "IIQQQQIIQQ"
    if shoff and not shnum:
        raise Refusal("%s uses extended section numbering" % where)
    parts = []
    for i in range(shnum):
        f = struct.unpack_from(fmt, data, shoff + i * shentsize)
        typ, flags, off, size = f[1], f[2], f[4], f[5]
        if flags & 2 and typ != 8:
            parts.append(data[off:off + size])
    return b"\x00" + b"\x00".join(parts) + b"\x00"


def blobs(tree, rel):
    """[(member, allocated bytes)] of one leaf, archive members included."""
    with open(os.path.join(tree, rel), "rb") as fh:
        data = fh.read()
    if data[:8] == b"!<thin>\n":
        raise Refusal("%s is a thin archive" % rel)
    if data[:8] != b"!<arch>\n":
        return [(rel, elf_alloc(data, rel))]
    out, pos, names = [], 8, b""
    while pos + 60 <= len(data):
        hdr = data[pos:pos + 60]
        name = hdr[:16].decode("ascii", "replace").rstrip()
        size = int(hdr[48:58].decode("ascii").strip())
        body = data[pos + 60:pos + 60 + size]
        if name == "//":
            names = body
        elif name not in ("/", "/SYM64/"):
            if name.startswith("/") and name[1:].isdigit():
                o = int(name[1:])
                name = names[o:names.index(b"/\n", o)].decode("ascii")
            mem = "%s[%s]" % (rel, name.rstrip("/"))
            out.append((mem, elf_alloc(body, mem)))
        pos += 60 + size + (size & 1)
    return out


def carriers(tree, leaves, names):
    """{name: [members whose allocated bytes hold NUL name NUL]}."""
    hit = collections.defaultdict(list)
    pats = [(n, b"\x00" + n.encode() + b"\x00") for n in names]
    for rel in leaves:
        for mem, blob in blobs(tree, rel):
            for n, pat in pats:
                if pat in blob:
                    hit[n].append(mem)
    return hit


# ------------------------------------------------------------------- helpers

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sysmap_names(tree):
    p = os.path.join(tree, "System.map")
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        return {f[2] for f in (l.split() for l in fh) if len(f) == 3}


def print_scope(leaves):
    print("scope     " + SCOPE_TEXT)
    print("kept      vendor code this census does NOT look at, and its "
          "leaves in this build:")
    for pre, what in KEPT:
        n = sum(1 for l in leaves if (l == pre if pre.endswith(".o")
                                      else l.startswith(pre)))
        print("            %-34s %4d  %s" % (pre, n, what))


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ---------------------------------------------------------------- population

def population(tree, out_path):
    tree = os.path.abspath(tree)
    vm = os.path.join(tree, "vmlinux")
    if not os.path.isfile(vm):
        raise Refusal("no vmlinux in %s" % tree)
    leaves, links = walk(tree)
    scope = [l for l in leaves if in_scope(l)]
    print(VERSION + "  --  population")
    print("  build   %s" % tree)
    print("  vmlinux sha256 %s  (%d bytes)" % (sha256(vm), os.path.getsize(vm)))
    print_scope(leaves)
    print("object    %d leaves through %d ld -r links; %d in scope"
          % (len(leaves), links, len(scope)))
    if not scope:
        raise Refusal("empty population: 0 leaves in scope -- a reference "
                      "must be a vendor-present build")
    syms, diff = symbols(tree, leaves)
    refuse_on(diff, "the reference's leaves")
    print("parsers   readelf and nm agree on all %d defined symbols of the "
          "%d leaves (member, name, binding, type, value, size, section)"
          % (len(syms), len(leaves)))
    vend = [s for s in syms if in_scope(container(s.member))]
    outside = collections.defaultdict(set)
    for s in syms:
        if not in_scope(container(s.member)):
            outside[s.name].add(s.member)
    fo = [s for s in vend if s.type in ("FUNC", "OBJECT")]
    names = {s.name for s in fo}
    glob = {s.name for s in fo if s.bind in ("GLOBAL", "WEAK")}
    m16 = sorted({s.name for s in fo if s.mips16})
    notype = sorted({s.name for s in vend if s.type not in ("FUNC", "OBJECT")})
    excluded = sorted(n for n in names if n in outside)
    pop = sorted(names - set(excluded))
    print("symbols   %d FUNC/OBJECT names defined in scope (%d global or "
          "weak), %d of them MIPS16: %s"
          % (len(names), len(glob), len(m16), " ".join(m16) or "-"))
    print("          %d other-typed names in scope, NOT in the population: %s"
          % (len(notype), " ".join(notype) or "-"))
    print("excluded  %d also defined outside scope (present in any vmlinux, "
          "so they cannot discriminate):" % len(excluded))
    for n in excluded:
        o = sorted(outside[n])
        print("            %-28s %s%s" % (n, ", ".join(o[:2]),
                                          " (+%d)" % (len(o) - 2)
                                          if len(o) > 2 else ""))
    if not pop:
        raise Refusal("empty population: no unambiguous name in scope")
    missing = [n for n in SEAM_NAMES if n not in pop]
    if missing:
        raise Refusal("seam name(s) %s are not in the population -- the "
                      "census could not see them" % ", ".join(missing))
    smap = sysmap_names(tree)
    if smap is None:
        raise Refusal("no System.map in %s" % tree)
    in_map = sorted(set(pop) & smap)
    print("population %d names; %d in System.map; not there: %s"
          % (len(pop), len(in_map),
             " ".join(sorted(set(pop) - smap)) or "-"))

    src = os.path.join(tree, PROC_SRC)
    if not os.path.isfile(src):
        raise Refusal("no %s in the tree" % PROC_SRC)
    with open(src, encoding="utf-8", errors="replace") as fh:
        regs = imgprocs.parse_names(fh.read())
    if not regs:
        raise Refusal("no create_proc_entry site in %s" % PROC_SRC)
    hit = carriers(tree, leaves, regs + [SANITY, ABSENT])
    if not any(not in_scope(m) for m in hit.get(SANITY, [])):
        raise Refusal("control: %s is carried by no out-of-scope leaf -- the "
                      "string search is broken" % SANITY)
    if hit.get(ABSENT):
        raise Refusal("control: the synthetic name %s was found" % ABSENT)
    shared = sorted(n for n in regs if any(not in_scope(m)
                                            for m in hit.get(n, [])))
    unique = sorted(n for n in regs if hit.get(n) and n not in shared)
    theirs = sorted(set(imgprocs.SHARED) & set(regs))
    print("strings   %d registered /proc names; carried by a vendor object "
          "only: %d (%s); also by retained code: %d (%s)"
          % (len(regs), len(unique), " ".join(unique), len(shared),
             " ".join(shared)))
    if shared != theirs:
        raise Refusal("the shared /proc names derived here (%s) are not "
                      "imgprocs.SHARED's (%s) -- two derivations disagree"
                      % (" ".join(shared), " ".join(theirs)))
    print("          agrees with imgprocs.SHARED (a derivation that shares "
          "no code with this one)")
    if not unique:
        raise Refusal("no vendor-unique /proc name: the string census "
                      "would have no positive control")

    head = [MAGIC,
            "# build %s" % tree,
            "# vmlinux %s %d" % (sha256(vm), os.path.getsize(vm)),
            "# scope %s + %s" % (SCOPE_DIR, SCOPE_OBJ),
            "# leaves %d links %d scope %d" % (len(leaves), links, len(scope)),
            "# defined %d global %d mips16 %d" % (len(names), len(glob),
                                                  len(m16)),
            "# excluded %d %s" % (len(excluded), " ".join(excluded)),
            "# population %d sysmap %d" % (len(pop), len(in_map)),
            "# proc %d %s" % (len(unique), " ".join(unique))]
    write_atomic(out_path, "\n".join(head + pop) + "\n")
    print("wrote     %s (%d names)" % (out_path, len(pop)))
    return 0


def load_fixture(path):
    if not os.path.isfile(path):
        raise Refusal("no fixture %s" % path)
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    if lines[-1] != "":
        raise Refusal("fixture %s does not end in a newline" % path)
    lines = lines[:-1]
    if not lines or lines[0] != MAGIC:
        raise Refusal("fixture %s does not start with %r" % (path, MAGIC))
    h, names = {}, []
    for l in lines[1:]:
        if l.startswith("# "):
            k, _, v = l[2:].partition(" ")
            h[k] = v
        else:
            names.append(l)
    for k in ("build", "vmlinux", "population", "excluded", "proc"):
        if k not in h:
            raise Refusal("fixture %s has no '# %s' line" % (path, k))
    try:
        n_pop = int(h["population"].split()[0])
        pw = h["proc"].split()
        proc = pw[1:]
        if int(pw[0]) != len(proc):
            raise ValueError
    except (ValueError, IndexError):
        raise Refusal("fixture %s: a count line does not parse" % path)
    if n_pop != len(names):
        raise Refusal("fixture %s: header says %d names, the list holds %d"
                      % (path, n_pop, len(names)))
    if not names:
        raise Refusal("fixture %s: empty population -- a census of nothing "
                      "reads 0 on every image" % path)
    if names != sorted(set(names)):
        raise Refusal("fixture %s: names not sorted and unique" % path)
    if not proc:
        raise Refusal("fixture %s: no vendor-unique /proc name" % path)
    missing = [n for n in SEAM_NAMES if n not in names]
    if missing:
        raise Refusal("fixture %s lacks seam name(s) %s" % (path,
                                                            " ".join(missing)))
    return h, names, proc


# --------------------------------------------------------------------- check

def flat_of(vm):
    need(OBJCOPY)
    d = tempfile.mkdtemp(prefix="ethcensus-")
    try:
        out = os.path.join(d, "flat")
        run([OBJCOPY, "-O", "binary", vm, out], d)
        return sha256(out)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def check(tree, image, seam, fixture):
    tree = os.path.abspath(tree)
    h, pop, proc = load_fixture(fixture)
    vm = os.path.join(tree, "vmlinux")
    if not os.path.isfile(vm):
        raise Refusal("no vmlinux in %s" % tree)
    if not os.path.isfile(image):
        raise Refusal("no image %s" % image)
    smap = sysmap_names(tree)
    if smap is None:
        raise Refusal("no System.map in %s -- check reads the symbol table "
                      "a second time through it, as population does" % tree)
    print(VERSION + "  --  check")
    print("  build   %s" % tree)
    print("  vmlinux sha256 %s" % sha256(vm))
    print("  image   %s" % image)
    print("  fixture %s  (reference %s, vmlinux %s)"
          % (fixture, h["build"], h["vmlinux"].split()[0][:16]))
    derived, given = flat_of(vm), sha256(image)
    if derived != given:
        raise Refusal("the image is not this build's flat image: sha256 %s, "
                      "objcopy -O binary of its vmlinux gives %s"
                      % (given[:16], derived[:16]))
    leaves, links = walk(tree)
    print_scope(leaves)
    exc = h["excluded"].split()
    print("excluded  from the population by the reference: %s"
          % (" ".join(exc[1:]) or "-"))

    seam_n = os.path.normpath(seam)
    if in_scope(seam_n):
        raise Refusal("--seam %s is inside the scope" % seam_n)
    if "/" in seam_n:
        seams = [l for l in leaves if l == seam_n]
    else:
        seams = [l for l in leaves if os.path.basename(l) == seam_n]
    if len(seams) > 1:
        raise Refusal("--seam %s matches %d leaves: %s" % (seam, len(seams),
                                                          " ".join(seams)))
    if seams and in_scope(seams[0]):
        raise Refusal("--seam %s is inside the scope" % seams[0])
    seam_obj = seams[0] if seams else None
    red = []

    scope = [l for l in leaves if in_scope(l)]
    print("")
    print("1 object  %d of %d leaves in scope (through %d ld -r links)"
          "   expect 0   %s" % (len(scope), len(leaves), links,
                                "ok" if not scope else "RED"))
    for l in scope[:25]:
        print("            " + l)
    if scope:
        red.append("%d in-scope leaves are linked" % len(scope))

    syms, diff = symbols(tree, leaves)
    refuse_on(diff, "this build's leaves")
    vsyms, vdiff = symbols(tree, ["vmlinux"])
    refuse_on(vdiff, "vmlinux")
    if not vsyms:
        raise Refusal("vmlinux carries no symbol table")
    vnames = {s.name for s in vsyms}
    vm16 = {s.name for s in vsyms if s.mips16}
    present = sorted(set(pop) & vnames)
    if (set(pop) & smap) - vnames:
        raise Refusal("System.map carries population names the vmlinux "
                      "symbol table does not: %s" % " ".join(
                          sorted((set(pop) & smap) - vnames)[:10]))
    defs = collections.defaultdict(set)
    for s in syms:
        defs[s.name].add(container(s.member))
    extra = [n for n in present if n not in SEAM_NAMES]
    lost = [n for n in SEAM_NAMES if n not in present]
    bad = [n for n in SEAM_NAMES
           if seam_obj is None or defs.get(n, set()) != {seam_obj}]
    print("2 symbol  %d of %d population names in vmlinux (%d by System.map)"
          "   expect the %d seam names   %s"
          % (len(present), len(pop), len(set(pop) & smap),
             len(SEAM_NAMES), "ok" if not (extra or lost or bad) else "RED"))
    print("          %d of them carry [MIPS16] in vmlinux; parsers agree on "
          "the %d leaves and on vmlinux's %d symbols"
          % (len([n for n in present if n in vm16]), len(leaves),
             len(vsyms)))
    print("          seam object: %s" % (seam_obj or
                                         "%s is not among the leaves" % seam))
    for n in extra[:40]:
        d = sorted(defs.get(n, ())) or ["no leaf (linker script?)"]
        print("            not a seam name: %s%s  defined by %s"
              % (n, " [MIPS16]" if n in vm16 else "", ", ".join(d[:3])))
    if len(extra) > 40:
        print("            ... and %d more" % (len(extra) - 40))
    for n in bad:
        d = sorted(defs.get(n, ())) or ["nothing"]
        print("            seam name %-26s defined by %s" % (n, ", ".join(d)))
    if extra:
        red.append("%d population name(s) besides the seam's in vmlinux"
                   % len(extra))
    if lost:
        red.append("seam name(s) missing from vmlinux: %s" % " ".join(lost))
    if bad:
        red.append("%d seam name(s) not defined by the seam object alone"
                   % len(bad))

    with open(image, "rb") as fh:
        img = fh.read()
    if imgprocs.count(img, SANITY) < 1:
        raise Refusal("control: %s is absent from the image -- the search "
                      "is not looking at an rlxfw image" % SANITY)
    if imgprocs.count(img, ABSENT):
        raise Refusal("control: the synthetic name %s is in the image"
                      % ABSENT)
    got = [(n, imgprocs.count(img, n)) for n in proc]
    on = [n for n, c in got if c]
    print("3 string  %d of %d vendor-unique /proc names in the image"
          "   expect 0   %s" % (len(on), len(proc), "ok" if not on else "RED"))
    print("          %s  (controls: %s %d, %s %d)"
          % (" ".join("%s:%d" % g for g in got), SANITY,
             imgprocs.count(img, SANITY), ABSENT, 0))
    if on:
        hit = carriers(tree, leaves, on)
        for n in on:
            print("            %-14s carried by %s"
                  % (n, ", ".join(hit.get(n, ["no leaf"])[:3])))
        red.append("%d vendor-unique /proc name(s) in the image" % len(on))

    print("")
    if red:
        print("RED: " + "; ".join(red))
        return 1
    print("GREEN: no in-scope object linked, only the %d seam names, each "
          "from %s alone, and 0 of %d vendor-unique /proc names"
          % (len(SEAM_NAMES), seam_obj, len(proc)))
    print("  Not established: vendor code outside the scope's paths, vendor "
          "code inlined into a kept object, or that this is the image the "
          "board boots (RLXFW-ID0).")
    return 0


# ----------------------------------------------------------------- self-test

LDS = """SECTIONS {
  . = 0x80000000;
  .text : { *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) }
  .bss : { *(.bss*) *(COMMON) }
  /DISCARD/ : { *(.discard*) *(.reginfo) *(.MIPS.abiflags) *(.pdr)
                *(.gnu.attributes) *(.MIPS.options) }
}
"""


def asm(defs=(), strings=()):
    """Assembly for (name, kind, global?) with kind func, m16, obj, big, or
    gone: a function in a section the link discards, as `__exit` is."""
    a = []
    for name, kind, glob in defs:
        if glob:
            a.append("\t.globl %s" % name)
        if kind in ("func", "m16", "gone"):
            a += ['\t.section .discard.text,"ax",@progbits' if kind == "gone"
                  else "\t.text",
                  "\t.set %s" % ("mips16" if kind == "m16" else "nomips16"),
                  "\t.type %s, @function" % name, "\t.ent %s" % name,
                  "%s:" % name, "\tjr $31", "\t.end %s" % name,
                  "\t.set nomips16"]
        else:
            n = 200000 if kind == "big" else 4
            a += ["\t.bss" if kind == "big" else "\t.data",
                  "\t.type %s, @object" % name, "\t.size %s, %d" % (name, n),
                  "%s:" % name, "\t.space %d" % n]
    for s in strings:
        a += ['\t.section .rodata.str1.4,"aMS",@progbits,1',
              '\t.asciz "%s"' % s]
    return "\n".join(a) + "\n"


SEAM_DEFS = [(n, "obj" if n.startswith(("cached", "rtl865x_cur")) else "func",
              True) for n in SEAM_NAMES]

#: The synthetic reference: seven vendor leaves (one reached through `../`),
#: a MIPS16 global and local, a size printed in hex, a local that collides
#: with a retained object's, and an archive.
R_VENDOR = {
    "drivers/net/rtl819x/rtl_nic.o":
        ([("re865x_open", "func", True), ("eth_skb_buf", "big", True),
          ("__func__.0", "obj", False), ("rx_tbl", "obj", False)]
         + [d for d in SEAM_DEFS if d[1] == "obj"],
         ["asicCounter", "port_status", "mac"]),
    "drivers/net/rtl819x/rtl865xc_swNic.o":
        ([("swNic_receive", "m16", True), ("release_pkthdr", "m16", False)],
         []),
    "drivers/net/rtl819x/rtl865x/../AsicDriver/96E/rtl865x_asicBasic.o":
        ([SEAM_DEFS[0]], []),
    "drivers/net/rtl819x/rtl865x/../common/rtl865x_netif.o":
        ([SEAM_DEFS[1]], []),
    "drivers/net/rtl819x/rtl865x/../l2Driver/rtl865x_fdb.o":
        ([SEAM_DEFS[2], SEAM_DEFS[8]], []),
    "drivers/net/rtl819x/rtl865x/../igmpsnooping/igmp_delete.o":
        ([SEAM_DEFS[3]], []),
    "drivers/net/rtk_vlan.o": ([("rtk_vlan_support_enable", "obj", True)],
                               []),
}
R_OTHER = {
    "arch/head.o": ([("_start", "func", True)], []),
    "drivers/net/rtl819x-switch.o":
        ([("rtl819x_switch_init", "func", True),
          ("__func__.0", "obj", False)], [SANITY]),
    "drivers/char/rtl_gpio.o": ([("rtl_gpio_init", "func", True)], []),
    "net/rtl/fastpath/fastpath_core.o": ([("rtl_fp_hook", "func", True)], []),
    "net/netfilter/xt_mac.o": ([("mac_mt", "func", True)], ["mac"]),
}
SEAM_OBJ = "drivers/net/rlxfw-seam.o"
NEW_OBJ = "drivers/net/rtl819x/rtl_new.o"   # in scope, not in the reference
EMPTY_BUILTIN = "drivers/misc/built-in.o"
PROC_C ="".join('create_proc_entry("%s", 0, d);\n' % n
                 for n in ("asicCounter", "port_status", "mac", "vlan"))


def build_tree(root, objs, net_extra=(), vendor=True, lib=True):
    """A kbuild-shaped tree: leaves assembled, ld -r links with .cmd files,
    vmlinux, System.map and the flat image.  Returns the flat's path."""
    def put(rel, text):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(text)

    def cmd(rel, text):
        d, b = os.path.split(rel)
        put(os.path.join(d, "." + b + ".cmd"), "cmd_%s := %s\n" % (rel, text))

    def ldr(out, ins):
        run([LD, "-EB", "-r", "-o", out] + ins, root)
        cmd(out, "mips-linux-gnu-ld -EB -r -o %s %s" % (out, " ".join(ins)))

    os.makedirs(os.path.join(root, "drivers/net/rtl819x/rtl865x"),
                exist_ok=True)
    for rel, (defs, strs) in objs.items():
        src = os.path.normpath(rel)[:-2] + ".S"
        put(src, asm(defs, strs))
        run([AS, "-EB", "-o", os.path.normpath(rel), src], root)
        cmd(os.path.normpath(rel), "mips-linux-gnu-as -EB -o %s %s"
            % (rel, src))
    put(PROC_SRC, PROC_C)
    sub = sorted(k for k in objs if "/rtl865x/../" in k)
    net = ["drivers/net/rtl819x-switch.o"] + [k for k in net_extra]
    if vendor:
        ldr("drivers/net/rtl819x/rtl865x/built-in.o", sub)
        ldr("drivers/net/rtl819x/built-in.o",
            ["drivers/net/rtl819x/rtl_nic.o",
             "drivers/net/rtl819x/rtl865xc_swNic.o",
             "drivers/net/rtl819x/rtl865x/built-in.o"])
        net += ["drivers/net/rtl819x/built-in.o", "drivers/net/rtk_vlan.o"]
    ldr("drivers/net/built-in.o", net)
    # kbuild's built-in.o for a directory that builds nothing: an empty
    # archive, which the walk must accept as a leaf.
    os.makedirs(os.path.join(root, os.path.dirname(EMPTY_BUILTIN)),
                exist_ok=True)
    run([AR, "rcs", EMPTY_BUILTIN], root)
    cmd(EMPTY_BUILTIN, "rm -f %s; mips-linux-gnu-ar rcs %s"
        % (EMPTY_BUILTIN, EMPTY_BUILTIN))
    ldr("drivers/built-in.o", ["drivers/net/built-in.o",
                               "drivers/char/rtl_gpio.o", EMPTY_BUILTIN])
    ldr("net/built-in.o", ["net/rtl/fastpath/fastpath_core.o",
                           "net/netfilter/xt_mac.o"])
    top = ["arch/head.o", "--start-group", "drivers/built-in.o",
           "net/built-in.o"]
    if lib:
        put("lib/ctype.S", asm([("_ctype", "obj", True)]))
        run([AS, "-EB", "-o", "lib/ctype.o", "lib/ctype.S"], root)
        run([AR, "rcs", "lib/lib.a", "lib/ctype.o"], root)
        top.append("lib/lib.a")
    top.append("--end-group")
    put("x.lds", LDS)
    run([LD, "-EB", "-T", "x.lds", "-e", "_start", "-o", "vmlinux"] + top,
        root)
    cmd("vmlinux", "mips-linux-gnu-ld -EB -T x.lds -o vmlinux %s"
        % " ".join(top))
    put("System.map", run([NM, "-n", "vmlinux"], root))
    run([OBJCOPY, "-O", "binary", "vmlinux", "flat"], root)
    return os.path.join(root, "flat")


def call(fn, *a):
    """(exit code, printed text) of a census function, refusals included."""
    buf, old = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        rc = fn(*a)
    except Refusal as e:
        print("REFUSED: %s" % e)
        rc = 2
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


def old_parse(text, first):
    """The segment-113 parser (`s113/r6b8/pop.py`'s regex), for the
    disagreement case: no room for st_other, and a decimal size.  Archive
    members are spelled as `parse_readelf` spells them, so every
    disagreement it produces is a line its regex dropped."""
    rx = re.compile(r"^\s*\d+:\s+([0-9a-f]+)\s+(\d+)\s+(\w+)\s+(\w+)\s+\w+"
                    r"\s+(\w+)\s+(\S+)")
    member, secs, out = first, {}, []
    for line in text.splitlines():
        if line.startswith("File: "):
            a = re.match(r"^(.*)\((.*)\)$", line[6:].strip())
            member = "%s[%s]" % a.groups() if a else line[6:].strip()
            continue
        s = SEC_LINE.match(line)
        if s:
            rest = s.group(2).split()
            secs[int(s.group(1))] = ("" if s.group(1) == "0" or not rest
                                     else rest[0])
            continue
        m = rx.match(line)
        if not m:
            continue
        val, size, typ, bind, ndx, name = m.groups()
        if typ in ("SECTION", "FILE") or ndx == "UND":
            continue
        sec = {"ABS": "*ABS*", "COM": "*COM*"}.get(ndx) or secs[int(ndx)]
        out.append(Sym(member, name, bind, typ, int(val, 16), int(size), sec,
                       False))
    return out


def self_test(keep=None):
    global PARSE_READELF
    need(AS, LD, AR, OBJCOPY, READELF, NM)
    cases = []

    def case(label, ok, detail):
        cases.append((label, bool(ok), detail))

    # --- P: the parsers on text --------------------------------------------
    sec = ("  [ 0]                   NULL            00000000 000000 000000 "
           "00      0   0  0\n  [ 1] .text             PROGBITS        "
           "00000000 000040 000010 00  AX  0   0 16\n")
    lines = [
        "     1: 00000000    20 FUNC    GLOBAL DEFAULT [MIPS16]     1 a16",
        "     2: 00000004 0x19f80 OBJECT  LOCAL  DEFAULT    1 bigone",
        "     3: 00000008     4 OBJECT  GLOBAL DEFAULT [<other>: 88]     1 "
        "oth",
        "     4: 00000000     0 NOTYPE  GLOBAL DEFAULT  UND undefd",
        "     5: 00000000     0 SECTION LOCAL  DEFAULT    1 ",
        "     6: 0000000c     4 FUNC    GLOBAL DEFAULT    1 plain"]
    got = parse_readelf(sec + "\n".join(lines) + "\n", "x.o")
    case("P1", [(s.name, s.mips16, s.size, s.section) for s in got]
         == [("a16", True, 20, ".text"), ("bigone", False, 0x19f80, ".text"),
             ("oth", False, 4, ".text"), ("plain", False, 4, ".text")],
         "readelf: [MIPS16] and a two-token st_other parsed, a hex size read, "
         "UND and SECTION skipped (got %d syms)" % len(got))
    case("P2", len(old_parse(sec + "\n".join(lines) + "\n", "x.o")) == 1,
         "the segment-113 regex keeps 1 of those 4 -- the drop this tool "
         "exists to catch")
    for lab, bad in (("P3", "     7: 0000000c     4 FUNC    GLOBAL DEFAULT"
                            " [MIPS16    1 x"),
                     ("P4", "     7: 0000000c     4 FUNC    GLOBAL"),
                     ("P5", "     7: 0000000c     4 FUNC    GLOBAL DEFAULT"
                            " 1 [X] 2 x"),
                     ("P6", "     7: 0000000c     4 FUNC    GLOBAL DEFAULT"
                            "    9 insec9")):
        try:
            parse_readelf(sec + bad + "\n", "x.o")
            case(lab, False, "an unparseable line was accepted: %r" % bad)
        except Refusal as e:
            case(lab, True, "refused, not skipped: %s" % str(e)[:60])
    arch = parse_readelf("File: lib/lib.a(c.o)\n" + sec + lines[5] + "\n",
                         "lib/lib.a")
    case("P7", arch and arch[0].member == "lib/lib.a[c.o]"
         and container(arch[0].member) == "lib/lib.a",
         "an archive member is named lib/lib.a[c.o], nm's spelling")
    nmt = ("Symbols from x.o:\n\nName Value Class Type Size Line Section\n\n"
           "a16  |00000000|   T  |  FUNC|00000014|     |.text\n"
           "bigone|00000004|  b  |OBJECT|00019f80|     |.text\n"
           "oth  |00000008|   D  |OBJECT|00000004|     |.text\n"
           "undefd|        |   U  |NOTYPE|        |     |*UND*\n"
           "plain|0000000c|   T  |  FUNC|00000004|     |.text\n")
    case("P8", not compare(got, parse_nm(nmt, "x.o")),
         "readelf and nm agree on the four, seven fields each")
    short = nmt.replace("a16  |00000000|   T  |  FUNC|00000014|     |.text\n",
                        "")
    d = compare(got, parse_nm(short, "x.o"))
    case("P9", len(d) == 1 and "readelf only" in d[0] and "a16" in d[0],
         "a symbol nm lacks is reported (%d line)" % len(d))
    d = compare(got, parse_nm(nmt.replace("00000014", "00000016"), "x.o"))
    case("P10", len(d) == 2, "a size that differs is two lines, one per "
         "side (%d)" % len(d))
    try:
        parse_nm("Symbols from x.o:\nfoo|1|T|FUNC\n", "x.o")
        case("P11", False, "a short nm row was accepted")
    except Refusal:
        case("P11", True, "a short nm row is refused")

    # --- F: the fixture ------------------------------------------------------
    t = tempfile.mkdtemp(prefix="ethcensus-st-")
    try:
        def fx(body):
            p = os.path.join(t, "fx.txt")
            with open(p, "w") as fh:
                fh.write(body)
            return p
        good = [MAGIC, "# build b", "# vmlinux 00 1", "# excluded 0 ",
                "# population %d sysmap 0" % len(SEAM_NAMES), "# proc 1 mmd"]
        ok_body = "\n".join(good + sorted(SEAM_NAMES)) + "\n"
        rc, _ = call(lambda: load_fixture(fx(ok_body)) and 0)
        case("F1", rc == 0, "a well-formed fixture loads")
        for lab, body, why in (
                ("F2", ok_body.replace("# population 10", "# population 11"),
                 "a header count that disagrees with the list"),
                ("F3", "\n".join(good[:4] + ["# population 0 sysmap 0",
                                             good[5]]) + "\n",
                 "an empty population"),
                ("F4", "\n".join(good + list(reversed(sorted(SEAM_NAMES))))
                 + "\n", "an unsorted list"),
                ("F5", "\n".join(good[:4] + ["# population 9 sysmap 0",
                                             good[5]]
                                 + sorted(SEAM_NAMES)[1:]) + "\n",
                 "a population without a seam name"),
                ("F6", ok_body.replace("# proc 1 mmd", "# proc 0 "),
                 "no vendor-unique /proc name")):
            rc, out = call(lambda b=body: load_fixture(fx(b)) and 0)
            case(lab, rc == 2, "refused: %s (%s)"
                 % (why, out.strip().split(": ", 2)[-1][:50]))

        # --- T: synthetic trees built with the host binutils ---------------
        base = dict(R_VENDOR)
        base.update(R_OTHER)
        ref = os.path.join(t, "ref")
        ref_flat = build_tree(ref, base)
        fixture = os.path.join(t, "ref.fixture")
        rc, out = call(population, ref, fixture)
        case("T1", rc == 0 and "; 7 in scope" in out
             and "2 of them MIPS16: release_pkthdr swNic_receive" in out,
             "population on the vendor-present tree: 7 in-scope leaves, both "
             "MIPS16 names counted (rc %d)" % rc)
        h, names, proc = load_fixture(fixture) if rc == 0 else ({}, [], [])
        case("T2", "__func__.0" in h.get("excluded", "")
             and "__func__.0" not in names and "eth_skb_buf" in names,
             "a local colliding with a retained object is excluded by name; "
             "the hex-sized one is in")
        case("T3", proc == ["asicCounter", "port_status"],
             "vendor-unique /proc names: asicCounter port_status, `mac` "
             "shared with xt_mac.o (got %s)" % " ".join(proc))

        rc, out = call(check, ref, ref_flat, SEAM_OBJ, fixture)
        case("C1", rc == 1 and "1 object  7 of" in out
             and "RED" in out and "2 of 2 vendor-unique" in out,
             "control: check on the vendor-present tree is RED with 7 "
             "objects and 2 of 2 strings (rc %d)" % rc)
        n_pop = len(names)
        case("C2", ("2 symbol  %d of %d" % (n_pop, n_pop)) in out,
             "control: every population name is found in its own vmlinux "
             "(%d of %d)" % (n_pop, n_pop))

        seam = (SEAM_DEFS, [])
        new_objs = dict(R_VENDOR)       # on disk, NOT linked
        new_objs.update(R_OTHER)
        new_objs[SEAM_OBJ] = seam

        def variant(name, change=None, extra=(SEAM_OBJ,), lib=True,
                    vendor=False):
            objs = {k: (list(v[0]), list(v[1])) for k, v in new_objs.items()}
            if change:
                change(objs)
            root = os.path.join(t, name)
            return root, build_tree(root, objs, net_extra=extra,
                                    vendor=vendor, lib=lib)

        good_root, good_flat = variant("good")
        rc, out = call(check, good_root, good_flat, SEAM_OBJ, fixture)
        case("G1", rc == 0 and "GREEN" in out and "1 object  0 of" in out
             and "2 symbol  10 of" in out and "0 of 2 vendor-unique" in out,
             "the vendor-free tree with the seam is GREEN: 0 objects, the "
             "10 seam names, 0 of 2 strings -- vendor .o files on disk but "
             "unlinked do not count (rc %d)" % rc)
        rc, out = call(population, good_root, os.path.join(t, "e.fx"))
        case("M3a", rc == 2 and "empty population" in out,
             "a reference with no in-scope leaf is REFUSED (rc %d)" % rc)
        e_fx = os.path.join(t, "empty.fx")
        body = MAGIC + "\n"
        if os.path.isfile(fixture):
            with open(fixture) as fh:
                body = fh.read()
        hdr = [l for l in body.split("\n") if l.startswith("#")]
        hdr = [re.sub(r"^# population \d+", "# population 0", l) for l in hdr]
        with open(e_fx, "w") as fh:
            fh.write("\n".join(hdr) + "\n")
        rc, out = call(check, good_root, good_flat, SEAM_OBJ, e_fx)
        case("M3b", rc == 2 and "empty population" in out,
             "an empty population fixture is REFUSED, not GREEN (rc %d)" % rc)

        r, f = variant("eleventh", lambda o: o[SEAM_OBJ][0].append(
            ("re865x_open", "func", True)))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M1", rc == 1 and "2 symbol  11 of" in out
             and "not a seam name: re865x_open" in out,
             "a seam defining an eleventh vendor name is RED (rc %d)" % rc)

        r, f = variant("second", lambda o: o[
            "net/rtl/fastpath/fastpath_core.o"][0].append(
                ("cached_dev", "obj", False)))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M2", rc == 1 and "seam name cached_dev" in out
             and "fastpath_core.o" in out,
             "a seam name also defined by a second object is RED (rc %d)"
             % rc)

        r, f = variant("mips16", lambda o: o[
            "net/rtl/fastpath/fastpath_core.o"][0].append(
                ("swNic_receive", "m16", True)))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M4", rc == 1 and "1 object  0 of" in out
             and "swNic_receive [MIPS16]" in out,
             "a surviving MIPS16 vendor function outside the scope's paths "
             "is counted and RED (rc %d)" % rc)
        r16, f16 = r, f

        PARSE_READELF = old_parse
        try:
            rc, out = call(population, ref, os.path.join(t, "x.fx"))
        finally:
            PARSE_READELF = parse_readelf
        case("M5", rc == 2 and "disagree" in out and "swNic_receive" in out
             and "eth_skb_buf" in out,
             "the segment-113 parser against nm: REFUSED, naming the MIPS16 "
             "and the hex-sized names it dropped (rc %d)" % rc)

        r, f = variant("objleft", extra=(SEAM_OBJ, "drivers/net/rtk_vlan.o"))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M6", rc == 1 and "1 object  1 of" in out,
             "one in-scope object left linked is RED (rc %d)" % rc)

        r, f = variant("strleft", lambda o: o[
            "net/rtl/fastpath/fastpath_core.o"][1].append("asicCounter"))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M7", rc == 1 and "1 of 2 vendor-unique" in out
             and "carried by net/rtl/fastpath/fastpath_core.o" in out,
             "a vendor-unique /proc literal left in a kept object is RED, "
             "and names its carrier (rc %d)" % rc)

        rc, out = call(check, good_root, ref_flat, SEAM_OBJ, fixture)
        case("R1", rc == 2 and "not this build's flat" in out,
             "another build's image is REFUSED (rc %d)" % rc)

        r, f = variant("nosanity", lambda o: o[
            "drivers/net/rtl819x-switch.o"][1].clear())
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("R2", rc == 2 and "control" in out,
             "an image without %s is REFUSED: the string search cannot be "
             "trusted there (rc %d)" % (SANITY, rc))

        rc, out = call(check, good_root, good_flat,
                       "drivers/net/rtl819x/rtl_nic.o", fixture)
        case("R3", rc == 2 and "inside the scope" in out,
             "a --seam inside the scope is REFUSED (rc %d)" % rc)

        rc, out = call(check, good_root, good_flat, "nosuch.o", fixture)
        case("R4", rc == 1 and "is not among the leaves" in out,
             "a --seam the link does not name is RED, with its reason "
             "(rc %d)" % rc)

        rc, out = call(walk, os.path.join(t, "nosuch"))
        case("R5", rc == 2 and "not a built kernel tree" in out,
             "a directory with no .vmlinux.cmd is REFUSED (rc %d)" % rc)

        r, f = variant("synthname", lambda o: o[
            "drivers/net/rtl819x-switch.o"][1].append(ABSENT))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("R6", rc == 2 and "synthetic name" in out,
             "an image carrying the synthetic name is REFUSED: a search "
             "that finds everything is not a search (rc %d)" % rc)

        sm = os.path.join(t, "smap")
        shutil.copytree(good_root, sm, symlinks=True)
        with open(os.path.join(sm, "System.map"), "a") as fh:
            fh.write("80000000 T re865x_open\n")
        rc, out = call(check, sm, os.path.join(sm, "flat"), SEAM_OBJ,
                       fixture)
        case("R7", rc == 2 and "System.map carries" in out,
             "a System.map naming a population name the symbol table lacks "
             "is REFUSED: one of the two readings is wrong (rc %d)" % rc)

        rc, out = call(check, good_root, good_flat, SEAM_OBJ, fixture)
        case("S1", SCOPE_TEXT in out and all(p in out for p, _ in KEPT)
             and "PIN_MUX_SEL" in out,
             "every check prints the scope and the four kinds of vendor "
             "code it keeps")

        objs = {k: (list(v[0]), list(v[1])) for k, v in base.items()}
        objs["net/netfilter/xt_mac.o"][1].append("port_status")
        rt = os.path.join(t, "refshared")
        build_tree(rt, objs)
        rc, out = call(population, rt, os.path.join(t, "s.fx"))
        case("T4", rc == 2 and "two derivations disagree" in out,
             "a shared /proc name imgprocs.SHARED does not list is REFUSED "
             "(rc %d)" % rc)

        objs = {k: (list(v[0]), list(v[1])) for k, v in base.items()}
        objs["drivers/net/rtl819x/rtl865x/../common/rtl865x_netif.o"] = \
            ([], [])
        rt = os.path.join(t, "refnoseam")
        build_tree(rt, objs)
        rc, out = call(population, rt, os.path.join(t, "n.fx"))
        case("T5", rc == 2 and "rtl865x_setNetifType" in out
             and "could not see" in out,
             "a reference whose scope lacks a seam name is REFUSED (rc %d)"
             % rc)

        # --- each census, and each guard, shown deciding on its own --------
        def red_lines(out):
            return [l for l in out.splitlines() if l.startswith("RED: ")]

        r, f = variant("newobj", lambda o: o.__setitem__(
            NEW_OBJ, ([("rtl_new_vendor_fn", "func", True)], [])),
            extra=(SEAM_OBJ, NEW_OBJ))
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M8", rc == 1 and "1 object  1 of" in out
             and "2 symbol  10 of" in out and "0 of 2 vendor-unique" in out
             and red_lines(out) == ["RED: 1 in-scope leaves are linked"],
             "a new in-scope leaf whose names the reference never saw is RED "
             "by the object census alone (rc %d)" % rc)

        def gone(o):
            o[SEAM_OBJ][0][0] = (SEAM_NAMES[0], "gone", True)
        r, f = variant("lost", gone)
        rc, out = call(check, r, f, SEAM_OBJ, fixture)
        case("M9", rc == 1 and red_lines(out)
             == ["RED: seam name(s) missing from vmlinux: %s" % SEAM_NAMES[0]],
             "a seam name the seam object defines in a section the link "
             "discards is RED by the missing-name rule alone (rc %d)" % rc)

        PARSE_READELF = old_parse
        try:
            rc, out = call(check, r16, f16, SEAM_OBJ, fixture)
        finally:
            PARSE_READELF = parse_readelf
        case("M5c", rc == 2 and "disagree" in out
             and "of this build's leaves" in out and "swNic_receive" in out,
             "check with the segment-113 parser, on a tree keeping a MIPS16 "
             "vendor function: REFUSED by nm on the leaves, naming it (rc %d)"
             % rc)

        def drop_vm(text, first):
            return [s for s in parse_readelf(text, first)
                    if first != "vmlinux" or s.name != "cached_dev"]
        PARSE_READELF = drop_vm
        try:
            rc, out = call(check, good_root, good_flat, SEAM_OBJ, fixture)
        finally:
            PARSE_READELF = parse_readelf
        case("M5v", rc == 2 and "of vmlinux" in out and "cached_dev" in out,
             "a readelf reading of vmlinux that drops a seam name is REFUSED "
             "by nm, not read as a missing name (rc %d)" % rc)

        nomap = os.path.join(t, "nomap")
        shutil.copytree(good_root, nomap, symlinks=True)
        os.remove(os.path.join(nomap, "System.map"))
        rc, out = call(check, nomap, os.path.join(nomap, "flat"), SEAM_OBJ,
                       fixture)
        case("R8", rc == 2 and "no System.map" in out,
             "check without System.map is REFUSED, not run on one reading "
             "(rc %d)" % rc)

        r, f = variant("dupseam", lambda o: o.__setitem__(
            "drivers/net/extra/rlxfw-seam.o", ([], [])),
            extra=(SEAM_OBJ, "drivers/net/extra/rlxfw-seam.o"))
        rc, out = call(check, r, f, "rlxfw-seam.o", fixture)
        rc1, _ = call(check, good_root, good_flat, "rlxfw-seam.o", fixture)
        case("R9", rc == 2 and "matches 2 leaves" in out and rc1 == 0,
             "a basename --seam naming one leaf is GREEN (rc %d); naming two "
             "is REFUSED (rc %d)" % (rc1, rc))

        rnc = os.path.join(t, "refnocmd")
        shutil.copytree(ref, rnc, symlinks=True)
        os.remove(os.path.join(rnc, "drivers/net/.built-in.o.cmd"))
        rc, out = call(check, rnc, os.path.join(rnc, "flat"), SEAM_OBJ,
                       fixture)
        walked = walk(good_root)[0]
        case("R10", rc == 2 and "drivers/net/built-in.o" in out
             and "not an empty archive" in out and EMPTY_BUILTIN in walked,
             "a built-in.o whose .cmd is gone is REFUSED, not walked as an "
             "out-of-scope leaf (rc %d); kbuild's empty-archive %s is "
             "walked as a leaf (%s)" % (rc, EMPTY_BUILTIN,
                                        EMPTY_BUILTIN in walked))

        def ref_variant(name, change):
            objs = {k: (list(v[0]), list(v[1])) for k, v in base.items()}
            change(objs)
            rt = os.path.join(t, name)
            build_tree(rt, objs)
            return call(population, rt, os.path.join(t, name + ".fx"))

        rc, out = ref_variant("refnosanity", lambda o: o[
            "drivers/net/rtl819x-switch.o"][1].clear())
        case("T6", rc == 2 and ("control: %s is carried by no out-of-scope "
                                "leaf" % SANITY) in out,
             "a reference whose %s carries no %s is REFUSED: the string "
             "search is not shown finding anything (rc %d)"
             % ("rtl819x-switch.o", SANITY, rc))
        rc, out = ref_variant("refabsent", lambda o: o[
            "net/netfilter/xt_mac.o"][1].append(ABSENT))
        case("T7", rc == 2 and ("the synthetic name %s was found" % ABSENT)
             in out,
             "a reference carrying the synthetic name is REFUSED (rc %d)" % rc)
        rc, out = ref_variant("refallshared", lambda o: o[
            "drivers/net/rtl819x/rtl_nic.o"][1].__setitem__(
                slice(None), ["mac"]))
        case("T8", rc == 2 and "no vendor-unique /proc name" in out,
             "a reference whose vendor objects carry only a shared /proc "
             "name is REFUSED: check's string census would have no "
             "positive control (rc %d)" % rc)

        if keep:
            os.makedirs(keep, exist_ok=True)
            for n in ("ref", "good", "eleventh", "second", "mips16",
                      "newobj"):
                shutil.copytree(os.path.join(t, n), os.path.join(keep, n),
                                symlinks=True, dirs_exist_ok=True)
            if os.path.isfile(fixture):
                shutil.copy(fixture, os.path.join(keep, "ref.fixture"))
    except Exception as e:  # a crash is a FAIL line, never a lost verdict
        case("CRASH", False, "the self-test stopped: %s: %s"
             % (type(e).__name__, e))
    finally:
        shutil.rmtree(t, ignore_errors=True)

    good = 0
    for label, ok, detail in cases:
        good += ok
        print("  %-4s %-5s %s" % ("ok" if ok else "FAIL", label, detail))
    print("%d of %d ok" % (good, len(cases)))
    return 0 if good == len(cases) else 1


# ---------------------------------------------------------------------- main

def opts(argv, allowed):
    got, i = {}, 0
    while i < len(argv):
        k = argv[i]
        if k not in allowed or i + 1 >= len(argv):
            raise SystemExit(usage("unknown or incomplete option %r" % k))
        got[k] = argv[i + 1]
        i += 2
    return got


def usage(why):
    print("usage error: %s" % why)
    print(__doc__[__doc__.index("usage\n"):].rstrip())
    return 3


def main(argv):
    if len(argv) < 2:
        return usage("no mode")
    mode, rest = argv[1], argv[2:]
    if mode == "self-test":
        o = opts(rest, ("--keep",))
        print(VERSION + "  --  self-test")
        return self_test(o.get("--keep"))
    if mode == "population":
        o = opts(rest, ("--build", "--out"))
        if set(o) != {"--build", "--out"}:
            return usage("population needs --build and --out")
        return population(o["--build"], o["--out"])
    if mode == "check":
        o = opts(rest, ("--build", "--image", "--seam", "--fixture"))
        if not {"--build", "--image", "--seam"} <= set(o):
            return usage("check needs --build, --image and --seam")
        return check(o["--build"], o["--image"], o["--seam"],
                     o.get("--fixture", FIXTURE))
    return usage("unknown mode %r" % mode)


if __name__ == "__main__":
    try:
        code = main(sys.argv)
    except Refusal as e:
        print("REFUSED: %s" % e)
        code = 2
    except (OSError, ValueError, UnicodeError) as e:
        print("REFUSED: %s: %s" % (type(e).__name__, e))
        code = 2
    except Exception as e:  # a defect of this tool: a reason, not a trace
        print("REFUSED: internal error %s: %s" % (type(e).__name__, e))
        code = 2
    sys.exit(code)
