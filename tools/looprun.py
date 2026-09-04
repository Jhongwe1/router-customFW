#!/usr/bin/env python3
"""looprun -- one `edit -> result` iteration as a single command, with controls.

`R4-3`, `D3` and `D4`.  The gate asks for a loop that "runs unattended and
reports a number", and for "a deliberately broken input turns it red".  Those
are two requirements and the second is the one that makes the first worth
having.

WHAT IT DOES NOT OWN
--------------------
🔴 It opens no serial port and speaks no TFTP.  `console-capture.py` owns *what
this project writes to the wire* -- that is what its `tool_version` field is a
claim about -- and `upstream/tools/loader-tftp.py` owns the transfer.  This file
runs them, in an order, and checks what came back.  A second implementation of
either would be a second thing that can be wrong about the one measurement this
project cannot repeat cheaply.

🔴 It does not own loop TIMING either.  `tools/looptime.py` reads a seating's
captures and reports the loop as it was *served*, including the operator.  What
this file times is its own subprocesses -- machine seconds, one stage at a time.
The two numbers are different quantities and neither is the other's check.

THE ASSERTION IS DERIVED FROM THE BUILD, NOT TYPED
--------------------------------------------------
🟢 This is the part that makes an unattended loop mean something.
`rlxfw-kbuild.sh` computes `RLXFW_SRC_ID` as a sha256 over every file under
`config/` and passes it into the compile; `ID0` in `config/rlxfw-marks.tsv`
prints it on the console as `RLXFW-ID0=xxxxxxxx` immediately after the banner.
So the loop can require that **the board printed the id the build just
computed** -- an eight-hex-digit statement that the thing executing on the
silicon came from this working tree and not from a stale image, the vendor's
firmware, or the loader's own re-staging of flash after a watchdog reset.

Nobody types that value.  It is read out of the driver's stdout at S2 and
required at S8, and if `config/` changed between them the run goes red for the
right reason.

⚠️ Its weakness, stated: `RLXFW_SRC_ID` is a digest of `config/` **only**.  A
change to `src-vendor/`, to the toolchain, or to the `.config` passed with
`--config` does not move it.  It attributes the DECLARATION, not the whole
build.  `notes/reproducible-build.md` owns the rest.

THE STAGES, AND WHICH NEED THE BOARD
-------------------------------------
    S2  build      tools/rlxfw-kbuild.sh                     desk
    S3  assemble   tools/rtkimage.py build                   desk
    S4  reset      console-capture --send 'J BFC00000'       bench
    S5  rescue     upstream/tools/console-dump.py rescue     bench
    S5b burnflag   console-capture --send 'DW 8040D4A0 1'   bench
    S6  upload     upstream/tools/loader-tftp.py put         bench
    S6b staged     console-capture --send 'DW 80500000 8'    bench
    S7  boot       console-capture --send 'J 80500000'       bench
    S8  assert     over S7's capture                         desk

`--mode plan` prints every command in order and runs none of them; that output
IS the bench card's command column, so the card and the tool cannot disagree
about what gets typed.  `--mode replay` runs no stage at all and asserts over a
committed capture -- that is what `--self-test` drives, and it is why the
controls below cost nothing.  `--mode desk` runs S2/S3/S8 for real and takes
S7's capture from `--replay-boot`, which exercises the build and the assertions
without spending a power cycle.  `--mode bench` runs all of it.

ABORT CONDITIONS, WRITTEN HERE BECAUSE UNATTENDED MEANS NOBODY IS WATCHING
--------------------------------------------------------------------------
* any stage exiting non-zero stops the iteration; no later stage runs;
* S4 must show `C-8`'s discriminator (`Reboot Result from Watchdog Timeout!`)
  or the reset did not happen, and **nothing is uploaded** -- the alternative to
  "my image is at 0x80500000" is the vendor's, freshly staged there by the
  loader on that same reset;
* 🔴 S5b must read `00000000` back out of `0x8040D4A0`, or **nothing is
  uploaded**.  `loader-tftp.py` already refuses a rescue report that does not
  echo `AutoBurning=0`; `C-6` is why that is not the same source as the word
  itself, and `RUNSHEET` `G2`/`H1a` make the read-back mandatory before a `put`.
  `--skip S5b` is REFUSED: a guard a flag can switch off is not a guard.  The
  absent case -- no read-back line at all -- fails, because silence is not a
  zero;
* 🔴 S6b must read back, out of 0x80500000, the head of the file S6 just sent
  -- derived from that file, never typed.  S4's reset re-stages 0x80500000 from
  flash, so a failed upload leaves the VENDOR's image there and `J 80500000`
  boots it; S8 would catch that afterwards, and this catches it before the
  power cycle is spent.  It is skippable where S5b is not, and the difference is
  deliberate: this one guards the seating, S5b guards the device;
* `--iterations` and `--budget-seconds` both bound the run, and a failing
  iteration stops the rest rather than being averaged into a green summary;
* 🔴 no stage here may write flash. `S6` is `loader-tftp put`, which lands in
  RAM, and this file refuses to pass `--allow-autoexec` under any flag.

Run:  tools/looprun.py --mode plan   --cell L1
      tools/looprun.py --mode replay --cell L1 --replay-boot bench/2026-08-31b/X-3
      tools/looprun.py --mode desk   --cell L1 --replay-boot bench/2026-08-31b/X-3 \\
                       --config ... --initramfs ... --image ...
      tools/looprun.py --mode bench  --cell LP --out-dir bench/2026-09-02 \\
                       --skip S2,S3 --recipe-override b1434383 \\
                       --image <the image the card names>
      tools/looprun.py --self-test

Exit codes:  0 the loop closed and every assertion held · 1 an assertion failed
             or a stage errored · 2 refused before doing anything
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = "1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_HOST = "10.1.1.1"
LOAD_ADDR = "80500000"
RESET_TARGET = "BFC00000"
# C-8: the loader prints this immediately after `ramSize: 32M` on a warm boot
# and a single space on a cold one.  SPEC.md C-8, 量 2026-08-24.
WATCHDOG_MARK = "Reboot Result from Watchdog Timeout!"
PROMPT = "<RealTek>"
# 🔴 `AUTOBURN` is a RAM variable in the loader, written at 0x8040D4A0 and read
# at exactly one instruction, 0x80401B9C, on the path that decides whether a
# completed upload is BURNED.  `RUNSHEET` `G2`/`H1a`: read it before the `put`
# and stop if it is not zero.  `loader-tftp.py` already refuses a rescue report
# that does not echo `AutoBurning=0` -- but `C-6`, 量 2026-08-24, is the reason
# an echo is not the same source as this word: `AUTOBURN: 0` returns
# `Unknown command !`, which in a flow with no read-back is indistinguishable
# from success.  The echo is the loader saying what it thinks it did.
AUTOBURN_ADDR = "8040D4A0"
AUTOBURN_RX = re.compile(r"8040D4A0:\s*([0-9A-Fa-f]{8})", re.I)
#: one `DW` output line: an address label, then one or more big-endian words.
#: 🔴 The trailing `\r?` is load-bearing and the self-test's positive control is
#: what found it missing: the console sends CRLF, so `$` under re.M sits behind
#: a `\r` and the whole parse returns nothing.  Every NEGATIVE control still
#: passed with it broken -- they were failing for the wrong reason.
DW_LINE_RX = re.compile(
    r"^[ \t]*([0-9A-Fa-f]{8}):[ \t]*((?:[0-9A-Fa-f]{8}[ \t]*)+)\r?$", re.M)
# The eleven boot marks config/rlxfw-marks.tsv declares, in order.
BOOT_MARKS = ["RLXFW-B%02d" % n for n in range(11)]
ID0_RX = re.compile(r"RLXFW-ID0=([0-9A-Fa-f]{8})")
RECIPE_RX = re.compile(r"recipe=([0-9a-f]{8})")
# 🔴 S3 assembles from the tree S2 stages, and until 2026-09-02 nothing carried
# the path between them: `--cell-top` defaulted to the literal placeholder
# below and S3 ran `rtkimage build --cell '<S2's staged tree>'`, which exits 1.
# So `--skip S2,S3` was not a convenience on block 7's card -- it was the only
# way this tool could run, and neither the tool nor the card said so.  The
# driver names the tree in its own `make -C` line; that is the link.
PLACEHOLDER_TOP = "<S2's staged tree>"
CELLTOP_RX = re.compile(r"make -C (\S+)/linux-2\.6\.30\b")
# 🔴 And this one is worse than an exit 1, because it SUCCEEDS: `<rtkimage work
# dir>` is a legal directory name on Linux, so S3 run from the repository root
# with the default would create it there.  CLAUDE.md already records that shape
# once -- a vendor binary writing `offset.tmp` into this repository's root,
# "a place no vendor-tree check watches".
PLACEHOLDER_WORK = "<rtkimage work dir>"
# RECIPE-1.  The driver writes one provenance record per build -- the digests
# of the .config it actually installed and of the initramfs spec, neither of
# which is inside RECIPE_ID.  It lands in $FWRE_WORK, which no seating commits;
# copying it beside the run's own captures is what makes it survive.
MANIFEST_RX = re.compile(r"^== \S+: manifest -> (\S+)$", re.M)
#: the stages that read `--image`.  S6 uploads it; S6b's `assert_staged`
#: derives its expectation FROM it.  Anything else never opens the file.
IMAGE_STAGES = ("S6", "S6b")


class Refused(Exception):
    pass


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class StageFailed(Exception):
    def __init__(self, sid, why):
        super().__init__("%s: %s" % (sid, why))
        self.sid, self.why = sid, why


# --------------------------------------------------------------- the plan
def build_plan(a):
    """-> [ {id, name, kind, argv, note} ], the whole iteration, in order.

    Every command this project would type, produced once and used by `plan`,
    `desk` and `bench` alike.  A card that is rendered from the same list the
    runner executes cannot drift from it.
    """
    out = os.path.join(a.out_dir, a.cell) if a.out_dir else a.cell
    cap = ["/usr/bin/python3", os.path.join("tools", "console-capture.py"),
           "capture", "--port", a.port]
    plan = [
        dict(id="S2", name="build", kind="desk", argv=[
            "bash", os.path.join("tools", "rlxfw-kbuild.sh"), a.cell]
            # CFG-1, 2026-09-04: rlxfw-kbuild.sh now takes EITHER a --config
            # path or a --variant to derive one from config/rlxfw-kernel.delta,
            # and refuses both or neither.  Passing `--config ""` used to mean
            # "fall through to the bare board template", which is the silent
            # default CFG-1 removed.
            + (["--config", a.config] if a.config
               else ["--variant", a.variant])
            + ["--initramfs", a.initramfs,
               "--marks", "--jobs", str(a.jobs)],
            note="prints `recipe=<8 hex>`; S8 requires the board to print it back"),
        dict(id="S3", name="assemble", kind="desk", argv=[
            "/usr/bin/python3", os.path.join("tools", "rtkimage.py"), "build",
            "--cell", a.cell_top, "--vmlinux", a.vmlinux or
            os.path.join(a.cell_top, "linux-2.6.30", "vmlinux"),
            "--label", a.label, "--work", a.work],
            note="rtkload's own nfjrom is the uploadable image; "
                 "S6 sends <work>/<label>/kroot/rtkload/nfjrom"),
        dict(id="S4", name="reset", kind="bench", argv=cap + [
            "--out", out + "-rz", "--send", "J " + RESET_TARGET,
            "--esc-after", "10", "--esc-period", "0.002",
            "--idle", "3", "--seconds", "25"],
            note="ABORT unless the capture holds %r" % WATCHDOG_MARK),
        dict(id="S5", name="rescue", kind="bench", argv=[
            "/usr/bin/python3", os.path.join("upstream", "tools", "console-dump.py"),
            "rescue", "--at-prompt", "--ip", a.host,
            "--load-addr", "0x" + LOAD_ADDR,
            "-o", out + "-rescue.json"],
            note="AutoBurning=0, then the load address, then the target IP"),
        dict(id="S5b", name="burnflag", kind="bench", argv=cap + [
            "--out", out + "-ab2", "--send", "DW " + AUTOBURN_ADDR + " 1",
            "--idle", "2", "--seconds", "6"],
            note="ABORT unless word 1 is 00000000. The rescue's echo and this "
                 "word are two sources and C-6 measured them disagreeing"),
        dict(id="S6", name="upload", kind="bench", argv=[
            "/usr/bin/python3", os.path.join("upstream", "tools", "loader-tftp.py"),
            "put", "--host", a.host, "--image", a.image,
            "--filename", a.cell,
            "--rescue-report", out + "-rescue.json",
            "--expect-load", LOAD_ADDR, "--yes"],
            note="lands in RAM. --allow-autoexec is never passed and cannot be"),
        dict(id="S6b", name="staged", kind="bench", argv=cap + [
            "--out", out + "-2a", "--send", "DW " + LOAD_ADDR + " 8",
            "--idle", "2", "--seconds", "8"],
            note="ABORT unless the head words ARE the image S6 sent -- derived "
                 "from the file, not typed. S4's reset re-staged 0x80500000 "
                 "from flash, so the alternative is a real image"),
        dict(id="S7", name="boot", kind="bench", argv=cap + [
            "--out", out + "-boot", "--send", "J " + LOAD_ADDR,
            "--idle", "8", "--seconds", "45"],
            note="--idle 8 because the boot log holds a 4.576 s silence at byte 350"),
        dict(id="S8", name="assert", kind="desk", argv=None,
             note="over S7's capture: the eleven marks, the derived id, a prompt"),
    ]
    return plan


def render_plan(plan, out=sys.stdout):
    print("looprun %s -- the iteration, in order" % VERSION, file=out)
    print("", file=out)
    for s in plan:
        cmd = " ".join(shlex.quote(x) for x in s["argv"]) if s["argv"] else "(in-process)"
        print("  %-3s %-9s %-6s %s" % (s["id"], s["name"], s["kind"], cmd), file=out)
        print("  %-3s %-9s %-6s    %s" % ("", "", "", s["note"]), file=out)
    print("", file=out)


# ------------------------------------------------------------- assertions
def assert_boot(text, want_id, control=None):
    """-> [(ok, id, detail)].  The S8 checks, each one refutable on its own."""
    res = []
    missing = [m for m in BOOT_MARKS if m not in text]
    res.append((not missing, "A1 the eleven boot marks",
                "all present" if not missing else "missing " + ", ".join(missing)))

    # 🔴 A2 is over the marks that are PRESENT, deliberately.  The first version
    # walked all eleven and took a `find` of -1 as out-of-order, so a missing
    # mark turned A1 and A2 red together -- and two checks that always fail
    # together are one check wearing two labels.  `N1` is that case and it is
    # what found it.
    present = [m for m in BOOT_MARKS if m in text]
    idxs = [text.find(m) for m in present]
    order_ok = idxs == sorted(idxs)
    if len(present) < 2:
        # 🔴 With fewer than two marks there is no order to be wrong about, so
        # A2 passes and SAYS it passed on nothing.  A check that is silently
        # vacuous on an empty population is this project's own "a tool
        # reporting 0 is making a claim", one level down.  A1 owns this case.
        odetail = "VACUOUS: %d mark(s) present, A1 owns this" % len(present)
    elif order_ok:
        odetail = "%d present mark(s) in order" % len(present)
    else:
        first = next(present[i] for i in range(1, len(idxs)) if idxs[i] < idxs[i - 1])
        odetail = "out of order at %s" % first
    res.append((order_ok, "A2 and in declaration order", odetail))

    m = ID0_RX.search(text)
    got = m.group(1).lower() if m else None
    if control == "wrong-id":
        want_id = "deadbeef"
    ok = got is not None and want_id is not None and got == want_id
    res.append((ok, "A3 the id the build computed",
                "board printed %s, build computed %s"
                % (got or "<no RLXFW-ID0 line>", want_id or "<unknown>")))

    res.append((PROMPT in text or text.rstrip().endswith("#"),
                "A4 a reachable prompt",
                "found" if (PROMPT in text or text.rstrip().endswith("#"))
                else "neither %r nor a shell prompt" % PROMPT))
    return res


def assert_reset(text):
    ok = WATCHDOG_MARK in text
    return [(ok, "A0 C-8's discriminator after the reset",
             "present" if ok else "ABSENT -- the reset did not happen")]


def assert_autoburn(text):
    """The burn flag read out of memory, rather than believed from an echo.

    🔴 The absent case is a FAILURE and not a skip.  A `DW` that produced no
    read-back line means the read did not happen, and this project's own rule is
    that a tool reporting nothing is making a claim: silence is not a zero.
    """
    rid = "A0b AUTOBURN read back at 0x%s" % AUTOBURN_ADDR
    m = AUTOBURN_RX.search(text)
    if not m:
        return [(False, rid, "NO READ-BACK LINE -- the read did not happen, "
                             "and silence is not a zero")]
    word = m.group(1).upper()
    ok = word == "00000000"
    return [(ok, rid, "00000000 -- the word the burn path reads is zero" if ok
             else "%s -- NOT zero. Nothing is uploaded" % word)]


def dw_words(text, base):
    """-> the words a `DW` printed, in address order, starting at `base`.

    Address-keyed rather than positional, so a capture that lost a line stops
    the run short instead of silently shifting every word by four bytes.
    """
    got = {}
    for m in DW_LINE_RX.finditer(text):
        addr = int(m.group(1), 16)
        for i, w in enumerate(m.group(2).split()):
            got[addr + 4 * i] = w.upper()
    out, k = [], int(base, 16)
    while k in got:
        out.append(got[k])
        k += 4
    return out


def assert_staged(text, image, n=8):
    """What is at 0x80500000 is the image S6 just sent.

    🔴 The expectation is DERIVED from the file that was uploaded, never typed.
    The card's own version of this cell names one word, `0x8050001C`, and names
    the previous image's value beside it so the reading is a contrast; here the
    whole head is compared and the contrast is automatic -- whatever else is at
    that address, it is not this file.
    """
    rid = "A0c the words at 0x%s are the image S6 sent" % LOAD_ADDR
    try:
        with open(image, "rb") as fh:
            raw = fh.read(4 * n)
    except OSError as e:
        return [(False, rid, "cannot read the image, so there is no expectation "
                             "to compare against: %s" % e)]
    want = ["%08X" % int.from_bytes(raw[i * 4:i * 4 + 4], "big")
            for i in range(len(raw) // 4)]
    if not want:
        return [(False, rid, "the image is empty; nothing to derive")]
    got = dw_words(text, LOAD_ADDR)
    if not got:
        return [(False, rid, "NO READ-BACK -- the DW printed nothing at 0x%s, "
                             "and silence is not a match" % LOAD_ADDR)]
    if len(got) < len(want):
        return [(False, rid, "read %d word(s) where the image gives %d -- the "
                             "capture is short, not a match" % (len(got), len(want)))]
    diffs = [i for i in range(len(want)) if got[i] != want[i]]
    if diffs:
        i = diffs[0]
        return [(False, rid, "%d of %d words differ, first at 0x%X: board %s, "
                             "image %s -- NOT the image just uploaded"
                 % (len(diffs), len(want), int(LOAD_ADDR, 16) + 4 * i,
                    got[i], want[i]))]
    return [(True, rid, "%d words, every one derived from the image rather than "
                        "typed" % len(want))]


# ----------------------------------------------------------------- runner
def run_stage(s, cwd, dry, log):
    t0 = time.monotonic()
    if dry:
        return 0, "", time.monotonic() - t0
    p = subprocess.run(s["argv"], cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    txt = p.stdout.decode("utf-8", "replace")
    if log:
        with open(log, "w", encoding="utf-8") as fh:
            fh.write(txt)
    return p.returncode, txt, time.monotonic() - t0


def loop_once(a, out=sys.stdout):
    plan = build_plan(a)
    skip = set(x.strip() for x in (getattr(a, "skip", "") or "").split(",") if x.strip())
    bad = skip - {st["id"] for st in plan}
    if bad:
        raise Refused("--skip names no such stage: %s" % ", ".join(sorted(bad)))
    if "S5b" in skip:
        raise Refused("--skip S5b removes the read-back of the loader's burn "
                      "flag, which RUNSHEET G2/H1a make mandatory before an "
                      "upload. A guard that a flag can switch off is not a "
                      "guard, and this one stands between an upload that lands "
                      "in RAM and one written to the only unit there is")
    # 🔴 S3's input is S2's output, and if S2 is not going to run then nobody
    # computes it.  Refusing here beats letting S3 exit 1 against a placeholder,
    # which is what happened until 2026-09-02 and which reads like a broken
    # rtkimage rather than a missing argument.
    if ("S2" in skip and "S3" not in skip and a.mode in ("desk", "bench")
            and getattr(a, "cell_top", PLACEHOLDER_TOP) == PLACEHOLDER_TOP):
        raise Refused("--skip S2 with no --cell-top: S3 assembles the image out "
                      "of the tree S2 stages, and with S2 skipped nothing "
                      "computes that path -- S3 would run against the literal "
                      "placeholder %r and exit 1. Pass --cell-top <tree>, or "
                      "skip S3 as well" % PLACEHOLDER_TOP)
    if ("S3" not in skip and a.mode in ("desk", "bench")
            and getattr(a, "work", PLACEHOLDER_WORK) == PLACEHOLDER_WORK):
        raise Refused("no --work: S3 would be handed the literal %r, which is a "
                      "legal directory name -- so rtkimage would CREATE it, in "
                      "whatever directory this was run from. A default that "
                      "succeeds in the wrong place is worse than one that "
                      "fails" % PLACEHOLDER_WORK)
    if "S2" in skip and not getattr(a, "recipe_override", None):
        raise Refused("--skip S2 removes the only thing that computes the recipe id, "
                      "so A3 would have nothing to require. Pass --recipe-override "
                      "with the id the staged image was built from, or do not skip S2")

    # ---------------------------------------------------- the image pre-flight
    # 🔴 LOOP-4, 量 2026-09-03: of the three bench inputs, `--image` was the
    # only one with no guard -- and it is consumed by S6, which runs AFTER the
    # reset, the rescue and the burn-flag read-back.  A bad path is therefore
    # discovered with four stages of a power cycle already spent.  Both checks
    # below run before the loop starts, which is the same placement rule
    # console-capture's terminator guard was measured into.
    #
    # 🔴 And the scope is the STAGES, not the mode.  S6 uploads the file and
    # S6b derives its expectation from it; every other stage never opens it.
    # A guard keyed on `--mode bench` alone would refuse `--mode desk`, where
    # `--image` is genuinely unused, and a guard that fires where there is
    # nothing to guard trains its reader to pass it something to shut it up.
    uses_image = (a.mode == "bench"
                  and bool(set(IMAGE_STAGES) - skip))
    img = getattr(a, "image", "") or ""
    want = (getattr(a, "image_sha256", None) or "").strip().lower()
    if uses_image:
        if not img:
            raise Refused(
                "no --image: %s consume it and its default is the empty "
                "string, so `loader-tftp.py put --image ''` would be reached "
                "with S4, S5 and S5b of a power cycle already spent. S3 writes "
                "<work>/<label>/kroot/rtkload/nfjrom and nothing carries that "
                "path here" % "/".join(IMAGE_STAGES))
        if not os.path.isfile(img):
            raise Refused("--image %r is not a regular file" % img)
        try:
            with open(img, "rb") as fh:
                fh.read(1)
        except OSError as exc:
            raise Refused("--image %r cannot be read: %s" % (img, exc))
        if os.path.getsize(img) == 0:
            raise Refused("--image %r is zero bytes" % img)
    # 🔴 RECIPE-1: `RLXFW-ID0` is a digest over `config/` and nothing else, so
    # A3 cannot tell two images built from one frozen `config/` apart -- 量
    # 2026-09-04, `r51quiet` and `r51loud` both compile 229d2983.  S6b's
    # `assert_staged` IS a discriminator, but it derives its expectation from
    # the file `--image` names, so it says "the board holds THIS file", not
    # "the board holds the image the card names".  Pinning the file closes
    # exactly that gap, and it is the one check that runs before the port opens.
    if want:
        if not uses_image:
            raise Refused(
                "--image-sha256 with no stage that reads --image (mode=%s, "
                "skip=%s): a pin on a file nobody opens asserts nothing, and a "
                "check that cannot fail is the shape this repository refuses "
                "on principle" % (a.mode, ",".join(sorted(skip)) or "-"))
        if len(want) != 64 or any(c not in "0123456789abcdef" for c in want):
            raise Refused("--image-sha256 %r is not 64 hex digits" % want)
        got = sha256_of(img)
        if got != want:
            raise Refused(
                "--image %s does not match --image-sha256:\n"
                "        want %s\n        got  %s\n"
                "      The card names one file; this is a different one. "
                "RLXFW-ID0 would not have caught it -- it is a digest over "
                "config/ only." % (img, want, got))
        print("  pre  image     sha256 %s  <- matches the pin" % got, file=out)

    timings, recipe = [], getattr(a, "recipe_override", None) if "S2" in skip else None
    results = []

    for s in plan:
        if s["id"] == "S8":
            break
        if (a.mode == "replay" or (s["kind"] == "bench" and a.mode == "desk")
                or s["id"] in skip):
            why = "--skip" if s["id"] in skip else "mode=" + a.mode
            print("  %-3s %-9s SKIPPED (%s)" % (s["id"], s["name"], why), file=out)
            timings.append((s["id"], None))
            continue
        if a.control == "build-fail" and s["id"] == "S2":
            s = dict(s, argv=s["argv"][:3] + ["--config", "/nonexistent/config"])
        rc, txt, dt = run_stage(s, ROOT, False, None)
        timings.append((s["id"], dt))
        print("  %-3s %-9s rc=%d  %6.2f s" % (s["id"], s["name"], rc, dt), file=out)
        if rc != 0:
            raise StageFailed(s["id"], "exit %d" % rc)
        if s["id"] == "S2":
            m = RECIPE_RX.search(txt)
            if not m:
                raise StageFailed("S2", "the driver printed no recipe= line; "
                                        "S8's assertion has nothing to require")
            recipe = m.group(1)
            print("      recipe=%s  <- S8 will require the board to print this"
                  % recipe, file=out)
            # Chain the staged tree into S3.  Derived from the driver's own
            # `make -C` line, never guessed: if it is not there, S3 has no
            # input and saying so beats assembling from somewhere else.
            t = CELLTOP_RX.search(txt)
            if not t:
                raise StageFailed(
                    "S2", "the driver printed no `make -C <tree>/linux-2.6.30` "
                          "line, so there is nothing to tell S3 which tree to "
                          "assemble from and it would fall back to the "
                          "placeholder")
            top = t.group(1)
            if a.cell_top == PLACEHOLDER_TOP:
                for st in plan:
                    if st["id"] == "S3" and st["argv"]:
                        st["argv"] = [x.replace(PLACEHOLDER_TOP, top)
                                      for x in st["argv"]]
                print("      staged tree=%s  <- S3 assembles from this" % top,
                      file=out)
            # RECIPE-1.  The provenance record the driver just wrote lives in
            # $FWRE_WORK/rebuild/r3-4/out/<cell>.manifest, which the next build
            # of the same cell name overwrites and which no seating commits.
            # Copying it beside this run's own captures is what makes it
            # durable.  Refusing when it is absent follows `make -C` above: a
            # run that produced no provenance is a run that cannot be audited,
            # and finding that out at S2 costs a desk build, not a power cycle.
            mm = MANIFEST_RX.search(txt)
            if not mm:
                raise StageFailed(
                    "S2", "the driver printed no `manifest -> <path>` line, so "
                          "this build left no record of the .config and "
                          "initramfs spec it used -- and neither of those is "
                          "inside RECIPE_ID")
            stem = os.path.join(a.out_dir, a.cell) if a.out_dir else a.cell
            try:
                shutil.copyfile(mm.group(1), stem + ".manifest")
            except OSError as exc:
                raise StageFailed("S2", "manifest %s could not be copied: %s"
                                  % (mm.group(1), exc))
            print("      manifest=%s  -> %s.manifest" % (mm.group(1), stem),
                  file=out)
        if s["id"] in ("S4", "S5b", "S6b"):
            stem = os.path.join(a.out_dir, a.cell) if a.out_dir else a.cell
            suffix, check = {
                "S4": ("-rz.log", assert_reset),
                "S5b": ("-ab2.log", assert_autoburn),
                "S6b": ("-2a.log", lambda t: assert_staged(t, a.image)),
            }[s["id"]]
            ctext = open(stem + suffix, encoding="utf-8", errors="replace").read() \
                if os.path.exists(stem + suffix) else ""
            for ok, rid, detail in check(ctext):
                results.append((ok, rid, detail))
                if not ok:
                    raise StageFailed(s["id"], detail)

    # ---- S8
    if a.mode in ("desk", "replay"):
        if not a.replay_boot:
            raise Refused("--mode %s needs --replay-boot <capture prefix>: "
                          "S8 has to read a boot log, and inventing one would "
                          "make every assertion below vacuous" % a.mode)
        bootlog = a.replay_boot + ".log"
        if a.recipe_override:
            recipe = a.recipe_override
    else:
        bootlog = (os.path.join(a.out_dir, a.cell) if a.out_dir else a.cell) + "-boot.log"
    if not os.path.exists(bootlog):
        raise StageFailed("S8", "no boot capture at %s" % bootlog)
    text = open(bootlog, encoding="utf-8", errors="replace").read()
    if a.control == "truncate-boot":
        text = text[:120]

    t0 = time.monotonic()
    results += assert_boot(text, recipe, a.control)
    timings.append(("S8", time.monotonic() - t0))

    print("", file=out)
    for ok, rid, detail in results:
        print("  %-4s %-38s %s" % ("ok" if ok else "FAIL", rid, detail), file=out)

    machine = sum(t for _i, t in timings if t is not None)
    print("", file=out)
    print("  stage seconds: %s"
          % "  ".join("%s=%s" % (i, "skipped" if t is None else "%.2f" % t)
                      for i, t in timings), file=out)
    print("  MACHINE TOTAL: %.2f s   (S1, the edit, and S8b, the read, are not "
          "this tool's to time -- looptime owns the served loop)" % machine,
          file=out)
    failed = [r for r in results if not r[0]]
    print("", file=out)
    if failed:
        print("RESULT: %d of %d assertion(s) failed" % (len(failed), len(results)),
              file=out)
        return 1
    print("RESULT: the loop closed, %d assertion(s) held, %.2f s of machine time"
          % (len(results), machine), file=out)
    return 0


# --------------------------------------------------------------- self-test
def selftest(out=sys.stdout):
    print("looprun %s --self-test" % VERSION, file=out)
    passed = failed = 0

    def ck(cid, label, expect, got):
        nonlocal passed, failed
        if expect == got:
            print("  ok     %-4s %-50s %s" % (cid, label, got), file=out)
            passed += 1
        else:
            print("  FAIL   %-4s %-50s expected %r, got %r"
                  % (cid, label, expect, got), file=out)
            failed += 1

    good = ("J 80500000\r\n---Jump to address=80500000\r\n"
            + "".join("%s\r\n" % m for m in BOOT_MARKS)
            + "RLXFW-ID0=b1434383\r\n"
            + "rlxfw: init running, RLXFW-R3-RUNG1-OK\r\n"
            + "/bin/sh: can't access tty; job control turned off\r\n#")

    def verdict(text, want, control=None):
        return tuple(ok for ok, _i, _d in assert_boot(text, want, control))

    # ---- P: the positive case
    ck("P1", "a whole boot with the matching id", (True, True, True, True),
       verdict(good, "b1434383"))

    # ---- N: each assertion must be able to fail ALONE.  A control set where
    # one broken input trips every check cannot tell which check is load-bearing.
    ck("N1", "one boot mark missing trips A1 and only A1",
       (False, True, True, True),
       verdict(good.replace("RLXFW-B07\r\n", ""), "b1434383"))
    ck("N2", "two marks swapped trips A2 and only A2",
       (True, False, True, True),
       verdict(good.replace("RLXFW-B03\r\nRLXFW-B04\r\n",
                            "RLXFW-B04\r\nRLXFW-B03\r\n"), "b1434383"))
    ck("N3", "the id line absent trips A3 and only A3",
       (True, True, False, True),
       verdict(good.replace("RLXFW-ID0=b1434383\r\n", ""), "b1434383"))
    ck("N4", "🔴 a STALE image: every mark right, the id from another build",
       (True, True, False, True), verdict(good, "d31f60bd"))
    # 🔴 The board prints UPPER case -- `rlxfw_puts_hex`'s own contract is
    # "eight upper-case hex digits" -- and the fixture above is lower case, so
    # until this case existed the suite exercised a form the device never
    # sends. The comparison folds case; that is now asserted rather than
    # assumed.
    ck("N4b", "🔴 the board's UPPER-case form is accepted",
       (True, True, True, True),
       verdict(good.replace("RLXFW-ID0=b1434383", "RLXFW-ID0=B1434383"), "b1434383"))
    ck("N4c", "and upper case does not make a WRONG id match",
       (True, True, False, True),
       verdict(good.replace("RLXFW-ID0=b1434383", "RLXFW-ID0=B1434383"), "d31f60bd"))
    ck("N5", "no prompt trips A4 and only A4", (True, True, True, False),
       verdict(good.rsplit("\r\n", 1)[0], "b1434383"))
    ck("N6", "the build printed no recipe: A3 fails rather than passing",
       (True, True, False, True), verdict(good, None))

    # ---- the vendor's own firmware must not satisfy any of this
    vendor = ("J 80500000\r\nLinux version 2.6.30.9 (admin@office.hopeiot) #1526\r\n"
              "init started: BusyBox v1.13.4\r\n#")
    ck("N7", "🔴 the VENDOR's boot text fails A1, A3, and reaches a prompt",
       (False, True, False, True), verdict(vendor, "b1434383"))
    ck("N7b", "and A2's pass on it is reported as VACUOUS, not as a pass", True,
       "VACUOUS" in assert_boot(vendor, "b1434383")[1][2])

    # ---- C-8 on the reset stage
    ck("C1", "the reset discriminator present",
       [True], [ok for ok, _i, _d in assert_reset("ramSize: 32M\r\n" + WATCHDOG_MARK)])
    ck("C2", "a COLD boot's single space is not the discriminator",
       [False], [ok for ok, _i, _d in assert_reset("ramSize: 32M\r\n \r\n")])

    # ---- C3..C5 on the burn flag.  Three outcomes and not two, because the
    # third -- no read-back line at all -- is the one a missing capture, a dead
    # port or a `DW` the loader did not understand all produce, and it must not
    # be quiet.
    def ab(t):
        return [ok for ok, _i, _d in assert_autoburn(t)]
    ck("C3", "the burn flag read back as zero passes", [True],
       ab("DW 8040D4A0 1\r\n8040D4A0:\t00000000\r\n<RealTek>"))
    ck("C4", "🔴 00000001 -- the power-on default -- FAILS before the upload",
       [False], ab("DW 8040D4A0 1\r\n8040D4A0:\t00000001\r\n<RealTek>"))
    ck("C5", "🔴 no read-back line at all FAILS: silence is not a zero",
       [False], ab("DW 8040D4A0 1\r\nUnknown command !\r\n<RealTek>"))

    # ---- C6..C9 on what is staged at 0x80500000.  The image is synthetic and
    # built here, so these run on a CI box with no $FWRE_WORK -- and the
    # expectation is derived from the bytes on both sides, which is the whole
    # claim this assertion makes.
    with tempfile.TemporaryDirectory() as d:
        img = os.path.join(d, "synthetic.bin")
        head = bytes(range(32))          # 00010203 04050607 ... 1C1D1E1F
        open(img, "wb").write(head + b"\xaa" * 64)
        real = ("DW 80500000 8\r\n"
                "80500000:\t00010203\t04050607\t08090A0B\t0C0D0E0F\r\n"
                "80500010:\t10111213\t14151617\t18191A1B\t1C1D1E1F\r\n<RealTek>")
        other = real.replace("1C1D1E1F", "2610B400")     # a different image
        short = ("DW 80500000 8\r\n"
                 "80500000:\t00010203\t04050607\t08090A0B\t0C0D0E0F\r\n<RealTek>")

        def st(t, i=img):
            return [ok for ok, _i, _d in assert_staged(t, i)]
        ck("C6", "the staged head matches the image byte for byte", [True], st(real))
        ck("C7", "🔴 one word different -- another image at that address -- FAILS",
           [False], st(other))
        ck("C8", "🔴 a capture that lost a line FAILS rather than matching four "
                 "of eight", [False], st(short))
        ck("C9", "🔴 an unreadable image FAILS: no file, no expectation, and "
                 "that is not a pass", [False], st(real, os.path.join(d, "gone")))
        # C10 is C6's negative control on the PARSER: the same words under a
        # different address label must not satisfy a read at 0x80500000.
        ck("C10", "🔴 the right words at the WRONG address do not match", [False],
           st(real.replace("80500000:", "80A00000:").replace("80500010:",
                                                             "80A00010:")))

    # ---- the plan renders, and it renders the same list the runner walks
    class A:
        cell = "L1"; out_dir = "bench/2026-09-02"; port = DEFAULT_PORT
        host = DEFAULT_HOST; config = "cfg"; initramfs = "spec"; jobs = 4
        variant = "quiet"
        image = "img.bin"; vmlinux = None; cell_top = "top"
        label = "rlxfw"; work = "work"
    plan = build_plan(A)
    # 🔴 Seven and four, both re-derived after this case failed on 8 and 3.
    # S1 -- the edit -- is not in the plan because no instrument here can time
    # it, and S4/S5/S6/S7 all need the board; the docstring's own stage table
    # is what these two numbers are checked against.
    ck("R1", "the plan has all nine stages", 9, len(plan))
    ck("R2", "six of them need the board", 6,
       sum(1 for s in plan if s["kind"] == "bench"))
    # 🔴 Order is the whole point of both guards: the burn flag has to be read
    # AFTER the rescue that clears it and BEFORE the upload it guards, and the
    # staged head AFTER the upload and BEFORE the jump.  A stage list that holds
    # all five and orders them wrongly reads as checked and is not.
    ids = [s["id"] for s in plan]
    ck("R2b", "🔴 the two guards each sit between the stages they guard", True,
       ids.index("S5") < ids.index("S5b") < ids.index("S6") < ids.index("S6b")
       < ids.index("S7"))
    joined = " ".join(" ".join(s["argv"] or []) for s in plan)
    ck("R3", "🔴 no stage can pass --allow-autoexec", False,
       "--allow-autoexec" in joined)
    ck("R4", "every capture stage carries a terminator", True,
       all(("--idle" in (s["argv"] or []) or "--seconds" in (s["argv"] or []))
           for s in plan if s["argv"] and "console-capture.py" in " ".join(s["argv"])))
    ck("R5", "the reset targets BFC00000 and the boot 80500000", True,
       ("J " + RESET_TARGET) in joined and ("J " + LOAD_ADDR) in joined)

    # 🔴 R6 exists because the first version of this file rendered S3 as
    # `rtkimage.py build --kernel X --out Y` and that program has neither
    # flag -- it takes --cell/--vmlinux/--label/--work.  `cardcheck commands`
    # asks whether a CARD's commands are invocable and nothing asked it of
    # the tool that renders them, while `--mode plan` is supposed to BE the
    # card's command column.  A plan whose commands do not run is worse than
    # no plan: it reads as checked.
    unknown = []
    for st in plan:
        if not st["argv"]:
            continue
        prog = next((x for x in st["argv"] if x.startswith("tools/")
                     or x.startswith("tools\\")), None)
        if not prog:
            continue
        src = os.path.join(ROOT, prog)
        if not os.path.isfile(src):
            unknown.append((st["id"], prog, "no such file"))
            continue
        body = open(src, encoding="utf-8", errors="replace").read()
        for tok in st["argv"]:
            if tok.startswith("--") and tok not in body:
                unknown.append((st["id"], prog, tok))
    ck("R6", "🔴 every flag the plan renders exists in the tool it is given to",
       [], unknown)

    # ---- M: the controls the gate asks for, end to end through loop_once
    with tempfile.TemporaryDirectory() as d:
        pre = os.path.join(d, "cap")
        open(pre + ".log", "w", encoding="utf-8").write(good)

        class B:
            cell = "L1"; out_dir = None; port = DEFAULT_PORT; host = DEFAULT_HOST
            config = "cfg"; initramfs = "spec"; jobs = 4; image = "img.bin"
            vmlinux = None; cell_top = "top"; label = "rlxfw"; work = "work"
            mode = "replay"; replay_boot = pre; skip = ""
            recipe_override = "b1434383"; control = None
        devnull = open(os.devnull, "w")
        ck("M0", "🔴 unmutated, mode=replay: the loop reports 0", 0,
           loop_once(B, out=devnull))
        B.control = "wrong-id"
        ck("M1", "a deliberately wrong id turns it red", 1, loop_once(B, out=devnull))
        B.control = "truncate-boot"
        ck("M2", "a truncated boot log turns it red", 1, loop_once(B, out=devnull))
        B.control = None
        B.recipe_override = None
        ck("M3", "no recipe at all turns it red", 1, loop_once(B, out=devnull))
        B.recipe_override = "b1434383"
        B.replay_boot = None
        try:
            loop_once(B, out=devnull)
            got = "no refusal"
        except Refused:
            got = "refused"
        ck("M4", "no --replay-boot is REFUSED, not vacuously green",
           "refused", got)

        B.replay_boot = pre
        B.skip = "S9"
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused:
            got = "refused"
        ck("M5", "--skip naming a stage that does not exist is refused",
           "refused", got)

        B.skip = "S2"
        B.recipe_override = None
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused:
            got = "refused"
        ck("M6", "🔴 --skip S2 without --recipe-override is refused",
           "refused", got)

        B.skip = "S5b"
        B.recipe_override = "b1434383"
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused:
            got = "refused"
        ck("M7", "🔴 --skip S5b is refused: a guard behind a flag is not a guard",
           "refused", got)
        # M7b is M7's negative control.  A refusal that fires on every --skip
        # would pass M7 while proving nothing, so one skip that IS allowed has
        # to go through the same path and come out the other side.
        B.skip = "S3"
        try:
            rc7 = loop_once(B, out=devnull); got = "rc=%d" % rc7
        except Refused:
            got = "refused"
        ck("M7b", "and --skip S3, which IS allowed, is not refused", "rc=0", got)
        B.skip = ""
        B.recipe_override = "b1434383"

        # ---- M8: --iterations is checked in main(), not in loop_once, so the
        # only control that can reach it drives the program.  Two runs, one
        # flag apart, and the second is the negative control: a refusal that
        # fired on every invocation would pass M8 and prove nothing.
        base = [sys.executable, os.path.join(ROOT, "tools", "looprun.py"),
                "--mode", "replay", "--replay-boot", pre,
                "--recipe-override", "b1434383"]

        def rc_of(extra):
            return subprocess.run(base + extra, cwd=ROOT, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,
                                  stdin=subprocess.DEVNULL).returncode
        ck("M8", "🔴 --iterations 2 is REFUSED (exit 2), not accepted and then "
                 "failed on a filename", 2, rc_of(["--iterations", "2"]))
        ck("M8b", "and --iterations 1, the only honest value, still runs", 0,
           rc_of(["--iterations", "1"]))

        # ---- M9: S3's input is S2's output.  Until 2026-09-02 nothing carried
        # it, and S3 exited 1 against a placeholder -- which looks like a broken
        # rtkimage and not a missing argument.  --mode desk runs S3 for real, so
        # this is the mode that can see it.
        B.mode = "desk"
        B.skip = "S2"
        # 🔴 The fixture has to carry the PLACEHOLDER, not a real path: with
        # `cell_top = "top"` this case never reaches the branch it is named
        # after, and the first run of M9 proved that by failing at S3 instead
        # of being refused.
        B.cell_top = PLACEHOLDER_TOP
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused:
            got = "refused"
        except StageFailed:
            got = "StageFailed -- S3 ran against the placeholder"
        ck("M9", "🔴 --skip S2 with no --cell-top is REFUSED, not left to fail "
                 "at S3", "refused", got)
        B.skip = "S2,S3"
        try:
            rc9 = loop_once(B, out=devnull); got = "rc=%d" % rc9
        except Refused:
            got = "refused"
        ck("M9b", "and --skip S2,S3 -- block 7's own invocation, placeholder "
                  "and all -- is not refused", "rc=0", got)

        # ---- M10: the OTHER placeholder, and it is worse because it succeeds.
        # `<rtkimage work dir>` is a legal directory name, so the default does
        # not fail -- it creates that directory wherever the run started.
        B.skip = ""
        B.work = PLACEHOLDER_WORK
        B.cell_top = "top"
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except (Refused, StageFailed) as exc:
            got = "refused" if isinstance(exc, Refused) else "StageFailed"
        ck("M10", "🔴 the --work placeholder is REFUSED before S3 can create a "
                  "directory named after it", "refused", got)
        B.work = "work"
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused:
            got = "refused"
        except StageFailed:
            got = "StageFailed"
        ck("M10b", "and a real --work is not refused (it reaches S2/S3)",
           "StageFailed", got)
        B.mode = "replay"
        B.skip = ""
        B.cell_top = "top"
        B.work = "work"

        # ---- M11: LOOP-4.  `--image` is read by S6/S6b, which sit AFTER the
        # reset, the rescue and the burn-flag read-back, so an unusable value
        # is found with four stages of a power cycle already spent.  The three
        # cases pin the guard's SCOPE, one edge each: it must fire where the
        # file is read, and stay silent in both places where it is not.
        def outcome(**kw):
            for k, v in kw.items():
                setattr(B, k, v)
            try:
                rc = loop_once(B, out=devnull)
                return "rc=%d" % rc
            except Refused:
                return "refused"
            except StageFailed as exc:
                return "StageFailed@" + exc.sid

        ck("M11", "🔴 --mode bench with no --image is REFUSED before any stage "
                  "runs, not at S6 with the power cycle spent",
           "refused", outcome(mode="bench", image="", skip="", image_sha256=None))
        ck("M11b", "and --mode desk with no --image is NOT refused -- desk "
                   "skips S6/S6b, so there is nothing to guard",
           "StageFailed@S2", outcome(mode="desk", image=""))
        ck("M11c", "and --mode bench --skip S6,S6b is NOT refused either: the "
                   "guard keys on the stages that read the file, not the mode "
                   "-- and S2 failing first is why the board is never touched",
           "StageFailed@S2", outcome(mode="bench", skip="S6,S6b", image=""))

        # ---- M12: RECIPE-1.  A3 compares the id the board printed against the
        # id the build computed, and RECIPE_ID is a digest over config/ ONLY --
        # 量 2026-09-04, r51quiet and r51loud both compile 229d2983 from
        # different .config files.  S6b's assert_staged derives its expectation
        # from the file --image names, so it cannot notice that the file is the
        # wrong one.  Pinning the file is the only check that can, and it is
        # the only one that runs before the port opens.
        realimg = os.path.join(d, "image.bin")
        open(realimg, "wb").write(b"\x3c\x10\x80\x60" * 64)
        good_sha = sha256_of(realimg)
        bad_sha = "0" * 64
        ck("M12", "🔴 a wrong --image-sha256 is REFUSED before any stage",
           "refused", outcome(mode="bench", skip="", image=realimg,
                              image_sha256=bad_sha))
        ck("M12b", "and the right one is not -- the run proceeds to S2",
           "StageFailed@S2", outcome(image_sha256=good_sha))
        ck("M12c", "a malformed --image-sha256 is refused rather than compared "
                   "and silently never equal",
           "refused", outcome(image_sha256="deadbeef"))
        ck("M13", "🔴 --image-sha256 where NOTHING reads --image is REFUSED: a "
                  "pin on a file nobody opens is a check that cannot fail",
           "refused", outcome(mode="desk", image_sha256=good_sha))

        # ---- M14: which refusal wins.  `--skip S5b` removes the burn-flag
        # read-back and `--image ''` wastes a power cycle; both are wrong at
        # once here.  The SAFETY refusal has to be the one reported, because it
        # is the one standing between an upload in RAM and one written to the
        # only unit there is.  Nothing but this case pins the order.
        B.mode = "bench"; B.image = ""; B.image_sha256 = None
        B.skip = "S5b"
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused as exc:
            got = "S5b" if "S5b" in str(exc) else "image"
        except StageFailed:
            got = "StageFailed"
        ck("M14", "🔴 with --skip S5b AND a bad --image, the S5b safety refusal "
                  "is the one reported", "S5b", got)

        B.mode = "replay"; B.skip = ""; B.image = "img.bin"; B.image_sha256 = None

    # ---- C11/C12: the chaining itself, on the driver's real output shape
    real = ("== i3: applied 16 declared row(s) from config/rlxfw-marks.tsv\n"
            "== i3: make -C /home/key/fwre-work/rebuild/r3-4/cells/i3/top/"
            "linux-2.6.30 -j4 vmlinux CFLAGS_KERNEL=-fno-if-conversion\n"
            "== OUTPUT 3968240 bytes  sha256 c788348d7b7f9886\n")
    mt = CELLTOP_RX.search(real)
    ck("C11", "the staged tree is read out of the driver's own `make -C` line",
       "/home/key/fwre-work/rebuild/r3-4/cells/i3/top", mt.group(1) if mt else None)
    ck("C12", "🔴 and a driver run that printed no such line yields nothing, so "
              "S2 raises rather than S3 assembling from somewhere else",
       None, CELLTOP_RX.search(real.replace("make -C", "MAKE -c")))

    # C13/C14: the manifest line, same shape as C11/C12 and for the same
    # reason -- the path is read out of the driver's own output, never guessed.
    real2 = real + "== i3: manifest -> /home/key/fwre-work/rebuild/r3-4/out/i3.manifest\n"
    m13 = MANIFEST_RX.search(real2)
    ck("C13", "the provenance record's path is read out of the driver's own "
              "`manifest ->` line", "/home/key/fwre-work/rebuild/r3-4/out/i3.manifest",
       m13.group(1) if m13 else None)
    ck("C14", "🔴 and a driver run that printed no such line yields nothing, so "
              "S2 raises rather than the build leaving no provenance",
       None, MANIFEST_RX.search(real))

    print("", file=out)
    print("RESULT: %d passed, %d failed" % (passed, failed), file=out)
    return 0 if failed == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="one edit->result iteration (R4-3)")
    ap.add_argument("--mode", choices=["plan", "replay", "desk", "bench"],
                    default="plan",
                    help="plan: print the commands and run none. replay: run no\nstage at all and assert over --replay-boot -- this is what the\nself-test drives. desk: run S2/S3 for real, replay the boot.\nbench: all of it, against a live board")
    ap.add_argument("--cell", default="L1")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--port", default=DEFAULT_PORT)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--config", default="")
    ap.add_argument("--variant", default="quiet",
                    help="CFG-1: the config/rlxfw-kernel.delta variant to "
                         "derive .config from when --config is not given")
    ap.add_argument("--initramfs", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--image", default="")
    ap.add_argument("--image-sha256", default=None,
                    help="the sha256 the card names for --image. RLXFW-ID0 is "
                         "a digest over config/ only, so it cannot tell two "
                         "images built from one frozen config/ apart; this can")
    ap.add_argument("--vmlinux", default=None)
    ap.add_argument("--cell-top", default=PLACEHOLDER_TOP,
                    help="the staged tree rtkimage builds against")
    ap.add_argument("--label", default="rlxfw")
    ap.add_argument("--work", default=PLACEHOLDER_WORK)
    ap.add_argument("--replay-boot", default=None,
                    help="mode=desk: a committed capture PREFIX to assert over")
    ap.add_argument("--recipe-override", default=None,
                    help="mode=desk: the id S8 should require, when S2 did not run")
    ap.add_argument("--skip", default="",
                    help="comma-separated stage ids not to run, e.g. S2,S3 when the\nimage is already staged. Skipping S2 REQUIRES --recipe-override")
    ap.add_argument("--control", default=None,
                    choices=["wrong-id", "truncate-boot", "build-fail"],
                    help="deliberately break one input; the run must go red")
    ap.add_argument("--iterations", type=int, default=1,
                    help="run the loop N times. Unattended means nobody is "
                         "watching, so this is bounded and so is --budget-seconds")
    ap.add_argument("--budget-seconds", type=float, default=1800.0,
                    help="stop starting new iterations once this much wall "
                         "clock has gone. It does not interrupt one in flight")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    try:
        if a.self_test:
            return selftest()
        if a.mode == "plan":
            render_plan(build_plan(a))
            return 0
        if a.iterations < 1:
            raise Refused("--iterations must be at least 1")
        # 🔴 讀 2026-09-02, at the bench, settled without spending the live
        # board.  S4 is `J BFC00000`, a LOADER command, and iteration 1 ends
        # with Linux running and the loader gone -- so iteration 2 sends a
        # loader command to a busybox shell.  It fails earlier and worse than
        # that: every capture stage renders --out from --cell with no iteration
        # index and console-capture.py refuses to overwrite, so iteration 2
        # dies on *the output file exists*, before it reaches the reason that
        # matters.  A run that fails on a filename teaches nothing about the
        # loop.  Refusing is honest; accepting a number this cannot honour is
        # the same defect as a plan rendering flags a tool does not have.
        if a.iterations > 1:
            raise Refused(
                "--iterations %d: this loop cannot repeat yet and will not "
                "pretend to. S4 is `J %s`, a LOADER command, and iteration 1 "
                "ends with the kernel running and the loader gone; and every "
                "capture stage renders --out from --cell with no iteration "
                "index, so iteration 2 would die on an existing output file "
                "before it reached that. Making it iterate needs a way back "
                "from Linux to the loader and per-iteration names, which is a "
                "design decision and not a flag" % (a.iterations, RESET_TARGET))
        t0 = time.monotonic()
        worst = 0
        for n in range(1, a.iterations + 1):
            spent = time.monotonic() - t0
            if n > 1 and spent >= a.budget_seconds:
                print("looprun: budget of %.0f s reached after %d iteration(s); "
                      "not starting another" % (a.budget_seconds, n - 1))
                break
            if a.iterations > 1:
                print("\n=== iteration %d of %d   (%.1f s spent)" % (n, a.iterations, spent))
            rc = loop_once(a)
            worst = max(worst, rc)
            if rc != 0:
                print("looprun: iteration %d failed; stopping rather than "
                      "averaging a red run into a green summary" % n)
                break
        return worst
    except Refused as exc:
        print("looprun: %s" % exc, file=sys.stderr)
        return 2
    except StageFailed as exc:
        print("looprun: STOPPED at %s -- %s" % (exc.sid, exc.why), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
