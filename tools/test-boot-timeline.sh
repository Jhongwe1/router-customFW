#!/usr/bin/env bash
# Controls for tools/boot-timeline.py.
#
# This tool exists to decide which of two adjacent, equal-length silences a
# published number belongs to. A tool for that job has one failure mode worth
# guarding: producing a confident table that measures the wrong pair of bytes.
# So the controls are about the ANCHORS and about the classifier, not about the
# arithmetic.
#
#   B1  the anchor is identified, not chosen. Over the nine captures that
#       existed before 2026-08-25, anchor C must reproduce CLK-15's published
#       range -- 344.7 .. 356.9 ms -- to the tenth of a millisecond, and the
#       other three anchors must NOT. That is what pins the definition.
#   B2  cold/warm is classified by the loader's own line and not by the
#       artifact byte. The mutation: delete the artifact byte from a copy of a
#       cold capture and the classification must not move.
#   B3  `entry` refuses a capture whose command is not a reset. `H1b` sent
#       `J 80500000`, so the largest gap before its boot text contains probe1's
#       whole run -- 0.1237 s, which is CLK-03's number and not CLK-14's.
#   B4  the population control: pointed at a directory with no boot text it
#       must REFUSE, not print an empty table with a clean summary.
# P2-1 (2026-09-23), the tool past the loader:
#   B5  the late-open detector names loader text only; kernel boots are
#       counted, not named.   B6  D1: segments equal an independent derivation
#       on a vendor and an rlxfw capture; one capture through both tables
#       differs exactly where the tables do.   B7  anchors named, n on every
#       cell.   B8  firmware, variant and image against a grep of each capture.
#   B9  cold/warm inherited, and when it must not be.   B10  the host-probe
#       join, and its refusal without t0_mono.   B11  TERM-1's silences.
#   B12  the per-seating scale fit, with a positive and a negative control.
#   B13  the retro's identity line and TSV.   B14  refusals.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
PY="${PYTHON:-python3}"
BT="$HERE/boot-timeline.py"

pass=0; fail=0
ck () {
    if [ "$2" = "$3" ]; then printf '  ok     %-54s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-54s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}

# The nine captures that existed before 2026-08-25 -- CLK-15's own population.
NINE=""
for d in 2026-08-24 2026-08-24b 2026-08-24c 2026-08-24d 2026-08-24e 2026-08-24f; do
    for f in "$ROOT/bench/$d"/*.log; do
        [ -e "$f" ] || continue
        grep -q 'Booting' "$f" 2>/dev/null && NINE="$NINE $f"
    done
done
ck "the pre-2026-08-25 population is nine captures" 9 "$(echo $NINE | wc -w)"

echo
echo "=== B1: anchor C reproduces CLK-15's published range, and no other does ==="
rng () {   # rng <anchor> -> "min max" over the nine, in milliseconds
    "$PY" "$BT" --anchor "$1" $NINE 2>/dev/null \
      | sed -n 's/^  booting, all  *n=[0-9]* *\([0-9.]*\) \.\. \([0-9.]*\).*/\1 \2/p'
}
ck "anchor C min (CLK-15 says 344.7 ms)" "0.3447" "$(rng C | cut -d' ' -f1)"
ck "anchor C max (CLK-15 says 356.9 ms)" "0.3569" "$(rng C | cut -d' ' -f2)"
# The pair. If every anchor gave the same numbers, B1 would be measuring
# nothing and "C is the one CLK-15 used" would be a guess.
same=0
for a in A B D; do [ "$(rng "$a")" = "$(rng C)" ] && same=$((same+1)); done
ck "the other three anchors differ from C"      0 "$same"

echo
echo "=== B2: cold/warm comes from the loader, not from the artifact byte ==="
base="$("$PY" "$BT" "$ROOT/bench" 2>/dev/null)"
# 🔄 7/7 until 2026-08-25b, which added one cold boot and one warm reset.
# 🔄 8/8 until 2026-08-30 (seating 5), which added THREE events from two
# directories -- and they were isolated before this number was touched:
# `2026-08-30/A-catch` and `2026-08-30b/A-catch` are the two power-ons (cold),
# and `2026-08-30/QJ` is warm because `probe3` ends by arming the watchdog and
# handing the prompt back, so its capture holds a second `Booting...`.
# 量: the same tree with those two directories removed still reports 8 cold,
# 8 warm, so the delta is exactly +2 cold / +1 warm and nothing reclassified.
# Re-measured rather than loosened: a population count that is allowed to drift
# is not a control.
# 🔄 10/9 until 2026-08-30 (seating 6), which added TWO cold power-ons and no
# warm reset: `2026-08-30c/V-A` (power cycle 3) and `2026-08-30d/Z-A` (power
# cycle 4). Same isolation check: the tree with those two directories removed
# still reports 10 cold, 9 warm, and each directory alone reports 1 cold /
# 0 warm -- so the delta is exactly +2 cold / +0 warm and nothing reclassified.
# 🔴 This is the assertion that broke CI on 2026-08-30, and the reason is worth
# more than the number: the session ran `ci-census --only <the suites it
# touched>` before pushing, and it had touched `tools/` -- but what it ALSO
# touched was `bench/`, which is the POPULATION every census-shaped case here
# reads. "Only the suites you changed" is the wrong rule when what changed is
# data. Every seating moves this line.
# 🔄 12/9 until 2026-08-31 (seating 7), which added TWO cold power-ons and no
# warm reset: `2026-08-31/W-A` (power cycle 5) and `2026-08-31b/X-A` (power
# cycle 6). Same isolation check, run before this line was touched: the tree
# with those two directories removed still reports 12 cold, 9 warm, and each
# directory alone reports 1 cold / 0 warm -- so the delta is exactly
# +2 cold / +0 warm and nothing reclassified. This seating ran the whole suite
# set rather than `--only`, for the reason the paragraph above gives, and this
# is the one case it caught.
# 🔄 14/9 -> 18/11 on 2026-08-31 (seating 8, `bench/2026-08-31c`), which is FOUR
# cold power-ons and TWO warm resets: `K-A`, `K2-A`, `K3-A`, `K4-A`, and the
# watchdog reboots inside `K-J` and `K2-J`. Isolation check, run before this
# line was touched: every bench directory EXCEPT `2026-08-31c` still reports
# 14 cold, 9 warm, and `2026-08-31c` alone reports 4 cold / 2 warm -- so the
# delta is exactly +4/+2 and nothing was reclassified. It went red here again,
# which is twice in two seatings, and both times the whole-suite rule is what
# caught it.
# 🔴 AND THE POPULATION CHANGED IN A WAY A COUNT CANNOT SHOW. Three of these
# four colds are power-ons after an off of MINUTES (~1-2, 0-7, 35.1); every
# cold before them was the first power-on of a seating, hours or days after the
# last. `SPEC.md`'s `CLK-15 cold/warm` row rested on the two ranges being
# DISJOINT, and after this seating they overlap. This case asserts the count;
# nothing here asserts the ranges, and that is stated so the green is not read
# as covering them.
# 🔄 18/11 -> 19/32 on 2026-09-01 (seating 9, `bench/2026-09-01`), which is
# ONE cold power-on and TWENTY-ONE warm resets: `Y-A`, then `Y-j1`,
# `Y-r02`..`Y-r20` and `T-rz`. Isolation check, run before this line was
# touched: every bench directory EXCEPT `2026-09-01` still reports 18 cold,
# 11 warm, and `2026-09-01` alone reports 1 cold / 21 warm -- so the delta is
# exactly +1/+21 and nothing was reclassified. Third seating in a row that
# turned this case red, and all three times the run-every-suite rule caught it.
# 🔄 19/32 -> 20/35 on 2026-09-02 (seating 10, `bench/2026-09-02`), which is
# ONE cold power-on and THREE warm resets: `LP-A`, then `LP-e5`, `LP-e5b` and
# `LP-rz` -- the last of those being `looprun`'s own S4, so a stage this
# project did not type by hand is now in this population. Isolation check, run
# before this line was touched: the 394 logs OUTSIDE `2026-09-02` still report
# 19 cold, 32 warm, and `2026-09-02` alone reports 1 cold / 3 warm -- so the
# delta is exactly +1/+3 and nothing was reclassified. Fourth seating in a row
# that turned this case red, and all four times it was the run-every-suite
# rule that caught it rather than a `--only` run.
# 🔄 20/35 -> 21/36 on 2026-09-03 (seating 11, `bench/2026-09-03`), which is
# ONE cold power-on and ONE warm reset: `SM-A`, the ESC catch that opened the
# seating, and `SM-rz`, `looprun`'s own S4. Isolation check, run before this
# line was touched: every directory EXCEPT `2026-09-03` still reports 20 cold,
# 35 warm, and `2026-09-03` alone reports 1 cold / 1 warm -- so the delta is
# exactly +1/+1 and nothing was reclassified. Fifth seating in a row that
# turned this case red.
# 🔄 21/36 -> 22/37 on 2026-09-04 (seating 12, `bench/2026-09-04`), which is
# ONE cold power-on and ONE warm reset: `SM-A`, the ESC catch that opened the
# seating, and `SM-rz`, `looprun`'s own S4.  Isolation check, run before this
# line was touched: every directory EXCEPT `2026-09-04` still reports 21 cold,
# 36 warm, and `2026-09-04` alone reports 1 cold / 1 warm -- so the delta is
# exactly +1/+1 and nothing was reclassified.  Sixth seating in a row that
# turned this case red.
# 🔴 A SECOND `looprun` ran on the same seating and produced NO row, which is
# the right answer rather than a miss: `SN-rz` sent `J BFC00000` while the
# board was in Linux, where `J` is not a command, so no reset happened and no
# boot text exists to classify.  `looprun`'s own S4 assertion caught it and
# stopped before the rescue stage -- and the tool agrees, because the seating
# reports `33 capture(s) produced no row; 0 of them hold boot text`.
# ⚠️ The other EIGHTEEN captures of that seating produce no row, and the tool
# says so itself: `NOT CLASSIFIED: 18 capture(s) produced no row; 0 of them
# hold boot text`. They are shell captures taken at a prompt after S7, so
# having no boot line is correct rather than a miss -- and the `0 of them hold
# boot text` half is what makes that a reading instead of an assumption.
# 🔄 22/37 -> 24/37 on 2026-09-06 (seating 13, `bench/2026-09-06`), which is
# THREE power-ons and NO warm reset -- `looprun` ran with `--skip S2,S3,S4` on
# every cycle, so its own S4 (`J BFC00000`) never fired and this is the first
# seating since 2026-09-02 to add no warm row at all. Isolation check, run
# before this line was touched: every directory EXCEPT `2026-09-06` still
# reports 22 cold, 37 warm, and `2026-09-06` alone reports 2 cold / 0 warm --
# so the delta is exactly +2/+0 and nothing was reclassified. Seventh seating
# in a row that turned this case red, and the seventh time it was the
# run-every-suite rule rather than a `--only` run that caught it.
# 🔴 THREE POWER-ONS AND TWO COLD ROWS, and the missing one is a reading rather
# than a miss. `SQ-A` is the second cycle's ESC catch and the operator reached
# the power switch before the capture opened the port, so stage-1's banner went
# to a port nobody was listening on. The tool does not drop it -- it names it:
# `bench/2026-09-06/SQ-A.log -- boot text but no `Booting` anchor -- the
# capture opened after the board started`, and it is the `1 of them hold boot
# text` in that seating's NOT CLASSIFIED line. **So this classifier, which
# knows nothing about the seating's procedure, independently measured the same
# operator error that `bench/2026-09-06/CORRECTIONS-block10.md` § 3.7 argues
# from the capture's shape.** The fix (wait ten seconds after replying, before
# touching power) has its own control: `SR-A`, taken with it, classifies cold.
# 🔄 24/37 -> 26/48 on 2026-09-06 (seating 14, `bench/2026-09-06b`), and this is
# the biggest single-seating delta the case has ever taken: TWO power-ons and
# ELEVEN warm resets. The warm ones are new in kind as well as in number -- they
# are not `looprun`'s `S4`, which was skipped on all twelve runs, but
# `busybox reboot -f` typed into the shell of the boot before (`SPEC.md`
# `FW-37`), which is what let one power press carry twelve boots. Isolation
# check, run before this line was touched: every directory EXCEPT
# `2026-09-06b` still reports 24 cold, 37 warm, and `2026-09-06b` alone reports
# 2 cold / 11 warm -- so the delta is exactly +2/+11 and nothing was
# reclassified. Eighth seating in a row that turned this case red, and the
# eighth time the run-every-suite rule rather than a `--only` run caught it.
# 🟢 And this seating gives the case something none of the seven before it did:
# a cold row and eleven warm rows from the SAME power cycle --
# `cold - max(warm) = +0.0101 s`, the largest warm population since 2026-09-01.
# 🔄 26/48 -> 27/57 on 2026-09-06 (seating 15, `bench/2026-09-06c`): ONE power-on
# and NINE warm resets. The warm ones are `busybox reboot -f` typed into the
# shell of the boot before (`SPEC.md` `FW-37`) and not `looprun`'s `S4`, which
# was skipped on all ten runs -- the same shape as seating 14, one press
# carrying ten boots. Isolation check, run before this line was touched: every
# directory EXCEPT `2026-09-06c` still reports 26 cold, 48 warm, and
# `2026-09-06c` alone reports 1 cold / 9 warm -- so the delta is exactly +1/+9
# and nothing was reclassified. NINTH seating in a row that turned this case
# red, and the ninth time the run-every-suite rule rather than a `--only` run
# caught it.
# ⚠️ SEVENTY-SIX captures of that seating produce no row and the tool says so
# itself -- `NOT CLASSIFIED: 76 capture(s) produced no row; 0 of them hold boot
# text`. They are shell captures taken at a prompt after S7, plus twenty-four
# `X*` cells that deviate from the card, so having no boot line is correct
# rather than a miss; the `0 of them hold boot text` half is what makes that a
# reading instead of an assumption.
# 🔄 27/57 -> 28/66 on 2026-09-08 (seating 16, `bench/2026-09-08`), which is ONE
# cold power-on and NINE warm resets -- the same +1/+9 shape as seating 15, and
# for the same reason: `C1-A` is the ESC catch the operator powered into, and
# `C2-A`..`C10-A` are `busybox reboot -f` typed into the shell of the boot
# before (`SPEC.md` `FW-37`), so one press carried ten boots. `looprun`'s own
# `S4` is absent again -- the card ran `--skip S2,S3,S4` because every reset in
# it is a `Cn-A` cell. Isolation check, run before this line was touched: the
# whole tree reports 28 cold / 66 warm and `2026-09-08` alone reports
# 1 cold / 9 warm, and 27+1 = 28 with 57+9 = 66 -- so the delta is exactly
# +1/+9 and nothing was reclassified. TENTH seating in a row that turned this
# case red, and the tenth time the run-every-suite rule caught it.
# 🟢 A second summary line agrees without being asked: `booting, cold n=28` and
# `booting, warm n=66` are computed from a different code path than the C-8
# classification line this case greps, so the count has two sources.
# ⚠️ `entry, warm n=32` did NOT move, and that is a reading rather than an
# oversight: this seating's warm resets are `busybox reboot -f`, not a typed
# `J <addr>`, and `--skip S4` meant no `looprun` reset ran -- so nothing here
# contributes an entry interval. The case below still asserts 32.
# ⚠️ SEVENTY-SEVEN captures of this seating produce no row, `0 of them hold
# boot text`. They are the shell captures after S7 plus the nineteen off-card
# `BIS-*` verify rungs, the three `SEC-*` cells and `BBLIST`.
# 🔄 2026-09-08 (seating 17): 28/66 -> 31/74. ELEVENTH seating in a row to turn
# this case red, and the eleventh time the run-every-suite rule caught it -- the
# derive-the-suites grep cannot see this one, because nothing in the diff names
# this file; it sweeps `bench/` as a POPULATION.
# 🟢 The delta is a consistency check that costs nothing and was not designed:
# +3 cold is exactly the three power cycles seating 17 spent (`C1-A`, `R1-A`,
# `R2-A2`), and +8 warm is exactly the eight watchdog resets whose loader banner
# was caught -- nine bites happened, and `C3-B`'s window closed before its own
# (41.9 s) answer arrived, so it contributes no row. The classifier reaches
# those two numbers from the loader's own reset-cause line, knowing nothing
# about power switches or `biteraw`.
# 2026-09-09, seating 19 (bench/2026-09-09b): +1 cold +8 warm -> 33/108.
# 🔄 33/108 -> 34/141 on 2026-09-10 (seating 20, `bench/2026-09-10`), which
# is ONE cold power-on and THIRTY-THREE warm resets -- and it is by far the
# largest single-seating delta this case has taken.  The cold one is `C1-A`,
# the 150 s ESC window the operator pressed power inside.  The thirty-three
# decompose exactly: SIXTEEN are `looprun`'s own S4 (`J BFC00000`) -- seventeen
# invocations minus `C1`, which ran `--skip S2,S3,S4` because `C1-A` had
# already reset the board -- and SEVENTEEN are `busybox reboot -f` cells
# (`C1-RB`..`C13-RB` plus the off-card `X17-RB`, `X21-RB`, `X22-RB`, `X29-RB`),
# each a watchdog bite at `OVSEL` 0 (`FW-37`, `CLK-08b`).  Isolation check, run
# before this line was touched: every directory EXCEPT `2026-09-10` still
# reports **33 cold, 108 warm**, and `2026-09-10` alone reports **1 cold, 33
# warm** -- so the delta is exactly +1/+33 and nothing was reclassified.
# ⚠️ The seating's other 135 captures produce no row and the tool says
# `135 capture(s) produced no row; 0 of them hold boot text` -- they are shell
# captures taken at a prompt after S7, so having no boot line is correct, and
# the `0 of them hold boot text` half is what makes that a reading rather than
# an assumption.  The corpus-wide `4 of them hold boot text` is older than this
# seating and none of the four is here.
# 🔴 THIS COMMENT DOES NOT ADD AN ORDINAL, AND THE REASON IS A READING.  The
# first draft said "EIGHTH seating in a row" and "the seventh time"; both were
# written without deriving them.  量, this file's own chain: the last ordinal
# it uses is **ELEVENTH** (seating 17), the entry after it (seating 19,
# `bench/2026-09-09b`) carries none, and that entry's stated `+1 cold +8 warm`
# does not close the gap from `31/74` to `33/108` -- so the chain is
# INCOMPLETE and no ordinal can be derived from it.  A number that cannot be
# derived is not written down here.
# 🔴 What IS derivable and is the point: `CLAUDE.md` carries the rule -- *a
# seating changes DATA, and data
# is what these cases assert on, so after a seating run every suite that can
# run on this host* -- and it was read past again.
# 🔄 34/141 -> 35/145 on 2026-09-14 (seating 21, `bench/2026-09-14`), which is
# ONE cold power-on and FOUR warm resets -- the smallest single-seating delta
# this case has taken, because the seating ran two bare-metal payloads and no
# kernel.  The cold one is `C1-A`, the 150 s ESC window the operator pressed
# power inside.  🟢 **The four warm ones are the four payload bites**, and that
# is a reading the card did not predict: `C1-P4j`, `C1-P5j`, `X1-P4j` and
# `X1-P5j` each carry the loader's `Reboot Result from Watchdog Timeout!` INSIDE
# the same capture as the payload's report, because every one of those cells
# carried `--esc-after` and caught the loader on the way back.  So `RESET=1`
# actually happened four times, confirmed by the loader's own line rather than
# by the prompt returning.  Isolation check, run before this line was touched:
# every directory EXCEPT `2026-09-14` still reports **34 cold, 141 warm**, and
# `2026-09-14` alone reports **1 cold, 4 warm** -- so the delta is exactly +1/+4
# and nothing was reclassified.
# ⚠️ The seating's other 9 captures produce no row and the tool says
# `9 capture(s) produced no row; 0 of them hold boot text` -- they are `DW`
# replies and the `?` help text taken at the loader prompt, so having no boot
# line is correct, and the `0 of them hold boot text` half is what makes that a
# reading rather than an assumption.
# 🟢 And one number that came free: within this one power cycle the cold
# `booting` interval is **0.3464 s** against four warm ones spanning
# **0.3445 .. 0.3524 s**, so `cold - max(warm) = -0.0060 s` -- the cold boot is
# NOT the slow one here, which is the opposite of what a reader would guess and
# is why the tool prints the within-one-power-cycle line at all.
# 🔴 THIS IS THE THIRD TIME `CLAUDE.md`'s rule has fired on this suite, and the
# full sweep is what caught it: `tools/desk-sweep.py run` reported
# `73 green, 2 expected-red, 1 unexpected` with this suite as the one, while a
# `--only` run over the suites whose CODE changed would have been green --
# nothing in this file changed, only the data it asserts on.
# 🔄 35/145 -> 36/159 on 2026-09-14 (seating 22, `bench/2026-09-14b` and
# `bench/2026-09-14c`): ONE cold power-on and FOURTEEN warm resets, from a
# single power press. The cold one is `C1-A`, the ESC window the operator
# pressed power inside; two of the warm ones are `probe6` biting its own
# watchdog at the end of a run (`C1-P6j`, `X1-P6j2`) and the other twelve are
# seven `looprun` `S4` resets plus five `busybox reboot -f` typed into the
# shell of the boot before. Isolation check, run before this line was touched:
# every directory EXCEPT those two still reports 35 cold, 145 warm; `2026-09-14b`
# alone reports 1 cold / 2 warm and `2026-09-14c` alone 0 cold / 12 warm -- so
# the delta is exactly +1/+14 and nothing was reclassified. Caught by the
# run-every-suite rule at the desk this time, before the push.
# 🔄 36/159 until 2026-09-15 (seating 23), which added ONE cold power-on
# (`2026-09-15/C1-esc`) and ONE warm reset (`2026-09-15/up2-rz`, looprun's `S4`
# `J BFC00000`).  Isolation check, run before this line was touched: every
# directory EXCEPT `2026-09-15` still reports 36 cold, 159 warm, and
# `2026-09-15` alone reports 1 cold / 1 warm -- so the delta is exactly +1/+1
# and nothing was reclassified.
# 🔴 NOT caught at the desk this time.  The closeout ran a hand-picked list of
# ten gates instead of every suite, and this went red on GitHub -- the third
# time this assertion has, and the first time the run-every-suite rule was
# available and skipped.  `CLAUDE.md` states that rule; the previous segment
# followed it and caught the 35→36 move before its push.
# 🔄 37/160 until 2026-09-16 (seating 24), which added ONE cold power-on
# (`2026-09-16/C1-A`) and SEVEN warm resets -- `C1-P3j` and `X6-P3j2` are
# `probe3`'s own watchdog bites, `X3-RB` and `X5-RB` are `busybox reboot -f`,
# and `uc1-rz`, `uc1-att2-rz`, `uc1-att3-rz` are looprun's three `S4`
# `J BFC00000`.  Isolation check, run before this line was touched: every
# directory EXCEPT `2026-09-16` still reports 37 cold, 160 warm, and
# `2026-09-16` alone reports 1 cold / 7 warm -- so the delta is exactly +1/+7
# and nothing was reclassified.  🟢 The breakdown is also an independent audit
# of that seating's own account of itself: one power cycle against a budget of
# one, and seven warm resets, which is what its record says.
# 🔴🔴 NOT caught at the desk, AGAIN, and this is the fourth and fifth time
# this assertion has gone red on GitHub.  The comment directly above says the
# previous segment ran "a hand-picked list of ten gates instead of every
# suite"; this one ran a hand-picked list of NINE, pushed, went red, pushed a
# repair without running the sweep either, and went red on the same assertion a
# second time.  **`tools/desk-sweep.py` exists for exactly this** -- it reads
# every `run:` step out of `ci.yml` rather than reconstructing a list -- and it
# was not run.  量 2026-09-16 over the last 60 completed CI runs: 10 red
# (17 %), and every one of the five distinct failing steps is a `.md` or
# data-population check that runs at this desk in seconds.  The rule is not
# "be more careful", it is "after a seating, run the sweep".
# 🔄 2026-09-17 (seating 25): 167 -> 169 warm.  Three `J BFC00000` resets
# and one `busybox reboot -f`; the seating's ONE cold power-on is NOT here,
# because its rescue capture went to $FWRE_WORK and not to bench/ -- which is
# why the cold count is unchanged at 38.  This row is the case CLAUDE.md
# names: a seating moves the POPULATION every census-shaped case reads, and
# `--only <the suites you touched>` cannot see it.
# 🔄 2026-09-17 (seating 26): 38/169 -> 39/170. `bench/2026-09-17b` alone
# reports `1 cold, 1 warm` -- the cold is `X1-esc`, the power-on that opened the
# seating, and the warm is `p11e-rz`, `looprun`'s own `J BFC00000`. 🔴 This
# suite went RED ON CI while the desk closeout was green, for the third time and
# for the reason CLAUDE.md names: the closeout ran spec-check, capdate,
# check-predictions, cardcheck, ledgerscan and xcheck, and **not this one**,
# because none of its code had changed. A seating changes DATA, and data is what
# this case asserts on.
# 🔄 2026-09-19 (seating 27): 39/170 -> 41/171, and BOTH deltas are named.
# +2 cold is this seating's two cold power-ons -- X1-esc at 00:58 and X16-esc3
# at ~02:00, the second forced by a `PHYR` fault that hung the loader.
# +1 warm is `looprun`'s S4, one `J BFC00000`, capture `r6sw1-rz`.
# 🔴 FOURTH time this row has gone red for the same reason, and the desk sweep
# is what caught it again while a six-gate targeted closeout ran green. The
# durable fix is not a bigger number: it is to assert the PROPERTY and report
# the count, the shape `ci-expected.tsv:338` already argues for. Carried
# forward rather than done here, because changing what this case asserts is
# not a thing to do at the end of a seating.
# 🔄 2026-09-20 (FIFTH red, and this is the fix rather than a fifth number).
# The constant is gone.  What is asserted now is what the constant was only
# ever standing in for:
#   * the classifier produced a parseable summary at all -- an empty or
#     renamed summary line reads as 0/0/0 and must not read as clean;
#   * `unknown` is 0, i.e. no row the tool built was left unclassified;
#   * neither class is empty, and neither is BELOW the count measured on
#     2026-09-20 (43 cold, 177 warm).  `bench/` is append-only committed
#     evidence, so a FLOOR can go stale without ever going red -- that is the
#     whole difference from the equality it replaces, and it is the shape
#     `ci-expected.tsv:338` argues for.
# WHAT THIS STILL CATCHES that the old case caught: a capture disappearing
# from bench/, a classifier that stops classifying, a class collapsing to
# empty, and an `unknown` appearing.
# 🔴 WHAT IT NO LONGER CATCHES, stated here rather than discovered later: a
# classifier that moves a capture from cold to warm while both stay above
# their floors.  That is covered instead by the NAMED witnesses -- B2b's
# `A-catch` must stay cold and `H2a` must stay warm, immediately below -- and
# by B2's own mutation case.  Those are invariant to corpus size.
c8="$(printf '%s\n' "$base" | sed -n 's/^classified by the loader.s own line (C-8): //p')"
n_cold="$(printf '%s\n' "$c8" | sed -n 's/^\([0-9][0-9]*\) cold.*/\1/p')"
n_warm="$(printf '%s\n' "$c8" | sed -n 's/.*[^0-9]\([0-9][0-9]*\) warm.*/\1/p')"
n_unk="$( printf '%s\n' "$c8" | sed -n 's/.*[^0-9]\([0-9][0-9]*\) unknown$/\1/p')"
echo "  observed  C-8 classification: ${n_cold:-?} cold, ${n_warm:-?} warm, ${n_unk:-?} unknown  (floors 43/177, unknown must be 0)"
ck "C-8 classifies every row, both classes above their floor" yes \
   "$([ -n "$n_cold" ] && [ -n "$n_warm" ] && [ "${n_unk:-1}" = 0 ] \
      && [ "${n_cold:-0}" -ge 43 ] && [ "${n_warm:-0}" -ge 177 ] \
      && echo yes || echo no)"

# 🆕 B2b: the artifact prefix is not always one byte, and it is not always the
# instrument's. Both halves have to hold or the column means something
# different on different rows.
ck "the two-byte prefix is reported whole" 1 \
   "$(printf '%s\n' "$base" | grep -c '2026-08-25b .*A-catch .*cold  00FC')"
# It used to read `g(0, 1)` = the gap BETWEEN the two artifact bytes = 4.2 ms.
# Anything under 0.1 s here is that defect back.
av="$(printf '%s\n' "$base" | awk '/2026-08-25b/ && /A-catch/ {print $5}')"
ck "and its artifact interval is a boot, not 4 ms" yes \
   "$(awk -v v="${av:-0}" 'BEGIN{print (v>0.30 && v<0.40) ? "yes" : "no"}')"
# And the other half: a WARM capture has device output before `Booting`, so it
# must have NO artifact column at all. Without this the same change reported
# 63.7 s for H2a and a pooled spread of 662%.
ck "a warm capture has no artifact byte"  0 \
   "$(printf '%s\n' "$base" | awk '/H2a / && /warm/ {print $4}' | grep -cv -- '--')"
# The mutation: take the one cold capture that HAS an artifact byte, strip it,
# and the classification must stay cold. If it flips, the classifier is reading
# the wrong evidence.
mkdir -p "$T/m"
tail -c +2 "$ROOT/bench/2026-08-25/A-catch.log" > "$T/m/A-catch.log"
"$PY" - "$ROOT/bench/2026-08-25/A-catch.timing" "$T/m/A-catch.timing" <<'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
out = []
for line in open(src, encoding="utf-8"):
    s = line.strip()
    if not s or s.startswith("#"):
        out.append(line); continue
    off, t = s.split()
    out.append("%d %s\n" % (max(0, int(off) - 1), t))
open(dst, "w", encoding="utf-8", newline="\n").writelines(out)
PYEOF
mut="$("$PY" "$BT" "$T/m/A-catch.log" 2>/dev/null)"
ck "still classified cold with no artifact byte" 1 \
   "$(printf '%s\n' "$mut" | grep -c '1 cold, 0 warm')"
ck "and its artifact interval is gone"           1 \
   "$(printf '%s\n' "$mut" | grep -c 'artifact (cold only by def.)   n=0')"

echo
echo "=== B3: entry refuses a command that is not a reset ==="
# H1b sent `J 80500000`. Its pre-boot gap is 0.1237 s -- probe1's delay loop,
# which is CLK-03's measurement. It must not appear in a reset column.
ck "H1b has no entry value"  1 \
   "$(printf '%s\n' "$base" | awk '$1=="H1b"{print ($NF=="--") ? 1 : 0}')"
ck "H3a, which sent J BFC00000, has one" 1 \
   "$(printf '%s\n' "$base" | awk '$1=="H3a"{print ($NF=="--") ? 0 : 1}')"
# 🔄 6 -> 27 with seating 9's twenty-one resets. The seating's own twenty-one
# are 0.0017 .. 0.0028 s, mean 0.0024, spread 43.7 % -- five times tighter than
# the six that preceded them (0.0021 .. 0.0211, spread 211 %), because they are
# twenty-one repetitions of one command inside one power cycle.
# 🔄 27 -> 30 on 2026-09-02 (seating 10): three more warm resets carry an
# `entry` -- LP-e5 and LP-e5b at `--esc-period 0.0005` and LP-rz, which is
# `looprun`'s own S4, at 0.002. Isolation: everything except bench/2026-09-02
# still reports n=27, and 2026-09-02 alone reports n=3.
# 🟢 And those three are the TIGHTEST sub-population in the corpus --
# 0.0023 .. 0.0024, spread 5.1 % -- because they are one command at two
# cadences 3.2x apart inside one power cycle, which is what separated `entry`
# from the instrument's own read floor. The pooled spread went 499.9 % ->
# 520.9 %, and that is the OLD outlier (0.0211, H3a) dominating a wider n,
# not this seating adding scatter.
# 🔄 30 -> 31 on 2026-09-03 (seating 11): `SM-rz`, `looprun`'s own S4, the one
# warm reset of that seating, `entry` 0.0024. It lands inside the tight
# sub-population above (0.0023..0.0024) and not near the outlier, so the pooled
# spread moving 520.9 % -> 527.1 % is the OLD 0.0211 (H3a) dominating a wider n
# again, not this seating adding scatter -- the same reading as the line above,
# and it is restated because a spread that grows while every new point is
# central is the shape a reader would otherwise misread.
# 🔄 31 -> 32 on 2026-09-04 (seating 12): `SM-rz`, `looprun`'s own S4 again,
# the one warm reset of that seating, `entry` **0.0020**. It lands inside the
# tight sub-population (0.0017..0.0024) and not near the 0.0211 outlier, so
# the pooled spread moving 527.1 % -> 534.9 % is again the OLD 0.0211 (H3a)
# dominating a wider n. Third seating in a row where the spread grows while
# every new point is central -- restated because that is the shape a reader
# would otherwise misread as this seating adding scatter.
# ⚠️ The seating's SECOND `looprun` (`SN-rz`) is NOT in this population and
# must not be: its `J BFC00000` went to a Linux shell, no reset happened, and
# no boot text exists. It contributes to `NOT CLASSIFIED` instead, where the
# tool's `0 of them hold boot text` half is what makes that a reading.
# 2026-09-09, seating 19: four more warm resets -- three `bite 3` rungs and
# one `biteraw` -- so n=45 -> n=49.
# 🔄 49 -> 65 on 2026-09-10 (seating 20): the same +16 the isolation
# check above measures for this row -- `2026-09-10` alone reports
# `entry, warm  n=16`, and every other directory still reports n=49.
# ⚠️ 33 warm resets but only 16 entry intervals, because an `entry`
# interval needs BOTH ends in one capture and a `-RB` cell ends at the
# loader prompt by design (`--until '<RealTek>'`).
# 🔄 65 -> 71 on 2026-09-14 (seating 22): SIX of the seating's fourteen warm
# resets produce an entry interval. `2026-09-14c` alone reports
# `entry, warm  n=6` and `2026-09-14b` alone reports `n=0` -- both `probe6`
# runs and every `-RB` cell end at the loader prompt by design
# (`--esc-after` / `--until '<RealTek>'`), and an `entry` interval needs BOTH
# ends in one capture. Every other directory still reports n=65.
# 🔄 n=71 until 2026-09-15 (seating 23).  `2026-09-15/up2-rz` is `looprun`'s
# `S4`, which sends `J BFC00000` with `--esc-after 10`, so both ends of the
# interval are in one capture and it qualifies.  Every other directory still
# reports n=71.
# 🔄 n=72 until 2026-09-16 (seating 24).  The three that qualify are
# `2026-09-16/uc1-rz`, `uc1-att2-rz` and `uc1-att3-rz` -- looprun's `S4` on each
# of the three boots, `J BFC00000` with `--esc-after 10`, so both ends of the
# interval are in one capture.  The seating's four OTHER warm resets do not
# qualify and that is the rule working: `C1-P3j` and `X6-P3j2` jump to `probe3`,
# which prints 6.8 KB before biting, and `X3-RB`/`X5-RB` are `reboot -f` from a
# shell -- none of them is a jump straight into a reset.  Isolation check: every
# directory EXCEPT `2026-09-16` still reports n=72, and `2026-09-16` alone
# reports n=3.
# 🔄 2026-09-17 (seating 25): 75 -> 77, the same two rows as above.
# 🔄 2026-09-17 (seating 26): 77 -> 78, one row, and it is `looprun`'s `S4`.
# Isolation check: `bench/2026-09-17b` alone reports `entry, warm n=1`.
# 🔄 2026-09-19 (seating 27): 78 -> 79, one row, and it is the same
# `looprun` S4 that moved the warm count above -- one `J BFC00000`.
# 🔄 2026-09-20: 79 -> 81, and the number stops being an assertion.  This case
# never tested `entry` -- the two cases ABOVE it do, by name: `H1b` sent
# `J 80500000` and must have NO entry value, `H3a` sent `J BFC00000` and must
# have one.  Those are the refutation and they are invariant to corpus size.
# All this row ever asserted was the SIZE of the population they run over, so
# it becomes a FLOOR: the population may not shrink, may not go empty, and the
# `entry, warm` row must exist at all -- a missing row prints nothing, which a
# `grep -c` for a specific number cannot tell from a wrong number.
# 🔴 WHAT IS LOST: a capture that stops qualifying as a warm reset while a new
# one starts is invisible here.  The isolation checks in the comments above
# were how that was actually caught, and they are notes, not cases -- if that
# matters enough to assert, the honest form is a per-directory case over a
# NAMED directory, not a total.
n_entry="$(printf '%s\n' "$base" | sed -n 's/^  entry, warm  *n=\([0-9][0-9]*\).*/\1/p')"
echo "  observed  entry, warm population: ${n_entry:-?}  (floor 81)"
ck "the entry population is non-empty and has not shrunk" yes \
   "$([ -n "$n_entry" ] && [ "${n_entry:-0}" -ge 81 ] && echo yes || echo no)"

echo
echo "=== B3b: a capture that produced no row is NAMED, not dropped ==="
# 量 2026-09-01: `bench/2026-09-01/Y0-A` has a .log and a .timing, sits in a
# directory the tool was pointed at, never became a row, and the summary still
# read `0 unknown` -- because `unknown` counts rows whose CLASS is undecided and
# a capture that never became a row is invisible to it. Two directions, because
# naming all 343 non-boot captures would be as useless as naming none.
mkdir -p "$T/orphan"
# a boot capture that opened after the board started: boot text, no `Booting`
printf 'P0phymode=01, embedded phy\r\n---Ethernet init Okay!\r\n<RealTek>' \
    > "$T/orphan/late-A.log"
printf '# offset seconds\n0 1.000\n1 1.001\n' > "$T/orphan/late-A.timing"
# a DW reply, which is correctly not a boot and must NOT be named
printf 'DW 80500000 1\r\n80500000:\t00000000\r\n<RealTek>' \
    > "$T/orphan/dw.log"
printf '# offset seconds\n0 1.000\n1 1.001\n' > "$T/orphan/dw.timing"
orph="$("$PY" "$BT" "$T/orphan" 2>&1)"
ck "a boot with no Booting anchor is named"   1 \
   "$(printf '%s\n' "$orph" | grep -c 'late-A.log -- boot text but no')"
ck "a DW reply is counted and NOT named"      0 \
   "$(printf '%s\n' "$orph" | grep -c 'dw.log --')"
ck "and both are in the count"                1 \
   "$(printf '%s\n' "$orph" | grep -c 'NOT CLASSIFIED: 2 capture(s)')"
# 🔴 the detector's first version tested only for `chipName` / the banner and
# missed `Y0-A`, whose first bytes are `P0phymode=` -- it did not fire on the
# case it was written for. This asserts the widened set on that exact shape.
ck "the real Y0-A is among them"              1 \
   "$("$PY" "$BT" bench 2>&1 | grep -c '2026-09-01/Y0-A.log -- boot text')"

echo
echo "=== B4: pointed at nothing, it must refuse ==="
mkdir -p "$T/empty"
"$PY" "$BT" "$T/empty" >/dev/null 2>"$T/err"; rc=$?
ck "exit code on an empty directory"     2 "$rc"
ck "and it said so"                      1 "$(grep -c REFUSING "$T/err")"

# =============================================================================
# P2-1, 2026-09-23: the tool past the loader.  Every case below states what
# would refute it before it runs.  Corpus cases assert PROPERTIES and FLOORS,
# never a count of bench/ -- read B2's tape above for why.  Synthetic captures
# are written once, here, by one generator: each part is one read() that
# returned at the time beside it, which is exactly what console-capture's
# .timing records (FW-35).
# =============================================================================
FX="$T/fx"
"$PY" - "$FX" <<'PYEOF'
import json, os, sys
FX = sys.argv[1]

def mk(path, parts, meta=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows, off = [], 0
    for b, t in parts:
        rows.append("%d %.6f" % (off, t))
        off += len(b)
    with open(path, "wb") as fh:
        fh.write(b"".join(b for b, _ in parts))
    with open(path[:-4] + ".timing", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# offset seconds\n" + "\n".join(rows) + "\n")
    if meta is not None:
        with open(path[:-4] + ".meta.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh)

def rlxfw(f=1.0, id0=b"AAAAAAAA"):
    # WLAN -> NIC is the largest gap, 3.25 s exactly at f = 1: B11's plant.
    return [(b"J 80500000\n\r---Jump to address=80500000\n", 0.010 * f),
            (b"\rdecompressing kernel:\r\n", 0.020 * f),
            (b"Uncompressing Linux... done, booting the kernel.\r\n", 0.030 * f),
            (b"done decompressing kernel.\r\n", 1.125 * f),
            (b"start address: 0x80003600\r\n", 1.250 * f),
            (b"RLXFW-B00\r\nRLXFW-ID0=" + id0 + b"\r\n", 1.375 * f),
            (b"RLXFW-B09\r\n", 1.500 * f),
            (b"Realtek WLAN driver driver version 1.6 (2012-12-04)\r\n", 1.750 * f),
            (b"\r\n\r\nProbing RTL8186 10/100 NIC-kenel stack size order[3]...\r\n", 5.000 * f),
            (b"Realtek FastPath:v1.03\r\n", 5.750 * f),
            (b"RLXFW-B10\r\n", 8.500 * f),
            (b"rlxfw: init running, X\r\n", 8.625 * f),
            (b"/bin/sh: can't access tty; job control turned off\r\n# ", 8.750 * f)]

def loader(f=1.0, warm=True, tail=2.5):
    return [(b"J BFC00000\n\r---Jump to address=BFC00000\n\r\r\n", 0.010),
            (b"Booting...\r\n", 0.020),
            (b"\x00", 0.030),
            (b"chipName: UNKNOWN\n\rramSize: 32M\n\r"
             + (b"Reboot Result from Watchdog Timeout!\n" if warm else b" \n"), 0.030 + 0.35 * f),
            (b"\r\n\r---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)\n",
             0.030 + 0.58 * f),
            (b"\r<RealTek>", tail)]

def meta(wall, dur, sent="J 80500000", **kw):
    m = {"started_wallclock": "2026-01-01T%s+0800" % wall, "duration_s": dur, "sent": sent}
    m.update(kw)
    return m

# B5: loader text alone, and a loud kernel's SPI table alone
mk(FX + "/b5/chip-only.log", [(b"\x00chipName: UNKNOWN\n\rramSize: 32M\n\r \n", 0.5)])
mk(FX + "/b5/spi-table.log", [(b"[    6.800000] |No chipID  Sft chipSize blkSize secSize "
                               b"pageSize sdCk opCk      chipName    |\r\n", 0.5)])

# B6: one capture holding BOTH firmwares' strings, at binary-exact times
mk(FX + "/both/both.log", [
    (b"J 80500000\n\r---Jump to address=80500000\n", 0.010),
    (b"\rdecompressing kernel:\r\n", 0.020),
    (b"done decompressing kernel.\r\n", 1.125),
    (b"start address: 0x80003600\r\n", 1.250),
    (b"RLXFW-B00\r\n", 1.375),
    (b"RLXFW-B09\r\n", 1.500),
    (b"Realtek WLAN driver - version 1.6 (2013-02-21)(SVN:)\r\n", 2.000),
    (b"\r\n\r\nProbing RTL8186 10/100 NIC-kenel stack size order[3]...\r\n", 6.500),
    (b"Realtek FastPath:v1.03\r\n", 7.250),
    (b"RLXFW-B10\r\n", 10.250),
    (b"rlxfw: init running, X\r\n", 10.375),
    (b"/bin/sh: can't access tty; job control turned off\r\n# \r\n", 10.500),
    (b"\rinit started: BusyBox v1.13.4 (2018-01-10 14:56:45 CST)\r\n", 11.000),
    (b"boa: starting server pid=350, port 80\r\n", 30.000)],
    meta("09:00:00", 31.0))

# B9: cold/warm by inheritance.  fit1: the unplaced cold catch (30 s long, no
# .meta.json) cannot fit between R-rz and K-boot; fit2: it can; fit3: a kernel
# boot stands between K2 and the last loader boot.
for d, kwall in (("fit1", "10:01:05"), ("fit2", "10:02:00")):
    mk(FX + "/%s/A-cold.log" % d, loader(warm=False), meta("10:00:00", 5.0, sent=None))
    mk(FX + "/%s/R-rz.log" % d, loader(warm=True), meta("10:01:00", 3.0, sent="J BFC00000"))
    mk(FX + "/%s/U-cold.log" % d, loader(warm=False, tail=30.0))
    mk(FX + "/%s/K-boot.log" % d, rlxfw(), meta(kwall, 12.0))
mk(FX + "/fit3/A-cold.log", loader(warm=False), meta("10:00:00", 5.0, sent=None))
mk(FX + "/fit3/K1-boot.log", rlxfw(), meta("10:00:10", 12.0))
mk(FX + "/fit3/K2-boot.log", rlxfw(), meta("10:00:40", 12.0))

# B10: the host-probe join.  t0_mono 5000, window 0 .. 40 s, sent_s 0.005.
new = meta("11:00:00", 40.0, clock="CLOCK_MONOTONIC", t0_mono=5000.0,
           t0_real=1.0e9, sent_s=0.005, end_mono=5040.0, end_real=1.0e9 + 40)
mk(FX + "/probe/cap.log", rlxfw(), new)
old = dict(new)
del old["t0_mono"]
mk(FX + "/probe/old.log", rlxfw(), old)
rt = dict(new, clock="CLOCK_REALTIME")
mk(FX + "/probe/rt.log", rlxfw(), rt)
with open(FX + "/probe/hp.events", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# hostprobe events -- synthetic\n"
             "4999.000000 start t_real=1.0\n"
             "5000.002000 icmp-reply seq=0 ttl=64 rtt_ms=0.5 ping_real=1.0\n"
             "5003.000000 neigh state=FAILED lladdr=-\n"
             "5004.000000 icmp-silent seq=1\n"
             "5009.000000 tcp port=80 result=refused errno=111 start_mono=5008.9 dur_ms=1\n"
             "5012.500000 neigh state=REACHABLE lladdr=aa:bb:cc:dd:ee:ff\n"
             "5012.750000 icmp-reply seq=5 ttl=64 rtt_ms=0.4 ping_real=1.0\n"
             "5015.250000 tcp port=80 result=ok errno=0 start_mono=5015.2 dur_ms=1\n"
             "5016.000000 udp port=9 peer=192.168.1.1:9 len=4 kernel_real=-\n"
             "5020.000000 icmp-reply seq=12 ttl=64 rtt_ms=0.4 ping_real=1.0\n"
             "5041.000000 icmp-reply seq=9 ttl=64 rtt_ms=0.4 ping_real=1.0\n"
             "5042.000000 stop t_real=2.0 reason=done\n")
with open(FX + "/probe/hp.meta.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"tool": "hostprobe", "clock": "CLOCK_MONOTONIC", "start_mono": 4999.0,
               "end_mono": 5042.0, "target": "192.168.1.1"}, fh)
with open(FX + "/probe/bad.events", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("5012.750000 icmp-reply seq=5\n5013.000000 tcp port80\n")
with open(FX + "/probe/bad.meta.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"tool": "hostprobe", "clock": "CLOCK_MONOTONIC"}, fh)

# B11: two loader resets, prompt at 2.5 s: R1 records no sent_s (timed from
# its echo at 0.010 -> 2.490), R2 records sent_s 0.004 (-> 2.496).
mk(FX + "/reset/R1-rz.log", loader(), meta("13:00:00", 3.0, sent="J BFC00000"))
mk(FX + "/reset/R2-rz.log", loader(), meta("13:00:10", 3.0, sent="J BFC00000",
                                           clock="CLOCK_MONOTONIC", sent_s=0.004))

# B12: three seatings of one image.  `scale1`: every kernel time scaled with
# the directory's loader; `scale0`: the loader scaled, the kernel not.  The
# factors are asymmetric on purpose: their median (1.00) is not their mean
# (1.02), so the denominator's definition is visible in the printed ratio.
for root, scale_kernel in (("scale1", True), ("scale0", False)):
    for i, f in enumerate((0.96, 1.00, 1.10)):
        d = "%s/%s/d%d" % (FX, root, i)
        mk(d + "/L-rz.log", loader(f=f), meta("12:00:0%d" % i, 3.0, sent="J BFC00000"))
        mk(d + "/K-boot.log", rlxfw(f=f if scale_kernel else 1.0), meta("12:01:00", 12.0))
PYEOF

echo
echo "=== B5: the late-open detector names loader text only (P2-1's defect) ==="
# REFUTED IF: a committed LOUD kernel boot is named as a boot this tool could
# not place (the defect: bare `chipName` matched the SPI driver's table), or a
# capture holding only the loader's `\0chipName: ` + `ramSize:` stops being
# named -- the fix must narrow the pattern, not stop detecting.  Positive
# controls: SQ-A (and B3b's Y0-A) still named; the synthetic chip-only
# capture named.  Negative controls: X20-boot, and a synthetic line holding
# only the kernel's table header.
# ⚠️ Two layers, and each case sees one.  A capture with rtkload's line is
# counted as a kernel boot BEFORE any loader-text test, so X20-boot guards that
# order; 量 2026-09-23, mutation M1 (bare `chipName` restored) left it green.
# Only the synthetic table-header line sees the pattern itself -- M1 turned it,
# and only it, red.
ck "a committed loud kernel boot (X20-boot) is NOT named" 0 \
   "$(printf '%s\n' "$base" | grep -c '2026-09-22b/X20-boot.log -- ')"
ck "SQ-A, a true late open, is still named"               1 \
   "$(printf '%s\n' "$base" | grep -c '2026-09-06/SQ-A.log -- boot text')"
b5="$("$PY" "$BT" "$FX/b5" 2>&1)"
ck "a capture of only \\0chipName: + ramSize: is named"   1 \
   "$(printf '%s\n' "$b5" | grep -c 'chip-only.log -- boot text but no')"
ck "the kernel's SPI table header alone is NOT named"      0 \
   "$(printf '%s\n' "$b5" | grep -c 'spi-table.log -- ')"
# The 19 are ACCOUNTED FOR, not dropped: the summary partitions what produced no
# row into kernel boots / named / no boot text, and the parts must add up.
# REFUTED IF the partition does not close, or kernel boots fall under 141 (the
# J-path boots on 2026-09-23: 138 rlxfw + G6, G7, H2a2 + C1-DV = 142).
nc="$(printf '%s\n' "$base" | sed -n 's/^NOT CLASSIFIED: //p')"
nc_all="$(printf '%s\n' "$nc" | sed -n 's/^\([0-9][0-9]*\) capture.*/\1/p')"
nc_k="$(printf '%s\n' "$nc" | sed -n 's/.*; \([0-9][0-9]*\) are kernel boots.*/\1/p')"
nc_n="$(printf '%s\n' "$nc" | sed -n 's/.*, \([0-9][0-9]*\) hold boot text this tool.*/\1/p')"
nc_z="$(printf '%s\n' "$nc" | sed -n 's/.*, \([0-9][0-9]*\) hold no boot text$/\1/p')"
named="$(printf '%s\n' "$base" | grep -c -- '\.log -- ')"
echo "  observed  no row: ${nc_all:-?} = kernel ${nc_k:-?} + named ${nc_n:-?} + none ${nc_z:-?}; named lines $named"
ck "the no-row population closes, and kernel boots >= 141" yes \
   "$([ -n "$nc_all" ] && [ -n "$nc_k" ] && [ -n "$nc_n" ] && [ -n "$nc_z" ] \
      && [ $((nc_k + nc_n + nc_z)) -eq "$nc_all" ] && [ "$nc_n" -eq "$named" ] \
      && [ "$nc_k" -ge 141 ] && echo yes || echo no)"
# 2026-08-23/A-catch is a console-dump.py transcript: no .timing, no meta.  The
# line must say what the capture shows, not guess a cause it cannot show.
ck "a capture with no .timing is named for what it shows" 1 \
   "$(printf '%s\n' "$base" | grep -c '2026-08-23/A-catch.log -- .*no .timing beside it')"

echo
echo "=== B6: D1 -- the same code for both columns; the table is the difference ==="
# REFUTED IF a segment the tool prints for a committed capture differs from the
# same segment derived HERE without the tool's code: offsets from `grep -abo`,
# times by FW-35's rule applied by awk (the LAST .timing row whose offset is
# <= the byte), the difference printed %.6f.  One vendor capture (G6) and one
# rlxfw capture (X20-boot), five segments each.
off () {   # off FILE STRING -> the byte offset of the first STRING in FILE
    grep -abo -F -- "$2" "$1" | head -1 | cut -d: -f1
}
tat () {   # tat TIMING BYTE -> the time of the LAST row with offset <= BYTE
    awk -v b="$2" '!/^#/ && NF == 2 && $1 + 0 <= b + 0 { t = $2 } END { print t }' "$1"
}
seg_by_hand () {   # seg_by_hand LOG FROM_BYTE TO_BYTE -> t(to) - t(from), %.6f
    awk -v a="$(tat "${1%.log}.timing" "$2")" -v b="$(tat "${1%.log}.timing" "$3")" \
        'BEGIN { printf "%.6f", b - a }'
}
seg_by_tool () {   # seg_by_tool KERNEL_OUTPUT SEGMENT -> the value printed on its `seg` line
    printf '%s\n' "$1" | awk -v s="$2" '$1 == "seg" && $2 == s { print $NF }'
}
agree_all () {     # agree_all KERNEL_OUTPUT LOG "seg from_string to_string" ... -> k/n + misses
    local out="$1" log="$2" n=0 k=0 miss="" sid a b ha hb want got
    shift 2
    for spec in "$@"; do
        IFS='|' read -r sid a b <<<"$spec"
        n=$((n + 1))
        ha="$(off "$log" "$a")"; hb="$(off "$log" "$b")"
        [ "$b" = "job control turned off" ] && hb=$((hb + 24))
        want="$(seg_by_hand "$log" "$ha" "$hb")"
        got="$(seg_by_tool "$out" "$sid")"
        if [ -n "$want" ] && [ "$want" = "$got" ]; then k=$((k + 1))
        else miss="$miss $sid(tool=$got,hand=$want)"; fi
    done
    echo "$k/$n$miss"
}
G6="$ROOT/bench/2026-08-24c/G6.log"
X20="$ROOT/bench/2026-09-22b/X20-boot.log"
KJ="$ROOT/bench/2026-08-31c/K-J.log"
kg6="$("$PY" "$BT" --kernel "$G6" 2>&1)"
kx20="$("$PY" "$BT" --kernel "$X20" 2>&1)"
kkj="$("$PY" "$BT" --kernel "$KJ" 2>&1)"
ck "vendor G6: 5 segments equal an independent derivation" "5/5" "$(agree_all "$kg6" "$G6" \
   "rtkload.decompress|decompressing kernel:|done decompressing kernel." \
   "kernel.wlan|Realtek WLAN driver|Probing RTL8186 10/100 NIC" \
   "kernel.total|start address: 0x|init started: BusyBox" \
   "user.ready|init started: BusyBox|boa: starting server" \
   "boot.jump_to_ready|---Jump to address=|boa: starting server")"
ck "rlxfw X20-boot: 5 segments equal an independent derivation" "5/5" "$(agree_all "$kx20" "$X20" \
   "rtkload.decompress|decompressing kernel:|done decompressing kernel." \
   "kernel.early|start address: 0x|Realtek WLAN driver" \
   "kernel.nic|Probing RTL8186 10/100 NIC|Realtek FastPath:v1.03" \
   "kernel.late|Realtek FastPath:v1.03|rlxfw: init running" \
   "boot.jump_to_ready|---Jump to address=|job control turned off")"
# K-J holds a payload's `---Jump to address=` at byte ~12 and the loader's own
# autoboot 7.5 s later.  THE SEARCH RULE must put `jump` on the autoboot.
# REFUTED IF `jump` sits anywhere but the first byte of `Jump to image start=`.
ck "K-J: jump sits on the loader's autoboot (the search rule)" \
   "$(off "$KJ" "Jump to image start=")" \
   "$(printf '%s\n' "$kkj" | awk '$1 == "lm" && $2 == "jump" { print $4 }')"
# LDR-15's warm ESC window, 5.036 s, re-derived from K-J by hand and by the tool.
ck "K-J: loader.esc by hand = by the tool = LDR-15's 5.036" "5.036206 5.036206 5.036" \
   "$(seg_by_hand "$KJ" "$(off "$KJ" "---RealTek(RTL8196E)")" "$(off "$KJ" "Jump to image start=")") $(seg_by_tool "$kkj" loader.esc) $(awk -v v="$(seg_by_tool "$kkj" loader.esc)" 'BEGIN{printf "%.3f", v}')"
# The synthetic capture holds BOTH firmwares' strings; `--firmware` computes it
# once with each table through the same function.  REFUTED IF a segment whose
# two landmarks are defined identically in both tables differs between the two
# runs, or if one whose landmark differs does NOT differ by exactly the planted
# amount -- the difference must be the table, not the code.
kv="$("$PY" "$BT" --kernel --firmware vendor "$FX/both/both.log" 2>&1)"
kr="$("$PY" "$BT" --kernel --firmware rlxfw "$FX/both/both.log" 2>&1)"
same=0
for s in rtkload.decompress rtkload.total kernel.early kernel.wlan kernel.nic; do
    a="$(seg_by_tool "$kv" "$s")"; b="$(seg_by_tool "$kr" "$s")"
    [ -n "$a" ] && [ "$a" != "--" ] && [ "$a" = "$b" ] && same=$((same + 1))
done
ck "identically defined segments agree across the two tables" 5 "$same"
dlt () { awk -v a="$(seg_by_tool "$kv" "$1")" -v b="$(seg_by_tool "$kr" "$1")" 'BEGIN { printf "%.6f", a - b }'; }
ck "the others differ by exactly what was planted" \
   "0.625000 0.625000 18.875000 19.500000" \
   "$(dlt kernel.late) $(dlt kernel.total) $(dlt user.ready) $(dlt boot.jump_to_ready)"
ck "a firmware-only segment exists under its own table only" "0.125000|" \
   "$(seg_by_tool "$kr" rlxfw.setup)|$(seg_by_tool "$kv" rlxfw.setup)"
# And the `=` marks in the legend are read off the tables, not typed: REFUTED IF
# the set of landmarks marked identical is not exactly the seven shared ones.
ck "the legend marks exactly the seven shared landmarks" \
   "decomp decomp_done fastpath jump kentry nic wlan" \
   "$("$PY" "$BT" --legend | awk '/^  VENDOR/ {v=1; next} /^  RLXFW/ {v=0} v && $1 == "=" {print $2}' | sort | tr '\n' ' ' | sed 's/ $//')"
# With both firmwares' evidence and no override, detection must refuse to guess.
ck "both firmwares' evidence, no override: not timed, named" 1 \
   "$("$PY" "$BT" --kernel "$FX/both/both.log" 2>&1 | grep -c "NOT TIMED: firmware unknown -- both firmwares' evidence")"

echo
echo "=== B7: every interval names its anchors, and every cell carries n ==="
# REFUTED IF a printed interval lacks its `from -> to`, or a summary cell of
# the retro's (a)/(b) lacks `n=`.  The retro runs ONCE here; B8, B11 and B13
# read the same output and TSV.
"$PY" "$BT" --retro "$ROOT/bench" --tsv "$T/retro.tsv" >"$T/retro.txt" 2>"$T/retro.err"; rrc=$?
ck "--retro over bench exits 0"                           0 "$rrc"
ck "every seg line of --kernel names from -> to"          0 \
   "$(printf '%s\n%s\n' "$kg6" "$kx20" | awk '$1 == "seg" && $4 != "->"' | wc -l)"
sumrows="$(sed -n '/^(a) LOADER/,/^(c) NAMED/p' "$T/retro.txt" \
           | grep -E '^ +(loader|rtkload|kernel|user|boot|rlxfw)\.[a-z_]+ +[a-z0-9_]+ -> ')"
cells="$(printf '%s\n' "$sumrows" | grep -c .)"
bad="$(printf '%s\n' "$sumrows" | awk '{ n = gsub(/n=/, "n="); if (n != 3) print }' | wc -l)"
echo "  observed  summary rows with three cells: $cells"
ck "every (a)/(b) summary row has n= in all three cells" yes \
   "$([ "$cells" -ge 30 ] && [ "$bad" -eq 0 ] && echo yes || echo no)"
# A TERM-1 data row is the quantity padded to its column; the section's prose
# names the same quantities without the padding.  At least six rows, or the
# check is vacuous.
t1rows="$(sed -n '/^(d) TERM-1/,/^(e) /p' "$T/retro.txt" \
          | grep -E '(longest silence|jump -> ready|send -> prompt)  +')"
ck "every TERM-1 row carries n=" yes \
   "$(n="$(printf '%s\n' "$t1rows" | grep -c .)"; b="$(printf '%s\n' "$t1rows" | grep -vc 'n=')"
      [ "$n" -ge 6 ] && [ "$b" -eq 0 ] && echo yes || echo no)"

echo
echo "=== B8: firmware detection, and a fragment keeps only what it has ==="
# REFUTED IF a capture the tool calls vendor holds `RLXFW-B00`, or one it calls
# rlxfw lacks it or holds the vendor's `init started: BusyBox` -- checked by
# grep on each file, not by the tool -- or a kernel boot's firmware is unknown.
# Floors from 2026-09-23 (138 rlxfw, 6 vendor), never an equality.
tsvcol () { awk -F'\t' -v r="$1" -v f="$2" '$1 == r && $2 == f { print $7 }' "$T/retro.tsv"; }
vbad=0; rbad=0
for c in $(tsvcol kboot vendor); do grep -aq 'RLXFW-B00' "$c" && vbad=$((vbad + 1)); done
for c in $(tsvcol kboot rlxfw); do
    { grep -aq 'RLXFW-B00' "$c" && ! grep -aq 'init started: BusyBox' "$c"; } || rbad=$((rbad + 1))
done
nv="$(tsvcol kboot vendor | wc -l)"; nr="$(tsvcol kboot rlxfw | wc -l)"
echo "  observed  kernel boots: vendor $nv, rlxfw $nr"
ck "no vendor capture holds RLXFW-B00, no rlxfw one lacks it" "0 0" "$vbad $rbad"
corpus="$(sed -n 's/^corpus: //p' "$T/retro.txt")"
ck "vendor >= 5, rlxfw >= 138, unknown firmware 0" yes \
   "$([ "$nv" -ge 5 ] && [ "$nr" -ge 138 ] \
      && printf '%s\n' "$corpus" | grep -q 'rlxfw ? 0, firmware unknown 0' && echo yes || echo no)"
# Variant and image, on EVERY rlxfw boot, against a grep of the capture: loud
# when the WLAN banner carries a printk time prefix, the image the first
# `RLXFW-ID0=` or `none`.  REFUTED IF one boot disagrees.
vi=0; vibad=""
for c in $(tsvcol kboot rlxfw); do
    if grep -aqE '\[ *[0-9]+\.[0-9]+\] Realtek WLAN driver' "$c"; then v=loud; else v=quiet; fi
    i="$(grep -aoE 'RLXFW-ID0=[0-9A-F]{8}' "$c" | head -1 | cut -d= -f2)"
    t="$(awk -F'\t' -v c="$c" '$1 == "kboot" && $7 == c { print $3 "/" $5 }' "$T/retro.tsv")"
    [ "$t" = "$v/${i:-none}" ] || { vi=$((vi + 1)); vibad="$vibad ${c##*/bench/}"; }
done
ck "variant and image agree with a grep, on every rlxfw boot" "0" "$vi$vibad"
ck "the six named vendor boots are all vendor" 6 \
   "$(tsvcol kboot vendor | grep -cE '/(2026-08-24c/G6|2026-08-24d/G7|2026-08-25b/H2a2|2026-08-31c/K-J|2026-09-21c/X8-WAIT|2026-09-08b/C1-DV)\.log$')"
# C1-DV opens on `Jump to image start=` and ends in the WLAN driver: exactly
# three segments exist, and no loader segment.  REFUTED IF any other appears.
ck "C1-DV yields exactly the three segments it has" \
   "kernel.early rtkload.decompress rtkload.total" \
   "$("$PY" "$BT" --kernel "$ROOT/bench/2026-09-08b/C1-DV.log" | awk '$1 == "seg" && $NF != "--" { print $2 }' | sort | tr '\n' ' ' | sed 's/ $//')"

echo
echo "=== B9: cold/warm for a kernel boot ==="
# REFUTED IF K-J (its own C-8 line: warm), X8-WAIT (its own: cold) or C1-DV
# (loader text, no C-8 line: ?) read otherwise.
ck "K-J warm, X8-WAIT cold, C1-DV ? -- from their own bytes" "warm cold ?" \
   "$(for c in 2026-08-31c/K-J 2026-09-21c/X8-WAIT 2026-09-08b/C1-DV; do
         awk -F'\t' -v c="$ROOT/bench/$c.log" '$1 == "kboot" && $7 == c { printf "%s ", $4 }' "$T/retro.tsv"
      done | sed 's/ $//')"
# A boot capture with no started_wallclock blocks inheritance only when it
# could have run in between.  Positive: fit1's 30 s catch cannot fit in the 3 s
# gap, so K-boot inherits warm from R-rz.  Negative: fit2 leaves 58 s, so `?`.
# And a kernel boot in between means an uncaptured reset: fit3's K2 is `?`.
cls () { "$PY" "$BT" --kernel "$1" | sed -n 's/^  class \([^ ]*\) .*/\1/p'; }
ck "the unplaced catch cannot fit: warm, inherited from R-rz" "warm" "$(cls "$FX/fit1/K-boot.log")"
ck "the unplaced catch could fit: ?"                          "?"    "$(cls "$FX/fit2/K-boot.log")"
ck "a kernel boot in between: the first cold, the second ?"   "cold ?" \
   "$(cls "$FX/fit3/K1-boot.log") $(cls "$FX/fit3/K2-boot.log")"

echo
echo "=== B10: the host-probe join ==="
# Planted: jump at s = 0.010; the first icmp-reply at t_mono 5012.75 with
# t0_mono 5000 -> net.up 12.740000; the first tcp:80 ok at 5015.25 -> net.http
# 15.240000.  A decoy reply at s = 0.002 precedes sent_s (0.005), a second
# reply at s = 20 is not the first, and three events fall outside the window.
# REFUTED IF either value differs, a decoy is used, or the counts differ.
pj="$("$PY" "$BT" --probe "$FX/probe/hp" "$FX/probe/cap.log" 2>&1)"; prc=$?
ck "the join exits 0"                                     0 "$prc"
ck "net.up and net.http land where they were planted" "12.740000 15.240000" \
   "$(printf '%s\n' "$pj" | awk '$1 == "net" && $2 == "net.up" { a = $NF } $1 == "net" && $2 == "net.http" { b = $NF } END { print a, b }')"
ck "the first neigh that is up, by state"                 "12.500000" \
   "$(printf '%s\n' "$pj" | awk '$1 == "host" && $2 == "net.neigh_first" { print $4 }')"
ck "events before sent_s and outside the window are counted and ignored" 1 \
   "$(printf '%s\n' "$pj" | grep -c '1 before sent_s, 8 considered, 3 outside the capture.s window')"
# Every capture committed before P2-1 lacks t0_mono: REFUTED IF such a capture
# is joined at all (an origin guessed from started_wallclock), or refused
# without saying why.
"$PY" "$BT" --probe "$FX/probe/hp" "$FX/probe/old.log" >/dev/null 2>"$T/perr"; orc=$?
ck "no t0_mono: refused, exit 2, naming t0_mono"          "2 1" "$orc $(grep -c 't0_mono' "$T/perr")"
"$PY" "$BT" --probe "$FX/probe/hp" "$FX/probe/rt.log" >/dev/null 2>"$T/perr"; orc=$?
ck "a capture on another clock: refused, exit 2"          "2 1" "$orc $(grep -c 'CLOCK_MONOTONIC' "$T/perr")"
"$PY" "$BT" --probe "$FX/probe/bad" "$FX/probe/cap.log" >/dev/null 2>"$T/perr"; orc=$?
ck "a malformed events line: refused with file:line"      "2 1" "$orc $(grep -c 'bad.events:2' "$T/perr")"

echo
echo "=== B11: TERM-1 -- the longest silence ==="
# Planted: 3.25 s exactly between the WLAN banner and the NIC probe, larger
# than every other gap.  REFUTED IF the tool reports any other length or place.
ck "a planted 3.25 s gap is reported exactly, before nic" 1 \
   "$("$PY" "$BT" --kernel "$FX/fit1/K-boot.log" | grep -c 'longest silence 3.250000 s from `jump` to `ready`, ending at byte [0-9]* before `nic`')"
# On the corpus the report NAMES the capture holding the max; recompute that
# capture's longest gap by hand between `---Jump to address=` and the prompt.
# REFUTED IF the named capture's own gap is not the reported max.
row="$(grep -E '^  rlxfw quiet +longest silence' "$T/retro.txt")"
mx="$(printf '%s\n' "$row" | awk '{ print $(NF-1) }')"; cap="$(printf '%s\n' "$row" | awk '{ print $NF }')"
hand=""
if [ -f "$cap" ]; then
    # the boot's first landmark: anchor C when the loader's boot is in the
    # capture (12 bytes past `Booting...`), else the jump
    b0="$(off "$cap" "Booting...")"
    if [ -n "$b0" ]; then b0=$((b0 + 12)); else b0="$(off "$cap" "---Jump to address=")"; fi
    b1=$(( $(off "$cap" "job control turned off") + 24 ))
    hand="$(awk -v b0="$b0" -v b1="$b1" '!/^#/ && NF == 2 {
               o = $1 + 0; t = $2 + 0
               if (o <= b0) { i0 = n } if (o <= b1) { i1 = n }
               tt[n++] = t }
             END { m = 0; for (k = i0 + 1; k <= i1; k++) if (tt[k] - tt[k-1] > m) m = tt[k] - tt[k-1]
                   printf "%.4f", m }' "${cap%.log}.timing")"
fi
echo "  observed  rlxfw quiet max silence ${mx:-?} s in ${cap:-?}"
ck "the named capture's own longest gap is the reported max" "$mx" "$hand"
# The same for the loader resets' send -> prompt: the send (`sent_s` when the
# capture records it, else the echo of `J BFC00000`) to the first `<RealTek>`
# after `Booting...`, by hand.
row="$(grep -E '^  J BFC00000 +send -> prompt' "$T/retro.txt")"
mx="$(printf '%s\n' "$row" | awk '{ print $(NF-1) }')"; cap="$(printf '%s\n' "$row" | awk '{ print $NF }')"
hand=""
if [ -f "$cap" ]; then
    e="$(off "$cap" "J BFC00000")"
    p="$(grep -abo -F -- '<RealTek>' "$cap" | cut -d: -f1 | awk -v b="$(off "$cap" "Booting...")" '$1 + 0 > b + 0 { print; exit }')"
    ts="$(sed -n 's/.*"sent_s": *\([0-9][0-9.]*\).*/\1/p' "${cap%.log}.meta.json" 2>/dev/null)"
    hand="$(awk -v a="${ts:-$(tat "${cap%.log}.timing" "$e")}" -v b="$(tat "${cap%.log}.timing" "$p")" 'BEGIN { printf "%.4f", b - a }')"
fi
ck "the reset whose send -> prompt is the max, by hand" "$mx" "$hand"
# No committed capture records sent_s yet, so its branch is controlled here.
# REFUTED IF R2 is not timed from its sent_s (2.4960, the max), or the count
# of each send anchor is not one and one.
rr="$("$PY" "$BT" --retro "$FX/reset" 2>&1)"
ck "a reset is timed from sent_s when recorded, else its echo" "2.4960 R2-rz.log|1 1" \
   "$(printf '%s\n' "$rr" | awk '/^  J BFC00000 +send -> prompt/ { n = split($NF, a, "/"); printf "%s %s", $(NF-1), a[n] }')|$(printf '%s\n' "$rr" | sed -n 's/.*the send is `sent_s` on \([0-9]*\) and the first byte of the echo on \([0-9]*\);.*/\1 \2/p')"

echo
echo "=== B12: the per-seating scale section ==="
# Positive control: kernel times scaled exactly with each directory's loader ->
# slope 1.000, r 1.000.  Negative: loader scaled, kernel not -> slope 0.000
# and the H-prop condition REFUTED for it.  If the fit cannot produce both, its
# verdicts on the corpus mean nothing.
fitline () { "$PY" "$BT" --retro "$1" | awk '/^  fit over every/ { on = 1; next } /^  fit without/ { on = 0 } on && $1 == "kernel.wlan"'; }
# A fit row: segment, from, ->, to, typical, pairs, slope, lo, .., hi, r,
# H-prop, H-add.
ck "segments that scale with the loader: slope 1, r 1" "1.000 1.000 stands" \
   "$(fitline "$FX/scale1" | awk '{ print $7, $11, $12 }')"
# The ratio's denominator is the image's MEDIAN of per-directory medians (the
# coordinator's definition): 1.10 / 1.00, not 1.10 / 1.02.
ck "a ratio is to the median of per-directory medians" "x0.960 x1.000 x1.100" \
   "$("$PY" "$BT" --retro "$FX/scale1" | awk '/^  image rlxfw\/quiet\/AAAAAAAA/ { on = 1 } on && $1 == "loader.booting" { print $6, $9, $12; exit }')"
ck "segments that do not: slope 0, H-prop refuted" "0.000 refuted" \
   "$(fitline "$FX/scale0" | awk '{ print $7, $12 }')"
# On the corpus: REFUTED IF no image occurs in two directories (nothing is
# fitted) or a fit rests on fewer than 20 pairs.
np="$(awk '/^  fit over every/ { on = 1; next } /^  fit without/ { on = 0 } on && $1 == "kernel.wlan" { print $6 }' "$T/retro.txt")"
echo "  observed  kernel.wlan fitted over ${np:-?} (image, directory) pairs"
ck "the corpus fit has at least 20 pairs" yes "$([ "${np:-0}" -ge 20 ] && echo yes || echo no)"

echo
echo "=== B13: the retro describes itself, and the TSV carries the rows ==="
# REFUTED IF the report stops saying it is a prediction, the loader-table
# identity breaks (the landmark engine and `analyse` disagree on one byte), or
# the TSV lacks its per-capture or summary records.
ck "it says it is a prediction, not a result" 1 "$(grep -c '^A PREDICTION, NOT A RESULT' "$T/retro.txt")"
idl="$(grep '^  identity:' "$T/retro.txt")"
i1="$(printf '%s\n' "$idl" | sed -n 's/.* on \([0-9]*\) of \([0-9]*\) loader boots.*/\1 \2/p')"
i2="$(printf '%s\n' "$idl" | sed -n 's/.* equals `banner` on \([0-9]*\) of \([0-9]*\)$/\1 \2/p')"
echo "  observed  identity ${i1:-?} / ${i2:-?}"
ck "the two code paths agree on every loader boot (>= 249)" yes \
   "$(set -- $i1 $i2; [ "$#" -eq 4 ] && [ "$1" = "$2" ] && [ "$3" = "$4" ] && [ "$2" -ge 249 ] && echo yes || echo no)"
ck "the TSV holds kboot, seg, cell, term1 and scalefit records" 5 \
   "$(for r in kboot seg cell term1 scalefit; do awk -F'\t' -v r="$r" '$1 == r { print r; exit }' "$T/retro.tsv"; done | wc -l)"
ck "every TSV cell record carries n"                       0 \
   "$(awk -F'\t' '$1 == "cell" && $12 == ""' "$T/retro.tsv" | wc -l)"

echo
echo "=== B14: refusals are reasons with exit 2, never a traceback ==="
"$PY" "$BT" --retro "$T/empty" >/dev/null 2>"$T/err"; rc=$?
ck "--retro over nothing: exit 2 and REFUSING"            "2 1 0" "$rc $(grep -c REFUSING "$T/err") $(grep -c Traceback "$T/err")"
"$PY" "$BT" --kernel "$FX/b5" >/dev/null 2>"$T/err"; rc=$?
ck "--kernel over no kernel boot: exit 2 and REFUSING"    "2 1 0" "$rc $(grep -c REFUSING "$T/err") $(grep -c Traceback "$T/err")"
"$PY" "$BT" --retro --kernel "$FX/b5" >/dev/null 2>"$T/err"; rc=$?
ck "two modes at once: exit 2 and REFUSING"               "2 1" "$rc $(grep -c REFUSING "$T/err")"
# A reader that is gone before the tool writes (`true` reads nothing and exits
# while the retro is still computing) must not produce a traceback.  REFUTED IF
# stderr holds one.  量: before the entry point caught it, B12's awk printed
# `BrokenPipeError` into this suite's output.
"$PY" "$BT" --retro "$FX/scale1" 2>"$T/err" | true
ck "a reader that closes early gets no traceback"          0 "$(grep -c 'Traceback\|BrokenPipe' "$T/err")"

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
