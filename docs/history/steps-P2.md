# `PROGRESS.md` § `P2`'s step list, archived verbatim

Moved here verbatim from `PROGRESS.md` at `e274ccb`, lines 2438–2620, by `R1y-4`
on 2026-09-30. A record: never edited. Cite a step by its id; `tools/docmove.py`
proves the move.

## `P2`'s step list — ✅ CLOSED 2026-09-25, in 10 segments (102nd–111th)

**Gate:** boot-time breakdown + throughput, both firmwares, same script
(`plan/router-rebuild-plan.md:1607-1638`). **Opened** 2026-09-23 by the owner.
**Est. 8 段** — the plan's 小計 (3 desk / 3 bench / 2 instrument, `:1980`); the
board's 6 is not the denominator. With `R6` as the twelfth calibration point the
band's edges do not move (0.333×–1.385×) and its median falls 0.833× → 0.735×:
**3–11 段, median ≈ 6.**

**This list is at the end of the file, not above § Gate board.** An insertion
there would move 23 line-number citations that still land on their row, 13 of
them in records nothing may edit (8 frozen cards, 5 `LOG.md`); below line 2340
an insertion moves none. Measured and simulated 2026-09-23: `SPEC.md` `FW-110`,
`notes/record-integrity.md` § 5.3.

### What the gate starts from

* **The control segment already has an instrument.** `tools/boot-timeline.py`
  measures the loader's `booting` and `banner` intervals and splits cold from
  warm by `C-8`'s line: 56 cold and 193 warm on disk. Warm `booting` medians
  drift **9.7 %** across 16 seatings, while the median range inside one seating
  is **6.5 ms** (`CLK-31`).
* **rlxfw, `J` → prompt:** 6.97–12.56 s over the 138 committed boots, because
  the image changed under them: 6.97–7.35 s before rlxfw's 300-jiffy pre-check
  wait arrived (image `EA6EE537`, 2026-09-06b), then 9.77–11.02 s quiet and
  11.79–12.56 s loud (`CLK-33`). Kernel init is dominated by the vendor's WLAN
  init (≈4.5 s, present in both kernels) and by that wait (≈3.0 s; `CLK-27`,
  `IRQ-13`).
* **Vendor:** `G6`, `G7`, `H2a2` (a `J` of the pre-staged image) reach `boa`
  25.7–26.1 s after `J`; `K-J` (a natural warm boot) 31.28 s after `Booting`.
  `J 80500000` boots the vendor with no upload, byte-exact with an autoboot
  from `decompressing kernel:` on (`LDR-22`).
* **Throughput on disk is all on rlxfw's kernel** (`NET-84`, `NET-85`,
  `NET-102`). No vendor-firmware figure and no vendor receive figure exist.

### Settled before any script

1. **The vendor firmware has no shell.** Its `inittab` runs only
   `::sysinit:/etc/init.d/rcS`; none of the five vendor boots on disk answered
   a command. Its column comes from what it prints unprompted and what the host
   sees on the wire. `iperf3`, `/proc` reads and per-daemon CPU time on the
   vendor are ⊘ — structural, not deferred.
2. **The identical-code segment is `Booting` → banner.** With ESC the loader
   goes banner → prompt; without it, banner → ≈5 s → `Jump to image start`
   (`LDR-15`: 5.036 s in `K-J`, a warm boot, and 5.210 s in `X8-WAIT`, a cold
   one; `CLK-33`). The two paths diverge at the banner.
3. **rlxfw brings no network up at boot** (`config/rlxfw-init.sh`). The image
   under test gets an `/init` that runs the bring-up commands itself. It is
   priced in `P2-2` and leaves Decision B intact.
4. **One clock.** Console bytes and host network events are stamped on the same
   `CLOCK_MONOTONIC`, and the offset between the two channels is measured on
   rlxfw, which can print and send in one command.
5. **A vendor boot writes flash only when its config self-test fails, and then
   only its own config sectors.** Evidence: the unit's `startup.sh:19-55`;
   `flash settime` only reads (`flash.c:408-494`); seating 17's bracket read
   0 bytes changed. The owner accepted the runs on 2026-09-23, with a `map`
   before and after every block of vendor boots.
6. **Two calendar days, and one power press per vendor boot**, because no
   command leaves the vendor firmware. The card states the press count before
   a seating is booked.
7. **`console-capture` already stamps on `CLOCK_MONOTONIC`.** 量 2026-09-23
   under WSL's `/usr/bin/python3`: `time.monotonic()` minus
   `clock_gettime(CLOCK_MONOTONIC)`, read back to back, is −4 µs. The
   one-clock work is recording each capture's absolute origin, not changing
   its clock (`FW-114`).
8. **An unprivileged ICMP socket is refused on this host.** 量 2026-09-23:
   `net.ipv4.ping_group_range` reads `1 0`, and
   `socket(AF_INET, SOCK_DGRAM, IPPROTO_ICMP)` raises `EACCES`. The host probe
   drives the system `ping` and cross-checks its stamps against a second
   clock; it does not change a system setting (`FW-114`).
9. **`EW` and `EB` each need the owner's dated yes, with no address
   allow-list** — the owner's ruling on 2026-09-23. `P2-2`'s `cardcheck`
   refusal (`FW-113`) implements exactly that.

### The steps

| Step | | What it produces | DoD | Where it is most likely to be wrong |
|---|---:|---|---|---|
| **`P2-0`** ✅ **2026-09-23** | desk 1 | This list, the owner's three rulings, and the disposition of the seventeen carried-forward rows `R6`'s closing orphaned | Each row adopted by a step below, re-owned, or declined with a refutable reason, **in place**; `cfcensus` `L1` down in the same commit | That "adopt" parks unrelated debts on a measurement gate. 🟢 Done: 8 adopted, 4 to `R6b`, 5 ⊘; `L1` 17 → 0. `NET-25` was not adopted, because settled item 3 breaks its protocol |
| **`P2-1`** ✅ **2026-09-23** | desk 1 + instr 1 | `boot-timeline` past the loader, with landmarks for both firmwares as DATA through one function; `console-capture` on `CLOCK_MONOTONIC`; a host probe (timestamps only, no frames); `looprun` running N boots per power press, with per-round artefacts and stage times written to a file (`LOOP-3`) and boot cells ending on `--until` chosen from the corpus silence distribution (`TERM-1`). **Then every committed boot capture is run through it** — the prediction `P2-3` is scored against | Comparable segments come from the same code for both columns, with a control that feeds one committed vendor capture and one rlxfw capture through it; every interval names its anchors; each cell carries `n`. The 19 loud boots the tool now misreads as late opens are fixed, with a control | That the committed captures were taken for other questions, so the retro table is a prediction with a stated weakness and not a result. 🟢 Done in one segment: the four instruments (`FW-115`–`FW-118`) and the retro table (`CLK-33`), which also measured one timebase factor per seating (`CLK-32`) and so gave `D3` a second reading written before seating A |
| **`P2-2`** ✅ **2026-09-23** | desk 1 | A quiet and a loud image of one recipe: `recover` on (`NET-107`); an `/init` that brings the LAN up; the vendor NIC's open path intact (`CONFIG_RLXFW_VENDOR_ETH_OPEN=y`, `0007`'s own switch back at its Kconfig default, `NET-106`); `kbuild` running `kconfig-delta check` and `rlxfw-marks verify` into the manifest (`CFG-3`, `TC-i`); a checker for a card's `declared-date` (`CAPD-1`); `cardcheck` refusing `FLW`, `EW`, `EB` and a non-zero `AUTOBURN` unless the card carries the owner's dated yes (`FW-113`); card A; and four things `P2-1` handed it: every block that can boot the vendor — a `looprun` block included — bracketed by the flash `map` (`notes/dev-loop.md` § 19); the probe's `start` line awaited before power (`FW-116`); the vendor's LAN address and the host's address on it; and a vendor cell whose stop before `boa` is a reading (`X8-WAIT`, `CLK-33`). `looprun`'s `M10b`–`M12b` run the real driver whose manifest this step changes, so they are re-verified here | The card frozen with `spec-check` green on a tree where it is staged; every prediction re-derived from the retro table; the press count stated; rows cited by id; `cardcheck` shown refusing each of those verbs and permitting them on a card that carries the yes | Predictions copied instead of re-derived. 🟢 Done in one segment: recipe `a2c56bc8` built quiet (`p2q`) and loud (`p2l`) under both declaration gates (`FW-121`) and, for the first time, the tripwire (`FW-122`), and rebuilt byte-identical; `CAPD-1` (`FW-120`), `CFG-3`, `TC-i` and `FW-113` closed; card A frozen as `bench/2026-09-23/PREDICTIONS-B44-block42.md` — twelve presses, `D2`'s two columns captured in one mode (the vendor started by `J 80500000` from a caught prompt, `LDR-22`), every prediction re-derived from `CLK-33`'s table, `cardcheck` 100 commands and 39 of 39 numbers. `looprun`'s `M10b`–`M12b` re-run: 105/0, and they now stop at kbuild's initramfs guard before any stage. Found on the way: the manifest's initramfs digest could not see contents (`FW-123`), and `hostprobe` 1.1's records would have turned `capdate` red (1.2) |
| **`P2-3`** ✅ **2026-09-23** | bench 1 | Seating A: both firmwares, cold and warm, through one script; the throughput matrix; `NET-109`'s pre-traffic `asicCounter` reading | Every cell captured; `D2` computed before any comparison is read | That the vendor writes flash while measured — the bracket makes it a reading. 🟢 Done in one segment, twelve presses: 223 of 223 cells on the declared date; the three map brackets identical to the prediction (`FLS-30`); `D2` held, computed before any comparison was read (`CLK-34`); `NET-109`'s pre-traffic pair read the healthy shape. Found: `rlx0` loses frames it reports as sent, below the engine, and `recover` cannot see it (`NET-112`, `NET-113`) — six of its twelve trials never finished their exchange and three could not connect, while the vendor driver finished all twelve (`NET-114`); the host's monotonic clock ran slow from ~15:49, 1.4 % deepening to 3.1 % (`CLK-35`, `CLK-38`). Deviations: `bench/2026-09-23/CORRECTIONS-block42.md`. Its readings were computed and second-sourced at the desk by the 106th segment (`notes/boot-time.md` § 7) |
| **`P2-4`** ✅ **2026-09-25** | bench 1 | Seating B, on another calendar day. Its card first carries what seating A exposed: every capture and probe stamped on `CLOCK_MONOTONIC_RAW`, which the host does not slew, with `timesyncd` stopped for the seating so the two time daemons cannot fight (`CLK-38`) and a host clock log for the whole seating and the board's ticks read at the start and end of every rlxfw press (`CLK-35`); `D8` from the probe's own monotonic ledger, never through realtime, reconstructed for whichever broadcast of a cycle is answered; both images kept up 2.5 RAW seconds past the prompt in every round, the last included (`looprun`'s `S9`, `FW-127`), because seating A's quiet replies beat the reset by 2.5–39.5 ms, `P3Q-r01`'s never came, and `P1L-r03` was reset by the card's `P1-RZ`, not by `looprun` (`CLK-36`); an rlxfw receive figure from the board's own server log, not `iperf3`'s end-of-test exchange (`NET-112`); and `cardcheck` refusing a `HOST` cell whose arguments its own tool rejects (`FW-124`). Its predictions are re-derived from seating A's numbers corrected for the host clock (`CLK-34`), and it tests the three inferences `notes/boot-time.md` § 7.7 still hands it (the fourth, the host clock's mechanism, was decided at the desk, `CLK-38`) | Every `P2-3` number measured again, with the date checked by the `CAPD-1` checker | That "another day" becomes the same session under a new date. 🟢 **Done in two segments — the bench in the 110th, the record in the 111th.** Seating 40, 2026-09-25 00:02–02:49, twelve presses, run from card B re-dated after its 2026-09-24 window passed unrun (`bench/2026-09-25/PREDICTIONS-B46-block44.md`): **246 of 246** captures after the prediction, and `capdate` 0 red, the directory's first capture 30.4 h after seating 39's last. Two stops, each handled by the card's own table and read by the owner (`bench/2026-09-25/CORRECTIONS-block44.md` §§ 1–2); each of the three map brackets reads 31 groups the same and one `DIFFER`, the expected group 0 (`FLS-31`). Every `P2-3` number was measured again on `CLOCK_MONOTONIC_RAW` — five `rlx0` trial figures have no seating-B reading, their trials having failed — and scored against a list frozen before any seating-B interval was computed: `D2` held (`CLK-45`); `D3` reproduced 134 of the 140 stable numbers, and none of the six misses is a row of the segmented table or `D7`'s Δ (`CLK-48`, carried as `D3-MISS`); `D7` held (`CLK-46`); `D8`'s own refutation fired as predicted, so network up stays a console-side bound (`CLK-47`). Of `notes/boot-time.md` § 7.7's three inferences, (iii) holds — between seatings A and B, `CLK-32`'s factor was the host's clock, and for earlier seatings it stays 推 (`CLK-43`) — and (i) and (ii) were not refuted, (i) by a weak test. Found, 量 unless marked: the board lost about 105 jiffies again in the same stretch, and jiffies are IRQ 25, not IRQ 13 (`CLK-42`); a console stamp can arrive 13.5 ms late (`CLK-44`); `rlx0` finished 0 of 12 exchanges and its UDP datagrams die above the driver (`NET-116`, `NET-117`); 52881 is 推 `wscd`'s, not `miniigd`'s (`NET-118`); rlxfw's ICMP round trip rose while the vendor's fell (`NET-121`); five instrument defects (`FW-135`–`FW-139`). Readings: `notes/boot-time.md` § 8, `notes/nic-driver.md` § 20 |
| **`P2-5`** ✅ **2026-09-25** | desk 1 | The write-up: the segmented table beside the feature table, whose method section states the enumeration rule (`GREP-1`); each daemon's start and readiness; throughput; sizes. Then `docs/GATE-RESULTS.md` entry 13 | The DoD read one row at a time; what was not established; the operating clause re-run at thirteen entries | 🟢 **Done in one desk segment, the 111th.** `docs/boot-time-table.md`: the cold and warm tables, each cell with n, median and range for seating A raw, seating A corrected and seating B, its class and its `D3` verdict; network up and readiness, with each vendor daemon's own start and readiness; the feature table from two sources per firmware (`D4`); throughput (`D5`); sizes and memory (`D6`); and a method section that states the instruments, the one clock, the `D3` contract and `GREP-1`'s enumeration rule with its counts (`FW-141`). The judge's score is `docs/boot-time-d3-score.tsv`. `docs/GATE-RESULTS.md`'s thirteenth entry reads the plan's two rows and `D1`–`D8` one at a time and states what `P2` did not establish; the operating clause, re-run at thirteen entries, does not fire, and the census is re-run beside it |
| **`P2-6`** ⊘ **not done, 2026-09-25** | desk 1, rides seatings | **Stretch:** the plan's *中斷延遲（LA 量）*, with the logic analyser `plan/router-rebuild-plan.md:1908` lists as on hand and never connected. First rung: the plan's own self-test on the console TX bit (26.04 µs, computed beforehand). Then a GPIO toggled every tick, and edge-to-edge jitter idle and under `iperf3` | The self-test within one sample period; at least 10,000 ticks per load condition | That the analyser is missing or broken — the first rung answers it. One segment; not a pass condition. ⊘ **Not done — the first rung never ran.** 讀: none of `P2`'s three bench directories (`bench/2026-09-23/`, `bench/2026-09-25/`, `bench/2026-09-25b/`) names the analyser, and the plan's hardware table lists it as on hand and never connected to anything. The stop-loss below wrote the failed-rung case, and the unrun rung is treated the same way: *中斷延遲* is recorded as not done, and the on-die counter does not stand in for it under the plan's name. Carried forward as `LA-1`, owned by `P3` |

### The DoD, split into what can be refuted

* **D1** — one script for both firmwares, and every segment called comparable is
  computed by the same code in both columns; what differs is a landmark table
  each.
* **D2** — the positive control: `Booting` → banner measures the same in both
  columns, cold against cold and warm against warm, **inside one seating**,
  within a band written before seating A from the retro spread.
* **D3** — every number is reproduced on a second calendar day within ±10 %
  (the plan's condition). Cold and warm boots go in separate tables, each cell
  with `n`, median and range, and misses are published. Pre-registered from
  `CLK-32`, before seating A: every segment of one image moves with its
  seating's loader `booting` by one factor, and one image has already differed
  by 6.7 % between two directories. So each cell is also published divided by
  its own seating's loader `booting` ratio — beside the raw figure, never
  instead of it, and the ±10 % is not widened.
* **D4** — rows are marked *identical*, *comparable* (both images' sizes
  printed beside them), or *not comparable*; for the last, each daemon's own
  start (its console line) and readiness (the first host-side success on its
  port) stand in for a total. The feature table comes from two sources each:
  vendor scripts plus its console announcements and a host port census; for
  rlxfw, the initramfs manifest plus `ps`.
* **D5** — throughput. (a) ICMP echo at fixed payloads from the host, both
  firmwares, one host script. (b) `iperf3` 3.1.3, TCP both directions plus UDP
  with `-l`, trials ≥ 30 s, n ≥ 3, for rlxfw's driver and for the vendor's
  driver on my kernel; board CPU from `/proc/stat`, and no typed verb needed.
  (c) ⊘ `iperf3` on the vendor firmware. Never printed beside the published
  ~94 Mbit/s, which is NAT forwarding.
* **D6** — kernel and rootfs sizes for both (讀); memory free after boot for
  rlxfw (量); ⊘ vendor runtime memory.
* **D7** — the loud image's *kernel entry → init* exceeds the quiet one's by its
  extra console bytes ÷ the sustained rate measured in `FW-70`, within `FW-32`'s
  residual. Byte counts come from committed captures before either image boots.
* **D8** — *network up* is the first ICMP echo reply (the loader has no ICMP),
  stamped on the console's clock, with the channel offset measured.

### Refutation conditions, written now

* **`D2`** *(the plan's)* — a difference inside one seating means the method is
  broken. The candidates are named now: read chunking while streaming ESC versus
  only listening; cold and warm boots pooled; USB latency drift. No comparison
  is published until the control agrees.
* **`D3`** *(the plan's)* — a miss means the method is broken for that number;
  it is published with the miss.
* **`D3`'s closing rule** — decided by the 111th segment on the owner's
  delegation, committed 2026-09-25 before any seating-B interval was computed
  (the only seating-B values read before it are the ones `LOG.md` 第一百一十段
  quotes). Card B § 3.10's test is unchanged: a hit needs (a) and (b) both within
  ±10 %. (1) A number is **not stable** — scored, published, deciding nothing —
  when card B § 3.10 lists it; when its own seating-A values already reach ±10 %
  of their median (the card's criterion, applied to every number: the larger of
  |max/median − 1| and |1 − min/median| is ≥ 0.10); when its seating-A range
  contains 0, since a signed offset has no ratio; or when it is under 20 ms,
  where the two `FW-35` read quanta at its ends alone move it by 10 %. The list is
  generated by a script from seating-A files only, before any seating-B value of
  a number on it is read. A number card B measures by a rule other than the one
  seating A published it with is compared with seating A's files re-read by card
  B's rule. (2) A stable miss on **a row of the segmented table** — a
  `boot-timeline` segment per firmware, variant and class, `J` → prompt, the
  vendor's `J` → `boa`, rlxfw's `J` → `N-NDOPEN`, the vendor's port-80 readiness
  from `J` — or on `D7`'s Δ **keeps `P2` open**: the table the gate exists to
  publish cannot carry a row the plan calls broken, so the method is repaired from
  a desk test that could have failed and those rows alone are measured on a third
  calendar day. (3) A stable miss on **any other** number is published with both
  columns as not reproduced, leaves the results, and becomes a carried-forward row
  naming the experiment that decides it; `P2` closes. (4) No number changes class
  after a seating-B value of it is read, and the ±10 % is not widened.
* **`D4`** — a process or port the vendor shows that its scripts do not start,
  or the reverse: the feature table is re-derived from what actually ran.
* **`D7`** — the expected difference is not seen. Either the method cannot
  resolve it or console output is not paced by the UART; the console write path
  decides which, and the table carries the measured resolution.
* **`D8`** — the channel offset is not stable to within one byte time: *network
  up* is then published only as a console-side bound.

### Stop-loss, written now

* **No segment budget**: the owner removed the 11-segment stop-loss on 2026-09-25
  (`LOG.md` 第一百一十段); segments are still counted in § Gate board's `Actual`.
* Any difference in a `map` bracket: no further vendor boot runs until the owner
  has read it.
* No cell touches the reset button while the vendor firmware runs (`FW-40`,
  `FW-62`).
* `D2` fails at seating A: seating B is not booked until the method is repaired.
* `P2-6` gets one segment. If its first rung fails, *中斷延遲* is recorded as not
  done; it is not substituted by the on-die counter under the plan's name.

### What this gate must be able to answer

Derived questions — the plan's § 11 has no `P2` row:

* *「你開機比較快，是不是只因為你少跑了東西？」* → the segmented table, the
  identical-code control, the feature table, and each daemon's own cost —
  including the 3 s this project's own timer driver waits on purpose.
* *「換一天量，還是這個數字嗎？」* → `D3`, with its misses printed.
* *「你的儀器分得出你在比的差嗎？」* → `D7`, and the capture floor seating 17
  measured (0.517 and 0.868 ms).
