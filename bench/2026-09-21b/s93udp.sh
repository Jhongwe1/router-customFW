#!/usr/bin/env bash
# D5's UDP ladder.  Not a card -- the card is PREDICTIONS-B36-block34.md § 5.
#
# WHAT CHANGED FROM bench/2026-09-21/bwladder.sh, AND WHY
#
# 1. UDP, board as RECEIVER (`-u -R`).  讀 iperf_udp.c:55-125 -- the receive
#    path is Nread plus counters plus `return r`; it transmits nothing.  Every
#    wedge in the record had the board transmitting ACKs.
#
# 2. `-l 1400`, never 3.1.3's UDP default of 8192.  ceil((8192+8)/1480) = 6 IP
#    fragments per datagram, which is the measured fragment-ladder failure
#    region (seating 31: 7 ok, 8 ok, 9 FAIL, 10 ok, 14 FAIL).
#
# 3. `-i 1`, never `-i 0`.  With `-i 1` the board prints a receiver line per
#    second as it happens, so a run that wedges still leaves its own number on
#    the console.  iperf3's end-of-test results travel over the TCP control
#    socket AFTER the test and a wedged run never sends them.  Every
#    seating-31 run used `-i 0`.
#
# 4. THREE runs per rung, not one.  D5 asks for "its spread over at least
#    three runs" (PROGRESS.md:128) and a spread needs repeats at ONE offered
#    rate, not one sample at each of several.
#
# 5. 🔴 bwladder.sh stops at the first wedge because "every wedge costs the
#    operator a cold power press".  THAT PREMISE IS NO LONGER TRUE -- the
#    recovery bisection in § 6 runs from the shell.  This script still stops,
#    for the opposite reason: a live wedge is what § 6 needs, and continuing
#    would destroy it.
#
# 6. 🔴 THE LISTENER IS RE-CHECKED AT THE POINT OF USE, not at the point of
#    start (FW-100).  Kept verbatim in spirit from bwladder.sh, which learned
#    it the expensive way.
set -o nounset
cd /mnt/c/Users/Key20/Desktop/router-rebuild

CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0"
OUT=bench/2026-09-21b
RUNS=3

alive() {
    ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>/dev/null \
        | grep -oE '[0-9]+ received' | grep -oE '^[0-9]+'
}

echo "=== s93udp.sh  $(date -Is)"

for RATE in 2M 10M 30M 60M; do
    PRE=$(alive)
    if [ "${PRE:-0}" -eq 0 ]; then
        echo "REFUSED rung $RATE: board already deaf before this rung (pre-ping ${PRE:-0}/2)"
        exit 1
    fi
    echo "--- rung $RATE  pre-ping ${PRE}/2"

    for i in $(seq 1 "$RUNS"); do
        TAG="C-${RATE}-r${i}"

        if ! ss -ltn 2>/dev/null | grep -q '10\.1\.1\.2:5201'; then
            echo "REFUSED $TAG: no listener on 10.1.1.2:5201 at the moment of use"
            exit 1
        fi

        $CAP --out "$OUT/$TAG" \
             --send "iperf3 -c 10.1.1.2 -p 5201 -t 10 -i 1 -f m -u -l 1400 -R -b $RATE" \
             --until 'iperf Done|error|refused|unable' \
             --seconds 45 > /dev/null 2>&1

        B=$(wc -c < "$OUT/$TAG.log")
        R=$(tr -d '\r' < "$OUT/$TAG.log" | grep -aE 'receiver|sender|datagrams' | tr '\n' ' ')
        echo "$TAG  bytes=$B  $R"

        # the driver's own counters bracketing every single run, because the
        # number is VOID if n_tx_stop moved (card § 5.4)
        $CAP --out "$OUT/$TAG-P" --send 'cat /proc/rtl819x-nic' --seconds 20 \
             > /dev/null 2>&1
        S=$(tr -d '\r' < "$OUT/$TAG-P.log" \
            | grep -aE '^(n_tx_stop|tx_stopped|n_xmit_busy|n_tx_wake|n_rx|n_tx|tpdcr0_pos|now_icr) ' \
            | tr '\n' ' ')
        echo "    $S"

        case "$S" in
            *"n_tx_stop 0 "*) : ;;
            *) echo "    !! n_tx_stop is NOT 0 -- this rung's number is VOID (card § 5.4)" ;;
        esac
    done

    POST=$(alive)
    echo "--- rung $RATE  post-ping ${POST:-0}/2"
    if [ "${POST:-0}" -eq 0 ]; then
        echo "=== WEDGED at $RATE"
        echo "=== stopping ON PURPOSE: the recovery bisection in card § 6 needs a"
        echo "=== LIVE wedge, and the next rung would destroy it."
        exit 3
    fi
done
echo "=== no rung wedged the board up to 60M"
