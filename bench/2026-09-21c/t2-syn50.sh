#!/bin/sh
# T2 -- fifty refused TCP connection attempts against the board.
#
# Nothing listens on 10.1.1.3:9999, so each attempt is one SYN out and one RST
# back: the BOARD's TCP stack transmits, and no iperf3 exists anywhere in the
# experiment.  This is the pre-registered instrument (`socat`) at the rate one
# process per connection allows; T3 is the same experiment at rate, with its
# instrument change declared in the card.
#
# Prints a count of each outcome so a no-wedge reading cannot be confused with
# a no-traffic reading -- a sweep that sent nothing and a sweep that sent fifty
# would otherwise print the same thing.
set -u
BOARD=10.1.1.3
PORT=9999
N=50
refused=0
other=0
t0=$(date +%s.%N)
i=0
while [ "$i" -lt "$N" ]; do
    if socat -T2 STDIO "TCP:$BOARD:$PORT" < /dev/null > /dev/null 2>&1; then
        other=$((other + 1))
    else
        refused=$((refused + 1))
    fi
    i=$((i + 1))
done
t1=$(date +%s.%N)
echo "T2-SYN50 attempts=$N refused=$refused connected=$other"
echo "T2-SYN50 elapsed_s=$(echo "$t1 - $t0" | bc)"
