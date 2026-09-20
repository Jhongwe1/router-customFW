#!/usr/bin/env bash
# THE WEDGE PROBE.  Off-card, written after the bandwidth ladder refuted its
# own hypothesis by wedging on its FIRST rung (1 Mbit/s, 1.25 MB over 10 s --
# less than half the 2.59 MB the board carried in the run before it, and far
# gentler than the 14-frame ping bursts it handled in the same seating).
#
# So the wedge is not a rate and not a burst size.  This block asks what the
# driver's own counters say ACROSS it.
#
# 🔴 THE ONE IDEA THAT MAKES IT MEASURABLE: background the iperf3 on the board
# so the shell stays free.  The kernel is alive during the wedge -- measured
# twice tonight, the tty echoes the exact bytes sent and nothing else -- so a
# `cat /proc/rtl819x-nic` should still answer while the network is deaf.
# Every previous observation of this fault was opaque because the shell was
# blocked behind a FOREGROUND client.
#
# What each reading can establish:
#   W1 before   -- the baseline
#   W2 during   -- whether n_rx / n_napi_poll / n_dsync are still moving while
#                  the host sees loss.  Moving => the driver is being fed and
#                  the loss is above it.  Frozen => ingress stopped.
#   W3 after    -- whether anything moved at all, and where seen_iisr ended up.
#                  Bit 16 (MBUF_RUNOUT) / bit 17 (PKTHDR_RUNOUT) are sticky.
#   W4 tx       -- n_tx_stop / n_xmit_busy / tx_stopped / n_tx_timeout.
#                  NET-57 makes a stopped queue a DROP, so these are loss
#                  counters and not health counters.
set -o nounset
cd /mnt/c/Users/Key20/Desktop/router-rebuild

CAP="/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0"
OUT=bench/2026-09-21
F='^n_rx |^n_tx |^n_rx_empty|^n_napi_poll|^n_napi_complete|^n_dsync|^dsync_|^seen_iisr|^last_iisr|^n_xmit|^n_tx_stop|^n_tx_wake|^tx_stopped|^n_tx_timeout|^n_skb_fail|^rpdcr0_pos|^rmdcr0_pos|^rx_idx|^tx_idx|^n_irq|^nd_stats|^n_arm_flush|^now_i'

say () { echo "--- $1 ---"; tr -d '\r' < "$OUT/$2.log" | grep -aE "$F" | tr '\n' ' '; echo; }

if ! ss -ltn 2>/dev/null | grep -q '10\.1\.1\.2:5201'; then
    echo "REFUSED: no listener at the moment of use"; exit 1
fi

$CAP --out $OUT/W1-BEFORE --send 'cat /proc/rtl819x-nic' --seconds 20 > /dev/null 2>&1
say "W1 BEFORE" W1-BEFORE

# background it: the '&' is what keeps the shell answering
$CAP --out $OUT/W2-START \
     --send 'iperf3 -c 10.1.1.2 -p 5201 -t 20 -i 0 -f m -R -b 1M > /dev/null 2>&1 &' \
     --seconds 8 > /dev/null 2>&1
echo "W2-START bytes=$(wc -c < $OUT/W2-START.log)"

$CAP --out $OUT/W3-DURING --send 'cat /proc/rtl819x-nic' --seconds 20 > /dev/null 2>&1
say "W3 DURING" W3-DURING
echo "host ping during: $(ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>/dev/null | grep -oE '[0-9]+ received')"

$CAP --out $OUT/W4-AFTER --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
say "W4 AFTER" W4-AFTER
echo "host ping after: $(ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>/dev/null | grep -oE '[0-9]+ received')"

$CAP --out $OUT/W5-LATE --send 'cat /proc/rtl819x-nic' --seconds 25 > /dev/null 2>&1
say "W5 LATE" W5-LATE
echo "host ping late: $(ping -I 10.1.1.2 -c 2 -W 2 -q 10.1.1.3 2>/dev/null | grep -oE '[0-9]+ received')"
echo "host link counters:"; ip -s link show dev enxfc19286184c9 | tail -4
