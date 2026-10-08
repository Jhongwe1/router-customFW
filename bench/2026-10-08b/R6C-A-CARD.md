# R6C-A — the flash-booted state, read before the take-over is written

**declared date 2026-10-08** · 128th segment · `R6c` (seating A of `R6c-2`'s design) · relaxed process: not frozen.

**Why.** `NET-171`: booted from flash, rlxfw's `rlx0` receives nothing, and the cause (no VLAN
entry, PVID 1 under ingress filtering) is 推 on 37 registers. Before rlxfw takes the VLAN group
over, this card reads what no flash boot has read — the three tables, the ALE run, `QNUMCR`, the
MIB — and asks the one question that could refute the design: do the host's frames reach port 3?

**The state.** The board runs S (recipe `6a11de02`), booted from slot B by `rlxboot` after the
cold power-on of `bench/2026-10-08/V08` (`V09`'s `bootslot judge` PASS), not at the loader
prompt. Nothing has been typed to it since `X-V08u` (2026-10-08T03:02:03+0800, uptime 950.27 s).

**What it may do.** Read only. No power action, no loader, no image upload. Zero `FLW`, `EW`,
`EB`, `AUTOBURN` and `FLR`; the mainline image has no install verb. No PHY read either: a
page-1 `pread` selects the page by writing register 31 (`notes/switch-driver.md` § 10.4).

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`

## Cells

```
CAP --out bench/2026-10-08b/PF --seconds 3
CAP --out bench/2026-10-08b/A01 --send 'cat /proc/uptime' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A02 --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A03 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A04 --send 'cat /proc/net/dev' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A05 --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A06 --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A07 --send 'echo tbl l2 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A08 --send 'echo peek 0xBB804400 14 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A09 --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A10 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
HOST bench/2026-10-08b/H11 :: I=enxfc19286184c9; ip -s link show $I; sudo -n ip neigh flush dev $I; (timeout 12 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; ping -c 3 -W 2 10.1.1.1; echo ping_rc=$?; sleep 6; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08b/A12 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A13 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-10-08b/H14 :: I=enxfc19286184c9; ip -s link show $I; (timeout 40 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; /usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out bench/2026-10-08b/A14 --send 'ping -c 4 10.1.1.2' --until 'packet loss' --seconds 35; echo cap_rc=$?; sleep 5; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08b/A15 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08b/A16 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08b/A17 --send 'cat /proc/uptime' --idle 3 --seconds 20
```

`H14`'s capture writes `A14`; `H11` and `H14` each run the host's `tcpdump` in the background
for their window, and its lines land in the HOST cell's log.

## What each cell decides — written before any of them ran

MIB columns are the `mo` row's order: 0–1 `ifInOctets`, 2 `ifInUcastPkts`, 13 multicast,
14 broadcast, 15 `dot1dTpPortInDiscards`, 16 `etherStatsDropEvents`, 21–22 `ifOutOctets`,
23–25 out unicast, multicast, broadcast (B `rtl865xc_asicregs.h` `OFFSET_*_P0`). Port 3 is
the host's jack; `m6` is the CPU port.

* **`PF`**: the pre-flight with the board on and idle, as in the 127th segment: three
  artefacts, ~3.08 s, 0 bytes.
* **`A01` identifies the boot.** Same boot as `V08`/`V09` iff the uptime is within ±60 s of
  950.27 + (`A01`'s start − 03:02:03). Otherwise the board was reset since and the census is of
  an unidentified boot: stop.
* **`A05`–`A07`**: predicted every VLAN, netif and L2 slot zero (推 from `SWTAA` 0 at the
  latch). Any non-empty VLAN slot refutes the take-over's premise.
* **`A08`**: `PLITIMR`, unread on this path; the take-over verifies it against `07FAC688`
  (the value after `reset full`, `bench/2026-09-28b/I7-SW1`) and refuses on a mismatch, so a
  different value here changes the design before it is written. `FFCR` predicted 0, `MSCR` 1,
  `SWTCR0` `00080000`.
* **`A09`**: `QNUMCR`'s power-on value; no prediction (`NET-161`: a reset leaves it alone).
* **The decisive pair, `A10` → `H11` → `A12`/`A13`** (host → board):
  * (a) port 3's broadcast count grows by the ARP requests `H11`'s `tcpdump` shows the host
    sending, the CPU port's out columns do not move and `rlx0`'s RX stays 0: the frames enter
    the switch and die before the CPU port, and the VLAN group can explain it. If column 15 of
    port 3 grows by the same count, ingress filtering is named by its own counter.
  * (b) port 3's in columns do not grow: the loss is before the switch, at the PHY or MAC, and
    the take-over cannot fix it — the design goes back to `R6c-2`.
  * (c) the CPU port's out columns grow and `rlx0`'s RX stays 0: the frames reach the CPU port
    and the NIC loses them — the take-over cannot fix that either.
  * If `A12`'s port-3 counts are below `A10`'s, the MIB clears on read and `A12` is the delta.
* **`H14`/`A14` → `A15`/`A16`** (board → host): `rlx0`'s TX grows by the board's ARP requests.
  (d) port 3's out columns grow and the host's `tcpdump` shows `who-has 10.1.1.2 tell
  10.1.1.1`: a CPU-sourced frame reaches the wire with no VLAN entry; (e) neither: it does not.
  (d) and (e) both fit the take-over; which one holds is what it must also cover.
* **`A17`** closes the identity bracket: uptime − `A01`'s uptime within ±10 s of the wall-clock
  gap.

## What this card cannot establish

Anything about the fix. The PHY registers (not read). The state after a watchdog reset: this
boot is a cold one. Whether a frame that reaches port 3 is dropped by ingress filtering rather
than by a lookup miss, unless column 15 or 16 says so.

## Closing count (filled after the cells)

Power actions 0 · `FLW` / `EW` / `EB` / non-zero `AUTOBURN` 0 · `FLR` 0 · flash bracket: none
(nothing written, nothing read from flash).
