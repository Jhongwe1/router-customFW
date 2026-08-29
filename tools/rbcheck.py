#!/usr/bin/env python3
"""rbcheck -- the result block, on both channels, as arithmetic.

`R1h-3`'s DoD says *"the result block agrees on both channels"*.  Until today
nothing in this repository parsed a result block, so that clause was an eyeball
over a 161-line hex dump.  This makes it three numbers that must be equal:

  (1) the UART's own ``rlxprobe: sum=`` line, printed by the running payload;
  (2) the seal word, the last word of the block, written by the payload;
  (3) ``sum(w0 .. w_seal-1)`` recomputed from the ``DW`` read-back, **minus
      that payload's own** ``P_SEALED - P_RESTORED``.

That subtraction is not a fudge.  ``progress(P_SEALED)`` re-stamps word 2
*after* the sum is taken, so a straight re-sum of a recovered block is high by
exactly one ladder step on every complete run.  It is 0x10 for both payloads
that exist, and it is still **derived from the ladder rather than written as
0x10**, because the two payloads do not share a ladder at all -- see PROGRESS
below.  Control C9 fails if the correction is ever a no-op, which is the only
thing that would make it a fudge.

Refusal, not tolerance
----------------------
The weak part of this tool is the parser, so it is the part that refuses.  A
``DW`` reply that is missing a line inside the requested range would let this
sum fewer words than the payload summed, and the disagreement would read as a
finding about the payload rather than about the capture.  Every address in
``[base, base + 4*words)`` must be present or the tool exits 2 and reports
nothing.  ``--seconds`` truncation is the failure this is aimed at: it is a
capture defect that looks exactly like a payload defect.

Exit codes
----------
0   every check that could run agreed
1   a check failed
2   refused -- the input could not be read as a complete block

Modes
-----
``<log>``            check one capture.  Needs ``--base`` and ``--words``.
``--self-test``      the controls and nothing else.

The controls run first on every invocation and the tool refuses to report on a
file if one of them fails, because a checksum comparison that has not been
shown able to fail is not a checksum comparison.  All ten run off captures
committed in this repository -- no ``$FWRE_WORK``, no device -- so they run on
a runner, which ``hazlint``'s population control cannot.

Run:  python3 tools/rbcheck.py bench/<dir>/<cell>.log --base 0x80A02000 \\
          --words 641 --uart bench/<dir>/<runcell>.log
      python3 tools/rbcheck.py --self-test
"""

import os
import re
import sys

MASK = 0xFFFFFFFF

#: The loader prints ``ADDR:`` then four tab-separated words.  Its lines end
#: LF CR, so from the reader's side each line begins with the CR of the one
#: before it -- 讀 `bench/2026-08-25b/H2g.log`, and the leading `\r` is
#: stripped rather than matched so a first line with no CR still parses.
DWLINE = re.compile(r"^([0-9A-Fa-f]{8}):((?:\t[0-9A-Fa-f]{8})+)\s*$")

#: `report.c`'s digit table is lower case; the loader's is upper.  That is the
#: free discriminator between a payload-printed word and a loader-printed one,
#: so the pattern is anchored to lower case deliberately.
UARTSUM = re.compile(r"rlxprobe:\s*sum=([0-9a-f]{8})")

POISON = 0xDEADC0DE

#: One progress ladder per payload, keyed by the magic word the block itself
#: carries, because **they are not the same ladder** -- 讀 `probe2.c:176-184`
#: and `probe3.c:181-192`.  `probe2` seals at `0x90`, which is `probe3`'s
#: `P_CACHEOP`, so a single hardcoded ladder reports a complete probe2 run as
#: having stopped nine stages early.  It did exactly that on this tool's first
#: run, which is why the ladder is selected by the block rather than by a flag.
PROGRESS = {
    0x524C5832: {
        0x10: "P_HEADER", 0x20: "P_STATUS", 0x30: "P_SAVED",
        0x40: "P_INSTALLED", 0x50: "P_BREAK", 0x60: "P_CENSUS",
        0x70: "P_COUNT", 0x80: "P_RESTORED", 0x90: "P_SEALED",
    },
    0x524C5833: {
        0x10: "P_HEADER", 0x20: "P_HANDLER", 0x30: "P_TIMER",
        0x40: "P_WALK_I", 0x50: "P_IMEM_OFF", 0x60: "P_SCRATCH",
        0x70: "P_COHERE", 0x80: "P_WALK_D", 0x90: "P_CACHEOP",
        0xA0: "P_ISC", 0xB0: "P_RESTORED", 0xC0: "P_SEALED",
    },
}

MAGICS = {0x524C5831: "probe1", 0x524C5832: "probe2", 0x524C5833: "probe3"}


def ladder(magic):
    """(names, sealed, restamp) for the payload this block names.

    ``restamp`` is ``P_SEALED - P_RESTORED`` **computed from that payload's own
    ladder**, not the literal 0x10.  It happens to be 0x10 for both payloads
    that exist, and control C9 is what would notice if a future one differed:
    a correction quoted as a constant is a constant that goes stale, and this
    one is the difference between two symbols in one header.
    """
    names = PROGRESS.get(magic)
    if not names:
        return None, None, None
    inv = {v: k for k, v in names.items()}
    return names, inv["P_SEALED"], inv["P_SEALED"] - inv["P_RESTORED"]


class Refuse(Exception):
    """The input cannot be read as a complete block.  Exit 2, report nothing."""


def parse_words(text):
    """``text`` -> {address: word}.

    Raises Refuse on a line that repeats an address with a different value:
    two readings of one address disagreeing means the capture holds two
    replies, and picking one is a decision this tool does not get to make.
    """
    words = {}
    for raw in text.splitlines():
        line = raw.lstrip("\r")
        m = DWLINE.match(line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        for i, tok in enumerate(m.group(2).split("\t")[1:]):
            a = addr + 4 * i
            v = int(tok, 16)
            if a in words and words[a] != v:
                raise Refuse(
                    f"address {a:08X} read twice and the readings differ "
                    f"({words[a]:08X} then {v:08X}) -- this capture holds "
                    f"more than one reply")
            words[a] = v
    if not words:
        raise Refuse("no DW reply lines in this capture at all")
    return words


def block(words, base, count):
    """The ``count`` words at ``base``, or Refuse naming the first hole."""
    out = []
    for i in range(count):
        a = base + 4 * i
        if a not in words:
            raise Refuse(
                f"word {i} at {a:08X} is not in this capture -- the reply is "
                f"short by at least one line.  A truncated --seconds window "
                f"looks exactly like this and is not a finding about the run")
        out.append(words[a])
    return out


def margin(words, base, count, poison_words):
    """The words past the block that ``LDR-07``'s round-up printed for free.

    ``DW base n`` prints ``4*ceil(n/4)`` words, so a request for 641 returns
    644 and the last three are margin the payload poisoned and no command asked
    for.  Returns [(index, address, value)] for those that are present.
    """
    out = []
    for i in range(count, poison_words):
        a = base + 4 * i
        if a in words:
            out.append((i, a, words[a]))
    return out


def check_block(words, base, count, uart_sum=None, seal_kind=1,
                poison_words=None, expect_magic=None, report=print):
    """Returns a list of failure strings.  Empty means everything agreed."""
    if poison_words is None:
        poison_words = count + 8
    b = block(words, base, count)
    fails = []

    magic, nonce, prog, seal = b[0], b[1], b[2], b[count - 1]
    who = MAGICS.get(magic, "unknown")
    report(f"  magic       {magic:08X}   {who}")
    if expect_magic is not None and magic != expect_magic:
        fails.append(f"magic is {magic:08X}, expected {expect_magic:08X} "
                     f"-- this is not the block that payload wrote")
    report(f"  nonce       {nonce:08X}")

    names, sealed, restamp = ladder(magic)
    if names is None:
        report(f"  progress    {prog:08X}   no ladder for magic {magic:08X}")
        fails.append(f"magic {magic:08X} names no payload this tool has a "
                     f"progress ladder for, so 'the run completed' cannot be "
                     f"checked at all -- reported rather than assumed")
        restamp = 0x10
    else:
        report(f"  progress    {prog:08X}   {names.get(prog, 'NOT A STAGE')}"
               f"   (sealed = {sealed:#04x})")
        if prog != sealed:
            fails.append(
                f"progress is {prog:08X} ({names.get(prog, 'not a stage')}), "
                f"not P_SEALED ({sealed:#04x}) -- the run stopped there and "
                f"the sum is of a partial block")

    naive = 0
    for w in b[:count - 1]:
        naive = (naive + w) & MASK
    corrected = (naive - restamp) & MASK if seal_kind == 1 else naive

    report(f"  seal word   {seal:08X}   w{count - 1} at "
           f"{base + 4 * (count - 1):08X}")
    report(f"  re-sum      {naive:08X}   naive, w0..w{count - 2}")
    report(f"  corrected   {corrected:08X}   "
           + (f"minus {restamp:#x} = P_SEALED - P_RESTORED, the re-stamp of "
              f"word 2" if seal_kind == 1 else "no correction (seal-kind 0)"))

    if seal == POISON:
        fails.append(
            f"the seal word reads {POISON:08X}, which is poison and not a sum "
            f"-- --words is past the end of the block.  RB_POISON_W is "
            f"RB_WORDS + 8 and reading the seal at the poison extent is the "
            f"off-by-the-margin this control exists for")
    elif corrected != seal:
        fails.append(f"corrected re-sum {corrected:08X} != seal {seal:08X} "
                     f"-- channels (2) and (3) disagree")

    if uart_sum is None:
        report("  UART sum    absent -- channel (1) did not run, "
               "and two agreeing channels are not three")
    else:
        report(f"  UART sum    {uart_sum:08X}   channel (1)")
        if uart_sum != seal:
            fails.append(f"UART sum {uart_sum:08X} != seal {seal:08X} "
                         f"-- channels (1) and (2) disagree")

    # The retained bitmap.  `probe3.c:1324-1329` says the boundary point's
    # pattern "survives to the read-back"; 量 2026-08-30, it does not --
    # `bmp_clear()` runs again at :1385, :1667 and :1808, all AFTER the boundary
    # rerun at :1336.  This is REPORTED and is not a failure: the sum, the seal
    # and both channels are unaffected, and refusing the whole block over a
    # stale region would be the wrong verdict.  It exists so the discrepancy is
    # visible instead of being reconstructed by a reader who trusts the header.
    if magic == 0x524C5833 and count >= 640:
        adv = b[23]                       # H_BMP_COUNT
        nib = 0
        for w in range(384, 640):
            v = b[w]
            for sh in range(28, -1, -4):
                if (v >> sh) & 0xF:
                    nib += 1
        report(f"  bitmap      header advertises {adv} victim(s) at "
               f"{b[22]:08X}; {nib} nibble(s) written")
        if adv and nib < adv:
            report(f"              ⚠️ {adv - nib} short -- the region was "
                   f"overwritten after the point that filled it "
                   f"(probe3.c:1385/1667/1808 vs :1336). Reported, not failed: "
                   f"the sum and both channels are unaffected")

    m = margin(words, base, count, poison_words)
    if not m:
        report("  margin      none in this reply -- the over-run control "
               "did not run")
    else:
        bad = [(i, a, v) for (i, a, v) in m if v != POISON]
        report(f"  margin      {len(m)} word(s) past the block, "
               f"{len(m) - len(bad)} poison")
        for (i, a, v) in bad:
            fails.append(f"margin word w{i} at {a:08X} is {v:08X}, not "
                         f"{POISON:08X} -- the run wrote past its own block")
    return fails


def read_uart_sum(path):
    with open(path, "rb") as f:
        text = f.read().decode("latin-1")
    hits = UARTSUM.findall(text)
    if not hits:
        return None
    if len(set(hits)) > 1:
        raise Refuse(f"{path}: {len(set(hits))} different sum= lines -- "
                     f"this capture holds more than one run")
    return int(hits[0], 16)


# ----------------------------------------------------------------- controls

H2G = "bench/2026-08-25b/H2g.log"
H2A = "bench/2026-08-25b/H2a.log"
P2_BASE, P2_WORDS, P2_SEAL = 0x80A01000, 809, 0xEC84408D

#: probe3's own block and run, from the device, 2026-08-29.  C16 uses them
#: because every other control runs on one capture of one payload.
P3RB = "bench/2026-08-30/Q5-rb.log"
P3QJ = "bench/2026-08-30/QJ.log"

#: where the ladders actually live.  C10 re-reads these rather than trusting
#: the copy above.
SRC = {0x524C5832: "tools/rlxprobe/probe2.c",
       0x524C5833: "tools/rlxprobe/probe3.c"}

DEFINE = re.compile(r"^#define\s+(P_[A-Z_]+)\s+(0x[0-9A-Fa-f]+)u?\s*$")


def _ladders_match_source():
    """Parse `#define P_*` out of each payload's .c and compare to PROGRESS.

    The point is that this control FAILS if somebody edits a ladder in the C
    and not here.  The previous version compared two hardcoded copies in this
    same file and could not fail for that reason at all.
    """
    notes = []
    ok = True
    for magic, rel in SRC.items():
        path = os.path.join(_root(), rel)
        try:
            text = io_read(path)
        except OSError as e:
            return False, f"{rel}: {e}"
        found = {}
        for line in text.splitlines():
            m = DEFINE.match(line.strip())
            if m:
                found[m.group(1)] = int(m.group(2), 16)
        if not found:
            return False, f"{rel}: no `#define P_*` lines parsed at all"
        mine = {v: k for k, v in PROGRESS[magic].items()}
        if found != mine:
            ok = False
            only_src = {k: v for k, v in found.items() if mine.get(k) != v}
            only_here = {k: v for k, v in mine.items() if found.get(k) != v}
            notes.append(f"{rel}: source-only {only_src}, here-only {only_here}")
        else:
            notes.append(f"{rel} {len(found)} stages match")
    return ok, "; ".join(notes)


def io_read(path):
    with open(path, "rb") as f:
        return f.read().decode("latin-1")


def _root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path):
    with open(os.path.join(_root(), path), "rb") as f:
        return f.read().decode("latin-1")


def _quiet(*_a, **_k):
    pass


def run_controls():
    """Sixteen, and eleven of them must fail.  Returns 0 if every one behaved."""
    print("rbcheck controls")
    ok = True

    def row(tag, name, good, detail):
        nonlocal ok
        ok = ok and good
        print(f"  {'ok  ' if good else 'FAIL'}  {tag} {name:<52} {detail}")

    try:
        h2g = _read(H2G)
        h2a = _read(H2A)
    except OSError as e:
        print(f"  FAIL  C0 the committed probe2 capture is readable    {e}")
        return 1

    words = parse_words(h2g)
    usum = read_uart_sum(os.path.join(_root(), H2A))

    # C1 -- the positive control, on silicon, on a different payload.
    f = check_block(words, P2_BASE, P2_WORDS, uart_sum=usum, report=_quiet)
    row("C1", "probe2 at 809 words: three channels agree",
        not f and usum == P2_SEAL,
        f"seal {P2_SEAL:08X}, UART {usum:08X}, {len(f)} failure(s)"
        if usum else "no UART sum found")

    # C2 -- yesterday's own mistake.  817 is RB_POISON_W, not RB_WORDS.
    f = check_block(words, P2_BASE, 817, uart_sum=usum, report=_quiet)
    row("C2", "probe2 at 817 words (RB_POISON_W) is caught",
        any("poison" in x for x in f),
        f"{len(f)} failure(s), and one names poison" if f else "reported clean")

    # C3 -- the negative control: one bit, and the comparison must notice.
    bent = dict(words)
    bent[P2_BASE] ^= 1
    f = check_block(bent, P2_BASE, P2_WORDS, uart_sum=usum, report=_quiet)
    row("C3", "one flipped bit in w0 fails the re-sum",
        any("re-sum" in x for x in f),
        f"{len(f)} failure(s)" if f else "reported clean -- the sum is inert")

    # C4 -- a hole must refuse, not sum what is left.
    holed = {a: v for a, v in words.items() if a != P2_BASE + 4 * 100}
    try:
        check_block(holed, P2_BASE, P2_WORDS, report=_quiet)
        row("C4", "a missing line refuses rather than summing fewer words",
            False, "it reported instead of refusing")
    except Refuse as e:
        row("C4", "a missing line refuses rather than summing fewer words",
            "word 100" in str(e), str(e).split(" -- ")[0])

    # C5 -- the free over-run control fires.
    dirty = dict(words)
    dirty[P2_BASE + 4 * P2_WORDS] = 0x1234ABCD
    f = check_block(dirty, P2_BASE, P2_WORDS, uart_sum=usum, report=_quiet)
    row("C5", "a margin word that is not poison is caught",
        any("past its own block" in x for x in f),
        f"{len(f)} failure(s)" if f else "reported clean")

    # C6 -- the wrong payload's block at the right address.
    f = check_block(words, P2_BASE, P2_WORDS, uart_sum=usum,
                    expect_magic=0x524C5833, report=_quiet)
    row("C6", "probe2's block refused when probe3's magic is demanded",
        any("not the block" in x for x in f),
        f"magic {words[P2_BASE]:08X} vs 524C5833")

    # C7 -- two replies in one capture is a refusal, not a coin toss.
    try:
        parse_words(h2g + "\r80A01000:\t00000000\t00000000\t00000000\t00000000\n")
        row("C7", "one address read twice with different values refuses",
            False, "it accepted the second reading")
    except Refuse as e:
        row("C7", "one address read twice with different values refuses",
            "read twice" in str(e), str(e).split(" -- ")[0])

    # C8 -- a missing channel is absent, never agreement.  Two agreeing
    # channels must not be reported as three.
    lines = []
    f = check_block(words, P2_BASE, P2_WORDS, uart_sum=None,
                    report=lambda s: lines.append(s))
    row("C8", "no UART sum reports the channel absent, not agreeing",
        not f and any("absent" in x for x in lines),
        "block still passes on channels (2) and (3)")

    # C9 -- the correction is load-bearing.  If a naive re-sum equalled the
    # seal, the re-stamp subtraction would be a fudge and this row says so.
    naive = 0
    for w in block(words, P2_BASE, P2_WORDS)[:P2_WORDS - 1]:
        naive = (naive + w) & MASK
    _, _, restamp = ladder(0x524C5832)
    row("C9", "the re-stamp subtraction is not a no-op",
        naive != P2_SEAL and (naive - restamp) & MASK == P2_SEAL,
        f"naive {naive:08X}, seal {P2_SEAL:08X}, difference "
        f"{(naive - P2_SEAL) & MASK:#x}, ladder says {restamp:#x}")

    # C10 -- the ladder is selected by the block, and the copy in this file is
    # checked AGAINST THE SOURCE.  🔴 The first version of this control compared
    # the hardcoded dict to hardcoded literals in the same file, written by the
    # same hand at the same time: it could not detect the source drift it exists
    # to prevent.  An adversarial pass called it vacuous and it was.
    src_ok, src_detail = _ladders_match_source()
    row("C10", "the ladders match probe2.c/probe3.c, re-read from source",
        src_ok, src_detail)

    # C11 -- a WRONG UART sum must fail.  Every earlier control fed either the
    # real sum or None, so `if uart_sum != seal` could be deleted outright and
    # all ten passed.  That comparison is one of the three the module docstring
    # is built on.
    f = check_block(words, P2_BASE, P2_WORDS, uart_sum=P2_SEAL ^ 1,
                    report=_quiet)
    row("C11", "a UART sum that disagrees with the seal is caught",
        any("UART sum" in x for x in f),
        f"{len(f)} failure(s)" if f else "reported clean -- channel (1) is inert")

    # C12 -- a block that did not reach P_SEALED must fail, and it is checked on
    # BOTH payloads.  This is the sole consumer of the ladder discovery, and
    # nothing exercised it: `if prog != sealed` could be deleted and all ten
    # passed.
    stopped = dict(words)
    stopped[P2_BASE + 8] = 0x50            # probe2's P_BREAK
    f = check_block(stopped, P2_BASE, P2_WORDS, uart_sum=usum, report=_quiet)
    row("C12", "a block that stopped short of P_SEALED is caught",
        any("not P_SEALED" in x for x in f),
        f"progress 0x50 (P_BREAK) against sealed 0x90; {len(f)} failure(s)")

    # C13 -- an unknown magic must SAY it cannot check completion rather than
    # silently falling back.  The fallback path had no control on it at all.
    alien = dict(words)
    alien[P2_BASE] = 0xDEADBEEF
    f = check_block(alien, P2_BASE, P2_WORDS, report=_quiet)
    row("C13", "an unrecognised magic refuses to judge completion",
        any("no payload this tool has a" in x for x in f),
        f"{len(f)} failure(s), one naming the missing ladder")

    # C14 -- the summation extent, on a synthetic block where EVERY word is
    # non-zero.  On the real capture 637 of 808 summed words are zero, so an
    # off-by-one in `b[:count-1]` changed nothing and passed 10/10.
    n = 32
    synth = {}
    tot = 0
    for i in range(n - 1):
        v = 0x11111111 * ((i % 15) + 1) & MASK
        if i == 0:
            v = 0x524C5833
        elif i == 2:
            v = 0xC0
        synth[0x80A02000 + 4 * i] = v
        tot = (tot + v) & MASK
    synth[0x80A02000 + 4 * (n - 1)] = (tot - 0x10) & MASK
    f = check_block(synth, 0x80A02000, n, report=_quiet)
    zeros = sum(1 for i in range(n - 1) if synth[0x80A02000 + 4 * i] == 0)
    row("C14", "the summed extent is exactly w0..w_seal-1",
        not f and zeros == 0,
        f"synthetic block, {n} words, {zeros} of {n-1} summed words are zero "
        f"(the real fixture has 637 of 808)")

    # C15 -- the UART pattern is anchored to LOWER case on purpose: report.c's
    # digit table is lower and the loader's is upper, so an upper-case sum= is
    # not something a correct run can print.  Nothing tested that anchoring.
    upper = h2a.replace("rlxprobe: sum=ec84408d", "rlxprobe: sum=EC84408D")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False,
                                     encoding="latin-1") as fh:
        fh.write(upper)
        tmp = fh.name
    try:
        got = read_uart_sum(tmp)
    finally:
        os.unlink(tmp)
    row("C15", "an UPPER-case sum= is not accepted as the payload's",
        got is None,
        "upper case is the loader's digit table, not report.c's"
        if got is None else f"matched {got:08X} -- the anchoring is gone")

    # C16 -- probe3's own block, from the device.  Every control above runs on
    # one capture of one payload; probe3's ladder was never exercised on data.
    try:
        p3 = parse_words(_read(P3RB))
        p3u = read_uart_sum(os.path.join(_root(), P3QJ))
        f = check_block(p3, 0x80A02000, 641, uart_sum=p3u,
                        expect_magic=0x524C5833, report=_quiet)
        row("C16", "probe3's own on-device block agrees on three channels",
            not f and p3u == 0xC93E60B5,
            f"seal/UART {p3u:08X}, {len(f)} failure(s)" if p3u
            else "no UART sum found")
    except (OSError, Refuse) as e:
        row("C16", "probe3's own on-device block agrees on three channels",
            False, f"{e}")

    print()
    return 0 if ok else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        return run_controls()
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-2].strip(), file=sys.stderr)
        return 2

    path, base, count, uart, seal_kind, poison, magic = argv[1], None, None, \
        None, 1, None, None
    rest = argv[2:]
    i = 0
    while i < len(rest):
        a = rest[i]
        try:
            if a == "--base":
                base = int(rest[i + 1], 0)
            elif a == "--words":
                count = int(rest[i + 1], 0)
            elif a == "--uart":
                uart = rest[i + 1]
            elif a == "--seal-kind":
                seal_kind = int(rest[i + 1], 0)
            elif a == "--poison-words":
                poison = int(rest[i + 1], 0)
            elif a == "--expect-magic":
                magic = int(rest[i + 1], 0)
            else:
                print(f"  unknown option {a}", file=sys.stderr)
                return 2
        except IndexError:
            print(f"  {a} needs a value", file=sys.stderr)
            return 2
        i += 2
    if base is None or count is None:
        print("  --base and --words are both required: this tool will not "
              "guess the extent of a block", file=sys.stderr)
        return 2

    rc = run_controls()
    if rc:
        print("  controls failed -- refusing to report on the file")
        return rc

    print(f"rbcheck {path}  base {base:#010x}  words {count}")
    try:
        with open(path, "rb") as f:
            words = parse_words(f.read().decode("latin-1"))
        usum = read_uart_sum(uart) if uart else None
        fails = check_block(words, base, count, uart_sum=usum,
                            seal_kind=seal_kind, poison_words=poison,
                            expect_magic=magic)
    except Refuse as e:
        print(f"\n  REFUSED: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"\n  REFUSED: {e}", file=sys.stderr)
        return 2

    print()
    if fails:
        for x in fails:
            print(f"  FAIL  {x}")
        print(f"\nRESULT: {len(fails)} disagreement(s)")
        return 1
    n = 3 if usum is not None else 2
    print(f"RESULT: the block agrees on {n} channel(s), and the controls that "
          f"could have said otherwise held")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
