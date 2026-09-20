#!/usr/bin/env bash
# The bandwidth ladder.  Off-card -- written after the seating's own card was
# frozen, because the card predicted the blocker was NET-61's ring desync and
# the ladder in it REFUTED that: the desync is transient, Delta 1-3, no
# MBUF_RUNOUT, and pings still complete.  What actually stops D5 is a bulk-load
# ingress wedge that leaves the kernel running, measured twice.
#
# THE QUESTION: at what offered rate does it wedge?
# A rung that completes is a throughput number (a floor).  The first rung that
# wedges is the threshold.  Both are worth more than the single D5 figure the
# row asks for, because a number with no threshold beside it cannot say what
# the path does under load.
#
# 🔴 IT STOPS AT THE FIRST WEDGE.  Every wedge costs the operator a cold power
# press, and the information is in the first failure -- climbing past it buys
# nothing and spends a press per rung.
#
# 🔴 THE LISTENER IS RE-CHECKED AT THE POINT OF USE, not at the point of start.
# The first attempt tonight checked it two seconds after starting the server
# and passed; the server then died with its parent shell before the board
# dialled, and the board wedged against nothing.
set -o nounset
cd /mnt/c/Users/Key20/Desktop/router-rebuild

CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0"
OUT=bench/2026-09-21

alive() {
    ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>/dev/null \
        | grep -oE '[0-9]+ received' | grep -oE '^[0-9]+'
}

for RATE in 1M 2M 5M 10M 20M; do
    TAG="F${RATE}"

    if ! ss -ltn 2>/dev/null | grep -q '10\.1\.1\.2:5201'; then
        echo "REFUSED $TAG: no listener at the moment of use"
        exit 1
    fi

    PRE=$(alive)
    if [ "${PRE:-0}" -eq 0 ]; then
        echo "REFUSED $TAG: board already deaf before this rung (pre-ping $PRE/2)"
        exit 1
    fi

    $CAP --out "$OUT/$TAG" \
         --send "iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 0 -f m -R -b $RATE" \
         --until 'iperf Done|error|refused|unable' \
         --seconds 45 > /dev/null 2>&1

    B=$(wc -c < "$OUT/$TAG.log")
    R=$(tr -d '\r' < "$OUT/$TAG.log" | grep -aE 'receiver|sender' | tr '\n' ' ')
    POST=$(alive)
    echo "$TAG  bytes=$B  post-ping=${POST:-0}/2  $R"

    if [ "${POST:-0}" -eq 0 ]; then
        echo "=== WEDGED at $RATE -- the threshold is between the last good rung and this one"
        echo "=== stopping: every further rung costs one cold power press and buys nothing"
        exit 3
    fi
done
echo "=== no rung wedged the board up to 20M"
