#!/usr/bin/env python3
"""Record every path under a root with the metadata a restore has to reproduce.

A content hash alone is not enough for this tree. Of 7,776 paths under
$FWRE_WORK, 762 are symlinks and 12 are device nodes -- neither has content for
sha256 to see -- and 294 carry a setuid or setgid bit, which is not content
either. A restore that turned every symlink into a regular file and flattened
every mode to 0644 would compare equal on content alone and be wrong in exactly
the way that matters here, because on this project part of the finding IS the
filesystem metadata.

Output is one TSV line per path, sorted bytewise by path, followed by a trailer
of counts. The trailer is the scope control: `unreadable` must be 0. A scan that
could not enter part of the tree is a scan whose zero means nothing -- and a
backup taken the same way would have skipped the same paths, silently.

Columns
  type   f d l b c p s  (regular, dir, symlink, block, char, fifo, socket)
  mode   4-digit octal, setuid/setgid/sticky included
  uid    numeric -- names are not stable across machines
  gid    numeric
  size   bytes for regular files, else 0
  mtime  seconds, integer
  digest sha256 hex | ->TARGET for a symlink | dev:MAJ:MIN for a node | -
  path   relative to the root

Known limits, recorded rather than hidden:
  - xattrs and POSIX ACLs are not captured. Check separately that none exist.
  - Hardlinks are recorded as independent paths, so a restore that broke the
    link but kept the content would compare equal.
  - The scan is not atomic. Nothing may write to the tree while it runs.
"""

import hashlib
import os
import stat
import sys

TYPE = [
    (stat.S_ISREG, "f"), (stat.S_ISDIR, "d"), (stat.S_ISLNK, "l"),
    (stat.S_ISBLK, "b"), (stat.S_ISCHR, "c"), (stat.S_ISFIFO, "p"),
    (stat.S_ISSOCK, "s"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root, fail):
    """Every path under root, each exactly once, never following a symlink.

    os.walk is not used: it files a symlink-to-directory under dirnames, so
    recording dirpath+filenames would miss it and recording dirnames as well
    would count every real directory twice.
    """
    yield root
    stack = [root]
    while stack:
        try:
            entries = sorted(os.scandir(stack.pop()), key=lambda e: e.name)
        except OSError as exc:
            fail(exc)
            continue
        for entry in entries:
            yield entry.path
            try:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
            except OSError as exc:
                fail(exc)


def main(root, out):
    root = os.path.abspath(root)
    rows, counts, special = [], {}, 0
    bad = []

    for full in walk(root, bad.append):
        try:
            st = os.lstat(full)
        except OSError as exc:
            bad.append(exc)
            continue

        kind = next((c for pred, c in TYPE if pred(st.st_mode)), "?")
        counts[kind] = counts.get(kind, 0) + 1
        mode = stat.S_IMODE(st.st_mode)
        if mode & (stat.S_ISUID | stat.S_ISGID):
            special += 1

        if kind == "l":
            digest = "->" + os.readlink(full)
        elif kind in ("b", "c"):
            digest = "dev:%d:%d" % (os.major(st.st_rdev), os.minor(st.st_rdev))
        elif kind == "f":
            try:
                digest = sha256(full)
            except OSError as exc:
                bad.append(exc)
                digest = "UNREADABLE"
        else:
            digest = "-"

        rel = "." if full == root else os.path.relpath(full, root)
        if "\t" in rel or "\n" in rel:
            sys.exit("path contains a tab or newline, TSV cannot hold it: %r" % rel)
        rows.append("%s\t%04o\t%d\t%d\t%d\t%d\t%s\t%s" % (
            kind, mode, st.st_uid, st.st_gid,
            st.st_size if kind == "f" else 0,
            int(st.st_mtime), digest, rel))

    rows.sort(key=lambda r: r.rsplit("\t", 1)[1].encode())
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(r + "\n" for r in rows))
        fh.write("# root %s\n" % root)
        fh.write("# paths %d\n" % len(rows))
        for k in sorted(counts):
            fh.write("# type.%s %d\n" % (k, counts[k]))
        fh.write("# setuid_setgid %d\n" % special)
        fh.write("# unreadable %d\n" % len(bad))

    print("paths=%d types=%s setuid_setgid=%d unreadable=%d"
          % (len(rows), counts, special, len(bad)))
    for exc in bad[:5]:
        print("  unreadable: %s" % exc, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: fsmanifest.py ROOT OUT.tsv")
    sys.exit(main(sys.argv[1], sys.argv[2]))
