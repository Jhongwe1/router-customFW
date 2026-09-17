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
ck "thirty-nine cold, one hundred and seventy warm"  1 "$(printf '%s\n' "$base" | grep -c 'C-8): 39 cold, 170 warm, 0 unknown')"

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
ck "entry population is seventy-eight warm resets" 1 \
   "$(printf '%s\n' "$base" | grep -c 'entry, warm  *n=78')"

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

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
