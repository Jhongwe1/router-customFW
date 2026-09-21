#!/bin/bash
# OFF-CARD, declared.  X12-X16 demonstrated a recovery ONCE, on a ring that had
# also had SOFTRST written to it and the engine stopped and restarted twice.
# That is an anecdote.  This is the same sequence on a PRISTINE wedge, from a
# fresh boot, with nothing else written to the engine in between.
#
# WRITTEN BEFORE IT RUNS:
#
#   R1  after the Y5 dose: ping fails, four txd OWN bits set, tx_stopped 1.
#       (If the fresh boot does NOT wedge, everything below is void and that
#       is itself a finding -- B2 and seating 35 both wedged at this dose.)
#   R2  after `engine off; arm; engine on`: ping 4/4, txd OWN bits clear,
#       tx_stopped 0, n_tx_wake 1.
#   R3  🔴 REFUTATION: ping still fails after the sequence -> X15 was the
#       SOFTRST, or the double engine cycle, or luck, and the recovery is not
#       `engine off; arm; engine on`.
#   R4  ⚠️ n_arm_flush must MOVE, or arm did not reach the ring.
#
# Zero power presses: reboot -f is FW-37, 2.407 s.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-21f
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
NB="/usr/bin/python3 tools/netblast.py"
DEV=enxfc19286184c9
say() { echo; echo "===== $* ====="; }
dump() { grep -aE "^txd|^n_tx_stop|^n_tx_wake|^tx_stopped|^nd_stats|^n_tx |^n_irq |^now_icr|^n_arm_flush|^tx_idx" "$1" | tr -d '\r'; }

say "X17-RB  reboot -f"
$CAP --out $D/X17-RB --send 'busybox reboot -f' --esc-after 25 --seconds 45 > /dev/null 2>&1
grep -ac "Reboot Result from Watchdog Timeout" $D/X17-RB.log

say "X17-BOOT  same image, same power-up"
/usr/bin/python3 tools/looprun.py --mode bench --cell X17 \
  --out-dir $D --skip S2,S3,S4 --recipe-override 84385d91 \
  --image /home/key/fwre-work/rebuild/imgwork/s32a/s32a/kroot/rtkload/nfjrom \
  --image-sha256 eee556f46adf9c0623fa3d0a0d4290f244707e4a9d0cdd0abf5ef767d2cd2b85 2>&1 | tail -6

say "X17-UP  switch + rlx0"
$CAP --out $D/X17-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --seconds 25 > /dev/null 2>&1
$CAP --out $D/X17-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --seconds 25 > /dev/null 2>&1
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/X17-P0.log 2>&1
echo "X17-P0 (healthy) rc=$?"; grep -a "packet loss" $D/X17-P0.log

say "X17-WEDGE  Y5's dose on a pristine boot"
$NB blast --target 10.1.1.3 --src 10.1.1.2 --dev $DEV --rates 0.5 --step-s 8 \
    --out $D/X17-WEDGE.json 2>&1 | tee $D/X17-WEDGE.log | tail -3

say "X17-N1  R1: the pristine wedge"
$CAP --out $D/X17-N1 --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
dump $D/X17-N1.log
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/X17-P1.log 2>&1
echo "X17-P1 (wedged) rc=$?"; grep -a "packet loss" $D/X17-P1.log

say "X17-REC  engine off ; arm ; engine on -- ONE cell, no gap"
$CAP --out $D/X17-REC --send 'echo unlock > /proc/rtl819x-nic ; echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 6 --seconds 35 > /dev/null 2>&1
cat -v $D/X17-REC.log | tr -d '\r' | tail -6

say "X17-N2  R2: after the recovery"
$CAP --out $D/X17-N2 --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
dump $D/X17-N2.log
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/X17-P2.log 2>&1
echo "X17-P2 (recovered?) rc=$?"; grep -a "packet loss" $D/X17-P2.log

say "X17-N3  and does it survive a SECOND wedge and a SECOND recovery?"
$NB blast --target 10.1.1.3 --src 10.1.1.2 --dev $DEV --rates 0.5 --step-s 8 \
    --out $D/X17-WEDGE2.json 2>&1 | tail -2
$CAP --out $D/X17-REC2 --send 'echo unlock > /proc/rtl819x-nic ; echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 6 --seconds 35 > /dev/null 2>&1
$CAP --out $D/X17-N3 --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
dump $D/X17-N3.log
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/X17-P3.log 2>&1
echo "X17-P3 rc=$?"; grep -a "packet loss" $D/X17-P3.log

say "X17 DONE"
