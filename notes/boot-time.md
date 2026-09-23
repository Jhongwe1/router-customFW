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
  `cpu` ticks and IRQ 13 on each rlxfw dump, placed at their lines' FW-35 arrival.

In every five-minute window holding two or more of them they give r within 0.0005 of
each other (three sparse windows 0.0013–0.0017). **r ≈ 1.000 until ~15:49** — `P1-A`
over its own 180 s 0.99972 — **then a slowdown that grew without a break**: 0.9861 at
15:52, 0.9824 at 16:18, 0.9781 at 16:38, 0.9767 at 16:59, 0.9727–0.9744 at
17:29–17:40, 0.9693–0.9700 at 18:00–18:17; and on top of the trend, 3–20 s swings
between 0.953 and 0.994 (`V7-WZ` fell in one: r = 0.9615, by K and W independently).
The lag was already building by 15:49:43, before `P1`'s first probe (15:54:33), so it
did not start with `P1`'s traffic, and it did not follow load afterwards either
(§ 7.9). Per capture, the corrected loader values are in § 7.1 and
`c-clock/f5-best.tsv`; for a warm catch K and W differ by at most 0.0007, and a cold
catch's r is an average over its 180 s, uncertain by ±0.3–0.8 % at the loader instant.

**The board's own rate** from 16:01 to 16:32: 100.0031 ticks per Windows second (48
values, rms 3.6 ms), 99.998 ± 0.001 per NTP second. Between `P1-N0` (15:57:43) and
`P1-TR1-S0` (16:01:16) the board's counters advanced **105 ticks fewer** than that rate
predicts (the condition written first was |Δ| ≤ 3) — which is the whole of the 99.93
per realtime second this section used to quote over `P1-N0` → `P1-US1-S1`. 推 timer
interrupts masked for about a second; the cell is not identified.

**What the correction does.** `P1-A`'s excess over the later cold catches (×1.0225 on
`booting`, ×1.0238 on `banner`) becomes ×0.9993 and ×1.0003; § 7.1's warm split
disappears; `D2` holds either way. So the loader did not drift inside this seating:
the host's clock did.

**Consequences.** (1) An interval measured after ~15:49 is short by 1.4 % (15:52) to
3.1 % (18:10), and by up to 3.9 % over 2–7 s stretches. (2) `CLK-32`'s per-seating
factor is, 推, mostly this host clock — § 5's retro test, where it is written what
that test could and could not decide. (3) § 5's "`D2` is unaffected: both columns
carry the same factor" holds only when both columns ran at the same host rate; here
the rlxfw warm catches ran at r 0.986 and the vendor warm ones at 0.961–0.976.
(4) `dmesg -T` converts old kernel lines with the current offset, so it shifted them
by the accumulated steps — 24–26 s in this seating (`CORRECTIONS` § 5.2); journald's
stamps do not.

🔄 Until the 106th segment this section quoted three references read by one
computation, called the steps Hyper-V's and load-driven, gave "0.000 % inside `P1-A`,
0.18 % from 15:13 to 15:55" (step counts, not rates), put the host at "up to 2.4 %"
slow, reached a corrected warm Δ of −3.8 ms by assuming `P1`'s resets ran at r = 1
(they ran at 0.9861), and cited a tick count of IRQ 24 (it reads 0; the tick is
IRQ 13).

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
  896.6 µs with the kernel's receive stamps converted through each capture's own
  real/mono pair. Both exceed 260.4 µs: the stability test fires, as the card
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
  loud one at NIC+4.45 s, just after.
* 🔄 **The quiet image was read through the same window** (107th segment): its first
  replies beat the next reset by 16.1, 2.5 and 39.5 ms in `P1Q-r01`…`r03` (量, two
  computations sharing no code), and `P3Q-r01` got none. Which boots have a reading is
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
  58,989 closed, 6,546 filtered (no response).
* The vendor (`V1-NMAP`, the same scan): 80/tcp open (predicted); 52869/tcp and
  52881/tcp open (first reading; 推 `miniigd`'s UPnP ports); 65,381 closed, 151
  filtered.
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
  stays 推 (`miniigd`'s port is configured).
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
  on all 19 boots that carry a send, so neither anchor moves a verdict.
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
  f ≥ 0.983658.
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
  a seating-B bracket that excludes that offset.
* 推 `boa` listens 0.111–0.127 s before its `boa: server version` line's first byte
  reaches the host, and the probe's 0.2 s connect phase sets the sign of "ok − line" —
  refuted by a seating-B boot whose last-refused-to-first-ok window excludes it.
* 推 `CLK-32`'s factor is the host clock — the loader's `booting` stamped on a clock the
  host does not slew should land within ~±0.5 % of 0.35625 s in every seating (§ 5).
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
  a function of load — while `RAW` stayed within 0.9997–1.0012.
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
