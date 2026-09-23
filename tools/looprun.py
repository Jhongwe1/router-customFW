#!/usr/bin/env python3
"""looprun -- one `edit -> result` iteration as a single command, with controls.

`R4-3`, `D3` and `D4`.  The gate asks for a loop that "runs unattended and
reports a number", and for "a deliberately broken input turns it red".  Those
are two requirements and the second is the one that makes the first worth having.

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
    S2  build      tools/rlxfw-kbuild.sh                     desk   once
    S3  assemble   tools/rtkimage.py build                   desk   once
    S4  reset      console-capture --send 'J BFC00000'       bench  round 1
                   console-capture --send 'busybox reboot -f'       rounds 2..N
    S5  rescue     upstream/tools/console-dump.py rescue     bench  every round
    S5b burnflag   console-capture --send 'DW 8040D4A0 1'   bench  every round
    S5c hostlink   ip route get / ping / ip neigh  (in-process) bench
    S6  upload     upstream/tools/loader-tftp.py put         bench  every round
    S6b staged     console-capture --send 'DW 80500000 8'    bench  every round
    S7  boot       console-capture --send 'J 80500000'       bench  every round
    S8  assert     over S7's capture                         desk   every round
    S9  dwell      until S7's end + --dwell-seconds (1.3)    bench  every round, if > 0

ROUNDS: N BOOTS ON ONE POWER PRESS (LOOP-3, 1.2)
------------------------------------------------
`--iterations N` runs S2/S3 once and then N rounds of S4..S8.  Round 1 starts
at the loader prompt, so its S4 is `J BFC00000`; every later round starts in
rlxfw's shell, where the way back is `busybox reboot -f` -- a watchdog bite,
`<RealTek>` 2.407 s later (SPEC.md `FW-37`).  After ANY reset the loader
re-stages 0x80500000 from flash (`LDR-22`), so every round uploads again and
every round reads the burn flag back.  `--skip S4` skips ROUND 1's reset only
-- the card that starts from a cold ESC catch -- and no other per-round stage
may be skipped when N >= 2.  With N >= 2 a round's artefacts carry `-rNN`;
with N == 1 every name is what it always was.  In `--mode bench` the stage
times go to `<stem>.stages.tsv`, rewritten whole after every stage -- since 1.3
on CLOCK_MONOTONIC_RAW, under a header naming it and the boot_id it restarts with.
Until 1.2 `--iterations` above 1 was refused (`M8`): S4 was a loader command
sent into the shell iteration 1 left, and no name carried an iteration index.

Every S4 and S7 ends ON an event -- `--until` -- and not on a silence
(`TERM-1`, 1.2); their `--esc-after` and `--seconds` are caps.

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
* 🔴 and S4's capture must END at the loader's `<RealTek>` (`A0a`, 1.2).  The
  watchdog line is printed on a reset whose ESC window was missed too, and then
  the loader boots the VENDOR's firmware and S5 types into it --
  `bench/2026-08-31c/K-J` is that capture, and `A0` passes on it;
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
  round stops the rest rather than being averaged into a green summary;
* 🔴 no stage here may write flash. `S6` is `loader-tftp put`, which lands in
  RAM, and this file refuses to pass `--allow-autoexec` under any flag.

Run:  tools/looprun.py --mode plan   --cell L1
      tools/looprun.py --mode plan   --cell L1 --iterations 3 --skip S2,S3,S4 \\
                       --recipe-override b1434383 --dwell-seconds 2
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
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = "1.3"
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

# ------------------------------------------------------ rounds (LOOP-3, 1.2)
#: the stages that run once, before round 1, and the stages that ARE a round.
ONCE_STAGES = ("S2", "S3")
ROUND_STAGES = ("S4", "S5", "S5b", "S5c", "S6", "S6b", "S7", "S8")
#: `-rNN` carries two digits.
MAX_ROUNDS = 99
# The way back from rlxfw's shell to the loader.  量 bench/2026-09-06b/K1-Z2: a
# watchdog bite, `<RealTek>` 2.407 s after the command (SPEC.md FW-37).  Plain
# `reboot` signals PID 1 -- a shell script on this image -- and resets nothing.
REBOOT_CMD = "busybox reboot -f"

# ------------------------------------------------- terminators (TERM-1, 1.2)
# 🔴 S4 ends ON the loader's prompt; --esc-after and --seconds stay, as the caps
# a reset that never reaches it still pays.  Until 1.2 round 1's S4 was
# `--esc-after 10 --esc-period 0.002 --idle 3 --seconds 25`, and the 58
# committed `-rz` captures that hold C-8's line lasted 13.13-13.19 s, ~10.6 s
# of it budget (notes/dev-loop.md § 10.2).  量, read 2026-09-23 out of the 82
# committed captures that sent `J BFC00000` and hold C-8's line: the first
# `<RealTek>` after it arrived 2.12-2.41 s into the capture.
S4_J_TERM = ["--esc-after", "10", "--esc-period", "0.002",
             "--until", PROMPT, "--seconds", "25"]
# Rounds 2..N: the terminators of the 25 committed `busybox reboot -f` cells
# that used this exact shape, every one of them ended on --until
# (bench/2026-09-10/C1-RB: 2.76 s).  量 over the 69 committed captures that sent
# it and hold C-8's line: the first `<RealTek>` 2.22-2.57 s into the capture.
S4_RB_TERM = ["--esc-after", "20", "--esc-period", "0.002",
              "--until", PROMPT, "--seconds", "40"]
# S7 ends ON the shell's prompt.  /init (config/rlxfw-init.sh) prints `rlxfw: init
# running, ...` and execs /bin/sh, which prints `/bin/sh: can't access tty; job
# control turned off`, CRLF, `# `.  量, read 2026-09-23 over every committed capture
# holding `rlxfw: init running` (138, all `J 80500000`): this matches in 138 of 138,
# and in every one the match ends on the capture's LAST byte -- so ending there loses
# nothing a committed boot printed.  The prompt is INSIDE the pattern because
# console-capture drains only 50 ms after a match and S8's A4 reads it.
# 🔴 No backslash, on purpose: `--mode plan` renders this into the card's
# command column, and a quoted heredoc from the Bash tool loses a backslash
# level (CLAUDE.md) -- `\r?\n` would arrive as `r?n`, which never matches, and
# every boot would silently pay the whole cap.
DEFAULT_BOOT_UNTIL = "job control turned off[^#]{1,2}# "
# The cap, paid only when the pattern never arrives.  Over the same 138 boots `J` ->
# the prompt's last byte took 6.99-12.57 s, so 45 leaves 32.4 s above the slowest.
# Until 1.2 S7 was `--idle 8 --seconds 45`, the 8 from a 4.576 s silence at byte 350
# of `quietm` (block 7's card): a boot holds silences, and --idle ends it inside one.
DEFAULT_BOOT_SECONDS = 45.0
# What the loader prints for `J 80500000` before the kernel prints a byte (讀,
# every committed `*-boot.log`).  console-capture arms --until as the command
# goes out, so this is inside the window: a pattern that matches here ends S7
# before the kernel has started -- console-capture's own case N36.
S7_ECHO = "J %s\n\r---Jump to address=%s\n\r" % (LOAD_ADDR, LOAD_ADDR)


class Refused(Exception):
    pass


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class StageFailed(Exception):
    def __init__(self, sid, why, rnd=None):
        super().__init__("%s: %s" % (sid, why))
        # `rnd` is the round it stopped in; the runner fills it in when the
        # raise site did not know it.
        self.sid, self.why, self.rnd = sid, why, rnd


# ------------------------------------------------- where a stage's files go
def rounds(a):
    """`--iterations`, read so that the self-test's older fixtures, which do
    not carry it, mean one round.  0 stays 0: `check_shape` refuses it."""
    n = getattr(a, "iterations", None)
    return 1 if n is None else n


def stem(a, rnd=None):
    """The prefix every stage artefact of this run is built on.

    One owner.  Before 1.1 this expression was written out at four call sites
    and the attempt suffix would have had to be added to each.

    🔴 The attempt suffix is what makes a failed run retryable.  量 2026-09-08
    (`notes/dev-loop.md` § 15.2): a retry died at `S5b` in 0.06 s -- too fast
    to have opened the port -- because `console-capture.py:368` correctly
    refuses to overwrite an existing capture and `C1-ab2` was still on disk
    from the first attempt.  **At a bench the natural response to that refusal
    is `--force`, and that is exactly the write the guard exists to prevent**:
    the first attempt's capture held a real burn-flag reading
    (`8040D4A0: 00000000`) that `--force` would have destroyed.

    ⚠️ It also fixes the CONSEQUENCE of the two tools disagreeing about
    overwriting -- `console-dump.py` (S5) silently rewrote `C1-rescue.json`
    on that retry while `console-capture.py` (S5b) refused -- without changing
    either tool: at attempt 2 they write to a different name and neither can
    reach attempt 1's files.

    🔴 LOOP-3, 1.2: with `--iterations` N >= 2, round `rnd`'s artefacts carry
    `-rNN` after all of the above (`<cell>-att2-r01-rz.log`), because every
    round runs the same stages and console-capture refuses to overwrite.  With
    N == 1 no index is added: every committed card and capture uses the plain
    names, and `L3` holds that against one of them.
    """
    base = os.path.join(a.out_dir, a.cell) if a.out_dir else a.cell
    n = getattr(a, "attempt", 1) or 1
    s = base if n == 1 else "%s-att%d" % (base, n)
    if rnd is not None and rounds(a) >= 2:
        s = "%s-r%02d" % (s, rnd)
    return s


def stages_path(a):
    """LOOP-3: the file the stage times go to -- one per invocation, so it
    carries the attempt and never a round."""
    return stem(a) + ".stages.tsv"


def parse_skip(a):
    return set(x.strip() for x in (getattr(a, "skip", "") or "").split(",")
               if x.strip())


def skipped_in(sid, rnd, skip, n):
    """Is stage `sid` skipped in round `rnd` (0 = S2/S3, which run once)?

    🔴 With N >= 2, `--skip S4` is ROUND 1's reset only.  Round 1 may start
    at a loader prompt someone else caught -- a cold ESC catch -- but every
    later round starts in rlxfw's shell, and `busybox reboot -f` is the only
    way back from there.  `check_shape` refuses every other per-round id when
    N >= 2, so S4 is the one case this has to know about.
    """
    if sid not in skip:
        return False
    if n >= 2 and sid == "S4":
        return rnd == 1
    return True


#: Every artefact a bench run creates, as suffixes on stem(a).  Used by the
#: pre-flight so a collision is a refusal BEFORE the board is touched rather
#: than a stage failure after four stages have run.
BENCH_ARTEFACTS = {
    "S4": ("-rz.log", "-rz.timing", "-rz.meta.json"),
    "S5": ("-rescue.json",),
    "S5b": ("-ab2.log", "-ab2.timing", "-ab2.meta.json"),
    "S6b": ("-2a.log", "-2a.timing", "-2a.meta.json"),
    "S7": ("-boot.log", "-boot.timing", "-boot.meta.json"),
}


def preflight_artefacts(a, skip):
    """[] or a list of paths that already exist.

    A run that is going to collide collides at the FIRST capture, which on a
    bench is after the reset and the rescue have already been spent.  Reading
    the whole set up front turns that into one refusal before power is
    touched, naming the flag that resolves it.

    LOOP-3, 1.2: EVERY round's names, and the stages file.  A clash in round
    2 found at round 2 is found with round 1's boot already spent.
    """
    clash = []
    n = rounds(a)
    for rnd in range(1, n + 1):
        for sid, suffixes in sorted(BENCH_ARTEFACTS.items()):
            if skipped_in(sid, rnd, skip, n):
                continue
            for suf in suffixes:
                p = stem(a, rnd) + suf
                if os.path.exists(p):
                    clash.append(p)
    if os.path.exists(stages_path(a)):
        clash.append(stages_path(a))
    return clash


def check_shape(a, skip):
    """The refusals that read nothing but the arguments.  1.2.

    They run in every mode, `plan` included: `--mode plan` IS the card's
    command column, so a run bench mode would refuse must not render.  Until
    1.2 `plan` returned before any refusal ran at all.
    """
    n = rounds(a)
    check_dwell(a, skip)            # 1.3: --dwell-seconds and the skips it forbids
    if n < 1:
        raise Refused("--iterations must be at least 1")
    if n > MAX_ROUNDS:
        raise Refused("--iterations %d: a round's names carry two digits "
                      "(-r01..-r%02d), so %d is the most one invocation takes"
                      % (n, MAX_ROUNDS, MAX_ROUNDS))
    bad = skip - set(ONCE_STAGES) - set(ROUND_STAGES)
    if bad:
        raise Refused("--skip names no such stage: %s" % ", ".join(sorted(bad)))
    if "S5b" in skip:
        raise Refused("--skip S5b removes the read-back of the loader's burn "
                      "flag, which RUNSHEET G2/H1a make mandatory before an "
                      "upload. A guard that a flag can switch off is not a "
                      "guard, and this one stands between an upload that lands "
                      "in RAM and one written to the only unit there is")
    # 🔴 Until 1.2 `--skip S8` was accepted and did nothing -- the stage loop
    # broke at S8 and ran its assertions regardless.  `notes/dev-loop.md` § 18
    # reasons from it as if it worked.  The plan now prints what --skip
    # removes, so a flag it cannot honour is refused rather than rendered.
    if "S8" in skip:
        raise Refused("--skip S8 would switch off the assertion, and a run with "
                      "its assertion off is an upload, not an iteration. It is "
                      "refused on the ground --skip S5b is")
    if n >= 2:
        if a.mode in ("replay", "desk"):
            raise Refused(
                "--iterations %d in --mode %s: this mode runs no bench stage, so "
                "every round would assert over the same --replay-boot capture -- "
                "one reading counted %d times. Rounds need the board: --mode "
                "bench, or --mode plan to print them" % (n, a.mode, n))
        per = sorted((skip & set(ROUND_STAGES)) - {"S4"})
        if per:
            raise Refused(
                "--skip %s with --iterations %d: from round 2 on, S4 is `%s` "
                "and the loader re-stages 0x80500000 from flash on that reset "
                "(SPEC.md LDR-22), so a round that skips S6 or S6b jumps into "
                "the VENDOR's image -- and the rest of a round's stages are what "
                "make it one. Only S4 may be skipped, and only in round 1"
                % (",".join(per), n, REBOOT_CMD))
    if a.mode in ("plan", "bench") and not (n == 1 and "S7" in skip):
        check_boot_terminator(a)


def check_boot_terminator(a):
    """TERM-1: S7's --until and --seconds, checked before the port is opened.

    console-capture refuses an empty or malformed --until and a zero --seconds
    itself -- but at S7, with S4..S6b of a power cycle already spent.  The
    placement rule its own terminator guard was measured into is: above the
    port.  Scoped to the modes and skips where S7 renders or runs, for the
    reason `M11b` gives about --image.
    """
    pat = getattr(a, "boot_until", DEFAULT_BOOT_UNTIL)
    secs = getattr(a, "boot_seconds", DEFAULT_BOOT_SECONDS)
    if not pat:
        raise Refused("--boot-until is empty, and an empty pattern matches at "
                      "offset 0: S7 would stop on the first byte of the jump")
    try:
        rx = re.compile(pat.encode())
    except re.error as exc:
        raise Refused("--boot-until %r is not a regex console-capture can "
                      "compile: %s" % (pat, exc))
    if rx.search(S7_ECHO.encode()):
        raise Refused(
            "--boot-until %r matches what the loader prints for `J %s` before "
            "the kernel prints a byte (%r). console-capture arms --until as the "
            "command goes out, so S7 would end on its own echo -- its case N36"
            % (pat, LOAD_ADDR, S7_ECHO))
    if not secs > 0:
        raise Refused("--boot-seconds %r: S7 has no --idle, so its --seconds is "
                      "the only thing that ends a boot whose pattern never "
                      "arrives, and console-capture refuses 0 -- at S7, after "
                      "the power cycle" % secs)


# ------------------------------------------- the host side of the TFTP link
def host_reaches_board(host, runner=None):
    """(ok, [(ok, rid, detail)]) -- can THIS HOST reach the board's loader?

    🔴 ICMP is the wrong instrument and using it would be worse than nothing:
    the loader answers ARP and does **not** answer ping, so 100 % packet loss
    is a PASS.  A precondition that aborted on it would abort every healthy
    run.

    量 2026-09-08 (`notes/dev-loop.md` § 15.1): `S6` died after a 12.11 s TFTP
    timeout and `looprun` reported `STOPPED at S6`.  The cause was on this
    desk -- the USB GbE had just been re-attached to WSL, `10.1.1.2/24` does
    not survive that, and the interface was `DOWN` with no address.  **Every
    abort gate this tool owns points at the BOARD** (`S5b` reads the burn flag,
    `S6b` reads the staged head), so a host fault was reported in the board's
    vocabulary at the stage where a board fault would be most alarming.

    Two readings, and the first is the one that actually failed:

      P-a  the route to <host> leaves an interface that HAS an IPv4 source
           address.  `ip -4 route get` prints `src <addr>` only when it does.
      P-b  the board answers ARP.  One ping is sent purely to provoke the
           exchange and **its exit code is ignored**; the reading is taken
           from `ip neigh`, where a usable entry carries an `lladdr` and a
           state that is not FAILED or INCOMPLETE.

    `runner` is injected so the self-test can drive both branches with no
    network and no board.
    """
    if runner is None:
        def runner(argv):
            p = subprocess.run(argv, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
            return p.returncode, p.stdout
    out = []

    rc, txt = runner(["ip", "-4", "route", "get", host])
    dev = re.search(r"\bdev\s+(\S+)", txt or "")
    src = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", txt or "")
    ok_a = rc == 0 and bool(dev) and bool(src)
    out.append((ok_a, "P-a the host has an address on the route to " + host,
                ("dev=%s src=%s" % (dev.group(1) if dev else "?",
                                    src.group(1) if src else "NONE"))
                if rc == 0 else "ip route get exited %d: %s"
                % (rc, (txt or "").strip()[:120])))
    if not ok_a:
        return False, out

    # Provoke the ARP exchange.  The return code is deliberately dropped: see
    # the docstring -- the loader does not answer ICMP.
    runner(["ping", "-c", "1", "-W", "1", host])

    rc, txt = runner(["ip", "-4", "neigh", "show", host, "dev", dev.group(1)])
    lladdr = re.search(r"\blladdr\s+([0-9a-fA-F:]{17})", txt or "")
    state = re.search(r"\b(REACHABLE|STALE|DELAY|PROBE|PERMANENT|FAILED|"
                      r"INCOMPLETE|NOARP)\b", txt or "")
    ok_b = bool(lladdr) and bool(state) and state.group(1) not in (
        "FAILED", "INCOMPLETE")
    out.append((ok_b, "P-b the board answers ARP",
                "%s %s" % (lladdr.group(1) if lladdr else "no lladdr",
                           state.group(1) if state else "no state")))
    return ok_a and ok_b, out


# --------------------------------------------------------------- the plan
def build_plan(a):
    """-> [ {id, name, kind, round, argv, note, out} ], the whole run, in order.

    Every command this project would type, produced once and used by `plan`,
    `desk` and `bench` alike.  A card that is rendered from the same list the
    runner executes cannot drift from it.

    LOOP-3, 1.2: `round` is 0 for S2/S3, which run once, and 1..--iterations
    for each round's S4..S8.  `out` is a capture stage's `--out` prefix -- and
    S8's, the capture it asserts over -- so a check reads the file its command
    wrote rather than re-deriving the name.
    """
    cap = ["/usr/bin/python3", os.path.join("tools", "console-capture.py"),
           "capture", "--port", a.port]
    plan = [
        dict(id="S2", name="build", kind="desk", argv=[
            "bash", os.path.join("tools", "rlxfw-kbuild.sh"), a.cell]
            # CFG-1, 2026-09-04: rlxfw-kbuild.sh now takes EITHER a --config path or a
            # --variant to derive one from config/rlxfw-kernel.delta, and refuses both
            # or neither.  Passing `--config ""` used to mean "fall through to the bare
            # board template", which is the silent default CFG-1 removed.
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
    ]
    for s in plan:
        s["round"], s["out"] = 0, None
    for rnd in range(1, max(rounds(a), 1) + 1):
        plan += round_plan(a, rnd, cap)
    return plan


def round_plan(a, rnd, cap):
    """S4..S8 of round `rnd`, every name under that round's stem."""
    out = stem(a, rnd)
    if rnd == 1:
        s4 = dict(id="S4", name="reset", kind="bench", argv=cap + [
            "--out", out + "-rz", "--send", "J " + RESET_TARGET] + S4_J_TERM,
            note="ABORT unless the capture holds %r (A0) and ends at %s (A0a)"
                 % (WATCHDOG_MARK, PROMPT))
    else:
        s4 = dict(id="S4", name="reset", kind="bench", argv=cap + [
            "--out", out + "-rz", "--send", REBOOT_CMD] + S4_RB_TERM,
            note="rlxfw's shell -> the loader: a watchdog bite, %s 2.407 s "
                 "later (FW-37). ABORT unless the capture holds %r (A0) and "
                 "ends at %s (A0a)" % (PROMPT, WATCHDOG_MARK, PROMPT))
    until = getattr(a, "boot_until", DEFAULT_BOOT_UNTIL)
    secs = getattr(a, "boot_seconds", DEFAULT_BOOT_SECONDS)
    stages = [
        s4,
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
        dict(id="S5c", name="hostlink", kind="bench", argv=None,
             note="HOST-side, and ARP not ICMP. `ip -4 route get %s` must "
                  "print a src address; one `ping -c1 -W1 %s` provokes the "
                  "exchange and ITS EXIT CODE IS IGNORED (the loader does not "
                  "answer ICMP, so 100%% loss is a pass); `ip -4 neigh show "
                  "%s dev <if>` must carry an lladdr. Aborts before S6 spends "
                  "a 12 s TFTP timeout reporting a host fault in the board's "
                  "vocabulary" % (a.host, a.host, a.host)),
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
            "--until", until, "--seconds", "%g" % secs],
            note="ends ON the shell's prompt (TERM-1); --seconds is the cap, "
                 "paid only when the pattern never arrives"),
        dict(id="S8", name="assert", kind="desk", argv=None,
             note="over S7's capture: the eleven marks, the derived id, a prompt"),
    ] + dwell_stage(a, rnd)         # S9, only with --dwell-seconds > 0 (1.3)
    for s in stages:
        argv = s["argv"] or []
        s["round"] = rnd
        s["out"] = argv[argv.index("--out") + 1] if "--out" in argv else None
    next(s for s in stages if s["id"] == "S8")["out"] = out + "-boot"  # by id, 1.3
    return stages


def render_plan(plan, a, out=sys.stdout):
    """The card's command column.  1.2: what `--skip` removes is printed as
    removed, and with N >= 2 every round is printed, because round 1 and the
    rest do not type the same S4."""
    n, skip = rounds(a), parse_skip(a)
    print("looprun %s -- the run, in order: S2/S3 once, then %d round(s) of "
          "S4..S%d" % (VERSION, n, 9 if dwell_of(a) > 0 else 8), file=out)
    if n >= 2:
        print("  one power press: round 1 starts at the loader prompt; rounds "
              "2..%d start in rlxfw's shell and reach it through `%s`"
              % (n, REBOOT_CMD), file=out)
    print("", file=out)
    cur = None
    for s in plan:
        if n >= 2 and s["round"] != cur:
            cur = s["round"]
            print("  -- %s --" % ("once, before round 1" if cur == 0 else
                                  "round %d of %d" % (cur, n)), file=out)
        note = s["note"]
        if skipped_in(s["id"], s["round"], skip, n):
            cmd, note = "SKIPPED (--skip %s)" % s["id"], "not run"
            if s["id"] == "S4":
                note = ("the board must already be at a loader prompt -- a cold "
                        "ESC catch")
            if s["id"] == "S4" and n >= 2:
                cmd = "SKIPPED (--skip S4: round 1 only)"
                note += (". %s: `%s` is the only way back from rlxfw's shell, "
                         "so it cannot be skipped there"
                         % ("Round 2 runs its S4" if n == 2 else
                            "Rounds 2..%d run theirs" % n, REBOOT_CMD))
        else:
            cmd = (" ".join(shlex.quote(x) for x in s["argv"]) if s["argv"]
                   else "(in-process)")
        print("  %-3s %-9s %-6s %s" % (s["id"], s["name"], s["kind"], cmd), file=out)
        print("  %-3s %-9s %-6s    %s" % ("", "", "", note), file=out)
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


def assert_loader_prompt(text):
    """A0a: the capture ENDS at the loader's prompt.  1.2, LOOP-3.

    🔴 `A0` cannot say this.  C-8's line is printed on a warm reset whose ESC
    window was missed too -- and then the loader jumps into flash, the
    VENDOR's firmware boots, and S5 types into it.  `bench/2026-08-31c/K-J` is
    that capture: the watchdog line, the banner, `Jump to image start`.
    CLAUDE.md: prove the prompt was caught before handing the board on.

    Read off the capture's last bytes, not off --until's metadata, so it is the
    same test on a capture from before 1.2 and on a replayed one.  Only what
    the instrument itself adds may follow the prompt -- the ESC stream's echo
    and the CR's reply -- so CR, LF, space and ESC are stripped and nothing
    else.  量, read 2026-09-23: of the 193 committed captures holding C-8's
    line, 191 end at `<RealTek>`, each with a prompt after its last watchdog
    line; the other two are K-J and `C1-WG`, which `--idle 3` cut short.
    """
    rid = "A0a the capture ends at the loader prompt"
    tail = text.rstrip("\r\n \x1b")
    if tail.endswith(PROMPT):
        return [(True, rid, "%s is the last thing the board printed" % PROMPT)]
    return [(False, rid, "NOT CAUGHT -- the capture ends %r, not at %s, so "
                         "nothing below may run" % (tail[-40:], PROMPT))]


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
def run_stage(s, cwd):
    """-> (rc, output).  The one place a stage's command is executed.

    1.2: the self-test replaces it through `a._stage_runner`, as it replaces
    S5c's commands through `a._link_runner`, so a whole bench run -- rounds,
    pre-flight, stages file -- can be driven with no board and no port.  Its
    unused `dry` and `log` parameters are gone; nothing passed them.
    """
    p = subprocess.run(s["argv"], cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    return p.returncode, p.stdout.decode("utf-8", "replace")


# ---------------------------------------------------------- the clock (1.3, P2-4)
# 🔴 Every stamp in the stages file, the budget and S9's deadline read RAW.  Until
# 1.2 they read time.monotonic(): CLOCK_MONOTONIC, which WSL's kernel slews slow
# while two time daemons fight over it (SPEC.md CLK-38; 量 2026-09-23, MONOTONIC/RAW
# 0.957429 over 60 s), so a row read short and lined up with no RAW capture.  Kernel
# waits (S9's sleep) still run on MONOTONIC, so S9 re-reads RAW whenever it wakes.
# RAW restarts with every WSL boot: the header names the boot_id beside it.
CLOCK = "CLOCK_MONOTONIC_RAW"   # matched as a whole word: CLOCK_MONOTONIC is a prefix


def clock_id():
    """-> time.CLOCK_MONOTONIC_RAW, or Refused (Linux only).  Looked up per call, never
    at import: cardcheck imports this file for refuse_args, which reads no clock."""
    cid = getattr(time, CLOCK, None)
    if cid is None:
        raise Refused("this Python has no time.%s (Linux only), and looprun %s "
                      "stamps every stage and computes every deadline on it"
                      % (CLOCK, VERSION))
    return cid


def now():
    """The one reader.  Looked up per call, so tools/clockshim.py reaches it."""
    return time.clock_gettime(clock_id())


def clock_triple():
    """(raw, mono, real): a RAW read with one CLOCK_MONOTONIC and one REALTIME read
    beside it, so the stages file carries its own MONOTONIC/RAW ratio."""
    raw = now()
    return raw, time.clock_gettime(time.CLOCK_MONOTONIC), time.time()


STAGES_COLS = ("round", "stage", "name", "kind", "start_raw", "end_raw",
               "seconds", "rc", "result")


class StageLog:
    """LOOP-3, 1.2: the stage times in a file, one row per stage per round.

    Until 1.2 they were printed and nothing kept them: `notes/dev-loop.md`
    § 13-14 re-derived twelve machine totals out of the captures' `.meta.json`
    because the tool's own numbers had gone with the terminal.

    🔴 REWRITTEN WHOLE after every stage, through `.tmp` and `os.replace`: a
    run that dies mid-stage leaves every completed row on disk, and the file
    is never open while its content is incomplete.  Its last line is the
    run's status -- `running` there is a run that did not finish, no file at
    all is one that never started (every refusal comes before the first
    write), and `closed`, `STOPPED` and `budget` are the three ways it ends.
    1.3: an ended run's line above its status is `# end:`, the clock at its end.
    """

    def __init__(self, path, head):
        self.path, self.head, self.rows, self.tail = path, list(head), [], []

    def add(self, s, t0, t1, rc, result):
        def stamp(x):
            return "" if x is None else "%.6f" % x
        self.rows.append([str(s["round"]), s["id"], s["name"], s["kind"],
                          stamp(t0), stamp(t1),
                          "" if t0 is None else "%.6f" % (t1 - t0),
                          "" if rc is None else str(rc), result])
        self.write("running -- round %d %s done" % (s["round"], s["id"]))

    def write(self, status):
        text = "\n".join(self.head + ["\t".join(STAGES_COLS)]
                         + ["\t".join(r) for r in self.rows]
                         + self.tail + ["# status: " + status]) + "\n"
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, self.path)


def stages_head(a, skip):
    return [
        "# looprun %s stage times (LOOP-3): one row per stage per round, and "
        "round 0 is S2/S3, which run once." % VERSION,
        "# start_raw/end_raw: absolute CLOCK_MONOTONIC_RAW, the clock console-capture "
        "1.5 stamps on (1.2 wrote start_mono/end_mono, CLOCK_MONOTONIC: CLK-38).",
        "# seconds = end_raw - start_raw.  rc is the command's exit status, empty for "
        "the in-process S5c, S8 and S9 and for a skipped stage.  result is ok, FAIL "
        "and the ids of the assertions that failed, or skipped.",
        "# cell=%s attempt=%d iterations=%d skip=%s boot-until=%r boot-seconds=%g "
        "dwell-seconds=%g" % (a.cell, getattr(a, "attempt", 1) or 1, rounds(a),
                              ",".join(sorted(skip)) or "-",
                              getattr(a, "boot_until", DEFAULT_BOOT_UNTIL),
                              getattr(a, "boot_seconds", DEFAULT_BOOT_SECONDS),
                              dwell_of(a)),
    ]


def image_args(a, skip):
    """(uses_image, img, want): what the --image guards read, with one owner --
    refuse_args's argument halves (1.3) and loop_once's file halves both use it,
    so the two cannot disagree about which runs read the file."""
    uses_image = (a.mode == "bench"
                  and bool(set(IMAGE_STAGES) - skip))
    img = getattr(a, "image", "") or ""
    want = (getattr(a, "image_sha256", None) or "").strip().lower()
    return uses_image, img, want


def loop_once(a, out=sys.stdout):
    """One invocation: S2/S3 once, then `--iterations` rounds of S4..S8 (S9).

    The name is from before rounds (LOOP-3, 1.2).  With `--iterations 1` this
    is exactly the one iteration it always was, and `notes/dev-loop.md` calls
    it by this name.  1.3: the refusals that read only the arguments are
    refuse_args's (below) and run first; then the clock; then the disk.
    """
    skip = refuse_args(a)
    clock_id()
    plan = build_plan(a)

    # ------------------------------------------------- the artefact pre-flight
    # 🔴 量 2026-09-08 (`notes/dev-loop.md` § 15.2): a retried run died at S5b
    # in 0.06 s because `console-capture.py` refuses to overwrite an existing
    # capture -- correctly -- and the first attempt's file was still there.  By
    # then S4 (a reset) and S5 (a rescue) had already run.  Reading the whole
    # artefact set up front turns that into ONE refusal before the port is
    # opened, and it names the flag that resolves it, so the operator's next
    # move is `--attempt 2` rather than the `--force` the guard exists to
    # prevent.
    if a.mode == "bench":
        clash = preflight_artefacts(a, skip)
        if clash:
            raise Refused(
                "these files already exist, so a stage would collide with a "
                "previous attempt after part of a power cycle had been "
                "spent:\n        %s\n      Pass --attempt %d. Do NOT pass "
                "--force to console-capture: the file it refuses to overwrite "
                "is the previous attempt's evidence, and on 2026-09-08 that "
                "was a real burn-flag reading."
                % ("\n        ".join(clash[:6]),
                   (getattr(a, "attempt", 1) or 1) + 1))

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
    uses_image, img, want = image_args(a, skip)
    if uses_image:
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
        got = sha256_of(img)
        if got != want:
            raise Refused(
                "--image %s does not match --image-sha256:\n"
                "        want %s\n        got  %s\n"
                "      The card names one file; this is a different one. "
                "RLXFW-ID0 would not have caught it -- it is a digest over "
                "config/ only." % (img, want, got))
        print("  pre  image     sha256 %s  <- matches the pin" % got, file=out)

    return run_plan(a, plan, skip, want, out)


# ------------------------------------------------------ FW-124: refuse_args (1.3)
def refuse_args(a):
    """Every refusal that reads nothing but the parsed arguments -> the --skip set.

    No file, environment variable, clock, port or host version is read, so it runs
    where the bench cannot.  `--mode plan` calls it: until 1.3 plan ran check_shape
    alone, so a bench line missing `--recipe-override`, rendered as a plan, passed
    (s107 hostcell REPORT § 1.3; SPEC.md FW-124).  loop_once calls it first, and
    cardcheck can call it on a card's HOST line, in-process, with build_parser():
    the check a card runs and the run it names cannot drift.  The refusals keep
    the order they always fired in -- check_shape's, the four that opened
    loop_once, then the argument halves of the --image guards -- so which one wins
    when two are wrong at once (M14) is unchanged.
    """
    skip = parse_skip(a)
    if getattr(a, "self_test", False):
        return skip                     # the self-test reads no other argument
    check_shape(a, skip)
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
    # Up here since 1.2; until then it fired at S8, after `--mode desk` had
    # already paid for S2 and S3.
    if a.mode in ("desk", "replay") and not getattr(a, "replay_boot", None):
        raise Refused("--mode %s needs --replay-boot <capture prefix>: "
                      "S8 has to read a boot log, and inventing one would "
                      "make every assertion below vacuous" % a.mode)
    # The argument halves of loop_once's image pre-flight (LOOP-4, RECIPE-1); the
    # halves that open the file stay there, after the clock's check.
    uses_image, img, want = image_args(a, skip)
    if uses_image and not img:
        raise Refused(
            "no --image: %s consume it and its default is the empty "
            "string, so `loader-tftp.py put --image ''` would be reached "
            "with S4, S5 and S5b of a power cycle already spent. S3 writes "
            "<work>/<label>/kroot/rtkload/nfjrom and nothing carries that "
            "path here" % "/".join(IMAGE_STAGES))
    # 🔴 `--mode plan` renders the S6 and S6b that read the file, so a pin there is a
    # pin on the run it prints: refusing it would refuse every card's bench line
    # rendered as a plan.  desk and replay never open the file (M13).
    renders = a.mode == "plan" and bool(set(IMAGE_STAGES) - skip)
    if want and not (uses_image or renders):
        raise Refused(
            "--image-sha256 with no stage that reads --image (mode=%s, "
            "skip=%s): a pin on a file nobody opens asserts nothing, and a "
            "check that cannot fail is the shape this repository refuses "
            "on principle" % (a.mode, ",".join(sorted(skip)) or "-"))
    if want and (len(want) != 64 or any(c not in "0123456789abcdef" for c in want)):
        raise Refused("--image-sha256 %r is not 64 hex digits" % want)
    return skip


# ---------------------------------------------------------------- the dwell (1.3)
# 🔴 WHY.  量 2026-09-23 (s107 srvlog REPORT § 1.10): looprun reset the board 0.189 s
# after rlxfw's prompt -- S7's capture ends 0.085 s after it, and the next round's
# S4 sends `busybox reboot -f` 0.104 s later -- and the prompt comes 0.029-0.031 s
# after N-NDOPEN (量, all nine rlxfw boots of card A, both images).  The host
# re-sends ARP about once a second (on-wire gaps 1.0004-1.048 s, 量 card A's P3), so
# a board reset 0.2 s after its link came up is never asked again: the loud image
# read no network-up in any boot, and the quiet image lost P3Q-r01 the same way.
# Not only between rounds: the loud block's LAST boot was reset by the card's next
# cell, P1-RZ, 0.098 s after looprun closed.  So S9 follows EVERY round's S8, the
# last included, and holds the board at its prompt until S7's end + D.
#
# Anchored on S7's end, which is at or after the prompt (console-capture drains 50
# ms past its --until match, then exits), so the board is up at least D past its
# prompt -- and it works when bring-up failed and no N-NDOPEN was printed.  D is
# RAW seconds, like every deadline here.  ⚠️ The host's ARP timer runs on
# CLOCK_MONOTONIC (推, s107 srvlog REPORT § 1.3), which WSL slews slow: D RAW
# seconds are D*r of the timer's own.  At r = 0.957429 (量 2026-09-23) D = 2 is
# 1.91 s of it (推, arithmetic).  Size D against the slowest r a seating expects.
DWELL_MAX = 60.0        # above it, not a dwell: a millisecond count typed as seconds
#: the longest single kernel sleep inside S9.  A sleep runs on CLOCK_MONOTONIC, so
#: at r = 0.957 each overshoots RAW by q(1/r - 1): 2.2 ms at 50 ms.
DWELL_QUANTUM = 0.05


def dwell_of(a):
    """--dwell-seconds, read so that a fixture without it means no dwell: 1.2's run."""
    d = getattr(a, "dwell_seconds", None)
    return 0.0 if d is None else d


def check_dwell(a, skip):
    """check_shape's dwell refusals (1.3), in every mode: they read only arguments.

    Called before check_shape's own, so `--skip S9` with a dwell is refused with the
    reason that is true; without one S9 is not a stage and M5's guard says so."""
    d = dwell_of(a)
    if not 0.0 <= d <= DWELL_MAX:           # NaN fails both comparisons
        raise Refused("--dwell-seconds %r: must lie in [0, %g]. 0, the default, is no "
                      "dwell; above %g s it is a different experiment, or milliseconds "
                      "typed as seconds" % (d, DWELL_MAX, DWELL_MAX))
    if d > 0 and "S9" in skip:
        raise Refused("--skip S9 with --dwell-seconds %g: S9 IS the dwell, and "
                      "--dwell-seconds 0 is how a run does not wait" % d)
    if d > 0 and rounds(a) == 1 and "S7" in skip:
        raise Refused("--dwell-seconds %g with --skip S7: S9 waits until S7's end + "
                      "%g s, and with S7 skipped no stage of this run reaches the "
                      "prompt it is anchored on" % (d, d))


def dwell_stage(a, rnd):
    """[] or [S9], the stage round_plan closes round `rnd` with.  In-process, and
    `bench` because it holds the board: desk and replay skip it."""
    d = dwell_of(a)
    if not d > 0:
        return []
    return [dict(id="S9", name="dwell", kind="bench", argv=None,
                 note="holds the board at rlxfw's prompt until S7's end + %g s -- "
                      "every round, the last included -- so the host's next ARP "
                      "broadcast (about 1 s apart) meets a board that answers" % d)]


def boot_ended_on(prefix):
    """TERM-1: what ended S7's capture, read out of its own `.meta.json`.

    Not an assertion.  A boot whose pattern never arrived is still a boot S8
    can judge; what it cost is the whole cap, and this line is where that
    shows instead of passing silently as a slow round.
    """
    try:
        with open(prefix + ".meta.json", encoding="utf-8") as fh:
            meta = json.load(fh)
    except (OSError, ValueError) as exc:
        return "      ended on ? -- no readable %s.meta.json (%s)" % (prefix, exc)
    if meta.get("until_offset") is not None:
        return "      ended on --until at offset %s" % meta["until_offset"]
    return ("      ⚠️ ended on %r, NOT on --boot-until: the pattern never "
            "arrived, so this round paid the whole cap" % meta.get("stop_reason"))


#: the two kernel files a stages header names beside the clock (1.3, spec § 2)
BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"
CLOCKSOURCE_PATH = "/sys/devices/system/clocksource/clocksource0/current_clocksource"


def kernel_line(path):
    """A one-line kernel file, stripped -- or `unreadable:<Error>`, recorded as not
    known rather than guessed, and never a refusal: a lost identity is a gap in
    the record, not a reason to lose the run."""
    try:
        with open(path, encoding="ascii", errors="replace") as fh:
            return fh.read().strip().replace(" ", "_") or "empty"
    except OSError as exc:
        return "unreadable:" + type(exc).__name__


def clock_line(which, t):
    """The header's clock line (`start`) or an ended run's (`end`), from one
    clock_triple(): RAW, the CLOCK_MONOTONIC and REALTIME reads beside it, and the
    clocksource -- so a record says which boot's RAW it is and carries its own
    MONOTONIC/RAW ratio.  Keys holding RAW end in `_raw` (spec § 1)."""
    raw, mono, real = t
    if which == "start":
        return ("# clock=%s boot_id=%s clocksource=%s start_raw=%.6f "
                "mono_at_start=%.6f start_real=%.6f"
                % (CLOCK, kernel_line(BOOT_ID_PATH), kernel_line(CLOCKSOURCE_PATH),
                   raw, mono, real))
    return ("# end: end_raw=%.6f mono_at_end=%.6f end_real=%.6f clocksource_end=%s"
            % (raw, mono, real, kernel_line(CLOCKSOURCE_PATH)))


def run_plan(a, plan, skip, want, out=sys.stdout):
    """Walk the plan -- S2/S3 once, then each round -- and stop at the first
    failure.  In `--mode bench` every row reaches the stages file as it
    completes.  LOOP-3, 1.2.  1.3: every stamp and the budget on RAW, through
    now(), and S9, the dwell, closing each round when --dwell-seconds > 0."""
    n = rounds(a)
    runner = getattr(a, "_stage_runner", None) or run_stage
    start = clock_triple()          # 1.3: the budget's origin is the header's RAW read
    log = None
    if a.mode == "bench":
        os.makedirs(os.path.dirname(os.path.abspath(stages_path(a))),
                    exist_ok=True)
        log = StageLog(stages_path(a),
                       stages_head(a, skip) + [clock_line("start", start)])
        log.write("started -- no stage has completed")

    def finish(status):
        # 1.3: an ended run's last write carries the clock at its end, then status
        log.tail = [clock_line("end", clock_triple())]
        log.write(status)
    checks = {
        "S4": lambda t: assert_reset(t) + assert_loader_prompt(t),
        "S5b": assert_autoburn,
        "S6b": lambda t: assert_staged(t, a.image),
    }
    recipe = getattr(a, "recipe_override", None) if "S2" in skip else None
    budget = getattr(a, "budget_seconds", 1800.0)
    results, rres, timings, pending = [], [], [], []
    t_run, cur, closed, stop, t_s7_end = start[0], 0, 0, None, None
    try:
        for s in plan:
            sid, rnd = s["id"], s["round"]
            if rnd != cur:
                spent = now() - t_run
                # Checked before a round starts, never inside one: between two
                # rounds the board sits at rlxfw's shell prompt, which is the
                # one state a stopped run may leave it in.
                if rnd > 1 and spent >= budget:
                    stop = ("budget -- %d of %d round(s) ran; round %d not "
                            "started, %.1f s spent of --budget-seconds %g"
                            % (closed, n, rnd, spent, budget))
                    print("looprun: budget of %.0f s reached after %d round(s); "
                          "not starting round %d" % (budget, closed, rnd), file=out)
                    break
                cur, t_s7_end = rnd, None       # S9 anchors on THIS round's S7 only
                if n >= 2:
                    print("\n=== round %d of %d   (%.1f s spent)" % (rnd, n, spent),
                          file=out)
            if sid == "S8":
                if a.mode in ("desk", "replay"):
                    bootlog = a.replay_boot + ".log"
                    if a.recipe_override:
                        recipe = a.recipe_override
                else:
                    bootlog = s["out"] + ".log"
                if not os.path.exists(bootlog):
                    if log:
                        log.add(s, None, None, None, "FAIL")
                    raise StageFailed("S8", "no boot capture at %s" % bootlog, rnd)
                text = open(bootlog, encoding="utf-8", errors="replace").read()
                if a.control == "truncate-boot":
                    text = text[:120]
                t0 = now()
                res = assert_boot(text, recipe, a.control)
                t1 = now()
                timings.append(("S8", t1 - t0))
                pending.append(("S8", t1 - t0))
                rres += res
                bad = [rid.split()[0] for ok, rid, _d in res if not ok]
                if log:
                    log.add(s, t0, t1, None, " ".join(["FAIL"] + bad) if bad else "ok")
                print("", file=out)
                for ok, rid, detail in rres:
                    print("  %-4s %-38s %s" % ("ok" if ok else "FAIL", rid, detail),
                          file=out)
                print("", file=out)
                print("  %sstage seconds: %s"
                      % ("round %d " % rnd if n >= 2 else "",
                         "  ".join("%s=%s" % (i, "skipped" if t is None else "%.2f" % t)
                                   for i, t in pending)), file=out)
                results += rres
                rres, pending = [], []
                if bad:
                    stop = "STOPPED at round %d S8 -- %s failed" % (rnd, " ".join(bad))
                    if n >= 2:
                        print("looprun: round %d failed; no later round runs, "
                              "rather than averaging a red round into a green "
                              "run" % rnd, file=out)
                    break
                closed = rnd
                continue
            if (a.mode == "replay" or (s["kind"] == "bench" and a.mode == "desk")
                    or skipped_in(sid, rnd, skip, n)):
                why = "--skip" if skipped_in(sid, rnd, skip, n) else "mode=" + a.mode
                print("  %-3s %-9s SKIPPED (%s)" % (sid, s["name"], why), file=out)
                pending.append((sid, None))
                if log:
                    log.add(s, None, None, None, "skipped")
                continue
            if sid == "S5c":
                # In-process, like S8: this is three commands and a parse, not one
                # command, and rendering it as one would hide which half failed.
                t0 = now()
                ok, rows = host_reaches_board(
                    a.host, getattr(a, "_link_runner", None))
                t1 = now()
                timings.append((sid, t1 - t0))
                pending.append((sid, t1 - t0))
                print("  %-3s %-9s %-4s  %6.2f s"
                      % (sid, s["name"], "ok" if ok else "FAIL", t1 - t0), file=out)
                for rok, rid, detail in rows:
                    rres.append((rok, rid, detail))
                    print("      %-4s %s -- %s"
                          % ("ok" if rok else "FAIL", rid, detail), file=out)
                if log:
                    log.add(s, t0, t1, None, " ".join(
                        ["ok" if ok else "FAIL"]
                        + [rid.split()[0] for rok, rid, _d in rows if not rok]))
                if not ok:
                    raise StageFailed(
                        "S5c", "the HOST cannot reach %s. This is not the board: "
                               "%s" % (a.host, rows[-1][2] if rows else "?"), rnd)
                continue
            if sid == "S9":
                # 1.3, the dwell (see DWELL_MAX): in-process, after S8, until this
                # round's S7 end + D on RAW.  Each kernel sleep is at most one
                # quantum and RAW is re-read after it, so MONOTONIC's slew costs
                # one quantum's overshoot, not D's.  Never longer than D from its
                # own start: the budget cannot interrupt a stage in flight.  Not
                # machine time, so neither `timings` nor the S8 line carries it.
                t0 = now()
                if t_s7_end is None:
                    if log:
                        log.add(s, None, None, None, "FAIL")
                    raise StageFailed("S9", "round %d has no S7 end to anchor the "
                                            "dwell on" % rnd, rnd)
                wake = min(t_s7_end, t0) + dwell_of(a)
                left = wake - t0
                while left > 0:
                    time.sleep(min(left, DWELL_QUANTUM))
                    left = wake - now()
                t1 = now()
                print("  %-3s %-9s %-4s  %6.2f s   %.3f s past S7's end"
                      % (sid, s["name"], "ok", t1 - t0, t1 - t_s7_end), file=out)
                if log:
                    log.add(s, t0, t1, None, "ok")
                continue
            if a.control == "build-fail" and sid == "S2":
                s = dict(s, argv=s["argv"][:3] + ["--config", "/nonexistent/config"])
            # 🔴 FW-100: a check belongs at the point of USE.  The pin was taken
            # before round 1, and with N rounds the file is uploaded N times --
            # S6b cannot see a change, because it derives its expectation from
            # the same file.  So the pin is re-taken before every upload.
            if sid == "S6" and want:
                # `taken`, not `now`: 1.3's clock reader is now(), and a local of
                # that name would shadow it for the whole of this function.
                taken = sha256_of(a.image)
                if taken != want:
                    if log:
                        log.add(s, None, None, None, "FAIL")
                    raise StageFailed(
                        "S6", "--image changed after the pre-flight pinned it "
                              "(want %s, now %s); nothing was uploaded in this "
                              "round" % (want[:16], taken[:16]), rnd)
            t0 = now()
            rc, txt = runner(s, ROOT)
            t1 = now()
            if sid == "S7":
                t_s7_end = t1               # S9's anchor: at or after the prompt
            timings.append((sid, t1 - t0))
            pending.append((sid, t1 - t0))
            print("  %-3s %-9s rc=%d  %6.2f s" % (sid, s["name"], rc, t1 - t0),
                  file=out)
            bad = []
            try:
                if rc != 0:
                    raise StageFailed(sid, "exit %d" % rc, rnd)
                if sid == "S2":
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
                    try:
                        shutil.copyfile(mm.group(1), stem(a) + ".manifest")
                    except OSError as exc:
                        raise StageFailed("S2", "manifest %s could not be copied: %s"
                                          % (mm.group(1), exc))
                    print("      manifest=%s  -> %s.manifest"
                          % (mm.group(1), stem(a)), file=out)
                if sid in checks:
                    # Every check of the stage is evaluated and recorded before
                    # the stage fails, so the record names each one that did.
                    cpath = s["out"] + ".log"
                    ctext = open(cpath, encoding="utf-8", errors="replace").read() \
                        if os.path.exists(cpath) else ""
                    res = checks[sid](ctext)
                    rres += res
                    bad = [rid.split()[0] for ok, rid, _d in res if not ok]
                    if bad:
                        raise StageFailed(sid, " / ".join(
                            d for ok, _r, d in res if not ok), rnd)
                if sid == "S7" and a.mode == "bench":
                    print(boot_ended_on(s["out"]), file=out)
            except StageFailed:
                if log:
                    log.add(s, t0, t1, rc, " ".join(["FAIL"] + bad))
                raise
            if log:
                log.add(s, t0, t1, rc, "ok")
    except StageFailed as exc:
        if exc.rnd is None:
            exc.rnd = cur
        if log:
            finish("STOPPED at round %d %s -- %s" % (exc.rnd, exc.sid, exc.why))
        raise

    machine = sum(t for _i, t in timings if t is not None)
    print("  MACHINE TOTAL: %.2f s   (S1, the edit, and S8b, the read, are not "
          "this tool's to time -- looptime owns the served loop)" % machine,
          file=out)
    if dwell_of(a) > 0:
        print("  S9's dwell is a wait, not machine time: the stages file has it",
              file=out)
    failed = [r for r in results if not r[0]]
    print("", file=out)
    if failed:
        if log:
            # Every failing result stops the run where it fails, so `stop` is
            # set here -- by reasoning.  The record must not depend on that.
            finish(stop or "STOPPED -- %d of %d assertion(s) failed"
                   % (len(failed), len(results)))
        print("RESULT: %d of %d assertion(s) failed" % (len(failed), len(results)),
              file=out)
        return 1
    if log:
        finish(stop or "closed -- %d of %d round(s), every assertion held"
               % (closed, n))
    print("RESULT: the loop closed%s, %d assertion(s) held, %.2f s of machine time"
          % (" %d of %d round(s)" % (closed, n) if n >= 2 else "",
             len(results), machine), file=out)
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

    # 1.3: the harness's own RAW reader, taken before any case patches the time
    # module -- so neither L5f's shim nor a defect in the tool's now() can make a
    # bracket agree with the tool by construction.
    _gettime = time.clock_gettime

    def raw_now():
        return _gettime(time.CLOCK_MONOTONIC_RAW)

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
    ck("R1", "the plan has all ten stages", 10, len(plan))
    ck("R2", "seven of them need the board", 7,
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
            iterations = 1; budget_seconds = 1800.0
            boot_until = DEFAULT_BOOT_UNTIL; boot_seconds = DEFAULT_BOOT_SECONDS
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

        # ---- M8: --iterations through the PROGRAM, so main()'s wiring is in
        # the case and not only loop_once's.  🔴 Until 1.2 M8 asserted that
        # `--iterations 2` was REFUSED (exit 2): S4 was a loader command sent
        # into the shell iteration 1 left behind, and every capture name lacked
        # an iteration index, so iteration 2 would have died on a filename.
        # LOOP-3 gave it a way back (`busybox reboot -f`) and per-round names,
        # so M8 now asserts the reverse, and asserts it on what is printed: the
        # plan of `--mode plan` is the card, and before 1.2 it silently rendered
        # ONE iteration for any N.  M8b is its negative control -- a program
        # that accepted every N everywhere would pass M8 -- and M8c is what M8b
        # used to be.
        base = [sys.executable, os.path.join(ROOT, "tools", "looprun.py"),
                "--mode", "replay", "--replay-boot", pre,
                "--recipe-override", "b1434383"]

        def run_of(argv):
            p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL)
            return p.returncode, p.stdout.decode("utf-8", "replace")

        def rc_of(extra):
            return run_of(base + extra)[0]
        rc8, txt8 = run_of([sys.executable, os.path.join(ROOT, "tools", "looprun.py"),
                            "--mode", "plan", "--iterations", "2"])
        ck("M8", "🔴 --iterations 2 is ACCEPTED, and the plan shows round 2 "
                 "reaching the loader through the reboot",
           (0, True, 1), (rc8, "-- round 2 of 2 --" in txt8,
                          sum(1 for ln in txt8.splitlines()
                              if "console-capture.py" in ln and REBOOT_CMD in ln)))
        ck("M8b", "and --mode replay, which has one capture and nothing to "
                  "repeat, still REFUSES it (exit 2)", 2,
           rc_of(["--iterations", "2"]))
        ck("M8c", "and --iterations 1 still runs", 0, rc_of(["--iterations", "1"]))

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
            # 1.2: a bench run that reaches S2 now writes its stages file, so
            # each run gets an --out-dir of its own -- one case's file must not
            # become the next case's artefact clash, and none may land in the
            # directory the self-test was started from.
            B.out_dir = tempfile.mkdtemp(dir=d)
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
        # 🔴 1.2: keyed on "G2/H1a", which only the S5b refusal says.  Until
        # then it was keyed on "S5b" -- and the --image refusal's own text says
        # "S5b of a power cycle already spent", so with the S5b guard deleted
        # this case still passed.  A mutation run of 1.2 is what found it.
        try:
            loop_once(B, out=devnull); got = "no refusal"
        except Refused as exc:
            got = "S5b" if "G2/H1a" in str(exc) else "image"
        except StageFailed:
            got = "StageFailed"
        ck("M14", "🔴 with --skip S5b AND a bad --image, the S5b safety refusal "
                  "is the one reported", "S5b", got)

        # ---- M15-M22: looprun 1.1.  🔴 `notes/dev-loop.md` § 15 records that
        # NEITHER of the two defects this covers is reachable from --self-test
        # as it stood -- both need a FAILED run followed by a SECOND run
        # against the same --out-dir, and the self-test drives --mode replay
        # once.  These cases are that missing shape.

        class A1:
            out_dir = "bench/2026-01-01"; cell = "L1"; attempt = 1

        class A2:
            out_dir = "bench/2026-01-01"; cell = "L1"; attempt = 2
        ck("M15", "attempt 1 keeps the plain stem, attempt 2 does not collide "
                  "with it", ["bench/2026-01-01/L1" .replace("/", os.sep),
                              "bench/2026-01-01/L1-att2".replace("/", os.sep)],
           [stem(A1), stem(A2)])

        with tempfile.TemporaryDirectory() as od:
            class C:
                out_dir = od; cell = "L1"; attempt = 1
            ck("M16a", "a clean out-dir has nothing to collide with", [],
               preflight_artefacts(C, set()))
            open(os.path.join(od, "L1-ab2.log"), "w").write("x")
            ck("M16b", "🔴 and S5b's capture left by a failed attempt IS seen, "
                       "before the port is opened",
               [os.path.join(od, "L1-ab2.log")],
               preflight_artefacts(C, set()))
            class C2:
                out_dir = od; cell = "L1"; attempt = 2
            ck("M17", "🔴 --attempt 2 clears it -- which is the move that "
                      "replaces `--force` destroying the evidence", [],
               preflight_artefacts(C2, set()))
            ck("M18", "and a SKIPPED stage's artefact is not a collision -- "
                      "the guard's scope is the stages that will run", [],
               preflight_artefacts(C, {"S5b"}))

            # And through loop_once, so the guard is wired and not merely
            # written.  The port is deliberately a path that cannot exist, so
            # a broken guard fails fast instead of reaching a real device.
            B.mode = "bench"; B.out_dir = od; B.cell = "L1"; B.attempt = 1
            B.skip = "S2,S3"; B.port = "/dev/rlxfw-no-such-port"
            B.image = "img.bin"; B.image_sha256 = None
            try:
                loop_once(B, out=devnull)
                got = "no refusal"
            except Refused as exc:
                got = "attempt" if "--attempt 2" in str(exc) else "other: %s" % exc
            except StageFailed as exc:
                got = "StageFailed@" + exc.sid
            ck("M19", "🔴 and loop_once refuses on it, naming --attempt, "
                      "BEFORE S4 resets the board", "attempt", got)
            B.mode = "replay"; B.out_dir = None; B.attempt = 1
            B.port = DEFAULT_PORT; B.skip = ""

        # ---- the host link, ARP not ICMP.  Both branches driven with no
        # network and no board, through the injected runner.
        def fake(route, neigh, ping_rc=1):
            def run(argv):
                if argv[:3] == ["ip", "-4", "route"]:
                    return (0, route) if route is not None else (2, "")
                if argv[0] == "ping":
                    return ping_rc, "100% packet loss"
                if argv[:3] == ["ip", "-4", "neigh"]:
                    return 0, neigh
                return 127, ""
            return run

        good_route = "10.1.1.1 dev eth4 src 10.1.1.2 uid 1000 \n    cache \n"
        good_neigh = "10.1.1.1 dev eth4 lladdr 00:11:22:33:44:55 REACHABLE\n"
        ck("M20", "🔴 the ping FAILS (the loader does not answer ICMP) and the "
                  "link is still a pass -- this is the whole reason the "
                  "instrument is ARP", True,
           host_reaches_board("10.1.1.1",
                              fake(good_route, good_neigh, ping_rc=1))[0])
        ck("M21", "🔴 P-a: an interface with no source address fails, which is "
                  "the fault that actually happened on 2026-09-08", False,
           host_reaches_board("10.1.1.1",
                              fake("10.1.1.1 dev eth4 \n", good_neigh))[0])
        ck("M22", "🔴 P-b: an ARP entry that never resolved fails", False,
           host_reaches_board("10.1.1.1", fake(
               good_route, "10.1.1.1 dev eth4  FAILED\n"))[0])
        ck("M23", "and P-a alone passing is not enough to report a pass",
           [True, False],
           [r[0] for r in host_reaches_board("10.1.1.1", fake(
               good_route, "10.1.1.1 dev eth4  INCOMPLETE\n"))[1]])

        # S5c must sit BEFORE S6.  A precondition after the stage it protects
        # is not a precondition.
        pids = [s["id"] for s in build_plan(B)]
        ck("M24", "🔴 S5c is in the plan and runs before S6", True,
           "S5c" in pids and pids.index("S5c") < pids.index("S6")
           and pids.index("S5b") < pids.index("S5c"))

        # ---- L: LOOP-3, 1.2 -- N rounds on one power press.  Each case's
        # comment says what refutes it.  The bench runs are driven through
        # `_stage_runner`: a fake that writes what each stage's real command
        # leaves on disk, in the shapes the committed captures have
        # (bench/2026-09-10/C10-*, C1-RB).  The port is a path that cannot
        # exist, so a seam that stopped being used fails fast instead of
        # reaching a device.
        def head_words(path, k=8):
            raw = open(path, "rb").read(4 * k)
            return ["%08X" % int.from_bytes(raw[i * 4:i * 4 + 4], "big")
                    for i in range(len(raw) // 4)]

        banner = ("---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 "
                  "[16bit](400MHz)\n\r")

        def fake_capture(s, image, fault):
            argv = s["argv"]
            send = argv[argv.index("--send") + 1]
            if s["id"] == "S4":
                after = (banner + "---Ethernet init Okay!\n\r" + PROMPT
                         + "\x1b" * 17 + "\n\rUnknown command !\r\n\r" + PROMPT)
                if fault == "missed-catch":      # K-J's own bytes after C-8's line
                    after = (banner + "Jump to image start=0x80500000...\n\r"
                             "decompressing kernel:\r\nUncompressing Linux... ")
                if fault == "not-taken":         # E0-rz's: no reset at all
                    return (send + "\n\rUnknown command !\r\n\r" + PROMPT
                            + "\x1b" * 17 + "\n\rUnknown command !\r\n\r" + PROMPT)
                return (send + "\r\n\r\nBooting...\r\n\x00chipName: UNKNOWN\n\r"
                        "ramSize: 32M\n\r" + WATCHDOG_MARK + "\n\r\n\r" + after)
            if s["id"] == "S5b":
                return ("%s\n\r8040D4A0:\t%s\t00000000\t00000000\t00000000\n\r%s"
                        % (send, "00000001" if fault == "burn-1" else "00000000",
                           PROMPT))
            if s["id"] == "S6b":
                w = head_words(image)
                if fault == "wrong-head":
                    w[7] = "2610B400"
                return ("%s\n\r80500000:\t%s\n\r80500010:\t%s\n\r%s"
                        % (send, "\t".join(w[:4]), "\t".join(w[4:8]), PROMPT))
            if fault == "no-mark":               # a boot S8 must fail on A1
                return (good + " ").replace("RLXFW-B07\r\n", "")
            return good + " "            # S7: the boot, ending `# ` as it does

        def fake_stages(calls, image, faults, manifest):
            """-> a `_stage_runner` that records every call and opens no port.
            `faults` maps (round, stage id) to the defect its output carries."""
            def run(s, cwd):
                sid, rnd, argv = s["id"], s["round"], s["argv"]
                calls.append((rnd, sid, list(argv)))
                fault = faults.get((rnd, sid))
                if fault == "crash":
                    raise RuntimeError("the process died inside %s" % sid)
                if fault == "slow":         # 1.3: 50 ms, so a stage's start and
                    time.sleep(0.05)        # end differ by more than a wakeup
                if sid == "S2":
                    open(manifest, "w").write("recipe_id\tb1434383\n")
                    return 0, ("== L1: stamp=0 [] recipe=b1434383  <- fake\n"
                               "== L1: make -C %s/top/linux-2.6.30 -j4 vmlinux\n"
                               "== L1: manifest -> %s\n"
                               % (os.path.dirname(manifest), manifest))
                if sid == "S5":
                    open(argv[argv.index("-o") + 1], "w").write(
                        '{"AutoBurning": 0}\n')
                if s["out"]:
                    body = fake_capture(s, image, fault)
                    um = (re.compile(argv[argv.index("--until") + 1].encode())
                          .search(body.encode()) if "--until" in argv else None)
                    open(s["out"] + ".log", "w", newline="").write(body)
                    open(s["out"] + ".timing", "w").write("# offset seconds\n0 0.001\n")
                    json.dump({"sent": argv[argv.index("--send") + 1],
                               "until_offset": um.start() if um else None,
                               "stop_reason": "--until matched at offset %d"
                               % um.start() if um else "--seconds elapsed"},
                              open(s["out"] + ".meta.json", "w"))
                if fault == "touch-image":
                    open(image, "ab").write(b"\x00")
                return 0, ""
            return run

        last = {"head": []}

        def fake_run(n, skip="S2,S3", faults=None, budget=1800.0, plant=(),
                     pin=False, boot_until=DEFAULT_BOOT_UNTIL, dwell=None):
            """-> (outcome, rows, status, calls) of one `--mode bench` run of
            `n` rounds, every stage faked, in an --out-dir of its own.  The
            stages file's `#` lines (1.3: the clock's too) land in last["head"]."""
            od2 = tempfile.mkdtemp(dir=d)
            img = os.path.join(od2, "image.bin")
            open(img, "wb").write(bytes(range(32)) + b"\xaa" * 64)
            for name in plant:
                open(os.path.join(od2, name), "w").write("x")

            class F:
                cell = "L1"; port = "/dev/rlxfw-no-such-port"; host = DEFAULT_HOST
                config = "cfg"; initramfs = "spec"; jobs = 4; variant = "quiet"
                vmlinux = None; cell_top = "top"; label = "rlxfw"; work = "work"
                mode = "bench"; replay_boot = None; recipe_override = "b1434383"
                control = None; attempt = 1; boot_seconds = DEFAULT_BOOT_SECONDS
            F.out_dir, F.image, F.iterations, F.skip = od2, img, n, skip
            F.budget_seconds, F.boot_until = budget, boot_until
            F.image_sha256 = sha256_of(img) if pin else None
            if dwell is not None:
                F.dwell_seconds = dwell
            calls = []
            F._stage_runner = fake_stages(calls, img, faults or {},
                                          os.path.join(od2, "fake.manifest"))
            F._link_runner = fake(good_route, good_neigh)
            try:
                outcome = "rc=%d" % loop_once(F, out=devnull)
            except Refused as exc:
                outcome = "refused" + (" --attempt 2" if "--attempt 2" in str(exc)
                                       else "")
            except StageFailed as exc:
                outcome = "StageFailed@r%s:%s" % (exc.rnd, exc.sid)
            except Exception as exc:        # 1.3: a defect is a FAIL line, not a
                outcome = "crashed: %s" % exc   # traceback that ends the suite
            rows, status, cols = [], None, None
            last["head"] = []
            if os.path.exists(stages_path(F)):
                for line in open(stages_path(F), encoding="utf-8").read().split("\n"):
                    if line.startswith("# status: "):
                        status = line[len("# status: "):]
                    elif line.startswith("#"):
                        last["head"].append(line)
                    elif line:
                        if cols is None:
                            cols = line.split("\t")
                        else:
                            rows.append(dict(zip(cols, line.split("\t"))))
            return outcome, rows, status, calls

        def shape(why=None, **kw):
            """"ok", or "refused" -- and with `why`, "refused" only when the
            refusal's text holds it, so a case can say WHICH guard fired."""
            class S:
                mode = "bench"; iterations = 1; skip = ""
                boot_until = DEFAULT_BOOT_UNTIL; boot_seconds = DEFAULT_BOOT_SECONDS
            for k, v in kw.items():
                setattr(S, k, v)
            try:
                check_shape(S, parse_skip(S))
                return "ok"
            except Refused as exc:
                return "refused" if why is None or why in str(exc) else \
                    "refused by another guard"

        class A3:
            cell = "L1"; out_dir = "bench/2026-09-02"; port = DEFAULT_PORT
            host = DEFAULT_HOST; config = "cfg"; initramfs = "spec"; jobs = 4
            variant = "quiet"; image = "img.bin"; vmlinux = None; cell_top = "top"
            label = "rlxfw"; work = "work"; iterations = 3; skip = ""; mode = "plan"
            boot_until = DEFAULT_BOOT_UNTIL; boot_seconds = DEFAULT_BOOT_SECONDS
        p3 = build_plan(A3)

        # L1 -- refuted by two rounds sharing a name (round 2 would die on
        # console-capture's refusal to overwrite -- the defect M8 guarded), or
        # by a name that does not carry its own round.
        names = [(s["round"], s["argv"][s["argv"].index(f) + 1]) for s in p3
                 if s["argv"] for f in ("--out", "-o") if f in s["argv"]]
        ck("L1", "🔴 N=3: fifteen artefact names, all distinct, each under its "
                 "own -r01..-r03", (15, 15, True),
           (len(names), len(set(nm for _r, nm in names)),
            all(("-r%02d-" % r) in nm for r, nm in names)))
        # L1b -- refuted by a round's upload vetted against ANOTHER round's
        # rescue report, which loader-tftp would accept as current.
        ck("L1b", "and each round's S6 reads the rescue report its own S5 "
                  "wrote", [True] * 3,
           [[s["argv"][s["argv"].index("-o") + 1] for s in p3
             if s["id"] == "S5" and s["round"] == r]
            == [s["argv"][s["argv"].index("--rescue-report") + 1] for s in p3
                if s["id"] == "S6" and s["round"] == r] for r in (1, 2, 3)])

        # L2 -- refuted by round 1's S4 not being `J BFC00000`, or by a later
        # round typing a loader command into rlxfw's shell (seating 12's
        # `J: not found`), or reaching the loader without the ESC stream and
        # the prompt it has to end on.
        s4s = [s["argv"] for s in p3 if s["id"] == "S4"]
        ck("L2", "🔴 round 1's S4 is J BFC00000; rounds 2-3 send busybox "
                 "reboot -f, with --esc-after and --until <RealTek>",
           [True, True, True],
           [("J " + RESET_TARGET) in s4s[0]]
           + [REBOOT_CMD in v and "--esc-after" in v and "--until" in v
              and v[v.index("--until") + 1] == PROMPT
              and ("J " + RESET_TARGET) not in v for v in s4s[1:]])
        buf = io.StringIO()
        render_plan(p3, A3, out=buf)
        cmds = [ln for ln in buf.getvalue().splitlines() if "console-capture.py" in ln]
        ck("L2b", "and --mode plan prints three rounds: the reboot on two "
                  "command lines, J BFC00000 on one", (3, 2, 1),
           (sum(("-- round %d of 3 --" % r) in buf.getvalue() for r in (1, 2, 3)),
            sum(REBOOT_CMD in ln for ln in cmds),
            sum(("J " + RESET_TARGET) in ln for ln in cmds)))

        # L3 -- refuted by a name N=1 derives that a committed card's run did
        # not leave, or a file it left that N=1 no longer derives.  The card
        # is bench/2026-09-10/PREDICTIONS-B18-block17.md's cell C10 (`--cell
        # C10 --out-dir bench/2026-09-10 --skip S2,S3`), and its captures are
        # committed beside it -- so the pre-flight, pointed at that directory,
        # must see exactly those thirteen files as clashes.
        class K:
            cell = "C10"; out_dir = os.path.join(ROOT, "bench", "2026-09-10")
            attempt = 1; iterations = 1
        left = sorted(x for x in os.listdir(K.out_dir) if re.match(
            r"C10-((rz|ab2|2a|boot)\.(log|timing|meta\.json)|rescue\.json)$", x))
        seen = sorted(os.path.basename(p)
                      for p in preflight_artefacts(K, {"S2", "S3"}))
        ck("L3", "🔴 N=1 keeps today's names: the pre-flight sees exactly the "
                 "13 files a committed card's run left", (13, True),
           (len(left), seen == left))
        K.iterations = 2
        ck("L3b", "and at N=2 not one of those names is derived: each round "
                  "has its own", [], preflight_artefacts(K, {"S2", "S3"}))

        # L4 -- refuted by any stage run before the refusal (round 1 would
        # spend a reset, a rescue and an upload before round 2 met the file),
        # or by a refusal that does not name the flag that resolves it.
        o, rows, status, calls = fake_run(2, plant=("L1-r02-ab2.log",))
        ck("L4", "🔴 a clash in ROUND 2's names is REFUSED before round 1 runs: "
                 "no stage called, no stages file", ("refused --attempt 2", 0, None),
           (o, len(calls), status))
        # L4b -- refuted by a previous run's stages file being accepted: the
        # first rewrite would replace a record nothing else holds.
        o, rows, status, calls = fake_run(1, plant=("L1.stages.tsv",))
        ck("L4b", "and so is a previous run's stages file", ("refused --attempt 2", 0),
           (o, len(calls)))

        # L5 -- refuted by a row missing for any stage of any round, rows out
        # of order, or a row that is not ok.  S2/S3 go through the fake too.
        order = (["0:S2", "0:S3"] + ["1:" + x for x in ROUND_STAGES]
                 + ["2:" + x for x in ROUND_STAGES])
        t_before = raw_now()
        o, rows, status, calls = fake_run(2, skip="")
        t_after = raw_now()
        rows_l5 = rows
        ck("L5", "🔴 a faked bench run of N=2 writes S2, S3 and 2 x 8 round "
                 "rows, in order, every one ok", ("rc=0", 18, True, True),
           (o, len(rows), ["%s:%s" % (r["round"], r["stage"]) for r in rows] == order,
            all(r["result"] == "ok" for r in rows)))
        # L5b -- refuted by an end before its start, a start earlier than the
        # row above it, `seconds` that is not end - start, or a time that is
        # not this host's CLOCK_MONOTONIC_RAW (1.3; relative times would sit
        # below t_before): absolute is what lets a row sit on a capture's
        # timeline.  Where MONOTONIC and RAW agree -- a CI runner -- this cannot
        # tell the two apart; L5f is the case that can.
        stamps = [(float(r["start_raw"]), float(r["end_raw"]), float(r["seconds"]))
                  for r in rows if r.get("start_raw")]
        ck("L5b", "and every row: start <= end, starts never go back, seconds "
                  "= end - start, and all of it absolute CLOCK_MONOTONIC_RAW",
           (18, True, True, True, True),
           (len(stamps), all(s0 <= s1 for s0, s1, _x in stamps),
            [s0 for s0, _s1, _x in stamps] == sorted(s0 for s0, _s1, _x in stamps),
            all(abs(s1 - s0 - x) < 2e-6 for s0, s1, x in stamps),
            bool(stamps) and t_before <= stamps[0][0] and stamps[-1][1] <= t_after))
        # L5c -- refuted by a last line that still reads `running`, or none.
        ck("L5c", "and its last line says the run CLOSED",
           "closed -- 2 of 2 round(s), every assertion held", status)
        # L5d -- refuted by a stages file from a mode that runs no stage: with
        # no --out-dir it would land wherever the run was started.
        B.mode, B.skip, B.out_dir = "replay", "", tempfile.mkdtemp(dir=d)
        rc5 = loop_once(B, out=devnull)
        ck("L5d", "and --mode replay, which runs no stage, writes no stages file",
           (0, False), (rc5, os.path.exists(stages_path(B))))
        B.out_dir = None
        # L5e -- refuted by completed rows missing after the process died
        # mid-stage (a file written only at the end), or by a status that
        # claims the run ended.  `running` is the reading that it did not.
        o, rows, status, calls = fake_run(2, faults={(2, "S5"): "crash"})
        ck("L5e", "🔴 a run that DIES inside round 2's S5 leaves every row "
                  "before it on disk, and a status that says it was running",
           ("crashed: the process died inside S5", 11, "running -- round 2 S4 done"),
           (o, len(rows), status))

        # ---- L5f/L5g: 1.3, the clock.  🔴 On a CI runner MONOTONIC and RAW
        # agree to a few ms, so L5b's bracket passes a tool that still reads
        # time.monotonic(): two counters agreeing is not evidence while they run
        # at one rate (CLAUDE.md).  These run with CLOCK_MONOTONIC's readers
        # patched in this process to half rate, +1000 s, by tools/clockshim.py's
        # own install() -- imported, not copied -- and restored after; RAW passes
        # through.  A MONOTONIC stamp then lands hundreds of seconds outside the
        # bracket, at the desk and on CI alike.  Stamps are asserted, never how
        # long a sleep lasted: kernel timers are out of the shim's reach.
        def load_shim():
            saved = sys.dont_write_bytecode
            sys.dont_write_bytecode = True          # no .pyc written into tools/
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "looprun_clockshim", os.path.join(ROOT, "tools", "clockshim.py"))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod, None
            except Exception as exc:                # a missing shim is a FAIL line
                return None, "%s: %s" % (type(exc).__name__, exc)
            finally:
                sys.dont_write_bytecode = saved
        shim, shim_err = load_shim()
        readers = ("monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns",
                   "clock_gettime", "clock_gettime_ns")

        def under_shim(fn):
            """-> (took, fn()).  `took` is True when the shim's own check() saw
            the patch take, else why not; the readers come back either way."""
            if shim is None:
                return "no tools/clockshim.py: %s" % shim_err, None
            saved = {k: getattr(time, k) for k in readers}
            try:
                true_mono = shim.install(0.5, 1000.0)
                try:
                    shim.check(true_mono, 1000.0)
                    took = True
                except shim.Refused as exc:
                    took = "the shim did not take: %s" % exc
                return took, fn()
            finally:
                for k, v in saved.items():
                    setattr(time, k, v)

        def mono_bracketed(fn):
            """-> (MONOTONIC before, fn(), MONOTONIC after), read through the
            time module -- inside under_shim, that is the patched clock."""
            m0 = time.clock_gettime(time.CLOCK_MONOTONIC)
            got = fn()
            return m0, got, time.clock_gettime(time.CLOCK_MONOTONIC)

        # L5f -- refuted by any row stamped on anything but RAW (it would sit
        # ~1000 s off), by fewer rows than L5's, or by a shim that did not take.
        t_before = raw_now()
        took, res = under_shim(lambda: mono_bracketed(lambda: fake_run(2, skip="")))
        t_after = raw_now()
        m_before, res, m_after = res if res else (None, None, None)
        o5f, rows5f = (res[0], res[1]) if res else (None, [])
        head5f = list(last["head"]) if res else []
        s5f = [(float(r["start_raw"]), float(r["end_raw"])) for r in rows5f
               if r.get("start_raw")]
        ck("L5f", "🔴 with CLOCK_MONOTONIC patched to half rate, +1000 s, every "
                  "row still sits inside the harness's RAW bracket",
           (True, "rc=0", 18, True),
           (took, o5f, len(s5f), bool(s5f) and all(t_before <= x0 <= x1 <= t_after
                                                   for x0, x1 in s5f)))
        # L5g -- refuted by a header naming any clock but CLOCK_MONOTONIC_RAW
        # exactly (a whole word: CLOCK_MONOTONIC is a prefix of it), a boot_id
        # other than this boot's, 1.2's column names, or a start/end pair that is
        # not one RAW read and one MONOTONIC read each: under L5f's shim the
        # `_raw` keys must sit in the RAW bracket and `mono_at_*` in the patched
        # MONOTONIC bracket, which lies ~1000 s away -- a header that read RAW
        # twice, or went round the time module, lands outside one of them.
        # Brackets and not the pair's ratio: 量 2026-09-23 23:4x, one 0.415 s run
        # read MONOTONIC/RAW 1.078 where a 10 s window read 0.998 -- 推 a read
        # descheduled inside one pair at load average 5 -- and ordering is the one
        # thing a preemption cannot change.
        kv = {}
        for line in head5f:
            for mark, cut in (("# clock=", 2), ("# end: ", 7)):
                if line.startswith(mark):
                    kv.update(tok.split("=", 1) for tok in line[cut:].split()
                              if "=" in tok)

        def within(lo, keys, hi):
            try:
                vals = [float(kv[k]) for k in keys]
            except (KeyError, ValueError, TypeError):
                return False
            return lo is not None and lo <= vals[0] <= vals[-1] <= hi
        try:
            with open("/proc/sys/kernel/random/boot_id") as fh:
                boot = fh.read().strip()
        except OSError as exc:
            boot = "the harness cannot read it: %s" % exc
        ck("L5g", "and the header names CLOCK_MONOTONIC_RAW and this boot's "
                  "boot_id, the columns are 1.3's, and start/end each pair one "
                  "RAW read with one MONOTONIC read",
           ("CLOCK_MONOTONIC_RAW", True, (True, False), True, True),
           (kv.get("clock"), kv.get("boot_id") == boot,
            ("start_raw" in rows5f[0], "start_mono" in rows5f[0]) if rows5f else None,
            within(t_before, ("start_raw", "end_raw"), t_after),
            within(m_before, ("mono_at_start", "mono_at_end"), m_after)))

        # L6 -- refuted by any round-3 row, any round-2 row after S6b, a last
        # row that is not round 2's S6b failing on A0c, or a status that does
        # not say where the run stopped.
        o, rows, status, calls = fake_run(3, faults={(2, "S6b"): "wrong-head"})
        ck("L6", "🔴 round 2 failing at S6b stops the run there, and the record "
                 "names round 2 S6b", ("StageFailed@r2:S6b", "2 S6b FAIL A0c", 16, True),
           (o, " ".join((rows[-1]["round"], rows[-1]["stage"], rows[-1]["result"]))
            if rows else None, len(rows),
            (status or "").startswith("STOPPED at round 2 S6b")))
        ck("L6b", "and nothing after it was even attempted: no round-2 S7, no "
                  "round 3", [], [c[:2] for c in calls if c[0] == 3
                                 or (c[0] == 2 and c[1] == "S7")])
        # L6c -- refuted by round 2 starting after round 1's S8 failed.  An S8
        # failure is not an exception -- the round's assertions are printed
        # first -- so it stops the run by a path of its own.
        o, rows, status, calls = fake_run(2, faults={(1, "S7"): "no-mark"})
        ck("L6c", "🔴 and a round that fails at S8 stops the run too: exit 1, "
                  "no round-2 stage", ("rc=1", "STOPPED at round 1 S8 -- A1 failed", []),
           (o, status, [c[:2] for c in calls if c[0] == 2]))

        # L7 -- refuted by round 2's S4 skipped too (round 2 would type into
        # the shell round 1 booted), or round 1's run (the board is already at
        # a cold prompt, and a reset re-stages 0x80500000 for nothing).
        o, rows, status, calls = fake_run(2, skip="S2,S3,S4")
        ck("L7", "🔴 --skip S4 with N=2 skips ROUND 1's reset only; round 2's "
                 "runs, and it is the reboot",
           ("rc=0", [("1", "skipped"), ("2", "ok")], [REBOOT_CMD]),
           (o, [(r["round"], r["result"]) for r in rows if r["stage"] == "S4"],
            [c[2][c[2].index("--send") + 1] for c in calls if c[1] == "S4"]))
        A3.iterations, A3.skip = 2, "S2,S3,S4"
        buf = io.StringIO()
        render_plan(build_plan(A3), A3, out=buf)
        ck("L7b", "and --mode plan says so in words, then renders round 2's "
                  "reboot", (True, 1),
           ("--skip S4: round 1 only" in buf.getvalue(),
            sum(1 for ln in buf.getvalue().splitlines()
                if "console-capture.py" in ln and REBOOT_CMD in ln)))

        # L8 -- refuted by `--skip S6` accepted with N >= 2 (round 2's reset
        # re-stages the vendor's image, and S7 would jump into it), or refused
        # at N=1, where a card may legitimately skip it.
        ck("L8", "🔴 --skip S6 with N=2 is REFUSED", "refused",
           shape(iterations=2, skip="S6"))
        ck("L8b", "and --skip S6 with N=1 is not: the rule is about rounds",
           "ok", shape(skip="S6"))

        # L9 -- refuted by round 2 uploading after its burn flag read back
        # 00000001: a read-back that guards round 1 only.
        o, rows, status, calls = fake_run(2, faults={(2, "S5b"): "burn-1"})
        ck("L9", "🔴 the burn-flag read-back runs in ROUND 2 too, and 00000001 "
                 "there stops the run before round 2's upload",
           ("StageFailed@r2:S5b", "FAIL A0b", []),
           (o, rows[-1]["result"] if rows else None,
            [c[:2] for c in calls if c[0] == 2 and c[1] in ("S6", "S6b", "S7")]))
        # L9b -- refuted by the refusal at N=2 coming from anything but the
        # S5b guard itself: the per-round rule refuses it too, and a case that
        # either guard satisfies cannot tell when the safety one is gone.
        ck("L9b", "and --skip S5b with N=2 is still REFUSED, by the burn-flag "
                  "guard itself", "refused",
           shape(why="G2/H1a", iterations=2, skip="S5b"))

        # L10 -- refuted by `--skip S8` accepted.  Until 1.2 it was, and did
        # nothing: the loop broke at S8 and asserted regardless.  L8b is the
        # control that this refusal does not fire on every skip.
        ck("L10", "🔴 --skip S8 is REFUSED: it used to be accepted and ignored",
           "refused", shape(skip="S8"))

        # L11 -- refuted by a round started after the budget was spent, or a
        # run that stops without saying it was the budget.
        o, rows, status, calls = fake_run(3, budget=0.0)
        ck("L11", "🔴 --budget-seconds bounds the whole run: at 0, round 1 runs "
                  "(one in flight is never cut) and round 2 never starts",
           ("rc=0", 0, True),
           (o, sum(1 for r in rows if r["round"] in ("2", "3")),
            (status or "").startswith("budget -- 1 of 3 round(s) ran")))
        # L11b -- 1.3: refuted by a budget read on MONOTONIC.  Under the shim a
        # MONOTONIC budget reads ~1000 s spent before round 2 and stops there; on
        # RAW a 100 s budget has barely begun after one faked round.  L11 cannot
        # see the clock: at 0 every clock has spent it.
        tookb, resb = under_shim(lambda: fake_run(3, budget=100.0))
        ck("L11b", "and the budget runs on RAW: under the shim a 100 s budget "
                   "lets all three faked rounds run",
           (True, "rc=0", "closed -- 3 of 3 round(s), every assertion held"),
           (tookb, resb[0] if resb else None, resb[2] if resb else None))

        # L12 -- refuted by 0 or 100 accepted, or 99 refused.
        ck("L12", "--iterations 0 and 100 are REFUSED; 99, the most -rNN can "
                  "carry, is not", ["refused", "refused", "ok"],
           [shape(iterations=0), shape(iterations=100), shape(iterations=99)])

        # L13 -- refuted by any pair other than the four written here.  Four
        # committed captures, one per combination, so each assertion is shown
        # failing ALONE on the device's own bytes: C1-RB (a reboot, caught),
        # K-J (a warm reset whose ESC window was missed: C-8's line, then the
        # vendor), E0-rz (a `J BFC00000` the loader did not take: a prompt and
        # no reset), SN-rz (`J BFC00000` into rlxfw's shell: neither).
        def pair(rel):
            t = open(os.path.join(ROOT, rel), encoding="utf-8",
                     errors="replace").read()
            return (assert_reset(t)[0][0], assert_loader_prompt(t)[0][0])
        ck("L13", "🔴 A0 and A0a each fail ALONE, on four committed captures",
           [(True, True), (True, False), (False, True), (False, False)],
           [pair(p) for p in ("bench/2026-09-10/C1-RB.log",
                              "bench/2026-08-31c/K-J.log",
                              "bench/2026-09-21/E0-rz.log",
                              "bench/2026-09-04/SN-rz.log")])
        # L14 -- refuted by S5 called after a reset whose prompt was not caught
        # (it would type into the vendor's firmware), or the stop blamed on A0.
        o, rows, status, calls = fake_run(2, faults={(2, "S4"): "missed-catch"})
        ck("L14", "🔴 and A0a is WIRED: a round-2 reset whose ESC window was "
                  "missed stops the run at S4, on A0a alone, before S5",
           ("StageFailed@r2:S4", "FAIL A0a", []),
           (o, rows[-1]["result"] if rows else None,
            [c[:2] for c in calls if c[0] == 2 and c[1] != "S4"]))
        # L14b -- refuted by a run going on past a `J BFC00000` the loader did
        # not take (E0-rz's bytes): a prompt, and no reset behind it.
        o, rows, status, calls = fake_run(2, faults={(1, "S4"): "not-taken"})
        ck("L14b", "and so is A0: a reset that did not happen stops round 1 at "
                   "S4, on A0 alone", ("StageFailed@r1:S4", "FAIL A0", 1),
           (o, rows[-1]["result"] if rows else None, len(calls)))

        # L15 -- refuted by round 2 uploading a file that changed after the
        # pre-flight pinned it.  S6b cannot see that: it derives its
        # expectation from the same changed file.  FW-100.
        o, rows, status, calls = fake_run(2, faults={(1, "S7"): "touch-image"},
                                          pin=True)
        ck("L15", "🔴 --image-sha256 is re-taken before EVERY upload: a file "
                  "changed after round 1 stops round 2 at S6, before it runs",
           ("StageFailed@r2:S6", []),
           (o, [c[:2] for c in calls if c[0] == 2 and c[1] in ("S6", "S6b", "S7")]))
        ck("L15b", "and an unchanged pinned file passes every re-take",
           "rc=0", fake_run(2, pin=True)[0])

        # ---- T: TERM-1, 1.2 -- the boot cells end on an event, not a silence.
        # T1 -- refuted by any round's S7 still carrying --idle, or an --until
        # with no --seconds cap behind it.
        s7s = [s["argv"] for s in p3 if s["id"] == "S7"]
        ck("T1", "🔴 every round's S7 ends on --until <the shell prompt>, capped "
                 "by --seconds, with no --idle", [True] * 3,
           [("--until" in v and v[v.index("--until") + 1] == DEFAULT_BOOT_UNTIL
             and "--seconds" in v and "--idle" not in v) for v in s7s])
        # T2 -- refuted by any round's S4 carrying --idle, ending on anything
        # but the loader's prompt, or losing --esc-after or --seconds as caps.
        ck("T2", "🔴 and every round's S4 ends on --until <RealTek>, with "
                 "--esc-after and --seconds as caps and no --idle", [True] * 3,
           [("--until" in v and v[v.index("--until") + 1] == PROMPT
             and "--esc-after" in v and "--seconds" in v and "--idle" not in v)
            for v in s4s])
        # T3 -- refuted by the default missing a committed rlxfw boot, or
        # matching before its last byte (the capture would end with boot
        # output still to come).  Over BYTES, as console-capture matches.
        raw = open(os.path.join(ROOT, "bench", "2026-09-10", "C10-boot.log"),
                   "rb").read()
        m3 = re.compile(DEFAULT_BOOT_UNTIL.encode()).search(raw)
        ck("T3", "🔴 the default --boot-until matches a committed rlxfw boot, "
                 "and the match ends on its LAST byte", (True, True),
           (m3 is not None, m3 is not None and m3.end() == len(raw)))
        # T4 -- refuted by A4 failing on a capture that ended ON the pattern
        # (the prompt would not be inside it), or passing on one cut before it.
        gb = good + " "
        m4 = re.compile(DEFAULT_BOOT_UNTIL.encode()).search(gb.encode())
        ck("T4", "🔴 A4 holds on a boot that ENDED on the pattern and fails on "
                 "one cut before it: the prompt is inside the pattern",
           (True, False), (assert_boot(gb[:m4.end()], "b1434383")[3][0],
                           assert_boot(gb[:m4.start()], "b1434383")[3][0]))
        # T5 -- refuted by the default matching the loader's echo of the jump
        # (S7 would end before the kernel printed a byte), or by a pattern
        # that does match it being accepted.
        ck("T5", "🔴 the default does not match the loader's echo of `J "
                 "80500000`; a --boot-until that does is REFUSED",
           (False, "refused", "refused", "ok"),
           (bool(re.compile(DEFAULT_BOOT_UNTIL.encode()).search(S7_ECHO.encode())),
            shape(boot_until="Jump to"), shape(boot_until="80500000"), shape()))
        # T5b -- refuted by the refusal arriving after a stage ran, or firing
        # where S7 never runs (a guard with nothing to guard teaches its
        # reader to feed it anything).
        o, rows, status, calls = fake_run(2, boot_until="Jump to")
        ck("T5b", "and it is refused before any stage runs -- and not at all "
                  "in --mode replay, where S7 never runs", ("refused", 0, "ok"),
           (o, len(calls), shape(mode="replay", boot_until="Jump to")))
        # T6 -- refuted by any of the three accepted -- a pattern console-capture
        # cannot compile, one that matches at offset 0, a boot with no cap --
        # or refused by a guard other than its own (an empty pattern also
        # matches the echo, so the echo check would hide a missing one).
        ck("T6", "an unparsable or empty --boot-until, and --boot-seconds 0, "
                 "are each REFUSED by their own guard", ["refused"] * 3,
           [shape(why="not a regex", boot_until="job (control"),
            shape(why="is empty", boot_until=""),
            shape(why="--boot-seconds", boot_seconds=0.0)])
        # T7 -- refuted by a backslash in the default.
        ck("T7", "the default carries no backslash: the plan renders it into "
                 "the card, and a quoted heredoc loses one level", False,
           "\\" in DEFAULT_BOOT_UNTIL)

        # ---- W: the dwell, 1.3 (s107 srvlog REPORT § 3 A).  Each case's
        # comment says what refutes it.
        class PW:
            cell = "L1"; out_dir = "bench/2026-09-02"; port = DEFAULT_PORT
            host = DEFAULT_HOST; config = "cfg"; initramfs = "spec"; jobs = 4
            variant = "quiet"; image = "img.bin"; vmlinux = None; cell_top = "top"
            label = "rlxfw"; work = "work"; iterations = 2; skip = "S2,S3,S4"
            mode = "plan"; boot_until = DEFAULT_BOOT_UNTIL
            boot_seconds = DEFAULT_BOOT_SECONDS; recipe_override = "b1434383"

        class PW0(PW):
            dwell_seconds = 0.0

        class PW3(PW):
            dwell_seconds = 0.3
        p0, p3w = build_plan(PW0), build_plan(PW3)

        # W1 -- refuted by S9 in a plan with no dwell; a round without one when
        # D > 0; S9 anywhere but straight after S8; or -- 🔴 the :626 trap --
        # S8 losing its `-boot` path to S9, which has S8 read None + ".log" on
        # the bench, after the upload.
        def s9_after_s8(plan, r):
            return [s["id"] for s in plan if s["round"] == r][-2:] == ["S8", "S9"]
        ck("W1", "🔴 S9 is in a plan only when --dwell-seconds > 0 -- then right "
                 "after S8 in every round -- and S8 keeps its -boot path",
           (0, [True, True], [True, True]),
           (sum(1 for s in p0 if s["id"] == "S9"),
            [s9_after_s8(p3w, r) for r in (1, 2)],
            [[s["out"] for s in p3w if s["round"] == r and s["id"] in ("S8", "S9")]
             == [stem(PW3, r) + "-boot", None] for r in (1, 2)]))

        # W2 -- refuted by a round with no S9 row (the last included: the card's
        # next cell resets the board too), an S9 ending less than D past its
        # round's S7 end, or round 2's reset starting less than D after round
        # 1's prompt.  Under the shim, so a dwell timed on MONOTONIC ends at
        # once, at the desk and on CI alike.  Each S7 takes 50 ms, so a dwell
        # anchored on S7's START ends 50 ms short -- far more than a wakeup's
        # overshoot.  The file prints microseconds, so each comparison allows
        # its 2 us of rounding.
        def dwell_held(rows, dd, n):
            at = {(r["round"], r["stage"]): i for i, r in enumerate(rows)}

            def t(r, sid, col):
                i = at.get((str(r), sid))
                v = rows[i].get(col) if i is not None else None
                return float(v) if v else None

            def ge(x, y):
                return x is not None and y is not None and x - y >= dd - 2e-6
            return (all(at.get((str(r), "S9"), -1) == at.get((str(r), "S8"), -9) + 1
                        for r in range(1, n + 1)),
                    all(ge(t(r, "S9", "end_raw"), t(r, "S7", "end_raw"))
                        for r in range(1, n + 1)),
                    all(ge(t(r + 1, "S4", "start_raw"), t(r, "S7", "end_raw"))
                        for r in range(1, n)))
        slow7 = {(1, "S7"): "slow", (2, "S7"): "slow"}
        took2, res2 = under_shim(lambda: fake_run(2, skip="", dwell=0.3, faults=slow7))
        o2, rows2 = (res2[0], res2[1]) if res2 else (None, [])
        ck("W2", "🔴 --dwell-seconds 0.3, N=2, under the shim: 20 rows, S9 closes "
                 "each round (the last too), each >= 0.3 RAW-s past its S7's "
                 "end, and round 2's reset >= 0.3 s after round 1's prompt",
           (True, "rc=0", 20, (True, True, True)),
           (took2, o2, len(rows2), dwell_held(rows2, 0.3, 2)))
        # W3 -- W2's own control: the same reading, in the same harness, over a
        # planted run WITHOUT the dwell must fail every part, or W2 cannot fail.
        took3, res3 = under_shim(lambda: fake_run(2, skip="", faults=slow7))
        ck("W3", "🔴 and W2's reading FAILS on a planted run with no dwell: no "
                 "S9 rows, and round 2's reset follows round 1's prompt by "
                 "milliseconds", (True, (False, False, False)),
           (took3, dwell_held(res3[1] if res3 else [], 0.3, 2)))

        # W4 -- refuted by any of -1, 61, NaN, inf accepted, a refusal from a
        # guard other than the dwell's own, or 0, 2 or 60 refused.
        ck("W4", "--dwell-seconds -1, 61, NaN and inf are each REFUSED by the "
                 "dwell's own guard; 0, 2 and 60 are not",
           ["refused"] * 4 + ["ok"] * 3,
           [shape(why="must lie in", dwell_seconds=v)
            for v in (-1.0, 61.0, float("nan"), float("inf"))]
           + [shape(dwell_seconds=v) for v in (0.0, 2.0, 60.0)])
        # W4b -- refuted by --skip S9 accepted with a dwell (S9 IS the dwell),
        # --skip S7 accepted with one at N=1 (S9 would anchor on nothing), or
        # either refusal firing without a dwell: then --skip S9 must stay M5's
        # "no such stage", and --skip S7 stay allowed.
        ck("W4b", "and the skips a dwell cannot run with are refused by its "
                  "guard -- S9, and S7 at N=1 -- while without one S9 is still "
                  "'no such stage' and S7 still allowed",
           ["refused", "refused", "refused", "ok"],
           [shape(why="--dwell-seconds 0 is", skip="S9", dwell_seconds=2.0),
            shape(why="no such stage", skip="S9"),
            shape(why="anchored on", skip="S7", dwell_seconds=2.0),
            shape(skip="S7")])
        # W5 -- refuted by --dwell-seconds 0 changing anything but the header's
        # record of it: its rows (not their times) must be L5's, and its plan
        # must render byte for byte as a plan without the argument does.
        o5w, rows5w, _st, _c = fake_run(2, skip="", dwell=0.0)
        head5w = list(last["head"])

        def key(rows):
            return [(r["round"], r["stage"], r["name"], r["kind"], r["rc"],
                     r["result"]) for r in rows]
        b0, b1 = io.StringIO(), io.StringIO()
        render_plan(build_plan(PW0), PW0, out=b0)
        render_plan(build_plan(PW), PW, out=b1)
        ck("W5", "--dwell-seconds 0 is 1.2's run: L5's 18 rows in L5's order, "
                 "the plan byte for byte a plan without the argument, and "
                 "dwell-seconds=0 in the header",
           ("rc=0", 18, True, True, True),
           (o5w, len(rows5w), key(rows5w) == key(rows_l5),
            b0.getvalue() == b1.getvalue(),
            any(h.startswith("# cell=") and h.endswith(" dwell-seconds=0")
                for h in head5w)))

        # ---- F: FW-124, the contract a card's HOST cell is checked against.
        # F1 -- refuted by refuse_args permitting card A's LR line with
        # --recipe-override removed (in bench, or rendered as a plan -- the gap
        # the 2026-09-23 one-off hit: plan ran check_shape alone), refusing the
        # whole line, permitting a malformed pin or a bench line with no
        # --image (M11 cannot see that one go: loop_once's isfile('') refuses
        # after it, and cardcheck calls refuse_args alone), or needing a file,
        # the clock or the environment to decide: the image it names does not
        # exist, and CLOCK_MONOTONIC_RAW is deleted from the time module.
        def no_raw(fn):
            saved = time.CLOCK_MONOTONIC_RAW
            del time.CLOCK_MONOTONIC_RAW
            try:
                return fn()
            finally:
                time.CLOCK_MONOTONIC_RAW = saved

        lr = ["--mode", "bench", "--out-dir", "bench/2026-09-23", "--skip",
              "S2,S3,S4", "--recipe-override", "a2c56bc8", "--cell", "P1L",
              "--image", os.path.join(d, "no-such-image.bin"),
              "--image-sha256", "88" * 32, "--iterations", "3"]

        def verdict_of(argv):
            try:
                refuse_args(build_parser().parse_args(argv))
                return "ok"
            except Refused as exc:
                t = str(exc)
                return ("refused: recipe" if "--recipe-override" in t else
                        "refused: hex" if "64 hex" in t else
                        "refused: image" if t.startswith("no --image") else
                        "refused: " + t[:40])

        def edit(argv, flag, val=None):
            i = argv.index(flag)
            return argv[:i] + ([flag, val] if val is not None else []) + argv[i + 2:]
        ck("F1", "🔴 refuse_args in-process: card A's LR line passes, in bench "
                 "and as a plan; without --recipe-override both refuse, and so "
                 "do a malformed pin and a bench line with no --image -- with "
                 "no image on disk and no RAW clock",
           ["ok", "refused: recipe", "ok", "refused: recipe", "refused: hex",
            "refused: image"],
           no_raw(lambda: [verdict_of(lr),
                           verdict_of(edit(lr, "--recipe-override")),
                           verdict_of(edit(lr, "--mode", "plan")),
                           verdict_of(edit(edit(lr, "--mode", "plan"),
                                           "--recipe-override")),
                           verdict_of(edit(lr, "--image-sha256", "deadbeef")),
                           verdict_of(edit(edit(lr, "--image"), "--image-sha256"))]))

        # F2 -- refuted by --mode plan rendering a run bench mode refuses (until
        # 1.3 plan ran check_shape alone).  Through the program, as M8 is.
        def run_err(argv):
            p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
            return p.returncode, p.stderr.decode("utf-8", "replace")
        plan_skip = [sys.executable, os.path.join(ROOT, "tools", "looprun.py"),
                     "--mode", "plan", "--iterations", "3", "--skip", "S2,S3,S4"]
        rc_a, err_a = run_err(plan_skip)
        rc_b, _err_b = run_err(plan_skip + ["--recipe-override", "b1434383"])
        ck("F2", "and main's --mode plan calls it: a plan skipping S2 with no "
                 "--recipe-override exits 2 with that reason, and with one, 0",
           (2, True, 0), (rc_a, "--recipe-override" in err_a, rc_b))

        # ---- K: 1.3, a Python without CLOCK_MONOTONIC_RAW (P2-4 spec § 1).
        # K1 -- refuted by such a Python getting past the pre-flight; by the
        # refusal coming from anything but the clock -- the image named does not
        # exist, so a clock check placed after the image pre-flight would report
        # the image instead; by a stage called or a stages file written first;
        # or, with the clock present, by the clock's refusal firing at all.
        od3 = tempfile.mkdtemp(dir=d)
        kcalls = []

        class KF:
            cell = "L1"; port = "/dev/rlxfw-no-such-port"; host = DEFAULT_HOST
            config = "cfg"; initramfs = "spec"; jobs = 4; variant = "quiet"
            vmlinux = None; cell_top = "top"; label = "rlxfw"; work = "work"
            mode = "bench"; replay_boot = None; recipe_override = "b1434383"
            control = None; attempt = 1; boot_seconds = DEFAULT_BOOT_SECONDS
            boot_until = DEFAULT_BOOT_UNTIL; iterations = 1; skip = "S2,S3"
            budget_seconds = 1800.0; image_sha256 = None; out_dir = od3
        KF.image = os.path.join(od3, "absent.bin")
        KF._stage_runner = lambda s, cwd: (kcalls.append(s["id"]), (0, ""))[1]

        def k1():
            try:
                loop_once(KF, out=devnull)
                return "no refusal"
            except Refused as exc:
                t = str(exc)
                return ("clock" if CLOCK in t else
                        "image" if "not a regular file" in t else "other: " + t[:40])
            except Exception as exc:        # a refusal that is not one is a FAIL
                return "crashed: " + type(exc).__name__
        ck("K1", "🔴 with CLOCK_MONOTONIC_RAW deleted, loop_once refuses on the "
                 "clock before the image pre-flight, any stage or the stages "
                 "file; with it present, the next refusal is the image's",
           ("clock", [], False, "image"),
           (no_raw(k1), list(kcalls), os.path.exists(stages_path(KF)), k1()))
        # K2 -- refuted by main() letting that refusal out as a traceback, or
        # exiting other than 2 (spec § 1: "refuses with exit 2 and a reason").
        # M8c is the same command with the clock present, and it exits 0.
        code = ("import runpy, sys, time; del time.CLOCK_MONOTONIC_RAW; "
                "sys.argv = sys.argv[1:]; "
                "runpy.run_path(sys.argv[0], run_name='__main__')")
        rc_k, err_k = run_err([sys.executable, "-c", code,
                               os.path.join(ROOT, "tools", "looprun.py"),
                               "--mode", "replay", "--replay-boot", pre,
                               "--recipe-override", "b1434383"])
        ck("K2", "and main() turns it into exit 2 with the reason, not a "
                 "traceback", (2, True, False),
           (rc_k, CLOCK in err_k, "Traceback" in err_k))

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


def build_parser():
    """The one parser main() uses (FW-124, 1.3): a card's HOST line is parsed with
    it and handed to refuse_args, in-process, with no second copy to drift."""
    ap = argparse.ArgumentParser(description="one edit->result iteration (R4-3)")
    ap.add_argument("--mode", choices=["plan", "replay", "desk", "bench"],
                    default="plan",
                    help="plan: print the commands and run none. replay: run no\nstage at all and assert over --replay-boot -- this is what the\nself-test drives. desk: run S2/S3 for real, replay the boot.\nbench: all of it, against a live board")
    ap.add_argument("--cell", default="L1")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--attempt", type=int, default=1,
                    help="attempt number. 1 writes <cell>-rz.log etc; N>1 "
                         "writes <cell>-attN-rz.log, so a failed run can be "
                         "retried without --force destroying its evidence")
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
                    help="rounds of S4..S8 on one power press (LOOP-3), 1..99. "
                         "Round 1 starts at the loader prompt; rounds 2..N reach "
                         "it through `busybox reboot -f`. With N >= 2 every "
                         "round's artefacts carry -rNN, and --skip may name S4 "
                         "(round 1 only) but no other per-round stage. Bounded, "
                         "and so is --budget-seconds")
    ap.add_argument("--budget-seconds", type=float, default=1800.0,
                    help="stop starting new rounds once this much time has "
                         "gone (CLOCK_MONOTONIC_RAW since 1.3). It does not "
                         "interrupt one in flight")
    ap.add_argument("--boot-until", default=DEFAULT_BOOT_UNTIL,
                    help="the regex S7's capture ends on (TERM-1). The default "
                         "is the shell prompt rlxfw's /init reaches. It must "
                         "include the prompt: console-capture drains only 50 ms "
                         "after a match, and S8's A4 reads it")
    ap.add_argument("--boot-seconds", type=float, default=DEFAULT_BOOT_SECONDS,
                    help="S7's --seconds cap, paid only when --boot-until never "
                         "arrives")
    ap.add_argument("--dwell-seconds", type=float, default=0.0,
                    help="1.3: S9 holds the board at rlxfw's prompt until S7's "
                         "end + this many seconds (CLOCK_MONOTONIC_RAW), in every "
                         "round, the last included, so the host's next ARP "
                         "broadcast meets a board that answers. 0, the default, "
                         "is no S9: 1.2's run. 0..60")
    ap.add_argument("--self-test", action="store_true")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        # FW-124: every argument-only refusal first, in every mode -- plan too --
        # before anything is read; the self-test is its own case inside it.
        refuse_args(a)
        if a.self_test:
            clock_id()
            return selftest()
        if a.mode == "plan":
            render_plan(build_plan(a), a)
            return 0
        # Until 1.2 `--iterations` above 1 was refused here (讀 2026-09-02):
        # S4 was a loader command sent into the shell iteration 1 left, and no
        # name carried an iteration index.  Rounds are loop_once's now.
        return loop_once(a)
    except Refused as exc:
        print("looprun: %s" % exc, file=sys.stderr)
        return 2
    except StageFailed as exc:
        where = exc.sid if rounds(a) < 2 else "round %s %s" % (exc.rnd, exc.sid)
        print("looprun: STOPPED at %s -- %s" % (where, exc.why), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
