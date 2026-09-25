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

`P2` settled item 4: console bytes and host network events on one clock —
`CLOCK_MONOTONIC` through seating A, `CLOCK_MONOTONIC_RAW` from seating B, because
WSL's `CLOCK_MONOTONIC` is slewed and RAW is not (§ 7.9, `CLK-38`). Both premises
were measured first (`FW-114`).

### 3.1 `console-capture` records its origin (`FW-115`)

1.4 (2026-09-23, `P2-1`) added six keys to `.meta.json` without one byte more or
less on the wire, so `tool_version` stayed 1.4 and the presence of `t0_mono` dates
that schema. 🔄 1.5 (2026-09-24, `P2-4`) moved every stamp and every deadline —
both ESC loops, the CR settle, `--seconds`, `--idle`, the drain — to
`CLOCK_MONOTONIC_RAW`. A deadline decides what is written (an `--esc N` loop lasts
N RAW seconds, where 1.4's lasted N/r on a host slewed to r), so the version moved.
🔴 To within one wait, not better: every wait is one kernel `select` of a whole quantum —
the ESC period in the ESC loops, 50 ms elsewhere — on the slewed clock, and RAW is re-read
only between waits, so a deadline ends up to one quantum late, and one shorter than
q/(1 − r) — the 0.4–0.5 s CR settle whenever r > 0.9 — lasts its MONOTONIC length. 量
2026-09-24 by the 108th segment's end-to-end run: a 0.5 s settle took 0.5284 s at r 0.948,
and `waited_s` recorded it. With `timesyncd` stopped r is 1.00000 and nothing differs.

| key | what it is |
|---|---|
| `clock` | 1.5: `CLOCK_MONOTONIC_RAW`, always. 1.4: the clock `time.monotonic()` reads, as the interpreter reports it — `CLOCK_MONOTONIC` here |
| `t0_raw` (1.5), `t0_mono` (1.4) | the origin every `.timing` second is measured from, unrounded: `t0_raw + seconds` is the instant a read returned on the host's clock. A new key, not `t0_mono` redefined |
| `t0_real` | `time.time()` read beside the origin, for tools that stamp realtime (`ping -D`); from 1.5 `started_wallclock` is this reading, to the second |
| `mono_at_t0`, `mono_at_end` (1.5) | one `CLOCK_MONOTONIC` read beside each end's RAW read, so a record carries its own MONOTONIC/RAW rate; nothing is timed on them |
| `boot_id`, `clocksource`, `clocksource_end` (1.5) | the boot the RAW stamps count from — RAW restarts at every WSL boot — and the kernel's clocksource at each end; `null` if unreadable |
| `sent_s` | seconds since `t0` at which `ser.flush()` of the `--send` line returned; `null` when nothing was sent |
| `end_raw` (1.5) or `end_mono` (1.4), `end_real` | one pair read after the port and files are closed; `duration_s` is `end - t0` from that same reading |

量 by the suite on a pty, 1.4 (cases P18–P23, N42–N43): the tool's origin and every
read fall inside the harness's own `CLOCK_MONOTONIC` bracket, each read landing
80–200 µs after the harness wrote the byte it delivered; two adjacent
`time.monotonic()` calls are 61 ns apart (median of 20,000); a pty answers
`tcdrain` in 6–16 µs. 1.5 (P18–P24, N42–N53; 2026-09-24, the 108th segment's
rehearsal): a read lands 159–464 µs after the harness's write inside its RAW
bracket; `end_raw − t0_raw − duration_s` = +0.325 µs. N44–N48 run the tool under
`tools/clockshim.py`, which slows every Python read of `CLOCK_MONOTONIC` to half
rate plus 1000 s: a played 1.0015 s gap reads 1.0016 s, `--seconds 3` gives
`duration_s` 3.023622, `--idle 0.8` stopped 0.822 s after the last byte, the two
ESC runs spanned 0.996 and 0.997 s on the wire, and the record's MONOTONIC/RAW read
0.4907 = 1.0000 × 0.5 r with the host's r at 0.9815 during the run. Every capture
committed before 2026-09-23 lacks these keys, and a join that needs them refuses
the capture rather than guess an origin from `started_wallclock`, which is a string
to the second.

殘留: when `flush()` returns on the real port (the CP2102 through usbip) is not
measured. `sent_s` marks the whole line handed over; the loader echoes a line
character by character, so on the real port the first echo byte can precede
`sent_s`, which the pty harness cannot show. No segment in § 2 is anchored on
`sent_s`; the join in § 3.3 uses it only as the lower edge of its window.

### 3.2 `tools/hostprobe.py` (`FW-116`)

The host's half: the first ICMP echo reply (`D8`), the first TCP success on a
daemon's port (`D4`), neighbour-table changes, and UDP arrivals, each stamped on
the capture's clock and written one line per event to `PREFIX.events`, flushed per
line; `PREFIX.meta.json` closes the record. 🔄 From 1.3 (2026-09-24, `P2-4`) the
stamp is `t_raw`, `CLOCK_MONOTONIC_RAW`, and so is every deadline the probe
computes; the events file's first line and the meta's `clock` both declare it, a
reader takes the clock from the header as a whole token, and a record whose two
declarations disagree is MALFORMED. The meta gains `start_raw`, `end_raw`,
`stop_decided_raw`, `ping.started_raw`, `mono_at_start`/`mono_at_end`,
`clocksource`/`clocksource_end`, and `boot_id` — written only when it is a version-4
UUID, because the address gate below would otherwise label its last group as a
hardware address (量: `unlisted-1`). A `tcp` line's `start_mono=` is `start_raw=`,
and a `udp` line gains `lag_ms=`, the probe's read time minus the kernel's receive
stamp. Records 1.0–1.2 wrote `t_mono` and still read, on `CLOCK_MONOTONIC`. No packet contents and no
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
timeline: an event at `t` sits at `t - t0` in the capture's `.timing` frame, where
both sides declare `CLOCK_MONOTONIC` (`t_mono`, `t0_mono`: console-capture 1.4,
hostprobe 1.0–1.2) or both `CLOCK_MONOTONIC_RAW` (`t_raw`, `t0_raw`: 1.5 and 1.3).
Only events inside the capture's window (`t0` … `end`) and after `sent_s` count.
Refused, with the reason: either record declaring no clock while carrying no
`*_mono` or `*_raw` key (written before `P2-1`), declaring a clock other than those
two, or carrying a key of the other clock beside the declared one; a capture with
no `t0` or `end` number for its clock; two records on different clocks; two records
whose `boot_id`s differ (both clocks restart at every boot). The capture is checked
before the probe record, in `origin()`'s order. The join prints the boot identity
on every run, and a NOTE when one side or both carry none. One
probe can therefore run across a whole `looprun` block while each round's boot
capture reads its own events out of it.

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
* `loader.banner`'s warm-minus-cold median is 13.1 ms. `C-8`'s warm line puts 37
  more bytes before the banner (≈9.6 ms at 38400 8N1) and the `booting` medians
  differ by 1.6 ms, which leaves ≈1.9 ms. It is across populations; `D2` compares
  inside one class and one seating. 🔄 2026-09-23 (106th segment): the count was 35
  and ≈2.4 ms until a byte count of every loader boot under `bench/` — `ramSize: 32M`
  to the banner is 17 B cold (`\n\r \n\r`) and 54 B warm, 274 of 274 — re-derived it.
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
event timed by the host. The host reading taken with `P2-1` (2026-09-23): over 120 s
`CLOCK_MONOTONIC_RAW` ran +310.8 ppm against `CLOCK_MONOTONIC`, with
`systemd-timesyncd` active and the clocksource `tsc` — so the host's monotonic
clock was not off by percent then, which says nothing about the seatings above.
🔄 2026-09-23 (106th segment): this paragraph also cited `CLOCK_MONOTONIC` and
`CLOCK_REALTIME` agreeing to 0.0 ppm as evidence, and said each capture's
`t0_real`/`end_real` pair records the host clock against realtime. Neither holds:
between `timesyncd`'s steps realtime advances at the monotonic rate, so the two agree
by construction — 量 119 of 158 seating-A captures read (end_real − t0_real) /
duration_s within 2 ppm of 1 while the host ran percent-slow. Only the steps
*between* captures carry the rate (§ 7.2), and the slewing itself is § 7.9's. The
device side still needs a clock that is neither, which is `P2-6`'s logic analyser
on the TX line.

**The retro test (106th segment), pre-registered in
`$FWRE_WORK/rebuild/s106/PREREG-clk32-host.md` before it ran.** Per capture, the
host's monotonic rate against Windows' clock is `duration_s` over the NTFS creation
times of its `.meta.json` and `.log`; per directory, the median r_d, against the
directory's loader `booting` factor f_d. **As registered, the method is refuted and the
hypothesis is not tested**: the control required every capture of seating A between
15:55 and 16:40 to lie within 0.3 % of `CLK-35`'s jiffies rate, and 3 of 14 did not —
the registration assumed a pairing error of ~10 ms, and 量 some captures carry
0.1–0.9 s (file creation on DrvFs). Beside the verdict, not instead of it and not
pre-registered: the window's median passes the control (+0.147 %), and over 21
directories ln f_d on ln r_d has slope 1.087 (95 % 0.904–1.271), r 0.943. Where the
host clock was right (seven directories, |ln r_d| < 0.003) the loader's `booting`
median is 0.3546–0.3578 s: a device-side per-seating factor is bounded at about
±0.5 %. The host ran fast as well as slow (`2026-09-10` 1.029). 推, not established by
a registered test: `CLK-32`'s factor is mostly the host clock. Seating B settles it
by stamping with a clock the host does not slew.

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

**Corrected for the host clock (106th segment).** Each capture divided by the host's
own rate at that moment (§ 7.2; corrected = measured / r): warm rlxfw − vendor
**+0.19 ms** (+0.01 … +2.27 over five ways of estimating r), cold **+0.15 ms**, the four
mode-control differences −0.73 … +0.27 ms. **`D2` holds raw and corrected.** The rlxfw
warm group split by press — `P1`'s six resets 0.5876–0.5890 s against `P2Q-r02-rz`
0.5822 and `P3Q-r02-rz` 0.5812, most of the raw +7.8 ms — does not survive: `P1` over
`P2Q` goes ×1.0105 → ×1.0009 and over `P3Q` ×1.0123 → ×1.0010. It was the host clock.
The control the correction could have failed: the 13 warm catches run identical
loader code, so a right correction must pull them together, and their spread falls
from 0.859 % to 0.094 %. Corrected group medians: rlxfw cold 0.586303 s, vendor cold
0.586157, rlxfw warm 0.596032, vendor warm 0.595841.

### 7.2 The host's `CLOCK_MONOTONIC` ran slow for most of the seating (`CLK-35`)

Four references that are not the host's monotonic clock (106th segment,
`$FWRE_WORK/rebuild/s106/c-clock/`; r = host-monotonic seconds per true second):

* **N — NTP, through `systemd-timesyncd`'s steps.** 量 the seating's journal (103,119
  entries, each carrying both clocks): realtime − monotonic is flat to 59 µs between
  steps, and the steps are `timesyncd`'s — 267, all forward, each followed within
  milliseconds by `systemd-resolved`'s `Clock change detected`, 265 of 266 gaps
  32.21–32.50 s, from 15:50:14 to 18:17:15, busy or idle alike; none before 15:50:14.
  Over one poll r = dM / (dM + step).
* **W — Windows' clock**, through the NTFS stamps of every capture and probe file (985
  pairs; four readers agree to the 100 ns tick), with Windows' own −36.42 ppm against
  NTP removed.
* **K — the WSL kernel's printk clock** (`sched_clock`, on the TSC), carried by every
  kernel journal entry: by 18:17 it was 205.2 s ahead of `CLOCK_MONOTONIC`, against a
  step total of 205.19 s.
* **B — the board's tick** (`CONFIG_HZ=100`, 讀 the image's `.config`): `/proc/stat`'s
  `cpu` ticks — jiffies, which rlxfw's TC1 drives on IRQ 25 — and IRQ 13, the vendor's TC0,
  on each rlxfw dump, placed at their lines' FW-35 arrival.

In every five-minute window holding two or more of them they give r within 0.0005 of
each other (four windows 0.0013–0.0020). **r ≈ 1.000 until ~15:49** — `P1-A`
over its own 180 s 0.99972 — **then a slowdown that grew without a break**: 0.9861 at
15:52, 0.9824 at 16:18, 0.9781 at 16:38, 0.9767 at 16:59, 0.9726–0.9744 at
17:29–17:40, 0.9693–0.9700 at 18:00–18:17; and on top of the trend, 3–20 s swings
between 0.953 and 0.994 (`V7-WZ` fell in one: r = 0.9615, by K and W independently).
The lag was already building by 15:49:43, before `P1`'s first probe (15:54:33), so it
did not start with `P1`'s traffic, and it did not follow load afterwards either
(§ 7.9). Per capture, the corrected loader values are in § 7.1 and
`c-clock/f5-best.tsv`; for a warm catch K and W (Windows' clock over ±10 s) differ by at
most 0.0007 — W over the catch's own bracket, `f5-best.tsv`'s `r_W_brk`, by up to
0.0014 (`V7-WZ`) — and a cold catch's r is an average over its 180 s, uncertain by
±0.3–0.8 % at the loader instant. 🔄 109th segment: "three sparse windows
0.0013–0.0017", "0.9727–0.9744" and "at most 0.0007" without its window were this
paragraph's until a second source re-read `f5-best.tsv` and `f6-rt4.tsv`.

**The board's own rate** from 16:01 to 16:32: 100.0031 ticks per Windows second (48
values, rms 3.6 ms), 99.998 ± 0.001 per NTP second. Between `P1-N0` (15:57:43) and
`P1-TR1-S0` (16:01:16) the board's jiffies advanced **105 ticks fewer** than that rate
predicts (the condition written first was |Δ| ≤ 3) — which is the whole of the 99.93
per realtime second this section used to quote over `P1-N0` → `P1-US1-S1`. 推 timer
interrupts masked for about a second; the cell is not identified. 🔄 111th segment: this
section took IRQ 13 for the tick — in *B*, here ("the board's counters advanced") and in the
note below — until seating B read `cpu` − IRQ 25 at 34 in 54 of 54 dumps across the same loss
while IRQ 13 − IRQ 25 went 35 → 100 (§ 8.3, `CLK-42`). Jiffies are rlxfw's TC1, IRQ 25, as
`docs/interrupt-map.md` § 7 already said; IRQ 13 is the vendor's TC0, which in seating B
lost ~45 where jiffies lost ~105, and which here read 65 above `cpu` at `P1-TR1-S0` as well.
A mask of both timers for about a second does not fit a loss TC0 shared only in part; 推
the cell is `P1-AC0`'s `asicCounter` read (§ 8.3).

**What the correction does.** `P1-A`'s excess over the later cold catches (×1.0225 on
`booting`, ×1.0238 on `banner`) becomes ×0.9993 and ×1.0003; § 7.1's warm split
disappears; `D2` holds either way. So the loader did not drift inside this seating:
the host's clock did.

**Consequences.** (1) An interval measured after ~15:49 is short by 1.4 % (15:52) to
3.1 % (18:10), and by up to 3.9 % over 2–7 s stretches. (2) `CLK-32`'s per-seating
factor is, 推, mostly this host clock — § 5's retro test, where it is written what
that test could and could not decide. (3) § 5's "`D2` is unaffected: both columns
carry the same factor" holds only when both columns ran at the same host rate; here
six of the eight rlxfw warm catches (press 1's) ran at r 0.986, `P2Q-r02-rz` and
`P3Q-r02-rz` at 0.977 and 0.975, and the vendor warm ones at 0.961–0.976 (🔄 109th
segment: this read "the rlxfw warm catches ran at r 0.986").
(4) `dmesg -T` converts old kernel lines with the current offset, so it shifted them
by the accumulated steps — 24–26 s in this seating (`CORRECTIONS` § 5.2); journald's
stamps do not.

🔄 Until the 106th segment this section quoted three references read by one
computation, called the steps Hyper-V's and load-driven, gave "0.000 % inside `P1-A`,
0.18 % from 15:13 to 15:55" (step counts, not rates), put the host at "up to 2.4 %"
slow, reached a corrected warm Δ of −3.8 ms by assuming `P1`'s resets ran at r = 1
(they ran at 0.9861), and cited a tick count of IRQ 24 (it reads 0; jiffies are
IRQ 25, 🔄 above).

**Not established:** who writes the host's tick (§ 7.9); r at a cold catch's loader
instant to better than ±0.3–0.8 %; that the corrected values are the loader's true
durations (they still carry FW-35's per-read latency); anything about earlier
seatings, which have no N, W or K record of this kind.

### 7.3 `D8` on rlxfw (`CLK-36`)

* **Channel offset** (card § 3.4). Fifteen `P1-OFF` cells, 139 B each; the probe
  recorded 15 `udp` events on port 50000, each `len=10`. offset = t_udp − t_console,
  the console event being the FW-35 time of the header's first byte (byte 66, the
  `t` of `traceroute to 10.1.1.2`). Over `OFF02`–`OFF15` (n = 14) the offset runs
  −206.5 to +494.4 µs, a range of **701.0 µs** with the probe's read stamps, and
  896.4 µs with the kernel's receive stamps converted through each capture's own
  real/mono pair (🔄 111th segment: 896.6 µs until the offsets were re-derived in exact
  decimals from the recorded stamps, 896.369 µs; float arithmetic on a 1.79e9 s realtime
  moves an offset by ~0.2 µs). Both exceed 260.4 µs: the stability test fires, as the card
  predicted, so network up is published only as a console-side bound. Two
  computations sharing no code agree on all fifteen offsets.
* **Network up, quiet image** (`P1Q-r01`…`r04`): J+[9.745–9.776, 10.777–10.806] s,
  width 1.028–1.037 s (the card: 1.00–1.09 s); the console's own `lan up` at
  J+10.61–10.62 lies inside every bracket. Each bracket is a reconstruction —
  `hostprobe` records no ARP broadcasts: the lower edge is the send of the answered
  cycle's first queued request, the upper edge is bounded by the reply's read time.
  **Checked against frames** (106th segment): `P3-TCPD`'s stamps, converted to
  monotonic through the boot's journal (each entry carries both clocks, so every
  realtime step is placed), put `P3Q-r02`'s answered `who-has` 5.0 ms before the
  reply's read and the method's lower edge within 0.3 ms of the frame — the method
  holds there, n = 1. Its limits, 量: it assumes the answer came on a cycle's second
  broadcast (true of every rlxfw boot here, never of the vendor's); an edge taken from
  ping's rtt is wrong across a realtime step, while the probe's own monotonic ledger is
  not; it assumes the host had carrier, and 11 of the 42 broadcasts the ledger implies
  in `P3` never reached the wire (the host loses carrier at each boot's NIC probe). On
  rlxfw the console's `N-NDOPEN` is the tighter lower bound (0.81 s later than the
  method's edge in `P3Q-r02`). `P3Q-r01` has no `is-at` at all: its `rlx0` was up
  0.212 s before `looprun` reset it, and no request reached it in that window.
* **The loud image has no reading.** In `P1L-r01`…`r03` no reply came before the next
  `busybox reboot -f`, sent 0.189–0.221 s after the prompt (0.220–0.251 s after
  `N-NDOPEN`) — by `looprun` after `r01` and `r02`, and after `r03` by the card's own
  `P1-RZ`, 0.098 s after `looprun` closed (量, 107th segment, `P1L.stages.tsv` against
  `P1-RZ.meta.json`). 量 from `P3-TCPD`: after the carrier loss at each NIC probe the
  host transmits nothing until the next ARP cycle, whose second broadcast lands at
  NIC+4.18–4.27 s; the quiet image opens `rlx0` at NIC+4.01–4.05 s, just before it, the
  loud one at NIC+4.45 s, just after. 🔄 111th segment: the loud image now has a reading —
  seating B's was answered at k = 3 in 3 of 3, first replies J+13.231–13.281 s (§ 8.7,
  `CLK-47`) — and NIC+4.01–4.05 and 4.45 s are raw values on the slow host clock: seating B's
  RAW reads 4.103–4.113 s (quiet, n = 8) and 4.511 s (loud, n = 3), medians within 0.6 ms of
  seating A's corrected ones. `N-NDOPEN`'s lead over the quiet image's #2 is not a board
  quantity: 0.13–0.22 s in this seating's ledger on its own clock (量
  `$FWRE_WORK/rebuild/s111/netup/netup-A.out`), 0.07–0.15 s by seating B's frames on RAW
  (推 the slow clock stretching the host's ARP schedule, untested).
* 🔄 **The quiet image was read through the same window** (107th segment): its first
  replies beat the next reset by 16.1, 2.5 and 39.5 ms in `P1Q-r01`…`r03` (量, two
  computations sharing no code), and `P3Q-r01` got none (🔄 111th segment: `P2Q-r01` and
  `P2Q-r02`, which this list left out, were answered at k = 2, first replies J+10.7145 and
  J+10.7120 — `P2Q-r01`'s read 2.6 ms *after* its next reset was sent; 量
  `$FWRE_WORK/rebuild/s111/netup/netup-A.out`). Which boots have a reading is
  decided by the host's ARP phase against a 0.2 s window, so seating B keeps **both**
  images up past the prompt in every round, the last included. The 1.05 s this bullet
  used to ask of the loud image alone — the longest gap between broadcasts on the wire in
  `P3`, the 1.000 s ARP retransmit plus one 50 ms ping interval — is a floor with no
  margin for a lost first answer; seating B waits 2.5 s (`looprun` 1.3's `S9`, `FW-127`:
  RAW seconds, while the host's ARP timer runs on the slewed clock, so the margin is
  wider than 2 s). With the wait the loud boots should
  be answered on a cycle's third broadcast (推, from seating A's timing), so the
  lower-edge rule above, which assumes the second, gives way to the general one used for
  the vendor's boots (§ 7.7).
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
  at `boa: starting server pid=350, port 80`, as predicted. Four — `V3`, `V4`, `V6`,
  `V7` — are byte-identical to `G6` and `G7` (sha256 `2f921f7508dd69b4…`); the other
  three, identical to each other (`89df2d260b86e48d…`), print `iwcontrol RegisterPID
  to (wlan0)` and `route: SIOCDELRT: No such process` in the other order — two
  processes printing in a race, 66 bytes, 1302–1368 counted from 1 (`cmp -l`). `M1-BOOT` (cold,
  listen) is 1,901 B and `M2-BOOT` (warm, listen) 1,979 B, both to `boa`; from
  decompression on, `M2`'s text is `G6`'s and `M1`'s has the other order. 🔄 2026-09-23
  (106th segment): this bullet said none of the seven was byte-identical to `G6`/`G7`
  until two digests taken independently (the `CLK-37` second computation's and
  `sha256sum`) refuted it.
* The loader's autoboot path (`M1`, `M2`) prints `Jump to image start=0x80500000...`
  straight after the banner, with no `P0phymode=01, embedded phy` and no
  `---Ethernet init Okay!`: those two lines appear only on the path that enters the
  prompt.
* Every burn-flag read (`*-AB`, `*-AB2`) returned `00000001`, as predicted.

### 7.5 `D4` and `D6`, first readings (`NET-115`, `MEM-19`)

* rlxfw: `P1-PS` lists `/bin/sh`, the kernel threads, and nothing else. `P1-NMAP`
  (a connect scan of all 65,535 TCP ports, `-T4 --max-retries 1`): none open,
  58,989 closed, 6,546 filtered (no response; 🔄 111th segment: 推 RSTs that arrived after
  `nmap` gave up rather than missing ones, by block 45's E3 — an analogy, since this scan
  had no host counters; `notes/nic-driver.md` § 21.3, `NET-120`).
* The vendor (`V1-NMAP`, the same scan): 80/tcp open (predicted); 52869/tcp and
  52881/tcp open (first reading; 推 `miniigd`'s UPnP ports — of 52869 only, 🔄 below);
  65,381 closed, 151 filtered.
* rlxfw memory after boot (`P1-FREE`): `MemTotal` 26,984 kB, `MemFree` 20,932 kB;
  `busybox free` used 6,012 kB.
* `D4` readiness, all nine vendor boots (J the loader's jump line; host monotonic, raw):

  | boot | regime | first ICMP reply | first `tcp:80` ok | `boa: starting server` | ok − line |
  |---|---|---:|---:|---:|---:|
  | `V1` | cold | 14.5406 | 26.2698 | 26.3096 | −0.0398 |
  | `V2` | cold | 14.9857 | 26.0696 | 26.0858 | −0.0161 |
  | `V3` | cold | 15.6499 | 26.2748 | 26.2582 | +0.0165 |
  | `V4` | warm | 14.4903 | 25.2496 | 25.3394 | −0.0898 |
  | `V5` | warm | 14.5123 | 26.2577 | 26.2158 | +0.0418 |
  | `V6` | warm | 14.4974 | 26.0582 | 26.1917 | −0.1336 |
  | `V7` | warm | 15.5855 | 26.2433 | 26.2376 | +0.0058 |
  | `M1` | listen, cold | 15.6368 | 26.0581 | 26.1757 | −0.1177 |
  | `M2` | listen, warm | 14.5307 | 26.1097 | 26.0574 | +0.0523 |

  The reply precedes the TCP success in 9 of 9, by 10.42–11.75 s, as predicted. The
  card's "`tcp 80` ok follows the `boa` line within ~1 s" holds in magnitude (all nine
  within 0.134 s) and not in sign: the success follows the line in 4 and precedes it in
  5. 推: `boa` listens 0.111–0.127 s before its `boa: server version` line's first byte
  reaches the host, and the probe's 0.2 s connect phase decides the sign; refuted by a
  seating-B boot whose last-refused-to-first-ok window excludes that offset. No
  cold/warm/listen difference is resolved at n = 3/4/1/1. The 52869/52881 attribution
  stays 推 (`miniigd`'s port is configured). 🔄 111th segment: this bullet and the census
  gave both ports to `miniigd` until seating B's first readiness readings put 52881's listen
  with the WPS daemon's `WiFi Simple Config` line, 4.79–5.96 s before `MiniIGD`'s, in 9 of 9
  boots, and the SDK tree names 52881 `RTK_WPS_LISTEN_PORT`: 推 `wscd`'s (§ 8.8, `NET-118`).
* `D5` (a), ICMP: all 30 runs (five payloads × `P1`, `P2`, `P3`, `V1`, `V2`, `V3`)
  20 of 20, 0 % loss, as predicted. Average rtt, rlxfw 1.516–1.815 ms at 56 B and
  2.052–2.252 ms at 1,472 B; vendor 1.504–1.710 and 1.656–1.956 ms; mdev 0.280–2.080 ms.
  The card's 56 B band, 1.9–3.5 ms, misses low in all six series; it came from 4-echo
  pings at the default 1 s interval, and these are 20 echoes at 50 ms. Second-sourced
  (106th segment): all 140 min/avg/max/mdev cells reproduce from the logs by a separate
  parser, with a planted-mutation control.

### 7.6 The timing predictions, computed twice (`CLK-37`)

Two computations sharing no code: by hand from `Z9-D2.tsv` (105th segment), and a
parser written for the purpose that never imports the tool (106th segment,
`$FWRE_WORK/rebuild/s106/t-clk37/`, its own FW-35 lookup in exact decimals, 26
controls, and a second derivation inside it that a planted FW-35 mutant disagrees with
190 times). Every value the two share is equal to the microsecond: 52 loader values
and their classes, 208 segment values, 223 landmark times and offsets, 20 kernel-boot
classes; of 93 pooled kernel cells, every n, min and max is equal and 18 even-n medians
differ by exactly 0.5 µs (the tool prints a float median to six places). `J` is the
tool's `jump` landmark: `---Jump to address=` after a typed `J`, `Jump to image
start=` on the autoboot path (`M1`, `M2`). Every interval is host `CLOCK_MONOTONIC`,
uncorrected (§ 7.2, § 7.9).

* f_A = 0.982209: this seating's warm `loader.booting` median 0.347425 s (n = 13) over
  0.353718. The other choices of B_A give 0.983020–0.986585 and change no banded
  verdict. The warm population splits by press — press 1's median 0.351351 s (f
  0.993308), presses 2–12's 0.347171 s (0.981491) — so dropping the one listen boot
  moves the median into the gap: a 0.45 % change in f from one boot.
* `J` → prompt, `p2q`: median 10.591562 s, 8 of 8 inside 10.15–11.71 s (the point f_A ×
  10.72 = 10.529280) — **hit**. `p2l`: median 12.361805 s, 3 of 3 inside 11.84–13.12 s
  (point 12.257968) — **hit**. The first read's arrival minus `sent_s` is +61…+140 µs
  on all 19 boots that carry a send. 🔄 111th segment: this sentence ended "so neither
  anchor moves a verdict", reading `sent_s` as the send, which it is not: the loader's
  `---Jump` line, printed once it has the CR, reached the host 1.0–6.3 ms before `sent_s` in
  23 of 23 typed-`J` captures (量 at ≤ 3,840 B/s, `$FWRE_WORK/rebuild/s111/timing-v/seatA/`),
  so `J`'s stamp is at least 1.1–6.4 ms late, and every `J`-anchored interval here reads
  short by that less its far end's own lateness (§ 8.5, `CLK-44`). Every verdict in this
  section clears its band's edge by more.
* The vendor's `kernel.total`: warm 5 of 5 inside the raw 6.8895–6.9817 s (median
  6.912024) — **hit**; 9 of 9 inside the § 5 form f_A × 6.93–7.15.
* The vendor's `J` → `boa`: 7 of 9 outside the raw 25.654–26.126 s — **miss**. Six above
  (`V1` 26.309627, `V3` 26.258240, `V5` 26.215816, `V6` 26.191747, `V7` 26.237552,
  `M1` 26.175747), one below (`V4` 25.339388), two inside (`V2`, `M2`). The spread is in
  userspace (`user.ready` 17.406–18.317 s); `V4` is fast by one step, `WiFi Simple
  Config` → `Register to wlan0` in 0.147 s against 1.114–1.131 s in the other eight.
* `D7`: Δ(`kernel.total`, loud − quiet, press 1) = 11.002774 − 9.314144 =
  **1.688630 s**, e = 0 in every loud capture (all twelve fields `tmpReg[0xe]`), inside
  the registered band [1.358917, 1.937168] s — **holds**. The whole 5,831-byte
  difference lies between `kentry` and `rlxfw: init running`: +810 B in `B00`→`B09`,
  +5,021 B in `B09`→`B10`, 0 in every other segment, 12 of 12 pairs. The implied rate
  f·ΔB/ΔT is 88.325 % with f_A — 0.1 point under `FW-70`'s 88.4–92.7 % — and inside
  it with the cold (88.455 %), cold-`esc` (88.512 %) or `esc_after`-only (88.718 %)
  median, or with press 1's own factor (89.323 %); which side of `FW-70` it lands on is
  decided by the choice of f, not by the measurement. 推: press 1's own factor is the
  like-for-like one, since each boot follows its press's loader better than the
  seating's. The card's no-residual range misses by 1.46 ms at f_A and holds for
  0.983060 ≤ f ≤ 1.030872 (🔄 109th segment: "f ≥ 0.983658" until a second source found
  that 0.983658 is the cold median's f, not the range's edge).
* `loader.esc` (no band): `M1` 5.121936 s against f_A × 5.2 = 5.107487 (+0.28 %), `M2`
  5.102142 s against 4.950333 (+3.07 %).
* 🔄 What the second computation corrected in the first (106th segment): `D7`'s Δ had been
  published as the interval [1.6884, 1.7906] s, which put press 12's quiet boot on the
  quiet side of an "inside one press" quantity; "at least five of nine above" was six
  above, one below and two inside; the points "10.531" and "12.260" were f_A times the
  unrounded 10.722 and 12.482; and "88.3 %, about 0.1 point under `FW-70`" had dropped
  that it flips with f.

### 7.7 The vendor's network up, and what seating B inherits as a test

Every item this section listed as owed was computed in the 106th segment (§ 7.1–7.6,
`notes/nic-driver.md` § 19; the agents' reports and scripts under
`$FWRE_WORK/rebuild/s106/`). The vendor's `D8`, all nine boots (J the loader's jump
line; raw host monotonic): the first reply at J+14.49–14.54, J+14.99 or J+15.59–15.65 —
a 1.1 s spread made by the host's ARP retransmit timing, not by the boot. Brackets,
reconstructed from the probe's own ledger and calibrated on `P3-TCPD`'s frames (推 for
the vendor, whose frames were not captured): the answered broadcast was a cycle's third
in five boots (`V1`, `V4`, `V5`, `V6`, `M2`, bracket 1.020–1.028 s) and the first of the
next cycle in four (`V2`, `V3`, `V7`, `M1`, 1.055–1.081 s); every flush read 0, and
neither void rule fired. No single offset from J fits all nine brackets.

What seating B tests, each written with what refutes it:

* 推 the vendor answers ARP 0.075–0.116 s before its `Start NTP daemon` line reaches the
  host (+0.924–0.997 s after `Init bridge interface...`) in all nine boots — refuted by
  a seating-B bracket that excludes that offset. 🔄 111th segment: not refuted, 9 of 9
  brackets hold it — a weak test, each bracket 1.03–1.10 s wide (§ 8.7).
* 推 `boa` listens 0.111–0.127 s before its `boa: server version` line's first byte
  reaches the host, and the probe's 0.2 s connect phase sets the sign of "ok − line" —
  refuted by a seating-B boot whose last-refused-to-first-ok window excludes it.
  🔄 111th segment: not refuted, 0 of 9 exclude it; the eighteen boots of both seatings
  intersect in (−0.117471, −0.111008], and of 41 console lines only the three `boa` lines
  fit both days. The window's upper edge is the first ok's start + 1 ms, s106's rule
  (§ 8.8).
* 推 `CLK-32`'s factor is the host clock — the loader's `booting` stamped on a clock the
  host does not slew should land within ~±0.5 % of 0.35625 s in every seating. 0.35625 s
  is not a registered value: it is the 106th segment's fit of the loader factor against
  the host rate over 21 directories, read at r = 1 (`$FWRE_WORK/rebuild/s106/r-retro/`
  `REPORT.md`); § 5's seven directories with a right host clock, 0.3546–0.3578 s, all
  lie inside its ±0.5 % (🔄 109th segment: this bullet cited § 5 for the number itself).
  🔄 111th segment: holds — warm 0.356060 s (n = 13), cold 0.355865 s (n = 12) on RAW
  (§ 8.5, `CLK-43`).
* ~~The host clock's mechanism — decided by resynchronizing Windows (§ 7.9).~~ 🔄 Decided
  at the desk by the 107th segment without touching Windows: a trace named the process that
  writes the tick, and stopping the other controller ended the slew (§ 7.9). Seating B no
  longer carries it.

Left open by seating A and not planned: which cell cost the board its 105 ticks
(§ 7.2); why three `rlx0` trials started with a full TX ring and what took `UR1`'s
remaining 6–7 s of setup (`notes/nic-driver.md` § 19.6).

### 7.8 What seating A does not establish

* `D3`: one calendar day cannot reproduce itself (`P2-4`).
* That § 7.2's host clock is the cause of `CLK-32`'s factor.
* Where inside its one-second bracket rlxfw's network came up; anything about the
  loud image's network up.
* That no flash byte was written: the maps compare 32 digests over 4,186,112 B of
  4,194,304, cannot see two writes that cancel, and do not read `H601`.

### 7.9 The host clock the same evening, after the seating (`CLK-38`)

量 2026-09-23 18:40–19:43 (106th segment), inside WSL (kernel
`6.6.87.2-microsoft-standard-WSL2`, clocksource `tsc`), the board off. Scripts and logs
in `$FWRE_WORK/rebuild/s106/` (`clocklog.py`, `clockfit.py`, `clockwin.py`,
`adjtimex-read.py`, `adjtimex-watch.sh`). The 107th segment's trace and interventions
(21:25–22:51, a later WSL boot, `39e37203`) are the bullets from *Who writes the tick*
through *Stopping one controller*; its clock-log build runs and E3 (22:53–02:23, the same
boot) are *A third rate term* and *E3*. Their scripts, logs and registration are in
`$FWRE_WORK/rebuild/s107/` (`e1-trace.sh`, `e1b-trace.sh`, `e2-aba.sh`, `e2-analyze.py`,
`e3/`, `b-hc/`, `PREREG-clk38-mechanism.md`); the 108th segment's re-derivations are in
`$FWRE_WORK/rebuild/s108/`.

* **The kernel's tick is being slewed.** `adjtimex(2)`, read only: `tick` 9721–9737 µs
  per jiffy at 18:42 (nominal 10,000), a new value every 5–10 s, `freq` −46…+48 ppm,
  `status` 0x2000; at 19:25, 9615–9626. So `CLOCK_MONOTONIC` runs at
  tick/10,000 + freq of the raw clocksource — freq is added, not multiplied, and the two
  forms differ by ≤ 2 ppm here — 0.972–0.974, then 0.9615–0.9628, in every second in which
  the kernel PLL holds no offset. 🔄 That condition is a third term (*A third rate term*,
  below, `CLK-39`); this bullet read "tick/10,000 × (1 + freq)" until the 108th segment.
* **The clocks agree with the tick.** Every 20 s one Windows read (`powershell.exe`:
  QPC, its frequency, `DateTime.UtcNow`) is bracketed by two `CLOCK_MONOTONIC` reads
  (bracket 0.09–1.1 s), 178 rows over 3,722.8 s of QPC (18:40–19:43):
  `CLOCK_MONOTONIC` 0.964972 per QPC second, `CLOCK_MONOTONIC_RAW` 1.000016, Windows'
  own `UtcNow` 1.000000. Per five-minute window, `MONOTONIC` fell 0.974 → 0.959 from
  18:41 to 19:38, through two desk sweeps' load and the gap between them — so it is not
  a function of load — while `RAW` stayed within 0.9997–1.0012. ⚠️ 109th segment: a
  second fit of the same log (`$FWRE_WORK/rebuild/s109/arith2/`) reproduces both
  `MONOTONIC` values (0.964972 on 178 rows; the 106th report's 0.964925 on 177, one row
  with a 2.223 s bracket apart) but reads `RAW` 1.000041 and 1.000024, not 1.000016 and
  1.000010: RAW's rate against QPC is known to tens of ppm, and which fit is right is
  not settled.
* **Realtime is stepped forward.** `REALTIME − MONOTONIC` jumped +0.83…+1.04 s every
  20–40 s, +32.49 s over the log's first 1,037.7 s. `systemd-timesyncd` is active
  (ntp.ubuntu.com, poll 32 s); `status` 0x2000 has `STA_PLL` clear, which fits a step
  (量, 107th segment: it steps with `clock_adjtime(ADJ_SETOFFSET)`, below). 🔄 It slews as
  well: with a smaller offset the kernel PLL's offset is written and nothing steps (*A third
  rate term* and *E3*, below), and `STA_PLL` is set only for seconds at a time, so one read
  of `status` cannot tell the two apart. During seating A the journal (whose
  every entry carries both clocks) shows no step before ~15:50, then +0.40–0.53 s every
  ~32.2 s until ~16:10 and +0.70–0.87 s during the vendor presses; the first step
  visible between two captures is inside `P1L-r01-ab2` (15:54:34, +0.494549 s), because
  no capture ran from 15:13 to 15:54.
* **Windows is not synchronized.** `w32tm /stripchart` against ntp.ubuntu.com: Windows
  0.63–0.70 s behind; `w32tm /query /status`: Leap Indicator 3 (not synchronized),
  last successful sync 13:14.
* **Who writes the tick: WSL's own `chronyd`** (107th segment; ftrace, which the kernel
  carries — nothing was installed; conditions written first in
  `$FWRE_WORK/rebuild/s107/PREREG-clk38-mechanism.md`). 量 over 6 min (22:08:55–22:14:59,
  one WSL boot): comm `chronyd`, PID 210, made 86 `clock_adjtime` calls with
  `ADJ_TICK|ADJ_FREQUENCY` — tick 9293–95xx µs, 4.5–7 % slow — each paired with an
  `ADJ_MAXERROR|ADJ_ESTERROR|ADJ_STATUS` call, one update per ~8.4 s; `systemd-timesyncd`
  made 11, all `ADJ_SETOFFSET` — one step each, one per ~32 s, the journal's 11 `Clock change
  detected` — and set no tick; no other process called. PID 210 is in neither Ubuntu's PID
  namespace nor the system distro's (`wsl --system`), so no `ps` lists it: it runs in WSL's
  root namespace. In 60 s it issued 240 `ioctl`s, every one `PTP_SYS_OFFSET` (0x43403d05)
  on one descriptor, one per 0.263 s, and no network call: it reads the only PTP clock
  present, `/dev/ptp0` → `ptp_hyperv`, the host's time. Its cadences, 0.25 s and 8 s on the
  clock it slews, read 0.263 s and 8.4 s on RAW. The kprobe's `tick` field is the value
  written: all 69 read-backs of a read-only `adjtimex` equal chronyd's last write before
  them, 0 of 69 the write before that. 🔴 Both positive controls as registered were
  mis-specified — `timesyncd` steps through `clock_adjtime(ADJ_SETOFFSET)`, not
  `clock_settime` (0 hits), and a kprobe at function entry sees a reader's input, not what
  it returns — so the instrument's sight rests on all three callers appearing and on the
  read-back.
* **When it starts.** 量 `systemd-resolved`'s `Clock change detected`, which follows
  every step: none in the boots of 14:15 and 14:21–15:03; in the seating's boot none
  for its first 42 minutes, then 267 from 15:50:14 to 18:17:15, one per ~32 s poll; in
  the boot after it (18:21), from its second second on. Across the seating Windows' clock
  ran −36 ppm against NTP (§ 7.2's four-reference analysis) and had last synchronized
  at 13:14; if it sat on NTP then, at that rate its offset reaches ~0.34 s by 15:50,
  about the 0.4 s at which `timesyncd` steps (推, the threshold as remembered). In the boot after the seating (18:42), the tick tracked the steps:
  9734–9737 within ~10 s of each step, 9721–9726 between them.
* **Stopping one controller ends the slew** (E2, 22:16–22:51, ABA with logged boundaries).
  A, `timesyncd` running: 19 steps in 10 min, per-minute MONOTONIC/RAW 0.946–0.989, tick
  9256–10833. B, `systemctl stop systemd-timesyncd`: 0 steps; the tick went to 10,000 about
  50 s later and stayed; every minute from 100 s after the stop read MONOTONIC/RAW 1.00000 —
  the registered prediction held. A′, restarted: 0 steps and tick 9976–10003 for 10 min —
  the registered prediction (steps and slew return) failed, and its refutation (steps return
  without slew) did not apply. Found after the run: Windows synchronized at 22:20:30 (System
  log, Time-Service event 37), six minutes before the stop, so A′ ran with Windows back on NTP
  and is confounded. Windows' successful syncs on 2026-09-23 are 04:08:14, 13:14:22 and
  22:20:30 — 32,768 s apart — and `w32tm` reads *not synchronized* between them.
* **A third rate term: the kernel PLL's residual offset** (`CLK-39`). 量 2026-09-23 23:42
  and 2026-09-24 00:12–00:13 (107th segment, boot `39e37203`, the board off) by
  `tools/hostclock.py` 1.0's two live build runs (`$FWRE_WORK/rebuild/s107/b-hc/`
  `live40.clock`, `desk90.clock`): `adjtimex` read-only every second and on every change at
  10 Hz. The offset was written +147.8 ms at 23:42:14, then +271.9, +295.3 and +316.3 ms
  31–32 s apart, each time with `status` 0x2001 (`STA_PLL`), and `status` read 0x0000 again
  0.70–3.61 s later. The offset then decays ×7/8 per second whatever `status` reads —
  `offset >> (2 + constant)` per second at `constant` 1 on this 6.6 kernel, where 2.6.30's
  `SHIFT_PLL` is 4 — each decrement at the first timekeeping update after a REALTIME second,
  and each decrement is added to that second. So MONO/RAW per 1 s pair read 0.9756–1.0166
  (23:41–23:42) and 0.9894–1.0280 (00:12–00:13): up to 35,925 ppm beyond tick/10,000 + freq,
  and `CLOCK_MONOTONIC` ran faster than RAW as well as slower. With the term modelled the
  tool's tick check agrees on 28 of 28 and 62 of 62 pairs. A second arithmetic, apart from
  the tool (`$FWRE_WORK/rebuild/s108/pll-check.py`): subtracting each pair's own decrease of
  the offset leaves a median of 89 and 128 ppm (worst 5,281 and 1,323 ppm; 33 and 74 pairs,
  any with a write inside skipped). 推: the writer is `timesyncd` — besides `chronyd` the
  only caller of `clock_adjtime` in E1's census, where every call it made was a step — and
  `chronyd`'s `ADJ_STATUS` clears `STA_PLL`.
* **E3: the fight returns, slewing before it steps — refuted as registered.** Registered
  before its first row: with `timesyncd` running, no step and every 60 s window's tick
  ≥ 9,900 until at least 00:15 on 2026-09-24; the first step between 00:15 and 01:47 (point
  estimate 00:56); within 10 min of it, a window below 9,900. 量 22:53:41–02:23:43, one WSL
  boot (`39e37203`), a row every 30 s, no Windows sync between: not void, and refuted on two
  conditions — the first step came at 00:14:13.9 (+0.412 s), 47 s before the window, and for
  the 10 min after it every row's tick read ≥ 9,901. The first clause missed as well: tick
  9752 at 23:42:11 and 9865 at 23:44:11 with no step, while MONO/RAW per row pair ran
  0.9929–1.0075 through the 23 h. Steps to 02:23:43: 151, each seen twice — a row interval
  whose `REALTIME − MONOTONIC` jumped, and one journal `Clock change detected` inside it (151
  of 151; none outside a jump) — growing through the night: +0.400…+0.465 s in the 00 h (5),
  +0.401…+0.795 s in the 01 h (102), +0.550…+0.993 s in 02:00–02:23 (44); the tick fell to
  9167 in the 01 h and 9200 at 02:23, and MONO/RAW per row pair to 0.9686–0.9848 after 02:00.
* **The mechanism, and what is still 推.** Two controllers: WSL's `chronyd` slews the guest
  toward Windows' clock through the tick; Ubuntu's `timesyncd` pulls it toward NTP, through
  the kernel PLL while its offset is small and by a step when it is not. While Windows sits
  on NTP they agree; as Windows drifts (−36 ppm) they fight — by slew alone at first, then
  with steps once the offset at a poll passes about 0.4 s (推: the night's five smallest
  steps read +0.400…+0.412 s; systemd's source is not read here), steps that grow as `chronyd`
  pulls the tick further — until Windows' next sync. Seating A's steps began 9,352 s after
  the 13:14:22 sync, E3's 6,824 s after the 22:20:30 one.
* **Consequence.** Seating A's stamps are on the slewed clock (§ 7.2's four references
  agree), and `CLOCK_MONOTONIC_RAW` is not slewed. Seating B stamps `RAW` (`PROGRESS.md`,
  `P2-4`), and runs with `timesyncd` stopped and restarted after, so `CLOCK_REALTIME` makes
  no NTP step, no PLL offset is written, and realtime-stamped tools convert smoothly — the
  rule written before E2, met by its B phase; its clock log (`tools/hostclock.py`) reads the
  host's state throughout.
* **What it does not establish:** that seating A itself ran on this mechanism (no trace then;
  its journal's step pattern matches); who writes the PLL's offset and who clears `STA_PLL`
  (推 above); the step threshold (推, about 0.4 s); the PLL's law beyond these ~40 minutes of
  one boot on one kernel; why Windows' syncs are 32,768 s apart while it reports a 1,024 s
  poll; Windows' own rate against true time; anything before 2026-09-23 05:54 (older
  journals are gone).
* **The guard card B uses, run on this host with `timesyncd` active** (`CLK-40`; 109th
  segment, 2026-09-24 11:03:52–11:04:52, a WSL boot started ~10:49, the board off,
  `$FWRE_WORK/rebuild/s109/guard/`). The exact command of card B's `Z0-HCG` without its
  100 s wait — `hostclock.py run` for 60 s with `--no-sntp --no-windows`, then
  `report` — read ticks of 9566–10000 across the minute (77 rows) and one step of
  +0.551906 s, seen by both of `hostclock`'s detectors (so its step detector was
  positively controlled on this kernel a second time); the report's tick check read
  `strong`, and both of the card's gate patterns refused the report, while both permit
  the permitting lines in the tool's own format. Windows' last successful sync was
  07:26:38 (`w32tm /query /status`), 32,768 s after 22:20:30 as the four intervals before
  it — but the System log carries no event 37 for it, so that log is not a complete
  record of Windows' syncs. The fight was on 12,434 s after that sync; seating A's steps
  began 9,352 s after its sync and E3's 6,824 s after its own.
* 🔄 **Block 46 (2026-09-25 21:22–21:46, `timesyncd` running; its card claims no duration):
  `CLOCK_REALTIME` − `CLOCK_MONOTONIC_RAW` is a sawtooth** (`CLK-38`; 量 from every console
  capture's `t0`/`end` in `bench/2026-09-25c/*.meta.json`, `s112/record/work/rdJ.py`,
  `rdL.py`). Between steps it falls 0.018–0.031 s per RAW second (10th–90th percentile of 197
  step-free intervals, median 0.023); the 13 steps bracketed by samples under 5 s apart are
  +0.595…+1.065 s each, and where two neighbouring steps are both visible they are 32.0–34.5 s
  apart (`CLK-35`'s `timesyncd` cadence). Over arm B's four minutes the offset spans 0.93 s,
  and `B-02-X` alone moves +0.738 s. **What it breaks:** any single realtime → RAW offset used
  across more than about 30 s — `W.pcap` (realtime) against the runner (RAW) is the case. With
  `B-01-R`'s one offset, arm B's frames read 0.50–0.86 s after their cell; each against its own
  cell's capture, 0.103–0.120 s (`notes/nic-driver.md` § 22.2). A1-06's reply to request 1
  reads +0.004 s after its `ping` began with the previous capture's end offset and −0.591 s with
  A1-06-R's own, a step of +0.595 s lying between them. Every pcap ↔ RAW comparison takes the
  offset of the capture around the frame, or `hostclock`'s step record.

## 8. Seating B (`P2-4`), 2026-09-25 — the reproduction

Every number seating A published, measured again on a second calendar day, stamped on
`CLOCK_MONOTONIC_RAW` with `timesyncd` stopped. The desk work over the captures is the 111th
segment's, under `$FWRE_WORK/rebuild/s111/`: one directory per family (`timing/`, `netup/`,
`services/`, `throughput/`, `clocks/`, `mbuntil/`), each re-derived by a second computation
that shares no code with it (the `-v` directories), and `D3` scored three times
(`score-S1/`, `score-S2/`, `score-judge/`). Where a primary and its second source
disagreed, the value below is the one the disagreement settled, and the place is named.

### 8.1 What ran, and what departed from the card (`FLS-31`)

Card `bench/2026-09-25/PREDICTIONS-B46-block44.md` is card B (block 43, frozen for
2026-09-24 and never run: the workstation slept from 14:03:43 to 23:34:33 that day) with
its date, block number and file names substituted, § 4's sync rule rewritten and § 0 ⑧
added; a line-by-line second source showed every other line to be card B's
(`$FWRE_WORK/rebuild/s110/redate/`), and it froze at `c979621`, 23:59:35 (讀 card § 0 ⑧,
`LOG.md` 第一百一十段). Card A's twelve presses in card A's order, 00:25:58–02:48:09; the
first capture began at 00:02:45, the clock log closed at 02:49:20. `check-predictions` read **246 of
246** fenced cells captured after the card, and `capdate` 0 RED (量, the bench night). Every
departure is in `bench/2026-09-25/CORRECTIONS-block44.md`, and there are two, both stops the
card's own stop table handled:

* **§ 1, the clock guard refused** (00:05:55). `Z0-HCG`'s tick check read `strong`: inside
  its minute the kernel's tick went 9937 → 9817 → 10834 → 10001, the 10834 run lasting
  25.302 s. No power; ten minutes later the same line, as the declared off-card cell
  `Z0-HCG2`, permitted (00:18:37). § 8.2 is what the clock log says about it.
* **§ 2, `P2-MB0` refused on its digest** (02:01:30). `P2-M0.log` is 3,009 B and ends
  `map_lines 32` with no line terminator: `--until` stops its capture 0–50 ms after the
  match (`FW-135`), and the card's `MB` digest hashes the last line's terminator
  (`FW-136`). The 34-line map section is byte-identical to `P1-M0`'s and to seating A's
  `P3-M0`'s, and with `awk 1` before `sha256sum` all six maps of both seatings read
  `0927be41e91fe4bd…` (量 `s111/services/mb.out`). The press finished `--from P2-HPX`; the
  owner read § 2 and ruled that `V4`–`V7` and `M2` continue.

**The brackets** (`FLS-31`, 量). `P1-M0`, `P2-M0` and `P3-M0` each carry the predicted header
(`map_hashed=4186112`, `map_h601_skipped=8192`, `map_h601_hashed=0`, `map_truncated=0`),
exactly one `DIFFER`, in group 0, against the 2026-08-16 dump, and the summary line
`31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing`; `flashmap compare` re-run at the desk
prints the same lines. `map_jiffies` read 1300, 1301, 1301. The card carries no
flash-writing command and no `FLR` (讀 card § 4). What the maps cannot see is § 7.8's: two
writes that cancel, `H601`, and the 8,192 B outside the 4,186,112 hashed.

**The exact predictions** (card § 3.2; 量 `s111/services/exact.out`, second source
`services-v/`): 21 of 23 hold, and the two misses are `P2-M0`'s size and digest above. Every
quiet boot 2,117 B (8 of 8); every loud boot 7,948 B with twelve `tmpReg[0xe]` fields, e = 0
(3 of 3); `RLXFW-ID0=A2C56BC8` and `RLXFW-N7=00000011` in 11 of 11; every `P1-OFF` cell
139 B, with 15 `udp` events of `len=10`; the vendor's seven `J 80500000` boots 1,789 B each,
ending at `boa: starting server pid=350, port 80`; `M1-BOOT` 1,901 B and `M2-BOOT` 1,979 B;
every `V*-HD` 118 B and byte-identical to `2026-08-31c/K2-2a` (7 of 7); every burn flag
`00000001` (12) and every `looprun` `S5b` read `00000000` (11). Both line orders of § 7.4
recur — `2f921f7508dd69b4…` in `V1`, `V2`, `V3`, `V5`, `V7`, `89df2d260b86e48d…` in `V4`,
`V6` — and the race moves no byte count.

**One WSL boot, one clock** (量). All 179 `.meta.json` of the seating (163 `console-capture`,
13 `hostprobe`, 3 `hostclock`) carry one `boot_id` (`ef62493d…`), `clocksource` `tsc` at
both ends and `CLOCK_MONOTONIC_RAW`; each capture's `t0_real` agrees with the clock log's
REALTIME at its `t0_raw` to within 6.9 µs (177 metas), so RAW ran unbroken through the
seating. That WSL boot has since ended; nothing in it can be read live.

Block 45 (`R6b`'s first bench block, `bench/2026-09-25b/`, 03:18–03:34) ran on the same
board after the seating; it is `notes/nic-driver.md` § 21's.

### 8.2 The host clock (`CLK-41`)

量 `bench/2026-09-25/Z0-HC.clock` (`hostclock` 1.0, `--no-sntp --no-windows`), read by
`s111/clocks/` and again by `clocks-v/` with its own parser: 11,375 rows over RAW
1423.921–11403.923 (00:02:59–02:49:20), 9,981 `linux` rows, 1,391 `adj` rows and **0 `step`
rows**. Every row reads `status` 0x2000 and `offset` 0: no PLL offset was written, so
`CLK-39`'s third term was absent.

* **The tick never read 10,000** — 0 of 11,372 rows. `timesyncd` stopped at 00:03:13
  (`Z0-TSD`); around that the tick moved in ~8 s runs between 9784 and 9863, then 9937,
  9817, and from RAW 1549.917 to 1575.219 **10834 for 25.302 s**: on its own rows MONOTONIC
  ran 1.083429 per RAW second (+83,428.8 ppm) and gained ~2.11 s. Then 10001 from 00:05:31,
  with four ~1 s dips to 9999 (RAW 1861.9, 1869.9, 2887.9, 2895.9), and **9999 from RAW
  3913.2 (00:44:29) to the end**. `freq` ran −143.56…+142.14 ppm; the net kernel rate from
  00:05:31 on −81.5…+97.8 ppm, except in the four dips, which reached −120.9 ppm (00:10:17)
  and −100.5 ppm (00:27:31).
* **The rows and the rate agree.** Measured MONOTONIC/RAW equals tick/10,000 + `freq` to
  −0.079…+0.029 ppm in every 5-minute window from RAW 1575.219 on. It fell through the
  night, from +72.0 ppm (00:08) to +3.0 ppm (02:43–02:48); per press `P1` +40.930, `V1`–`V3`
  and `M1` +11.752…+12.028, `P2` +8.378, `V4`–`V7` and `M2` +4.271…+5.982, `P3` +3.643 ppm
  (over each press's captures). MONOTONIC gained 0.257030 s on RAW from 00:05:30 to
  02:49:19, a mean of +26.15 ppm, and read 1.00000 per minute only after 02:25, in 23 of 164
  minute windows.
* **What that does to an interval.** A host timer runs on MONOTONIC, so a 10 s timer spanned
  9.99959–9.99996 RAW s, short by 0.04–0.41 ms; every boot capture and probe event is
  stamped on RAW and carries none of it. Card § 3.8's containment names every window whose
  rows show a tick other than 10,000 or `freq` beyond ±100 ppm — here all 9,866.4 s from
  `Z0-TSD` + 100 s to the stop. It tests the two separately, so it names a compensated pair
  (tick 9999 with `freq` +100…+142 ppm nets 0…+42 ppm) as it names a fast clock, and it
  states no size; the sizes above are what the host parts of `D5` and `D8` carry.
* **E2's settled state did not recur** (`CLK-38`). With `timesyncd` stopped there was no
  step and no PLL write, as in E2's B phase, but the tick never settled at 10,000. 推
  stopping `timesyncd` ends the fight between the two controllers and not `chronyd`'s
  following of Windows, and the 10834 run is `chronyd` slewing at its default
  `maxslewrate`, 83,333.3 ppm, on a base near +95 ppm (the guard's later rows net
  +72.7…+90.1 ppm), after a Windows clock that had just woken; and the drift after it is
  Windows slewing out its wake offset —
  `w32tm`'s *Phase Offset* read 0.3208324 s at 00:06:39 (quoted in `CORRECTIONS` § 1; no file
  keeps it) and 0.0002180 s at 06:53:39, with no sync between. The run read +83,428.8 ppm,
  not the 83,333 ppm `CORRECTIONS` § 1 names: the tick alone is +83,400 (a tick moves in
  steps of 100 ppm) and `freq` the rest.
* **The guard** (`CLK-40`). `Z0-HCG` refused on the 10834 run through its tick check
  (`strong`, worst −0.573 ppm; `timerfd 0`), its step gate silent. `Z0-HCG2` permitted at
  00:18:37 (`vacuous`, worst +0.452 ppm): every row tick 10001 with `freq` −36.426…−36.573
  ppm, a kernel rate of +63.43…+63.57 ppm, 36.4 ppm inside the 100 ppm line and on one side
  only — at tick 10001 any `freq` of 0 or more crosses it. The guard judges the rate and the
  containment the tick (讀 card § 3.8), so the guard permitted a regime the containment calls
  affected. `CORRECTIONS` § 1's "tick 10001 from RAW 1575.2 on" held for the 270 s of rows it
  had read; from 00:44:29 the tick read 9999.
* **Windows** (量 `s111/clocks/`: `w32tm` and the System log; the last read the
  coordinator's, 2026-09-25 13:07). No sync fell inside the seating: *Last Successful Sync
  Time* read 23:35:29 at 00:00:09, 02:49:38 and 06:53:39, so card § 4's 推 held, and the
  1,024 s *Poll Interval* (H-a) is refuted by the first of those reads alone. The next sync
  came at **08:41:21** (time.stdtime.gov.tw): the System log's Kernel-General 1 at
  08:41:22.648 stepped the clock +1.0815 s (00:41:21.5656420Z → 00:41:22.6471540Z), then
  +0.25 ms at 08:41:22.684, with no Time-Service event 37 for either — as for 2026-09-24's
  07:26:38 — and no sleep since the wake. The wake sync's event 37 at 23:35:13 plus 32,768 s
  is 08:41:21. 推 the wake sync restarted the 32,768 s cadence (H-b), counted from event 37's
  instant and not from `w32tm`'s 23:35:29. As registered before the read, H-b does not
  hold: card § 4 put the next sync at 08:41:37, counting from 23:35:29, and the test the
  111th segment wrote before the read (`s111/clocks/REPORT.md` § 8) held H-b to 08:41:37
  ± 2 s and refuted it at any other time; the sync came 16 s earlier, and the event-37
  anchor that makes 08:41:21 fit was chosen after the read. By that anchor the next sync
  falls at about 17:47:29, which tests it. Over those 9.1 h Windows fell 1.0815 s behind
  its source, ≈33 ppm slow on average (1.0815 / 32,768), uncertain by the 0.32 s *Phase
  Offset* it was slewing out after the wake (±10 ppm, arithmetic).
  🔄 111th segment, 17:49:14 (量, the coordinator's read, after `41bf452` was pushed at
  17:40:04): *Last Successful Sync Time* 17:47:30; Kernel-General 1 at 17:47:32.026
  stepped the clock +1.1001 s (09:47:30.9207799Z → 09:47:32.0208578Z), then +1.6 ms, again
  with no event 37 and no sleep between. The window written before it, 17:47:28–17:47:31,
  holds, so the cadence counted from the previous sync held once as predicted: H-b is one
  confirmed prediction, not an established rule. The old time at the step, 17:47:30.921,
  lies 0.27 s after the previous step's new time plus 32,768 s (08:41:22.647 + 32,768 s),
  and 1.36 s after its old time plus 32,768 s, so the count 推 starts when a sync completes.
  Windows fell 1.1001 s behind over this interval, ≈33.6 ppm, with no wake offset inside.

### 8.3 The board's tick, and the jiffies it lost again (`CLK-42`)

量 `s111/clocks/` and `clocks-v/`, from each rlxfw press's `TK0` and `TK1` (`/proc/stat`'s
`cpu` and `intr` lines, each at its FW-35 arrival on `t0_raw`), every driver dump's `j_now`,
and `/proc/interrupts`.

* **Jiffies are IRQ 25, not IRQ 13.** `cpu` − IRQ 25 read 34 in 54 of 54 dumps over `P1`,
  `P2` and `P3`, through `P1`'s loss, while IRQ 13 − IRQ 25 went 35 → 100 across it; over
  `P1-TK0` → `P1-TR1-S0` the `cpu` ticks advanced 24,311, IRQ 25 24,311 and IRQ 13 24,376.
  The `cpu` ticks count jiffies, which rlxfw's TC1 drives on IRQ 25 (讀 `docs/interrupt-map.md`
  § 7, which says so); IRQ 13 is the vendor's TC0, counting on its own line. Seating A's IRQ
  13 − `cpu` read 65 at its `P1-TR1-S0` as well. § 7.2 called the tick IRQ 13 (🔄 there).
* **Ticks per RAW second** (card § 3.8 predicted 99.998–100.000). `P1` 99.921673 over `TK0`
  → `TK1` (00:32:09 → 00:54:58, 1,369.35 s, 136,828 ticks), a miss by the loss below; `P2`
  100.002276 (171.48 s, ±0.030) and `P3` 99.967306 (24.80 s, ±0.21), each inside its ±0.1
  (`P3`'s is the second source's exact-decimal value; the primary rounded the instants first
  and read 99.967304). After the loss `P1` runs **100.002869** per RAW second (the 25
  stat-first reads `P1-TR1-S1` … `P1-TK1`, se 0.000102): 29 ppm above 100, outside the
  card's band with nothing lost. `P2` and `P3` are consistent with it and cannot resolve
  it (±0.030 and ±0.21 ticks per second against 0.0029). RAW running that much slow of
  true time in this WSL boot, the board's crystal running that much fast of seating A's,
  and seating A's own figure being off would each produce it — seating A's 100.0031 per
  Windows second, with Windows' −36.42 ppm removed, is 99.9995 per NTP second, about 15 ppm
  from the 99.998 it published, and the two are not reconciled (arithmetic; `CLK-35`). The
  seating logged no reference that separates them. The card's ±0.001 for `P1` assumed ~35
  minutes; `TK0` → `TK1` was 22.8, where two ticks of quantisation are ±0.0015.
* **The loss.** Seating A's recipe — `P1-N0`'s `j_now` placed at its arrival less 1,489 B at
  3,840 B/s, the end at the stat-first `P1-TR1-S1`, the post-loss rate — gives **105.2
  ticks** lost between `P1-N0` and `P1-TR1-S0`, where seating A lost 105. By placement the
  same loss reads 104.2–109.4, the top on first-output instants, against seating A's ~108.4
  on those (seating A's `N0` dump ran at 3,527 B/s, not 3,840, so its recipe placed `N0`
  34.5 ms late); measured from `P1-TK0` it is 110.5, which adds `TK0` → `N0`'s 1.1
  (量 `s111/clocks-v/findings.tsv`). Nothing else lost a tick: `P1-TK0` → `P1-N0` 1.1
  across the map, `MB0`, `HPX`, `FREE` and `PS`; each map's `map_jiffies`, 1300/1301/1301
  over its ~13.00 s silence; and from `P1-TR1-S0` to `P1-TK1` every `rlx0` and `eth4` trial
  0, every `-S1` residual within ±0.18 tick. TC0 lost 45.3–45.6 ticks over the same span.
* **Where, 推.** Between `P1-N0` and `P1-TR1-S0` ran `P1-AC0` (`cat
  /proc/rtl865x/asicCounter`), the fifteen offset cells, `P1-ICMP` and `P1-NMAP`. Block 45
  holds a second population (量 `s111/throughput/b45jiffies.out`): each of its seven `D1-N`
  → `D1-N` driver-dump intervals holds exactly one `asicCounter` read and loses 111.7–114.3
  jiffies whatever its length, 15.2–134.3 RAW s; its `/proc/net/snmp` read is in every
  interval too, and seating B's window has none. The one interval between two driver dumps
  that holds no `asicCounter` read, `D1-TN` → `D1-TN2` (17.4 RAW s), lost 0.0 (量
  `s111/throughput-v/tick45.out`). 推 the cell is the `asicCounter` read: in the SDK drop
  its handler prints about 4 kB through `panic_printk` to the 38,400-baud console (讀
  `rtl865x_proc_debug.c`, not confirmed to be the file `p2q` compiled), ~1.07 s of line
  time, ~107 ticks. How that costs jiffies is open: interrupts held off for the
  whole print would have stopped TC0 too, and TC0 lost ~45 where TC1 lost ~110 on
  first-output instants (推 about 0.45 s with both timers held and ~65 TC1 deliveries lost
  besides; `docs/interrupt-map.md` § 3.6's read-modify-write is a candidate, untested). The
  board-timed waits inside the span show no stretch: by `clocks-v/`'s measure, from the
  echo's last byte to the first output byte and from the header line's last byte to the
  next line's first, `P1-AC0`'s `sleep 1` with its exec read 1.0190 s, the fifteen
  `P1-OFF` cells' 1.0217–1.0345 s and their `-w 2` waits 1.9991–2.0011 s (the primary,
  bracketing from `sent_s` and from the header line's first byte, reads 1.032–1.045 s and
  2.017–2.019 s; the two brackets differ by the echo and the header line on the wire).
  That puts the loss outside them only if those timers run on jiffies, which nothing here
  read (`CLK-42`'s 殘留). Card § 3.8's promise that each trial's `-S0`/`-S1` would place a
  shortfall could not be kept: the loss came before the first trial, and no `/proc/stat`
  read sits between `P1-N0` and `P1-TR1-S0`.
  What decides it: a lone `cat /proc/rtl865x/asicCounter` between two `/proc/stat` reads
  (predicted ≈107 ticks lost), with a `seq_file` read of the same size as the control
  (predicted 0). 🔄 Withdrawn 2026-09-26: the attribution closed without it (next bullet).
* 🔄 **2026-09-26 (block 46, `R6b-1`): the attribution closes on two sources; the mechanism
  stays open.** 讀 the card: each of block 46's 77 board reads is one `cat` of
  `/proc/rtl819x-nic`, `/proc/net/snmp`, `/proc/net/arp`, `/proc/rtl865x/asicCounter` and
  `/proc/rtl819x-nic`, so the jiffies lost between the two dumps' `j_now` are what lies
  between them. 量 on the host's RAW clock, which is independent of the board's ticks
  (re-derived from `bench/2026-09-25c/*-R` by `s112/record/work/rdC.py`, with a planted
  control): jiffies advance 5–8 across each read's window, from dump 1's first byte through
  the `CpuEvent` line, which lasts 1.1955–1.2086 s; so **each read loses 112.55–115.72
  jiffies** (n 77, mean 114.00, sd 0.70) against 100 per RAW second. The window holds
  4,156–4,199 B, 1.082–1.093 s of line time at 3,840 B/s, and runs 0.113–0.116 s past its
  bytes. The 76 cycles from one read's first byte to the next last 8.28–23.97 s (the spans
  between reads 7.08–22.76 s, with pings, driver verbs and console output in them), and each
  loses −0.11…+0.80 tick beyond its read's window (mean 0.33, sd 0.17): nothing outside the
  window costs a tick.
  量 Inside the window the first `asicCounter` printk line arrives 3.0–5.2 ms after dump 1's
  first byte, with 14–15 bytes of dump 1 before it in all 77 reads. 讀 `cat` reads its files
  in order, so the snmp and arp handlers ran and returned inside those ≤ 5.2 ms (about half a
  tick at most); with the between-read remainder ruling out a delay after the print, at least
  ~112 of each read's lost ticks accrue while `asicCounter` prints its 86 lines.
  讀 The path, in the tree that builds (`tools/rlxfw-kbuild.sh:58` stages
  `src-vendor/rtl819x-toolchain`): `rtl865x_proc_mibCounter_read`
  (`drivers/net/rtl819x/rtl865x_proc_debug.c:4406`) returns 0 bytes after calling
  `rtl865xC_dumpAsicDiagCounter` (`AsicDriver/rtl865x_asicCom.c:1776`), which prints every
  line through `rtlglue_printf`, defined as `panic_printk` (`include/net/rtl/rtl_types.h:366`);
  `panic_printk` (`kernel/printk_log.c:668`, built under `CONFIG_RTL_819X`, `kernel/Makefile`
  lines 5–6) calls `vprintk`, which saves and disables interrupts at `:750`, writes the console
  through `release_console_sem()` at `:844` and restores them at `:848`. 量 The `p2q` kroot
  `.config` has `CONFIG_PANIC_PRINTK=y`, and its `vmlinux` (`c5e2cfdba7730d47`) holds the
  strings `rtl865x_proc_mibCounter_read`, `rtl865xC_dumpAsicDiagCounter` and `prt_start`, a
  name `printk_log.c` has and `printk.c` does not (a string that must be absent counts 0).
  推 That shows those functions compiled in, not that the compiled text equals the drop's.
  So "the cell is the `asicCounter` read" is 量 + 讀 now, and the ≈107-tick estimate from line
  time was 7 short: the window exceeds its bytes' line time by about 1.3 ms per line.
  ⚠️ **The number belongs to its context**, a read sharing one `cat` with dump 1's pending tty
  output: seating B's lone read lost ~105 (104.2–109.4 by placement), block 45's reads
  111.7–114.3 and block 46's 112.55–115.72. An effect that moves between seatings is not a
  hardware constant.
  **The IRQ reading exists twice already** (量): across seating B's loss IRQ 13 − IRQ 25 went
  35 → 100, +65 for one read (above); in block 45, `D1-ETH4` (`/proc/interrupts`) →
  `D1-E-S0` (`/proc/stat`), an interval holding one lone `asicCounter` read and one
  `/proc/net/snmp` read, moved it +71 — the difference, which no anchor moves; the absolutes do (TC0 46.2 and TC1 117.2 short over 14.622 RAW s anchored on the `CPU0` header and the `intr` line, 41.8 and 112.8 over 14.578 s anchored on the ` 13:` line),
  `D1-T-S1` → `D1-DOWN`, holding four such reads, +286 (71.5 per read), and the intervals with
  none moved 0 (`D1-T-S0` → `D1-T-S1`, `D1-E-S0` → `D1-E-S1`) and −1 (`D1-DOWN` → `D1-ETH4`)
  (`s112/record/work/`, from `bench/2026-09-25b/`). So the lone-read pair once asked of
  `R6b-3` would repeat a known result, and it is withdrawn (`PROGRESS.md`, `R6b-3`'s row).
  **What stays open is the mechanism** (推): why TC1 (IRQ 25, the jiffies) loses about 115
  ticks per read while TC0 (IRQ 13) loses about 45. Candidates: `docs/interrupt-map.md`
  § 8.4's two — timeouts collapsing inside an interrupt-disabled region, and § 3.6's
  read-modify-write of `TCIR` erasing a latched TC1 pending bit — and a third, that TC0 on the
  LOPI and TC1 on the ICTL latch differently. The discriminating experiment is an image whose
  TC0 acknowledge writes only `TC0IP`: § 3.6 predicts TC1's per-read loss falling to about
  TC0's. It is not on the TX path and so not `R6b`'s; it is re-owned to `docs/interrupt-map.md`
  § 8.4, beside `IRQ-13`'s own open mechanism, and no open gate carries it.
  量 Side cost: the 77 reads cost the press about 8,778 ticks (~88 s) of board time; card
  § 0 ⑥ claims no duration, so no verdict moves.

### 8.4 `D2` holds on RAW (`CLK-45`)

Card § 3.1's groups, computed on the bench night by `Z9-D2X` before any comparison was read,
and reproduced at the desk to 4 dp (量 `s111/timing/checks.out` § 8). Quantity:
`loader.banner`, s; seating A's values are the frozen list's.

| group | captures | n | seating B | seating A raw | seating A corrected |
|---|---|---:|---:|---:|---:|
| rlxfw cold | `P1-A`, `P2-A`, `P3-A` | 3 | 0.585971 | 0.572666 | 0.586303 |
| vendor cold | `V1-A`…`V3-A` | 3 | 0.586138 | 0.573108 | 0.586157 |
| rlxfw warm | `P1L-r02/r03-rz`, `P1-RZ`, `P1Q-r02/r03/r04-rz`, `P2Q-r02-rz`, `P3Q-r02-rz` | 8 | 0.596812 | 0.587768 | 0.596032 |
| vendor warm | `V4-WZ`…`V7-WZ` | 4 | 0.595988 | 0.579959 | 0.595841 |
| loader-only cold (context) | `V4-A`…`V7-A`, `M2-A` | 5 | 0.585957 | 0.572033 | 0.586096 |
| mode control, cold (listen) | `M1-BOOT` | 1 | 0.581514 | 0.572643 | 0.585572 |
| mode control, warm (listen) | `M2-BOOT` | 1 | 0.597166 | 0.580757 | 0.596113 |

Warm rlxfw − vendor **+0.8245 ms** (band ±10 ms; seating A raw +7.8, corrected +0.19); cold
**−0.167 ms** (±25 ms; seating A raw −0.4, corrected +0.15); `M1-BOOT` − rlxfw cold
−4.457 ms and − vendor cold −4.624 ms, `M2-BOOT` − rlxfw warm +0.3535 ms and − vendor warm
+1.178 ms (±10 ms each). **`D2` holds**, on RAW with nothing corrected.

* **The correction's prediction, met.** The press split seating A's raw values showed is
  absent: `P1`'s six warm catches read 0.595915–0.597136 s, `P2Q-r02-rz` 0.596842 and
  `P3Q-r02-rz` 0.595782. The 13 warm catches' `loader.booting` span 1.363 ms, 0.383 % of
  their median, where seating A's spanned 3.08 % raw and 0.545 % corrected by the same
  measure (range over median). Three of the six differences land within 0.64 ms of seating
  A's corrected ones, and a fourth, `M2` − vendor, within 0.91 ms (量 `s111/timing/checks.out`
  § 8: warm +0.633, cold −0.313, `M2` − rlxfw +0.273, `M2` − vendor +0.906 ms).
* **`M1`'s two land 3.7–4.0 ms away, and 推 not through listen mode.** `M1-BOOT`'s
  `loader.booting` is 4.371 ms under the eleven `esc` cold catches' median while its `banner`
  − `booting` is −0.12 ms: the read that carried its anchor-C byte returned 5.39 ms after
  the read before it, against 0.54–1.10 ms in the other 24 loader boots and 0.94 ms in
  seating A's `M1-BOOT`. Measured from anchor A (the last `.`) instead, `M1` − rlxfw cold is
  −0.05 ms and `M1` − vendor cold −0.19 ms (量 `s111/timing-v/vanchor.out`). 推 one late
  read; `M2-BOOT`, listening too, shows none. Card § 3.1 said the raw differences would
  "land near" the corrected seating-A values and gave no tolerance, so that sentence could
  not fail; the bands could.

### 8.5 Segment timing, inference (iii), and how late a stamp can be (`CLK-43`, `CLK-44`)

`bench/2026-09-25/Z9-D2.tsv`, written on the bench night, is byte-identical to the desk's
`boot-timeline --retro` over the directory (sha256 `8b40db9a862b04f6…`, tool
`a541392a0ffe7216…`). A second reader sharing no code (`s111/timing-v/`: its own landmarks,
FW-35 lookup in exact decimals, C-8 class by `t0_raw` order) agrees on 52 of 52 loader
values, 208 of 208 segment values, 223 of 223 landmarks, 12 of 12 resets and 20 of 20
kernel-boot classes, and refuses a planted +1 µs and a planted class. The classes are
seating A's composition: `P1L-r01`, `P2Q-r01`, `P3Q-r01`, `V1`–`V3` and `M1` cold, the rest
warm. Every cell with n, median and range, cold and warm, beside seating A's raw and
corrected values, is `docs/boot-time-table.md`'s; the groups the tests below read:

| group | n | median (s) | range (s) |
|---|---:|---:|---|
| `loader.booting`, cold | 12 | 0.355865 | 0.351504 (`M1-BOOT`) … 0.356368 |
| `loader.booting`, warm | 13 | 0.356060 | 0.355618 … 0.356981 |
| rlxfw quiet, `J` → prompt | 8 | 10.792753 | 10.790948 … 10.795582 |
| rlxfw loud, `J` → prompt | 3 | 12.535714 | 12.534490 … 12.536925 |
| rlxfw quiet warm, `kernel.total` | 6 | 9.445702 | 9.445069 … 9.446463 |
| vendor, `kernel.total` | 9 | 7.098017 | 7.097306 … 7.109743 |
| vendor, `J` → `boa` | 9 | 26.836990 | 25.851886 (`V7`) … 27.035197 |

* **Inference (iii) holds** (`CLK-43`). Registered before power (card § 3.9): seating B's
  warm `loader.booting` median (n = 13) and its cold median (n = 12) lie in [0.354469,
  0.358031] s, 0.35625 × (1 ± 0.005). 量 warm **0.356060**, cold **0.355865** (0.355875
  without the listen boot). Seating A's raw warm median, 0.347425 s, lies 2.0 % under the
  band's floor, and its value corrected for the host clock, 0.355963 s, 0.027 % under
  seating B's: the device's own factor between the days is g = 0.356060 / 0.355963 =
  1.000273 (card band [0.99580, 1.00581]), so the 2.5 % seating A carried was its host
  clock, and `CLK-32`'s per-seating factor, 推 in § 5, is the host clock's for these two
  seatings. f_B = 0.356060 / 0.353718 = 1.006621 (card band [1.002122, 1.012194]). Not
  shown: that every earlier directory's factor was the host clock's too — § 5's retro fit
  still says so only as 推.
* **Card § 3.7's reproduction bands: 67 of 68 medians inside.** The one outside is
  `rlxfw.setup`, loud, cold (n = 1, `P1L-r01-boot`): 0.293701 s against [0.2757, 0.2827].
  The read that carried `RLXFW-B09` (byte 1116) returned 15.86 ms after its predecessor, and
  it and the next two reads delivered bytes 1115–1180 — 66 B, 17.2 ms of line time — within
  3.18 ms; `kernel.early`, which spans `B00` and `B09`, reads 1.523894 s against the warm
  boots' 1.524926. The boot ran on schedule and the stamp came late (量 the gap and the
  backlog; which of the host's scheduler, usbip and the CP2102 held the bytes is 推).
  Bounded at both ends by the line rate the interval lies in [0.278069, 0.291798] s, inside
  the band only if `B00` arrived after 1.289105 s — likely, not shown. The smallest margins
  among the 67: `rlxfw.initpost` loud cold 1.5 ms, `rlxfw.setup` quiet cold 1.8 ms.
* **Card A's model at the measured f_B** (T = f·(k·0.353718 + Δ)), 4 of 4 inside the card's
  bands: `p2q` `J` → prompt 10.792753 against its point 10.793163; `p2q` `kernel.total`
  9.445702 against 9.447251; `p2q` `user.ready` 0.116154, 3.35 ms above 0.112806, the point
  at card A's registered mid Δ of 67.0 ms; `p2l` `J` → prompt 12.535714 against 12.564847,
  −0.23 % (推 the model's loud constant is ~29 ms high: seating A's corrected 12.5336–12.5490
  s sat under its point as well).
* **The vendor's rules** (own line landmarks, FW-35). Eight boots took the slow `WiFi Simple
  Config` → `Register to wlan0` step (1.151434–1.163527 s) and reached `boa` at `J` +
  26.823020…27.035197 s, 8 of 8 inside [26.553, 27.074]; `V7` took the fast one, 0.149520 s,
  and reached `boa` at 25.851886 s, 1.0078 s under the slow median — the step's own shortfall,
  1.006803 s, accounts for it to 1.0 ms. Seating A's fast boot was `V4` (0.146649 s), and
  seating B's `V4` took 1.156723 s: 推 a userspace race tied to neither press nor class, two
  in eighteen boots. `Init bridge interface...` − `sysconf wlanapp kill wlan0` 0.854441–0.860235
  s (9 of 9 inside 0.848–0.883); `J BFC00000` → `<RealTek>` 2.300066–2.305369 s (median
  2.304802, n = 4); `M1`/`M2` `loader.esc` 5.238773 / 5.237828 s.
* **A console stamp can be 13.5 ms late** (`CLK-44`). Card § 3.7 allowed one FW-35 read
  quantum, ~1 ms, at each end of an interval, and that is not a bound. Stamps provably late
  by the line-rate bound (the board sends at most 3,840 B/s, 讀 38,400 8N1): 13.5 ms on
  `P1L-r01`'s `B09`, 11.3 ms on `V4-BOOT`'s `userinit`, 8.4 ms on `P2Q-r02`'s `nic`, and
  0.9–6.8 ms on the `---Jump` byte in all 23 typed-`J` captures (量
  `s111/timing-v/vlate.out`). Reads that stall past 10 ms and then deliver a backlog occur in
  both seatings (seating A's `P1-EV2-S1` 25.7 ms, `P1-TS3-S1` 20.8 ms). The closing rule's
  "under 20 ms" criterion rests on the same ~1 ms premise.
* **`sent_s` is not the send** (`CLK-44`). The loader prints `---Jump to address=` only after
  it has the line's CR, and that byte reached the host 0.8–6.6 ms before `sent_s` in 23 of
  23 typed-`J` captures here, and 1.0–6.3 ms before it in 23 of 23 in seating A (量, at
  ≤ 3,840 B/s; `s111/timing-v/vlate.out`, `seatA/vlate-A.out`). `sent_s` is where `flush()`
  returned — later than the line left, on this port — and the first read after it carries
  a backlog of 14–39 B. So `J`'s stamp is at least 0.9–6.8 ms late (1.1–6.4 ms in seating
  A), and a `J`-anchored interval reads short by that less its far end's own lateness, in
  both seatings alike: `D3`, which compares them, does not move. `SEG+`, the first read's
  arrival minus `sent_s`, reads 60–122 µs in 18 of 19 boots and 375 µs in `P3Q-r02-boot`
  (median 85 µs; seating A 61–140 µs): it measures `flush()`'s return to the next read.
  The control that could have failed: re-stamping `J` at its line-rate bound pulls
  identical boots together — quiet `rtkload.total`'s spread 4.26 → 0.71 ms (n = 8), the
  vendor's 5.06 → 1.19 ms (n = 7), loud 2.38 → 0.63 ms (n = 3). This answers § 3.1's
  殘留; § 7.6 read it the other way (🔄 there).

### 8.6 `D7` holds (`CLK-46`)

量 `s111/timing/checks.out` § 11, second source `timing-v/`. Press 1's `kernel.total`: loud
`P1L-r01`…`r03` 11.155614, 11.156569, 11.156054 s (median 11.156054); quiet
`P1Q-r01`…`r04` 9.445737, 9.445107, 9.445667, 9.445802 s (median 9.445702). **Δ = 1.710352
s**, inside the test band at the measured f_B, [1.398905, 1.979101] s — **holds**; inside card
A's no-residual range at f_B, [1.648905, 1.729101] (18.7 ms under its top), and inside the
card's 1.705…1.722 s (1.712433 × g = 1.712900). Every loud boot is 7,948 B with twelve
`tmpReg[0xe]` fields (e = 0), every quiet boot 2,117 B, and in 12 of 12 pairs ΔB = 5,831 B
= 810 (`B00` → `B09`) + 5,021 (`B09` → `B10`); the 5,021 splits 1,575 + 2,088 + 1,300 + 58
over `B09` → `wlan` → `nic` → `fastpath` → `B10`, and every other landmark pair differs by 0.
The implied rate f_B·ΔB/Δ is 3,431.8 B/s, **89.370 %** of 3,840 (88.782 % at f = 1): inside
`FW-70`'s 88.4–92.7 % at either f, where seating A's raw 88.325 % fell under it (§ 7.6).
Against seating A's raw Δ, 1.688630 s, (a) +1.29 %; against its corrected Δ, 1.712433 s,
(b) −0.12 %. Not established:
which f belongs in the rate; `FW-70`'s range was itself measured on host clocks of unknown
rate.

### 8.7 `D8` (`CLK-47`)

Card § 3.4's rules over `hostprobe` 1.3's RAW ledger (量 `s111/netup/`; its second source
`netup-v/`, with its own parsers, equals it to 1 µs on 71 of 72 shared ids, and the one
difference — one `b3-fail` value the primary read 1.58 ms late, because two error lines
arrived in two reads — is settled in the second source's favour). `J` is the loader's jump landmark and
every figure is seconds after it on RAW. Frames: `P1-TCPD` and `P3-TCPD` (1,859 and 1,192
frames, 0 dropped), placed on RAW by `tools/hostclock.py convert` against `Z0-HC` (0 of
3,051 stamps refused); no reply was read before its frame (753 in `P1`, 474 in `P3`).

* **Channel offset: the test fires again.** 15 `udp` events on port 50000, each `len=10`, one
  per `P1-OFF` cell; offset = t_udp − t_console (byte 66). Over `OFF02`–`OFF15` (n = 14):
  read stamps −277.4…+215.2 µs, range **492.6 µs**; kernel stamps (`t_raw − lag_ms/1000`)
  −545.4…−94.6 µs, range **450.8 µs**; both over 260.4 µs, as the card predicted (seating A
  701.0 / 896.4 µs). The kernel stamp precedes the console's read of byte 66 in all 14.
  Network up stays a console-side bound.

| round | class | NIC → `N-NDOPEN` | `J` → `N-NDOPEN` | first reply | k | width, card rule (mid) | width, frames |
|---|---|---:|---:|---:|---|---:|---:|
| `P1L-r01` | loud, cold | 4.511256 | 12.503737 | 13.230903 | 3 (frames) | 0.713143 | 0.7150 |
| `P1L-r02` | loud, warm | 4.511009 | 12.504668 | 13.281312 | 3 (frames) | 0.738561 | 0.7662 |
| `P1L-r03` | loud, warm | 4.510966 | 12.505901 | 13.262704 | 3 (frames) | 0.719894 | 0.7449 |
| `P1Q-r01` | quiet, warm | 4.111323 | 10.761850 | 10.876994 | 2 (frames) | 0.117001 | 0.1050 |
| `P1Q-r02` | quiet, warm | 4.111984 | 10.760967 | 10.845176 | 2 (frames) | 0.082275 | 0.0778 |
| `P1Q-r03` | quiet, warm | 4.111742 | 10.763234 | 10.897048 | 2 (frames) | 0.134960 | 0.1276 |
| `P1Q-r04` | quiet, warm | 4.112900 | 10.763097 | 10.840007 | 2 (frames) | 0.081153 | 0.0715 |
| `P2Q-r01` | quiet, cold | 4.111776 | 10.764227 | 10.884312 | 2 (ledger) | 0.094550 | — |
| `P2Q-r02` | quiet, warm | 4.102999 | 10.762463 | 10.904706 | 2 (ledger) | 0.130450 | — |
| `P3Q-r01` | quiet, cold | 4.111394 | 10.760109 | 10.869487 | 2 (frames) | 0.114647 | 0.1031 |
| `P3Q-r02` | quiet, warm | 4.111886 | 10.761901 | 10.910604 | 2 (frames) | 0.129736 | 0.1449 |

* **rlxfw: both images answered in every round**, 11 of 11 before the next reset (1.967–2.702
  s ahead of it where one followed: the 2.5 s dwell, `FW-127`, was enough); `--neigh` read
  `INCOMPLETE` at all 11 jumps, and every lower edge is `N-NDOPEN`. Quiet: the `is-at` follows
  the cycle's second who-has in 6 of 6 framed boots, and `N-NDOPEN` leads that #2 by
  0.0715–0.1449 s. **Loud, the first reading**: the `is-at` follows the cycle's **third**
  who-has, 2.8–3.6 ms after it, in 3 of 3; #2 came 0.258–0.309 s before `N-NDOPEN` and went
  unanswered — the k = 3 the 107th segment inferred from seating A's timing (§ 7.3). First
  reply `J` + 13.230903…13.281312 s; bracket [`N-NDOPEN`, #3], 0.715–0.766 s wide by frames.
* **What the board decides reproduces seating A's corrected values**: on `J` → NIC, `J` →
  `N-NDOPEN`, NIC → `N-NDOPEN` and `J` → `lan up`, `D3` (b) −0.16…+0.02 % and (a)
  +1.25…+2.48 %, the host clock seating A carried. NIC → `N-NDOPEN` is 4.102999–4.112900 s
  quiet (n = 8, median 4.111759) and 4.510966–4.511256 s loud (n = 3, median 4.511009): the
  medians lie within 0.6 ms of seating A's corrected ones, 4.111872 and 4.511570, and
  `P2Q-r02`'s 4.102999 lies 8.9 ms under the quiet one. § 7.3's NIC+4.01–4.05 / 4.45 s
  were slow-clock values (🔄 there). The lead of `N-NDOPEN` over the quiet image's #2 is
  the host's ARP phase against the board and moved between the days: 0.0715–0.1449 s here
  by frames, 0.13–0.22 s in seating A's ledger on its own clock (量
  `s111/netup/netup-A.out`; 推 the slow clock stretching the host's ARP schedule,
  untested). The host's first who-has after the NIC probe is the next cycle's #1, at
  NIC+3.180–3.233 s (9 of 9), and its #2 at NIC+4.184–4.257 s.
* **The vendor answered on a cycle's first broadcast in 9 of 9** (seating A: the third in
  five, the first in four), by the ledger's reconstruction: no capture ran on a vendor
  press. First reply `J` + 15.725381…15.781849 s, a 56 ms spread where seating A's was
  1.16 s. Each answered who-has opened the cycle after a failed one and was
  answered in 2–5 ms; the failed cycle's #3, reconstructed at `J` + 14.628…14.746, went
  unanswered in all nine. The phase is set by the carrier loss at the vendor's NIC probe (one
  purged cycle per boot, then failed cycles from `J` + 6.45–6.52). 推 seating A's five/four
  split is its slow host clock stretching the ~9 s of host ARP timers after the NIC probe by
  ~0.2 s of true time; not tested. `Start NTP daemon` reached the host at `J` +
  14.852597…14.926873 s, (b) −1.07…+0.10 % against seating A.
* **Inference (i): not refuted, 9 of 9.** The window `Start NTP daemon` − 0.116…−0.075 s lies
  inside every bracket [the failed cycle's #3, the answered #1], each 1.03–1.10 s wide; the
  window's upper end falls 0.055–0.146 s after the latest possible lower edge. A weak test:
  refuting it needed the vendor to answer a #3 at least 55 ms later than the reconstruction
  allows.
* **Where the card's reconstruction was too narrow** (量 the frames). #1 → #2 on the wire ran
  1.001240–1.033472 s (n = 47), 8 of them above the rule's 1.028; #2 → #3 1.019934–1.027979
  s (n = 36); #3 − T1 reached 2.0575 s against the rule's 2.056. `P3Q-r02`'s answered #2
  lies 1.2 ms past its reconstructed upper edge; no verdict moved. The card's fixed 5.0 ms
  from the answered broadcast to the reply's read is not a constant: 3.780–10.128 ms quiet,
  10.490–12.149 ms loud (推 the loud image's console load). An `icmp-reply` line carries no
  `lag_ms`, so the card's second stamp for a reply does not exist; `ping -D` stamps the
  printing of the line, 0.056–0.215 ms after the echo-reply frame.
* **Broadcasts missing from the wire.** Of those the ledger implies, 107 of 158 reached the
  wire in `P1` and 31 of 42 in `P3` (seating A's `P3`: 31 of 42 too); the missing ones are
  exactly the cycle opened ~0.1 s after each NIC probe and the five after each reset (推
  carrier loss; no carrier log was kept).
* **The host clock under these windows** (§ 8.2): named affected by card § 3.8, at no more
  than +46 ppm — ≤ 0.05 ms on a 1 s retransmit and ≤ 0.2 ms on NIC → #2, under the
  reconstruction's ±14–28 ms. `tools/boot-timeline.py --probe` reads no network up for 7 of
  the 11 rlxfw rounds: it counts only events inside the capture's window, and the first reply
  comes in the dwell after the prompt (`FW-137`); where it reads, it equals this join to the
  microsecond.

### 8.8 `D4`, `D6` and inference (ii) (`NET-118`, `MEM-20`)

The vendor's readiness (量 `s111/services/`, second source `services-v/`); `hostprobe` 1.3
tried 80, 52869 and 52881 every 0.2 s each; seconds after `J`, on RAW:

| boot | class | first ICMP reply | first `tcp:80` ok | `boa: starting server` | ok − line | first `tcp:52881` ok | first `tcp:52869` ok | `MiniIGD` line |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `V1` | cold | 15.741339 | 27.020731 | 26.971659 | +0.049072 | 17.421601 | 32.421049 | 23.194764 |
| `V2` | cold | 15.747473 | 26.872633 | 26.882316 | −0.009683 | 17.273567 | 32.273124 | 23.091256 |
| `V3` | cold | 15.771203 | 26.875883 | 26.828089 | +0.047794 | 17.272929 | 32.272360 | 23.044914 |
| `V4` | warm | 15.781849 | 26.818717 | 26.823020 | −0.004303 | 17.219634 | 32.219094 | 23.045880 |
| `V5` | warm | 15.747125 | 27.095343 | 27.035197 | +0.060146 | 17.296168 | 32.495463 | 23.250394 |
| `V6` | warm | 15.749031 | 26.868374 | 26.958244 | −0.089870 | 17.268969 | 32.268255 | 23.173328 |
| `V7` | warm | 15.725381 | 25.873200 | 25.851886 | +0.021314 | 17.274216 | 31.273790 | 22.066864 |
| `M1` | listen, cold | 15.771420 | 26.878518 | 26.834309 | +0.044209 | 17.079865 | 32.278574 | 23.040289 |
| `M2` | listen, warm | 15.740246 | 26.834073 | 26.836990 | −0.002917 | 17.236483 | 32.235122 | 23.046628 |

* **Card § 3.6.** The first port-80 success within ±0.14 s of `boa: starting server` in 9 of
  9 (−0.089870…+0.060146; after the line in five, before it in four); inside the slow-step
  band `J` + 26.53…27.08 s in 7 of 8, `V5` 15.3 ms past it at 27.095343 (the band is seating
  A's eight-boot extreme × g, not a bound on the next boot); the fast boot `V7` inside `J` +
  25.72…26.01; the first ICMP reply ahead of it by 10.4–12.2 s in 8 of 9, `V7` at 10.147819 s,
  where the fast step met the late ARP phase every seating-B boot had — a pair seating A did
  not sample. `D3` on the load-bearing rows: `D4|p80|cold` 26.875883 s, (a) +2.31 %, (b)
  +0.07 %; `D4|p80|warm` 26.843546 s (the exact median, 26.8435455; the primary's float read
  26.843545), (a) +2.65 %, (b) +0.10 %.
* **Inference (ii): not refuted, and now the only fit.** Per boot the window is (last refused
  connect start, first ok start + 1 ms] less the FW-35 time of `boa: server version`'s first
  byte — s106's rule, whose + 1 ms § 7.5 and § 7.7 do not state (without it seating A's
  nine intersect in (−0.127283, −0.112008]; no verdict moves). 0 of 9 windows exclude
  (−0.1273, −0.1110]; seating B's nine intersect in (−0.117471, −0.067905], and the eighteen
  of both seatings in **(−0.117471, −0.111008]**, 6.5 ms: `boa` listens 0.111–0.117 s before
  that line reaches the host, if one offset holds for all eighteen. Of the 41 console lines
  present exactly once in all 18 vendor captures, eleven give port 80 a single-offset fit on
  seating B alone (among them `Register to wlan0` and `MiniIGD`), and across both days only
  the three `boa` lines do: `server version` (−0.117471, −0.111008], `server built`
  (−0.128385, −0.121603], `starting server` (−0.141224, −0.134056] (量
  `s111/services-v/linescan.out`). Timing, not a mechanism: that `boa` listens before it
  prints stays 推.
* **52881, 推 not `miniigd`'s** (`NET-118`). Its first success comes at `J` +
  17.079865…17.421601 s (median 17.272929), 4.79–5.96 s *before* the `MiniIGD v1.09.1` line
  in 9 of 9, and its listen windows fit one offset from the `WiFi Simple Config
  v2.18-wps1.0` line, (−0.018571, +0.011910] s (+0.012910] with the + 1 ms), and none from
  `Register to wlan0`, `MiniIGD` or the `boa` lines. 讀 the SDK tree:
  `src-vendor/rtl819x-toolchain/linux-2.6.30/net/bridge/br_input.c` has `#define
  RTK_WPS_LISTEN_PORT 52881`; the vendor's rootfs starts `/bin/wscd` through `sysconf
  wlanapp` (讀 `s111/feature-table/FEATURES.md`). 推 52881 is the WPS daemon `wscd`'s
  listener: the SDK is a related drop, not TOTOLINK's build, and neither the unit's `wscd`
  nor a boot with `wscd` stopped has been read. § 7.5 gave it to `miniigd` (🔄 there).
* **52869, 推 `miniigd`'s.** First success at `J` + 31.273790…32.495463 s (median 32.272360),
  9.09–9.25 s after the `MiniIGD` line. Its windows fit one offset from each of three lines —
  `Register to wlan0` (13.870540, 13.898714], `MiniIGD` (9.043636, 9.093208], `boa: server
  version` (5.282586, 5.332085] — so timing cannot choose; `V7`'s fast step moves all three.
  讀 the same tree: `linux-2.6.30/net/ipv4/ip_input.c`, `if (hdr->dest == 52869) // IGD
  port`, and `users/script/picsdesc.xml`'s `URLBase` on port 52869.
* **The census** (量). `V1-NMAP`: open 80, 52869, 52881 (as predicted), 65,532 closed, 0
  filtered (seating A 65,381 and 151). `P1-NMAP`: none open (as predicted), 57,296 closed,
  8,239 filtered (seating A 58,989 and 6,546); what the filtered ports are is `notes/nic-driver.md`
  § 21's (`NET-120`). `P1-PS`: `/bin/sh`, the kernel threads and `ps`, as in seating A; `ps`
  is PID 20 against seating A's 18 (推 the two `cat`s of `P1-TK0`, a cell seating A did not
  have).
* **`D6`** (`MEM-20`; 量 `P1-FREE`, `p2q`). `MemTotal` 26,984 kB (the exact prediction);
  `MemFree` 20,924 kB (seating A 20,932, −0.04 %); `busybox free` total/used/free 26,984 /
  6,028 / 20,956 kB (seating A used 6,012). `busybox free` runs first in the same send, and
  its `free` column reads 32 kB above `/proc/meminfo`'s `MemFree` (seating A 40 kB). One
  reading after one boot sequence, not a steady state.

### 8.9 `D3`: `P2`'s table is reproduced (`CLK-48`)

The contract is `docs/boot-time-d3-list.tsv`, committed at `76deef8` before any seating-B
value of a listed number was read: 294 rows generated from seating-A files only, with the
rulings R1–R6 in its `adjudication` column. The closing rule is `PROGRESS.md`'s (`P2`,
*Refutation conditions*), committed at `e2f15ff` before any seating-B interval was computed.
Per number: (a) seating B against seating A raw, (b) against seating A corrected, a hit when
both lie within ±10 %; (c), each over its seating's warm `loader.booting` median, is
published and decides nothing. Two scorers wrote their verdicts from the same B values
independently (`s111/score-S1/`, `score-S2/`) and a third, in exact fractions
(`score-judge/final.py`), agrees with both on every row; the B values' own second sources
are the `-v` directories above. The judge's controls: a planted miss on a load-bearing row
turns the verdict to "stays open", and +10 % exactly scores a hit where 1e-9 past it scores a
miss. The score is `docs/boot-time-d3-score.tsv`, and the table `P2` exists to publish is
`docs/boot-time-table.md`.

| verdict | rows |
|---|---:|
| stable, hit | 134 |
| stable, miss | 6 |
| exact, hit | 27 |
| exact, miss | 2 |
| not stable, inside ±10 % | 43 |
| not stable, outside ±10 % | 43 |
| not stable, no ratio | 19 |
| not stable, no seating-B value | 5 |
| first reading (no seating-A value) | 15 |

* **No stable miss on a load-bearing row.** Nothing falls on a row of the segmented table
  or on `D7`'s Δ, so rule (2) keeps nothing open. The 114 stable board rows hit with (a)
  +1.10…+6.71 % and (b) −1.10…+5.23 %; without the one stalled read of § 8.5 (`rlxfw.setup`,
  loud, cold, whose |a| 6.712 % and |b| 5.229 % are the largest on a load-bearing row), (a)
  +1.10…+3.58 % and (b) −1.10…+0.98 %. Column (a) carries seating A's slow host clock by
  construction; column (b) is seating A's correction checked against an unslewed clock.
  `D7`'s Δ: (a) +1.29 %, (b) −0.12 %. The stable hit closest to the edge is
  `D5b|eth4|ER|cpu`, −8.214 %, of which ~3.3 points are the longer `/proc/stat` bracket (every
  seating-B `eth4` window is 3.1–3.4 % longer, and idle).
* **The six stable misses**, published with both columns as not reproduced (rule (3)) and
  carried forward as `D3-MISS`, each with the experiment that decides it:
  * `D8|width|quiet|cold`, (a) −44.30 %, (b) +13.71 %: a defect of the list. Seating A's
    value is one boot, `P2Q-r01`, stable by n = 1, and its raw and corrected values differ
    ×2.04, so the two ±10 % windows, [0.169, 0.207] and [0.083, 0.101] s, are disjoint and
    no seating-B value could hit both; (b) misses on the reconstruction's midpoint (±14 ms
    against a ±9.2 ms band), and `P3Q-r01`'s frame puts its #2 11.5 ms before that midpoint.
    Experiment: a third day on RAW, B compared with C.
  * `D5a|rlxfw|256|avg` +18.05 %, `D5a|rlxfw|1472|avg` +12.16 %, `D5a|rlxfw|1472|mdev`
    +16.60 % (realtime, so (a) = (b)): rlxfw's rtt rose 12–18 % while the vendor's fell 12–26 %
    against seating A. The capture's own stamps agree with `ping`'s to 0.043 ms, so `ping`'s
    userspace is not the cause; split by whether `tcpdump` ran, rlxfw's 256 B and 1,472 B
    averages moved +7.2 % and +9.9 % without it and +13.5 % and +19.7 % with it (n = 1–2 per
    stratum). Experiment: the same ICMP series with and without the host capture inside one
    boot — `R6b`'s, whose regression re-measures ICMP (`NET-121`, `notes/nic-driver.md`
    § 20).
  * `NET109|crcalignerr` and `NET109|p3egress`, 294 → 414 (+40.8 %): a run length, not a
    device quantity. In both seatings the count is the echo replies `P1-HP` drew inside the
    last boot plus two (量: 412 + 2 here, `P1-TCPD` holding 412 echo replies, one ARP reply
    and one ARP request; 292 + 2 in seating A), and the list's n = 1 rule made it stable. The
    property the rows stand for held: `CRCAlignErr` − port-3 egress 0 in both seatings, 414 =
    414. Experiment: none — redefine the row as that per-echo identity.
* **The two exact misses** are `P2-M0`'s 3,009 B and its digest (§ 8.1): the capture tool's
  tail, an instrument miss (`FW-136`), not a device quantity.

### 8.10 What seating B does not establish

* That any number is stable beyond two samples: a hit says the second day landed within
  ±10 % of the first, and `D3`'s verdict is a statement about the frozen list only.
* RAW's rate against true time. The clock log ran `--no-sntp --no-windows`, so the board's
  post-loss 100.002869 ticks per RAW second cannot be split between RAW and the board
  (§ 8.3), and the WSL boot has ended.
* What held the stalled reads (15.86 ms on `P1L-r01`'s `B09`, 5.39 ms on `M1-BOOT`'s anchor):
  the host's scheduler, usbip and the CP2102 were not told apart; nor that `M1`'s late read
  is no property of listen mode (n = 1 in each seating).
* Which cell cost the jiffies, or why TC0 lost fewer: the `asicCounter` read is 推 (§ 8.3),
  and the board-timed waits exclude a loss inside them only if they run on jiffies.
* Where inside its bracket either firmware's network came up. The vendor's brackets rest on a
  reconstruction no frame checks, and the rlxfw frames show it too narrow by up to 5.5 ms for
  #2; the channel offset is measured on rlxfw only.
* That the vendor's k = 1 in 9 of 9 belongs to the vendor rather than to this host's timers.
* Which daemon owns 52881 or 52869 on this unit (timing and a related SDK drop, 推); that any
  daemon serves (`tcp ok` is a completed handshake); anything about the vendor's UDP daemons.
* Which f belongs in `D7`'s implied rate; how often the vendor's fast WSC step happens (two
  in eighteen boots).
* That no flash byte was written: the maps compare 32 digests over 4,186,112 B of 4,194,304,
  cannot see two writes that cancel, and do not read `H601`.
* Windows' own rate during the seating, and that its slew after the wake drove the guest's
  +0.257030 s (推, § 8.2).
