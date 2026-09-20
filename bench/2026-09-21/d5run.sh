#!/usr/bin/env bash
# D5's runner.  Not a card -- the card is PREDICTIONS-B35-block33.md § 5.
#
# 🔴 THE VERIFICATION SITS AT THE POINT OF USE, NOT THE POINT OF START.
# The first attempt started the server, checked `ss` two seconds later, and
# passed -- and the server died with its parent shell before the board dialled.
# A check taken before the thing it certifies can change is not a check.  So
# every run below re-reads `ss` immediately before the board is told to
# connect, and refuses rather than measuring against nothing.
#
# Usage: d5run.sh <tag> <n> <extra iperf3 args...>
set -o nounset
cd /mnt/c/Users/Key20/Desktop/router-rebuild

TAG=$1; shift
N=$1; shift
EXTRA="$*"

CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0"
OUT=bench/2026-09-21

for i in $(seq 1 "$N"); do
    if ! ss -ltn 2>/dev/null | grep -q '10\.1\.1\.2:5201'; then
        echo "REFUSED $TAG$i: no listener on 10.1.1.2:5201 at the moment of use"
        exit 1
    fi
    $CAP --out "$OUT/$TAG$i" \
         --send "iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 0 -f m $EXTRA" \
         --until 'iperf Done|error|refused|unable' \
         --seconds 60 > /dev/null 2>&1
    B=$(wc -c < "$OUT/$TAG$i.log")
    R=$(tr -d '\r' < "$OUT/$TAG$i.log" | grep -aE 'receiver|sender' | tr '\n' ' ')
    echo "$TAG$i  bytes=$B  $R"
    if [ "$B" -lt 100 ]; then
        echo "  !! short capture -- probing before continuing"
        ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>&1 | tail -2
        exit 2
    fi
done
