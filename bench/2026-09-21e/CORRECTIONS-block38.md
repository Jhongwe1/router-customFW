# CORRECTIONS — block 38, seating 35

Every departure from the frozen card, written after the seating. The card
itself is not edited: `check-predictions` reads its mtime, and repairing even a
typo would destroy that evidence.

`check-predictions bench/2026-09-21e/PREDICTIONS-B40-block38.md` → **43 of 52**.

---

## 1. The nine cells that did not run, one reason each

| cell | why |
|---|---|
| `W5-SW` | 🔴 **`W5` killed the shell.** § 2.8 of the card named this in advance as a reading: `W5-ALIVE` returned the echo of `echo ALIVE-W5` and no output line, which is `NET-75`'s state. No `/proc` read is possible from it. |
| `W5-ACNT` | same |
| `W5-SNMP` | same |
| `W5-PING` | same — and the host-side half was taken off-card as `X18-PING`/`X18-TCPDUMP`, which is where the six-ARP-requests-zero-replies reading comes from |
| `W3-SOCAT` | ⚠️ **Subsumed, not skipped.** `W3` was on the card to remove `iperf3`'s protocol bytes from the wire while the board's `iperf3 -s` still read them. The off-card `Y1` removed **more**: no TCP at all, no listener, and no userspace process on the board — and it wedged. A non-wedge at `W3` could not have refuted anything `Y1` did not already exclude, and a wedge would have said less. |
| `W3-ALIVE` | same |
| `W4-UDP` | ⚠️ **Answered by `Y1`.** `W4`'s question was *does the bulk have to be TCP*; `Y1` is UDP and it wedges. |
| `W4-ALIVE` | same |
| `W4-NIC` | same |

🔴 **What that costs, stated rather than argued**: `W3` and `W4` would have run
with the board's `iperf3 -s` listening, so there is no measurement of *inbound
bulk into a real socket without the `iperf3` protocol*. Nothing in this seating
claims one.

---

## 2. Departures in how a carded cell was run

1. **`W1-IPERF` and `W2-RIPERF` were given a `timeout`.** The card writes
   `qemu-mips-static iperf3 -c …` bare. `W1`'s client hung for **353.56 s**
   after the board went silent — `iperf3` has no total-run timeout — so the
   invocation was killed by hand and `W2` onwards carried `timeout 70`. The
   binary, the arguments and the direction are the card's.
2. **`W0-SRV` redirects to `/dev/null`, not to a file.** The card's first draft
   wrote `> /tmp/isrv.log`; `cardcheck commands` **refused** it before the
   freeze, because `/tmp/isrv.log` is not a declared path in
   `config/rlxfw-initramfs.tsv`. The card as frozen already carries
   `/dev/null`, so this is not a departure — it is recorded because the
   refusal is the reason the cell has no server-side log, and § 3 clause 3's
   two liveness proofs (`ps`, and `/proc/net/tcp` showing `:1451` in state
   `0A`) exist because of it.
3. **`V6-TCPDUMP` and `W5-TCPDUMP` were backgrounded inside the cell's own
   script** so they overlapped the capture they bracket. `-c 200` ends them;
   `V6`'s reached 205 lines, `W5`'s 25.

---

## 3. Off-card work, declared

Everything named `L*`, `S*`, `X*` or `Y*` is off-card. In order:

| prefix | what |
|---|---|
| `S0-catch`, `S1-catch` | the two cold-boot ESC catch windows, one per power press. Deliberately outside the `cells` fence — they precede the card's first cell and the second one precedes nothing at all. |
| `L1`…`L9` | `looprun` uploads. `L1` and `L2` are on the card; `L3`, `L4`, `L6`, `L7`, `L8`, `L9` are the extra boots, each reached by `busybox reboot -f` at no power cost. **`L5` does not exist**: the reboot before it never ran because `W5` had killed the shell, and `S5 rescue rc=1` is that failure. |
| `X1`…`X18` | the host-side and post-state reads around the `W1` and `W2` failures, including the two counted brackets in `notes/nic-driver.md` § 14.4. |
| `Y0`…`Y7` | the UDP ladder and the `tx_mode` A/B. `y5-rateladder.py` is committed beside them. |

🔴 **The off-card work is where the seating's strongest results came from**,
and that is a fact about the card rather than a defect in it: the card was
written to separate `NET-77`'s three candidates, and the first rung refuted one
so hard that the remaining rungs were answerable by a cheaper experiment the
card's author had not thought of.

---

## 4. Instruments that refused, and one that was wrong

1. 🟢 `console-capture` refused a **132-character** `--send` against the
   loader's 128-byte line buffer, before opening the port. The payload was
   split into two cells and re-run.
2. 🟢 `console-capture` refused to overwrite `Y6-NIC`. **That refusal is the
   only reason a stale file was not read as a measurement** — the re-run's
   `grep` printed the previous, aborted run's all-zero dump, and it looked
   exactly like a clean reading. The real post-state is `Y6-NIC2`.
3. 🟢 `y5-rateladder.py`'s pre-probe returned `REFUSED: the board does not
   answer before the ladder starts` rather than producing a table of zeros.
4. 🔴 **Mine**: `env PATH=.:$PATH qemu-mips-static iperf3 …` exits **127**
   under WSL because this host's `PATH` carries Windows paths with spaces.
   Re-run with the binary's full path. The board was never touched by it.

---

## 5. What the seating did not write down anywhere else

* The `V3-ETH4` capture shows `eth4` reporting `RX packets:6 … RX bytes:536`
  and `TX packets:6 … TX bytes:536` **the instant it came up**, before it had
  carried anything — and those are exactly port 3's MIB numbers from `V1-ACNT`,
  which rlxfw's traffic produced. 讀 `NET-46`: the vendor's netdev counters are
  the switch's. **So the vendor driver reports counters for traffic it never
  carried**, which is worth knowing before any future A/B quotes them.
* `seen_iisr` grew a bit in two of the fault states and not in the others:
  `0002320E` in `W1`, `Y1` and `Y4`; `0001320E` in `W2`; plain `0000320E` in
  `Y5` and `Y6`. Bits 16 and 17 are unnamed in this driver's table, like bits
  12 and 13 before them.
