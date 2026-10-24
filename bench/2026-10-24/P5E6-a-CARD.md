# P5E6-a -- the v1.0 video, filmed live: a cold boot from slot A, the release image from RAM, one flipped bit refused by `rlxboot` in RAM, the flash boot that follows, the shell, 2026-10-24

**declared date 2026-10-24** · attempt `a` · drafted in the 139th segment (2026-10-19) for a seating
whose day was not known, and dated by `mkcard.sh`, which replaces two strings and nothing else ·
`P5e`, step `P5e-6` · relaxed process, not frozen. NOT relaxed: the flash rules, `H601`, the power
handshake (the owner is the operator and the one who powers), `NET-165`. The owner films the
terminal while `tools/cardrun.py` runs these cells; nothing here is replayed.

**The state before the card, from the bench record.** 量 slot A holds T, version 5
(`113f55427c0798ec9fbf6ecd7f6b5ddea90bc4573496f500931b9df4eacc9ba8`, installed by
`bench/2026-10-08c/I10`); slot B holds S, version 4 (`3f728d56…`, `bench/2026-10-08/V05b`);
`0x010000` and `0x020000` hold the `cs6c` `rlxboot` (`RLXBOOT-V1 build=127a71cf`) and its rescue
copy. 量 `bench/2026-10-08c/C01` (cold) and `W01` (watchdog reset, no ESC) booted T from slot A,
`bootslot judge` PASS both. 讀 the 130th to 138th segments made no power action and no write
(`LOG.md`), so a power-on today boots T from slot A.

**What it may do.** Zero flash-writing commands: zero `FLW`, `EW`, `EB`, non-zero `AUTOBURN`,
`FLR`; nothing written to `/proc/rtl819x-spi`; no armed image and no container T anywhere on it.
Uploads land in RAM only, each after a rescue that sets `AutoBurning=0` and after `DW 8040D4A0 1`
reads `00000000` (`C-6`): the release image through `looprun` (`S5b` is mandatory there), and
`R8a`'s two files through `loader-tftp.py`, each gated by `take.sh`. Power actions: the owner's
power-on in take 1, with the board off before it; none in take 2. The board never waits at
`<RealTek>`: every cell that reaches the prompt is followed in the same `cardrun` call by the cell
that leaves it (`NET-165`).

**Why `J 81800000` carries no `--esc-after`.** The rule exists so that a reset does not boot the
vendor firmware. 量 flash no longer holds it on the boot path: after a reset the loader loads
`rlxboot` from `0x010000`, which boots T from slot A (`C01`, `W01`). `R8a`'s `rlxboot` build
`6395889d` refuses the flipped container, prints `refuse-action reset` and arms the watchdog
(`bench/2026-09-30/R8A-2j`); with no ESC the loader then boots flash, so one capture shows the
refusal, the reset and the boot through `rlxboot` from slot A. `bootslot judge` reads one `rlxboot`
run per capture, so `Va32` copies the capture from its second `RLXBOOT-V1` line on, outside the
repository, and `Va33` judges the copy.

**The files `R8a` staged, unchanged since 2026-09-30** (sha256 rows below; 讀 their build log
`/home/key/fwre-work/rebuild/s118/r8run/logs/build.out`): `rlxboot.bin`, 16,240 bytes, build
`6395889d`, development key, format 1, linked at `0x81800000`, `RLXBOOT_REFUSE_RESET 1`;
`B-flip.rlxu`, `A-good.rlxu` with bit 0 of the byte at file offset `0x080000` flipped, header
identical. Recorded: `R8A-2j` printed `RLXBOOT-SIG ok`, `RLXBOOT-DIGEST bad`,
`RLXBOOT-REFUSE digest`, `refuse-action reset`. It is the `R8a` build, not the flash `rlxboot`:
the caption says so.

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`

## The cells

**Take 1 -- 60 s: the pre-flight with the board off, then the owner's power-on, a boot from slot A
through `rlxboot`, `rlx0` both ways, `httpd`**

```
CAP --out bench/2026-10-24/Va00 --seconds 3
CAP --out bench/2026-10-24/Va01 --until 'for a list of built-in commands[.][^#]{1,8}# |refuse-action halt|<RealTek>' --seconds 300
HOST bench/2026-10-24/Va02 :: /usr/bin/python3 tools/bootslot.py judge bench/2026-10-24/Va01.log --expect-slot A --expect-a ok:5 --expect-b ok:4 --expect-from 05010000 --build-manifest /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest
CAP --out bench/2026-10-24/Va03 --send 'ping -c 4 10.1.1.2' --until 'packet loss' --seconds 35
HOST bench/2026-10-24/Va04 :: ping -c 4 -W 2 10.1.1.1
HOST bench/2026-10-24/Va05 :: curl -sS -m 8 http://10.1.1.1/api/status; echo; curl -sS -m 8 -o /dev/null -w 'GET / -> HTTP %{http_code}, %{size_download} bytes' http://10.1.1.1/; echo
```

**Take 2, part a -- the release image from RAM through the loader's prompt**

```
CAP --out bench/2026-10-24/Va10 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-24/Va11 :: /usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-10-24/ --skip S2,S3,S4 --recipe-override 9bb2bec7 --dwell-seconds 5 --boot-until 'for a list of built-in commands[.][^#]{1,8}# |Booting[.][.][.]|---RealTek' --cell Va11 --image /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img --image-sha256 295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd --iterations 1; echo looprun_rc=$?
HOST bench/2026-10-24/Va12 :: sleep 6
CAP --out bench/2026-10-24/Va13 --send 'cat /proc/uptime' --idle 3 --seconds 20
```

`Va11`'s exit status is printed, not obeyed: `looprun` exits 1 when only `A4` fails (`FW-252`,
five times in twenty-five runs), so `take.sh` gates on its log instead -- `A0b` reads `00000000`,
`A3` reads the id the manifest names, and no assertion but `A4` failed. When `A4` fails `looprun`
skips its dwell, so `Va12` waits six seconds for init to finish printing (the 257 bytes `FW-252`
measured) before `Va13`, `FW-252`'s own check that the shell is alive.

**Take 2, part b -- `R8a`'s `rlxboot` and the flipped container into RAM, the refusal, the reset,
the boot from slot A through the flash `rlxboot`**

```
CAP --out bench/2026-10-24/Va20 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-24/Va21 :: /usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x81800000 -o bench/2026-10-24/Va21-rescue.json
CAP --out bench/2026-10-24/Va22 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-10-24/Va23 :: ip -4 route get 10.1.1.1; ping -c 1 -W 1 10.1.1.1; ip -4 neigh show 10.1.1.1 dev enxfc19286184c9
HOST bench/2026-10-24/Va24 :: grep -qE '8040D4A0:[[:space:]]+00000000[[:space:]]' bench/2026-10-24/Va22.log && /usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin --filename Va24 --rescue-report bench/2026-10-24/Va21-rescue.json --expect-load 81800000 --yes
HOST bench/2026-10-24/Va25 :: /usr/bin/python3 upstream/tools/console-dump.py rescue --at-prompt --ip 10.1.1.1 --load-addr 0x81000000 -o bench/2026-10-24/Va25-rescue.json
CAP --out bench/2026-10-24/Va26 --send 'DW 8040D4A0 1' --idle 2 --seconds 6
HOST bench/2026-10-24/Va27 :: grep -qE '8040D4A0:[[:space:]]+00000000[[:space:]]' bench/2026-10-24/Va26.log && /usr/bin/python3 upstream/tools/loader-tftp.py put --host 10.1.1.1 --image /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu --filename Va27 --rescue-report bench/2026-10-24/Va25-rescue.json --expect-load 81000000 --yes
CAP --out bench/2026-10-24/Va28 --send 'DW 81800000 4' --idle 2 --seconds 8
CAP --out bench/2026-10-24/Va29 --send 'DW 81000000 4' --idle 2 --seconds 8
CAP --out bench/2026-10-24/Va30 --send 'DW 81080000 4' --idle 2 --seconds 8
CAP --out bench/2026-10-24/Va31 --send 'J 81800000' --until 'for a list of built-in commands[.][^#]{1,8}# |job control turned off[^#]{1,2}# |refuse-action halt|<RealTek>' --seconds 120
HOST bench/2026-10-24/Va32 :: /usr/bin/python3 /home/key/fwre-work/rebuild/s139/video/banner2.py bench/2026-10-24/Va31.log /home/key/fwre-work/rebuild/video/2026-10-24/Va31-flash.log
HOST bench/2026-10-24/Va33 :: /usr/bin/python3 tools/bootslot.py judge /home/key/fwre-work/rebuild/video/2026-10-24/Va31-flash.log --expect-slot A --expect-a ok:5 --expect-b ok:4 --expect-from 05010000 --build-manifest /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest
```

讀 `cardcheck commands` refuses `Va21`, `Va24`, `Va25` and `Va27` because `upstream/tools`
carries no argument contract it can check; their arguments are `R8a`'s, run on this board on
2026-09-30 (`$FWRE_WORK/rebuild/s118/r8run/30-plan.py`, `R8A-2a`/`2A`/`2b`/`2B`) with `upstream/`
at the same pin, and `mkcard.sh` exempts exactly those four names and stops on any other refusal,
or if one of the four stops being refused. Each upload cell also refuses by itself: `Va24` runs
`loader-tftp.py` only if `Va22`'s capture holds `8040D4A0:` and `00000000` (`Va27`, `Va26`'s),
so no order of running these cells uploads before the burn flag reads zero (`C-6`; `REG-23`: every
reset sets it back to 1). `take.sh` gates `Va22` and `Va26` on `00000000`, `Va23` on an `lladdr`, and `Va28`-`30` on
the words the `cardnum` rows derive from the two files -- `Va30`'s row is the flip's own -- before
the next cell; `Va31` on its `--until`, `RLXBOOT-DIGEST bad` and `RLXBOOT-REFUSE digest`.

**Take 2, part c -- the shell T booted: `rlx0` both ways, the privilege drops, `httpd`, the SPI
driver's write counters**

```
CAP --out bench/2026-10-24/Va40 --send 'ping -c 4 10.1.1.2' --until 'packet loss' --seconds 35
HOST bench/2026-10-24/Va41 :: ping -c 4 -W 2 10.1.1.1
CAP --out bench/2026-10-24/Va42 --send 'ps' --idle 3 --seconds 20
CAP --out bench/2026-10-24/Va43 --send 'busybox grep Uid /proc/13/status /proc/14/status' --idle 3 --seconds 20
CAP --out bench/2026-10-24/Va44 --send 'ls -l /proc/13/root' --idle 3 --seconds 20
HOST bench/2026-10-24/Va45 :: curl -sS -m 8 http://10.1.1.1/api/status; echo; curl -sS -m 8 -o /dev/null -w 'GET / -> HTTP %{http_code}, %{size_download} bytes' http://10.1.1.1/; echo
CAP --out bench/2026-10-24/Va46 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

`Va43` and `Va44` name PIDs 13 and 14 because 量 `C01` and `bench/2026-09-30/R78-ps` started
`httpd` as 13 and `dnsfwd` as 14; `Va42`'s `ps` is printed first so a different order shows.

## The image each cell runs on

```cardimage
mainline	Va03 Va13 Va40 Va42 Va43 Va44 Va46
```

## The owner's dated yes, one row per flash-writing payload

None: this card writes no flash, and `cardcheck commands` is what says so.

## Declared off-card cells

Each runs only on its condition; none can write flash.
* `X-Va10b`, `X-Va20b`: `busybox reboot -f` with `--esc-after 30 --until '<RealTek>'
  --seconds 60`, only if `Va10` or `Va20` missed the prompt and the loader booted flash.
* `looprun --attempt 2` of `Va11`, only if the first attempt stopped before `S7`.
* Any stop at `<RealTek>`: the owner powers the board off and on; it boots T from slot A.

## Every capture prefix (for `check-predictions`)

```cells
bench/2026-10-24/Va00
bench/2026-10-24/Va01
bench/2026-10-24/Va02
bench/2026-10-24/Va03
bench/2026-10-24/Va04
bench/2026-10-24/Va05
bench/2026-10-24/Va10
bench/2026-10-24/Va11
bench/2026-10-24/Va12
bench/2026-10-24/Va13
bench/2026-10-24/Va20
bench/2026-10-24/Va21
bench/2026-10-24/Va22
bench/2026-10-24/Va23
bench/2026-10-24/Va24
bench/2026-10-24/Va25
bench/2026-10-24/Va26
bench/2026-10-24/Va27
bench/2026-10-24/Va28
bench/2026-10-24/Va29
bench/2026-10-24/Va30
bench/2026-10-24/Va31
bench/2026-10-24/Va32
bench/2026-10-24/Va33
bench/2026-10-24/Va40
bench/2026-10-24/Va41
bench/2026-10-24/Va42
bench/2026-10-24/Va43
bench/2026-10-24/Va44
bench/2026-10-24/Va45
bench/2026-10-24/Va46
```

## The numbers

Every word a gate in `take.sh` compares is read from this fence at run time, never typed there.

```cardnum
img-bytes	1110016	size /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img
img-sha256	295d4f6aec14f8b6ee21ebccec05e6b5492d8785274afe676fbfa5a070fb86bd	sha256 /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.img
img-recipe	1	count /home/key/fwre-work/rebuild/s128/p/run/r6c/out/mainline-9bb2bec7.kbuild-manifest ^recipe_id\t9bb2bec7$
rlxboot-bytes	16240	size /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin
rlxboot-sha256	26a5a81f10e02d32d76aad6bcf50fe31bdb3cb113682a6f2e96c73c8d8bd3b8d	sha256 /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin
rlxboot-w0	3C1D8181	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin 0
rlxboot-w1	27BDC740	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin 4
rlxboot-w2	3C088180	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin 8
rlxboot-w3	25083F70	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/rlxboot.bin 12
flip-bytes	1114272	size /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu
flip-sha256	10ef4fae6e801d3ea6bffe9b3b2a71c34c33689f4c4e37da64bfa317d5b3ad1b	sha256 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu
flip-h0	524C5855	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 0
flip-h1	00010060	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 4
flip-h2	00000001	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 8
flip-h3	00110000	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 12
flip-w0	4BE4B216	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 524288
flip-w1	59B831AC	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 524292
flip-w2	492F8AFF	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 524296
flip-w3	5333CFF5	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/B-flip.rlxu 524300
good-w0	4AE4B216	word32 /home/key/fwre-work/rebuild/s118/r8run/stage/A-good.rlxu 524288
```

`good-w0` is the control on the flip row: the unflipped file's word, one bit away from `flip-w0`.

## What this card does not establish

That the flash `rlxboot` (`127a71cf`) refuses a flipped bit: the refusal filmed is `R8a`'s RAM build
`6395889d` under the development key. That `httpd` and `dnsfwd` are PIDs 13 and 14 on every boot.
Anything about a power cut during an update: not filmed (the owner's decision, 2026-10-19).
