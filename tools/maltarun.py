#!/usr/bin/env python3
"""maltarun -- `make run`: v1.0's userspace on qemu-system-mips -M malta.

A SIMULATION, NOT A MEASUREMENT.  Nothing this tool prints is a reading of the
device: the CPU is qemu's 24Kf, the kernel is Debian's 4.19, the network card
is qemu's PCnet.  docs/run.md lists every substitution and how it is made, and
`docs/emulation-surface.md` § 8.1 says why an emulator's answer is not the
silicon's.

USAGE
-----
  maltarun.py run     --cache DIR --out DIR [--port N] [--omit brokerd|httpd]
  maltarun.py test    --cache DIR --out DIR [--port N] [--cap S] [--green N]
  maltarun.py probe   [--port N] [--cap S]
  maltarun.py fetch   --cache DIR
  maltarun.py prepare --cache DIR --out DIR
  maltarun.py --self-test

fetch    downloads every row of tools/maltarun-pins.tsv that has a URL into
         --cache, a directory holding nothing else, and refuses a file whose
         size or sha256 differs from its pin.  A file already there is
         re-verified, never trusted.
prepare  cuts v1.0's initramfs out of the release image byte for byte and
         prints its sha256; builds the SECOND cpio (Debian's static busybox,
         mii.ko, pcnet32.ko and tools/maltarun-rdinit.sh, all under /rlxsim/);
         refuses unless the two cpio listings share no path; writes
         initrd.cpio = the cut followed by the second cpio.
run      fetch, prepare, then boots in the foreground: the guest console is
         this terminal (Ctrl-A then X quits qemu) and the web API answers on
         http://127.0.0.1:PORT/.
probe    the host test, once, against a guest already running on PORT.
test     fetch, prepare, then --green boots (default 1) and the two red
         controls -- brokerd left out, httpd left out -- one qemu at a time,
         each in the background with its console in a file.  rc 0 only when
         every green boot PASSES and each control reads RED for its reason.

THE HOST TEST, and what each condition is for
---------------------------------------------
It polls GET /api/status every 0.5 s until --cap seconds have passed since
qemu started -- never a fixed sleep: brokerd's socket appears some time after
httpd starts, and a request in between is answered 503 broker.  It PASSES only
when all three hold:
  S  /api/status answers 200, the body begins {"ok":true and its "version" is
     BK_VERSION_STR as v1.0's src/brokerd/brokerd.h defines it, read with
     `git show v1.0:...` and never typed: httpd writes that string only from
     brokerd's answer, so a stand-in server cannot satisfy S.
  A  /api/config with a well-formed invented rlxs cookie (32 hex digits from
     the host's CSPRNG) answers 401 {"ok":false,"error":"auth"}: brokerd's
     decision that the session is not one it issued.
  N  /api/config with a malformed rlxs cookie (31 hex digits) answers 401
     {"ok":false,"error":"nosession"}: httpd's parser drops a malformed token
     (src/httpd/http.c take_tok32), so this is decided without the broker and
     shows that A's 401 came from a different place.
`test`'s controls: with rlxsim.omit=brokerd, every answer S gets is 503 broker
until the cap, A gets the same and N still holds; with rlxsim.omit=httpd,
nothing answers at all.  Each also needs the loader's and /init's console
lines that show the omission.  The cpio bytes are the same in every run:
tools/maltarun-rdinit.sh deletes the one program from the unpacked root when
the kernel command line asks.

SAFETY
------
v1.0's /init and every guest binary run only inside qemu-system-mips: this
tool never executes a file it extracted, writes every one of them mode 0644,
and refuses to run any emulator but qemu-system-mips (qemu-user would run the
guest's programs against THIS host's kernel and files).  Networking is qemu's
user mode with restrict=on; the only way in is one hostfwd bound to 127.0.0.1
on a port >= 20000.  Downloads are untrusted until their sha256 matches.

WHAT IT DOES NOT ESTABLISH
--------------------------
Anything about the RLX4181 -- its timing, hazards or drivers; any code path the
host test does not reach.  A PASS says v1.0's userspace programs, cut from the
release image, answer these three requests on this emulator.

Exit codes: 0 PASS (or a clean run), 1 RED, 2 refused (a reason, never a
traceback).
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import io
import json
import lzma
import os
import re
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

TOOL_VERSION = "1.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PINS = os.path.join(HERE, "maltarun-pins.tsv")
RDINIT = os.path.join(HERE, "maltarun-rdinit.sh")
PAGE = os.path.join(ROOT, "docs", "run.md")

SIM = "A SIMULATION, NOT A MEASUREMENT"
TAG = "v1.0"
IMAGE_NAME = "mainline-9bb2bec7.img"
KVER = "4.19.0-21-4kc-malta"
KERNEL_MEMBERS = {
    "vmlinux": "boot/vmlinux-" + KVER,
    "mii.ko": "lib/modules/" + KVER + "/kernel/drivers/net/mii.ko",
    "pcnet32.ko": "lib/modules/" + KVER + "/kernel/drivers/net/ethernet/amd/pcnet32.ko",
}
BUSYBOX_MEMBERS = {"busybox": "bin/busybox"}
QEMU = "qemu-system-mips"
GUEST_RAM_MB = 32          # the board's SDRAM, docs/bringup.md MEM-04
GUEST_IP = "10.1.1.1"      # v1.0's lan.ip default, which /init sets on rlx0
OMITS = ("brokerd", "httpd")
PORT_MIN = 20000
POLL_S = 0.5

HEXB = frozenset(b"0123456789abcdefABCDEF")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Refuse(Exception):
    """A refusal: printed as one line with its reason, rc 2."""


def say(msg: str) -> None:
    print("maltarun: " + msg, flush=True)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_file(path: str, data: bytes, mode: int = 0o644) -> None:
    """Build first, write path.tmp, then os.replace -- never a half file."""
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


# --------------------------------------------------------------------- pins

class Pin:
    def __init__(self, name, size, digest, source):
        self.name, self.size, self.digest, self.source = name, size, digest, source

    @property
    def url(self):
        return self.source if self.source.startswith("https://") else None

    @property
    def filename(self):
        return self.source.rsplit("/", 1)[1] if self.url else None


def parse_pins(text: str) -> dict:
    pins = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) != 4:
            raise Refuse(f"pins line {n}: {len(f)} fields, want 4")
        name, size, digest, source = f
        if not size.isdigit():
            raise Refuse(f"pins line {n}: size {size!r} is not a number")
        if digest != "manifest" and not HEX64.match(digest):
            raise Refuse(f"pins line {n}: sha256 {digest!r} is neither 64 hex nor 'manifest'")
        if not (source.startswith("https://") or source.startswith("cut:")):
            raise Refuse(f"pins line {n}: source {source!r} is neither https:// nor cut:")
        if name in pins:
            raise Refuse(f"pins line {n}: {name} twice")
        pins[name] = Pin(name, int(size), digest, source)
    for need in ("manifest", "image", "kernel-deb", "busybox-deb", "v10-cpio"):
        if need not in pins:
            raise Refuse(f"pins: no row {need}")
    return pins


def load_pins() -> dict:
    try:
        with open(PINS, encoding="utf-8") as f:
            return parse_pins(f.read())
    except OSError as e:
        raise Refuse(f"cannot read {PINS}: {e.strerror}")


PIN_PAIR = re.compile(r"([0-9][0-9,]*) bytes, sha256\s+`([0-9a-f]{64})`")
SHA_ANY = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


def page_section(page: str, heading: str) -> str:
    m = re.search(r"^## " + re.escape(heading) + r"[ \t]*\n(.*?)(?=^## |\Z)",
                  page, re.S | re.M)
    return m.group(1) if m else ""


def pin_drift(pins: dict, page: str) -> list:
    """Every disagreement between tools/maltarun-pins.tsv, which owns the pins,
    and docs/run.md, which repeats them, in both directions; [] when they agree.
    The page's pins are the rows of its Prerequisites table (file, bytes,
    sha256) and every 'N bytes, sha256 `X`' it carries -- the v10-cpio value in
    "What it boots"; a 64-hex string anywhere on the page must be a pin too."""
    out, table = [], {}
    for line in page_section(page, "Prerequisites").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or len(cells) != 4 \
                or not re.match(r"^[0-9][0-9,]*$", cells[1]):
            continue                      # prose, the header, the delimiter row
        name = re.search(r"`([^`]+)`", cells[0])
        table[name.group(1) if name else cells[0]] = \
            (int(cells[1].replace(",", "")), cells[2])
    pairs = [(int(n.replace(",", "")), h) for n, h in PIN_PAIR.findall(page)]
    byfile = {p.filename: p for p in pins.values() if p.url}
    owned = {p.digest for p in pins.values() if HEX64.match(p.digest)}
    # page -> tsv: every value the page shows is a row's
    for h in sorted(set(SHA_ANY.findall(page)) - owned):
        out.append(f"page -> tsv: sha256 {h[:12]}... is on the page and in no row")
    for f, (size, cell) in sorted(table.items()):
        p = byfile.get(f)
        if p is None:
            out.append(f"page -> tsv: the table names {f}, which no row pins")
        elif size != p.size:
            out.append(f"page -> tsv: {f} is {size:,} bytes on the page, not the row's")
        elif ("manifest" if p.digest == "manifest" else p.digest) not in cell:
            out.append(f"page -> tsv: {f}'s sha256 cell is not the row's")
    for size, h in pairs:
        if not any(p.size == size and p.digest == h for p in pins.values()):
            out.append(f"page -> tsv: '{size:,} bytes, sha256 {h[:12]}...' is no row's")
    # tsv -> page: every row's values are on the page, where the page shows them
    for p in pins.values():
        if p.url:
            row = table.get(p.filename)
            want = "manifest" if p.digest == "manifest" else p.digest
            if row is None or row[0] != p.size or want not in row[1]:
                out.append(f"tsv -> page: {p.name}'s {p.size:,} bytes and sha256 "
                           f"{want[:12]} are not a Prerequisites row")
        elif (p.size, p.digest) not in pairs:
            out.append(f"tsv -> page: {p.name}'s '{p.size:,} bytes, sha256 "
                       f"{p.digest[:12]}...' is not on the page")
    return out


def parse_manifest(text: str) -> dict:
    """SHA256SUMS: '<64 hex>  <name>' per line -> {name: digest}."""
    out = {}
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^([0-9a-f]{64})  (\S+)$", line)
        if not m:
            raise Refuse(f"manifest line {n} is not '<sha256>  <name>'")
        if m.group(2) in out:
            raise Refuse(f"manifest names {m.group(2)} twice")
        out[m.group(2)] = m.group(1)
    return out


# -------------------------------------------------------------- git reads

def git_show(spec: str) -> str:
    p = subprocess.run(["git", "-C", ROOT, "show", spec], capture_output=True)
    if p.returncode != 0:
        raise Refuse(f"git show {spec} failed -- a clone needs the tag {TAG} "
                     "(git fetch --tags)")
    return p.stdout.decode("utf-8")


def parse_bk_version(header: str) -> str:
    hits = re.findall(r'^#define[ \t]+BK_VERSION_STR[ \t]+"([^"\\\n]+)"[ \t]*$',
                      header, re.M)
    if len(hits) != 1:
        raise Refuse(f"BK_VERSION_STR: {len(hits)} definitions in brokerd.h, want 1")
    return hits[0]


def bk_version() -> str:
    return parse_bk_version(git_show(f"{TAG}:src/brokerd/brokerd.h"))


def git_ignored(path: str) -> bool | None:
    """True/False for a path inside the clone, None outside it."""
    ap = os.path.abspath(path)
    if os.path.commonpath([ap, ROOT]) != ROOT:
        return None
    p = subprocess.run(["git", "-C", ROOT, "check-ignore", "-q", ap],
                       capture_output=True)
    if p.returncode not in (0, 1):
        raise Refuse(f"git check-ignore {ap}: rc {p.returncode}")
    return p.returncode == 0


def need_ignored(path: str, what: str) -> None:
    if git_ignored(path) is False:
        raise Refuse(f"{what} {path} is inside the clone and not ignored by git; "
                     "give a path under build/ or outside the clone")


# ------------------------------------------------------------------- fetch

def fetch(cache: str, pins: dict) -> dict:
    """-> {pin name: path}.  Every file re-verified before it is returned."""
    need_ignored(cache, "--cache")
    os.makedirs(cache, exist_ok=True)
    expected = {p.filename: p for p in pins.values() if p.url}
    for e in os.listdir(cache):
        if e.startswith(".part-"):
            os.remove(os.path.join(cache, e))
        elif e not in expected:
            raise Refuse(f"the cache {cache} holds {e}, which this tool did not put "
                         "there: give an empty or a maltarun-only directory")
    manifest = None
    paths = {}
    for p in [pins["manifest"], pins["image"], pins["kernel-deb"], pins["busybox-deb"]]:
        if p.digest == "manifest":
            if manifest is None:
                raise Refuse("the manifest must be verified before the image")
            want = manifest.get(p.filename)
            if want is None:
                raise Refuse(f"the release manifest has no line for {p.filename}")
        else:
            want = p.digest
        dst = os.path.join(cache, p.filename)
        if not os.path.exists(dst):
            download(p.url, dst, os.path.join(cache, ".part-" + p.filename))
        data = open(dst, "rb").read()
        got = sha256(data)
        if len(data) != p.size or got != want:
            raise Refuse(f"{dst}: {len(data)} bytes, sha256 {got}; the pin is "
                         f"{p.size} bytes, {want} -- delete it and fetch again")
        say(f"verified {p.filename}: {len(data):,} bytes, sha256 {got}")
        if p.name == "manifest":
            manifest = parse_manifest(data.decode("ascii"))
        paths[p.name] = dst
    # A second source for the image: the digest committed at the tag.
    if manifest[pins["image"].filename] not in git_show(f"{TAG}:CHANGELOG.md"):
        raise Refuse(f"{TAG}:CHANGELOG.md does not carry the manifest's digest of "
                     f"{pins['image'].filename}")
    say(f"the image's digest is the manifest's line and the one {TAG}:CHANGELOG.md carries")
    return paths


def download(url: str, dst: str, part: str) -> None:
    say(f"fetching {url}")
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(part, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
        if os.path.exists(part):
            os.remove(part)
        raise Refuse(f"download of {url} failed: {e!r}")
    os.replace(part, dst)


# ---------------------------------------------------------------- newc cpio

S_IFMT, S_IFDIR, S_IFREG, S_IFLNK = 0o170000, 0o040000, 0o100000, 0o120000
KIND = {0o040000: "dir", 0o100000: "file", 0o120000: "slink",
        0o020000: "chr", 0o060000: "blk", 0o010000: "fifo", 0o140000: "sock"}


def newc_parse(buf: bytes, start: int = 0):
    """-> ([(name, mode, data)], end), end being the offset after the
    TRAILER!!! record.  Refuses anything that is not well-formed newc."""
    p, out = start, []
    while True:
        h = buf[p:p + 110]
        if len(h) < 110 or h[:6] != b"070701" or not all(c in HEXB for c in h[6:]):
            raise Refuse(f"cpio: no newc header at offset {p}")
        f = [int(h[6 + 8 * i:14 + 8 * i], 16) for i in range(13)]
        mode, filesize, namesize = f[1], f[6], f[11]
        ns = p + 110
        raw = buf[ns:ns + namesize]
        if namesize < 1 or len(raw) != namesize or raw[-1] != 0:
            raise Refuse(f"cpio: bad name at offset {p}")
        try:
            name = raw[:-1].decode("utf-8")
        except UnicodeDecodeError:
            raise Refuse(f"cpio: name at offset {p} is not UTF-8")
        ds = (ns + namesize + 3) & ~3
        if ds + filesize > len(buf):
            raise Refuse(f"cpio: {name} runs past the end")
        data = buf[ds:ds + filesize]
        p = (ds + filesize + 3) & ~3
        if name == "TRAILER!!!":
            return out, p
        out.append((name, mode, data))


def newc_record(ino: int, name: str, mode: int, data: bytes) -> bytes:
    nb = name.encode("utf-8") + b"\0"
    nlink = 2 if (mode & S_IFMT) == S_IFDIR else 1
    fields = (ino, mode, 0, 0, nlink, 0, len(data), 0, 0, 0, 0, len(nb), 0)
    rec = b"070701" + "".join("%08X" % v for v in fields).encode() + nb
    rec += b"\0" * (-len(rec) % 4) + data
    return rec + b"\0" * (-len(rec) % 4)


def newc_build(entries) -> bytes:
    """entries: [(name, mode, data)] -> a newc archive padded to 512, as
    gen_init_cpio pads one."""
    buf = b"".join(newc_record(0x7100 + i, n, m, d)
                   for i, (n, m, d) in enumerate(entries))
    buf += newc_record(0, "TRAILER!!!", 0, b"")
    return buf + b"\0" * (-len(buf) % 512)


def norm(name: str) -> str:
    while name.startswith("./"):
        name = name[2:]
    return name.strip("/")


def listing(entries) -> str:
    rows = []
    for name, mode, data in entries:
        k = KIND.get(mode & S_IFMT, "?")
        extra = (f"{len(data)}\t{sha256(data)}" if k == "file" else
                 f"-> {data.decode('utf-8', 'replace')}" if k == "slink" else "")
        rows.append(f"{k}\t/{norm(name)}\t{mode & 0o7777:o}\t{extra}".rstrip("\t"))
    return "\n".join(rows) + "\n"


def overlap(base, added) -> list:
    """Paths the added archive names that the base archive already holds --
    each one would be replaced (a file) or re-moded (a directory)."""
    have = {norm(n) for n, _m, _d in base}
    return sorted(norm(n) for n, _m, _d in added if norm(n) in have)


# ------------------------------------------------------------------ the cut

def find_lzma(img: bytes):
    for off in range(0, min(len(img), 1 << 16)):
        if img[off] != 0x5D or off + 13 > len(img):
            continue
        dic = struct.unpack_from("<I", img, off + 1)[0]
        if dic == 0 or dic & (dic - 1) or dic > (1 << 26):
            continue
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        try:
            out = d.decompress(img[off:])
        except lzma.LZMAError:
            continue
        if d.eof and len(out) > 1_000_000:
            return off, out
    raise Refuse("no complete LZMA stream of more than 1 MB starts in the "
                 "image's first 64 KiB")


def cut_initramfs(img: bytes):
    """-> (cut bytes, entries, facts).  The cut runs from the first newc
    header that parses to a TRAILER!!! record, through that record, then
    through the zero bytes to the next 512-byte boundary: gen_init_cpio's own
    padding (linux-2.6.30/usr/gen_init_cpio.c, cpio_trailer)."""
    off, dec = find_lzma(img)
    start = None
    for m in re.finditer(rb"070701", dec):
        i = m.start()
        if i % 4 or not all(c in HEXB for c in dec[i + 6:i + 110]):
            continue
        try:
            entries, end = newc_parse(dec, i)
        except Refuse:
            continue
        start = i
        break
    if start is None:
        raise Refuse("no newc archive in the decoded image")
    end512 = start + -(-(end - start) // 512) * 512
    if end512 > len(dec) or dec[end:end512] != bytes(end512 - end):
        raise Refuse(f"the {end512 - end} bytes after the trailer are not zero padding")
    facts = {"lzma_offset": off, "decoded": len(dec), "start": start,
             "trailer_end": end, "end": end512, "entries": len(entries),
             "at_stream_end": end512 == len(dec)}
    return dec[start:end512], entries, facts


# -------------------------------------------------------------- .deb reads

def ar_members(blob: bytes) -> dict:
    if blob[:8] != b"!<arch>\n":
        raise Refuse("not an ar archive (.deb)")
    p, out = 8, {}
    while p + 60 <= len(blob):
        h = blob[p:p + 60]
        if h[58:60] != b"`\n":
            raise Refuse(f"ar: bad member header at {p}")
        name = h[:16].decode("ascii", "replace").strip().rstrip("/")
        field = h[48:58].decode("ascii", "replace").strip()
        if not field.isdigit():
            raise Refuse(f"ar: bad member size at {p}")
        size = int(field)
        out[name] = blob[p + 60:p + 60 + size]
        p += 60 + size + (size & 1)
    return out


def deb_members(path: str, wanted: dict) -> dict:
    """{key: member path} -> {key: bytes}, regular files only, read from
    data.tar.xz in memory: nothing from the archive is written by tarfile."""
    ar = ar_members(open(path, "rb").read())
    if "data.tar.xz" not in ar:
        raise Refuse(f"{path}: no data.tar.xz (members: {', '.join(sorted(ar))})")
    byname = {v: k for k, v in wanted.items()}
    got = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(ar["data.tar.xz"]), mode="r|xz") as tf:
            for m in tf:
                n = norm(m.name)
                if n in byname:
                    if not m.isreg():
                        raise Refuse(f"{path}: {n} is not a regular file")
                    got[byname[n]] = tf.extractfile(m).read()
    except (tarfile.TarError, lzma.LZMAError, EOFError) as e:
        raise Refuse(f"{path}: data.tar.xz cannot be read: {e!r}")
    missing = sorted(set(wanted) - set(got))
    if missing:
        raise Refuse(f"{path}: no member {', '.join(wanted[k] for k in missing)}")
    return got


# ----------------------------------------------------------------- prepare

def prepare(cache: str, out: str, pins: dict) -> dict:
    paths = fetch(cache, pins)
    need_ignored(out, "--out")
    if "," in os.path.abspath(out):
        raise Refuse("--out may not contain a comma (qemu's option syntax)")
    gdir = os.path.join(out, "guest")
    os.makedirs(gdir, exist_ok=True)

    img = open(paths["image"], "rb").read()
    cut, v10, facts = cut_initramfs(img)
    pc = pins["v10-cpio"]
    if len(cut) != pc.size or sha256(cut) != pc.digest:
        raise Refuse(f"the cut is {len(cut)} bytes, sha256 {sha256(cut)}; the pin is "
                     f"{pc.size} bytes, {pc.digest}")
    say(f"v1.0 initramfs: {len(cut):,} bytes, sha256 {sha256(cut)}, cut byte for byte "
        f"from {IMAGE_NAME} (LZMA stream at {facts['lzma_offset']}, decoded "
        f"{facts['decoded']:,} bytes; newc archive at decoded {facts['start']}, "
        f"{facts['entries']} entries, trailer ends at {facts['trailer_end']}, zero "
        f"padding to {facts['end']}{', the end of the stream' if facts['at_stream_end'] else ''})")

    k = deb_members(paths["kernel-deb"], KERNEL_MEMBERS)
    b = deb_members(paths["busybox-deb"], BUSYBOX_MEMBERS)
    try:
        rdinit = open(RDINIT, "rb").read()
    except OSError as e:
        raise Refuse(f"cannot read {RDINIT}: {e.strerror}")
    for key, data in list(k.items()) + list(b.items()):
        # 0644 on the host: nothing extracted here is ever executed here.
        write_file(os.path.join(gdir, key), data, 0o644)
        say(f"guest {key}: {len(data):,} bytes, sha256 {sha256(data)}")
    say(f"guest load (tools/maltarun-rdinit.sh): {len(rdinit):,} bytes, sha256 {sha256(rdinit)}")

    added = [("rlxsim", S_IFDIR | 0o755, b""),
             ("rlxsim/busybox", S_IFREG | 0o755, b["busybox"]),
             ("rlxsim/load", S_IFREG | 0o755, rdinit),
             ("rlxsim/mii.ko", S_IFREG | 0o644, k["mii.ko"]),
             ("rlxsim/pcnet32.ko", S_IFREG | 0o644, k["pcnet32.ko"])]
    second = newc_build(added)
    reread, _end = newc_parse(second)
    if [(n, m, d) for n, m, d in reread] != added:
        raise Refuse("the second cpio does not read back as written")
    both = overlap(v10, added)
    if both:
        raise Refuse("the second cpio would replace v1.0 paths: " + ", ".join(both))
    write_file(os.path.join(out, "v10-cpio.list"), listing(v10).encode())
    write_file(os.path.join(out, "rlxsim-cpio.list"), listing(added).encode())
    say(f"second cpio: {len(second):,} bytes, sha256 {sha256(second)}, {len(added)} "
        f"paths, all under /rlxsim/; paths in both listings: 0 (v1.0 {len(v10)}, "
        f"added {len(added)}; out/v10-cpio.list, out/rlxsim-cpio.list)")
    initrd = cut + second
    write_file(os.path.join(out, "v10-initramfs.cpio"), cut)
    write_file(os.path.join(out, "initrd.cpio"), initrd)
    say(f"initrd.cpio: {len(initrd):,} bytes, sha256 {sha256(initrd)} = the v1.0 cut, "
        "then the second cpio")
    return {"vmlinux": os.path.join(gdir, "vmlinux"),
            "initrd": os.path.join(out, "initrd.cpio"),
            "cut_sha256": sha256(cut)}


# -------------------------------------------------------------------- boot

def qemu_path() -> str:
    q = shutil.which(QEMU)
    if q is None:
        raise Refuse(f"{QEMU} is not installed (Ubuntu 24.04: apt-get install qemu-system-mips)")
    if os.path.basename(q) != QEMU:
        raise Refuse(f"{q} is not {QEMU}")
    return q


def check_port(port: int) -> None:
    """Nothing may listen on the port before qemu does, or the host test
    would read that listener.  A connect must be refused, and a bind with
    SO_REUSEADDR -- as qemu binds its hostfwd, so the TIME_WAIT sockets of a
    previous run do not count -- must succeed."""
    if not PORT_MIN <= port <= 65535:
        raise Refuse(f"--port {port}: give {PORT_MIN}..65535")
    busy = f"127.0.0.1:{port} is already in use; nothing may listen there " \
           "before the guest does, or the host test would read it"
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2.0):
            raise Refuse(busy)
    except OSError:
        pass
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
    except OSError:
        raise Refuse(busy)
    finally:
        s.close()


def qemu_argv(q: str, art: dict, port: int, omit, console) -> list:
    if omit is not None and omit not in OMITS:
        raise Refuse(f"--omit {omit}: give one of {', '.join(OMITS)}")
    # nokaslr: Debian's kernel moves itself by up to 16 MiB at random
    # (CONFIG_RANDOMIZE_BASE_MAX_OFFSET); in 32 MiB one boot without it printed
    # nothing at all.  rlxfw's own kernel has no such relocation.
    append = "console=ttyS0 nokaslr rdinit=/rlxsim/load"
    if omit:
        append += f" rlxsim.omit={omit}"
    nic = ("user,model=pcnet,restrict=on,net=10.1.1.0/24,host=10.1.1.2,"
           f"hostfwd=tcp:127.0.0.1:{port}-{GUEST_IP}:80")
    argv = [q, "-M", "malta", "-cpu", "24Kf", "-m", str(GUEST_RAM_MB), "-no-reboot",
            "-kernel", art["vmlinux"], "-initrd", art["initrd"], "-append", append,
            "-nic", nic]
    if console is None:
        argv += ["-nographic"]
    else:
        argv += ["-display", "none", "-monitor", "none", "-serial", "file:" + console]
    return argv


# -------------------------------------------------------------- host test

def http_get(port: int, path: str, cookie, timeout: float) -> bytes:
    """The raw answer, b'' for none: refused, reset, timed out, or closed
    with no byte -- qemu accepts on the host side and closes when nothing in
    the guest listens."""
    req = f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n"
    if cookie:
        req += f"Cookie: {cookie}\r\n"
    chunks = []
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
            s.sendall((req + "\r\n").encode("ascii"))
            while True:
                c = s.recv(65536)
                if not c:
                    break
                chunks.append(c)
    except OSError:
        pass
    return b"".join(chunks)


def parse_answer(raw: bytes):
    """-> None for no answer, else (status line, code, body bytes)."""
    if not raw:
        return None
    head, _sep, body = raw.partition(b"\r\n\r\n")
    line = head.split(b"\r\n", 1)[0].decode("latin-1")
    m = re.match(r"^HTTP/1\.[01] (\d{3})(?: |$)", line)
    return (line, int(m.group(1)) if m else 0, body)


def show(ans) -> str:
    if ans is None:
        return "no answer"
    line, _c, body = ans
    return f"{line} | {body.decode('utf-8', 'backslashreplace')}"


def json_body(ans):
    try:
        return json.loads(ans[2].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def judge_status(ans, bk: str) -> bool:
    if ans is None or ans[1] != 200 or not ans[2].startswith(b'{"ok":true'):
        return False
    j = json_body(ans)
    return isinstance(j, dict) and j.get("ok") is True and j.get("version") == bk


def judge_error(ans, code: int, err: str) -> bool:
    return (ans is not None and ans[1] == code
            and json_body(ans) == {"ok": False, "error": err})


def host_test(port: int, cap: float, bk: str, t0: float, alive=None) -> dict:
    """Poll until S holds or the cap passes; then A and N.  `alive` is a
    callable answering whether qemu still runs."""
    r = {"attempts": 0, "status": None, "ready_s": None, "answered": False,
         "exited": False, "seen": {}, "answers": []}
    while True:
        now = time.monotonic()
        if now - t0 >= cap:
            break
        if alive is not None and not alive():
            r["exited"] = True
            break
        r["attempts"] += 1
        ans = parse_answer(http_get(port, "/api/status", None,
                                    min(5.0, max(0.5, cap - (now - t0)))))
        r["status"] = ans
        r["answered"] |= ans is not None
        r["seen"][show(ans)] = r["seen"].get(show(ans), 0) + 1
        if ans is not None:
            r["answers"].append(ans)
        if judge_status(ans, bk):
            r["ready_s"] = time.monotonic() - t0
            break
        time.sleep(POLL_S)
    good = "rlxs=" + secrets.token_hex(16)
    bad = "rlxs=" + secrets.token_hex(16)[:31]
    r["config"] = parse_answer(http_get(port, "/api/config", good, 5.0))
    r["malformed"] = parse_answer(http_get(port, "/api/config", bad, 5.0))
    r["answered"] |= r["config"] is not None or r["malformed"] is not None
    r["S"] = r["ready_s"] is not None
    r["A"] = judge_error(r["config"], 401, "auth")
    r["N"] = judge_error(r["malformed"], 401, "nosession")
    r["verdict"] = "PASS" if (r["S"] and r["A"] and r["N"]) else "RED"
    return r


def report(r: dict, bk: str, cap: float) -> None:
    when = (f"ready at {r['ready_s']:.1f} s after qemu started" if r["S"] else
            "qemu exited" if r["exited"] else f"not ready within the {cap:.0f} s cap")
    print(f"  S  GET /api/status, {r['attempts']} attempts, {when}:", flush=True)
    for text, n in r["seen"].items():
        print(f"       {n:>4} x  {text}")
    print(f"       200, body begins {{\"ok\":true, version {bk!r}: {'yes' if r['S'] else 'NO'}")
    print(f"  A  GET /api/config, rlxs = 32 invented hex digits: {show(r['config'])}")
    print(f"       401 auth: {'yes' if r['A'] else 'NO'}")
    print(f"  N  GET /api/config, rlxs = 31 hex digits (malformed): {show(r['malformed'])}")
    print(f"       401 nosession: {'yes' if r['N'] else 'NO'}")
    print(f"  host test: {r['verdict']}  ({SIM})", flush=True)


# ------------------------------------------------------------ console facts

CONSOLE_KEYS = ("Linux version", "rlxsim:", "rlxfw: init running", "SIOCSIF",
                "rlxfw: lan up", "entropy_avail", "started pid=", "NOT STARTED",
                "missing:", "GIVEN UP", "Kernel panic")


def console_facts(path: str) -> list:
    """The lines worth printing.  The controls below read only lines that one
    write() puts on the console before or without a child running beside it --
    the loader's, and /init's own (src/init/main.c lb_out) -- because the
    children's lines interleave (dnsfwd writes its message in pieces)."""
    try:
        text = open(path, "rb").read().decode("utf-8", "replace").replace("\r", "")
    except OSError:
        return ["(no console capture)"]
    out = [ln for ln in text.split("\n") if any(k in ln for k in CONSOLE_KEYS)]
    out.append(f"lines carrying RLXFW-ID0: {text.count('RLXFW-ID0')}")
    return out


# ------------------------------------------------------------------- runs

def one_boot(q, art, port, cap, bk, omit, rdir) -> dict:
    os.makedirs(rdir, exist_ok=True)
    console = os.path.join(rdir, "console.txt")
    for f in (console,):
        if os.path.exists(f):
            os.remove(f)
    check_port(port)
    argv = qemu_argv(q, art, port, omit, console)
    write_file(os.path.join(rdir, "qemu.argv"), ("\n".join(argv) + "\n").encode())
    say(f"boot{' with ' + omit + ' left out' if omit else ''}: {' '.join(argv)}")
    err = open(os.path.join(rdir, "qemu.stderr"), "wb")
    t0 = time.monotonic()
    p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=err, stderr=err)
    try:
        r = host_test(port, cap, bk, t0, alive=lambda: p.poll() is None)
    finally:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(15)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        err.close()
    r["qemu_rc"] = p.returncode
    r["console"] = console_facts(console)
    return r


def expectation(kind: str, r: dict):
    """-> (met, reason) for one boot of `test`."""
    lines = r["console"]

    def has(s):
        return any(s in ln for ln in lines)
    if kind == "green":
        return r["verdict"] == "PASS", "PASS"
    if kind == "brokerd":
        # Every answer S got is 503 broker; A gets the same; N still holds,
        # which is the reading that N is decided without the broker.
        ok = (r["verdict"] == "RED" and r["answers"]
              and all(judge_error(x, 503, "broker") for x in r["answers"])
              and judge_error(r["config"], 503, "broker") and r["N"]
              and has("rlxsim: left out /usr/sbin/brokerd")
              and has("missing: /usr/sbin/brokerd") and has("httpd started pid="))
        return bool(ok), "RED: 503 broker, N holds; console: brokerd out, httpd up"
    ok = (r["verdict"] == "RED" and not r["answered"]
          and has("rlxsim: left out /usr/sbin/httpd")
          and has("missing: /usr/sbin/httpd") and has("brokerd started pid="))
    return ok, "RED: no answer at all; console: httpd out, brokerd up"


def cmd_test(a) -> int:
    pins = load_pins()
    bk = bk_version()
    say(f"{SIM}.  BK_VERSION_STR at {TAG}: {bk!r} (git show {TAG}:src/brokerd/brokerd.h)")
    q = qemu_path()
    art = prepare(a.cache, a.out, pins)
    plan = [("green", None)] * a.green + [("brokerd", "brokerd"), ("httpd", "httpd")]
    rows = []
    for i, (kind, omit) in enumerate(plan, 1):
        label = f"{i}-{'green' if kind == 'green' else 'no-' + kind}"
        say(f"--- run {label} ---")
        r = one_boot(q, art, a.port, a.cap, bk, omit, os.path.join(a.out, "runs", label))
        report(r, bk, a.cap)
        for ln in r["console"]:
            print(f"  console: {ln}")
        met, want = expectation(kind, r)
        rows.append((label, want, r, met))
    print()
    say(f"summary ({SIM}):")
    for label, want, r, met in rows:
        t = f"{r['ready_s']:.1f} s" if r["ready_s"] is not None else "-"
        print(f"  {label:<12} expected {want:<64} got {r['verdict']:<4} ready {t:<8} "
              f"{'met' if met else 'NOT MET'}")
    allmet = all(m for *_x, m in rows)
    say("test: PASS -- every green boot passed and both controls read red for their "
        "reason" if allmet else "test: RED -- an expectation above was not met")
    return 0 if allmet else 1


def cmd_run(a) -> int:
    say(f"{SIM}: v1.0's userspace, cut from the release image, on {QEMU} -M malta "
        "-cpu 24Kf with Debian's 4.19 kernel -- docs/run.md says what differs from the device")
    pins = load_pins()
    q = qemu_path()
    art = prepare(a.cache, a.out, pins)
    check_port(a.port)
    argv = qemu_argv(q, art, a.port, a.omit, None)
    say(f"{SIM}.  Nothing printed below is a reading of the device.")
    say(f"v1.0 initramfs sha256 {art['cut_sha256']}")
    say(f"web API: http://127.0.0.1:{a.port}/  (host test: tools/maltarun.py probe --port {a.port})")
    say("quit qemu with Ctrl-A then X")
    say(" ".join(argv))
    return subprocess.run(argv).returncode


def cmd_probe(a) -> int:
    bk = bk_version()
    say(f"{SIM}.  host test against 127.0.0.1:{a.port}, cap {a.cap:.0f} s")
    r = host_test(a.port, a.cap, bk, time.monotonic())
    report(r, bk, a.cap)
    return 0 if r["verdict"] == "PASS" else 1


def cmd_fetch(a) -> int:
    fetch(a.cache, load_pins())
    return 0


def cmd_prepare(a) -> int:
    prepare(a.cache, a.out, load_pins())
    return 0


# --------------------------------------------------------------- self-test

def self_test() -> int:
    results = []

    def case(cid, title, ok):
        results.append(ok)
        print(f"  {'ok' if ok else 'FAIL'}  {cid:<4} {title}")

    def refuses(fn, *args):
        try:
            fn(*args)
        except Refuse:
            return True
        return False

    ents = [("d", S_IFDIR | 0o755, b""), ("d/f", S_IFREG | 0o644, b"abc"),
            ("d/l", S_IFLNK | 0o777, b"f")]
    arc = newc_build(ents)
    back, end = newc_parse(arc)
    case("C1", "a newc archive reads back entry for entry",
         back == ents and len(arc) % 512 == 0 and arc[end:] == bytes(len(arc) - end))
    case("C2", "a truncated archive is refused", refuses(newc_parse, arc[:150]))
    # v1.0's archive stores its names with a leading '/' (gen_init_cpio), the
    # second one without; the kernel unpacks both relative to the root.
    base = [("/init", S_IFREG | 0o755, b"x"), ("/bin", S_IFDIR | 0o755, b"")]
    case("C3", "overlap finds a replaced file and a re-moded directory, however spelled",
         overlap(base, [("./init", S_IFREG, b""), ("bin/", S_IFDIR, b""),
                        ("rlxsim", S_IFDIR, b"")]) == ["bin", "init"]
         and overlap([("init", S_IFREG, b"x")], [("/init", S_IFREG, b"")]) == ["init"])
    case("C4", "overlap is empty for paths only under rlxsim/",
         overlap(base, [("rlxsim", S_IFDIR, b""), ("rlxsim/x", S_IFREG, b"")]) == [])
    hdr = '#define X 1\n#define BK_VERSION_STR "rlxfw-brokerd-1"\n'
    case("C5", "BK_VERSION_STR is read from the header text",
         parse_bk_version(hdr) == "rlxfw-brokerd-1")
    case("C6", "a header without it, or with two, is refused",
         refuses(parse_bk_version, "#define Y 2\n")
         and refuses(parse_bk_version, hdr + hdr))
    ok200 = b'HTTP/1.1 200 OK\r\nContent-Length: 9\r\n\r\n{"ok":true,"uptime_s":3,"version":"rlxfw-brokerd-1"}'
    stand = b'HTTP/1.1 200 OK\r\n\r\n{"ok":true}'
    other = b'HTTP/1.1 200 OK\r\n\r\n{"ok":true,"version":"something-else"}'
    late = b'HTTP/1.1 200 OK\r\n\r\n{"version":"rlxfw-brokerd-1","ok":true}'
    b503 = b'HTTP/1.1 503 Service Unavailable\r\n\r\n{"ok":false,"error":"broker"}'
    a401 = b'HTTP/1.1 401 Unauthorized\r\n\r\n{"ok":false,"error":"auth"}'
    bk = "rlxfw-brokerd-1"
    case("C7", "S holds for 200 with the prefix and the version",
         judge_status(parse_answer(ok200), bk))
    case("C8", "S fails for a stand-in: no version, another version, another order",
         not judge_status(parse_answer(stand), bk)
         and not judge_status(parse_answer(other), bk)
         and not judge_status(parse_answer(late), bk))
    case("C9", "S fails for 503 broker and for no answer",
         not judge_status(parse_answer(b503), bk) and not judge_status(parse_answer(b""), bk))
    case("C10", "A holds for 401 auth and not for 503 broker or 401 nosession",
         judge_error(parse_answer(a401), 401, "auth")
         and not judge_error(parse_answer(b503), 401, "auth")
         and not judge_error(parse_answer(a401.replace(b'"auth"', b'"nosession"')), 401, "auth"))
    good = "a" * 64
    pins_ok = (f"manifest\t10\t{good}\thttps://x/SHA256SUMS\n"
               "image\t5\tmanifest\thttps://x/i.img\n"
               f"kernel-deb\t1\t{good}\thttps://x/k.deb\n"
               f"busybox-deb\t1\t{good}\thttps://x/b.deb\n"
               f"v10-cpio\t1\t{good}\tcut:image\n")
    case("C11", "a pins table parses; a short digest and a missing row are refused",
         len(parse_pins(pins_ok)) == 5
         and refuses(parse_pins, pins_ok.replace(good, good[:63], 1))
         and refuses(parse_pins, pins_ok.replace("kernel-deb", "#kernel-deb")))
    man = f"{good}  T.rlxu\n{'b' * 64}  {IMAGE_NAME}\n"
    case("C12", "the manifest maps names to digests; a bad line is refused",
         parse_manifest(man)[IMAGE_NAME] == "b" * 64
         and refuses(parse_manifest, man + "zz  x\n"))
    payload = newc_build([("init", S_IFREG | 0o755, b"\x7fELF" + bytes(2_000_000))])
    stream = lzma.compress(b"\0" * 4096 + payload, format=lzma.FORMAT_ALONE)
    img = b"cvimg" + bytes(11) + stream + b"\xff" * 64
    try:
        cut, cents, facts = cut_initramfs(img)
        c13 = cut == payload and facts["entries"] == 1 and facts["start"] == 4096
    except Refuse:
        c13 = False
    case("C13", "the cut recovers a padded archive byte for byte from an LZMA image", c13)
    flipped = bytearray(img)
    flipped[16 + len(stream) // 2] ^= 0x01
    case("C14", "one flipped bit in the stream is refused, not cut",
         refuses(cut_initramfs, bytes(flipped)))
    case("C15", "--omit takes brokerd or httpd and nothing else",
         refuses(qemu_argv, "q", {"vmlinux": "v", "initrd": "i"}, 20080, "cfgstore", None)
         and "rlxsim.omit=httpd" in " ".join(
             qemu_argv("q", {"vmlinux": "v", "initrd": "i"}, 20080, "httpd", None)))
    argv = qemu_argv("q", {"vmlinux": "v", "initrd": "i"}, 20080, None, None)
    nic = argv[argv.index("-nic") + 1]
    case("C16", "user-mode networking, restricted, one hostfwd on 127.0.0.1",
         nic.startswith("user,") and "restrict=on" in nic
         and nic.count("hostfwd=") == 1 and "hostfwd=tcp:127.0.0.1:20080-" in nic)
    case("C17", "a port below 20000 is refused", refuses(check_port, 8080))
    try:
        drift = pin_drift(load_pins(), open(PAGE, encoding="utf-8").read())
    except (Refuse, OSError) as e:
        drift = [f"unreadable: {e}"]
    case("C18", "docs/run.md shows exactly the pins tools/maltarun-pins.tsv owns, "
         "both ways" + ("" if not drift else " -- " + "; ".join(drift)), not drift)
    fx_pins = parse_pins(
        f"manifest\t10\t{'a' * 64}\thttps://x/SHA256SUMS\n"
        "image\t20\tmanifest\thttps://x/i.img\n"
        f"kernel-deb\t1000\t{'b' * 64}\thttps://x/k.deb\n"
        f"busybox-deb\t30\t{'c' * 64}\thttps://x/b.deb\n"
        f"v10-cpio\t4096\t{'d' * 64}\tcut:image\n")
    fx_page = ("## Prerequisites\n\n| file | bytes | sha256 | from |\n|---|---:|---|---|\n"
               f"| `SHA256SUMS` | 10 | `{'a' * 64}` | r |\n"
               "| `i.img` | 20 | the manifest's line | r |\n"
               f"| `k.deb` | 1,000 | `{'b' * 64}` | d |\n"
               f"| `b.deb` | 30 | `{'c' * 64}` | d |\n\n"
               f"## What it boots\n\nthe cut: 4,096 bytes, sha256\n   `{'d' * 64}`, pinned.\n")
    stray = fx_page + f"\nand 12 bytes, sha256 `{'e' * 64}`\n"
    lost = fx_page.replace(f"| `b.deb` | 30 | `{'c' * 64}` | d |\n", "")
    moved = fx_page.replace("4,096 bytes", "4,097 bytes")
    case("C23", "the drift check passes a matched pair and reads each direction: a page "
         "value no row owns, a row the page lacks, a moved byte count",
         pin_drift(fx_pins, fx_page) == []
         and [d[:12] for d in pin_drift(fx_pins, stray)] == ["page -> tsv:"] * 2
         and [d[:12] for d in pin_drift(fx_pins, lost)] == ["tsv -> page:"]
         and any(d.startswith("tsv -> page: v10-cpio") for d in pin_drift(fx_pins, moved))
         and any(d.startswith("page -> tsv: '4,097") for d in pin_drift(fx_pins, moved)))
    with tempfile.TemporaryDirectory() as d:
        deb = os.path.join(d, "t.deb")
        tbuf = io.BytesIO()
        with tarfile.open(fileobj=tbuf, mode="w:xz") as tf:
            ti = tarfile.TarInfo("./bin/busybox")
            ti.size = 3
            tf.addfile(ti, io.BytesIO(b"bbx"))
            tl = tarfile.TarInfo("./bin/sh")
            tl.type = tarfile.SYMTYPE
            tl.linkname = "busybox"
            tf.addfile(tl)
        data = tbuf.getvalue()

        def arm(name, blob):
            h = f"{name:<16}{0:<12}{0:<6}{0:<6}{100644:<8}{len(blob):<10}".encode() + b"`\n"
            return h + blob + (b"\n" if len(blob) & 1 else b"")
        open(deb, "wb").write(b"!<arch>\n" + arm("debian-binary", b"2.0\n")
                              + arm("data.tar.xz", data))
        c19 = (deb_members(deb, {"busybox": "bin/busybox"}) == {"busybox": b"bbx"}
               and refuses(deb_members, deb, {"sh": "bin/sh"}))
    case("C19", "a .deb member is read in memory; a symlink member is refused", c19)
    b_r = {"verdict": "RED", "answers": [parse_answer(b503)], "config": parse_answer(b503),
           "N": True, "answered": True,
           "console": ["rlxsim: left out /usr/sbin/brokerd (rlxsim.omit=brokerd)",
                       "rlxfw: init:   missing: /usr/sbin/brokerd",
                       "rlxfw: init: httpd started pid=70"]}
    case("C20", "the brokerd control is met by 503 broker only: not after a 200, "
         "not without its console line",
         expectation("brokerd", b_r)[0]
         and not expectation("brokerd", dict(b_r, answers=[parse_answer(b503),
                                                           parse_answer(ok200)]))[0]
         and not expectation("brokerd", dict(b_r, console=b_r["console"][1:]))[0])
    h_r = {"verdict": "RED", "answered": False,
           "console": ["rlxsim: left out /usr/sbin/httpd (rlxsim.omit=httpd)",
                       "rlxfw: init:   missing: /usr/sbin/httpd",
                       "rlxfw: init: brokerd started pid=70"]}
    case("C21", "the httpd control is met by silence only: not once anything answered",
         expectation("httpd", h_r)[0]
         and not expectation("httpd", dict(h_r, answered=True))[0])
    with tempfile.TemporaryDirectory() as d:
        bad = os.path.join(d, "bad.deb")
        junk = b"\xfd7zXZ\x00 not really xz"
        open(bad, "wb").write(b"!<arch>\n" + f"{'data.tar.xz':<16}{0:<12}{0:<6}{0:<6}"
                              f"{100644:<8}{len(junk):<10}".encode() + b"`\n" + junk)
        case("C22", "a .deb whose data.tar.xz does not decode is refused, not a traceback",
             refuses(deb_members, bad, {"busybox": "bin/busybox"}))
    n_ok = sum(results)
    print(f"maltarun --self-test: {n_ok} of {len(results)} cases passed")
    return 0 if n_ok == len(results) else 1


# -------------------------------------------------------------------- main

def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--self-test"]:
        return self_test()
    ap = argparse.ArgumentParser(prog="maltarun.py", description=SIM + ": " +
                                 "v1.0's userspace on qemu-system-mips -M malta")
    ap.add_argument("--version", action="version", version=TOOL_VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "test", "probe", "fetch", "prepare"):
        s = sub.add_parser(name)
        if name != "probe":
            s.add_argument("--cache", required=True)
        if name in ("run", "test", "prepare"):
            s.add_argument("--out", required=True)
        if name in ("run", "test", "probe"):
            s.add_argument("--port", type=int, default=20080)
        if name in ("test", "probe"):
            s.add_argument("--cap", type=float, default=120.0)
        if name == "test":
            s.add_argument("--green", type=int, default=1)
        if name == "run":
            s.add_argument("--omit", choices=OMITS)
    a = ap.parse_args(argv)
    if getattr(a, "cap", 1) <= 0 or getattr(a, "green", 1) < 1:
        raise Refuse("--cap must be > 0 and --green >= 1")
    for attr in ("cache", "out"):
        if getattr(a, attr, None) is not None:
            setattr(a, attr, os.path.abspath(getattr(a, attr)))
    return {"run": cmd_run, "test": cmd_test, "probe": cmd_probe,
            "fetch": cmd_fetch, "prepare": cmd_prepare}[a.cmd](a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refuse as e:
        print(f"maltarun: REFUSED: {e}", file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(f"maltarun: REFUSED: {e.strerror or e}: {e.filename or ''}",
              file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("maltarun: interrupted", file=sys.stderr)
        sys.exit(2)
