#!/bin/bash
# Part B of block 39.
#
# 🔴 THREE CELLS HERE ARE OFF-CARD AND DECLARED.  The frozen card's Part B
# jumps straight to B1-PING against 10.1.1.3 and NOTHING on the card brings
# rlx0 up -- the same defect seating 13's card had ("a ping cell whose
# interface no cell on that cycle brings up").  Caught before it was typed,
# recorded rather than quietly patched:
#
#   B0a-SW   the switch's SIRR/TRXRDY start.  Without it ping is 100 % loss
#            and it looks like a driver fault (PROGRESS.md, R6-5's carried-
#            forward item 通電前必做).
#   B0b-UP   unlock + netdev on + ifconfig rlx0 10.1.1.3 up.
#   B2-CON   a passive console capture across the blast.  The card has no
#            console cell for B2, so a kernel oops during the wedge would be
#            invisible.  Sends nothing.
#
# The card's own cells are unchanged, in card order, with the card's own
# durations.  The +5/+30/+120/+600 schedule is NOMINAL: each cat cell runs for
# 25 s by the card, so the later cells start later than their nominal offset.
# The ACTUAL offsets are computed afterwards from each capture's
# started_wallclock, and those are what gets reported.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9

say() { echo; echo "===== $* ====="; }

say "B0a-SW  OFF-CARD: switch start"
$CAP --out $D/B0a-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25 > /dev/null 2>&1
cat -v $D/B0a-SW.log

say "B0b-UP  OFF-CARD: bring rlx0 up"
$CAP --out $D/B0b-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25 > /dev/null 2>&1
cat -v $D/B0b-UP.log

say "B0-SW  CARD: R6-6's readable half"
$CAP --out $D/B0-SW --send 'cat /proc/rtl819x-switch' --seconds 30 > /dev/null 2>&1
cat -v $D/B0-SW.log

say "B1-PING  CARD: the before half.  A failure here voids the ladder."
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/B1-PING.log 2>&1
echo "B1-PING rc=$?"; cat $D/B1-PING.log

say "B1-NIC  CARD"
$CAP --out $D/B1-NIC --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
cat -v $D/B1-NIC.log

say "B2-LADDER  CARD: Y5's dose against rlxfw"
$CAP --out $D/B2-CON --seconds 30 > /dev/null 2>&1 &
CONPID=$!
sleep 1
$NB blast --target 10.1.1.3 --src 10.1.1.2 --dev $DEV \
    --rates 0.5 --step-s 8 --out $D/B2-LADDER.json 2>&1 | tee $D/B2-LADDER.log
T0=$(date +%s)
echo "WEDGE-T0=$T0"
wait $CONPID
echo "B2-CON bytes: $(wc -c < $D/B2-CON.log)"
echo "--- B2-CON ---"; cat -v $D/B2-CON.log

wait_until() {   # $1 = seconds after T0
  local target=$((T0 + $1)) now
  while :; do
    now=$(date +%s)
    [ "$now" -ge "$target" ] && break
    sleep 1
  done
  echo "  (t = +$(( $(date +%s) - T0 )) s)"
}

for spec in "5 B3-T5 B3-P5" "30 B4-T30 B4-P30" "120 B5-T120 B5-P120" "600 B6-T600 B6-P600"; do
  set -- $spec
  OFF=$1; TC=$2; PC=$3
  say "$TC  CARD: nominal +$OFF s"
  wait_until "$OFF"
  $CAP --out $D/$TC --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
  cat -v $D/$TC.log
  say "$PC  CARD"
  ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/$PC.log 2>&1
  echo "$PC rc=$?  (t = +$(( $(date +%s) - T0 )) s)"; cat $D/$PC.log
done

say "PART B DONE"
