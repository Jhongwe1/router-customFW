# R6b-8 8e/8f — arm I: `rtl819x-switch` 1.5's `init`, typed by the standard `/init`, on its own boots from the board's cold power-on and a warm reboot

Written 2026-09-28 (segment 116) by the arm I desk agent, for the main session to type. Not a frozen
card: the owner's rule for `R6b` is no freeze, predictions optional, test while doing. The flash
rules are unchanged, and every rule this file relies on is below. Generated with its line scripts
from one list of cells by `gen-armI.py` (`/home/key/fwre-work/rebuild/s116/run-armI`), modelled on arm II's `s31-runsheets.py`.

## § 0 What runs, and on what

* **The seating**: one power cycle. The owner powers the board on once (the cold catch) and off
  once (at the end, the board at its loader prompt). Nothing else is physical: no button, no
  cable, no LED to report. Two boots of the image (ruling 9): after the cold power-on, and after
  `busybox reboot -f` (a watchdog bite, `FW-37`) and a catch.
* **The image**: `r6b8i` — `CONFIG_RTL_819X_SWCORE=n`, `rtl819x-switch` 1.5, `rtl819x-view` 1.1,
  `rtl819x-nic` 1.6 at its default, the standard `/init` typing `init` between `unlock i-mean-it`
  and `start` (ruling 8). `nfjrom` `/home/key/fwre-work/rebuild/s116/rtk/r6b8i/rlxfw/kroot/rtkload/nfjrom`, 1,114,112 bytes, sha256 `539b29b2d7a5ea761855a7a85fc7f051c573701e59abe64bb6f3b398413f7488`; vmlinux
  `b89bd21a3db323e9ce089b14786847127c0ddb97045e6b937df471fd7564883c`; recipe `3685a3a4`. Every value here is `fill-armI.py`'s, read from the build's
  manifest, its `rtkimage` record and its initramfs manifest; `looprun` pins the `nfjrom` by
  digest before the port opens and S8 compares the boot's `RLXFW-ID0` with the recipe; the `/proc`
  route is `recipe_id` on each boot's `NW` read. `RLXFW-ID0` cannot tell images of one `config/`
  apart (`FW-99`): the `nfjrom` digest, the seam's `RLXFW-SM0=` (the `n` image only) and the
  `lan up` line (the standard `/init` only) do.
* **What passes** (ruling 9), per boot, read by `armI-verdict.py` into `I2-V` and `I5-V`: `RLXFW-ID0`
  the build's (the tool compares); `/init`'s `rlxfw: lan up` with no verb typed (the boot capture's
  one send is `J 80500000`); the switch page's `init` line ok with five stored and no failure
  (`init calls 1 ok 1 refused 0 rc 0 stored 1F on 1F`, each `phyifN` `rc 0 st 1`, `rb` = `pre` \| 1);
  host → board 4 of 4 at 18(46) B and at 56(84) B; board → host 4 of 4; the host's neighbour
  entry `REACHABLE` at rlxfw's locally administered address, compared by script and never printed.
  It fails on no ping either way with `init` ok. A failed ping is a reading, never a stop: the
  reads after it are `NET-54` 殘留's and `NET-124` 殘留's set, taken before any recovery (the sheet
  types none). Stop-loss (the `R6b-8` row): two seatings with arm I failing end `D8` ⊘.
* **No verb typed before the pings.** Between `J` and ruling 9's pings the board is sent three
  `cat`s (`I2-SW`, `I2-TX`, `I2-NIC0`) and nothing else; the host flushes its entry. The MIB needs
  a verb (`echo mib`), so arm II's four-counter reads ride a second set of pings (`I3`/`I6`) right
  after; the pass bracket keeps the two-counter half (host ↔ `n_rx`/`n_tx`, `NIC0` → `NIC1`).
* **The boot and its pings are one line**, so no watch sends ESC into the shell between them;
  the line boundaries are in Linux after each boot's reads, where the main session reads the
  verdict and a watch holds the console (arm II's `n-line1` pattern). The loader prompt is never
  a boundary except at the end (`NET-165`: never unattended).
* **Carried items** (the `R6b-8` row): `NET-30` 殘留 — `DW BB804134 1` as the first command at
  each caught prompt and again after `IPCONFIG`, gated on `LDR-07`'s reply (four words to a line,
  `ceil(N/4)` lines, the first at the address given); the kernel side is the boot's `RLXFW-SW7=`.
  The row's third read, after the TFTP upload, is not here: `looprun` has no stop between S6b and
  S7. `NET-124` 殘留 and `NET-54` 殘留 — the host kernel-log follower from before the attach
  (`dmesg-follow.sh`), the port-3 link state (`psrp3` on the first switch page), and at a liveness
  failure the switch page, the MIB and the MDIO page before any recovery, which every boot reads.
  `C-19` — named here: `I0-C19`/`I3-C19`/`I6-C19`/`IZ-C19` count `USB disconnect`, `cp210x` and
  `ttyUSB` lines in the follower's log; the record states every console drop and every idle over a
  minute, with the idle before it.
* **The off-D8 tail** (line 3, boot 2 only, after every `D8` cell and every read): ruling 6's guard
  shown refusing (`reset full` while `CPUICR` has `TXCMD`/`RXCMD`) and then permitting (after
  `ifconfig rlx0 down ; echo disarm`), group A's `AR-DN` order; `reset full`, not `reset vendor`:
  `FULL_RST` alone from the loader's `MEMCR` `7F7F` (`NET-33` 殘留 ②'s after-reset half), with
  `PSRP0`–`4` read after rlxfw's reset (`NET-31` 殘留). Its writes: `reset full` ×2 (one refused
  before any write), `ifconfig rlx0 down`, `disarm`; no `unlock` is typed (`I7-SW0` gates on the
  `unlocked 1` the standard `/init` leaves).
* **Zero flash writes, zero `FLR`**: § 5 counts every string the card sends. The upload is
  `looprun`'s: S5b reads `8040D4A0` back as `00000000` before S6 puts the image in RAM, S6b reads
  the staged head before `J 80500000`. The map is bracketed (`I3-M0` → `I6-M1`) and gated.
* **Every `--send` is at most 127 characters** (86 sends, the longest 83), every
  capture has a terminator and a `--seconds` cap, every Linux cell's `--until` carries the reset
  banner and is followed by a gate that refuses loader text in it; no Linux cell carries
  `--esc-after` — a line that stops starts its tail watch at once.

## § 1 What each read is expected to show (推, optional, for reading only)

* The prompt: `PSRP3` `000010E0` (bit 8 0, block 50's cold read) or bit 8 set (the latch); `PCRP0`–`4`
  `nn7F0039`; `CPUICR` `C4000000` (arm II's `M1-DW*`).
* The boot: `RLXFW-SM0=C4000000`, `SM1` and `N1` `04000000`; `RLXFW-SW-INIT=00001F1F` before
  `RLXFW-SW-START`; `rlxfw: lan up, rlx0 10.1.1.3`.
* `I2-SW`: `init calls 1 ok 1 refused 0 rc 0 stored 1F on 1F reset_busy 0`; `phyifN pre nn7F0038 rb
  nn7F0039 rc 0 st 1`; `phyif … stored 5 already 0`; `n_writes 6` (five stores and `start`'s);
  `unlocked 1`; live `PCRP0`–`4` `nn7F0039`, the rest of the page live = slot 0 (S0′).
* The pings 4 of 4 each way and the entry `REACHABLE` (推, from arm II: the one variable arm II
  changed, `EnablePHYIf` on ports 0–4, is what `init` stores). Host tx Δ = `n_rx` Δ and `n_tx` Δ
  = host rx Δ; in `I3`, port 3 and the CPU port agree with them (arm II's 14 = 14).
* `tbl vlan`: slot 8 `00807E3F`, the rest 0; `tbl netif`: slot 0 valid, VID 8 (`M2-VV`, `M2-VN`).
  `tbl l2`: at least the host's and the board's addresses (`NET-37` 殘留's candidate, 未定).
* The 13 words: `QNUMCR` `00001249`, `CSCR` `00000008`, `EEECR` `294A5294`, `IBCR0`–`2` 0,
  `SBFCTR` `000000F4`, `WFQRCRP0`–`4` `00003FFF`, `P5` 0 (group A's L, § 16.2).
* The tail: `I7-C0` `C4000000` → `I7-RF` `cat: write error: Device or resource busy`, `reset_busy 1`,
  `n_reset 0`; `I7-C1` `04000000`; `I7-RS` `n_reset 1`, `n_writes` +1; `I7-SW1` `MEMCR` `00007F00`
  (`NET-33` ② 推), `PSRP0`–`4` bit 12 set again (group A's R), `PCRP0`–`4` `nn7F0038`, the VLAN
  group as `R` of § 16.3.

## § 2 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-28b/ --skip S2,S3,S4 --recipe-override 3685a3a4 --dwell-seconds 2.5 --boot-until 'job control turned off[^#]{1,2}# |Booting[.][.][.]|---RealTek'` — arm II's; the recipe is the build's manifest's
`IMG` = `--image /home/key/fwre-work/rebuild/s116/rtk/r6b8i/rlxfw/kroot/rtkload/nfjrom --image-sha256 539b29b2d7a5ea761855a7a85fc7f051c573701e59abe64bb6f3b398413f7488` — `looprun` pins it before the port opens
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — arm II's; the entry's state only
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets ; grep -e '^Icmp:' -e '^Udp:' /proc/net/snmp` — arm II's
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — arm II's: 18(46) B, 60-B frames
`PD` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 10.1.1.3` — arm II's: 56(84) B
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — arm II's
`ARPL` = `sudo -n arping -c 4 -w 6 -I enxfc19286184c9 10.1.1.1 ; ip -4 neigh show 10.1.1.1 dev enxfc19286184c9 ; true` — arm II's `M1-ARP`, verbatim (the loader's address is synthesised, `56:0a:`…, allowlisted)
`NB` = `/usr/bin/python3 -B /home/key/fwre-work/rebuild/s116/run-armI/armI-nb.py 10.1.1.3 enxfc19286184c9` — the host's entry for the board, its address judged against the driver's `nic_mac` and never printed
`VD <boot>` = `/usr/bin/python3 -B /home/key/fwre-work/rebuild/s116/run-armI/armI-verdict.py bench/2099-12-31 <boot> 3685a3a4` — ruling 9's verdict for one boot
`CARRIER` = `grep -H . /sys/class/net/enxfc19286184c9/carrier /sys/class/net/enxfc19286184c9/carrier_changes /sys/class/net/enxfc19286184c9/operstate ; true` — block 50's
`C19` = `grep -c -E 'USB disconnect|cp210x|ttyUSB' /home/key/fwre-work/rebuild/s116/run-armI/host/dmesg-w.log ; grep -c . /home/key/fwre-work/rebuild/s116/run-armI/host/dmesg-w.log ; true` — two counts; no line of the host's kernel log reaches `bench/`

**Line 0 — before power, the board off (host and pre-flight)**

```
CAP --out bench/2026-09-28b/I0-PRE --seconds 3
HOST bench/2026-09-28b/I0-PREC :: ls bench/2026-09-28b/I0-PRE.log bench/2026-09-28b/I0-PRE.timing bench/2026-09-28b/I0-PRE.meta.json && cat bench/2026-09-28b/I0-PRE.meta.json
HOST bench/2026-09-28b/I0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-28b/I0-LINK :: CARRIER
HOST bench/2026-09-28b/I0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-28b/I0-C19 :: C19
HOST bench/2026-09-28b/I0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s116/run-armI/armI-nb.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s116/run-armI/armI-verdict.py --self-test
HOST bench/2026-09-28b/I0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
```

**Line 1 — the owner's power-on caught; at the cold prompt: `NET-30`'s read, arm II's reads, `IPCONFIG`, `NET-30` again, ARP, `looprun`, boot 1's marks**

```
CAP --out bench/2026-09-28b/I1-CATCH --esc-after 360 --esc-period 0.002 --until '<RealTek>' --seconds 380
CAP --out bench/2026-09-28b/I1-PSA --send 'DW BB804134 1' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I1-DWP --send 'DW BB804100 8' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I1-DWS --send 'DW BB804200 4' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I1-DWC --send 'DW B8010000 16' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I1-IPC --send 'IPCONFIG 10.1.1.1' --until '<RealTek>' --seconds 5
CAP --out bench/2026-09-28b/I1-PSB --send 'DW BB804134 1' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
HOST bench/2026-09-28b/I1-ARP :: ARPL
HOST bench/2026-09-28b/I1Q :: LR --cell I1Q IMG --iterations 1
HOST bench/2026-09-28b/I1-MK :: grep -a -o -E 'RLXFW-(SM0|SM1|B07|N1|N2|N3|N4|SW1|SW2|SW3|SW4|SW5|SW7|ID0|SW-INIT)=[0-9A-F]{8}' bench/2026-09-28b/I1Q-boot.log ; true
HOST bench/2026-09-28b/I1-VT :: grep -a -c -E 'Probing RTL8186|added[.] vid=|peth0' bench/2026-09-28b/I1Q-boot.log ; true
HOST bench/2026-09-28b/I1-UP :: grep -a -c 'rlxfw: lan up, rlx0 10.1.1.3' bench/2026-09-28b/I1Q-boot.log ; true
```

**Line 1 — boot 1, ruling 9's bracket: only `cat`s before the pings**

```
CAP --out bench/2026-09-28b/I2-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I2-TX --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I2-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I2-HP0 :: HP
HOST bench/2026-09-28b/I2-FL :: FL 10.1.1.3
HOST bench/2026-09-28b/I2-PL :: PL
HOST bench/2026-09-28b/I2-PD :: PD
HOST bench/2026-09-28b/I2-NB :: NB
CAP --out bench/2026-09-28b/I2-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28b/I2-NIC1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I2-SN --send 'cat /proc/net/snmp /proc/net/arp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-28b/I2-HN :: HN
HOST bench/2026-09-28b/I2-V :: VD 1
```

**Line 1 — boot 1, the four-counter bracket (the first verbs of the boot)**

```
CAP --out bench/2026-09-28b/I3-VM0 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I3-HP0 :: HP
HOST bench/2026-09-28b/I3-FL :: FL 10.1.1.3
HOST bench/2026-09-28b/I3-PL :: PL
HOST bench/2026-09-28b/I3-PD :: PD
HOST bench/2026-09-28b/I3-NB :: NB
CAP --out bench/2026-09-28b/I3-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28b/I3-VM1 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-NIC1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I3-HN :: HN
```

**Line 1 — boot 1, step 6's reads, `mfgtest`, the map (opening)**

```
CAP --out bench/2026-09-28b/I3-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I3-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-VV --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-VN --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-VL --send 'echo tbl l2 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-QN --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-CS --send 'echo peek 0xBB804048 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-EE --send 'echo peek 0xBB804160 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-IB --send 'echo peek 0xBB804704 3 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-SB --send 'echo peek 0xBB804500 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ0 --send 'echo peek 0xBB8048B0 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ1 --send 'echo peek 0xBB8048BC 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ2 --send 'echo peek 0xBB8048C8 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ3 --send 'echo peek 0xBB8048D4 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ4 --send 'echo peek 0xBB8048E0 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-WQ5 --send 'echo peek 0xBB8048EC 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I3-DEV --send 'cat /proc/net/dev ; ls /proc/rtl865x ; cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28b/I3-MT --send 'cd /tmp && /bin/mfgtest auto 3685a3a4 > mt1.log 2>&1 ; cat /tmp/mt1.log ; cd /' --until '(?: of 9 ok, [0-9]+ FAIL|No check below ran[^\r\n]*|reports a smaller green\.)\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-28b/I3-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28b/I3-MB0 :: MB bench/2026-09-28b/I3-M0
CAP --out bench/2026-09-28b/I3-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I3-C19 :: C19
```

**Line 2 — `busybox reboot -f` caught; at the warm prompt as at the cold one; boot 2**

```
CAP --out bench/2026-09-28b/I4-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
CAP --out bench/2026-09-28b/I4-PSA --send 'DW BB804134 1' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I4-DWP --send 'DW BB804100 8' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I4-DWS --send 'DW BB804200 4' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I4-DWC --send 'DW B8010000 16' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28b/I4-IPC --send 'IPCONFIG 10.1.1.1' --until '<RealTek>' --seconds 5
CAP --out bench/2026-09-28b/I4-PSB --send 'DW BB804134 1' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
HOST bench/2026-09-28b/I4-ARP :: ARPL
HOST bench/2026-09-28b/I4Q :: LR --cell I4Q IMG --iterations 1
HOST bench/2026-09-28b/I4-MK :: grep -a -o -E 'RLXFW-(SM0|SM1|B07|N1|N2|N3|N4|SW1|SW2|SW3|SW4|SW5|SW7|ID0|SW-INIT)=[0-9A-F]{8}' bench/2026-09-28b/I4Q-boot.log ; true
HOST bench/2026-09-28b/I4-VT :: grep -a -c -E 'Probing RTL8186|added[.] vid=|peth0' bench/2026-09-28b/I4Q-boot.log ; true
HOST bench/2026-09-28b/I4-UP :: grep -a -c 'rlxfw: lan up, rlx0 10.1.1.3' bench/2026-09-28b/I4Q-boot.log ; true
```

**Line 2 — boot 2, ruling 9's bracket**

```
CAP --out bench/2026-09-28b/I5-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I5-TX --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I5-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I5-HP0 :: HP
HOST bench/2026-09-28b/I5-FL :: FL 10.1.1.3
HOST bench/2026-09-28b/I5-PL :: PL
HOST bench/2026-09-28b/I5-PD :: PD
HOST bench/2026-09-28b/I5-NB :: NB
CAP --out bench/2026-09-28b/I5-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28b/I5-NIC1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I5-SN --send 'cat /proc/net/snmp /proc/net/arp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-28b/I5-HN :: HN
HOST bench/2026-09-28b/I5-V :: VD 2
```

**Line 2 — boot 2, the four-counter bracket**

```
CAP --out bench/2026-09-28b/I6-VM0 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I6-HP0 :: HP
HOST bench/2026-09-28b/I6-FL :: FL 10.1.1.3
HOST bench/2026-09-28b/I6-PL :: PL
HOST bench/2026-09-28b/I6-PD :: PD
HOST bench/2026-09-28b/I6-NB :: NB
CAP --out bench/2026-09-28b/I6-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28b/I6-VM1 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-NIC1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I6-HN :: HN
```

**Line 2 — boot 2, step 6's reads, `mfgtest`, the map (closing)**

```
CAP --out bench/2026-09-28b/I6-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I6-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-VV --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-VN --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-VL --send 'echo tbl l2 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-QN --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-CS --send 'echo peek 0xBB804048 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-EE --send 'echo peek 0xBB804160 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-IB --send 'echo peek 0xBB804704 3 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-SB --send 'echo peek 0xBB804500 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ0 --send 'echo peek 0xBB8048B0 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ1 --send 'echo peek 0xBB8048BC 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ2 --send 'echo peek 0xBB8048C8 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ3 --send 'echo peek 0xBB8048D4 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ4 --send 'echo peek 0xBB8048E0 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-WQ5 --send 'echo peek 0xBB8048EC 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I6-DEV --send 'cat /proc/net/dev ; ls /proc/rtl865x ; cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28b/I6-MT --send 'cd /tmp && /bin/mfgtest auto 3685a3a4 > mt2.log 2>&1 ; cat /tmp/mt2.log ; cd /' --until '(?: of 9 ok, [0-9]+ FAIL|No check below ran[^\r\n]*|reports a smaller green\.)\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-28b/I6-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28b/I6-MB1 :: MB bench/2026-09-28b/I6-M1
CAP --out bench/2026-09-28b/I6-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28b/I6-C19 :: C19
```

**Line 3 — OFF-D8 TAIL (boot 2 only): ruling 6's guard refusing then permitting; `NET-33` 殘留 ②, `NET-31` 殘留**

```
CAP --out bench/2026-09-28b/I7-SW0 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I7-NIC0 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-C0 --send 'echo peek 0xB8010000 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-RF --send 'echo reset full | cat > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-DN --send 'ifconfig rlx0 down ; echo disarm > /proc/rtl819x-nic' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28b/I7-NIC1 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-C1 --send 'echo peek 0xB8010000 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-RS --send 'echo reset full | cat > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28b/I7-SW1 --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28b/I7-MEM --send 'echo peek 0xBB804234 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
```

**Line 3 (or line 4 alone) — the end: `busybox reboot -f` caught at the prompt**

```
CAP --out bench/2026-09-28b/IZ-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
HOST bench/2026-09-28b/IZ-C19 :: C19
```

## § 3 Cell by cell

Every cell of § 2 in order, with its terminator and why, what it reads, and its gates (the items
the line hands `cardrun`; their count per line: `line0-preflight` 16, `line1-cold` 163, `line2-warm` 161, `line3-tail` 57, `line4-end` 3). "no loader text" is
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))`.

| cell | line | terminator, and why | what is read | gates (a failed gate, or a non-zero exit, stops the line) |
|---|---|---|---|---|
| `I0-PRE` | line0 | `--seconds 3`: the pre-flight's own length | **a reading** (`I0-PRE?`: its exit is recorded, never a stop) — the pre-flight, board off: 0 bytes in ~3.08 s, three artefacts (its exit 1 is a reading) | — |
| `I0-PREC` | line0 | a host command: its own exit ends it | the three artefacts, 0 bytes, 3.0x s | exit 0; `^  "bytes": 0,$`; `^  "duration_s": 3\.[01][0-9]*,$` |
| `I0-ADDR` | line0 | a host command: its own exit ends it | the host's address on the GbE adapter | exit 0; `inet 10\.1\.1\.2/24` |
| `I0-LINK` | line0 | a host command: its own exit ends it | the adapter attached before power, carrier 0 with the board off (`NET-30` 殘留's condition) | exit 0; `/operstate:[a-z]+$` |
| `I0-DMSG` | line0 | a host command: its own exit ends it | exactly one host kernel-log follower, started before the attach (`NET-124` 殘留, `C-19`) | exit 0; `\A1\n\Z` |
| `I0-C19` | line0 | a host command: its own exit ends it | `C-19`'s baseline counts | exit 0 |
| `I0-ST` | line0 | a host command: its own exit ends it | the two host instruments' own controls, before the port is used for the board | exit 0; `^armI-nb self-test: 9 of 9 passed$`; `^armI-verdict self-test: 18 of 18 passed$` |
| `I0-FL` | line0 | a host command: its own exit ends it | no stale entry for the loader or the board | exit 0; `\A(?:0\n)+\Z` |
| `I1-CATCH` | line1 | `--esc-after 360`: ESC every 2 ms for the whole power-on window; `<RealTek>` ends it (`B-CATCH`: 15.4 s after its start); 380 s cap | the cold catch: caught, `C-8`'s one-space line (cold), no watchdog line | exit 0; caught; `ramSize: 32M\n \n`; `\A(?![\s\S]*Reboot Result from Watchdog Timeout)` |
| `I1-PSA` | line1 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `NET-30` 殘留: `PSRP3` (and `PSRP4`-`6`, LDR-07) at the cold prompt, before anything else is typed; bit 8 `LinkDownEventFlag`, read-to-clear | exit 0; until; `^BB804134:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I1-DWP` | line1 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `PITCR`, `PCRP0`-`6` at the prompt: `nn7F0039` before `J` (arm II's `M1-DWP`) | exit 0; until; `^BB804100:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^BB804110:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){2}\Z` |
| `I1-DWS` | line1 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `CVIDR`, `SSIR`, `CRMR`, `BISTCR` (arm II's `M1-DWS`) | exit 0; until; `^BB804200:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I1-DWC` | line1 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `CPUICR` and the loader's CPU ring registers (arm II's `M1-DWC`) | exit 0; until; `^B8010000:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010010:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010020:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010030:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){4}\Z` |
| `I1-IPC` | line1 | the reply's prompt; 0.12 s measured (`X-ARP2`/`X-ARP3`); 5 s cap | the loader's network up: it answers ARP only after `IPCONFIG` (`NET-95`) | exit 0; until; `^Now your Target IP is 10\.1\.1\.1$` |
| `I1-PSB` | line1 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `NET-30` 殘留: `PSRP3` again, after `IPCONFIG` (the row's second read) | exit 0; until; `^BB804134:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I1-ARP` | line1 | a host command: its own exit ends it (`arping -w 6`) | the loader answers ARP for 10.1.1.1 before `looprun` uploads (arm II's `M1-ARP`) | exit 0; `^[0-9]+ packets transmitted, [1-9][0-9]* packets received` |
| `I1Q` | line1 | looprun's own: S7 ends on `--boot-until` (the shell prompt or the banner), 45 s cap | S5 `AUTOBURN 0`/`LOADADDR`/`IPCONFIG`; S5b `DW 8040D4A0 1` must read `00000000`; S5c the host link; S6 TFTP into RAM; S6b `DW 80500000 8` = the file's head; S7 `J 80500000` and the boot; S8 `RLXFW-ID0` = `--recipe-override`, the build's digest; S9 2.5 s | exit 0 |
| `I1-MK` | line1 | a host command: its own exit ends it | the boot's marks: `ID0` (second reader of S8), the seam `SM0`/`SM1`, `N1` bits 31:30 clear, `SW7` (`NET-30`'s kernel side), `SW-INIT` (verdict info) | exit 0; `^RLXFW-ID0=3685A3A4$`; `^RLXFW-SM0=[0-9A-F]{8}$`; `^RLXFW-SM1=[0-3][0-9A-F]{7}$`; `^RLXFW-N1=[0-3][0-9A-F]{7}$` |
| `I1-VT` | line1 | a host command: its own exit ends it | no vendor Ethernet probe in the boot (`SWCORE=n`) | exit 0; `\A0\n\Z` |
| `I1-UP` | line1 | a host command: its own exit ends it | the standard `/init` reached `lan up` (the quiet `/init` never prints it) | exit 0; `\A[1-9][0-9]*\n\Z` |
| `I2-SW` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | the first board command of the boot, a read: 1.5's `init` line, `phyif0`-`4`, `n_writes`, `unlocked`; `psrp3` is the port-3 link (`NET-124`) | exit 0; until; no loader text; `^version rtl819x-switch 1\.5$` |
| `I2-TX` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | no 1.5/1.6 NIC verb accepted or refused since boot | exit 0; until; no loader text; `^v15 last - 0 ok 0 refused 0 ` |
| `I2-NIC0` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | 1.6 at its default policy; `nd_up`; `n_rx`/`n_tx` before the pings | exit 0; until; no loader text; `^version rtl819x-nic 1\.6$`; `^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$` |
| `I2-HP0` | line1 | a host command: its own exit ends it | host rx/tx packets, `Icmp:`/`Udp:` before | exit 0 |
| `I2-FL` | line1 | a host command: its own exit ends it | the host's entry for the board flushed: prints 0 | exit 0; `\A0\n\Z` |
| `I2-PL` | line1 | a host command: its own exit ends it (`-c 4 -W 1`) | **a reading** (`I2-PL?`: its exit is recorded, never a stop) — **ruling 9**: host -> board 4 of 4 at 18(46) B | — |
| `I2-PD` | line1 | a host command: its own exit ends it (`-c 4 -W 1`) | **a reading** (`I2-PD?`: its exit is recorded, never a stop) — **ruling 9**: host -> board 4 of 4 at 56(84) B | — |
| `I2-NB` | line1 | a host command: its own exit ends it | **a reading** (`I2-NB?`: its exit is recorded, never a stop) — **ruling 9**: the host's entry `REACHABLE` at rlxfw's address, compared by `armI-nb.py` against the driver's `nic_mac`, never printed (a refusal is V7's FAIL, not a stop) | — |
| `I2-BP` | line1 | the echo `PING-END` and the prompt; the longest silence is the `sleep 15` after the board's four replies (~12 s), so no `--idle`; 30 s cap | **ruling 9**: board -> host 4 of 4 (this `ping` ignores `-c`; arm II's bound, verbatim) | exit 0; until; no loader text |
| `I2-NIC1` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` after the pings | exit 0; until; no loader text |
| `I2-SN` | line1 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | the board's ICMP counters and ARP table (arm II's `M4-SN`) | exit 0; no loader text |
| `I2-HN` | line1 | a host command: its own exit ends it | host counters after; the entry's state (last field only) | exit 0 |
| `I2-V` | line1 | a host command: its own exit ends it | **a reading** (`I2-V?`: its exit is recorded, never a stop) — **ruling 9's verdict for boot 1**: V1-V7, `PASS`/`FAIL`; a reading, never a stop | — |
| `I3-VM0` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the MIB before (the first verb of the boot, after ruling 9's pings) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I3-NIC0` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` before | exit 0; until; no loader text |
| `I3-HP0` | line1 | a host command: its own exit ends it | host counters before | exit 0 |
| `I3-FL` | line1 | a host command: its own exit ends it | flushed: prints 0 | exit 0; `\A0\n\Z` |
| `I3-PL` | line1 | a host command: its own exit ends it | **a reading** (`I3-PL?`: its exit is recorded, never a stop) — host -> board, 4 at 46 B (a second sample) | — |
| `I3-PD` | line1 | a host command: its own exit ends it | **a reading** (`I3-PD?`: its exit is recorded, never a stop) — host -> board, 4 at 84 B (a second sample) | — |
| `I3-NB` | line1 | a host command: its own exit ends it | **a reading** (`I3-NB?`: its exit is recorded, never a stop) — the entry again (a second sample) | — |
| `I3-BP` | line1 | as the pass bracket's | board -> host (a second sample) | exit 0; until; no loader text |
| `I3-VM1` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the MIB after: port 3 in/out and the CPU port's, arm II's four counters | exit 0; until; no loader text |
| `I3-NIC1` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` after | exit 0; until; no loader text |
| `I3-HN` | line1 | a host command: its own exit ends it | host counters after | exit 0 |
| `I3-SW` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | after the pings: `PCRP0`-`4` live `nn7F0039`; the VLAN group (`VCR0`, `PVCR0`-`4`, `PBVCR0`, `PLITIMR` via `SWTCR`s) live = slot 0; `PSRP0`-`7`, `MACCR`, `FFCR`, `SWTCR0` (`NET-54` 殘留's set); `MEMCR` (`NET-33` 殘留 ②'s before) | exit 0; until; no loader text |
| `I3-MD` | line1 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | the MDIO page (arm II's `M2-MD`) | exit 0; until; no loader text |
| `I3-VV` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the VLAN table (ruling 3: arm I reads it again) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I3-VN` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the netif table (`NET-37` 殘留's path) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I3-VL` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the L2 table, new in view 1.1: its non-zero slots and count line (`NET-37` 殘留) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I3-QN` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `QNUMCR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-CS` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `CSCR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-EE` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `EEECR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-IB` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `IBCR0-2` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-SB` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `SBFCTR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ0` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP0` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ1` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP1` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ2` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP2` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ3` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP3` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ4` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP4` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-WQ5` | line1 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP5` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I3-DEV` | line1 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | `rlx0`'s counters; `/proc/rtl865x` absent (`SWCORE=n`); IRQs (arm II's `M2-DEV`) | exit 0; no loader text |
| `I3-MT` | line1 | the summary line (or the refusal) and the prompt; the run writes to tmpfs and is silent ~27 s (block 23: 26.9 s), so no `--idle`; 90 s cap | `mfgtest auto`, 9 checks, no operator (block 50's form: its lines to tmpfs, `FW-47`); a reading | exit 0; until; no loader text |
| `I3-M0` | line1 | `map_lines N` and the prompt; the traversal is silent ~13 s (arm II's `M2-M0`: 13.9 s); 60 s cap | the flash map, opening the bracket | exit 0; until; no loader text |
| `I3-MB0` | line1 | a host command: its own exit ends it | the map's digest and `flashmap compare`: 31 same, 1 `DIFFER` at 000000 (every map since block 46) | exit 0; `^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$`; `^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$`; `-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$` |
| `I3-NW0` | line1 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | `n_writes 0`; `recipe_id` = the build's (the `/proc` route to the image's id) | exit 0; no loader text; `^n_writes 0$`; `^recipe_id 3685A3A4$` |
| `I3-C19` | line1 | a host command: its own exit ends it | `C-19`: console-adapter events in the host kernel log (counts only) | exit 0 |
| `I4-RB` | line2 | the loader's prompt after the bite (`<RealTek>` ~2.4 s after the send, `FW-37`; `B-RB` 2.55 s); `--esc-after 20` catches it; 40 s cap | boot 1 ends; the warm catch: `C-8`'s watchdog line, ends at `<RealTek>` | exit 0; prompt |
| `I4-PSA` | line2 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `NET-30` 殘留: `PSRP3` (and `PSRP4`-`6`, LDR-07) at the warm prompt, before anything else is typed; bit 8 `LinkDownEventFlag`, read-to-clear | exit 0; until; `^BB804134:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I4-DWP` | line2 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `PITCR`, `PCRP0`-`6` at the prompt: `nn7F0039` before `J` (arm II's `M1-DWP`) | exit 0; until; `^BB804100:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^BB804110:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){2}\Z` |
| `I4-DWS` | line2 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `CVIDR`, `SSIR`, `CRMR`, `BISTCR` (arm II's `M1-DWS`) | exit 0; until; `^BB804200:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I4-DWC` | line2 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `CPUICR` and the loader's CPU ring registers (arm II's `M1-DWC`) | exit 0; until; `^B8010000:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010010:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010020:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `^B8010030:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){4}\Z` |
| `I4-IPC` | line2 | the reply's prompt; 0.12 s measured (`X-ARP2`/`X-ARP3`); 5 s cap | the loader's network up: it answers ARP only after `IPCONFIG` (`NET-95`) | exit 0; until; `^Now your Target IP is 10\.1\.1\.1$` |
| `I4-PSB` | line2 | the loader's reply: the prompt ends it (`RealTek>`); no silence in it (a 71-B reply takes 0.02 s, LDR-40); `--esc-after 10` streams ESC in case the read resets the board, arm II's M1-DW form; 25 s cap | `NET-30` 殘留: `PSRP3` again, after `IPCONFIG` (the row's second read) | exit 0; until; `^BB804134:[ \t]*[0-9A-Fa-f]{8}(?:[ \t]+[0-9A-Fa-f]{8}){3}[ \t]*$`; `\A(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*(?:^[0-9A-Fa-f]{8}:[^\n]*(?:(?!^[0-9A-Fa-f]{8}:)[\s\S])*){1}\Z` |
| `I4-ARP` | line2 | a host command: its own exit ends it (`arping -w 6`) | the loader answers ARP for 10.1.1.1 before `looprun` uploads (arm II's `M1-ARP`) | exit 0; `^[0-9]+ packets transmitted, [1-9][0-9]* packets received` |
| `I4Q` | line2 | looprun's own: S7 ends on `--boot-until` (the shell prompt or the banner), 45 s cap | S5 `AUTOBURN 0`/`LOADADDR`/`IPCONFIG`; S5b `DW 8040D4A0 1` must read `00000000`; S5c the host link; S6 TFTP into RAM; S6b `DW 80500000 8` = the file's head; S7 `J 80500000` and the boot; S8 `RLXFW-ID0` = `--recipe-override`, the build's digest; S9 2.5 s | exit 0 |
| `I4-MK` | line2 | a host command: its own exit ends it | the boot's marks: `ID0` (second reader of S8), the seam `SM0`/`SM1`, `N1` bits 31:30 clear, `SW7` (`NET-30`'s kernel side), `SW-INIT` (verdict info) | exit 0; `^RLXFW-ID0=3685A3A4$`; `^RLXFW-SM0=[0-9A-F]{8}$`; `^RLXFW-SM1=[0-3][0-9A-F]{7}$`; `^RLXFW-N1=[0-3][0-9A-F]{7}$` |
| `I4-VT` | line2 | a host command: its own exit ends it | no vendor Ethernet probe in the boot (`SWCORE=n`) | exit 0; `\A0\n\Z` |
| `I4-UP` | line2 | a host command: its own exit ends it | the standard `/init` reached `lan up` (the quiet `/init` never prints it) | exit 0; `\A[1-9][0-9]*\n\Z` |
| `I5-SW` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | the first board command of the boot, a read: 1.5's `init` line, `phyif0`-`4`, `n_writes`, `unlocked`; `psrp3` is the port-3 link (`NET-124`) | exit 0; until; no loader text; `^version rtl819x-switch 1\.5$` |
| `I5-TX` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | no 1.5/1.6 NIC verb accepted or refused since boot | exit 0; until; no loader text; `^v15 last - 0 ok 0 refused 0 ` |
| `I5-NIC0` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | 1.6 at its default policy; `nd_up`; `n_rx`/`n_tx` before the pings | exit 0; until; no loader text; `^version rtl819x-nic 1\.6$`; `^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$` |
| `I5-HP0` | line2 | a host command: its own exit ends it | host rx/tx packets, `Icmp:`/`Udp:` before | exit 0 |
| `I5-FL` | line2 | a host command: its own exit ends it | the host's entry for the board flushed: prints 0 | exit 0; `\A0\n\Z` |
| `I5-PL` | line2 | a host command: its own exit ends it (`-c 4 -W 1`) | **a reading** (`I5-PL?`: its exit is recorded, never a stop) — **ruling 9**: host -> board 4 of 4 at 18(46) B | — |
| `I5-PD` | line2 | a host command: its own exit ends it (`-c 4 -W 1`) | **a reading** (`I5-PD?`: its exit is recorded, never a stop) — **ruling 9**: host -> board 4 of 4 at 56(84) B | — |
| `I5-NB` | line2 | a host command: its own exit ends it | **a reading** (`I5-NB?`: its exit is recorded, never a stop) — **ruling 9**: the host's entry `REACHABLE` at rlxfw's address, compared by `armI-nb.py` against the driver's `nic_mac`, never printed (a refusal is V7's FAIL, not a stop) | — |
| `I5-BP` | line2 | the echo `PING-END` and the prompt; the longest silence is the `sleep 15` after the board's four replies (~12 s), so no `--idle`; 30 s cap | **ruling 9**: board -> host 4 of 4 (this `ping` ignores `-c`; arm II's bound, verbatim) | exit 0; until; no loader text |
| `I5-NIC1` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` after the pings | exit 0; until; no loader text |
| `I5-SN` | line2 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | the board's ICMP counters and ARP table (arm II's `M4-SN`) | exit 0; no loader text |
| `I5-HN` | line2 | a host command: its own exit ends it | host counters after; the entry's state (last field only) | exit 0 |
| `I5-V` | line2 | a host command: its own exit ends it | **a reading** (`I5-V?`: its exit is recorded, never a stop) — **ruling 9's verdict for boot 2**: V1-V7, `PASS`/`FAIL`; a reading, never a stop | — |
| `I6-VM0` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the MIB before (the first verb of the boot, after ruling 9's pings) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I6-NIC0` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` before | exit 0; until; no loader text |
| `I6-HP0` | line2 | a host command: its own exit ends it | host counters before | exit 0 |
| `I6-FL` | line2 | a host command: its own exit ends it | flushed: prints 0 | exit 0; `\A0\n\Z` |
| `I6-PL` | line2 | a host command: its own exit ends it | **a reading** (`I6-PL?`: its exit is recorded, never a stop) — host -> board, 4 at 46 B (a second sample) | — |
| `I6-PD` | line2 | a host command: its own exit ends it | **a reading** (`I6-PD?`: its exit is recorded, never a stop) — host -> board, 4 at 84 B (a second sample) | — |
| `I6-NB` | line2 | a host command: its own exit ends it | **a reading** (`I6-NB?`: its exit is recorded, never a stop) — the entry again (a second sample) | — |
| `I6-BP` | line2 | as the pass bracket's | board -> host (a second sample) | exit 0; until; no loader text |
| `I6-VM1` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the MIB after: port 3 in/out and the CPU port's, arm II's four counters | exit 0; until; no loader text |
| `I6-NIC1` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | `n_rx`/`n_tx` after | exit 0; until; no loader text |
| `I6-HN` | line2 | a host command: its own exit ends it | host counters after | exit 0 |
| `I6-SW` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | after the pings: `PCRP0`-`4` live `nn7F0039`; the VLAN group (`VCR0`, `PVCR0`-`4`, `PBVCR0`, `PLITIMR` via `SWTCR`s) live = slot 0; `PSRP0`-`7`, `MACCR`, `FFCR`, `SWTCR0` (`NET-54` 殘留's set); `MEMCR` (`NET-33` 殘留 ②'s before) | exit 0; until; no loader text |
| `I6-MD` | line2 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | the MDIO page (arm II's `M2-MD`) | exit 0; until; no loader text |
| `I6-VV` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the VLAN table (ruling 3: arm I reads it again) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I6-VN` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the netif table (`NET-37` 殘留's path) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I6-VL` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | the L2 table, new in view 1.1: its non-zero slots and count line (`NET-37` 殘留) | exit 0; until; no loader text; `^version rtl819x-view 1\.1$` |
| `I6-QN` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `QNUMCR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-CS` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `CSCR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-EE` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `EEECR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-IB` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `IBCR0-2` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-SB` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `SBFCTR` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ0` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP0` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ1` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP1` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ2` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP2` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ3` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP3` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ4` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP4` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-WQ5` | line2 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | `WFQRCRP5` by `peek` (view 1.1 admits it, ruling 7(b)); a refusal is a reading | exit 0; until; no loader text |
| `I6-DEV` | line2 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | `rlx0`'s counters; `/proc/rtl865x` absent (`SWCORE=n`); IRQs (arm II's `M2-DEV`) | exit 0; no loader text |
| `I6-MT` | line2 | the summary line (or the refusal) and the prompt; the run writes to tmpfs and is silent ~27 s (block 23: 26.9 s), so no `--idle`; 90 s cap | `mfgtest auto`, 9 checks, no operator (block 50's form: its lines to tmpfs, `FW-47`); a reading | exit 0; until; no loader text |
| `I6-M1` | line2 | `map_lines N` and the prompt; the traversal is silent ~13 s (arm II's `M2-M0`: 13.9 s); 60 s cap | the flash map, closing the bracket | exit 0; until; no loader text |
| `I6-MB1` | line2 | a host command: its own exit ends it | the map's digest and `flashmap compare`: 31 same, 1 `DIFFER` at 000000 (every map since block 46) | exit 0; `^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$`; `^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$`; `-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$` |
| `I6-NW1` | line2 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | `n_writes 0`; `recipe_id` = the build's (the `/proc` route to the image's id) | exit 0; no loader text; `^n_writes 0$`; `^recipe_id 3685A3A4$` |
| `I6-C19` | line2 | a host command: its own exit ends it | `C-19`: console-adapter events in the host kernel log (counts only) | exit 0 |
| `I7-SW0` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | t1: the premise -- the switch unlocked by `/init` and never relocked, no reset yet; `MEMCR` live (推 `7F7F`), `PSRP0`-`4`, `PCRP0`-`4`, `SSIR`, the VLAN group | exit 0; until; no loader text; `^unlocked 1$`; `^n_reset 0$`; `^init calls [0-9]+ ok [0-9]+ refused [0-9]+ rc -?[0-9]+ stored [0-9A-F]{2} on [0-9A-F]{2} reset_busy 0$` |
| `I7-NIC0` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | t1: the NIC armed, its engine on (`now_icr`, the second instrument for `CPUICR`) | exit 0; until; no loader text; `^armed 1$`; `^engine_on 1$` |
| `I7-C0` | line3 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | t1: `CPUICR` with `TXCMD` or `RXCMD` set (推 `C4000000`), so the guard must refuse | exit 0; until; no loader text; `^peek B8010000 n 1$`; `^last peek j [0-9]+ rc 0$`; `^a B8010000 [4-9A-F][0-9A-F]{7}$` |
| `I7-RF` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too; the refusal's text comes from `cat` (FW-41: no payload residue), before the page | t2: `reset full` while armed REFUSED -EBUSY before any write: `reset_busy` 1, `n_reset` 0 | exit 0; until; no loader text; `^cat: write error: Device or resource busy$`; `^n_reset 0$`; `^init [^\n]* reset_busy 1$` |
| `I7-DN` | line3 | `--idle 3`: the output comes at once and nothing follows it; the banner ends it too | t3: group A's `AR-DN`, verbatim: `ndo_stop` (engine off, NAPI off, IRQ freed), then `disarm` (ring bases 0, `armed` 0; its stores need the NIC unlock `/init` left) | exit 0; no loader text |
| `I7-NIC1` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | t3: disarmed (group A's `AR-NIC` gates) | exit 0; until; no loader text; `^armed 0$`; `^engine_on 0$`; `^nd_up 0$`; `^now_icr [0-3][0-9A-F]{7}$` |
| `I7-C1` | line3 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | t3: `CPUICR` bits 31:30 clear (推 `04000000`): the guard must permit | exit 0; until; no loader text; `^peek B8010000 n 1$`; `^last peek j [0-9]+ rc 0$`; `^a B8010000 [0-3][0-9A-F]{7}$` |
| `I7-RS` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too; the reset's `mdelay(300)` is inside the write, before the page | t4: `reset full` PERMITTED: `n_reset` 1, `SW-RST=00000001` (a mark: read, not gated), `reset_busy` still 1; the page is the first after-reset read | exit 0; until; no loader text; `\A(?![\s\S]*write error)`; `^n_reset 1$`; `^init [^\n]* reset_busy 1$` |
| `I7-SW1` | line3 | the page's last line and the shell prompt; a `cat` has no silence; the banner ends it too | t5: `NET-33` 殘留 ② `MEMCR` after `FULL_RST` from `7F7F` (推 `7F00`); `NET-31` 殘留 `PSRP0`-`4` after rlxfw's reset; `PCRP0`-`4`, `SSIR`, the VLAN group, slot 0 beside live | exit 0; until; no loader text; `^n_reset 1$` |
| `I7-MEM` | line3 | the view page's terminator `jiffies N` and the prompt; the verb and the `cat` print at once; the banner ends it too; `\| cat >` so a refused verb shows its errno and no FW-41 residue | t5: `MEMCR` by the second instrument | exit 0; until; no loader text; `^peek BB804234 n 1$`; `^last peek j [0-9]+ rc 0$`; `^a BB804234 [0-9A-F]{8}$` |
| `IZ-RB` | line3 | the loader's prompt after the bite (`<RealTek>` ~2.4 s after the send, `FW-37`; `B-RB` 2.55 s); `--esc-after 20` catches it; 40 s cap | the end: the board at the loader prompt for the power-off | exit 0; prompt |
| `IZ-C19` | line3 | a host command: its own exit ends it | `C-19`'s closing counts | exit 0 |

## § 4 The lines, the owner, the stops

Each line script takes the seating's bench directory `bench/<YYYY-MM-DD[x]>`, refuses without it or
malformed, and before the port is opened: instantiates this card for it in `/home/key/fwre-work/rebuild/s116/run-armI/run/<dir>/`
(the master's cell paths name the directory `bench/2099-12-31`, and that string with its slash
alone is rewritten, the count checked, and a later line refuses a copy that differs), dry-runs its items
through `tools/cardrun.py --dry`, refuses if any cell it will write or its watch has a record in the
directory, refuses while any console capture runs, and refuses while any of the image's values is
still `fill-armI.py`'s unfilled placeholder. `--dry` as the second argument stops there. `line0` creates the directory if it is today's
and it is before 23:52 (a power cycle's captures belong to its directory's date); every later line
requires it. A line that ends in Linux (`line1`, `line2`) starts its tail watch `X-I<n>` always; a
line that ends on its reboot's `gate:prompt` (`line3`, `line4`) starts none; a line that stops early
starts its watch at once. Exit codes go to `run/<dir>/rc.tsv`.

```text
# PowerShell tool, working directory C:\Users\Key20\Desktop\router-rebuild (WSL starts in the
# repository root, which every line requires).  <D> is the seating's directory: today's date, the first
# free suffix (line0 creates it and refuses another day's).  '# bg' = run_in_background.  Transcripts,
# rc.tsv and the instantiated card: /home/key/fwre-work/rebuild/s116/run-armI/run/<D>/.
# desk, any time before (no port, no packet):
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/items.sh
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line0-preflight.sh bench/<D> --dry          (and line1-cold, line2-warm, line3-tail, line4-end the same)
# before power, in order (PowerShell): the keeper; the host kernel-log follower (bg); usbipd list/attach
wsl -d Ubuntu-24.04 -- sleep 36000                                              # bg
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/dmesg-follow.sh                                  # bg
# the owner has confirmed the board is OFF:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line0-preflight.sh bench/<D>
# say -> stop -> the owner's reply authorises -> then:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line1-cold.sh bench/<D>                                              # bg
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/say.sh bench/<D>        # repeat until it prints SAY; tell the owner exactly that sentence
# line1 ends in Linux and starts the watch X-I1; once it has printed 'watch X-I1 start':
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/stopwatch.sh bench/<D> X-I1
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line2-warm.sh bench/<D>                                              # bg
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/stopwatch.sh bench/<D> X-I2
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line3-tail.sh bench/<D>                                              # bg; ends at the prompt
# -> ask the owner to power off now (NET-165); then:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/dmesg-stop.sh
# only after a line stopped with the board in Linux (per the stop rules): stopwatch.sh <D> X-I<n>, then
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s116/run-armI/line4-end.sh bench/<D>                                               # bg; the reboot alone
```

**The owner's actions, and where the main session stops and waits.**

1. Before `line0`: the owner confirms the board is **off**. Wait for the reply. (The keeper, the
   follower and both `usbipd attach`es — the CP2102 and the GbE adapter, `usbipd list` read fresh
   each time, `attach`'s output read — come before `line0`; the adapter is not touched again.)
2. After `line0` rc 0: tell the owner the catch is about to open and that power-on comes on the
   word "now"; **stop and wait for the reply**. The reply authorises; it is not the action.
3. Start `line1` (background). Run `say.sh` until it prints `SAY` (the catch's `.timing` exists and
   at least 40 s of its window remain); tell the owner that sentence: *"now — power on, at the latest
   HH:MM:SS"* (the catch's start + 350 s). `DO NOT SAY` means the window is too short: tell the owner
   not to power on; `line1` will time out and stop (its watch keeps streaming ESC).
4. Nothing more from the owner until the end: `line1` → `stopwatch X-I1` → `line2` →
   `stopwatch X-I2` → `line3`. Between lines, read the verdict (`I2-V`/`I5-V` in the transcript).
5. When `line3` (or `line4`) prints that the board is at the loader prompt: ask the owner to
   **power off now** and wait for the confirmation (`NET-165`: never unattended at the prompt).
   Then `dmesg-stop.sh`.

**Not in the main line: the checks that need the owner's eye or hand** (8e's "LED, button and
GPIO controls"; none is typed by any line, and each would be a declared off-card cell with its own
handshake): `mfgtest led` (`MT-LED` writes the LED node and asks the owner whether LED #2 is lit —
a visual report is data, `FW-63`); `mfgtest button` (`MT-BUTTON` holds `/dev/input/event0` open 20 s
and needs the owner to hold reset about 3 s inside that window — `FW-62`: a boot's first hold over
~2 s is the one that reaches a timer, and between LED or button episodes the `REG-37` latch is
cleared with `echo 0 > …/brightness`). `mfgtest auto` (both boots) needs neither.

Estimates (guesses, from arm II's and block 50's transcripts): `line0` 10 s; the owner's power-on
within the window, then the loader's prompt ~2.5 s later (`B-CATCH` ended 15.4 s after its start);
the prompt cells 3 s; ARP 4.4 s; `looprun` 21 s; ruling 9's bracket ~25 s; the four-counter bracket
~26 s; the reads ~15 s; `mfgtest` ~30 s; the map ~18 s — `line1` about 2.5 min after the catch;
`line2` about the same plus 2.5 s of reboot; `line3` ~20 s. With the main session's turns, about 8–10
minutes from power-on to power-off.

**Stop rules.** Every stop leaves `run/<dir>/<line>.log`'s last `STOP` line as the reason.

* **`line0` fails**: nothing is powered. Fix the attach, the adapter, the follower or the
  instruments' self-tests (`I0-ST`), and run `line0` again in a new directory (a line is never
  re-run into one that holds its records).
* **`I1-CATCH` fails** (no `<RealTek>` within 380 s, or not cold): if the owner powered on late, the
  vendor's firmware may be booting from flash (it writes flash, the `FLS-26` family): the watch
  `X-I1` streams ESC and catches a later banner, but **ask the owner to power off at once** unless
  `X-I1` ended on the prompt. The seating is re-planned.
* **A prompt cell fails** (`I1-PSA`…`I1-ARP`, or `I4-…` after the warm catch): nothing has been
  uploaded. `stopwatch <dir> X-I<n>`; the board is at the prompt: **ask the owner to power off**
  (the default), or the owner re-plans — a retry is a declared off-card cell (arm II's
  `X-ARP2`/`X-ARP3`), never a re-run.
* **`I1Q`/`I4Q` fails** (any `looprun` stage): read `run/<dir>/line<n>.log` and `<cell>.log`. Before
  S6 nothing was uploaded; after S6b a wrong boot is S8's. `stopwatch`, then **power off**: the
  board may run an image that is not this sheet's.
* **`I1-MK`/`-VT`/`-UP` fails**: the booted image is not `r6b8i` with the standard `/init`
  (another `ID0`, no seam, a vendor probe, the quiet `/init`). `stopwatch`, `line4`, power off.
* **A map gate fails** (`I3-MB0`, `I6-MB1`, `I3-NW0`, `I6-NW1`): stop for the owner before anything
  else is typed — not even `line4` (`R6b`'s stop-loss).
* **A verdict reads FAIL** (`I2-V?`, `I5-V?`): a reading, not a stop. `line1` still takes boot 1's
  reads; the default is to go on to `line2` (the second boot is the second sample ruling 9 asks
  for); the main session may instead end with `line4`.
* **The tail's premise fails** (`I7-SW0`: locked or already reset; `I7-NIC0`/`I7-C0`: not armed): no
  reset has been typed. `stopwatch <dir> X-I3`, `line4`.
* **`I7-RF` is not refused** (no `write error`, or `n_reset` moved): the guard failed on the silicon;
  a reset ran with the engine on. `stopwatch`, `line4`, power off; the record says so.
* **`I7-NIC1`/`I7-C1` fails** (the engine still on after `disarm`): no permitted reset is typed.
  `stopwatch`, `line4`.
* **`IZ-RB`/`I4-RB` `gate:prompt` fails**: the watch `X-I<n>` starts at once. If it reads a reset
  caught at the prompt, power off; if it never saw `<RealTek>`, the board may be in the vendor's
  firmware: **power off at once**.
* **Any other gate stops a line with the board in Linux**: `stopwatch <dir> X-I<n>`, then `line4`
  (or `line3`, whose tail checks its own premises), then power off.

## § 5 The flash-safety count, before power

Every string this card sends to the console, 86 in all: loader verbs 10 `DW`, 2 `IPCONFIG`; the
rest are Linux commands (`cat`, `echo … | cat >` to `/proc/rtl819x-view`, `echo map 0 >
/proc/rtl819x-spi`, the board's `ping`, `ls`, `mfgtest`, `busybox reboot -f`, the tail's `reset
full`, `ifconfig rlx0 down` and `disarm`). `looprun` adds, per round (two rounds): its rescue's
`AUTOBURN 0`, `LOADADDR 80500000` and `IPCONFIG 10.1.1.1` (each first tried in a colon form the
loader answers `Unknown command !`), `DW 8040D4A0 1` (S5b), `DW 80500000 8` (S6b) and `J 80500000`
(S7); its upload is TFTP into RAM at `0x80500000`, after S5b has read `00000000`. **Zero `FLW`, `EW`,
`EB`, `DB`, `FLR` and non-zero `AUTOBURN`**; no `FLR` at all, so no `flrbracket` round. `mfgtest`'s
`MT-FLASH-2` writes `trywrite`, which the SPI driver refuses with no transaction (its stubs hold
none), `n_writes` read 0 after it on each boot (`I3-NW0`, `I6-NW1`); its `MT-MAC`/`MT-RFCAL` read
`H601` inside the kernel and print booleans only (`docs/mfgtest.md`). The Linux-side register
writes: `/init`'s (the switch's `init` — `PCRP0`–`4` bit 0, five stores — and `start`; the NIC's
bring-up), and the tail's. The bracket's reach: `I3-M0` (boot 1, after its reads) to `I6-M1` (boot
2, before the tail); it cannot see `H601`, two writes that cancel, anything outside the map's
windows, or the time before `I3-M0` and after `I6-M1` (the tail and the last reboot).

## § 6 What this run does not establish

A pass says that on these two boots the loader's switch state plus `init`'s five `EnablePHYIf` bits,
typed by `/init`, carried a ping both ways with no vendor Ethernet code in the image; not that the
state holds on a boot the loader did not bring its network up on (autoboot from flash, which the
zero-write rule keeps unreachable), nor after a link flap with EEE left on (ruling 4), nor under load.
It does not separate the five bits (all five are stored together), nor say how the loader's tables
deliver to the CPU (`NET-37` 殘留: the L2 and netif reads are the reading, not the answer). The
tail's `reset full` is one reset on one boot: it does not say what `reset vendor`'s clock gate adds,
and a refusal shows the guard's test on this word, not its behaviour under a racing timer. `NET-30`'s
reads place the latch at the prompt and after `IPCONFIG`, not between the upload and `J`. Nothing here
reads the flash beyond the map's windows.
