#!/usr/bin/env bash
# Self-test for tools/console-capture.py.
#
# The tool's whole claim is that a number comes out of the wire rather than out
# of a stopwatch, and that the bytes it stores are the bytes the device sent.
# Both halves are checkable without a device: a pty stands in for the CP2102, a
# writer on the master side plays a known script with known gaps, and the tool
# reads the slave believing it is a serial port.
#
# Forty-five cases, FORTY-SIX results (P3 checks two things). Thirty of them
# are controls whose job is to FAIL -- the tool must refuse, or a mutant of it
# must break a case above -- because a test suite that cannot fail proves
# nothing: the same argument tools/audit-bench-log.py
# makes about its own patterns and the reason PROGRESS.md rejected hazlint's
# original "stage 2 must report zero" control.
#
# 🔴 That count has been wrong before and this line is re-measured rather than
# incremented: it read "twenty-four cases, twenty-five results" while the suite
# printed 29, for at least the three sessions between P8's arrival and
# 2026-08-30. `tools/ci-expected.tsv` is what CHECKS the number; this comment is
# a convenience and has no gate behind it.
#
# 🔴 AND FORTY GREEN RESULTS WERE NOT ENOUGH. 量 2026-08-30 with
# tools/test-console-capture-mutants.py: 25 mutants of the terminator guard,
# TEN alive against the forty. N25-N30 close the four classes they fell into;
# the mutant runner is what says so and what will say so again.
#
#   P1  byte-exactness      log identical to the played script, CRs and all
#   P2  interval            a 1.50 s gap is reported as 1.50 s, not as 0
#   N1  exactness can fail  one flipped byte in the comparison must be caught
#   N2  interval can fail   a 0.00 s gap must NOT report 1.50 s
#   N3  missing pattern     an absent FROM must exit non-zero, not report 0.000
#   N4  whitespace refusal  --send " DW ..." must be refused, not sent
#   N5  the --idle trap     an --idle shorter than the measured silence must
#                           truncate loudly, not report a plausible interval
#   P3  --esc-after        ESC is streamed AFTER the send, and the reply that
#                           arrives during it still reaches the log
#   N6  --esc-after can be off  with 0, no ESC follows the command, so P3 is
#                           measuring the flag and not the tool's habits
#   N7  the 128-byte cliff   a 128-character --send must be refused, and the
#                           input is the exact line RUNSHEET C7 nearly sent
#   P4  the cliff is AT 128  a 127-character --send must be ACCEPTED, or the
#                           guard is at the wrong threshold and C7b cannot run
#   N8  non-ASCII refusal    refused by _check_send, not by a traceback out of
#                           .encode("ascii") with the port already open
#   P5  the ESC terminator   --esc-after leaves the port on a CR, not on an ESC
#   N9  --no-cr can turn it off, so P5 measures the behaviour and not a habit
#   P6  ordering             --esc's CR lands BETWEEN the last ESC and the
#                           command line, which is the only place it helps
#   P7  no ESC, no extra CR  a --send-only capture writes the command and
#                           nothing else -- every C cell is one of those
#   N10 the mutation         with the CR write removed from a copy of the tool,
#                           P5's check must report NONE. Without this, P5 cannot
#                           tell the patched tool from the shipped one
#
#   P8  no command after   --esc with no --send still ends on a CR. That is the
#                           A-catch shape and the only --esc shape on record
#   N11 gating the terminator on --send makes P8 fail, so P8 tests that path
#   P9  the settle          a prompt played after the CR is seen, and the wait
#                           ends early -- the only cases here that read .meta.json
#   N12 and with nothing played back it runs to expiry and records false
#   N13 a PROMPT that cannot match makes P9 fail
#   N14 no settle budget    --seconds can zero the settle; that records
#                           prompt_seen null, never false
#   P10 Ctrl-C mid-ESC      an interrupted ESC loop still writes its terminator
#   P11 --esc-period 0.002  the ESC grid actually gets ten times finer, and the
#                           period the run ACHIEVED is in its own metadata
#   N15 the default grid    20 ms is still 20 ms, so P11 measures the flag
#   N16 impossible period   asking for 0.1 us reports what was achieved, not
#                           what was asked -- the field is a measurement
#   N17 hard-coded grid     a tool that ignores --esc-period fails P11
#
#   N18 no terminator       neither --seconds nor --idle must be REFUSED: both
#                           default to 0.0 and the read loop breaks on neither,
#                           so the command never returns (rc=124, 2026-08-29)
#   N19 and before the port  the refusal must not carry `cannot open`
#   P12 --seconds alone     satisfies the guard and reaches the port
#   P13 --idle alone        satisfies it too -- a guard on --seconds only would
#                           refuse RUNSHEET D1, whose quantity IS a silence
#   N20 zero in longhand    --seconds 0 --idle 0 is the default, not a terminator
#   P14 the metadata        records `seconds` and `idle`, which until today it
#                           did not -- so a census of what was passed was an
#                           inference off stop_reason and one-directional
#   N21 the port side       a 127-char --send with no terminator gets the
#                           TERMINATOR refusal, so the port was never opened.
#                           🔴 It does NOT pin the _check_send side, although
#                           this line said "the sandwich ... after _check_send,
#                           before the port" until 2026-08-30: 127 is a length
#                           _check_send ACCEPTS. N29 is that edge
#   N22 and they move       a second run with different values moves both fields
#   P15 report is exempt    the guard is capture()'s; a guard in main() breaks it
#   N23 guard mutation      with the condition dead, N18's command reaches the port
#   N24 field mutation      with the two fields hardcoded, P14 and N22 go red
#
#   N25 the --esc waiver    --esc 1 with no terminator must STILL be refused.
#                           A-catch's own shape, and the mutant that reproduced
#                           the never-returning capture on a pty
#   N26 the other waivers   six more non-default flags in one command, so no
#                           flag the guard has no business reading waives it
#   N27 the contract        a refusal exits non-zero AND writes nothing to
#                           stdout. Neither was asserted anywhere before
#   N28 the message         it names BOTH flags that satisfy it, so a mutant
#                           naming a flag that does not exist goes red
#   N29 the upper side      a 128-char --send with no terminator gets the
#                           LENGTH refusal -- _check_send first, by assertion
#                           rather than by N4/N7/N8 happening to have none
#   N30 the lower side      with the .log/.timing/.meta.json already present,
#                           the TERMINATOR refusal still comes first
#
# P5/N9/P6/P7/N10 were added 2026-08-24 with the CR itself; P8/N11/P9/N12/N13/P10
# came out of the adversarial review of that change the same day, and every one
# of them killed a mutant the first eighteen cases had let through -- the review
# ran three of those mutants and got "18 passed, 0 failed" from each.
#
# These cases do NOT retire `flush-d1` and `flush-d3`. They prove what the tool
# WRITES; only the board can say what the loader did with it, and RUNSHEET keeps
# both cells with the expectation inverted (a bare prompt, not `Unknown command !`)
# as exactly that control. The half of rule 2 about a USB re-enumeration is also
# not covered and still needs a throwaway capture -- no capture can see an event
# that happened while it was not running.
#
# P3/N6 were added 2026-08-24, the day RUNSHEET section D was stopped before it
# ran because --esc streams before --send and D1 needs the opposite. The option
# was written at the desk with its control, rather than improvised at the bench.
#
# N5 is here because it happened. The first run of this file used --idle 0.8
# against a played 1.50 s gap, the capture ended inside the silence at 29 bytes,
# and the report said the second endpoint never arrived. That is the correct
# behaviour and it is also the exact shape of RUNSHEET D1 -- where the quantity
# being measured IS a silence -- so it is a case rather than a fixed bug.
#
# Run:  bash tools/test-console-capture.sh
set -u

PY=/usr/bin/python3
HERE="$(cd "$(dirname "$0")" && pwd)"
# The tool under test.  `CC_TOOL` exists so tools/test-console-capture-mutants.py
# can point this suite at a MUTANT of console-capture.py and require it to go
# red -- the claim "these forty-odd cases pin the terminator guard" is otherwise
# a sentence nobody has shown can fail.  Unset, it is the shipped tool, so an
# ordinary run and a CI run are unaffected.  It is deliberately NOT a positional
# argument: an operator at the bench types this file's name and nothing else.
TOOL="${CC_TOOL:-$HERE/console-capture.py}"
if [ ! -f "$TOOL" ]; then
  echo "console-capture self-test: no such tool: $TOOL" >&2
  exit 2
fi
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ok()   { printf '  ok    %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

"$PY" -c 'import serial' 2>/dev/null || {
  echo "console-capture self-test: $PY cannot import serial (apt: python3-serial)" >&2
  exit 2
}

# --------------------------------------------------------------------------
# The stand-in device. Plays a script of (delay, bytes) pairs into a pty and
# tells us the slave's name, then the tool is run against that slave.
# --------------------------------------------------------------------------
run_case() {           # run_case <outprefix> <gap_seconds> <idle_seconds>
  local out="$1" gap="$2" idle="$3"
  "$PY" - "$TOOL" "$out" "$gap" "$idle" <<'PYEOF'
import os, pty, subprocess, sys, time

tool, out, gap, idle = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
master, slave = pty.openpty()
name = os.ttyname(slave)

proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", name, "--out", out,
     "--idle", idle, "--seconds", "25"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Give the tool time to open the port and set the slave to raw. Anything
# written before that is at the mercy of the default line discipline, which
# would translate \n to \r\n -- and this test exists to detect exactly that
# class of edit.
time.sleep(0.6)

# The two strings are the real ones from this unit: the J handler's echo at
# 0x8040B35C, and the stage-1 banner. \r\n because the loader's format strings
# end \r\n -- measured 2026-08-23, 20 such bytes in B.log and 47 in E.log.
os.write(master, b"---Jump to address=BFC00000\r\n")
time.sleep(gap)
os.write(master, b"---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)\r\n")
os.write(master, b"<RealTek>")
proc.wait(timeout=25)
os.close(master); os.close(slave)
PYEOF
}

echo "console-capture self-test"
echo

# --- P1 / P2 -------------------------------------------------------------
run_case "$WORK/p" 1.50 3.0
EXPECT="$WORK/expect.bin"
printf -- '---Jump to address=BFC00000\r\n---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)\r\n<RealTek>' > "$EXPECT"

if cmp -s "$EXPECT" "$WORK/p.log"; then
  ok "P1 byte-exact: $(wc -c < "$WORK/p.log") bytes, CRs preserved"
else
  bad "P1 byte-exact -- the log is not what was played"
  cmp -l "$EXPECT" "$WORK/p.log" | head -3
fi

RPT="$("$PY" "$TOOL" report "$WORK/p" --from 'Jump to address=BFC00000' --to 'RealTek\(RTL8196E\)' 2>&1)"
IVAL="$(printf '%s\n' "$RPT" | sed -n 's/.*INTERVAL *\([0-9.]*\) s.*/\1/p')"
if [ -n "$IVAL" ] && "$PY" -c "import sys; sys.exit(0 if 1.20 <= $IVAL <= 1.90 else 1)"; then
  ok "P2 interval: reported ${IVAL}s for a played 1.50s gap"
else
  bad "P2 interval: reported '${IVAL}' for a played 1.50s gap"
  printf '%s\n' "$RPT" | sed 's/^/        /'
fi

# --- N1 the exactness check must be able to fail -------------------------
cp "$WORK/p.log" "$WORK/tampered.log"
"$PY" - "$WORK/tampered.log" <<'PYEOF'
import sys
p = sys.argv[1]
b = bytearray(open(p, 'rb').read())
b[5] ^= 0x01                       # one bit, one byte
open(p, 'wb').write(bytes(b))
PYEOF
if cmp -s "$EXPECT" "$WORK/tampered.log"; then
  bad "N1 the comparison passed a file with one flipped byte -- P1 proves nothing"
else
  ok "N1 one flipped byte is caught, so P1's 'identical' means something"
fi

# --- N2 the interval must be able to be wrong ----------------------------
run_case "$WORK/z" 0.00 3.0
RPT0="$("$PY" "$TOOL" report "$WORK/z" --from 'Jump to address=BFC00000' --to 'RealTek\(RTL8196E\)' 2>&1)"
IVAL0="$(printf '%s\n' "$RPT0" | sed -n 's/.*INTERVAL *\([0-9.]*\) s.*/\1/p')"
if [ -n "$IVAL0" ] && "$PY" -c "import sys; sys.exit(0 if $IVAL0 < 0.50 else 1)"; then
  ok "N2 a 0.00s gap reports ${IVAL0}s, not 1.50s -- the timing file is being read"
else
  bad "N2 a 0.00s gap reported '${IVAL0}' -- the number may not come from the wire"
fi

# --- N3 an absent pattern must not report 0.000 --------------------------
if "$PY" "$TOOL" report "$WORK/p" --from 'THIS STRING IS NOT IN THE CAPTURE' \
     --to 'RealTek' >/dev/null 2>&1; then
  bad "N3 an absent FROM pattern exited 0 -- a missing endpoint would read as a measurement"
else
  ok "N3 an absent FROM pattern exits non-zero rather than reporting an interval"
fi

# --- N4 the whitespace refusal -------------------------------------------
OUTW="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/w" --send ' DW 8040DBC0 1' 2>&1)"
# --port /dev/null cannot be opened as a serial port. The refusal must come out
# anyway, because the check runs before the port is touched -- that ordering is
# what N4 tests, and it failed here on 2026-08-24 with a pyserial traceback.
if printf '%s\n' "$OUTW" | grep -q 'leading or trailing whitespace'; then
  ok "N4 --send with a leading space is refused (the C5 trap, 2026-08-23)"
else
  bad "N4 --send accepted a leading space"
  printf '%s\n' "$OUTW" | sed 's/^/        /'
fi

# --- N5 the --idle trap ---------------------------------------------------
run_case "$WORK/t" 1.50 0.8
TBYTES=$(wc -c < "$WORK/t.log")
if "$PY" "$TOOL" report "$WORK/t" --from 'Jump to address=BFC00000'      --to 'RealTek\(RTL8196E\)' >/dev/null 2>&1; then
  bad "N5 --idle 0.8 truncated the capture at ${TBYTES} bytes but report still gave an interval"
else
  ok  "N5 --idle 0.8 truncates a 1.50s silence at ${TBYTES} bytes and the report refuses"
fi

# --- P3 / N6  --esc-after, and the pair is the point ----------------------
# D1 sends `J BFC00000`, the board resets, and D2/D2b must read the prompt of
# the WARM boot. So one capture has to send a command and THEN stream ESC across
# the reboot that command caused. --esc streams before --send and cannot do it.
# This is the option that can -- and N6 is what stops P3 from passing on a tool
# that streams ESC unconditionally.
#
# The judgement is on what the TOOL WROTE, which the log never shows: the log is
# what the device said. So the pty master is recorded and analysed separately.
esc_case() {           # esc_case <outprefix> <esc_after_seconds> <masterdump>
  "$PY" - "$TOOL" "$1" "$2" "$3" <<'INNERPY'
import os, pty, select, subprocess, sys, time

tool, out, esc_after, dump = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
master, slave = pty.openpty()
name = os.ttyname(slave)
proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", name, "--out", out,
     "--send", "J BFC00000", "--esc-after", esc_after, "--seconds", "6"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.6)
seen = bytearray()
deadline = time.monotonic() + 3.0
while time.monotonic() < deadline:
    r, _, _ = select.select([master], [], [], 0.05)
    if r:
        seen += os.read(master, 4096)
# The "warm boot" arrives while ESC is being streamed. If --esc-after did not
# keep the capture alive and reading, this never reaches the log.
os.write(master, b"---RealTek(RTL8196E)at 2014.04.22-16:22+0800 v1.3 [16bit](400MHz)\r\n<RealTek>")
proc.wait(timeout=15)
open(dump, "wb").write(bytes(seen))
os.close(master); os.close(slave)
INNERPY
}

esc_after_count() {    # how many ESC bytes the tool wrote AFTER the command line
  "$PY" - "$1" <<'INNERPY'
import sys
b = open(sys.argv[1], 'rb').read()
i = b.find(b'J BFC00000\r')
print(-1 if i < 0 else b[i + 11:].count(0x1b))
INNERPY
}

esc_case "$WORK/e" 2.0 "$WORK/e.sent"
NESC="$(esc_after_count "$WORK/e.sent")"
if [ "$NESC" = "-1" ]; then
  bad "P3 the command was never sent -- nothing below this means anything"
elif [ "$NESC" -gt 0 ]; then
  ok "P3 --esc-after wrote $NESC ESC bytes AFTER the command, which --esc cannot do"
else
  bad "P3 --esc-after wrote no ESC after the command"
fi
if grep -q 'RealTek(RTL8196E)' "$WORK/e.log" 2>/dev/null; then
  ok "P3 the warm-boot banner played during ESC streaming reached the log"
else
  bad "P3 the banner played during ESC streaming did not reach the log"
fi

esc_case "$WORK/n" 0.0 "$WORK/n.sent"
NESC0="$(esc_after_count "$WORK/n.sent")"
if [ "$NESC0" = "0" ]; then
  ok "N6 with --esc-after 0 no ESC follows the command, so P3 measures the flag"
elif [ "$NESC0" = "-1" ]; then
  bad "N6 the command was never sent"
else
  bad "N6 $NESC0 ESC bytes were sent with --esc-after 0 -- P3 proves nothing"
fi

# --- N7 / P4  the 128-byte cliff, and the pair is the point ---------------
# The loader's console line buffer is 128 bytes -- measured on the device
# 2026-08-24, exactly 128 ESC bytes came back `Unknown command !` seven times
# -- and readline writes its NUL only on the CR path, so a line that FILLS the
# buffer is unterminated and the tokeniser at 0x80407248 runs off the end of it
# into the saved registers. RUNSHEET C7 was written to send 173 characters with
# `EW` as the command, which readline would have cut at exactly 128.
#
# N7's input IS that cut line: `EW 81000400` plus thirteen values.
# P4's input is C7b as it will actually be typed: eleven values padded to 127
# with leading zeros. P4 is what stops N7 from passing on a tool that refuses
# anything long -- a guard written at 100 would pass N7 and fail P4.
L128="EW 81000400"
for i in 1 2 3 4 5 6 7 8 9 A B C D; do L128="$L128 C7A0000$i"; done
L127="EW 81000440"
for v in 00C7B00001 00C7B00002 00C7B00003 00C7B00004 00C7B00005 00C7B00006 \
         0C7B00007 0C7B00008 0C7B00009 0C7B0000A 0C7B0000B; do L127="$L127 $v"; done

if [ ${#L128} -ne 128 ] || [ ${#L127} -ne 127 ]; then
  bad "N7/P4 built their own inputs at ${#L128} and ${#L127} characters, not 128 and 127 -- neither case can test the cliff"
else
  OUT128="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/l" --send "$L128" 2>&1)"
  if printf '%s\n' "$OUT128" | grep -q 'console line buffer is'; then
    ok "N7 a 128-character --send is refused -- the line RUNSHEET C7 nearly sent"
  else
    bad "N7 a 128-character --send was NOT refused"
    printf '%s\n' "$OUT128" | sed 's/^/        /'
  fi

  # --seconds 1 is here from 2026-08-30 and it is not decoration. P4's subject
  # is the 127-character boundary and its assertion is that the run REACHES the
  # port; capture() now refuses a run with no terminator before the port is
  # opened, so without this flag P4 would go red for a reason that has nothing
  # to do with the cliff. 量 that day: of the four terminator-less invocations
  # in this file, this is the ONLY one that changes -- N4, N7 and N8 are refused
  # inside _check_send, which runs first. 🔴 N21 does NOT pin that ordering,
  # although this comment said so until 2026-08-30: N21 sends 127 characters, a
  # length _check_send ACCEPTS, so it passes either way. N29 sends 128 and
  # requires the LENGTH refusal -- that is the case.
  OUT127="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/k" --send "$L127" --seconds 1 2>&1)"
  if printf '%s\n' "$OUT127" | grep -q 'console line buffer is'; then
    bad "P4 a 127-character --send was refused -- the guard is at the wrong threshold and C7b cannot run"
  elif printf '%s\n' "$OUT127" | grep -q 'cannot open'; then
    ok "P4 a 127-character --send passes the length check and fails on the port instead"
  else
    bad "P4 a 127-character --send neither passed the length check nor reached the port"
    printf '%s\n' "$OUT127" | sed 's/^/        /'
  fi
fi

# --- N8 the non-ASCII refusal --------------------------------------------
# capture() does .encode("ascii") AFTER the port is open, so without this check
# a non-ASCII character is a traceback from a tool that has already touched the
# device -- the same ordering defect N4 exists to prevent. The byte is built
# with printf so this file stays ASCII.
NONASCII="DW 8040DBC0 1$(printf '\303\251')"
OUTA="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/a" --send "$NONASCII" 2>&1)"
if printf '%s\n' "$OUTA" | grep -q 'is not ASCII'; then
  ok "N8 a non-ASCII --send is refused before the port is touched"
else
  bad "N8 a non-ASCII --send was not refused by _check_send"
  printf '%s\n' "$OUTA" | sed 's/^/        /'
fi

# --- P5 / N9 / P6 / P7 / N10  the CR that ends an ESC loop -----------------
# RUNSHEET seating 2 rule 2: any capture whose last byte written to the port was
# not a CR leaves `N mod 128` bytes in the loader's readline buffer, and the next
# command line is appended to them. Until 2026-08-24 that was enforced by a flush
# cell typed afterwards -- flush, flush-cont, flush-b7c, flush-d1, flush-d3. The
# tool writes the terminator itself now, and these five cases are what make that
# a property rather than a habit.
#
# The judgement is on what the tool WROTE, which the .log can never show: the
# .log is what the device said, and this CR's whole point is that no device
# needs to be there. So the pty master is recorded and read back.
wrote_case() {         # wrote_case <tool> <outprefix> <masterdump> <tool args...>
  local tool="$1" out="$2" dump="$3"; shift 3
  "$PY" - "$tool" "$out" "$dump" "$@" <<'INNERPY'
import os, pty, select, subprocess, sys, time

tool, out, dump = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4:]
master, slave = pty.openpty()
name = os.ttyname(slave)
proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", name, "--out", out] + extra,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
# Read for as long as the tool runs. Nothing is ever played back: these cases
# are about the ORDER of the bytes the tool sends, and the last one it sends has
# to actually be the last one recorded.
seen = bytearray()
while proc.poll() is None:
    r, _, _ = select.select([master], [], [], 0.05)
    if r:
        seen += os.read(master, 4096)
deadline = time.monotonic() + 0.3
while time.monotonic() < deadline:
    r, _, _ = select.select([master], [], [], 0.05)
    if not r:
        break
    seen += os.read(master, 4096)
open(dump, "wb").write(bytes(seen))
os.close(master); os.close(slave)
INNERPY
}

# Classify what followed the command line: how many ESC, and whether exactly one
# CR closed the run. Prints "<n_esc> <trailer>" where trailer is CR / NONE / MESS.
esc_tail_shape() {     # esc_tail_shape <masterdump>
  "$PY" - "$1" <<'INNERPY'
import re, sys
b = open(sys.argv[1], 'rb').read()
i = b.find(b'J BFC00000\r')
if i < 0:
    print("-1 NOSEND"); raise SystemExit
tail = b[i + 11:]
n = tail.count(0x1b)
if re.fullmatch(rb'\x1b+\r', tail):
    print(f"{n} CR")
elif re.fullmatch(rb'\x1b+', tail):
    print(f"{n} NONE")
else:
    print(f"{n} MESS")
INNERPY
}

wrote_case "$TOOL" "$WORK/cr" "$WORK/cr.sent" \
  --send 'J BFC00000' --esc-after 1.0 --cr-settle 0.4 --seconds 3
read -r NCR SHAPE <<< "$(esc_tail_shape "$WORK/cr.sent")"
if [ "$SHAPE" = "CR" ] && [ "$NCR" -gt 0 ]; then
  ok "P5 --esc-after ends with one CR after $NCR ESC -- flush-d1 is the tool's job now"
else
  bad "P5 --esc-after left the port on '$SHAPE' after $NCR ESC, not on a CR"
fi

wrote_case "$TOOL" "$WORK/nocr" "$WORK/nocr.sent" \
  --send 'J BFC00000' --esc-after 1.0 --no-cr --seconds 3
read -r NNC SHAPE0 <<< "$(esc_tail_shape "$WORK/nocr.sent")"
if [ "$SHAPE0" = "NONE" ] && [ "$NNC" -gt 0 ]; then
  ok "N9 --no-cr writes no terminator, so P5 measures the behaviour and not a habit"
else
  bad "N9 --no-cr produced '$SHAPE0' after $NNC ESC -- P5 proves nothing"
fi

# P6: --esc runs BEFORE the send, so its CR has to land between the last ESC and
# the command line. If it landed after, the residue would still be the front of
# the command -- which is the defect the whole section exists to remove.
wrote_case "$TOOL" "$WORK/pre" "$WORK/pre.sent" \
  --esc 1.0 --cr-settle 0.4 --send 'DW 8040DBC0 1' --seconds 3
if "$PY" - "$WORK/pre.sent" <<'INNERPY'
import re, sys
b = open(sys.argv[1], 'rb').read()
sys.exit(0 if re.fullmatch(rb'\x1b+\rDW 8040DBC0 1\r', b) else 1)
INNERPY
then
  ok "P6 --esc puts its CR between the last ESC and the command, not after it"
else
  bad "P6 --esc did not terminate its ESC run before sending the command"
  "$PY" -c "print(repr(open('$WORK/pre.sent','rb').read()[:80]))" | sed 's/^/        /'
fi

# P7: no ESC loop ran, so the only CR is the one --send has always written. A
# tool that writes a CR unconditionally would pass P5 and P6 and be wrong about
# every ordinary cell -- C1 through C7b, every one of them --send only.
wrote_case "$TOOL" "$WORK/plain" "$WORK/plain.sent" --send 'DW 8040DBC0 1' --seconds 2
if [ "$("$PY" -c "print(open('$WORK/plain.sent','rb').read() == b'DW 8040DBC0 1\r')")" = "True" ]; then
  ok "P7 with no ESC loop the tool writes the command and nothing else"
else
  bad "P7 a --send-only capture wrote something other than the command line"
  "$PY" -c "print(repr(open('$WORK/plain.sent','rb').read()[:80]))" | sed 's/^/        /'
fi

# N10: the mutation. P5 passing on the shipped tool says nothing unless it fails
# on a tool with the write removed -- PROGRESS.md 2026-08-24, hazlint's suite
# went 42->56 because the old one could not tell the patched tool from the
# shipped one.
"$PY" - "$TOOL" "$WORK/mutant.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
if "ser.write(CR)" not in src:
    sys.exit("mutation target 'ser.write(CR)' not found -- N10 cannot run")
open(sys.argv[2], "w", encoding="utf-8").write(
    src.replace("ser.write(CR)", "pass  # MUTANT: the terminator is not written", 1))
INNERPY
if [ -s "$WORK/mutant.py" ]; then
  wrote_case "$WORK/mutant.py" "$WORK/mut" "$WORK/mut.sent" \
    --send 'J BFC00000' --esc-after 1.0 --cr-settle 0.4 --seconds 3
  read -r NMU SHAPEM <<< "$(esc_tail_shape "$WORK/mut.sent")"
  # `!= CR` is not the assertion: NOSEND and MESS are the shapes a mutant that
  # never RAN produces, and scoring those as a killed mutation is how a broken
  # harness reports itself as a working control. The ESC guard is N9's.
  if [ "$SHAPEM" = "NONE" ] && [ "$NMU" -gt 0 ]; then
    ok "N10 removing the CR write leaves $NMU ESC and no terminator -- P5 is testing the write"
  else
    bad "N10 the mutant produced '$SHAPEM' after $NMU ESC; only NONE with ESC>0 means P5 discriminates"
  fi
else
  bad "N10 the mutant was not produced, so P5 is unguarded"
fi

# --- P8 / N11  the shape with no command after it -------------------------
# A-catch is `--esc 25` with NO --send, and it is the only --esc shape on record
# (bench/2026-08-24/A-catch.meta.json and bench/2026-08-24b/A-catch.meta.json,
# both "sent": null). It is also the capture whose 12-byte residue mangled A0's
# first attempt. Every case above passes --send, so without this one a tool that
# terminated only the ESC loops that precede a command would score 18/18 and
# fail on the first cell of the next seating.
wrote_case "$TOOL" "$WORK/bare" "$WORK/bare.sent" --esc 1.0 --cr-settle 0.4 --seconds 3
if [ "$("$PY" -c "
import re
b = open(r'$WORK/bare.sent','rb').read()
print(bool(re.fullmatch(rb'\x1b+\r', b)))")" = "True" ]; then
  ok "P8 --esc with no --send still ends on a CR -- the A-catch shape"
else
  bad "P8 --esc with no --send did not terminate its ESC run"
  "$PY" -c "print(repr(open(r'$WORK/bare.sent','rb').read()[-40:]))" | sed 's/^/        /'
fi

"$PY" - "$TOOL" "$WORK/mut2.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
target = '                terminate_esc_line("esc")'
if target not in src:
    sys.exit("mutation target for N11 not found")
open(sys.argv[2], "w", encoding="utf-8").write(src.replace(
    target,
    '                if args.send is not None:  # MUTANT\n' + target + '    ', 1))
INNERPY
if [ -s "$WORK/mut2.py" ]; then
  wrote_case "$WORK/mut2.py" "$WORK/bare2" "$WORK/bare2.sent" --esc 1.0 --cr-settle 0.4 --seconds 3
  if [ "$("$PY" -c "
import re
b = open(r'$WORK/bare2.sent','rb').read()
print(bool(re.fullmatch(rb'\x1b+\r', b)))")" = "True" ]; then
    bad "N11 a tool that terminates only ESC loops followed by a command still passed P8"
  else
    ok "N11 gating the terminator on --send makes P8 fail -- P8 is testing the no-command path"
  fi
else
  bad "N11 the mutant was not produced, so P8 is unguarded"
fi

# --- P9 / N12 / N13  the settle, in both directions ------------------------
# The CR write is guarded by N10. The WAIT that follows it was guarded by
# nothing: with the budget forced to 0, with the settle loop deleted, or with
# PROMPT changed to a literal that can never match, the suite still printed
# "18 passed, 0 failed" -- all three measured 2026-08-24. These three cases are
# the control, and they are the only ones here that read a .meta.json, which is
# where everything this change records about the instrument lives.
settle_case() {        # settle_case <tool> <outprefix> <masterdump> <play|silent> <args...>
  local tool="$1" out="$2" dump="$3" mode="$4"; shift 4
  "$PY" - "$tool" "$out" "$dump" "$mode" "$@" <<'INNERPY'
import os, pty, select, subprocess, sys, time

tool, out, dump, mode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
extra = sys.argv[5:]
master, slave = pty.openpty()
proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", os.ttyname(slave), "--out", out] + extra,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
seen = bytearray()
played = False
while proc.poll() is None:
    r, _, _ = select.select([master], [], [], 0.05)
    if r:
        seen += os.read(master, 4096)
    # ESC immediately followed by CR is the terminator's signature on the wire,
    # and it is the only moment at which a prompt played back is answering the
    # CR rather than one of the ESC stream's own 128-byte fills.
    if mode == "play" and not played and b"\x1b\r" in seen:
        os.write(master, b"\r\n<RealTek>")
        played = True
open(dump, "wb").write(bytes(seen))
os.close(master); os.close(slave)
INNERPY
}

cr_meta() {            # cr_meta <outprefix> <which> <key>
  "$PY" - "$1.meta.json" "$2" "$3" <<'INNERPY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
print(m.get("cr", {}).get(sys.argv[2], {}).get(sys.argv[3]))
INNERPY
}

settle_case "$TOOL" "$WORK/s1" "$WORK/s1.sent" play \
  --send 'J BFC00000' --esc-after 1.0 --cr-settle 2.0 --seconds 6
S1SEEN="$(cr_meta "$WORK/s1" esc_after prompt_seen)"
S1WAIT="$(cr_meta "$WORK/s1" esc_after waited_s)"
if [ "$S1SEEN" = "True" ] && "$PY" -c "import sys; sys.exit(0 if $S1WAIT < 1.0 else 1)"; then
  ok "P9 a prompt played after the CR is seen in ${S1WAIT}s and the settle ends early"
else
  bad "P9 prompt_seen=$S1SEEN waited_s=$S1WAIT -- the settle did not observe the reply"
fi

settle_case "$TOOL" "$WORK/s2" "$WORK/s2.sent" silent \
  --send 'J BFC00000' --esc-after 1.0 --cr-settle 2.0 --seconds 6
S2SEEN="$(cr_meta "$WORK/s2" esc_after prompt_seen)"
S2WAIT="$(cr_meta "$WORK/s2" esc_after waited_s)"
if [ "$S2SEEN" = "False" ] && "$PY" -c "import sys; sys.exit(0 if $S2WAIT >= 1.5 else 1)"; then
  ok "N12 with nothing played back the settle runs to expiry (${S2WAIT}s) and records false"
else
  bad "N12 prompt_seen=$S2SEEN waited_s=$S2WAIT -- P9 could be passing without a settle"
fi

"$PY" - "$TOOL" "$WORK/mut3.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
if 'PROMPT = b"<RealTek>"' not in src:
    sys.exit("mutation target for N13 not found")
open(sys.argv[2], "w", encoding="utf-8").write(
    src.replace('PROMPT = b"<RealTek>"', 'PROMPT = b"<NEVER-MATCHES>"', 1))
INNERPY
if [ -s "$WORK/mut3.py" ]; then
  settle_case "$WORK/mut3.py" "$WORK/s3" "$WORK/s3.sent" play \
    --send 'J BFC00000' --esc-after 1.0 --cr-settle 2.0 --seconds 6
  if [ "$(cr_meta "$WORK/s3" esc_after prompt_seen)" = "True" ]; then
    bad "N13 a PROMPT that cannot match still reported prompt_seen -- P9 is not reading the port"
  else
    ok "N13 a PROMPT that cannot match makes P9 fail -- P9 is testing the match"
  fi
else
  bad "N13 the mutant was not produced, so P9 is unguarded"
fi

# --- N14  the settle that never ran must not look like one that found nothing
# `--seconds` clamps the settle budget, so `--esc-after 2 --seconds 2` leaves
# zero. `prompt_seen: false` there would be indistinguishable from "waited the
# full window and the board said nothing" -- and under the rewritten flush-d1
# row that second reading is the operator's evidence that D1's terminator failed
# to go out. So no-budget records null and says so. Found by the completeness
# critic of this change's own review, 2026-08-24; unreachable from every other
# case here, which all carry >= 2 s of headroom.
settle_case "$TOOL" "$WORK/s4" "$WORK/s4.sent" silent   --send 'J BFC00000' --esc-after 2.0 --cr-settle 2.0 --seconds 2
S4SEEN="$(cr_meta "$WORK/s4" esc_after prompt_seen)"
S4W="$(cr_meta "$WORK/s4" esc_after written)"
S4B="$(cr_meta "$WORK/s4" esc_after settle_budget_s)"
if [ "$S4W" = "True" ] && [ "$S4SEEN" = "None" ] && [ "$S4B" = "0.0" ]; then
  ok "N14 a zeroed settle budget records prompt_seen null, not false, and still writes the CR"
else
  bad "N14 written=$S4W prompt_seen=$S4SEEN budget=$S4B -- 'never looked' is being recorded as 'looked and saw nothing'"
fi

# --- P10  Ctrl-C inside an ESC loop ---------------------------------------
# Measured 2026-08-24 on a pty against 1.2 before this case existed: an
# interrupt inside the ESC loop skipped the terminator entirely, left 245 ESC
# on the wire and a residue of 117 -- and 117 + len('DW B8003110 1') = 130,
# which is the 128-byte cliff and not a recoverable `Unknown command !`. The
# metadata recorded "cr": {}, which this tool defines as "the loop did not run",
# so the capture was a 1.1 capture carrying 1.2's version number.
"$PY" - "$TOOL" "$WORK/int.sent" "$WORK/int" <<'INNERPY'
import os, pty, select, signal, subprocess, sys, time

tool, dump, out = sys.argv[1], sys.argv[2], sys.argv[3]
master, slave = pty.openpty()
proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", os.ttyname(slave), "--out", out,
     "--send", "J BFC00000", "--esc-after", "20", "--cr-settle", "0.4", "--seconds", "45"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
seen = bytearray()
t0 = time.monotonic()
sent = False
while proc.poll() is None:
    r, _, _ = select.select([master], [], [], 0.05)
    if r:
        seen += os.read(master, 4096)
    if not sent and time.monotonic() - t0 > 2.0:
        proc.send_signal(signal.SIGINT)     # the operator, mid-ESC-loop
        sent = True
open(dump, "wb").write(bytes(seen))
os.close(master); os.close(slave)
INNERPY
read -r NINT SHAPEI <<< "$(esc_tail_shape "$WORK/int.sent")"
IWRITTEN="$(cr_meta "$WORK/int" esc_after written)"
if [ "$SHAPEI" = "CR" ] && [ "$IWRITTEN" = "True" ] && [ "$NINT" -gt 0 ]; then
  ok "P10 Ctrl-C inside an ESC loop still writes the terminator after $NINT ESC"
else
  bad "P10 an interrupted ESC loop left '$SHAPEI' after $NINT ESC, cr.written=$IWRITTEN -- residue for the next cell"
fi

# --- P11 / N15 / N16 / N17  the ESC heartbeat is a measured grid ------------
# CLK-08b is open because the two watchdog OVSEL points cannot separate a fixed
# residual from a proportional one: the two hypotheses differ by about 15 ms and
# the ESC-echo grid was 20 ms. SPEC.md section 17 names the fix -- a finer
# heartbeat -- and this is the half of it that can fail.
#
# The thing being guarded is NOT "the constant is now 0.002". It is that the
# period each capture achieved is written into that capture's own metadata as a
# measurement. The previous grid was requested at 20.00 ms and came out at
# 20.35 / 20.32 (SPEC.md CLK-08), so a reader who takes the requested value is
# already 1.75% wrong, and at 2 ms the same relative error is what the whole
# experiment is trying to resolve.
esc_meta() {           # esc_meta <outprefix> <which> <key>
  "$PY" - "$1.meta.json" "$2" "$3" <<'INNERPY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
print(m.get("esc", {}).get(sys.argv[2], {}).get(sys.argv[3]))
INNERPY
}

fnum() {               # fnum <expr-in-python> -> exit 0 if true
  "$PY" -c "import sys; sys.exit(0 if ($1) else 1)"
}

wrote_case "$TOOL" "$WORK/pf" "$WORK/pf.sent" \
  --send 'J BFC00000' --esc-after 1.0 --esc-period 0.002 --cr-settle 0.4 --seconds 3
read -r NFINE _ <<< "$(esc_tail_shape "$WORK/pf.sent")"
FINEACH="$(esc_meta "$WORK/pf" esc_after achieved_period_s)"
FINEREQ="$(esc_meta "$WORK/pf" esc_after requested_period_s)"

wrote_case "$TOOL" "$WORK/pc" "$WORK/pc.sent" \
  --send 'J BFC00000' --esc-after 1.0 --cr-settle 0.4 --seconds 3
read -r NCOARSE _ <<< "$(esc_tail_shape "$WORK/pc.sent")"
COARSEACH="$(esc_meta "$WORK/pc" esc_after achieved_period_s)"

if [ "$FINEREQ" = "0.002" ] && [ "$NFINE" -gt 200 ] && fnum "$FINEACH < 0.006"; then
  ok "P11 --esc-period 0.002 wrote $NFINE ESC in 1 s and records an achieved ${FINEACH}s"
else
  bad "P11 --esc-period 0.002 wrote $NFINE ESC, achieved=$FINEACH requested=$FINEREQ -- the knob is not reaching the loop"
fi

# The pair. Without it, P11 could pass on a tool that ignores the flag and just
# happens to be fast, and the 10x claim would be about the host and not the
# knob.
if [ "$NCOARSE" -gt 20 ] && [ "$NCOARSE" -lt 80 ] \
   && fnum "0.018 <= $COARSEACH <= 0.032" \
   && fnum "$NFINE > 4 * $NCOARSE"; then
  ok "N15 the default is still 20 ms ($NCOARSE ESC, achieved ${COARSEACH}s) so P11 measures the flag"
else
  bad "N15 default wrote $NCOARSE ESC achieved=$COARSEACH against fine $NFINE -- the two are not distinguishable"
fi

# THE SHARP ONE. A field that reported back the number it was given would pass
# every check above. Ask for a period no host can deliver: the achieved value
# must come out very much larger, because it is measured.
wrote_case "$TOOL" "$WORK/pi" "$WORK/pi.sent" \
  --send 'J BFC00000' --esc-after 0.2 --esc-period 0.0000001 --cr-settle 0.2 --seconds 2
IMPACH="$(esc_meta "$WORK/pi" esc_after achieved_period_s)"
IMPREQ="$(esc_meta "$WORK/pi" esc_after requested_period_s)"
if fnum "$IMPACH > 10 * $IMPREQ" && fnum "$IMPACH > 0" ; then
  ok "N16 an impossible ${IMPREQ}s request reports an achieved ${IMPACH}s -- the field is measured, not echoed"
else
  bad "N16 requested=$IMPREQ achieved=$IMPACH -- achieved_period_s is repeating the argument back"
fi

# And the mutation: a tool that hard-codes the old grid must make P11 fail.
"$PY" - "$TOOL" "$WORK/mut4.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
if "drain(args.esc_period)" not in src:
    sys.exit("mutation target for N17 not found")
open(sys.argv[2], "w", encoding="utf-8").write(
    src.replace("drain(args.esc_period)", "drain(0.02)"))
INNERPY
if [ -s "$WORK/mut4.py" ]; then
  wrote_case "$WORK/mut4.py" "$WORK/pm" "$WORK/pm.sent" \
    --send 'J BFC00000' --esc-after 1.0 --esc-period 0.002 --cr-settle 0.4 --seconds 3
  read -r NMUT _ <<< "$(esc_tail_shape "$WORK/pm.sent")"
  if [ "$NMUT" -lt 200 ]; then
    ok "N17 a tool that hard-codes 0.02 writes only $NMUT ESC under --esc-period 0.002, so P11 is testing the wiring"
  else
    bad "N17 the mutant still wrote $NMUT ESC -- P11 would pass on a tool that ignores the flag"
  fi
else
  bad "N17 the mutant was not produced, so P11 is unguarded"
fi

# --- N18..N24 / P12..P15  the terminator, and where its guard sits -----------
# A capture given neither --seconds nor --idle NEVER RETURNS: both default to
# 0.0 and the final read loop breaks on neither. 量 2026-08-29, rc=124 under
# `timeout -s TERM 8`. Fourteen of the fifteen console-capture rows on RUNSHEET
# B5's card were written without one, so the first person to follow that card
# literally is the person the refusal exists for.
#
# WHY THE GUARD'S POSITION IS ITSELF A CASE. It has to sit after _check_send
# (whose three refusals N4/N7/N8 assert, all with --port /dev/null) and before
# the port is opened (for the reason _check_send exists at all: a tool that
# opens the port and then refuses has already touched the device).
#
# 🔴 THIS BLOCK SAID "N21 is the sandwich that pins both sides with one command"
# AND THAT IS FALSE. N21 sends 127 characters -- a length _check_send ACCEPTS --
# so it gets the terminator refusal whether or not the guard sits above
# _check_send. N19 holds the lower edge (no `cannot open` in the refusal), N29
# holds the upper one (128 characters must get the LENGTH refusal) and N30 holds
# it against the overwrite check. One edge per case, by assertion rather than by
# three other cases happening to carry no terminator.

OUTNT="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/nt" 2>&1)"
if printf '%s\n' "$OUTNT" | grep -q 'needs a terminator'; then
  ok "N18 a capture with neither --seconds nor --idle is refused"
else
  bad "N18 a capture with no terminator was NOT refused -- it would not have returned"
  printf '%s\n' "$OUTNT" | sed 's/^/        /'
fi

# The port must not have been touched. --port /dev/null cannot be opened, so
# `cannot open` in the output is proof the guard ran too late.
if printf '%s\n' "$OUTNT" | grep -q 'cannot open'; then
  bad "N19 the no-terminator refusal came AFTER the port was opened"
  printf '%s\n' "$OUTNT" | sed 's/^/        /'
else
  ok "N19 the refusal happens before the port is opened -- no 'cannot open' in it"
fi

OUTS="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/ts" --seconds 1 2>&1)"
if printf '%s\n' "$OUTS" | grep -q 'cannot open'; then
  ok "P12 --seconds alone satisfies the guard and the run reaches the port"
else
  bad "P12 --seconds alone did not get past the terminator guard"
  printf '%s\n' "$OUTS" | sed 's/^/        /'
fi

# P13 is not a duplicate of P12. A guard written `if args.seconds <= 0` alone
# passes P12 and refuses every --idle capture -- including RUNSHEET D1, whose
# measured quantity IS a silence.
OUTI="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/ti" --idle 1 2>&1)"
if printf '%s\n' "$OUTI" | grep -q 'cannot open'; then
  ok "P13 --idle alone satisfies the guard too, so the guard is on the pair"
else
  bad "P13 --idle alone was refused -- the guard is on --seconds only"
  printf '%s\n' "$OUTI" | sed 's/^/        /'
fi

# Zero is the default. A run that passes it in longhand has asked for the same
# loop that does not return, and `if not args.seconds and not args.idle` would
# catch this one while `if args.seconds is None` would not.
OUTZ="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/tz" --seconds 0 --idle 0 2>&1)"
if printf '%s\n' "$OUTZ" | grep -q 'needs a terminator'; then
  ok "N20 an explicit --seconds 0 --idle 0 is still refused -- zero is not a terminator"
else
  bad "N20 --seconds 0 --idle 0 was accepted; that is the never-returning loop in longhand"
  printf '%s\n' "$OUTZ" | sed 's/^/        /'
fi

# N21. The reply must be the TERMINATOR refusal, which means the 127-byte line
# already passed _check_send (or it would say `console line buffer is`) and the
# port was never opened (or it would say `cannot open`).
#
# 🔴 THIS WAS LABELLED "THE SANDWICH" AND CLAIMED TO PIN BOTH SIDES. It pins
# ONE: the port side. 127 characters is a length _check_send ACCEPTS, so it can
# never produce that function's refusal and therefore cannot tell whether the
# guard sits above it. N29 sends 128 and is the case for that edge.
if [ ${#L127} -eq 127 ]; then
  OUTSW="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/sw" --send "$L127" 2>&1)"
  if printf '%s\n' "$OUTSW" | grep -q 'needs a terminator' \
     && ! printf '%s\n' "$OUTSW" | grep -q 'console line buffer is' \
     && ! printf '%s\n' "$OUTSW" | grep -q 'cannot open'; then
    ok "N21 a 127-char --send with no terminator hits the terminator guard (N29 is what pins the _check_send side; this one does not)"
  else
    bad "N21 the guard is not between _check_send and the port"
    printf '%s\n' "$OUTSW" | sed 's/^/        /'
  fi
else
  bad "N21 L127 is ${#L127} characters, so the sandwich cannot be built"
fi

# The metadata half, and it is the LARGER of the two defects
# bench/2026-08-30/CORRECTIONS-block0.md found: until 2026-08-30 the .meta.json
# recorded esc_seconds, esc_after_seconds, esc_period_requested_s and
# cr_settle_s and NEITHER terminator, so a census of what was passed had to be
# inferred from the stop_reason string -- which can prove a flag WAS given and
# can never prove it was not.
term_meta() {          # term_meta <outprefix> <key>
  "$PY" - "$1.meta.json" "$2" <<'INNERPY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
print(m.get(sys.argv[2], "ABSENT"))
INNERPY
}

wrote_case "$TOOL" "$WORK/tm1" "$WORK/tm1.sent" --send 'DW 8040DBC0 1' --seconds 2
TM1S="$(term_meta "$WORK/tm1" seconds)"
TM1I="$(term_meta "$WORK/tm1" idle)"
if [ "$TM1S" = "2.0" ] && [ "$TM1I" = "0.0" ]; then
  ok "P14 the metadata records the terminator it was given (seconds=$TM1S idle=$TM1I)"
else
  bad "P14 metadata seconds=$TM1S idle=$TM1I, wanted 2.0 and 0.0"
fi

# A field that reported a constant would pass P14. Vary BOTH, in opposite
# directions, and require both to move -- the same argument N16 makes about
# achieved_period_s.
wrote_case "$TOOL" "$WORK/tm2" "$WORK/tm2.sent" --send 'DW 8040DBC0 1' --seconds 3 --idle 1.5
TM2S="$(term_meta "$WORK/tm2" seconds)"
TM2I="$(term_meta "$WORK/tm2" idle)"
if [ "$TM2S" = "3.0" ] && [ "$TM2I" = "1.5" ] && [ "$TM2S" != "$TM1S" ] && [ "$TM2I" != "$TM1I" ]; then
  ok "N22 both fields move with the arguments ($TM1S/$TM1I -> $TM2S/$TM2I), so they are recorded and not constant"
else
  bad "N22 seconds=$TM2S idle=$TM2I against P14's $TM1S/$TM1I -- at least one field is a constant"
fi

# The guard is capture()'s. `report` reads a capture off disk and has no port,
# no loop and nothing to terminate; a guard installed in main() would refuse it.
if "$PY" "$TOOL" report "$WORK/tm1" --from 'DW' --to 'DW' >/dev/null 2>&1; then
  ok "P15 report takes no terminator and is not refused -- the guard is capture()'s alone"
else
  RP="$("$PY" "$TOOL" report "$WORK/tm1" --from 'DW' --to 'DW' 2>&1)"
  if printf '%s\n' "$RP" | grep -q 'needs a terminator'; then
    bad "P15 report was refused by the terminator guard -- it is installed too high"
  else
    ok "P15 report takes no terminator and is not refused -- the guard is capture()'s alone"
  fi
fi

# And the two mutations. Without these, N18 and P14 are assertions about a tool
# nobody has shown can fail them.
"$PY" - "$TOOL" "$WORK/mut5.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
target = "    if args.seconds <= 0 and args.idle <= 0:"
if target not in src:
    sys.exit("mutation target for N23 not found")
open(sys.argv[2], "w", encoding="utf-8").write(
    src.replace(target, "    if False:"))
INNERPY
if [ -s "$WORK/mut5.py" ]; then
  OUTM5="$("$PY" "$WORK/mut5.py" capture --port /dev/null --out "$WORK/m5" 2>&1)"
  if printf '%s\n' "$OUTM5" | grep -q 'needs a terminator'; then
    bad "N23 the mutant still refused -- N18 is not testing this guard"
  else
    ok "N23 with the guard disabled the same command runs on to the port, so N18 is testing the guard"
  fi
else
  bad "N23 the mutant was not produced, so N18 is unguarded"
fi

"$PY" - "$TOOL" "$WORK/mut6.py" <<'INNERPY'
import sys
src = open(sys.argv[1], encoding="utf-8").read()
target = '        "seconds": args.seconds,\n        "idle": args.idle,'
if target not in src:
    sys.exit("mutation target for N24 not found")
open(sys.argv[2], "w", encoding="utf-8").write(
    src.replace(target, '        "seconds": 0.0,\n        "idle": 0.0,'))
INNERPY
if [ -s "$WORK/mut6.py" ]; then
  wrote_case "$WORK/mut6.py" "$WORK/m6" "$WORK/m6.sent" --send 'DW 8040DBC0 1' --seconds 3 --idle 1.5
  M6S="$(term_meta "$WORK/m6" seconds)"
  M6I="$(term_meta "$WORK/m6" idle)"
  if [ "$M6S" = "3.0" ] || [ "$M6I" = "1.5" ]; then
    bad "N24 the hardcoding mutant still reported seconds=$M6S idle=$M6I -- P14/N22 would pass on it"
  else
    ok "N24 a tool that hardcodes the fields reports $M6S/$M6I, so P14 and N22 are reading the arguments"
  fi
else
  bad "N24 the mutant was not produced, so P14 and N22 are unguarded"
fi

# --- N25..N30  the guard's CONTRACT, not just its condition ------------------
# 量 2026-08-30, tools/test-console-capture-mutants.py against the forty cases
# above: 24 mutations, TEN alive. They fall into four classes and none of the
# forty could see a class, only instances of one:
#
#   WAIVER   an early `return` on a flag the guard has no business reading.
#            Every one of N18-N21 leaves --esc, --esc-after, --no-cr, --force,
#            --baud, --cr-settle and --esc-period at their defaults, so
#            `if args.esc > 0: return` in front of the guard passes all forty --
#            and `--esc 25` is A-catch's own shape. 量 on a pty, that mutant
#            with `--esc 1` and no terminator: rc=124 after 8 s, .log written,
#            .meta.json lost. The failure the guard was added for, back.
#   CONTRACT what a refusal IS. Not one of the forty asserted an exit code, so
#            `_fail` raising SystemExit(0) was green -- and a card written
#            `cmd || abort` would read a refusal as a success. Nor did any of
#            them look at stdout, so a refusal printed there instead of stderr
#            was green too, and a card that redirects would have captured it.
#   MESSAGE  one substring. A refusal naming a flag that does not exist passed.
#   POSITION the guard moved BELOW the overwrite refusal passed, which also
#            inverts which error the operator sees first.
#
# The cases below close all four. They are deliberately NOT more in-suite
# mutations: tools/test-console-capture-mutants.py owns "does this suite catch
# mutant X" and runs all 25 against the whole file. N23/N24 predate it and stay,
# because they keep this suite self-contained where the mutant runner is not run.

# The refusal contract in one place -- the same shape as flashwin's `refused()`,
# which was rebuilt around it on 2026-08-30 after three mutants that PRINTED
# this unit's MAC and then refused passed every check it had. stdout and stderr
# are captured SEPARATELY, which is the whole point: `2>&1` is what let E2 live.
cc_refuse() {          # cc_refuse <capture args...>  -> RC, ROUT, RERR
  RC=0
  ROUT="$("$PY" "$TOOL" capture "$@" 2>"$WORK/cc.err")" || RC=$?
  RERR="$(cat "$WORK/cc.err")"
}

# N25 and N26 partition the waiver class: N25 is --esc alone, because that is
# A-catch's shape and the one measured to reproduce the never-returning capture;
# N26 is every OTHER non-terminator flag at a non-default value, in one command,
# so a waiver on any of them goes red.
cc_refuse --port /dev/null --out "$WORK/wv1" --esc 1
if printf '%s' "$RERR" | grep -q 'needs a terminator' \
   && ! printf '%s' "$RERR" | grep -q 'cannot open'; then
  ok "N25 --esc 1 with no terminator is still refused -- the guard is not waived by A-catch's own flag"
else
  bad "N25 --esc 1 with no terminator was not refused by the guard (rc=$RC)"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

cc_refuse --port /dev/null --out "$WORK/wv2" --esc-after 1 --esc-period 0.002 \
          --no-cr --cr-settle 0.5 --baud 115200 --force --send 'DW 8040DBC0 1'
if printf '%s' "$RERR" | grep -q 'needs a terminator' \
   && ! printf '%s' "$RERR" | grep -q 'cannot open'; then
  ok "N26 six other non-default flags with no terminator are still refused -- no flag waives the guard"
else
  bad "N26 a non-terminator flag waived the guard (rc=$RC)"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

# N27 is the exit code AND stdout, on N18's own command. Two assertions, one
# case, because they are one contract: a refusal that exits 0 and a refusal that
# prints to stdout are the same mistake seen from two sides -- the caller cannot
# tell it happened.
cc_refuse --port /dev/null --out "$WORK/rc1"
if [ "$RC" -ne 0 ] && [ -z "$ROUT" ]; then
  ok "N27 a refusal exits $RC and writes nothing to stdout -- \`cmd || abort\` sees it, \`cmd > log\` does not swallow it"
else
  bad "N27 refusal contract: rc=$RC (want != 0), ${#ROUT} byte(s) on stdout (want 0)"
  [ -n "$ROUT" ] && printf '%s\n' "$ROUT" | sed 's/^/        stdout: /' | head -2
fi

# N28 is the message, and the assertion is on the FIRST LINE only.
#
# 🔴 That is not fussiness, it is a measurement. The first version of this case
# grepped the whole refusal for both flag names and the M1 mutant -- which
# rewrites the imperative line to name `--timeout`, a flag that does not exist
# -- SURVIVED it: the message is fourteen lines long and its sizing paragraph
# says `--seconds 4` and `--idle N ends on N seconds of silence`, so both names
# are still in there. A substring test over a message that long is very nearly
# unfalsifiable. What an operator retypes is line one, so line one is the
# contract.
RERR1="$(printf '%s\n' "$RERR" | head -1)"
if printf '%s' "$RERR1" | grep -q -- '--seconds' \
   && printf '%s' "$RERR1" | grep -q -- '--idle'; then
  ok "N28 the refusal's FIRST LINE names both flags that satisfy it, so what an operator retypes exists"
else
  bad "N28 the first line of the refusal does not name both --seconds and --idle"
  printf '%s\n' "$RERR1" | sed 's/^/        /'
fi

# N29 pins the guard's UPPER side directly, which N21 does not. N21 sends a
# 127-character line -- one _check_send accepts -- so it passes whether or not
# the guard sits above it. This one sends 128, which _check_send must refuse
# FIRST: with the guard moved above it the reply becomes the terminator refusal
# and this case goes red. Until today that side was held only by N4/N7/N8
# happening to have no terminator, which is coverage by accident.
if [ ${#L128} -eq 128 ]; then
  cc_refuse --port /dev/null --out "$WORK/ord" --send "$L128"
  if printf '%s' "$RERR" | grep -q 'console line buffer is' \
     && ! printf '%s' "$RERR" | grep -q 'needs a terminator'; then
    ok "N29 a 128-char --send with no terminator gets the LENGTH refusal -- _check_send runs first, by assertion"
  else
    bad "N29 the terminator guard is above _check_send"
    printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
  fi
else
  bad "N29 L128 is ${#L128} characters, so the ordering cannot be pinned"
fi

# N30 pins the LOWER side against the overwrite refusal. Both are refusals
# before the port, so nothing above notices which comes first -- and the order
# matters to the operator: told `exists`, they pass --force and hit the
# never-returning loop the guard exists for.
: > "$WORK/ovw.log"; : > "$WORK/ovw.timing"; : > "$WORK/ovw.meta.json"
cc_refuse --port /dev/null --out "$WORK/ovw"
if printf '%s' "$RERR" | grep -q 'needs a terminator' \
   && ! printf '%s' "$RERR" | grep -q 'Refusing to overwrite'; then
  ok "N30 with the output files already present the TERMINATOR refusal still comes first"
else
  bad "N30 the overwrite refusal is above the terminator guard -- the operator is told the wrong thing"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

# --------------------------------------------------------------------------
# --until, 2026-09-09.  Ten cases, two of them positive because the flag has
# TWO break sites -- the --esc-after loop and the final read loop -- and a
# suite that exercised one would leave the other unmeasured.
#
# WHY THE FLAG EXISTS, so a reader of this block does not have to go looking:
# every --esc-after window on seating 17's card was sized from a frequency the
# card's own third cell then refuted by 76x, and two of that seating's three
# power cycles went on a cell whose window was shorter than the answer -- the
# board reset with nothing streaming ESC, the loader prompt went by uncaught,
# and the vendor firmware booted.  "Take three times the prediction" does not
# cover 76x and does not exist at all for FW-53's bit scan, where not knowing
# the answer is the point.  量 bench/2026-09-08b/R2-B8.timing: the console is
# SILENT for 41.931 s while a bite is pending, so --idle cannot wait for it
# either.  Stopping on the event is the only shape left.
# --------------------------------------------------------------------------

until_case() {         # until_case <outprefix> <dump> <playspec> -- <capture args...>
  local _out="$1" _dump="$2" _play="$3"; shift 3
  [ "$1" = "--" ] && shift
  "$PY" - "$TOOL" "$_out" "$_dump" "$_play" "$@" <<'INNERPY'
import os, pty, select, subprocess, sys, time

tool, out, dump, play = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
extra = sys.argv[5:]
# playspec: "at:text|at:text|..."  text goes through unicode_escape so \r and
# \n are writable from the shell without a second quoting layer.
script = []
if play and play != "-":
    for part in play.split("|"):
        at, _, text = part.partition(":")
        script.append((float(at),
                       text.encode().decode("unicode_escape").encode("latin-1")))
script.sort()

master, slave = pty.openpty()
name = os.ttyname(slave)
proc = subprocess.Popen(
    ["/usr/bin/python3", tool, "capture", "--port", name, "--out", out] + extra,
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0 = time.monotonic()
seen = bytearray()
i = 0
while proc.poll() is None:
    r, _, _ = select.select([master], [], [], 0.02)
    if r:
        try:
            seen += os.read(master, 4096)
        except OSError:
            break
    now = time.monotonic() - t0
    while i < len(script) and now >= script[i][0]:
        try:
            os.write(master, script[i][1])
        except OSError:
            pass
        i += 1
    if now > 60:
        proc.kill()
        break
proc.wait(timeout=15)
open(dump, "wb").write(bytes(seen))
os.close(master); os.close(slave)
INNERPY
}

# P16 -- the --esc-after loop ends on the pattern.  This is the site that costs
# a power cycle when it is missing: the ESC stream is what catches the loader
# after a reset the command caused, and once it HAS caught it every further ESC
# is residue.  --esc-after 4, pattern played at 1.0 s.
until_case "$WORK/u1" "$WORK/u1.sent" '1.0:---RealTek(RTL8196E)at 2014.04.22\r\n<RealTek>' -- \
  --send 'J BFC00000' --esc-after 4 --seconds 12 --until '<RealTek>'
U1W="$(esc_meta "$WORK/u1" esc_after window_s)"
U1E="$(esc_meta "$WORK/u1" esc_after ended_on_until)"
U1S="$(term_meta "$WORK/u1" stop_reason)"
U1O="$(term_meta "$WORK/u1" until_offset)"
if [ "$U1E" = "True" ] && fnum "$U1W < 2.5" \
   && printf '%s' "$U1S" | grep -q -- '--until matched at offset' \
   && [ "$U1O" != "None" ] && [ "$U1O" != "ABSENT" ]; then
  ok "P16 --until ended the --esc-after loop at ${U1W}s of a 4 s window, offset $U1O"
else
  bad "P16 --esc-after did not end on the pattern (window_s=$U1W ended_on_until=$U1E offset=$U1O stop=$U1S)"
fi

# N31 -- the control.  Same play, same window, no --until: the loop must run
# the full 4 s.  Without this, P16 cannot tell the flag from a tool that got
# bored.
until_case "$WORK/u2" "$WORK/u2.sent" '1.0:---RealTek(RTL8196E)at 2014.04.22\r\n<RealTek>' -- \
  --send 'J BFC00000' --esc-after 4 --seconds 12
U2W="$(esc_meta "$WORK/u2" esc_after window_s)"
U2E="$(esc_meta "$WORK/u2" esc_after ended_on_until)"
U2O="$(term_meta "$WORK/u2" until_offset)"
if fnum "$U2W >= 3.5" && [ "$U2E" = "None" ] && [ "$U2O" = "None" ]; then
  ok "N31 without --until the same window runs its full ${U2W}s, so P16 measures the flag"
else
  bad "N31 the no---until control did not run the full window (window_s=$U2W ended_on_until=$U2E offset=$U2O)"
fi

# P17 -- the second break site.  The pattern arrives AFTER the ESC window has
# closed, so the ESC loop cannot be what stopped the run; the final read loop
# is.  --esc-after 1, pattern at 2.5 s, cap 12 s.
until_case "$WORK/u3" "$WORK/u3.sent" '2.5:RLXFW-B00\r\n' -- \
  --send 'reboot -f' --esc-after 1 --cr-settle 0.4 --seconds 12 --until 'RLXFW-B00'
U3S="$(term_meta "$WORK/u3" stop_reason)"
U3D="$(term_meta "$WORK/u3" duration_s)"
U3E="$(esc_meta "$WORK/u3" esc_after ended_on_until)"
if printf '%s' "$U3S" | grep -q -- '--until matched at offset' \
   && [ "$U3E" = "None" ] && fnum "$U3D < 6.0"; then
  ok "P17 a pattern arriving after the ESC window stops the FINAL loop instead, at ${U3D}s of a 12 s cap"
else
  bad "P17 the final read loop did not stop on the pattern (stop=$U3S dur=$U3D ended_on_until=$U3E)"
fi

# N32 -- A PATTERN THAT ARRIVES IN TWO PIECES MUST STILL MATCH.  The two halves
# are played 0.6 s apart, so they land in different read() calls and a tool
# that tested each chunk on its own would never see `RealTek`.  This is the one
# defect in this flag that would be invisible at the bench: the cell would just
# run to its cap and look like a window that was too short, which is exactly
# the reading --until exists to remove.
until_case "$WORK/u4" "$WORK/u4.sent" '1.0:Real|1.6:Tek>\r\n' -- \
  --send 'J BFC00000' --esc-after 6 --seconds 12 --until 'RealTek'
U4S="$(term_meta "$WORK/u4" stop_reason)"
U4E="$(esc_meta "$WORK/u4" esc_after ended_on_until)"
if printf '%s' "$U4S" | grep -q -- '--until matched at offset' && [ "$U4E" = "True" ]; then
  ok "N32 a pattern split across two read()s 0.6 s apart still matches -- the search is on the buffer, not the chunk"
else
  bad "N32 a split pattern was missed, so --until is testing chunks (stop=$U4S ended_on_until=$U4E)"
fi

# N33 -- ORDER against the terminator guard, and it is a decision.  A run given
# a bad regex AND no terminator is told about the TERMINATOR, because that is
# the defect that costs a power cycle; a bad regex costs a retype.
cc_refuse --port /dev/null --out "$WORK/uo1" --until '('
if printf '%s' "$RERR" | grep -q 'needs a terminator' \
   && ! printf '%s' "$RERR" | grep -q 'bad pattern'; then
  ok "N33 a bad --until with no terminator gets the TERMINATOR refusal -- _check_until runs after, by assertion"
else
  bad "N33 _check_until is above the terminator guard (rc=$RC)"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

# N34 -- and with a terminator present the regex IS checked, before the port.
cc_refuse --port /dev/null --out "$WORK/uo2" --seconds 2 --until '('
if printf '%s' "$RERR" | grep -q -- '--until: bad pattern' \
   && ! printf '%s' "$RERR" | grep -q 'cannot open'; then
  ok "N34 a bad --until regex is refused before the port is opened"
else
  bad "N34 a bad --until regex reached the port or was not refused (rc=$RC)"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

# N35 -- the empty pattern.  `re.compile(b"")` is VALID and matches at offset 0
# of everything, so a capture given it would stop on the first byte that
# arrives and report a stop_reason that reads like a successful catch.  It is
# refused by value, not by compilation.
cc_refuse --port /dev/null --out "$WORK/uo3" --seconds 2 --until ''
if printf '%s' "$RERR" | grep -q 'empty pattern'; then
  ok "N35 --until '' is refused -- a pattern that matches at offset 0 is not a terminator, it is a truncation"
else
  bad "N35 an empty --until pattern was accepted (rc=$RC)"
  printf '%s\n' "$RERR" | sed 's/^/        /' | head -3
fi

# N36 -- THE FOOTGUN, MEASURED RATHER THAN DOCUMENTED.  Arming happens when the
# command line is WRITTEN, not when its echo comes back, so a pattern that is a
# substring of --send matches the board's own echo in milliseconds.  This case
# asserts the hazard reproduces; it is what the --help text is quoting.
until_case "$WORK/u5" "$WORK/u5.sent" '0.5:echo bite 9 > /proc/rtl819x-wdt\r\n' -- \
  --send 'echo bite 9 > /proc/rtl819x-wdt' --seconds 8 --until 'bite 9'
U5S="$(term_meta "$WORK/u5" stop_reason)"
U5O="$(term_meta "$WORK/u5" until_offset)"
if printf '%s' "$U5S" | grep -q -- '--until matched at offset' \
   && [ "$U5O" != "None" ] && fnum "$U5O < 40"; then
  ok "N36 a --until that is a substring of --send matches the board's ECHO at offset $U5O -- the hazard is real and is in --help"
else
  bad "N36 the echo hazard did not reproduce, so the --help text is asserting something unmeasured (stop=$U5S offset=$U5O)"
fi

# N37 -- the pre-send --esc window does NOT arm the search.  Without this, a
# card using `<RealTek>` on a reset cell could not use --esc on the same run:
# the ESC loop emits a prompt of its own every 128 bytes and would fire the
# pattern before the command was ever sent.  The play here lands INSIDE the
# --esc window and nowhere else, so a correctly armed run never matches and
# ends on its cap.
until_case "$WORK/u6" "$WORK/u6.sent" '0.5:<RealTek>' -- \
  --esc 2 --send 'DW 8040DBC0 1' --cr-settle 0.4 --seconds 6 --until '<RealTek>'
U6S="$(term_meta "$WORK/u6" stop_reason)"
U6O="$(term_meta "$WORK/u6" until_offset)"
U6U="$(term_meta "$WORK/u6" until)"
if printf '%s' "$U6S" | grep -q -- '--seconds' && [ "$U6O" = "None" ] \
   && [ "$U6U" = "<RealTek>" ]; then
  ok "N37 a match inside the pre-send --esc window does not stop the run -- the search is armed at the command line"
else
  bad "N37 --until was armed during the --esc window (stop=$U6S offset=$U6O until=$U6U)"
fi

# N38 -- a pattern that never arrives is a READING, not a failure.  The capture
# runs to its cap, stop_reason names the cap, and until_offset is null beside a
# non-null until -- which is the two-directional record stop_reason alone
# cannot give: "armed and did not see it" and "never armed" are different
# facts and this is where they are told apart.
until_case "$WORK/u7" "$WORK/u7.sent" '0.5:hello\r\n' -- \
  --send 'DW 8040DBC0 1' --seconds 3 --until 'NEVER-ARRIVES-XYZ'
U7S="$(term_meta "$WORK/u7" stop_reason)"
U7O="$(term_meta "$WORK/u7" until_offset)"
U7U="$(term_meta "$WORK/u7" until)"
if printf '%s' "$U7S" | grep -q -- '--seconds 3.0 elapsed' && [ "$U7O" = "None" ] \
   && [ "$U7U" = "NEVER-ARRIVES-XYZ" ]; then
  ok "N38 an unmatched --until runs to the cap and records armed-and-unseen, which stop_reason alone cannot say"
else
  bad "N38 an unmatched --until did not fall through cleanly (stop=$U7S offset=$U7O until=$U7U)"
fi

# --------------------------------------------------------------------------
# N39/N40 -- until_offset must POINT AT THE PATTERN, and the two cases exist
# because the ten above cannot tell whether it does.
#
# 🔴 Found by auditing this block rather than by a red case: in every case up
# to N38 the search is armed when the log is still empty, so the offset of a
# match inside the rolling buffer and its offset inside the .log are the same
# number, and an implementation that forgot the base entirely would pass all
# ten.  The base moves for two different reasons -- it is SET at the arming
# point, and it ADVANCES when the buffer rolls past _UNTIL_WINDOW -- so there
# are two edges and one case each.  Both assert by reading the .log at the
# offset the metadata gives, which is the only check that cannot be satisfied
# by a plausible-looking number.
# --------------------------------------------------------------------------

at_offset() {          # at_offset <outprefix> <offset> <nbytes>
  "$PY" - "$1.log" "$2" "$3" <<'INNERPY'
import sys
b = open(sys.argv[1], "rb").read()
o, n = int(sys.argv[2]), int(sys.argv[3])
sys.stdout.write(b[o:o + n].decode("latin-1"))
INNERPY
}

# N39 -- the base is SET at the arming point.  200 bytes arrive during the
# pre-send --esc window, so a match reported without the base would come back
# ~200 low and land in the middle of that filler.
until_case "$WORK/u8" "$WORK/u8.sent" \
  "0.5:$(printf 'F%.0s' $(seq 1 200))|3.6:<RealTek>" -- \
  --esc 2 --send 'DW 8040DBC0 1' --cr-settle 0.4 --seconds 9 --until '<RealTek>'
U8O="$(term_meta "$WORK/u8" until_offset)"
if [ "$U8O" != "None" ] && [ "$U8O" != "ABSENT" ] && fnum "$U8O >= 200" \
   && [ "$(at_offset "$WORK/u8" "$U8O" 9)" = '<RealTek>' ]; then
  ok "N39 with 200 bytes logged before arming, until_offset $U8O points at the pattern in the .log"
else
  bad "N39 until_offset does not carry the arming base (offset=$U8O, log there: '$(at_offset "$WORK/u8" "${U8O:-0}" 9)')"
fi

# N40 -- the base ADVANCES when the buffer rolls.  _UNTIL_WINDOW is 8192, so
# 20,000 bytes of filler after arming force it to drop and re-base three times
# before the pattern arrives.  A tool that never advances it reports a number
# under 8192 and this case reads filler at that offset instead of the pattern.
until_case "$WORK/u9" "$WORK/u9.sent" \
  "0.6:$(printf 'F%.0s' $(seq 1 20000))|2.2:<RealTek>" -- \
  --send 'DW 8040DBC0 1' --seconds 9 --until '<RealTek>'
U9O="$(term_meta "$WORK/u9" until_offset)"
if [ "$U9O" != "None" ] && [ "$U9O" != "ABSENT" ] && fnum "$U9O >= 20000" \
   && [ "$(at_offset "$WORK/u9" "$U9O" 9)" = '<RealTek>' ]; then
  ok "N40 after 20,000 bytes rolled the 8,192-byte window, until_offset $U9O still points at the pattern"
else
  bad "N40 until_offset does not advance with the rolling window (offset=$U9O, log there: '$(at_offset "$WORK/u9" "${U9O:-0}" 9)')"
fi

# N41 -- --until is tested BEFORE --seconds, and the case is deterministic
# rather than a race.  The trick is to let --seconds expire during the ESC
# window and its settle, so that on the FIRST iteration of the final loop both
# conditions are already true and only the order can decide:
#
#   --esc-after 4 --seconds 2, pattern at 1.0 s.  The ESC loop breaks on the
#   pattern at ~1.0 s; terminate_esc_line then gets budget = 2.0 - 1.0 and
#   spends all of it waiting for a prompt that does not come again; the final
#   loop is entered at ~2.05 s with until_at already set.
#
# Correct order says --until.  The other order says "--seconds elapsed" on a
# capture that DID see its event, which reads as "the window was too short" --
# the exact misreading this flag exists to remove.
until_case "$WORK/ua" "$WORK/ua.sent" '1.0:---RealTek(RTL8196E)\r\n<RealTek>' -- \
  --send 'J BFC00000' --esc-after 4 --seconds 2 --until '<RealTek>'
UAS="$(term_meta "$WORK/ua" stop_reason)"
UAD="$(term_meta "$WORK/ua" duration_s)"
if printf '%s' "$UAS" | grep -q -- '--until matched at offset' && fnum "$UAD >= 1.9"; then
  ok "N41 with the cap already expired on entry (${UAD}s of 2 s), stop_reason still names --until"
else
  bad "N41 --seconds wins over a matched --until, so a caught event reads as a short window (stop=$UAS dur=$UAD)"
fi

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
