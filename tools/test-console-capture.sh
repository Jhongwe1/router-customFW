#!/usr/bin/env bash
# Self-test for tools/console-capture.py.
#
# The tool's whole claim is that a number comes out of the wire rather than out
# of a stopwatch, and that the bytes it stores are the bytes the device sent.
# Both halves are checkable without a device: a pty stands in for the CP2102, a
# writer on the master side plays a known script with known gaps, and the tool
# reads the slave believing it is a serial port.
#
# Twenty-four cases, twenty-five results (P3 checks two things). Fourteen of
# them are controls whose job is to FAIL, because a test suite that cannot fail
# proves nothing -- the same argument tools/audit-bench-log.py
# makes about its own patterns and the reason PROGRESS.md rejected hazlint's
# original "stage 2 must report zero" control.
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
TOOL="$HERE/console-capture.py"
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

  OUT127="$("$PY" "$TOOL" capture --port /dev/null --out "$WORK/k" --send "$L127" 2>&1)"
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

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
