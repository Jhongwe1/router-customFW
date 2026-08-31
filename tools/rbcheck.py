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
shown able to fail is not a checksum comparison.  🔄 **Thirty-one of them since
2026-08-31** -- the prose here and the row in ``tools/ci-expected.tsv`` both
still said *ten* while the count column said sixteen, once.  C1..C16 run off
captures committed in this repository -- no ``$FWRE_WORK``, no device -- so
they run on a runner, which ``hazlint``'s population control cannot; C17..C30
run on a block this file synthesises, and that is stated in the code beside
them because **they show the check works, not that any payload does.**

Group F, and the line this tool does NOT cross
----------------------------------------------
`docs/probe3-cells.md` § 6.8.3 writes six refutation conditions for the flash
window group.  **Four of them are checked here and two deliberately are not**,
and the line is INTERNAL CONTRADICTION against PREDICTION:

* ``f.faults``, ``f.live``, the ``f.win.seq``/``f.win.seq2`` pair and the
  window-against-DRAM ordering make the block's own tick words **not mean what
  they say**.  No card, no prediction and no knowledge of the device is needed
  to see it, so this tool sees it.
* ``f.alias`` and ``f.sfcr`` are predictions **about the device**.  They belong
  on the card and to ``check-predictions.py``.  Asserting them here would make
  this file a second owner of a finding, which house rule 1 forbids.

⚠️ ``--words`` is the payload's ``RB_WORDS`` and it MOVED TWICE: probe3's
block is **718** words since 2026-08-31 (Group F, the memory-mapped SPI
window), was 707 from 2026-08-31 (a retained bitmap region and Group W's
``M(T)`` ladder) and 641 before that.  Both parse -- the layout is read out of the
block's own ``H_LAYOUT_*`` header words rather than out of a table here -- but
passing the wrong ``--words`` reads the seal at the wrong offset, which is what
control C2 exists for.

Run:  python3 tools/rbcheck.py bench/<dir>/<cell>.log --base 0x80A02000 \\
          --words 707 --uart bench/<dir>/<runcell>.log
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
        0xA0: "P_ISC", 0xA8: "P_FLASHWIN", 0xB0: "P_RESTORED",
        0xC0: "P_SEALED",
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

    # The bitmap regions.  🔄 2026-08-31: there are TWO, and this reads the
    # offsets OUT OF THE BLOCK rather than out of a table here.  The header has
    # carried them since the layout was written -- `H_LAYOUT_*`, "so the desk
    # can parse the block from the block rather than from this file" -- and this
    # tool hardcoded 384/640 anyway, which is why it needed editing when the
    # layout moved.  A capture is now readable whatever its layout, and the
    # 641-word blocks already committed still parse.
    #
    # `O_BMP` is the SCRATCHPAD: seven cells clear it and read it back in
    # place, so what survives to a read-back is the last of them (x-c10's two
    # victims, 量 2026-08-30 on bench/2026-08-30/Q5-rb.log).  That is reported,
    # never failed -- the sum, the seal and both channels are unaffected, and
    # refusing a whole block over a region that is a scratchpad by design would
    # be the wrong verdict.
    #
    # 🔴 THE THREE INDICES BELOW MOVED ON 2026-08-31, from 48/49/50 to 52/53/54,
    # because all three collided with `H_KSEG0`, `H_G_TIMER` and `H_T_SEP_A` --
    # words Group T writes AFTER the header is laid down.  No committed capture
    # is affected: the 707-word layout was never seated.  probe3.c's own comment
    # beside `H_BMP_KEPT` carries the whole finding, and `test-rlxprobe.sh` Y2c
    # is the census that would have caught it.
    #
    # `O_BMPK` is the RETAINED COPY and it IS checkable, because the payload
    # now writes its own FRESH count beside it (`H_BMP_FRESH`).  Two numbers
    # over one region, computed by different code at different times.
    # `count > H_BMP_FRESH` because the layout words live in the header and a
    # block shorter than the header has none of them.  C14's synthetic block is
    # 32 words and carries probe3's magic on purpose; without this guard the
    # tool raised IndexError on it rather than reporting, which is the failure
    # mode where an instrument that cannot fail is indistinguishable from one
    # that passed.
    # --- Group F, 2026-08-31.  `docs/probe3-cells.md` § 6.8.
    #
    # PRESENCE IS DECIDED BY THE BLOCK, NOT BY ITS LENGTH.  `RB_RES` is not a
    # header word, but `H_LAYOUT_ROWS - H_LAYOUT_RES` is exactly it, so a 641-
    # or 707-word capture reports 192 or 194 and is skipped -- and the skip is
    # PRINTED.  A length test would have read Group F's slots out of the row
    # area of every older block and failed them all.
    if magic == 0x524C5833 and count > 50:
        o_res, o_rows = b[40], b[41]
        n_res = o_rows - o_res if o_rows > o_res else 0
        if n_res < 205:
            report(f"  group F     not in this block: the header says "
                   f"{n_res} result words, and Group F starts at 194")
        else:
            g = {k: b[o_res + v] for k, v in (
                ("sfcr", 194), ("win.seq", 195), ("win.str", 196),
                ("boot.seq", 197), ("boot.str", 198), ("dram.seq", 199),
                ("dram.str", 200), ("win.seq2", 201), ("alias", 202),
                ("live", 203), ("faults", 204))}
            report("  group F     " + "  ".join(
                f"{k}={g[k]:08X}" for k in
                ("win.seq", "win.str", "dram.str", "win.seq2", "faults")))

            # 🔴 ALL SEVEN POISON IS A REFUSAL, NOT A READING, and a MIX is
            # a defect.  probe3 leaves the timing legs at stage 0's poison
            # when `g_timer` is 0 -- the payload's own *this cell did not run*
            # -- so reading them as ticks would report seven findings about a
            # group that correctly declined to run.  Some poison and some not
            # is neither, and it is the only one of the three that is a bug.
            legs = ("win.seq", "win.str", "boot.seq", "boot.str",
                    "dram.seq", "dram.str", "win.seq2")
            npois = sum(1 for k in legs if g[k] == POISON)
            if npois == len(legs):
                report("  group F     timing VOID -- all seven legs are "
                       "poison, which is the payload declining because Group "
                       "T did not ship. f.alias and f.live still stand")
                legs = ()
            elif npois:
                fails.append(
                    f"Group F has {npois} of {len(legs)} timing legs poisoned "
                    f"and the rest written -- the gate is all-or-nothing, so "
                    f"a mix means a leg did not reach its res_put")
            for k in legs:
                if g[k] == 0xFFFFFFFF:
                    fails.append(
                        f"Group F leg {k} is FFFFFFFF -- tc_ticks' sentinel "
                        f"for a bracket whose destination register was never "
                        f"written, so the leg has no reading at all")
                elif g[k] == 0:
                    fails.append(
                        f"Group F leg {k} is zero ticks -- the counter did "
                        f"not move across 1,024 loads, which no band in "
                        f"§ 6.8.2 allows")

            if g["faults"] != 0:
                fails.append(
                    f"Group F took {g['faults']} fault(s) -- the handler's "
                    f"own time is INSIDE every bracket, so every tick in the "
                    f"group is void rather than merely suspect")

            win_live, boot_live = (g["live"] >> 8) & 0xFF, g["live"] & 0xFF
            if win_live == 0 or boot_live == 0:
                fails.append(
                    f"Group F f.live is {g['live']:08X} -- win={win_live} "
                    f"boot={boot_live} of 15 words differing from word 0, and "
                    f"a zero means that window returned sixteen identical "
                    f"words: a floating bus, not flash")

            s1, s2 = g["win.seq"], g["win.seq2"]
            if s1 not in (0, 0xFFFFFFFF) and s2 not in (0, 0xFFFFFFFF):
                d = s2 - s1 if s2 > s1 else s1 - s2
                if d * 10 > s1:
                    fails.append(
                        f"Group F is not repeatable: f.win.seq {s1} against "
                        f"f.win.seq2 {s2}, {100.0 * d / s1:.1f} % apart over "
                        f"one run. No ratio computed from it is worth reading")

            if 0 < g["dram.str"] != 0xFFFFFFFF and 0 < g["win.str"] < g["dram.str"]:
                fails.append(
                    f"Group F: f.win.str {g['win.str']} < f.dram.str "
                    f"{g['dram.str']} -- the SPI window read FASTER than "
                    f"uncached DRAM, which nothing in § 6.8.2's model allows. "
                    f"The framework is wrong, not one term")

    if magic == 0x524C5833 and count > 50:
        o_bmp, o_bmpk, o_seal = b[42], b[53], b[43]
        adv, point = b[23], b[22]

        def nibbles(lo, hi, limit=None):
            """FRESH-or-STALE nibbles in [lo, hi), first `limit` if given."""
            n, seen = 0, 0
            for w in range(lo, min(hi, count)):
                for sh in range(28, -1, -4):
                    if limit is not None and seen >= limit:
                        return n
                    seen += 1
                    if (b[w] >> sh) & 0xF:
                        n += 1
            return n

        def fresh(lo, hi, limit=None):
            n, seen = 0, 0
            for w in range(lo, min(hi, count)):
                for sh in range(28, -1, -4):
                    if limit is not None and seen >= limit:
                        return n
                    seen += 1
                    if ((b[w] >> sh) & 0xF) == 2:      # V_FRESH
                        n += 1
            return n

        def fresh_positions(lo, hi, limit=None):
            """The victim INDICES whose nibble is FRESH, ascending.

            `fresh()` answers *how many*; § 6.2a (2)'s prediction is about
            WHERE, and the two hypotheses give the same count.  Deliberately a
            second pass rather than folded into `fresh()`, so that an indexing
            defect in either one makes the two disagree out loud below.
            """
            out, seen = [], 0
            for w in range(lo, min(hi, count)):
                for sh in range(28, -1, -4):
                    if limit is not None and seen >= limit:
                        return out
                    nib = (b[w] >> sh) & 0xF
                    if nib == 2:                       # V_FRESH, see fresh()
                        out.append(seen)
                    seen += 1
            return out

        if not (0 < o_bmp < o_seal <= count):
            report(f"  bitmap      header layout words are "
                   f"{o_bmp}/{o_bmpk}/{o_seal} against a {count}-word block "
                   f"-- not parsed")
        elif o_bmpk == POISON or not (o_bmp < o_bmpk < o_seal):
            # A pre-2026-08-31 block: one region, and the defect it carries.
            nib = nibbles(o_bmp, o_seal)
            report(f"  bitmap      one region (pre-2026-08-31 layout); header "
                   f"advertises {adv} victim(s) at {point:08X}; "
                   f"{nib} nibble(s) written")
            if adv and nib < adv:
                report(f"              ⚠️ {adv - nib} short -- the scratchpad "
                       f"was overwritten after the point that filled it. "
                       f"Reported, not failed: the sum and both channels are "
                       f"unaffected")
        else:
            kept, said = b[52], b[54]
            nib = nibbles(o_bmp, o_bmpk)
            report(f"  scratchpad  {nib} nibble(s) at w{o_bmp} -- the LAST "
                   f"cell to use it, not the boundary point. Never failed")
            got = fresh(o_bmpk, o_seal, kept)
            report(f"  retained    {kept} of {adv} victim(s) at {point:08X} "
                   f"copied to w{o_bmpk}; {got} FRESH, payload said {said}")
            if kept > adv:
                fails.append(
                    f"H_BMP_KEPT {kept} exceeds H_BMP_COUNT {adv} -- the "
                    f"snapshot claims more victims than the point swept")
            elif kept == adv and got != said:
                fails.append(
                    f"retained region holds {got} FRESH where the payload "
                    f"counted {said} over the same victims -- the snapshot "
                    f"was not taken at the point whose count is in the header")
            elif kept < adv and got > said:
                fails.append(
                    f"retained region holds {got} FRESH over its first {kept} "
                    f"victims, more than the {said} the payload counted over "
                    f"all {adv} -- arithmetically impossible")

            # 🔴 § 6.2a (2) -- the PATTERN, which is the half no count can
            # carry.  At the boundary point the victims are 32 B apart, so the
            # set index advances by TWO per victim: under two-way (512 sets)
            # victims k and k + kept/2 share a set; under direct-mapped (1,024
            # sets) no two of the kept victims ever do.  **The two hypotheses
            # predict the same COUNT and different POSITIONS**, which is why
            # `bmp.rerun.fresh` alone never separated them.
            pos = fresh_positions(o_bmpk, o_seal, kept)
            if len(pos) != got:
                fails.append(
                    f"the pairing pass found {len(pos)} FRESH where the "
                    f"counting pass found {got} over the same region -- two "
                    f"passes over one region disagree, so one of them indexes "
                    f"wrong and neither reading is usable")
            period = kept // 2
            if period == 0 or not pos or len(pos) == kept:
                # 🔴 THE POPULATION CONTROL, and it lives inside the tool
                # because a region that is entirely FRESH pairs every k with
                # k+period trivially.  A PURE PAIRING verdict off such a region
                # is a verdict from a region that says nothing -- this
                # repository's "a tool reporting 0 is making a claim", with the
                # sign reversed.
                report(f"  pairing     no verdict -- {len(pos)} FRESH of "
                       f"{kept} victim(s): single-valued, or no period. Any "
                       f"pattern claim off this region is vacuous")
            else:
                s = set(pos)
                pairs = sorted(k for k in pos
                               if k < period and k + period in s)
                alone = sorted(k for k in pos
                               if (k < period and k + period not in s)
                               or (k >= period and k - period not in s))
                if len(pairs) * 2 == len(pos) and not alone:
                    verdict = ("PURE PAIRING -- two-way. Direct-mapped is "
                               "refuted by the pattern")
                elif not pairs:
                    verdict = ("ALL SINGLETONS -- direct-mapped by the "
                               "pattern. It must agree with w.assoc.mt, and "
                               "this tool does not check that")
                else:
                    verdict = ("MIXED -- § 6.2a: the pairing model is WRONG, "
                               "and the M(T) ladder is the only route left")
                report(f"  pairing     {len(pos)} FRESH over {kept} "
                       f"victim(s), period {period}: {len(pairs)} pair(s), "
                       f"{len(alone)} unpaired -- {verdict}")

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
# 🔴 The 718-word block C39 reads.  `K2b-rb` and not `K2-rb`: the latter is the
# copy that sat in DRAM through a vendor-firmware boot and carries a flipped
# bit at w126 (`bench/2026-08-31c/CORRECTIONS-block4.md` § 7).  Both give the
# same pairing, which is itself the finding -- but a control anchors on the
# block whose three channels agree.
PAIRRB = "bench/2026-08-31c/K2b-rb.log"

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

    # C17..C20 -- the RETAINED bitmap region, 2026-08-31.  🔴 There is no
    # capture of a 707-word block yet, and there will not be one until the next
    # seating, so these run on a synthesised block.  That is stated rather than
    # hidden: they show the CHECK works, not that the payload does.  C16 is the
    # one that runs on silicon and it is deliberately left on the 641-word
    # capture -- a control rewritten to match new code stops being evidence
    # about the old capture.
    def synth707(kept, said, fresh_nibbles, adv=512, stale_nibbles=0,
                 beyond=(), n_res=194, gf=None, fresh_at=None):
        """A well-formed probe3 block with a retained region.

        `stale_nibbles` are laid down AFTER the FRESH ones so the two kinds
        occupy different victims.  They exist because without them every
        non-zero nibble in the region is FRESH, and a recount that counted
        *any written nibble* would agree with one that counted FRESH -- the
        two are only distinguishable on a region holding both.

        `n_res` is the RESULT-AREA size, and it is a parameter rather than a
        constant because the point of C30 is that ONE synthesiser produces
        both layouts: 194 is the 707-word block that Group F is absent from and
        205 is the 718-word block it is present in.  The offsets below are
        computed from it exactly as probe3.c computes them, which is also what
        makes the header's layout words honest here.
        """
        o_rows = 64 + n_res
        o_bmp = o_rows + 16 * 8
        o_bmpk = o_bmp + 256
        o_seal = o_bmpk + 64
        n = o_seal + 1
        w = [0] * n
        w[0] = 0x524C5833
        w[2] = 0xC0                       # P_SEALED
        w[22], w[23] = 0x57004000, adv    # H_BMP_POINT / H_BMP_COUNT
        w[40], w[41] = 64, o_rows         # H_LAYOUT_RES / H_LAYOUT_ROWS
        w[42], w[43] = o_bmp, o_seal
        w[52], w[53], w[54] = kept, o_bmpk, said
        for k, v in (gf or {}).items():   # Group F, by result index
            w[64 + k] = v
        # `fresh_at` places the FRESH victims at EXPLICIT indices.
        # Without it they are the first `fresh_nibbles`, which is contiguous
        # and therefore all-singletons under every period -- correct for the
        # counting controls C17..C23 and useless for the pattern ones.
        at = list(range(fresh_nibbles)) if fresh_at is None else list(fresh_at)
        for i in at:                      # V_FRESH = 2, packed 8 per word
            w[o_bmpk + i // 8] |= 2 << (28 - 4 * (i % 8))
        atset = set(at)
        for i in range(fresh_nibbles, fresh_nibbles + stale_nibbles):
            if i in atset:                # never lay STALE over a FRESH victim
                continue
            w[o_bmpk + i // 8] |= 1 << (28 - 4 * (i % 8))   # V_STALE
        for i in beyond:                  # FRESH past H_BMP_KEPT: not evidence
            w[o_bmpk + i // 8] |= 2 << (28 - 4 * (i % 8))
        tot = 0
        for i in range(n - 1):
            tot = (tot + w[i]) & MASK
        w[n - 1] = (tot - 0x10) & MASK
        d = {0x80A02000 + 4 * i: w[i] for i in range(n)}
        for i in range(n, n + 8):         # the poison margin
            d[0x80A02000 + 4 * i] = POISON
        return d

    # 🔴 C17 ASSERTS THE BRANCH WAS ENTERED, NOT ONLY THAT NOTHING FAILED, and
    # it did not until 2026-08-31.  量, by `test-rbcheck.py`'s W0 -- which
    # requires a mutation to turn the case it NAMES red: M24 (the layout
    # hardcoded back to the 641-word offsets) and M26 (the branch skipped for
    # short blocks) both push the tool into the `elif` above, the
    # pre-2026-08-31 one-region path, which REPORTS and never fails.  `not f`
    # was therefore true and C17 stayed green while the retained region was not
    # looked at at all.  A positive control that passes when the check does not
    # run is the failure this repository keeps catching, in the one place it is
    # least visible: the case whose job is to be green.
    cap = []
    f = check_block(synth707(512, 20, 20), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=cap.append)
    entered = any("retained  " in x for x in cap)
    row("C17", "a consistent retained region passes, and was ENTERED",
        not f and entered,
        f"kept 512 of 512, 20 FRESH, payload said 20; {len(f)} failure(s), "
        f"retained line {'present' if entered else 'ABSENT -- the branch never ran'}")

    f = check_block(synth707(512, 20, 19), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=_quiet)
    row("C18", "a recount that differs from the payload's count FAILS",
        any("not taken at the point" in x for x in f),
        f"19 FRESH against a payload count of 20; {len(f)} failure(s)")

    f = check_block(synth707(600, 20, 20), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=_quiet)
    row("C19", "H_BMP_KEPT above H_BMP_COUNT FAILS",
        any("exceeds H_BMP_COUNT" in x for x in f),
        f"kept 600 of 512; {len(f)} failure(s)")

    f = check_block(synth707(256, 20, 21), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=_quiet)
    row("C20", "more FRESH in a truncated copy than in the whole point FAILS",
        any("arithmetically impossible" in x for x in f),
        f"21 FRESH over the first 256 of 512 against a total of 20; "
        f"{len(f)} failure(s)")

    # C21 -- the population control for C17..C20.  Each of those asserts on a
    # substring, and a substring that no code path can emit makes a control
    # that cannot fail.  This one says the truncated-but-consistent case is
    # accepted, so C20's refusal is about the arithmetic and not about `kept`
    # being less than `adv`.
    f = check_block(synth707(256, 20, 12), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=_quiet)
    row("C21", "a truncated copy that is arithmetically possible passes",
        not f, f"12 FRESH over the first 256 of 512, total 20; "
               f"{len(f)} failure(s)")

    # C22 -- 🔴 THE ONE THAT SEPARATES *FRESH* FROM *WRITTEN*.  C17..C21 all run
    # on regions whose only non-zero nibbles are FRESH, so a recount that
    # counted every written nibble would agree with them everywhere and no
    # control could tell.  Found by asking what a mutation of `fresh()` would
    # break, before writing the mutation.  492 STALE beside 20 FRESH: a recount
    # that ignores the verdict reads 512 against a payload count of 20.
    f = check_block(synth707(512, 20, 20, stale_nibbles=492), 0x80A02000, 707,
                    expect_magic=0x524C5833, report=_quiet)
    row("C22", "STALE nibbles are not counted as FRESH", not f,
        f"492 STALE beside 20 FRESH, payload said 20; {len(f)} failure(s)")

    # C23 -- 🔴 THE RECOUNT STOPS AT H_BMP_KEPT.  The region is a fixed 64 words
    # whatever the boundary point's size, so when the point is smaller than 512
    # victims the nibbles past `kept` belong to nothing -- normally V_NEVER,
    # but a snapshot taken at the wrong moment or a partial copy puts a previous
    # point's verdicts there.  Reading them is reading leftovers.
    # ⚠️ Written because M25 SURVIVED against C17..C22: every one of those has
    # its FRESH nibbles inside `kept`, so removing the limit changed no answer
    # and a control that cannot see a mutation is not covering it.
    f = check_block(synth707(256, 20, 20, adv=256, beyond=range(300, 320)),
                    0x80A02000, 707, expect_magic=0x524C5833, report=_quiet)
    row("C23", "the recount stops at H_BMP_KEPT", not f,
        f"20 FRESH inside 256 kept, 20 more beyond it, payload said 20; "
        f"{len(f)} failure(s)")

    # C33..C39 -- 🔴 THE PAIRING PATTERN, 2026-08-31 (nineteenth session).
    # `bmp.rerun.fresh` is the SAME number under both hypotheses, so the count
    # never separated them; § 6.2a (2) predicts the positions.  C33..C38 are
    # synthetic; C39 is the capture the finding was actually taken from, and
    # it is the regression test on the reading rather than on the code.
    def pairline(**kw):
        """-> (failures, the `pairing` report line) for a synthesised block."""
        n_res = kw.get("n_res", 194)
        cap = []
        f = check_block(synth707(**kw), 0x80A02000,
                        64 + n_res + 128 + 256 + 64 + 1,
                        expect_magic=0x524C5833, report=cap.append)
        return f, next((x for x in cap if x.startswith("  pairing")), "")

    f, line = pairline(kept=512, said=20, fresh_nibbles=20,
                       fresh_at=list(range(10)) + list(range(256, 266)))
    row("C33", "10 pairs {k, k+256} read as PURE PAIRING",
        not f and "10 pair(s), 0 unpaired" in line and "PURE PAIRING" in line,
        line.strip() or "no pairing line")

    f, line = pairline(kept=512, said=20, fresh_nibbles=20)
    row("C34", "20 contiguous FRESH read as ALL SINGLETONS",
        not f and "0 pair(s), 20 unpaired" in line and "SINGLETONS" in line,
        line.strip() or "no pairing line")

    # C35 -- 🔴 the outcome § 6.2a says refutes the model, and it must be
    # SAYABLE.  Without this case, a tool that only ever emits the two clean
    # verdicts would look identical to one that can report the third.
    f, line = pairline(kept=512, said=3, fresh_nibbles=3, fresh_at=[0, 1, 256])
    row("C35", "some paired and some not is reported as MIXED",
        not f and "1 pair(s), 1 unpaired" in line and "MIXED" in line,
        line.strip() or "no pairing line")

    # C36 -- 🔴 THE POPULATION CONTROL.  An all-FRESH region pairs every k with
    # k+period trivially, so PURE PAIRING off it is a verdict from a region
    # that says nothing.  This is the case that a tool without the control
    # passes while being wrong.
    f, line = pairline(kept=512, said=512, fresh_nibbles=512)
    row("C36", "an all-FRESH region gets NO verdict, not PURE PAIRING",
        "no verdict" in line and "PAIRING" not in line,
        line.strip() or "no pairing line")

    f, line = pairline(kept=512, said=0, fresh_nibbles=0, stale_nibbles=512)
    row("C37", "a region with no FRESH at all gets NO verdict",
        "no verdict" in line and "0 FRESH" in line,
        line.strip() or "no pairing line")

    # C38 -- 🔴 THE PERIOD IS kept/2 AND NOT THE NUMBER 256.  A boundary point
    # of 256 victims pairs at 128; a tool with 256 written into it finds no
    # pair at all and reports ALL SINGLETONS, which is a different answer to
    # the same question.
    f, line = pairline(kept=256, said=4, fresh_nibbles=4, adv=256,
                       fresh_at=[0, 1, 128, 129])
    row("C38", "the pairing period is kept/2, not a hardcoded 256",
        not f and "period 128" in line and "2 pair(s), 0 unpaired" in line,
        line.strip() or "no pairing line")

    # C39 -- 🔴 THE READING ITSELF, on the committed capture it came from.
    # 量 2026-08-31, power cycle 9: 20 FRESH at
    # {15,16, 231..238, 271,272, 487..494} -- ten {k, k+256} pairs and no
    # singleton.  If this row ever goes red, either the capture moved or the
    # analysis behind `CPU-25`'s second route did.
    try:
        pw = parse_words(_read(PAIRRB))
        cap = []
        f = check_block(pw, 0x80A02000, 718, expect_magic=0x524C5833,
                        report=cap.append)
        line = next((x for x in cap if x.startswith("  pairing")), "")
        row("C39", "the committed 2026-08-31 capture reads 10 pairs, 0 alone",
            not f and "10 pair(s), 0 unpaired" in line
            and "PURE PAIRING" in line,
            line.strip() or "no pairing line")
    except (OSError, Refuse) as e:
        row("C39", "the committed 2026-08-31 capture reads 10 pairs, 0 alone",
            False, f"{e}")

    # C24..C30 -- Group F, 2026-08-31.  Synthetic, and for the same reason
    # C17..C23 are: the 718-word payload has never been seated.  A clean leg
    # set is 20,000-ish ticks; the numbers below are shapes, not predictions --
    # § 6.8.2 owns the bands and this file owns none of them.
    GF_OK = {194: 0x3FC00000, 195: 9000, 196: 21000, 197: 9100, 198: 21100,
             199: 2000, 200: 3000, 201: 9050, 202: 0, 203: 0x0F0F, 204: 0}

    def gfsynth(over=None):
        """The clean leg set with `over` applied.  A dict rather than keyword
        arguments because the keys are RESULT INDICES, and an index is not an
        identifier -- writing them as names here would be a second copy of the
        layout in a file whose whole point is reading the layout out of the
        block."""
        d = dict(GF_OK)
        d.update(over or {})
        return synth707(512, 20, 20, n_res=205, gf=d)

    f = check_block(gfsynth(), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C24", "a consistent Group F passes", not f,
        f"718-word block, seven legs, 0 faults; {len(f)} failure(s)")

    f = check_block(gfsynth({204: 1}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C25", "a fault inside Group F voids the group",
        any("void rather than merely suspect" in x for x in f),
        f"f.faults=1; {len(f)} failure(s)")

    f = check_block(gfsynth({197: 0xFFFFFFFF}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C26", "tc_ticks' never-written sentinel on a leg FAILS",
        any("FFFFFFFF" in x and "boot.seq" in x for x in f),
        f"f.boot.seq=FFFFFFFF; {len(f)} failure(s)")

    f = check_block(gfsynth({203: 0x0F00}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C27", "a window that returned sixteen identical words FAILS",
        any("floating bus" in x for x in f),
        f"f.live=00000F00, boot byte zero; {len(f)} failure(s)")

    f = check_block(gfsynth({201: 10500}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C28", "f.win.seq2 more than 10 % from f.win.seq FAILS",
        any("not repeatable" in x for x in f),
        f"9000 against 10500, 16.7 % apart; {len(f)} failure(s)")

    # 🔴 C28b is C28's other edge.  One case at a boundary passes whether the
    # comparison is `>` or `>=`, and `console-capture`'s guard cost ten live
    # mutants to that exact shape.  9,000 -> 9,890 is 9.9 % and must be clean.
    f = check_block(gfsynth({201: 9890}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C28b", "9.9 % apart is still accepted", not f,
        f"9000 against 9890; {len(f)} failure(s)")

    f = check_block(gfsynth({196: 2500}), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C29", "a window faster than uncached DRAM FAILS",
        any("FASTER than" in x for x in f),
        f"f.win.str 2500 against f.dram.str 3000; {len(f)} failure(s)")

    POIS = 0xDEADC0DE
    allp = {k: POIS for k in range(195, 202)}
    f = check_block(gfsynth(allp), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C31", "all seven legs poisoned is a REFUSAL, not seven findings",
        not f, f"the g_timer gate shut; {len(f)} failure(s)")

    mix = dict(allp)
    del mix[199]
    f = check_block(gfsynth(mix), 0x80A02000, 718,
                    expect_magic=0x524C5833, report=_quiet)
    row("C32", "SOME legs poisoned and some written FAILS",
        any("all-or-nothing" in x for x in f),
        f"six of seven poisoned; {len(f)} failure(s)")

    # 🔴 C30 IS THE POPULATION CONTROL FOR C24..C29, and it is the one that
    # would have caught a length test.  The SAME synthesiser at n_res=194 --
    # the 707-word layout -- carries Group F's numbers in its ROW area, and
    # every check above must decline to run rather than read them.  Without
    # it, C25..C29 pass on a tool that fails every block it is handed.
    f = check_block(synth707(512, 20, 20, n_res=194, gf={204: 1}),
                    0x80A02000, 707, expect_magic=0x524C5833, report=_quiet)
    row("C30", "a 707-word block declines Group F rather than reading it",
        not f, f"n_res=194 with a fault word planted in the row area; "
               f"{len(f)} failure(s)")

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
