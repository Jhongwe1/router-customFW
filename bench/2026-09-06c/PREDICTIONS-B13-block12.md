# Block 12 — `R5-4`: a `gpio_chip` of mine on `PABCD`, ten boots, and a button

**Written 2026-09-06, thirty-seventh segment, at the desk, before power.**
`R5-4`'s bench half. The desk half is done and its artefacts are frozen (§1).

🔴 **THIS CARD IS NOT FROZEN AND ITS DIRECTORY NAME IS A PREDICTION.**
`bench/` is *one directory per power cycle*, named for the day the power cycle
happened. This card was written on 2026-09-06 and the seating is **not
scheduled**. Seating 14's card carried a directory named for a day the seating
did not happen on, and that was defect ① of that block. So: if the seating is
not on 2026-09-06, **rename this directory and re-run the expansion in §4.3
before freezing** — the directory appears in exactly one place in §4.1 (`OUT`)
and once per line in §4.3, and `cardcheck` compares the two, so a half-done
rename is caught rather than typed.

🔴 **And freeze order**: run `tools/spec-check.py` **before** the freezing
commit. Seating 14 froze first, `C8` then found three header defects, and
repairing them made six capture cells "older than the prediction" — that card's
`check-predictions` has read `0 of 24` ever since, and the mtime evidence is not
recoverable. Two seconds.

---

## 0. What this block is, in one paragraph

`rtl819x-gpio` 1.0 registers a `struct gpio_chip` on the `PABCD` port at
`subsys_initcall`, reads the reset button through gpiolib, and **writes
nothing**. Ten boots establish that it registers and reports, with no oops.
Inside two of those boots the operator presses the button by hand while a `cat`
is running, which is what makes the ten boots contain *the thing the driver
does* rather than *the driver not crashing*. Two `tryout` cells make the write
guard refuse **on the silicon** at two different layers with two different
errnos. One cell reads a register nothing in this project has ever read.

---

## 1. The image, staged and pinned

| | |
|---|---|
| uploadable image | `$FWRE_WORK/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin` |
| bytes | **1,036,288** |
| sha256 | `7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660` |
| `RECIPE_ID` | `5da34246` → **the board must print `RLXFW-ID0=5DA34246`** |
| `vmlinux` | 3,978,029 bytes, sha256-16 `04cd5b151aae6df4`, kept beside the image |
| `System.map` | kept beside the image |
| build cell | `r54b` |

🔴 **`vmlinux` and `System.map` are staged beside the image on purpose.** In
seating 14 a mid-seating rebuild reused a cell name and overwrote the previous
image's two files; that card's `cardcheck numbers` has read `23 of 28` ever
since. `r54b` is this image's only cell name and nothing else will be built
under it.

### 1.1 What the desk already established, before power

Each of these is a reading taken at the desk and none of them needs the board.

| | |
|---|---|
| `FW-38` | `CONFIG_GPIOLIB` is unreachable on `arch/rlx` without `config/host-compat/0005`. Measured, with `CONFIG_SWAP` flipped in the same file in the same run as the positive control |
| `FW-39` | **the image contains no instruction that writes the GPIO block from this driver.** `n_writes`'s address is stored to **0** times; the two refusal counters are stored to **1** time each, which is the control |
| `REG-35` | the **vendor's** `rtl_gpio_init` writes `PABCD_CNR` and `PABCD_DIR` at `device_initcall` — after this driver's `subsys_initcall` |
| marks | `MK3`'s witness `rtl819x-pabcd` is present in the artefact (`rlxfw-marks verify`) |
| initramfs | `mkinitramfs verify`: **OK**, 31 entries, every one matching in kind, mode and dev |

---

## 2. The experiment, and why no boot holds the button

### 2.1 🔴 The button is NOT held through the loader, and that is a safety decision

The obvious design is five boots with the button released and five with it
held, comparing `G3`/`G5`. **It is not run.**

`BRD-05` establishes the button is a GPIO and not `RESET#`, and `REG-30`
establishes that one loader branch which reads it is not taken on this unit.
Neither establishes what the loader *does* with the pin it configures at
`0x804083AC`. A factory-reset path reached by holding a button through boot is
an ordinary thing for this class of device to have, and it would be a **flash
write** — on the unit with `H601` on it and no spare. **The reading that would
license that boot has not been taken, so the boot is not run.**

### 2.2 What replaces it, and it is a stronger comparison

A **within-boot paired triple**: released → held → released, three `cat`s of
`/proc/rtl819x-gpio` in one boot, with the operator's hand the only thing that
changes. Everything else — the image, the boot, the vendor's driver state, the
temperature — is held constant, which an across-boot comparison cannot claim.

🟢 **The negative control is in the same three readings.** `cnr` and `dir` must
be **identical** in all three, because pressing a button cannot change a pin's
function or direction. `dat` bit 5 and `btn_raw` must change and change **back**
— a one-way change is a stuck read, not a button.

### 2.3 What makes a boot count

All ten of: `RLXFW-ID0=5DA34246`; `G0`; `G1`; `G2`; `G3`; `G4=00000000`; `G5`;
`G6`; no oops text in the capture (`FW-36`); and `/proc/rtl819x-gpio` readable
with `added 1`, `add_rc 0`, `n_writes 0`.

---

## 3. Before power

1. `usbipd list`, then attach the CP2102 and the NIC. 🔴 **Re-read the busid
   every time** — the NIC moved `2-4` → `3-4` on 2026-09-06 without anything
   being unplugged.
2. A 3-second capture with the board OFF. **0 bytes is the pass**: it separates
   the adapter and the port from the board before a power cycle is spent.
3. `ip addr add 10.1.1.2/24 dev enxfc19286184c9` — 量 2026-09-06, the address
   does **not** survive a re-attach and has to be set again.
4. 🔴 **ESC ordering**: the capture opens the port first, the operator moves the
   power switch second, and **the operator replies and then waits ten more
   seconds** before anything else is typed.

---

## 4. The cells

### 4.1 The two invocations

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0`,
`OUT` = `--out bench/2026-09-06c/`. **Every row carries a terminator.**

`LOOP` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir
bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image
$FWRE_WORK/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin
--image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660`

🔴 **`--skip S2,S3` is necessary, not a convenience.** `S3` assembles from the
tree `S2` stages, and nothing carries that path when `S2` is skipped
(`notes/dev-loop.md` §10.3). `--skip S4` is chosen: every reset in this card
happens before `looprun` starts.

🔴 **Warm resets use `busybox reboot -f`, with the `-f`.** `FW-37`: without it
the command signals PID 1, and this image's PID 1 is `config/rlxfw-init.sh`, a
shell script that ignores it. Seating 14's card had the form without `-f` and
it cost a cycle to find out. 2.407 s from the command to `<RealTek>`.

🔴 **`ping` ignores `-c` on this image** (`NET-26`); it always sends 4. No cell
asks for another number.

🔴 **Eleven busybox symlinks exist** — `sh ash cat echo ls mount ps ifconfig
ping mkdir sleep`. Anything else is `busybox <name>`.

### 4.2 The rule

| capture | typed | expect | 🔴 stop if |
|---|---|---|---|
| **`Bn-A`** cold (n=1 only) | `CAP OUT Bn-A --esc 150 --esc-period 0.002 --seconds 165` | operator presses power inside the window; loader banner, then `<RealTek>` | no `<RealTek>` → the window was missed and the board is running the **vendor** firmware from flash. Power-cycle and repeat |
| **`Bn-A`** warm (n≥2) | `CAP OUT Bn-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12` | echo, reset, `<RealTek>` | no reset → the shell is gone; power-cycle |
| **`Bn-*`** | `LOOP --cell Bn` | five stages; the board prints `RLXFW-ID0=5DA34246` | `S5b` reads anything but `00000000` at `0x8040D4A0` → **nothing is uploaded**, and that guard is not skippable |
| **`Bn-P`** | `CAP OUT Bn-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20` | §5.1's field table | `added 0` → read `add_rc`; `n_writes` ≠ 0 → **stop the block**, §5.4 |

### 4.3 The expansion — one line per cell, and it is what gets typed

§4.2 is the RULE; this is the rule applied. It exists because a parameterised
row is invisible to the checker: seating 14's §4.1 alone showed `cardcheck
commands` **6 commands for 24 cells**. Expanded, that card went 6 → 29.

量, to be re-derived at freeze and cross-checked in **both** directions against
this card's own `cells` fence.

```
#-- boot 1, cold: the operator presses power inside this window
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-A --esc 150 --esc-period 0.002 --seconds 165
/usr/bin/python3 tools/looprun.py --mode bench --cell B1 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boot 1 only: the guard, refusing on the silicon at two different layers
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-T5 --send 'echo tryout 5 > /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-T12 --send 'echo tryout 12 > /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-TP --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boot 1 only: the framework path a real consumer takes
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-C --send 'echo claim > /proc/rtl819x-gpio ; echo sample > /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-CP --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boot 1 only: a word nothing in this project has read
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B1-U --send 'echo probe04 > /proc/rtl819x-gpio ; cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boot 2: warm, and the button triple.  OPERATOR ACTION between B2-BTN1 and B2-BTN2.
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B2-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B2 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B2-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B2-BTN1 --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B2-BTN2 --send 'sleep 6 ; cat /proc/rtl819x-gpio' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B2-BTN3 --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boot 3: warm, and the button triple a second time (n=2 for the paired reading)
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B3-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B3 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B3-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B3-BTN1 --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B3-BTN2 --send 'sleep 6 ; cat /proc/rtl819x-gpio' --seconds 30
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B3-BTN3 --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
#-- boots 4..10: warm, and the DoD's remaining boots
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B4-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B4 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B4-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B5-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B5 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B5-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B6-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B6 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B6-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B7-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B7 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B7-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B8-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B8 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B8-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B9-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B9 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B9-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B10-A --send 'busybox reboot -f' --esc-after 8 --esc-period 0.002 --seconds 12
/usr/bin/python3 tools/looprun.py --mode bench --cell B10 --out-dir bench/2026-09-06c --skip S2,S3,S4 --recipe-override 5da34246 --image /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin --image-sha256 7f3473da61cc11a4846e588abf75f913f01224b94379fb752f9aeac783b5d660
/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --out bench/2026-09-06c/B10-P --send 'cat /proc/rtl819x-gpio' --idle 3 --seconds 20
```

🔴 **`B2-BTN2` and `B3-BTN2` use `--seconds` ALONE, not `--idle`.** The cell
contains a `sleep 6`, which on the board is six seconds of silence, and `--idle`
would end the capture inside it. The operator presses and **holds** the button
during that sleep and keeps holding until the `cat` output appears.

### 4.4 The cells fence

```cells
B1-A B1-P B1-T5 B1-T12 B1-TP B1-C B1-CP B1-U
B2-A B2-P B2-BTN1 B2-BTN2 B2-BTN3
B3-A B3-P B3-BTN1 B3-BTN2 B3-BTN3
B4-A B4-P B5-A B5-P B6-A B6-P B7-A B7-P
B8-A B8-P B9-A B9-P B10-A B10-P
```

### 4.5 The numbers this card states, and where each is re-derived FROM

🔴 **Every row below names a FROZEN artefact.** Seating 14's card pointed
`cardnum` rows at `config/rlxfw-src/…/rtl819x-timer.c` — a live source file —
and the moment that driver was edited the card went red for a reason that had
nothing to do with the seating. A check that goes red on its own schedule
trains a reader to ignore the report. The staged `System.map` and `vmlinux`
beside the image carry the same facts and never move.

🟢 **The one-to-one is exact and it was cross-checked in both directions**:
**32 capture lines in §4.3, 32 cells in §4.4's fence**, neither list holding an
entry the other lacks. Unlike seating 14's card there is no duplicated `-A`
form, because boot 1 is always cold and boots 2–10 are always warm — the branch
that made that card's mapping two-to-one does not exist here. 33 `--send`
strings, longest **66** characters, **0** at or over `console-capture.py`'s
128-byte refusal.

```cardnum
img-bytes	1036288	size /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin
img-sha16	7f3473da61cc11a4	sha256-16 /home/key/fwre-work/rebuild/bench-only/r54-20260906/rlxfw-r54-20260906.bin
vmlinux-bytes	3978029	size /home/key/fwre-work/rebuild/bench-only/r54-20260906/vmlinux
vmlinux-sha16	04cd5b151aae6df4	sha256-16 /home/key/fwre-work/rebuild/bench-only/r54-20260906/vmlinux
map-gpio-initcall	1	count /home/key/fwre-work/rebuild/bench-only/r54-20260906/System.map ^[0-9a-f]{8} t __initcall_rtl819x_gpio_init4$
map-vendor-initcall	1	count /home/key/fwre-work/rebuild/bench-only/r54-20260906/System.map ^[0-9a-f]{8} t __initcall_rtl_gpio_init6$
map-n-writes	1	count /home/key/fwre-work/rebuild/bench-only/r54-20260906/System.map ^[0-9a-f]{8} b rtl819x_gpio_n_writes$
map-chip	1	count /home/key/fwre-work/rebuild/bench-only/r54-20260906/System.map ^[0-9a-f]{8} d rtl819x_gpio_chip$
map-gpiochip-add	1	count /home/key/fwre-work/rebuild/bench-only/r54-20260906/System.map ^[0-9a-f]{8} T gpiochip_add$
expansion-captures	32	count bench/2026-09-06c/PREDICTIONS-B13-block12.md ^/usr/bin/python3 tools/console-capture[.]py capture .*--out bench/2026-09-06c/B[0-9]+-
expansion-loops	10	count bench/2026-09-06c/PREDICTIONS-B13-block12.md ^/usr/bin/python3 tools/looprun[.]py --mode bench --cell B[0-9]+ 
expansion-warm	9	count bench/2026-09-06c/PREDICTIONS-B13-block12.md --out bench/2026-09-06c/B[0-9]+-A --send 'busybox reboot -f'
expansion-cold	1	count bench/2026-09-06c/PREDICTIONS-B13-block12.md --out bench/2026-09-06c/B[0-9]+-A --esc 150 
send-over-127	0	count bench/2026-09-06c/PREDICTIONS-B13-block12.md -{2}send '[^']{128,}'
```

---

## 5. The arithmetic, written before the board is powered

### 5.1 The boot marks, and the negative control is two of them

Printed by `rtl819x_gpio_init()` at `subsys_initcall`, **before** the vendor's
`rtl_gpio_init` at `device_initcall` and before any shell exists.

| mark | prediction | why |
|---|---|---|
| `RLXFW-G0` | present | the driver was entered |
| `RLXFW-G1=FFFFFFDF` | 🟢 **identical on all ten boots** | `REG-26`, the loader's CNR. **This is a negative control** — nothing between the loader and `subsys_initcall` may change it |
| `RLXFW-G2=FF000000` | 🟢 **identical on all ten boots** | `REG-27`, the loader's DIR. Same |
| `RLXFW-G3=0000003C` | bit 5 **set** on all ten | `REG-28` released. ⚠️ Bit 5 is the firm prediction; the other bits are pins in peripheral mode and their DAT reading is not something this project has established |
| `RLXFW-G4=00000000` | `gpiochip_add()` returned 0 | base 0 and ngpio 32 fit inside `ARCH_NR_GPIOS = 256` and nothing else has registered |
| `RLXFW-G5=00000001` | released | bit 5 of `G3` |
| `RLXFW-G6` | present | `/proc` entry created |

🔴 **If `G1` or `G2` moves with anything, `REG-26`/`REG-27` are wrong about this
die and the driver's premise that the loader configured the pin is unsupported.**

### 5.2 🔴 The vendor writes these registers after I do, and this is the cell that measures it

`REG-35`, derived at the desk from the artefact and **not yet seen on the
board**. `Bn-P` reads `boot_*` (latched at level 4) and the live values (read
at shell time, after level 6) in one dump:

| field | prediction | mark |
|---|---|---|
| `boot_cnr` | `FFFFFFDF` | 讀 → 量 |
| `boot_dir` | `FF000000` | 讀 → 量 |
| `cnr` (live) | **`FFFFFF8B`** | 推 — `0xFFFFFFDF & ~0x74` |
| `dir` (live) | **`FF000040`** | 推 — `0xFF000000 \| 0x40` |
| `cnr_as_spec` | **0** | it is deliberately not 1: `REG-26` describes the loader, not a booted Linux |
| `dir_as_spec` | **0** | as above |
| `dat` (live) | **not predicted** | after the vendor's write, bits 2/4/6 are GPIO too and bit 6 is an output it drives. Only bit 5 is predicted |

🔴 **If `cnr` reads `FFFFFF8B`, that is a disassembly of the vendor's driver
confirmed on silicon and `REG-35` goes 讀 → 量.** If it reads `FFFFFFDF`, then
either `rtl_gpio_init` did not run or the decode is wrong, and **the decode is
the more likely of the two** — it was read once, by me, today.

### 5.3 🟢 The guard, refusing on the silicon, at two layers with two errnos

This is `FW-39`'s runtime counterpart. `FW-39` says the write instructions are
not in the image; these cells say the framework's own call path reaches the
refusal and returns.

| cell | typed | prediction | which layer refused |
|---|---|---|---|
| `B1-T5` | `tryout 5` | `RLXFW-G-TRYRC=FFFFFFFF` (**−1, `-EPERM`**), and `G-TRYCNR`/`G-TRYDIR`/`G-TRYDAT` all **`00000000`** | `.direction_output` — line 5 passes `.request` and is refused by the allow-mask |
| `B1-T12` | `tryout 12` | `RLXFW-G-TRYRC=FFFFFFED` (**−19, `-ENODEV`**) and the three XORs still `00000000` | `.request` — line 12 is outside `KNOWN_MASK` and never reaches `.direction_output` |
| `B1-TP` | dump | `n_dirout_no` **1**, `n_req_no` **1**, `n_req_ok` **1**, `n_writes` **0** | the counters say which path each took |

🟢 **Two different errnos from two different layers is what makes this more
than "it returned an error".** A single refusal that swallowed everything would
print the same number twice.

### 5.4 🔴 `n_writes` is the block's stop condition

Any dump with `n_writes` ≠ 0 **stops the block**. `FW-39` says no instruction
in this image can increment it, so a non-zero value means the image on the
board is not the image this card names — and the next thing to read is
`RLXFW-ID0`, not the GPIO registers.

### 5.5 The button, and it must change **back**

| reading | `dat` bit 5 | `btn_raw` | `btn_pressed` | `cnr` / `dir` |
|---|---|---|---|---|
| `Bn-BTN1` released | 1 | 1 | 0 | X, Y |
| `Bn-BTN2` **held** | **0** | **0** | **1** | **X, Y — unchanged** |
| `Bn-BTN3` released | 1 | 1 | 0 | **X, Y — unchanged** |

🟢 `n = 2` (boots 2 and 3). The XOR of `dat` between BTN1 and BTN2 must be
exactly **`00000020`** — `REG-28`'s value, now read through a driver of mine
instead of through the loader's `DW`.

🔴 **A change that does not come back is not a button.** If `BTN3` still reads
0, the cell measured a latch or a stuck read, and the paired design is what
makes that visible rather than the press looking like a success.

### 5.6 `claim` / `sample` — the path a real consumer takes

`B1-C` calls `gpio_request(5)` and `gpio_get_value(5)` **through gpiolib**, not
through this driver's own functions, so what it exercises is what `gpio_keys`
would do in `R5-8`. Prediction: no error, `RLXFW-G-SAMPLE=00000001` (released),
and in `B1-CP` `n_req_ok` **2** (the `tryout 5` in `B1-T5` took one) and `n_get`
**≥ 1**.

### 5.7 `probe04` — a word this project has never read

`B1-U` reads `0xB8003504`, the gap between `PABCD_CNR` and `PABCD_DIR`. It is
**not** read at boot and is not read by any other cell, because a read-to-clear
status register is a write in effect and nothing here knows what `+0x04` is.
`RLXFW-G-UNK04=<8 hex>` is a new number with no prediction attached — the point
is to have it, and `MAP-09` gains a row either way.

### 5.8 The boot capture's size

The image adds seven marks to the ladder: `G0` and `G6` are bare
(`RLXFW-G0` + CRLF = **10** bytes each), `G1`…`G5` carry a value
(`RLXFW-G1=` + 8 hex + CRLF = **19** bytes each). **+115 bytes.**

⚠️ **The absolute is conditional and this card says so.** Seating 14's boot
capture was 1,069 bytes; if that baseline holds for this image, the prediction
is **1,184**. The derived quantity is the **delta**, and it is the delta that
is refuted or confirmed.

---

## 6. What would refute the block

| | |
|---|---|
| `G4` ≠ 0 | `gpiochip_add()` failed. Read the value: `-EINVAL` means base/ngpio, `-EBUSY` means something else claimed the range |
| an oops in any capture | `FW-36`: this kernel prints one even with `CONFIG_PRINTK=n`, so absence is measurable |
| `G1` or `G2` differing between boots | `REG-26`/`REG-27` are wrong about this die |
| `dat` bit 5 not changing under the operator's hand | either the button is not on bit 5 (`BRD-05` wrong) or `.get` is not reading `PABCD_DAT` |
| `n_writes` ≠ 0 | §5.4 — the image is not this one |
| `G-TRYRC` = 0 | the guard did not refuse. **This is the one cell whose success is the bad outcome** |
| a link failure before any of this | `gpio_to_irq()` — but `CONFIG_DEBUG_FS` is not set in this image and the build already succeeded, so this is closed at the desk |

---

## 7. What this block will NOT establish, written before it runs

1. **Which port letter bit 5 is.** `PABCD` packs four ports; nothing here
   separates them. The `.dts` node and the binding `R5`'s DoD asks for cannot
   be written until something does.
2. **That bits 2, 4 and 6 are usable.** The vendor's driver treats them as
   GPIO (`REG-35`) and this driver refuses them, deliberately — taking the
   vendor's bit numbers into `KNOWN_MASK` is what would spend the diff.
3. **Any output.** `RTL819X_GPIO_ALLOW_OUT_MASK` is 0 and no cell changes it.
4. **A GPIO interrupt.** `.to_irq` is NULL and no cell asks for one.
5. **That the loader is safe to boot with the button held** — §2.1. That
   question is open and this block does not touch it.
