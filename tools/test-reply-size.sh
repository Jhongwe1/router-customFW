#!/usr/bin/env bash
# Controls for tools/reply-size.py.
#
# The tool carries twelve controls of its own and refuses to report on a file
# until every one of them passes. This file exists for the two things the tool
# cannot check about itself.
#
#   S1  the controls are wired in: a build with a broken model must REFUSE,
#       not report. `--self-test` proving itself green says nothing about
#       whether `check` consults it.
#   S2  the sweep looked at a real population. `0 unexplained` over 0 captures
#       is the sweep-with-no-positive-control this project keeps finding.
#   S3  the mutation: change one fitted constant and the sweep must go from
#       0 unexplained to many. Without this, S2 passes on a model that has been
#       accidentally fitted to nothing.
#   S4  the answer it was built to get right. `DW 81000400 16` is fourteen
#       characters and the reply is 213 bytes. A person counted fifteen on
#       2026-08-25 and predicted 214; that is the whole reason this is a tool.
#   S5  the UNREADABLE branch actually reaches the printer. 量 2026-08-25 at
#       the bench: it did not. `check` over a directory of `.log` files died
#       with `TypeError: %d format: a real number is required, not str` on the
#       first file, because the branch that exists to report an unusable
#       capture stored its error message in the column the printer formats
#       with %+d. The branch existed, was tallied, and counted toward
#       `misses` -- and could never print. Same defect class as `hazlint`
#       1.0's K4 and `test-gitignore.sh`'s exit-1: a control that cannot fire.
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
PY="${PYTHON:-python3}"

pass=0; fail=0
ck () {
    if [ "$2" = "$3" ]; then printf '  ok     %-52s %s\n' "$1" "$3"; pass=$((pass+1))
    else printf '  FAIL   %-52s expected %s, got %s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi
}

echo "=== S1: the tool's own controls, and they gate everything else ==="
out="$("$PY" "$HERE/reply-size.py" --self-test 2>&1)"; rc=$?
ck "self-test exit code"                  0 "$rc"
ck "controls that failed"                 0 "$(printf '%s\n' "$out" | sed -n 's/^RESULT: [0-9]* passed, \([0-9]*\) failed$/\1/p')"
n="$(printf '%s\n' "$out" | grep -c '^  ok  ')"
ck "and there were at least ten of them" yes "$([ "${n:-0}" -ge 10 ] && echo yes || echo no)"

echo
echo "=== S2: the sweep over every capture on disk ==="
out="$("$PY" "$HERE/reply-size.py" check "$ROOT/bench" 2>&1)"; rc=$?
ck "check exit code"                      0 "$rc"
mod="$(printf '%s\n' "$out" | sed -n 's/^RESULT: \([0-9]*\) modelled.*/\1/p')"
une="$(printf '%s\n' "$out" | sed -n 's/^RESULT: [0-9]* modelled, \([0-9]*\) unexplained$/\1/p')"
ck "unexplained captures"                 0 "${une:-MISSING}"
ck "and the population is not tiny"     yes "$([ "${mod:-0}" -ge 100 ] && echo yes || echo no)"
# The two captures that do NOT match the formula are named states, not misses.
# If either of them ever reads as SHORT, the classifier has lost a distinction
# that a bench operator needs.
ck "CONT is ECHO-ONLY, not SHORT"         1 "$(printf '%s\n' "$out" | grep -c 'ECHO-ONLY .*8040DCE8')"
ck "the reopen control is UNKNOWN-COMMAND" 1 "$(printf '%s\n' "$out" | grep -c 'UNKNOWN-COMMAND .*8040DBC0')"

echo
echo "=== S3: the mutation -- one fitted constant moved, and the sweep must fail ==="
# 47 is one DW output line. Every one of the 91 DW captures behind the model
# would have to be wrong for 46 to be right, so a sweep that still reports
# 0 unexplained is a sweep that is not reading the captures.
sed 's/^DW_LINE = 47 /DW_LINE = 46 /' "$HERE/reply-size.py" > "$T/mutant.py"
ck "the mutant differs from the original" 1 \
   "$(cmp -s "$T/mutant.py" "$HERE/reply-size.py" && echo 0 || echo 1)"
out="$("$PY" "$T/mutant.py" check "$ROOT/bench" 2>&1)"; rc=$?
ck "the mutant refuses or reports misses" yes "$([ "$rc" -ne 0 ] && echo yes || echo no)"

echo
echo "=== S4: the arithmetic error this tool exists to remove ==="
ck "DW 81000400 16 -> 213"              213 \
   "$("$PY" "$HERE/reply-size.py" predict 'DW 81000400 16' | awk '{print $4}')"
# And the one the runsheet already measured by a different route: H1c read
# probe1's block back with DW 80A00000 137 and the capture was 1,671 bytes.
ck "DW 80A00000 137 -> 1671 (H1c, measured)" 1671 \
   "$("$PY" "$HERE/reply-size.py" predict 'DW 80A00000 137' | awk '{print $4}')"

echo
echo "=== S5: the UNREADABLE branch must PRINT, not crash ==="
# One good capture and one file that is not JSON. The good one is what makes
# this a control rather than a smoke test: the tool has to get past the bad
# file and still classify the good one.
cp "$ROOT/bench/2026-08-25b/A0.meta.json" "$T/good.meta.json"
printf 'not json at all\n' > "$T/bad.meta.json"
out="$("$PY" "$HERE/reply-size.py" check "$T/good.meta.json" "$T/bad.meta.json" 2>&1)"; rc=$?
ck "it does not traceback"                0 \
   "$(printf '%s\n' "$out" | grep -c 'Traceback')"
ck "the bad file is reported UNREADABLE"  1 \
   "$(printf '%s\n' "$out" | grep -c 'UNREADABLE .*bad.meta.json')"
ck "and it counts as unexplained"         1 \
   "$(printf '%s\n' "$out" | grep -c 'RESULT: 1 modelled, 1 unexplained')"
ck "exit code says so"                    1 "$rc"
# `1 modelled` and not `2`: an unreadable file was not modelled by anything.
# The tool counted it until 2026-08-25, which inflated the population figure
# this project quotes without ever changing a verdict.
ck "UNREADABLE is not counted as modelled" 0 \
   "$(printf '%s\n' "$out" | grep -c '2 modelled')"
# The good file alone must be clean, or the rows above prove nothing about
# which file the tool objected to.
out="$("$PY" "$HERE/reply-size.py" check "$T/good.meta.json" 2>&1)"; rc=$?
ck "the good file alone is clean"         0 "$rc"

# The mutation: put BOTH halves back the way they were until 2026-08-25 -- the
# message in the column the printer formats with %+d, and the printer that
# formats it that way. Either half alone is harmless; the crash needs both,
# which is why the mutation restores both.
"$PY" - "$HERE/reply-size.py" "$T/mutant2.py" <<'MUT'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
a = src.replace('rows.append((p, ("%s: %s" % (type(e).__name__, e))[:34],\n'
                '                         None, "UNREADABLE", None, None))',
                'rows.append((p, "", None, "UNREADABLE", None, str(e)))')
b = a.replace('d = " (%+d)" % delta if isinstance(delta, int) and delta else ""',
              'd = "" if delta in (None, 0) else " (%+d)" % delta')
open(sys.argv[2], "w", encoding="utf-8").write(b)
print("both" if (a != src and b != a) else "INCOMPLETE")
MUT
ck "both halves of the mutation applied"  yes \
   "$(cmp -s "$T/mutant2.py" "$HERE/reply-size.py" && echo no || echo yes)"
out="$("$PY" "$T/mutant2.py" check "$T/good.meta.json" "$T/bad.meta.json" 2>&1)"
ck "and the mutant tracebacks"            1 \
   "$(printf '%s\n' "$out" | grep -c 'Traceback')"
ck "on exactly the TypeError this repaired" 1 \
   "$(printf '%s\n' "$out" | grep -c 'TypeError: %d format')"

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
