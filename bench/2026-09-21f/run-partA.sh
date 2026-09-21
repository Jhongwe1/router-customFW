#!/bin/bash
# Part A of block 39, run as one command so there is no operator gap between
# cells.  Every cell is exactly the line the frozen card carries.
#
# A3-CON/A3-LADDER and A5-CON/A5-LONG are concurrent by construction: the
# console capture is started in the background and the ladder runs inside its
# window.  The console capture sends NOTHING (no --esc, no --send), so it
# cannot perturb the loader's command loop -- card § 2.4.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9

say() { echo; echo "===== $* ====="; }

say "A0-IPCFG  the command the old framing was missing"
$CAP --out $D/A0-IPCFG --send 'IPCONFIG 10.1.1.1' --seconds 10
echo "A0_rc=$?"
echo "--- A0 log ---"; cat -v $D/A0-IPCFG.log

say "A1-ARP  THE POSITIVE CONTROL -- SILENT here voids every SILENT below"
$NB probe --target 10.1.1.1 --dev $DEV --src 10.1.1.2 > $D/A1-ARP.log 2>&1
echo "A1_rc=$?"; cat $D/A1-ARP.log

say "A2  does an ESC stream suppress the polled NIC service loop?"
$CAP --out $D/A2-CON --esc 16 --esc-period 0.02 --seconds 18 > /dev/null 2>&1 &
CONPID=$!
sleep 2
$NB probe --target 10.1.1.1 --dev $DEV --src 10.1.1.2 > $D/A2-ARP.log 2>&1
echo "A2_rc=$?"; cat $D/A2-ARP.log
wait $CONPID
echo "A2-CON bytes: $(wc -c < $D/A2-CON.log)"

say "A3  THE LADDER -- rung 1 is Y5's dose exactly"
$CAP --out $D/A3-CON --seconds 110 > /dev/null 2>&1 &
CONPID=$!
sleep 1
$NB blast --target 10.1.1.1 --src 10.1.1.2 --dev $DEV \
    --rates 0.5,1.0,2.0,4.0,8.0 --step-s 8 --arp-load \
    --out $D/A3-LADDER.json 2>&1 | tee $D/A3-LADDER.log
echo "A3_rc=${PIPESTATUS[0]}"
wait $CONPID
echo "A3-CON bytes: $(wc -c < $D/A3-CON.log)"
echo "--- A3-CON content (should be empty) ---"; cat -v $D/A3-CON.log

say "A4-ARP"
$NB probe --target 10.1.1.1 --dev $DEV --src 10.1.1.2 > $D/A4-ARP.log 2>&1
echo "A4_rc=$?"; cat $D/A4-ARP.log

say "A5  the 30 s rung at the top of the ladder"
$CAP --out $D/A5-CON --seconds 50 > /dev/null 2>&1 &
CONPID=$!
sleep 1
$NB blast --target 10.1.1.1 --src 10.1.1.2 --dev $DEV \
    --rates 8.0 --step-s 30 --arp-load \
    --out $D/A5-LONG.json 2>&1 | tee $D/A5-LONG.log
echo "A5_rc=${PIPESTATUS[0]}"
wait $CONPID
echo "A5-CON bytes: $(wc -c < $D/A5-CON.log)"
echo "--- A5-CON content (should be empty) ---"; cat -v $D/A5-CON.log

say "A6-ARP"
$NB probe --target 10.1.1.1 --dev $DEV --src 10.1.1.2 > $D/A6-ARP.log 2>&1
echo "A6_rc=$?"; cat $D/A6-ARP.log

say "A7-PROMPT  is the command loop still there, and did the board reset?"
$CAP --out $D/A7-PROMPT --esc 6 --esc-period 0.02 --seconds 10
echo "A7_rc=$?"
echo "--- A7 log ---"; cat -v $D/A7-PROMPT.log | head -20

say "PART A DONE"
