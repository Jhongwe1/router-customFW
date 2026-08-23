#!/usr/bin/env bash
# Self-test for tools/console-capture.py.
#
# The tool's whole claim is that a number comes out of the wire rather than out
# of a stopwatch, and that the bytes it stores are the bytes the device sent.
# Both halves are checkable without a device: a pty stands in for the CP2102, a
# writer on the master side plays a known script with known gaps, and the tool
# reads the slave believing it is a serial port.
#
# Ten cases. Six of them are controls whose job is to FAIL, because a test
# suite that cannot fail proves nothing -- the same argument tools/audit-bench-log.py
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

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
