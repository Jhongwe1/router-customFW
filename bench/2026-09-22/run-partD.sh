#!/bin/bash
# Part D of block 40, seating 37 -- `D5`.
#
# 🔴 THIS RUNNER DEPARTS FROM THE FROZEN CARD IN TWO WAYS AND BOTH ARE
# DECLARED HERE RATHER THAN QUIETLY APPLIED.  The card is not edited; a card
# edited after its captures exist destroys the mtime evidence
# `check-predictions` reads.
#
# DEPARTURE 1 -- the direction is reversed.  The card runs `iperf3 -c` on the
# BOARD, in the foreground.  量 tonight at `C2-IPERF`: that hangs the board's
# only shell behind a client with no total-run timeout (`CORRECTIONS-block38`
# § 2.1 measured 353.56 s), and then nothing can be read -- which is seating
# 31's recorded finding ("讓它可量的是把板子端的 client 放到背景 `&`") arriving
# again in a card I wrote.  The NIC was fine throughout; the instrument was
# not.  So here the BOARD is the server, backgrounded, and the HOST drives:
#   - the board-side command returns immediately and the shell stays usable;
#   - the host side carries `timeout 70`, so a hang costs 70 s and not 6 min;
#   - this is seating 35's `W0-SRV` shape, which did not have this problem.
#
# DEPARTURE 2 -- `recovms` is swept.  The card says it is left at its default
# and that sweeping it is a separate seating.  量 tonight at `B8`: one 8 s /
# 0.5 Mbit/s ladder produces THREE stalls, so at `recovms 1000` the interface
# is out for about a third of the time under load and any throughput figure is
# mostly measuring the detector's own latency.  A figure like that would be
# published as `D5` and read as the path's capacity, which is exactly the
# mistake `NET-85`'s 203 MBytes / 23.3 Mbit/s already made once.  So `D5` is
# taken at BOTH thresholds, and the pair separates the defect from the
# detector.  `n_recov_spurious` is the control on the short one: a threshold
# too short to be a stall detector fires on transients the level test has
# already cleared, and that counter is where it shows.
#
# THE CONTROL ARM comes first: `recover 0`, one run.  Without it, three numbers
# taken with the detector armed say what this driver does and not what the
# detector bought.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-22
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
IPERF=/home/key/fwre-work/iperf3-port/iperf3
K='n_tx |n_rx |n_irq |n_tx_stop|n_tx_wake|tx_stopped|n_recov_arm|n_recov_fire|n_recov_ok|n_recov_wake|n_recov_spurious|n_recov_fail|recov_ms|recov_jiffies|n_xmit_busy|nd_stats|n_ph_chk|n_ph_diff|truncated'

say() { echo; echo "===== $* ====="; }
dumpkeys() { grep -aE "$K" "$1" | tr -d '\r'; }

say "D-SRV  board becomes the server, BACKGROUNDED so the shell stays usable"
$CAP --out $D/D-SRV --send 'iperf3 -s > /dev/null 2>&1 & sleep 3 ; ps' --idle 4 --seconds 40 > /dev/null 2>&1
tr -d '\r' < $D/D-SRV.log | tail -14

run_one() {   # $1 = tag
  local tag=$1
  say "$tag  host drives, timeout 70"
  timeout 70 qemu-mips-static $IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m \
      > $D/$tag.log 2>&1
  echo "$tag rc=$?"
  tail -6 $D/$tag.log
  $CAP --out $D/$tag-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
  dumpkeys $D/$tag-N.log
}

say "D0  THE CONTROL ARM -- detector OFF"
$CAP --out $D/D0-OFF --send 'echo recover 0 > /proc/rtl819x-nic' --idle 3 --seconds 20 > /dev/null 2>&1
run_one D0-CTRL

say "D0-RESCUE  put the board back by hand, so the next arm starts clean"
$CAP --out $D/D0-RESCUE --send 'echo recover 1 > /proc/rtl819x-nic' --idle 3 --seconds 20 > /dev/null 2>&1
tr -d '\r' < $D/D0-RESCUE.log | tail -6

say "D1  detector ON at the DEFAULT threshold, 1000 ms"
for t in D1-R1 D1-R2 D1-R3; do run_one $t; done

say "D2  detector ON at 20 ms -- n_recov_spurious is the control on this"
$CAP --out $D/D2-MS --send 'echo recovms 20 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
grep -aE 'recov_ms|recov_jiffies|n_recov_spurious' $D/D2-MS.log | tr -d '\r'
for t in D2-R1 D2-R2 D2-R3; do run_one $t; done

say "PART D DONE"
