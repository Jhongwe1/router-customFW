# PREDICTIONS — block 40, seating 37 (the stall detector, and whether `D5` is a number or a duty cycle)

**declared date 2026-09-22** — the power press happened at **2026-09-22 00:45**
and every capture in this directory belongs to that cycle. One press, budgeted
one.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Two honesty notes, written rather than left to be found

**① This card's image is the fourth build of the evening and the first three
are on disk.** `s99a` (`RECIPE_ID 1818b849`) and `s99b` were built and
discarded at the desk — `s99a` before the `NET-82` detector had a positive
control, `s99b` before `recover 1` could arm over an existing stall. Neither
reached the board. The rule *one cell name per image* is why they were not
rebuilt under one name: their manifests stay as the record of what was
rejected. **The only image this seating uploads is `s99c`**, and the
discriminator is `--image-sha256`, not `RECIPE_ID` (`FW-99`).

**② The `AUTOBURN` reading taken at 00:44 is a bare-cold-boot one and the
record has few of them.** `DW 8040D4A0 1` read **`00000001`** with no rescue
having run. That is `RUNSHEET` `B6`'s documented default — the loader's
initialiser for that word is `1` — and `LOG.md:13411` records the population:
*12 post-rescue reads `00000000` pass, 5 post-reset reads `00000001` correctly
go red*. It is recorded here because it is also the live hazard that governs
every cell below: **until `S5` has sent `AUTOBURN 0` and `S5b` has read
`00000000`, a TFTP upload to this board is written to flash.** Nothing in this
seating hand-rolls an upload; `A0` is `looprun`, which refuses `--skip S5b`.

---

## § 1 The image

| | `s99c` |
|---|---|
| variant | loud, `CONFIG_PRINTK=y` |
| `RECIPE_ID` | **`c3cb552b`** (`s32a` was `84385d91`) |
| `vmlinux` | 4,573,451 B (`s32a` 4,572,389 → **+1,062**) |
| assembled `nfjrom` | **1,181,696 B** (`s32a` 1,180,672 → **+1,024**) |
| `nfjrom` sha256 | `5f1c61c63263d42c…` |
| initramfs spec sha256 | `7130245fbcd92afc…` — **byte-identical to `s32a`'s** |
| driver version string | `rtl819x-nic 1.2` (was `1.1`) |

🟢 The initramfs digest matching is the control that says **only the kernel
differs** between this image and the one every `R6-5` seating has used.

🟢 **It was compiled-checked before it was built.** The patched driver was
compiled against `s32a`'s already-staged tree using that tree's own recorded
`rsdk-linux-gcc` command line, with the object written outside the tree and the
tree's mtimes verified unchanged. That gate caught one real defect
(`implicit declaration of nic_dw` — a helper placed above the accessor inlines
it calls) which would otherwise have cost a full build.

### 1.1 What is new, and all four are runtime switches defaulting to today's behaviour

| verb | default | what it does |
|---|---|---|
| `recover 0\|1` | **0** | the stall detector. `1` also arms immediately if the queue is already stopped |
| `recovms <N>` | **1000** | the stall threshold in ms, bounded 10…600000 |
| `iimr <hex>` | `7E0FFE` | the interrupt mask this driver arms, and what `nic_poll` restores |
| `phfollow 0\|1` | **0** | follow `ph_mbuf` instead of indexing the mbuf ring |

**Nothing else changed.** In `recover 0` / `phfollow 0` / `iimr 7E0FFE` this
image is `s32a` plus counters.

---

## § 2 What this block decides

### 2.1 🔴🔴 `B` — the single-variable demonstration that the detector is a repair

`R6-5` has a repair that works and it has only ever been typed by hand
(`NET-101`, three `/proc` writes, three times on one evening). This block asks
whether a driver can do it by itself.

The experiment is deliberately **not** "arm it and see if anything breaks",
because a clean run cannot distinguish *the detector worked* from *it never
wedged*. Instead the fault is created first, read whole, and then the detector
is switched on **in front of it**:

| cell | state | prediction |
|---|---|---|
| `B1-OFF` | `recover 0` | `recov_mode 0`, `n_recov_arm 0` |
| `B2-LADDER` | `Y5`'s dose, 347 frames / 8 s / 0.5 Mbit/s | the board goes silent |
| `B3-PING` | | **0/4, 100 % loss** |
| `B4-WEDGE` | | four `txd*` with bit 0 set, `n_tx` frozen, `n_tx_stop 1`, `tx_stopped 1`, **`n_recov_arm 0`** |
| `B5-ON` | `recover 1` | — |
| `B6-AFTER` | ≥ 3 s later | `n_recov_arm 1`, `n_recov_fire 1`, `n_recov_ok 1`, `n_recov_wake 1`, `n_recov_fail 0`, `recov_rc 0 0 0`, four `txd*` back to `A15B81D0 / 81E8 / 8200 / 821A` |
| `B7-PING` | | **4/4, 0 % loss** |

🔴 **Refutation conditions, and each one names a different mistake:**

* `n_recov_arm > 0` at `B4-WEDGE` → the arming is not gated on the mode, and
  `B1`–`B4` are not a `recover 0` arm at all. **Everything below is void.**
* `n_recov_arm 0` at `B6-AFTER` → `recover 1` did not arm over the existing
  stall, so the whole single-variable shape collapses and the demonstration
  falls back to arming before the wedge.
* `n_recov_ok ≥ 1` with `B7-PING` still 0/4 → **these three calls are not a
  recovery.** They returned 0 and the interface did not come back. `NET-101`
  measured the opposite twice by hand; this would refute it from inside.
* `n_recov_fail ≥ 1` → read `recov_rc`. `1` in a slot means *not attempted*
  (no errno is positive); `-1` is `-EPERM`, i.e. the driver was locked;
  `-16` is `-EBUSY` from `nic_do_arm` finding the engine still on, which would
  mean `nic_do_engine(0)` did not take.
* **`n_recov_spurious ≥ 1` with `n_recov_fire 0`** → the timer fires on
  transients the level test has already cleared, i.e. `recov_ms 1000` is too
  short to be a stall detector. Nothing in `NET-99` predicts this; a healthy
  stop is resolved by the next interrupt.

🟢 **And the latency is a prediction, not an event.**
`recov_j_fire − recov_j_arm` must equal **`recov_jiffies` = 100** (`HZ = 100`,
`msecs_to_jiffies(1000)`) ± 1. A value of 0 would mean the timer fired in the
same tick it was armed, which `mod_timer` cannot do.

### 2.2 🔴 `C` — `D1`, and it decides whether `D5` is worth taking

30 s of `iperf3` with the detector armed, then `n_tx_stop`.

* **single digits** → the recovery is fast relative to the run and a throughput
  figure measures the path. `D2` proceeds.
* **tens** → the figure measures a duty cycle. `D2` still runs, but every
  number is published beside `n_tx_stop` / `n_recov_fire`, and the
  `recover 0` control arm (`D0-CTRL`) is what says what the fix bought.

🔴 **This cell runs BEFORE the three `D5` runs**, because it can make them mean
something different. **"There is a recovery" is not "D5 is reachable."**

### 2.3 🔴 `E` — § 12.4's run-out mask, and the confound the repo had not named

Arm B sets `CPUIIMR` to the loader's `0x000007F8`. 🔴 **`NIC_IIMR_LADDER`'s own
comment records that `0x7FE` — the loader's value plus `TX_ALL_DONE` — made
this interface permanently RX-DEAF under load** (`bench/2026-09-19b/C58-afterflood2`:
pkthdr ring ran out, `CPUIISR` latched bit 17, masked, no interrupt, NAPI never
scheduled). So arm B may reproduce that instead of illuminating the TX wedge.

🟢 **They are distinguishable and the discriminator is already printed:**

| | RX-deaf (`C58`'s failure) | TX wedge (`NET-98`'s failure) |
|---|---|---|
| `n_rx` across the fault | **frozen** | **climbing** |
| `now_iisr` at rest | holds a run-out bit (`00020000`) | `00000000` |
| four `txd*` OWN | clear | **all set** |
| `n_tx_stop` | 0 | 1 |

**A cell that reads only *did it stop answering* cannot tell them apart.** `E4`
reads all four.

🟢 **And this is why it needed an image.** 讀 `rtl819x-nic.c`, the NAPI-complete
path used to OR the three RX-work enables back in on every completion, so a
mask written through the vendor's `/proc/rtl865x/memory` would be undone by the
first arriving packet — and the read-back cell would have shown a **false
green**, because `echo read` puts nothing on the wire. In `1.2` the restore is
bounded by `iimr_base`. **`iimr_base` and `now_iimr` are two sources**: if they
disagree, something else is writing `CPUIIMR`.

### 2.4 🟢 `A3` — the `NET-82` detector's positive control, and its arguments are PREDICTED

`n_ph_diff 0` is a claim. `phtest <w0> <slot>` drives the same classifier with
typed values and touches no hardware.

讀 `nic_do_alloc`'s layout: `rx_ring +0x00`, `mb_ring +0x20`, `tx_ring +0x40`,
`rx_ph +0x50`, **`rx_mb +0x110`**, `tx_ph +0x1D0`, `tx_mb +0x230`,
`bufs +0x290`. 🟢 **That layout is confirmed against silicon already measured**:
with `base = A15B8000` it puts `tx_ph` at `A15B81D0`, so the four TX slots are
`1D0 / 1E8 / 200 / 218`, and with OWN and the WRAP bit on the last that is
`A15B81D1 / 81E9 / 8201 / 821B` — **exactly** `NET-98`'s reading of the wedged
board. So `rx_mb = A15B8110` is a prediction and not a runtime read.

| cell | command argument | `ph_test_cls` | `ph_test_j` | what it proves |
|---|---|---|---|---|
| `A3-PH1` | `A15B8110 0` | **0** AGREE | 0 | it does not fire spuriously |
| `A3-PH2` | `A15B8128 0` | **1** SKEW | **1** | it fires, and the `/24` arithmetic is right |
| `A3-PH3` | `DEADBEEF 0` | **2** BAD | 0 | it tells a usable pointer from a word |
| `A3-PH4` | `A15B8114 0` | **2** BAD | 0 | in range but mis-strided — the only one that tests the modulus |

🔴 If `A3-PH1` reads **2** instead of **0**, the ring did not land at
`A15B8000` on this boot. That is a refuted prediction and not an instrument
failure — `A4-BASE` prints `mb_ring`, and `rx_mb = mb_ring + 0xF0`.

⚠️ **What `phtest` does NOT cover, said rather than left to be found**: the
dereference. It exercises classification and index arithmetic only. The load
has its own check — `ph_last_bf` must equal `bufs + ph_last_j × 2048 + 2`, and
`bufs` is printed in the same dump.

### 2.5 ⚠️ `A0` — the boot capture is a hard byte prediction

Seating 36's two boot captures are **7,717 bytes each**, byte-for-byte the same
length. `s99c` adds **no new boot mark** — the one that was drafted was removed
precisely so this prediction stays clean — and `RLXFW-ID0`'s value changes
length-neutrally (`84385D91` → `C3CB552B`). 推 **7,717 bytes**.

🔴 A different length means a mark appeared or disappeared, and the diff
against `bench/2026-09-21f/B1-boot.log` says which.

---

## § 3 Standing rules for this seating

🔴 **No flash write. No `FLR`. No `EW`/`EB`/`FLW`/`AUTOBURN` typed by hand.**
🔴 **No `ifconfig rlx0 down`** — `NET-58`, reproduced on demand as seating 36's
`X16`: re-opening a recovered interface breaks it again.
🔴 **No `arm` with the engine running** — `NET-64`, 112 minutes of a hard-hung
board and 0 console bytes. Every recovery path in this image orders
`engine off` first, and `nic_do_arm`'s own `-EBUSY` is the second layer.
🔴 **Every `--send` is ≤ 127 characters.** `_check_send` refuses at `>= 128`;
seating 36 lost a whole cell to a 133-character line. Three `echo … > /proc/…`
verbs on one line is about the limit.
🔴 **Board-side `ping` ignores `-c`** on this image — every ping cell is
host-side.
⚠️ **One `cat` is TWO `read_proc` invocations** (`FW-64`), so `n_reads` moves by
2 per dump cell. No other counter in this card is affected.
🟢 **Extra boots are free**: `busybox reboot -f` reaches the loader prompt in
2.407 s (`FW-37`), and every cell whose payload can reset the board carries
`--esc-after 25`.

---

## § 4 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`NB`  = `/usr/bin/python3 tools/netblast.py`
`HOST <prefix> :: <cmd>` runs `<cmd>` on the workstation with output to `<prefix>.log`.

### Part A — boot `s99c` and bring the interface up

```
HOST bench/2026-09-22/A0 :: looprun --mode bench --cell A0 --skip S2,S3 --recipe-override c3cb552b --image <imgwork>/s99c/s99c/kroot/rtkload/nfjrom --image-sha256 5f1c61c63263d42c1bf08e490e0bd40d96142f40b521a6ef13ea8067b18ac656
CAP --out bench/2026-09-22/A1-SW --send 'echo unlock i-mean-it > /proc/rtl819x-switch ; echo start > /proc/rtl819x-switch' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A2-UP --send 'echo unlock > /proc/rtl819x-nic ; echo netdev on > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A3-PH1 --send 'echo phtest A15B8110 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A3-PH2 --send 'echo phtest A15B8128 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A3-PH3 --send 'echo phtest DEADBEEF 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A3-PH4 --send 'echo phtest A15B8114 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/A4-BASE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22/A5-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-22/A6-SW --send 'cat /proc/rtl819x-switch' --idle 3 --seconds 30
```

* `A0` — `looprun`'s own `A1`–`A4` assertions plus `S4`/`S5b`/`S6b`'s abort
  gates. 推 `A0-boot.log` **7,717 bytes**, `RLXFW-ID0=C3CB552B`.
  🔴 **`S5b` must read `00000000`.** It read `00000001` at 00:44 before any
  rescue; if it still reads `00000001` after `S5`, `AUTOBURN 0` did not take
  and **the seating stops** — an upload in that state writes flash.
* `A1-SW` — `R6-5`'s 通電前必做. Without it every ping is 100 % loss and reads
  as a driver fault. **This cell is ON the card this time**; on seating 36 and
  on seating 13 it was not, and both cards carried a `ping` whose interface
  nothing brought up.
* `A4-BASE` — 推 `recov_mode 0`, `recov_ms 1000`, `recov_jiffies 100`,
  `iimr_base 007E0FFE`, `iimr_ladder 007E0FFE`, `now_iimr 007E0FFE`,
  `ph_follow 0`, all `n_recov_*` **0**, `n_ph_used 0`, **`truncated` absent**.
  🔴 The absence of `truncated` is the reading: the handler now caps itself at
  `NIC_PROC_CAP` and a present line would mean the dump hit 3,900 bytes.
* `A5-PING` — **4/4 or everything below is void.**
* `A6-SW` — `R6-6`'s readable half, fifth consecutive reading. 推 `VCR0`,
  `VCR1`, `PVCR0`–`PVCR4` byte-identical to seatings 33/34/35/36.

### Part B — the detector, single variable

```
CAP --out bench/2026-09-22/B1-OFF --send 'echo recover 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/B2-CON --seconds 30
HOST bench/2026-09-22/B2-LADDER :: NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5 --step-s 8 --out bench/2026-09-22/B2-LADDER.json
HOST bench/2026-09-22/B3-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-22/B4-WEDGE --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/B5-ON --send 'echo recover 1 > /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/B6-AFTER --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22/B7-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
HOST bench/2026-09-22/B8-LADDER :: NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5 --step-s 8 --out bench/2026-09-22/B8-LADDER.json
CAP --out bench/2026-09-22/B9-AFTER --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22/B9-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

* `B2-CON` sends nothing. It exists because a kernel oops during the wedge
  would otherwise be invisible — seating 36's card had no console cell across
  its blast either.
* `B4-WEDGE` — 🟢 **the `mbd*` lines read in a wedged state, which nothing in
  this project has ever done.** `ph` is pkthdr word 0 exactly as the engine
  left it; `ml` is the mbuf's `m_len`, which `nic_refill()` zeroes only for the
  slot it is handed, **so a non-zero `ml` on slot j is the engine saying it put
  a frame in mbuf j** — hardware-written evidence that does not depend on any
  of the new code being right.
* `B8`/`B9` — the reproduction, with the detector left armed. 推 the board
  never goes unreachable: `n_recov_fire 2`, `n_recov_ok 2`, ping 4/4.
  🔴 If `B9-PING` is 0/4, the recovery worked once and not twice, which is
  worth more than the success.

### Part C — `D1`, the decision cell

```
HOST bench/2026-09-22/C0-SRV :: (start the mips iperf3 server under qemu, backgrounded outside this shell)
HOST bench/2026-09-22/C1-SS :: ss -ltn
CAP --out bench/2026-09-22/C2-IPERF --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 5 -f m' --idle 8 --seconds 90
CAP --out bench/2026-09-22/C3-AFTER --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

* `C1-SS` — 🔴 **the listener is re-checked immediately before use, not once at
  the start.** `FW-102`: a server started with `nohup … &` inside
  `wsl -- bash -ls` dies with its parent, and seatings 33/34 measured a listener
  that did not exist. A check taken two seconds after start certifies nothing.
  Expected row: `LISTEN 0 5 10.1.1.2:5201`.
* `C2-IPERF` — the host and the board run **the same** `iperf 3.1.3` MIPS
  binary; `NET-60` measured 3.1.3 ↔ 3.16 succeeding on loopback and failing on
  the real 1500-byte path, so `/usr/bin/iperf3` (3.16, native) may not be used.
* `C3-AFTER` — **`n_tx_stop` is `D1`'s answer.** Also `n_recov_fire`,
  `n_recov_ok`, `n_recov_fail`, `n_recov_spurious`.

### Part D — `D5`, three runs and a control

```
CAP --out bench/2026-09-22/D0-OFF --send 'echo recover 0 > /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/D0-CTRL --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 5 -f m' --idle 8 --seconds 90
CAP --out bench/2026-09-22/D0-N --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/D1-ON --send 'echo recover 1 > /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/D1-R1 --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 5 -f m' --idle 8 --seconds 90
CAP --out bench/2026-09-22/D1-N1 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/D1-R2 --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 5 -f m' --idle 8 --seconds 90
CAP --out bench/2026-09-22/D1-N2 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/D1-R3 --send 'iperf3 -c 10.1.1.2 -p 5201 -t 30 -i 5 -f m' --idle 8 --seconds 90
CAP --out bench/2026-09-22/D1-N3 --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

🔴 **`D0-CTRL` is the arm that makes the other three mean something.** Without
it, three numbers taken with the detector armed say what this driver does and
not what the detector bought. 推 `D0-CTRL` either reports a truncated transfer
or dies, and `D0-N` shows `tx_stopped 1` with `n_recov_fire 0`.

⚠️ **`D5`'s clause is *a figure with its method and its spread over ≥ 3 runs*.**
`D1-R1..R3` supply it. **Whatever the spread, the figure is published beside
`n_tx_stop` and `n_recov_fire` from the matching `D1-N*`** — a throughput number
from a driver that is being rescued mid-transfer is a duty cycle unless the
rescues are counted with it. `NET-85`'s 203 MBytes / 23.3 Mbit/s is exactly the
number that should not have been quoted alone.

### Part E — § 12.4's run-out mask A/B

```
CAP --out bench/2026-09-22/E1-SET --send 'echo iimr 7F8 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/E2-CON --seconds 30
HOST bench/2026-09-22/E2-LADDER :: NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5 --step-s 8 --out bench/2026-09-22/E2-LADDER.json
HOST bench/2026-09-22/E3-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-22/E4-DUMP --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
CAP --out bench/2026-09-22/E5-RST --send 'echo iimr 7E0FFE > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

* `E1-SET` — 推 `iimr_base 000007F8` **and** `now_iimr 000007F8`. 🔴 If
  `now_iimr` disagrees with `iimr_base`, something else writes `CPUIIMR` and
  the whole A/B is void; that is the failure § 14.4 predicted for the `/proc`
  route and the reason this needed an image.
* `E4-DUMP` — read § 2.3's four-row table. **The verdict is which failure
  happened, not whether one did.**
* `E5-RST` — restores the compiled default. `iimr_ladder` in the same dump is
  the source for that value, so it is not typed from memory.

### Part F — `phfollow`, conditional

**Runs only if `n_ph_diff > 0` in any dump above.** If `n_ph_diff` is 0 across
Parts A–E then `NET-82` is **refuted for this die as a cause of frame loss**:
the pkthdr↔mbuf pairing is the identity here and the switch cannot matter. That
is a result obtained in the DEFAULT mode, at no risk, and it is the outcome
this card expects.

```
CAP --out bench/2026-09-22/F1-SET --send 'echo phfollow 1 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --idle 3 --seconds 30
HOST bench/2026-09-22/F2-LADDER :: NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5 --step-s 8 --out bench/2026-09-22/F2-LADDER.json
CAP --out bench/2026-09-22/F3-DUMP --send 'cat /proc/rtl819x-nic' --idle 3 --seconds 30
```

### Part G — `R6-6`'s write half. THE ONE HIGH-RISK CELL, AND IT IS LAST

```
CAP --out bench/2026-09-22/G1-RD --send 'echo read 0xbb804100 > /proc/rtl865x/memory' --idle 3 --seconds 30
CAP --out bench/2026-09-22/G2-WR --send 'echo write 0xbb804100 0x00000001 > /proc/rtl865x/memory' --idle 3 --seconds 30
CAP --out bench/2026-09-22/G3-RB --send 'echo read 0xbb804100 > /proc/rtl865x/memory' --idle 3 --seconds 30
HOST bench/2026-09-22/G4-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

🔴 **Scheduled last on the owner's instruction**, because a hard hang here costs
a power press and every cell above will already have its reading.
🔴 **Constraints, unchanged from `R6-6`:** only `PVCR0`–`PVCR3`; **no**
`reset full`; **no** `restore 0`; every `echo write` is preceded by an
`echo read` of the same address; the payload is far under 64 characters.
⚠️ **Two of `R6-6`'s three DoD clauses are unreachable before power and that
was measured, not assumed**: one cable gives one `LinkUp` (thirteen readings),
and rlxfw cannot write the VLAN table at all — 讀 `rtl819x-switch.c:88-92`, the
table sits behind the `TACI` indirect path. `R6-7` writes the weaker true
statement.

---

## § 5 What this block does NOT do

* It does not explain **why the engine stops**. `NET-67 殘留` is untouched by
  a repair; Part E is a candidate, not an answer.
* It does not test `phfollow 1` unless Parts A–E give it a target, and the
  expected outcome is that they do not.
* It runs **no `FLR`**, so `FLS-26`'s ledger does not move: proven identical
  4,177,920 B, proven different 8,192 B, undetermined 8,192 B.
* `recovms` is left at its default throughout. The threshold is a tunable that
  trades throughput against confidence that a stop was real, and sweeping it is
  a separate seating.

### ⚠️ The fence's scope, said rather than left to be inferred

The `cells` fence below holds **Parts A–E only**. Parts **F** and **G** are
deliberately outside it: `F` is conditional on `n_ph_diff > 0`, and `G` is the
one high-risk cell, so neither is a cell whose absence is a failure. That means
a green `check-predictions` on this card is a statement about A–E and **not**
about the whole seating — the same limit seating 15's card hit when `PC3` sat
outside its fence and `32 of 32` was read as *the whole seating was checked*.
Whatever F and G produce is reported in the closeout as declared off-card work.

---

```cells
bench/2026-09-22/A1-SW
bench/2026-09-22/A2-UP
bench/2026-09-22/A3-PH1
bench/2026-09-22/A3-PH2
bench/2026-09-22/A3-PH3
bench/2026-09-22/A3-PH4
bench/2026-09-22/A4-BASE
bench/2026-09-22/A5-PING
bench/2026-09-22/A6-SW
bench/2026-09-22/B1-OFF
bench/2026-09-22/B2-CON
bench/2026-09-22/B2-LADDER
bench/2026-09-22/B3-PING
bench/2026-09-22/B4-WEDGE
bench/2026-09-22/B5-ON
bench/2026-09-22/B6-AFTER
bench/2026-09-22/B7-PING
bench/2026-09-22/B8-LADDER
bench/2026-09-22/B9-AFTER
bench/2026-09-22/B9-PING
bench/2026-09-22/C1-SS
bench/2026-09-22/C2-IPERF
bench/2026-09-22/C3-AFTER
bench/2026-09-22/D0-OFF
bench/2026-09-22/D0-CTRL
bench/2026-09-22/D0-N
bench/2026-09-22/D1-ON
bench/2026-09-22/D1-R1
bench/2026-09-22/D1-N1
bench/2026-09-22/D1-R2
bench/2026-09-22/D1-N2
bench/2026-09-22/D1-R3
bench/2026-09-22/D1-N3
bench/2026-09-22/E1-SET
bench/2026-09-22/E2-CON
bench/2026-09-22/E2-LADDER
bench/2026-09-22/E3-PING
bench/2026-09-22/E4-DUMP
bench/2026-09-22/E5-RST
```

```cardnum
cells-fence	39	count bench/2026-09-22/PREDICTIONS-B42-block40.md ^bench/2026-09-22/[A-E]
declared-date	1	count bench/2026-09-22/PREDICTIONS-B42-block40.md [*][*]declared date 2026-09-22[*][*]
cap-cells	35	count bench/2026-09-22/PREDICTIONS-B42-block40.md ^CAP -{2}out
host-cells	13	count bench/2026-09-22/PREDICTIONS-B42-block40.md ^HOST bench/2026-09-22/
blast-cells	4	count bench/2026-09-22/PREDICTIONS-B42-block40.md ^HOST .*NB blast
send-over-127	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']*AUTOBURN
no-ifdown	0	count bench/2026-09-22/PREDICTIONS-B42-block40.md -{2}send '[^']*ifconfig rlx0 down
s99c-nfjrom-bytes	1181696	size /home/key/fwre-work/rebuild/imgwork/s99c/s99c/kroot/rtkload/nfjrom
s99c-nfjrom-sha256	5f1c61c63263d42c	sha256-16 /home/key/fwre-work/rebuild/imgwork/s99c/s99c/kroot/rtkload/nfjrom
s99c-vmlinux-bytes	4573451	size /home/key/fwre-work/rebuild/r3-4/out/s99c.vmlinux.elf
s36-boot-bytes	7717	size bench/2026-09-21f/B1-boot.log
```
