# v1.0 -- the qualification seating: the release image from RAM, then from slot B through rlxboot, 2026-10-08

Written by hand in the 127th segment, under the relaxed process (not frozen, no
predictions file).  It qualifies on the device the image `v1.0` releases:
`mainline-6a11de02.img`, built twice byte-equal from `f257a848`, which differs
from the `f9adc9e8` that every `R8b` reading ran only in the recipe id (`FW-254`).
Phase 1 boots it from RAM with `looprun` and writes nothing.  Phase 2 boots the
armed image `6b1bde59` from RAM, which installs container S -- version 4, slot B,
signed with the owner's production key -- through the product's own update path.
Phase 3 lets `rlxboot` boot S from flash after a `busybox reboot -f`, and phase 4
from cold: the owner cuts the power and restores it, two power actions, each on
the owner's word.  One flash-writing command (`V05b`, under the owner's dated yes
below); no `FLW`, `EW`, `EB` or non-zero `AUTOBURN`; no `FLR`.  NOT relaxed: the
flash rules, `H601`, the power handshake, `NET-165`, and the owner's dated yes for
the write (`FW-113`).

The board starts ON at slot A's shell (R, version 3, `f9adc9e8`), where the 125th
segment left it, so no cell before phase 4 needs a power action.  The pre-flight `PF` therefore
runs with the board idle at a shell rather than off.  An idle shell prints
nothing, so it is judged the same way: three artefacts, ~3.08 s, 0 bytes.  Any
byte in it is a finding to read, not a pass.

## Abbreviations

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`

Payloads: the release image `a3a75f8c92488c4adb22fc370088308723824251d70aca28c1002cb8587f1178` (1,108,992 bytes, recipe `6a11de02`); container S `3f728d56a12544d5e37f8a22c3bdd23f98afe6c0c81187e0d06053ebff608d2b` (1,109,152 bytes: version 4, slot B at `0x190000`, form whole, recipe `6a11de02`); the armed image `05d4b635c49e7128244a7cce8630588c438879eb3637cc9e524a8a34e58fe100` (recipe `6b1bde59`).  On the device before this card: slot A holds R `5a38d96922ec89136ed88e56205b045521e85772308431539ce18f8d093564df` (version 3), slot B holds Q `9578da72a29871f2f443b02e226d72590f03229cf53503e02a47fa9166622a00` (version 2), and `0x010000`/`0x020000` hold the `cs6c` `rlxboot` and rescue copy (build `127a71cf`).

**Phase 0 -- the host, then the pre-flight and a shell probe**

```
HOST bench/2026-10-08/P01 :: pgrep -a -f rlxfw-keeper
HOST bench/2026-10-08/P02 :: ip -4 addr show enxfc19286184c9
HOST bench/2026-10-08/P03 :: /usr/bin/python3 tools/sendimg.py --self-test
HOST bench/2026-10-08/P04 :: /usr/bin/python3 tools/bootslot.py --self-test
CAP --out bench/2026-10-08/PF --seconds 3
CAP --out bench/2026-10-08/P05 --send 'cat /proc/uptime' --idle 3 --seconds 20
```

**Phase 1 -- the release image from RAM; no write**

```
CAP --out bench/2026-10-08/V01 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-08/V02 :: /usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-10-08/ --skip S2,S3,S4 --recipe-override 6a11de02 --dwell-seconds 5 --boot-until 'job control turned off[^#]{1,2}# |Booting[.][.][.]|---RealTek' --cell V02 --image /home/key/fwre-work/rebuild/s126/p/run/v10/out/mainline-6a11de02.img --image-sha256 a3a75f8c92488c4adb22fc370088308723824251d70aca28c1002cb8587f1178 --iterations 1
```

**Phase 2 -- the armed image from RAM installs S into slot B: the one write**

```
CAP --out bench/2026-10-08/V03 --send 'busybox reboot -f' --esc-after 30 --until '<RealTek>' --seconds 60
HOST bench/2026-10-08/V04 :: /usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-10-08/ --skip S2,S3,S4 --recipe-override 6b1bde59 --dwell-seconds 5 --boot-until 'job control turned off[^#]{1,2}# |Booting[.][.][.]|---RealTek' --cell V04 --image /home/key/fwre-work/rebuild/s125/fix/out/armed-6b1bde59.img --image-sha256 05d4b635c49e7128244a7cce8630588c438879eb3637cc9e524a8a34e58fe100 --iterations 1
CAP --out bench/2026-10-08/V05s1 --send 'echo img reset > /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08/V05s2 --send 'busybox nc -l -p 5000 </dev/null >/proc/rtl819x-spi-img &' --idle 2 --seconds 10
HOST bench/2026-10-08/V05s3 :: /usr/bin/python3 tools/sendimg.py send --to 10.1.1.1:5000 --src 10.1.1.2 --file /home/key/fwre-work/rebuild/s126/p/run/v10/signed/S.rlxu --sha256 3f728d56a12544d5e37f8a22c3bdd23f98afe6c0c81187e0d06053ebff608d2b
CAP --out bench/2026-10-08/V05s4 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08/V05a --send 'echo arm 0x190000 0x2b0000 0x120000 > /proc/rtl819x-spi' --idle 3 --seconds 20
CAP --out bench/2026-10-08/V05b --send 'echo install slotB sha=3f728d56a12544d5e37f8a22c3bdd23f98afe6c0c81187e0d06053ebff608d2b > /proc/rtl819x-spi' --until 'RLXFW-SI-END' --idle 30 --seconds 900
CAP --out bench/2026-10-08/V05c --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 20
```

**Phase 3 -- `rlxboot` boots S from slot B**

```
CAP --out bench/2026-10-08/V06 --send 'busybox reboot -f' --until 'for a list of built-in commands[.][^#]{1,8}# |refuse-action halt' --seconds 180
HOST bench/2026-10-08/V07 :: /usr/bin/python3 tools/bootslot.py judge bench/2026-10-08/V06.log --expect-slot B --expect-a ok:3 --expect-b ok:4 --build-manifest /home/key/fwre-work/rebuild/s126/p/run/v10/out/mainline-6a11de02.kbuild-manifest
```

**Phase 4 -- from cold: owner OFF, the pre-flight with the board off, the window opened, owner ON (no ESC)**

```
CAP --out bench/2026-10-08/PF2 --seconds 3
CAP --out bench/2026-10-08/V08 --until 'for a list of built-in commands[.][^#]{1,8}# |refuse-action halt' --seconds 300
HOST bench/2026-10-08/V09 :: /usr/bin/python3 tools/bootslot.py judge bench/2026-10-08/V08.log --expect-slot B --expect-a ok:3 --expect-b ok:4 --build-manifest /home/key/fwre-work/rebuild/s126/p/run/v10/out/mainline-6a11de02.kbuild-manifest
```

The handshake: the owner is asked, and answers, before each power action.  `PF2`
runs once the owner says the board is off.  `V08` is opened only after the
owner's answer, and the owner is told to power on only once `V08.timing` exists,
with the latest time that leaves the boot 60 s inside the window.

Declared off-card cells, run by the session's scripts between the cells above:
`X-V02n`, `X-V04n`, `X-V06n` and `X-V08n` flush the host's neighbour entry, `ping -c 2 -W 2
10.1.1.1` and show the entry again, so the host reaches the image that has just
booted; `X-V04n` must show the armed image's MAC `02:52:4c:58:46:57` before
`V05s3`.  `X-V05w<n>` reads `cat /proc/rtl819x-spi` until `img_len` is 1,109,152
(`FW-248`).  A shell probe `X-V02p` or `X-V04p` (`cat /proc/uptime`) runs only if
`looprun` fails on `A4` alone (`FW-252`).

## What stops the card

- `V01` or `V03` without `<RealTek>`: nothing is uploaded (`looprun`'s `A0a` refuses as well).
- `V02` not printing `RLXFW-ID0=6A11DE02`, or failing on any assertion but `A4`: stop before phase 2. The release image does not boot from RAM, and nothing has been written.
- `V04` failing on any assertion but `A4`, or `X-V04n` without the armed image's MAC: no staging.
- `V05s4` with `img_len` other than 1,109,152 or `img_err` other than `none`: no arm and no install.
- `V05b` without `RLXFW-SI-END OK rc=0 cmp=1`: no reboot; `V05c`'s `/proc` fields say what happened.
- `V07` not `PASS`: no phase 4; the record says so, and the device stays as `V06` left it.
- `PF2` with any byte, or `V08` with no `V08.timing`: the owner is not told to power on.

## What this card does not establish

- More than one cold power-on of the release image (`V08` is one), or a cold power-on with ESC under `cs6c` (`FW-249` measured warm boots only).
- That the release image behaves as `f9adc9e8` did under load. `FW-254` is the desk argument: the two `vmlinux` differ in the 8 bytes of the recipe id.
- That S would be refused by a device without the production key: `build-v10.sh verify` showed that on the host (`V4`: the development key halts on `sig`), not on the device.

## The image each cell runs on

```cardimage
armed	V05s1 V05s2 V05s4 V05a V05b V05c V06
```

## The owner's dated yes, one row per flash-writing payload

```owner-yes
2026-10-08	echo install slotB sha=3f728d56a12544d5e37f8a22c3bdd23f98afe6c0c81187e0d06053ebff608d2b > /proc/rtl819x-spi
```
