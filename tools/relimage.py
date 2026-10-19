#!/usr/bin/env python3
"""relimage -- read what a released rlxfw image holds, from its bytes alone.

An image (`nfjrom`, the file a release publishes as `mainline-<recipe>.img`) is
the loader stub followed by an 8-byte `cvimg` header and an LZMA `alone`
stream of the flat kernel image, `vmlinux_img`, whose `.init.ramfs` carries the
initramfs as a newc cpio (`tools/rtkimage.py`'s header gives the pipeline).
This tool finds the stream by its own header, decodes it, finds the cpio and
parses it.  It needs no build product, no symbol table and no typed offset.

USAGE
  relimage.py info    --image FILE    stream offset, sizes, banner, cpio census
  relimage.py files   --image FILE    one row per cpio file: path, bytes, sha256
  relimage.py extract --image FILE --member PATH --out FILE
  relimage.py srcdir  --image FILE --member PATH --names A.c,B.c,...
        the one absolute directory the named source files were compiled
        from, as their `__FILE__` strings in that member record it
  relimage.py paths   --image FILE [--member PATH]
        every NUL-terminated string that is an absolute path ending in .c, .h
        or .S -- a `__FILE__` a build embedded -- in the kernel image, or in
        one member

Every verb first decodes the image twice: once as given, which must reach the
end of the stream with the length the LZMA header declares, and once cut in
the middle of the stream, which must not decode.  If the second is accepted
the reader cannot tell a damaged image from a good one, and the verb exits 2
without printing a result.  An LZMA `alone` stream carries no checksum, so a
flipped bit inside it may decode to other bytes of the right length: what
this tool extracts is evidence only beside a second source for the same bytes
(for a release, the digests `docs/sbom.md` lists for the initramfs files).

EXIT  0 read; 1 the image does not hold what was asked (no stream, no cpio, no
      such member, not exactly one directory); 2 the cut-stream control was
      accepted; 3 usage.

WHAT IT DOES NOT ESTABLISH
  * That the image boots, or that the stub before the stream is the drop's.
  * That the stream it decodes is the one the stub decompresses: it is the
    first offset whose header and decode both hold (`docs/sbom.md` § 3 names
    the same offset for v1.0's image).
  * Anything about a string's use: `paths` lists what a build embedded, not
    what the code prints.
"""

import argparse
import hashlib
import lzma
import os
import re
import stat
import struct
import sys

NEWC = b"070701"


class Fail(Exception):
    pass


def decode(raw):
    """The first offset whose cvimg header and LZMA stream both hold."""
    for o in range(0, len(raw) - 21):
        props = raw[o + 8]
        if props >= 225:
            continue
        dic, = struct.unpack_from("<I", raw, o + 9)
        lo, hi = struct.unpack_from("<II", raw, o + 13)
        if hi or not (1 << 20) <= lo <= (64 << 20) or dic & (dic - 1) or dic < 4096:
            continue
        kstart, = struct.unpack_from(">I", raw, o + 4)
        if kstart >> 24 != 0x80:
            continue
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        try:
            plain = d.decompress(raw[o + 8:])
        except lzma.LZMAError:
            continue
        if d.eof and len(plain) == lo:
            return o, len(raw) - len(d.unused_data), kstart, plain
    raise Fail("no cvimg header followed by a complete LZMA stream")


def decode_checked(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    o, end, kstart, plain = decode(raw)
    # The control: the same image cut in the middle of its stream must not
    # decode.  An LZMA `alone` stream carries no checksum, so a flipped bit is
    # not guaranteed to be refused; a short stream is, by the end-of-stream and
    # declared-length test, and that test is what stands between a damaged
    # image and a confident answer.
    try:
        decode(raw[:o + 8 + (end - o - 8) // 2])
        accepted = True
    except Fail:
        accepted = False
    if accepted:
        print("CONTROL FAILED: the image cut inside its stream still decoded; "
              "nothing read from %s is evidence" % path)
        sys.exit(2)
    return raw, o, end, kstart, plain


def parse_cpio(img):
    """(offset, [(name, mode, data)]) for the first newc archive that parses
    to its TRAILER!!! with at least two entries."""
    start = 0
    while True:
        at = img.find(NEWC, start)
        if at < 0:
            raise Fail("no newc cpio that parses to TRAILER!!! in the kernel image")
        start = at + 1
        try:
            out, p = [], at
            while True:
                h = img[p:p + 110]
                if len(h) < 110 or h[:6] != NEWC:
                    raise ValueError
                f = [int(h[6 + 8 * i:14 + 8 * i], 16) for i in range(13)]
                mode, size, nsz = f[1], f[6], f[11]
                name = img[p + 110:p + 110 + nsz - 1].decode("ascii")
                p = (p + 110 + nsz + 3) & ~3
                data = img[p:p + size]
                p = (p + size + 3) & ~3
                if name == "TRAILER!!!":
                    break
                out.append(("/" + name.lstrip("/") if name != "." else "/", mode, data))
            if len(out) >= 2:
                return at, out
        except (ValueError, UnicodeDecodeError):
            continue


def kind(mode):
    t = stat.S_IFMT(mode)
    return {stat.S_IFREG: "file", stat.S_IFDIR: "dir", stat.S_IFLNK: "slink",
            stat.S_IFCHR: "nod", stat.S_IFBLK: "nod"}.get(t, "other")


def member(entries, path):
    hits = [e for e in entries if e[0] == path and kind(e[1]) == "file"]
    if len(hits) != 1:
        raise Fail("%d regular file(s) named %s in the cpio" % (len(hits), path))
    return hits[0][2]


def abs_source_strings(blob):
    return sorted(set(m.group(1).decode("ascii") for m in
                      re.finditer(rb"(?<![\x21-\x7e])(/[\x21-\x7e]+\.[chS])\x00", blob)))


def banner(img):
    m = re.search(rb"Linux version [\x20-\x7e]+", img)
    return m.group(0).decode("ascii") if m else None


def main(argv):
    ap = argparse.ArgumentParser(prog="relimage.py")
    ap.add_argument("verb", choices=("info", "files", "extract", "srcdir", "paths"))
    ap.add_argument("--image", required=True)
    ap.add_argument("--member")
    ap.add_argument("--out")
    ap.add_argument("--names")
    a = ap.parse_args(argv)
    if a.verb in ("extract", "srcdir") and not a.member:
        ap.error("%s needs --member" % a.verb)
    if a.verb == "extract" and not a.out:
        ap.error("extract needs --out")
    if a.verb == "srcdir" and not a.names:
        ap.error("srcdir needs --names")
    if not os.path.isfile(a.image):
        print("REFUSED: no file %s" % a.image)
        return 3
    try:
        raw, o, end, kstart, img = decode_checked(a.image)
        at, entries = parse_cpio(img)
        if a.verb == "info":
            census = {}
            for e in entries:
                census[kind(e[1])] = census.get(kind(e[1]), 0) + 1
            print("image          %s  %d bytes  sha256 %s" % (a.image, len(raw),
                  hashlib.sha256(raw).hexdigest()))
            print("stream         cvimg header at %d, LZMA stream %d..%d, kernelStartAddr 0x%08X"
                  % (o, o + 8, end, kstart))
            print("vmlinux_img    %d bytes  sha256 %s" % (len(img), hashlib.sha256(img).hexdigest()))
            print("control        the image cut inside its stream: refused")
            print("banner         %s" % banner(img))
            print("cpio           newc at %d: %d entries (%s)" % (at, len(entries), ", ".join(
                "%d %s" % (census[k], k) for k in sorted(census))))
        elif a.verb == "files":
            for name, mode, data in entries:
                if kind(mode) == "file":
                    print("%s\t%d\t%s" % (name, len(data), hashlib.sha256(data).hexdigest()))
        elif a.verb == "extract":
            data = member(entries, a.member)
            with open(a.out + ".tmp", "wb") as fh:
                fh.write(data)
            os.replace(a.out + ".tmp", a.out)
            print("%s\t%d\t%s" % (a.member, len(data), hashlib.sha256(data).hexdigest()))
        elif a.verb == "srcdir":
            names = [n for n in a.names.split(",") if n]
            found = abs_source_strings(member(entries, a.member))
            dirs = set()
            for n in names:
                hit = [s for s in found if s.endswith("/" + n)]
                if len(hit) != 1:
                    raise Fail("%d absolute __FILE__ string(s) end in /%s in %s"
                               % (len(hit), n, a.member))
                dirs.add(hit[0][:-len(n) - 1])
            if len(dirs) != 1:
                raise Fail("the named files were compiled from %d directories, not one"
                           % len(dirs))
            print(dirs.pop())
        elif a.verb == "paths":
            blob = member(entries, a.member) if a.member else img
            for s in abs_source_strings(blob):
                print(s)
    except Fail as e:
        print("NOT FOUND: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
