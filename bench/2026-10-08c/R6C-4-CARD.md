# R6C-4 -- the take-over on the device: the release image from RAM, T into slot A, then a warm and a cold flash boot, 2026-10-08

**declared date 2026-10-08** · drafted in the 129th segment for a seating whose day was not yet
known, and re-dated by one string when the owner chose to seat it that evening, the day's third
seating · `R6c`, step `R6c-4` · relaxed process, not frozen; but the card carries its predictions and
a `cardnum` fence, because it is the test of `NET-173`. Derived from `bench/2026-10-08/V10-CARD.md`
(the install, the owner's yes, the flash boots, the closing) and `bench/2026-10-08b/R6C-A-CARD.md`
(the switch reads). NOT relaxed: the flash rules, `H601`, the power handshake, `NET-165`, and the
owner's dated yes for the one write (`FW-113`).

**Why.** 量 `NET-171`: booted from flash, `rlx0` receives nothing. 量 `NET-172`: the switch discards
every frame from the host at port 3; the three tables are empty and `PVCR0`-`3` read `00010001`.
讀 `NET-173`: `rtl819x-switch` 1.6's `vlan`, typed by PID 1 between `init` and `start`, writes the
loader's one-VLAN layout (the owner's ruling O1) and stores only what differs. None of 1.6 has run
on the device. This card runs it first from RAM through the loader's prompt, where the loader has
already written the group and `vlan` clears only netif slot 0 (the regression O1 asks for); then,
only if that pings both ways, installs T in slot A and boots it from flash after a watchdog reset
and after a cold power-on.

**The state before the card, from the bench record.** 量 slot A holds R, version 3
(`5a38d96922ec89136ed88e56205b045521e85772308431539ce18f8d093564df`, installed by
`bench/2026-10-07/ACb`); slot B holds S, version 4 (`3f728d56…`, installed by
`bench/2026-10-08/V05b`); `0x010000` and `0x020000` hold the `cs6c` `rlxboot` and its rescue copy
(`RLXBOOT-V1 build=127a71cf` in `V06` and `V08`). `bench/2026-10-08/V07` and `V09` (`bootslot judge`
PASS): A `ok:3`, B `ok:4`, B chosen, `RLXBOOT-FROM 05010000`, after a watchdog reset and after a cold
power-on. So a flash boot today chooses B. After `I10`: A = T `ok:5`, B = S `ok:4`, A chosen -- 讀
the host's `slotcheck` (`$FWRE_WORK/rebuild/s128/p/run/r6c/log/slot-V2.log`), not yet the device.
量 The board runs S (`6a11de02`) from slot B, booted by `V08`'s cold power-on and read without a write
by seating A, whose last cell `A17` read an uptime of 33,159.07 s at 2026-10-08T11:58:52+0800; 讀
nothing has been typed to it since (`LOG.md`, 128th segment; `PROGRESS.md` § Now). So the board is at
S's shell, not at the loader prompt, and no cell before phase 4 needs a power action. As in V10, the
pre-flight `PF` runs with the board idle at a shell.

**What it may do.** One flash-writing command, `I10` (`install slotA`), under the owner's dated yes
below; two power actions, both in phase 4, each on the owner's word; zero `FLW`, `EW`, `EB` and
non-zero `AUTOBURN`; zero `FLR`; no PHY access; nothing typed to `/proc/rtl819x-switch` by hand (PID 1
types `vlan` on every boot of both images); no `--force`. The board never waits at `<RealTek>`: `R01`
and `I01` are each followed at once by `looprun` (`NET-165`).

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`

Payloads, each pinned by a `cardnum` row below: the release image
`/home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img` (1,110,016 bytes,
`295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd`, recipe `9bb2bec7`); the armed image
`/home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.img` (1,117,184 bytes,
`9328dcf9ddaaa4b4f8bc1e586d2993c7a670f2fd13d3f72c16f8da6cd16cd735`, recipe `8dce09c5`); container T
`/home/key/fwre-work/rebuild/s128/p/run/r6c/signed/T.rlxu` (1,110,176 bytes,
`113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8`: version 5, slot A at `0x070000`,
form whole, payload the release image, signed with the owner's production key `4a6eda72…3096e`;
`mkfw2` accepts it for `0x070000` and refuses `0x190000` on `flash_match`). Both images were built
twice byte-equal from `034b5a7d` (rows `img-twice`, `armed-twice`: the second build's record names
the same digest), whose `rtl819x-switch.c` the build clone, the armed tree and the
repository hold byte-equal (rows `src-switch*`). The arithmetic is
`/home/key/fwre-work/rebuild/s129/r6c4/derive.py` over that clone and the bench record; its output,
`derive.out`, is pinned line by line, and `derive-controls.sh` shows it refusing a driver its model
does not describe (6 of 6).

## The cells

**Phase 0 -- the host, the pre-flight with the board idle at S's shell, a shell probe**

```
HOST bench/2026-10-08c/P01 :: pgrep -a -f rlxfw-keeper
HOST bench/2026-10-08c/P02 :: ip -4 addr show enxfc19286184c9
HOST bench/2026-10-08c/P03 :: /usr/bin/python3 tools/sendimg.py --self-test
HOST bench/2026-10-08c/P04 :: /usr/bin/python3 tools/bootslot.py --self-test
CAP --out bench/2026-10-08c/PF --seconds 3
CAP --out bench/2026-10-08c/P05 --send 'cat /proc/uptime' --idle 3 --seconds 20
```

**Phase 1 -- B1, the RAM regression: the release image from RAM through the prompt; no write**

```
CAP --out bench/2026-10-08c/R01 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-08c/R02 :: /usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-10-08c/ --skip S2,S3,S4 --recipe-override 9bb2bec7 --dwell-seconds 5 --boot-until 'for a list of built-in commands[.][^#]{1,8}# |Booting[.][.][.]|---RealTek' --cell R02 --image /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img --image-sha256 295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd --iterations 1
CAP --out bench/2026-10-08c/R03 --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/R04 --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/R05 --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/R06 --send 'echo peek 0xBB804400 14 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/R07 --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/R08 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/R09 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
HOST bench/2026-10-08c/R10 :: I=enxfc19286184c9; ip -s link show $I; sudo -n ip neigh flush dev $I; (timeout 14 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; ping -c 4 -W 2 10.1.1.1; echo ping_rc=$?; sleep 6; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/R11 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/R12 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-10-08c/R13 :: I=enxfc19286184c9; ip -s link show $I; (timeout 40 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; /usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out bench/2026-10-08c/R14 --send 'ping 10.1.1.2' --until 'packet loss' --seconds 35; echo cap_rc=$?; sleep 5; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/R15 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/R16 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

`R13`'s capture writes `R14`; `R10` and `R13` run the host's `tcpdump` in the background for their
window, and its lines land in the HOST cell's log (R6C-A's `H11`/`H14`). **Decision point D1 is here:
nothing below runs unless D1 holds.**

**Phase 2 -- the armed image from RAM installs T into slot A: the one write**

```
CAP --out bench/2026-10-08c/I01 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-08c/I02 :: /usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-10-08c/ --skip S2,S3,S4 --recipe-override 8dce09c5 --dwell-seconds 5 --boot-until 'for a list of built-in commands[.][^#]{1,8}# |Booting[.][.][.]|---RealTek' --cell I02 --image /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.img --image-sha256 9328dcf9ddaaa4b4f8bc1e586d2993c7a670f2fd13d3f72c16f8da6cd16cd735 --iterations 1
HOST bench/2026-10-08c/I03 :: I=enxfc19286184c9; sudo -n ip neigh flush dev $I; ping -c 2 -W 2 10.1.1.1; echo ping_rc=$?; ip neigh show 10.1.1.1
CAP --out bench/2026-10-08c/I04 --send 'echo img reset > /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/I05 --send 'busybox nc -l -p 5000 </dev/null >/proc/rtl819x-spi-img &' --idle 2 --seconds 10
HOST bench/2026-10-08c/I06 :: /usr/bin/python3 tools/sendimg.py send --to 10.1.1.1:5000 --src 10.1.1.2 --file /home/key/fwre-work/rebuild/s128/p/run/r6c/signed/T.rlxu --sha256 113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8
CAP --out bench/2026-10-08c/I07 --send 'sleep 15 ; cat /proc/rtl819x-spi' --idle 20 --seconds 45
CAP --out bench/2026-10-08c/I08 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/I09 --send 'echo arm 0x70000 0x190000 0x120000 > /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/I10 --send 'echo install slotA sha=113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8 > /proc/rtl819x-spi' --until 'RLXFW-SI-END' --idle 30 --seconds 900
CAP --out bench/2026-10-08c/I11 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

**Phase 3 -- the warm flash boot: `rlxboot` boots T from slot A after a watchdog reset (no ESC)**

```
CAP --out bench/2026-10-08c/W01 --send 'busybox reboot -f' --until 'for a list of built-in commands[.][^#]{1,8}# |refuse-action halt|<RealTek>' --seconds 180
HOST bench/2026-10-08c/W02 :: /usr/bin/python3 tools/bootslot.py judge bench/2026-10-08c/W01.log --expect-slot A --expect-a ok:5 --expect-b ok:4 --expect-from 05010000 --build-manifest /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest
CAP --out bench/2026-10-08c/W03 --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/W04 --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/W05 --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/W06 --send 'echo peek 0xBB804400 14 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/W07 --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/W08 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/W09 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
HOST bench/2026-10-08c/W10 :: I=enxfc19286184c9; ip -s link show $I; sudo -n ip neigh flush dev $I; (timeout 14 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; ping -c 4 -W 2 10.1.1.1; echo ping_rc=$?; sleep 6; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/W11 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/W12 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-10-08c/W13 :: I=enxfc19286184c9; ip -s link show $I; (timeout 40 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; /usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out bench/2026-10-08c/W14 --send 'ping 10.1.1.2' --until 'packet loss' --seconds 35; echo cap_rc=$?; sleep 5; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/W15 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/W16 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/W17 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

**Phase 4 -- from cold: owner OFF, the pre-flight with the board off, the window opened, owner ON (no ESC)**

```
CAP --out bench/2026-10-08c/PF2 --seconds 3
CAP --out bench/2026-10-08c/C01 --until 'for a list of built-in commands[.][^#]{1,8}# |refuse-action halt|<RealTek>' --seconds 300
HOST bench/2026-10-08c/C02 :: /usr/bin/python3 tools/bootslot.py judge bench/2026-10-08c/C01.log --expect-slot A --expect-a ok:5 --expect-b ok:4 --expect-from 05010000 --build-manifest /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest
CAP --out bench/2026-10-08c/C03 --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/C04 --send 'echo tbl vlan | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/C05 --send 'echo tbl netif | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/C06 --send 'echo peek 0xBB804400 14 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/C07 --send 'echo peek 0xBB804754 1 | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/C08 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/C09 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
HOST bench/2026-10-08c/C10 :: I=enxfc19286184c9; ip -s link show $I; sudo -n ip neigh flush dev $I; (timeout 14 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; ping -c 4 -W 2 10.1.1.1; echo ping_rc=$?; sleep 6; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/C11 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/C12 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-10-08c/C13 :: I=enxfc19286184c9; ip -s link show $I; (timeout 40 sudo -n tcpdump -n -l -i $I arp or icmp 2>&1 &); sleep 1; /usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400 --out bench/2026-10-08c/C14 --send 'ping 10.1.1.2' --until 'packet loss' --seconds 35; echo cap_rc=$?; sleep 5; ip neigh show 10.1.1.1; ip -s link show $I
CAP --out bench/2026-10-08c/C15 --send 'echo mib | cat > /proc/rtl819x-view ; cat /proc/rtl819x-view' --idle 3 --seconds 20
CAP --out bench/2026-10-08c/C16 --send 'cat /proc/net/dev ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-10-08c/C17 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

## The handshake (phase 4, and only there)

Before the owner is asked for OFF, `W01`-`W17` have all run and been read: nothing of the warm boot
is owed once the power is cut. The owner is asked, and answers, before each power action. `PF2`
runs once the owner says the board is off. `C01` is opened only after `PF2` is read, and the owner
is told to power on only once `C01.timing` exists, with the latest time: `C01`'s start + 240 s (the
300 s window less 60 s for the boot, which took 15.6 s from power-on to the shell in `V08`, row
`d-tc`).

## What each cell decides -- written before power

Marks: 量 measured, 讀 read out of the code or a record, 推 inferred. Every number below sits in a
`cardnum` row (named in brackets). "Live / latch" is the switch page's register row: the value now,
then slot 0, latched at `subsys_initcall` before `/init` ran.

**Phase 0.**
* `P01`: one `rlxfw-keeper` process. `P02`: `inet 10.1.1.2/24` on `enxfc19286184c9`. `P03`, `P04`:
  each self-test passes. A failure is the host's, fixed before anything is typed to the board.
* `PF`: three artefacts, ~3.08 s, 0 bytes (an idle shell prints nothing). A byte is a finding to
  read, not a pass.
* `P05`: one uptime line. Same boot as seating A iff the uptime is 33,159.07 + (`P05`'s `t0_real`
  − 1,791,431,932.24) within ±60 s [`d-a17u`, `d-a17t`]; seating A saw 0.2 s of drift over 8.9 h.
  Outside it: the board was reset since seating A -- recorded, and the card goes on, because `R01`
  resets it anyway. No uptime line: stop (the board is off, hung or at the loader).

**Phase 1 (the RAM path: the loader has written the group before the image runs).**
* `R01`: `Reboot Result from Watchdog Timeout!`, then the capture ends at `<RealTek>` (`V01` caught
  it at 0.99 s).
* `R02`: `RESULT: the loop closed, 8 assertion(s) held`; `A0b` `00000000`; `A3` `board printed
  9bb2bec7, build computed 9bb2bec7`; `S7` ends on the boot-until match, about 10.4 s after `J`
  [`d-tj`], not on the 45 s cap.
* `R03`, the boot's first read of the switch page. 讀 from the code, over 量 inputs [`d-r*`]:
  `version rtl819x-switch 1.6`; `unlocked 1`; `n_refused 0`; `n_reset 0`; `n_dumb 0`; `n_restore 0`;
  `boot_cvidr 81964000`; **`n_writes 18`** = `init`'s 5 (`PCRP0`-`4`) + `vlan`'s 12 + `start`'s 1
  [`d-r18`, `d-r12`, `d-boot6`, `d-m6r`]: one table write, netif slot 0, the one item that differs
  (item 16) [`d-rdiff`, `d-rtw`]; **`n_reads` = 126 + `sta` + `spin`**, the last two read off the
  same page [`d-r126`]: the boot's 52 without the verb (CVIDR 1, the census 37, the three PSRPs the
  census lacks, `init`'s 10, `start`'s 1 [`d-boot52`]; 量 52 on `PER-SW` [`d-m52r`]) plus `vlan`'s 74
  [`d-r74`]. An excess is an idle poll that did not answer at its first read: a reading, not a
  refutation. 推 `sta` 1 (`SWTCR0` reads `00080000`, bit 19 set, on both paths), so 127 + `spin`.
  The `phyif` and `init` lines as `PER-SW`'s: `phyif unlocked 0 ok 0 stored 5 already 0 refused 0
  idfail 0 rbfail 0`, `init calls 1 ok 1 refused 0 rc 0 stored 1F on 1F reset_busy 0`. The `vlan`
  line: `vlan calls 1 ok 1 refused 0 rc 0 at -1 step 0 vw 0000 nw 01 rw 00 vm 0 vr 00000001 000001FF
  00000000 07FAC688 tlu T sta S spin K swtasr X final 0 ld 784 to 0 rb 0` [`d-rvw`, `d-rnw`, `d-rrw`,
  `d-vr`, `d-rld`]. `T`, `S`, `K` and `X` are read, not predicted: `tlu` is `000C0000` if bit 18
  reads back set and `00080000` if not, and neither is required; `ld 784` = 24 × 16 + 16 + 24 × 16
  holds only if every double read agrees at once. The register table, live / latch: **`SWTCR0
  00080000 00080000` (bit 18 clear)**; `FFCR 00000003 00000003`; `VCR0 000001FF 000001FF`;
  `PVCR0`-`3` `00080008 00080008`; `PVCR4 00000001 00000001`; `PBVCR0 00000000 00000000`
  [`d-rregs`, `d-rver`]; `SWTAA BB040000 BB060100` [`d-rswtaa`] (推: `SWTAA` reads back the last
  address stored, as `PER-SW`'s latch reads the loader's last table write, VLAN slot 8);
  `TCR7 00000000 00000000`; `SWTACR` bit 0 clear; `SSIR 00000001 00000001`; `MACCR 804A0185`,
  `MDCIOCR 96181441`, `MEMCR 00007F7F`, live equal to latch (the loader's, untouched); `PCRP0`-`4`
  `nn7F0039 nn7F0038`.
* `R04`: `tbl vlan`: `s08 t1 eq 00807E3F` and seven `00000000` [`d-entry`, `d-slot`]; the other
  fifteen slots `t1 eq` and eight `00000000` -- the loader's, unchanged (`M2-VV`).
* `R05`: `tbl netif`: all eight slots `t1 eq` and eight `00000000` (`M2-VN` read slot 0 non-zero).
  This is the netif-cleared hypothesis.
* `R06`: `a BB804410 00000001`, `a BB804418 00080000`, `a BB80441C 00000200`, `a BB804420 07FAC688`,
  `a BB804428 00000003`, the other nine words `00000000` (`M2-VP3` word for word).
* `R07`: `a BB804754 00001249` [`d-qr3`, `d-qr6`]: the loader's path; `vlan` never touches it.
* `R10` (host → board): `4 packets transmitted, 4 received, 0% packet loss`, `ping_rc=0`; `10.1.1.1
  dev enxfc19286184c9 lladdr 02:52:4c:58:46:57 REACHABLE` [`d-mac`, `d-ip`]; the host's TX packets
  grow by ≥ 5 (an ARP request after the flush, four echo requests), and its `tcpdump` shows them with
  the board's ARP reply and four echo replies (and any probe the board's own neighbour entry makes).
* `R08` → `R12`: `rlx0`'s RX packets and `n_rx` grow by ≥ 5, its TX by ≥ 5. Exact counts are not
  predicted: the host's own frames reach port 3 too (1,579 in 9.2 h in seating A, mostly multicast),
  and `FFCR`'s two traps send unknown unicast and multicast to the CPU (`NET-169`).
* `R09` → `R11`: port 3's in columns grow (14 broadcast ≥ 1, 2 unicast ≥ 4) and the CPU port's out
  columns grow by the same amounts, column for column (0↔21 octets, 2↔23, 13↔24, 14↔25); port 3's
  discard columns 15 and 16 do not move. 推 from arm I's RAM path, where the totals were equal column
  for column (`bench/2026-09-28b/I3-VM0`, `I3-VM1`) -- but with netif slot 0 present. Here it is
  absent, so `rlx0`'s unicast reaches the CPU port only through `FFCR`'s unknown-unicast trap
  (`NET-169`, 推 on one source): this pair is that mechanism's first test.
* `R13`/`R14` (board → host): `4 packets transmitted, 4 packets received, 0% packet loss`,
  `cap_rc=0`; four echo requests and four replies in the host's `tcpdump` (and any ARP the board's
  entry for 10.1.1.2 needs). `R12` → `R16`: `rlx0` TX and RX each ≥ +4. `R11` → `R15`: port 3's
  out unicast (column 23) ≥ +4, and the CPU port's column 17 grows by the frames `rlx0` sent (the
  CPU's frames are counted there, `notes/switch-driver.md` § 8.15; 量 seating A `A15`, arm I
  `I3-VM0`). A reading, not a gate: the MIB and `/proc/net/dev` are read at different instants.

**Phase 2.**
* `I01` as `R01`. `I02` as `R02`, with `A3` `8dce09c5`. `I03`: `2 received`, `ping_rc=0`,
  `lladdr 02:52:4c:58:46:57 REACHABLE` -- the release image's MAC too, so `I02`'s `A3` is what tells
  the images apart (`LOG.md`, 127th segment).
* `I04` and `I09` type only `echo` and carry no expectation; `I08` and `I11` read what they did.
  `I05`: the shell's job line only.
* `I06`: `sendimg: sent 1110176 bytes sha256 113f5542… to 10.1.1.1:5000 (peer sent 0 bytes back)`
  [`T-bytes`].
* `I07`: 15 s after `I06`, the drain `FW-248` measured is predicted complete: `img_len 1110176`,
  `img_err none`. A short `img_len` here is `FW-248` again, a reading; `I08` is the gate.
* `I08` (the gate): `img_cap 1179648`, `img_len 1110176`, `img_err none`, `inst_attempts 0`,
  `wr_armed 0`, `n_writes 0`, `recipe_id 8DCE09C5` [`d-asize`, `d-tlen`].
* `I10`: `RLXFW-SI-GO install slotA len=1110176 pace=0`; 18 `E` lines, 17 `P`, one `H`, 18 `V`
  [`d-tE`, `d-tP`]; `RLXFW-SI-END OK rc=0 cmp=1 ms=… pace=0` (S's took 11,340 ms [`d-tins`]; T's is
  not predicted).
* `I11`: `inst_attempts 1`, `inst_done 1`, `inst_refused 0`, `inst_failed 0`, `inst_region slotA`,
  `inst_base 070000`, `inst_size 1179648`, `inst_len 1110176`, `inst_reason OK`, `inst_rc 0`,
  `inst_arm_ok 1`, `inst_sha_ok 1`, `inst_hdr_ok 1`, `inst_ops 4625` and `inst_ops_planned 4625`,
  `inst_n_se 288`, `inst_n_pp 4337`, `inst_erased 1179648`, `inst_programmed 1110176`,
  `inst_committed 1`, `inst_phase D`, `inst_cmp_ok 1`, `inst_cmp_bytes 1179648`, `inst_cmp_diff 0`,
  `inst_cmp_first -1`, `n_writes 4625`, `wr_armed 0` [`d-tse`, `d-tpp`, `d-tops`, `d-terased`,
  `d-tcmp`, `d-abase`; the page count's rule checked on S: `d-spp` = `d-sppm`].

**Phase 3 (the flash path after a watchdog reset: nothing has written the group since the reset).**
* `W01`: `Reboot Result from Watchdog Timeout!`; `RLXBOOT-V1 build=127a71cf`; `RLXBOOT-FROM
  05010000`; `RLXBOOT-READ A flash=00070000 buf=81000000 n=1110176` and 16 dots [`d-tdots`];
  `RLXBOOT-VER cur=5 ctr=0 ok`; `RLXBOOT-VERDICT A ok ver=5`; `RLXBOOT-READ B flash=00190000
  buf=81200000 n=1109152` and 16 dots [`d-slen`, `d-sdots`]; `RLXBOOT-VERDICT B ok ver=4`;
  `RLXBOOT-SLOT A`; `RLXBOOT-BOOT load=80500000 entry=80500000`; `RLXFW-ID0=9BB2BEC7`;
  `RLXFW-SW5=00010001` (`PVCR0` at `subsys_initcall`: the reset value, as in `V06` [`d-v06sw5`]);
  `rlxfw: lan up, rlx0 10.1.1.1/24`; no `short write to /proc/rtl819x-switch` (the line PID 1 prints
  when `vlan` is refused); the shell about 15.7 s after the command [`d-tw`]. Marks are read, never
  gated on (`FW-47`): `W02` and `W03` are the gates.
* `W02`: `RESULT: PASS`.
* `W03`: as `R03`, with the flash path's numbers [`d-f*`]: **`n_writes 23`** = 5 + 17 + 1, the 17
  being VLAN slot 8's table write (12) and `PVCR0`-`3` and `FFCR` (5) [`d-f23`, `d-f17`, `d-fdiff`];
  **`n_reads` = 131 + `sta` + `spin`** [`d-f131`, `d-f79`; 量 52 without the verb on `X-V08r-sw`,
  `d-m52f`] (推 132 + `spin`); `vlan … rc 0 at -1 step 0 vw 0100 nw 00 rw 1F vm 0 vr 00000001
  000001FF 00000000 07FAC688 … final 0 ld 784 to 0 rb 0` [`d-fvw`, `d-fnw`, `d-frw`, `d-fld`]. Live /
  latch: **`SWTCR0 00080000 00080000`**; `FFCR 00000003 00000000`; `PVCR0`-`3` `00080008 00010001`
  [`d-fregs`]; `PVCR4 00000001 00000001`; `VCR0 000001FF 000001FF`; `PBVCR0 00000000 00000000`
  [`d-fver`]; `SWTAA BB060100 00000000` [`d-fswtaa`]; `TCR7 00000000 00000000`; `SSIR 00000001
  00000000`; `MACCR 80420186 80420186`; `MDCIOCR 00000000 00000000`; `MEMCR 00007F00 00007F00`;
  `PCRP0`-`4` `nn7F0039 nn7F0038`. ⚠️ **No warm flash boot's switch page has ever been read.**
  These latches are the cold path's (`X-V08r-sw`, seating A). For a watchdog reset they are 推, on
  `V06`'s four boot marks (`SW2`-`SW5` equal to the cold boot's, `PVCR0` `00010001` [`d-v06sw5`,
  `d-v06sw4`]) and on `X-V06q`'s deafness. If a verified word differs on this path, `vlan` refuses
  with `rc -71`, `vm` naming the word, and stores nothing; if `PCRP` bit 0 survived the reset,
  `init` stores nothing and `n_writes` reads 18. A third (main session's review): the ASIC tables are
  on-chip memory, and a reset that clears the registers -- as `V06`'s `PVCR0` latch says it does --
  need not clear them. Then slot 8 still holds the entry the loader wrote on `I02`'s boot and netif
  slot 0 the zero the armed image's own `vlan` wrote, so `vlan` makes no table write [`d-wktw`]
  and stores `PVCR0`-`3` and `FFCR` alone [`d-wk5`]: `vw 0000`, `rw 1F` [`d-wkvw`, `d-wkrw`],
  `n_writes 11` [`d-wk11`], and `SWTAA` is not stored, so it reads its latch. Each refutes the warm-path premise,
  not the write set -- the end state is the write set in all but the first -- and `W03` is the
  reading that settles which.
* `W04`: as `R04` -- here written by `vlan`, not by the loader. `W05`: all zero (none written; they
  read zero at boot in seating A). `W06`: as `R06`, `FFCR` now `00000003` where `A08` read 0.
* `W07`: `a BB804754 00041249` [`d-qf`] (量 `A09`, cold; warm 推).
* `W08`-`W16`: as `R08`-`R16`. This is the first flash boot predicted to receive: the control's
  were 0 of 3 with the entry `FAILED` (`X-V06q`, `X-V08q`, seating A).
* `W17`: `n_writes 0`, `wr_linked 0`, `n_mtd_write_calls 0`, `n_mtd_erase_calls 0`, `recipe_id
  9BB2BEC7`: the release image has no write path [`img-map-inst` 0].

**Phase 4.**
* `PF2`: three artefacts, ~3.08 s, 0 bytes, the board off.
* `C01`: as `W01` but with no `Reboot Result from Watchdog Timeout!` (cold, `C-8`); the shell about
  15.6 s after `Booting...` [`d-tc`].
* `C02`-`C17`: as `W02`-`W17`; here the latches are the ones 量 on a cold flash boot (`X-V08r-sw`,
  seating A) and `C07`'s `00041249` is `A09`'s.

## The decision points, and what stops the card

* Phase 0: `P01`-`P04` failing: fix the host first. `PF` with a byte: read it before typing. `P05`
  with no uptime line: stop.
* `R01` or `I01` not ending at `<RealTek>`: nothing is uploaded and `looprun` is not run. With
  `--skip S4` `looprun`'s `A0a` reads only its own `S4` capture, never `R01`'s, so the cell's own
  ending is the guard. The loader then boots S from slot B (both cells come before `I10`): a second
  try is the declared off-card cell `X-R01b` or `X-I01b`, or the card stops.
* `R02` or `I02` stopping before `S7` leaves the board at `<RealTek>`: retry at once with
  `--attempt 2`, never `--force`; a second failure stops the card, and the board does not stay at
  the prompt (`NET-165`): `X-R02j` or `X-I02j` takes it off, or, on the owner's word, a power cycle.
  Failing on `A4` alone: the shell probe `X-R02p` or `X-I02p` (`FW-252`).
* **D1, after `R16`.** Phase 2 runs only if every one of these holds (the plan's B1, read
  strictly): `R02` PASS; `R03`'s `vlan` line reads `rc 0`, `vm 0`, `final 0`, `to 0`, `rb 0`,
  `vw 0000`, `nw 01`, `rw 00`; `R03` `n_writes 18`; `R03`'s live `SWTCR0` with bit 18 clear,
  `PVCR0`-`3` `00080008` and `FFCR` `00000003`; `R04` and `R05` as predicted; `R10` `4 received` and
  `ping_rc=0`; `R14` `4 packets received`; `rlx0`'s RX grown across `R10`. Any one failing: **stop.
  No install, no flash write.** The board stays at the release image's shell, in RAM; a reset would
  boot S from slot B, as before the card. The fallback -- netif slot 0 with `rlx0`'s own address,
  ruling O1 -- is a rebuild at the desk, not a bench action. Every other phase-1 prediction is a
  reading: a wrong one is recorded and does not stop the card.
* `I02` failing on any assertion but `A4`, or `I03` without `2 received`: no staging.
* `I08` with `img_err` other than `none`, or with `img_len` other than 1,110,176 after the re-reads
  `X-I08w1`-`3` allow: no arm and no install.
* `I10` without `RLXFW-SI-END OK rc=0 cmp=1`, or `I11` with `inst_reason` other than `OK` or
  `inst_cmp_diff` other than 0: no reboot; `I11`'s fields say what happened, and the owner decides.
  Slot B is outside the arm window, so S stays whole, and a flash boot falls back to B if A is bad
  (R8b's ten pulls, `bench/2026-10-07` `A1`-`A5`).
* `W01` or `C01` ending at `<RealTek>` or `refuse-action halt`: stop; a board at the loader prompt is
  not left there (`NET-165`): the owner chooses between `J BFC00000` (as `X-R02j`, which would
  boot flash again) and a power cycle, and nothing else is typed until then.
* `W02` or `C02` not PASS: stop; nothing else is typed; the record says what the boot capture shows.
* `W03`-`W16` failing: a result, recorded. Phase 4 still runs if the owner agrees: a cold boot that
  differs from the warm one is the risk `R6c-4`'s row names.
* `PF2` with any byte, or no `C01.timing`: the owner is not told to power on.

## Refuted by, and the control (the plan's, carried in)

**Refuted by**: any flash boot below 4/4 in either direction (`W10`, `W14`, `C10`, `C14`); `n_rx` 0
while the host's TX grows (`W08` → `W12`, `C08` → `C12`, against `W10`'s and `C10`'s `ip -s link`);
a table or register different from the write set (`W03`-`W06`, `C03`-`C06`: VLAN slot 8
`00807E3F` and the rest zero, netif zero, `PVCR0`-`3` `00080008`, `FFCR` 3, and the four verified
words); the `vlan` line's rc other than 0 (`R03`, `W03`, `C03`); `STOP_TLU` left set (`SWTCR0`
bit 18 [`d-stoptlu`] in `R03`, `W03`, `C03`, `R06`, `W06`, `C06`); B1 failing (D1). If the CPU
port's out counters move and `rlx0` still counts nothing, `QNUMCR`'s CPU field (`00041249` on the
flash path, `00001249` on the RAM path; `W07`, `C07`, `R07`) is the first suspect.

**Control**: 2026-10-08's flash boots without the verb -- `X-V06q` (after a watchdog reset),
`X-V08q` (cold) and seating A (`bench/2026-10-08b`): no `vlan` line, `n_writes` 6, `PVCR0`-`3`
`00010001`, `FFCR` 0, every table slot zero, port 3's discard columns counting every frame from the
host, the host's ping 0 of 3 and its entry `FAILED`, and the board's ping 0 of 4: its six ARP
requests reached the host and the host's six replies were discarded at port 3 (`H14`, `A15`).

## What this card does not establish

* More than one warm and one cold flash boot of the release image; a cold boot with ESC.
* Which rule discarded the frames before: ingress filtering or the lookup of a VID with no entry.
  The write set changes the PVIDs and the table together.
* Which of the five register stores and the one table write is sufficient: the group is written as
  a unit (O1) and no cell takes it apart.
* How many `TCR` words the engine copies: the read-backs compare all eight words, and equality says
  the slot reads back as stored, not which words the engine took.
* What the switch does with a frame that arrives while `STOP_TLU` holds the lookups on the RAM path,
  where `TRXRDY` is already set: a frame lost there does not show in a later ping.
* That a second `vlan` stores nothing on silicon: no cell types it (the harness's `K55` does).
* Anything about `MACCR`, `QNUMCR`'s CPU field, the PHY patch or `LEDCREG` beyond what is read here
  (`MACCR` and `QNUMCR` are read, the others not; none is written).
* Anything under load, on a second port, or on the vendor's firmware. The host's adapter ran at
  100 Mb/s half duplex in seating A.
* That T would be refused by a device without the production key: the host's `slotcheck` showed the
  development key halting on `sig` (`slot-V4.log`), not the device.
* Flash, as in the closing count: two writes that cancel; any byte outside slot A (which `I10`
  compares whole) and the two containers (which `rlxboot` digests); slot B's 70,496 bytes after S. No
  region is compared with the 2026-08-16 dump: there is no `FLR` on this card.
* That the column-for-column MIB equality holds exactly under the host's background frames: deltas
  only, and only across one exchange each.

## The image each cell runs on

```cardimage
armed	I04 I05 I07 I08 I09 I10 I11 W01
```

## The owner's dated yes, one row per flash-writing payload

```owner-yes
2026-10-08	echo install slotA sha=113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8 > /proc/rtl819x-spi
```

The owner's yes: 2026-10-08, about 20:15, the owner's reply "yes" to the main session's message
that quoted this payload and said it would be used only if D1 holds. Written in by the main
session before power; until it was, `cardcheck commands` refused `I10` (rc 1).

## Declared off-card cells

Each runs only on its condition, and each is recorded with its reason; none can write flash.
* `X-R01b`, `X-I01b`: `busybox reboot -f` with `--esc-after 30 --until '<RealTek>' --seconds 60`,
  only if `R01` or `I01` missed the prompt and the loader booted flash.
* `X-R02p`, `X-I02p`: `cat /proc/uptime`, only if `looprun` fails on `A4` alone (`FW-252`).
* `X-I08w1`-`3` (main session's review): `cat /proc/rtl819x-spi` with `--idle 3 --seconds 20`, about
  10 s apart, only while `I08` or the last of them reads `img_len` short with `img_err none`
  (`FW-248`: after a short first read, the next read was whole in 14 of 14). The gate is the last
  read; a third short one stops the card.
* `looprun --attempt 2` of `R02` or `I02`, only if the first attempt stopped before `S7`.
* `X-R02j`, `X-I02j`: `J BFC00000` with no ESC, `--until 'for a list of built-in
  commands[.][^#]{1,8}# |refuse-action halt|<RealTek>' --seconds 180`, only if that retry failed too
  with the board at `<RealTek>`: the loader runs again and boots S from slot B (推: `looprun`'s
  round-1 `S4` sends the same jump, with ESC, to come back to the prompt). A loader verb, no write.

## Every capture prefix (for `check-predictions`)

```cells
bench/2026-10-08c/P01
bench/2026-10-08c/P02
bench/2026-10-08c/P03
bench/2026-10-08c/P04
bench/2026-10-08c/PF
bench/2026-10-08c/P05
bench/2026-10-08c/R01
bench/2026-10-08c/R02
bench/2026-10-08c/R03
bench/2026-10-08c/R04
bench/2026-10-08c/R05
bench/2026-10-08c/R06
bench/2026-10-08c/R07
bench/2026-10-08c/R08
bench/2026-10-08c/R09
bench/2026-10-08c/R10
bench/2026-10-08c/R11
bench/2026-10-08c/R12
bench/2026-10-08c/R13
bench/2026-10-08c/R14
bench/2026-10-08c/R15
bench/2026-10-08c/R16
bench/2026-10-08c/I01
bench/2026-10-08c/I02
bench/2026-10-08c/I03
bench/2026-10-08c/I04
bench/2026-10-08c/I05
bench/2026-10-08c/I06
bench/2026-10-08c/I07
bench/2026-10-08c/I08
bench/2026-10-08c/I09
bench/2026-10-08c/I10
bench/2026-10-08c/I11
bench/2026-10-08c/W01
bench/2026-10-08c/W02
bench/2026-10-08c/W03
bench/2026-10-08c/W04
bench/2026-10-08c/W05
bench/2026-10-08c/W06
bench/2026-10-08c/W07
bench/2026-10-08c/W08
bench/2026-10-08c/W09
bench/2026-10-08c/W10
bench/2026-10-08c/W11
bench/2026-10-08c/W12
bench/2026-10-08c/W13
bench/2026-10-08c/W14
bench/2026-10-08c/W15
bench/2026-10-08c/W16
bench/2026-10-08c/W17
bench/2026-10-08c/PF2
bench/2026-10-08c/C01
bench/2026-10-08c/C02
bench/2026-10-08c/C03
bench/2026-10-08c/C04
bench/2026-10-08c/C05
bench/2026-10-08c/C06
bench/2026-10-08c/C07
bench/2026-10-08c/C08
bench/2026-10-08c/C09
bench/2026-10-08c/C10
bench/2026-10-08c/C11
bench/2026-10-08c/C12
bench/2026-10-08c/C13
bench/2026-10-08c/C14
bench/2026-10-08c/C15
bench/2026-10-08c/C16
bench/2026-10-08c/C17
```

## The numbers

`d-*` rows pin a line of `derive.out`; the rest read the artefact, the build record, the build
clone's source or the bench record directly. Paths without a leading `/` are the repository's.

```cardnum
derive-py	33165bff630417ea1a2d2ecbd4d449787308ab607e18ab9b62fc37a7a9d6984e	sha256 /home/key/fwre-work/rebuild/s129/r6c4/derive.py
derive-out	372c7457a834ad2e48e6df98811c58291da1a569158bf73e74547266a3a31ed4	sha256 /home/key/fwre-work/rebuild/s129/r6c4/derive.out
img-bytes	1110016	size /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img
img-sha256	295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd	sha256 /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img
armed-bytes	1117184	size /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.img
armed-sha256	9328dcf9ddaaa4b4f8bc1e586d2993c7a670f2fd13d3f72c16f8da6cd16cd735	sha256 /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.img
T-bytes	1110176	size /home/key/fwre-work/rebuild/s128/p/run/r6c/signed/T.rlxu
T-sha256	113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8	sha256 /home/key/fwre-work/rebuild/s128/p/run/r6c/signed/T.rlxu
T-magic	524C5855	word32 /home/key/fwre-work/rebuild/s128/p/run/r6c/signed/T.rlxu 0
S-bytes	1109152	size /home/key/fwre-work/rebuild/s126/p/run/v10/signed/S.rlxu
S-sha256	3f728d56a12544d5e37f8a22c3bdd23f98afe6c0c81187e0d06053ebff608d2b	sha256 /home/key/fwre-work/rebuild/s126/p/run/v10/signed/S.rlxu
img-recipe	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest ^recipe_id\t9bb2bec7$
img-green	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest ^verdict\tgreen$
img-config	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest ^config_sha256\t981477c23034906aa2376e87ac4b50530eba27b0fcef18653d9206e5b4357515$
v10-config	1	count /home/key/fwre-work/rebuild/s126/p/run/v10/out/mainline-6a11de02.kbuild-manifest ^config_sha256\t981477c23034906aa2376e87ac4b50530eba27b0fcef18653d9206e5b4357515$
img-nfjrom	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.rtkimage-record.tsv ^nfjrom_sha256\t295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd$
img-tripwire	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN
img-twice	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/img/s128p-r6c-mB/rtkimage-record.tsv ^nfjrom_sha256\t295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd$
armed-twice	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/img/s128p-r6c-aB/rtkimage-record.tsv ^nfjrom_sha256\t9328dcf9ddaaa4b4f8bc1e586d2993c7a670f2fd13d3f72c16f8da6cd16cd735$
armed-recipe	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.kbuild-manifest ^recipe_id\t8dce09c5$
armed-green	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.kbuild-manifest ^verdict\tgreen$
T-accepted	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/log/verify-T.log ACCEPTED: 1110016-byte payload -> 0x80500000, entry 0x80500000, version 5, recipe 9bb2bec7, flash destination 0x070000 form whole$
T-slotB-refused	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/log/verify-T-wrong.log REJECTED at step 2 \(flash_match\)
slotcheck-A	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/log/slot-V2.log ^OUTCOME A version=5 recipe=9bb2bec7 payload_len=1110016
slotcheck-B	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/log/slot-V2.log ^RLXBOOT-VERDICT B ok ver=4$
img-map-vlan-read	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.System.map ^[0-9a-f]{8} t rtl819x_vlan_read$
img-map-vlan-rval	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.System.map ^[0-9a-f]{8} r rtl819x_vlan_rval$
img-map-sw-write	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.System.map ^[0-9a-f]{8} t rtl819x_sw_write_proc$
img-map-inst	0	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.System.map ^[0-9a-f]{8} r rlxfw_spi_inst_regions$
armed-map-vlan-read	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.System.map ^[0-9a-f]{8} t rtl819x_vlan_read$
armed-map-inst	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/armed-8dce09c5.System.map ^[0-9a-f]{8} r rlxfw_spi_inst_regions$
src-switch	ed62234410944f43a770a8d7274b256a8860fa3611aa05975b25b5c21400eab0	sha256 /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c
src-switch-armed	ed62234410944f43a770a8d7274b256a8860fa3611aa05975b25b5c21400eab0	sha256 /home/key/fwre-work/rebuild/s128/p/run/r6c/armed/config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c
src-switch-repo	ed62234410944f43a770a8d7274b256a8860fa3611aa05975b25b5c21400eab0	sha256 config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c
src-slotA-base	1	count /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h ^#define RLXFW_SPI_INST_SLOTA_BASE\t0x00070000u$
src-slotA-size	1	count /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi-install.h ^#define RLXFW_SPI_INST_SLOTA_SIZE\t0x00120000u
src-view-qnumcr	1	count /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-view.c \{ 0xBB804754, +1, 1, 0 \},\t/\* QNUMCR
src-voff-plitimr	1	count /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t0x4A18, 0x4A00, 0x4A1C, 0x4420$
src-nic-mac	1	count /home/key/fwre-work/rebuild/s128/p/clone/config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^static const u8 nic_mac\[6\] = \{ 0x02, 0x52, 0x4C, 0x58, 0x46, 0x57 \};$
ctl-a02-pvcr0	1	count bench/2026-10-08b/A02.log ^r PVCR0 +4A08 00010001 00010001 11$
ctl-a02-ffcr	1	count bench/2026-10-08b/A02.log ^r FFCR +4428 00000000 00000000 10$
ctl-a02-n-writes	1	count bench/2026-10-08b/A02.log ^n_writes 6$
ctl-a05-zero	16	count bench/2026-10-08b/A05.log ^s[0-9][0-9] t1 eq 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000$
ctl-a06-zero	8	count bench/2026-10-08b/A06.log ^s[0-9][0-9] t1 eq 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000$
ctl-v08q-ping	1	count bench/2026-10-08/X-V08q-p.log 100% packet loss
ram-m2vv-s08	1	count bench/2026-09-28/M2-VV.log ^s08 t1 eq 00807E3F 00000000 00000000 00000000 00000000 00000000 00000000 00000000$
ram-m2vn-zero	7	count bench/2026-09-28/M2-VN.log ^s0[0-7] t1 eq 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000$
ram-m2vn-s00	0	count bench/2026-09-28/M2-VN.log ^s00 t1 eq 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000$
ram-persw-swtaa	1	count bench/2026-10-04/PER-SW.log ^r SWTAA +4D08 BB060100 BB060100 10$
ping-four	1	count notes/rootfs-census.md ^\*\*量: this image's .ping. ignores .-c. and always sends exactly four packets\.\*\*$
d-pid1	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^pid1_switch_verbs unlock_i-mean-it,init,vlan,start$
d-entry	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^vlan_entry 00807E3F$
d-slot	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^vlan_entry_slot 8$
d-pvcr	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^pvcr_target 00080008$
d-ffcr	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ffcr_target 00000003$
d-vr	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^vr 00000001 000001FF 00000000 07FAC688$
d-cmd	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^swtacr_cmd 9$
d-stoptlu	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^stop_tlu_bit 18$
d-boot52	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^boot_reads_no_vlan 52$
d-boot6	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^boot_stores_no_vlan 6$
d-cat90	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^cat_reads 90$
d-m52f	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^measured_no_vlan_n_reads_flash 52$
d-m52r	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^measured_no_vlan_n_reads_ram 52$
d-m90	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^measured_cat_reads_flash 90$
d-m6f	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^measured_no_vlan_n_writes_flash 6$
d-m6r	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^measured_no_vlan_n_writes_ram 6$
d-f17	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_vlan_stores 17$
d-ftw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_table_writes 1$
d-f23	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_n_writes 23$
d-f79	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_vlan_reads_fixed 79$
d-f131	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_first_cat_n_reads_fixed 131$
d-fld	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_ld 784$
d-fvw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_vw 0100$
d-fnw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_nw 00$
d-frw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_rw 1F$
d-fswtaa	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_swtaa_after BB060100$
d-fregs	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_regs_before 00010001 00010001 00010001 00010001 00000000$
d-fver	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_ver_before 00000001 000001FF 00000000 07FAC688$
d-fdiff	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^flash_slots_differing 8$
d-r12	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_vlan_stores 12$
d-rtw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_table_writes 1$
d-r18	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_n_writes 18$
d-r74	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_vlan_reads_fixed 74$
d-r126	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_first_cat_n_reads_fixed 126$
d-rld	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_ld 784$
d-rvw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_vw 0000$
d-rnw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_nw 01$
d-rrw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_rw 00$
d-rswtaa	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_swtaa_after BB040000$
d-rregs	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_regs_before 00080008 00080008 00080008 00080008 00000003$
d-rver	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_ver_before 00000001 000001FF 00000000 07FAC688$
d-rdiff	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^ram_slots_differing 16$
d-second	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^second_vlan_stores 0$
d-wk5	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^warmkept_vlan_stores 5$
d-wktw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^warmkept_table_writes 0$
d-wk11	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^warmkept_n_writes 11$
d-wkvw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^warmkept_vw 0000$
d-wkrw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^warmkept_rw 1F$
d-abase	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^slotA_base 0x70000$
d-aend	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^slotA_end 0x190000$
d-asize	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^slotA_size 1179648$
d-arm	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^arm_line arm_0x70000_0x190000_0x120000$
d-tlen	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_len 1110176$
d-tse	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_inst_n_se 288$
d-tpp	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_inst_n_pp 4337$
d-tops	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_inst_ops 4625$
d-terased	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_inst_erased 1179648$
d-tcmp	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_inst_cmp_bytes 1179648$
d-tE	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_si_E_lines 18$
d-tP	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_si_P_lines 17$
d-tdots	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^T_rlxboot_dots 16$
d-slen	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^S_len 1109152$
d-spp	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^S_inst_n_pp_model 4333$
d-sppm	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^S_inst_n_pp_measured 4333$
d-sdots	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^S_rlxboot_dots 16$
d-a17u	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^A17_uptime 33159\.07$
d-a17t	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^A17_t0_real 1791431932\.238448$
d-v06sw5	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V06_warm_flash_PVCR0_latch 00010001$
d-v06sw4	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V06_warm_flash_VCR0_latch 000001FF$
d-qf	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^QNUMCR_flash_cold_A09 00041249$
d-qr3	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^QNUMCR_ram_I3 00001249$
d-qr6	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^QNUMCR_ram_I6 00001249$
d-mac	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^rlx0_mac 02:52:4c:58:46:57$
d-ip	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^lan_ip 10\.1\.1\.1$
d-tj	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V02_J_to_shell_s 10\.4$
d-tw	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V06_reboot_to_shell_s 15\.7$
d-tc	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V08_poweron_to_shell_s 15\.6$
d-tins	1	count /home/key/fwre-work/rebuild/s129/r6c4/derive.out ^V05b_install_ms 11340$
```

## Closing count (filled after the cells)

Power actions __ (planned 2: `PF2`'s OFF and `C01`'s ON) · flash-writing commands __ (planned 1:
`I10`, under the owner's yes of __________) · `FLW` / `EW` / `EB` / non-zero `AUTOBURN` __ (planned
0) · `FLR` __ (planned 0) · the loader's `AUTOBURN` word read back `00000000` before each upload
(`R02`, `I02`: `A0b`) · rlxfw's `n_writes`: `I11` __ (predicted 4,625 = 288 sector erases + 4,337
page programs), `W17` __ and `C17` __ (predicted 0) · the bracket's reach: `I10`'s read-back of slot
A's 1,179,648 bytes (`inst_cmp_bytes` __, `inst_cmp_diff` __), and `rlxboot`'s digest of slot A's
1,110,176 and slot B's 1,109,152 bytes on both flash boots (`W01`, `C01`). What it cannot see: two
writes that cancel; every byte outside slot A and the two containers; no region compared with the
2026-08-16 dump.
