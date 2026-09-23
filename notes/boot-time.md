# Boot time — the instrument, the one clock, and the retro table (`P2`)

This file owns what `P2` measures about a boot: the segment definitions (kept as
data in `tools/boot-timeline.py`, so the definitions and the code cannot drift
apart), the one-clock instruments that put console bytes and network events on
one timeline, the retro table that seating A (`P2-3`) is scored against, and the
per-seating timebase factor the retro table exposed. `SPEC.md` rows `FW-115`,
`FW-116`, `FW-117`, `CLK-32` and `CLK-33` index it; `FW-118`'s terminator figures
are `notes/dev-loop.md` § 19's.

Everything below is desk work over committed captures, 2026-09-23. No capture in
this file was taken for `P2`.

## 1. What `P2` compares

The plan's segmentation runs from power-on to a usable device, both firmwares,
one script (`plan/router-rebuild-plan.md`, `P2`). Its confound is stated there:
the vendor runs WiFi, UPnP, DNS forwarding and a whole MIB bring-up that rlxfw
does not, so the two totals are not comparable, and the comparison is made per
segment. Each segment carries one of three classes, and the class is part of the
tool's table rather than a label added in a write-up:

* **identical** — the same code runs in both columns. Only the loader's own
  segments qualify; `loader.banner` is `D2`'s positive control.
* **comparable** — the same kind of work by different builds: rtkload's
  decompression (image sizes differ, `D4` prints them), and the kernel segments
  between drivers present in both kernels (the WLAN driver's banner reads
  `version 1.6 (2013-02-21)` in the vendor's kernel and
  `driver version 1.6 (2012-12-04)` in rlxfw's).
* **not-comparable** — userspace. The vendor runs `rcS` and its daemons; rlxfw
  execs a shell. For these, each daemon's own start and readiness stand in (`D4`).

## 2. The instrument — `tools/boot-timeline.py` past the loader (`FW-117`)

**Landmarks and segments are data.** Three landmark tables — `LOADER`, `VENDOR`,
`RLXFW` — and one segment table. A kernel boot is searched with `LOADER` and then
its firmware's table; each landmark is searched from the previous one found, and a
named group `at` marks the byte a landmark sits on (rlxfw's `ready` is the `#` of
the first prompt). One function, `measure()`, computes every segment for both
firmwares; the firmware only selects the table (`D1`). A segment exists only when
both its landmarks are in the firmware's table and in the capture; otherwise it
prints `--`, never 0. `--legend` prints both tables with a `=` beside every
landmark defined identically in the two.

| segment | from → to | class |
|---|---|---|
| `loader.booting` | `booting` (anchor C) → `chipname` | identical |
| `loader.banner` | `booting` → `banner` | identical |
| `loader.esc` | `banner` → `autoboot` | identical |
| `rtkload.decompress` | `decomp` → `decomp_done` | comparable |
| `rtkload.total` | `jump` → `kentry` | comparable |
| `kernel.early` | `kentry` → `wlan` | comparable |
| `kernel.wlan` | `wlan` → `nic` | comparable |
| `kernel.nic` | `nic` → `fastpath` | comparable |
| `kernel.late` | `fastpath` → `userinit` | comparable |
| `kernel.total` | `kentry` → `userinit` | comparable |
| `user.ready` | `userinit` → `ready` | not-comparable |
| `boot.jump_to_ready` | `jump` → `ready` | not-comparable |
| `net.up`, `net.http` | `jump` → first ICMP reply / first TCP 80 success | not-comparable (§ 3.3) |

`userinit` is the first line printed by each firmware's init: the vendor's
`init started: BusyBox`, rlxfw's `rlxfw: init running`. `ready` is the vendor's
`boa: starting server` and rlxfw's first shell prompt. `kernel.late` holds rlxfw's
own 300-jiffy pre-check wait (`CLK-27`, `IRQ-13`): about 3 s from image `EA6EE537`
(2026-09-06b) on, 0.024–0.041 s on every image before it.

**Firmware, variant, image.** A kernel boot is rlxfw on `RLXFW-B00` or
`rlxfw: init running`, and the vendor's on `init started: BusyBox v1.13.4` or its
WLAN build string; both or neither is `?`, named and not timed. rlxfw is `loud`
when the WLAN, NIC and FastPath lines carry a printk time prefix; the image is its
`RLXFW-ID0=` (a digest of `config/`), or `none` before that mark existed.

**Cold or warm, for a kernel boot.** `C-8`'s line decides, read from the capture
itself when the loader's boot is in it (`K-J` warm, `X8-WAIT` cold). Otherwise the
class is inherited from the latest boot-holding capture in the same directory by
`started_wallclock`, and it is `?` when that capture is itself a kernel boot or
when a capture with no metadata could have run in between. Weakness:
`started_wallclock` is to the second, and a directory can hold several power
cycles; 10 of the 144 kernel boots come out `?`, each named in the report.

**The defect this fixed.** The late-open detector named 22 captures "opened after
the board started". Nineteen were rlxfw kernel boots — the 18 `*-boot.log` in
2026-09-21b…2026-09-22b and `2026-08-30b/L3` — because a loud kernel's SPI driver
prints a table header containing `chipName`, and the detector matched bare
`chipName`. The loader prints `\0chipName: `; the detector now matches only the
loader's own forms. After the fix the 2,189 captures with no loader row split
**142** kernel boots, **3** named, and **2,044** with no boot text. The three named
are `2026-09-01/Y0-A` and `2026-09-06/SQ-A`, whose resets are not in the capture,
and `2026-08-23/A-catch`, which is not a `console-capture` capture at all (no
`.timing`; a `console-dump.py` transcript).

**Controls** (`tools/test-boot-timeline.sh` B5–B14, each written refutation
first). `D1`'s: five segments of `G6` and of `X20-boot` equal a derivation the
test makes with `grep -abo` and the `FW-35` rule by hand, and one synthetic
capture holding both firmwares' strings agrees across the two tables on the five
identically defined segments and differs on the others by exactly what was
planted. The landmark engine reproduces the loader table's `booting` and `banner`
on 249 of 249 loader boots. Eighteen mutants of the tool were each killed; the
harness is not committed.

## 3. One clock

`P2` settled item 4: console bytes and host network events on the same
`CLOCK_MONOTONIC`. Both premises were measured first (`FW-114`).

### 3.1 `console-capture` records its origin (`FW-115`)

`.meta.json` gains six keys. Not one byte more or less goes out on the wire, so
`tool_version` stays 1.4; the presence of `t0_mono` dates the schema.

| key | what it is |
|---|---|
| `clock` | the clock `time.monotonic()` reads, as the interpreter reports it: `CLOCK_MONOTONIC` here; anything else is written verbatim and a reader expecting `CLOCK_MONOTONIC` refuses it |
| `t0_mono` | the variable every `.timing` second is measured from, unrounded: `t0_mono + seconds` is the instant a read returned on the host's clock |
| `t0_real` | `time.time()` read on the next statement, for tools that stamp realtime (`ping -D`) |
| `sent_s` | seconds since `t0` at which `ser.flush()` of the `--send` line returned; `null` when nothing was sent |
| `end_mono`, `end_real` | one pair read after the port and files are closed; `duration_s` is `end_mono - t0` from that same reading |

量 by the suite on a pty (cases P18–P23, N42–N43): the tool's origin and every
read fall inside the harness's own `CLOCK_MONOTONIC` bracket, each read landing
80–200 µs after the harness wrote the byte it delivered; two adjacent
`time.monotonic()` calls are 61 ns apart (median of 20,000); a pty answers
`tcdrain` in 6–16 µs. Every capture committed before 2026-09-23 lacks these keys,
and a join that needs them refuses the capture rather than guess an origin from
`started_wallclock`, which is a string to the second.

殘留: when `flush()` returns on the real port (the CP2102 through usbip) is not
measured. `sent_s` marks the whole line handed over; the loader echoes a line
character by character, so on the real port the first echo byte can precede
`sent_s`, which the pty harness cannot show. No segment in § 2 is anchored on
`sent_s`; the join in § 3.3 uses it only as the lower edge of its window.

### 3.2 `tools/hostprobe.py` (`FW-116`)

The host's half: the first ICMP echo reply (`D8`), the first TCP success on a
daemon's port (`D4`), neighbour-table changes, and UDP arrivals, each stamped
`t_mono` on the same clock and written one line per event to `PREFIX.events`,
flushed per line; `PREFIX.meta.json` closes the record. No packet contents and no
frames are kept, and — from 1.1, 2026-09-23 — no hardware address the allowlist
does not name. An `lladdr` is written verbatim only when its canonical form is one
of the addresses `tools/audit-bench-log.py`'s `ALLOW` names; any other is
`unlisted-N`, its order of first appearance in the run, with nothing derived from
its bytes. The same gate covers comment lines, the meta, stdout, stderr and
`report`, a failed `ip` poll's output is withheld, and without the allowlist
`--neigh` is refused. 1.0 wrote `ip`'s raw `lladdr`, which against the vendor
firmware on 10.1.1.1 — this unit's live `IP_ADDR` (`upstream/notes/compcs-decode.md`)
— is this unit's `H601` address; no 1.0 record exists under `bench/`. The loader's
synthesised `56:0a:01:01:01:e8` stays on the allowlist: its owner already publishes
it, and the vendor analysis needs to tell, across runs, the loader answering for
10.1.1.1 from the vendor doing so. Its residual — whether bytes 1 and 6 are
per-unit — is the allowlist entry's own. ICMP goes through the system `ping`, whose
own `-D` realtime stamp is kept beside the probe's read time — the second clock
the lag cross-check reads. 1.2 (2026-09-23) adds `started_wallclock` to the meta -- `console-capture`'s field, in its format, from the same `time.time()` reading as `start_real` -- because `capdate` dates every `.meta.json` in a bench directory by it (`D7`, `D8`), and 量 on a scratch copy of `bench/` one 1.1 record turned `capdate` RED. `F6` reads every record through `capdate`'s own reader, loaded by path, and requires it to refuse the same meta with the key removed; the mutant without the key fails `F3` and `F6`. The 1.1 docstring's claim that the vendor NIC driver on rlxfw's kernel answers with the H601 address was wrong: 量 `bench/2026-09-21e/V3-ETH4` reads the SDK placeholder `00:12:34:56:78:94`.

量, loopback only, 2026-09-23, iputils 20240117 with `cap_net_raw=ep`:

* **The unprivileged floor is 2 ms, not 0.2 s.** `-i 0.0019` exits 2 with
  *minimal interval for user must be >= 2 ms*; `-i 0.002` runs. `-i` is truncated
  to whole milliseconds (0.0029 ran at a 2.034 ms median gap).
* **From 10 ms up the achieved interval exceeds the request:** 10 → 16.0,
  20 → 24.0, 50 → 56.0, 100 → 104.0, 200 → 204.0, 500 → 512.0 ms (median gaps).
  `FW-97` derived 0.106 and 0.206 s per packet on the bench for 0.1 and 0.2 — a
  second source that agrees. That the cause is jiffy-rounded sleeps at
  `CONFIG_HZ=250` is 推.
* **`ping` flushes per line into a pipe:** 766 reply lines were read 0.026–0.435
  ms after their `-D` stamps; the control, a relay that held output for 1 s, put
  12 of 15 lines over 10 ms.
* A SIGKILL of the probe orphans `ping`, which died of SIGPIPE 0.207 s later. The
  probe starts `ping` in its own session, so a terminal Ctrl-C reaches only the
  probe, which then stops `ping`.
* The probe listens only once its `start` line exists: 0.271 s after launch from
  DrvFs. A card waits for that line before it powers the board or sends anything.

What it does not establish: whose address an `unlisted-N` is, and that two runs'
labels name the same address (labels are per run); wire time (a stamp is when the
probe read the line);
network-up finer than the achieved interval, which the meta records; that a
daemon serves (`tcp ok` is a completed handshake with a listening socket); the
channel offset (a `udp` event is the host's half only); when a neighbour entry
changed (an event is an upper bound after the previous poll); that it is passive —
every echo, SYN and the ARP they provoke is load on a booting board, so a card
states its rates. Two readings wait for the first bench run: whether `ping` stamps
its `no answer yet` lines with `-D`, and whether it counts a truncated reply as
received.

### 3.3 The join

`tools/boot-timeline.py --probe PREFIX` places one probe record on one capture's
timeline: an event at `t_mono` sits at `t_mono - t0_mono` in the capture's
`.timing` frame. Only events inside the capture's window (`t0_mono` … `end_mono`)
and after `sent_s` count, and a capture with no `t0_mono`, no `end_mono`, or a
`clock` other than `CLOCK_MONOTONIC` is refused. One probe can therefore run
across a whole `looprun` block while each round's boot capture reads its own
events out of it.

## 4. The retro table — what `P2-3` is scored against (`CLK-33`)

`python3 tools/boot-timeline.py --retro bench --tsv FILE`, tool sha256
`05dd4a74c349be5e`, 2,438 `.log`: 249 loader boots (56 cold, 193 warm), 144 kernel
boots (vendor 6, rlxfw quiet 119, rlxfw loud 19). The text and the TSV are
byte-identical across runs. Cells are n, median, min..max, in seconds; a byte's
time is the last `.timing` row at or before it (`FW-35`), an upper bound.

**Loader** (identical code):

| segment | cold | warm |
|---|---|---|
| `loader.booting` | n=56 0.3521 (0.3259..0.3686) | n=193 0.3537 (0.3263..0.3707) |
| `loader.banner` | n=56 0.5794 (0.5370..0.6069) | n=193 0.5925 (0.5470..0.6213) |
| `loader.esc` | n=1 5.2101 (`X8-WAIT`) | n=1 5.0362 (`K-J`) |

`LDR-15`'s 4.886 s (2026-08-18) is `upstream/`'s reading; these two are this
repository's. `X8-WAIT` is a cold boot: `C-8`'s line after `ramSize: 32M` is a
single space.

**Vendor** (one image; 6 boots: cold 2, warm 3, `?` 1):

| segment | cold | warm |
|---|---|---|
| `rtkload.decompress` | n=2 1.0492 (1.0438..1.0546) | n=3 1.0337 (1.0215..1.0364) |
| `kernel.wlan` | n=2 4.5939 (4.5204..4.6673) | n=3 4.5078 (4.4880..4.5201) |
| `kernel.total` | n=2 7.0499 (6.9450..7.1548) | n=3 6.9251 (6.8895..6.9817) |
| `user.ready` | n=1 18.1253 | n=3 17.7440 (17.6212..18.0583) |
| `boot.jump_to_ready` | n=1 26.1258 | n=3 25.6713 (25.6540..26.0281) |

**rlxfw, the images nearest `P2-2`'s** (per `RLXFW-ID0`; the pooled cells mix
kernels with and without the 3 s wait and predict no image):

| image | variant | boots | `kernel.total` | `boot.jump_to_ready` |
|---|---|---|---|---|
| `EDC94765` (2026-09-20) | quiet | 5 (cold 1, warm 2, `?` 2) | 9.0733–9.5408 | 10.3337–10.8535 |
| `F179CF21` (2026-09-21) | quiet | 5 (warm 1, `?` 4) | 8.9888–9.2676 | 10.2435–10.5134 |
| `F179CF21` (2026-09-21b) | loud | 3 (cold 1, `?` 2) | 10.5797–11.1942 | 11.8156–12.5145 |
| `84385D91` (2026-09-21c) | loud | 12 (cold 3, warm 9) | 10.5784–11.2612 | 11.7886–12.5573 |
| `82724C8F` (2026-09-22b) | loud | 2 (warm 2) | 10.9370–11.0416 | 12.2186–12.3265 |

`F179CF21` is one recipe built both ways (`RLXFW-ID0` digests `config/` only), so
its two rows are the corpus's only quiet/loud pair of one recipe — the shape `D7`
compares.

Over all 138 rlxfw boots `boot.jump_to_ready` runs 6.97–12.56 s: 6.97–7.35 s on
images built before the 300-jiffy wait, 9.77–11.02 s quiet after it, 11.79–12.56
s loud after it, and 8.97 s for the one loud image before it (`2026-08-30b/L3`).

**Terminators** (`TERM-1`): the longest silence inside a boot, from its first
landmark to `ready`, is at most 4.7756 s quiet (`2026-09-08/C6-boot`), 3.0362 s
loud (`2026-09-21e/L9-boot`) and 5.0189 s for the vendor — `K-J`'s ESC window on
the autoboot path. What `looprun` 1.2 does with that is `notes/dev-loop.md`
§ 19's.

**What the report cannot explain yet**

* `X8-WAIT`, the cold vendor boot, printed `sysconf wlanapp kill wlan0` at 98.756
  s and then nothing for the remaining 201.3 s of a 300 s capture; in `K-J` and
  `G6`, `Init bridge interface...` follows that line about 0.8 s later. A vendor
  boot can stop before `boa` for a reason no capture shows.
* `loader.banner`'s warm-minus-cold median is 13.1 ms. `C-8`'s warm line puts 35
  more bytes before the banner (≈9.1 ms at 38400 8N1) and the `booting` medians
  differ by 1.6 ms, which leaves ≈2.4 ms. It is across populations; `D2` compares
  inside one class and one seating.
* Image `0A3135AF`'s `kernel.late` is 0.041 s against 0.024–0.025 s for the other
  images built before the 3 s wait.

## 5. One factor per seating (`CLK-32`)

**The same image runs slower or faster by one factor per directory, and every
segment carries it.** `CLK-31` measured the loader's `booting` interval drifting
9.7 % across seatings and left the cause open between host USB latency and the
device. The retro's section (e) puts each image's per-directory medians beside that
directory's loader `booting` median. Image `84385D91` in `2026-09-21e` (n=8):
loader ×0.959, `rtkload.decompress` ×0.959, `kernel.wlan` ×0.951, `kernel.total`
×0.954, `boot.jump_to_ready` ×0.954. Image `692A2801`: `2026-09-10` ×1.020 against
×1.020–×1.022 for its kernel segments, and `2026-09-14c` ×0.980 against
×0.978–×0.983. The vendor's own image moves the same way: `X8-WAIT`'s directory
×1.022 and its `kernel.total` ×1.030.

Fitting ln(segment ratio) on ln(loader ratio) over every (image, directory) pair,
without `id0=none` (it pools several builds):

| segment | typical (s) | pairs | slope | 95 % interval | r |
|---|---|---|---|---|---|
| `rtkload.decompress` | 1.132 | 22 | 0.926 | 0.730 .. 1.122 | 0.911 |
| `kernel.wlan` | 4.532 | 21 | 0.966 | 0.775 .. 1.157 | 0.924 |
| `kernel.late` | 3.089 | 21 | 0.979 | 0.644 .. 1.314 | 0.814 |
| `kernel.total` | 9.268 | 21 | 0.942 | 0.761 .. 1.123 | 0.928 |
| `boot.jump_to_ready` | 10.554 | 20 | 0.940 | 0.757 .. 1.123 | 0.931 |

The pairs are not independent (an image in two directories gives two points
mirrored about 1), so the intervals are indicative.

**What this settles.** USB latency is additive — milliseconds per read — and
cannot stretch a 4.5 s interval by 4 %. For every segment of a second or more the
slope's interval excludes 0, so the additive explanation is refuted there, and it
holds 1, so one multiplicative factor per seating stands. **What it does not
settle** is whose clock carries the factor: a fast host monotonic clock and a slow
device timebase produce the same ratios, because every interval here is a device
event timed by the host. Today's host reading: over 120 s WSL's `CLOCK_MONOTONIC`
and `CLOCK_REALTIME` agreed to 0.0 ppm (`MONOTONIC_RAW` +310.8 ppm), with
`systemd-timesyncd` active and the clocksource `tsc` — so the host clock was not
off by percent today, which says nothing about the seatings above. From 2026-09-23
every capture carries its own `t0_real`/`end_real` pair, and every probe its
start/end pairs, so each seating records its host clock against realtime; the
device side needs a clock that is neither, which is `P2-6`'s logic analyser on the
TX line.

**Consequences, written before seating A:**

* `D2` is unaffected: both columns inside one seating carry the same factor.
* `D3` compares seatings. One image has already differed by 6.7 % between two of
  its directories (`F179CF21` loud, `rtkload.total`: 1.1950 s in `2026-09-21b`,
  n=2, against 1.2745 s in `2026-09-21c`, n=1), before any firmware difference
  enters. The plan's ±10 % stays as written; each `D3` cell is published a second
  time divided by its own seating's loader `booting` ratio, beside the raw figure
  and never instead of it.

## 6. What the retro table does not establish

* It is a prediction, not a result: every capture was taken for another question,
  on images that differ from `P2-2`'s, often with the NIC in states `P2` does not
  use. `P2-2`'s card re-derives each prediction from the nearest image and names
  the delta (its `/init` brings the LAN up; `recover` is on).
* The vendor column is 6 boots, 3 of them `J 80500000` of the staged image, one a
  warm autoboot, one a cold autoboot that stopped before `ready`, and one fragment.
* No committed capture has an absolute origin, so no retro value exists for
  network up (`D8`) or daemon readiness (`D4`). `P2-3`'s first readings of those
  are first readings, not scored predictions.
* The per-seating factor is a property of the setup this corpus was taken in.
  Whether the host or the device carries it is open (§ 5).

## 7. Seating A (`P2-3`), 2026-09-23 — the first readings

Card `bench/2026-09-23/PREDICTIONS-B44-block42.md`; every departure from it is in
`bench/2026-09-23/CORRECTIONS-block42.md` §§ 1–6. Twelve presses, 15:09–17:37;
`check-predictions` read 223 of 223 fenced cells captured after the card, all on
the declared date. The three flash-map brackets matched the prediction (`FLS-30`):
`P1-M0`, `P2-M0` and `P3-M0` are 3,013 B each with body digest `0927be41e91fe4bd`,
one `DIFFER` in group 0 against the 2026-08-16 dump, and 31 groups the same.

### 7.1 `D2` holds (`CLK-34`)

Computed from `Z9-D2.tsv` (`boot-timeline --retro`, run as `CORRECTIONS` § 1 says)
by a script written at 15:30 — after `P1-A` (15:09–15:13), before every other
capture the groups use (the first warm reset 15:54:54, the first vendor capture
16:36), so before any rlxfw-vs-vendor number existed. Quantity: `loader.banner`
(`booting` → banner), s.

| group (card § 3.1) | captures | n | values | median |
|---|---|---:|---|---:|
| rlxfw cold | `P1-A`, `P2-A`, `P3-A` | 3 | 0.5861, 0.5727, 0.5706 | 0.5727 |
| vendor cold | `V1-A`…`V3-A` | 3 | 0.5733, 0.5729, 0.5731 | 0.5731 |
| rlxfw warm | `P1L-r02/r03-rz`, `P1-RZ`, `P1Q-r02/r03/r04-rz`, `P2Q-r02-rz`, `P3Q-r02-rz` | 8 | 0.5890, 0.5889, 0.5878, 0.5877, 0.5890, 0.5876, 0.5822, 0.5812 | 0.5878 |
| vendor warm | `V4-WZ`…`V7-WZ` | 4 | 0.5786, 0.5813, 0.5822, 0.5727 | 0.5800 |
| loader-only cold (context) | `V4-A`…`V7-A`, `M2-A` | 5 | 0.5724, 0.5664, 0.5732, 0.5711, 0.5720 | 0.5720 |
| mode control, cold (listen) | `M1-BOOT` | 1 | 0.5726 | — |
| mode control, warm (listen) | `M2-BOOT` | 1 | 0.5808 | — |

Against the bands written before power: warm rlxfw − vendor **+0.0078 s** (±0.010)
within; cold **−0.0004 s** (±0.025, a limit at n = 3) within; `M1-BOOT` − rlxfw cold
−0.0000 and − vendor cold −0.0005, `M2-BOOT` − rlxfw warm −0.0070 and − vendor warm
+0.0008, each within ±0.010. **`D2` holds.**

**What the verdict does not carry.** The rlxfw warm group splits by press: `P1`'s
six resets read 0.5876–0.5890 s, `P2Q-r02-rz` 0.5822 and `P3Q-r02-rz` 0.5812 — a
6–8 ms step inside one image family, and most of the +7.8 ms. The leading
candidate, 推, is the host clock (§ 7.2); the others are the board's state before
the watchdog reset (`P1`'s rounds ran with the LAN under a 20 Hz probe and TFTP)
and a drift of the loader itself.

### 7.2 The host's `CLOCK_MONOTONIC` ran slow for most of the seating (`CLK-35`)

量, three references that are not the host's monotonic clock:

* **The board's timer.** `CONFIG_HZ=100` (讀, the image's `.config`). From `P1-N0`
  (`j_now` 4294941931, which is −25,365 as a signed 32-bit value) to `P1-US1-S1`
  (124,620): 149,985 jiffies over 1,476.20 s of host monotonic and 1,500.98 s of
  host realtime — 101.60 per monotonic second, 99.93 per realtime second. A second
  computation over the tick-IRQ count of 24 reads: 101.749 against 100.0025.
* **Windows' clock.** The NTFS mtimes of `P1`'s `.meta.json` files advance
  1.0137–1.0184 Windows seconds per host-monotonic second from 15:54 on, and 1.0014
  over the 41 minutes before.
* **WSL's realtime**, which Hyper-V time sync steps forward: +0.41 to +0.58 s every
  20–35 s under load, six steps totalling +2.7386 s inside `P1-HP`'s 165.2 s;
  realtime − monotonic grew 27.14 s between 15:57:43 and 16:24:41.

So the host monotonic clock — the one every console and probe stamp is on — ran
slow while the device's own timer agreed with realtime to within 0.07 %. Over the
whole seating, from the realtime − monotonic offsets of successive captures (one
computation, 量, assuming the steps follow Windows' clock): 0.000 % inside `P1-A`
(15:09), 0.18 % from 15:13 to 15:55, then 1.80 % from 15:55 to 16:40 and 1.74–2.41 %
in every window through 17:08 — the vendor presses included, whose traffic is a
probe at 20 Hz. So the slowing began with `P1`'s traffic and did not end with it;
§ 5's 0.0 ppm (a quiet 120 s, earlier that day) is not contradicted, and "load"
alone does not describe it.

**The loader's in-seating drift matches it** (推). `P1-A`, captured while the rate was
near 0, exceeds the later cold catches by ×1.0225 on `loader.booting` and ×1.0238 on
`loader.banner` — the host's later rate almost exactly; `P1`'s warm resets exceed
`P2`'s and `P3`'s by ×1.0118 and ×1.0114, as the rate did between 15:55 and 17:03.
If so, § 7.1's warm split and most of `D2`'s +7.8 ms are the host clock: with a
rate ratio of 1.022 the warm Δ would read about −3.8 ms, still inside the band.

**Consequences.** (1) An interval this seating measured after 15:55 is short by up
to 2.4 %, by an amount that changed over the afternoon. (2) `CLK-32`'s per-seating
factor is, 推, at least partly this host clock and not the device; refuted by a
seating whose host monotonic rate, measured against the board's jiffies, stays
constant while `CLK-32`'s factor still moves. (3) § 5's "`D2` is unaffected: both
columns carry the same factor" holds only when both columns were captured at the
same host rate; here most rlxfw warm catches ran at 15:55–15:57 and the vendor warm
catches at 17:08–17:29. (4) `dmesg -T` converts old kernel lines with the current
offset, so it shifted them by the accumulated steps — 24–26 s in this seating
(`CORRECTIONS` § 5.2); journald's stamps do not.

**Not established:** the mechanism; anything about earlier seatings, whose captures
carry no real/mono pairs.

### 7.3 `D8` on rlxfw (`CLK-36`)

* **Channel offset** (card § 3.4). Fifteen `P1-OFF` cells, 139 B each; the probe
  recorded 15 `udp` events on port 50000, each `len=10`. offset = t_udp − t_console,
  the console event being the FW-35 time of the header's first byte (byte 66, the
  `t` of `traceroute to 10.1.1.2`). Over `OFF02`–`OFF15` (n = 14) the offset runs
  −206.5 to +494.4 µs, a range of **701.0 µs** with the probe's read stamps, and
  896.6 µs with the kernel's receive stamps converted through each capture's own
  real/mono pair. Both exceed 260.4 µs: the stability test fires, as the card
  predicted, so network up is published only as a console-side bound. Two
  computations sharing no code agree on all fifteen offsets.
* **Network up, quiet image** (`P1Q-r01`…`r04`): J+[9.745–9.776, 10.777–10.806] s,
  width 1.028–1.037 s (the card: 1.00–1.09 s); the console's own `lan up` at
  J+10.61–10.62 lies inside every bracket. Each bracket is a reconstruction —
  `hostprobe` records no ARP broadcasts: the lower edge is the send of the answered
  cycle's first queued request (推, from ping's rtt), the upper edge is bounded by
  the reply's read time (量). One computation, not yet second-sourced.
* **The loud image has no reading.** In `P1L-r01`…`r03` no reply came before
  `looprun`'s `busybox reboot -f`, 0.16–0.22 s after the prompt. 推: the host's ARP
  cycle restarts at each boot's NIC probe and its answered broadcast falls 4.19 s
  later — after the quiet image's `N-NDOPEN` (4.054 s) and before the loud one's
  (4.449 s).
* **The card's regimes did not occur.** At all seven jumps `--neigh` read
  INCOMPLETE with no address: the "cached entry" regime never happened, and the one
  flushed loud boot has no reading, so the flushed-versus-cached contrast is not
  available from `P1`.
* **The card's stamp rule is wrong on this host.** `ping_real − (start_real −
  start_mono)` assumes realtime − monotonic is constant; with § 7.2's steps it
  places the first replies 1.362–2.270 s late. The probe's own read time is what
  survives.

### 7.4 Byte predictions, the vendor's boots, and the loader's two paths (`LDR-46`)

* rlxfw: every loud boot 7,948 B (`P1L` ×3, twelve `tmpReg` fields, e = 0); every
  quiet boot 2,117 B (`P1Q` ×4, `P2Q` ×2, `P3Q` ×2); each with `RLXFW-ID0=A2C56BC8`
  and `RLXFW-N7=00000011`; every map 3,013 B; every offset cell 139 B — all as
  predicted.
* The vendor: all seven `J 80500000` boots (`V1-BOOT`…`V7-BOOT`) are 1,789 B and end
  at `boa: starting server pid=350, port 80`, as predicted. None is byte-identical to
  `G6`/`G7`: the lines are the same, but `iwcontrol RegisterPID to (wlan0)` and
  `route: SIOCDELRT: No such process` come out in the other order — two processes
  printing in a race. `M1-BOOT` (cold, listen) is 1,901 B and `M2-BOOT` (warm,
  listen) 1,979 B, both to `boa`.
* The loader's autoboot path (`M1`, `M2`) prints `Jump to image start=0x80500000...`
  straight after the banner, with no `P0phymode=01, embedded phy` and no
  `---Ethernet init Okay!`: those two lines appear only on the path that enters the
  prompt.
* Every burn-flag read (`*-AB`, `*-AB2`) returned `00000001`, as predicted.

### 7.5 `D4` and `D6`, first readings (`NET-115`, `MEM-19`)

* rlxfw: `P1-PS` lists `/bin/sh`, the kernel threads, and nothing else. `P1-NMAP`
  (a connect scan of all 65,535 TCP ports, `-T4 --max-retries 1`): none open,
  58,989 closed, 6,546 filtered (no response).
* The vendor (`V1-NMAP`, the same scan): 80/tcp open (predicted); 52869/tcp and
  52881/tcp open (first reading; 推 `miniigd`'s UPnP ports); 65,381 closed, 151
  filtered.
* rlxfw memory after boot (`P1-FREE`): `MemTotal` 26,984 kB, `MemFree` 20,932 kB;
  `busybox free` used 6,012 kB.
* `D4` readiness, `V1` only (one computation): first ICMP reply J+14.541 s, first
  `tcp port=80 result=ok` J+26.270 s, the `boa: starting server` line's first byte
  J+26.310 s. The reply precedes the TCP success, as predicted; the TCP success comes
  40 ms *before* the console line, where the card predicted it would follow within
  ~1 s — a miss in sign at n = 1.
* `D5` (a), ICMP: all 30 runs (five payloads × `P1`, `P2`, `P3`, `V1`, `V2`, `V3`)
  20 of 20, 0 % loss, as predicted. Average rtt, rlxfw 1.516–1.815 ms at 56 B and
  2.052–2.252 ms at 1,472 B; vendor 1.504–1.710 and 1.656–1.956 ms. The card's 56 B
  band, 1.9–3.5 ms, misses low in all six series; it came from 4-echo pings at the
  default 1 s interval, and these are 20 echoes at 50 ms.

### 7.6 Computed once, not yet second-sourced (`CLK-37`)

One computation, by hand from `Z9-D2.tsv`, with `J` the tool's `jump` landmark (the
loader's `---Jump to address=` line, § 3.1), not `sent_s`:

* f_A: this seating's warm `loader.booting` median 0.347425 s (n = 13) / 0.353718 =
  0.98221. The other choices of B_A (cold, all, `esc_after` only) give
  0.98302–0.98659 and change no banded verdict.
* `J` → prompt, `p2q`: median 10.5916 s, 8 of 8 inside 10.15–11.71 s (predicted
  f_A × 10.72 = 10.531) — **hit**. `p2l`: median 12.3618 s, 3 of 3 inside 11.84–13.12 s
  (predicted 12.260) — **hit**.
* The vendor's `kernel.total`: warm 6.8934–6.9252 s inside the raw 6.8895–6.9817 —
  **hit**; 9 of 9 inside the § 5 form f_A × 6.93–7.15.
* The vendor's `J` → `boa`: medians 26.217 s cold and 26.192 s warm against the raw
  25.654–26.126 s — **miss**: at least five of nine above the band, one below (25.339).
* `D7`: loud `kernel.total` median 11.0028 s; Δ(loud − quiet) inside [1.6884, 1.7906] s
  against the registered band [1.3589, 1.9372] s — **holds** for every e from 0 to 12
  and every f_A above. The implied rate, 3,390–3,392 B/s, is 88.3 %, about 0.1 point
  under `FW-70`'s 88.4–92.7 %.
* `M2`'s `loader.esc` 5.1021 s against 4.9503 predicted (+3.07 %, no band).

### 7.7 Owed to the next segment — computed nowhere yet

* A second, independent computation of § 7.6.
* `D2` corrected for § 7.2's host clock, capture by capture, beside the raw verdict:
  fit Windows' mtimes and the board's jiffies against monotonic in windows.
* `D5`'s tables (ICMP for both firmwares; the `iperf3` matrix with board CPU per
  trial). The outcomes on `rlx0` and `eth4` are in `notes/nic-driver.md` § 19.
* `D4` readiness (the first `tcp 80` success against the `boa` line), the vendor's
  `D8` from `V*-HP`/`M*-HP`, and `P3-TCPD`'s check of the `D8` reconstruction.

### 7.8 What seating A does not establish

* `D3`: one calendar day cannot reproduce itself (`P2-4`).
* That § 7.2's host clock is the cause of `CLK-32`'s factor.
* Where inside its one-second bracket rlxfw's network came up; anything about the
  loud image's network up.
* That no flash byte was written: the maps compare 32 digests over 4,186,112 B of
  4,194,304, cannot see two writes that cancel, and do not read `H601`.
