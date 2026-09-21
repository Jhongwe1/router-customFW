#!/bin/sh
# T5 -- push bulk host -> board into an ESTABLISHED TCP connection, no iperf3.
#
# This is NET-67's mechanism reproduced without iperf3: the board's stack
# acknowledges inbound data, so the board emits bare TCP ACKs -- the same thing
# the frozen descriptors held at len 82/74/82/74 in seating 31.
#
# 🔴 THE BOUND IS STATED BEFORE THE RUN, in the card at section 4.5.  Nothing on
# the board reads this socket (telnetd cannot allocate a pty: there is no
# /dev/ptmx in config/rlxfw-initramfs.tsv), so the receive window closes after
# roughly one window's worth of data and the ACK stream stops.  T5 is a SHORT
# ACK burst, not a sustained one.  A no-wedge here is weak evidence and the card
# says so.
#
# It reports bytes actually accepted, because "socat exited" and "the board took
# the data" are two different readings and only the second one is the experiment.
set -u
BOARD=10.1.1.3
PORT=9999
SECONDS_CAP=20

# First: is anything listening at all?  If T4's telnetd did not start, this
# degenerates into T1 and must say so rather than be read as a bulk transfer.
if socat -T2 STDIO "TCP:$BOARD:$PORT" < /dev/null > /dev/null 2>&1; then
    echo "T5-BULK precondition=LISTENER-PRESENT"
else
    echo "T5-BULK precondition=REFUSED -- no listener on $BOARD:$PORT"
    echo "T5-BULK verdict=NOT-RUN (this would be a repeat of T1, not a bulk transfer)"
    exit 0
fi

t0=$(date +%s.%N)
bytes=$(timeout "$SECONDS_CAP" socat -u "OPEN:/dev/zero,rdonly" \
        "TCP:$BOARD:$PORT" 2>/dev/null; echo "")
rc=$?
t1=$(date +%s.%N)

# socat -u gives no byte count, so take it from the kernel's own view of the
# socket instead of trusting the tool: count what left this host for the board
# on that port.  Reported as a lower bound, named as one.
echo "T5-BULK socat_rc=$rc elapsed_s=$(echo "$t1 - $t0" | bc)"
echo "T5-BULK note=byte count is taken host-side by tcpdump off-card; socat -u reports none"
