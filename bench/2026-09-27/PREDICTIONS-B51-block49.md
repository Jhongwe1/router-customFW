# PREDICTIONS — block 49, seating 43, card A (`R6b-3`'s third card, part A: one press of `P2`'s quiet image `p2q`, a cold quiet boot, carrying `D3-MISS` ①, ② and ③)

**declared date 2026-09-27** — **one power press**; its catch window opens no later than 23:00
that day, or the card is re-dated before power (§ 6).

The row of `R6b-3` puts a cold quiet boot of `P2`'s quiet image in its seating as the
before-column `D3-MISS` asks for, carrying ①'s width on `CLOCK_MONOTONIC_RAW` and ②'s series,
and since 2026-09-26 ③ in the rows' own one-read shape (`PROGRESS.md`, `R6b-3` and `D3-MISS`).
Card 2 (block 48, `bench/2026-09-26b/`, recorded in `notes/nic-driver.md` § 27) left ① and ② to
this press (`$FWRE_WORK/rebuild/s112/r6b3/card2/NOTES-card3.txt`); ③ joined `R6b-3`'s card 3
from `R6b-2` at its close (`PROGRESS.md`, `R6b-2` and `R6b-3`). The owner's decisions this card
rests on are recorded in `LOG.md`'s entry for the 113th segment (第一百一十三段), § 六: two presses in
seating 43, this one on `p2q` and card B's on `r6b6q`; and `D3-MISS` ②'s vendor series, which
the owner handed to the session, decided as `eth4` with the vendor-firmware series ⊘, and
written into the `D3-MISS` row by `3e72889` (`cardnum` rows count both). The card's shape — the
press, the three rules, the stop rule S1 — was drafted from a plan of 2026-09-26, of which no
copy is committed; § 0 ⑪ names where the card departs from that plan and why. Card B of seating
43 (`r6b6q`) is a separate card, drafted beside this one; the order of the two presses in the
seating is the owner's.

Marks: **量** measured on the device · **讀** read out of code or a dump · **推** inferred,
pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this block is, and which rows it carries.** One press of `p2q` (driver `rtl819x-nic`
1.4, recipe `a2c56bc8`), the image seatings 39 and 40 and blocks 45 and 46 booted; a cold catch
and one round, so the boot every reading below comes from is a cold quiet boot.

| row | carried here | not here |
|---|---|---|
| `D3-MISS` ① (`D8\|width\|quiet\|cold`) | one cold quiet boot on RAW: the probe's ledger, `P2`'s text capture across the boot, the clock log and its guard; the rule in § 3.4, fixed now | a second cold boot (n = 1 against seating B's two) |
| `D3-MISS` ② (`D5a` rows, `NET-121`) | twelve ICMP series on `rlx0` at 1.4 and twelve on `eth4`, the vendor's driver on the same boot, as the row asks since `3e72889`, the host capture on and off ABBA; the rule in § 3.5 | the vendor firmware's series: ⊘, decided 2026-09-26 on the owner's delegation (`LOG.md`, 第一百一十三段 § 六) and written into the `D3-MISS` row by `3e72889` — another kernel, another driver and a vendor boot, whose flash effect is 推 (§ 0 ⑦), so a flash-write exception for a comparison that cannot isolate the driver |
| `D3-MISS` ③ (`NET109\|crcalignerr`, `NET109\|p3egress`) | the rows' own shape: one `asicCounter` read on a healthy fresh boot, after the probe stops, between two host reads, against W from a capture started before `J`; the readings fixed in § 3.3 | a second healthy boot |
| `NET-124` 殘留, `NET-54` 殘留 ② | a liveness gate before every series, a port-3 gate before each arm, a path gate after every series, the host's kernel log from before the press; on a liveness failure the stop rule S1 (§ 6) | — |
| `C-19` | named: every kernel-log window counts its signatures, and the record states every console drop and every idle over a minute, with the idle before it | — |
| `D1`, `D2`, `D3`, `NET-117` 殘留, `NET-131` 殘留 | — | this image carries 1.4 only and no fix arm: card B and later cards |

**② Why `p2q`, and why 1.4 is not a hazard the card ignores.** ① and ② are numbers of `P2`'s
quiet image, so they are re-read on it (the carried-forward row's ⚠️: on a changed driver they
compare a different build). At 1.4 a TX stall is possible — block 48's one stop was a 1.4 stall
with the host reaching the board (量 `notes/nic-driver.md` § 27.9) — so every series has its own
liveness gate and board bracket, and a failed liveness gate is classified from the board before
the host is touched (S1, § 6). 推 every frame this card makes the board send is clean at 1.4
(§ 3.5, P10), which is itself a prediction the card tests.

**③ Every rule is fixed before power.** ①'s band, ②'s references, test and decision, ③'s three
identities and the boot shape they are scored on, and S1's branch rule are in §§ 3 and 6 and in
`cardnum` rows; nothing in them is chosen after a reading.

**④ What reads silicon for the first time.** Four new instruments, each with a self-test, a
mutation run that kills every planted defect after an unmutated pass, and a control on
committed data (counts in `cardnum`):
* `rttseries.py` 1.1 (②): the series' state, the ABBA order, the medians, the Mann-Whitney
  count and the references; its parser read seating B's `P3-ICMP` bytes.
* `w3.py` 1.0 (③): the three rows from one board read, pcapwin's record-order anchor and the
  whole capture's destination classes; its end-to-end control reads block 46's 76 board reads
  against block 46's capture (every row holds, 228 of 228) and fails when each read is scored
  against the next bracket's counters (`w3ctl46-shift.out`).
* `w1width.py` 1.0 (①, run after power-off in `I-C9`): `netup`'s readers of the 111th segment
  imported unchanged and its per-boot rule copied for one boot; it reproduces seating B's cold
  widths 0.094550 and 0.114647 s, the warm ones and the loud one to 1 µs, with the frames put
  on RAW by `tools/hostclock.py convert`.
* `s1class.py` 1.0 (S1, shared with card B at `$FWRE_WORK/rebuild/s113/shared/`): branch a on
  block 48's `D3-LUS1-L` episode (host tx 6, port 3 rx 6), branch b on block 46's 55 pairs from
  `NET-124`'s onset on; a planted port 3 count one frame short flips branch a to b. Its limit,
  pinned as K5: on block 46's 21 pairs before the onset, where the host reached the board, 2
  read branch b by 1 and 2 frames, because block 46 took no host read before its board reads
  and its later `-H` stood in; every bracket here, and S1's own `X-HP<n>`, is such a read
  before the board read, which is what the rule needs.

None of the four has read a capture this card makes; a cell that fails because an instrument is
wrong is a finding about the instrument.

**⑤ The host is restarted before the seating** (card 2's engineering decision, kept): a fresh
WSL, a fresh attach of both USB devices, and a kernel-log follower started before the attach
into `$FWRE_WORK/rebuild/s113/card43a/host/dmesg-w.log`; `R0-DW0` refuses power unless that log
reads `bug_preempt 0`, `usbnet_xmit 0` and `call_trace 0` with the board off.

**⑥ Containment, which does not depend on any outcome.**
* **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR` (`cardcheck` refuses
  them, `FW-113`; `cardnum` rows count zero); every upload is `looprun`'s, which requires
  `00000000` read back from the `AUTOBURN` word first; the press is bracketed by two maps
  (`A1-M0`, `A1-M1`) and `n_writes` (`A1-NW0`, `A1-NW1`). No vendor boot is typed; a reset's is
  § 0 ⑦'s, which does not depend on any reading either.
* **The owner's handshake**, for the card's two physical actions, the press (a power-on) and
  the power-off, as the owner stated it on 2026-09-27: for every power-on and power-off the
  session tells the owner and STOPS until the owner replies; only then does it open the catch
  (or the power-off window) in the background, confirm from the transcript that the
  ESC-streaming cell is running, and then tell the owner "catch open — power on now" (or "power
  off now"); the owner acts only on that word. No count-to-five after the reply, and nothing
  physical happens between the reply and the session's "now". Nothing physical is timed from
  the reply, because the session's own latency between a reply and a window's start can exceed
  any count the owner makes. Each window streams ESC from its start for 60 s for the session to
  open it, confirm it and say "now", plus 300 s for the owner after "now", both guesses
  (`arith43a`'s `HANDSHAKE` line): 360 s for the catch — which ends sooner, at the loader's
  first prompt, once the press is caught — and 360 s for the power-off window, and the "now"
  message states that length (§ 6, *The owner's actions*). With the board at the loader's
  prompt a power-off has no window (§ 6, *The watch*).
* **Frames at 1.4 on the wire are bounded by what the card sends**, whatever they do: the
  probe's replies until `A1-HPX`, twelve `rlx0` liveness gates and any S1 re-pings (four 60-B
  echoes each), the board's own 60-B ARP replies and requests, and twelve `rlx0` series of 100
  echoes of 98–1,514 B; no driver verb is typed (`cardnum` counts no `> /proc/rtl819x-nic` in
  any send), so no sweep and no raw frame. Whether those frames are clean at 1.4 is a
  prediction the card tests (P10), not containment.
* **What the host keeps of a frame**: `P2`'s text capture (`TDT`, block 44's filter unchanged)
  prints ICMP by IP and ARP only from `rlx0`'s and the loader's addresses (量
  `$FWRE_WORK/rebuild/s109/tcpdfilter/`: no other address prints); ③'s capture (`TDE`) keeps
  only frames from `rlx0`'s address, cut at 64 bytes, into `$FWRE_WORK`, never the repository,
  and only `pcapwin.py` 1.3 reads it (counts, never an address).
* **`rlx0` goes down once** (`H-DOWN`) and is not re-opened on this boot (`NET-58`); no cell
  touches the reset button or the watchdog.

**⑦ Resets, and the one this image can do by itself.** No cell types anything that resets the
board, but `p2q` carries `rtl819x-wdt` 1.1, built in (`CONFIG_WATCHDOG=y` and `MK6`'s `obj-y`;
its `bootguard` parameter is in the image's `System.map`), which arms `BOOTGUARD` at
`late_initcall` at OVSEL 9 and kicks it from a kernel timer every 250 ms (讀 `66ddb93`'s
`rtl819x-wdt.c`, extracted by `src43a.sh`; `cardnum` rows): a kernel whose timer wheel stops
for 83.8 s by the driver's own figure — 84.001 s as measured at OVSEL 9 (量 `CLK-08b`) — is
reset, and the loader then boots the vendor firmware unless ESC reaches it inside its window of
about 4.9 s (`console-capture`'s own record). What that vendor boot writes to flash is 推: 讀 a
vendor boot writes only its own config sectors, and only when its config self-test fails
(`PROGRESS.md`, `P2`'s settled item 5), and 量 nine vendor boots on 2026-09-23 left the three
map brackets around them as predicted (`FLS-30`) — a bound that does not see `H601`, two writes
that cancel, or any byte outside the map. `VDR-1`'s flash write is not this: it belongs to the
`formSysCmd` entry into vendor userspace, which writes `COMPCS`, and nothing on this card takes
that entry. The card catches the loader rather than let the vendor firmware boot (`CLAUDE.md`),
whatever that boot would write; at the press itself a missed catch also loses the press (§ 6,
*The owner's actions*). A capture that only *ends* on the banner stops nothing. So, whatever
any reading says: **(i)** every board cell's capture ends on the loader's banner — a board
read's and a map's `--until` holds `Booting\.\.\.|---RealTek` as an alternative, every `--idle`
cell carries it beside its idle (a `cardnum` row counts every `--idle` cell and every one so
ended), and the generator refuses a fenced board cell or a § 6 text without it, the pre-flight
and the catch excepted — and every board cell after the round carries the gate
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (35 gates), so a reset
stops the run in the cell it happens in; **(ii)** from one board cell to the next, the host
cells between them plus the next cell's cap stay under 83.8 s — the longest is before
`R-S02-R`: 54.7 s of host cells if every echo of the series before it times out (推: the
estimate's times and the `ping`s' `-w` deadlines; 7.8 s nominally) and its 15-s cap, 69.7 s;
the maps' cap is 60 s, and 6 committed maps of this command took at most 13.804 s — so a timer
wheel that stops leaves the next board cell silent, ended by its cap or its idle, and the
invocation stops, before the bite, 14.1 s being left for the runner's stop and the watch's
start (推, never timed); **(iii)** the press is one command line whose last command, run however
the runner ended, is the watch `X-W1`, which streams ESC and ends on the loader's prompt (§ 6):
a bite after the runner's stop is caught there and nothing boots; **(iv)** outside an
invocation, while the board runs a kernel, a watch holds the console at every later moment with
no other capture open for more than about 30 s, until the owner's power-off window, which
streams ESC too, and after any stop it holds, before any board cell is typed and before any
continuation starts, until at least 90 s after the latest board cell's capture **ended** — a
reading that showed the kernel running, or a board cell that ended silent, whose kernel's last
kick can be as late as its end — so that a kernel stopped by then has been bitten and the
loader has taken the watch's ESC: the bite as measured, 84.001 s, plus the loader's 2.288 s
from its banner to its first prompt with ESC streaming (量 block 48's `R1-CATCH`), plus 3 s (a
guess), rounded up (`arith43a`'s `HOLD` line; § 6, *The watch*) — where (ii) keeps the driver's
83.8 s, the shorter figure being the conservative one there; at the loader's prompt no watch is
opened, since the loader boots nothing by itself and a watch opened there ends on the loader's
own reply (§ 6). **What this does not cover** — three resets with nothing streaming ESC, after
which the loader boots the vendor firmware, whose flash effect is 推 as above and which this
card does not claim to prevent; § 6's loader rule then has the owner power it off, and the next
card's first map brackets that boot: **(a)** a reset from a cause other than `BOOTGUARD`, such
as the supply, inside a board cell: it ends that cell on the banner, and the watch that follows
it on its command line opens after the runner's stop or the cell's end, 推 inside the loader's
4.9 s but never timed; **(b)** the same reset in one of the 35 host stretches inside the
press's invocations after the round, where no capture is open: 24 of them a series' (6.0–7.8 s
each nominally, up to 54.7 s with every echo timed out), the longest nominally 12.1 s before
`B-AC0-R`, 191 s in all of the press's about 13 minutes (推, the estimate's figures, § 2) — the
next board cell's loader gate finds it only afterwards — or in a gap of up to about 30 s
outside an invocation, between a watch's stop and the next capture's start, or while the board
waits at the loader's prompt with nothing streaming ESC — from the catch to `A1Q`'s `J`, and
from a caught reset to the power-off — where the loader, restarted, finds no ESC; **(c)** a
kernel that stops after the board capture a stop's hold counts from, during the hold or after
it: it bites 84.001 s after it stopped, past the hold, and the bite can fall inside the next
board cell the session types (an S1 read, a stand-in, a map's repeat, `X-RT<n>`), which streams
no ESC, or inside a continuation's first host stretch, where no capture is open — the hold
covers a kernel stopped by that capture's end, and no hold of any length covers one that stops
later without a reading that it still runs. The console is also unwatched while WSL itself is
down (§ 6).

**⑧ The clock.** ①'s width is on `CLOCK_MONOTONIC_RAW`: the probe (`hostprobe` 1.3), the
console captures (`console-capture` 1.5) and the runner stamp RAW, and the frames are put on
RAW through the clock log (`hostclock` 1.0, `I-C0`) with `systemd-timesyncd` stopped for the
press and the guard `Z0-HCG` read before power — block 44's regime, its step gate lengthened to
read the detectors' verdict (量 seating B: 0 `step` rows over the seating, `notes/boot-time.md`
§ 8.2, from a detector whose positive control is § 3.4 P5's). ② and ③ claim no duration: ②
reads `ping`'s own rtt statistics, ③ counts.

**⑨ Runner limits worked around** (card 2's, and one new). The runner's background cells know
three programs, so the kernel-log follower is an off-card process started before `I-0`. Each
capture is a `HOST&` cell of the invocation that stops it, so a stop anywhere in that
invocation also interrupts its captures: 量 at the desk
(`$FWRE_WORK/rebuild/s113/card43a/stopctl/`), `cardrun`'s stop sent SIGINT to two
`timeout 900 sudo -n tcpdump` cells of this card's two shapes (text, and `-w` with
`-U -Q in -s 64`), both wrote tcpdump's three summary lines and ended 0.102 s after the SIGINT
(`stopctl/run.log`), and no `tcpdump` was left running — on the loopback interface with no
traffic, so § 6 still checks after any stop that none runs (`X-TCPK<n>`). New: the capture
state around a series (`-C0`, `-C1`, `pgrep -xc tcpdump`) is a reading, not a gate — a gate
would stop the run in the middle of the ABBA sequence — and the reader (`rttseries`, fixed now)
voids any series whose two counts are not its planned state; the capture's stop (`-X`) is a
gate, because a capture left running would contaminate every later off-series. The runner
cannot hold a console capture in the background either, so the watch (§ 6) runs after the
runner, on the press's own command line, never beside it. S1's cells are declared in § 6 with
their text.

**⑩ `C-19`** (the console adapter leaving the USB bus) is named: the kernel-log windows count
`USB disconnect`, `cp210x` and `ttyUSB` lines, and the record states every console drop and
every idle longer than a minute, with the idle before it. The row stays open after block 48 (0
drops, its trigger not exercised: `PROGRESS.md`, `C-19`), and this card exercises it less: from
the round to the power-off, while the board runs a kernel, a capture or a watch keeps the
console busy (§ 6) but in § 0 ⑦'s host stretches inside an invocation (the longest 12.1 s
nominally, 54.7 s with every echo timed out) and for up to about 30 s outside one, so no idle
there reaches a minute, and a drop after a long idle can happen only before the press, or with
the board waiting at the loader's prompt, where no watch is opened (§ 6).

**⑪ Where this card departs from the plan of 2026-09-26, each for a reason.**
* ①'s band is seating B's eight quiet widths, not its two cold ones ±10 % (the plan's example):
  a band from two points is the two-point constant `CLAUDE.md` forbids, it holds 3 of seating
  B's own 8 quiet widths, and no source separates cold from warm for this quantity. The cold
  pair ±10 % is kept as a reading, and ①'s decision is the list's own stability rule, computed
  now (§ 3.4).
* ②'s off medians are judged against seating A's range ±10 %, as the plan says, but the range
  is seating A's **uncaptured** series (P1, P2): its P3 ran inside the host's capture
  (`NET-121`), so it belongs to the on-state, which is judged against it. The frozen rows are
  also re-scored by `D3`'s own rule, the A median ±10 % (P7) — but three of the five A medians
  are P3's, captured (1,024 B avg, 1,472 B avg and mdev), so P7 decides only the rows whose A
  median is uncaptured; the 1,472-B avg row is closed on P6 (a)'s uncaptured band instead, its
  P7 score against the captured median published beside it, and the captured state's
  between-day shift stays open whatever the press reads (§ 3.5). ②'s decision is enumerated so
  that every outcome lands in exactly one case.
* Each series is followed by a board bracket (not in the plan): it gives S1 the previous
  bracket it classifies against, and `rttseries` voids a series whose bracket pair reads
  `covered no` or `jfd` ≥ 1.
* ③: one identity decides each row — `crcalignerr` by c = W + j + f + d, `p3egress` by its own
  measured quantity, unicast out of port 3 = W − B − M (the plan wrote W − B; M is predicted 0
  and read, never assumed) — and o = W is a reading beside it; only an `exact` hold is **met**.
  The probe's stop is followed by 12 s of quiet before the read, longer than the board's own
  ARP timers can keep it sending, 8 s (讀 `arp.c` and `neighbour.c`, § 3.3).
* `pgrep`'s counts are readings with the reader's void rule (⑨), not gates.
* Not in the plan, and shared with card B where the two cards have the same shape: the watch
  and the power-off window, which stream ESC so that a reset is caught at the loader's prompt
  (§ 0 ⑦, § 6); the owner's handshake (§ 0 ⑥), under which nothing physical is timed from the
  owner's reply, and with it a catch of up to 360 s of ESC instead of blocks 46–48's 180 s,
  which ends at the loader's first prompt instead of streaming to its end, so the board waits
  at the prompt before `J` only for the cells between the catch and `J` (`A1-FL`, three
  background starts, `looprun`'s steps before its `J`), where blocks 46–48's and seating B's
  cold catches held it to the end of their 180-s stream and its tail — 推 no reading here
  depends on it: the loader only answers ESC at its prompt, ① is timed from `J`, and P4's band
  already holds rounds whose `J` followed a prompt caught moments before, seating B's second
  and later rounds of a press, reached by `looprun`'s own reset (讀 `tools/looprun.py`); the
  step detector's desk control (§ 3.4 P5); the map's cap lowered from 180 s to 60 s (§ 0 ⑦
  (ii)).

---

## § 1 The image

The image is `p2q`, unchanged since `P2`: recipe `a2c56bc8`, `nfjrom`
`/home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom`
(`4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`), vmlinux
`c5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863`, initramfs manifest
`51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59`: driver `rtl819x-nic` 1.4 (量
block 46's `A1-00-R`, its version line), `rtl819x-spi` 1.2 (量 block 46's `R1-NW0`), watchdog
driver `rtl819x-wdt` 1.1 (讀 only, from git; its `BOOTGUARD` is § 0 ⑦'s), switch driver
`rtl819x-switch` 1.1 (讀 only: no card has read `/proc/rtl819x-switch` or
`/proc/rtl865x/port_status` on this image, so `R-LS` and `E-LS` are first reads of both pages
on `p2q`; the file is byte-identical to the one `r6b2q` ran, where block 48's gates matched it
28 times, 量). The chain is checked by this card's `cardnum` rows: the manifest `verdict green`,
`variant quiet`, that recipe, vmlinux and initramfs; the `rtkimage` record naming that vmlinux
and `nfjrom` digest with a CLEAN tripwire verdict; the `nfjrom` on disk with that digest, the
same file block 46's committed `QIMG` names; the image's `System.map` holding the switch
driver's `/proc` reader and `port_status_read`, the reader of `/proc/rtl865x/port_status` in
the vendor's `rtl865x_proc_debug.c` (讀 `r6b2q`'s build cell). Its build cell (`r3-4/cells/p2q`)
is gone, so the sources are read from git: 讀 the commit whose `config/` tree gives recipe
`a2c56bc8` by `rlxfw-kbuild.sh`'s own rule is `66ddb93` (2026-09-23), the rule reproducing
`r6b2q`'s `06c39ca3` at `92aeaa8` and `r6b6q`'s `acf8ed3d` at `920875f` as its controls
(`src43a.out`); its switch driver is byte-identical to `r6b2q`'s build cell's (both
`38685f0a…`), whose `PSRP3` row and link bit the port-3 gate reads. `looprun` pins the `nfjrom`
by digest before the port opens and compares the booted image's `RLXFW-ID0` with the build's.
No cell names an address from `System.map`.

---

## § 2 The press, in order

| invocation | what runs | est. min (a guess) |
|---|---|---:|
| `I-0` | before power | 0.7 |
| `I-C0` | the clock log starts | 0.0 |
| `I-C1` | the clock guard (before power) | 2.8 |
| `I-1` | the catch, the round, ③, the opening map | 7.4 |
| `I-R` | ② on `rlx0`: twelve series | 2.4 |
| `I-H` | the handover | 0.1 |
| `I-E` | ② on `eth4`: twelve series | 2.5 |
| `I-Z` | the closing map, the kernel log | 0.3 |
| `I-C9` | after power-off: the clock, the retro table, ① | 0.0 |

About 13 minutes from the catch's window to power-off (12.9 as `gencard43a` sums it, a guess) —
from the catch's cap, 380 s, its longest (it ends at the loader's first prompt, § 6, *The
owner's actions*); for each other cell the median `END` line of block 48's run logs for its
shape — a board bracket 5.3 s, a port-3 read 3.9, a liveness gate 0.9, a map 13.9, the round
24.7 with its 2.5 s dwell, an `--idle` board cell 3.4, a host read 0.1 — and block 44's for a
five-size ICMP series, 4.9 s (each an `arith43a.out` line with its count); and guesses: 2 s
between invocations — the runner's start-up, since the press is one command line (§ 6) — and
0.5 s for a background cell's start. `I-0` and `I-C1` are before power (`Z0-HCG` alone is 160
s, its sleep and its run). 26 board brackets, 26 host pre-reads, 24 liveness gates, 24 ICMP
series.

The order protects the readings: ③'s one read comes first after the round, before any traffic
but the probe's and 12 s after the probe's stop; ①'s captures and probe run from before `J`
through it; ② runs after both captures have stopped (`pkill -x tcpdump` stops every capture, so
an on-series' capture cannot start before ③'s stops); the handover comes after `rlx0`'s twelve
series, and `rlx0` is not re-opened.

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

A **bracket** is the board read `<name>-R` (card 2's:
`sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic`)
between a host read just before it (`-P`, `HP`: the adapter's `rx_packets` and `tx_packets`,
the host's ICMP line) and one just after it (`-H`, `HN` and the kernel log's window). `brdelta`
1.2 prints per pair of brackets the driver's `n_tx`, `n_recov_fire`, `n_tx_stop`, `n_rx`, the
CPU port's `c` (`CRCAlignErr`), `j`, `f`, `d` (`JabberErr`, `FragErr`, `Drop`), port 3's output
`o` and input, `ident … k` (K = o − (c − j − f − d)), `hbound … within`, `path … covered` and
`fault jfd`; it reads a 1.4 page (its self-test reads block 46's, which is 1.4's). **W** is the
number of frames the host received from `rlx0` since ③'s capture started, before `J`: pcapwin's
record index at a host read (§ 3.3). A **series** is `P2`'s ICMP — 20 echoes at 50 ms at each
of 56, 256, 512, 1,024 and 1,472 B, one `ping -q` per size — and its reading is each size's
`rtt min/avg/max/mdev` line. The **width** is card B's (`bench/2026-09-25`'s card) § 3.4 rule,
as `w1width` states it.

### 3.1 The premise, tested in every series bracket (P0)

* **P0.** At every pair of consecutive brackets in `I-R` and `I-E` (the first pair of each arm
  from `B-AC0-R` and `E-00-R`): **(a)** `k 0`; **(b)** `within yes`; **(c)** `covered yes` (a
  gate: every echo request the host sent reached port 3). (a) on `eth4` rests on block 45's
  `eth4` bracket, `c` = `o` = 16,215 with `j`/`f`/`d` 0 (量 `notes/nic-driver.md` § 26.2) — one
  bracket, at `iperf3`'s and `ping`'s lengths, so `I-E` is the first reading of k under the
  vendor's driver at the `D5a` lengths and the first through `brdelta` — and on 1.4 on block
  46's 76 of 76 brackets (`notes/nic-driver.md` § 26). **What a failure voids**, card 2's rule:
  (a) failing by K frames voids that bracket's stage chain, and a single counter's threshold
  verdict only where K could carry it across; (b) failing voids that bracket's host side; (c)
  failing is § 6's (`NET-124`), never read as a board fault. Nothing outside the bracket is
  voided, and a series' own `ping` statistics never are.

### 3.2 The boot and the maps (P1)

* **P1.** `A1-CATCH` is a cold catch (`C-8`'s one space); `A1Q` passes `looprun`'s gates and
  its round reaches `rlxfw`'s prompt with `RLXFW-ID0=A2C56BC8` (量 block 46's `R1Q-boot`);
  `A1-PS` shows `/bin/sh` as PID 1; `A1-MB0` and `A1-MB1` read the map digest `0927be41…` with
  its one `DIFFER` in group 0 and 31 the same (量 block 46's and block 48's); `A1-NW0` and
  `A1-NW1` read `n_writes 0`. **Refuted by** another digest or group line (flash moved since
  block 48), or `n_writes` other than 0: the owner is told before anything else is read.

### 3.3 ③ — the two `NET109` rows in their own shape

讀 `docs/boot-time-d3-list.tsv`: `NET109|crcalignerr` is *the CPU port's `CRCAlignErr` at
`P1-AC0`* and `NET109|p3egress` *port 3's egress unicast packets at `P1-AC0`*, each an absolute
value read once on a healthy fresh boot, 294 in seating A; the rows were redefined as the
per-echo identity (`41bf452`), and `notes/nic-driver.md` § 26.5 scored that on block 46 four
ways without a single "met" and asked for a reading fixed before the next score, on the boot
shape the rows were defined on. This is that reading. `B-AC0-R` is the one read: after the
probe's stop (`A1-HPX`), with nothing typed between, between `B-AC0-P` and `B-AC0-H`; ③'s
capture (`W-TCPE`, from before `J`, every frame from `rlx0`'s address) is stopped right after,
at `W-TCPX`, whose two host reads anchor pcapwin's record order (`W-EORD`); `W-EWALL` counts
the whole capture's destinations; `W3` scores.

* **P2, the boot shape, defined now.** *Healthy fresh boot* = at `B-AC0-R`, absolute:
  `JabberErr`, `FragErr` and `Drop` 0 at the CPU port; the driver's last dump `n_recov_fire 0`,
  `n_tx_stop 0`, `tx_stopped 0`; and the first liveness gate after it (`R-S01-L`) 4 of 4 (if it
  does not run, P2 is undetermined and ③ is not scored). 推 healthy: every frame the board sends
  before `B-AC0-R` is an echo reply of 98 B or an ARP frame of 60 B (its replies to the host,
  and its own requests), clean under `M1`-cover8; the one 1.4 stall a liveness gate has met so
  far held a 78-B frame, a length the rule calls wrong, in its engine-owned slots (量
  `notes/nic-driver.md` § 26.4, § 27.9). **If it is not healthy, ③ is not scored on this boot**
  — a reading of why, never a miss of the rows.
* **P3, the readings, one identity per row.** With W_P and W_H the record indices at `B-AC0-P`
  and `B-AC0-H` (`w3`'s `w at` line), B and M the broadcast and multicast destinations among
  W's frames: **`NET109|crcalignerr`** is decided by c = W + j + f + d (`w3`'s
  `row crcalignerr`), 推 with j = f = d = 0, so c = W; **`NET109|p3egress`**, as the row was
  measured — port 3's unicast egress — is decided by u = W − B − M (`w3`'s
  `row p3egress-unicast`), 推 M = 0. Beside them, a reading that decides no row: port 3's whole
  egress, unicast + multicast + broadcast, o = W (`w3`'s `row p3egress`), the absolute form of
  P0 (b).
* **P3's exactness, and what refutes it.** 推 W_P = W_H: the board sends nothing across its own
  read, because after the probe's stop `A1-HPX` waits 12 s before `B-AC0-P`, longer than the
  board's own ARP timers can keep it sending — 讀 `arp.c` and `neighbour.c`, the vendor drop's
  own files (no `rlxfw` mark, host-compat patch or file of its own touches `net/` at `66ddb93`,
  `p2q`'s recipe, or at `92aeaa8`, `r6b2q`'s, whose staged copies the `cardnum` rows read, each
  check with its control; and those copies equal the drop's at the commit it was cloned at:
  `src43a.out`): an entry left in DELAY waits `delay_probe_time`, 5 s, then in PROBE sends at
  most `neigh_max_probes`, which in PROBE counts only `ucast_probes`, 3 unicast probes
  `retrans_time` (1 s) apart, so its last probe goes before 5 + 3 × 1 = 8 s — and the host's
  own entry for the board settles inside the same 12 s (推: the same timers' defaults on the WSL
  kernel). 推 the anchor ok (the capture dropped nothing, and the host's `rx_packets` did not
  move across the stop), so each row is `exact`. **Refuted by** a row that `misses`: the
  absolute counters did not start with the board's first frame (the rows' premise, 推 on
  seatings A and B and on block 46's `A1-00-R`, where every counter read 0 on a boot the board
  had not yet sent on), or port 3 sent a frame the host adapter did not count, or the CPU port
  counted a frame port 3 did not send. A `bounded` row (W_P < W_H) is scored against its
  interval and marked so. An anchor that is void scores nothing (`w3` exit 3).
* **What ③ is decided as.** A row whose deciding identity holds `exact` on this healthy boot is
  **met**, closing its part of `D3-MISS` ③: the row is the identity the record says it stands
  for, read in its own shape. A row that holds only `bounded` is **not met and not refuted**:
  it stays open with its interval. A row that misses stays open with its reading. If P2 is not
  healthy, or the anchor is void, ③ moves to the next cold quiet boot a card plans.

### 3.4 ① — the width on RAW, n = 1, a third calendar day

The frozen list's `D8|width|quiet|cold` is `stable` on seating A's n = 1 (0.187804 s raw,
0.091986 s corrected, 2.04× apart), so no seating-B value could hit both columns (`CLK-48`);
the record's experiment is a third day on RAW against seating B. Seating B's two cold quiet
widths, 量 `notes/boot-time.md` § 8.7 and re-derived here by `w1width` (its self-test's C1 and
C2): `P2Q-r01` 0.094550 s (k 2, by the ledger) and `P3Q-r01` 0.114647 s (k 2, by the frames;
0.1031 s frame to `N-NDOPEN`).

* **P4.** The cold quiet boot's width by card B's rule lies inside seating B's quiet range,
  **[0.081153, 0.134960] s** (its eight quiet boots, cold and warm: no source separates the two
  for this quantity, which is the host's ARP phase against `N-NDOPEN`, `notes/boot-time.md`
  § 8.7), with k 2 and the lower edge `N-NDOPEN` (seating B: 6 of 6 framed quiet boots answered
  at #2), and no void rule fired; with the frames, the answered who-has on the wire at place 2.
  **The base rate, stated now**: a new draw from seating B's own distribution lies inside its
  8-sample range with probability 7/9, so *inside* is weak evidence and *outside* is the
  informative outcome — the host's ARP phase against the board moved between the days.
  **Refuted by** a width outside the range, or k other than 2 (at k 3 the bracket is
  [`N-NDOPEN`, #3], up to 1.028 s wide: another quantity). A void rule firing (the loader's
  address valid in the probe's neighbour record, no lower edge, or the answered broadcast not
  on the wire) leaves ① unmeasured on this boot, reported as that. A reading beside it: whether
  the width lies inside seating B's two cold widths ±10 %, [0.085095, 0.126112] s (3 of seating
  B's 8 quiet widths do).
* **P5, the clock.** `Z0-HCG` permits (`AGREE … vacuous`, and
  `steps: timerfd 0, agreed with the rows 0, NO STEPS`). The guard has been seen both ways on
  this host: in seating B it refused once (`strong`: the kernel's clock 8.34 % fast after the
  workstation woke) and permitted 12.7 minutes later as `Z0-HCG2` (量
  `bench/2026-09-25/Z0-HCG.log`, `Z0-HCG2.log`, `CORRECTIONS-block44.md` § 1); both logs' step
  lines read `timerfd 0, agreed with the rows 0, NO STEPS`, so the lengthened gate permits
  both. **The step detector's positive control.** A stepless run's report says its own zero is
  uncontrolled — no live step happened, so nothing showed the detector would see one — and
  block 44's gate read only the timerfd's count. So at the desk, and again in `R0-ST` before
  power, `hcstepctl.py` plants clock logs with `hostclock`'s own planter and runs
  `tools/hostclock.py report` on each, the command `Z0-HCG` and `Z9-HCR` run: a +1.4 s step in
  both the 1 Hz rows and the timerfd's rows reads `timerfd 1, agreed with the rows 1, AGREE`
  and controlled; the step in the rows alone (a timerfd that missed it), or a timerfd step the
  rows never show, reads `DISAGREE` and exits 1; no step reads `NO STEPS`. `Z0-HCG`'s step gate
  is `hcstepctl`'s own constant; it refuses the first three and permits the last, while block
  44's shorter gate text permits the rows-only step (its exit code refused it there). Each
  mutant of the detector and of the gate in its mutation run turns the control red
  (`hcstepctl-mutate.out`). On this host's kernel the two detectors also saw two live steps,
  +0.723937 s (`FW-129`) and +0.551906 s (the 109th segment, `notes/boot-time.md`). Over the
  press, 推 no `step` row (seating B: 0 in 11,375 rows, `notes/boot-time.md` § 8.2) and a net
  kernel rate — (tick − 10,000)·100 + `freq`/65,536 ppm — inside ±100 ppm from `J` − 5 s to the
  first reply (seating B: −81.5…+97.8 ppm after its first minutes, save four ~1 s dips to
  −120.9, `notes/boot-time.md` § 8.2); the tick itself is not predicted to read 10,000 (it
  never did in seating B, so block 44's 推 that it would is not repeated). 100 ppm moves the
  10.88 s from `J` to seating B's later cold quiet first reply by 1.088 ms, under the
  reconstruction's ±14–28 ms (`notes/boot-time.md` § 8.7), so ①'s width does not rest on it
  (推). **Refuted by** the guard refusing twice (no power, § 6) or a step inside `J` − 5 s … the
  first reply (① then unmeasured on this boot); a window beyond ±100 ppm is named, and every
  host-timer interval in it published as affected.
* **What ① is decided as, fixed now.** `D3-MISS` ① is the list's defect whatever the width
  reads: the row was `stable` on seating A's n = 1, on a slow clock (`CLK-48`). It is re-scored
  by the list's own stability rule — the largest |value/median − 1| under 0.10, a rule
  `arith43a` reproduces on two of the list's rows — over the three cold widths on RAW, seating
  B's two and this one. By that rule seating B's pair alone reads 0.0961 (stable), and the
  three stay stable only if this width lies in **[0.104225, 0.105055] s**, computed now on a 1
  µs grid: inside that window the row stays `stable` on n = 3 on two days; outside it — 推, a
  window under 1 ms against a quantity seating B's quiet boots spread over 53.8 ms — the row is
  reclassified not stable. **The rule is applied only to a width read at k 2 with no void rule
  fired**: at k other than 2 the reading is another quantity (P4), so it does not enter the
  three-point spread, ① is not re-scored on this boot and the row stays open, the reading
  published; a void rule leaves ① unmeasured (P4). At k 2 with no void, either way the row
  stops being open, and the width, P4's reading and the frames are published with it.

### 3.5 ② — the rtt, with the host capture on and off, on both drivers of one boot

Twelve series on each interface in the order 011001100110 (0 off, 1 on; ABBA from off, so a
drift linear in the series' order weighs both states alike — and in time only to within an
on-series' two extra cells, `-T` and `-X`, which lengthen its slot by about 1.5 s: the `-X`'s
`sleep 1` and the `-T`'s start, the estimate's 0.5 s, a guess). An on-series runs inside `P2`'s
text capture (`TDT`, the capture that ran around seating A's `P3-ICMP` and seating B's
`P1-ICMP` and `P3-ICMP`), started just before its `-C0` and stopped just after its `-C1`; an
off-series with no `tcpdump` running. `rttseries` 1.1 counts a series only if all five sizes
read 20 of 20, both `pgrep` counts read its planned state, its liveness gate read 4 of 4 and
its bracket pair `covered yes` and `jfd 0` (§ 0 ⑨); per size, per state, the median of the
series' averages and mdevs; E = median(on) − median(off); and U = #(on > off) over the 36
pairs, ties a half. **The test, fixed now**: `raises` iff U ≥ 31, `lowers` iff U ≤ 5,
`unresolved` otherwise — a two-sided 5 % Mann-Whitney test, 6 against 6, `rttseries`
recomputing lo and hi exactly for the counting n (5 against 6: 3 and 27; 5 against 5: 2 and
23); `unmeasured` if either state has fewer than 5 counting series (`D3-MISS` ② asks for at
least five of each). **With no effect at any size**, one size reads `lowers` with probability
19/924 = 0.021 (6 against 6, no ties), so a prediction refuted by `lowers` at any of the five
sizes (P8, P9) is refuted falsely with probability at most 0.103 whatever the sizes'
dependence, 0.099 were they independent — they share one boot and one path, so they are not.
The rule stands as written; this is the chance that it refutes a prediction that is true.

| size | seating A, uncaptured P1, P2 (ms) | off band (P6) | seating A, captured P3 | on band (P6) | D3 row, A median and the series it is (P7) | seating B, uncaptured P2 | seating B, captured P1, P3 |
|---|---|---|---|---|---|---|---|
| 56 B | 1.586, 1.516 | 1.3644–1.7446 | 1.815 | 1.6335–1.9965 | — (not a stable row) | 1.723 (inside; +8.6 % of the A median) | 2.305, 1.401 (median 1.8530, inside) |
| 256 B | 1.367, 1.518 | 1.2303–1.6698 | 1.641 | 1.4769–1.8051 | avg 1.518 (P2) | 1.546 (inside; +1.8 % of the A median) | 1.792, 1.933 (median 1.8625, above) |
| 512 B | 1.736, 1.64 | 1.4760–1.9096 | 1.618 | 1.4562–1.7798 | avg 1.64 (P2) | 1.685 (inside; +2.7 % of the A median) | 2.128, 1.743 (median 1.9355, above) |
| 1024 B | 2.03, 2.124 | 1.8270–2.3364 | 2.086 | 1.8774–2.2946 | avg 2.086 (P3, captured) | 1.889 (inside; -9.4 % of the A median) | 2.455, 2.020 (median 2.2375, inside) |
| 1472 B | 2.052, 2.252 | 1.8468–2.4772 | 2.139 | 1.9251–2.3529 | avg 2.139 (P3, captured), mdev 0.476 (P3, captured) | 2.364 (inside; +10.5 % of the A median) | 2.720, 2.399 (median 2.5595, above) |

The references, each named: seating A's three rlxfw series per size are its `P1`, `P2` and `P3`
in the list's order; `P3` ran inside the host's capture and `P1` and `P2` did not (`NET-121`).
So the **off band** is `P1`–`P2` widened by ±10 % and the **on band** is `P3` ±10 %; seating
B's own series are readings beside them, not references.

* **P6, the before-column (`rlx0`).** (a) At every size the off-state median lies inside the
  off band — 推 from seating B's one uncaptured series, inside at all five. (b) At 256 and 1,472
  B the on-state median lies **above** the on band — 推 from seating B's two captured series,
  whose median lay above it at both (the table's last column; `NET-121`: `P3` against `P3`,
  both captured, +18.1 % and +12.3 %). **Refuted by** (a) a size whose off median is outside
  its band, or (b) an on median inside or below the on band at 256 or 1,472 B.
* **P7, the frozen rows re-scored (`rlx0`, capture off).** The five stable `D5a` rows by `D3`'s
  own rule, the off-state median within ±10 % of the A median. Each A median is one of seating
  A's three series (the table): 256 and 512 B avg are P2's, uncaptured, so P7 is like against
  like there and its score is the row's re-score; 1,024 B avg and 1,472 B avg and mdev are
  P3's, **captured** (`NET-121`), so P7 compares this boot's uncaptured median with a captured
  one there — a reading against a captured reference, which decides no row (§ 3.5's decision).
  推 **within** at 256, 512 and 1,024 B (seating B's uncaptured series read +1.8, +2.7 and −9.4
  % against the A median); **no prediction of the side** at 1,472 B avg and mdev — seating B's
  uncaptured series read +10.5 % and +16.6 %, and a 20-echo mdev's own sampling error is 推
  about 16 % (`NET-121`'s own 推; 1/√(2(n − 1)) = 0.162 for n = 20), wider than the band.
  **Refuted by** 256, 512 or 1,024 outside ±10 %.
* **P8, the capture's effect within the boot (`rlx0`).** 推 at no size `lowers`. Between the
  days seating B's captured series moved +13.5 and +19.7 % against seating A at 256 and 1,472 B
  and its uncaptured one +7.2 and +9.9 % (`NET-121`, each against seating A's series in the
  same state), so a capture effect of a few percent is what the record suggests; seating A's
  series spread (the list's `spread` column: 14.4 % at 56 B, 2.7–9.9 % at the others) and six
  series a state make `unresolved` likely even if the effect is real — the test's power is low,
  and the card says so rather than widening anything. **Refuted by** `lowers` at any size
  (falsely, with no effect anywhere, with probability at most 0.103: the test above).
* **P9, the capture's effect within the boot (`eth4`, the vendor's driver).** A first reading
  on this kernel (no series exists: seating B's `P1-EPING` was 4 echoes, and the vendor
  firmware's series ran another kernel). 推 at no size `lowers`, and at no size do the two
  interfaces resolve in opposite directions (a host-side effect acts on both alike). **Refuted
  by** either (the first falsely, with no effect anywhere, with probability at most 0.103, as
  P8).
* **P10, 1.4 at every `D5a` length.** At every `rlx0` series bracket `fault jfd 0` and `k 0`,
  and every size of every `rlx0` series 20 of 20. 推: `M1`-cover8 (`NET-129`) calls every frame
  here clean (the table below), though it does not explain every stack loss — block 47's E2 at
  1.4 lost the first 29 requests at 276 B and the first 62 at 1,513 B, lengths it calls clean
  (讀 card B50 § 0 ②, which puts them down to the previous length's state on the same ring, 推);
  on a ring re-armed for each length, 1.4 read 20 of 20 with `j` = `f` = `d` = 0 at 60, 276,
  1,513 and 1,514 B (量 block 48's `SL` brackets, `notes/nic-driver.md` § 27.4, P6), and this
  boot sends no wrong length at all; seatings A and B lost none of their rlxfw echoes at these
  sizes (量 their 30 size-series, 600 echoes, every one received: `bench/2026-09-23` and
  `bench/2026-09-25`, `P1`–`P3-ICMP`). Block 48's one 1.4 stall held a 66-B frame (clean)
  beside a 78-B one (wrong) in its engine-owned slots (§ 26.4), so a stall is not excluded.
  **Refuted by** `jfd` ≥ 1 in any `rlx0` series bracket: the CPU port counted a wrong frame at
  F mod 8 = 2 or 4, and `M1`-cover8 does not cover the stack's frames here. A loss with `jfd 0`
  is a reading (host side and board side not separated) and voids its series, as `jfd` ≥ 1
  does.

| frame | ping `-s` | length F | F mod 8 | M1-cover8 at 1.4 |
|---|---:|---:|---:|---|
| liveness | 18 | 60 | 4 | clean |
| probe | 56 | 98 | 2 | clean |
| series | 56 | 98 | 2 | clean |
| series | 256 | 298 | 2 | clean |
| series | 512 | 554 | 2 | clean |
| series | 1024 | 1066 | 2 | clean |
| series | 1472 | 1514 | 2 | clean |
| ARP request or reply (padded) | — | 60 | 4 | clean |

* **What ② is decided as, fixed now, on `rlx0`** — by P6 at 256 and 1,472 B, the sizes of
  `D3-MISS` ②'s three rows (`256|avg`, `1472|avg`, `1472|mdev`); the cases are read in this
  order, and every outcome lands in exactly one:
  * **(iv)**, read first: fewer than five counting series in either state — ② is unmeasured on
`rlx0` on this boot, whatever `rttseries` prints beside it; (i)–(iii) and P7 are read only when
both states count at least five.
  * **(i)** off inside the off band at both, and on above the on band at both: without the
capture this day reproduces seating A, and with it seating B's shift recurs. The rows are
re-scored with the capture off, like against like, and two of them are closed. `256|avg` is
closed on its P7 score against its A median, P2's (uncaptured), which the case does not decide:
the off band reaches below P7's, from P1's 1.367. `1472|avg` is scored against P6 (a)'s off
band, seating A's uncaptured P1–P2 ±10 %, because its A median is P3's (captured); an off
median inside that band at 1,472 B is this case's own entry condition, so the case itself is
that row's score and closes it as reproducing with the capture off — no reading inside (i) or
(ii) could score it otherwise — and its P7 score against the captured median is published
beside it, marked a captured reference. **Closed** records, for each of the two rows: this
boot's off-state median, the reference and band it was scored against, its verdict (`256|avg`
within or outside, `1472|avg` inside) and the case that closed it, so that row's part of
`D3-MISS` ② is decided by this reading, as `D5` asks, whatever `256|avg`'s verdict; it does not
record the between-day shift as explained. `1472|mdev`'s A median is P3's too, and its
statistic's own sampling error (推 about 16 %, P7) is wider than the band: its scores in both
states are published and it stays open. The captured state's between-day shift stays open
(`NET-121`) — this case shows it, it does not explain it — with the capture's within-boot
effect (P8) beside it.
  * **(ii)** off inside at both, and on inside or below the on band at either: the same
re-scoring and closing as (i), `1472|avg` again closed by the case's own entry condition; the
captured state did not reproduce seating B's shift on this boot, and that shift stays open
(`NET-121`).
  * **(iii)** off outside its band at 256 or 1,472 B, above or below: without the capture the
rtt is not seating A's — the shift is not the capture's — and the rows stay open as a
between-day change of the board's or the host's rtt, `NET-121` naming which still undetermined.
  `eth4`'s series decide nothing about the rows (they are `rlx0`'s): P9 is their reading. The
vendor-firmware series are ⊘ (§ 0 ①), as the amended `D3-MISS` row says.

### 3.6 The host path, the kernel log and `C-19`

* **P11 (`NET-124` 殘留, `NET-54` 殘留).** Every liveness gate 4 of 4 (24), both port-3 gates
  `LinkUp` on `PSRP3` and on `port_status`, every path gate `covered yes`, every kernel-log
  window `follower 1`, and the log clean of the three gated signatures before power (`urb -104`
  lines are not gated: block 47 read 302 with the board off). The host's `BUG` trace is counted
  per window beside the host's Δ`tx_packets`, a reading and not `NET-124`'s silent-state
  marker: block 47 counted it while the path worked and not before power (card 2's § 0). **If a
  liveness gate fails**, S1 classifies it from the board first (§ 6); the classification and
  every read of the episode are readings for `NET-124` 殘留 and `NET-54` 殘留, and branch a is also
  a reading beside `NET-67` 殘留 (a 1.4 stall at a clean length).
* **`C-19`**: `dmesgwin`'s `usb_disc`, `cp210x` and `ttyusb` per window; the desk counts
  console drops and every gap over a minute between console captures, as card 2's record did.

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck` refuses
the verbs (`FW-113`); every upload is `looprun`'s, which requires `00000000` read back from the
`AUTOBURN` word before it uploads; no vendor boot is typed. 🔴 **From the round to the
power-off, while the board runs a kernel, the console has no capture open only in § 0 ⑦ (ii)'s
host stretches inside an invocation — the longest 12.1 s nominally and 54.7 s with every echo
timed out, and none with the next board cell's cap over 69.7 s, under the bite's 83.8 s — and
outside an invocation for no more than about 30 s**: the press's command line ends with the
watch, and a watch holds it across every wait (§ 6, *The watch*); at the loader's prompt none
is opened; every other console capture ends on the loader's banner (§ 0 ⑦). 🔴 **The owner's
handshake** (§ 0 ⑥, § 6 *The owner's actions*): for every power-on and power-off the session
tells the owner and STOPS until the owner replies; only then does it open the catch (or the
power-off window) in the background, confirm from the transcript that the ESC-streaming cell is
running, and then tell the owner "catch open — power on now" (or "power off now"); the owner
acts only on that word. No count-to-five after the reply, and nothing physical happens between
the reply and the session's "now". 🔴 Every `--send` is at most 127 characters, holds no `$` and
no upper-case word. 🔴 **No gate reads a console mark** (`FW-47`; a `cardnum` row counts zero).
🔴 **No driver verb is typed**: 1.4's defaults throughout. 🔴 **No frame capture is printed**:
③'s is cut at 64 bytes, filtered to `rlx0`'s address, and read only by `pcapwin.py`; `P2`'s
text capture prints no address off its allowlist. 🔴 **No line of the host's kernel log reaches
`bench/`**: only `dmesgwin.py`'s counts. 🔴 No host cell prints a home path into `bench/`. 🔴 No
cell touches the reset button or the watchdog. 🔴 `rlx0` goes down only in `H-DOWN` and is not
re-opened (`NET-58`). 🔴 No step removes `/proc/rtl865x/`. 🔴 `sudo -n pkill -INT -x tcpdump`
stops every `tcpdump` on the host: `R0-TCPC` requires none before power, `W-TCPC` none after
③'s stop, and an on-series' `-X` none after its own. 🔴 Exactly one `dmesg` process, the
off-card follower, runs from before `I-0` to after `I-Z`. 🔴 `hostclock` never runs under
`sudo`, and every `--out` is a relative `bench/2026-09-27/…` path. 🔴 `timesyncd` is stopped
only for the seating: `Z9-TSD` starts it again whenever the seating ends. ⚠️ Off-card cells are
declared in `bench/2026-09-27/CORRECTIONS-block49.md` before they run, except those § 6
declares now with their text (each still logged there as it runs) and a power-off, which § 6
decides now.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-27 --skip S2,S3,S4 --recipe-override a2c56bc8 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`
`HPR` = `/usr/bin/python3 tools/hostprobe.py run`
`HCL` = `/usr/bin/python3 tools/hostclock.py`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 46's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets ; grep '^Icmp:' /proc/net/snmp` — the host read just before a board read
`PL <ip>` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 <ip>` — the liveness probe: 60-B frames, card 2's
`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done` — `P2`'s series, block 44's macro unchanged
`TDT` = `timeout 900 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or (arp and arp[6:2] = 1 and arp[18:4] = 0 and arp[22:2] = 0) or (arp and arp[6:2] = 2 and ((arp[8:4] = 0x02524c58 and arp[12:2] = 0x4657) or (arp[8:4] = 0x560a0101 and arp[12:2] = 0x01e8)))'` — `P2`'s text capture: block 44's filter, a longer cap
`TDE <f>` = `timeout 900 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s113/card43a/pcap/<f> ether src 02:52:4c:58:46:57` — ③'s capture, card 2's `TDE` with a shorter cap
`PWA <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py window /home/key/fwre-work/rebuild/s113/card43a/pcap/A.pcap --if enxfc19286184c9 --prev <prev>`
`PWO` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py order`
`DW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py window /home/key/fwre-work/rebuild/s113/card43a/host/dmesg-w.log --prev <prev>`
`BD` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py`
`RTS` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43a/rttseries.py`
`W3R` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43a/w3.py`
`W1W` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s113/card43a/w1width.py`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — card 2's, unchanged

A board read's longest silence is its `sleep 2`, and it ends on a pattern (`--until`) that also
matches the loader's banner; a stimulus cell's `--idle` is 3 and its payload has no `sleep`. A
series (`ICMP`) runs on the host and is a reading: its own statistics are what it measures.
Every `-H` and every liveness cell passes `dmesgwin` a `--prev` list (§ 6, *Chained
references*), so each window starts where the previous one on the path the press took ended.

### Before power — the pre-flight, the host, the checkers

```
CAP --out bench/2026-09-27/R0-PRE --seconds 3
HOST bench/2026-09-27/R0-PREC :: ls bench/2026-09-27/R0-PRE.log bench/2026-09-27/R0-PRE.timing bench/2026-09-27/R0-PRE.meta.json && cat bench/2026-09-27/R0-PRE.meta.json
HOST bench/2026-09-27/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-27/R0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9 ; uname -r
HOST bench/2026-09-27/R0-EVICT :: cat /proc/sys/net/ipv4/conf/enxfc19286184c9/arp_evict_nocarrier
HOST bench/2026-09-27/R0-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-27/R0-DW0 :: DW none
HOST bench/2026-09-27/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3 ; FL 10.1.1.4
HOST bench/2026-09-27/R0-PCAP :: mkdir -p /home/key/fwre-work/rebuild/s113/card43a/pcap && find /home/key/fwre-work/rebuild/s113/card43a/pcap -name '*.pcap' | wc -l
HOST bench/2026-09-27/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ; sha256sum < /home/key/fwre-work/rebuild/s113/shared/s1class.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/rttseries.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/w3.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/w1width.py ; sha256sum < /home/key/fwre-work/rebuild/s111/netup/common.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/arith43a.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/hcstepctl.py ; sha256sum < /home/key/fwre-work/rebuild/s109/card/runblock.py ; sha256sum < /home/key/fwre-work/rebuild/s113/card43a/line43a.sh
HOST bench/2026-09-27/R0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/shared/s1class.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43a/rttseries.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43a/w3.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43a/w1width.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s113/card43a/hcstepctl.py --self-test
HOST bench/2026-09-27/R0-H :: HN
```

* `R0-PRE` — the pre-flight with the board off, judged by its three artefacts and ~3.08 s,
  never its exit code (`R0-PREC`). `R0-EVICT` — the adapter's `arp_evict_nocarrier` (block 44's
  `Z1-EVICT`: 1 there, so each carrier loss evicts the host's entry for 10.1.1.3), a reading ①
  rests on. `R0-SUM` — every checker this card runs from outside `tools/` at its pinned digest;
  `R0-ST` — each one's self-test, all passing, the lines pinned in `cardnum`.

### The clock log, and its guard (before power)

```
HOST& bench/2026-09-27/Z0-HC :: HCL run --out bench/2026-09-27/Z0-HC --seconds 18000 --no-sntp --no-windows
```

```
HOST bench/2026-09-27/Z0-HCW :: HCL wait bench/2026-09-27/Z0-HC --timeout 20
HOST bench/2026-09-27/Z0-TSD :: sudo -n systemctl stop systemd-timesyncd ; systemctl show -p ActiveState systemd-timesyncd
HOST bench/2026-09-27/Z0-HCG :: sleep 100 ; HCL run --out bench/2026-09-27/Z0-HCG --seconds 60 --no-sntp --no-windows ; HCL report bench/2026-09-27/Z0-HCG
```

* `Z0-HC` — `hostclock` for the whole seating, started before `timesyncd` stops so its first
  rows are the host as it was; `Z9-HCX` stops it. `Z0-HCW` — the logger alive, or `timesyncd`
  is not touched. `Z0-TSD` — `ActiveState=inactive`. `Z0-HCG` — block 44's guard with its step
  gate lengthened (§ 3.4 P5): `AGREE … vacuous` and
  `steps: timerfd 0, agreed with the rows 0, NO STEPS`, or no power.

### The press — the catch, the captures and the probe, the round, ③, the opening map

```
CAP --out bench/2026-09-27/A1-CATCH --esc-after 360 --esc-period 0.002 --until '<RealTek>' --seconds 380
HOST bench/2026-09-27/A1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST& bench/2026-09-27/W-TCPD :: TDT
HOST& bench/2026-09-27/W-TCPE :: TDE A.pcap
HOST& bench/2026-09-27/A1-HP :: HPR --out bench/2026-09-27/A1-HP --target 10.1.1.3 --seconds 900 --icmp --icmp-interval 0.05 --neigh
HOST bench/2026-09-27/A1Q :: LR --cell A1Q QIMG --iterations 1
HOST bench/2026-09-27/A1-HPX :: pkill -INT -f 'A1-HP --target' ; sleep 12 ; tail -n 1 bench/2026-09-27/A1-HP.events
HOST bench/2026-09-27/B-AC0-P :: HP
CAP --out bench/2026-09-27/B-AC0-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/B-AC0-H :: HN ; DW bench/2026-09-27/R0-DW0.log
HOST bench/2026-09-27/W-TCPX :: HN ; sudo -n pkill -INT -x tcpdump && sleep 1 ; HN
HOST bench/2026-09-27/W-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/W-EWALL :: PWA none
HOST bench/2026-09-27/W-EORD :: PWO /home/key/fwre-work/rebuild/s113/card43a/pcap/A.pcap --if enxfc19286184c9 --tcpdump bench/2026-09-27/W-TCPE.log --stop bench/2026-09-27/W-TCPX.log bench/2026-09-27/B-AC0-P.log bench/2026-09-27/B-AC0-H.log bench/2026-09-27/W-TCPX.log
HOST bench/2026-09-27/W3 :: W3R read --board bench/2026-09-27/B-AC0-R.log --order bench/2026-09-27/W-EORD.log --wall bench/2026-09-27/W-EWALL.log
CAP --out bench/2026-09-27/A1-PS --send 'ps' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-27/A1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27/A1-MB0 :: MB bench/2026-09-27/A1-M0
CAP --out bench/2026-09-27/A1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
```

* `A1-CATCH` — the press's first cell, ESC from its start for up to 360 s, ending at the
  loader's first prompt `<RealTek>`, which the cold boot prints after its banner and `C-8`'s
  line (量 block 48's `R1-CATCH`), so the chain goes on once the press is caught: the session
  starts the press's command line only after the owner's reply, confirms from its transcript
  that this cell streams, and only then tells the owner "catch open — power on now", with the
  catch's 360 s, so the press lands inside its stream (the owner's handshake, § 6 *The owner's
  actions*). `A1-FL` — the host's entries for 10.1.1.1 and 10.1.1.3 flushed before `looprun`
  (its `S5c` prints the first; ① needs no cached entry for the second).
* `W-TCPD`, `W-TCPE`, `A1-HP` — `P2`'s text capture (①'s frames), ③'s capture and the probe
  (①'s ledger, `--icmp` at 50 ms and `--neigh`), each awaited for its start signal, all from
  before `J`.
* `A1Q` — one round of `p2q` at the caught prompt: a cold quiet boot; `looprun` holds it 2.5 s
  past the prompt. `A1-HPX` — the probe stopped with SIGINT, then 12 s in which no cell sends
  anything (§ 3.3); its last line is `stop`.
* `B-AC0-P`, `B-AC0-R`, `B-AC0-H` — ③'s one read (§ 3.3); nothing is typed between the probe's
  stop and it.
* `W-TCPX` — both captures stopped, the host's counters read on both sides of the stop;
  `W-TCPC` — none running. `W-EWALL`, `W-EORD` — the whole capture's destinations and its
  record-order anchor over `B-AC0-P`, `B-AC0-H` and the stop; `W3` — ③'s three rows.
* `A1-PS`, `A1-M0`, `A1-MB0`, `A1-NW0` — the shell's shape, the opening map and `n_writes`
  (P1): console only, no traffic.

### ② on `rlx0`

```
CAP --out bench/2026-09-27/R-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27/R-S01-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/B-AC0-H.log
HOST bench/2026-09-27/R-S01-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S01 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S01-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S01-P :: HP
CAP --out bench/2026-09-27/R-S01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S01-H :: HN ; DW bench/2026-09-27/R-S01-L.log
HOST bench/2026-09-27/R-S01-D :: BD pair bench/2026-09-27/B-AC0-R.log,bench/2026-09-27/X-B-AC0-R.log bench/2026-09-27/R-S01-R.log,bench/2026-09-27/X-R-S01-R.log --host bench/2026-09-27/B-AC0-H.log bench/2026-09-27/R-S01-H.log --pre bench/2026-09-27/B-AC0-P.log bench/2026-09-27/R-S01-P.log
HOST bench/2026-09-27/R-S02-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S01-H.log
HOST& bench/2026-09-27/R-S02-T :: TDT
HOST bench/2026-09-27/R-S02-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S02 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S02-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S02-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S02-P :: HP
CAP --out bench/2026-09-27/R-S02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S02-H :: HN ; DW bench/2026-09-27/R-S02-L.log
HOST bench/2026-09-27/R-S02-D :: BD pair bench/2026-09-27/R-S01-R.log,bench/2026-09-27/X-R-S01-R.log bench/2026-09-27/R-S02-R.log,bench/2026-09-27/X-R-S02-R.log --host bench/2026-09-27/R-S01-H.log bench/2026-09-27/R-S02-H.log --pre bench/2026-09-27/R-S01-P.log bench/2026-09-27/R-S02-P.log
HOST bench/2026-09-27/R-S03-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S02-H.log
HOST& bench/2026-09-27/R-S03-T :: TDT
HOST bench/2026-09-27/R-S03-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S03 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S03-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S03-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S03-P :: HP
CAP --out bench/2026-09-27/R-S03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S03-H :: HN ; DW bench/2026-09-27/R-S03-L.log
HOST bench/2026-09-27/R-S03-D :: BD pair bench/2026-09-27/R-S02-R.log,bench/2026-09-27/X-R-S02-R.log bench/2026-09-27/R-S03-R.log,bench/2026-09-27/X-R-S03-R.log --host bench/2026-09-27/R-S02-H.log bench/2026-09-27/R-S03-H.log --pre bench/2026-09-27/R-S02-P.log bench/2026-09-27/R-S03-P.log
HOST bench/2026-09-27/R-S04-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S03-H.log
HOST bench/2026-09-27/R-S04-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S04 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S04-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S04-P :: HP
CAP --out bench/2026-09-27/R-S04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S04-H :: HN ; DW bench/2026-09-27/R-S04-L.log
HOST bench/2026-09-27/R-S04-D :: BD pair bench/2026-09-27/R-S03-R.log,bench/2026-09-27/X-R-S03-R.log bench/2026-09-27/R-S04-R.log,bench/2026-09-27/X-R-S04-R.log --host bench/2026-09-27/R-S03-H.log bench/2026-09-27/R-S04-H.log --pre bench/2026-09-27/R-S03-P.log bench/2026-09-27/R-S04-P.log
HOST bench/2026-09-27/R-S05-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S04-H.log
HOST bench/2026-09-27/R-S05-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S05 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S05-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S05-P :: HP
CAP --out bench/2026-09-27/R-S05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S05-H :: HN ; DW bench/2026-09-27/R-S05-L.log
HOST bench/2026-09-27/R-S05-D :: BD pair bench/2026-09-27/R-S04-R.log,bench/2026-09-27/X-R-S04-R.log bench/2026-09-27/R-S05-R.log,bench/2026-09-27/X-R-S05-R.log --host bench/2026-09-27/R-S04-H.log bench/2026-09-27/R-S05-H.log --pre bench/2026-09-27/R-S04-P.log bench/2026-09-27/R-S05-P.log
HOST bench/2026-09-27/R-S06-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S05-H.log
HOST& bench/2026-09-27/R-S06-T :: TDT
HOST bench/2026-09-27/R-S06-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S06 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S06-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S06-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S06-P :: HP
CAP --out bench/2026-09-27/R-S06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S06-H :: HN ; DW bench/2026-09-27/R-S06-L.log
HOST bench/2026-09-27/R-S06-D :: BD pair bench/2026-09-27/R-S05-R.log,bench/2026-09-27/X-R-S05-R.log bench/2026-09-27/R-S06-R.log,bench/2026-09-27/X-R-S06-R.log --host bench/2026-09-27/R-S05-H.log bench/2026-09-27/R-S06-H.log --pre bench/2026-09-27/R-S05-P.log bench/2026-09-27/R-S06-P.log
HOST bench/2026-09-27/R-S07-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S06-H.log
HOST& bench/2026-09-27/R-S07-T :: TDT
HOST bench/2026-09-27/R-S07-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S07 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S07-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S07-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S07-P :: HP
CAP --out bench/2026-09-27/R-S07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S07-H :: HN ; DW bench/2026-09-27/R-S07-L.log
HOST bench/2026-09-27/R-S07-D :: BD pair bench/2026-09-27/R-S06-R.log,bench/2026-09-27/X-R-S06-R.log bench/2026-09-27/R-S07-R.log,bench/2026-09-27/X-R-S07-R.log --host bench/2026-09-27/R-S06-H.log bench/2026-09-27/R-S07-H.log --pre bench/2026-09-27/R-S06-P.log bench/2026-09-27/R-S07-P.log
HOST bench/2026-09-27/R-S08-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S07-H.log
HOST bench/2026-09-27/R-S08-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S08 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S08-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S08-P :: HP
CAP --out bench/2026-09-27/R-S08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S08-H :: HN ; DW bench/2026-09-27/R-S08-L.log
HOST bench/2026-09-27/R-S08-D :: BD pair bench/2026-09-27/R-S07-R.log,bench/2026-09-27/X-R-S07-R.log bench/2026-09-27/R-S08-R.log,bench/2026-09-27/X-R-S08-R.log --host bench/2026-09-27/R-S07-H.log bench/2026-09-27/R-S08-H.log --pre bench/2026-09-27/R-S07-P.log bench/2026-09-27/R-S08-P.log
HOST bench/2026-09-27/R-S09-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S08-H.log
HOST bench/2026-09-27/R-S09-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S09 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S09-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S09-P :: HP
CAP --out bench/2026-09-27/R-S09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S09-H :: HN ; DW bench/2026-09-27/R-S09-L.log
HOST bench/2026-09-27/R-S09-D :: BD pair bench/2026-09-27/R-S08-R.log,bench/2026-09-27/X-R-S08-R.log bench/2026-09-27/R-S09-R.log,bench/2026-09-27/X-R-S09-R.log --host bench/2026-09-27/R-S08-H.log bench/2026-09-27/R-S09-H.log --pre bench/2026-09-27/R-S08-P.log bench/2026-09-27/R-S09-P.log
HOST bench/2026-09-27/R-S10-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S09-H.log
HOST& bench/2026-09-27/R-S10-T :: TDT
HOST bench/2026-09-27/R-S10-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S10 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S10-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S10-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S10-P :: HP
CAP --out bench/2026-09-27/R-S10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S10-H :: HN ; DW bench/2026-09-27/R-S10-L.log
HOST bench/2026-09-27/R-S10-D :: BD pair bench/2026-09-27/R-S09-R.log,bench/2026-09-27/X-R-S09-R.log bench/2026-09-27/R-S10-R.log,bench/2026-09-27/X-R-S10-R.log --host bench/2026-09-27/R-S09-H.log bench/2026-09-27/R-S10-H.log --pre bench/2026-09-27/R-S09-P.log bench/2026-09-27/R-S10-P.log
HOST bench/2026-09-27/R-S11-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S10-H.log
HOST& bench/2026-09-27/R-S11-T :: TDT
HOST bench/2026-09-27/R-S11-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S11 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S11-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S11-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S11-P :: HP
CAP --out bench/2026-09-27/R-S11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S11-H :: HN ; DW bench/2026-09-27/R-S11-L.log
HOST bench/2026-09-27/R-S11-D :: BD pair bench/2026-09-27/R-S10-R.log,bench/2026-09-27/X-R-S10-R.log bench/2026-09-27/R-S11-R.log,bench/2026-09-27/X-R-S11-R.log --host bench/2026-09-27/R-S10-H.log bench/2026-09-27/R-S11-H.log --pre bench/2026-09-27/R-S10-P.log bench/2026-09-27/R-S11-P.log
HOST bench/2026-09-27/R-S12-L :: FL 10.1.1.3 ; PL 10.1.1.3 ; DW bench/2026-09-27/R-S11-H.log
HOST bench/2026-09-27/R-S12-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S12 :: ICMP 10.1.1.3
HOST bench/2026-09-27/R-S12-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/R-S12-P :: HP
CAP --out bench/2026-09-27/R-S12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/R-S12-H :: HN ; DW bench/2026-09-27/R-S12-L.log
HOST bench/2026-09-27/R-S12-D :: BD pair bench/2026-09-27/R-S11-R.log,bench/2026-09-27/X-R-S11-R.log bench/2026-09-27/R-S12-R.log,bench/2026-09-27/X-R-S12-R.log --host bench/2026-09-27/R-S11-H.log bench/2026-09-27/R-S12-H.log --pre bench/2026-09-27/R-S11-P.log bench/2026-09-27/R-S12-P.log
HOST bench/2026-09-27/R-RTS :: RTS read --dir bench/2026-09-27 --arm R --plan 011001100110 --ref 56:1.516:1.586 --ref 256:1.367:1.518 --ref 512:1.64:1.736 --ref 1024:2.03:2.124 --ref 1472:2.052:2.252 --ref-on 56:1.815:1.815 --ref-on 256:1.641:1.641 --ref-on 512:1.618:1.618 --ref-on 1024:2.086:2.086 --ref-on 1472:2.139:2.139 --row 256:avg:1.518 --row 512:avg:1.64 --row 1024:avg:2.086 --row 1472:avg:2.139 --row 1472:mdev:0.476
```

* `R-LS` — the port-3 gate (`PSRP3` and `port_status` `LinkUp`; the switch page's read clears
  `PSRP` bit 8 on driver 1.1, 讀).
* Each series `R-Skk`: its liveness gate (`-L`); for an on-series its capture (`-T`); the
  capture count (`-C0`); the series; the count again (`-C1`); for an on-series the capture
  stopped (`-X`, a gate: none left running); its bracket (`-P`, `-R`, `-H`) and `brdelta`'s
  pair with the path gate (`-D`).
* `R-RTS` — `rttseries` over the twelve, with seating A's references and the five stable rows'
  A medians (§ 3.5).

### The handover

```
CAP --out bench/2026-09-27/H-DOWN --send 'ifconfig rlx0 down ; cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 30
CAP --out bench/2026-09-27/H-ETH4 --send 'ifconfig eth4 10.1.1.4 up ; ifconfig eth4 ; cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 40
```

* `H-DOWN` — `rlx0` down: IRQ 12 leaves `/proc/interrupts`. `H-ETH4` — `eth4` up at 10.1.1.4,
  IRQ 12 now `eth4`'s (block 44's handover, 量 `bench/2026-09-25/P1-DOWN`, `P1-ETH4`).

### ② on `eth4`

```
CAP --out bench/2026-09-27/E-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12
HOST bench/2026-09-27/E-00-P :: HP
CAP --out bench/2026-09-27/E-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-00-H :: HN ; DW bench/2026-09-27/R-S12-H.log
HOST bench/2026-09-27/E-S01-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-00-H.log
HOST bench/2026-09-27/E-S01-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S01 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S01-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S01-P :: HP
CAP --out bench/2026-09-27/E-S01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S01-H :: HN ; DW bench/2026-09-27/E-S01-L.log
HOST bench/2026-09-27/E-S01-D :: BD pair bench/2026-09-27/E-00-R.log,bench/2026-09-27/X-E-00-R.log bench/2026-09-27/E-S01-R.log,bench/2026-09-27/X-E-S01-R.log --host bench/2026-09-27/E-00-H.log bench/2026-09-27/E-S01-H.log --pre bench/2026-09-27/E-00-P.log bench/2026-09-27/E-S01-P.log
HOST bench/2026-09-27/E-S02-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S01-H.log
HOST& bench/2026-09-27/E-S02-T :: TDT
HOST bench/2026-09-27/E-S02-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S02 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S02-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S02-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S02-P :: HP
CAP --out bench/2026-09-27/E-S02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S02-H :: HN ; DW bench/2026-09-27/E-S02-L.log
HOST bench/2026-09-27/E-S02-D :: BD pair bench/2026-09-27/E-S01-R.log,bench/2026-09-27/X-E-S01-R.log bench/2026-09-27/E-S02-R.log,bench/2026-09-27/X-E-S02-R.log --host bench/2026-09-27/E-S01-H.log bench/2026-09-27/E-S02-H.log --pre bench/2026-09-27/E-S01-P.log bench/2026-09-27/E-S02-P.log
HOST bench/2026-09-27/E-S03-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S02-H.log
HOST& bench/2026-09-27/E-S03-T :: TDT
HOST bench/2026-09-27/E-S03-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S03 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S03-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S03-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S03-P :: HP
CAP --out bench/2026-09-27/E-S03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S03-H :: HN ; DW bench/2026-09-27/E-S03-L.log
HOST bench/2026-09-27/E-S03-D :: BD pair bench/2026-09-27/E-S02-R.log,bench/2026-09-27/X-E-S02-R.log bench/2026-09-27/E-S03-R.log,bench/2026-09-27/X-E-S03-R.log --host bench/2026-09-27/E-S02-H.log bench/2026-09-27/E-S03-H.log --pre bench/2026-09-27/E-S02-P.log bench/2026-09-27/E-S03-P.log
HOST bench/2026-09-27/E-S04-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S03-H.log
HOST bench/2026-09-27/E-S04-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S04 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S04-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S04-P :: HP
CAP --out bench/2026-09-27/E-S04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S04-H :: HN ; DW bench/2026-09-27/E-S04-L.log
HOST bench/2026-09-27/E-S04-D :: BD pair bench/2026-09-27/E-S03-R.log,bench/2026-09-27/X-E-S03-R.log bench/2026-09-27/E-S04-R.log,bench/2026-09-27/X-E-S04-R.log --host bench/2026-09-27/E-S03-H.log bench/2026-09-27/E-S04-H.log --pre bench/2026-09-27/E-S03-P.log bench/2026-09-27/E-S04-P.log
HOST bench/2026-09-27/E-S05-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S04-H.log
HOST bench/2026-09-27/E-S05-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S05 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S05-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S05-P :: HP
CAP --out bench/2026-09-27/E-S05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S05-H :: HN ; DW bench/2026-09-27/E-S05-L.log
HOST bench/2026-09-27/E-S05-D :: BD pair bench/2026-09-27/E-S04-R.log,bench/2026-09-27/X-E-S04-R.log bench/2026-09-27/E-S05-R.log,bench/2026-09-27/X-E-S05-R.log --host bench/2026-09-27/E-S04-H.log bench/2026-09-27/E-S05-H.log --pre bench/2026-09-27/E-S04-P.log bench/2026-09-27/E-S05-P.log
HOST bench/2026-09-27/E-S06-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S05-H.log
HOST& bench/2026-09-27/E-S06-T :: TDT
HOST bench/2026-09-27/E-S06-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S06 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S06-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S06-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S06-P :: HP
CAP --out bench/2026-09-27/E-S06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S06-H :: HN ; DW bench/2026-09-27/E-S06-L.log
HOST bench/2026-09-27/E-S06-D :: BD pair bench/2026-09-27/E-S05-R.log,bench/2026-09-27/X-E-S05-R.log bench/2026-09-27/E-S06-R.log,bench/2026-09-27/X-E-S06-R.log --host bench/2026-09-27/E-S05-H.log bench/2026-09-27/E-S06-H.log --pre bench/2026-09-27/E-S05-P.log bench/2026-09-27/E-S06-P.log
HOST bench/2026-09-27/E-S07-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S06-H.log
HOST& bench/2026-09-27/E-S07-T :: TDT
HOST bench/2026-09-27/E-S07-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S07 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S07-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S07-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S07-P :: HP
CAP --out bench/2026-09-27/E-S07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S07-H :: HN ; DW bench/2026-09-27/E-S07-L.log
HOST bench/2026-09-27/E-S07-D :: BD pair bench/2026-09-27/E-S06-R.log,bench/2026-09-27/X-E-S06-R.log bench/2026-09-27/E-S07-R.log,bench/2026-09-27/X-E-S07-R.log --host bench/2026-09-27/E-S06-H.log bench/2026-09-27/E-S07-H.log --pre bench/2026-09-27/E-S06-P.log bench/2026-09-27/E-S07-P.log
HOST bench/2026-09-27/E-S08-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S07-H.log
HOST bench/2026-09-27/E-S08-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S08 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S08-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S08-P :: HP
CAP --out bench/2026-09-27/E-S08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S08-H :: HN ; DW bench/2026-09-27/E-S08-L.log
HOST bench/2026-09-27/E-S08-D :: BD pair bench/2026-09-27/E-S07-R.log,bench/2026-09-27/X-E-S07-R.log bench/2026-09-27/E-S08-R.log,bench/2026-09-27/X-E-S08-R.log --host bench/2026-09-27/E-S07-H.log bench/2026-09-27/E-S08-H.log --pre bench/2026-09-27/E-S07-P.log bench/2026-09-27/E-S08-P.log
HOST bench/2026-09-27/E-S09-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S08-H.log
HOST bench/2026-09-27/E-S09-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S09 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S09-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S09-P :: HP
CAP --out bench/2026-09-27/E-S09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S09-H :: HN ; DW bench/2026-09-27/E-S09-L.log
HOST bench/2026-09-27/E-S09-D :: BD pair bench/2026-09-27/E-S08-R.log,bench/2026-09-27/X-E-S08-R.log bench/2026-09-27/E-S09-R.log,bench/2026-09-27/X-E-S09-R.log --host bench/2026-09-27/E-S08-H.log bench/2026-09-27/E-S09-H.log --pre bench/2026-09-27/E-S08-P.log bench/2026-09-27/E-S09-P.log
HOST bench/2026-09-27/E-S10-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S09-H.log
HOST& bench/2026-09-27/E-S10-T :: TDT
HOST bench/2026-09-27/E-S10-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S10 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S10-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S10-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S10-P :: HP
CAP --out bench/2026-09-27/E-S10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S10-H :: HN ; DW bench/2026-09-27/E-S10-L.log
HOST bench/2026-09-27/E-S10-D :: BD pair bench/2026-09-27/E-S09-R.log,bench/2026-09-27/X-E-S09-R.log bench/2026-09-27/E-S10-R.log,bench/2026-09-27/X-E-S10-R.log --host bench/2026-09-27/E-S09-H.log bench/2026-09-27/E-S10-H.log --pre bench/2026-09-27/E-S09-P.log bench/2026-09-27/E-S10-P.log
HOST bench/2026-09-27/E-S11-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S10-H.log
HOST& bench/2026-09-27/E-S11-T :: TDT
HOST bench/2026-09-27/E-S11-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S11 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S11-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S11-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S11-P :: HP
CAP --out bench/2026-09-27/E-S11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S11-H :: HN ; DW bench/2026-09-27/E-S11-L.log
HOST bench/2026-09-27/E-S11-D :: BD pair bench/2026-09-27/E-S10-R.log,bench/2026-09-27/X-E-S10-R.log bench/2026-09-27/E-S11-R.log,bench/2026-09-27/X-E-S11-R.log --host bench/2026-09-27/E-S10-H.log bench/2026-09-27/E-S11-H.log --pre bench/2026-09-27/E-S10-P.log bench/2026-09-27/E-S11-P.log
HOST bench/2026-09-27/E-S12-L :: FL 10.1.1.4 ; PL 10.1.1.4 ; DW bench/2026-09-27/E-S11-H.log
HOST bench/2026-09-27/E-S12-C0 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S12 :: ICMP 10.1.1.4
HOST bench/2026-09-27/E-S12-C1 :: pgrep -xc tcpdump ; true
HOST bench/2026-09-27/E-S12-P :: HP
CAP --out bench/2026-09-27/E-S12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/E-S12-H :: HN ; DW bench/2026-09-27/E-S12-L.log
HOST bench/2026-09-27/E-S12-D :: BD pair bench/2026-09-27/E-S11-R.log,bench/2026-09-27/X-E-S11-R.log bench/2026-09-27/E-S12-R.log,bench/2026-09-27/X-E-S12-R.log --host bench/2026-09-27/E-S11-H.log bench/2026-09-27/E-S12-H.log --pre bench/2026-09-27/E-S11-P.log bench/2026-09-27/E-S12-P.log
HOST bench/2026-09-27/E-RTS :: RTS read --dir bench/2026-09-27 --arm E --plan 011001100110
```

* `E-LS`, the opening bracket `E-00`, and the same twelve series against 10.1.1.4, cell for
  cell (the generator refuses two arms whose cells differ but for the target and `nd_up`).
  Every `E` bracket gates on `nd_up 0`: 讀 `66ddb93`'s `nic_ndo_stop` clears the flag the 1.4
  page prints as `nd_up`, and leaves the ring allocated, so the page still prints; `E-00-R` is
  this card's first read of a 1.4 page with `nd_up 0`. `E-RTS` — `rttseries` over them; no
  reference exists for `eth4`.

### The closing map and the kernel log

```
CAP --out bench/2026-09-27/A1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# |Booting\.\.\.|---RealTek' --seconds 60
HOST bench/2026-09-27/A1-MB1 :: MB bench/2026-09-27/A1-M1
CAP --out bench/2026-09-27/A1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-27/Z-DW :: DW bench/2026-09-27/B-AC0-H.log,bench/2026-09-27/R-S01-L.log,bench/2026-09-27/R-S01-H.log,bench/2026-09-27/R-S02-L.log,bench/2026-09-27/R-S02-H.log,bench/2026-09-27/R-S03-L.log,bench/2026-09-27/R-S03-H.log,bench/2026-09-27/R-S04-L.log,bench/2026-09-27/R-S04-H.log,bench/2026-09-27/R-S05-L.log,bench/2026-09-27/R-S05-H.log,bench/2026-09-27/R-S06-L.log,bench/2026-09-27/R-S06-H.log,bench/2026-09-27/R-S07-L.log,bench/2026-09-27/R-S07-H.log,bench/2026-09-27/R-S08-L.log,bench/2026-09-27/R-S08-H.log,bench/2026-09-27/R-S09-L.log,bench/2026-09-27/R-S09-H.log,bench/2026-09-27/R-S10-L.log,bench/2026-09-27/R-S10-H.log,bench/2026-09-27/R-S11-L.log,bench/2026-09-27/R-S11-H.log,bench/2026-09-27/R-S12-L.log,bench/2026-09-27/R-S12-H.log,bench/2026-09-27/E-S01-L.log,bench/2026-09-27/E-S01-H.log,bench/2026-09-27/E-S02-L.log,bench/2026-09-27/E-S02-H.log,bench/2026-09-27/E-S03-L.log,bench/2026-09-27/E-S03-H.log,bench/2026-09-27/E-S04-L.log,bench/2026-09-27/E-S04-H.log,bench/2026-09-27/E-S05-L.log,bench/2026-09-27/E-S05-H.log,bench/2026-09-27/E-S06-L.log,bench/2026-09-27/E-S06-H.log,bench/2026-09-27/E-S07-L.log,bench/2026-09-27/E-S07-H.log,bench/2026-09-27/E-S08-L.log,bench/2026-09-27/E-S08-H.log,bench/2026-09-27/E-S09-L.log,bench/2026-09-27/E-S09-H.log,bench/2026-09-27/E-S10-L.log,bench/2026-09-27/E-S10-H.log,bench/2026-09-27/E-S11-L.log,bench/2026-09-27/E-S11-H.log,bench/2026-09-27/E-S12-L.log,bench/2026-09-27/E-S12-H.log
HOST bench/2026-09-27/Z-DWALL :: DW none
```

* `A1-M1`, `A1-MB1`, `A1-NW1` — P1's closing bracket. `Z-DW`, `Z-DWALL` — the kernel log's last
  window and its whole count. Then the press's command line opens the watch `X-W1`, and the
  owner powers off by the owner's handshake (§ 6, *The owner's actions*).

### After power-off

```
HOST bench/2026-09-27/Z9-HCX :: HCL stop bench/2026-09-27/Z0-HC
HOST bench/2026-09-27/Z9-HCR :: HCL report bench/2026-09-27/Z0-HC
HOST bench/2026-09-27/Z9-TSD :: sudo -n systemctl start systemd-timesyncd ; systemctl show -p ActiveState systemd-timesyncd
HOST bench/2026-09-27/Z9-D2 :: /usr/bin/python3 tools/boot-timeline.py --retro bench/2026-09-27 --tsv bench/2026-09-27/Z9-D2.tsv
HOST bench/2026-09-27/Z9-W1 :: W1W read --bench bench/2026-09-27 --boot A1Q-boot --probe A1-HP --frames bench/2026-09-27/W-TCPD.log --clock bench/2026-09-27/Z0-HC
```

* `Z9-HCX` — `hostclock stop`, a reading, so a logger that already died cannot keep `timesyncd`
  stopped; `Z9-HCR` — its report over the press (P5); `Z9-TSD` — `ActiveState=active`; `Z9-D2`
  — `boot-timeline --retro` over this card's directory into the table `w1width` reads (the file
  name `netup`'s reader expects), in `I-C9` so that a press ended by a power-off, which skips
  `I-Z`, still has it; `Z9-W1` — ①'s width (P4), the frames put on RAW over the closed clock
  log.

---

## § 6 How the cells are run

**Before any cell** (none of it a cell), in this order: (1) `w32tm /query /status` for the last
sync, kept in the transcripts' directory, and read again after `I-C9`; (2) no other WSL job is
running, because (3) kills every WSL process; (3) `wsl --shutdown` from PowerShell, then the
keeper `wsl -d Ubuntu-24.04 -- sleep 36000` in the background; (4) the kernel-log follower,
from PowerShell in the background:
`wsl -d Ubuntu-24.04 -- bash -c "mkdir -p /home/key/fwre-work/rebuild/s113/card43a/host && exec dmesg -w > /home/key/fwre-work/rebuild/s113/card43a/host/dmesg-w.log"`
— before the attach, so the attach is in the log; (5) `usbipd list`, read fresh, then
`usbipd attach` of the CP2102 and of the GbE adapter, reading what each prints; (6) in WSL,
from the repository root: `mkdir -p /home/key/fwre-work/rebuild/s113/card43a/run`;
`/usr/bin/python3 tools/cardcheck.py numbers` and `commands` on this card;
`/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 274 captures came after the prediction, 274 did not`**; every invocation once through
`runblock.py … --dry`, each ending `ALL ITEMS DONE`. **The catch window opens no later than
23:00 on the declared date** (midnight less a margin for the press and its stops, a guess,
`arith43a`), so every capture is dated that day; later, the card is re-dated before power.

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py bench/2026-09-27/PREDICTIONS-B51-block49.md NAME --log LOG`,
with LOG `/home/key/fwre-work/rebuild/s113/card43a/run/run-NAME.log`, in the order `I-0`,
`I-C0` (in the background for the whole seating, as a background task of the session that runs
it; its transcript read for `BG  Z0-HC … start seen` before `I-C1` starts), `I-C1`, then the
press — `I-1`, `I-R`, `I-H`, `I-E`, `I-Z` — as one command line, then, after the owner's
power-off, `I-C9`. **The press's command line** is a script file run by path, in the background
of the session (*The owner's actions*, below), through `line43a.sh` —
`bash /home/key/fwre-work/rebuild/s113/card43a/line43a.sh /home/key/fwre-work/rebuild/s113/card43a/run/line<k>.sh`,
`<k>` counting the session's command lines — which keeps its watch stoppable (*The watch*): the
five invocations chained with `&&`, then `;` and the watch `X-W1` (*The watch*), so that no gap
between two of them is longer than the runner's start-up, and the watch opens the moment the
runner stops, whether `I-Z` ended or a stop ended an invocation earlier; the session follows
the run logs and takes the appearance of `X-W1.log` as the chain's end. `NAME?` marks a cell
whose non-zero exit is a reading; `gate:` items are the decision points; any failed cell or
gate stops its own invocation, and so the chain, and interrupts its own background cells, never
another invocation's. A continuation (`--from CELL`) writes a new log, `run-NAME-r<k>.log` with
k = 2, 3, … counting that invocation's runs (the runner refuses an existing log), and is itself
such a command line — the continued invocation and those after it in the press, chained with
`&&`, then `;` and the next watch — started only after the watch's hold of 90 s (*The watch*),
once the running watch has been stopped. **After any stop while a capture of the stopped
invocation was running**, before anything else on the host (and after the power-off, where the
stop calls for one): `X-TCPK<n>` —
`sudo -n pkill -INT -x tcpdump ; sleep 1 ; pgrep -xc tcpdump ; true` — must read `0` (the desk
control of § 0 ⑨ ran on the loopback interface with no traffic); not `0`: `X-KILL<n>` below.

**Chained references, on every path.** A kernel-log window's `--prev` (`dmesgwin` 1.2) and a
pair's previous read (`brdelta` 1.2: its `R`, `--host` and `--pre` logs) each name,
comma-separated in run order, every log that is that chain's last on some path this section
allows, and the tool reads the last of them that exists; a pair's current read is named with
its stand-in after it (`<read>.log,X-<read>.log`). The generator enumerates the paths — the
full run, each event below at every cell it can happen at (a stand-in read, a host-path failure
whose recovery passes or fails, the loader gate), and every ordered pair of a stand-in or a
passed recovery with a later failure or loader gate: 3282 paths, 123 chained lists — and
refuses a card on which a cell on any path reads a log that path never wrote, reads a list
whose last written log is not that chain's last on the path, or names a read without the
stand-in the path wrote for it; its two positive controls (a list naming a stale predecessor, a
pair naming a read without its stand-in) are refused before the card is written. Nothing a
recovery types writes a log a list names (`X-HN<n>` is `HN` alone; `X-L<n>` counts the whole
log). ③'s reader `W3` reads `B-AC0-R` itself on every path: ③ is scored on that read or not at
all.

**The watch.** `X-W<n>` —
`CAP --out bench/2026-09-27/X-W<n> --esc-after 3600 --esc-period 0.01 --until '<RealTek>' --seconds 3605`
— sends nothing but ESC, at the period of block 15's `C5-UB`, which streamed ESC into a live
`rlxfw` for 145.9 s, until the hardware watchdog bit (a `/dev/watchdog` deadline left to
lapse), and caught the loader at its prompt (量 `bench/2026-09-09/C5-UB`); it ends on the
loader's prompt `<RealTek>`, on its cap, or on the session's SIGINT. A reset inside it reaches
the loader while ESC is streaming, so the loader stops at its prompt instead of booting the
vendor firmware, and the capture ends there. It is the one kind of console capture here that
must not end on the banner, which would stop the ESC before the loader's window (§ 0 ⑦; the
generator refuses a watch text holding the banner). It holds the console at every moment
outside an invocation, past the round, that the board runs a kernel with no other capture open
for more than about 30 s (a guess of one of the session's turns; inside an invocation § 0 ⑦
(ii) bounds the host stretches instead): from the end of the press's command line, across every
wait for the owner, every host-only step of a recovery (`X-RA<n>`, the WSL-stop rule's
re-attach) and every decision a stop below calls for, until the power-off window. Host cells
run beside it. Every watch runs in the background of the session, as part of a command line
started there, never in the foreground: it lasts up to an hour, longer than a foreground
command the session can hold, and the session must stay free to talk to the owner and read the
other logs while the watch holds the console. **Every such command line — the press's, a
continuation's, a board cell's with its next watch, a power-off window's with its next watch —
is a script file run through `line43a.sh`**
(`bash /home/key/fwre-work/rebuild/s113/card43a/line43a.sh /home/key/fwre-work/rebuild/s113/card43a/run/line<k>.sh`,
pinned in `R0-SUM`), because the stop below is a SIGINT, and `console-capture` ends on one only
if it started with SIGINT not ignored: Python installs its interrupt handler only then, and a
command started with `&` from a shell without job control inherits SIGINT ignored, which `bash`
cannot undo. `line43a.sh` re-executes itself through a shim that sets SIGINT to its default
(with SIGPIPE and SIGXFSZ, which the shim's Python would otherwise hand on ignored) before it
runs the file, and refuses (exit 2, the file not run) if SIGINT is still ignored. 量 at the desk
(`sigctl43a.sh`: a real `console-capture` on a pseudo-terminal, every line written from this
card's text with the port and the directory substituted, stopped by this card's `pkill`): the
press's line started with `&` and no `line43a.sh` ignored the SIGINT, still running 10 s after
it with no `.meta.json`; through `line43a.sh`, started with `&` or with SIGINT at its default,
a watch and a power-off window each ended `interrupted`; started the way the session's own
background commands start (from Windows, through `wsl`), the line ended `interrupted` with and
without `line43a.sh`; a shim planted to restore nothing was refused. Before a board cell the
session types, or a continuation, the session stops it — `pkill -INT -f 'X-W<n> '`
(`console-capture` ends an interrupted ESC loop with its CR), then its `.meta.json` read for a
stop reason that is the interrupt; none 10 s after the SIGINT, the watch has not stopped, and
no board cell is typed and no continuation starts until the owner has read it — and the board
cell runs as a command line of its own, in the background, with `;` and the next watch
`X-W<n+1>` after it, as the press's does, so that the watch follows the cell however it ends;
the session reads the cell once its `.meta.json` exists. A watch that reaches its cap is
followed at once by the next. **The hold after a stop.** After any stop past the round with the
board running a kernel — a board cell's gate, a host gate (`-L`, `-D`, `-T`, `-X`) or any other
— the watch holds the console, before any board cell is typed and before any continuation
starts, until at least 90 s after the latest board cell's capture **ended** — its
`.meta.json`'s `t0_real` plus `duration_s`, later than any byte it received — by when a kernel
that had stopped by then has been bitten, inside the watch, and the loader has taken the
watch's ESC: the bite as measured, 84.001 s (`CLK-08b`), plus the loader's 2.288 s from its
banner to its first prompt with ESC streaming (量 block 48's `R1-CATCH`), plus 3 s (a guess),
rounded up (`arith43a`'s `HOLD` line; § 0 ⑦ (iv)). A hold of the bite alone could end the ESC
before the loader reads it, about 2.288 s after its banner. That capture is either a reading
that showed the kernel running, ended on its own text, or **a board cell that ended silent** —
one whose capture holds neither its own expected text nor the loader's, however it ended, on
its cap or on its `--idle` (`R-LS`, `E-LS`, `H-DOWN`, `H-ETH4`, `A1-PS`, `A1-NW0`, `A1-NW1`,
S1's `X-SW<n>`, `X-PHY<n>` and `X-PS<n>`, `X-RT<n>` and the port-3 gate's stand-ins end on
their idle) — which may be a kernel whose timer wheel stopped before the cell or during it, so
its last kick of `BOOTGUARD` can be as late as the cell's end. Counted from the cell's start,
the hold would end up to the cell's length early (up to its cap: 15 s for a bracket, 60 s for a
map), and the bite could then fall inside the stand-in or the map's repeat typed next, which
streams no ESC; a kernel that stops after the capture the hold counts from is § 0 ⑦'s (c). What
an hour of ESC does to `ash` is 推 harmless: it echoes or drops them, and the watch's closing CR
runs one line of them, which `ash` does not find as a command (`C5-UB` streamed 145.9 s into a
running shell). **At the loader's prompt no watch is opened.** A watch opened with the board
already at the loader's prompt ends within about 1.3 s on the loader's own reply to its ESC:
`console-capture` arms `--until` from the start of a capture with no `--esc` and no `--send` (讀
`tools/console-capture.py`), and the loader answers every 128 ESC at its prompt with
`Unknown command !` and its prompt (量 `bench/2026-09-26b/R1-CATCH.log`, 550 replies). So **a
watch caught a reset only if the loader's banner (`Booting...` or `---RealTek`) precedes its
`<RealTek>`**: the board is then at the loader's prompt, and the loader rule below applies; the
same holds for a power-off window `X-OFF<n>`. A `<RealTek>` with no banner before it is the
loader's reply to the watch's own ESC: it records no reset inside the watch, but it does mean
the board is at the loader's prompt, whatever its last known state — where that was a running
kernel, a reset fell before the watch opened the port, its banner unseen, and the board has
reset as the loader rule below reads it. Where the board's last known state is the loader's
prompt — before the round, after `gate:caught` passed and before `A1Q`'s `J` (sent by its
`A1Q-boot` capture, absent then), or once a catch, a watch or a window has caught the loader —
no further watch is opened, and one already on a command line ends on that reply: the loader
boots nothing by itself, and the power-off there needs no ESC window (*The owner's actions*).

**The owner's actions** — the press (a power-on) and the power-off, the card's only physical
actions — go by the owner's handshake, as the owner stated it on 2026-09-27: for every power-on
and power-off the session tells the owner and STOPS until the owner replies; only then does it
open the catch (or the power-off window) in the background, confirm from the transcript that
the ESC-streaming cell is running, and then tell the owner "catch open — power on now" (or
"power off now"); the owner acts only on that word. No count-to-five after the reply, and
nothing physical happens between the reply and the session's "now". Why nothing is timed from
the reply: the session's own latency between receiving a reply and starting a window can exceed
any count the owner makes, and a power-on before the catch streams misses the loader's ESC
window of about 4.9 s, so the loader boots the vendor firmware — whose flash effect is 推
(§ 0 ⑦), and which the card prevents by catching the loader (`CLAUDE.md`) — and the press is
lost. The owner is told of both actions in one message before the first — the press first, and
the power-off after `I-Z`, about 13 minutes after the catch opens (a guess, § 2) — and each
still goes by the handshake on its own. **What the session tells the owner.** Before the reply:
which action comes next and the length of its window. After confirming the window: "catch open
— power on now", with "the catch streams ESC for 360 s from its start"; or "power off now",
with "the window streams ESC for 360 s from its start". Each length is 60 s for the session to
open the window, confirm it and send "now", plus 300 s for the owner after "now", both guesses
(`arith43a`'s `HANDSHAKE` line), each over the owner's standing 40 s. **The confirmation from
the transcript**: the run log's `RUN` line for a runner cell, and the capture's `.timing` file,
which `console-capture` creates only once the port is open, just before its ESC loop, with no
`.meta.json` yet (讀 `tools/console-capture.py`). The watch is not a window: it holds the
console while the owner is asked. **The press**, after `I-C1`: its window is the press's
command line, started in the background after the reply, whose first cell `A1-CATCH` streams
ESC from its start for up to 360 s and ends at the loader's first prompt (its cap 380 s); the
confirmation is `A1-CATCH`'s `RUN` line in `run-I-1.log` and `A1-CATCH.timing`. A press after
that stream is not caught by it: `gate:caught` fails, the chain stops, and its watch `X-W1`,
streaming ESC, catches the loader if the press comes after it opens (§ 6's rule for
`gate:caught`). **The power-off**, after `I-Z` or wherever a stop below calls for one — "at
once" there means that telling the owner is the session's first action — with the watch holding
the console until the reply; its window is `X-OFF<n>` —
`CAP --out bench/2026-09-27/X-OFF<n> --esc-after 360 --esc-period 0.01 --until '<RealTek>' --seconds 365`
(its cap 365 s) — started after the reply, once the session has stopped the watch, in the
background as a command line of its own with `;` and the next watch after it, and confirmed by
`X-OFF<n>.timing`; that next watch keeps the console watched if the board is still on when
`X-OFF<n>` reaches its cap. **At the loader's prompt** (*The watch*) the power-off has no
window and no watch holds the console: after the owner's reply the session sends "power off
now" with nothing to open or confirm, since the loader boots nothing by itself. The owner
confirms the power-off in words, a report that is data; the session then stops `X-OFF<n>` if it
still runs and the watch its command line starts next, each by its SIGINT as *The watch* stops
one, and `I-C9` runs.

**`I-0`** — before power: the pre-flight, the address, the adapter, no capture, one kernel-log follower and a clean log, the flush, the capture directory, the checkers' digests and self-tests

```run
R0-PRE?
R0-PREC
gate:grep=^  "bytes": 0,$:R0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:R0-PREC
R0-ADDR
gate:grep=inet 10\.1\.1\.2/24:R0-ADDR
R0-ETH?
R0-EVICT?
R0-TCPC
gate:grep=\A0\n\Z:R0-TCPC
R0-DMSG
gate:grep=\A1\n\Z:R0-DMSG
R0-DW0
gate:grep=^window 0 [1-9][0-9]*$:R0-DW0
gate:grep=^bug_preempt 0$:R0-DW0
gate:grep=^usbnet_xmit 0$:R0-DW0
gate:grep=^call_trace 0$:R0-DW0
gate:grep=^follower 1$:R0-DW0
R0-FL
gate:grep=\A(?:0\n)+\Z:R0-FL
R0-PCAP
gate:grep=\A0\n\Z:R0-PCAP
R0-SUM
gate:grep=^6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095  -$:R0-SUM
gate:grep=^030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984  -$:R0-SUM
gate:grep=^2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1  -$:R0-SUM
gate:grep=^fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431  -$:R0-SUM
gate:grep=^fbae2a34a798514f8fff35fbea7dbf189ae537f79718f2c7a12fca460993cecf  -$:R0-SUM
gate:grep=^1834535265e74eb696bd9fd4e64a23df39182e90e3c66f58c8b60c4a402fc647  -$:R0-SUM
gate:grep=^519fd40e64e7b290dab7e49186c53562c4c86186972440aecb07e2aea7ef1773  -$:R0-SUM
gate:grep=^af52c0af565528154c517b8747e2c5da8089c02a577fe77af005bfc2aaddb959  -$:R0-SUM
gate:grep=^07107201433f83e7d6f215c9ed5ff27eda668a18fff37701533c4a78bd418da0  -$:R0-SUM
gate:grep=^d7422a6f497e4bd7579a6187152b999dbd2587eab809f22f0b08c45f8acbe187  -$:R0-SUM
gate:grep=^21287d2e33c7b8e87fb0f426ed728a4eec052fc6722356f8136aeb1bdbb6363b  -$:R0-SUM
gate:grep=^112bc19eed610fdab3ea3e8b0ce4f63b076420992b73588d22fc1c10d4687014  -$:R0-SUM
R0-ST
gate:grep=^pcapwin\ self\-test:\ 29\ of\ 29\ passed$:R0-ST
gate:grep=^brdelta\ self\-test:\ 40\ of\ 40\ passed$:R0-ST
gate:grep=^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$:R0-ST
gate:grep=^s1class\ self\-test:\ 15\ of\ 15\ passed$:R0-ST
gate:grep=^rttseries\ self\-test:\ 22\ of\ 22\ passed$:R0-ST
gate:grep=^w3\ self\-test:\ 17\ of\ 17\ passed$:R0-ST
gate:grep=^w1width\ self\-test:\ 9\ of\ 9\ passed$:R0-ST
gate:grep=^hcstepctl\ self\-test:\ 5\ of\ 5\ passed$:R0-ST
R0-H?
```

**`I-C0`** — `hostclock` for the whole seating, in the background; it ends when `Z9-HCX` stops the logger

```run
Z0-HC
```

**`I-C1`** — the clock guard, before power: the logger alive, `timesyncd` stopped, a 60 s run that must read no step and the tick agreeing

```run
Z0-HCW
Z0-TSD
gate:grep=^ActiveState=inactive$:Z0-TSD
Z0-HCG
gate:grep=^  tick check: AGREE over [0-9]+ pair\(s\), worst [-+][0-9.]+ ppm, vacuous:Z0-HCG
gate:grep=^  steps: timerfd 0, agreed with the rows 0, NO STEPS; :Z0-HCG
```

**`I-1`** — the press: the catch, the two captures and the probe from before `J`, one cold round, the probe stopped, the one `asicCounter` read between two host reads (③), the captures stopped and read, the process table, the opening map, `n_writes`

```run
A1-CATCH
gate:caught:A1-CATCH
A1-FL
gate:grep=\A(?:0\n)+\Z:A1-FL
W-TCPD
W-TCPE
A1-HP
A1Q
A1-HPX
gate:hpstop:A1-HPX
B-AC0-P?
B-AC0-R
gate:until:B-AC0-R
gate:grep=^version rtl819x-nic 1\.4$:B-AC0-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-AC0-R
gate:grep=^nd_up 1$:B-AC0-R
B-AC0-H?
W-TCPX?
W-TCPC
gate:grep=\A0\n\Z:W-TCPC
W-EWALL?
W-EORD?
W3?
A1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:A1-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-PS
A1-M0
gate:until:A1-M0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-M0
A1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:A1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:A1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:A1-MB0
A1-NW0
gate:grep=^n_writes 0$:A1-NW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-NW0
```

**`I-R`** — ② on `rlx0` at 1.4: the port-3 gate, then twelve ICMP series ABBA from off, each behind a liveness gate, its capture state read before and after, and a board bracket after it

```run
R-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:R-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:R-LS
R-S01-L
gate:grep=^4 packets transmitted, 4 received:R-S01-L
gate:grep=^follower 1$:R-S01-L
R-S01-C0?
R-S01?
R-S01-C1?
R-S01-P?
R-S01-R
gate:until:R-S01-R
gate:grep=^version rtl819x-nic 1\.4$:R-S01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S01-R
gate:grep=^nd_up 1$:R-S01-R
R-S01-H?
R-S01-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S01-D
R-S02-L
gate:grep=^4 packets transmitted, 4 received:R-S02-L
gate:grep=^follower 1$:R-S02-L
R-S02-T
R-S02-C0?
R-S02?
R-S02-C1?
R-S02-X
gate:grep=\A0\n\Z:R-S02-X
R-S02-P?
R-S02-R
gate:until:R-S02-R
gate:grep=^version rtl819x-nic 1\.4$:R-S02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S02-R
gate:grep=^nd_up 1$:R-S02-R
R-S02-H?
R-S02-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S02-D
R-S03-L
gate:grep=^4 packets transmitted, 4 received:R-S03-L
gate:grep=^follower 1$:R-S03-L
R-S03-T
R-S03-C0?
R-S03?
R-S03-C1?
R-S03-X
gate:grep=\A0\n\Z:R-S03-X
R-S03-P?
R-S03-R
gate:until:R-S03-R
gate:grep=^version rtl819x-nic 1\.4$:R-S03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S03-R
gate:grep=^nd_up 1$:R-S03-R
R-S03-H?
R-S03-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S03-D
R-S04-L
gate:grep=^4 packets transmitted, 4 received:R-S04-L
gate:grep=^follower 1$:R-S04-L
R-S04-C0?
R-S04?
R-S04-C1?
R-S04-P?
R-S04-R
gate:until:R-S04-R
gate:grep=^version rtl819x-nic 1\.4$:R-S04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S04-R
gate:grep=^nd_up 1$:R-S04-R
R-S04-H?
R-S04-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S04-D
R-S05-L
gate:grep=^4 packets transmitted, 4 received:R-S05-L
gate:grep=^follower 1$:R-S05-L
R-S05-C0?
R-S05?
R-S05-C1?
R-S05-P?
R-S05-R
gate:until:R-S05-R
gate:grep=^version rtl819x-nic 1\.4$:R-S05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S05-R
gate:grep=^nd_up 1$:R-S05-R
R-S05-H?
R-S05-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S05-D
R-S06-L
gate:grep=^4 packets transmitted, 4 received:R-S06-L
gate:grep=^follower 1$:R-S06-L
R-S06-T
R-S06-C0?
R-S06?
R-S06-C1?
R-S06-X
gate:grep=\A0\n\Z:R-S06-X
R-S06-P?
R-S06-R
gate:until:R-S06-R
gate:grep=^version rtl819x-nic 1\.4$:R-S06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S06-R
gate:grep=^nd_up 1$:R-S06-R
R-S06-H?
R-S06-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S06-D
R-S07-L
gate:grep=^4 packets transmitted, 4 received:R-S07-L
gate:grep=^follower 1$:R-S07-L
R-S07-T
R-S07-C0?
R-S07?
R-S07-C1?
R-S07-X
gate:grep=\A0\n\Z:R-S07-X
R-S07-P?
R-S07-R
gate:until:R-S07-R
gate:grep=^version rtl819x-nic 1\.4$:R-S07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S07-R
gate:grep=^nd_up 1$:R-S07-R
R-S07-H?
R-S07-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S07-D
R-S08-L
gate:grep=^4 packets transmitted, 4 received:R-S08-L
gate:grep=^follower 1$:R-S08-L
R-S08-C0?
R-S08?
R-S08-C1?
R-S08-P?
R-S08-R
gate:until:R-S08-R
gate:grep=^version rtl819x-nic 1\.4$:R-S08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S08-R
gate:grep=^nd_up 1$:R-S08-R
R-S08-H?
R-S08-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S08-D
R-S09-L
gate:grep=^4 packets transmitted, 4 received:R-S09-L
gate:grep=^follower 1$:R-S09-L
R-S09-C0?
R-S09?
R-S09-C1?
R-S09-P?
R-S09-R
gate:until:R-S09-R
gate:grep=^version rtl819x-nic 1\.4$:R-S09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S09-R
gate:grep=^nd_up 1$:R-S09-R
R-S09-H?
R-S09-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S09-D
R-S10-L
gate:grep=^4 packets transmitted, 4 received:R-S10-L
gate:grep=^follower 1$:R-S10-L
R-S10-T
R-S10-C0?
R-S10?
R-S10-C1?
R-S10-X
gate:grep=\A0\n\Z:R-S10-X
R-S10-P?
R-S10-R
gate:until:R-S10-R
gate:grep=^version rtl819x-nic 1\.4$:R-S10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S10-R
gate:grep=^nd_up 1$:R-S10-R
R-S10-H?
R-S10-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S10-D
R-S11-L
gate:grep=^4 packets transmitted, 4 received:R-S11-L
gate:grep=^follower 1$:R-S11-L
R-S11-T
R-S11-C0?
R-S11?
R-S11-C1?
R-S11-X
gate:grep=\A0\n\Z:R-S11-X
R-S11-P?
R-S11-R
gate:until:R-S11-R
gate:grep=^version rtl819x-nic 1\.4$:R-S11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S11-R
gate:grep=^nd_up 1$:R-S11-R
R-S11-H?
R-S11-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S11-D
R-S12-L
gate:grep=^4 packets transmitted, 4 received:R-S12-L
gate:grep=^follower 1$:R-S12-L
R-S12-C0?
R-S12?
R-S12-C1?
R-S12-P?
R-S12-R
gate:until:R-S12-R
gate:grep=^version rtl819x-nic 1\.4$:R-S12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R-S12-R
gate:grep=^nd_up 1$:R-S12-R
R-S12-H?
R-S12-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:R-S12-D
R-RTS?
```

**`I-H`** — the handover: `rlx0` down, `eth4` up at 10.1.1.4 (the vendor's driver, the same boot)

```run
H-DOWN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):H-DOWN
gate:grep=\A(?![\s\S]*\n +12: ):H-DOWN
H-ETH4
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):H-ETH4
gate:grep=inet addr:10\.1\.1\.4 :H-ETH4
gate:grep=\n +12: +\d+ +RLX LOPI +eth4:H-ETH4
```

**`I-E`** — ② on `eth4`: the port-3 gate, an opening bracket, then the same twelve series

```run
E-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:E-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:E-LS
E-00-P?
E-00-R
gate:until:E-00-R
gate:grep=^version rtl819x-nic 1\.4$:E-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-00-R
gate:grep=^nd_up 0$:E-00-R
E-00-H?
E-S01-L
gate:grep=^4 packets transmitted, 4 received:E-S01-L
gate:grep=^follower 1$:E-S01-L
E-S01-C0?
E-S01?
E-S01-C1?
E-S01-P?
E-S01-R
gate:until:E-S01-R
gate:grep=^version rtl819x-nic 1\.4$:E-S01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S01-R
gate:grep=^nd_up 0$:E-S01-R
E-S01-H?
E-S01-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S01-D
E-S02-L
gate:grep=^4 packets transmitted, 4 received:E-S02-L
gate:grep=^follower 1$:E-S02-L
E-S02-T
E-S02-C0?
E-S02?
E-S02-C1?
E-S02-X
gate:grep=\A0\n\Z:E-S02-X
E-S02-P?
E-S02-R
gate:until:E-S02-R
gate:grep=^version rtl819x-nic 1\.4$:E-S02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S02-R
gate:grep=^nd_up 0$:E-S02-R
E-S02-H?
E-S02-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S02-D
E-S03-L
gate:grep=^4 packets transmitted, 4 received:E-S03-L
gate:grep=^follower 1$:E-S03-L
E-S03-T
E-S03-C0?
E-S03?
E-S03-C1?
E-S03-X
gate:grep=\A0\n\Z:E-S03-X
E-S03-P?
E-S03-R
gate:until:E-S03-R
gate:grep=^version rtl819x-nic 1\.4$:E-S03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S03-R
gate:grep=^nd_up 0$:E-S03-R
E-S03-H?
E-S03-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S03-D
E-S04-L
gate:grep=^4 packets transmitted, 4 received:E-S04-L
gate:grep=^follower 1$:E-S04-L
E-S04-C0?
E-S04?
E-S04-C1?
E-S04-P?
E-S04-R
gate:until:E-S04-R
gate:grep=^version rtl819x-nic 1\.4$:E-S04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S04-R
gate:grep=^nd_up 0$:E-S04-R
E-S04-H?
E-S04-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S04-D
E-S05-L
gate:grep=^4 packets transmitted, 4 received:E-S05-L
gate:grep=^follower 1$:E-S05-L
E-S05-C0?
E-S05?
E-S05-C1?
E-S05-P?
E-S05-R
gate:until:E-S05-R
gate:grep=^version rtl819x-nic 1\.4$:E-S05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S05-R
gate:grep=^nd_up 0$:E-S05-R
E-S05-H?
E-S05-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S05-D
E-S06-L
gate:grep=^4 packets transmitted, 4 received:E-S06-L
gate:grep=^follower 1$:E-S06-L
E-S06-T
E-S06-C0?
E-S06?
E-S06-C1?
E-S06-X
gate:grep=\A0\n\Z:E-S06-X
E-S06-P?
E-S06-R
gate:until:E-S06-R
gate:grep=^version rtl819x-nic 1\.4$:E-S06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S06-R
gate:grep=^nd_up 0$:E-S06-R
E-S06-H?
E-S06-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S06-D
E-S07-L
gate:grep=^4 packets transmitted, 4 received:E-S07-L
gate:grep=^follower 1$:E-S07-L
E-S07-T
E-S07-C0?
E-S07?
E-S07-C1?
E-S07-X
gate:grep=\A0\n\Z:E-S07-X
E-S07-P?
E-S07-R
gate:until:E-S07-R
gate:grep=^version rtl819x-nic 1\.4$:E-S07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S07-R
gate:grep=^nd_up 0$:E-S07-R
E-S07-H?
E-S07-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S07-D
E-S08-L
gate:grep=^4 packets transmitted, 4 received:E-S08-L
gate:grep=^follower 1$:E-S08-L
E-S08-C0?
E-S08?
E-S08-C1?
E-S08-P?
E-S08-R
gate:until:E-S08-R
gate:grep=^version rtl819x-nic 1\.4$:E-S08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S08-R
gate:grep=^nd_up 0$:E-S08-R
E-S08-H?
E-S08-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S08-D
E-S09-L
gate:grep=^4 packets transmitted, 4 received:E-S09-L
gate:grep=^follower 1$:E-S09-L
E-S09-C0?
E-S09?
E-S09-C1?
E-S09-P?
E-S09-R
gate:until:E-S09-R
gate:grep=^version rtl819x-nic 1\.4$:E-S09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S09-R
gate:grep=^nd_up 0$:E-S09-R
E-S09-H?
E-S09-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S09-D
E-S10-L
gate:grep=^4 packets transmitted, 4 received:E-S10-L
gate:grep=^follower 1$:E-S10-L
E-S10-T
E-S10-C0?
E-S10?
E-S10-C1?
E-S10-X
gate:grep=\A0\n\Z:E-S10-X
E-S10-P?
E-S10-R
gate:until:E-S10-R
gate:grep=^version rtl819x-nic 1\.4$:E-S10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S10-R
gate:grep=^nd_up 0$:E-S10-R
E-S10-H?
E-S10-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S10-D
E-S11-L
gate:grep=^4 packets transmitted, 4 received:E-S11-L
gate:grep=^follower 1$:E-S11-L
E-S11-T
E-S11-C0?
E-S11?
E-S11-C1?
E-S11-X
gate:grep=\A0\n\Z:E-S11-X
E-S11-P?
E-S11-R
gate:until:E-S11-R
gate:grep=^version rtl819x-nic 1\.4$:E-S11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S11-R
gate:grep=^nd_up 0$:E-S11-R
E-S11-H?
E-S11-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S11-D
E-S12-L
gate:grep=^4 packets transmitted, 4 received:E-S12-L
gate:grep=^follower 1$:E-S12-L
E-S12-C0?
E-S12?
E-S12-C1?
E-S12-P?
E-S12-R
gate:until:E-S12-R
gate:grep=^version rtl819x-nic 1\.4$:E-S12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-S12-R
gate:grep=^nd_up 0$:E-S12-R
E-S12-H?
E-S12-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-S12-D
E-RTS?
```

**`I-Z`** — the closing map, `n_writes` and the kernel log's last window; then the owner powers off

```run
A1-M1
gate:until:A1-M1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-M1
A1-MB1
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:A1-MB1
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:A1-MB1
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:A1-MB1
A1-NW1
gate:grep=^n_writes 0$:A1-NW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-NW1
Z-DW?
Z-DWALL?
```

**`I-C9`** — after power-off (on every path): the clock log stopped and reported, `timesyncd` back, the boot's retro table and the width read (①)

```run
Z9-HCX?
Z9-HCR?
Z9-TSD
gate:grep=^ActiveState=active$:Z9-TSD
Z9-D2?
Z9-W1?
```

**S1 — a liveness gate fails** (a series' `-L`: fewer than 4 of 4). `follower` alone failing is
card 2's rule, with one change: the follower is restarted with (4)'s command with `dmesg -W >>`
in place of `dmesg -w >` (`-W` prints only messages newer than its start — 讀 this WSL's
`dmesg --help` — so no line already in the log is appended twice), the liveness is typed again
as `X-L<n>`, and every kernel-log window since the last `follower 1` is void, the next one
included (the messages between the follower's death and its restart are not in the log).
Otherwise the failure is **classified from the board before anything on the host is touched**
(after the watch's hold of 90 s, *The watch*; stopping the watch the chain opened touches only
the console), as declared cells whose text is fixed here, logged in `CORRECTIONS-block49.md` as
they run, `<n>` counting episodes, `<ip>` the arm's target:

1. `X-NIC<n>` —
`CAP --out bench/2026-09-27/X-NIC<n> --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10`:
the ring as the failure left it. At 1.4 the driver's own recovery arms only when all four TX
descriptors are engine-owned and a fifth frame is offered, and fires 100 jiffies later (讀
`NET-113`; 量 block 48's `X-BR1`, `notes/nic-driver.md` § 27.9), so this read comes first —
after the hold, during which a frame the board itself offers can arm that recovery; the page's
`n_recov_fire` shows whether it fired.
2. `X-HP<n>` — `HP`; 3. `X-BR<n>` — the board read, the card's `-R` text.
4. `X-S1<n>` —
`/usr/bin/python3 /home/key/fwre-work/rebuild/s113/shared/s1class.py classify --nic bench/2026-09-27/X-NIC<n>.log --br bench/2026-09-27/X-BR<n>.log --prev-br <P>.log --pre bench/2026-09-27/X-HP<n>.log --host <H>.log`,
with `<P>` the last `-R` this press wrote before the failed gate (its stand-in `X-<read>` where
one was typed) and `<H>` that read's `-H`. It prints `s1 branch a` iff the host sent at least
one frame between `<H>` and `X-HP<n>` and port 3 received at least as many between `<P>` and
`X-BR<n>` (the host reached the board), else `s1 branch b`; a refusal prints `s1 branch b`.

**Branch a** (the host reached port 3; the board's TX side is the question): (a1) `X-NIC<n>a` —
`CAP --out bench/2026-09-27/X-NIC<n>a --send 'sleep 3 ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15`,
at least 3 s for the board's own recovery; (a2) `X-L<n>a` — `FL <ip> ; PL <ip> ; DW none`. **No
re-attach.** If `X-L<n>a` reads 4 of 4, the invocation continues `--from` the cell after the
failed `-L` (the series' `-T` or `-C0`), and that series is void for ② (its `-L` reads the
failure; `rttseries` voids it). If not: branch b from its step 1.

**Branch b** (a frame the host sent did not reach port 3, or the host sent nothing, or the
classifier refused): card 2's read set, less the bracket S1 already read: (1) `X-SW<n>` —
`CAP --out bench/2026-09-27/X-SW<n> --send 'cat /proc/rtl819x-switch' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12`,
first, since this read clears `PSRP` bit 8 on switch driver 1.1; (2) `X-PHY<n>` —
`CAP --out bench/2026-09-27/X-PHY<n> --send 'echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12`
(port 3's `BMCR`, and `BMSR` twice: its link bit latches low until read); (3) `X-PS<n>` —
`CAP --out bench/2026-09-27/X-PS<n> --send 'cat /proc/rtl865x/port_status' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12`;
(4) `X-HN<n>` — `HN`. Then the recovery, a software action on the host that runs without the
owner's word (`CLAUDE.md` waits for it only for power and physical actions; block 48's § 6 ran
the same recovery so): (5) `X-RA<n>` — from PowerShell, `usbipd list` read fresh for the GbE
adapter's busid (never the CP2102's), `usbipd detach --busid <b>`,
`usbipd attach --wsl --busid <b>`, reading what each prints (right after a detach `usbipd list`
can read as a drop for about a second: re-read it), then `R0-ADDR`'s command in WSL; (6)
`X-SW<n>b`, `X-PHY<n>b`, `X-PS<n>b`, the text of (1)–(3) after it; (7) `X-TC<n>` —
`pgrep -xc tcpdump ; true`; (8) `X-L<n>` — `FL <ip> ; PL <ip> ; DW none`. If it passes, the
invocation continues `--from` the cell after the failed one, that series void, and the brackets
spanning the re-attach have their host side void (the adapter's counters restart). If it fails,
the arms that need the host are skipped: after a failure in `I-R`, `I-H` and `I-E` are not run;
`I-Z` and `I-C9` run, and the power-off between them goes by the owner's handshake: for every
power-on and power-off the session tells the owner and STOPS until the owner replies; only then
does it open the catch (or the power-off window) in the background, confirm from the transcript
that the ESC-streaming cell is running, and then tell the owner "catch open — power on now" (or
"power off now"); the owner acts only on that word. No count-to-five after the reply, and
nothing physical happens between the reply and the session's "now".

**After an episode**, of either branch: the first path gate after it (the `-D` whose pair spans
the episode) is a reading, never a second episode — `covered no` there sends no read set, the
invocation continues `--from` the next cell, and that series is void. **In `I-E`** the same
cells run against 10.1.1.4: `X-NIC<n>` then reads `rlx0`'s page, still printed after `H-DOWN`
because `nic_ndo_stop` leaves the ring allocated (讀 `66ddb93`), so `s1class` parses it but it
says nothing of `eth4`'s ring; the branch rule reads only the host and port 3, the same for
both drivers, and branch a's 3 s is the vendor driver's chance to recover before anything on
the host is touched.

S1's positive controls are `s1class`'s self-test cases, run in `R0-ST`: block 48's `D3-LUS1-L`
(`D3-LUR1-R` → `X-BR1`, host tx 6, port 3 rx 6) reads branch a, and block 46 from `A2-02-R` →
`A2-03-R` (`NET-124`'s onset: host tx 20, port 3 rx 0) reads branch b at every one of its 55
pairs.

**What each other stop means, decided now** — a repeat is always a new name, declared in
`bench/2026-09-27/CORRECTIONS-block49.md` before it runs, **except the cells whose text this
section fixes now (logged there as they run) and a power-off, which this card decides now and
which waits only for the owner's reply**. Every power-off below goes by the owner's handshake:
for every power-on and power-off the session tells the owner and STOPS until the owner replies;
only then does it open the catch (or the power-off window) in the background, confirm from the
transcript that the ESC-streaming cell is running, and then tell the owner "catch open — power
on now" (or "power off now"); the owner acts only on that word. No count-to-five after the
reply, and nothing physical happens between the reply and the session's "now".

* **The loader gate on any board cell** (the capture holds `Booting...`, `---RealTek`,
  `<RealTek>` or `Linux version`), the same text in any other failed board cell's capture,
  which is read first, or a watch's or a power-off window's log holding the loader's banner
  before its `<RealTek>`, or a `<RealTek>` alone in a watch opened while the board last ran a
  kernel (*The watch*): the board has reset. The watch that followed that cell on its command
  line is read at once: `<RealTek>` in it, the loader was caught at its prompt and waits there
  (the banner may be in the cell's capture rather than the watch's), and no further watch is
  opened; not, the vendor firmware may be booting (§ 0 ⑦, what it does not cover), and the
  watch still runs. Either way **the owner is asked to power off at once** — the session's
  first action, before any other cell and any `CORRECTIONS` entry — the watch holding the
  console meanwhile if it still runs, and with no window if the loader waits at its prompt
  (*The watch*), by the owner's handshake: for every power-on and power-off the session tells
  the owner and STOPS until the owner replies; only then does it open the catch (or the
  power-off window) in the background, confirm from the transcript that the ESC-streaming cell
  is running, and then tell the owner "catch open — power on now" (or "power off now"); the
  owner acts only on that word. No count-to-five after the reply, and nothing physical happens
  between the reply and the session's "now". The stop interrupts that invocation's captures and
  probe; `I-Z` does not run, `I-C9` does, and the next card's first map closes this press's
  bracket.
* **`R0-PREC`**, **`R0-ADDR`**, **`R0-FL`**, **`R0-PCAP`**, **`R0-TCPC`**: card 2's; no power
  until each reads as its gate asks. **`R0-DMSG`** `0`: the follower is not running — start it
  ((4)) and run `R0-DMSG2`; `2` or more: another `dmesg` runs, its owner stops it.
  **`R0-DW0`**: an empty log or `follower` not 1 — no power until (4) is redone; a non-zero
  gated signature with the board off — no power; WSL restarted and both devices re-attached
  once more, and if the fresh log is still not clean the owner decides. **`R0-SUM`**,
  **`R0-ST`**: a checker is not the one this card pins, or fails its own self-test — no power.
* **`Z0-HCW`**, **`Z0-TSD`**, **`Z0-HCG`**: block 44's. The guard refusing: no power; after 10
  minutes the same line once more as the declared off-card cell `Z0-HCG2`; a second refusal: no
  power, and the owner decides the day. `timesyncd` is started again (`Z9-TSD`'s text) whenever
  the seating ends.
* **`gate:caught`** on `A1-CATCH`: the catch did not catch the loader, and the chain's watch
  `X-W1` is read at once — the loader's banner before `<RealTek>` in it, a press after the
  catch's stream was caught there and nothing booted; `<RealTek>` with no banner before it, the
  board already waited at the loader's prompt when `X-W1` opened; neither, the loader may have
  autobooted the vendor, unless the owner had not yet pressed (their report is data). Either
  way power off — with no window in the first two cases, the loader waiting at its prompt (*The
  watch*) — by the owner's handshake: for every power-on and power-off the session tells the
  owner and STOPS until the owner replies; only then does it open the catch (or the power-off
  window) in the background, confirm from the transcript that the ESC-streaming cell is
  running, and then tell the owner "catch open — power on now" (or "power off now"); the owner
  acts only on that word. No count-to-five after the reply, and nothing physical happens
  between the reply and the session's "now". The press is lost, and the next card's first map
  brackets that boot.
* **`A1-FL`**: the same command once more as `A1-FL2` — the board waits at the loader's prompt,
  and `X-W1` has ended on the loader's reply there, which records no reset (*The watch*); a
  second failure ends the press — power off, with no window, by the owner's handshake: for
  every power-on and power-off the session tells the owner and STOPS until the owner replies;
  only then does it open the catch (or the power-off window) in the background, confirm from
  the transcript that the ESC-streaming cell is running, and then tell the owner "catch open —
  power on now" (or "power off now"); the owner acts only on that word. No count-to-five after
  the reply, and nothing physical happens between the reply and the session's "now".
* **A background cell's start** (`W-TCPD`, `W-TCPE`, `A1-HP`: no start signal in 20 s): the
  invocation stops before the round, the board waiting at the loader's prompt, and the press is
  a new card; the owner powers off, with no window (*The watch*), by the owner's handshake: for
  every power-on and power-off the session tells the owner and STOPS until the owner replies;
  only then does it open the catch (or the power-off window) in the background, confirm from
  the transcript that the ESC-streaming cell is running, and then tell the owner "catch open —
  power on now" (or "power off now"); the owner acts only on that word. No count-to-five after
  the reply, and nothing physical happens between the reply and the session's "now".
* **Any stop of `I-1` between `W-TCPD`'s start and `W-TCPX`** interrupts both captures and the
  probe (the runner signals every background cell of the invocation it stops): ③ is then
  unmeasured on this boot — its capture ended before its read — and ① is read if the probe
  recorded the first reply, and the text capture its frames, before the stop.
* **`A1Q`'s exit**: its artefacts are the reading; if its round reached `rlxfw`'s prompt, `I-1`
  continues `--from A1-HPX` (the probe already stopped: its last line reads `stop`); if not,
  the rest is a new card, and the power-off goes — with no window if `A1Q` stopped before its
  `J`, with no `A1Q-boot` capture, the board then at the loader's prompt (*The watch*) — by the
  owner's handshake: for every power-on and power-off the session tells the owner and STOPS
  until the owner replies; only then does it open the catch (or the power-off window) in the
  background, confirm from the transcript that the ESC-streaming cell is running, and then tell
  the owner "catch open — power on now" (or "power off now"); the owner acts only on that word.
  No count-to-five after the reply, and nothing physical happens between the reply and the
  session's "now".
* **`A1-HPX`'s `hpstop`**: `pkill -INT -f 'A1-HP --target'` once more as `A1-HPX2`, and the
  invocation continues `--from B-AC0-P`, ③ unmeasured as above.
* **A board bracket's gate** (`until`, `version`, `nd_up`) with no loader text: the watch holds
  the console first (*The watch*: until 90 s after the read ended, whether it ended silent or
  on its text); then `/dev/ttyUSB0` is checked and the read typed again as its **stand-in
  `X-<read>`**; if it passes, it stands in and the invocation continues `--from` the next cell
  (every pair after it names `X-<read>` right after `<read>`). A stand-in for `B-AC0-R` does
  not stand in for ③, which is then unmeasured on this boot. **If the stand-in returns nothing,
  garbage, or never ends on the prompt, the owner is asked to power off**, by the owner's
  handshake: for every power-on and power-off the session tells the owner and STOPS until the
  owner replies; only then does it open the catch (or the power-off window) in the background,
  confirm from the transcript that the ESC-streaming cell is running, and then tell the owner
  "catch open — power on now" (or "power off now"); the owner acts only on that word. No
  count-to-five after the reply, and nothing physical happens between the reply and the
  session's "now".
* **`W-TCPC`** (a `tcpdump` still running after ③'s stop): `X-KILL<n>` —
  `sudo -n pkill -KILL -x tcpdump ; sleep 1 ; pgrep -xc tcpdump ; true` — once; `0`: the
  invocation continues `--from W-EWALL` and ③'s anchor is read as `pcapwin` finds it; not `0`:
  no cell of `I-R` runs until the owner has read it.
* **A series' capture start** (`-T`: no start signal in 20 s): the invocation stops; it
  continues `--from` that series' `-C0`, the series runs in its on-slot with no capture, and
  `rttseries` voids it (`-C0` reads 0). **A series' capture stop** (`-X` not `0`): `X-KILL<n>`
  as above; `0`: continue `--from` the series' `-P`; not `0`: no further series runs until the
  owner has read it.
* **A path gate** (`-D`: `covered no`) or **a port-3 gate** (`-LS`): the host → board path is
  the question by construction — branch b from its step 1, then the same continuation (a
  path-gate failure voids its series) — except a path gate whose pair spans an S1 episode (a
  reading, above), and a port-3 gate whose capture holds no `PSRP3` row or no port-3 line of
  `port_status` at all: that capture ended silent (*The watch*), not with a finding about the
  page — the switch driver is byte-identical to the one whose page block 48's gates matched 28
  times on `r6b2q` (§ 1) — and is handled as a bracket's silent read: after the watch's hold of
  90 s, `/dev/ttyUSB0` is checked and the read typed again as its stand-in `X-R-LS` or
  `X-E-LS`, read as the gate reads it — both `LinkUp`, the invocation continues `--from` the
  next cell; silent again, or garbage, the owner is asked to power off. A row present and not
  `LinkUp`, in the gate's capture or its stand-in's, is branch b.
* **`H-DOWN`** or **`H-ETH4`**'s gate with no loader text: the page is read, `X-RT<n>` —
  `CAP --out bench/2026-09-27/X-RT<n> --send 'cat /proc/interrupts' --idle 3 --until 'Booting\.\.\.|---RealTek' --seconds 12`
  (after the watch's hold of 90 s, *The watch*); if `eth4` is up at 10.1.1.4 with IRQ 12, `I-E`
  runs; if not, `I-E` is not run and `I-Z` runs.
* **The maps and `n_writes`**: block 46's rules with this card's names — a map repeated once as
  `A1-M0B`/`A1-MB0B` (or `A1-M1B`/`A1-MB1B`) on `until`, after the watch's hold of 90 s (*The
  watch*); another digest or group line: the owner is told, and nothing boots the vendor until
  it has been read; an `n_writes` other than 0: the owner is told, and the press ends at a
  power-off by the owner's handshake: for every power-on and power-off the session tells the
  owner and STOPS until the owner replies; only then does it open the catch (or the power-off
  window) in the background, confirm from the transcript that the ESC-streaming cell is
  running, and then tell the owner "catch open — power on now" (or "power off now"); the owner
  acts only on that word. No count-to-five after the reply, and nothing physical happens
  between the reply and the session's "now".
* **WSL itself stops mid-press**: the console is unwatched from that moment until a watch runs
  again (§ 0 ⑦), so, in this order: WSL started again with (3)'s keeper; `usbipd list` read
  fresh, and each device no longer attached attached again, the CP2102 first, the GbE adapter
  as branch b's (5); `X-PRE<n>` —
  `CAP --out bench/2026-09-27/X-PRE<n> --until 'Booting\.\.\.|---RealTek' --seconds 3` — with
  the board on, the throwaway capture a re-attach needs, then the watch at once — unless the
  board's last known state is the loader's prompt, where no watch is opened (*The watch*); the
  follower restarted with (4)'s command with `dmesg -W >>` in place of `dmesg -w >`, as in S1 —
  only messages newer than its start, whether or not the WSL kernel restarted, so no line is
  counted twice — and every kernel-log window since the last `follower 1` void, the next one
  included. The interrupted invocation continues `--from` the interrupted cell if that cell
  left no log, else a board read is typed as its stand-in and a host cell's partial log stands;
  the bracket spanning the outage is void, and so is ③'s anchor if ③'s capture was running.
* **A host reading, a checker's reading, a series**: `NAME?`; never a stop. **A background
  cell's exit** never stops a run.
* **Anything not listed**: no cell runs until the owner has read it; the decision goes into
  `CORRECTIONS-block49.md` first.

**Re-dating — what scheduling this draft changes, and nothing else.** The card is generated by
`gencard43a.py` from one table; its date is one parameter. Scheduling it for the day
`YYYY-MM-DD` in the directory `bench/<dir>/` is
`gencard43a.py bench/<dir>/PREDICTIONS-B51-block49.md <dir>`, `<dir>` the day or the day and
one letter, which changes exactly: the declared date and the `declared-date` `cardnum` row (the
day, never the letter), and the draft's sentence after the declared date, which goes; the
directory `bench/2026-09-27/` → `bench/<dir>/` in every cell line (274 lines of the `cells`
fence, every `CAP --out`, every `HOST` prefix, every log a host cell reads and every chained
list), in `LR`'s `--out-dir`, in the `rttseries` and `boot-timeline` directory arguments, in
§ 4's and § 6's `CORRECTIONS` path, and in every `cardnum` expression that names the card's
directory or path (regex-escaped in a pattern); the card's own path. Nothing else moves: no
prediction depends on the date (① compares with seating B's RAW values, ② with seating A's and
seating B's, ③ is exact), and the transcripts' and captures' directories under `$FWRE_WORK` are
not dated. The paragraphs that hold the directory re-wrap, so lines move and the line count can
change; the desk test `$FWRE_WORK/rebuild/s113/card43a/t-redate.sh` generates the card for
`2026-09-27`, compares it with the draft word by word with those substitutions undone, and
finds no other difference. Constraints on the date, checked before the freeze: not 2026-09-23
or 2026-09-25 (① needs a third calendar day besides seatings A and B; `capdate` checks the
captures' day against the directory), and a directory name no other card uses — this card is
the day's first card, so its directory is the bare day (`2026-09-27` on 2026-09-27), and card
B's, if card B is pressed the same day, is the day and the next letter, as block 48's
`bench/2026-09-26b/` (`capdate` reads the day before the letter). The freeze commit also gives
the directory its row in `bench/README.md`'s index: without it `capdate`'s `D4` reads the
directory *on disk and not in the index*, and the desk test reads `capdate` both without that
row and with it. After re-dating: `cardcheck numbers` and `commands`, `check-predictions`,
every `runblock --dry`, `drycheck`, `fromcheck` and `capdate`, all re-run on the new file.

---

## § 7 What this block does not establish

* **① on more than one cold boot.** n = 1 against seating B's two; P4's range is seating B's
  eight quiet boots, so *inside* is weak evidence (7/9 by chance alone), and the row is decided
  by the list's stability rule over three points, not by a distribution of cold widths. Whether
  the host's ARP phase or the board's `N-NDOPEN` moved, if it lies outside, is not separated
  beyond what the frames show.
* **Why `rlx0`'s rtt moved between the days** (`NET-121`), beyond the capture's part on one
  boot. ② compares the capture's two states within one boot and the no-capture state with
  seating A; a host-side cause other than the capture (the WSL kernel, the adapter's state) is
  not separated from a board-side one.
* **The capture's effect below this design's resolution.** Six series a state against seating
  A's series spread per size (2.7–9.9 %, and 14.4 % at 56 B): an effect of a few percent reads
  `unresolved`, and the card says so rather than calling it absent.
* **`eth4`'s rtt against any earlier day**: no prior series exists on this kernel. The vendor
  firmware's rtt is not measured (⊘, § 0 ①).
* **③ beyond one healthy boot**, and the rows' premise — that the switch's counters count from
  the board's first frame of the boot — beyond this boot and the three it rests on.
* **A frame the host adapter dropped before counting it** (`r8153_ecm` has no tally counters);
  why `NET-124` happened, unless it happens again; the mechanism of a 1.4 TX stall, if S1's
  branch a fires.
* **`D3-MISS` ②'s `1472|mdev` row**: its A median is a captured series and a 20-echo mdev's own
  sampling error (推 about 16 %) is wider than the ±10 % band, so this card publishes its scores
  and does not close it; nor does it close ① on a width read at k other than 2 (§ 3.4).
* **One `lowers` as proof of an effect**: with no effect anywhere, one of five sizes reads
  `lowers` with probability up to 0.103 (§ 3.5); and **equal spacing in time** of the on- and
  off-series: an on-series' slot is about 1.5 s longer, so ABBA balances a drift linear in the
  series' order, not exactly one linear in time.
* **`eth4`'s TX state on a failed `I-E` liveness gate**: S1 reads only the host, port 3 and
  `rlx0`'s idle page.
* **Containment of every reset** (§ 0 ⑦, what it does not cover): a reset from a cause other
  than `BOOTGUARD` inside a board cell, which ends that cell on the banner with no ESC
  streaming, the watch that follows possibly opening after the loader's window; the same reset
  in one of the 35 host stretches inside the press's invocations, where no capture is open (24
  of them a series', up to 54.7 s each, 191 s in all nominally), or in a gap of up to about 30
  s outside an invocation between a watch's stop and the next capture, or while the board waits
  at the loader's prompt with nothing streaming ESC; a kernel that stops after the board
  capture a stop's hold counts from, whose bite can fall inside the next board cell the session
  types or a continuation's first host stretch; the console while WSL itself is down; and what
  streaming ESC into `ash` for an hour does, which is 推.
* **`D1`, `D2`, `D3`**: none is carried by this image.
* A flash write by anything but `rlxfw`'s SPI driver between the two maps that the map does not
  see (`FLS-30`'s limits), an uncaught vendor boot's included (§ 0 ⑦: its flash effect is 推);
  `H601`'s 8,192 B are never hashed.

---

```cells
bench/2026-09-27/R0-PRE
bench/2026-09-27/R0-PREC
bench/2026-09-27/R0-ADDR
bench/2026-09-27/R0-ETH
bench/2026-09-27/R0-EVICT
bench/2026-09-27/R0-TCPC
bench/2026-09-27/R0-DMSG
bench/2026-09-27/R0-DW0
bench/2026-09-27/R0-FL
bench/2026-09-27/R0-PCAP
bench/2026-09-27/R0-SUM
bench/2026-09-27/R0-ST
bench/2026-09-27/R0-H
bench/2026-09-27/Z0-HC
bench/2026-09-27/Z0-HCW
bench/2026-09-27/Z0-TSD
bench/2026-09-27/Z0-HCG
bench/2026-09-27/A1-CATCH
bench/2026-09-27/A1-FL
bench/2026-09-27/W-TCPD
bench/2026-09-27/W-TCPE
bench/2026-09-27/A1-HP
bench/2026-09-27/A1Q
bench/2026-09-27/A1-HPX
bench/2026-09-27/B-AC0-P
bench/2026-09-27/B-AC0-R
bench/2026-09-27/B-AC0-H
bench/2026-09-27/W-TCPX
bench/2026-09-27/W-TCPC
bench/2026-09-27/W-EWALL
bench/2026-09-27/W-EORD
bench/2026-09-27/W3
bench/2026-09-27/A1-PS
bench/2026-09-27/A1-M0
bench/2026-09-27/A1-MB0
bench/2026-09-27/A1-NW0
bench/2026-09-27/R-LS
bench/2026-09-27/R-S01-L
bench/2026-09-27/R-S01-C0
bench/2026-09-27/R-S01
bench/2026-09-27/R-S01-C1
bench/2026-09-27/R-S01-P
bench/2026-09-27/R-S01-R
bench/2026-09-27/R-S01-H
bench/2026-09-27/R-S01-D
bench/2026-09-27/R-S02-L
bench/2026-09-27/R-S02-T
bench/2026-09-27/R-S02-C0
bench/2026-09-27/R-S02
bench/2026-09-27/R-S02-C1
bench/2026-09-27/R-S02-X
bench/2026-09-27/R-S02-P
bench/2026-09-27/R-S02-R
bench/2026-09-27/R-S02-H
bench/2026-09-27/R-S02-D
bench/2026-09-27/R-S03-L
bench/2026-09-27/R-S03-T
bench/2026-09-27/R-S03-C0
bench/2026-09-27/R-S03
bench/2026-09-27/R-S03-C1
bench/2026-09-27/R-S03-X
bench/2026-09-27/R-S03-P
bench/2026-09-27/R-S03-R
bench/2026-09-27/R-S03-H
bench/2026-09-27/R-S03-D
bench/2026-09-27/R-S04-L
bench/2026-09-27/R-S04-C0
bench/2026-09-27/R-S04
bench/2026-09-27/R-S04-C1
bench/2026-09-27/R-S04-P
bench/2026-09-27/R-S04-R
bench/2026-09-27/R-S04-H
bench/2026-09-27/R-S04-D
bench/2026-09-27/R-S05-L
bench/2026-09-27/R-S05-C0
bench/2026-09-27/R-S05
bench/2026-09-27/R-S05-C1
bench/2026-09-27/R-S05-P
bench/2026-09-27/R-S05-R
bench/2026-09-27/R-S05-H
bench/2026-09-27/R-S05-D
bench/2026-09-27/R-S06-L
bench/2026-09-27/R-S06-T
bench/2026-09-27/R-S06-C0
bench/2026-09-27/R-S06
bench/2026-09-27/R-S06-C1
bench/2026-09-27/R-S06-X
bench/2026-09-27/R-S06-P
bench/2026-09-27/R-S06-R
bench/2026-09-27/R-S06-H
bench/2026-09-27/R-S06-D
bench/2026-09-27/R-S07-L
bench/2026-09-27/R-S07-T
bench/2026-09-27/R-S07-C0
bench/2026-09-27/R-S07
bench/2026-09-27/R-S07-C1
bench/2026-09-27/R-S07-X
bench/2026-09-27/R-S07-P
bench/2026-09-27/R-S07-R
bench/2026-09-27/R-S07-H
bench/2026-09-27/R-S07-D
bench/2026-09-27/R-S08-L
bench/2026-09-27/R-S08-C0
bench/2026-09-27/R-S08
bench/2026-09-27/R-S08-C1
bench/2026-09-27/R-S08-P
bench/2026-09-27/R-S08-R
bench/2026-09-27/R-S08-H
bench/2026-09-27/R-S08-D
bench/2026-09-27/R-S09-L
bench/2026-09-27/R-S09-C0
bench/2026-09-27/R-S09
bench/2026-09-27/R-S09-C1
bench/2026-09-27/R-S09-P
bench/2026-09-27/R-S09-R
bench/2026-09-27/R-S09-H
bench/2026-09-27/R-S09-D
bench/2026-09-27/R-S10-L
bench/2026-09-27/R-S10-T
bench/2026-09-27/R-S10-C0
bench/2026-09-27/R-S10
bench/2026-09-27/R-S10-C1
bench/2026-09-27/R-S10-X
bench/2026-09-27/R-S10-P
bench/2026-09-27/R-S10-R
bench/2026-09-27/R-S10-H
bench/2026-09-27/R-S10-D
bench/2026-09-27/R-S11-L
bench/2026-09-27/R-S11-T
bench/2026-09-27/R-S11-C0
bench/2026-09-27/R-S11
bench/2026-09-27/R-S11-C1
bench/2026-09-27/R-S11-X
bench/2026-09-27/R-S11-P
bench/2026-09-27/R-S11-R
bench/2026-09-27/R-S11-H
bench/2026-09-27/R-S11-D
bench/2026-09-27/R-S12-L
bench/2026-09-27/R-S12-C0
bench/2026-09-27/R-S12
bench/2026-09-27/R-S12-C1
bench/2026-09-27/R-S12-P
bench/2026-09-27/R-S12-R
bench/2026-09-27/R-S12-H
bench/2026-09-27/R-S12-D
bench/2026-09-27/R-RTS
bench/2026-09-27/H-DOWN
bench/2026-09-27/H-ETH4
bench/2026-09-27/E-LS
bench/2026-09-27/E-00-P
bench/2026-09-27/E-00-R
bench/2026-09-27/E-00-H
bench/2026-09-27/E-S01-L
bench/2026-09-27/E-S01-C0
bench/2026-09-27/E-S01
bench/2026-09-27/E-S01-C1
bench/2026-09-27/E-S01-P
bench/2026-09-27/E-S01-R
bench/2026-09-27/E-S01-H
bench/2026-09-27/E-S01-D
bench/2026-09-27/E-S02-L
bench/2026-09-27/E-S02-T
bench/2026-09-27/E-S02-C0
bench/2026-09-27/E-S02
bench/2026-09-27/E-S02-C1
bench/2026-09-27/E-S02-X
bench/2026-09-27/E-S02-P
bench/2026-09-27/E-S02-R
bench/2026-09-27/E-S02-H
bench/2026-09-27/E-S02-D
bench/2026-09-27/E-S03-L
bench/2026-09-27/E-S03-T
bench/2026-09-27/E-S03-C0
bench/2026-09-27/E-S03
bench/2026-09-27/E-S03-C1
bench/2026-09-27/E-S03-X
bench/2026-09-27/E-S03-P
bench/2026-09-27/E-S03-R
bench/2026-09-27/E-S03-H
bench/2026-09-27/E-S03-D
bench/2026-09-27/E-S04-L
bench/2026-09-27/E-S04-C0
bench/2026-09-27/E-S04
bench/2026-09-27/E-S04-C1
bench/2026-09-27/E-S04-P
bench/2026-09-27/E-S04-R
bench/2026-09-27/E-S04-H
bench/2026-09-27/E-S04-D
bench/2026-09-27/E-S05-L
bench/2026-09-27/E-S05-C0
bench/2026-09-27/E-S05
bench/2026-09-27/E-S05-C1
bench/2026-09-27/E-S05-P
bench/2026-09-27/E-S05-R
bench/2026-09-27/E-S05-H
bench/2026-09-27/E-S05-D
bench/2026-09-27/E-S06-L
bench/2026-09-27/E-S06-T
bench/2026-09-27/E-S06-C0
bench/2026-09-27/E-S06
bench/2026-09-27/E-S06-C1
bench/2026-09-27/E-S06-X
bench/2026-09-27/E-S06-P
bench/2026-09-27/E-S06-R
bench/2026-09-27/E-S06-H
bench/2026-09-27/E-S06-D
bench/2026-09-27/E-S07-L
bench/2026-09-27/E-S07-T
bench/2026-09-27/E-S07-C0
bench/2026-09-27/E-S07
bench/2026-09-27/E-S07-C1
bench/2026-09-27/E-S07-X
bench/2026-09-27/E-S07-P
bench/2026-09-27/E-S07-R
bench/2026-09-27/E-S07-H
bench/2026-09-27/E-S07-D
bench/2026-09-27/E-S08-L
bench/2026-09-27/E-S08-C0
bench/2026-09-27/E-S08
bench/2026-09-27/E-S08-C1
bench/2026-09-27/E-S08-P
bench/2026-09-27/E-S08-R
bench/2026-09-27/E-S08-H
bench/2026-09-27/E-S08-D
bench/2026-09-27/E-S09-L
bench/2026-09-27/E-S09-C0
bench/2026-09-27/E-S09
bench/2026-09-27/E-S09-C1
bench/2026-09-27/E-S09-P
bench/2026-09-27/E-S09-R
bench/2026-09-27/E-S09-H
bench/2026-09-27/E-S09-D
bench/2026-09-27/E-S10-L
bench/2026-09-27/E-S10-T
bench/2026-09-27/E-S10-C0
bench/2026-09-27/E-S10
bench/2026-09-27/E-S10-C1
bench/2026-09-27/E-S10-X
bench/2026-09-27/E-S10-P
bench/2026-09-27/E-S10-R
bench/2026-09-27/E-S10-H
bench/2026-09-27/E-S10-D
bench/2026-09-27/E-S11-L
bench/2026-09-27/E-S11-T
bench/2026-09-27/E-S11-C0
bench/2026-09-27/E-S11
bench/2026-09-27/E-S11-C1
bench/2026-09-27/E-S11-X
bench/2026-09-27/E-S11-P
bench/2026-09-27/E-S11-R
bench/2026-09-27/E-S11-H
bench/2026-09-27/E-S11-D
bench/2026-09-27/E-S12-L
bench/2026-09-27/E-S12-C0
bench/2026-09-27/E-S12
bench/2026-09-27/E-S12-C1
bench/2026-09-27/E-S12-P
bench/2026-09-27/E-S12-R
bench/2026-09-27/E-S12-H
bench/2026-09-27/E-S12-D
bench/2026-09-27/E-RTS
bench/2026-09-27/A1-M1
bench/2026-09-27/A1-MB1
bench/2026-09-27/A1-NW1
bench/2026-09-27/Z-DW
bench/2026-09-27/Z-DWALL
bench/2026-09-27/Z9-HCX
bench/2026-09-27/Z9-HCR
bench/2026-09-27/Z9-TSD
bench/2026-09-27/Z9-D2
bench/2026-09-27/Z9-W1
bench/2026-09-27/A1Q-ab2
bench/2026-09-27/A1Q-2a
bench/2026-09-27/A1Q-boot
```

```cardnum
cells-fence	274	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^bench/2026\-09\-27/
declared-date	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md [*][*]declared date 2026-09-27[*][*]
presses-caught	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out bench/2026\-09\-27/A1-CATCH -{2}esc-after 360 -{2}esc-period 0\.002 -{2}until '<RealTek>' -{2}seconds 380$
cap-cells	37	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out
host-cells	234	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST&? bench/2026\-09\-27/
send-over-127	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*AUTOBURN
no-esc-after-but-catch	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out (?!bench/2026\-09\-27/A1-CATCH ).*-{2}esc-after
esc-after-cells	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP .*-{2}esc-after
no-watchdog-cell	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*(watchdog|rtl819x-wdt)
no-mark-gate	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=RLXFW-
no-driver-verb	0	count bench/2026-09-27/PREDICTIONS-B51-block49.md -{2}send '[^']*> /proc/rtl819x-nic
board-brackets	26	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out bench/2026\-09\-27/\S+-R[0-9]? -{2}send 'sleep\ 2\ ;\ cat\ /proc/rtl819x\-nic\ /proc/net/snmp\ /proc/net/arp\ /proc/rtl865x/asicCounter\ /proc/rtl819x\-nic' -{2}until 'rx_ph4\ \[0\-9A\-F\]\{8\}\(\?:\\r\\n\)\+\#\ \|Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds 15$
host-pre-reads	26	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/\S+-P[0-9]? :: HP$
loader-gates	35	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
liveness-cells	24	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/\S+-L :: FL 10[.]1[.]1[.][34] ; PL 10[.]1[.]1[.][34] ; DW 
series-cells	24	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/[RE]-S[0-9][0-9] :: ICMP 10[.]1[.]1[.][34]$
series-rlx0	12	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/R-S[0-9][0-9] :: ICMP 10[.]1[.]1[.]3$
series-eth4	12	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/E-S[0-9][0-9] :: ICMP 10[.]1[.]1[.]4$
capture-starts	12	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST& bench/2026\-09\-27/[RE]-S[0-9][0-9]-T :: TDT$
capture-stops	12	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/[RE]-S[0-9][0-9]-X :: sudo -n pkill -INT -x tcpdump && sleep 1 ; pgrep -xc tcpdump ; true$
state-reads	48	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/[RE]-S[0-9][0-9]-C[01] :: pgrep -xc tcpdump ; true$
path-gates	24	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\^path p3 rx d .*:[RE]-S[0-9][0-9]-D$
follower-gates	25	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\^follower 1\$:
port3-gates	2	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\^Port3 Force Mode disable
psrp3-gates	2	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\^r PSRP3 
icmp-macro	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
icmp-macro-b44	1	count bench/2026-09-25/PREDICTIONS-B46-block44.md ^`ICMP <ip>` = `for s in 56 256 512 1024 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
tdt-macro	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^`TDT` = `timeout 900 sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or [(]arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0[)] or [(]arp and arp\[6:2\] = 2 and [(][(]arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657[)] or [(]arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8[)][)][)]'`
tdt-filter-b44	2	count bench/2026-09-25/PREDICTIONS-B46-block44.md sudo -n tcpdump -n -tt -i enxfc19286184c9 'icmp or [(]arp and arp\[6:2\] = 1 and arp\[18:4\] = 0 and arp\[22:2\] = 0[)] or [(]arp and arp\[6:2\] = 2 and [(][(]arp\[8:4\] = 0x02524c58 and arp\[12:2\] = 0x4657[)] or [(]arp\[8:4\] = 0x560a0101 and arp\[12:2\] = 0x01e8[)][)][)]'$
tde-macro	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^`TDE <f>` = `timeout 900 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s113/card43a/pcap/<f> ether src 02:52:4c:58:46:57`
pl-macro	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^`PL <ip>` = `ping -I enxfc19286184c9 -c 4 -i 0[.]25 -W 1 -s 18 <ip>`
probe-cell	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST& bench/2026\-09\-27/A1-HP :: HPR -{2}out bench/2026\-09\-27/A1-HP -{2}target 10[.]1[.]1[.]3 -{2}seconds 900 -{2}icmp -{2}icmp-interval 0[.]05 -{2}neigh$
probe-cell-b44	1	count bench/2026-09-25/PREDICTIONS-B46-block44.md ^HOST& bench/2026-09-25/P3-HP :: HP -{2}out bench/2026-09-25/P3-HP -{2}target 10[.]1[.]1[.]3 -{2}seconds 300 -{2}icmp -{2}icmp-interval 0[.]05 -{2}neigh$
round-cell	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/A1Q :: LR -{2}cell A1Q QIMG -{2}iterations 1$
guard-gate	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^gate:grep=\^ {2}steps: timerfd 0, agreed with the rows 0, NO STEPS; :Z0-HCG$
guard-cell	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/Z0-HCG :: sleep 100 ; HCL run -{2}out bench/2026\-09\-27/Z0-HCG -{2}seconds 60 -{2}no-sntp 
b44-guard-refused	1	count bench/2026-09-25/Z0-HCG.log ^ {2}tick check: AGREE over 50 pair[(]s[)], worst -0[.]573 ppm, strong: 
b44-guard-permitted	1	count bench/2026-09-25/Z0-HCG2.log ^ {2}tick check: AGREE over 52 pair[(]s[)], worst [+]0[.]452 ppm, vacuous: 
b44-guard-no-steps	1	count bench/2026-09-25/Z0-HCG2.log ^ {2}steps: timerfd 0, agreed with the rows 0, NO STEPS; 
b44-guard-refused-no-steps	1	count bench/2026-09-25/Z0-HCG.log ^ {2}steps: timerfd 0, agreed with the rows 0, NO STEPS; 
hcstepctl-cases	5	count /home/key/fwre-work/rebuild/s113/card43a/selftest-hcstepctl.out ^ {2}ok {4}K[1-5] 
hcstepctl-k1	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-hcstepctl.out ^ {2}ok {4}K1 a step both detectors see [|] steps: timerfd 1, agreed with the rows 1, AGREE; positively controlled: yes [|] gate refuses$
hcstepctl-k4	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-hcstepctl.out ^ {2}ok {4}K4 no step [|] steps: timerfd 0, agreed with the rows 0, NO STEPS; .* [|] gate permits$
hcstepctl-gate-is-card	1	count /home/key/fwre-work/rebuild/s113/card43a/hcstepctl.py ^STEP_GATE = r"\^ {2}steps: timerfd 0, agreed with the rows 0, NO STEPS; "$
live-step-fw129	1	count SPEC.md 一次活的 [+]0[.]723937 s REALTIME 步進
live-step-clk40	1	count notes/boot-time.md ^ {2}[+]0[.]551906 s, seen by both of `hostclock`'s detectors
live-step-clk40-control	1	count notes/boot-time.md ^ {2}positively controlled on this kernel a second time
corr44-slew-834	1	count bench/2026-09-25/CORRECTIONS-block44.md the kernel's clock 8[.]34 % fast
notes-8-2-rows	1	count notes/boot-time.md 11,375 rows over RAW
notes-8-7-recon	1	count notes/boot-time.md reconstruction's ±14–28 ms
b44-corrections-hcg2	1	count bench/2026-09-25/CORRECTIONS-block44.md ^## § 1 `Z0-HCG` refused; `Z0-HCG2` runs
notes-8-2-no-step	1	count notes/boot-time.md 1,391 `adj` rows and [*][*]0 `step`$
notes-8-2-rate	1	count notes/boot-time.md 00:05:31 on −81[.]5…[+]97[.]8 ppm, except in the four dips, which reached −120[.]9 ppm
map-until-prompt	2	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out bench/2026\-09\-27/A1-M[01] .* -{2}until 'map_lines \[0-9\][+]\\r\\n# [|]Booting.{6}[|]---RealTek' -{2}seconds 60$
nw-cells	2	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out bench/2026\-09\-27/A1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}until 'Booting\\[.]\\[.]\\[.][|]---RealTek' -{2}seconds 15$
idle-cells-end-on-banner	7	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out .* -{2}idle 3 -{2}until 'Booting\\[.]\\[.]\\[.][|]---RealTek' 
idle-cells	7	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^CAP -{2}out .* -{2}idle 
probe-quiet-12	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md ^HOST bench/2026\-09\-27/A1-HPX :: pkill -INT -f 'A1-HP -{2}target' ; sleep 12 ; tail -n 1 
neigh-probe-ucast-only	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/core/neighbour.c ^\treturn [(]n->nud_state & NUD_PROBE [?]$
neigh-probe-ucast-only-2	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/core/neighbour.c ^\t\tp->ucast_probes :$
arp-delay-probe	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/arp.c ^\t\t[.]delay_probe_time =\t5 [*] HZ,$
arp-retrans	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/arp.c ^\t\t[.]retrans_time =\t1 [*] HZ,$
arp-ucast-probes	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/arp.c ^\t\t[.]ucast_probes =\t3,$
arp-mcast-probes	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/arp.c ^\t\t[.]mcast_probes =\t3,$
marks-66ddb93-no-net	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^marks-net 66ddb93 rlxfw-marks rows naming net/ipv4 or net/core 0; host-compat patches naming arp or neighbour 0 by name, 0 by content$
n3-marks-net-check-66ddb93	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^marks\-net\-check\ 66ddb93\ rlxfw\-marks\ rows\ naming\ net/ipv4\ or\ net/core\ 0\ \(control:\ rows\ naming\ drivers/net\ 2\);\ host\-compat\ files\ 7,\ naming\ arp\ or\ neighbour\ 0\ by\ name,\ 0\ by\ content,\ patching\ net/\ 0\ \(control:\ patching\ any\ file\ 7\)$
n3-marks-net-check-92aeaa8	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^marks\-net\-check\ 92aeaa8\ rlxfw\-marks\ rows\ naming\ net/ipv4\ or\ net/core\ 0\ \(control:\ rows\ naming\ drivers/net\ 2\);\ host\-compat\ files\ 7,\ naming\ arp\ or\ neighbour\ 0\ by\ name,\ 0\ by\ content,\ patching\ net/\ 0\ \(control:\ patching\ any\ file\ 7\)$
n3-rlxfw-src-check-66ddb93	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^rlxfw\-src\-check\ 66ddb93\ rlxfw's\ own\ kernel\ files\ under\ linux\-2\.6\.30/net/\ 0\ \(control:\ its\ files\ 11\)$
n3-rlxfw-src-check-92aeaa8	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^rlxfw\-src\-check\ 92aeaa8\ rlxfw's\ own\ kernel\ files\ under\ linux\-2\.6\.30/net/\ 0\ \(control:\ its\ files\ 12\)$
n3-kbuild-drop-66ddb93	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^kbuild\-drop\ 66ddb93\ DROP=\$SV/rtl819x\-toolchain\ lines\ 1$
n3-kbuild-drop-92aeaa8	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^kbuild\-drop\ 92aeaa8\ DROP=\$SV/rtl819x\-toolchain\ lines\ 1$
n3-vendor-drop-head	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^vendor\-drop\ HEAD\ 5c9be5d943318fdb4d048ae22078129594eb5a10\ CLONED\.tsv\ 5c9be5d943318fdb4d048ae22078129594eb5a10$
n3-vendor-drop-net-ipv4-arp-c	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^vendor\-drop\ net/ipv4/arp\.c\ HEAD\ blob\ =\ work\ tree\ yes;\ r6b2q\ cell's\ copy\ =\ the\ drop's\ yes\ \(sha256\ 073d5005a55b693d7cfb481a2258805503e170c43eec9b4551f6f249f9c0294c\)$
n3-vendor-drop-net-core-neighbour-c	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^vendor\-drop\ net/core/neighbour\.c\ HEAD\ blob\ =\ work\ tree\ yes;\ r6b2q\ cell's\ copy\ =\ the\ drop's\ yes\ \(sha256\ 1d5138e8e6f04b611c8a4f76d3eaa3c8ff01ff31db375583a0f9aad442099e3f\)$
stopctl-both-ended	1	count /home/key/fwre-work/rebuild/s113/card43a/stopctl/result.txt ^end: tcpdump processes 0$
stopctl-sigint	2	count /home/key/fwre-work/rebuild/s113/card43a/stopctl/result.txt ^SIGINT T[12] pid=
stopctl-summaries	2	count /home/key/fwre-work/rebuild/s113/card43a/stopctl/result.txt ^0 packets captured$
stopctl-after-stop	1	count /home/key/fwre-work/rebuild/s113/card43a/stopctl/result.txt ^after the stop: tcpdump processes 0$
sigctl-local	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^sigctl43a local: 8 of 8 as expected$
sigctl-amp-noshim	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^ok +amp-noshim\tstill running 10 s after SIGINT, no [.]meta[.]json; SIGINT ignored 1$
sigctl-amp-launcher	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^ok +amp-launcher\tended: interrupted; SIGINT ignored 0; restored, SIGINT SIGPIPE SIGXFSZ default$
sigctl-dfl-launcher	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^ok +dfl-launcher\tended: interrupted; SIGINT ignored 0; as started, SIGINT SIGPIPE SIGXFSZ default$
sigctl-off-launcher	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^ok +off-launcher\tX-OFF94 ended: interrupted; SIGINT ignored 0 / X-W95 ended: interrupted; SIGINT ignored 0$
sigctl-refuse-shim	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out/sigctl-local.out ^ok +refuse-broken-shim\trc 2; the line not run; its reason$
sigctl-harness-plain	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out-h/H97.row ^harness-plain\tended: interrupted; SIGINT ignored 0$
sigctl-harness-launcher	1	count /home/key/fwre-work/rebuild/s113/card43a/sigint/out-h/H98.row ^harness-launcher\tended: interrupted; SIGINT ignored 0$
sigctl-tool	b4649bd491bbefec8b0893caef4bd74a78fce8ec457b0b6e951eb9509ccbdadb	sha256 /home/key/fwre-work/rebuild/s113/card43a/sigctl43a.sh
sigctl-mkline	c389cf3d5308cb7bf2c72f4a0fb4699978e36699ef33f0d4309781b756c52776	sha256 /home/key/fwre-work/rebuild/s113/card43a/sigint/mkline.py
sigctl-ptyhold	85a94d414621c63f2a00692cc49f4dcddc44556ce2491f58ba501990cc66b35f	sha256 /home/key/fwre-work/rebuild/s113/card43a/sigint/ptyhold.py
net121-uncaptured	1	count SPEC.md 沒擷取 [+]7[.]2／[+]9[.]9 %、有擷取 [+]13[.]5／[+]19[.]7 %
net121-sd-16	1	count SPEC.md 每個 SD 約 16 %
net121-p3-p3	1	count SPEC.md `P3` 對 `P3` 在擷取的層次平均 [+]18[.]1 %（256 B）、[+]12[.]3 %（1,472 B）
notes-8-7-6of6	1	count notes/boot-time.md the cycle's second who-has in 6 of 6 framed boots
d3miss-204x	1	count PROGRESS.md its two seating-A values are 2[.]04× apart
d3miss-vendor-fw-void	1	count PROGRESS.md a vendor-firmware series is ⊘, since it changes kernel, userspace and configuration together
d3miss-b51-eth4	1	count PROGRESS.md seating 43's card B51 carries `eth4`'s series
log113-sec6	1	count LOG.md ^### 六、兩份設計審查與擁有者的裁示（2026-09-26）$
log113-two-presses	1	count LOG.md ^- seating 43：擁有者選兩次按壓（A `p2q`
log113-eth4-delegated	1	count LOG.md `D3-MISS` ② 的「廠商序列」擁有者交給我：`eth4`
b47-urb-302	1	count bench/2026-09-26/R0-DW0.log ^urb_104 302$
netup-arp-hi	1	count /home/key/fwre-work/rebuild/s111/netup/common.py ^ARP_LO, ARP_HI = 1[.]000, 1[.]028 
b46-spi-1.2	1	count bench/2026-09-25c/R1-NW0.log ^version rtl819x-spi 1[.]2
notes-b46-76	1	count notes/nic-driver.md P0's identities hold at 76 of 76 brackets
wdt-version	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-wdt.c ^#define RTL819X_WDT_VERSION\t"rtl819x-wdt 1[.]1"$
wdt-bootguard-armed	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-wdt.c ^\tif [(]bootguard[)] [{]$
wdt-late-initcall	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-wdt.c ^late_initcall[(]rtl819x_wdt_init[)];$
wdt-sysmap-bootguard	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.System.map ^[0-9a-f]{8} r __param_bootguard$
hold-src-clk08b	1	count SPEC.md ^[|] `CLK-08b` 🆕 [|] .*、9 = [*][*]84,001\.412 ms[*][*]
hold-src-banner	1	count bench/2026-09-26b/R1-CATCH.timing ^[0-9]+ 14\.986257$
hold-src-prompt	1	count bench/2026-09-26b/R1-CATCH.timing ^[0-9]+ 17\.274354$
wdt-mk6-obj-y	1	count config/rlxfw-marks.tsv ^MK6\tlinux-2[.]6[.]30/drivers/watchdog/Makefile\tafter\t.*\tobj-y [+]= rtl819x-wdt[.]o\t
wdt-config-watchdog	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/.config ^CONFIG_WATCHDOG=y$
wdt-config-no-wtdog	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/.config ^# CONFIG_RTL_WTDOG is not set$
spec-vdr1	1	count PROGRESS.md ^[|] `VDR-1` 🆕 [|]
vdr1-formsyscmd	1	count PROGRESS.md ^[|] `VDR-1` 🆕 [|] .*唯一實證的入口 `formSysCmd` 觸發後會把 `SYSCMD_SELECT` 寫進 `0x00C000` 的 `COMPCS`
fls30-nine-boots	1	count SPEC.md ^[|] `FLS-30` 🆕 [|] [*][*]九次原廠開機前後的三個 map bracket 全部與預測相同[*][*] [|] 量 2026-09-23
fls30-limits	1	count SPEC.md ^[|] `FLS-30` 🆕 [|] .*看不到：兩次互相抵銷的寫入、`H601`（map 不讀）、4,186,112 B 以外的位元組
p2-settled-5	1	count PROGRESS.md ^5[.] [*][*]A vendor boot writes flash only when its config self-test fails, and then$
c19-b48-zero-drops	1	count PROGRESS.md 🔄 2026-09-26 [(]block 48, `notes/nic-driver[.]md` § 27[.]10[)]: 212 console captures, 0 drops; six gaps longer than a minute, none followed by a drop; the trigger not exercised
c5ub-cell	1	count bench/2026-09-09/PREDICTIONS-B16-block15.md -{2}out bench/2026-09-09/C5-UB -{2}send 'sleep 400 > /dev/watchdog' -{2}esc-after 450 -{2}esc-period 0[.]01 -{2}until '<RealTek>'
escwin-tool	1	count tools/console-capture.py # The ESC window on this unit is ~4[.]9 s wide, banner to
watch-text	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md `CAP\ -{2}out\ bench/2026\-09\-27/X\-W<n>\ -{2}esc\-after\ 3600\ -{2}esc\-period\ 0\.01\ -{2}until\ '<RealTek>'\ -{2}seconds\ 3605`
offwin-text	1	count bench/2026-09-27/PREDICTIONS-B51-block49.md `CAP\ -{2}out\ bench/2026\-09\-27/X\-OFF<n>\ -{2}esc\-after\ 360\ -{2}esc\-period\ 0\.01\ -{2}until\ '<RealTek>'\ -{2}seconds\ 365`
gencard-paths	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^ {2}§ 6 paths checked 3282 
gencard-lists	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ; chained lists 123, 
gencard-captexts	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^ {2}console captures: § 6 texts 7 ending on the loader's banner, 2 streaming ESC ending on its prompt; controls fired 3$
gencard-stretch	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^ {2}resets: the longest host stretch plus the next board cell's cap is before R\-S02\-R: 7\.8 s nominal, 54\.7 s with every echo timed out, [+] 15 s cap = 69\.7 s, under the bite's 83\.8 s by 14\.1 s$
gencard-stretches	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ host\ stretches\ after\ the\ round,\ no\ capture\ open:\ 35,\ 24\ of\ them\ a\ series'\ \(6\.0\ to\ 7\.8\ s\ nominal\);\ 191\ s\ nominal\ in\ all;\ the\ longest\ nominal\ 12\.1\ s\ before\ B\-AC0\-R;\ the\ longest\ with\ every\ echo\ timed\ out\ 54\.7\ s$
gencard-estimate	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ estimate:\ the\ press\ 776\ s\ =\ 12\.9\ min,\ about\ 13\ min;\ the\ catch's\ 380\ s\ of\ it,\ and\ 2\ s\ between\ invocations\ 4\ times\ \(a\ guess\)$
gencard-onextra	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ on\-series\ extra:\ the\ \-X's\ sleep\ 1\ s\ \+\ the\ \-T's\ start\ 0\.5\ s\ \(a\ guess\)\ =\ 1\.5\ s$
gencard-handshake	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ the\ owner's\ handshake:\ its\ text\ 12\ times,\ §\ 0:\ 1,\ §\ 4:\ 1,\ §\ 6:\ 10;\ the\ control\ \(one\ word\ changed\)\ found\ 0\ and\ 11$
b46-map-cap-180	2	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/R1-M[01] .* -{2}seconds 180$
hcstepctl-planted-step	1	count /home/key/fwre-work/rebuild/s113/card43a/hcstepctl.py ^ {4}step = [(][(]1010[.]5, 1[.]4[)],[)]$
img-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^verdict\tgreen$
img-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
img-manifest-variant	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^variant\tquiet$
img-manifest-recipe	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^recipe_id\ta2c56bc8$
img-manifest-irfs	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^initramfs_manifest_sha256\t51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59$
img-record-nfjrom	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae$
img-record-vmlinux	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
img-record-clean	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
img-nfjrom-sha256	4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae	sha256 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
img-qimg-b46	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`$
img-sysmap-switch-proc	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.System.map ^[0-9a-f]{8} t rtl819x_sw_read_proc$
img-sysmap-port-status-proc	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.System.map ^[0-9a-f]{8} t port_status_read$
vendor-port-status-reader	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x/rtl865x_proc_debug.c ^\t+port_status_entry->read_proc = port_status_read;$
src-recipe-66ddb93	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^commit 66ddb93 2026-09-23T14:58 recipe a2c56bc8$
src-recipe-control-r6b2q	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^commit 92aeaa8 2026-09-26T06:44 recipe 06c39ca3$
src-recipe-control-r6b6q	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a.out ^commit 920875f 2026-09-26T14:20 recipe acf8ed3d$
src-nic-1.4	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]4"$
src-nic-nd-up-print	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-nic.c len [+]= sprintf[(]page [+] len, "nd_up %d[\\]n", nic_ndev_up[)];$
src-nic-nd-up-cleared	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-nic.c ^\tnic_ndev_up = 0;$
src-nic-ring-never-freed	0	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-nic.c nic_allocated = 0
b45-eth4-c-eq-o	1	count notes/nic-driver.md ^[|] vendor `eth4` [(]block 45[)] [|] D1-K8 → D1-K9 [|] 16,215 [|] 16,215 [|]
src-switch-1.1	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-switch.c ^#define RTL819X_SW_VERSION\t"rtl819x-switch 1[.]1"$
src-switch-psrp3-row	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-switch.c ^\t[{] "PSRP3",\t0x4134, 0, 0 [}],$
src-switch-linkup-bit	1	count /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-switch.c ^#define RTL819X_PSRP_LINKUP\t[(]1u << 4[)]$
src-switch-is-r6b2q-cell	38685f0a14854762aa3eb73636bd1417dec4ab9904e3e79cd2902ea22d258c1b	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x-switch.c
src-switch-sha	38685f0a14854762aa3eb73636bd1417dec4ab9904e3e79cd2902ea22d258c1b	sha256 /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-switch.c
src-nic-sha	e68999336dce354f1e3093d5e6f0ac18141badbc451af38b4da1387e352d4633	sha256 /home/key/fwre-work/rebuild/s113/card43a/src43a/rtl819x-nic.c
src-tool	edd5f3b8bcb32642e5903757a5450f2e99079f0235919752207a88b9944e612d	sha256 /home/key/fwre-work/rebuild/s113/card43a/src43a.sh
b46-id0	1	count bench/2026-09-25c/R1Q-boot.log ^RLXFW-ID0=A2C56BC8
b46-version-1.4	1	count bench/2026-09-25c/A1-00-R.log ^version rtl819x-nic 1[.]4$
b46-nd-up	2	count bench/2026-09-25c/A1-00-R.log ^nd_up 1$
b46-mb0	1	count bench/2026-09-25c/R1-MB0.log ^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46 {2}-$
b46-nw0	1	count bench/2026-09-25c/R1-NW0.log ^n_writes 0
b46-ps-sh	1	count bench/2026-09-25c/R1-PS.log ^ +1 0 +[0-9]+ S +/bin/sh
b46-zero-at-first-read	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-w3.out ^ {2}ok {3}R2 block 46's A1-00-R [(]the first read of a boot, driver 1[.]4[)]: every counter 0 
b44-eth4-inet	1	count bench/2026-09-25/P1-ETH4.log inet addr:10[.]1[.]1[.]4 
b44-eth4-irq	1	count bench/2026-09-25/P1-ETH4.log ^ +12: +[0-9]+ +RLX LOPI +eth4
b44-down-no-irq12	0	count bench/2026-09-25/P1-DOWN.log ^ +12: 
b44-eping	1	count bench/2026-09-25/P1-EPING.log ^4 packets transmitted, 4 received
b44-p3-tcpd-timeout	1	count bench/2026-09-25/PREDICTIONS-B46-block44.md ^HOST& bench/2026-09-25/P3-TCPD :: timeout 240 
b44-p3-icmp-20	5	count bench/2026-09-25/P3-ICMP.log ^20 packets transmitted, 20 received, 0% packet loss
b48-psrp3-live	1	count bench/2026-09-26b/D3-X-LS.log ^r PSRP3 +4134 000000F9 
d3-spread-56-avg	1	count docs/boot-time-d3-list.tsv ^D5a[|]rlxfw[|]56[|]avg.*face.0[.]144388.N
d3-spread-256-avg	1	count docs/boot-time-d3-list.tsv ^D5a[|]rlxfw[|]256[|]avg.*face.0[.]099473.N
d3-spread-1024-avg	1	count docs/boot-time-d3-list.tsv ^D5a[|]rlxfw[|]1024[|]avg.*face.0[.]026846.N
b48-ls-28	1	count notes/nic-driver.md all 28 port-3 gates read `PSRP3` LinkUp and `port_status` LinkUp
b48-p6-sl	1	count notes/nic-driver.md ^[*] [*][*]P6[*][*] holds, 4 of 4 [(]量[)]: `SL` at 60, 276, 1,513 and 1,514 read 20 of 20
b50-e2-losses	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md E2 at 1[.]4 lost the first 29 requests at 276 and the first 62 at 1,513
b48-lus1-l-failed	1	count bench/2026-09-26b/D3-LUS1-L.log ^4 packets transmitted, 0 received
b48-x-hp1-tx	1	count bench/2026-09-26b/X-HP1.log /statistics/tx_packets:397550$
b46-a2-03-p3-frozen	1	count bench/2026-09-25c/A2-03-R.log Unicast 1132 pkts, Multicast 2 pkts, Broadcast 13 pkts
notes-27-9	1	count notes/nic-driver.md ^### 27[.]9 The stop: the host reached the board, and the board's TX stalled
notes-26-5	1	count notes/nic-driver.md ^### 26[.]5 `D3-MISS` ③ scored on block 46$
notes-8-7-p2q	1	count notes/boot-time.md ^[|] `P2Q-r01` [|] quiet, cold [|] 4[.]111776 [|] 10[.]764227 [|] 10[.]884312 [|] 2 [(]ledger[)] [|] 0[.]094550 [|]
notes-8-7-p3q	1	count notes/boot-time.md ^[|] `P3Q-r01` [|] quiet, cold [|] 4[.]111394 [|] 10[.]760109 [|] 10[.]869487 [|] 2 [(]frames[)] [|] 0[.]114647 [|] 0[.]1031 [|]
list-d8-cold	1	count docs/boot-time-d3-list.tsv ^D8[|]width[|]quiet[|]cold\tD8\t
list-net109-p3	1	count docs/boot-time-d3-list.tsv ^NET109[|]p3egress\tNET109\tport 3 egress unicast packets at P1-AC0\t
list-net109-crc	1	count docs/boot-time-d3-list.tsv ^NET109[|]crcalignerr\tNET109\tCPU port CRCAlignErr at P1-AC0\t
spec-clk48	1	count SPEC.md ^[|] `CLK-48` 🆕 [|]
spec-net121	1	count SPEC.md ^[|] `NET-121` 🆕 [|]
spec-net129	1	count SPEC.md ^[|] `NET-129` 🆕 [|]
netup-common-read-z9	1	count /home/key/fwre-work/rebuild/s111/netup/common.py self[.]z9 = tsv_rows[(]self[.]B [+] "/Z9-D2[.]tsv"[)]$
pcapwin-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py ^VERSION = "1[.]3"$
brdelta-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py ^VERSION = "1[.]2"$
dmesgwin-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ^VERSION = "1[.]2"$
s1class-version	1	count /home/key/fwre-work/rebuild/s113/shared/s1class.py ^VERSION = "1[.]0"$
s1class-rule	1	count /home/key/fwre-work/rebuild/s113/shared/s1class.py ^ {4}branch = "a" if [(]H >= 1 and P >= H[)] else "b"$
w3ctl46-pass	1	count /home/key/fwre-work/rebuild/s113/card43a/w3ctl46.out ^w3ctl46: PASS every row of every read holds$
w3ctl46-rows	1	count /home/key/fwre-work/rebuild/s113/card43a/w3ctl46.out ^rows holds 228 misses 0; reads not scored 0$
w3ctl46-shift-fails	1	count /home/key/fwre-work/rebuild/s113/card43a/w3ctl46-shift.out ^w3ctl46: FAIL$
w3ctl46-tool	4951bfa3a2a02acd4b760ff8fec5db19fd88b2b344e192cb61051f52550dbfea	sha256 /home/key/fwre-work/rebuild/s113/card43a/w3ctl46.py
gencard-est-I-0	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-0\ \ \ \ 13\ cells,\ \ 45\ items,\ \~0\.7\ min$
gencard-est-I-C0	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-C0\ \ \ \ 1\ cells,\ \ \ 1\ items,\ \~0\.0\ min$
gencard-est-I-C1	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-C1\ \ \ \ 3\ cells,\ \ \ 6\ items,\ \~2\.8\ min$
gencard-est-I-1	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-1\ \ \ \ 19\ cells,\ \ 36\ items,\ \~7\.4\ min$
gencard-est-I-R	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-R\ \ \ 110\ cells,\ 203\ items,\ \~2\.4\ min$
gencard-est-I-H	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-H\ \ \ \ \ 2\ cells,\ \ \ 7\ items,\ \~0\.1\ min$
gencard-est-I-E	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-E\ \ \ 113\ cells,\ 210\ items,\ \~2\.5\ min$
gencard-est-I-Z	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-Z\ \ \ \ \ 5\ cells,\ \ 12\ items,\ \~0\.3\ min$
gencard-est-I-C9	1	count /home/key/fwre-work/rebuild/s113/card43a/gencard43a.out ^\ \ I\-C9\ \ \ \ 5\ cells,\ \ \ 6\ items,\ \~0\.0\ min$
rttseries-mutations	1	count /home/key/fwre-work/rebuild/s113/card43a/rttseries-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
w3-mutations	1	count /home/key/fwre-work/rebuild/s113/card43a/w3-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
w1width-mutations	1	count /home/key/fwre-work/rebuild/s113/card43a/w1width-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
s1class-mutations	1	count /home/key/fwre-work/rebuild/s113/shared/s1class-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
brdelta-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
pcapwin-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
dmesgwin-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
hcstepctl-mutations	1	count /home/key/fwre-work/rebuild/s113/card43a/hcstepctl-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
sha-pcapwin-py	6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py
sha-brdelta-py	030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py
sha-dmesgwin-py	2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py
sha-s1class-py	fd24afbfca10546cc59cd1d71fe3f836041d5a636acc57f655e2db153c861431	sha256 /home/key/fwre-work/rebuild/s113/shared/s1class.py
sha-rttseries-py	fbae2a34a798514f8fff35fbea7dbf189ae537f79718f2c7a12fca460993cecf	sha256 /home/key/fwre-work/rebuild/s113/card43a/rttseries.py
sha-w3-py	1834535265e74eb696bd9fd4e64a23df39182e90e3c66f58c8b60c4a402fc647	sha256 /home/key/fwre-work/rebuild/s113/card43a/w3.py
sha-w1width-py	519fd40e64e7b290dab7e49186c53562c4c86186972440aecb07e2aea7ef1773	sha256 /home/key/fwre-work/rebuild/s113/card43a/w1width.py
sha-common-py	af52c0af565528154c517b8747e2c5da8089c02a577fe77af005bfc2aaddb959	sha256 /home/key/fwre-work/rebuild/s111/netup/common.py
sha-arith43a-py	07107201433f83e7d6f215c9ed5ff27eda668a18fff37701533c4a78bd418da0	sha256 /home/key/fwre-work/rebuild/s113/card43a/arith43a.py
sha-hcstepctl-py	d7422a6f497e4bd7579a6187152b999dbd2587eab809f22f0b08c45f8acbe187	sha256 /home/key/fwre-work/rebuild/s113/card43a/hcstepctl.py
sha-runblock-py	21287d2e33c7b8e87fb0f426ed728a4eec052fc6722356f8136aeb1bdbb6363b	sha256 /home/key/fwre-work/rebuild/s109/card/runblock.py
sha-line43a-sh	112bc19eed610fdab3ea3e8b0ce4f63b076420992b73588d22fc1c10d4687014	sha256 /home/key/fwre-work/rebuild/s113/card43a/line43a.sh
selftest-pcapwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-pcapwin.out ^pcapwin\ self\-test:\ 29\ of\ 29\ passed$
selftest-brdelta	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-brdelta.out ^brdelta\ self\-test:\ 40\ of\ 40\ passed$
selftest-dmesgwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-dmesgwin.out ^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$
selftest-s1class	1	count /home/key/fwre-work/rebuild/s113/shared/selftest-s1class.out ^s1class\ self\-test:\ 15\ of\ 15\ passed$
selftest-rttseries	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-rttseries.out ^rttseries\ self\-test:\ 22\ of\ 22\ passed$
selftest-w3	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-w3.out ^w3\ self\-test:\ 17\ of\ 17\ passed$
selftest-w1width	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-w1width.out ^w1width\ self\-test:\ 9\ of\ 9\ passed$
selftest-hcstepctl	1	count /home/key/fwre-work/rebuild/s113/card43a/selftest-hcstepctl.out ^hcstepctl\ self\-test:\ 5\ of\ 5\ passed$
arith-w1-seatb-cold-p2q-r01-0-094550-p3q-r01-0-114647	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ seatB\ cold\ P2Q\-r01\ 0\.094550\ P3Q\-r01\ 0\.114647\ \(notes/boot\-time\.md\ 8\.7\)$
arith-w1-w1width-re-derived-p2q-r01-0-094550-p3q-r01-0	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ w1width\ re\-derived\ P2Q\-r01\ 0\.094550\ P3Q\-r01\ 0\.114647\ agree\ yes$
arith-w1-cold-pair-band-10-a-reading-0-085095-0-126112	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ cold\-pair\ band\ \+\-10\ %\ \(a\ reading\):\ \[0\.085095,\ 0\.126112\]$
arith-w1-seatb-quiet-widths-n-8-cold-2-warm-6-p1q-r01	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ seatB\ quiet\ widths\ n\ 8\ cold\ 2\ warm\ 6:\ P1Q\-r01:0\.117001\ P1Q\-r02:0\.082275\ P1Q\-r03:0\.134960\ P1Q\-r04:0\.081153\ P2Q\-r01:0\.094550\ P2Q\-r02:0\.130450\ P3Q\-r01:0\.114647\ P3Q\-r02:0\.129736$
arith-w1-band-seating-b-s-quiet-range-p4-0-081153-0-13	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ band\ seating\ B's\ quiet\ range\ \(P4\):\ \[0\.081153,\ 0\.134960\]$
arith-w1-seatb-quiet-widths-inside-the-cold-pair-band	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ seatB\ quiet\ widths\ inside\ the\ cold\-pair\ band:\ 3\ of\ 8$
arith-w1-seatb-quiet-range-spread-0-053807-s-the-large	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ seatB\ quiet\ range\ spread\ 0\.053807\ s\ \(the\ largest\ quiet\ width\ less\ the\ smallest\)$
arith-w1-seatb-cold-quiet-first-reply-after-j-p2q-r01	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ seatB\ cold\ quiet\ first\ reply\ after\ J\ P2Q\-r01\ 10\.884312\ P3Q\-r01\ 10\.869487\ s;\ 100\ ppm\ over\ the\ longer\ 1\.088\ ms$
arith-w1-base-rate-a-new-draw-from-the-same-distributi	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ base\ rate:\ a\ new\ draw\ from\ the\ same\ distribution\ lies\ inside\ the\ n\-sample\ range\ with\ probability\ \(n\-1\)/\(n\+1\)\ =\ 7/9$
arith-w1-list-row-d8-width-quiet-cold-a-raw-0-187804-c	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^W1\ list\ row\ D8\|width\|quiet\|cold\ A\ raw\ 0\.187804\ corr\ 0\.091986\ stable\ Y$
arith-spread-rule-max-v-median-1-reproduces-the-list-d	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^SPREAD\ rule\ max\|v/median\-1\|\ reproduces\ the\ list:\ D8\|width\|quiet\|warm\ 0\.182967\ \(list\ 0\.182967\)\ D5a\|rlxfw\|56\|avg\ 0\.144388\ \(list\ 0\.144388\)$
arith-spread-seatb-cold-pair-0-096067-stable-by-rule-y	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^SPREAD\ seatB\ cold\ pair\ 0\.096067\ stable\-by\-rule\ yes$
arith-spread-third-cold-width-keeping-the-three-stable	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^SPREAD\ third\ cold\ width\ keeping\ the\ three\ stable\-by\-rule:\ \[0\.104225,\ 0\.105055\]\ \(1\ us\ grid\)$
arith-plan-011001100110-n-12-on-6-off-6-abba-yes	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^PLAN\ 011001100110\ n\ 12\ on\ 6\ off\ 6\ abba\ yes$
arith-d5a-ref-56-a-uncaptured-p1-1-586-p2-1-516-band-1	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ ref\ 56\ A\ uncaptured\ P1\ 1\.586\ P2\ 1\.516\ band\ \[1\.3644,\ 1\.7446\]\ ref\-arg\ 56:1\.516:1\.586$
arith-d5a-refon-56-a-captured-p3-1-815-band-1-6335-1-9	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ refon\ 56\ A\ captured\ P3\ 1\.815\ band\ \[1\.6335,\ 1\.9965\]\ refon\-arg\ 56:1\.815:1\.815$
arith-d5a-seatb-captured-p1-p3-56-avg-2-305-1-401-medi	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-captured\ \(P1,\ P3\)\ 56\ avg\ 2\.305,1\.401\ median\ 1\.8530\ against\ the\ captured\ band\ inside$
arith-d5a-ref-256-a-uncaptured-p1-1-367-p2-1-518-band	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ ref\ 256\ A\ uncaptured\ P1\ 1\.367\ P2\ 1\.518\ band\ \[1\.2303,\ 1\.6698\]\ ref\-arg\ 256:1\.367:1\.518$
arith-d5a-refon-256-a-captured-p3-1-641-band-1-4769-1	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ refon\ 256\ A\ captured\ P3\ 1\.641\ band\ \[1\.4769,\ 1\.8051\]\ refon\-arg\ 256:1\.641:1\.641$
arith-d5a-seatb-captured-p1-p3-256-avg-1-792-1-933-med	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-captured\ \(P1,\ P3\)\ 256\ avg\ 1\.792,1\.933\ median\ 1\.8625\ against\ the\ captured\ band\ above$
arith-d5a-ref-512-a-uncaptured-p1-1-736-p2-1-64-band-1	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ ref\ 512\ A\ uncaptured\ P1\ 1\.736\ P2\ 1\.64\ band\ \[1\.4760,\ 1\.9096\]\ ref\-arg\ 512:1\.64:1\.736$
arith-d5a-refon-512-a-captured-p3-1-618-band-1-4562-1	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ refon\ 512\ A\ captured\ P3\ 1\.618\ band\ \[1\.4562,\ 1\.7798\]\ refon\-arg\ 512:1\.618:1\.618$
arith-d5a-seatb-captured-p1-p3-512-avg-2-128-1-743-med	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-captured\ \(P1,\ P3\)\ 512\ avg\ 2\.128,1\.743\ median\ 1\.9355\ against\ the\ captured\ band\ above$
arith-d5a-ref-1024-a-uncaptured-p1-2-03-p2-2-124-band	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ ref\ 1024\ A\ uncaptured\ P1\ 2\.03\ P2\ 2\.124\ band\ \[1\.8270,\ 2\.3364\]\ ref\-arg\ 1024:2\.03:2\.124$
arith-d5a-refon-1024-a-captured-p3-2-086-band-1-8774-2	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ refon\ 1024\ A\ captured\ P3\ 2\.086\ band\ \[1\.8774,\ 2\.2946\]\ refon\-arg\ 1024:2\.086:2\.086$
arith-d5a-seatb-captured-p1-p3-1024-avg-2-455-2-020-me	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-captured\ \(P1,\ P3\)\ 1024\ avg\ 2\.455,2\.020\ median\ 2\.2375\ against\ the\ captured\ band\ inside$
arith-d5a-ref-1472-a-uncaptured-p1-2-052-p2-2-252-band	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ ref\ 1472\ A\ uncaptured\ P1\ 2\.052\ P2\ 2\.252\ band\ \[1\.8468,\ 2\.4772\]\ ref\-arg\ 1472:2\.052:2\.252$
arith-d5a-refon-1472-a-captured-p3-2-139-band-1-9251-2	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ refon\ 1472\ A\ captured\ P3\ 2\.139\ band\ \[1\.9251,\ 2\.3529\]\ refon\-arg\ 1472:2\.139:2\.139$
arith-d5a-seatb-captured-p1-p3-1472-avg-2-720-2-399-me	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-captured\ \(P1,\ P3\)\ 1472\ avg\ 2\.720,2\.399\ median\ 2\.5595\ against\ the\ captured\ band\ above$
arith-d5a-row-256-avg-a-median-1-518-stable-y-row-arg	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ row\ 256\ avg\ A\ median\ 1\.518\ stable\ Y\ row\-arg\ 256:avg:1\.518$
arith-d5a-row-512-avg-a-median-1-64-stable-y-row-arg-5	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ row\ 512\ avg\ A\ median\ 1\.64\ stable\ Y\ row\-arg\ 512:avg:1\.64$
arith-d5a-row-1024-avg-a-median-2-086-stable-y-row-arg	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ row\ 1024\ avg\ A\ median\ 2\.086\ stable\ Y\ row\-arg\ 1024:avg:2\.086$
arith-d5a-row-1472-avg-a-median-2-139-stable-y-row-arg	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ row\ 1472\ avg\ A\ median\ 2\.139\ stable\ Y\ row\-arg\ 1472:avg:2\.139$
arith-d5a-row-1472-mdev-a-median-0-476-stable-y-row-ar	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ row\ 1472\ mdev\ A\ median\ 0\.476\ stable\ Y\ row\-arg\ 1472:mdev:0\.476$
arith-d5a-stable-rows-5	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ stable\ rows\ 5$
arith-d5a-rowsrc-256-avg-a-median-1-518-is-p2-uncaptur	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ rowsrc\ 256\ avg\ A\ median\ 1\.518\ is\ P2\ uncaptured$
arith-d5a-rowsrc-512-avg-a-median-1-64-is-p2-uncapture	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ rowsrc\ 512\ avg\ A\ median\ 1\.64\ is\ P2\ uncaptured$
arith-d5a-rowsrc-1024-avg-a-median-2-086-is-p3-capture	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ rowsrc\ 1024\ avg\ A\ median\ 2\.086\ is\ P3\ captured$
arith-d5a-rowsrc-1472-avg-a-median-2-139-is-p3-capture	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ rowsrc\ 1472\ avg\ A\ median\ 2\.139\ is\ P3\ captured$
arith-d5a-rowsrc-1472-mdev-a-median-0-476-is-p3-captur	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ rowsrc\ 1472\ mdev\ A\ median\ 0\.476\ is\ P3\ captured$
arith-d5a-seatb-p2-no-capture-56-avg-1-723-band-inside	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 56\ avg\ 1\.723\ band\ inside\ ratio\-to\-A\-median\ \+0\.0864$
arith-d5a-seatb-p2-no-capture-256-avg-1-546-band-insid	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 256\ avg\ 1\.546\ band\ inside\ ratio\-to\-A\-median\ \+0\.0184$
arith-d5a-seatb-p2-no-capture-512-avg-1-685-band-insid	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 512\ avg\ 1\.685\ band\ inside\ ratio\-to\-A\-median\ \+0\.0274$
arith-d5a-seatb-p2-no-capture-1024-avg-1-889-band-insi	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 1024\ avg\ 1\.889\ band\ inside\ ratio\-to\-A\-median\ \-0\.0944$
arith-d5a-seatb-p2-no-capture-1472-avg-2-364-band-insi	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 1472\ avg\ 2\.364\ band\ inside\ ratio\-to\-A\-median\ \+0\.1052$
arith-d5a-seatb-p2-no-capture-1472-mdev-0-555-ratio-to	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^D5A\ seatB\-P2\ \(no\ capture\)\ 1472\ mdev\ 0\.555\ ratio\-to\-A\-median\ \+0\.1660$
arith-u-null-n-on-6-n-off-6-lo-5-hi-31-of-36	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ null\ n_on\ 6\ n_off\ 6\ lo\ 5\ hi\ 31\ of\ 36$
arith-u-false-lowers-n-on-6-n-off-6-p-u-5-19-924-0-020	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ false\ lowers\ n_on\ 6\ n_off\ 6\ P\(U\ <=\ 5\)\ 19/924\ =\ 0\.0206;\ at\ any\ of\ 5\ sizes\ at\ most\ 0\.1028\ \(union\),\ 0\.0987\ if\ independent$
arith-u-null-n-on-5-n-off-6-lo-3-hi-27-of-30	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ null\ n_on\ 5\ n_off\ 6\ lo\ 3\ hi\ 27\ of\ 30$
arith-u-false-lowers-n-on-5-n-off-6-p-u-3-7-462-0-0152	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ false\ lowers\ n_on\ 5\ n_off\ 6\ P\(U\ <=\ 3\)\ 7/462\ =\ 0\.0152;\ at\ any\ of\ 5\ sizes\ at\ most\ 0\.0758\ \(union\),\ 0\.0735\ if\ independent$
arith-u-null-n-on-6-n-off-5-lo-3-hi-27-of-30	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ null\ n_on\ 6\ n_off\ 5\ lo\ 3\ hi\ 27\ of\ 30$
arith-u-false-lowers-n-on-6-n-off-5-p-u-3-7-462-0-0152	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ false\ lowers\ n_on\ 6\ n_off\ 5\ P\(U\ <=\ 3\)\ 7/462\ =\ 0\.0152;\ at\ any\ of\ 5\ sizes\ at\ most\ 0\.0758\ \(union\),\ 0\.0735\ if\ independent$
arith-u-null-n-on-5-n-off-5-lo-2-hi-23-of-25	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ null\ n_on\ 5\ n_off\ 5\ lo\ 2\ hi\ 23\ of\ 25$
arith-u-false-lowers-n-on-5-n-off-5-p-u-2-4-252-0-0159	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^U\ false\ lowers\ n_on\ 5\ n_off\ 5\ P\(U\ <=\ 2\)\ 4/252\ =\ 0\.0159;\ at\ any\ of\ 5\ sizes\ at\ most\ 0\.0794\ \(union\),\ 0\.0769\ if\ independent$
arith-mdev-a-20-echo-sd-s-relative-sampling-error-1-sq	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^MDEV\ a\ 20\-echo\ SD's\ relative\ sampling\ error\ 1/sqrt\(2\(n\-1\)\)\ =\ 0\.162$
arith-net121-seatings-a-and-b-rlxfw-icmp-series-2026-0	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^NET121\ seatings\ A\ and\ B\ rlxfw\ ICMP\ series\ \(2026\-09\-23,\ 2026\-09\-25\ P1\-P3\-ICMP\):\ 6\ logs,\ 30\ size\-series,\ 30\ of\ them\ 20\ of\ 20;\ echoes\ received\ 600\ of\ 600\ sent$
arith-f-liveness-s-18-frame-60-mod8-4-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ liveness\ s\ 18\ frame\ 60\ mod8\ 4\ cover8\ clean$
arith-f-probe-s-56-frame-98-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ probe\ s\ 56\ frame\ 98\ mod8\ 2\ cover8\ clean$
arith-f-series-s-56-frame-98-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ series\ s\ 56\ frame\ 98\ mod8\ 2\ cover8\ clean$
arith-f-series-s-256-frame-298-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ series\ s\ 256\ frame\ 298\ mod8\ 2\ cover8\ clean$
arith-f-series-s-512-frame-554-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ series\ s\ 512\ frame\ 554\ mod8\ 2\ cover8\ clean$
arith-f-series-s-1024-frame-1066-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ series\ s\ 1024\ frame\ 1066\ mod8\ 2\ cover8\ clean$
arith-f-series-s-1472-frame-1514-mod8-2-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ series\ s\ 1472\ frame\ 1514\ mod8\ 2\ cover8\ clean$
arith-f-arp-frame-60-mod8-4-cover8-clean	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ arp\ frame\ 60\ mod8\ 4\ cover8\ clean$
arith-f-cover8-bad-residues-0-5-6-7	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^F\ cover8\ bad\ residues\ 0\ 5\ 6\ 7$
arith-n3-list-row-net109-crcalignerr-quantity-cpu-port	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^N3\ list\ row\ NET109\|crcalignerr\ quantity\ 'CPU\ port\ CRCAlignErr\ at\ P1\-AC0'\ A\ 294\ stable\ Y$
arith-n3-list-row-net109-p3egress-quantity-port-3-egre	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^N3\ list\ row\ NET109\|p3egress\ quantity\ 'port\ 3\ egress\ unicast\ packets\ at\ P1\-AC0'\ A\ 294\ stable\ Y$
arith-arp-board-delay-then-probe-delay-probe-time-5-s	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^ARP\ board\ DELAY\ then\ PROBE:\ delay_probe_time\ 5\ s\ \+\ ucast_probes\ 3\ x\ retrans_time\ 1\ s\ =\ 8\ s\ \(neigh_max_probes\ in\ NUD_PROBE:\ ucast\ only\);\ the\ quiet\ 12\ s\ exceeds\ it\ by\ 4\ s$
arith-hcg-seating-b-s-guard-refused-at-raw-1539-314-pe	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^HCG\ seating\ B's\ guard\ refused\ at\ RAW\ 1539\.314,\ permitted\ at\ RAW\ 2301\.444:\ 12\.7\ min\ later$
arith-stopctl-cardrun-s-sigint-to-ended-t1-0-102018-s	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^STOPCTL\ cardrun's\ SIGINT\ to\ ENDED:\ T1\ 0\.102018\ s\ T2\ 0\.102034\ s$
arith-wdt-p2q-s-rtl819x-wdt-bootguard-1-hw-ovsel-9-kic	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^WDT\ p2q's\ rtl819x\-wdt:\ bootguard\ 1\ hw_ovsel\ 9\ kick_ms\ 250;\ OVSEL\ 9's\ deadline\ 83\.8\ s$
arith-bitem-ovsel-9-s-bite-as-measured-84-001412-s-spe	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^BITEM\ OVSEL\ 9's\ bite\ as\ measured\ 84\.001412\ s\ \(SPEC\.md\ CLK\-08b,\ seating\ 18\);\ the\ driver's\ own\ figure\ 83\.8\ s,\ 0\.24\ %\ under\ it$
arith-b2p-the-loader-s-banner-to-its-first-prompt-with	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^B2P\ the\ loader's\ banner\ to\ its\ first\ prompt\ with\ ESC\ streaming:\ block\ 48's\ R1\-CATCH,\ Booting\.\.\.\ at\ 14\.986257\ s,\ the\ first\ <RealTek>\ ended\ 17\.274354\ s:\ 2\.288097\ s$
arith-hold-the-watch-s-hold-after-a-stop-90-s-ceil-the	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^HOLD\ the\ watch's\ hold\ after\ a\ stop\ 90\ s\ =\ ceil\(the\ bite\ as\ measured\ 84\.001\ s\ \+\ the\ loader's\ banner\ to\ its\ first\ prompt\ 2\.288\ s\ \+\ a\ margin\ 3\.0\ s\ \(a\ guess\)\)\ =\ ceil\(89\.290\)$
arith-map-committed-maps-of-this-command-n-6-longest-1	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^MAP\ committed\ maps\ of\ this\ command\ n\ 6\ longest\ 13\.804\ s;\ cap\ 60\ s\ =\ 4\.35x\ the\ longest,\ 23\.8\ s\ under\ BOOTGUARD's\ 83\.8\ s$
arith-escwin-the-loader-s-esc-window-4-9-s-console-cap	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^ESCWIN\ the\ loader's\ ESC\ window\ \~4\.9\ s\ \(console\-capture's\ record\);\ its\ CR\ settle\ 2\.0\ s$
arith-watch-esc-after-3600-esc-period-0-01-seconds-360	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^WATCH\ esc\-after\ 3600\ esc\-period\ 0\.01\ seconds\ 3605\ until\ <RealTek>;\ C5\-UB:\ period\ 0\.01,\ ESC\ 145\.869442\ s\ into\ a\ live\ rlxfw,\ ended\ on\ the\ prompt\ yes$
arith-nocap-a-watch-for-any-wait-longer-than-about-30	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^NOCAP\ a\ watch\ for\ any\ wait\ longer\ than\ about\ 30\ s\ with\ the\ board\ running\ and\ no\ capture\ open\ \(a\ guess\)$
arith-handshake-the-owner-s-reaction-after-the-session	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^HANDSHAKE\ the\ owner's\ reaction\ after\ the\ session's\ 'now'\ 300\ s\ \(a\ guess\)\ \+\ the\ session's\ opening,\ confirmation\ and\ message\ after\ the\ reply\ 60\ s\ \(a\ guess\)\ =\ 360\ s\ of\ ESC\ a\ window$
arith-catch-esc-after-360-esc-period-0-002-until-realt	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^CATCH\ esc\-after\ 360\ esc\-period\ 0\.002\ until\ <RealTek>\ seconds\ 380:\ block\ 48's\ R1\-CATCH\ \-\-esc\ 180\ \-\-seconds\ 200,\ its\ tail\ 20\ s\ kept$
arith-loader-at-its-prompt-block-48-s-r1-catch-550-rep	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^LOADER\ at\ its\ prompt:\ block\ 48's\ R1\-CATCH,\ 550\ replies\ before\ its\ CR,\ each\ after\ 128\ ESC,\ each\ 'Unknown\ command\ !'\ and\ the\ prompt\ yes;\ a\ watch\ opened\ at\ the\ prompt\ ends\ on\ the\ first,\ 128\ x\ 0\.01\ s\ =\ 1\.28\ s,\ about\ 1\.3\ s$
arith-catchprompt-block-48-s-r1-catch-its-first-realte	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^CATCHPROMPT\ block\ 48's\ R1\-CATCH:\ its\ first\ <RealTek>\ after\ the\ banner\ yes\ and\ C\-8's\ cold\ line\ yes$
arith-ccarm-console-capture-arms-until-from-the-start	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^CCARM\ console\-capture\ arms\ \-\-until\ from\ the\ start\ of\ a\ capture\ with\ no\ \-\-esc\ and\ no\ \-\-send:\ its\ line\ 1;\ C5\-UB's\ \-\-esc\-after\ loop\ ended\ on\ \-\-until\ yes,\ its\ CR's\ prompt\ seen\ yes$
arith-offwin-esc-after-360-esc-period-0-01-seconds-365	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^OFFWIN\ esc\-after\ 360\ esc\-period\ 0\.01\ seconds\ 365,\ the\ owner's\ window\ at\ least\ 40\ s$
arith-est-figure-bracket-median-5-30-s-over-86-end-lin	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ bracket\ median\ 5\.30\ s\ over\ 86\ END\ lines,\ max\ 7\.3\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-ps-median-3-90-s-over-28-end-lines-ma	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ ps\ median\ 3\.90\ s\ over\ 28\ END\ lines,\ max\ 4\.8\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-map-median-13-90-s-over-2-end-lines-m	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ map\ median\ 13\.90\ s\ over\ 2\ END\ lines,\ max\ 13\.9\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-nw-median-3-65-s-over-2-end-lines-max	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ nw\ median\ 3\.65\ s\ over\ 2\ END\ lines,\ max\ 3\.8\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-stim-median-3-40-s-over-44-end-lines	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ stim\ median\ 3\.40\ s\ over\ 44\ END\ lines,\ max\ 5\.9\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-live-median-0-90-s-over-42-end-lines	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ live\ median\ 0\.90\ s\ over\ 42\ END\ lines,\ max\ 2\.1\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-round-median-24-70-s-over-1-end-lines	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ round\ median\ 24\.70\ s\ over\ 1\ END\ lines,\ max\ 24\.7\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-hostp-median-0-00-s-over-86-end-lines	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ hostp\ median\ 0\.00\ s\ over\ 86\ END\ lines,\ max\ 0\.4\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-host-median-0-10-s-over-89-end-lines	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ host\ median\ 0\.10\ s\ over\ 89\ END\ lines,\ max\ 1\.1\ s\ \(block\ 48's\ 14\ run\ logs\)$
arith-est-figure-icmp-median-4-90-s-over-3-end-lines-m	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ icmp\ median\ 4\.90\ s\ over\ 3\ END\ lines,\ max\ 4\.9\ s\ \(block\ 44's\ 19\ run\ logs\)$
arith-est-figure-quiet-12-10-s-a1-hpx-s-sleep-12-s-a-h	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ figure\ quiet\ 12\.10\ s:\ A1\-HPX's\ sleep\ 12\ s\ \+\ a\ host\ cell's\ 0\.10\ s$
arith-est-guess-bg-0-5-s-a-background-cell-s-start-its	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ bg\ 0\.5\ s:\ a\ background\ cell's\ start,\ its\ start\ signal\ awaited\ \(a\ guess\)$
arith-est-guess-order-1-0-s-pcapwin-s-record-order-rea	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ order\ 1\.0\ s:\ pcapwin's\ record\-order\ read\ \(a\ guess\)$
arith-est-guess-selftest-40-0-s-r0-st-s-eight-self-tes	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ selftest\ 40\.0\ s:\ R0\-ST's\ eight\ self\-tests\ \(before\ power\)\ \(a\ guess\)$
arith-est-guess-report-5-0-s-a-hostclock-report-after	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ report\ 5\.0\ s:\ a\ hostclock\ report\ after\ Z0\-HCG's\ own\ sleep\ and\ run\ \(before\ power\)\ \(a\ guess\)$
arith-est-guess-pre-3-1-s-the-pre-flight-s-3-08-s-boar	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ pre\ 3\.1\ s:\ the\ pre\-flight's\ \~3\.08\ s\ \(board\ off\)\ \(a\ guess\)$
arith-est-guess-gap-2-0-s-between-two-chained-invocati	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^EST\ guess\ gap\ 2\.0\ s\ between\ two\ chained\ invocations:\ the\ runner's\ start\-up\ \(a\ guess\)$
arith-latest-the-catch-opens-by-23-00-midnight-less-60	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^LATEST\ the\ catch\ opens\ by\ 23:00:\ midnight\ less\ 60\ min\ \(a\ guess:\ the\ press's\ estimate\ and\ its\ stops\),\ so\ every\ capture\ is\ dated\ the\ declared\ day$
arith-arith43a-controls-19-of-19-hold	1	count /home/key/fwre-work/rebuild/s113/card43a/arith43a.out ^arith43a\ controls:\ 19\ of\ 19\ hold$
```
