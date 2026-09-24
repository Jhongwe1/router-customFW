# PREDICTIONS — block 45, seating 40 (where `rlx0` loses the frames it counts as sent)

**declared date 2026-09-25** — **one power press**, the last capture before midnight.
Block 44 (`bench/2026-09-25/PREDICTIONS-B46-block44.md`) ended at 02:49:20 with its `I9`;
this block runs after it, the same night, on the same board, host and attaches.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① Why this block exists, and what it is not.** The owner's decision, 2026-09-25 ~02:1x,
when asked what a new card should target: `rlx0`'s loss, run right after seating B. It is
not a `P2` step — `P2-4`'s bench half closed with block 44 — and `NET-112`'s mechanism is
`R6b`'s, booked and not opened; which gate records this block is the owner's ruling at
closeout. It localizes the **stage** at which frames are lost. It does not find the field
at fault, and it publishes no throughput figure.

**② What tonight already showed** (量, block 44's captures, read only after `iperflog
compare` read AGREE 6 of 6 on its `eth4` control at 02:5x):

* `P1-TR1`: the host's client timed out (rc 124) while the driver's `n_recov_fire` still
  read 0 at `P1-TR1-S1` with every `txd` CPU-owned: a stall with no recovery before it.
* `P1-TR2` … `P1-TS3`: five trials in about a minute, each `unable to connect to server:
  No route to host`, while `n_tx` rose by 3 in each and one recovery fired (during `TR2`):
  the board counted as sent ARP replies the host never received.
* `P1-US1`: `tx_stopped 1` with all four `txd` engine-owned at `-S1` — the other form.
* `P1-NMAP`: 57,296 ports closed and **8,239 filtered** of 65,535 (seating A 6,546,
  `NET-115`): the RSTs for 12.6 % of the ports never reached the host.

The per-trial table is `$FWRE_WORK/rebuild/s110/rlx0trials.sh`'s output. The experiment
design was a subagent's memo, re-read and cut down here; its derivations from committed
captures are 讀 and not yet second-sourced, and § 3 says where each is tested.

**③ The stage chain, and the one premise it rests on.** Every experiment is bracketed by
the same four reads, taken while nothing generates traffic: the driver (`n_tx`, `n_rx`,
`nd_stats`, the recovery counters, `txd` ownership), the board's stack
(`/proc/net/snmp`), the switch (`asicCounter`: the CPU port's receive counters and size
histogram, port 3's output counters and bytes) and the host adapter (sysfs statistics,
the host's `/proc/net/snmp` and `netstat`). 讀 from six committed `asicCounter` readings
(the subagent's derivation): port 3's output equals the CPU port's `CRCAlignErr` −
`JabberErr` − `Drop` exactly, so `CRCAlignErr` counts every frame the CPU port takes in.
**`E1` tests that premise first, and if it fails, every later localization in this block
is void — decided now.** 量 2026-09-25 03:2x: the host adapter is bound to `r8153_ecm`,
and `ethtool -S` reads `no stats available`, so the host side is the generic netdev
counters only.

**④ No vendor boot is planned; a map closes the block anyway.** A missed catch could
autoboot the vendor, so the block ends with a map (`D1-M0`) against block 44's prediction.
Its capture now ends on the prompt (`--until 'map_lines [0-9]+\r\n# '`) and `MB` inserts
`awk 1`, because block 44's `P2-MB0` was refused on a digest whose section lacked only its
final line terminator (`bench/2026-09-25/CORRECTIONS-block44.md` § 2). 量 on all six maps
committed or captured by 2026-09-25: `awk 1` leaves a complete section's digest at
`0927be41…`, turns `P2-M0`'s into it, and a changed byte still changes it.

**⑤ The clock.** `timesyncd` runs again (block 44's `I9`); this block claims no duration,
and what it reads are counts. Its host timestamps may be slewed or stepped.

---

## § 1 The image

`p2q`, block 44's quiet image, unchanged: recipe `a2c56bc8`, `nfjrom` 1,155,072 B
`4972edbadd2655a8…`. `cardnum` re-checks the chain as block 44 did, and `looprun` pins
the digest again before the port opens.

---

## § 2 The press

One press. `D0` before power; then the cold catch, one `looprun` round to rlxfw's shell,
`E1`–`E6` on `rlx0`, the handover to `eth4` and `E10`, the map, and power off.

---

## § 3 Predictions, each with what refutes it

Bracket k is the reads `D1-Nk` (driver), `D1-Sk` (board stack), `D1-Kk` (switch) and
`D1-Hk` (host); `D1-G0`, `D1-G3`, `D1-G4` add the switch's `GDSR0`. Δ is bracket k+1
minus bracket k. The TX chain is Δ`n_tx` → Δ CPU-port `CRCAlignErr` → Δ port-3 output
(U + M + B) → Δ host `rx_packets`; the RX chain is Δ host `tx_packets` → Δ port-3 receive →
Δ CPU-port output → Δ`n_rx`. Brackets 8 and 9, on `eth4`, have no driver read: the board
stack's count stands in for it.

* **E1 — the instrument's positive control** (`D1-ICMP`, 5 sizes × 20). **100 of 100**
  replies; every TX-chain Δ equal (100 + a, with a the board's own ARP frames) and every
  RX-chain Δ equal. The replies are 98, 298, 554, 1,066 and 1,514 B, or 102, 302, 558,
  1,070 and 1,518 B with the FCS (推 the size buckets count the FCS, as port 3's byte
  counter does, `NET-112`), so the CPU port's histogram moves by 65–127 +20, 256–511 +20,
  512–1023 +20, 1024–1518 +40 and 64 +a, and port 3's bytes by 20 × (102 + 302 + 558 +
  1,070 + 1,518) = 20 × 3,550 = **71,000** + 64a. **Refuted by** any two stages differing
  by one frame or more: that counter is not a per-frame count here, and every bracket that
  relies on it is void.
* **E2 — frame length** (`D1-ISZ`, 11 sizes × 20: replies of 60, 61, 62, 63, 263, 276,
  277, 1,511, 1,512, 1,513 and 1,514 B, every residue mod 4; every control before tonight
  used lengths ≡ 2 mod 4). **220 of 220**, the chains equal; the histogram 64 +20, 65–127
  +60, 256–511 +60, 1024–1518 +80; port 3's bytes 20 × (64 + 65 + 66 + 67 + 267 + 280 +
  281 + 1,515 + 1,516 + 1,517 + 1,518) = 20 × 7,156 = **143,120** + 64a. **Refuted by** a
  lost reply at some sizes (the chain says where), or a count in a bucket these lengths
  cannot fill (the engine sent a length it was not given).
* **E3 — many small frames** (`D1-NMAP`, a connect scan of 65,535 ports; each closed port
  costs the board one RST). 推 some thousands filtered (6,546 and 8,239 on the last two
  readings), and 推 — weakly, from two committed pairs read in different cells — the
  shortfall sits between Δ`n_tx` and Δ`CRCAlignErr`: after the driver hands a frame to
  the engine and before the switch takes it in. **Refuted by** the shortfall at another
  stage, or by Δ`n_tx` itself short of the RSTs the board's stack sent (`OutRsts`): then
  the frames never reached the driver.
* **E4 — a stall** (`D1-T`, block 44's `TR` shape). 推 rc 124: four of four connected `TR`
  trials over two nights stalled. At `D1-TN`, after the client's end, `tx_stopped 0`,
  every `txd` CPU-owned and `n_recov_fire` as at `D1-T-S0` (tonight's `TR1` form); ten
  seconds later (`D1-TN2`) the same. **Refuted by** rc 0 — then `E5` and `E6` are healthy
  controls — or by `tx_stopped 1` with the `txd` engine-owned (`US1`'s form).
* **E5 — the mute** (`D1-P1`, 20 × 56 B and 20 × 600 B right after the kill, where `TR2`
  followed `TR1`). 推 fewer than 40 replies, with Δ`n_tx` at least the echo requests the
  driver received: the board sends what the host never gets. The stage whose Δ falls short
  is the reading; the 646 B replies land in 512–1023, which nothing else here fills.
  **Refuted by** 40 of 40.
* **E6 — what ends it.** After the re-arm (`D1-X1`: engine off, arm, engine on), `D1-P2`
  reads 40 of 40 (推 `NET-110`: the mute ended near a recovery); 120 s later `D1-P3` reads
  40 of 40. **Refuted by** fewer, each in its own bracket.
* **E10 — the other driver on the same host path** (after `D1-DOWN`: `eth4` at 10.1.1.4,
  block 44's `P1-ETH4`). `D1-EPING` 4 of 4; `D1-E` rc 0 (量 24 of 24 `eth4` trials over two
  nights); `D1-EP` 40 of 40; the board stack's sent count equal to the switch's and the
  host's. **Refuted by** any loss on `eth4`: then the `rlx0` attribution is not
  driver-specific.
* **The map**: `D1-MB0`'s three gates, block 44's.

**What this block does not establish**: why — it names a stage, not a field; more than one
instance per condition; the frames a recovery discards (bounded by four per fire, never
counted, `NET-113`); what the host adapter drops inside itself (`r8153_ecm` exposes no
tally counters); any throughput figure; the `UR`, `US` and `TS` shapes.

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck`
refuses the verbs. 🔴 Every `--send` is at most 127 characters and carries no `$`.
🔴 `tcpdump` runs with block 44's filter verbatim and never with `-e`. 🔴 No cell touches
the reset button. 🔴 `ifconfig rlx0 down` once, in `D1-DOWN`; `rlx0` is not re-opened in
that boot (`NET-58`). ⚠️ Off-card cells are declared in
`bench/2026-09-25b/CORRECTIONS-block45.md` before they run.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-25b --skip S2,S3,S4 --recipe-override a2c56bc8 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`; never `-s -s`, which would print each flushed entry's address
`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`PRB <ip>` = `for s in 56 600; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 <ip>; done` — no `-q`, so the capture shows which sequence numbers came back
`HC <ip>` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp /proc/net/netstat ; ip -4 neigh show <ip> dev enxfc19286184c9 | awk '{print $NF}'` — the neighbour's state only, never its address
`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — `awk 1` ends the section's last line whether or not the capture did (§ 0 ④); `; true` because `flashmap compare` exits 1 on the expected group-0 `DIFFER`

### Before power

```
CAP --out bench/2026-09-25b/D0-PRE --seconds 3
HOST bench/2026-09-25b/D0-PREC :: ls bench/2026-09-25b/D0-PRE.log bench/2026-09-25b/D0-PRE.timing bench/2026-09-25b/D0-PRE.meta.json && cat bench/2026-09-25b/D0-PRE.meta.json
HOST bench/2026-09-25b/D0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-25b/D0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9
HOST bench/2026-09-25b/D0-H :: HC 10.1.1.3
```

### The press — the catch and the shell

```
CAP --out bench/2026-09-25b/D1-A --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-25b/D1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-25b/D1Q :: LR --cell D1Q QIMG --iterations 1
CAP --out bench/2026-09-25b/D1-PS --send 'ps' --idle 3 --seconds 30
```

### The press — E1 to E6 on `rlx0`

```
HOST& bench/2026-09-25b/D1-TCPD :: timeout 600 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or (arp and arp[6:2] = 1 and arp[18:4] = 0 and arp[22:2] = 0) or (arp and arp[6:2] = 2 and ((arp[8:4] = 0x02524c58 and arp[12:2] = 0x4657) or (arp[8:4] = 0x560a0101 and arp[12:2] = 0x01e8)))'
CAP --out bench/2026-09-25b/D1-N0 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S0 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K0 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H0 :: HC 10.1.1.3
CAP --out bench/2026-09-25b/D1-G0 --send 'sleep 1 ; echo read 0xBB806100 4 >/proc/rtl865x/memory' --idle 3 --seconds 25
HOST bench/2026-09-25b/D1-ICMP :: ICMP 10.1.1.3
CAP --out bench/2026-09-25b/D1-N1 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S1 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K1 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H1 :: HC 10.1.1.3
HOST bench/2026-09-25b/D1-ISZ :: ISZ 10.1.1.3
CAP --out bench/2026-09-25b/D1-N2 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S2 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K2 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H2 :: HC 10.1.1.3
HOST bench/2026-09-25b/D1-NMAP :: timeout 900 nmap -sT -p- -T4 -n --max-retries 1 10.1.1.3
CAP --out bench/2026-09-25b/D1-N3 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S3 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K3 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H3 :: HC 10.1.1.3
CAP --out bench/2026-09-25b/D1-G3 --send 'sleep 1 ; echo read 0xBB806100 4 >/proc/rtl865x/memory' --idle 3 --seconds 25
CAP --out bench/2026-09-25b/D1-T-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/D1T.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat ; cat /proc/rtl819x-nic' --idle 4 --seconds 30
HOST bench/2026-09-25b/D1-T :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-25b/D1-TN --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-TT --send 'cat /proc/net/tcp' --idle 3 --seconds 30
HOST bench/2026-09-25b/D1-TW :: sleep 10
CAP --out bench/2026-09-25b/D1-TN2 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-T-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/D1T.log ; cat /proc/rtl819x-nic' --idle 3 --seconds 40
CAP --out bench/2026-09-25b/D1-N4 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S4 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K4 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H4 :: HC 10.1.1.3
CAP --out bench/2026-09-25b/D1-G4 --send 'sleep 1 ; echo read 0xBB806100 4 >/proc/rtl865x/memory' --idle 3 --seconds 25
HOST bench/2026-09-25b/D1-P1 :: PRB 10.1.1.3
CAP --out bench/2026-09-25b/D1-N5 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S5 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K5 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H5 :: HC 10.1.1.3
CAP --out bench/2026-09-25b/D1-X1 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 20
HOST bench/2026-09-25b/D1-P2 :: PRB 10.1.1.3
CAP --out bench/2026-09-25b/D1-N6 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S6 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K6 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H6 :: HC 10.1.1.3
HOST bench/2026-09-25b/D1-W :: sleep 120
HOST bench/2026-09-25b/D1-P3 :: PRB 10.1.1.3
CAP --out bench/2026-09-25b/D1-N7 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-S7 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K7 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H7 :: HC 10.1.1.3
```

### The press — the handover, E10, the map

```
CAP --out bench/2026-09-25b/D1-DOWN --send 'ifconfig rlx0 down ; cat /proc/interrupts' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-ETH4 --send 'ifconfig eth4 10.1.1.4 up ; ifconfig eth4 ; cat /proc/interrupts' --idle 3 --seconds 40
HOST bench/2026-09-25b/D1-EPING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.4
CAP --out bench/2026-09-25b/D1-S8 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K8 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H8 :: HC 10.1.1.4
CAP --out bench/2026-09-25b/D1-E-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/D1E.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-25b/D1-E :: IPERF -c 10.1.1.4 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-25b/D1-E-S1 --send 'cat /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/D1E.log' --idle 3 --seconds 40
HOST bench/2026-09-25b/D1-EP :: PRB 10.1.1.4
CAP --out bench/2026-09-25b/D1-S9 --send 'cat /proc/net/snmp' --idle 3 --seconds 30
CAP --out bench/2026-09-25b/D1-K9 --send 'sleep 1 ; cat /proc/rtl865x/asicCounter' --until 'CpuEvent' --seconds 40
HOST bench/2026-09-25b/D1-H9 :: HC 10.1.1.4
CAP --out bench/2026-09-25b/D1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-25b/D1-MB0 :: MB bench/2026-09-25b/D1-M0
```

A bracket's reads, written out in every fence above: `D1-Nk` `cat /proc/rtl819x-nic`,
`D1-Sk` `cat /proc/net/snmp`, `D1-Kk` `sleep 1 ; cat /proc/rtl865x/asicCounter` until
`CpuEvent`, `D1-Hk` `HC` for the address in use, and where marked `D1-Gk`, the
`GDSR0` read committed eight times before (`sleep 1 ; echo read 0xBB806100 4
>/proc/rtl865x/memory`). The re-arm string in `D1-X1` is committed 45 times before tonight.

---

## § 6 How the cells are run

**Before any cell** (none of it a cell): block 44's `I9` has run and the keeper and both
attaches are block 44's (one WSL boot); `/usr/bin/python3 tools/check-predictions.py` on
this card reads **`0 of 78 captures came after the prediction, 78 did not`**
(exit 1: nothing is captured yet); and every invocation below once through
`runblock.py … --dry`, each ending `ALL ITEMS DONE`.

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log LOG`,
with LOG `/home/key/fwre-work/rebuild/s110/run-NAME.log`, exactly as block 44's § 6
describes. `NAME?` marks a cell whose non-zero exit is a reading, not a stop.

**The owner's power**: `I-D1a` starts with its catch; the owner is told when it opens and
presses inside its 180 s window, and powers off after `I-D1c`.

One item per line; each line is one argument.

**`I-D0`** — before power: the pre-flight, the address, the host adapter

```run
D0-PRE?
D0-PREC
gate:grep=^  "bytes": 0,$:D0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:D0-PREC
D0-ADDR
gate:grep=inet 10\.1\.1\.2/24:D0-ADDR
D0-ETH?
D0-H
```

**`I-D1a`** — the press: the catch, the flush, one round to the shell, the process table

```run
D1-A
gate:caught:D1-A
D1-FL
gate:grep=\A(?:0\n)+\Z:D1-FL
D1Q
D1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:D1-PS
```

**`I-D1b`** — the press: E1 to E6 on `rlx0`

```run
D1-TCPD
D1-N0
D1-S0
D1-K0
D1-H0
D1-G0
D1-ICMP?
D1-N1
D1-S1
D1-K1
D1-H1
D1-ISZ?
D1-N2
D1-S2
D1-K2
D1-H2
D1-NMAP?
D1-N3
D1-S3
D1-K3
D1-H3
D1-G3
D1-T-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/D1T\.log *$:D1-T-S0
D1-T?
D1-TN
D1-TT
D1-TW
D1-TN2
D1-T-S1
D1-N4
D1-S4
D1-K4
D1-H4
D1-G4
D1-P1?
D1-N5
D1-S5
D1-K5
D1-H5
D1-X1
D1-P2?
D1-N6
D1-S6
D1-K6
D1-H6
D1-W
D1-P3?
D1-N7
D1-S7
D1-K7
D1-H7
```

**`I-D1c`** — the press: the handover, E10, the map; then the owner powers off

```run
D1-DOWN
D1-ETH4
D1-EPING
gate:grep=\b4 packets transmitted, 4 received\b:D1-EPING
D1-S8
D1-K8
D1-H8
D1-E-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/D1E\.log *$:D1-E-S0
D1-E?
D1-E-S1
D1-EP?
D1-S9
D1-K9
D1-H9
D1-M0
gate:until:D1-M0
D1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:D1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:D1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:D1-MB0
```

**What each stop means, decided now** — any stop interrupts the invocation's background
cells, and a repeat is always a new name, declared in
`bench/2026-09-25b/CORRECTIONS-block45.md` before it runs:

* **`D0-PREC`**, **`D0-ADDR`**: as block 44's `Z0-PREC` and `Z1-ADDR`; no power.
* **`gate:caught`** on `D1-A`: the loader was not caught and may have autobooted the
  vendor — power off; the press is lost, and the next card's first map brackets that boot
  before any vendor boot of its own.
* **`D1-FL`'s gate**: the same command once more as `D1-FL2`; a second failure ends the
  press — power off.
* **`D1Q`'s exit**: its artefacts are the reading. If its round reached rlxfw's prompt (its
  `-boot` capture ends at `# `), `I-D1a` continues `--from D1-PS`; if not, power off, and
  the rest is a new card.
* **`D1-PS`'s gate**: the rows are not the shape `D1-T-S0`'s gate reads; `I-D1b` still
  runs, and a refusal at `D1-T-S0` is handled as the next rule says.
* **`D1-T-S0`'s gate**: `I-D1b` continues `--from D1-T-S1`, whose `killall` ends any
  server left; `D1-T` is not run.
* **a `CAP` cell's non-zero exit** (nothing came back — after a stall the shell may be
  gone): `/dev/ttyUSB0` and a command round trip are checked (`CLAUDE.md`, *Environment*);
  if the shell answers, the invocation continues from that cell under a new name; if not,
  power off, and the rest is a new card.
* **`D1-EPING`'s gate**: the `eth4` experiment is void (`NET-54`); `I-D1c` continues
  `--from D1-M0`.
* **`gate:until`** on `D1-M0`: the map did not complete; it is repeated once as `D1-M0B`
  and `D1-MB0B`, whose output must match the same three patterns, applied with `grep -P`;
  a second failure ends the press.
* **a map gate**: a difference — no vendor boot until the owner has read it (none is
  planned); the press ends at power-off as planned.
* **a background cell's exit** never stops a run.

Estimated duration, a guess from block 44's cell times: the catch 200 s, the round ~25 s,
`E1`–`E6` ~7.5 min with `D1-W`'s 120 s, the handover and `E10` ~2.5 min, the map 15 s:
about 14 minutes after the press.

---

```cells
bench/2026-09-25b/D0-PRE
bench/2026-09-25b/D0-PREC
bench/2026-09-25b/D0-ADDR
bench/2026-09-25b/D0-ETH
bench/2026-09-25b/D0-H
bench/2026-09-25b/D1-A
bench/2026-09-25b/D1-FL
bench/2026-09-25b/D1Q
bench/2026-09-25b/D1-PS
bench/2026-09-25b/D1-TCPD
bench/2026-09-25b/D1-N0
bench/2026-09-25b/D1-S0
bench/2026-09-25b/D1-K0
bench/2026-09-25b/D1-H0
bench/2026-09-25b/D1-G0
bench/2026-09-25b/D1-ICMP
bench/2026-09-25b/D1-N1
bench/2026-09-25b/D1-S1
bench/2026-09-25b/D1-K1
bench/2026-09-25b/D1-H1
bench/2026-09-25b/D1-ISZ
bench/2026-09-25b/D1-N2
bench/2026-09-25b/D1-S2
bench/2026-09-25b/D1-K2
bench/2026-09-25b/D1-H2
bench/2026-09-25b/D1-NMAP
bench/2026-09-25b/D1-N3
bench/2026-09-25b/D1-S3
bench/2026-09-25b/D1-K3
bench/2026-09-25b/D1-H3
bench/2026-09-25b/D1-G3
bench/2026-09-25b/D1-T-S0
bench/2026-09-25b/D1-T
bench/2026-09-25b/D1-TN
bench/2026-09-25b/D1-TT
bench/2026-09-25b/D1-TW
bench/2026-09-25b/D1-TN2
bench/2026-09-25b/D1-T-S1
bench/2026-09-25b/D1-N4
bench/2026-09-25b/D1-S4
bench/2026-09-25b/D1-K4
bench/2026-09-25b/D1-H4
bench/2026-09-25b/D1-G4
bench/2026-09-25b/D1-P1
bench/2026-09-25b/D1-N5
bench/2026-09-25b/D1-S5
bench/2026-09-25b/D1-K5
bench/2026-09-25b/D1-H5
bench/2026-09-25b/D1-X1
bench/2026-09-25b/D1-P2
bench/2026-09-25b/D1-N6
bench/2026-09-25b/D1-S6
bench/2026-09-25b/D1-K6
bench/2026-09-25b/D1-H6
bench/2026-09-25b/D1-W
bench/2026-09-25b/D1-P3
bench/2026-09-25b/D1-N7
bench/2026-09-25b/D1-S7
bench/2026-09-25b/D1-K7
bench/2026-09-25b/D1-H7
bench/2026-09-25b/D1-DOWN
bench/2026-09-25b/D1-ETH4
bench/2026-09-25b/D1-EPING
bench/2026-09-25b/D1-S8
bench/2026-09-25b/D1-K8
bench/2026-09-25b/D1-H8
bench/2026-09-25b/D1-E-S0
bench/2026-09-25b/D1-E
bench/2026-09-25b/D1-E-S1
bench/2026-09-25b/D1-EP
bench/2026-09-25b/D1-S9
bench/2026-09-25b/D1-K9
bench/2026-09-25b/D1-H9
bench/2026-09-25b/D1-M0
bench/2026-09-25b/D1-MB0
bench/2026-09-25b/D1Q-r01-ab2
bench/2026-09-25b/D1Q-r01-2a
bench/2026-09-25b/D1Q-r01-boot
```

```cardnum
cells-fence	78	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^bench/2026-09-25b/
declared-date	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md [*][*]declared date 2026-09-25[*][*]
presses-caught	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^CAP -{2}out bench/2026-09-25b/D1-A -{2}esc 180 -{2}esc-period
cap-cells	45	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^CAP -{2}out
host-cells	30	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^HOST&? bench/2026-09-25b/
send-over-127	0	count bench/2026-09-25b/PREDICTIONS-B47-block45.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-25b/PREDICTIONS-B47-block45.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-25b/PREDICTIONS-B47-block45.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-25b/PREDICTIONS-B47-block45.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-25b/PREDICTIONS-B47-block45.md -{2}send '[^']*AUTOBURN
tcpdump-cells	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^HOST& .* tcpdump -n -tt -i enxfc19286184c9 'icmp or [(]arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0[)] or [(]arp and arp\[6:2\] = 2 and [(][(]arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657[)] or [(]arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8[)][)][)]'$
icmp-sizes	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`ICMP <ip>` = `for s in 56 256 512 1024 1472; do 
isz-sizes	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do 
prb-sizes	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`PRB <ip>` = `for s in 56 600; do 
mb-awk	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`MB <cap>` = `.* [|] awk 1 [|] sha256sum 
map-until-prompt	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^CAP -{2}out bench/2026-09-25b/D1-M0 .* -{2}until 'map_lines \[0-9\][+]\\r\\n# '
rearm-cell	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^CAP -{2}out bench/2026-09-25b/D1-X1 -{2}send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic'
A-nmap-filtered	1	count bench/2026-09-25/P1-NMAP.log 8239 filtered tcp ports
A-nmap-closed	1	count bench/2026-09-25/P1-NMAP.log 57296 closed tcp ports
A-tr1-fire0	1	count bench/2026-09-25/P1-TR1-S1.log ^n_recov_fire 0
A-tr2-noroute	1	count bench/2026-09-25/P1-TR2.log No route to host
A-us1-stopped	1	count bench/2026-09-25/P1-US1-S1.log ^tx_stopped 1
A-map-full	3013	size bench/2026-09-25/P3-M0.log
A-map-short	3009	size bench/2026-09-25/P2-M0.log
p2q-nfjrom-bytes	1155072	size /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-nfjrom-sha256	4972edbadd2655a8	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^verdict\tgreen$
p2q-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-manifest-irfs	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^initramfs_manifest_sha256\t51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59$
p2q-record-vmlinux	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-record-nfjrom	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae$
p2q-record-clean	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
runblock-script	21287d2e33c7b8e8	sha256-16 /home/key/fwre-work/rebuild/s109/card/runblock.py
console-capture-1.5	1	count tools/console-capture.py ^TOOL_VERSION = "1[.]5"$
looprun-1.3	1	count tools/looprun.py ^VERSION = "1[.]3"$
cardrun-1.0	1	count tools/cardrun.py ^TOOL_VERSION = "1[.]0"$
```
