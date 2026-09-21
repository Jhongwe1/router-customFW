#!/bin/bash
# Part F of block 40, seating 37 -- NET-82's A/B, which the frozen card made
# CONDITIONAL on `n_ph_diff > 0` and which that condition has now met.
#
# 量 at X10-PH: n_ph_diff 281 of n_ph_chk 1555 = 18.1 %, n_ph_bad 0, and the
# first divergence kept whole -- harvesting pkthdr slot 4, ph_mbuf pointed at
# mbuf slot 0 (ph_first_w0 A15B8110 against ph_first_exp A15B8170).  Under the
# 347-frame UDP blast of Part B the same counter read 0 over 732 frames, so the
# effect is LOAD-DEPENDENT and the earlier reading refuted NET-82 only for that
# load.
#
# THE A/B IS RUN IN BOTH ORDERS.  One pair (follow, then index) cannot separate
# "the pointer was right" from "the second run of anything is different" -- the
# board has been wedged and recovered 15 times tonight and its state is not
# obviously stationary.  Four runs, alternating, is the cheapest shape that can
# see an ordering effect at all.
#
# 🔴 THE REFUTATION CONDITION, WRITTEN FIRST: if n_ph_used stays 0 in a
# `phfollow 1` arm, the switch did not take and BOTH arms are the same
# experiment -- every comparison below is void and says nothing about NET-82.
# n_ph_used is incremented only on the branch that returns the FOLLOWED
# address, so it cannot read non-zero for any other reason.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-22
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"
IPERF=/home/key/fwre-work/iperf3-port/iperf3
K='n_tx |n_rx |n_tx_stop|n_recov_fire|n_recov_ok|n_recov_fail|ph_follow|n_ph_chk|n_ph_diff|n_ph_bad|n_ph_used|ph_agree|ph_first|nd_stats|truncated'

say() { echo; echo "===== $* ====="; }
dumpkeys() { grep -aE "$K" "$1" | tr -d '\r'; }

arm() {   # $1 = tag, $2 = 0|1
  local tag=$1 mode=$2
  say "$tag  phfollow $mode"
  $CAP --out $D/$tag-SET --send "echo phfollow $mode > /proc/rtl819x-nic" --idle 3 --seconds 20 > /dev/null 2>&1
  timeout 70 qemu-mips-static $IPERF -c 10.1.1.3 -p 5201 -t 30 -i 10 -f m > $D/$tag.log 2>&1
  echo "$tag rc=$?"
  grep -aE 'sender|receiver|error' $D/$tag.log | tail -4
  $CAP --out $D/$tag-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
  dumpkeys $D/$tag-N.log
}

say "F0-BASE  the state this A/B starts from"
$CAP --out $D/F0-BASE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
dumpkeys $D/F0-BASE.log

arm F1 1
arm F2 0
arm F3 1
arm F4 0

say "PART F DONE"
