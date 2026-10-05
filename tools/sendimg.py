#!/usr/bin/env python3
"""sendimg.py -- R8b's host-side sender: stream one payload to the armed image's
one-shot `busybox nc -l -p PORT </dev/null >/proc/rtl819x-spi-img`.

    sendimg.py send --to 10.1.1.1:5000 --src 10.1.1.2 --file F --sha256 HEX
    sendimg.py --self-test

The payloads cannot ride inside the provisioning image: inside it they overrun
the boot image's decompression ceiling (SPEC.md FW-240), so they cross the
bench's GbE link, and the kernel's sha256 check at `install` makes the
transport irrelevant to integrity.

`send` REFUSES before connecting unless F's sha256 equals --sha256 -- the
digest the owner's yes names and the `install <region> sha=` line types --
so the bytes put on the wire are the bytes the device will be asked to
install.  It sends everything, half-closes (SHUT_WR, which is the EOF that
ends the device's nc), waits for the device to close, and prints the byte
count and the digest.  It never receives payload data and never writes a
file: it is a sender only.

What it does NOT establish: that the device staged what was sent.  The
device's own `img_len` / `img_err` in /proc/rtl819x-spi, and then the
kernel's sha256 over the staged bytes at `install`, are that check (D7).

FW-124's contract: build_parser() and refuse_args() let cardcheck judge a
card's HOST cell before power; refuse_args() reads no file.

Exit: 0 sent, 1 the transfer failed, 2 a self-test control failed,
3 usage/input refusal.  One line and a reason, never a traceback.
(First written as a session helper in the 124th segment, s124/p.)
"""
import argparse
import hashlib
import os
import re
import socket
import sys
import tempfile
import threading


class Refused(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused("usage: " + message)


def die(msg, code=3):
    sys.stderr.write("sendimg: %s\n" % msg)
    raise SystemExit(code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def to_shape(s):
    """-> (host, port), or raise Refused: HOST:PORT with a port in 1..65535."""
    host, _, port = (s or "").rpartition(":")
    if not host or not port.isdigit() or not 0 < int(port) < 65536:
        raise Refused("--to wants HOST:PORT, got %r" % s)
    return host, int(port)


def parse_to(s):
    try:
        return to_shape(s)
    except Refused as e:
        die(str(e))


def send(path, to, src, want, timeout=30.0):
    """-> (bytes sent, sha256).  Raises OSError on a transfer failure."""
    if not os.path.isfile(path):
        die("no such file: %s" % path)
    got = sha256_file(path)
    if got != want.lower():
        die("%s has sha256 %s, not the %s this send was declared for: "
            "nothing was sent" % (path, got, want.lower()))
    data = open(path, "rb").read()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        if src:
            s.bind((src, 0))
        s.connect(to)
        s.sendall(data)
        s.shutdown(socket.SHUT_WR)
        # The device's nc sends nothing (its stdin is /dev/null) and closes
        # after our EOF; anything it does send is counted, never kept.
        extra = 0
        while True:
            b = s.recv(4096)
            if not b:
                break
            extra += len(b)
    finally:
        s.close()
    return len(data), got, extra


def build_parser():
    """The parser main() uses, and the one cardcheck builds (FW-124). No
    option may be abbreviated."""
    ap = _Parser(prog="sendimg.py", allow_abbrev=False)
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("send", allow_abbrev=False)
    p.add_argument("--to", required=True)
    p.add_argument("--src")
    p.add_argument("--file", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--timeout", type=float, default=30.0)
    return ap


def refuse_args(a):
    """FW-124's contract: refuse what the arguments alone show is wrong,
    reading no file -- the payload need not exist when a card is checked."""
    if a.self_test:
        return
    if a.cmd != "send":
        raise Refused("no subcommand: `send` or `--self-test`")
    to_shape(a.to)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", a.sha256 or ""):
        raise Refused("--sha256 wants 64 hex digits, got %r" % a.sha256)
    if not a.timeout > 0:
        raise Refused("--timeout must be positive, got %r" % a.timeout)


def self_test():
    rows = []
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "payload.bin")
        blob = bytes((i * 7 + 3) & 0xFF for i in range(300001))
        with open(p, "wb") as fh:
            fh.write(blob)
        want = hashlib.sha256(blob).hexdigest()
        got = []
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]

        def accept():
            c, _ = srv.accept()
            buf = bytearray()
            while True:
                b = c.recv(65536)
                if not b:
                    break
                buf += b
            c.close()
            got.append(bytes(buf))

        t = threading.Thread(target=accept)
        t.start()
        n, h, extra = send(p, ("127.0.0.1", port), "127.0.0.1", want)
        t.join(10)
        srv.close()
        rows.append(("S1", "a send delivers every byte, in order",
                     bool(got) and got[0] == blob and n == len(blob),
                     "%d sent, %d received" % (n, len(got[0]) if got else -1)))
        rows.append(("S2", "the digest it prints is the file's", h == want, h[:16]))
        # S3: the guard REFUSES a file whose digest is not the declared one,
        # before any connection (port 9 on loopback: nothing listens).
        rc = None
        try:
            send(p, ("127.0.0.1", 9), None, "00" * 32)
        except SystemExit as e:
            rc = e.code
        rows.append(("S3", "a wrong --sha256 is refused before connecting",
                     rc == 3, "rc=%s" % rc))

    def av(argv):
        try:
            refuse_args(build_parser().parse_args(argv))
            return "ok"
        except Refused as e:
            return "REFUSED " + str(e)
    good = ["send", "--to", "10.1.1.1:5000", "--src", "10.1.1.2", "--file",
            "/nonexistent/P.rlxu", "--sha256", "a" * 64]
    v = av(good)
    rows.append(("K1", "refuse_args permits a well-formed send (file absent)", v == "ok", v))
    v = av(good[:8] + ["0" * 63])
    rows.append(("K2", "refuse_args refuses a digest that is not 64 hex",
                  v.startswith("REFUSED --sha256"), v))
    v = av(["send", "--to", "10.1.1.1", "--file", "f", "--sha256", "a" * 64])
    rows.append(("K3", "refuse_args refuses a --to with no port",
                  v.startswith("REFUSED --to"), v))
    v = av(["send", "--t", "10.1.1.1:5000", "--file", "f", "--sha256", "a" * 64])
    rows.append(("K4", "the parser refuses an abbreviated option",
                  v.startswith("REFUSED usage"), v))
    bad = 0
    for cid, what, ok, det in rows:
        print("  %-6s %-4s %-52s %s" % ("ok" if ok else "FAIL", cid, what, det))
        bad += 0 if ok else 1
    print("  %d passed, %d failed" % (len(rows) - bad, bad))
    return 2 if bad else 0


def main():
    try:
        a = build_parser().parse_args()
        refuse_args(a)
    except Refused as e:
        die(str(e))
    if a.self_test:
        return self_test()
    try:
        n, h, extra = send(a.file, parse_to(a.to), a.src, a.sha256, a.timeout)
    except OSError as e:
        die("transfer failed: %s" % e, code=1)
    print("sendimg: sent %d bytes sha256 %s to %s (peer sent %d bytes back)"
          % (n, h, a.to, extra))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        die("interrupted")
