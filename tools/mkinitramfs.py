#!/usr/bin/env python3
"""Build R3's initramfs from a declaration, and refuse rather than substitute.

R3-5.  Decision B (`notes/kernel-build.md` §4) is that the first boot mounts an
initramfs made of **this unit's own userspace**, so that if the shell does not
come up, the shell is not the new thing.  That claim is only worth anything if
every byte in the image can be pointed at a source, so the image is built from a
declaration in which every entry names one -- and every entry is tagged either
`unit` (carved out of this device's own flash dump) or `rlxfw` (mine).

WHAT IT REFUSES TO DO, and each refusal is a control:

  * A declared source file that is not there is an ERROR.  It is never skipped
    and never replaced with something similar.  `tools/rebuild-census.py`'s `A6`
    pins the same shape for the same reason: a build tool that quietly
    substitutes turns "built from this unit's binaries" into a sentence nobody
    can check afterwards.
  * `/init` and `/dev/console` must be declared.  Without `/init`,
    `init/main.c:885-891` falls through to `prepare_namespace()` and mounts
    whatever `root=` names -- on this device, the vendor's own flash rootfs,
    which would come up looking like a pass.  Without `/dev/console`,
    `init_post()` prints one warning and `init` runs with no stdio, which reads
    on the console exactly like a hang.
  * A source path containing whitespace is an ERROR.  `scripts/
    gen_initramfs_list.sh`'s dependency pass is `while read type dir file perm`,
    so a space in a path silently truncates the dependency list and the image
    then goes stale without saying so.
  * An entry tagged `unit` whose source is not inside the unit tree is an ERROR.
    That tag is the traceability claim; it is checked, not trusted.

Usage
    tools/mkinitramfs.py build --decl F --unit DIR --repo DIR --out DIR
                              [--kernel-image F] [--ceiling N]
    tools/mkinitramfs.py self-test
"""

import hashlib
import os
import posixpath
import re
import stat
import struct
import sys

VERSION = "1.1"

# `notes/kernel-build.md` §3.4: the image is entered at 0x80500000 and
# decompresses to 0x80000000, so the decompressed image must end below its own
# input.
CEILING = 5242880

OWNERS = ("unit", "rlxfw")
KINDS = ("dir", "file", "slink", "nod")


class Refused(Exception):
    pass


_RAISE = False


def die(msg):
    if _RAISE:
        raise Refused(msg)
    sys.stderr.write("mkinitramfs: %s\n" % msg)
    sys.exit(3)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Entry(object):
    def __init__(self, kind, path, source, mode, owner, note, lineno):
        self.kind, self.path, self.source = kind, path, source
        self.mode, self.owner, self.note = mode, owner, note
        self.lineno = lineno
        self.resolved = None
        self.size = 0
        self.digest = "-"


def parse_decl(path, text=None):
    if text is None:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    out, seen = [], {}
    for lineno, ln in enumerate(text.split("\n"), 1):
        ln = ln.rstrip("\r")
        if not ln.strip() or ln.startswith("#"):
            continue
        f = ln.split("\t")
        if len(f) != 6:
            die("%s:%d: %d tab-separated fields, expected 6 "
                "(kind, path, source, mode, owner, note)" % (path, lineno, len(f)))
        kind, p, source, mode, owner, note = f
        if kind not in KINDS:
            die("%s:%d: kind %r is not one of %s" % (path, lineno, kind,
                                                     ", ".join(KINDS)))
        if not p.startswith("/"):
            die("%s:%d: path %r must be absolute" % (path, lineno, p))
        # M4: `//init`, `/bin/./busybox` and `/bin/../bin/busybox` all name the
        # same file to gen_init_cpio, which writes BOTH and lets the second win
        # -- the exact thing the duplicate refusal below exists to stop.  The
        # comparison is on the normalised path.
        # `posixpath.normpath` KEEPS exactly two leading slashes -- POSIX leaves
        # `//foo` implementation-defined -- so `//init` survived it and was the
        # duplicate A16 was written to catch.
        if posixpath.normpath(p) != p or "//" in p:
            die("%s:%d: path %r is not in normal form (%r). gen_init_cpio "
                "would write it and a differently-spelled duplicate as two "
                "entries, and the second would win"
                % (path, lineno, p, posixpath.normpath(p)))
        # M5: the ban is cited against `while read type dir file perm` in
        # gen_initramfs_list.sh, and the image path is read into `$dir` by the
        # same loop.  Covering only the source column was half a check.
        for label, field in (("path", p), ("source", source)):
            if kind == "nod" and label == "source":
                continue
            if any(ch.isspace() for ch in field):
                die("%s:%d: the %s column contains whitespace (%r). "
                    "gen_initramfs_list.sh reads its dependency list with "
                    "`while read type dir file perm`, so this truncates it"
                    % (path, lineno, label, field))
        if owner not in OWNERS:
            die("%s:%d: owner %r is not one of %s -- every entry is either "
                "this unit's or mine, and 'not sure' is not a third option"
                % (path, lineno, owner, ", ".join(OWNERS)))
        if not re.match(r"^[0-7]{3,4}$", mode):
            die("%s:%d: mode %r must be three or four octal digits. `int(x, 8)` "
                "alone accepted -1, 0o755 and 7_5_5, and gen_init_cpio passes "
                "the string through" % (path, lineno, mode))
        if p in seen:
            die("%s:%d: %s is already declared at line %d. gen_init_cpio would "
                "put both in and the second would win silently"
                % (path, lineno, p, seen[p]))
        seen[p] = lineno
        out.append(Entry(kind, p, source, mode, owner, note, lineno))
    if not out:
        die("%s: no entries. An empty initramfs is a kernel that panics with "
            "'No init found', which is not the experiment" % path)
    return out


def _inside(child, parent):
    """True if `child` is inside `parent` after BOTH are fully resolved.

    M2: the first version compared `os.path.normpath(src)` against a prefix,
    and `os.path.islink` only inspects the final component.  This unit's own
    tree has `tmp -> /var/tmp`, `web -> /var/web` and a dozen `etc/*` symlinks
    out of it, so a source under any of those satisfied the prefix compare while
    reading a file that is not in the dump at all -- measured, with a file
    planted in the host's /var/tmp.
    """
    c = os.path.realpath(child)
    p = os.path.realpath(parent)
    return c == p or c.startswith(p + os.sep)


def _unit_counterpart(e, unit, decl_path):
    """The `unit` tag says "this is what the dump has here".  Check it.

    Until 2026-08-28 the tag was checked for `file` entries only, and 15 of the
    31 entries in the real declaration are `slink`.  Turning the check on found
    two wrong ones immediately: `/bin/dmesg` is not in the dump at all (and the
    applet is not in this busybox either), and `/tmp` is a SYMLINK to /var/tmp
    there, not the directory it was declared as.
    """
    up = os.path.join(unit, e.path.lstrip("/"))
    if e.kind == "slink":
        if not os.path.islink(up):
            die("%s:%d: %s is tagged `unit` but this device's dump has no "
                "symlink there. `unit` means the dump has this, and it does "
                "not" % (decl_path, e.lineno, e.path))
        got = os.readlink(up)
        if got != e.source:
            die("%s:%d: %s is tagged `unit` and the dump's link points at %r, "
                "not %r" % (decl_path, e.lineno, e.path, got, e.source))
    elif e.kind == "dir":
        if os.path.islink(up) or not os.path.isdir(up):
            die("%s:%d: %s is tagged `unit` but the dump has %s there. Declare "
                "it as mine, with the reason"
                % (decl_path, e.lineno, e.path,
                   "a symlink to %r" % os.readlink(up) if os.path.islink(up)
                   else "no directory"))
    elif e.kind == "nod":
        die("%s:%d: a device node cannot be tagged `unit`: 量, this unit's "
            "extracted rootfs holds 0 device nodes" % (decl_path, e.lineno))


def resolve(entries, unit, repo, decl_path):
    unit = os.path.abspath(unit)
    repo = os.path.abspath(repo)
    declared = set(e.path for e in entries)
    for e in entries:
        if e.kind != "file" and e.owner == "unit":
            _unit_counterpart(e, unit, decl_path)
        if e.kind in ("dir",):
            continue
        if e.kind == "slink":
            if not e.source or e.source == "-":
                die("%s:%d: a slink needs a target in the source column"
                    % (decl_path, e.lineno))
            # A slink whose target is not in the image is a file that is not
            # there.  M1's worst case is exactly this on /init.
            tgt = e.source if e.source.startswith("/") else posixpath.join(
                posixpath.dirname(e.path), e.source)
            tgt = posixpath.normpath(tgt)
            if tgt not in declared:
                die("%s:%d: %s points at %s, which nothing in this declaration "
                    "puts in the image. A dangling /init is the "
                    "prepare_namespace() failure this tool exists to stop, and "
                    "a dangling anything else fails at exec with no message "
                    "that says why" % (decl_path, e.lineno, e.path, tgt))
            continue
        if e.kind == "nod":
            parts = e.source.split(":")
            if len(parts) != 3 or parts[0] not in ("c", "b"):
                die("%s:%d: a nod's source column is <c|b>:<major>:<minor>, "
                    "got %r" % (decl_path, e.lineno, e.source))
            for what, v in (("major", parts[1]), ("minor", parts[2])):
                if not re.match(r"^[0-9]{1,3}$", v):
                    die("%s:%d: a nod's %s must be a decimal number, got %r. "
                        "It was never parsed until 2026-08-28, so "
                        "`/dev/console c:4:64` passed"
                        % (decl_path, e.lineno, what, v))
            continue
        # kind == file.  normpath because the `unit` tag below is checked with
        # a prefix comparison, and on a host whose separator is not "/" the
        # substitution leaves a mixed path that no prefix matches.
        src = os.path.normpath(
            e.source.replace("$UNIT", unit).replace("$REPO", repo))
        if any(ch.isspace() for ch in src):
            die("%s:%d: the source path contains whitespace (%r). "
                "gen_initramfs_list.sh reads its dependency list with "
                "`while read type dir file perm`, so this would truncate it "
                "and the image would go stale without saying so"
                % (decl_path, e.lineno, src))
        if not os.path.isabs(src):
            die("%s:%d: source %r did not resolve to an absolute path -- "
                "$UNIT and $REPO are the only substitutions"
                % (decl_path, e.lineno, src))
        if not os.path.exists(src):
            die("%s:%d: %s declares source %s and it is not there. This tool "
                "does NOT look for something similar: an image built from a "
                "substitute is not an image built from this unit"
                % (decl_path, e.lineno, e.path, src))
        if os.path.islink(src):
            die("%s:%d: %s is a symlink in the source tree. Declare it as "
                "`slink` so the image says so, rather than silently inlining "
                "the target" % (decl_path, e.lineno, src))
        if not os.path.isfile(src):
            die("%s:%d: %s is not a regular file" % (decl_path, e.lineno, src))
        if e.owner == "unit" and not _inside(src, unit):
            die("%s:%d: %s is tagged `unit` but its source %s is not inside "
                "the unit tree %s. That tag is the whole traceability claim"
                % (decl_path, e.lineno, e.path, src, unit))
        if e.owner == "rlxfw" and not _inside(src, repo):
            die("%s:%d: %s is tagged `rlxfw` but its source %s is not inside "
                "this repository" % (decl_path, e.lineno, e.path, src))
        e.resolved = src
        e.size = os.path.getsize(src)
        e.digest = sha256(src)
    check_no_writable_flash_node(entries, decl_path)
    return entries


# --------------------------------------------------------------------------
# The flash-write node ban.  R3-9, 2026-08-30.
#
# `CLAUDE.md`'s Never table forbids writing 0x000000-0x005FFF (the loader) and
# 0x006000-0x007FFF (H601) on a device with no spare.  Until today the thing
# keeping a writable node out of the image was an ARGUMENT in a comment --
# notes/kernel-build.md 17.7a reasons its way from /dev/mtdblock0 to
# /dev/mtdblock1 and ends "the control is the absence of a node, not the mode
# bits".  An argument in a comment is not a check.  This is the check.
#
#   讀 drivers/mtd/mtdblock.c: `.major = 31, .part_bits = 0`, and
#   mtdblock_writesect is a read-modify-erase-write of a whole erase block.  So
#   EVERY major-31 node is writable by root, whatever its mode -- root ignores
#   DAC, which is why 0400 was never the control.
#   讀 drivers/mtd/mtdchar.c mtd_open:
#   `if ((file->f_mode & FMODE_WRITE) && (minor & 1)) return -EACCES;`
#   so a major-90 node is read-only BY THE KERNEL if its minor is ODD, and is
#   not if it is even.
#   讀 include/linux/mtd/mtd.h:21 -- `#define MTD_CHAR_MAJOR 90`.
#
# THE RULE: no declared node may be one the kernel would let anything write to
# flash through.  It keys on the dev numbers, never on the path -- a node named
# /dev/harmless with b:31:0 is the same node.
#
# THERE IS DELIBERATELY NO ALLOWLIST.  An escape hatch written before anything
# needs one is an escape hatch that gets used; the build that genuinely needs a
# writable node edits this predicate with a reason, which is a diff a reviewer
# sees.  R5b will want the mtdblock read path back and that is the moment.
MTD_BLOCK_MAJOR = 31
MTD_CHAR_MAJOR = 90


def check_no_writable_flash_node(entries, decl_path):
    """Refuse any device node the kernel would permit a write to flash through.

    Called from the END of resolve(), which is ONE call site on purpose.  The
    control path (_try) and the real path (cmd_build) both go through resolve;
    a check added to cmd_build alone would be exercised by nothing, which is
    `TC-j`'s defect (a private copy of the pipeline that the controls drove
    while the real command line took another route).
    """
    for e in entries:
        if e.kind != "nod":
            continue
        kind, maj, mnr = e.source.split(":")
        maj, mnr = int(maj), int(mnr)
        if maj == MTD_BLOCK_MAJOR:
            die("%s:%d: %s is %s -- major %d is mtdblock, and 讀 "
                "drivers/mtd/mtdblock.c mtdblock_writesect is a whole-erase-block "
                "read-modify-erase-write, so root can write flash through ANY "
                "node with this major whatever its mode. On this device mtd0 "
                "spans 0x000000-0x130000 and contains both regions CLAUDE.md "
                "forbids. No mode bit is a control here; the absence of the "
                "node is"
                % (decl_path, e.lineno, e.path, e.source, maj))
        if maj == MTD_CHAR_MAJOR and mnr % 2 == 0:
            die("%s:%d: %s is %s -- major %d is mtdchar and minor %d is EVEN. "
                "讀 drivers/mtd/mtdchar.c mtd_open: the read-only refusal is "
                "`(f_mode & FMODE_WRITE) && (minor & 1)`, so only an ODD minor "
                "cannot be opened for writing. Declare /dev/mtd%dro as c:%d:%d "
                "instead, which is the same device read-only BY THE KERNEL"
                % (decl_path, e.lineno, e.path, e.source, maj, mnr,
                   mnr // 2, maj, mnr + 1))


def check_required(entries, decl_path):
    have = {e.path: e for e in entries}
    init = have.get("/init")
    if init is not None:
        # M1: `/init` used to be checked only as a string in the path set.  A
        # dangling slink, a directory, a device node and a mode-0644 file all
        # passed -- and every one of them lands in prepare_namespace(), which
        # on this device mounts the vendor's own flash rootfs and looks like a
        # pass.
        if init.kind != "file":
            die("%s:%d: /init is declared as a `%s`. init/main.c:885-891 does "
                "sys_access(X_OK is not tested, but execve is) and then "
                "execve's it: it has to be a regular file"
                % (decl_path, init.lineno, init.kind))
        if not (int(init.mode, 8) & 0o111):
            die("%s:%d: /init has mode %s, with no execute bit. execve returns "
                "EACCES, kernel_init falls through, and the boot mounts root= "
                "instead" % (decl_path, init.lineno, init.mode))
    if "/init" not in have:
        die("%s: /init is not declared. init/main.c:885-891 falls through to "
            "prepare_namespace() when /init is not accessible, and on this "
            "device that mounts the vendor's own flash rootfs -- a boot that "
            "would look like a pass" % decl_path)
    if "/dev/console" not in have:
        die("%s: /dev/console is not declared. init_post() prints one warning "
            "and then init runs with no stdio, which reads on the console "
            "exactly like a hang" % decl_path)
    for e in entries:
        if e.path == "/dev/console":
            if e.kind != "nod":
                die("%s:%d: /dev/console must be a `nod`" % (decl_path, e.lineno))
            if e.source != "c:5:1":
                die("%s:%d: /dev/console is declared %r and has to be c:5:1 -- "
                    "TTYAUX_MAJOR 5, minor 1, which is what init_post() opens. "
                    "Parsing the numbers is not enough: a wrong console device "
                    "is exactly the failure this row exists to stop, with this "
                    "row green" % (decl_path, e.lineno, e.source))


def emit_spec(entries):
    lines = []
    for e in entries:
        if e.kind == "dir":
            lines.append("dir %s %s 0 0" % (e.path, e.mode))
        elif e.kind == "file":
            lines.append("file %s %s %s 0 0" % (e.path, e.resolved, e.mode))
        elif e.kind == "slink":
            lines.append("slink %s %s %s 0 0" % (e.path, e.source, e.mode))
        elif e.kind == "nod":
            t, maj, mnr = e.source.split(":")
            lines.append("nod %s %s 0 0 %s %s %s" % (e.path, e.mode, t, maj, mnr))
    return "\n".join(lines) + "\n"


def emit_manifest(entries, unit, repo):
    out = ["# path\tkind\tbytes\tsha256\towner\tsource",
           "# unit = carved from this device's own flash dump (%s)" % unit,
           "# rlxfw = mine (%s)" % repo]
    for e in entries:
        src = e.resolved if e.resolved else e.source
        if e.resolved:
            src = src.replace(unit, "$UNIT").replace(repo, "$REPO")
        out.append("%s\t%s\t%d\t%s\t%s\t%s"
                   % (e.path, e.kind, e.size, e.digest, e.owner, src))
    return "\n".join(out) + "\n"


def write_atomic(path, text):
    """Build the whole string first, write to .tmp, os.replace.

    `CLAUDE.md` carries this rule because open(path,'w') truncates immediately
    and a raise one line later leaves a zero-byte file; it emptied PROGRESS.md
    on 2026-08-27.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def loaded_extent(path):
    """(bytes, how) -- how far the DECOMPRESSED image reaches, not the file size.

    🔴 Until 2026-08-28 this was `os.path.getsize(vmlinux)`, and that is the
    wrong number by 495,729 bytes on this kernel: an ELF carries a symbol
    table, a string table and section headers, and none of them is loaded.
    量: the file is 3,968,113 and the image the decompressor writes is
    3,472,384 -- 75.7 % of the ceiling reported where the truth is 66.2 %.

    The error was CONSERVATIVE, so nothing over-ceiling ever got through; what
    it would have caused is a false alarm, and the documented response to a
    false alarm here is to move LOAD_START_ADDR -- a change to the boot address
    for a reason that was not real.  And `RUNSHEET` P9 attributed 3,472,384 to
    this tool while this tool could not produce it, which is the more
    expensive half: a number in a runsheet whose stated source does not
    compute it.

    The right measurement is what `objcopy -O binary` emits: over the PT_LOAD
    segments, `max(p_vaddr + p_filesz) - min(p_vaddr)`.  `p_filesz` and not
    `p_memsz`, because `.bss` is NOT in the payload the decompressor writes --
    the kernel zeroes it afterwards.  (It is worth knowing separately that
    `.bss` on this build ends at 0x805E5280, above the 0x80500000 the
    compressed image sits at; that is fine, because by then the wrapper has
    jumped away and its bytes are dead.  It is a different question from this
    one and it is not what the ceiling is about.)

    Read from the program headers directly rather than by shelling out to
    objcopy: this check has to run where there is no cross toolchain.
    """
    with open(path, "rb") as f:
        b = f.read()
    if b[:4] != b"\x7fELF":
        # A flat binary is already the image.  Not an error: `R3-2`'s pipeline
        # produces one and pointing this at it must give the same answer.
        return len(b), "flat file"
    if b[4:6] != b"\x01\x02":
        die("--kernel-image %s: not a 32-bit big-endian ELF (this board is "
            "both, and guessing would give a number that looks fine)" % path)
    if len(b) < 52:
        die("--kernel-image %s: %d bytes, shorter than an ELF header" % (path,
                                                                         len(b)))
    phoff, = struct.unpack_from(">I", b, 28)
    phentsize, phnum = struct.unpack_from(">HH", b, 42)
    # A truncated program header table has to be an error and not a traceback:
    # the caller is a gate, and a gate that crashes is a gate whose answer
    # nobody records.  Found by A22's fixture, 2026-08-28.
    if phentsize < 32 or phoff + phnum * phentsize > len(b):
        die("--kernel-image %s: program header table (phoff %d, %d x %d) runs "
            "past the end of a %d-byte file"
            % (path, phoff, phnum, phentsize, len(b)))
    lo, hi = None, None
    for i in range(phnum):
        o = phoff + i * phentsize
        p_type, p_off, p_vaddr, _, p_filesz = struct.unpack_from(">5I", b, o)
        if p_type != 1 or p_filesz == 0:        # PT_LOAD, non-empty
            continue
        lo = p_vaddr if lo is None else min(lo, p_vaddr)
        hi = p_vaddr + p_filesz if hi is None else max(hi, p_vaddr + p_filesz)
    if lo is None:
        die("--kernel-image %s: no non-empty PT_LOAD. An image with nothing "
            "to load would measure 0 and pass any ceiling" % path)
    return hi - lo, "%d PT_LOAD, 0x%08x-0x%08x" % (phnum, lo, hi)


# ==========================================================================
# `verify` -- the declaration checked against the ARTEFACT.   R3-9, 2026-08-30.
#
# WHY IT EXISTS.  `build` reads config/rlxfw-initramfs.tsv and writes a spec;
# nothing then read the image.  On 2026-08-30 the declaration carried a device
# node that was in no built kernel, and PROGRESS.md recorded that as a row
# nothing could check -- "a declaration ahead of every artefact".  A document
# that describes something that does not exist is worse than no document,
# because it reads as current.  This is `rlxfw-marks.py`'s own `check` / `verify`
# split, which was measured on its first run: only the one that reads the built
# artefact can catch a change that compiled and is not in the image.
#
# 🔴 WHERE THE ARCHIVE IS, AND THE TRAP THAT IS NOT HYPOTHETICAL.  With
# CONFIG_INITRAMFS_COMPRESSION_NONE the cpio is linked into the ELF section
# `.init.ramfs`.  The obvious alternative -- scan the file for the newc magic
# `070701` -- reads the WRONG BYTES on this kernel, and that is 量 rather than a
# worry: in r3-4/out/quietm.vmlinux.elf the first occurrence of `070701` is at
# file offset 2,556,664, inside the kernel's own string data (the next bytes are
# `no cpio magic`, init/initramfs.c's error message), while `.init.ramfs` starts
# at 2,920,448.  A magic-scanning verifier parses the kernel's diagnostics.
# `V6` is that measurement turned into a case.
#
# WHAT IT DOES NOT DO.  It does not check file CONTENT.  The manifest already
# carries a sha256 per source file and `build` computes it; re-hashing the bytes
# out of the archive would be a second owner of the same claim.  What is checked
# here is the SHAPE the kernel will see: which paths exist, what kind each one
# is, its permission bits, and -- the reason this exists at all -- a device
# node's major and minor.

CPIO_MAGIC = b"070701"
CPIO_TRAILER = "TRAILER!!!"

#: cpio mode type bits against this declaration's `kind` column.
S_IFMT = 0o170000
KIND_IFMT = {"dir": 0o040000, "file": 0o100000,
             "slink": 0o120000, "nod-c": 0o020000, "nod-b": 0o060000}


def elf_section(path, want):
    """Return (offset, size) of a named section, or None.

    Both endiannesses are read rather than assuming big-endian MIPS: the
    controls build their fixtures on this host and a decoder that only works on
    one byte order would pass every synthetic case and fail on nothing.
    """
    with open(path, "rb") as fh:
        blob = fh.read()
    if blob[:4] != b"\x7fELF":
        die("%s is not an ELF file" % path)
    if blob[4] != 1:
        die("%s is not ELFCLASS32; this kernel is 32-bit" % path)
    end = ">" if blob[5] == 2 else "<"
    if len(blob) < 0x34:
        die("%s: truncated ELF header" % path)
    e_shoff, = struct.unpack_from(end + "I", blob, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from(end + "HHH", blob, 0x2E)
    if e_shoff == 0 or e_shnum == 0:
        die("%s has no section header table, so `.init.ramfs` cannot be "
            "located. A stripped image is not what this checks" % path)
    if e_shstrndx >= e_shnum:
        die("%s: e_shstrndx %d is past e_shnum %d" % (path, e_shstrndx, e_shnum))

    def sh(i):
        off = e_shoff + i * e_shentsize
        if off + 40 > len(blob):
            die("%s: section header %d is past EOF" % (path, i))
        return struct.unpack_from(end + "10I", blob, off)

    str_off = sh(e_shstrndx)[4]
    found = None
    for i in range(e_shnum):
        name, _typ, _fl, _addr, offset, size = sh(i)[:6]
        s = blob[str_off + name:str_off + name + 64]
        nm = s.split(b"\0")[0].decode("utf-8", "replace")
        if nm == want:
            if offset + size > len(blob):
                die("%s: section %s runs past EOF" % (path, want))
            found = (offset, size)
    return found, blob


def parse_cpio(blob, start, size, where):
    """Parse a newc archive into [(name, mode, size, rdevmajor, rdevminor)]."""
    out = []
    pos = start
    limit = start + size
    while True:
        if pos + 110 > limit:
            die("%s: ran off the end of the section at %d with no %s entry"
                % (where, pos, CPIO_TRAILER))
        hdr = blob[pos:pos + 110]
        if hdr[:6] != CPIO_MAGIC:
            die("%s: no newc magic at offset %d (found %r). The archive is not "
                "where this expects it, or the image is compressed -- 讀 "
                "CONFIG_INITRAMFS_COMPRESSION_NONE" % (where, pos, hdr[:6]))
        try:
            f = [int(hdr[6 + 8 * k:6 + 8 * (k + 1)], 16) for k in range(13)]
        except ValueError:
            die("%s: malformed newc header at offset %d" % (where, pos))
        mode, fsize, rmaj, rmin, nsize = f[1], f[6], f[9], f[10], f[11]
        if nsize == 0 or pos + 110 + nsize > limit:
            die("%s: name size %d at offset %d is out of range"
                % (where, nsize, pos))
        name = blob[pos + 110:pos + 110 + nsize - 1].decode("utf-8", "replace")
        if name == CPIO_TRAILER:
            return out
        out.append((name, mode, fsize, rmaj, rmin))
        pos += 110 + nsize
        pos += (-pos) % 4
        pos += fsize
        pos += (-pos) % 4


def declared_shape(entries):
    """{path: (ifmt, perm, rdevmajor, rdevminor)} from the declaration."""
    shape = {}
    for e in entries:
        if e.kind == "nod":
            t, maj, mnr = e.source.split(":")
            ifmt = KIND_IFMT["nod-" + t]
            dev = (int(maj), int(mnr))
        else:
            ifmt = KIND_IFMT[e.kind]
            dev = (0, 0)
        shape[e.path] = (ifmt, int(e.mode, 8), dev[0], dev[1])
    return shape


def cmd_verify(a):
    decl = a["decl"]
    entries = parse_decl(decl)
    check_required(entries, decl)
    resolve(entries, a["unit"], a["repo"], decl)

    print("mkinitramfs %s   verify" % VERSION)
    print("declaration %s   (%d entries)" % (decl, len(entries)))
    print("image       %s" % a["image"])

    # --- the declaration as it stands, against the spec the build consumed ---
    # A mismatch below has two repairs and they are opposite: rebuild, or revert
    # the declaration.  Nothing can tell them apart from a difference alone.
    if a["built_spec"]:
        want = emit_spec(entries)
        with open(a["built_spec"], "r", encoding="utf-8") as fh:
            got = fh.read()
        if want != got:
            print("")
            print("REFUSED: the declaration has CHANGED since this image was "
                  "built.")
            print("  built from %s" % a["built_spec"])
            print("  the declaration now emits a different spec, so a difference "
                  "below would be the declaration's and not the image's.")
            print("  Rebuild, or revert the declaration. This is not a verdict "
                  "on the image.")
            return 2
        print("built-spec  %s (identical to what this declaration emits)"
              % a["built_spec"])

    sec, blob = elf_section(a["image"], ".init.ramfs")
    if sec is None:
        die("%s has no `.init.ramfs` section. That is a finding rather than a "
            "missing file: 讀 usr/Makefile:31, CONFIG_INITRAMFS_SOURCE=\"\" "
            "builds an image holding ONE EMPTY DIRECTORY, and "
            "CONFIG_BLK_DEV_INITRD=n links no archive at all. Either way the "
            "boot falls through to prepare_namespace()" % a["image"])
    off, size = sec
    got = parse_cpio(blob, off, size, a["image"])
    print("archive     .init.ramfs at file offset %d, %d bytes, %d entries"
          % (off, size, len(got)))
    print("")

    want = declared_shape(entries)
    have = {}
    for name, mode, _fsize, rmaj, rmin in got:
        have[name] = (mode & S_IFMT, mode & 0o7777, rmaj, rmin)

    bad = []
    for path in sorted(set(want) | set(have)):
        w, h = want.get(path), have.get(path)
        if w is None:
            bad.append(("UNEXPECTED", path,
                        "in the image, in no declaration row"))
        elif h is None:
            bad.append(("MISSING", path,
                        "declared, and not in the image"))
        elif w != h:
            what = []
            if w[0] != h[0]:
                what.append("type %o vs %o" % (w[0], h[0]))
            if w[1] != h[1]:
                what.append("mode %04o vs %04o" % (w[1], h[1]))
            if (w[2], w[3]) != (h[2], h[3]):
                what.append("dev %d:%d vs %d:%d" % (w[2], w[3], h[2], h[3]))
            bad.append(("DIFFERS", path, "declared " + ", ".join(what)
                        + "  (declared vs image)"))

    nod = [p for p in sorted(have) if have[p][0] in (0o020000, 0o060000)]
    print("device nodes in the image (%d):" % len(nod))
    for p in nod:
        ifmt, perm, maj, mnr = have[p]
        writable = ("b" if ifmt == 0o060000 else "c", maj, mnr)
        note = ""
        if writable[0] == "b" and maj == MTD_BLOCK_MAJOR:
            note = "  🔴 mtdblock -- root can write flash through this"
        elif writable[0] == "c" and maj == MTD_CHAR_MAJOR:
            note = ("  read-only BY THE KERNEL (odd minor)" if mnr % 2
                    else "  🔴 mtdchar EVEN minor -- writable")
        print("  %-24s %s %d:%d  %04o%s"
              % (p, writable[0], maj, mnr, perm, note))
    print("")

    if not bad:
        print("\033[32mOK\033[0m  %d entries, and every one matches the "
              "declaration in kind, mode and dev" % len(got))
        return 0
    for kind, path, why in bad:
        print("  %-11s %-30s %s" % (kind, path, why))
    print("")
    print("\033[31mFAILED\033[0m  %d difference(s) between %s and %s"
          % (len(bad), decl, a["image"]))
    return 1

def cmd_build(a):
    decl = a["decl"]
    entries = parse_decl(decl)
    check_required(entries, decl)
    resolve(entries, a["unit"], a["repo"], decl)

    unit = os.path.abspath(a["unit"])
    repo = os.path.abspath(a["repo"])
    os.makedirs(a["out"], exist_ok=True)
    spec_path = os.path.join(a["out"], "rlxfw-initramfs.spec")
    man_path = os.path.join(a["out"], "rlxfw-initramfs.manifest.tsv")
    write_atomic(spec_path, emit_spec(entries))
    write_atomic(man_path, emit_manifest(entries, unit, repo))

    by_owner = {}
    for e in entries:
        by_owner.setdefault(e.owner, [0, 0])
        by_owner[e.owner][0] += 1
        by_owner[e.owner][1] += e.size
    print("mkinitramfs %s" % VERSION)
    print("declaration %s   (%d entries)" % (decl, len(entries)))
    print("unit tree   %s" % unit)
    print("spec        %s" % spec_path)
    print("manifest    %s" % man_path)
    print("")
    for k in KINDS:
        n = sum(1 for e in entries if e.kind == k)
        if n:
            print("  %-6s %3d" % (k, n))
    print("")
    for owner in OWNERS:
        n, b = by_owner.get(owner, (0, 0))
        print("  %-6s %3d entr%s, %d bytes of file content"
              % (owner, n, "y" if n == 1 else "ies", b))
    total = sum(e.size for e in entries)
    print("  total  %d bytes of file content before cpio and compression"
          % total)

    ceiling = a["ceiling"]
    img = a["kernel_image"]
    print("")
    if img:
        if not os.path.isfile(img):
            die("--kernel-image %s: no such file" % img)
        n, how = loaded_extent(img)
        margin = ceiling - n
        print("ceiling     decompressed image %d bytes (%s), ceiling %d, "
              "margin %d (%.1f%% used)"
              % (n, how, ceiling, margin, 100.0 * n / ceiling))
        if margin < 0:
            print("REFUSED: over the ceiling. The decompressor reads from "
                  "0x80500000 and writes to 0x80000000; this image would "
                  "overwrite its own input. The answer is "
                  "LOAD_START_ADDR=0x80A00000, not a smaller initramfs.")
            return 1
    else:
        print("ceiling     not checked -- pass --kernel-image to measure the "
              "margin against %d. The file content above is a LOWER bound on "
              "what the image grows by and says nothing on its own." % ceiling)
    print("")
    print("RESULT: \033[32mevery declared source resolved; nothing was "
          "substituted\033[0m")
    return 0


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------

GOOD = (
    "dir\t/bin\t-\t0755\tunit\t-\n"
    "dir\t/dev\t-\t0755\tunit\t-\n"
    "file\t/bin/busybox\t$UNIT/bin/busybox\t0755\tunit\tunmodified\n"
    "slink\t/bin/sh\tbusybox\t0777\tunit\tas the unit ships it\n"
    "nod\t/dev/console\tc:5:1\t0600\trlxfw\tinit gets no stdio without it\n"
    "file\t/init\t$REPO/init.sh\t0755\trlxfw\tmine\n"
)

# The controls' fixture tree has to satisfy the `unit` counterpart check now,
# so the dirs and the symlink have to exist in it.  run_controls() builds them.


class Controls(object):
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail):
        self.rows.append((name, bool(ok), detail))

    def skip(self, name, why):
        """A control that could not run says so, and is never counted as a pass.

        Only A7 can land here, and only on a host where an unprivileged process
        cannot create a symlink -- which is Windows, not the WSL side where
        every build actually happens.  A silent pass would be the worse of the
        two available lies.
        """
        self.rows.append((name, None, "SKIPPED -- " + why))

    @property
    def failed(self):
        return [r for r in self.rows if r[1] is False]

    @property
    def skipped(self):
        return [r for r in self.rows if r[1] is None]


# --- the `verify` fixture ---------------------------------------------------
# 🔴 EVERY CONTROL ABOVE THIS POINT IS ABOUT THE DECLARATION, and until
# 2026-09-01 that was the whole suite.  `cmd_verify` -- the half `CLAUDE.md`
# names as *the only one that can catch a mark that compiled and is not in the
# image* -- had NONE, and that is why the mutation suite this repository owed
# for five sessions could not be written: there was nothing to mutate against.
#
# The fixture is an ELF32 carrying a `.init.ramfs` newc archive, built here
# rather than taken from a build, so these run anywhere git does.  Both writers
# are deliberately independent of anything `build` uses: a fixture emitted by
# the code under test would agree with it however wrong both were.

def _cpio_newc(items):
    """items: [(name, mode, data, rdevmajor, rdevminor)] -> a newc archive.

    ⚠️ The padding is relative to the START OF THE ARCHIVE, and `parse_cpio`
    pads relative to the ABSOLUTE file offset -- so the caller must place the
    section on a four-byte boundary or the two disagree.  `_elf_with_section`
    does; this comment is here because nothing else would say so.
    """
    out = b""
    ino = 1
    for name, mode, data, rmaj, rmin in list(items) + [(CPIO_TRAILER, 0, b"", 0, 0)]:
        nb = name.encode() + b"\0"
        f = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, rmaj, rmin, len(nb), 0]
        out += CPIO_MAGIC + b"".join(b"%08X" % v for v in f) + nb
        out += b"\0" * ((-len(out)) % 4)
        out += data
        out += b"\0" * ((-len(out)) % 4)
        ino += 1
    return out


def _elf_with_section(path, secname, payload, big=True):
    """Write an ELF32 whose section header table names `secname`."""
    end = ">" if big else "<"
    names = b"\0" + secname.encode() + b"\0" + b".shstrtab\0"
    off_payload = 52
    off_names = off_payload + len(payload)
    off_names += (-off_names) % 4
    off_sh = off_names + len(names)
    off_sh += (-off_sh) % 4

    eh = bytearray(52)
    eh[0:4] = b"\x7fELF"
    eh[4] = 1                                   # ELFCLASS32
    eh[5] = 2 if big else 1
    eh[6] = 1
    struct.pack_into(end + "HHI", eh, 16, 2, 8, 1)          # ET_EXEC, EM_MIPS
    struct.pack_into(end + "III", eh, 24, 0, 0, off_sh)     # entry, phoff, shoff
    struct.pack_into(end + "IHHHHHH", eh, 36,
                     0, 52, 32, 0, 40, 3, 2)                # flags..shstrndx

    def shdr(name, typ, off, size, align):
        return struct.pack(end + "10I", name, typ, 0, 0, off, size, 0, 0,
                           align, 0)

    blob = bytes(eh) + payload
    blob += b"\0" * (off_names - len(blob))
    blob += names
    blob += b"\0" * (off_sh - len(blob))
    blob += shdr(0, 0, 0, 0, 0)                             # SHT_NULL
    blob += shdr(1, 1, off_payload, len(payload), 4)        # secname, PROGBITS
    blob += shdr(1 + len(secname) + 1, 3, off_names, len(names), 1)
    with open(path, "wb") as fh:
        fh.write(blob)
    return path


#: What the fixture declaration and its archive agree on when nothing is
#: planted.  The modes are the ones GOOD declares, so `declared_shape` and this
#: must match entry for entry.
_VFIX = [
    ("/bin", 0o040755, b"", 0, 0),
    ("/dev", 0o040755, b"", 0, 0),
    ("/bin/busybox", 0o100755, b"\x7fELFbusybox", 0, 0),
    ("/bin/sh", 0o120777, b"busybox", 0, 0),
    ("/dev/console", 0o020600, b"", 5, 1),
    ("/init", 0o100755, b"#!/bin/sh\n", 0, 0),
]


def _verify_run(d, items, decl_text=None, built_spec=None, secname=".init.ramfs"):
    """Run cmd_verify over a synthesised image.  -> (rc, stdout, refusal)."""
    import contextlib
    import io as _io
    global _RAISE
    unit = os.path.join(d, "unit")
    repo = os.path.join(d, "repo")
    decl = os.path.join(d, "decl.tsv")
    with open(decl, "w", encoding="utf-8") as fh:
        fh.write(decl_text if decl_text is not None else GOOD)
    img = _elf_with_section(os.path.join(d, "fx.elf"), secname,
                            _cpio_newc(items))
    a = {"decl": decl, "unit": unit, "repo": repo, "image": img,
         "built_spec": built_spec}
    buf = _io.StringIO()
    _RAISE = True
    try:
        with contextlib.redirect_stdout(buf):
            rc = cmd_verify(a)
        return rc, buf.getvalue(), None
    except Refused as ex:
        return None, buf.getvalue(), str(ex)
    finally:
        _RAISE = False


def _try(decl_text, unit, repo):
    global _RAISE
    _RAISE = True
    try:
        e = parse_decl("<decl>", decl_text)
        check_required(e, "<decl>")
        resolve(e, unit, repo, "<decl>")
        return None, e
    except Refused as ex:
        return str(ex), None
    finally:
        _RAISE = False


def run_controls():
    import tempfile
    c = Controls()
    with tempfile.TemporaryDirectory() as d:
        unit = os.path.join(d, "unit")
        repo = os.path.join(d, "repo")
        os.makedirs(os.path.join(unit, "bin"))
        os.makedirs(os.path.join(unit, "dev"))
        os.makedirs(repo)
        with open(os.path.join(unit, "bin", "busybox"), "wb") as f:
            f.write(b"\x7fELFbusybox")
        with open(os.path.join(repo, "init.sh"), "w") as f:
            f.write("#!/bin/sh\n")

        # The fixture tree has to look like a dump, because the `unit` tag is
        # now checked against one for every entry kind and not just for files.
        # Where symlinks cannot be created (an unprivileged Windows process),
        # the one `slink … unit` entry is retagged and the two controls that
        # need a real one say so rather than passing.
        can_link = True
        try:
            os.symlink("busybox", os.path.join(unit, "bin", "sh"))
        except OSError:
            can_link = False
        good = GOOD
        if not can_link:
            good = GOOD.replace("slink\t/bin/sh\tbusybox\t0777\tunit",
                                "slink\t/bin/sh\tbusybox\t0777\trlxfw")
            c.skip("A13 a `slink` tagged `unit` is checked against the dump",
                   "cannot create a symlink on this host")

        err, e = _try(good, unit, repo)
        c.add("A1  the real shape resolves", err is None and e is not None,
              err or "%d entries" % (len(e) if e else 0))

        # A2 -- THE control this tool exists for.
        bad = good.replace("$UNIT/bin/busybox", "$UNIT/bin/busybox-that-is-gone")
        err, _ = _try(bad, unit, repo)
        c.add("A2  a declared source that is NOT there is refused",
              err is not None and "not there" in err, (err or "did not refuse")[:70])

        # A3 -- /init missing: the image would fall through to root=.
        bad = "".join(l + "\n" for l in GOOD.strip().split("\n")
                      if not l.startswith("file\t/init"))
        err, _ = _try(bad, unit, repo)
        c.add("A3  a declaration with no /init is refused",
              err is not None and "prepare_namespace" in err,
              (err or "did not refuse")[:70])

        # A4 -- /dev/console missing: reads like a hang.
        bad = "".join(l + "\n" for l in GOOD.strip().split("\n")
                      if not l.startswith("nod\t/dev/console"))
        err, _ = _try(bad, unit, repo)
        c.add("A4  a declaration with no /dev/console is refused",
              err is not None and "no stdio" in err, (err or "did not refuse")[:70])

        # A5 -- the `unit` tag is checked, not trusted.
        bad = good.replace("file\t/bin/busybox\t$UNIT/bin/busybox\t0755\tunit",
                           "file\t/bin/busybox\t$REPO/init.sh\t0755\tunit")
        err, _ = _try(bad, unit, repo)
        c.add("A5  an entry tagged `unit` sourced outside the unit tree is "
              "refused", err is not None and "traceability" in err,
              (err or "did not refuse")[:70])

        # A6 -- whitespace in a source path breaks the dependency list.
        os.makedirs(os.path.join(unit, "bin with space"), exist_ok=True)
        with open(os.path.join(unit, "bin with space", "x"), "w") as f:
            f.write("x")
        bad = good.replace("$UNIT/bin/busybox", "$UNIT/bin with space/x")
        err, _ = _try(bad, unit, repo)
        c.add("A6  whitespace in a source path is refused",
              err is not None and "whitespace" in err,
              (err or "did not refuse")[:70])

        # A7 -- a symlink declared as a file would silently inline its target.
        # This unit's rootfs is 50 symlinks into busybox, so it is the entry
        # most likely to be written wrong.
        # The fixture already has `bin/sh -> busybox` if symlinks work here.
        if not can_link:
            c.skip("A7  a symlink declared as `file` is refused",
                   "cannot create a symlink on this host")
        if can_link:
            bad = good.replace("$UNIT/bin/busybox\t0755\tunit\tunmodified",
                               "$UNIT/bin/sh\t0755\tunit\tunmodified")
            err, _ = _try(bad, unit, repo)
            c.add("A7  a symlink declared as `file` is refused",
                  err is not None and "symlink" in err,
                  (err or "did not refuse")[:70])

        # A8 -- a duplicate path: gen_init_cpio takes both and the second wins.
        err, _ = _try(good + "file\t/init\t$REPO/init.sh\t0755\trlxfw\tagain\n",
                      unit, repo)
        c.add("A8  a duplicate path is refused",
              err is not None and "already declared" in err,
              (err or "did not refuse")[:70])

        # A9 -- an owner tag outside the closed set.
        err, _ = _try(GOOD.replace("\trlxfw\tmine", "\tprobably-mine\tmine"),
                      unit, repo)
        c.add("A9  an owner tag outside {unit, rlxfw} is refused",
              err is not None and "not one of" in err,
              (err or "did not refuse")[:70])

        # A10 -- the spec is what gen_init_cpio actually parses.
        err, e = _try(good, unit, repo)
        spec = emit_spec(e) if e else ""
        fl = [l for l in spec.split("\n") if l.startswith("file /bin/busybox ")]
        ok = ("nod /dev/console 0600 0 0 c 5 1" in spec
              and "slink /bin/sh busybox 0777 0 0" in spec
              and "dir /bin 0755 0 0" in spec
              # the path in the middle is the host's, so match the shape
              and len(fl) == 1 and fl[0].endswith(" 0755 0 0"))
        c.add("A10 the emitted spec is in gen_init_cpio's four forms", ok,
              "dir/file/slink/nod all in the shape usr/gen_init_cpio.c:458-461 "
              "documents")

        # A11 -- the manifest records a digest of the BYTES that were read.
        # The first version computed its expectation with sha256(), the function
        # under test, so a mutant that hashed the path instead of the contents
        # passed it.  hashlib directly, on bytes this control writes itself.
        man = emit_manifest(e, unit, repo) if e else ""
        want = hashlib.sha256(b"\x7fELFbusybox").hexdigest()
        c.add("A11 the manifest carries a digest of the source's BYTES",
              want in man, want[:16])

        # A12 -- an empty declaration is refused, not built.
        err, _ = _try("# only a comment\n", unit, repo)
        c.add("A12 an empty declaration is refused",
              err is not None and "No init found" in err,
              (err or "did not refuse")[:70])

        # ---- the checks the adversarial pass of 2026-08-28 added, each with
        # the input that used to get past it.
        if can_link:
            # A13: 15 of the real declaration's 31 entries are `slink` and the
            # tag was checked for `file` only. Turning it on found two wrong.
            bad = good.replace("slink\t/bin/sh\tbusybox",
                               "slink\t/bin/sh\tnot-busybox")
            err, _ = _try(bad, unit, repo)
            ok1 = err is not None and "points at" in err
            bad = good.replace("slink\t/bin/sh\tbusybox\t0777\tunit",
                               "slink\t/bin/nosuch\tbusybox\t0777\tunit")
            err, _ = _try(bad, unit, repo)
            ok2 = err is not None and "no\nsymlink" not in err
            c.add("A13 a `slink` tagged `unit` is checked against the dump",
                  ok1 and ok2,
                  "a wrong target and a link the dump does not have both refuse")

        # A14 -- /init as anything but an executable regular file lands in
        # prepare_namespace(), which on this device mounts the vendor rootfs.
        bads = [
            ("a dangling slink",
             good.replace("file\t/init\t$REPO/init.sh\t0755\trlxfw\tmine",
                          "slink\t/init\t/bin/nothing-here\t0777\trlxfw\tmine")),
            ("a directory",
             good.replace("file\t/init\t$REPO/init.sh\t0755\trlxfw\tmine",
                          "dir\t/init\t-\t0755\trlxfw\tmine")),
            ("a device node",
             good.replace("file\t/init\t$REPO/init.sh\t0755\trlxfw\tmine",
                          "nod\t/init\tc:1:3\t0666\trlxfw\tmine")),
            ("mode 0644",
             good.replace("$REPO/init.sh\t0755\trlxfw\tmine",
                          "$REPO/init.sh\t0644\trlxfw\tmine")),
        ]
        missed = [w for w, t in bads if _try(t, unit, repo)[0] is None]
        c.add("A14 /init must be an EXECUTABLE REGULAR FILE",
              not missed,
              "4/4 refused" if not missed else "accepted: " + ", ".join(missed))

        # A15 -- a `nod`'s major/minor were never parsed, so a wrong console
        # device passed while A4 stayed green.
        bads = ["c:4:64", "c:5:1abc", "c::1", "x:5:1"]
        missed = [v for v in bads
                  if _try(good.replace("c:5:1", v), unit, repo)[0] is None]
        c.add("A15 a nod's major/minor are parsed, not passed through",
              not missed,
              "4/4 refused" if not missed else "accepted: " + ", ".join(missed))

        # A16 -- differently-spelled duplicates.  gen_init_cpio writes both.
        bads = ["//init", "/bin/./busybox", "/bin/../bin/busybox"]
        missed = [v for v in bads
                  if _try(good + "file\t%s\t$REPO/init.sh\t0755\trlxfw\tdup\n"
                          % v, unit, repo)[0] is None]
        c.add("A16 a path not in normal form is REFUSED",
              not missed,
              "3/3 refused" if not missed else "accepted: " + ", ".join(missed))

        # A17 -- the whitespace ban has to cover the IMAGE PATH too: it goes
        # into the same `while read type dir file perm` the ban is cited against.
        err, _ = _try(good.replace("/bin/busybox\t$UNIT",
                                   "/bin/busy box\t$UNIT"), unit, repo)
        c.add("A17 whitespace in the IMAGE PATH is refused too",
              err is not None and "whitespace" in err,
              (err or "did not refuse")[:70])

        # A18 -- a mode that is not three or four octal digits.
        bads = ["-1", "0o755", "7_5_5", "8755"]
        missed = [v for v in bads
                  if _try(good.replace("$REPO/init.sh\t0755", "$REPO/init.sh\t" + v),
                          unit, repo)[0] is None]
        c.add("A18 the mode must be three or four octal digits",
              not missed,
              "4/4 refused" if not missed else "accepted: " + ", ".join(missed))

        # A19 -- a slink pointing at something nothing puts in the image.  The
        # mutation must not assume the fixture's owner tag: on a host without
        # symlinks `good` carries `rlxfw` there, and a replace keyed on `unit`
        # silently did nothing and the control passed for no reason.
        bad = good.replace("slink\t/bin/sh\tbusybox\t0777\tunit\t",
                           "slink\t/bin/sh\tnowhere\t0777\trlxfw\t")
        bad = bad.replace("slink\t/bin/sh\tbusybox\t0777\trlxfw\t",
                          "slink\t/bin/sh\tnowhere\t0777\trlxfw\t")
        assert "nowhere" in bad, "A19's mutation did not land"
        err, _ = _try(bad, unit, repo)
        c.add("A19 a slink whose target is not in the image is refused",
              err is not None and "puts in the image" in err,
              (err or "did not refuse")[:70])

        # --- A20-A22: the ceiling measures the IMAGE, not the FILE --------
        # 🔴 Until 2026-08-28 this was os.path.getsize(vmlinux). 量 on the R3
        # kernel: the file is 3,968,113 and the image is 3,472,384, so the
        # ceiling read 75.7 % used where the truth was 66.2 %. The fixture
        # below is built so the two numbers CANNOT coincide -- 0x200 bytes of
        # PT_LOAD inside a file padded well past it -- because a control on a
        # fixture where file size and load extent agree could not have failed.
        eh = (b"\x7fELF" + bytes(bytearray([1, 2, 1, 0])) + bytes(8)
              + struct.pack(">HHI", 2, 8, 1)
              + struct.pack(">III", 0x80000000, 52, 0)
              + struct.pack(">I", 0)
              + struct.pack(">HHHHHH", 52, 32, 1, 40, 0, 0))
        ph = struct.pack(">8I", 1, 84, 0x80000000, 0x80000000,
                         0x200, 0x400, 5, 0x1000)
        blob = eh + ph + b"\0" * 0x200 + b"\xAA" * 0x4000   # padding after
        p_elf = os.path.join(d, "fx.elf")
        open(p_elf, "wb").write(blob)
        n, how = loaded_extent(p_elf)
        c.add("A20 the ceiling reads PT_LOAD p_filesz, not the file size",
              n == 0x200 and os.path.getsize(p_elf) > 0x4000,
              "extent %d (%s) against a %d-byte file -- must be 512"
              % (n, how, os.path.getsize(p_elf)))

        # A21 -- p_filesz and not p_memsz.  .bss is not in what the
        # decompressor writes; the fixture's memsz is deliberately 0x400.
        c.add("A21 and p_filesz, not p_memsz -- .bss is not in the payload",
              n == 0x200, "memsz is 0x400 in the fixture, extent read %d" % n)

        # A22 -- a flat file is already the image, and an ELF with nothing
        # loadable is an error rather than a very small image that passes.
        p_flat = os.path.join(d, "fx.bin")
        open(p_flat, "wb").write(b"\xAA" * 1234)
        nf, howf = loaded_extent(p_flat)
        bad = eh[:40] + struct.pack(">HHHHHH", 52, 32, 0, 40, 0, 0)
        p_bad = os.path.join(d, "fx-noload.elf")
        open(p_bad, "wb").write(bad + b"\0" * 64)
        try:
            loaded_extent(p_bad)
            ok22 = False
        except (Refused, SystemExit):
            ok22 = True
        # A23 -- and a truncated program header table refuses rather than
        # raising struct.error.  A gate that crashes is a gate whose answer
        # nobody writes down; A22's first fixture found this by accident.
        p_trunc = os.path.join(d, "fx-trunc.elf")
        open(p_trunc, "wb").write(blob[:60])
        try:
            loaded_extent(p_trunc)
            ok23 = False
        except (Refused, SystemExit):
            ok23 = True
        c.add("A22 a flat file measures itself; an ELF with no PT_LOAD refuses",
              nf == 1234 and howf == "flat file" and ok22,
              "flat %d (%s), no-PT_LOAD refused %s" % (nf, howf, ok22))
        c.add("A23 a truncated program header table refuses, not tracebacks",
              ok23, "refused %s" % ok23)
        # --- A24-A26: the flash-write node ban -----------------------------
        # A24 -- it fires.  All three of these were reachable declarations:
        # mtdblock0 is the one 17.7a talked itself out of, mtdblock1 is the one
        # that was IN THIS FILE until today, and c:90:0 is the even mtdchar
        # minor that looks like the node the step originally asked for.
        bads = [
            ("mtdblock0", "nod\t/dev/mtdblock0\tb:31:0\t0400\trlxfw\tx\n"),
            ("mtdblock1", "nod\t/dev/mtdblock1\tb:31:1\t0400\trlxfw\tx\n"),
            ("mtd0 even", "nod\t/dev/mtd0\tc:90:0\t0400\trlxfw\tx\n"),
        ]
        missed = [w for w, t in bads if _try(good + t, unit, repo)[0] is None]
        c.add("A24 a node the kernel would let root write flash through",
              not missed,
              "3/3 refused" if not missed else "accepted: " + ", ".join(missed))

        # A25 -- and it does NOT fire on the two nodes this image needs, which
        # is what stops A24 being passed by a ban that refuses everything.
        oks = [
            ("mtd0ro", "nod\t/dev/mtd0ro\tc:90:1\t0400\trlxfw\tx\n"),
            ("mtd1ro", "nod\t/dev/mtd1ro\tc:90:3\t0400\trlxfw\tx\n"),
        ]
        wrong = [w for w, t in oks if _try(good + t, unit, repo)[0] is not None]
        c.add("A25 …and an ODD mtdchar minor is accepted (control on A24)",
              not wrong,
              "2/2 accepted" if not wrong else "refused: " + ", ".join(wrong))

        # A26 -- the rule reads the dev numbers, not the path.  A15's defect
        # one level up: a nod's major/minor were once passed through as text,
        # and a ban keyed on the NAME would pass A24 and A25 both.
        err_name, _ = _try(
            good + "nod\t/dev/harmless\tb:31:9\t0400\trlxfw\tx\n", unit, repo)
        err_high, _ = _try(
            good + "nod\t/dev/mtd9ro\tc:90:19\t0400\trlxfw\tx\n", unit, repo)
        c.add("A26 the ban keys on major/minor, never on the path",
              err_name is not None and err_high is None,
              "b:31:9 named /dev/harmless refused=%s; c:90:19 accepted=%s"
              % (err_name is not None, err_high is None))

        # --- V1..V8: `cmd_verify`, which had no controls at all -------------
        # Every case drives the WHOLE subcommand over a synthesised image, so
        # what is asserted is the verdict and not a helper's return value.
        vok, vout, _ = _verify_run(d, _VFIX)
        c.add("V1  a clean image verifies, and it is the positive control",
              vok == 0 and "every one matches" in vout,
              "rc=%s" % vok)

        miss = [x for x in _VFIX if x[0] != "/bin/sh"]
        vrc, vout, _ = _verify_run(d, miss)
        c.add("V2  a declared entry absent from the image is MISSING",
              vrc == 1 and "MISSING" in vout and "/bin/sh" in vout,
              "rc=%s" % vrc)

        extra = _VFIX + [("/bin/telnetd", 0o100755, b"x", 0, 0)]
        vrc, vout, _ = _verify_run(d, extra)
        c.add("V3  an entry in the image and in no row is UNEXPECTED",
              vrc == 1 and "UNEXPECTED" in vout and "/bin/telnetd" in vout,
              "rc=%s" % vrc)

        wrongmode = [(n_, 0o100777 if n_ == "/init" else m, dd, rj, rn)
                     for n_, m, dd, rj, rn in _VFIX]
        vrc, vout, _ = _verify_run(d, wrongmode)
        c.add("V4  a mode that differs from the declaration is DIFFERS",
              vrc == 1 and "DIFFERS" in vout and "mode" in vout,
              "rc=%s" % vrc)

        # V5 -- the dev numbers, which are the ones a wrong image would use to
        # hand root a writable flash node.  A24-A26 ban that in the
        # DECLARATION; nothing had ever checked the IMAGE.
        wrongdev = [(n_, m, dd, (31 if n_ == "/dev/console" else rj),
                     (9 if n_ == "/dev/console" else rn))
                    for n_, m, dd, rj, rn in _VFIX]
        vrc, vout, _ = _verify_run(d, wrongdev)
        # 🔴 THE ASSERTION NAMES THE NUMBERS, and the first version did not.
        # It read `"dev" in vout`, and `dev` occurs three lines above in
        # *device nodes in the image* -- so `M4`, which deletes the dev
        # comparison entirely, left this case GREEN.  The outer `w != h` still
        # fires, so the finding is still REPORTED; what the mutation removes is
        # the REASON, and only a case that reads the reason can see that.
        c.add("V5  a dev major/minor that differs is DIFFERS, WITH the numbers",
              vrc == 1 and "DIFFERS" in vout and "dev 5:1 vs 31:9" in vout,
              "rc=%s" % vrc)

        # V6 -- the image the kernel builds when CONFIG_INITRAMFS_SOURCE="" is
        # an image with no section, and that is a finding rather than a missing
        # file.  The refusal must SAY so.
        _vrc, _vout, vref = _verify_run(d, _VFIX, secname=".notramfs")
        c.add("V6  an image with no `.init.ramfs` refuses, and names why",
              vref is not None and "CONFIG_INITRAMFS_SOURCE" in vref,
              (vref or "no refusal")[:46])

        # V7 -- the built-spec drift refusal.  Without it a difference below
        # would be the declaration's and not the image's, and the two repairs
        # are opposite.
        bs = os.path.join(d, "stale.spec")
        with open(bs, "w", encoding="utf-8") as fh:
            fh.write("dir /bin 0755 0 0\n")
        vrc, vout, _ = _verify_run(d, _VFIX, built_spec=bs)
        c.add("V7  a declaration that changed since the build REFUSES",
              vrc == 2 and "has CHANGED since this image was built" in vout,
              "rc=%s" % vrc)

        # V8 -- the control on V7: the SAME check must accept the spec this
        # declaration actually emits, or V7 passes on a checker that refuses
        # everything.
        bs2 = os.path.join(d, "fresh.spec")
        with open(bs2, "w", encoding="utf-8") as fh:
            fh.write(emit_spec(_try(GOOD, unit, repo)[1]))
        vrc, vout, _ = _verify_run(d, _VFIX, built_spec=bs2)
        c.add("V8  …and accepts the spec it does emit (control on V7)",
              vrc == 0 and "identical to what this declaration emits" in vout,
              "rc=%s" % vrc)

    return c


def main(argv):
    if not argv:
        die("no command. One of: build, verify, self-test")
    cmd, rest = argv[0], argv[1:]

    if cmd == "self-test":
        c = run_controls()
        print("controls (they run first; nothing is built if one fails)")
        for name, ok, detail in c.rows:
            # Uncoloured: tools/ci-census.py counts these with
            # `^ {2}(ok|FAIL|skip)\s{2,}` and an escape sequence hides them.
            mark = "ok" if ok is True else "skip" if ok is None else "FAIL"
            print("  %-5s %-58s %s" % (mark, name, detail))
        print("")
        nf, ns = len(c.failed), len(c.skipped)
        if nf:
            print("RESULT: %d passed, \033[31m%d failed\033[0m, %d skipped"
                  % (len(c.rows) - nf - ns, nf, ns))
            return 2
        print("RESULT: \033[32m%d passed, 0 failed\033[0m, %d skipped"
              % (len(c.rows) - ns, ns))
        return 0

    if cmd == "verify":
        a = {"decl": None, "unit": None, "repo": None, "image": None,
             "built_spec": None}
        i = 0
        while i < len(rest):
            x = rest[i]
            if x in ("--decl", "--unit", "--repo", "--image", "--built-spec"):
                if i + 1 >= len(rest):
                    die("%s needs a value" % x)
                a[x[2:].replace("-", "_")] = rest[i + 1]
                i += 2
            else:
                die("unknown option %s" % x)
        for k in ("decl", "unit", "repo", "image"):
            if not a[k]:
                die("verify needs --%s" % k)
        for k in ("decl", "image"):
            if not os.path.isfile(a[k]):
                die("--%s %s: no such file" % (k, a[k]))
        c = run_controls()
        if c.failed:
            print("REFUSED: %d control(s) failed; nothing is reported about an "
                  "image until the tool itself is trusted." % len(c.failed))
            return 2
        return cmd_verify(a)

    if cmd != "build":
        die("unknown command %r" % cmd)

    a = {"decl": None, "unit": None, "repo": None, "out": None,
         "kernel_image": None, "ceiling": CEILING}
    i = 0
    while i < len(rest):
        x = rest[i]
        key = x[2:].replace("-", "_")
        if x in ("--decl", "--unit", "--repo", "--out", "--kernel-image"):
            if i + 1 >= len(rest):
                die("%s needs a value" % x)
            a[key] = rest[i + 1]
            i += 2
        elif x == "--ceiling":
            a["ceiling"] = int(rest[i + 1], 0)
            i += 2
        else:
            die("unknown option %s" % x)
    for k in ("decl", "unit", "repo", "out"):
        if not a[k]:
            die("build needs --%s" % k)
    if not os.path.isfile(a["decl"]):
        die("--decl %s: no such file" % a["decl"])
    if not os.path.isdir(a["unit"]):
        die("--unit %s: no such directory. This is the tree carved out of this "
            "device's own dump and nothing is built without it" % a["unit"])

    c = run_controls()
    if c.failed:
        print("REFUSED: %d control(s) failed; nothing is built until the tool "
              "itself is trusted." % len(c.failed))
        for name, ok, detail in c.rows:
            if not ok:
                print("  FAIL %s  %s" % (name, detail))
        return 2
    return cmd_build(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
