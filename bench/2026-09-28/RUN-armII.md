# R6b-8 arm II with `rtl819x-switch` 1.4 — the SWCORE=n image from the board's loader prompt, step (5) typed

Written 2026-09-27 (segment 115) by the `R6b-10` desk agent, for the main session to type; it
replaces 8b's `RUN-armII.md` (`$FWRE_WORK/rebuild/s115/r6b8b/`), whose step (5) could not be typed.
Not a frozen card: the owner's rule for `R6b` from today is no freeze, predictions optional, test
while doing. The flash rules are unchanged, and every rule this file relies on is below.

## § 0 What runs, and on what

* **The board**: at the loader's `<RealTek>` prompt, where `RUN-r6b10.md`'s `YZ-RB` leaves it — the
  main session's plan (2026-09-27): group A, then `RUN-r6b10.md`, then this card, in one power cycle
  and one bench directory. Nothing here needs power, the reset button or a cable move. `M1-ARP`
  checks that the loader answers ARP for 10.1.1.1 before `looprun` uploads anything.
* **The image**: `r6b10n`, `CONFIG_RTL_819X_SWCORE=n` (`--variant quiet-noswcore`), branch `r6b10`
  (built at `bc3311b`, the same `config/` as the landed tip), recipe `1cc05e88`, quiet kernel, quiet
  `/init` (`_irfs-r6b10`), `rtl819x-nic` 1.6 and `rtl819x-switch` 1.4, built twice byte-identical
  (`r6b10n2`). `nfjrom` `/home/key/fwre-work/rebuild/s115/r6b10/rtk/r6b10n/rlxfw/kroot/rtkload/nfjrom`, 1,113,088 bytes, sha256 `e587fa3517b83b73ad2c9e8b2d5a8684ebbbbce6b9085d3c5c61a20e0593a767`; vmlinux `a05591339bd7d2b3e0a60ebe21032794a61e7443e8a6285c3d6ba38ddeefe242`. `RLXFW-ID0`
  cannot tell it from `r6b10y` (`FW-99`): `looprun` pins the `nfjrom` digest, and `M1-MK` requires
  `RLXFW-SM0=`, which only the seam prints.
* **What changed from 8b's sheet**: the image; the cell names (`M…`); an ARP check before `looprun`;
  step (3), which types no `txlen` — 1.6 boots at the vendor's lengths, and `M3-NICR` gates on it;
  and step (5), which 1.4 makes typeable. Everything else is 8b's, reviewed there.
* **Zero flash writes, zero `FLR`**, as in 8b's § 0: the upload is `looprun`'s (S5b's `AUTOBURN` read,
  S6b's staged-head read); the map is bracketed (`M2-M0`/`M6-M1`) and gated.
* **No switch write before the pings** (`M4-*`): the only writes before them are the NIC's own
  (`M3-UP`: `unlock`, `netdev on`, `ifconfig rlx0 10.1.1.3 up`). No `echo start > /proc/rtl819x-switch`:
  `SSIR`'s `TRXRDY` is read (`M2-SW`, `M2-VP2`) and left as the loader set it.
* **Step (5), the one declared write class**: `PCRP0`–`PCRP4 |= EnablePHYIf`, bit 0, the inverse of
  `J` (讀 the loader's code, `notes/switch-driver.md` § 8.3). Two sources for the bit: the datasheet's
  Table 64 (bit 0 `EnablePHYIf`, *"When disabled, the PHY interface will be isolated from the MAC"*)
  and `rtl865xc_asicregs.h:1258` in the build's `CONFIG_RTL_8196E` arm; 量 the prompt's `nn7F0039`
  against `S0′`'s `nn7F0038` (`C1-L4104`, `C9-SW0`). The verb is `rtl819x-switch` 1.4's `phyif all`
  (`notes/switch-driver.md` § 15): behind its own token `unlock phyif-i-mean-it` and the switch's
  `unlock i-mean-it`, IRQs off per port, a pre-read that must carry the port's `ExtPHYID`, a store of
  the word read with bit 0 set, a read-back that must equal it. `M5-REF` types it once without the
  token first: the guard is seen refusing on the silicon (`refused 1`, `n_writes 0`) before it is
  seen permitting. Both unlocks are taken back (`M5-LOCK`) before the pings.
* **Every `--send` is at most 127 characters, every capture has a terminator and a `--seconds` cap**,
  every board cell's `--until` carries the reset banner, and every Linux cell is followed by a gate
  that refuses loader text in it. No Linux cell carries `--esc-after`. The card ends at the loader
  prompt: `MZ-RB`, `busybox reboot -f` under a catch, `gate:prompt`, at the end of `n-line2`,
  `n-line3` or `n-line4`.

## § 1 What each read is expected to show (推, optional, for reading only)

* `M1-ARP`: `4 packets transmitted, 4 packets received` (a gate: at least one).
* The boot, as 8b predicted: `RLXFW-SM0=C4000000`, `SM1` and `N1` `04000000` (bits 31:30 clear:
  the seam's disarm), `B07` `00000000`, `SW2` `00000001`; no `Probing RTL8186`, no `ethN added`.
* `M2-SW`: `PCRP0`–`PCRP4` live `nn7F0038` (`EnablePHYIf` clear since `J`), 1.4's `phyif` lines at
  boot (`unlocked 0 … refused 0`, each port `rc 1`), `n_writes 0`. `M2-NIC`: `version rtl819x-nic
  1.6`, the boot policy line. `M2-TX`: no verb since boot.
* `M4`: host → board 0 of 4 and board → host none (推, from `EnablePHYIf` clear on all five ports, as
  8b wrote): the reason step (5) exists.
* `M5-REF`: refused, `refused 1`, `n_writes 0`. `M5-PHY`: `ok 1 stored 5 already 0 … rbfail 0`, each
  port `pre nn7F0038 rb nn7F0039 rc 0 st 1`, the switch's `n_writes 5`; `M5-VP1` reads the same five
  words through `rtl819x-view`. `M5`'s pings: 推, they pass — the one variable changed since `M4` is
  bit 0 of five registers.

## § 2 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-28/ --skip S2,S3,S4 --recipe-override 1cc05e88 --dwell-seconds 2.5 --boot-until 'job control turned off[^#]{1,2}# |Booting[.][.][.]|---RealTek'`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 48's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets ; grep -e '^Icmp:' -e '^Udp:' /proc/net/snmp` — 8b's
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — 60-B frames, the liveness gate: 4 of 4 or the line stops
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — card C's
`NIMG` = `--image /home/key/fwre-work/rebuild/s115/r6b10/rtk/r6b10n/rlxfw/kroot/rtkload/nfjrom --image-sha256 e587fa3517b83b73ad2c9e8b2d5a8684ebbbbce6b9085d3c5c61a20e0593a767`
`PD` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 10.1.1.3` — the default 98-B frames

The host, before the board is touched (no console):

```
HOST bench/2026-09-28/M0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-28/M0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
```

(1) At the loader prompt, zero-write `DW` reads for this power-on's before-`J` baseline, the ARP
check, then the upload and the boot, and the boot's marks:

```
CAP --out bench/2026-09-28/M1-DWP --send 'DW BB804100 8' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28/M1-DWS --send 'DW BB804200 4' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
CAP --out bench/2026-09-28/M1-DWC --send 'DW B8010000 16' --esc-after 10 --esc-period 0.02 --until 'RealTek>' --seconds 25
HOST bench/2026-09-28/M1-ARP :: sudo -n arping -c 4 -w 6 -I enxfc19286184c9 10.1.1.1 ; ip -4 neigh show 10.1.1.1 dev enxfc19286184c9 ; true
HOST bench/2026-09-28/M1Q :: LR --cell M1Q NIMG --iterations 1
HOST bench/2026-09-28/M1-MK :: grep -a -o -E 'RLXFW-(SM0|SM1|B07|N1|N2|N3|N4|SW1|SW2|SW3|SW4|SW5|SW7|ID0)=[0-9A-F]{8}' bench/2026-09-28/M1Q-boot.log ; true
HOST bench/2026-09-28/M1-VT :: grep -a -c -E 'Probing RTL8186|added[.] vid=|peth0' bench/2026-09-28/M1Q-boot.log ; true
```

(2) The zero-write reads, before any write:

```
CAP --out bench/2026-09-28/M2-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/M2-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28/M2-MB0 :: MB bench/2026-09-28/M2-M0
CAP --out bench/2026-09-28/M2-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-TX --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/M2-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VM --send 'echo mib > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VV --send 'echo tbl vlan > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VN --send 'echo tbl netif > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP1 --send 'echo peek 0xBB804100 10 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP2 --send 'echo peek 0xBB804200 4 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP3 --send 'echo peek 0xBB804400 14 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP4 --send 'echo peek 0xBB804A00 8 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP5 --send 'echo peek 0xB8010000 15 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-VP6 --send 'echo peek 0xB8000040 2 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M2-DEV --send 'cat /proc/net/dev ; ls /proc/rtl865x ; cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
```

(3) The NIC up at 1.6's default — `unlock`, `netdev on`, `ifconfig`; no policy verb:

```
CAP --out bench/2026-09-28/M3-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/M3-NICR --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
```

(4) The pings, before any switch write (this image's `ping` ignores `-c`: the board's is bounded by
a background job and a `kill`):

```
HOST bench/2026-09-28/M4-HP0 :: HP
HOST bench/2026-09-28/M4-FL :: FL 10.1.1.3
HOST bench/2026-09-28/M4-PL :: PL
HOST bench/2026-09-28/M4-PD :: PD
HOST bench/2026-09-28/M4-NB :: ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 ; true
CAP --out bench/2026-09-28/M4-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28/M4-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M4-SN --send 'cat /proc/net/snmp /proc/net/arp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/M4-VM --send 'echo mib > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/M4-HN :: HN
```

(5) Only if (4) had no reply: the guard refusing, the unlocks, the one write class, the relock, and
the pings again:

```
CAP --out bench/2026-09-28/M5-REF --send 'echo phyif all > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/M5-UNL --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo unlock phyif-i-mean-it > /proc/rtl819x-switch' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/M5-PHY --send 'echo phyif all > /proc/rtl819x-switch ; cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/M5-LOCK --send 'echo lock phyif > /proc/rtl819x-switch ; echo lock > /proc/rtl819x-switch' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/M5-VP1 --send 'echo peek 0xBB804100 10 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
```

```
HOST bench/2026-09-28/M5-HP0 :: HP
HOST bench/2026-09-28/M5-FL :: FL 10.1.1.3
HOST bench/2026-09-28/M5-PL :: PL
HOST bench/2026-09-28/M5-PD :: PD
HOST bench/2026-09-28/M5-NB :: ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 ; true
CAP --out bench/2026-09-28/M5-BP --send 'ping 10.1.1.2 & sleep 15 ; kill $! ; echo PING-""END' --until 'PING-END\r\n# |Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-28/M5-NIC --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M5-SN --send 'cat /proc/net/snmp /proc/net/arp' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
CAP --out bench/2026-09-28/M5-VM --send 'echo mib > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-28/M5-HN :: HN
```

(6) The reads again, the map closed, and back to the loader (`busybox reboot -f`, `FW-37`, under a
catch):

```
CAP --out bench/2026-09-28/M6-SW --send 'cat /proc/rtl819x-switch' --until 'r TCR7 +4D3C [0-9A-F]{8} [0-9A-F]{8} \d\d\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-28/M6-VP1 --send 'echo peek 0xBB804100 10 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M6-VP5 --send 'echo peek 0xB8010000 15 > /proc/rtl819x-view ; cat /proc/rtl819x-view' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M6-MD --send 'cat /proc/rtl819x-mdio' --until 'jiffies [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/M6-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-28/M6-MB1 :: MB bench/2026-09-28/M6-M1
CAP --out bench/2026-09-28/M6-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-28/MZ-RB --send 'busybox reboot -f' --esc-after 20 --esc-period 0.002 --until '<RealTek>' --seconds 40
```

The tail watches, run only as § 3 says:

```
CAP --out bench/2026-09-28/X-M1 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
CAP --out bench/2026-09-28/X-M2 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
CAP --out bench/2026-09-28/X-M3 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
CAP --out bench/2026-09-28/X-M4 --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605
```

## § 3 The lines the main session types, from the repository root in WSL

Generated with the cells from one list (`s31-runsheets.py`), each dry-run through `tools/cardrun.py
--dry`. **(4) → (5) is a decision point, so it is two lines.** Every line script takes the night's bench directory as its first argument and refuses
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
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line0.sh bench/2026-09-28 --dry
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line1.sh bench/2026-09-28 --dry
# at the loader prompt y-line1 (or y-line2) left:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line0.sh bench/2026-09-28
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line1.sh bench/2026-09-28        # bg; (1)-(4), ends in Linux and starts the watch X-M1
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/stopwatch.sh bench/2026-09-28 X-M1    # always, once n-line1 has printed 'watch X-M1 start'
# read (4) -- M4-PL?/M4-PD?'s rc in run10/2026-09-28/n-line1.log, M4-BP's reply lines -- then ONE of:
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line2.sh bench/2026-09-28        # bg; (4) had no reply: (5), (6), the reboot
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line3.sh bench/2026-09-28        # bg; (4) was answered: (6), the reboot
# only after a line stopped with the board in Linux: stopwatch.sh bench/2026-09-28 X-M<n>, then
wsl -d Ubuntu-24.04 -- bash /home/key/fwre-work/rebuild/s115/r6b10/n-line4.sh bench/2026-09-28        # bg; the reboot alone
```

**Stop rules** (8b's, renamed; two added).

* **`M1-DW*` or `M1-ARP` fails** (a `DW` without its word, no ARP reply from 10.1.1.1): nothing has
  been uploaded. `stopwatch.sh <dir> X-M1` (the line started it); the board is at the prompt. Stop.
* **`M1Q` fails** (any `looprun` stage): read `M1Q.log`; a boot log ending on the banner is a reset
  during the first boot, `X-M1` the catch. `stopwatch.sh <dir> X-M1`, then stop; the owner re-plans.
* **`M1-MK` or `M1-VT` fails**: the booted image is not the seam's, or the loader's engine was not
  disarmed (bits 31:30 of `SM1`/`N1`). Nothing has been typed to the NIC. `stopwatch.sh <dir> X-M1`,
  then `n-line4.sh <dir>`.
* **A map gate fails** (`M2-MB0`, `M6-MB1`, `M2-NW0`, `M6-NW1`): stop for the owner, nothing else typed.
* **`M5-REF` is not refused, or `M5-PHY` reads any `rc` other than 0, `idfail` or `rbfail` above 0**:
  the line stops with both unlocks still set. `stopwatch.sh <dir> X-M2`, then type
  `echo lock phyif > /proc/rtl819x-switch ; echo lock > /proc/rtl819x-switch` as one declared
  off-card cell, then `n-line4.sh <dir>`; the `phyif` lines are the reading (which port, which word).
* **`M4-PL?`/`M4-PD?` non-zero, or `M4-BP` without a reply**: a reading, not a stop — the decision
  for `n-line2`.
* **Any other gate stops a line with the board in Linux**: `stopwatch.sh <dir> X-M<n>`, then
  `n-line4.sh <dir>`.

## § 4 What this run does not establish

It reads the loader's switch state under an `SWCORE=n` kernel and whether that state carries a ping,
then — if it does not — whether `EnablePHYIf` on ports 0–4 is the missing piece. A pass at (5)'s
pings says the five bits were sufficient on this boot with the loader's other switch state; it does
not say that each is necessary (all five are set together), nor that anything else of the vendor's
init is unneeded on another boot, nor that the port a ping crossed was the one the bit enabled —
`D8` asks for rlxfw's own switch init with a positive discriminator, arm I. A fail at (5) says the
bit is not sufficient on this boot. Nothing here reads the flash beyond the map's windows.
