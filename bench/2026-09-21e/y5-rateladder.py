#!/usr/bin/python3
"""Y5 -- the inbound-rate ladder, off-card.

Seating 35 measured three points and they do not separate one variable:

    Y1  1,440 B datagrams,   744 frame/s,  8.6 Mbit/s inbound  -> WEDGE
    Y4    106 B datagrams, 5,806 frame/s,  4.9 Mbit/s inbound  -> WEDGE
    W2     66 B ACKs,      1,023 frame/s,  0.54 Mbit/s inbound -> survived 73 s

Frame size is excluded (Y1 and Y4 differ by 13x and both wedge).  Frame rate
is not the variable either (W2 is above Y1 in frame/s and survives).  What is
left is the inbound BYTE rate, and this walks it at a fixed frame size so the
threshold is a number rather than a bracket.

Method: send 1,400-byte UDP datagrams to a CLOSED port at a held rate for
STEP_S seconds, then probe the board with one ICMP echo.  The first step whose
probe fails is the threshold; the board never recovers, so the ladder ends
itself and the last surviving step is the lower bound.

The probe is the refutation condition: if the board answers after every step
including the highest, the rate hypothesis is refuted on this range and the
variable is something else.
"""
import socket
import subprocess
import sys
import time

BOARD = "10.1.1.3"
PORT = 9999
SRC = "10.1.1.2"
PAYLOAD = b"\x00" * 1400
FRAME_BITS = (1400 + 28 + 14 + 4) * 8      # UDP payload + IP/UDP + Eth + FCS
STEP_S = 8.0
RATES_MBIT = [0.5, 1.0, 2.0, 4.0, 8.0]


def alive():
    r = subprocess.run(
        ["ping", "-I", SRC, "-c", "2", "-W", "2", "-q", BOARD],
        capture_output=True, text=True, encoding="utf-8")
    return r.returncode == 0


def blast(rate_mbit):
    """Send at rate_mbit for STEP_S, paced against the wall clock."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((SRC, 0))
    interval = FRAME_BITS / (rate_mbit * 1e6)
    t0 = time.monotonic()
    n = 0
    while True:
        now = time.monotonic()
        if now - t0 >= STEP_S:
            break
        target = t0 + n * interval
        if target > now:
            time.sleep(target - now)
        try:
            s.sendto(PAYLOAD, (BOARD, PORT))
        except OSError as e:
            print("  send failed: %s" % e)
            break
        n += 1
    s.close()
    dt = time.monotonic() - t0
    return n, dt


def main():
    if not alive():
        print("REFUSED: the board does not answer before the ladder starts")
        return 1
    print("pre-ladder probe: board answers")
    for rate in RATES_MBIT:
        n, dt = blast(rate)
        got = n * FRAME_BITS / dt / 1e6
        ok = alive()
        print("%5.1f Mbit/s requested  %8d frames in %5.2f s  = %5.2f Mbit/s "
              "actual  ->  board %s" % (rate, n, dt, got,
                                        "ANSWERS" if ok else "SILENT"))
        sys.stdout.flush()
        if not ok:
            print("threshold is between the previous step and %.1f Mbit/s"
                  % rate)
            return 0
    print("every step survived -- the rate hypothesis is refuted on "
          "0.5..8 Mbit/s and the variable is something else")
    return 0


if __name__ == "__main__":
    sys.exit(main())
