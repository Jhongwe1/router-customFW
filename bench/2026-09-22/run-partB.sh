#!/bin/bash
# Part B of block 40, seating 37.
#
# The single-variable demonstration: create the fault with the detector OFF,
# read it whole, then switch the detector on IN FRONT OF IT.  A run with the
# detector armed the whole time cannot distinguish "it worked" from "it never
# wedged"; this one can, because the fault is already present when the only
# variable moves.
#
# Output goes to a FILE.  Piping a bench runner into `head` killed run-partA.sh
# with SIGPIPE at cell 6 of 8 tonight -- the bash form of the `Select-Object
# -First N` trap CLAUDE.md already records for PowerShell.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-22
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9

say() { echo; echo "===== $* ====="; }
keys='recov_mode|recov_ms|recov_jiffies|n_recov_|recov_rc|recov_j_|n_tx |n_tx_stop|n_tx_wake|n_rx |n_irq |tx_stopped|txd|n_ph_|ph_agree|ph_last|now_iisr|now_iimr|iimr_base|n_arm_flush|truncated'
dumpkeys() { grep -aE "$keys" "$1" | tr -d '\r'; }

say "B1-OFF  confirm recover 0"
$CAP --out $D/B1-OFF --send 'echo recover 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
dumpkeys $D/B1-OFF.log

say "B2  Y5's dose, 347 frames / 8 s / 0.5 Mbit/s, with a passive console capture"
$CAP --out $D/B2-CON --seconds 30 > /dev/null 2>&1 &
CONPID=$!
sleep 1
$NB blast --target 10.1.1.3 --src 10.1.1.2 --dev $DEV \
    --rates 0.5 --step-s 8 --out $D/B2-LADDER.json > $D/B2-LADDER.log 2>&1
echo "B2-LADDER rc=$?"
cat $D/B2-LADDER.log
wait $CONPID
echo "B2-CON bytes: $(wc -c < $D/B2-CON.log)  (0 = no oops on the console)"

say "B3-PING  expect 0/4"
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/B3-PING.log 2>&1
echo "B3-PING rc=$?"; cat $D/B3-PING.log

say "B4-WEDGE  the wedged state, read whole"
$CAP --out $D/B4-WEDGE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
dumpkeys $D/B4-WEDGE.log
echo "--- mbd lines: the engine's own record of which mbuf it used ---"
grep -aE '^(mbd|rxd)' $D/B4-WEDGE.log | tr -d '\r'

say "B5-ON  THE SINGLE VARIABLE"
$CAP --out $D/B5-ON --send 'echo recover 1 > /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
cat -v $D/B5-ON.log | sed 's/\^\[/ESC/g'

say "B6-AFTER"
$CAP --out $D/B6-AFTER --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
dumpkeys $D/B6-AFTER.log

say "B7-PING  expect 4/4"
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/B7-PING.log 2>&1
echo "B7-PING rc=$?"; cat $D/B7-PING.log

say "B8-LADDER  the reproduction, detector left armed"
$NB blast --target 10.1.1.3 --src 10.1.1.2 --dev $DEV \
    --rates 0.5 --step-s 8 --out $D/B8-LADDER.json > $D/B8-LADDER.log 2>&1
echo "B8-LADDER rc=$?"
cat $D/B8-LADDER.log

say "B9-AFTER"
$CAP --out $D/B9-AFTER --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
dumpkeys $D/B9-AFTER.log

say "B9-PING"
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/B9-PING.log 2>&1
echo "B9-PING rc=$?"; cat $D/B9-PING.log

say "PART B DONE"
