#!/usr/bin/env python3
"""bootslot -- which flash slot rlxboot booted, read from a console capture.

Why this file exists
--------------------
`R8b-6`'s DoD reads `RLXBOOT-SLOT` and `RLXFW-ID0` *by tool*, and before this
file no tool read `RLXBOOT-SLOT` or `RLXBOOT-VERDICT` at all: `looprun`'s
`assert_boot` reads the eleven boot marks, their order, the id and the prompt,
which say a kernel booted and not which slot it came from or why the other
slot lost.  Ten power pulls are judged here, each by the TORN slot's verdict
and by the slot that booted, so a misread is a gate result read wrong.

What it reads, and from where -- 讀, `src/rlxboot` at `94d97924`
---------------------------------------------------------------
Every line format below is the payload's own, and `S1`-`S4` re-read the
sources on every self-test so a changed printf turns this file red instead of
turning a capture silently unreadable:

    RLXBOOT-V1 build=<8 hex>                          main.c, once per run
    RLXBOOT-FROM <8 hex>                              main.c, right after it (D28)
    RLXBOOT-KEY prod|dev <64 hex>                     main.c, after those
    RLXBOOT-CTRSRC flash                              main.c (slots build)
    RLXBOOT-READ A flash=00070000 buf=81000000 n=<dec>[ <dots>]   slots.c
    RLXBOOT-HDR ok | RLXBOOT-HDR bad=<r>              main.c report()
    RLXBOOT-SIG ok|bad, RLXBOOT-DIGEST ok|bad         main.c report()
    RLXBOOT-VER cur=<dec> ctr=<dec> ok|bad            main.c report()
    RLXBOOT-VERDICT A ok ver=<dec> | bad=<reason>     slots.c
    ... the same for B ...
    RLXBOOT-SLOT A|B   or   RLXBOOT-HALT A=<r> B=<r>  slots.c
    RLXBOOT-BOOT load=<8 hex> entry=<8 hex>           main.c, before the jump
    RLXFW-ID0=<8 HEX>                                 the kernel, rlxfw_mark.c

Hex from the payload is lower case (`out_hex8`, `rlx_puthex32`); the kernel's
id is UPPER case (`rlxfw_puts_hex`), and the manifest's `recipe_id` is
`sha256sum`'s lower case, so the id comparison folds case.  One dot is printed
per 64 KiB copied, after `n=` and a space, so the dot count of a finished copy
is exactly n // 65536 -- the host output in `notes/rlxboot.md` (n=100160 one
dot, n=300160 four, n=1114272 seventeen) is `S5`.  Captures are CRLF and
device lines may arrive CR CR LF, so every `\\r` is removed before a line is
compared.

The expected id comes from a FILE, never from a typed value (CLAUDE.md: a
booted image is identified by a tool comparing RLXFW-ID0 with the build's
digest): `--build-manifest` names the `rlxfw-build-manifest` that
`tools/rlxfw-kbuild.sh` writes beside the image, and its `recipe_id` row is
the expectation.

`RLXBOOT-FROM` (D28) is the word rlxboot reads at the stock loader's global
0x8040DD3C: the flash candidate the loader accepted, so it separates a boot of
`rlxboot` at 0x010000 from one of the rescue at 0x020000.  It is judged only
when `--expect-from <hex>` is given, and then a capture without the line is
REFUSED rather than passed.  ⚠️ What the word holds is 讀 only:
`docs/loader-command-semantics.md` s a and s 8 row 1 predict the offset
biased by 0x05000000 (0x05010000 and 0x05020000).  Nothing has read it on this
unit, so the first bench reading is the measurement and an expectation is
written from it, not from this paragraph.

Refusals, and why they are not verdicts
---------------------------------------
* No `RLXBOOT-V1` line: the capture never reached rlxboot (a vendor boot, a
  loader prompt, a capture started late).  That is not "no slot booted", and
  reading it as one would turn a missed capture into a pass for a HALT.
* Two banners: two rlxboot runs in one file; which one is being judged would
  be a guess.
* A slot was chosen and no `RLXFW-ID0` follows its `RLXBOOT-BOOT` line, or two
  do: the booted kernel cannot be identified.  An id that appears only BEFORE
  the banner is a previous image's and is never used (`R9` is that trap: a
  reader taking the first id would pass it).
* No KEY line after the banner (an rlxboot older than `94d97924`), a
  `CTRSRC ram` build (it reads no slot), a capture that ends before the choice,
  an unreadable file, a malformed expectation, or a manifest without a
  well-formed `recipe_id`.
* `--expect-from` given and no `RLXBOOT-FROM` line (an rlxboot older than
  D28), or two of them after one banner.

Exit: 0 PASS, 1 FAIL (the capture contradicts the expectation or itself),
2 a self-test control failed, 3 REFUSED -- one line and a reason, never a
traceback.

What it does NOT establish
--------------------------
That the capture is complete or unedited -- it reads what the file holds.
That the key printed is the owner's: it requires `prod` (unless
`--allow-dev-key`) and prints the hex; comparing the hex with the committed
key is `src/rlxboot/mkprodkey.py check`'s, and not restated here.  Where in a
write a power cut landed: the install's own `RLXFW-SI` lines say that.  And
what the loader's word MEANS: the rescue and `rlxboot` are one payload under
two headers, so without `RLXBOOT-FROM` this tool cannot tell their boots
apart; with it, it compares a word with an expectation, and that the word is
the accepted candidate is the loader's reading above, not this tool's.

Run:  /usr/bin/python3 tools/bootslot.py judge CAPTURE.log --expect-slot B \\
          --expect-a bad --expect-b ok:2 --build-manifest IMAGE.kbuild-manifest \\
          [--expect-from 05010000]
      /usr/bin/python3 tools/bootslot.py show CAPTURE.log
      /usr/bin/python3 tools/bootslot.py --self-test
"""
import argparse
import os
import re
import sys
import tempfile

sys.dont_write_bytecode = True          # an import must not write the tree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import looprun  # noqa: E402  -- one owner for the RLXFW-ID0 pattern

VERSION = "1.1"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 讀 src/rlxboot/container.c reason_names[] (S2 re-reads it)
REASONS = ("ok", "short", "magic", "format", "header_len", "version",
           "payload_len", "flags", "reserved", "load_addr", "entry_addr",
           "dst_self", "dst_buf", "dst_loader", "truncated", "sig", "digest",
           "rollback", "flash_dst", "flash_match", "flash_form")
OUT_OF_RANGE = "bad_reason"     # what rlxu_reason_name() returns past the end
# 讀 src/rlxboot/rlxboot.h, slots.h (S3 re-reads them)
SLOTS = {"A": (0x00070000, 0x81000000), "B": (0x00190000, 0x81200000)}
SLOT_SIZE = 0x00120000
TICK = 0x10000

BANNER_RE = re.compile(r"RLXBOOT-V1 build=([0-9a-f]{8})")
FROM_RE = re.compile(r"^RLXBOOT-FROM ([0-9a-f]{8})$")
FROM_EXPECT_RE = re.compile(r"^(?:0x)?([0-9a-fA-F]{1,8})$")
KEY_RE = re.compile(r"^RLXBOOT-KEY (prod|dev) ([0-9a-f]{64})$")
CTR_RE = re.compile(r"^RLXBOOT-CTRSRC (flash|ram)$")
READ_RE = re.compile(r"^RLXBOOT-READ ([AB]) flash=([0-9a-f]{8}) "
                     r"buf=([0-9a-f]{8}) n=(\d+)( \.*)?$")
VERDICT_RE = re.compile(r"^RLXBOOT-VERDICT ([AB]) (?:ok ver=(\d+)|bad=([a-z_]+))$")
STAGE_OK = ("RLXBOOT-HDR ok", "RLXBOOT-SIG ok", "RLXBOOT-DIGEST ok")
VER_RE = re.compile(r"^RLXBOOT-VER cur=(\d+) ctr=(\d+) (ok|bad)$")
SLOT_RE = re.compile(r"^RLXBOOT-SLOT ([AB])$")
HALT_RE = re.compile(r"^RLXBOOT-HALT A=([a-z_]+) B=([a-z_]+)$")
BOOT_RE = re.compile(r"^RLXBOOT-BOOT load=([0-9a-f]{8}) entry=([0-9a-f]{8})$")
ID0_RE = looprun.ID0_RX
EXPECT_RE = re.compile(r"^(ok|bad)(?::([0-9]+|[a-z_]+))?$")


class Refused(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refused("usage: " + message)


# ------------------------------------------------------------------- parse
def lines_of(text):
    """The capture as lines, every CR removed first (CRLF and CR CR LF)."""
    return text.replace("\r", "").split("\n")


def parse(text):
    """-> what the capture says, as a dict.  Raises Refused when it cannot be
    judged at all; contradictions are left for judge() to FAIL on."""
    ln = lines_of(text)
    banners = [i for i, s in enumerate(ln) if BANNER_RE.search(s)]
    if not banners:
        raise Refused("no `RLXBOOT-V1 build=` line: this capture never reached "
                      "rlxboot, so it says nothing about which slot booted")
    if len(banners) > 1:
        raise Refused("%d rlxboot banners (lines %s): one capture, one rlxboot "
                      "run -- split it" % (len(banners),
                                           ", ".join(str(i + 1) for i in banners)))
    b0 = banners[0]
    f = {"build": BANNER_RE.search(ln[b0]).group(1), "banner_line": b0 + 1,
         "slots": {}, "choice": None, "halt": None, "boot": None,
         "id0": None, "id0_before": [], "problems": []}
    seg = [(i, s) for i, s in enumerate(ln) if i > b0]
    keys = [(i, KEY_RE.match(s)) for i, s in seg if KEY_RE.match(s)]
    if not keys:
        raise Refused("no `RLXBOOT-KEY` line after the banner: an rlxboot "
                      "older than 94d97924, which reads no slot")
    if len(keys) > 1:
        raise Refused("%d KEY lines after one banner" % len(keys))
    f["key"] = (keys[0][1].group(1), keys[0][1].group(2))
    froms = [FROM_RE.match(s).group(1) for _i, s in seg if FROM_RE.match(s)]
    if len(froms) > 1:
        raise Refused("%d `RLXBOOT-FROM` lines after one banner" % len(froms))
    f["from"] = froms[0] if froms else None
    ctrs = [CTR_RE.match(s).group(1) for _i, s in seg if CTR_RE.match(s)]
    if len(ctrs) != 1:
        raise Refused("%d `RLXBOOT-CTRSRC` lines after the banner, want 1"
                      % len(ctrs))
    if ctrs[0] != "flash":
        raise Refused("`RLXBOOT-CTRSRC ram`: a BOOT=ram rlxboot, which reads "
                      "no slot")
    f["id0_before"] = [m.group(1) for s in ln[:b0] for m in [ID0_RE.search(s)] if m]

    order = []                      # (line, kind, slot) in capture order
    for i, s in seg:
        m = READ_RE.match(s)
        if m:
            order.append((i, "READ", m.group(1)))
            f["slots"].setdefault(m.group(1), {})["read"] = (
                int(m.group(2), 16), int(m.group(3), 16), int(m.group(4)),
                len((m.group(5) or "").strip()), m.group(5) is not None)
            f["slots"][m.group(1)]["stages"] = []
            continue
        m = VERDICT_RE.match(s)
        if m:
            order.append((i, "VERDICT", m.group(1)))
            v = ("ok", int(m.group(2))) if m.group(2) else ("bad", m.group(3))
            f["slots"].setdefault(m.group(1), {})["verdict"] = v
            continue
        if SLOT_RE.match(s):
            order.append((i, "SLOT", SLOT_RE.match(s).group(1)))
            continue
        if HALT_RE.match(s):
            order.append((i, "HALT", HALT_RE.match(s).groups()))
            continue
        if BOOT_RE.match(s):
            order.append((i, "BOOT", BOOT_RE.match(s).groups()))
            continue
        # a stage line belongs to the slot whose READ came last
        if s in STAGE_OK or VER_RE.match(s):
            reads = [o for o in order if o[1] == "READ"]
            if reads:
                f["slots"][reads[-1][2]]["stages"].append(s)
    f["order"] = order
    kinds = [o[1] for o in order]
    for k in ("SLOT", "HALT", "BOOT"):
        if kinds.count(k) > 1:
            raise Refused("%d `RLXBOOT-%s` lines after one banner" % (kinds.count(k), k))
    if "SLOT" not in kinds and "HALT" not in kinds:
        raise Refused("the capture ends before rlxboot chose (no `RLXBOOT-SLOT` "
                      "and no `RLXBOOT-HALT`): extend it with --until, do not "
                      "read it as a halt")
    for o in order:
        if o[1] == "SLOT":
            f["choice"], f["choice_line"] = o[2], o[0]
        elif o[1] == "HALT":
            f["choice"], f["halt"], f["choice_line"] = "HALT", o[2], o[0]
        elif o[1] == "BOOT":
            f["boot"], f["boot_line"] = o[2], o[0]
    if f["choice"] in SLOTS:
        start = f.get("boot_line", f["choice_line"])
        ids = [m.group(1) for i, s in seg if i > start
               for m in [ID0_RE.search(s)] if m]
        if not ids:
            raise Refused("rlxboot chose slot %s and no `RLXFW-ID0=` follows %s: "
                          "the booted kernel cannot be identified%s"
                          % (f["choice"], "its BOOT line" if f["boot"] else "the choice",
                             " (an id BEFORE the banner is a previous image's and "
                             "is never used)" if f["id0_before"] else ""))
        if len(ids) > 1:
            raise Refused("%d `RLXFW-ID0` lines after the boot: more than one "
                          "kernel ran in this capture" % len(ids))
        f["id0"] = ids[0]
    return f


# ----------------------------------------------------------------- expect
def parse_expect(spec, what):
    m = EXPECT_RE.match(spec or "")
    if not m:
        raise Refused("%s %r: want ok, ok:<version>, bad or bad:<reason>"
                      % (what, spec))
    kind, arg = m.group(1), m.group(2)
    if kind == "ok" and arg is not None and not arg.isdigit():
        raise Refused("%s %r: an ok verdict carries a version number" % (what, spec))
    if kind == "bad" and arg is not None and (arg.isdigit() or arg == "ok"
                                              or arg not in REASONS + (OUT_OF_RANGE,)):
        raise Refused("%s %r: %r is not a reason rlxboot prints" % (what, spec, arg))
    return kind, (int(arg) if kind == "ok" and arg else arg)


def read_manifest(path):
    """-> recipe_id from an rlxfw-build-manifest (tools/rlxfw-kbuild.sh)."""
    try:
        with open(path, encoding="utf-8") as fh:
            rows = fh.read().replace("\r", "").split("\n")
    except OSError as e:
        raise Refused("build manifest %s is unreadable: %s" % (path, e.strerror))
    head = rows[0].split("\t") if rows else []
    if len(head) != 2 or head[0] != "rlxfw-build-manifest" or not head[1].isdigit():
        raise Refused("%s is not an rlxfw-build-manifest (first line %r)"
                      % (path, rows[0][:60] if rows else ""))
    ids = [r.split("\t", 1)[1] for r in rows if r.startswith("recipe_id\t")]
    if len(ids) != 1 or not re.fullmatch(r"[0-9a-f]{8}", ids[0]):
        raise Refused("%s holds %d recipe_id row(s)%s; want exactly one of eight "
                      "lower-case hex digits" % (path, len(ids),
                                                 " (%r)" % ids[0] if ids else ""))
    return ids[0]


def d4(slots):
    """The choice the slots' own verdicts imply (spec D4)."""
    ok = {s: v["verdict"][1] for s, v in slots.items()
          if v.get("verdict", ("", 0))[0] == "ok"}
    if "A" in ok and "B" in ok:
        return "B" if ok["B"] > ok["A"] else "A"
    return "A" if "A" in ok else "B" if "B" in ok else "HALT"


# ------------------------------------------------------------------ judge
def judge(text, want_slot, want_a, want_b, manifest=None, allow_dev=False,
          want_from=None):
    """-> (result, [(ok, label, detail)], facts).  result: PASS or FAIL.
    Raises Refused when there is nothing to judge."""
    if want_slot not in ("A", "B", "HALT"):
        raise Refused("--expect-slot %r: want A, B or HALT" % (want_slot,))
    exp = {"A": parse_expect(want_a, "--expect-a"),
           "B": parse_expect(want_b, "--expect-b")}
    if want_from is not None:
        m = FROM_EXPECT_RE.match(want_from)
        if not m:
            raise Refused("--expect-from %r: want up to eight hex digits, 0x "
                          "optional" % (want_from,))
        want_from = "%08x" % int(m.group(1), 16)
    if want_slot == "HALT" and manifest:
        raise Refused("a HALT boots no kernel, so there is no id to compare "
                      "-- drop --build-manifest")
    if want_slot in SLOTS and not manifest:
        raise Refused("an expected slot needs --build-manifest: the expected "
                      "id comes from the build, never from a typed value")
    want_id = read_manifest(manifest) if manifest else None
    f = parse(text)
    if want_from is not None and f["from"] is None:
        raise Refused("--expect-from %s given and the capture has no "
                      "`RLXBOOT-FROM` line: an rlxboot older than D28, which "
                      "never read the loader's word -- not a mismatch" % want_from)
    res = []

    def chk(okv, label, detail):
        res.append((bool(okv), label, detail))

    if want_from is not None:
        chk(f["from"] == want_from, "from",
            "the loader's word at 0x8040DD3C read %s, want %s"
            % (f["from"], want_from))

    chk(f["key"][0] == "prod" or allow_dev, "key",
        "%s %s...%s" % (f["key"][0], f["key"][1][:8],
                        "" if f["key"][0] == "prod" or allow_dev
                        else " -- a dev-key rlxboot accepts anyone's container"))
    seq = [(o[1], o[2]) for o in f["order"] if o[1] in ("READ", "VERDICT")]
    chk(seq == [("READ", "A"), ("VERDICT", "A"), ("READ", "B"), ("VERDICT", "B")],
        "order", "READ/VERDICT sequence %s" % " ".join("%s %s" % x for x in seq))
    for s in ("A", "B"):
        info = f["slots"].get(s, {})
        rd = info.get("read")
        if rd:
            flash, buf, n, dots, spaced = rd
            chk((flash, buf) == SLOTS[s], "read %s" % s,
                "flash=%08x buf=%08x (layout wants %08x %08x)"
                % (flash, buf, SLOTS[s][0], SLOTS[s][1]))
            want_dots = n // TICK
            chk(dots == want_dots and spaced == (n >= TICK), "copy %s" % s,
                "n=%d with %d dot(s), a finished copy prints %d" % (n, dots, want_dots))
        v = info.get("verdict")
        if v and v[0] == "ok":
            vers = [VER_RE.match(x) for x in info.get("stages", []) if VER_RE.match(x)]
            stages_ok = all(x in info.get("stages", []) for x in STAGE_OK)
            chk(stages_ok and len(vers) == 1 and vers[0].group(3) == "ok"
                and int(vers[0].group(1)) == v[1], "stages %s" % s,
                "an ok verdict needs HDR/SIG/DIGEST ok and one `VER cur=%d ... ok`"
                " (got %s)" % (v[1], [x for x in info.get("stages", [])]))
        kind, arg = exp[s]
        got = "%s %s" % (v[0], v[1]) if v else "none"
        hit = bool(v) and v[0] == kind and (arg is None or v[1] == arg)
        chk(hit, "verdict %s" % s, "want %s%s, got %s"
            % (kind, "" if arg is None else ":%s" % arg, got))
    implied = d4(f["slots"])
    chk(f["choice"] == implied, "D4",
        "rlxboot chose %s, its own verdicts imply %s" % (f["choice"], implied))
    if f["halt"]:
        hv = {s: f["slots"].get(s, {}).get("verdict", ("", ""))[1] for s in SLOTS}
        chk(f["halt"] == (hv["A"], hv["B"]), "halt",
            "HALT A=%s B=%s against verdicts A=%s B=%s"
            % (f["halt"][0], f["halt"][1], hv["A"], hv["B"]))
    if f["choice"] in SLOTS:
        chk(f["boot"] is not None, "boot",
            "load=%s entry=%s" % f["boot"] if f["boot"] else
            "chose slot %s and printed no RLXBOOT-BOOT line" % f["choice"])
        chk(f["id0"].lower() == want_id, "id",
            "board printed %s, the build manifest says %s" % (f["id0"], want_id))
    chk(f["choice"] == want_slot, "slot",
        "want %s, got %s" % (want_slot, f["choice"]))
    return ("PASS" if all(r[0] for r in res) else "FAIL"), res, f


# -------------------------------------------------------------- self-test
KEY_FX = "5a" * 32          # a fixture value; the FORMAT is main.c's


def fx_slot(name, verdict, arg, n=None, dots=None, ctr=0, ver_cur=None):
    """One slot's lines exactly as slots.c and main.c print them."""
    flash, buf = SLOTS[name]
    if n is None:
        n = 1109152 if verdict == "ok" else 160
    read = "RLXBOOT-READ %s flash=%08x buf=%08x n=%d" % (name, flash, buf, n)
    if n >= TICK:
        read += " " + "." * (n // TICK if dots is None else dots)
    out = [read]
    if verdict == "ok":
        out += ["RLXBOOT-HDR ok", "RLXBOOT-SIG ok", "RLXBOOT-DIGEST ok",
                "RLXBOOT-VER cur=%d ctr=%d ok" % (arg if ver_cur is None else ver_cur, ctr),
                "RLXBOOT-VERDICT %s ok ver=%d" % (name, arg)]
    else:
        out += {"magic": ["RLXBOOT-HDR bad=magic"],
                "sig": ["RLXBOOT-HDR ok", "RLXBOOT-SIG bad"],
                "digest": ["RLXBOOT-HDR ok", "RLXBOOT-SIG ok", "RLXBOOT-DIGEST bad"]
                }.get(arg, ["RLXBOOT-HDR bad=%s" % arg])
        out += ["RLXBOOT-VERDICT %s bad=%s" % (name, arg)]
    return out


def fx_capture(a, b, choice, key="prod", ctr="flash", id0="4BE284C6", eol="\r\n",
               boot=True, ids_after=1, pre=(), banners=1, keyline=True, cut=False,
               froms=()):
    ln = ["Reboot Result from Watchdog Timeout!", "Booting..."] + list(pre)
    for _ in range(banners):
        ln += ["RLXBOOT-V1 build=6b1dc4fd"]
    ln += ["RLXBOOT-FROM %s" % w for w in froms]     # D28, right after the banner
    if keyline:
        ln += ["RLXBOOT-KEY %s %s" % (key, KEY_FX)]
    ln += ["RLXBOOT-CTRSRC %s" % ctr] + a + b
    if cut:
        return eol.join(ln) + eol
    if choice == "HALT":
        ra = a[-1].rsplit("=", 1)[1]
        rb = b[-1].rsplit("=", 1)[1]
        ln += ["RLXBOOT-HALT A=%s B=%s" % (ra, rb), "refuse-action halt"]
    else:
        ln += ["RLXBOOT-SLOT %s" % choice]
        if boot:
            ln += ["RLXBOOT-BOOT load=80500000 entry=80500000"]
        ln += ["Linux version 2.6.30.9 (fixture)"]
        ln += ["RLXFW-ID0=%s" % id0] * ids_after
        ln += ["rlxfw: init running, RLXFW-R3-RUNG1-OK", "/ # "]
    return eol.join(ln) + eol


def _c_literals(path):
    with open(path, encoding="utf-8") as fh:
        return re.findall(r'"((?:[^"\\\n]|\\.)*)"', fh.read())


def self_test():
    cases, bad = [], 0
    tmp = tempfile.mkdtemp(prefix="bootslot-")

    def man(rid, head="rlxfw-build-manifest\t2"):
        """A manifest in tools/rlxfw-kbuild.sh's shape; rid None leaves out the
        recipe_id row."""
        p = os.path.join(tmp, "m-%d.manifest" % len(os.listdir(tmp)))
        body = "%s\ncell\tfixture\n" % head
        if rid is not None:
            body += "recipe_id\t%s\n" % rid
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body + "verdict\tgreen\n")
        return p

    good = man("4be284c6")

    def run(text, slot, a, b, m=None, dev=False, frm=None):
        try:
            r, _res, _f = judge(text, slot, a, b, m, dev, frm)
            return r, [x for x in _res if not x[0]]
        except Refused as e:
            return "REFUSED", str(e)

    def case(cid, what, okv, detail=""):
        nonlocal bad
        cases.append(cid)
        if okv:
            print("  ok    %-4s %s" % (cid, what))
        else:
            bad += 1
            print("  FAIL  %-4s %s -- %s" % (cid, what, detail))

    # ---- S: the formats are the source's, re-read every run --------------
    rb = os.path.join(REPO, "src", "rlxboot")
    try:
        lit = {"main.c": _c_literals(os.path.join(rb, "main.c")),
               "slots.c": _c_literals(os.path.join(rb, "slots.c"))}
        need = {"main.c": ("RLXBOOT-V1 build=", "RLXBOOT-FROM ",
                           "RLXBOOT-KEY prod ", "RLXBOOT-KEY dev ",
                           "RLXBOOT-CTRSRC flash", "RLXBOOT-HDR ", "RLXBOOT-SIG ok",
                           "RLXBOOT-DIGEST ok", "RLXBOOT-VER cur=", " ctr=", " ok",
                           "RLXBOOT-BOOT load=", " entry=", "refuse-action halt"),
                "slots.c": ("RLXBOOT-READ ", " flash=", " buf=", " n=",
                            "RLXBOOT-VERDICT ", " ok ver=", " bad=",
                            "RLXBOOT-SLOT ", "RLXBOOT-HALT ")}
        miss = [(f, s) for f, ss in need.items() for s in ss
                if not any(s in x for x in lit[f])]
        case("S1", "every literal this parser keys on is a string in main.c/slots.c",
             not miss, "missing %s" % miss)
        with open(os.path.join(rb, "container.c"), encoding="utf-8") as fh:
            tbl = re.search(r"reason_names\[[^\]]*\]\s*=\s*\{(.*?)\};", fh.read(), re.S)
        names = tuple(re.findall(r'"([a-z_]+)"', tbl.group(1))) if tbl else ()
        case("S2", "REASONS is container.c's reason_names[], in order",
             names == REASONS, "source %s" % (names,))
        hdr = ""
        for h in ("rlxboot.h", "slots.h"):
            with open(os.path.join(rb, h), encoding="utf-8") as fh:
                hdr += fh.read()
        defs = dict((k, int(v, 16)) for k, v in
                    re.findall(r"#define\s+(RLXB_\w+)\s+0x([0-9A-Fa-f]+)UL", hdr))
        want = {"RLXB_SLOT_A_FLASH": SLOTS["A"][0], "RLXB_SLOT_B_FLASH": SLOTS["B"][0],
                "RLXB_SLOT_A_BUF": SLOTS["A"][1], "RLXB_SLOT_B_BUF": SLOTS["B"][1],
                "RLXB_SLOT_SIZE": SLOT_SIZE, "RLXB_TICK_BYTES": TICK}
        case("S3", "the slot layout and the dot step are rlxboot.h/slots.h's",
             all(defs.get(k) == v for k, v in want.items()),
             "source %s" % {k: hex(defs[k]) for k in want if k in defs})
        with open(os.path.join(REPO, "config", "rlxfw-src", "linux-2.6.30", "arch",
                               "rlx", "kernel", "rlxfw_mark.c"), encoding="utf-8") as fh:
            mk = fh.read()
        with open(os.path.join(REPO, "config", "rlxfw-marks.tsv"), encoding="utf-8") as fh:
            marks = fh.read()
        case("S4", "the kernel prints ID0 as rlxfw_markx(\"ID0\") in UPPER-case hex",
             '"0123456789ABCDEF"' in mk and 'rlxfw_markx("ID0"' in marks
             and ID0_RE.search("RLXFW-ID0=4BE284C6") is not None,
             "rlxfw_mark.c or rlxfw-marks.tsv changed")
    except (OSError, AttributeError) as e:
        case("S1", "the sources this parser is checked against are readable", False, str(e))
    # S5: slots.c's own output on the host (notes/rlxboot.md, `t_slots show`)
    host = ["RLXBOOT-READ A flash=00070000 buf=81000000 n=100160 .",
            "RLXBOOT-READ B flash=00190000 buf=81200000 n=1114272 .................",
            "RLXBOOT-READ B flash=00190000 buf=81200000 n=300160 ...."]
    dm = [READ_RE.match(x) for x in host]
    case("S5", "the dot rule (n // 65536) reproduces slots.c's recorded host output",
         all(m and len(m.group(5).strip()) == int(m.group(4)) // TICK for m in dm),
         "%s" % [(m.group(4), len(m.group(5).strip())) if m else None for m in dm])

    # ---- P: each verdict read right -------------------------------------
    p1 = fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B")
    p2 = fx_capture(fx_slot("A", "magic", "magic"), fx_slot("B", "ok", 2), "B")
    p3 = fx_capture(fx_slot("A", "ok", 1),
                    fx_slot("B", "digest", "digest", n=1109152), "A")
    p4 = fx_capture(fx_slot("A", "ok", 3), fx_slot("B", "ok", 2), "A")
    p5 = fx_capture(fx_slot("A", "ok", 2), fx_slot("B", "ok", 2), "A")
    p6 = fx_capture(fx_slot("A", "magic", "magic"), fx_slot("B", "magic", "magic"), "HALT")
    pos = [("P1", "both ok, B higher -> B", p1, "B", "ok:1", "ok:2", good),
           ("P2", "A torn (magic), B ok -> B", p2, "B", "bad:magic", "ok:2", good),
           ("P3", "B torn (digest), A ok -> A", p3, "A", "ok:1", "bad:digest", good),
           ("P4", "A v3 over B v2 -> A", p4, "A", "ok:3", "ok:2", good),
           ("P5", "a tie boots A (D4)", p5, "A", "ok:2", "ok:2", good),
           ("P6", "neither verifies -> HALT, no id needed", p6, "HALT", "bad:magic",
            "bad:magic", None),
           ("P7", "CR CR LF line endings read as CRLF", p1.replace("\r\n", "\r\r\n"),
            "B", "ok:1", "ok:2", good),
           ("P8", "`bad` with no reason matches any refusal",
            fx_capture(fx_slot("A", "sig", "sig", n=1109152), fx_slot("B", "ok", 2), "B"),
            "B", "bad", "ok", good),
           ("P9", "a previous image's id before the banner is ignored",
            fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B",
                       pre=("RLXFW-ID0=6AEDE68A",)), "B", "ok:1", "ok:2", good)]
    for cid, what, text, s, a, b, m in pos:
        r, why = run(text, s, a, b, m)
        case(cid, what + ": PASS", r == "PASS", "%s %s" % (r, why))

    # ---- M: a wrong expectation, or a self-contradicting capture, goes red.
    # Each mutant's base is a P case shown passing above, so a red here is the
    # mutation and not a tool that fails everything.
    off = man("4be284c7")
    muts = [("M1", "the wrong slot", p1, "A", "ok:1", "ok:2", good),
            ("M2", "the wrong version", p1, "B", "ok:2", "ok:2", good),
            ("M3", "a torn slot expected ok", p2, "B", "ok", "ok:2", good),
            ("M4", "the wrong refusal reason", p2, "B", "bad:digest", "ok:2", good),
            ("M5", "the manifest's id one digit off", p1, "B", "ok:1", "ok:2", off),
            ("M6", "a HALT expected to boot B", p6, "B", "bad:magic", "bad:magic", good),
            ("M7", "a choice against D4 (B is higher, SLOT A)",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "A"),
             "A", "ok:1", "ok:2", good),
            ("M8", "a dev-key rlxboot without --allow-dev-key",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", key="dev"),
             "B", "ok:1", "ok:2", good),
            ("M9", "HALT reasons that are not the verdicts'",
             p6.replace("RLXBOOT-HALT A=magic", "RLXBOOT-HALT A=sig"),
             "HALT", "bad:magic", "bad:magic", None),
            ("M10", "slot A read from the wrong flash offset",
             p1.replace("flash=00070000", "flash=00080000"), "B", "ok:1", "ok:2", good),
            ("M11", "a copy one dot short (stopped or lost bytes)",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2, dots=15), "B"),
             "B", "ok:1", "ok:2", good),
            ("M12", "an ok verdict whose VER line says another version",
             fx_capture(fx_slot("A", "ok", 1, ver_cur=2), fx_slot("B", "ok", 2), "B"),
             "B", "ok:1", "ok:2", good),
            ("M13", "a slot chosen and no BOOT line",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", boot=False),
             "B", "ok:1", "ok:2", good),
            ("M14", "B's lines before A's",
             fx_capture(fx_slot("B", "ok", 2), fx_slot("A", "ok", 1), "B"),
             "B", "ok:1", "ok:2", good)]
    for cid, what, text, s, a, b, m in muts:
        r, why = run(text, s, a, b, m)
        case(cid, what + ": FAIL", r == "FAIL", "%s %s" % (r, why))

    # ---- R: refusals, each for its own reason ---------------------------
    vendor = "Booting...\r\nLinux version 2.6.30 (vendor)\r\n<RealTek>\r\n"
    refs = [("R1", "no rlxboot banner (a vendor boot): not 'no slot'", vendor,
             "B", "ok", "ok", good, "never reached rlxboot"),
            ("R2", "two banners",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", banners=2),
             "B", "ok", "ok", good, "rlxboot banners"),
            ("R3", "a slot chosen and no id after the boot",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", ids_after=0),
             "B", "ok", "ok", good, "cannot be identified"),
            ("R4", "two ids after the boot",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", ids_after=2),
             "B", "ok", "ok", good, "more than one"),
            ("R5", "a banner with no KEY line (rlxboot before 94d97924)",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", keyline=False),
             "B", "ok", "ok", good, "RLXBOOT-KEY"),
            ("R6", "the capture ends before the choice",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", cut=True),
             "B", "ok", "ok", good, "ends before"),
            ("R7", "a file that is not an rlxfw-build-manifest", p1, "B", "ok", "ok",
             man("4be284c6", head="not-a-manifest\t2"), "not an rlxfw-build-manifest"),
            ("R7b", "a manifest with no recipe_id row", p1, "B", "ok", "ok",
             man(None), "0 recipe_id row"),
            ("R8", "HALT expected with a manifest", p6, "HALT", "bad", "bad", good,
             "no id to compare"),
            ("R9", "the only id is BEFORE the banner (the trap a first-id reader passes)",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", ids_after=0,
                        pre=("RLXFW-ID0=4BE284C6",)), "B", "ok", "ok", good,
             "previous image"),
            ("R10", "an expectation that is not ok/ok:N/bad/bad:R", p1, "B", "maybe", "ok",
             good, "want ok"),
            ("R11", "a BOOT=ram rlxboot",
             fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B", ctr="ram"),
             "B", "ok", "ok", good, "BOOT=ram"),
            ("R12", "a slot expected and no manifest", p1, "B", "ok", "ok", None,
             "needs --build-manifest"),
            ("R13", "a reason rlxboot cannot print", p2, "B", "bad:nonesuch", "ok", good,
             "not a reason")]
    for cid, what, text, s, a, b, m, frag in refs:
        r, why = run(text, s, a, b, m)
        case(cid, what + ": REFUSED", r == "REFUSED" and frag in str(why),
             "%s %s" % (r, why))
    # R14: an unreadable capture refuses through main(), the bench path
    rc = main(["judge", os.path.join(tmp, "absent.log"), "--expect-slot", "A",
               "--expect-a", "ok", "--expect-b", "ok", "--build-manifest", good],
              quiet=True)
    case("R14", "an unreadable capture: rc 3, not a traceback", rc == 3, "rc=%s" % rc)

    # ---- F: RLXBOOT-FROM (D28), judged only when an expectation is given --
    # 05010000 is s 8 row 1's 讀 for a boot of 0x010000, a fixture value here.
    pf = fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B",
                    froms=("05010000",))
    r, why = run(pf, "B", "ok:1", "ok:2", good, False, "0x5010000")
    case("F1", "FROM 05010000 expected as 0x5010000 (normalised): PASS",
         r == "PASS", "%s %s" % (r, why))
    r, why = run(pf, "B", "ok:1", "ok:2", good, False, "05020000")
    case("F2", "FROM 05010000 expected 05020000 (the rescue's word): FAIL",
         r == "FAIL" and any(x[1] == "from" for x in why), "%s %s" % (r, why))
    r, why = run(p1, "B", "ok:1", "ok:2", good, False, "05010000")
    case("F3", "an expectation and NO FROM line: REFUSED, not FAIL",
         r == "REFUSED" and "no `RLXBOOT-FROM`" in str(why), "%s %s" % (r, why))
    r, why = run(pf, "B", "ok:1", "ok:2", good, False, "0x0501000g")
    case("F4", "a malformed --expect-from: REFUSED",
         r == "REFUSED" and "eight hex digits" in str(why), "%s %s" % (r, why))
    r, why = run(fx_capture(fx_slot("A", "ok", 1), fx_slot("B", "ok", 2), "B",
                            froms=("05010000", "05020000")),
                 "B", "ok:1", "ok:2", good, False, "05010000")
    case("F5", "two FROM lines after one banner: REFUSED",
         r == "REFUSED" and "RLXBOOT-FROM" in str(why), "%s %s" % (r, why))
    r, why = run(pf, "B", "ok:1", "ok:2", good)
    case("F6", "a FROM line and no expectation: judged as before, PASS",
         r == "PASS", "%s %s" % (r, why))

    # FW-124's contract, which cardcheck uses to judge a card's HOST cell
    # before power: refuse_args() permits and refuses on the arguments alone,
    # reading no file, and the parser refuses an abbreviated option.
    def av(argv):
        try:
            refuse_args(build_parser().parse_args(argv))
            return "ok"
        except Refused as e:
            return "REFUSED " + str(e)
    gl = ["judge", os.path.join(tmp, "absent.log"), "--expect-slot", "A",
          "--expect-a", "ok:1", "--expect-b", "bad", "--build-manifest",
          os.path.join(tmp, "absent.manifest")]
    v = av(gl)
    case("K1", "refuse_args permits a well-formed judge line whose files do not exist yet",
         v == "ok", v)
    v = av(gl[:3] + ["C"] + gl[4:])
    case("K2", "refuse_args refuses an unknown slot", v.startswith("REFUSED --expect-slot"), v)
    v = av(gl + ["--expect-from", "zz"])
    case("K3", "refuse_args refuses a malformed --expect-from",
         v.startswith("REFUSED --expect-from"), v)
    v = av(gl[:8])
    case("K4", "refuse_args refuses a slot expectation with no build manifest",
         v.startswith("REFUSED an expected slot"), v)
    v = av(["judge", "x.log", "--expect-s", "A", "--expect-a", "ok", "--expect-b",
            "ok", "--build-manifest", "m"])
    case("K5", "the parser refuses an abbreviated option",
         v.startswith("REFUSED usage"), v)
    print("bootslot %s self-test: %d passed, %d failed" % (VERSION, len(cases) - bad, bad))
    return 2 if bad else 0


# ------------------------------------------------------------------- main
def build_parser():
    """The parser main() uses -- and the one cardcheck builds to judge a card's
    HOST cell before the board is powered (FW-124's contract). No option may
    be abbreviated."""
    ap = _Parser(prog="bootslot.py", allow_abbrev=False)
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    j = sub.add_parser("judge", allow_abbrev=False)
    j.add_argument("capture")
    j.add_argument("--expect-slot", required=True)
    j.add_argument("--expect-a", required=True)
    j.add_argument("--expect-b", required=True)
    j.add_argument("--build-manifest")
    j.add_argument("--allow-dev-key", action="store_true")
    j.add_argument("--expect-from", help="the RLXBOOT-FROM word to require, in "
                   "hex; a capture without the line is then REFUSED")
    sh = sub.add_parser("show", allow_abbrev=False)
    sh.add_argument("capture")
    return ap


def refuse_args(a):
    """FW-124's contract: refuse what the arguments alone show is wrong, with
    judge()'s own rules and messages, and READ NO FILE -- a card is checked
    before the capture it judges exists."""
    if a.self_test:
        return
    if a.cmd not in ("judge", "show"):
        raise Refused("no subcommand: judge, show or --self-test")
    if a.cmd == "show":
        return
    if a.expect_slot not in ("A", "B", "HALT"):
        raise Refused("--expect-slot %r: want A, B or HALT" % (a.expect_slot,))
    parse_expect(a.expect_a, "--expect-a")
    parse_expect(a.expect_b, "--expect-b")
    if a.expect_from is not None and not FROM_EXPECT_RE.match(a.expect_from):
        raise Refused("--expect-from %r: want up to eight hex digits, 0x "
                      "optional" % (a.expect_from,))
    if a.expect_slot == "HALT" and a.build_manifest:
        raise Refused("a HALT boots no kernel, so there is no id to compare "
                      "-- drop --build-manifest")
    if a.expect_slot in SLOTS and not a.build_manifest:
        raise Refused("an expected slot needs --build-manifest: the expected "
                      "id comes from the build, never from a typed value")


def main(argv=None, quiet=False):
    ap = build_parser()
    say = (lambda *a: None) if quiet else print
    try:
        a = ap.parse_args(argv)
        refuse_args(a)
        if a.self_test:
            return self_test()
        try:
            with open(a.capture, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as e:
            raise Refused("capture %s is unreadable: %s" % (a.capture, e.strerror))
        if a.cmd == "show":
            f = parse(text)
            say("bootslot %s: %s" % (VERSION, a.capture))
            say("banner   build=%s (line %d)" % (f["build"], f["banner_line"]))
            say("from     %s" % (f["from"] or "(no RLXBOOT-FROM line)"))
            say("key      %s %s" % f["key"])
            for s in ("A", "B"):
                say("slot %s   %s" % (s, f["slots"].get(s)))
            say("choice   %s   boot %s   id0 %s   ids before the banner %s"
                % (f["choice"], f["boot"], f["id0"], f["id0_before"]))
            return 0
        r, res, f = judge(text, a.expect_slot, a.expect_a, a.expect_b,
                          a.build_manifest, a.allow_dev_key, a.expect_from)
        say("bootslot %s: %s (rlxboot build %s, banner line %d)"
            % (VERSION, a.capture, f["build"], f["banner_line"]))
        for okv, label, detail in res:
            say("check %-10s %-4s %s" % (label, "pass" if okv else "FAIL", detail))
        say("RESULT: %s" % r)
        return 0 if r == "PASS" else 1
    except Refused as e:
        say("RESULT: REFUSED -- %s" % e)
        return 3


if __name__ == "__main__":
    sys.exit(main())
