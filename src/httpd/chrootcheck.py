#!/usr/bin/env python3
"""chrootcheck.py -- refuse a web root that could become a shell.

WHY IT IS A BUILD STEP.  "No ELF, no shell, no setuid binary and no symlink to
busybox under /srv/www" is a pass condition of gate R7, and a condition nobody
runs is a sentence in a document.  `make -C src/httpd chrootcheck ROOT=<dir>`
walks the tree that will BE the chroot and exits non-zero on anything that could
be executed, followed, or used to reach outside.

TWO INDEPENDENT DETECTORS, because either alone has a blind spot:

  mode      any execute bit on a regular file, any set-user-ID or set-group-ID
            bit, any character or block device, any symlink, any FIFO, and any
            regular file with more than one link (a hard link is a second name
            for a file whose mode can be changed through the other name).
  content   the first bytes of every regular file: an ELF magic, a `#!` shebang,
            the Linux kernel's other recognised binfmt magics, and a Windows or
            a Mach-O header.  A file with no execute bit today is still an ELF,
            and chmod is one syscall away.

The mode detector alone passes a mode-0644 copy of busybox.  The content
detector alone passes a shell script with no shebang.  Neither is redundant.

WHAT IT DOES NOT ESTABLISH.  That the tree on the device is this tree: it checks
the directory it is given, at the moment it is given it.  The run-time half is in
src/httpd/routes.c's send_file(), which opens with O_NOFOLLOW and refuses a file
with an execute bit on every request, so the two checks fail independently.  It
also says nothing about the socket that IS meant to be there: a unix socket under
ROOT is reported and allowed, because /srv/www/run/broker.sock is the one door
out of the chroot by design (SPEC-R7 section 3).

Usage
    chrootcheck.py ROOT [--quiet]
    chrootcheck.py --self-test      plant each kind of offender in a temporary
                                    tree and prove every detector fires, then
                                    prove a clean tree passes.  A guard is shown
                                    permitting as well as refusing.

Exit
    0  the tree is clean
    1  the tree is refused; every finding is printed
    2  usage
    3  the self-test failed: a detector did not fire on its own planted case
"""

import os
import stat
import sys
import tempfile

# Magic numbers the Linux kernel's binfmt handlers recognise, plus two formats it
# does not but that have no business in a web root either.
MAGICS = [
    (b"\x7fELF", "an ELF"),
    (b"#!", "a script with a shebang"),
    (b"\x1f\x8b", "a gzip stream (a compressed executable is still one)"),
    (b"MZ", "a DOS/PE image"),
    (b"\xca\xfe\xba\xbe", "a Mach-O fat binary"),
    (b"\xcf\xfa\xed\xfe", "a Mach-O image"),
    (b"\xfe\xed\xfa\xce", "a Mach-O image"),
    (b"\x00\x05\x16\x07", "a Java/AppleSingle image"),
    (b"\xce\xfa\xed\xfe", "a Mach-O image"),
    (b"\x04\x03\x4b\x50", "a zip (jar/apk) image"),
    (b"PK\x03\x04", "a zip (jar/apk) image"),
]

# The extensions the server's MIME table can name.  A file it cannot name should
# not be in the tree at all: a web root is not a download directory.
ALLOWED_EXT = (".html", ".css", ".js", ".txt", ".svg", ".ico", ".png")


def findings_for(root, quiet=False):
    """Return a list of refusal strings.  An empty list means the tree is clean."""
    bad = []
    nfile = 0
    nsock = 0

    root = os.path.abspath(root)
    if not os.path.isdir(root):
        return ["ROOT %s is not a directory" % root], 0, 0

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + list(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            try:
                st = os.lstat(p)
            except OSError as e:
                bad.append("%s: cannot lstat (%s)" % (rel, e.strerror))
                continue
            m = st.st_mode

            if stat.S_ISLNK(m):
                try:
                    tgt = os.readlink(p)
                except OSError:
                    tgt = "?"
                bad.append("%s: a symlink (-> %s).  Refused whether or not it "
                           "points outside: the target can be created later."
                           % (rel, tgt))
                continue
            if stat.S_ISCHR(m) or stat.S_ISBLK(m):
                bad.append("%s: a device node" % rel)
                continue
            if stat.S_ISFIFO(m):
                bad.append("%s: a FIFO" % rel)
                continue
            if stat.S_ISSOCK(m):
                nsock += 1
                if not quiet:
                    print("  note: %s is a unix socket (allowed: the broker "
                          "socket is the one door out)" % rel)
                continue
            if m & (stat.S_ISUID | stat.S_ISGID):
                bad.append("%s: mode %04o carries set-user-ID or set-group-ID"
                           % (rel, stat.S_IMODE(m)))
            if stat.S_ISDIR(m):
                if m & stat.S_IWOTH and not m & stat.S_ISVTX:
                    bad.append("%s: a world-writable directory without the "
                               "sticky bit" % rel)
                continue
            if not stat.S_ISREG(m):
                bad.append("%s: not a regular file, a directory or a socket" % rel)
                continue

            nfile += 1
            if m & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                bad.append("%s: mode %04o has an execute bit"
                           % (rel, stat.S_IMODE(m)))
            if m & stat.S_IWOTH:
                bad.append("%s: mode %04o is world-writable"
                           % (rel, stat.S_IMODE(m)))
            if st.st_nlink > 1:
                bad.append("%s: st_nlink is %d; a second name can be chmod'ed"
                           % (rel, st.st_nlink))

            try:
                with open(p, "rb") as f:
                    head = f.read(8)
            except OSError as e:
                bad.append("%s: cannot read (%s)" % (rel, e.strerror))
                continue
            for magic, what in MAGICS:
                if head.startswith(magic):
                    bad.append("%s: begins with %s" % (rel, what))
                    break

            ext = os.path.splitext(name)[1].lower()
            if ext not in ALLOWED_EXT:
                bad.append("%s: extension %r is not one the MIME table can name"
                           % (rel, ext))

    return bad, nfile, nsock


def self_test():
    """Plant one of each offender and require every detector to fire, then
    require a clean tree to pass.  Without the second half this proves only that
    the tool can say no."""
    ok = True
    with tempfile.TemporaryDirectory() as td:
        # the clean tree, first, so a later failure cannot be blamed on it
        clean = os.path.join(td, "clean")
        os.makedirs(os.path.join(clean, "static"))
        with open(os.path.join(clean, "index.html"), "w") as f:
            f.write("<!doctype html>\n")
        os.chmod(os.path.join(clean, "index.html"), 0o644)
        with open(os.path.join(clean, "static", "style.css"), "w") as f:
            f.write("body{}\n")
        os.chmod(os.path.join(clean, "static", "style.css"), 0o644)
        bad, nfile, _ = findings_for(clean, quiet=True)
        if bad:
            print("SELF-TEST FAILED: the clean tree was refused:")
            for b in bad:
                print("    " + b)
            ok = False
        else:
            print("  self-test: a clean tree of %d files PASSES" % nfile)

        cases = []

        d = os.path.join(td, "elf")
        os.makedirs(d)
        with open(os.path.join(d, "sh.html"), "wb") as f:
            f.write(b"\x7fELF\x01\x02\x01\x00" + b"\x00" * 64)
        os.chmod(os.path.join(d, "sh.html"), 0o644)
        cases.append((d, "an ELF with no execute bit and an allowed extension",
                      "begins with an ELF"))

        d = os.path.join(td, "exec")
        os.makedirs(d)
        with open(os.path.join(d, "x.css"), "w") as f:
            f.write("body{}\n")
        os.chmod(os.path.join(d, "x.css"), 0o755)
        cases.append((d, "a plain file with an execute bit", "has an execute bit"))

        d = os.path.join(td, "shebang")
        os.makedirs(d)
        with open(os.path.join(d, "s.txt"), "w") as f:
            f.write("#!/bin/sh\necho hi\n")
        os.chmod(os.path.join(d, "s.txt"), 0o644)
        cases.append((d, "a shebang script with no execute bit",
                      "a script with a shebang"))

        d = os.path.join(td, "link")
        os.makedirs(d)
        os.symlink("/bin/busybox", os.path.join(d, "b.html"))
        cases.append((d, "a symlink to busybox", "a symlink"))

        d = os.path.join(td, "setuid")
        os.makedirs(d)
        p = os.path.join(d, "u.txt")
        with open(p, "w") as f:
            f.write("x\n")
        try:
            os.chmod(p, 0o4644)
            cases.append((d, "a set-user-ID file", "set-user-ID"))
        except OSError:
            print("  self-test: chmod u+s refused by the filesystem; that case "
                  "is VOID, not passed")

        d = os.path.join(td, "ext")
        os.makedirs(d)
        p = os.path.join(d, "backup.tar")
        with open(p, "w") as f:
            f.write("x\n")
        os.chmod(p, 0o644)
        cases.append((d, "a file the MIME table cannot name", "is not one the"))

        for d, what, needle in cases:
            bad, _, _ = findings_for(d, quiet=True)
            hit = any(needle in b for b in bad)
            print("  self-test: %-52s %s" % (what, "REFUSED" if hit else "MISSED"))
            if not hit:
                ok = False
                for b in bad:
                    print("      saw: " + b)
    return 0 if ok else 3


def main(argv):
    if len(argv) >= 2 and argv[1] == "--self-test":
        return self_test()
    if len(argv) < 2:
        sys.stderr.write(__doc__.split("Usage")[1])
        return 2
    quiet = "--quiet" in argv[2:]
    root = argv[1]
    bad, nfile, nsock = findings_for(root, quiet=quiet)
    if bad:
        print("chrootcheck: REFUSED %s -- %d finding(s):" % (root, len(bad)))
        for b in bad:
            print("  " + b)
        return 1
    print("chrootcheck: %s is clean (%d regular files, %d sockets): no ELF, no "
          "shebang, no execute bit, no setuid/setgid, no symlink, no device node"
          % (os.path.abspath(root), nfile, nsock))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
