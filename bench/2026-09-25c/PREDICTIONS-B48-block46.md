# PREDICTIONS — block 46, seating 41 (`R6b-1`: where on the transmit path a frame of a given length goes wrong, one length at a time)

**declared date 2026-09-25** — **one power press**; its catch window opens no later than
23:10 that day, or the card is re-dated before power (§ 6).
Block 45 (`bench/2026-09-25b/PREDICTIONS-B47-block45.md`) is the last press before this
one; this block reruns its frame-length experiment one length at a time, on the same image.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this block is.** `R6b-1`, the first carded step of `R6b` (opened 2026-09-25 on the
owner's ruling; no segment cap; this card declared for 2026-09-25, one press). It measures,
for each of block 45's eleven `E2` frame lengths separately, at which stage a frame the driver
counts as sent stops being the frame it was given: the driver, the CPU port's ingress
counters, port 3's output, the host adapter, the host's IP layer, and the wire as the host's
frame capture sees it. Four arms, each built only from verbs this image already has
(`config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c` 1.4, 讀): **A** the stack (host
`ping`), at `E2`'s 50 ms spacing (`A1`) and at 250 ms (`A2`); **B** the raw `tx` verb with the
stack silent; **C** loopback (`lb on`), the engine's own view of what it sent; **D**
`txmode 1` at 61 and 1,511 B. It names a stage, not a field, and fixes nothing. The
mechanisms it can refute, and the three it cannot (`M1`, `M2`, `M5`), are § 3.9.

**② What block 45 showed, which every prediction below is re-derived from** (量, block 45's
committed captures; every number here is a `cardnum` row). `E2` ran the eleven lengths back
to back with one bracket around all of them, each length a `ping -c 20 -w 10` that kept
sending until 20 replies or 10 s: the driver sent 935 frames (`n_tx` 102 → 1,037), the CPU
port took in 894 (`CRCAlignErr` 102 → 996), of which 678 were counted `JabberErr`, 1
`FragErr` and 43 `Drop` (`etherStatsDropEvents` 20); the host adapter received 172
(`rx_packets` 727,929 → 728,101). The CPU port's `512 - 1023` bucket rose by 6 (20 → 26)
although no length given lies in it. The recovery fired 5 times (`n_recov_fire` 0 → 5,
`n_tx_stop` 0 → 5). The board's stack sent 1,202 datagrams (`Ip.OutRequests` 100 → 1,302)
and discarded 86 at the device (`Ip.OutDiscards` 0 → 86); 9 were host-unreachables
(`Icmp.OutDestUnreachs` 0 → 9). Per length:

| frame (B) | ping `-s` | requests | ping's replies | replies on the wire | on the wire, requests 1–60 |
|---:|---:|---:|---:|---:|---:|
| 60 | 18 | 20 | 20 | 20 | 20 (of 20) |
| 61 | 19 | 181 | 19 | 19 | 17 |
| 62 | 20 | 74 | 20 | 20 | 16 |
| 63 | 21 | 180 | 9 | 9 | 9 |
| 263 | 221 | 179 | 1 | 1 | 0 |
| 276 | 234 | 25 | 20 | 20 | 20 (of 25) |
| 277 | 235 | 134 | 20 | 39 | 18 |
| 1,511 | 1,469 | 179 | 0 | 0 | 0 |
| 1,512 | 1,470 | 179 | 1 | 1 | 0 |
| 1,513 | 1,471 | 22 | 20 | 20 | 20 (of 22) |
| 1,514 | 1,472 | 20 | 20 | 20 | 20 (of 20) |

At 277 B, 39 replies reached the host adapter and the host's ICMP layer counted 20, with no
host error counter moving; `E2`'s host-side bytes exceed its frames' content by 76 B = 19 × 4
(the `R6b-0` dossier's byte identity, `$FWRE_WORK/rebuild/s111/r6b-dossier/a45e.out`, exact
(+0 B) on `E1`). 推 the 19 carried a 4-byte 802.1Q tag and the host dropped them before IP
(`M4`, § 3.7). Every per-length figure in block 45 is ping's own count or the wire's; no
counter was read per length, which is what this card adds.

**③ Three statements of block 45's record are wrong, and this card uses the corrected
form.** (a) Card B47 § 0 ③'s chain premise, *port 3's output equals `CRCAlignErr` −
`JabberErr` − `Drop`*, is off by one in `E2` (894 − 678 − 43 = 173 against the host's 172)
and in `E4`; it is exact with `FragErr` also subtracted (the dossier, § 2.6 ②). (b) *The CPU
port's histogram does not count the 64 B ARP frames* is false: its `64:` bucket rose by 2 in
`E1` (0 → 2); the parser that said so matched `< 64:` (dossier § 2.6 ①). This card predicts
the `64:` bucket counts every 60 B frame. (c) Block 45's `cells` fence misnamed `looprun`'s
single-round artefacts (`bench/2026-09-25b/CORRECTIONS-block45.md` § 1); this fence names
them `R1Q-ab2`, `R1Q-2a`, `R1Q-boot`.

**④ What reads silicon for the first time tonight, and what each rests on.**
* **One host frame capture, written to disk, for all four arms.** `tcpdump -n -U -Q in -w`
  into `$FWRE_WORK/rebuild/s111/r6b/pcap/W.pcap`, never the repository: a raw frame carries
  hardware addresses. No filter, because a frame whose EtherType or addresses came out wrong
  is the reading; `-Q in` keeps only what the host received. It runs in an invocation of its
  own, `I-W0`, started in the background after the round, as block 44's `I0` ran its clock
  logger for a whole seating (量 `run-I0.log`, 2 h 46 min) — because a stop interrupts every
  background cell *of the invocation that stopped* (讀 `tools/cardrun.py` `stop_children`),
  and a capture inside an arm would end at that arm's first stop and take every later window
  of the arm with it. `R0-TCPC` requires no process named `tcpdump` before power, `A-LIVE`
  exactly one before the arms, and every window prints how many exist. The capture is
  counted by `$FWRE_WORK/rebuild/s111/r6b/card/pcapwin.py` 1.1 (pinned by digest,
  `e64118dee79d5487…`), which prints counts, histograms and the sequence numbers of the echo
  replies, and never an address or an ICMP identifier: self-test 17 of 17, and 13 of 13
  planted defects turned it red. 量 on this host, 2026-09-25, a throwaway veth pair with the
  card's exact `tcpdump` flags and its exact stop (`$FWRE_WORK/rebuild/s111/r6b/card/ctl-veth/`):
  an in-band 802.1Q tag **is kept in the saved record**; a VID-5 frame is dropped before IP
  and a VID-0 frame is not (the host's `Icmp.InEchoReps` rose by 3 for the 4 ICMP frames
  sent); `ip -s -s link` (iproute2 6.1.0) prints **no** `otherhost` column while it is 0 and
  prints `otherhost 1` after the drop, so its absence in a bracket means zero, and the
  capture is still the witness; `pgrep -xc tcpdump` reads 1 while the capture runs and 0
  after; `sudo -n pkill -INT -x tcpdump` stops it with `0 packets dropped by kernel` and
  exit 0. What the veth cannot show: the host adapter (`r8153_ecm`) dropping a frame before
  the kernel sees it.
* **One board bracket per length, in one cell and one `cat`.** `sleep 2`, then the driver,
  the stack's SNMP, the neighbour table, the switch, **and the driver again**: the two driver
  reads bound the switch's count (§ 3.1), so a frame sent while the switch is being read — the
  one-frame difference block 45's `E5` shows between `n_tx` 40 and `CRCAlignErr` 41 — is
  bounded by the instrument, not excused by a tolerance. The capture ends on the prompt after
  the second driver dump's last line. 讀 `tools/console-capture.py` and the 111th segment's
  desk measurement: bytes after an `--until` match are read for only 0–50 ms, so every
  `--until` on this card ends on the shell prompt and no gate reads a byte after its match.
  The `sleep 2` puts every recovery a run *arms* (1,000 ms after its stop, `recov_ms`, 讀)
  before the driver is read, so that fire is counted in its own run's bracket. **A stall
  that begins with fewer than four frames left in a run arms nothing** (讀 `nic_xmit`: the
  recovery is armed only when a frame is offered to a slot the engine still owns; `NET-113`,
  量 2026-09-23: such stalls stopped late) and carries into the next run; the two dumps'
  `txd` OWN bits and `tx_stopped` show it, and § 3.0's CARRIED rule assigns it.
  `/proc/net/arp` has never been captured on this board: it is a reading, never a gate.
* **`lb on` with `rlx0` registered and up.** Rung 1 (2026-09-19, driver 1.0) ran loopback
  before the `net_device` existed and harvested with the `rx` verb (量 `rx_ph1 00400000`,
  `rx_len 60`, one 60 B frame). Tonight the looped frame is harvested by NAPI, which records
  `rx_ph1` and counts `nd_stats` rx but keeps no copy (讀 `nic_napi_harvest`). Loopback has
  never been read beside the switch's counters.
* **The `tx` verb in its four-argument form**, at every length, with `rlx0` up (§ 0 ⑤).
* **The ring re-armed before every raw, loopback and `txmode 1` length**
  (`engine off ; arm ; engine on`, the string block 45's `D1-X1` typed and `NET-101`'s three
  calls). It is a constant intervention, declared: every such length starts on TX slot 0 of a
  CPU-owned ring, so four raw frames use slots 0–3 once each.
* **`cat /proc/rtl819x-spi` on driver 1.2** (`R1-NW0` after the opening map, `R1-NW1` after
  the closing one), for `n_writes`, the count `CLAUDE.md` § Flash asks a press to claim and
  blocks 44 and 45 did not read. 讀 the source at HEAD (`rtl819x-spi 1.2`) and, at the desk,
  the image's own `vmlinux` (`c5e2cfdb…`), which carries the `rtl819x-spi 1.2` and
  `recipe_id %08X` strings. The handler reads three SPI controller registers and prints
  counters and flags — no flash byte and no `H601` byte (讀 `rtl819x_spi_read_proc`). No
  committed capture holds 1.2's file whole: `bench/2026-09-16/X7-NW0` read 1.1's up to
  `n_writes 0`, and the last committed attempt, `bench/2026-09-21/R7-SPI`, holds 1 byte after
  25 s with no file saying why. A read with no `n_writes` line is repeated once and then
  recorded; it does not stop the press (§ 6).

**⑤ No cell carries `--esc-after`; a reset is caught by a gate in the cell it happens in.**
No payload here is designed to reset the board, but not all of it has run on this die in
the form typed tonight. The re-arm string is the `sent` of committed captures since
2026-09-20 (block 45's `D1-X1` the last) and runs inside the driver as its recovery
(`n_recov_ok`); `txmode 1` was typed on 2026-09-21 (`bench/2026-09-21e/Y6-MODE`). **The `tx`
verb has only ever been typed in its one-argument form**, `echo tx 0x3F`, one 60 B frame each
time, all on 2026-09-19 with driver `1.0` (`bench/2026-09-19b`; 量 by a grep of every
committed file at the desk): `C18`, `C27` and `C28` on a build with no `net_device`, and
`G1` twice with `rlx0` registered and up but idle (`G2-state`: `nd_up 1`, `n_xmit 0`,
`n_napi_poll 0`). The four-argument form, lengths 61–1,514, and a `tx` beside a stack that has
been transmitting and a NAPI that has been polling are first readings, in 38 cells of B and
22 of C. `lb on` has run once (rung 1, driver 1.0, no `net_device`).
`--esc-after` on a cell that does not reset streams escapes into `ash` for its whole window.
The containment does not depend on the outcome: every board cell after the round carries a
gate that fails on the loader's or a kernel's boot text,
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (179 gates; the loader prints
`Booting...` and then `---RealTek(RTL8196E)`, 量 block 45's `D1-A`); every board read also
carries its prompt gate and its `version rtl819x-nic 1.4` gate; board reads are capped at
15 s and stimulus cells at 8 s. A reset therefore stops the invocation in the cell it
happens in, within about 20 s of it (a guess: a ping cell's ~4 s and a board read's 15 s
cap), and § 6 has the owner power off on the failed capture's own text, before any other
cell and before any `CORRECTIONS` entry. 推 a power-off that soon comes before a vendor boot
reaches the configuration check that wrote flash in `FLS-26`; that timing has never been
measured, and nine vendor boots of seating A wrote nothing the map sees (`FLS-30`).

**⑥ The clock.** This block claims no duration: every prediction is a count. Host
timestamps are not used — the capture is windowed by record order, not by time — so
`timesyncd`'s state does not enter any number, and no host-clock guard is run.

**⑦ Runner limits worked around, as in block 44 (§ 0 ⑥ ⑦) and block 45.** A cell whose
non-zero exit is a reading is declared `NAME?`: every host stimulus, every host bracket, the
capture stop and its summary. `MB` ends in `; true` and is judged by its three `grep=` gates
(`FW-134`). `runblock.py` hands each fence line to `cardrun` as argv. **No `wait:` item** is
used, so `--from` accepts every cell. The capture's own invocation, `I-W0`, holds one
background cell and nothing else; its runner waits for that cell to end (讀 `Runner.run`:
`WAIT (end)`), which `I-W9`'s `W-TCPX` causes.

**⑧ ARP is read, not pinned.** The host's entry for the board could be pinned
(`nud permanent`), but `ip neigh flush` does not remove a permanent entry (讀 `ip-neighbour(8)`),
so the next card's `FL` gate would stop on it. Instead every bracket reads the board's
neighbour table and the host's neighbour state, and the capture counts the board's ARP
frames, which travel the same transmit path as its replies. The flush runs before power
(`R0-FL`) as well as after the catch (`R1-FL`), so an entry the flush cannot remove stops the
card before the owner presses.

---

## § 1 The image

`p2q`, the image blocks 44 and 45 booted, unchanged: recipe `a2c56bc8`, `nfjrom` 1,155,072 B
`4972edbadd2655a8…`, vmlinux `c5e2cfdba7730d47…`, initramfs content `51ea1604c7c163f3…`,
driver `rtl819x-nic 1.4`. 量 the chain is checked again by this card's own `cardnum` rows at
the freeze: the manifest `verdict green` with that vmlinux, the `rtkimage` record naming that
vmlinux, that `nfjrom_sha256` and a CLEAN tripwire verdict, the `nfjrom` and the `vmlinux` on
disk with those digests, and block 45's boot printing `RLXFW-ID0=A2C56BC8`; `looprun`'s
`--image-sha256` pins it again before the port opens, and `looprun` compares the booted
image's `RLXFW-ID0` with the build's digest. Nothing was rebuilt.

---

## § 2 The press, in order

| invocation | what runs | brackets |
|---|---|---:|
| `I-0` | before power: the pre-flight, the address, the adapter, no process named `tcpdump`, the flush, the capture directory empty, `pcapwin`'s digest and self-test, the host's counters | 0 |
| `I-1` | the press: cold catch, the flush, one `looprun` round to rlxfw's shell, `ps`, the opening map, `n_writes` | 0 |
| `I-W0` | in the background from here to `I-W9`: the host frame capture `W.pcap` | 0 |
| `I-A` | exactly one `tcpdump`; bracket 0; `A1`: 19 runs at 50 ms, each followed by its bracket; `A2`: the same 19 at 250 ms | 39 |
| `I-B` | bracket 0; 19 runs: re-arm, four raw frames, bracket | 20 |
| `I-C` | bracket 0; 11 runs: re-arm, two looped frames, bracket | 12 |
| `I-D` | `txmode 1`; bracket 0; 5 runs: re-arm, 60 pings, bracket; `txmode 0` | 6 |
| `I-W9` | the capture stopped and summed | 0 |
| `I-Z` | the closing map and `n_writes`; then the owner powers off | 0 |

The order of lengths in `A1`, `A2` and `B` is the same 19 runs: **60, 61, 60, 62, 60, 63, 60,
263, 60, 276, 60, 277, 1,514, 1,511, 1,514, 1,512, 1,514, 1,513, 1,514** — a control length
(60 or 1,514, both clean in `E2`) before and after every other length. `C` runs the eleven once
each in ascending order, with no control between them: its per-length re-arm is the
substitute (§ 7). `D` runs 60, 61, 60, 1,511, 1,514. 77 board brackets in all.

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

A **run** is one length in one arm; its **bracket** is the board read `<run>-R` and the host
read `<run>-H` that follow it, and Δ is this bracket minus the previous one — within an
invocation and across them (`B-00` is taken against `A2-19`, `C-00` against `B-19`, `D-00`
against `C-11`; the capture's windows chain the same way). The board read holds two driver
dumps, `n1` before the switch and `n2` after it. From the board read: `n` = Δ`n_tx` between
the first dumps (every frame the driver handed the engine, stack and `tx` verb alike),
`s` = Δ`nd_stats` tx packets (the stack's frames only), Δ`n_tx_stop`, Δ`n_recov_fire`,
Δ`n_tx_drop_full`, the four `txd` OWN bits and `tx_stopped` in both dumps, `rx_ph1`,
Δ`nd_stats` rx, Δ`n_rx`, Δ`n_skb_fail`; the board's `Ip`/`Icmp` counters; its neighbour
table; and at the switch the CPU port's `CRCAlignErr` (`c`), `JabberErr` (`j`), `FragErr`
(`f`), `Drop` (`d`), `etherStatsDropEvents` and size buckets, and port 3's output (`o` =
Unicast + Multicast + Broadcast). From the host read: Δ`rx_packets` (`h`), Δ`tx_packets`,
the adapter's error columns, `Icmp.InEchoReps` (`i`, host-wide: every interface counts), the
neighbour state, and the capture's window since the previous host read (`w` frames; `w_r`
echo replies with their sequence numbers, `echo_vid` the VIDs of the tagged ones; `w_n` the
driver's `0x88B5` frames; `w_a` ARP; their lengths; `vlan8100`; the IPv4 excess;
`capture_live` and `tcpdump_procs`). A stimulus cell's `ping` prints each reply it counted
(`p`), a reading only (P6).

Bucket arithmetic, 讀 and 量 by block 45's host-to-board control: the CPU port's buckets count
the frame with its FCS, so a frame of L bytes lands in the bucket of L + 4 — 60 → `64:`,
61–63 → `65 -127:`, 263–277 → `256 - 511:`, 1,511–1,514 → `1024 - 1518:`. No length on this card
lies in `512 - 1023:`.

A run is **CLEAN** when `j = f = d = 0`, `c` lies inside P0's two-read bound, `o = c`,
`h = o`, `w = h` wherever P0 tests it, and (stack runs) `w_r` — or `i` where the capture is
not live — equals the requests sent. It is **FAULT** when `j + f + d ≥ 1`: the CPU port
refused at least one frame the driver sent. Anything else — no port error and still a
shortfall — is **LOSS ELSEWHERE**, and the stage chain says where. At a length L, `A1`'s
**refused fraction** is `r = (j + f + d) / c`.

A run in `A1` or `A2` is **CARRIED** when its previous bracket shows a stall no recovery was
armed for: a `txd` OWN bit set in both driver dumps, or `tx_stopped 1` in the second (B, C and
D re-arm before every run, so none of their runs can be). The run then fills the ring, stops
and fires, and loses what the fire discards. At a CARRIED run the fire, the stop, the stack's
discards while stopped and `n − c` belong to the previous run: `0 ≤ n − c ≤ 3` replaces P0's
lower bound (讀 `nic_recov_fn` → `nic_do_arm`: a fire discards the four slots, at least one
of which holds the carried frame), nothing of it refutes P4 or P5, and the previous run reads
as a stall with no fire in its own bracket. A CARRIED run's own class is read from `j`, `f`
and `d` only.

**Bracket 0** of each arm (`A1-00`, `B-00`, `C-00`, `D-00`) follows no stimulus. `A1-00`'s
host Δ spans the boot and the `looprun` round, while the capture began after them: P0 is not
tested there. `B-00`, `C-00` and `D-00` span only quiet cells (the previous arm's last reads,
and D's mode switch): their Δs are read, and refute nothing.

### 3.1 The premise, tested in every bracket (and void for its arm if it fails at a control)

* **P0.** At every bracket after bracket 0: `o = c − j − d − f` exactly; `h = o`; `w = h`
  wherever both ends of the window read `capture_live yes` and `tcpdump_procs 1` — a capture
  that ended (a declared stop, its `timeout`, a crash) ends this conjunct there and voids
  nothing already captured; and the capture's own log, `W-TCPD`, ends with
  `0 packets dropped by kernel` once `W-TCPX` has stopped it.
  In `A1`, `A2`, `B` and `D`, at every control run (60 or 1,514) that is not CARRIED, the
  switch's count lies inside the bound the two driver reads give:
  `n1_k − n2_(k−1) ≤ c ≤ n2_k − n1_(k−1)` (Δ`n_tx` read on the two sides of each switch
  read), which is `c = n` exactly whenever nothing was sent during either read. `C` has no
  control run, and its looped frames are not expected at the switch: there only the upper
  half holds, and `c = 0` is P9's reading, not P0's. **Refuted by** any bracket where one of
  these fails by one frame or more. At a control run, that makes the stage chain void for
  every run of that arm; at another run, it makes that run's localization void.

### 3.2 Arm `A1` — the stack at `E2`'s spacing (60 requests, 50 ms apart, fixed count)

* **P1, the class of each length** (推, one instance, `E2`, plus the contamination reading of
  the `R6b-0` dossier): **FAULT at 61, 62, 63, 263, 277, 1,511 and 1,512; CLEAN at every 60 and
  1,514 control that is not CARRIED, and at 276 and 1,513.** 276 and 1,513 lost their first 5
  and 2 requests in `E2`, each right after a failing length; here each follows a clean
  control, so the prediction is that they start clean.
  **Refuted by** a CLEAN run at any of the seven (the loss is not a property of the length at
  this spacing); a FAULT at a control or at 276 or 1,513. A FAULT at a control has three
  readings: a control does not isolate one length from the next; the start losses were not
  the previous length's state; or the control length is itself faulty at a low rate. 60 B is
  well founded (block 45's `E3`: 71,828 frames of 60 B with `JabberErr`, `FragErr` and `Drop`
  unchanged); 1,514 B rests on 40 clean frames (`E1` 20 of 20, `E2` 20 of 20), which do not
  exclude a rate up to about 7.5 % (3 / 40, the rule of three), and at 1 % a 60-frame
  control faults with probability 1 − 0.99⁶⁰ ≈ 0.45. The capture separates them in part:
  losses at a control's first sequence numbers (`echo_seq`) are the previous length's
  state, losses scattered through it are the control's own.
* **P2, the count on the wire** (推, one rule): each length after a control starts clean
  (P1's premise), so `w_r` is the number of requests 1–60 the length answers in its `E2`
  pattern — `E2`'s own answers among its first 60, with the requests `E2` lost at its very
  start to the previous length (62: 1–4; 63: 1–5; 276: 1–5; 1,513: 1–2; 263 and 1,512: all
  of the first 60, each after a blackout) restored as the length answered its later
  requests. 276 and 1,513 answered every later one → **60**. 62 answered exactly 61's
  sequence numbers from 5 on, and 61 answered 1 and not 2–4 → **17**. 263 and 1,512 answered
  1 of 179 → **0 or 1**. 63 answered 6 and 7 and then lost the next 32, so `E2` does not say
  how its first five fare → **9 to 14** (its 9, plus at most the 5 restored). Where `E2`'s run
  began clean the count is
  `E2`'s own: **60** at 60 and 1,514 (`E2`'s 20 of 20, extended), **17** at 61, **18** at 277,
  **0 or 1** at 1,511 (0 of 179). **Refuted by** a count outside these: the reply pattern is
  then not a fixed property of the length at this spacing. A miss here does not refute P1.
  A reading beside it, not a refutation of it: 推 (the dossier: the pattern is locked to each
  run's start) 61 and 62 answer `E2`'s sequence numbers 1, 5, 7, 13, 15, 20, 22, 27, 29, 35,
  37, 42, 44, 50, 52, 57, 59, and 277 answers 1, 3, 8, 10, 15, 17, 22, 24, 29, 31, 36, 38, 43,
  45, 50, 52, 57, 59 (`echo_seq`).
* **P3, the CPU port at FAULT runs** (推 from `E2`'s totals): summed over the seven FAULT runs,
  `Σj > Σd` (`E2` 678 against 43) and `Σf ≤ 2` (`E2` 1, block 45's `E4` 1; at their rate the
  chance of 3 or more over `A1`'s 420 requests is about 0.01); the `512 - 1023:` bucket rises
  by 0 in every CLEAN run. **Refuted by** `Σj ≤ Σd`, `Σf ≥ 3`, or a `512 - 1023:` count in a
  CLEAN run (the engine emits lengths never given even at clean lengths). The
  `512 - 1023:` total over the FAULT runs is a reading: `E2` counted 6 over the 1,106
  requests at the seven lengths, so `A1`'s 420 predict 2.3, and 0 has probability
  e^−2.3 ≈ 0.10 with the mechanism unchanged. `n − c` at a FAULT run is a reading, not a
  prediction: `E2` lost 41 between the driver and the switch, of which at most 20 are frames
  its 5 recoveries discarded unsent (four per fire, `NET-113`), so at least 21 are
  unexplained; this card gives each its run.
* **P13, the CPU port by class of length** (推 from `E2`'s bucket arithmetic, the dossier
  § 2.4: `E2`'s 43 drops sat 1 in `65 -127:`, 27 in `256 - 511:`, 6 in `512 - 1023:` and 9 in
  `1024 - 1518:`, while 61–63 lost 387 replies and 1,511/1,512 lost 357): (a) `Σd` over `A1`'s
  61, 62 and 63 runs ≤ 1; (b) `Σd` over 263, 276 and 277 exceeds `Σd` over 61, 62, 63, 1,511
  and 1,512 together; (c) within {61, 62, 63} and within {1,511, 1,512}, `Σj > Σd`.
  **Refuted by** any of the three failing. At `E2`'s rate (1 drop over 435 requests; `A1`
  sends 180) (a) fails by chance with probability about 0.06. (c) failing with `Σj = Σd = 0`
  says the loss at those lengths is not the CPU port refusing frames: it happened before the
  switch.
* **P4, stall and recovery** (`M8`): Δ`n_recov_fire` ≥ 1 only in runs with `j + f ≥ 1`, and 0
  in every CLEAN run, a CARRIED run's fire belonging to the run before it (§ 3.0).
  **Refuted by** a fire in a run whose `j + f = 0` that is not CARRIED — the stall is then
  not caused by the length fault, and `NET-67 殘留` stays separate from it (the dossier's 否證
  `D4`).
* **P5, the board's stack** (讀 `net/core/dev.c` with `tx_queue_len 0`, `NET-57`): Δ`Ip.OutDiscards`
  ≥ 1 only in runs with Δ`n_tx_stop` ≥ 1 (a stopped queue drops); Δ`Icmp.OutDestUnreachs` ≥ 1
  only in runs where the board's neighbour resolution for the host failed (the dossier reads
  `E2`'s 9 as 3 neighbour failures × `queue_len` 3). **Refuted by** discards with no stop. The
  board's neighbour table is read in every bracket; its format on this kernel is 推 (never
  captured), so it is a reading, not the refutation.
* **P6, the host.** `w_r − i` equals the number of the window's echo replies tagged with a
  non-zero VID (`echo_vid`), at every run: every echo reply the capture holds reaches the
  host's ICMP layer unless its tag has a VID this host has no device for (量 veth: VID 5
  dropped, VID 0 kept). **Refuted by** any other difference: the host lost or gained echo
  replies between the adapter and ICMP for a reason the capture does not show (`icmpcsum_ok`,
  the `dst` classes and the adapter's error columns then say which) — or, `i` being
  host-wide, an echo reply arrived on another interface during the window. `i − p` is a
  reading: replies the host counted after `ping` stopped waiting, and duplicates, which ping
  counts apart. 讀 iputils 20240117, `ping_common.c` `__schedule_exit`: once any reply has
  come, ping waits 2 × its largest rtt (at least one interval) after its last request, and
  `-W`'s 1 s only when none has; `E2` used `-w 10`, which kept ping alive, and its 150 = 150
  (ping's replies against the host's `Icmp.InEchoReps`) rests on that. `E2`'s largest rtt at
  a FAULT length was 2.33 ms, and 165 ms at 1,513.

### 3.3 Arm `A2` — the stack at 250 ms (20 requests, fixed count), `M3`

`E2` has no isolated reading, so this arm carries a decision rule, written now, and a partial
prediction.

* **Decision rule, per length L that `A1` read FAULT:** `A2` FAULT at L → the fault needs no
  50 ms spacing and no frame in flight: the timing and in-flight part of `M3` is refuted as
  its sole cause at L. The part about fields left from the frame last sent from the same slot
  is not tested (A2 reuses each of the four slots every fourth frame, all at L). `A2` CLEAN at
  L (20 of 20, `j = f = d = 0`) → a history or timing effect at L, `M3` supported — **only
  where `A1`'s r at L exceeds 0.139**, the rate at which 20 clean frames have probability
  below 0.05 ((1 − r)²⁰ < 0.05); below it, `A2` CLEAN at L is undetermined. A control run
  that is not CLEAN makes the arm's verdicts for the lengths beside it undetermined, unless
  it is CARRIED and its own bracket ends with no OWN bit set and `tx_stopped 0`.
* **P7** (推): FAULT at 263, 1,511 and 1,512, whose `E2` loss was near-total; **no prediction**
  at 61, 62, 63 and 277, the lengths whose `E2` replies continued through the run (19, 20, 9
  and 39 on the wire). CLEAN at every control that is not CARRIED, and at 276 and 1,513.
  **Refuted by** a CLEAN run at 263, 1,511 or 1,512 where `A1`'s r there exceeds 0.139, or a
  FAULT at a control.

### 3.4 Arm `B` — the raw `tx` verb, the stack silent (`M7`)

Four broadcast frames of L bytes per run (`tx 0x3f 0x8800 0 <L − 14>`: portlist `0x3F`, flags
`0x8800`, VID 0 — the descriptor fields `nic_xmit` writes, 讀), two per cell, 1 s apart, on a
ring re-armed just before: slots 0–3 once each.

* **Stack silent, a precondition checked in every B bracket:** `s = 0`, Δ`Ip.OutRequests` = 0,
  Δ`n_rx` = 0. 讀 `nic_do_tx` takes no lock and shares `nic_tx_idx` with `nic_xmit`; a run in
  which the stack sent anything is void for `M7`. 量 block 45: the host sent 6 frames on this
  adapter between `D1-H7` (03:30:07) and `D1-H8` (03:33:34), 4 of them `D1-EPING`'s requests
  (推 the other 2 its ARP) — no background traffic of its own there.
* **P8** (推, the dossier's view that the fault is below the driver's code path): **B
  reproduces `A1`'s class length for length** — at a length `A1` read CLEAN, `n = c = o = h =
  w_n = 4`, every `w_n` frame L bytes long with `content_ok` 4; at a length `A1` read FAULT,
  `j + f + d ≥ 1` of 4. B differs from `A1` in five things at once: the code path
  (`nic_do_tx`, not `nic_xmit`), the content (`0x88B5` filler, not IPv4/ICMP), the destination
  (broadcast, not unicast), the spacing (four frames ≥ 1 s apart, not 60 at 50 ms) and the
  ring (freshly re-armed, not in use). So: **B FAULT at a length `A1` read FAULT is the
  informative direction** — the fault then needs neither the stack's path nor the 50 ms
  spacing nor a ring in use: `M7` is refuted as its cause at L, and so is `M3`'s timing and
  in-flight part. **B CLEAN at such a length separates nothing by itself**, and counts at all
  only where `A1`'s r at L exceeds 0.527 ((1 − r)⁴ < 0.05): read beside `A2` at L, `A2` CLEAN
  too → spacing or history (`M3`) accounts for it and `M7` stays undetermined; `A2` FAULT →
  `M7`, or the content, or the destination, which B does not separate. B FAULT at a length
  `A1` read CLEAN is a separate reading (content or broadcast dependence).
  **Refuted by** B CLEAN, with r above 0.527, at a length `A1` read FAULT; or B FAULT at a
  length `A1` read CLEAN. A `txd` bit still set at the bracket after four frames is a stall
  with no recovery possible (the `tx` verb never arms one, 讀) and is recorded per slot.

### 3.5 Arm `C` — loopback, the engine's own view (`M6`, the dossier's `D1`)

Two frames of L bytes per run, `lb on` before the first and `lb off` 1 s after the second,
on a freshly re-armed ring.

* **Nothing else received, a precondition checked in every C bracket:** `s = 0` and the host
  adapter's Δ`tx_packets` = 0. 讀 `nic_napi_harvest` sets `rx_ph1` from every frame it
  harvests and counts every one in `nd_stats` rx, so one frame from the host overwrites the
  looped frame's `rx_ph1` and adds to rx; a run in which the host sent anything is void for
  `M6`.
* **P9** (推, from one reading: rung 1, L = 60): at every L, `rx_ph1`'s upper 16 bits read
  L + 4 (`00400000` at 60 is `0x40` = 64), Δ`nd_stats` rx = 2 frames and 2L bytes, Δ`n_rx` = 2,
  Δ`n_skb_fail` = 0; nothing reaches the switch (`c = 0`), the host (`h = 0`) or the capture
  (`w = 0`). Δ rx bytes is not a second source: the driver adds `ph_len − 4` from the same
  word (讀 `nic_napi_harvest`), so it says only that both frames carried the same length.
  **Refuted, in the direction that matters, by** `rx_ph1`'s length other than L + 4, Δ rx
  bytes other than 2L, or Δ`n_skb_fail` ≥ 1, at any L: the looped descriptor then carries a
  length the driver did not write — the engine framed or fetched the frame differently from
  its descriptor, and `M1`/`M2` (the descriptor conventions) come first. **The right values at
  every L do not refute the engine's fetch as the stage.** They are what a correct fetch
  gives, and also what a `ph_len` carried over from the TX descriptor gives: rung 1's
  `rx_ph1 00400000` equals bit for bit the TX word the driver wrote (`NIC_PH_MK1(64, 0, 0)`,
  `txd0 … len 64` in the same dump), while its `rx_ph3 821F0000` shows the engine did write
  the RX header. C does not tell the two apart (§ 7). Two frames count against `A1`'s rate
  only where `A1`'s r at L exceeds 0.776 ((1 − r)² < 0.05). `c > 0` in a C bracket refutes
  "loopback diverts": the engine then also transmits to the switch, and C's `j` per length is
  one more raw-frame reading.

### 3.6 Arm `D` — `txmode 1` (the vendor's ring-full rule) at 61 and 1,511

* **P10** (讀 `nic_xmit`: mode 1 polls a busy slot up to 128 times and then drops, and never
  stops the queue): Δ`n_tx_stop` = 0 and Δ`n_recov_fire` = 0 in every D bracket; D bracket 0
  reads `tx_mode 1` (a gate). (推) **61 and 1,511 are FAULT as in `A1`; the 60 and 1,514
  controls CLEAN.** In mode 1 nothing re-arms a stalled ring (the recovery is armed only on
  the stop path, which mode 1 never takes), so a stall at a FAULT length shows as
  Δ`n_tx_drop_full` ≥ 1 with the rest of that run lost, and a loss without a stall shows as
  `j` with Δ`n_tx_drop_full` = 0 — the two forms `NET-67 殘留` has never told apart. The
  re-arm before each D run keeps a stall from carrying into the next.
  **Refuted by** 61 or 1,511 CLEAN under `txmode 1` (the length fault then needs the stop and
  recovery path — or the re-arm, which D adds beside the mode, § 7); a stop or a fire in D
  (the mode did not take).

### 3.7 The tag (`M4`)

* **P11** (推, block 45's 39 − 20 = 19 and 76 B = 19 × 4): at every run where `w_r > i` the
  window holds `w_r − i` echo replies with EtherType `0x8100` at byte 12 and a non-zero VID
  (`vlan8100`, `echo_vid`), each with IPv4 excess 4, and the host's `otherhost` column rises by
  that count. 推 this happens at 277 in `A1`, and at no CLEAN run. The capture runs through
  every arm, so this is read at every run, not only at `A1-12`; `echo_seq_tagged` names the
  requests whose replies carried a tag.
  **Refuted (`M4` false) by** `w_r − i ≥ 1` with no echo reply of non-zero VID in the window:
  the host dropped those replies before IP for another reason (the excess and the `dst`
  classes then say which). Tagged frames at a CLEAN run refute "the tag belongs to the length
  fault".

### 3.8 The maps and `n_writes`

* **P12.** `R1-M0` (after the round) and `R1-M1` (before power-off): the section digest
  `0927be41…`, one `DIFFER` in group 0, 31 same — block 45's `D1-MB0` exactly, whose map is
  the bracket's "before". **Refuted by** any other digest or group line: flash moved since
  block 45, and no vendor boot follows until the owner has read it.
* **P14.** `R1-NW0` and `R1-NW1` read `n_writes 0` (a gate), `n_write_refused 0` and
  `recipe_id A2C56BC8` — the image's recipe through `/proc`, a second route to the number
  `looprun` checks in `RLXFW-ID0`. **Refuted by** `n_writes` other than 0 (rlxfw wrote flash:
  the owner is told and the press ends, § 6), or another `recipe_id` (the booted image is not
  `p2q`). What it cannot see: a write by anything but rlxfw's driver.

### 3.9 Which mechanism each arm can refute, and which it cannot

| candidate (dossier § 3.4) | arm | refuted when |
|---|---|---|
| `M3` history or timing | `A2`; B's fresh ring | § 3.3's rule; B FAULT refutes its timing part (P8) |
| `M4` a tag the frame was not given | the capture, every run | P11 |
| `M6` the CPU interface's own framing | C | P9's informative direction only |
| `M7` the stack's path | B | B FAULT at a length `A1` read FAULT (P8); B CLEAN alone does not support it |
| `M8` jabber causes the stall | `A1`, `A2`, D | P4, P10 |
| `M1` `m_len`/`m_extsize` against `ph_len` | — | needs a driver verb (`txlen`), `R6b-2` |
| `M2` the buffer's start offset | — | needs a driver verb (`txoff`), `R6b-2` |
| `M5` portlist `0x3F` or direct/lookup flags | — | the `tx` verb could sweep it (the dossier: portlist `0x08`, `0x1F`, `0x3F`, flags `0x8860`); not in this card's arms |

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck`
refuses the verbs (`FW-113`); every upload is `looprun`'s, which requires `00000000` read
back out of the `AUTOBURN` word before it uploads. 🔴 Every `--send` is at most 127
characters and carries no `$`. 🔴 **No frame capture is printed**: `tcpdump` writes only to
`$FWRE_WORK/rebuild/s111/r6b/pcap/`, and only `pcapwin.py`, which prints no address, no ICMP
identifier and no directory, reads it at the bench; its cell logs, and `tcpdump`'s own
(`listening on`, the three stop counts), are what reaches `bench/`. 🔴 No host cell prints a
home path into `bench/` (`tools/audit-bench-log.py`, a CI exit-code gate): `R0-SUM` reads its
file on stdin. 🔴 `HN` prints the adapter's counters through `grep -v link/` and the
neighbour's state only. 🔴 No cell touches the reset button. 🔴 `rlx0` is never brought
down in this boot (`NET-58`). 🔴 `sudo -n pkill -INT -x tcpdump` stops every process named
`tcpdump` on the host: `R0-TCPC` requires none before power, `A-LIVE` exactly one (the
card's) before the arms, every window prints the count, and no other capture is started
during the press. ⚠️ Off-card cells are declared in
`bench/2026-09-25c/CORRECTIONS-block46.md` before they run.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-25c --skip S2,S3,S4 --recipe-override a2c56bc8 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`; never `-s -s`, which would print each flushed entry's address
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — the adapter's counters, the host's `Ip`/`Icmp` counters, the adapter's error columns (with `otherhost` when non-zero), and the neighbour's state only
`PW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py window /home/key/fwre-work/rebuild/s111/r6b/pcap/W.pcap --if enxfc19286184c9 --prev <prev>`
`PE <s>` = `ping -I enxfc19286184c9 -c 60 -i 0.05 -W 1 -s <s> 10.1.1.3`
`PI <s>` = `ping -I enxfc19286184c9 -c 20 -i 0.25 -W 1 -s <s> 10.1.1.3`
`TD <f>` = `timeout 3600 sudo -n tcpdump -n -U -Q in -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s111/r6b/pcap/<f>`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — block 45's macro, unchanged; `; true` because `flashmap compare` exits 1 on the expected group-0 `DIFFER`

A ping's `-s` is L − 42 and a `tx` verb's last argument L − 14 (the driver adds the 14-byte
header, 讀 `nic_do_tx`). A board read's `sleep 2` is shorter than its `--seconds 15` and it
has no `--idle`; a stimulus cell's longest silence, its `sleep 1`, is shorter than its
`--idle 3`. Every host bracket passes the previous host bracket's log to `pcapwin` as `--prev`,
across arms as well, so its window starts where the previous one ended; `A1-00-H` and the
closing summary `W-WALL` pass `none`. The capture's `timeout 3600` outlasts the arms' budget
(§ 6).

### Before power

```
CAP --out bench/2026-09-25c/R0-PRE --seconds 3
HOST bench/2026-09-25c/R0-PREC :: ls bench/2026-09-25c/R0-PRE.log bench/2026-09-25c/R0-PRE.timing bench/2026-09-25c/R0-PRE.meta.json && cat bench/2026-09-25c/R0-PRE.meta.json
HOST bench/2026-09-25c/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-25c/R0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9
HOST bench/2026-09-25c/R0-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-25c/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-25c/R0-PCAP :: mkdir -p /home/key/fwre-work/rebuild/s111/r6b/pcap && find /home/key/fwre-work/rebuild/s111/r6b/pcap -name '*.pcap' | wc -l
HOST bench/2026-09-25c/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py
HOST bench/2026-09-25c/R0-PWT :: /usr/bin/python3 /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py --self-test
HOST bench/2026-09-25c/R0-H :: HN
```

### The press — the catch, the shell, the opening map, `n_writes`

```
CAP --out bench/2026-09-25c/R1-CATCH --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-25c/R1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-25c/R1Q :: LR --cell R1Q QIMG --iterations 1
CAP --out bench/2026-09-25c/R1-PS --send 'ps' --idle 3 --seconds 30
CAP --out bench/2026-09-25c/R1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-25c/R1-MB0 :: MB bench/2026-09-25c/R1-M0
CAP --out bench/2026-09-25c/R1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
```

### The capture, in the background from here to `I-W9`

```
HOST& bench/2026-09-25c/W-TCPD :: TD W.pcap
```

### Arm A — the stack: `A1` at 50 ms, then `A2` at 250 ms

```
HOST bench/2026-09-25c/A-LIVE :: pgrep -xc tcpdump ; true
CAP --out bench/2026-09-25c/A1-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-00-H :: HN ; PW none
HOST bench/2026-09-25c/A1-01-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-01-H :: HN ; PW bench/2026-09-25c/A1-00-H.log
HOST bench/2026-09-25c/A1-02-P0061 :: PE 19
CAP --out bench/2026-09-25c/A1-02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-02-H :: HN ; PW bench/2026-09-25c/A1-01-H.log
HOST bench/2026-09-25c/A1-03-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-03-H :: HN ; PW bench/2026-09-25c/A1-02-H.log
HOST bench/2026-09-25c/A1-04-P0062 :: PE 20
CAP --out bench/2026-09-25c/A1-04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-04-H :: HN ; PW bench/2026-09-25c/A1-03-H.log
HOST bench/2026-09-25c/A1-05-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-05-H :: HN ; PW bench/2026-09-25c/A1-04-H.log
HOST bench/2026-09-25c/A1-06-P0063 :: PE 21
CAP --out bench/2026-09-25c/A1-06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-06-H :: HN ; PW bench/2026-09-25c/A1-05-H.log
HOST bench/2026-09-25c/A1-07-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-07-H :: HN ; PW bench/2026-09-25c/A1-06-H.log
HOST bench/2026-09-25c/A1-08-P0263 :: PE 221
CAP --out bench/2026-09-25c/A1-08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-08-H :: HN ; PW bench/2026-09-25c/A1-07-H.log
HOST bench/2026-09-25c/A1-09-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-09-H :: HN ; PW bench/2026-09-25c/A1-08-H.log
HOST bench/2026-09-25c/A1-10-P0276 :: PE 234
CAP --out bench/2026-09-25c/A1-10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-10-H :: HN ; PW bench/2026-09-25c/A1-09-H.log
HOST bench/2026-09-25c/A1-11-P0060 :: PE 18
CAP --out bench/2026-09-25c/A1-11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-11-H :: HN ; PW bench/2026-09-25c/A1-10-H.log
HOST bench/2026-09-25c/A1-12-P0277 :: PE 235
CAP --out bench/2026-09-25c/A1-12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-12-H :: HN ; PW bench/2026-09-25c/A1-11-H.log
HOST bench/2026-09-25c/A1-13-P1514 :: PE 1472
CAP --out bench/2026-09-25c/A1-13-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-13-H :: HN ; PW bench/2026-09-25c/A1-12-H.log
HOST bench/2026-09-25c/A1-14-P1511 :: PE 1469
CAP --out bench/2026-09-25c/A1-14-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-14-H :: HN ; PW bench/2026-09-25c/A1-13-H.log
HOST bench/2026-09-25c/A1-15-P1514 :: PE 1472
CAP --out bench/2026-09-25c/A1-15-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-15-H :: HN ; PW bench/2026-09-25c/A1-14-H.log
HOST bench/2026-09-25c/A1-16-P1512 :: PE 1470
CAP --out bench/2026-09-25c/A1-16-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-16-H :: HN ; PW bench/2026-09-25c/A1-15-H.log
HOST bench/2026-09-25c/A1-17-P1514 :: PE 1472
CAP --out bench/2026-09-25c/A1-17-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-17-H :: HN ; PW bench/2026-09-25c/A1-16-H.log
HOST bench/2026-09-25c/A1-18-P1513 :: PE 1471
CAP --out bench/2026-09-25c/A1-18-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-18-H :: HN ; PW bench/2026-09-25c/A1-17-H.log
HOST bench/2026-09-25c/A1-19-P1514 :: PE 1472
CAP --out bench/2026-09-25c/A1-19-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A1-19-H :: HN ; PW bench/2026-09-25c/A1-18-H.log
HOST bench/2026-09-25c/A2-01-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-01-H :: HN ; PW bench/2026-09-25c/A1-19-H.log
HOST bench/2026-09-25c/A2-02-P0061 :: PI 19
CAP --out bench/2026-09-25c/A2-02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-02-H :: HN ; PW bench/2026-09-25c/A2-01-H.log
HOST bench/2026-09-25c/A2-03-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-03-H :: HN ; PW bench/2026-09-25c/A2-02-H.log
HOST bench/2026-09-25c/A2-04-P0062 :: PI 20
CAP --out bench/2026-09-25c/A2-04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-04-H :: HN ; PW bench/2026-09-25c/A2-03-H.log
HOST bench/2026-09-25c/A2-05-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-05-H :: HN ; PW bench/2026-09-25c/A2-04-H.log
HOST bench/2026-09-25c/A2-06-P0063 :: PI 21
CAP --out bench/2026-09-25c/A2-06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-06-H :: HN ; PW bench/2026-09-25c/A2-05-H.log
HOST bench/2026-09-25c/A2-07-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-07-H :: HN ; PW bench/2026-09-25c/A2-06-H.log
HOST bench/2026-09-25c/A2-08-P0263 :: PI 221
CAP --out bench/2026-09-25c/A2-08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-08-H :: HN ; PW bench/2026-09-25c/A2-07-H.log
HOST bench/2026-09-25c/A2-09-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-09-H :: HN ; PW bench/2026-09-25c/A2-08-H.log
HOST bench/2026-09-25c/A2-10-P0276 :: PI 234
CAP --out bench/2026-09-25c/A2-10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-10-H :: HN ; PW bench/2026-09-25c/A2-09-H.log
HOST bench/2026-09-25c/A2-11-P0060 :: PI 18
CAP --out bench/2026-09-25c/A2-11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-11-H :: HN ; PW bench/2026-09-25c/A2-10-H.log
HOST bench/2026-09-25c/A2-12-P0277 :: PI 235
CAP --out bench/2026-09-25c/A2-12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-12-H :: HN ; PW bench/2026-09-25c/A2-11-H.log
HOST bench/2026-09-25c/A2-13-P1514 :: PI 1472
CAP --out bench/2026-09-25c/A2-13-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-13-H :: HN ; PW bench/2026-09-25c/A2-12-H.log
HOST bench/2026-09-25c/A2-14-P1511 :: PI 1469
CAP --out bench/2026-09-25c/A2-14-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-14-H :: HN ; PW bench/2026-09-25c/A2-13-H.log
HOST bench/2026-09-25c/A2-15-P1514 :: PI 1472
CAP --out bench/2026-09-25c/A2-15-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-15-H :: HN ; PW bench/2026-09-25c/A2-14-H.log
HOST bench/2026-09-25c/A2-16-P1512 :: PI 1470
CAP --out bench/2026-09-25c/A2-16-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-16-H :: HN ; PW bench/2026-09-25c/A2-15-H.log
HOST bench/2026-09-25c/A2-17-P1514 :: PI 1472
CAP --out bench/2026-09-25c/A2-17-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-17-H :: HN ; PW bench/2026-09-25c/A2-16-H.log
HOST bench/2026-09-25c/A2-18-P1513 :: PI 1471
CAP --out bench/2026-09-25c/A2-18-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-18-H :: HN ; PW bench/2026-09-25c/A2-17-H.log
HOST bench/2026-09-25c/A2-19-P1514 :: PI 1472
CAP --out bench/2026-09-25c/A2-19-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/A2-19-H :: HN ; PW bench/2026-09-25c/A2-18-H.log
```

### Arm B — the raw `tx` verb, the stack silent

```
CAP --out bench/2026-09-25c/B-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-00-H :: HN ; PW bench/2026-09-25c/A2-19-H.log
CAP --out bench/2026-09-25c/B-01-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-01-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-01-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-01-H :: HN ; PW bench/2026-09-25c/B-00-H.log
CAP --out bench/2026-09-25c/B-02-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-02-T0061a --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-02-T0061b --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-02-H :: HN ; PW bench/2026-09-25c/B-01-H.log
CAP --out bench/2026-09-25c/B-03-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-03-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-03-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-03-H :: HN ; PW bench/2026-09-25c/B-02-H.log
CAP --out bench/2026-09-25c/B-04-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-04-T0062a --send 'echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-04-T0062b --send 'echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-04-H :: HN ; PW bench/2026-09-25c/B-03-H.log
CAP --out bench/2026-09-25c/B-05-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-05-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-05-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-05-H :: HN ; PW bench/2026-09-25c/B-04-H.log
CAP --out bench/2026-09-25c/B-06-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-06-T0063a --send 'echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-06-T0063b --send 'echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-06-H :: HN ; PW bench/2026-09-25c/B-05-H.log
CAP --out bench/2026-09-25c/B-07-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-07-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-07-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-07-H :: HN ; PW bench/2026-09-25c/B-06-H.log
CAP --out bench/2026-09-25c/B-08-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-08-T0263a --send 'echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-08-T0263b --send 'echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-08-H :: HN ; PW bench/2026-09-25c/B-07-H.log
CAP --out bench/2026-09-25c/B-09-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-09-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-09-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-09-H :: HN ; PW bench/2026-09-25c/B-08-H.log
CAP --out bench/2026-09-25c/B-10-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-10-T0276a --send 'echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-10-T0276b --send 'echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-10-H :: HN ; PW bench/2026-09-25c/B-09-H.log
CAP --out bench/2026-09-25c/B-11-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-11-T0060a --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-11-T0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-11-H :: HN ; PW bench/2026-09-25c/B-10-H.log
CAP --out bench/2026-09-25c/B-12-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-12-T0277a --send 'echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-12-T0277b --send 'echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-12-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-12-H :: HN ; PW bench/2026-09-25c/B-11-H.log
CAP --out bench/2026-09-25c/B-13-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-13-T1514a --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-13-T1514b --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-13-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-13-H :: HN ; PW bench/2026-09-25c/B-12-H.log
CAP --out bench/2026-09-25c/B-14-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-14-T1511a --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-14-T1511b --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-14-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-14-H :: HN ; PW bench/2026-09-25c/B-13-H.log
CAP --out bench/2026-09-25c/B-15-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-15-T1514a --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-15-T1514b --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-15-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-15-H :: HN ; PW bench/2026-09-25c/B-14-H.log
CAP --out bench/2026-09-25c/B-16-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-16-T1512a --send 'echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-16-T1512b --send 'echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-16-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-16-H :: HN ; PW bench/2026-09-25c/B-15-H.log
CAP --out bench/2026-09-25c/B-17-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-17-T1514a --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-17-T1514b --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-17-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-17-H :: HN ; PW bench/2026-09-25c/B-16-H.log
CAP --out bench/2026-09-25c/B-18-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-18-T1513a --send 'echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-18-T1513b --send 'echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-18-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-18-H :: HN ; PW bench/2026-09-25c/B-17-H.log
CAP --out bench/2026-09-25c/B-19-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-19-T1514a --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-19-T1514b --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/B-19-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/B-19-H :: HN ; PW bench/2026-09-25c/B-18-H.log
```

### Arm C — loopback

```
CAP --out bench/2026-09-25c/C-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-00-H :: HN ; PW bench/2026-09-25c/B-19-H.log
CAP --out bench/2026-09-25c/C-01-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-01-L0060a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-01-L0060b --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-01-H :: HN ; PW bench/2026-09-25c/C-00-H.log
CAP --out bench/2026-09-25c/C-02-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-02-L0061a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-02-L0061b --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-02-H :: HN ; PW bench/2026-09-25c/C-01-H.log
CAP --out bench/2026-09-25c/C-03-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-03-L0062a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-03-L0062b --send 'echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-03-H :: HN ; PW bench/2026-09-25c/C-02-H.log
CAP --out bench/2026-09-25c/C-04-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-04-L0063a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-04-L0063b --send 'echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-04-H :: HN ; PW bench/2026-09-25c/C-03-H.log
CAP --out bench/2026-09-25c/C-05-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-05-L0263a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-05-L0263b --send 'echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-05-H :: HN ; PW bench/2026-09-25c/C-04-H.log
CAP --out bench/2026-09-25c/C-06-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-06-L0276a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-06-L0276b --send 'echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-06-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-06-H :: HN ; PW bench/2026-09-25c/C-05-H.log
CAP --out bench/2026-09-25c/C-07-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-07-L0277a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-07-L0277b --send 'echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-07-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-07-H :: HN ; PW bench/2026-09-25c/C-06-H.log
CAP --out bench/2026-09-25c/C-08-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-08-L1511a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-08-L1511b --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-08-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-08-H :: HN ; PW bench/2026-09-25c/C-07-H.log
CAP --out bench/2026-09-25c/C-09-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-09-L1512a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-09-L1512b --send 'echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-09-H :: HN ; PW bench/2026-09-25c/C-08-H.log
CAP --out bench/2026-09-25c/C-10-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-10-L1513a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-10-L1513b --send 'echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-10-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-10-H :: HN ; PW bench/2026-09-25c/C-09-H.log
CAP --out bench/2026-09-25c/C-11-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-11-L1514a --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-11-L1514b --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/C-11-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/C-11-H :: HN ; PW bench/2026-09-25c/C-10-H.log
```

### Arm D — `txmode 1`

```
CAP --out bench/2026-09-25c/D-00-M1 --send 'echo txmode 1 > /proc/rtl819x-nic' --idle 3 --seconds 8
CAP --out bench/2026-09-25c/D-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-00-H :: HN ; PW bench/2026-09-25c/C-11-H.log
CAP --out bench/2026-09-25c/D-01-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
HOST bench/2026-09-25c/D-01-P0060 :: PE 18
CAP --out bench/2026-09-25c/D-01-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-01-H :: HN ; PW bench/2026-09-25c/D-00-H.log
CAP --out bench/2026-09-25c/D-02-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
HOST bench/2026-09-25c/D-02-P0061 :: PE 19
CAP --out bench/2026-09-25c/D-02-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-02-H :: HN ; PW bench/2026-09-25c/D-01-H.log
CAP --out bench/2026-09-25c/D-03-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
HOST bench/2026-09-25c/D-03-P0060 :: PE 18
CAP --out bench/2026-09-25c/D-03-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-03-H :: HN ; PW bench/2026-09-25c/D-02-H.log
CAP --out bench/2026-09-25c/D-04-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
HOST bench/2026-09-25c/D-04-P1511 :: PE 1469
CAP --out bench/2026-09-25c/D-04-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-04-H :: HN ; PW bench/2026-09-25c/D-03-H.log
CAP --out bench/2026-09-25c/D-05-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 8
HOST bench/2026-09-25c/D-05-P1514 :: PE 1472
CAP --out bench/2026-09-25c/D-05-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# ' --seconds 15
HOST bench/2026-09-25c/D-05-H :: HN ; PW bench/2026-09-25c/D-04-H.log
CAP --out bench/2026-09-25c/D-06-M0 --send 'echo txmode 0 > /proc/rtl819x-nic' --idle 3 --seconds 8
```

### The capture stopped

```
HOST bench/2026-09-25c/W-TCPX :: sudo -n pkill -INT -x tcpdump && sleep 1
HOST bench/2026-09-25c/W-WALL :: PW none
```

### The closing map and `n_writes`

```
CAP --out bench/2026-09-25c/R1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-25c/R1-MB1 :: MB bench/2026-09-25c/R1-M1
CAP --out bench/2026-09-25c/R1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
```

---

## § 6 How the cells are run

**Before any cell** (none of it a cell): the keeper `wsl -d Ubuntu-24.04 -- sleep 36000` in
the background before any attach; `usbipd list`, read fresh, then `usbipd attach` of the
CP2102 and of the GbE adapter, reading what each prints. Then in WSL, from the repository root:
`mkdir -p /home/key/fwre-work/rebuild/s111/r6b/run` (the transcripts' directory; `cardrun`
refuses a missing one); `/usr/bin/python3 tools/cardcheck.py numbers` on this card, every row
re-derived; `/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 321 captures came after the prediction, 321 did not`** (exit 1: nothing
is captured yet); and every invocation below once through `runblock.py … --dry`, each ending
`ALL ITEMS DONE`. **The catch window opens no later than 23:10 on 2026-09-25**; later, the
card is re-dated before power (`capdate` dates every capture by the card's declared date,
and the press is estimated below at about 22 minutes and allowed 45).

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log LOG`,
with LOG `/home/key/fwre-work/rebuild/s111/r6b/run/run-NAME.log`, exactly as block 44's § 6
describes (`--from CELL` only where a stop below says so), in the order `I-0`, `I-1`, `I-W0`,
`I-A`, `I-B`, `I-C`, `I-D`, `I-W9`, `I-Z`. **`I-W0` is started in the background** as soon as
`I-1` ends, as block 44's `I0` was; its transcript is read for `BG  W-TCPD … start seen`
before `I-A` starts, and it ends by itself (`DONE W-TCPD`, `ALL ITEMS DONE`) when `I-W9`'s
`W-TCPX` stops the capture. `NAME?` marks a cell whose non-zero exit is a reading, not a
stop; `gate:` items are the decision points; any failed cell or gate stops the invocation
and interrupts its own background cells — never another invocation's.

**The owner's power**: `I-1` starts with its catch; the owner is told when it opens and
presses inside its 180 s window, and powers off after `I-Z`, or at once where a stop below
says so. One item per line; each line is one argument.

**`I-0`** — before power: the pre-flight, the address, the adapter, no other capture, the flush, the capture directory, the checker

```run
R0-PRE?
R0-PREC
gate:grep=^  "bytes": 0,$:R0-PREC
gate:grep=^  "duration_s": 3\.[01][0-9]*,$:R0-PREC
R0-ADDR
gate:grep=inet 10\.1\.1\.2/24:R0-ADDR
R0-ETH?
R0-TCPC
gate:grep=\A0\n\Z:R0-TCPC
R0-FL
gate:grep=\A(?:0\n)+\Z:R0-FL
R0-PCAP
gate:grep=\A0\n\Z:R0-PCAP
R0-SUM
gate:grep=^e64118dee79d5487b8b7aa11272f007924680bd32b48fbdb3f6afd5a7d88e19f  -$:R0-SUM
R0-PWT
gate:grep=^pcapwin self-test: 17 of 17 passed$:R0-PWT
R0-H?
```

**`I-1`** — the press: the catch, the flush, one round to the shell, the process table, the opening map, `n_writes`

```run
R1-CATCH
gate:caught:R1-CATCH
R1-FL
gate:grep=\A(?:0\n)+\Z:R1-FL
R1Q
R1-PS
gate:grep=^ *1 +\S+ +\S+ +\S+ +/bin/sh *$:R1-PS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-PS
R1-M0
gate:until:R1-M0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M0
R1-MB0
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB0
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB0
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB0
R1-NW0
gate:grep=^n_writes 0$:R1-NW0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW0
```

**`I-W0`** — the host frame capture, one for all four arms, run in the background from here until `I-W9` stops it

```run
W-TCPD
```

**`I-A`** — arm A: the capture is running and is the only one; the stack, host ping, at E2's spacing (`A1`) and at 250 ms (`A2`)

```run
A-LIVE
gate:grep=\A1\n\Z:A-LIVE
A1-00-R
gate:until:A1-00-R
gate:grep=^version rtl819x-nic 1\.4$:A1-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-00-R
A1-00-H?
A1-01-P0060?
A1-01-R
gate:until:A1-01-R
gate:grep=^version rtl819x-nic 1\.4$:A1-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-01-R
A1-01-H?
A1-02-P0061?
A1-02-R
gate:until:A1-02-R
gate:grep=^version rtl819x-nic 1\.4$:A1-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-02-R
A1-02-H?
A1-03-P0060?
A1-03-R
gate:until:A1-03-R
gate:grep=^version rtl819x-nic 1\.4$:A1-03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-03-R
A1-03-H?
A1-04-P0062?
A1-04-R
gate:until:A1-04-R
gate:grep=^version rtl819x-nic 1\.4$:A1-04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-04-R
A1-04-H?
A1-05-P0060?
A1-05-R
gate:until:A1-05-R
gate:grep=^version rtl819x-nic 1\.4$:A1-05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-05-R
A1-05-H?
A1-06-P0063?
A1-06-R
gate:until:A1-06-R
gate:grep=^version rtl819x-nic 1\.4$:A1-06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-06-R
A1-06-H?
A1-07-P0060?
A1-07-R
gate:until:A1-07-R
gate:grep=^version rtl819x-nic 1\.4$:A1-07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-07-R
A1-07-H?
A1-08-P0263?
A1-08-R
gate:until:A1-08-R
gate:grep=^version rtl819x-nic 1\.4$:A1-08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-08-R
A1-08-H?
A1-09-P0060?
A1-09-R
gate:until:A1-09-R
gate:grep=^version rtl819x-nic 1\.4$:A1-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-09-R
A1-09-H?
A1-10-P0276?
A1-10-R
gate:until:A1-10-R
gate:grep=^version rtl819x-nic 1\.4$:A1-10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-10-R
A1-10-H?
A1-11-P0060?
A1-11-R
gate:until:A1-11-R
gate:grep=^version rtl819x-nic 1\.4$:A1-11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-11-R
A1-11-H?
A1-12-P0277?
A1-12-R
gate:until:A1-12-R
gate:grep=^version rtl819x-nic 1\.4$:A1-12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-12-R
A1-12-H?
A1-13-P1514?
A1-13-R
gate:until:A1-13-R
gate:grep=^version rtl819x-nic 1\.4$:A1-13-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-13-R
A1-13-H?
A1-14-P1511?
A1-14-R
gate:until:A1-14-R
gate:grep=^version rtl819x-nic 1\.4$:A1-14-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-14-R
A1-14-H?
A1-15-P1514?
A1-15-R
gate:until:A1-15-R
gate:grep=^version rtl819x-nic 1\.4$:A1-15-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-15-R
A1-15-H?
A1-16-P1512?
A1-16-R
gate:until:A1-16-R
gate:grep=^version rtl819x-nic 1\.4$:A1-16-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-16-R
A1-16-H?
A1-17-P1514?
A1-17-R
gate:until:A1-17-R
gate:grep=^version rtl819x-nic 1\.4$:A1-17-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-17-R
A1-17-H?
A1-18-P1513?
A1-18-R
gate:until:A1-18-R
gate:grep=^version rtl819x-nic 1\.4$:A1-18-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-18-R
A1-18-H?
A1-19-P1514?
A1-19-R
gate:until:A1-19-R
gate:grep=^version rtl819x-nic 1\.4$:A1-19-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A1-19-R
A1-19-H?
A2-01-P0060?
A2-01-R
gate:until:A2-01-R
gate:grep=^version rtl819x-nic 1\.4$:A2-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-01-R
A2-01-H?
A2-02-P0061?
A2-02-R
gate:until:A2-02-R
gate:grep=^version rtl819x-nic 1\.4$:A2-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-02-R
A2-02-H?
A2-03-P0060?
A2-03-R
gate:until:A2-03-R
gate:grep=^version rtl819x-nic 1\.4$:A2-03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-03-R
A2-03-H?
A2-04-P0062?
A2-04-R
gate:until:A2-04-R
gate:grep=^version rtl819x-nic 1\.4$:A2-04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-04-R
A2-04-H?
A2-05-P0060?
A2-05-R
gate:until:A2-05-R
gate:grep=^version rtl819x-nic 1\.4$:A2-05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-05-R
A2-05-H?
A2-06-P0063?
A2-06-R
gate:until:A2-06-R
gate:grep=^version rtl819x-nic 1\.4$:A2-06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-06-R
A2-06-H?
A2-07-P0060?
A2-07-R
gate:until:A2-07-R
gate:grep=^version rtl819x-nic 1\.4$:A2-07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-07-R
A2-07-H?
A2-08-P0263?
A2-08-R
gate:until:A2-08-R
gate:grep=^version rtl819x-nic 1\.4$:A2-08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-08-R
A2-08-H?
A2-09-P0060?
A2-09-R
gate:until:A2-09-R
gate:grep=^version rtl819x-nic 1\.4$:A2-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-09-R
A2-09-H?
A2-10-P0276?
A2-10-R
gate:until:A2-10-R
gate:grep=^version rtl819x-nic 1\.4$:A2-10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-10-R
A2-10-H?
A2-11-P0060?
A2-11-R
gate:until:A2-11-R
gate:grep=^version rtl819x-nic 1\.4$:A2-11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-11-R
A2-11-H?
A2-12-P0277?
A2-12-R
gate:until:A2-12-R
gate:grep=^version rtl819x-nic 1\.4$:A2-12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-12-R
A2-12-H?
A2-13-P1514?
A2-13-R
gate:until:A2-13-R
gate:grep=^version rtl819x-nic 1\.4$:A2-13-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-13-R
A2-13-H?
A2-14-P1511?
A2-14-R
gate:until:A2-14-R
gate:grep=^version rtl819x-nic 1\.4$:A2-14-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-14-R
A2-14-H?
A2-15-P1514?
A2-15-R
gate:until:A2-15-R
gate:grep=^version rtl819x-nic 1\.4$:A2-15-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-15-R
A2-15-H?
A2-16-P1512?
A2-16-R
gate:until:A2-16-R
gate:grep=^version rtl819x-nic 1\.4$:A2-16-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-16-R
A2-16-H?
A2-17-P1514?
A2-17-R
gate:until:A2-17-R
gate:grep=^version rtl819x-nic 1\.4$:A2-17-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-17-R
A2-17-H?
A2-18-P1513?
A2-18-R
gate:until:A2-18-R
gate:grep=^version rtl819x-nic 1\.4$:A2-18-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-18-R
A2-18-H?
A2-19-P1514?
A2-19-R
gate:until:A2-19-R
gate:grep=^version rtl819x-nic 1\.4$:A2-19-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):A2-19-R
A2-19-H?
```

**`I-B`** — arm B: the raw `tx` verb, the stack silent, the ring re-armed before every length

```run
B-00-R
gate:until:B-00-R
gate:grep=^version rtl819x-nic 1\.4$:B-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-R
B-00-H?
B-01-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-01-X
B-01-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-01-T0060a
B-01-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-01-T0060b
B-01-R
gate:until:B-01-R
gate:grep=^version rtl819x-nic 1\.4$:B-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-01-R
B-01-H?
B-02-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-02-X
B-02-T0061a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-02-T0061a
B-02-T0061b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-02-T0061b
B-02-R
gate:until:B-02-R
gate:grep=^version rtl819x-nic 1\.4$:B-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-02-R
B-02-H?
B-03-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-03-X
B-03-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-03-T0060a
B-03-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-03-T0060b
B-03-R
gate:until:B-03-R
gate:grep=^version rtl819x-nic 1\.4$:B-03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-03-R
B-03-H?
B-04-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-04-X
B-04-T0062a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-04-T0062a
B-04-T0062b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-04-T0062b
B-04-R
gate:until:B-04-R
gate:grep=^version rtl819x-nic 1\.4$:B-04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-04-R
B-04-H?
B-05-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-05-X
B-05-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-05-T0060a
B-05-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-05-T0060b
B-05-R
gate:until:B-05-R
gate:grep=^version rtl819x-nic 1\.4$:B-05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-05-R
B-05-H?
B-06-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-06-X
B-06-T0063a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-06-T0063a
B-06-T0063b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-06-T0063b
B-06-R
gate:until:B-06-R
gate:grep=^version rtl819x-nic 1\.4$:B-06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-06-R
B-06-H?
B-07-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-07-X
B-07-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-07-T0060a
B-07-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-07-T0060b
B-07-R
gate:until:B-07-R
gate:grep=^version rtl819x-nic 1\.4$:B-07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-07-R
B-07-H?
B-08-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-08-X
B-08-T0263a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-08-T0263a
B-08-T0263b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-08-T0263b
B-08-R
gate:until:B-08-R
gate:grep=^version rtl819x-nic 1\.4$:B-08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-08-R
B-08-H?
B-09-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-09-X
B-09-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-09-T0060a
B-09-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-09-T0060b
B-09-R
gate:until:B-09-R
gate:grep=^version rtl819x-nic 1\.4$:B-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-09-R
B-09-H?
B-10-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-10-X
B-10-T0276a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-10-T0276a
B-10-T0276b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-10-T0276b
B-10-R
gate:until:B-10-R
gate:grep=^version rtl819x-nic 1\.4$:B-10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-10-R
B-10-H?
B-11-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-11-X
B-11-T0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-11-T0060a
B-11-T0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-11-T0060b
B-11-R
gate:until:B-11-R
gate:grep=^version rtl819x-nic 1\.4$:B-11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-11-R
B-11-H?
B-12-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-12-X
B-12-T0277a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-12-T0277a
B-12-T0277b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-12-T0277b
B-12-R
gate:until:B-12-R
gate:grep=^version rtl819x-nic 1\.4$:B-12-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-12-R
B-12-H?
B-13-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-13-X
B-13-T1514a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-13-T1514a
B-13-T1514b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-13-T1514b
B-13-R
gate:until:B-13-R
gate:grep=^version rtl819x-nic 1\.4$:B-13-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-13-R
B-13-H?
B-14-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-14-X
B-14-T1511a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-14-T1511a
B-14-T1511b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-14-T1511b
B-14-R
gate:until:B-14-R
gate:grep=^version rtl819x-nic 1\.4$:B-14-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-14-R
B-14-H?
B-15-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-15-X
B-15-T1514a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-15-T1514a
B-15-T1514b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-15-T1514b
B-15-R
gate:until:B-15-R
gate:grep=^version rtl819x-nic 1\.4$:B-15-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-15-R
B-15-H?
B-16-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-16-X
B-16-T1512a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-16-T1512a
B-16-T1512b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-16-T1512b
B-16-R
gate:until:B-16-R
gate:grep=^version rtl819x-nic 1\.4$:B-16-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-16-R
B-16-H?
B-17-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-17-X
B-17-T1514a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-17-T1514a
B-17-T1514b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-17-T1514b
B-17-R
gate:until:B-17-R
gate:grep=^version rtl819x-nic 1\.4$:B-17-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-17-R
B-17-H?
B-18-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-18-X
B-18-T1513a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-18-T1513a
B-18-T1513b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-18-T1513b
B-18-R
gate:until:B-18-R
gate:grep=^version rtl819x-nic 1\.4$:B-18-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-18-R
B-18-H?
B-19-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-19-X
B-19-T1514a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-19-T1514a
B-19-T1514b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-19-T1514b
B-19-R
gate:until:B-19-R
gate:grep=^version rtl819x-nic 1\.4$:B-19-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-19-R
B-19-H?
```

**`I-C`** — arm C: loopback, the engine's own view of what it sent

```run
C-00-R
gate:until:C-00-R
gate:grep=^version rtl819x-nic 1\.4$:C-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-00-R
C-00-H?
C-01-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-01-X
C-01-L0060a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-01-L0060a
C-01-L0060b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-01-L0060b
C-01-R
gate:until:C-01-R
gate:grep=^version rtl819x-nic 1\.4$:C-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-01-R
C-01-H?
C-02-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-02-X
C-02-L0061a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-02-L0061a
C-02-L0061b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-02-L0061b
C-02-R
gate:until:C-02-R
gate:grep=^version rtl819x-nic 1\.4$:C-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-02-R
C-02-H?
C-03-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-03-X
C-03-L0062a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-03-L0062a
C-03-L0062b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-03-L0062b
C-03-R
gate:until:C-03-R
gate:grep=^version rtl819x-nic 1\.4$:C-03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-03-R
C-03-H?
C-04-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-04-X
C-04-L0063a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-04-L0063a
C-04-L0063b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-04-L0063b
C-04-R
gate:until:C-04-R
gate:grep=^version rtl819x-nic 1\.4$:C-04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-04-R
C-04-H?
C-05-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-05-X
C-05-L0263a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-05-L0263a
C-05-L0263b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-05-L0263b
C-05-R
gate:until:C-05-R
gate:grep=^version rtl819x-nic 1\.4$:C-05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-05-R
C-05-H?
C-06-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-06-X
C-06-L0276a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-06-L0276a
C-06-L0276b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-06-L0276b
C-06-R
gate:until:C-06-R
gate:grep=^version rtl819x-nic 1\.4$:C-06-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-06-R
C-06-H?
C-07-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-07-X
C-07-L0277a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-07-L0277a
C-07-L0277b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-07-L0277b
C-07-R
gate:until:C-07-R
gate:grep=^version rtl819x-nic 1\.4$:C-07-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-07-R
C-07-H?
C-08-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-08-X
C-08-L1511a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-08-L1511a
C-08-L1511b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-08-L1511b
C-08-R
gate:until:C-08-R
gate:grep=^version rtl819x-nic 1\.4$:C-08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-08-R
C-08-H?
C-09-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-09-X
C-09-L1512a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-09-L1512a
C-09-L1512b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-09-L1512b
C-09-R
gate:until:C-09-R
gate:grep=^version rtl819x-nic 1\.4$:C-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-09-R
C-09-H?
C-10-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-10-X
C-10-L1513a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-10-L1513a
C-10-L1513b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-10-L1513b
C-10-R
gate:until:C-10-R
gate:grep=^version rtl819x-nic 1\.4$:C-10-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-10-R
C-10-H?
C-11-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-11-X
C-11-L1514a
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-11-L1514a
C-11-L1514b
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-11-L1514b
C-11-R
gate:until:C-11-R
gate:grep=^version rtl819x-nic 1\.4$:C-11-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):C-11-R
C-11-H?
```

**`I-D`** — arm D: `txmode 1` at 61 and 1,511 B, the stack, the ring re-armed before every length

```run
D-00-M1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-00-M1
D-00-R
gate:until:D-00-R
gate:grep=^version rtl819x-nic 1\.4$:D-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-00-R
gate:grep=^tx_mode 1$:D-00-R
D-00-H?
D-01-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-01-X
D-01-P0060?
D-01-R
gate:until:D-01-R
gate:grep=^version rtl819x-nic 1\.4$:D-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-01-R
D-01-H?
D-02-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-02-X
D-02-P0061?
D-02-R
gate:until:D-02-R
gate:grep=^version rtl819x-nic 1\.4$:D-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-02-R
D-02-H?
D-03-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-03-X
D-03-P0060?
D-03-R
gate:until:D-03-R
gate:grep=^version rtl819x-nic 1\.4$:D-03-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-03-R
D-03-H?
D-04-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-04-X
D-04-P1511?
D-04-R
gate:until:D-04-R
gate:grep=^version rtl819x-nic 1\.4$:D-04-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-04-R
D-04-H?
D-05-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-05-X
D-05-P1514?
D-05-R
gate:until:D-05-R
gate:grep=^version rtl819x-nic 1\.4$:D-05-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-05-R
D-05-H?
D-06-M0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D-06-M0
```

**`I-W9`** — the capture stopped and summed, whatever ended the arms

```run
W-TCPX?
W-WALL?
```

**`I-Z`** — the closing map and `n_writes`; then the owner powers off

```run
R1-M1
gate:until:R1-M1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-M1
R1-MB1
gate:grep=^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46  -$:R1-MB1
gate:grep=^  DIFFER  000000  device c66a4126d7b1b862\.\.\. dump 8494cc8666b5c6f6\.\.\.$:R1-MB1
gate:grep=-- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$:R1-MB1
R1-NW1
gate:grep=^n_writes 0$:R1-NW1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):R1-NW1
```

**What each stop means, decided now** — a repeat is always a new name, declared in
`bench/2026-09-25c/CORRECTIONS-block46.md` before it runs, **except a power-off, which this
card decides and which waits for nothing**:

* **The loader gate on any board cell** (the capture holds `Booting...`, `---RealTek`,
  `<RealTek>` or `Linux version`) — and, for any other failed board cell, the same text found
  when its capture is read, which is done first: **the owner powers off at once** (§ 0 ⑤);
  no other cell and no `CORRECTIONS` entry comes before it. `I-W9` still runs (it touches
  only the host); `I-Z` does not, and the next card's first map closes this press's bracket.
  The rest is a new card.
* **`R0-PREC`**, **`R0-ADDR`**: as block 45's `D0-PREC` and `D0-ADDR`; no power.
  **`R0-TCPC`**: another `tcpdump` runs on the host — its owner stops it (never this card's
  `pkill`), and `R0-TCPC` runs again as `R0-TCPC2`; no power until it reads `0`.
  **`R0-FL`**: the same command once more as `R0-FL2`; a second failure: no power, and the
  host's entry is read at the desk. **`R0-PCAP`**: a capture file is already in the
  directory — it is moved out of it by hand, and `R0-PCAP` runs again as `R0-PCAP2`; no power
  until it reads `0`. **`R0-SUM`**, **`R0-PWT`**: the checker is not the one this card pins,
  or fails its own self-test — no power.
* **`gate:caught`** on `R1-CATCH`: the loader was not caught and may have autobooted the
  vendor — power off; the press is lost, and the next card's first map brackets that boot.
* **`R1-FL`'s gate**: the same command once more as `R1-FL2`; a second failure ends the press
  — power off.
* **`R1Q`'s exit**: its artefacts are the reading. If its round reached rlxfw's prompt (its
  `-boot` capture ends at `# `), `I-1` continues `--from R1-PS`; if not, power off, and the
  rest is a new card.
* **`R1-PS`'s shape gate**: a reading of the shell's shape; `I-1` continues `--from R1-M0`.
* **`gate:until`** on `R1-M0` or `R1-M1`: the map did not complete; it is repeated once as
  `R1-M0B`/`R1-MB0B` (or `R1-M1B`/`R1-MB1B`), whose output must match the same three
  patterns, applied with `grep -P`; a second failure ends the press. **A map gate** on
  `R1-MB0`: flash differs from block 45's map — the owner is told, `I-1` continues
  `--from R1-NW0`, and the arms still run (none boots the vendor or writes flash); no vendor
  boot until the owner has read it. On `R1-MB1`: the same, `I-Z` continues `--from R1-NW1`,
  and the press ends at power-off as planned.
* **`R1-NW0` or `R1-NW1`'s `n_writes` gate**: if the capture holds an `n_writes` line other
  than `n_writes 0`, rlxfw wrote flash — the owner is told, the press ends at power-off, and
  no vendor boot follows until the owner has read it. If it holds no `n_writes` line, the
  read is repeated once as `R1-NW0B` (or `R1-NW1B`); a second read with no line is recorded,
  the press's flash claim rests on the commands issued and the map bracket, and the next
  invocation starts as planned.
* **`W-TCPD`'s start** (no `listening on` within 20 s, 讀 `cardrun` `START_TIMEOUT_S`): no arm
  starts. The capture is repeated once as the off-card cell `W-TCPD2` — the same command,
  run by hand in the background — and `A-LIVE` then decides. If it too fails, the arms run
  without a capture, `I-A` starting `--from A1-00-R`: P0's `w = h` is not tested, P6 and P11
  are undetermined, and the counters stand alone.
* **`A-LIVE`'s gate**: `0` — the capture is not running: `I-W0`'s transcript is read, and the
  branch above applies. `2` or more — another `tcpdump` runs: its owner stops it, and
  `A-LIVE` runs again as `A-LIVE2`; the arms wait.
* **A board bracket's gate** (`-R`: the capture did not end on the prompt, or the driver did
  not answer `version rtl819x-nic 1.4`), with no loader or kernel text in it: `/dev/ttyUSB0`
  is checked, and the board read is typed again as the off-card cell `X-RT<n>` (the failed
  `-R` cell's own command under a new name). If it ends on the prompt with
  `version rtl819x-nic 1.4` and no loader or kernel text, it stands in for the failed `-R`,
  and the invocation continues `--from` the host bracket that follows. If it shows loader or
  vendor text, the owner powers off at once. **If it returns nothing, garbage, or a read that
  does not end on the prompt** (a `NET-64`-style hang, the watchdog still kicked), **the
  owner powers off**; the rest is a new card.
* **A stimulus, re-arm or mode `CAP` cell exits non-zero** (nothing came back), with no loader
  or kernel text: `X-RT<n>` as above. If rlxfw answers, the invocation continues `--from`
  **the same run's `-R` cell**, so that run still gets its bracket; that run is void (whether
  its stimulus ran is unknown), and the next run is measured against its bracket as usual.
  Otherwise, power off.
* **`D-00-R`'s `tx_mode 1` gate**: the mode did not take; `I-D` continues `--from D-06-M0`,
  and arm D is void.
* **a host stimulus, a host bracket, the capture stop or its summary**: `NAME?`, a reading;
  never a stop.
* **a background cell's exit** never stops a run.

Estimated duration, a guess from block 45's transcripts (`$FWRE_WORK/rebuild/s110/run-I-D1*.log`):
the catch runs its full 200 s; the `looprun` round took 21.3 s; `ps`, a map (`D1-M0` 13.9 s)
and an `n_writes` read (about 3.5 s: its bytes and `--idle 3`) follow; a board read is about
5.5 s (its `sleep 2`; about 10.4 KB — two driver dumps of 2,549 B, the SNMP of 1,116 B, the
switch of 4,126 B — at 38,400 baud, about 2.7 s; and what block 45's separate reads spent
beyond their bytes, `D1-N1` 3.9 s with `--idle 3`, `D1-K1` 2.4 s with a `sleep 1`); a host
read under 0.1 s (`D1-H1` 0.0 s); a re-arm or a mode cell about
3.2 s (`D1-X1` 3.16 s); a raw-frame cell about 4.3 s (its `sleep 1` and `--idle 3`); an `A1`
ping about 3 s (60 × 50 ms) and an `A2` ping about 5 s (20 × 250 ms); block 45 started an
invocation 16 s after the last ended. That gives the catch and the round about 4 min, arm A
about 6.2 min, arm B about 5.6 min, arm C about 3.1 min, arm D about 1.2 min, the capture's
stop and the closing map and `n_writes` about 0.3 min, and the gaps between the nine
invocations about 2 min — about 22 minutes from the catch's window to power-off (block 45's
press: 16 minutes, 03:18:48 to 03:34:38), against the ~45 minutes the owner allowed; the
capture's `timeout 3600` outlasts both.

---

## § 7 What this block does not establish

* The field at fault: it names a stage per length. `M1`, `M2` and `M5` (§ 3.9). Any length
  not among the eleven. More than one instance of any run.
* What the host adapter drops inside itself (`r8153_ecm` exposes no tally counters); a frame
  the switch drops with no counter. The content of a looped frame (NAPI keeps no copy).
* Which frame of a run the CPU port refused — only how many; the capture names which
  requests were answered (`echo_seq`), not which replies were refused.
* **What separates `A1` from `B`.** B differs in five things at once — the code path, the
  content, the destination, the spacing and the ring's state — so B CLEAN where `A1` read
  FAULT does not isolate `M7` (§ 3.4).
* **Whether the loopback `ph_len` is measured by the engine or carried from the TX
  descriptor.** Rung 1's one reading equals the TX word bit for bit; C's right values are
  what either gives (§ 3.5).
* **C has no control length between its lengths**, as the brief asked for the others; its
  per-length re-arm is the substitute: every C length starts on a freshly re-armed ring, which
  isolates the ring's state and nothing the re-arm does not reset.
* **`A1` reproduces `E2`'s spacing within a run, not `E2`'s back-to-back runs** or the
  between-length contamination they caused: here a bracket of about 5.5 s separates every
  run, by design.
* **The detection limits of the short arms.** A CLEAN verdict from `A2`'s 20 frames, B's 4 or
  C's 2 counts only where `A1`'s refused fraction at L exceeds 0.139, 0.527 or 0.776; below,
  it is undetermined, and the frames are assumed independent (推).
* **D adds the re-arm before every length beside `txmode 1`**: a difference between D and
  `A1` is not the mode's alone.
* **1,514's own fault rate** below about 7.5 % is not excluded by block 45 (§ 3.2 P1).
* `i` is host-wide: an echo reply from another interface during a window reads as a
  difference in P6.
* Whether a length that is CLEAN at 50 ms and at 250 ms stays clean under `NET-111`'s TCP
  load. Anything about `eth4`, which this press never opens. Any throughput or duration.
* A flash write by anything other than rlxfw's SPI driver, between the two maps, that the
  map does not see (`FLS-30`'s limits).

---

```cells
bench/2026-09-25c/R0-PRE
bench/2026-09-25c/R0-PREC
bench/2026-09-25c/R0-ADDR
bench/2026-09-25c/R0-ETH
bench/2026-09-25c/R0-TCPC
bench/2026-09-25c/R0-FL
bench/2026-09-25c/R0-PCAP
bench/2026-09-25c/R0-SUM
bench/2026-09-25c/R0-PWT
bench/2026-09-25c/R0-H
bench/2026-09-25c/R1-CATCH
bench/2026-09-25c/R1-FL
bench/2026-09-25c/R1Q
bench/2026-09-25c/R1-PS
bench/2026-09-25c/R1-M0
bench/2026-09-25c/R1-MB0
bench/2026-09-25c/R1-NW0
bench/2026-09-25c/W-TCPD
bench/2026-09-25c/A-LIVE
bench/2026-09-25c/A1-00-R
bench/2026-09-25c/A1-00-H
bench/2026-09-25c/A1-01-P0060
bench/2026-09-25c/A1-01-R
bench/2026-09-25c/A1-01-H
bench/2026-09-25c/A1-02-P0061
bench/2026-09-25c/A1-02-R
bench/2026-09-25c/A1-02-H
bench/2026-09-25c/A1-03-P0060
bench/2026-09-25c/A1-03-R
bench/2026-09-25c/A1-03-H
bench/2026-09-25c/A1-04-P0062
bench/2026-09-25c/A1-04-R
bench/2026-09-25c/A1-04-H
bench/2026-09-25c/A1-05-P0060
bench/2026-09-25c/A1-05-R
bench/2026-09-25c/A1-05-H
bench/2026-09-25c/A1-06-P0063
bench/2026-09-25c/A1-06-R
bench/2026-09-25c/A1-06-H
bench/2026-09-25c/A1-07-P0060
bench/2026-09-25c/A1-07-R
bench/2026-09-25c/A1-07-H
bench/2026-09-25c/A1-08-P0263
bench/2026-09-25c/A1-08-R
bench/2026-09-25c/A1-08-H
bench/2026-09-25c/A1-09-P0060
bench/2026-09-25c/A1-09-R
bench/2026-09-25c/A1-09-H
bench/2026-09-25c/A1-10-P0276
bench/2026-09-25c/A1-10-R
bench/2026-09-25c/A1-10-H
bench/2026-09-25c/A1-11-P0060
bench/2026-09-25c/A1-11-R
bench/2026-09-25c/A1-11-H
bench/2026-09-25c/A1-12-P0277
bench/2026-09-25c/A1-12-R
bench/2026-09-25c/A1-12-H
bench/2026-09-25c/A1-13-P1514
bench/2026-09-25c/A1-13-R
bench/2026-09-25c/A1-13-H
bench/2026-09-25c/A1-14-P1511
bench/2026-09-25c/A1-14-R
bench/2026-09-25c/A1-14-H
bench/2026-09-25c/A1-15-P1514
bench/2026-09-25c/A1-15-R
bench/2026-09-25c/A1-15-H
bench/2026-09-25c/A1-16-P1512
bench/2026-09-25c/A1-16-R
bench/2026-09-25c/A1-16-H
bench/2026-09-25c/A1-17-P1514
bench/2026-09-25c/A1-17-R
bench/2026-09-25c/A1-17-H
bench/2026-09-25c/A1-18-P1513
bench/2026-09-25c/A1-18-R
bench/2026-09-25c/A1-18-H
bench/2026-09-25c/A1-19-P1514
bench/2026-09-25c/A1-19-R
bench/2026-09-25c/A1-19-H
bench/2026-09-25c/A2-01-P0060
bench/2026-09-25c/A2-01-R
bench/2026-09-25c/A2-01-H
bench/2026-09-25c/A2-02-P0061
bench/2026-09-25c/A2-02-R
bench/2026-09-25c/A2-02-H
bench/2026-09-25c/A2-03-P0060
bench/2026-09-25c/A2-03-R
bench/2026-09-25c/A2-03-H
bench/2026-09-25c/A2-04-P0062
bench/2026-09-25c/A2-04-R
bench/2026-09-25c/A2-04-H
bench/2026-09-25c/A2-05-P0060
bench/2026-09-25c/A2-05-R
bench/2026-09-25c/A2-05-H
bench/2026-09-25c/A2-06-P0063
bench/2026-09-25c/A2-06-R
bench/2026-09-25c/A2-06-H
bench/2026-09-25c/A2-07-P0060
bench/2026-09-25c/A2-07-R
bench/2026-09-25c/A2-07-H
bench/2026-09-25c/A2-08-P0263
bench/2026-09-25c/A2-08-R
bench/2026-09-25c/A2-08-H
bench/2026-09-25c/A2-09-P0060
bench/2026-09-25c/A2-09-R
bench/2026-09-25c/A2-09-H
bench/2026-09-25c/A2-10-P0276
bench/2026-09-25c/A2-10-R
bench/2026-09-25c/A2-10-H
bench/2026-09-25c/A2-11-P0060
bench/2026-09-25c/A2-11-R
bench/2026-09-25c/A2-11-H
bench/2026-09-25c/A2-12-P0277
bench/2026-09-25c/A2-12-R
bench/2026-09-25c/A2-12-H
bench/2026-09-25c/A2-13-P1514
bench/2026-09-25c/A2-13-R
bench/2026-09-25c/A2-13-H
bench/2026-09-25c/A2-14-P1511
bench/2026-09-25c/A2-14-R
bench/2026-09-25c/A2-14-H
bench/2026-09-25c/A2-15-P1514
bench/2026-09-25c/A2-15-R
bench/2026-09-25c/A2-15-H
bench/2026-09-25c/A2-16-P1512
bench/2026-09-25c/A2-16-R
bench/2026-09-25c/A2-16-H
bench/2026-09-25c/A2-17-P1514
bench/2026-09-25c/A2-17-R
bench/2026-09-25c/A2-17-H
bench/2026-09-25c/A2-18-P1513
bench/2026-09-25c/A2-18-R
bench/2026-09-25c/A2-18-H
bench/2026-09-25c/A2-19-P1514
bench/2026-09-25c/A2-19-R
bench/2026-09-25c/A2-19-H
bench/2026-09-25c/B-00-R
bench/2026-09-25c/B-00-H
bench/2026-09-25c/B-01-X
bench/2026-09-25c/B-01-T0060a
bench/2026-09-25c/B-01-T0060b
bench/2026-09-25c/B-01-R
bench/2026-09-25c/B-01-H
bench/2026-09-25c/B-02-X
bench/2026-09-25c/B-02-T0061a
bench/2026-09-25c/B-02-T0061b
bench/2026-09-25c/B-02-R
bench/2026-09-25c/B-02-H
bench/2026-09-25c/B-03-X
bench/2026-09-25c/B-03-T0060a
bench/2026-09-25c/B-03-T0060b
bench/2026-09-25c/B-03-R
bench/2026-09-25c/B-03-H
bench/2026-09-25c/B-04-X
bench/2026-09-25c/B-04-T0062a
bench/2026-09-25c/B-04-T0062b
bench/2026-09-25c/B-04-R
bench/2026-09-25c/B-04-H
bench/2026-09-25c/B-05-X
bench/2026-09-25c/B-05-T0060a
bench/2026-09-25c/B-05-T0060b
bench/2026-09-25c/B-05-R
bench/2026-09-25c/B-05-H
bench/2026-09-25c/B-06-X
bench/2026-09-25c/B-06-T0063a
bench/2026-09-25c/B-06-T0063b
bench/2026-09-25c/B-06-R
bench/2026-09-25c/B-06-H
bench/2026-09-25c/B-07-X
bench/2026-09-25c/B-07-T0060a
bench/2026-09-25c/B-07-T0060b
bench/2026-09-25c/B-07-R
bench/2026-09-25c/B-07-H
bench/2026-09-25c/B-08-X
bench/2026-09-25c/B-08-T0263a
bench/2026-09-25c/B-08-T0263b
bench/2026-09-25c/B-08-R
bench/2026-09-25c/B-08-H
bench/2026-09-25c/B-09-X
bench/2026-09-25c/B-09-T0060a
bench/2026-09-25c/B-09-T0060b
bench/2026-09-25c/B-09-R
bench/2026-09-25c/B-09-H
bench/2026-09-25c/B-10-X
bench/2026-09-25c/B-10-T0276a
bench/2026-09-25c/B-10-T0276b
bench/2026-09-25c/B-10-R
bench/2026-09-25c/B-10-H
bench/2026-09-25c/B-11-X
bench/2026-09-25c/B-11-T0060a
bench/2026-09-25c/B-11-T0060b
bench/2026-09-25c/B-11-R
bench/2026-09-25c/B-11-H
bench/2026-09-25c/B-12-X
bench/2026-09-25c/B-12-T0277a
bench/2026-09-25c/B-12-T0277b
bench/2026-09-25c/B-12-R
bench/2026-09-25c/B-12-H
bench/2026-09-25c/B-13-X
bench/2026-09-25c/B-13-T1514a
bench/2026-09-25c/B-13-T1514b
bench/2026-09-25c/B-13-R
bench/2026-09-25c/B-13-H
bench/2026-09-25c/B-14-X
bench/2026-09-25c/B-14-T1511a
bench/2026-09-25c/B-14-T1511b
bench/2026-09-25c/B-14-R
bench/2026-09-25c/B-14-H
bench/2026-09-25c/B-15-X
bench/2026-09-25c/B-15-T1514a
bench/2026-09-25c/B-15-T1514b
bench/2026-09-25c/B-15-R
bench/2026-09-25c/B-15-H
bench/2026-09-25c/B-16-X
bench/2026-09-25c/B-16-T1512a
bench/2026-09-25c/B-16-T1512b
bench/2026-09-25c/B-16-R
bench/2026-09-25c/B-16-H
bench/2026-09-25c/B-17-X
bench/2026-09-25c/B-17-T1514a
bench/2026-09-25c/B-17-T1514b
bench/2026-09-25c/B-17-R
bench/2026-09-25c/B-17-H
bench/2026-09-25c/B-18-X
bench/2026-09-25c/B-18-T1513a
bench/2026-09-25c/B-18-T1513b
bench/2026-09-25c/B-18-R
bench/2026-09-25c/B-18-H
bench/2026-09-25c/B-19-X
bench/2026-09-25c/B-19-T1514a
bench/2026-09-25c/B-19-T1514b
bench/2026-09-25c/B-19-R
bench/2026-09-25c/B-19-H
bench/2026-09-25c/C-00-R
bench/2026-09-25c/C-00-H
bench/2026-09-25c/C-01-X
bench/2026-09-25c/C-01-L0060a
bench/2026-09-25c/C-01-L0060b
bench/2026-09-25c/C-01-R
bench/2026-09-25c/C-01-H
bench/2026-09-25c/C-02-X
bench/2026-09-25c/C-02-L0061a
bench/2026-09-25c/C-02-L0061b
bench/2026-09-25c/C-02-R
bench/2026-09-25c/C-02-H
bench/2026-09-25c/C-03-X
bench/2026-09-25c/C-03-L0062a
bench/2026-09-25c/C-03-L0062b
bench/2026-09-25c/C-03-R
bench/2026-09-25c/C-03-H
bench/2026-09-25c/C-04-X
bench/2026-09-25c/C-04-L0063a
bench/2026-09-25c/C-04-L0063b
bench/2026-09-25c/C-04-R
bench/2026-09-25c/C-04-H
bench/2026-09-25c/C-05-X
bench/2026-09-25c/C-05-L0263a
bench/2026-09-25c/C-05-L0263b
bench/2026-09-25c/C-05-R
bench/2026-09-25c/C-05-H
bench/2026-09-25c/C-06-X
bench/2026-09-25c/C-06-L0276a
bench/2026-09-25c/C-06-L0276b
bench/2026-09-25c/C-06-R
bench/2026-09-25c/C-06-H
bench/2026-09-25c/C-07-X
bench/2026-09-25c/C-07-L0277a
bench/2026-09-25c/C-07-L0277b
bench/2026-09-25c/C-07-R
bench/2026-09-25c/C-07-H
bench/2026-09-25c/C-08-X
bench/2026-09-25c/C-08-L1511a
bench/2026-09-25c/C-08-L1511b
bench/2026-09-25c/C-08-R
bench/2026-09-25c/C-08-H
bench/2026-09-25c/C-09-X
bench/2026-09-25c/C-09-L1512a
bench/2026-09-25c/C-09-L1512b
bench/2026-09-25c/C-09-R
bench/2026-09-25c/C-09-H
bench/2026-09-25c/C-10-X
bench/2026-09-25c/C-10-L1513a
bench/2026-09-25c/C-10-L1513b
bench/2026-09-25c/C-10-R
bench/2026-09-25c/C-10-H
bench/2026-09-25c/C-11-X
bench/2026-09-25c/C-11-L1514a
bench/2026-09-25c/C-11-L1514b
bench/2026-09-25c/C-11-R
bench/2026-09-25c/C-11-H
bench/2026-09-25c/D-00-M1
bench/2026-09-25c/D-00-R
bench/2026-09-25c/D-00-H
bench/2026-09-25c/D-01-X
bench/2026-09-25c/D-01-P0060
bench/2026-09-25c/D-01-R
bench/2026-09-25c/D-01-H
bench/2026-09-25c/D-02-X
bench/2026-09-25c/D-02-P0061
bench/2026-09-25c/D-02-R
bench/2026-09-25c/D-02-H
bench/2026-09-25c/D-03-X
bench/2026-09-25c/D-03-P0060
bench/2026-09-25c/D-03-R
bench/2026-09-25c/D-03-H
bench/2026-09-25c/D-04-X
bench/2026-09-25c/D-04-P1511
bench/2026-09-25c/D-04-R
bench/2026-09-25c/D-04-H
bench/2026-09-25c/D-05-X
bench/2026-09-25c/D-05-P1514
bench/2026-09-25c/D-05-R
bench/2026-09-25c/D-05-H
bench/2026-09-25c/D-06-M0
bench/2026-09-25c/W-TCPX
bench/2026-09-25c/W-WALL
bench/2026-09-25c/R1-M1
bench/2026-09-25c/R1-MB1
bench/2026-09-25c/R1-NW1
bench/2026-09-25c/R1Q-ab2
bench/2026-09-25c/R1Q-2a
bench/2026-09-25c/R1Q-boot
```

```cardnum
cells-fence	321	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^bench/2026-09-25c/
declared-date	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md [*][*]declared date 2026-09-25[*][*]
presses-caught	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/R1-CATCH -{2}esc 180 -{2}esc-period
cap-cells	181	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out
host-cells	137	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST&? bench/2026-09-25c/
send-over-127	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md -{2}send '[^']*AUTOBURN
no-esc-after	0	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP .*-{2}esc-after
board-brackets	77	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/\S+-R -{2}send 'sleep\ 2\ ;\ cat\ /proc/rtl819x\-nic\ /proc/net/snmp\ /proc/net/arp\ /proc/rtl865x/asicCounter\ /proc/rtl819x\-nic' -{2}until 'rx_ph4\ \[0\-9A\-F\]\{8\}\(\?:\\r\\n\)\+\#\ ' -{2}seconds 15$
board-brackets-A	39	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/A[12]-[0-9]{2}-R 
board-brackets-B	20	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/B-[0-9]{2}-R 
board-brackets-C	12	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/C-[0-9]{2}-R 
board-brackets-D	6	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/D-[0-9]{2}-R 
host-brackets	77	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/\S+-H :: HN ; PW (none|bench/2026-09-25c/\S+-H[.]log)$
host-brackets-first	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/\S+-H :: HN ; PW none$
loader-gates	179	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
rearm-cells	35	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/[BCD]-[0-9]{2}-X -{2}send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' -{2}idle 3 -{2}seconds 8$
tx-cells-B	38	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/B-[0-9]{2}-T[0-9]{4}[ab] -{2}send 'echo tx 0x3f 0x8800 0 [0-9]+ > /proc/rtl819x-nic ; sleep 1 ; echo tx 0x3f 0x8800 0 [0-9]+ > /proc/rtl819x-nic' -{2}idle 3 -{2}seconds 8$
lb-on-cells	11	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/C-[0-9]{2}-L[0-9]{4}a -{2}send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 [0-9]+ > /proc/rtl819x-nic' -{2}idle 3 -{2}seconds 8$
lb-off-cells	11	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/C-[0-9]{2}-L[0-9]{4}b -{2}send 'echo tx 0x3f 0x8800 0 [0-9]+ > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic' -{2}idle 3 -{2}seconds 8$
txmode-1	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/D-00-M1 -{2}send 'echo txmode 1 > /proc/rtl819x-nic'
txmode-0	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/D-06-M0 -{2}send 'echo txmode 0 > /proc/rtl819x-nic'
nw-cells	2	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/R1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}seconds 15$
pe-cells	24	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/[AD]1?-[0-9]{2}-P[0-9]{4} :: PE [0-9]+$
pi-cells	19	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/A2-[0-9]{2}-P[0-9]{4} :: PI [0-9]+$
pe-macro	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^`PE <s>` = `ping -I enxfc19286184c9 -c 60 -i 0[.]05 -W 1 -s <s> 10[.]1[.]1[.]3`
pi-macro	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^`PI <s>` = `ping -I enxfc19286184c9 -c 20 -i 0[.]25 -W 1 -s <s> 10[.]1[.]1[.]3`
td-macro	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^`TD <f>` = `timeout 3600 sudo -n tcpdump -n -U -Q in -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s111/r6b/pcap/<f>`
tcpdump-cells	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST& bench/2026-09-25c/W-TCPD :: TD W[.]pcap$
tcpdump-stops	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/W-TCPX :: sudo -n pkill -INT -x tcpdump && sleep 1$
tcpdump-census	2	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/(R0-TCPC|A-LIVE) :: pgrep -xc tcpdump ; true$
sum-on-stdin	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^HOST bench/2026-09-25c/R0-SUM :: sha256sum < /home/
mb-awk	1	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^`MB <cap>` = `.* [|] awk 1 [|] sha256sum 
map-until-prompt	2	count bench/2026-09-25c/PREDICTIONS-B48-block46.md ^CAP -{2}out bench/2026-09-25c/R1-M[01] .* -{2}until 'map_lines \[0-9\][+]\\r\\n# '
pcapwin-sha256	e64118dee79d5487b8b7aa11272f007924680bd32b48fbdb3f6afd5a7d88e19f	sha256 /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py
pcapwin-version	1	count /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py ^VERSION = "1[.]1"$
pcapwin-selftest-cases	17	count /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin.py ^ +check[(]"S[0-9]+",
pcapwin-selftest-out	1	count /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin-selftest.out ^pcapwin self-test: 17 of 17 passed$
pcapwin-mutations	1	count /home/key/fwre-work/rebuild/s111/r6b/card/pcapwin-mutate.out ^mutations: 13 planted, 0 not as expected$
veth-tag-kept	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^vlan_vid 0:1 5:1$
veth-otherhost	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out 'otherhost', 1[)]
veth-otherhost-at-zero	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^otherhost-columns-at-zero 0$
veth-otherhost-after	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^otherhost-columns-after 1$
veth-icmp-sent	4	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^sent .*icmp
veth-icmp-delta	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^host Icmp.InEchoReps delta: 3$
veth-pkill-rc	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^pkill rc=0$
veth-tcpdump-rc	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^tcpdump-chain rc=0$
veth-live	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^capture_live yes$
veth-closed	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^capture_live no$
veth-procs-live	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^tcpdump_procs 1$
veth-pgrep-live	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^pgrep-live 1$
veth-pgrep-after	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^pgrep-after 0$
veth-iproute2	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^ip utility, iproute2-6[.]1[.]0,
veth-iputils	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^ping from iputils 20240117$
veth-kernel-drops	1	count /home/key/fwre-work/rebuild/s111/r6b/card/ctl-veth/ctl-veth.out ^0 packets dropped by kernel$
B45-isz-macro	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`ISZ <ip>` = `for s in .*; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
B45-isz-60	1	count bench/2026-09-25b/D1-ISZ.log ^20 packets transmitted, 20 received, 0% packet loss, time 1037ms$
B45-isz-61	1	count bench/2026-09-25b/D1-ISZ.log ^181 packets transmitted, 19 received,
B45-isz-62	1	count bench/2026-09-25b/D1-ISZ.log ^74 packets transmitted, 20 received,
B45-isz-63	1	count bench/2026-09-25b/D1-ISZ.log ^180 packets transmitted, 9 received,
B45-isz-263	1	count bench/2026-09-25b/D1-ISZ.log ^179 packets transmitted, 1 received, 99.4413% packet loss, time 10453ms$
B45-isz-276	1	count bench/2026-09-25b/D1-ISZ.log ^25 packets transmitted, 20 received,
B45-isz-277	1	count bench/2026-09-25b/D1-ISZ.log ^134 packets transmitted, 20 received,
B45-isz-1511	1	count bench/2026-09-25b/D1-ISZ.log ^179 packets transmitted, 0 received,
B45-isz-1512	1	count bench/2026-09-25b/D1-ISZ.log ^179 packets transmitted, 1 received, 99.4413% packet loss, time 10067ms$
B45-isz-1513	1	count bench/2026-09-25b/D1-ISZ.log ^22 packets transmitted, 20 received,
B45-isz-1514	1	count bench/2026-09-25b/D1-ISZ.log ^20 packets transmitted, 20 received, 0% packet loss, time 979ms$
B45-isz-rtt-fault-max	1	count bench/2026-09-25b/D1-ISZ.log ^rtt min/avg/max/mdev = 1[.]037/1[.]648/2[.]330/
B45-isz-rtt-1513-max	1	count bench/2026-09-25b/D1-ISZ.log ^rtt min/avg/max/mdev = 1[.]375/18[.]293/164[.]978/
B45-wire-req-60	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24920, seq
B45-wire-rep-60	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24920, seq
B45-wire-first60-60	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24920, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-61	181	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24921, seq
B45-wire-rep-61	19	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24921, seq
B45-wire-first60-61	17	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24921, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-62	74	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24922, seq
B45-wire-rep-62	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24922, seq
B45-wire-first60-62	16	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24922, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-63	180	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24923, seq
B45-wire-rep-63	9	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24923, seq
B45-wire-first60-63	9	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24923, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-263	179	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24933, seq
B45-wire-rep-263	1	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24933, seq
B45-wire-first60-263	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24933, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-276	25	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24934, seq
B45-wire-rep-276	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24934, seq
B45-wire-first60-276	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24934, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-277	134	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24935, seq
B45-wire-rep-277	39	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24935, seq
B45-wire-first60-277	18	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24935, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-1511	179	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24939, seq
B45-wire-rep-1511	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24939, seq
B45-wire-first60-1511	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24939, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-1512	179	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24940, seq
B45-wire-rep-1512	1	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24940, seq
B45-wire-first60-1512	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24940, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-1513	22	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24941, seq
B45-wire-rep-1513	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24941, seq
B45-wire-first60-1513	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24941, seq ([1-9]|[1-5][0-9]|60),
B45-wire-req-1514	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo request, id 24942, seq
B45-wire-rep-1514	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24942, seq
B45-wire-first60-1514	20	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24942, seq ([1-9]|[1-5][0-9]|60),
B45-seqset-61	17	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24921, seq (1|5|7|13|15|20|22|27|29|35|37|42|44|50|52|57|59),
B45-seqset-62	16	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24922, seq (1|5|7|13|15|20|22|27|29|35|37|42|44|50|52|57|59),
B45-seqset-277	18	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24935, seq (1|3|8|10|15|17|22|24|29|31|36|38|43|45|50|52|57|59),
B45-seq-62-first5	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24922, seq [1-4],
B45-seq-63-first5	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24923, seq [1-5],
B45-seq-63-6-7	2	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24923, seq [67],
B45-seq-63-8-39	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24923, seq ([89]|[1-3][0-9]),
B45-seq-276-first5	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24934, seq [1-5],
B45-seq-1513-first2	0	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24941, seq [1-2],
B45-277-icmp-length	39	count bench/2026-09-25b/D1-TCPD.log ICMP echo reply, id 24935, seq [0-9]+, length 243$
B45-K0-all-64-zero	7	count bench/2026-09-25b/D1-K0.log ^ +< 64: 0 pkts, 64: 0 pkts, 65 -127: 0 pkts, 128 -255: 0 pkts$
B45-K1-cpu-crc	1	count bench/2026-09-25b/D1-K1.log ^ +CRCAlignErr 102, SymbolErr 0, FragErr 0, JabberErr 0$
B45-K1-cpu-64	2	count bench/2026-09-25b/D1-K1.log ^ +< 64: 0 pkts, 64: 2 pkts, 65 -127: 20 pkts, 128 -255: 0 pkts$
B45-K2-cpu-crc-jab	1	count bench/2026-09-25b/D1-K2.log ^ +CRCAlignErr 996, SymbolErr 0, FragErr 1, JabberErr 678$
B45-K2-cpu-drop	1	count bench/2026-09-25b/D1-K2.log ^ +Rcv 0 bytes, Drop 43 pkts,etherStatsDropEvents 20$
B45-K2-cpu-64	1	count bench/2026-09-25b/D1-K2.log ^ +< 64: 0 pkts, 64: 25 pkts, 65 -127: 69 pkts, 128 -255: 0 pkts$
B45-K1-cpu-hist	2	count bench/2026-09-25b/D1-K1.log ^ +256 - 511: 20 pkts, 512 - 1023: 20 pkts, 1024 - 1518: 40 pkts$
B45-K2-cpu-hist	1	count bench/2026-09-25b/D1-K2.log ^ +256 - 511: 107 pkts, 512 - 1023: 26 pkts, 1024 - 1518: 90 pkts$
B45-K1-p3-snd	1	count bench/2026-09-25b/D1-K1.log ^ +Snd 71128 bytes, Unicast 102 pkts, Multicast 0 pkts$
B45-K2-p3-snd	1	count bench/2026-09-25b/D1-K2.log ^ +Snd 154876 bytes, Unicast 273 pkts, Multicast 0 pkts$
B45-H1-rx-packets	1	count bench/2026-09-25b/D1-H1.log ^/sys/class/net/enxfc19286184c9/statistics/rx_packets:727929$
B45-H2-rx-packets	1	count bench/2026-09-25b/D1-H2.log ^/sys/class/net/enxfc19286184c9/statistics/rx_packets:728101$
B45-H7-tx-packets	1	count bench/2026-09-25b/D1-H7.log ^/sys/class/net/enxfc19286184c9/statistics/tx_packets:939762$
B45-H8-tx-packets	1	count bench/2026-09-25b/D1-H8.log ^/sys/class/net/enxfc19286184c9/statistics/tx_packets:939768$
B45-H1-icmp	1	count bench/2026-09-25b/D1-H1.log ^Icmp: 18553 1628 0 3516 0 0 0 0 0 15037 0 
B45-H2-icmp	1	count bench/2026-09-25b/D1-H2.log ^Icmp: 18703 1628 0 3516 0 0 0 0 0 15187 0 
B45-dossier-excess-E2	1	count /home/key/fwre-work/rebuild/s111/r6b-dossier/a45e.out ^E2 .* excess [+]76 B$
B45-dossier-excess-E1	1	count /home/key/fwre-work/rebuild/s111/r6b-dossier/a45e.out ^E1 .* excess [+]0 B$
B45-dossier-unreach	1	count /home/key/fwre-work/rebuild/s111/r6b-dossier/DOSSIER.md ^[*] 9 host-unreachables = 3 neighbour failures × `queue_len` 3
B45-dossier-drops-by-bucket	1	count /home/key/fwre-work/rebuild/s111/r6b-dossier/DOSSIER.md drops sit in 65–127 [(]1[)], 256–511 [(]27[)], [*][*]512–1023 [(]6[)][*][*], 1024–1518 [(]9[)]
B45-dossier-m5-sweep	1	count /home/key/fwre-work/rebuild/s111/r6b-dossier/DOSSIER.md ^ +verb with `0x08`, `0x1F`, `0x3F` and with `0x8860`
B45-N1-ntx	1	count bench/2026-09-25b/D1-N1.log ^n_tx 102\r?$
B45-N2-ntx	1	count bench/2026-09-25b/D1-N2.log ^n_tx 1037\r?$
B45-N1-fire	1	count bench/2026-09-25b/D1-N1.log ^n_recov_fire 0\r?$
B45-N2-fire	1	count bench/2026-09-25b/D1-N2.log ^n_recov_fire 5\r?$
B45-N1-stop	1	count bench/2026-09-25b/D1-N1.log ^n_tx_stop 0\r?$
B45-N2-stop	1	count bench/2026-09-25b/D1-N2.log ^n_tx_stop 5\r?$
B45-S1-ip	1	count bench/2026-09-25b/D1-S1.log ^Ip: 2 64 100 0 0 0 0 0 100 100 0 0 0 0 0 0 0 0 0\r?$
B45-S1-icmp	1	count bench/2026-09-25b/D1-S1.log ^Icmp: 100 0 0 0 0 0 0 100 0 0 0 0 0 100 0 0 0 0 0 0 0 100 0 0 0 0\r?$
B45-S2-ip	1	count bench/2026-09-25b/D1-S2.log ^Ip: 2 64 1293 0 0 0 0 0 1293 1302 86 0 0 0 0 0 0 0 0\r?$
B45-S2-icmp	1	count bench/2026-09-25b/D1-S2.log ^Icmp: 1293 0 0 0 0 0 0 1293 0 0 0 0 0 1302 0 9 0 0 0 0 0 1293 0 0 0 0\r?$
B45-map-digest	1	count bench/2026-09-25b/D1-MB0.log ^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46\s+-$
B45-map-groups	1	count bench/2026-09-25b/D1-MB0.log -- 31 same, 1 DIFFER, 0 scope, 0 extra, 0 missing$
B45-E1-1514	1	count bench/2026-09-25b/D1-ICMP.log ^20 packets transmitted, 20 received, 0% packet loss, time 965ms$
B45-E1-1472	1	count bench/2026-09-25b/D1-ICMP.log ^PING 10[.]1[.]1[.]3 .*: 1472[(]1500[)] bytes of data
B45-K3-cpu-crc	1	count bench/2026-09-25b/D1-K3.log ^ +CRCAlignErr 72824, SymbolErr 0, FragErr 1, JabberErr 678$
B45-K3-cpu-drop	1	count bench/2026-09-25b/D1-K3.log ^ +Rcv 0 bytes, Drop 43 pkts,etherStatsDropEvents 20$
B45-K3-cpu-64	1	count bench/2026-09-25b/D1-K3.log ^ +< 64: 0 pkts, 64: 71853 pkts, 65 -127: 69 pkts, 128 -255: 0 pkts$
B45-K4-cpu-crc	1	count bench/2026-09-25b/D1-K4.log ^ +CRCAlignErr 73962, SymbolErr 0, FragErr 2, JabberErr 679$
B45-K5-cpu-crc	1	count bench/2026-09-25b/D1-K5.log ^ +CRCAlignErr 74003, SymbolErr 0, FragErr 2, JabberErr 679$
B45-N4-ntx	1	count bench/2026-09-25b/D1-N4.log ^n_tx 74009\r?$
B45-N5-ntx	1	count bench/2026-09-25b/D1-N5.log ^n_tx 74049\r?$
B45-recipe-id	1	count bench/2026-09-25b/D1Q-boot.log RLXFW-ID0=A2C56BC8
rung1-lb-ph1	1	count bench/2026-09-19b/C21-nic7.log ^rx_ph1 00400000\r?$
rung1-lb-len	1	count bench/2026-09-19b/C21-nic7.log ^rx_len 60\r?$
rung1-tx-ph	1	count bench/2026-09-19b/C21-nic7.log ^txd0 [0-9A-F]{8} len 64\r?$
rung1-rx-ph3	1	count bench/2026-09-19b/C21-nic7.log ^rx_ph3 821F0000\r?$
rung1-driver-1.0	1	count bench/2026-09-19b/C21-nic7.log ^version rtl819x-nic 1[.]0\r?$
rung1-no-net-device	0	count bench/2026-09-19b/C17-nic5.log ^nd_
g1-driver-1.0	1	count bench/2026-09-19b/G2-state.log ^version rtl819x-nic 1[.]0\r?$
g1-rlx0-up	1	count bench/2026-09-19b/G2-state.log ^nd_up 1\r?$
g1-stack-idle	1	count bench/2026-09-19b/G2-state.log ^n_xmit 0\r?$
g1-napi-idle	1	count bench/2026-09-19b/G2-state.log ^n_napi_poll 0\r?$
lb-on-typed-before	1	count bench/2026-09-19b/C16-lbon.meta.json echo lb on > /proc/rtl819x-nic
txmode1-typed-before	1	count bench/2026-09-21e/Y6-MODE.meta.json echo txmode 1 > /proc/rtl819x-nic
spi-nw-typed-before	1	count bench/2026-09-16/X7-NW0.log ^n_writes 0\r?$
spi-last-attempt-bytes	1	size bench/2026-09-21/R7-SPI.log
spi-last-attempt-time	1	count bench/2026-09-21/R7-SPI.meta.json "duration_s": 25[.]06
spi-1.1-read	1	count bench/2026-09-16/X7-NW0.log ^version rtl819x-spi 1[.]1\r?$
until-drain-desk	1	count /home/key/fwre-work/rebuild/s111/mbuntil/REPORT.md it stops 0–50 ms after the match
spi-driver-1.2	1	count config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c ^#define RTL819X_SPI_VERSION\t"rtl819x-spi 1[.]2"$
spi-n-writes-line	1	count config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c "n_writes %lu\\n", rtl819x_spi_n_writes
spi-recipe-line	1	count config/rlxfw-src/linux-2.6.30/drivers/mtd/devices/rtl819x-spi.c "recipe_id %08X\\n"
fls30-nine-boots	1	count SPEC.md ^[|] `FLS-30` 🆕 [|] [*][*]九次原廠開機前後
p2q-nfjrom-bytes	1155072	size /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-nfjrom-sha256	4972edbadd2655a8	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/rtkload/nfjrom
p2q-vmlinux-sha256	c5e2cfdba7730d47	sha256-16 /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/kroot/vmlinux
p2q-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^verdict\tgreen$
p2q-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-manifest-irfs	1	count /home/key/fwre-work/rebuild/r3-4/out/p2q.manifest ^initramfs_manifest_sha256\t51ea1604c7c163f379a70dd7b042dae3d2429db380dda1375675f1a0a5d24a59$
p2q-record-vmlinux	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^vmlinux_sha256\tc5e2cfdba7730d479c5a23664d41fa734cc7989ee3db784f106559e6ed654863$
p2q-record-nfjrom	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t4972edbadd2655a815e80606a83b8e5e5987334dfd1c990fcc806291eaf182ae$
p2q-record-clean	1	count /home/key/fwre-work/rebuild/p2-2/rtk/p2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
p2q-recipe-override	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md --recipe-override a2c56bc8
driver-version	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]4"$
driver-tx-desc-4	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define NIC_TX_DESC\s+4$
driver-retry-128	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define NIC_TX_RETRY_MAX\s+128$
driver-recov-ms-1000	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^static unsigned int\s+nic_recov_ms = 1000;$
driver-flags-8800	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define NIC_PH_FLAGS_TX_DEFAULT\s+0x8800u$
driver-xmit-3f	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c NIC_PH_MK3[(]NIC_PH_FLAGS_TX_DEFAULT, 0x3F[)]
driver-xmit-phlen	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\s+nic_dw_set[(]nic_tx_ph, i, 1, NIC_PH_MK1[(]len [+] 4, 0, 0[)][)];$
driver-harvest-len	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\s+nic_ndev->stats.rx_bytes [+]= len;$
driver-harvest-ph1	2	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\s+nic_last_rx_ph1 = w1;$
run-looprun-round	1	count /home/key/fwre-work/rebuild/s110/run-I-D1a.log END D1Q rc=0 21[.]3 s
run-M0-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1c.log END D1-M0 rc=0 13[.]9 s
run-N1-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1b.log END D1-N1 rc=0 3[.]9 s
run-H7-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1b.log 03:30:07[]] END D1-H7 rc=0
run-H8-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1c.log 03:33:34[]] END D1-H8 rc=0
run-EPING-4	1	count bench/2026-09-25b/D1-EPING.log ^4 packets transmitted, 4 received
block44-I0-start	1	count /home/key/fwre-work/rebuild/s110/run-I0.log 00:02:59[]] BG +Z0-HC
block44-I0-end	1	count /home/key/fwre-work/rebuild/s110/run-I0.log 02:49:20[]] ALL ITEMS DONE
run-K1-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1b.log END D1-K1 rc=0 2[.]4 s
run-H1-time	1	count /home/key/fwre-work/rebuild/s110/run-I-D1b.log END D1-H1 rc=0 0[.]0 s
run-gap-a	1	count /home/key/fwre-work/rebuild/s110/run-I-D1a.log 03:22:32[]] ALL ITEMS DONE
run-gap-b	1	count /home/key/fwre-work/rebuild/s110/run-I-D1b.log 03:22:48[]] RUN HOST& D1-TCPD
run-block45-first	1	count /home/key/fwre-work/rebuild/s110/run-I-D1a.log 03:18:48[]] RUN CAP +D1-A 
run-block45-last	1	count /home/key/fwre-work/rebuild/s110/run-I-D1c.log 03:34:38[]] ALL ITEMS DONE
size-N1	2549	size bench/2026-09-25b/D1-N1.log
size-S1	1116	size bench/2026-09-25b/D1-S1.log
size-K1	4126	size bench/2026-09-25b/D1-K1.log
rearm-time	1	count bench/2026-09-25b/D1-X1.meta.json "duration_s": 3[.]16
runblock-script	21287d2e33c7b8e8	sha256-16 /home/key/fwre-work/rebuild/s109/card/runblock.py
console-capture-1.5	1	count tools/console-capture.py ^TOOL_VERSION = "1[.]5"$
looprun-1.3	1	count tools/looprun.py ^VERSION = "1[.]3"$
cardrun-1.0	1	count tools/cardrun.py ^TOOL_VERSION = "1[.]0"$
cardrun-start-timeout	1	count tools/cardrun.py ^START_TIMEOUT_S = 20[.]0 
cardrun-kill-grace	1	count tools/cardrun.py ^KILL_GRACE_S = 8[.]0$
block44-background-I0	1	count bench/2026-09-25/PREDICTIONS-B46-block44.md ^[*][*]`I0`[*][*] — in the background for the whole seating
tx-typed-C18-tx	1	count bench/2026-09-19b/C18-tx.log echo tx 0x3F >
tx-typed-C27-tx1	1	count bench/2026-09-19b/C27-tx1.log echo tx 0x3F >
tx-typed-C28-tx2	1	count bench/2026-09-19b/C28-tx2.log echo tx 0x3F >
tx-typed-G1-rawtx	1	count bench/2026-09-19b/G1-rawtx.log echo tx 0x3F >
```
