#!/usr/bin/env python3
"""T3 -- thirty seconds of refused TCP connections against the board, at rate.

WHY THIS IS NOT socat
---------------------
The pre-registration in five committed files says `socat`.  `socat` spawns one
process per connection, so on this host it reaches a few hundred connections a
minute, not a second, and T3's whole point is RATE: making the board emit a
sustained stream of small TCP segments with no connection in existence and no
`iperf3` anywhere.  The card declares this substitution in section 4.3, before
the experiment runs, rather than recording it afterwards as a departure.

What it still is: a pure TCP connection opened by the host, with no `iperf3`.
What changes: the tool that opens it.

WHAT IT PRINTS, AND WHY EACH LINE IS THERE
------------------------------------------
A sweep that sent nothing and a sweep that sent thirty thousand would both
print "no wedge".  So this prints the count and the achieved rate, and a run
whose `attempts` is small is a run that did not test what it claims to.

`refused` is the expected outcome for every attempt: nothing listens on the
port.  A `connected` greater than zero means something DOES listen there and
the experiment is not the one described -- it is reported rather than ignored.
"""
import errno
import socket
import sys
import time

BOARD = "10.1.1.3"
PORT = 9999
SRC = "10.1.1.2"
WINDOW_S = 30.0
CONNECT_TIMEOUT_S = 1.0

def main() -> int:
    attempts = refused = connected = other = 0
    errs: dict[str, int] = {}
    t0 = time.monotonic()
    while time.monotonic() - t0 < WINDOW_S:
        attempts += 1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(CONNECT_TIMEOUT_S)
        try:
            s.bind((SRC, 0))
            s.connect((BOARD, PORT))
            connected += 1
        except ConnectionRefusedError:
            refused += 1
        except OSError as e:
            other += 1
            name = errno.errorcode.get(e.errno, str(e.errno))
            errs[name] = errs.get(name, 0) + 1
        finally:
            s.close()
    elapsed = time.monotonic() - t0

    print(f"T3-SYNRATE window_s={WINDOW_S:.1f} elapsed_s={elapsed:.6f}")
    print(f"T3-SYNRATE attempts={attempts} refused={refused} "
          f"connected={connected} other={other}")
    print(f"T3-SYNRATE rate_per_s={attempts / elapsed:.2f}")
    if errs:
        print("T3-SYNRATE other_errors=" +
              " ".join(f"{k}:{v}" for k, v in sorted(errs.items())))
    # Every refused attempt is one RST the board transmitted.  That number is
    # what the card compares against seating 32's 2,450,389 TX frames.
    print(f"T3-SYNRATE board_tx_segments_lower_bound={refused}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
