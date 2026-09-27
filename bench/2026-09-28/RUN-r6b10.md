# R6b-10 — the regression at `rtl819x-nic` 1.6's default, with no verb typed: the `y` image from the loader prompt

Written 2026-09-27 (segment 115) by the `R6b-10` desk agent, for the main session to type. Not a
frozen card: the owner's rule for `R6b` from today is no freeze, predictions optional, test while
doing. The flash rules are unchanged, and every rule this file relies on is below.

## § 0 What runs, and on what

* **The board**: at a fresh loader prompt — the main session's plan (2026-09-27): after `NET-25`'s
  tenth cold boot and group A, in the same power cycle and the same bench directory, this card, then
  `RUN-armII.md`. Nothing here needs power, the reset button or a cable move. `Y1-ARP` checks that
  the loader answers ARP for 10.1.1.1 before `looprun` uploads anything (`2026-09-27d`'s `A1Q`
  stopped at `looprun`'s own ARP check, S5c).
* **The image**: `r6b10y`, `CONFIG_RTL_819X_SWCORE=y` (`--variant quiet`, the vendor Ethernet tree
  present: mainline's shape), branch `r6b10` (built at `bc3311b`, the same `config/` as the landed
  tip), recipe `1cc05e88`, quiet kernel, quiet `/init` (`_irfs-r6b10`, content-identical to 8b's
  `_irfs-r6b8b`), `rtl819x-nic` 1.6 and `rtl819x-switch` 1.4, built twice byte-identical
  (`r6b10y2`). `nfjrom` `/home/key/fwre-work/rebuild/s115/r6b10/rtk/r6b10y/rlxfw/kroot/rtkload/nfjrom`, 1,171,456 bytes, sha256 `c22a961185da651ffb095cc8975f633b5129ffc2fd15c2bad715cbf16f1cd404`; vmlinux `c4d9eb305cb5f7721fc348f02648e66d666d3b24185e2de0509a7cda68ca9d1c`. ⚠️
  `RLXFW-ID0` cannot tell this image from the `n` image of the same commit (`r6b10n`, the same
  recipe: `FW-99`); `looprun` pins the `nfjrom` by digest before the port opens, and `Y1-MK` refuses
  a boot that printed `RLXFW-SM0=`, which only the `n` image's seam prints.
* **No verb typed**: nothing here types `txlen`, `txoff`, `txrb` or `arm`. The only writes to
  `/proc/rtl819x-nic` before the sweeps are the standard `/init`'s LAN block, cell for cell
  (`config/rlxfw-init.sh`: `unlock`, `netdev on`, then `ifconfig rlx0 10.1.1.3 up`), preceded as
  there by the switch's `unlock i-mean-it` and `start`. `Y2-TX` shows no 1.5/1.6 verb since boot
  (`v15 last - 0 ok 0 refused 0`) and `Y2-NIC`/`Y3-NIC` the boot policy in force
  (`tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1`). No length has a `-SW` cell: block 48's `SF`
  re-armed the ring per length through `arm`, a verb, so here each length's bracket carries the
  previous length's history — the stronger form of the regression for a default.
* **The sweeps are `R6b`'s D2 instrument, not a policy**: `sweep` and `swclear` run at the policy in
  force and change none of it. `Y5-LB`, the loopback map at the default, is the containment gate
  block 48 ran as `W-00`: the wire sweep runs only if it reads clean over all 1,455 lengths. The
  owner's wire bound permits a multi-length wire sweep only at `txlen vendor`, and 1.6 boots there,
  so `Y5-W` needs no verb; at `rlxfw` it would be refused -EPERM.
* **Zero flash writes, zero `FLR`**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; the upload is
  `looprun`'s, which reads `8040D4A0` back as `00000000` (S5b) before it puts the image in RAM and
  reads the staged head back (S6b) before `J 80500000`. The map is bracketed (`Y2-M0`/`Y6-M1`,
  `FLS-30`'s form) and gated to card C's reading of the same flash.
* **Every `--send` is at most 127 characters, every capture has a terminator and a `--seconds` cap**,
  every board cell's `--until` carries the reset banner, and every Linux cell is followed by a gate
  that refuses loader text in it. No Linux cell carries `--esc-after`; the catch is the tail watch a
  line starts when it stops early. The card ends at the loader prompt: `YZ-RB`, `busybox reboot -f`
  (a watchdog bite, `FW-37`) under a catch, `gate:prompt`.

## § 1 What each read is expected to show (推, for reading only)

* `Y1-ARP`: `4 packets transmitted, 4 packets received` (a gate: at least one).
* The boot: `RLXFW-ID0=1CC05E88`; no `RLXFW-SM0=`; `RLXFW-N1=00000000` (the vendor probe disarms the
  engine and resets the core, 63 committed boots).
* `Y2-NIC`: `version rtl819x-nic 1.6` and the boot policy line above; `Y2-SW`: `version
  rtl819x-switch 1.4`, `phyif unlocked 0 ok 0 stored 0 already 0 refused 0 idfail 0 rbfail 0`,
  `n_writes 0`.
* E2, per length (`Y4-<L>`): 20 of 20 with `-w 10`, and in the bracket `JabberErr`, `FragErr` and
  `Drop` Δ 0 at the CPU port, the 512–1023 bucket Δ 0, `n_recov_fire` Δ 0 — blocks 47 and 48 read
  220 of 220 at `txlen vendor` twice each (`NET-128`, `NET-132`). What refutes 1.6's default: any
  length under 20 of 20 or a `j + f + d` ≥ 1 while the liveness gate held.
* `Y5-LB`: `sw done mode loop … rc 0`, `sw scored 1455 bad_a 0 bad_b 0 void 0 skew 0`. `Y5-W`: `sw
  done mode wire from 60 to 1514 probe 60 rc 0`; in `Y5-R0`→`Y5-R1` `j = f = d = 0` and the CPU
  port's `c` = port 3's `o` = 2,910 (two frames a length, `rlx0` down so no stack frame).
* `Y6-TX` (a gate): `v15 last sweep … ok 3 refused 0 … arm15 0` — the two sweeps and `swclear`
  accepted, nothing refused, and `arm15 0`: no behaviour verb was accepted on this boot, because
  only an accepted `txlen`, `txoff` or `txrb` marks the policy dirty and only a dirty arm counts.

## § 2 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-28/ --skip S2,S3,S4 --recipe-override 1cc05e88 --dwell-seconds 2.5 --boot-until 'job control turned off[^#]{1,2}# |Booting[.][.][.]|---RealTek'`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 48's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets ; grep -e '^Icmp:' -e '^Udp:' /proc/net/snmp` — 8b's
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — 60-B frames, the liveness gate: 4 of 4 or the line stops
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — card C's
`YIMG` = `--image /home/key/fwre-work/rebuild/s115/r6b10/rtk/r6b10y/rlxfw/kroot/rtkload/nfjrom --image-sha256 c22a961185da651ffb095cc8975f633b5129ffc2fd15c2bad715cbf16f1cd404`
`PG <s>` = `ping -I enxfc19286184c9 -c 20 -s <s> -i 0.05 -w 10 -q 10.1.1.3` — E2's stimulus at block 45's spacing: 20 requests, a 10-s deadline; `-s` is L − 42

The host, before the board is touched (no console):

```
HOST bench/2026-09-28/Y0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-28/Y0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
```

(1) The ARP check, then the upload and the boot, from the prompt:

```
HOST bench/2026-09-28/Y1-ARP :: sudo -n arping -c 4 -w 6 -I enxfc19286184c9 10.1.1.1 ; ip -4 neigh show 10.1.1.1 dev enxfc19286184c9 ; true
HOST bench/2026-09-28/Y1Q :: LR --cell Y1Q YIMG --iterations 1
HOST bench/2026-09-28/Y1-MK :: grep -a -o -E 'RLXFW-(SM0|SM1|B07|N1|N2|N3|N4|N7|SW1|SW2|SW3|SW4|SW5|SW7|ID0)=[0-9A-F]{8}' bench/2026-09-28/Y1Q-boot.log ; true
```

(2) The opening reads, before any write:

```
CAP --out bench/2026-09-28/Y2-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/Y2-TX --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/Y2-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/Y2-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28/Y2-MB0 :: MB bench/2026-09-28/Y2-M0
CAP --out bench/2026-09-28/Y2-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
```

(3) The LAN, as the standard `/init` brings it up — no policy verb:

```
CAP --out bench/2026-09-28/Y3-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/Y3-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/Y3-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/Y3-LS --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
```

(4) E2's eleven lengths at block 45's spacing, each in its own bracket (`-L` the liveness gate, `-P0`
host read, `-R0` board read, `-H0` host read, `-PG` the stimulus — a reading, a loss does not stop
the line — then `-P1`, `-R1`, `-H1`):

```
HOST bench/2026-09-28/Y4-0060-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0060-P0 :: HP
CAP --out bench/2026-09-28/Y4-0060-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0060-H0 :: HN
HOST bench/2026-09-28/Y4-0060-PG :: PG 18
HOST bench/2026-09-28/Y4-0060-P1 :: HP
CAP --out bench/2026-09-28/Y4-0060-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0060-H1 :: HN
HOST bench/2026-09-28/Y4-0061-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0061-P0 :: HP
CAP --out bench/2026-09-28/Y4-0061-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0061-H0 :: HN
HOST bench/2026-09-28/Y4-0061-PG :: PG 19
HOST bench/2026-09-28/Y4-0061-P1 :: HP
CAP --out bench/2026-09-28/Y4-0061-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0061-H1 :: HN
HOST bench/2026-09-28/Y4-0062-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0062-P0 :: HP
CAP --out bench/2026-09-28/Y4-0062-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0062-H0 :: HN
HOST bench/2026-09-28/Y4-0062-PG :: PG 20
HOST bench/2026-09-28/Y4-0062-P1 :: HP
CAP --out bench/2026-09-28/Y4-0062-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0062-H1 :: HN
HOST bench/2026-09-28/Y4-0063-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0063-P0 :: HP
CAP --out bench/2026-09-28/Y4-0063-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0063-H0 :: HN
HOST bench/2026-09-28/Y4-0063-PG :: PG 21
HOST bench/2026-09-28/Y4-0063-P1 :: HP
CAP --out bench/2026-09-28/Y4-0063-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0063-H1 :: HN
HOST bench/2026-09-28/Y4-0263-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0263-P0 :: HP
CAP --out bench/2026-09-28/Y4-0263-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0263-H0 :: HN
HOST bench/2026-09-28/Y4-0263-PG :: PG 221
HOST bench/2026-09-28/Y4-0263-P1 :: HP
CAP --out bench/2026-09-28/Y4-0263-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0263-H1 :: HN
HOST bench/2026-09-28/Y4-0276-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0276-P0 :: HP
CAP --out bench/2026-09-28/Y4-0276-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0276-H0 :: HN
HOST bench/2026-09-28/Y4-0276-PG :: PG 234
HOST bench/2026-09-28/Y4-0276-P1 :: HP
CAP --out bench/2026-09-28/Y4-0276-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0276-H1 :: HN
HOST bench/2026-09-28/Y4-0277-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-0277-P0 :: HP
CAP --out bench/2026-09-28/Y4-0277-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0277-H0 :: HN
HOST bench/2026-09-28/Y4-0277-PG :: PG 235
HOST bench/2026-09-28/Y4-0277-P1 :: HP
CAP --out bench/2026-09-28/Y4-0277-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-0277-H1 :: HN
HOST bench/2026-09-28/Y4-1511-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-1511-P0 :: HP
CAP --out bench/2026-09-28/Y4-1511-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1511-H0 :: HN
HOST bench/2026-09-28/Y4-1511-PG :: PG 1469
HOST bench/2026-09-28/Y4-1511-P1 :: HP
CAP --out bench/2026-09-28/Y4-1511-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1511-H1 :: HN
HOST bench/2026-09-28/Y4-1512-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-1512-P0 :: HP
CAP --out bench/2026-09-28/Y4-1512-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1512-H0 :: HN
HOST bench/2026-09-28/Y4-1512-PG :: PG 1470
HOST bench/2026-09-28/Y4-1512-P1 :: HP
CAP --out bench/2026-09-28/Y4-1512-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1512-H1 :: HN
HOST bench/2026-09-28/Y4-1513-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-1513-P0 :: HP
CAP --out bench/2026-09-28/Y4-1513-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1513-H0 :: HN
HOST bench/2026-09-28/Y4-1513-PG :: PG 1471
HOST bench/2026-09-28/Y4-1513-P1 :: HP
CAP --out bench/2026-09-28/Y4-1513-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1513-H1 :: HN
HOST bench/2026-09-28/Y4-1514-L :: FL 10.1.1.3 ; PL
HOST bench/2026-09-28/Y4-1514-P0 :: HP
CAP --out bench/2026-09-28/Y4-1514-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1514-H0 :: HN
HOST bench/2026-09-28/Y4-1514-PG :: PG 1472
HOST bench/2026-09-28/Y4-1514-P1 :: HP
CAP --out bench/2026-09-28/Y4-1514-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y4-1514-H1 :: HN
```

(5) The `tx` sweep over every length from 60 to 1,514 on the wire, behind the loopback gate, in one
bracket:

```
CAP --out bench/2026-09-28/Y5-DN --send 'ifconfig rlx0 down ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/Y5-LB --send 'echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-28/Y5-P0 :: HP
CAP --out bench/2026-09-28/Y5-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y5-H0 :: HN
CAP --out bench/2026-09-28/Y5-W --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-28/Y5-P1 :: HP
CAP --out bench/2026-09-28/Y5-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/Y5-H1 :: HN
```

(6) Up again, the reads, the map closed, and back to the loader (`busybox reboot -f`, a watchdog
bite, `<RealTek>` about 2.4 s later, `FW-37`, under a catch):

```
CAP --out bench/2026-09-28/Y6-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-28/Y6-L :: FL 10.1.1.3 ; PL
CAP --out bench/2026-09-28/Y6-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/Y6-TX --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/Y6-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/Y6-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28/Y6-MB1 :: MB bench/2026-09-28/Y6-M1
CAP --out bench/2026-09-28/Y6-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/YZ-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
```

The tail watches, run only as § 3 says:

```
CAP --out bench/2026-09-28/X-Y1 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
CAP --out bench/2026-09-28/X-Y2 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
```

## § 3 The lines the main session types, from the repository root in WSL

Generated with the cells above from one list (`s31-runsheets.py`), each dry-run through
`tools/cardrun.py --dry`. Every line script takes the night's bench directory as its first argument and refuses
without it, or if it is not `bench/<YYYY-MM-DD[x]>`, or if the directory does not exist. It then,
before the port is opened: instantiates this card for that directory in
`/home/key/fwre-work/rebuild/s115/run10/<dir>/` — the master's cell paths name the directory
`bench/2026-09-27d`, and that string with its slash alone is rewritten, the count checked, and a
later line refuses a copy that differs from its own instantiation; dry-runs its items through
`tools/cardrun.py --dry`; and refuses if any cell it will write, its tail watch included, already has
a record in the directory (another group's cells share it). `--dry` as a second argument stops there.
A board line refuses while any console capture runs. A line that ends with its reboot's
`gate:prompt` held leaves the board at the loader prompt and starts no watch; a line that stops
earlier starts its tail watch (under a SIGINT shim, ended by `stopwatch.sh <dir> X-…`), and so
does `n-line1`, which ends in Linux by design. Exit codes go to `run10/<dir>/rc.tsv`.

```text
# PowerShell tool, working directory C:\Users\Key20\Desktop\router-rebuild (WSL starts
# in the repository root, which every line requires).  bench/2026-09-28 stands for the
# night's directory -- the one group A wrote into; it must exist.  A '# bg' line runs
# with run_in_background; its transcript is run10/2026-09-28/<line>.log and its exit
# code run10/2026-09-28/rc.tsv, both under /home/key/fwre-work/rebuild/s115/.
# optional, any time before (no port, no packet): the pre-flight alone
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/y-line0.sh bench/2026-09-28 --dry
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/y-line1.sh bench/2026-09-28 --dry
# at the loader prompt group A left:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/y-line0.sh bench/2026-09-28
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/y-line1.sh bench/2026-09-28        # bg; ends at the loader prompt, no watch
# only if y-line1 exits non-zero (it then leaves the watch X-Y1 running), per the stop rules:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/stopwatch.sh bench/2026-09-28 X-Y1
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/y-line2.sh bench/2026-09-28        # bg; the reboot alone
```

**Stop rules.**

* **`Y1-ARP` fails** (no ARP reply from 10.1.1.1): nothing has been uploaded; the loader's link is
  the question (`FL`, the cable, the prompt). `stopwatch.sh <dir> X-Y1` (the line started it); the
  board is at the prompt. Stop.
* **`Y1Q` fails** (any `looprun` stage — S5c's ARP, S5b's `AUTOBURN` read): nothing was uploaded
  unless S6 ran; read `Y1Q.log`. A `Y1Q-boot.log` ending on the banner is a reset during the first
  boot: `X-Y1` is the catch. `stopwatch.sh <dir> X-Y1`, then stop; the run is the owner's to re-plan.
* **`Y1-MK` fails**: the booted image is not `r6b10y` (an `SM0` line, another `ID0`) or `N1` has bit
  31 or 30 set. `stopwatch.sh <dir> X-Y1`, then `y-line2.sh <dir>`.
* **`Y2-*` fails on the version, the policy or `v15`**: the image is not 1.6 at its default, and
  nothing after it means anything. `stopwatch.sh <dir> X-Y1`, then `y-line2.sh <dir>`.
* **A liveness gate fails** (`Y4-<L>-L`, `Y6-L`: `PL` under 4 of 4): the host does not reach the
  board (`NET-124` 殘留); the brackets after it would test nothing. `stopwatch.sh <dir> X-Y1`; read
  `Y3-LS` and the last `-H1`; then `y-line2.sh <dir>`.
* **`Y5-LB` fails** (any bad length, or `rc` other than 0): the default is not clean in loopback, and
  the wire sweep does not run (containment). `stopwatch.sh <dir> X-Y1`, then `y-line2.sh <dir>`; the
  map is the reading.
* **A map gate fails** (`Y2-MB0`, `Y6-MB1`, `Y2-NW0`, `Y6-NW1`): stop for the owner before anything
  else is typed (`R6b`'s stop-loss) — not even `y-line2.sh`.
* **Any other gate stops the line with the board in Linux**: `stopwatch.sh <dir> X-Y1`, then
  `y-line2.sh <dir>`.

## § 4 What this run does not establish

It reads 1.6's default on one boot of the `y` image: `D2`'s E2 conjunct and its sweep conjunct at
the policy a boot starts in, without the 1.4 arm beside it — `D2`'s own clause asks for 1.4's
setting reproducing the loss on the same boot, and this run types no verb, so it is a regression of
the default and not a third `D2` boot. The wire sweep is one bracket: a `j + f + d` ≥ 1 there is not
placed at a length by it (block 48's quarters, `W-1a`…`W-1d`, are the form that places one). It
says nothing about the `n` image, arm II or D8; nothing about TCP (`D3`) or time under load (`D4`);
nothing about a length it did not send. The flash beyond the map's windows is not read.
