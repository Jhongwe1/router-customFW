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
ck "twelve cold, nine warm"  1 "$(printf '%s\n' "$base" | grep -c 'C-8): 12 cold, 9 warm, 0 unknown')"

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
ck "entry population is six warm resets" 1 \
   "$(printf '%s\n' "$base" | grep -c 'entry, warm  *n=6')"

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
