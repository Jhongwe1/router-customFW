#!/bin/bash
# OFF-CARD, declared, and run on the OWNER'S EXPLICIT AUTHORISATION because it
# carries a power-press risk: NET-58 and NET-64 are both "poke the engine"
# operations that hard-hung this board with console 0 bytes.
#
# QUESTION: does CPUICR bit 22 -- SOFTRST, 讀 rtl865xc_asicregs.h:527-548,
# "Re-initialize all descriptors" (SPEC.md NET-38) -- bring the wedged engine
# back?  It decides whether P2's recovery path is one register write or a full
# teardown and re-arm, and the board is in the exact state the question needs.
#
# WRITTEN BEFORE THE WRITE:
#
#  ① txd OWN bits 1111 -> 0000  = the hardware re-initialised.  PRIMARY, and
#    it does not depend on the driver noticing.
#  ② n_tx_wake 0 -> 1           = the driver's ISR level test (:754) saw the
#    level drop and called netif_wake_queue() by itself.
#  ③ ping 4/4                   = the outcome.
#
#  ①&②&③  -> P2's recovery is `detect stall; write SOFTRST`.
#  ① only  -> the hardware half works and the driver must also reset its own
#             indices and wake the queue.  Still decides the build.
#  none    -> SOFTRST excluded, one reading, and NET-38's "re-initialize all
#             descriptors" does not mean this.
#  console silent -> the NET-58/NET-64 class.  Power press.
#
# The written value is the CURRENT CPUICR (C4000000, 量 X10 through the
# vendor's path AND rlxfw's /proc) with bit 22 set: 0xC4400000.  TXCMD and
# RXCMD are deliberately left ON -- turning them off would be a different
# experiment.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9

say() { echo; echo "===== $* ====="; }

say "X12-PRE  the state immediately before the write"
$CAP --out $D/X12-PRE --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
grep -aE "^txd|^n_tx_stop|^n_tx_wake|^tx_stopped|^nd_stats|^n_tx |^n_irq " $D/X12-PRE.log | tr -d '\r'

say "X12-W  CPUICR <- 0xC4400000  (current value | SOFTRST)"
$CAP --out $D/X12-W --send 'echo write 0xB8010000 0xC4400000 > /proc/rtl865x/memory' --idle 4 --seconds 25 > /dev/null 2>&1
echo "bytes: $(wc -c < $D/X12-W.log)"
cat -v $D/X12-W.log | tr -d '\r'

say "X12-R  read back -- does SOFTRST self-clear?"
$CAP --out $D/X12-R --send 'echo read 0xB8010000 4 > /proc/rtl865x/memory' --idle 4 --seconds 25 > /dev/null 2>&1
cat -v $D/X12-R.log | tr -d '\r'

say "X12-N  the three discriminators"
$CAP --out $D/X12-N --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
grep -aE "^txd|^n_tx_stop|^n_tx_wake|^tx_stopped|^nd_stats|^n_tx |^n_irq |^now_icr|^now_iisr" $D/X12-N.log | tr -d '\r'

say "X12-P  ping"
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/X12-P.log 2>&1
echo "rc=$?"; cat $D/X12-P.log

say "X12 DONE"
