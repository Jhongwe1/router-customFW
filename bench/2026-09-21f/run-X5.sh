#!/bin/bash
# OFF-CARD, and declared as such.  The frozen card has no cell that asks
# whether the blast's frames reached the ENGINE, and without that "the loader
# survived 31,475 frames" is a claim about the host's sending loop.
#
# Method: bracket a blast with a read of the loader's own globals.
# docs/nic-vendor-diff.md § 12.1 locates tx_count at 0x8040EAC8; anything
# beside it that moves by the frame count is the receive side.  The negative
# control is the IDLE bracket that runs first: the same two reads with no
# blast between them.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9

say() { echo; echo "===== $* ====="; }

say "X5-GLOB-A  globals, first read"
$CAP --out $D/X5-globA --send 'DW 8040EAC0 16' --seconds 15 > /dev/null 2>&1
cat -v $D/X5-globA.log

say "X5-IDLE  the NEGATIVE control: 10 s with no blast"
sleep 10

say "X5-GLOB-B  globals again, nothing sent between A and B"
$CAP --out $D/X5-globB --send 'DW 8040EAC0 16' --seconds 15 > /dev/null 2>&1
cat -v $D/X5-globB.log

say "X6-BLAST  8 Mbit/s for 8 s, NO arp load -- nothing else on the wire"
$NB blast --target 10.1.1.1 --src 10.1.1.2 --dev $DEV \
    --rates 8.0 --step-s 8 --out $D/X6-BLAST.json 2>&1 | tee $D/X6-BLAST.log

say "X7-GLOB-C  globals after the blast"
$CAP --out $D/X7-globC --send 'DW 8040EAC0 16' --seconds 15 > /dev/null 2>&1
cat -v $D/X7-globC.log

say "X8-RINGS  RX pkthdr ring + TX0 ring"
$CAP --out $D/X8-rings --send 'DW A040FC70 8' --seconds 15 > /dev/null 2>&1
cat -v $D/X8-rings.log

say "X9-MBUFRING  RX mbuf ring"
$CAP --out $D/X9-mbufring --send 'DW A040FCD0 4' --seconds 15 > /dev/null 2>&1
cat -v $D/X9-mbufring.log

say "X5-X9 DONE"
