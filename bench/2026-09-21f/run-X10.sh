#!/bin/bash
# OFF-CARD, declared.  A SECOND SOURCE on the wedged engine.
#
# Every number Part B reports about the engine -- now_icr, now_iisr,
# tpdcr0_pos, the four txd OWN bits -- is read by rlxfw's own driver through
# rlxfw's own /proc.  "A tool reporting 0 is making a claim": now_iisr
# 00000000 on a wedged engine is exactly the reading that would look identical
# if the driver's register access were broken.
#
# The vendor's /proc/rtl865x/memory reaches the same registers through code
# this project did not write (NET-33 measured it moving four of six registers,
# which is the control that says the path reaches hardware).  It prints ONE
# word for a length of 4.
#
# READS ONLY.  No `echo write` anywhere in this script.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"

rd() {  # $1 = cell name, $2 = address, $3 = what it is
  echo; echo "===== $1  $2  $3 ====="
  $CAP --out $D/$1 --send "echo read $2 4 > /proc/rtl865x/memory" --idle 3 --seconds 20 > /dev/null 2>&1
  cat -v $D/$1.log
}

rd X10-ICR   0xB8010000 "CPUICR  -- rlxfw says C4000000"
rd X10-IISR  0xB801002C "CPUIISR -- rlxfw says 00000000, and that is the claim being checked"
rd X10-IIMR  0xB8010028 "CPUIIMR -- rlxfw says 007E0FFE"
rd X10-TPD   0xB8010020 "CPUTPDCR0 -- rlxfw says tpdcr0_pos A15B8044"
rd X10-TXD0  0xA15B8040 "TX ring word 0 -- rlxfw says txd0 A15B81D1 (OWN set)"
rd X10-TXD1  0xA15B8044 "TX ring word 1 -- rlxfw says txd1 A15B81E9"

echo; echo "===== X10 DONE ====="
