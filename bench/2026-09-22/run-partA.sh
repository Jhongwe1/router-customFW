#!/bin/bash
# Part A of block 40, seating 37.  Bring-up and the NET-82 positive control.
#
# Every cell is ON the card this time, including the switch start and the
# interface bring-up.  Seating 36 and seating 13 both carded a `ping` whose
# interface nothing brought up; A1-SW and A2-UP are that defect's fix, and they
# are carded rather than declared off-card.
set -u
cd /mnt/c/Users/Key20/Desktop/router-rebuild
D=bench/2026-09-22
CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400"

say() { echo; echo "===== $* ====="; }
show() { cat -v "$1" | sed 's/\^\[/ESC/g'; }

say "A1-SW  switch start (R6-5's 通電前必做)"
$CAP --out $D/A1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --idle 3 --seconds 30 > /dev/null 2>&1
show $D/A1-SW.log

say "A2-UP  unlock + netdev on + ifconfig rlx0 10.1.1.3 up"
$CAP --out $D/A2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 30 > /dev/null 2>&1
show $D/A2-UP.log

for spec in "A3-PH1 A15B8110 0" "A3-PH2 A15B8128 0" "A3-PH3 DEADBEEF 0" "A3-PH4 A15B8114 0"; do
  set -- $spec
  NAME=$1; W0=$2; IX=$3
  say "$NAME  phtest $W0 $IX"
  $CAP --out $D/$NAME --send "echo phtest $W0 $IX > /proc/rtl819x-nic ; cat /proc/rtl819x-nic" --idle 3 --seconds 30 > /dev/null 2>&1
  grep -aE 'ph_test_cls|ph_test_j|ph_test_seen|mb_ring' $D/$NAME.log | tr -d '\r'
done

say "A4-BASE  the baseline dump"
$CAP --out $D/A4-BASE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30 > /dev/null 2>&1
show $D/A4-BASE.log

say "A5-PING  4/4 or everything below is void"
ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3 > $D/A5-PING.log 2>&1
echo "A5-PING rc=$?"; cat $D/A5-PING.log

say "A6-SW  R6-6's readable half, fifth consecutive reading"
$CAP --out $D/A6-SW --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30 > /dev/null 2>&1
show $D/A6-SW.log

say "PART A DONE"
