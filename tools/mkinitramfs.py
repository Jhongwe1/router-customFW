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

VERSION = "1.0"

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
    return entries


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
    return c


def main(argv):
    if not argv:
        die("no command. One of: build, self-test")
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
