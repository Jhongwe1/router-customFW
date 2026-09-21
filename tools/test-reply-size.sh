#!/usr/bin/env bash
# Controls for tools/reply-size.py.
#
# The tool carries its own controls and refuses to report on a file until every
# one of them passes.  (This comment used to say "twelve" -- a count of
# something that grows, asserted in prose where nothing can check it, which is
# the same defect this project spent 2026-09-19 removing from five test cases.)
# This file exists for the things the tool cannot check about itself.
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
#   S6  the same thing one layer up: a capture whose COMMAND the model cannot
#       parse must be reported, not raise. 量 2026-09-19: three bare-`DW`
#       captures took a 516-capture sweep down with `IndexError`, while
#       `--self-test` stayed green -- all ten of its controls went through the
#       helper and the crash was in the caller.
#   S7  a SILENT whose predecessor recorded `prompt_seen: false` is EXPLAINED
#       and the sweep is green.
#   S8  THE POSITIVE CONTROL ON S7, and the reason S7 is worth anything: the
#       same two files with that one field flipped to `true` must go RED.
#       Without it the new branch could excuse every silence and nothing here
#       would notice.
#   S9  a SILENT that is FIRST in its directory has nothing to hide behind and
#       stays a miss. This is the dead-port case.
#   S10 the real corpus holds exactly ONE SILENT and it is EXPLAINED -- and
#       every OTHER state agrees, capture for capture, with a build that has
#       the SILENT branch cut out of it. That differential is how "nothing else
#       moved" is asserted WITHOUT hardcoding a corpus count that the next
#       seating would turn red for an unrelated reason (`test-boot-timeline`'s
#       B2 went red on GitHub twice that way).
#   S11 the order is `started_wallclock`, not mtime and not filename. One
#       fixture, arranged so that a filename-sorting build and an
#       mtime-sorting build each reach the WRONG verdict on it.
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
echo "=== S6: one unparseable command must not take the sweep down ==="
# S5 proves the tool survives a file it cannot READ.  This proves it survives a
# capture whose COMMAND it cannot parse, which is a different layer and was not
# covered until 2026-09-19.
#
# 量 2026-09-19: it did not survive.  Three `DW <addr>` captures with no length
# made `check` over bench/ die with `IndexError: list index out of range` before
# it classified any of the other 513 -- and `--self-test` was green throughout,
# because all ten of its controls went through `_dw_body` and the crash was in
# `predict`.  A green self-test beside a crashing sweep is the shape this
# project keeps finding: the control and the caller were not the same code.
#
# The good file beside the bad one is what makes this a control rather than a
# smoke test -- the sweep has to get PAST the bad row and still classify the
# good one.
cp "$ROOT/bench/2026-08-25b/A0.meta.json" "$T/g2.meta.json"
sed -e 's/"sent": "[^"]*"/"sent": "DW"/' \
    -e 's/"sent_hex": "[^"]*"/"sent_hex": ""/' \
    "$ROOT/bench/2026-08-25b/A0.meta.json" > "$T/nolen.meta.json"
ck "the fixture really carries a bare DW"  1 \
   "$(grep -c '"sent": "DW"' "$T/nolen.meta.json")"
out="$("$PY" "$HERE/reply-size.py" check "$T/g2.meta.json" "$T/nolen.meta.json" 2>&1)"; rc=$?
ck "it does not traceback"                 0 \
   "$(printf '%s\n' "$out" | grep -c 'Traceback')"
# TWO lines carry the word -- the row and the tally -- so a bare
# `grep -c UNPARSEABLE` counts 2, and a case asserting 1 is a case that is
# wrong rather than a tool that is.  量 2026-09-19: the first draft of this
# case did exactly that and went red on a tool that was behaving correctly.
ck "the tally counts exactly one"          1 \
   "$(printf '%s\n' "$out" | grep -cE '^ +UNPARSEABLE +1$')"
ck "and the row names the command"         1 \
   "$(printf '%s\n' "$out" | grep -c 'UNPARSEABLE *DW \[')"
# `1 modelled` and not 2: a capture whose command could not be parsed was not
# modelled by anything, exactly as an UNREADABLE one was not.
ck "the good one is still modelled"        1 \
   "$(printf '%s\n' "$out" | grep -c 'RESULT: 1 modelled, 1 unexplained')"
ck "and it counts as a miss, so exit 1"    1 "$rc"

# The mutation: take the guard away and the sweep must die again. Without it,
# the rows above would pass on a tool that never had a bad row to survive.
"$PY" - "$HERE/reply-size.py" "$T/mutant3.py" <<'MUT'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
head = '        try:\n            st, want, delta = classify(sent, m.get("bytes"))\n'
tail = '        tally[st] = tally.get(st, 0) + 1\n'
i = src.find(head)
j = src.find(tail, i) if i >= 0 else -1
out = src
if i >= 0 and j > i:
    out = src[:i] + '        st, want, delta = classify(sent, m.get("bytes"))\n' + src[j:]
open(sys.argv[2], "w", encoding="utf-8").write(out)
print("cut" if out != src else "INCOMPLETE")
MUT
ck "the mutant differs from the original"  1 \
   "$(cmp -s "$T/mutant3.py" "$HERE/reply-size.py" && echo 0 || echo 1)"
out="$("$PY" "$T/mutant3.py" check "$T/g2.meta.json" "$T/nolen.meta.json" 2>&1)"
ck "and the mutant tracebacks"             1 \
   "$(printf '%s\n' "$out" | grep -c 'Traceback')"

echo
echo "=== S7-S11: SILENT, and the evidence that is allowed to excuse it ==="
# Fixtures, not bench/ -- S5 and S6 build theirs the same way and for the same
# reason: a case that asserts on a real capture asserts on whatever the last
# seating happened to do.
#
# `p1-rb` carries `esc_after_seconds: 15.0` on purpose. The REAL explaining
# capture is ESC-streamed, so the sweep skips it before classifying and it is
# in no row list; a lookup that only saw the sweep's own rows would find
# nothing. The fixture reproduces that.
#
# mtimes are set explicitly rather than left to the order of the writes: S11
# asserts on mtime order, and on a filesystem with coarse timestamps three
# writes in the same second would make that assertion measure nothing.
"$PY" - "$T" <<'FIX'
import json, os, sys
T = sys.argv[1]

def meta(d, name, sw, sent, nbytes, prompt_seen=None, esc_after=0.0, mtime=None):
    os.makedirs(d, exist_ok=True)
    m = {
        "tool_version": "1.4",
        "port": "/dev/ttyUSB0",
        "baud": 38400,
        "started_wallclock": sw,
        "esc_seconds": 0.0,
        "esc_after_seconds": esc_after,
        "esc": {},
        "cr": {},
        "cr_settle_s": 2.0,
        "seconds": 6.0,
        "idle": 0.0,
        "until": None,
        "until_offset": None,
        "sent": sent,
        "stop_reason": "--seconds 6.0 elapsed",
        "bytes": nbytes,
        "duration_s": 6.0,
    }
    if prompt_seen is not None:
        m["cr"] = {"esc_after": {"written": True,
                                 "prompt_seen": prompt_seen,
                                 "waited_s": 2.008716,
                                 "log_offset": nbytes,
                                 "settle_budget_s": 2.0}}
    p = os.path.join(d, name + ".meta.json")
    open(p, "w", encoding="utf-8").write(json.dumps(m, indent=2))
    if mtime is not None:
        os.utime(p, (mtime, mtime))

# S7 and S8 are the same two files and differ in ONE field.
for sub, seen in (("s7", False), ("s8", True)):
    meta(T + "/" + sub, "p1-rb", "2026-09-21T02:08:11+0800",
         "busybox reboot -f", 7883, prompt_seen=seen, esc_after=15.0)
    meta(T + "/" + sub, "p2-prompt", "2026-09-21T02:08:48+0800",
         "DW 8040D4A0 1", 0)

# S9: nothing before it on disk.
meta(T + "/s9", "p2-prompt", "2026-09-21T02:08:48+0800", "DW 8040D4A0 1", 0)

# S11: three captures arranged so the three candidate orderings disagree.
#   by wallclock: aaa-ok(08:11) zzz-rb(08:40) mmm-silent(08:48)
#                 -> predecessor zzz-rb, prompt_seen false -> EXPLAINED, green
#   by filename:  aaa-ok  mmm-silent  zzz-rb
#                 -> predecessor aaa-ok, prompt_seen true  -> a miss, red
#   by mtime:     mmm-silent(1000) zzz-rb(2000) aaa-ok(3000)
#                 -> the silent one is FIRST, no predecessor -> a miss, red
# Only the wallclock reading is green, so this one fixture kills both of the
# orderings the requirement ruled out.
meta(T + "/s11", "mmm-silent", "2026-09-21T02:08:48+0800", "DW 8040D4A0 1", 0,
     mtime=1000000000)
meta(T + "/s11", "zzz-rb", "2026-09-21T02:08:40+0800",
     "busybox reboot -f", 7883, prompt_seen=False, esc_after=15.0,
     mtime=1000002000)
meta(T + "/s11", "aaa-ok", "2026-09-21T02:08:11+0800",
     "busybox reboot -f", 7883, prompt_seen=True, esc_after=15.0,
     mtime=1000003000)
print("built")
FIX

echo
echo "=== S7: a SILENT explained by the capture before it ==="
# The fixture pair must differ in exactly one field, or S8 is not a CONTROL on
# S7 -- it is a second experiment.
ck "S7 the pair differs on prompt_seen"   2 \
   "$(diff "$T/s7/p1-rb.meta.json" "$T/s8/p1-rb.meta.json" | grep -c 'prompt_seen')"
ck "S7 and on nothing else"               0 \
   "$(diff "$T/s7/p1-rb.meta.json" "$T/s8/p1-rb.meta.json" | grep -cEv 'prompt_seen|^[0-9,]+c[0-9,]+$|^---$')"
ck "S7 the silent halves are identical"   0 \
   "$(cmp -s "$T/s7/p2-prompt.meta.json" "$T/s8/p2-prompt.meta.json" && echo 0 || echo 1)"
out="$("$PY" "$HERE/reply-size.py" check "$T/s7" 2>&1)"; rc=$?
ck "S7 exit code"                         0 "$rc"
ck "S7 reported SILENT-EXPLAINED"         1 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT-EXPLAINED 1$')"
ck "S7 and the row names the predecessor" 1 \
   "$(printf '%s\n' "$out" | grep -c 'p2-prompt.meta.json   <- p1-rb.meta.json recorded cr.esc_after.prompt_seen=false')"
ck "S7 no bare SILENT in the tally"       0 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT +[0-9]+$')"
ck "S7 and it still counts as modelled"   1 \
   "$(printf '%s\n' "$out" | grep -c 'RESULT: 1 modelled, 0 unexplained')"

echo
echo "=== S8: THE POSITIVE CONTROL -- the predecessor DID see the prompt ==="
# Without this case the SILENT branch can never fail, and a rule that cannot
# fail is not a rule.  Same two files as S7; `prompt_seen` is `true`.
out="$("$PY" "$HERE/reply-size.py" check "$T/s8" 2>&1)"; rc=$?
ck "S8 exit code"                         1 "$rc"
ck "S8 reported SILENT, unexplained"      1 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT +1$')"
ck "S8 and NOT explained"                 0 \
   "$(printf '%s\n' "$out" | grep -c 'SILENT-EXPLAINED')"
ck "S8 and it counts as a miss"           1 \
   "$(printf '%s\n' "$out" | grep -c 'RESULT: 1 modelled, 1 unexplained')"

echo
echo "=== S9: a SILENT with nothing before it stays a miss ==="
# The dead-port case.  A sweep that excused this could not tell a bench session
# from a session in which nothing was plugged in.
out="$("$PY" "$HERE/reply-size.py" check "$T/s9" 2>&1)"; rc=$?
ck "S9 exit code"                         1 "$rc"
ck "S9 reported SILENT, unexplained"      1 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT +1$')"
ck "S9 and it counts as a miss"           1 \
   "$(printf '%s\n' "$out" | grep -c 'RESULT: 1 modelled, 1 unexplained')"
# The file itself is byte-identical to S7's, so S9 is about the ABSENCE of the
# neighbour and not about the capture.
ck "S9 the capture is S7's, byte for byte" 0 \
   "$(cmp -s "$T/s9/p2-prompt.meta.json" "$T/s7/p2-prompt.meta.json" && echo 0 || echo 1)"

echo
echo "=== S10: the real corpus -- one SILENT, explained, nothing else moved ==="
# THE POPULATION IS FROZEN FIRST, and both builds below are handed the same
# list.  量 2026-09-21, while this case was being written: a seating was live
# and captures were landing in `bench/` every ~25 s, so two sweeps taken three
# seconds apart can legitimately disagree -- and the differential would have
# reported that as "a state moved" with nothing wrong.  A sweep certifies the
# tree it saw; naming that tree is what turns a silent hole into a stated
# scope.  (`desk-sweep.py` copies the tree for the same reason; a list is
# enough here because nothing under test writes to `bench/`.)
find "$ROOT/bench" -name '*.meta.json' | sort > "$T/metalist.txt"
ck "S10 the frozen list is not tiny"    yes \
   "$([ "$(wc -l < "$T/metalist.txt")" -ge 500 ] && echo yes || echo no)"
# The list is expanded unquoted below, so this is the assumption that makes
# that legal, asserted instead of assumed.
ck "S10 and no capture path needs quoting" 0 \
   "$(grep -c '[[:space:]]' "$T/metalist.txt")"
out="$("$PY" "$HERE/reply-size.py" check $(cat "$T/metalist.txt") 2>&1)"; rc=$?
ck "S10 check exit code"                  0 "$rc"
ck "S10 exactly one SILENT-EXPLAINED"     1 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT-EXPLAINED 1$')"
ck "S10 no unexplained SILENT at all"     0 \
   "$(printf '%s\n' "$out" | grep -cE '^ +SILENT +[0-9]+$')"
ck "S10 the row names F0-PROMPT and F0-RB" 1 \
   "$(printf '%s\n' "$out" | grep -c 'SILENT-EXPLAINED .*F0-PROMPT.meta.json   <- F0-RB.meta.json')"

# (e), as a DIFFERENTIAL rather than as a hardcoded count.  Cut the SILENT
# branch out of a copy -- with its controls and its fixture row, or the copy
# refuses to report -- and every state but SHORT/SILENT/SILENT-EXPLAINED must
# come out identical over all of bench/.
cuts="$("$PY" - "$HERE/reply-size.py" "$T/nosilent.py" <<'MUT'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
n = 0

def cut(s, start, end):
    global n
    i = s.find(start)
    j = s.find(end, i) if i >= 0 else -1
    if i < 0 or j < 0:
        return s
    n += 1
    return s[:i] + s[j + len(end):]

src = cut(src, "    if nbytes == 0:\n",
          '        return "SILENT", want, nbytes - want\n')
src = cut(src, '    ("DW 8040D4A0 1",          0, "SILENT",',
          '"bench/2026-09-21b/F0-PROMPT.log"),\n')
src = cut(src, "    # 11. SILENT, and the controls",
          '           for c, b, _, _ in FIXTURES))\n')
open(sys.argv[2], "w", encoding="utf-8").write(src)
print("cut%d" % n)
MUT
)"
# Named rather than inferred from `cmp`: any ONE of the three cuts would make
# the file differ, and a copy that kept its C11 controls would REFUSE to report
# instead of disagreeing -- which is a silence, not a result.
ck "S10 all three cuts applied"        cut3 "$cuts"
ck "S10 the no-SILENT build differs"      1 \
   "$(cmp -s "$T/nosilent.py" "$HERE/reply-size.py" && echo 0 || echo 1)"
# It must still REPORT, not refuse -- a copy whose own controls fail exits 2
# and prints no tally, and comparing two empty tallies would pass forever.
old="$("$PY" "$T/nosilent.py" check $(cat "$T/metalist.txt") 2>&1)"; rc_old=$?
ck "S10 the no-SILENT build calls it SHORT" 1 \
   "$(printf '%s\n' "$old" | grep -c 'SHORT .*F0-PROMPT')"
ck "S10 and goes red on it, as CI did"    1 "$rc_old"
STATES='^ {4}(OK|ECHO-ONLY|UNKNOWN-COMMAND|UNMODELLED|NO-COMMAND|LONG|UNREADABLE|UNPARSEABLE|ESC-STREAMED) '
printf '%s\n' "$out" | grep -E "$STATES" > "$T/states-new.txt"
printf '%s\n' "$old" | grep -E "$STATES" > "$T/states-old.txt"
# The population control on the comparison below: two empty files are equal.
ck "S10 there are states to compare"    yes \
   "$([ "$(wc -l < "$T/states-new.txt")" -ge 5 ] && echo yes || echo no)"
ck "S10 every other state is unchanged"   0 \
   "$(cmp -s "$T/states-new.txt" "$T/states-old.txt" && echo 0 || echo 1)"
# And the modelled population did not move either: a SILENT-EXPLAINED is still
# a capture whose length this model predicted.
ck "S10 the modelled population is unchanged" \
   "$(printf '%s\n' "$old" | sed -n 's/^RESULT: \([0-9]*\) modelled.*/\1/p')" \
   "$(printf '%s\n' "$out" | sed -n 's/^RESULT: \([0-9]*\) modelled.*/\1/p')"

echo
echo "=== S11: the order is started_wallclock, not mtime and not filename ==="
ck "S11 filename order picks aaa-ok"   "aaa-ok.meta.json" \
   "$(ls "$T/s11" | sort | grep -B1 '^mmm-silent' | head -1)"
ck "S11 mtime order puts the silent one first" "mmm-silent.meta.json" \
   "$(ls -tr "$T/s11" | head -1)"
out="$("$PY" "$HERE/reply-size.py" check "$T/s11" 2>&1)"; rc=$?
ck "S11 exit code"                        0 "$rc"
ck "S11 and the predecessor named is zzz-rb" 1 \
   "$(printf '%s\n' "$out" | grep -c 'mmm-silent.meta.json   <- zzz-rb.meta.json recorded cr.esc_after.prompt_seen=false')"

echo
echo "=== the mutation on the new branch: excuse every SILENT ==="
# S7, S10 and S11 all stay green under it.  It is S8 and S9 that have to fire,
# which is exactly what makes those two the controls and not the decoration.
"$PY" - "$HERE/reply-size.py" "$T/mutant4.py" <<'MUT'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
old = "            ex = _explained_by(p)\n"
new = "            ex = _explained_by(p) or ('(nothing)', 'nothing')\n"
out = src.replace(old, new)
open(sys.argv[2], "w", encoding="utf-8").write(out)
print("cut" if out != src else "INCOMPLETE")
MUT
ck "the always-excuse mutant differs"     1 \
   "$(cmp -s "$T/mutant4.py" "$HERE/reply-size.py" && echo 0 || echo 1)"
"$PY" "$T/mutant4.py" check "$T/s8" > "$T/m4s8.out" 2>&1; rc=$?
ck "S8's fixture goes GREEN under it"     0 "$rc"
"$PY" "$T/mutant4.py" check "$T/s9" > "$T/m4s9.out" 2>&1; rc=$?
ck "and so does S9's"                     0 "$rc"

echo
if [ "$fail" -ne 0 ]; then
    printf 'RESULT: %d passed, \033[31m%d failed\033[0m\n' "$pass" "$fail"; exit 1
fi
printf 'RESULT: \033[32m%d passed, 0 failed\033[0m\n' "$pass"
