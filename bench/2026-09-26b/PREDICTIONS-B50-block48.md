# PREDICTIONS — block 48, seating 42 (`R6b-3`, second card: `D2`'s second boot, `D1`'s stack arm one length a bracket at the fix and at 1.4, `D3`'s first boot)

**declared date 2026-09-26** — **one power press**; its catch window opens no later than 23:00
that day, or the card is re-dated before power (§ 6).
Block 47 (`bench/2026-09-26/PREDICTIONS-B49-block47.md`, frozen in `a9e2501`, captures in
`ad9c563`) is the press before this one, a block of the same seating on the same image,
recorded in `563281d` (`notes/nic-driver.md` § 25, `NET-128`–`NET-131`, `FW-145`). This card
was drafted after that block's readings and follows them (the coordinator's adjudication of
2026-09-26, `ADJ-b47.md` in `$FWRE_WORK/rebuild/s112/r6b3/read/`, items R1–R12, cited below as
ADJ R*n*); it is a second block of seating 42 by the owner's answer of 2026-09-26.

Marks: **量** measured on the device · **讀** read out of code or a dump · **推** inferred,
pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this block is, and which conjuncts of the gate it carries.** One press of `r6b2q`
(driver 1.5), the image block 47 booted. Priority, decided before any sizing: `D2`'s second
boot, then `D1`'s stack arm, then `D3`'s first boot; all three fit one press on block 47's
timings (§ 2), and § 6 decides what is cut, in that order reversed, if the press runs long.

| conjunct | carried here | not here |
|---|---|---|
| `D2`, E2's eleven at block 45's spacing, 220 of 220 on the fix, 1.4 reproducing the loss on the same boot | boot 2 of 2 (`I-E`: fix, 1.4, fix — card 1's cells and spacing) | — |
| `D2`, a `tx` sweep over every length 60–1,514 with `JabberErr` Δ 0 | the fix on the wire again (`W-1a`…`W-1d`) behind the fix's own loopback map and its positive control (`LB-P`), and 1.4's bounded wire sweep at E2's eleven (`W-2`, 11 lengths), the owner's bound shown refusing first (`W-2-EP`) | — |
| `D1`, the stack arm at each of E2's eleven lengths in its own bracket (ADJ R3: block 47 ran the `tx`-verb and loopback arms per length, the stack arm as one E2 bracket) | `I-S`: each length on a re-armed ring, 20 requests, one bracket, at the fix and at 1.4, identical cells | — |
| the o-identity miss of block 47's E-L1 bracket (o = c − j − f − d + 4, cause 未定; `NET-131` 殘留) | the 22 per-length brackets and the three E brackets, each compared with the capture by record order, and a decision rule written now (P9) | the experiment that decides it if this card's brackets cannot (P9 (iii)) |
| `D3`, `NET-111`'s twelve `rlx0` trials on the fixed image, on two boots | boot 1: the twelve at `txlen vendor`, then 1.4's control (one UDP trial each way) on the same boot (`I-D3`) | boot 2 (card 3) |
| `NET-117` 殘留, the board's `Udp:` line around each UDP receive trial | every trial's server-start and server-stop cells read `/proc/net/snmp`, and every trial is bracketed (P18) | why the datagrams die, beyond the counter that says where |
| `NET-124` 殘留 and `NET-54` 殘留 ② | the liveness, port-3 and path gates before and inside every host arm; § 6's ordered read set on a failure, before any recovery; the host's kernel log followed from before the press | — |
| `R6b-2`'s read-back conjunct | not repeated: met on block 47 (ADJ R7: `RB-01-C` and `RB-02-C` EQUAL, 量). `I-B` reads the boot page only to show 1.5 untouched since boot | — |
| `NET-61` 殘留's burst half and `NET-103` 殘留 ④ | not repeated: closed for E2's eleven by block 47 (ADJ R8); this card extends neither | the other 1,444 lengths |
| `D3-MISS` ① and ②, `P2`'s quiet-image cold boot, `D3`'s second boot | — | card 3, not in seating 42 (ADJ R11) |

**② Block 47's lessons, each applied here.**
* *Card 1's P0 voided "every verdict below that reads it"*, which reached P4's `j + f + d ≥ 1`
  conjunct (625 read) over a 4-frame miss (ADJ R1, `NET-131`). P0 below says plainly what a
  failed bracket voids: the stage chain of that bracket, and a single counter's threshold
  verdict only if the miss could have carried it across the threshold (§ 3.1).
* *Two of card 1's three P0 misses were a board ARP request crossing the ~3 s between the board
  read's switch counters and the host read after it* (ADJ R1; records 232 and 400 of that
  capture). The experiment is changed, not the tolerance: every board read now has a host read
  just before it (`-P`, the adapter's counters and ICMP line only) and one just after (`-H`),
  so the host's counts bound port 3's output from both sides, `inner ≤ o ≤ outer` (P0 (b),
  `brdelta` 1.2's `hbound` line). No neighbour entry is pinned (ADJ R12: half of the board's
  ARP frames were replies to the host's own requests, and pinning's blast radius was not
  enumerated).
* *pcapwin 1.2's `--prev` read dmesgwin's `window_end`* (the last one in the previous host
  log), so 63 of 67 of card 1's windows fell back to cumulative counts with exit 3, masked by
  dmesgwin's exit code (`FW-145`; 量 `bench/2026-09-26/E-L1-H1.log`'s `prev_beyond_file`).
  pcapwin 1.3 reads only its own block, ends every block with `pcapwin end rc N`, and — ADJ R12
  — windows by **record order**: once a capture stops, `pcapwin order` maps every host read's
  `rx_packets` onto a record index through an anchor read on both sides of the stop, so each
  window is exactly the frames the host counted, whatever tcpdump's delivery latency (its
  real-data control reproduces the adjudicated windows of card 1's capture, records 6–226,
  233–400 and 406–626, § 3.0).
* *A recovery fired after a held page and its marks broke an `until`* (`CORRECTIONS-block47.md`
  § 1, `X-RT1`). No cell here holds the ring: no `txstall`, no `tx` verb (cardnum rows count
  zero).
* *The host's `BUG` trace is not `NET-124`'s silent-state marker*: 282 of them during block
  47's press while the path worked, 0 before power (ADJ R9, 量). It stays a counted reading; the
  silent state is what the liveness, port-3 and path gates detect.
* *E2 at 1.4 lost the first 29 requests at 276 and the first 62 at 1,513* (block 47's capture,
  seq 30–49 and 63–82), lengths M1-cover8 calls clean: the previous length's state, 推. `I-S`
  starts every length on a ring re-armed by its own switch cell, so a length's result is its
  own (P6).

**③ What reads silicon for the first time tonight.** `iperf3` on driver 1.5, at `txlen vendor`
and at 1.4's lengths; the per-length stack arm with a fixed count of 20 requests (`ping -c 20`
with no deadline, so the stimulus does not depend on the loss); the host reads before every
board read; `pcapwin` 1.3's record-order windows and `brdelta` 1.2's `ident`, `buckets`,
`hbound` and `snmp` lines (self-tests on block 47's own captures, mutation runs, § 5); `LB-P`,
two single-length loopback units at probe 60, as the fix's loopback gate's positive control.
None of the per-frame predictions (P7) has been tested: they apply M1-cover8 (推, fitted after
blocks 45–46, left standing by block 47) to the stack's reply sequence.

**④ The host is restarted before the seating** (card 1's engineering decision, kept): a fresh
WSL, a fresh attach of both USB devices, and a kernel-log follower started before the attach
into a new file (`host/dmesg-w2.log`, card 1's `dmesg-w.log` is kept); `R0-DW0` refuses power
unless that log reads `bug_preempt 0`, `usbnet_xmit 0` and `call_trace 0` with the board off.
What the restart cannot do: say why block 46 went silent.

**⑤ Containment, which does not depend on any outcome.**
* **Frames at 1.4's settings on the wire are bounded by construction.** `E-L1` is block 45's E2
  at 1.4, the regression itself (1,327 requests on block 47). `I-S`'s eleven 1.4 lengths are 20
  requests each, 220 in all. `W-2` is 11 single-length wire sweeps, at most one mis-sent frame
  each (7 predicted), and the driver refuses a wire sweep over more than one length at any
  `txlen` but `vendor` (`nic15_sweep_gate`, -EPERM), shown refusing at `W-2-EP` before the
  first of them. `LB-P` is two loopback units at 1.4 (a leak is read by `LB-P-D`: at most four
  frames, two of them mis-sent). The D3 control is two `iperf3` trials at 1.4 (`LUR1`, `LUS1`),
  the stimulus `NET-111` already ran at 1.4 on two seatings.
* **The fix's full wire sweep is bounded whatever the maps read.** `W-00` reads the fix's own
  loopback map before any multi-length wire sweep (`rc 0`, 1,455 scored, 0 bad, 0 VOID, 0 SKEW,
  `delta0 0`, the key `txlen vendor … mode loop probe 60`, 1,455 records), and that map says
  something only because `LB-P` shows the loopback seeing 1.4's fault on this boot first (P10):
  if `LB-P` does not, no multi-length wire sweep runs (§ 6). After that, each quarter runs only
  if the quarter before it read `fault jfd 0`: at most one quarter's frames (364 units) can be
  mis-sent.
* **What the host keeps of a frame.** Two captures, each `tcpdump -Q in -s 64` into
  `$FWRE_WORK/rebuild/s112/r6b3/pcap2/`, never the repository: during `I-E` and `I-S` every
  frame from the board's address (`WE.pcap`); during `I-W` only the board's frames whose
  EtherType is `0x88B5`, untagged or behind one `0x8100` tag with `0x88B5` inside (`WS.pcap`) —
  card 1's two filters, the owner's. From `WS.pcap`'s first host read (`W-00-P`) to its stop
  `rlx0` is down — from `W-00-DN` on, and up again only in `I-U`, after the stop — so every
  frame the host adapter counts there is a `0x88B5` frame the filter keeps, which the
  record-order anchor needs (P0 (c)). No capture runs during `I-D3`: `NET-111`'s trials ran
  uncaptured on seatings 39 and 40, and a capture at 20 Mbit/s would load the host that runs
  the MIPS client under qemu (§ 7). The files are read only by `pcapwin.py` 1.3, which prints
  counts, lengths and sequence numbers, never an address.
* **Verdicts come from counters**: the CPU port's `CRCAlignErr`, `JabberErr`, `FragErr`,
  `Drop`, port 3's output and input, the host adapter's counters, the board's `/proc/net/snmp`,
  read in brackets around each experiment; ping's and `iperf3`'s own lines; the captures are
  readings beside them.

**⑥ Resets.** No cell carries `--esc-after`. Every `--until` on the card but the two maps' also
ends on the loader's banner (a map ends on its `map_lines` line and the prompt, and a reset
inside one runs to its `--seconds` cap), and every board cell after the round carries the gate
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (200 gates): a reset ends
the capture it happens in, the gate fails, and § 6 has the owner power off before any other
cell. 量 block 47's boot printed `RLXFW-W4=00240000`; no cell touches the watchdog (a cardnum
row counts zero).

**⑦ The clock.** This card claims no duration. No verdict rests on a host timestamp, and no
capture is mapped onto RAW with one offset: every verdict is a counter difference or a count,
and every capture is windowed by record order (§ 3.0).

**⑧ Runner limits worked around** (card 1's, unchanged). The runner's background cells know
three programs, so the kernel-log follower is an off-card process started before `I-0` (§ 6);
`R0-DMSG` requires exactly one `dmesg`, and every kernel-log window prints `follower`. Each
capture runs in an invocation of its own (`I-WE0`, `I-WS0`), because a stop interrupts every
background cell of the invocation that stopped. A cell whose non-zero exit is a reading is
declared `NAME?`. Macros take one parameter, so multi-argument calls spell their arguments in
the cell.

**⑨ `C-19`** (the console adapter leaving the USB bus) is named: the kernel-log windows count
`USB disconnect`, `cp210x` and `ttyUSB` lines, and the record states every console drop and
every idle longer than a minute, with the idle before it.

**⑩ The sweep's records, and `swclear`** (card 1's § 0 ⑩, 讀 `nic15_keycheck`): a sweep under a
new key is refused (-EEXIST) while any record exists, so the first sweep under every new key
starts with `swclear` in the same send (4 sends); `W-1`'s quarters and `W-2`'s lengths
accumulate and do not. `sweep F T P` loops back; only a trailing ` wire` puts frames on the
wire. `verbcheck50.py` replays the whole card through the committed header's parser, refusal
table, wire bound and key check before power, and refuses any refusal that is not a gated
guard.

---

## § 1 The image

`r6b2q`, driver `rtl819x-nic 1.5`, quiet variant, built twice byte-identical by `R6b-2` — the image block 47 booted (`RLXFW-ID0=06C39CA3` there, 量), so every value below is the one card B49 was filled with: recipe `06c39ca3`, `nfjrom` `/home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom` (`7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9`), vmlinux `900faed7c8bfdf2e984b7abee0bb03cfb6929fc5fe33fa5e6ce696c639037337`, initramfs from `_irfs-p2` (`/bin/iperf3`, 讀 the manifest and its spec). The chain is checked by this card's `cardnum` rows: the manifest `verdict green`, `variant quiet`, that vmlinux and that initramfs source; the `rtkimage` record naming that `nfjrom` digest with a CLEAN tripwire verdict; the `nfjrom` on disk with that digest; card B49's committed `QIMG` naming the same file and digest; the build cell's `rtl819x-nic-tx.h` equal to the committed one. The switch driver the image runs is the build cell's `rtl819x-switch.c` 1.1 — HEAD holds 1.2 (`R6b-6`, `920875f`), which reads `PSRP` differently — so the card's switch rows read the build cell's copy. `looprun` pins the `nfjrom` by digest before the port opens and compares the booted image's `RLXFW-ID0` with the build's. No cell names an address from `System.map`.

---

## § 2 The press, in order

| invocation | what runs | est. min (a guess) |
|---|---|---:|
| `I-0` | before power | 0.2 |
| `I-1` | the catch, the round, the opening map | 4.0 |
| `I-B` | the opening state | 0.1 |
| `I-WE0` | the stack arms' capture starts | 0.0 |
| `I-E` | E2: the fix, 1.4, the fix | 2.5 |
| `I-S` | the stack, one length a bracket: the fix and 1.4 at each of the eleven | 7.6 |
| `I-WE9` | that capture stops | 0.0 |
| `I-WS0` | the sweeps' capture starts | 0.0 |
| `I-W` | the wire: the gate's control and map, the fix, then 1.4 bounded | 3.4 |
| `I-WS9` | that capture stops | 0.0 |
| `I-U` | `rlx0` up again at 1.4 | 0.2 |
| `I-D3` | twelve trials at the fix, two at 1.4 | 13.5 |
| `I-Z` | the closing map, `n_writes`, the kernel log | 0.3 |

About 35 minutes from the catch's window to power-off with 15 s between invocations, if every
trial at the fix completes; about 42 if every one runs to `timeout 70` (a guess from block 47's
transcripts — a bracket 5.3 s, a switch 3.3, port-3 3.9, liveness 0.8, E2 10.7 s at the fix and
73.7 at 1.4, a full loopback map 36.6, a wire quarter 9.9, a single-length sweep 0.9, the catch
200.2, the round 21.2, a map 13.9 — and, for the trials, from block 44's
(`$FWRE_WORK/rebuild/s110/run-I3.log` and `run-I4.log`: a trial 30.2–30.6 s when its exchange
completed, on `eth4`, and 70.0 s when `timeout` ended it, a server start 6.5–7.3 s, a stop
5.0–6.1 s)). `I-U` ends about 20 minutes after the catch; if `I-D3` starts at the latest minute
§ 6 allows (27) and every trial runs to `timeout 70`, the press is about 49 minutes. 86 board
brackets, 86 host pre-reads, 1 full sweep. `I-0` is before power and not in the figure.

The order protects the priorities: `I-E` first (`D2`'s second boot, the DoD's first conjunct),
then `I-S` (`D1`), both under the stack capture; then the wire, whose containment gate needs
`rlx0` down; then `I-D3` last, whose 1.4 control runs after the twelve at the fix so that a 1.4
trial's aftermath cannot void them. If the press runs long, `I-D3` is the invocation that is
not run (§ 6), and `D3`'s first boot moves to card 3.

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

A **bracket** is the board read `<name>-R…` (card 1's, unchanged: the driver, the board's SNMP
and ARP, the switch's counters, the driver again) between two host reads: `-P…` just before it
(`HP`: the adapter's `rx_packets` and `tx_packets`, the host's ICMP line) and `-H…` just after
it (`HN`, the capture's read-time window, the kernel log's window). Δ is this bracket minus the
previous one. From the board: `n` Δ`n_tx`, the CPU port's `c` (`CRCAlignErr`), `j`, `f`, `d`
(`JabberErr`, `FragErr`, `Drop`), `dropev`, its size buckets (a frame of L bytes counts in the
bucket of L + 4), port 3's output `o` and input; from the last intact driver dump
`n_recov_fire`, `n_tx_stop`, `nd_up`, `tx15`; the board's `Ip:` and `Udp:` lines. From the
host: `h` Δ`rx_packets`, `i` Δ`Icmp.InEchoReps`, Δ`Icmp.OutEchos`. `brdelta.py` 1.2 prints, per
pair of brackets, 1.1's lines (`board`, `cpu`, `p3`, `host`, `path`, `fault`, `leak`) and four
new ones: `ident o d O cjfd d M k K` (K = o − (c − j − f − d)),
`buckets legal d B cjf d N lt64 d Z`, `hbound inner d I outer d U o d O within yes|no` (I: the
host's rx from the previous `-H` to this `-P`; U: from the previous `-P` to this `-H`), and
`snmp ip … | udp …`; `brdelta snmp A B` prints the same `snmp` line for two cells that each
print `/proc/net/snmp`.

**The captures, by record order.** At every `-H` read, `pcapwin` 1.3's `window` prints the
read-time window (a reading: a frame the host has counted may not yet be in the file). After a
capture stops, its `W-…ORD` cell runs `pcapwin order` over every `-P` and `-H` read taken while
it ran (100 for `WE.pcap`, 36 for `WS.pcap`): the anchor is the host's `rx_packets` read on
both sides of the stop (`W-TCP…X`) and tcpdump's own summary; with the anchor ok (captured =
the file's records, 0 dropped, the two rx reads equal, no partial record) each host read's
`rx_packets` is a record index, and each window between two reads is exactly the frames the
host counted there, printed with the same lines as a window (frames, lengths, the six classes,
`vlan8100`, `excess`, `echo_seq` per identifier, `lenby`). 量 its control: over block 47's
`WE.pcap` and host logs it gives the indices 5, 226, 232, 400, 405 and 626 at `E-F1-H0` …
`E-F2-H1`, the adjudicated windows (card2 `order-b47.out`).

### 3.1 The premise, tested in every bracket

* **P0.** At every pair of consecutive board reads: **(a)** `o = c − j − f − d` exactly (`k 0`;
  block 46 76 of 76, block 47 65 of 66, the miss at E-L1: `NET-131`, `notes/nic-driver.md`
  § 25.4); **(b)** `inner ≤ o ≤ outer` (`within yes`); **(c)** for each capture, the
  record-order anchor holds (`anchor ok`: tcpdump dropped nothing, the file holds every record
  it counted, and the host's `rx_packets` did not move across the stop — which also needs every
  frame the host counts between the capture's first host read and its stop to be one the filter
  keeps: `WE.pcap` keeps every board frame, and `WS.pcap` runs with `rlx0` down, § 0 ⑤);
  **(d)** in every stack bracket, port 3's input Δ is at least the host's Δ`Icmp.OutEchos`
  (`path … covered yes`, a gate). **What a failure voids, written now.** (a) failing by K
  frames: that bracket's **stage chain** is void — every verdict that subtracts one stage's
  count from another's in that bracket (o against c − j − f − d, h or a window against o, the
  driver's n against c) — and a verdict that compares one counter of that bracket with a
  threshold stands only if that counter lies at least |K| beyond the threshold on the side it
  claims (so `j + f + d ≥ 1` read as 625 stands against K = 4, and `j = f = d = 0` stands only
  where K = 0). Nothing outside that bracket is voided, and a ping's or an `iperf3`'s own count
  and a capture's sequence numbers never are. (b) failing: that bracket's host side (h, i, its
  capture window) is void; the board's counters stand. (c) failing: every record-order window
  of that capture is void, the read-time windows are then the only ones and are marked so, and
  the counters stand. (d) failing: § 6 (`NET-124`), never read as the fix failing.

### 3.2 The opening state

* **P1** (`I-B`). With 1.4's defaults and `rlx0` up (`tx15 txlen rlxfw txoff 2 txrb 0 dirty 0`,
  `nd_up 1`), the page reads 1.5 untouched since boot:
  `v15 last - 0 ok 0 refused 0 txq N arm15 0`,
  `sw never mode loop from 0 to 0 probe 0 rc 0 bufs 00000000`, the boot key, `mt none 1455`
  (block 47's `RB-00-T` read the same, 量). **Refuted by** anything else: a 1.5 verb, record or
  sweep since boot, and no cell after it runs until the owner has read the page (§ 6). This is
  not the read-back: nothing is held and nothing is graded.

### 3.3 `D2`'s second boot: E2 at block 45's spacing (`I-E`: the fix `F1`, 1.4 `L1`, the fix `F2`)

Card 1's arms, cell for cell (the generator refuses an arm whose cells differ from another's
but for the `txlen` word): the policy switch (`ifconfig rlx0 down`, `txlen`, `arm`,
`ifconfig rlx0 up`), the port-3 and liveness gates, a bracket, block 45's own E2 (`ISZ`: eleven
`ping -c 20 -i 0.05 -w 10` runs back to back), a bracket, the path gate over the pair.

* **P2, the fix (`F1` and `F2` each; `D2`'s E2 conjunct on boot 2).** 220 of 220 — each of the
  eleven `ping`s `20 packets transmitted, 20 received`; `i` = 220; the stack capture's
  record-order window holds 220 echo replies, eleven identifiers with sequence numbers 1-20
  each; `j = f = d = 0`, `dropev` Δ 0, the `512 - 1023` bucket Δ 0, `n_recov_fire` Δ 0,
  `vlan8100 0`, `excess 0` only; buckets Δ `64:` 20 + a, `65 -127:` 60, `128 -255:` 0,
  `256 - 511:` 60, `1024 - 1518:` 80, `c` = 220 + a, a the board's ARP frames in the bracket
  (block 47: 220 of 220 in both arms, a = 1, 量). **Refuted by** any conjunct failing while the
  arm's `path` reads `covered yes`: `D2` is not met on this boot.
* **P3, 1.4 (`L1`), the positive control.** The loss reproduces: at least one of the seven
  lengths (61, 62, 63, 263, 277, 1,511, 1,512) left requests unanswered — fewer than 20
  received by `-w 10`, or more than 20 transmitted (block 47: 61, 263, 1,511 and 1,512 received
  fewer than 20, 量) — **and** `j + f + d ≥ 1` in the bracket (block 47: 625), subject to P0
  (a)'s threshold rule. **Refuted by** 220 of 220 with no refusal, every `ping` 20 transmitted
  and 20 received: the positive control failed, and this boot says nothing about the fix (the
  gate's `D2` clause). **Two edge cases, read now.** Every length received 20 but a faulty
  length transmitted more than 20: **held** if `j + f + d ≥ 1` — requests went unanswered at a
  faulty length and `-w 10`'s retries filled the count (the loss is transmitted − received, not
  the final figure); with `j + f + d = 0` it is the next case. A length received fewer than 20
  (or transmitted more) with `j + f + d = 0`: **undetermined**, neither held nor refuted — the
  loss is there but no counter names the length fault, so it is not attributed to it (P0 (a)
  and the capture say where the frames went), and this boot's E2 conjunct of `D2` stands
  without its positive control.
* **P4, order.** `F2` repeats `F1` after `L1` has faulted on the same boot: if the fix held
  only on a fresh history, `F2` fails where `F1` passed.
* **`D2` after this block.** Boot 1 is block 47's (`NET-128`, ADJ R2: met on card 1's P4 ping
  conjunct, its `jfd` conjunct void under that card's wording). If P2 (both arms) and P3 hold
  here, `D2`'s E2 conjunct is met on two boots; with P12 below, its sweep conjunct is met on
  both.

### 3.4 `D1`'s stack arm, one length a bracket (`I-S`)

At each of E2's eleven lengths, in E2's order, the fix (`SF-<L>`) then 1.4 (`SL-<L>`), each an
arm of eleven cells identical but for the `txlen` word: the switch (which re-arms the ring),
the port-3 gate, the liveness gate (its 60-B replies are the last frames the board sends before
the arm), `-P0`, `-R0`, `-H0`, the stimulus `PG`: `ping -c 20 -s L−42 -i 0.05 -W 1`, **20
requests, no deadline**, then `-P1`, `-R1`, `-H1` and `-D`, the path gate. Every figure here is
a line of `arith50.out`.

* **P5, the fix at every length (`SF`).** 20 of 20 at each of the eleven; the record-order
  window from `-H0` to `-P1` (the stimulus's) holds 20 echo replies of one identifier, sequence
  numbers 1-20, `vlan8100 0`, `excess 0`; `j = f = d = 0`, `k 0`, `dropev` Δ 0, `n_recov_fire`
  Δ 0; the CPU port's bucket of L + 4 Δ 20 (plus the board's ARP frames in `64:`). **Refuted
  by** any of these failing while `path` reads `covered yes`: the fix does not hold on the
  stack path at that length (and `D2`'s refutation clause fires, P14).
* **P6, 1.4 at the four clean lengths (`SL-0060`, `-0276`, `-1513`, `-1514`; L mod 8 ∈ {4, 4,
  1, 2}).** 20 of 20, `j = f = d = 0`, `k 0`, `n_recov_fire` Δ 0: E2's losses at 276 (block 45
  20/25, block 47 20/49) and 1,513 (20/22, 20/82) were the previous length's state, not a fault
  of those lengths (the M3 clause of R6b's candidates). **Refuted by** any loss or
  `j + f + d ≥ 1` at those four with `path` covered: M1-cover8 does not describe the stack path
  at 1.4 there — a second mechanism, named from the bracket and the capture.
* **P7, 1.4 at the seven faulty lengths (61, 62, 63, 263, 277, 1,511, 1,512), per frame.** On
  the record-order window from `-H0` to `-P1` (the stimulus's), **sequence 1 is answered** at
  all seven: reply 1 follows the liveness gate's 60-B replies, clean under M1-cover8. Reply 2
  follows a faulty reply 1 at L, so M1-cover8 sends it wrong, and under H-prev its `ph_len` is
  reply 1's own two bytes at offset 8⌈L/8⌉ − 12 — which in the stack path are the host's ping
  payload, echoed, not the `tx` verb's pattern `arith49` models: a 16-byte timestamp (payload
  bytes 8–15 a little-endian microsecond count) and then byte i = i mod 256 (量 on block 47's
  captured replies, 364 of 364: payload bytes 16–21 read `10 11 12 13 14 15`, byte 10 in 0–15,
  byte 11 0; 推 past the 64-byte cut). **At 263, 277, 1,511 and 1,512** that is the fill, giving
  4,819, 8,931, 12,979 and 12,979, each past `AcptMaxLen` 1,536 (讀 on port 0,
  `notes/switch-driver.md`; the CPU port's own value is unread): a jabber, so there **sequence
  2 is not answered, ping reads at most 19 received, and `j ≥ 1`**. **At 61, 62 and 63** the
  offset (52) falls on the timestamp: reply 2's `ph_len` is 256 × k, k being reply 1's payload
  byte 10, which the capture keeps (pcapwin 1.3's `echo_first … b10 k`). So, per length: **k ≥
  7** — 1,792 or more, a jabber: sequence 2 not answered, at most 19 received, `j ≥ 1`; **k = 0
  or 6** — not predicted (a runt; `ph_len` exactly 1,536); **1 ≤ k ≤ 5** — a legal wrong
  length, where this card predicts no branch over another. **The decision rule, written now**,
  read on the inner window's capture first and then on the bracket: **(a)** sequence 2
  answered, 256k − 4 − L bytes longer than its datagram (`echo_seq` holds 2 and
  `echo_excess … 2:`256k − 4 − L; the host trims the tail and its ICMP layer counts the reply):
  M1-cover8 and H-prev both stand at that length, offset and byte source included, and the
  engine put `ph_len` − 4 bytes and an FCS on the wire, as for a right frame; **(b)** sequence
  2 not answered at any length (`echo_seq` without 2, no `2:` in `echo_excess`), with
  `j = f = 0` and `d ≥ 1`: M1-cover8 stands (reply 2 went wrong), H-prev's value is tested only
  as under 1,536, and the CPU port counted a legal wrong-length frame `Drop` and did not
  forward it (it adds to `d`, not to `NET-131`'s K); **(c)** sequence 2 not answered, with
  `j ≥ 1`: M1-cover8 stands and H-prev's value at 61–63 does not — the engine used a length
  over 1,536, so the offset (52) or the byte source (the timestamp's byte 10) is wrong at these
  lengths. The counters are the bracket's: where sequence 2 is the only one of the twenty not
  answered and no reply carries an excess (19 received, `echo_seq … 1,3-20`), `j`, `f` and `d`
  are reply 2's alone and name its branch; where more frames are wrong, they sum over all of
  them, (b) reads only as `j = 0` over them all, and `j ≥ 1` is (c) for some frame of that
  length, reply 2's own branch then undetermined. Sequence 2 answered at its own length
  (`excess 0`) is none of the three (a refutation, below); answered with another excess, the
  wire model is refuted and the excess is the length the engine used. **The prior, from block
  47** (`prior47.out`, a second reader of that capture beside the review's, 量): in `E-L1`'s
  window every reply answered at 62 or 63 with k from 1 to 5 — nine: at 62 sequences 5, 7, 62,
  116 and 132 (k 2, 3, 4, 4, 2), at 63 sequences 16, 141, 143 and 157 (k 4, 3, 5, 1) — was
  followed by a sequence never answered, and no frame of 256k − 4 bytes reached the host (the
  bracket's 168 host frames are 145 replies at their own lengths, 19 tagged 277-B replies and 4
  ARP): nine of nine (b)- or (c)-shaped, none (a). That bracket cannot tell (b) from (c) (`jab`
  581, `frag` 3, `drop` 41, summed over every wrong frame of eleven `ping`s); its 512–1023
  bucket moved by 3, a length no E2 frame has, where the four cases at k 2 or 3 would put four
  frames of 512 or 768 bytes there under H-prev at 52 (推: one of them did not, or a frame
  dropped there is not bucketed). The prior may not carry over: each of the nine was
  mid-stream, after wrong frames of its identifier whose carry-over is 未定 (`NET-130`), where
  `SL`'s reply 2 is the first wrong frame after a re-armed ring and the liveness gate's 60-B
  replies. **What fixes H-prev's offset:** the 19 tagged 277-B replies carry TCI `06E7`, the
  fill's bytes at frame offset 272 = 8⌈277/8⌉ − 12 + 4 (payload bytes 230–231, `E6 E7`, VID
  1,767; 量 `prior47.out`), which fixes the H-prev block's absolute offset on the stack path at
  277; the `tx`-verb and loopback maps fix it only modulo their pattern's 64-byte period. At
  61–63 the offset 8⌈L/8⌉ − 12 = 52 is **推** (the same formula, never read at these lengths). 量
  block 47's `E-L1` at 61 read k = 13 and only sequence 1 answered. Beyond sequence 2 nothing
  is predicted (the carry-over is 未定: block 47's `HI-3`/`HI-4` refuted both history rules, ADJ
  R5, `NET-130`). **Refuted by** sequence 1 unanswered at any of the seven (the re-arm did not
  give a clean start, or M1-cover8 does not describe the stack's first frame); where a jabber
  is predicted, sequence 2 answered while the bracket's `n` equals 20 plus the board frames of
  other lengths the **inner** window (`-H0` to `-P1`, never a frame outside the bracket) holds
  — so no uncaptured frame, a board ARP that took the fault in reply 2's place, sat between
  replies 1 and 2 — or `j + f + d = 0`; at 61–63 with 1 ≤ k ≤ 5, sequence 2 answered at its own
  length (`excess 0`: it did not go wrong), or sequence 2 not answered with `j + f + d = 0` (a
  wrong frame no counter saw; P0 (a) says whether one went missing). Branches (a), (b) and (c)
  are readings, not refutations: each is written above with what it means. Every figure is a
  line of `arith50.out` (`SLB`, `SLK`) or of `prior47.out`.
* **P8, `D1`'s reading for the stack arm, written now.** At each faulty length, if `SL` reads
  the fault at the CPU port (`j + f + d ≥ 1`, or at 61–63 a reply on the capture longer than
  its datagram) with the driver having handed the replies to the engine (`n` Δ ≥ 20 − the
  replies the board's stack discarded, Ip `OutDiscards` Δ, `NET-57`) while `SF` at the same
  length, identical cells, reads `j = f = d = 0`: under `txlen` alone, the stack arm's frames
  change length after the driver's fill (whose words block 47 read back EQUAL, not repeated)
  and at or before the CPU port's receive MAC — the placement block 47 read for the `tx`-verb
  and loopback arms (ADJ R3, 推 from 量 parts). If the seven read so, with P5 standing at all
  eleven and P6 at the four clean ones, `D1`'s stack arm is met per length and `D1` is named,
  with its three arms; a length that does not is recorded with the arm that failed to separate
  it, and `D1` stays open. What stays 推 whatever this card reads: that the stage is the TX DMA
  engine (nothing between descriptor memory and the CPU port's MAC is measured), and what the
  engine fetched.

### 3.5 The o-identity, decided where it can be

* **P9** (`NET-131` 殘留; the candidates are ADJ R3's and that row's: (1) a frame counted as
  `Drop` and also as `JabberErr` or `FragErr`; (2) frames counted as `Drop` and forwarded to
  port 3 — the aggregate E-L1 bracket cannot tell them apart, since both give o = c − j − f − d
  + K with the legal buckets summing to c − j − f). Predicted (推, blocks 46–47): K = 0 in every
  bracket at the fix and in every bracket where `d = 0`. **The decision, written now, for any
  bracket with K ≠ 0** (the 22 `S` brackets, the three E brackets, and every other pair of
  board reads): **(i)** `j = f = 0` and 0 < K ≤ `d` there: candidate (2) stands and (1) is
  excluded for that bracket (no more than `d` Drop-counted frames can have been forwarded, so K
  above `d` excludes both); **(ii)** `d = 0` there, or K below 0 outside a read-skew pair (both
  candidates add frames to o): both are excluded — a third cause, named from that bracket's
  `buckets` line and its record-order window; **(iii)** `j + f > 0` and `d > 0`: (1) alone
  requires K ≤ min(`d`, `j + f`) there (the frames counted twice cannot outnumber either
  counter), so a K above that excludes (1) as the only cause for that bracket, while (1) and
  (2) together allow any K ≤ `d` and only a K above `d` excludes both; otherwise this card does
  not decide it, and the row stays open naming the experiment that does: a 1.4 bracket in which
  `Drop` moves with `j = f = 0`. A K of −x in one bracket and +x in the next is x frames that
  crossed the CPU port and port 3 between one read's two prints (the board read prints port 3
  before the CPU port, so such a frame is in the first bracket's c and the next one's o: read
  skew), neither candidate, and the pair reads K = 0; +x then −x is not skew. Beside each such
  bracket, the record-order window says which requests were answered and at which lengths, per
  frame. If K ≠ 0 recurs in no bracket, the miss is not reproduced here (a reading; the row
  keeps block 47's one instance).

### 3.6 The wire (`I-W`)

* **P10, the loopback's positive control (`LB-P`, 1.4, probe 60, one unit each at 61 and 1,511,
  `rlx0` down).** `LB-P-1511`'s page: `mt none 1453 clean 0 bad_b 2 bad_a 0 void 0 skew 0` (a
  gate); `hb 9831:1:61-61 3663:1:1511-1511` — H-prev's values (H-own gives 9,831 at both,
  H-slot 9,831 and 8,224), the source block 47's maps and carry-over cells left standing for
  the frame after a faulty one (ADJ R6, `NET-129`); frame b's class 5 (alien) at both (block
  47: class 5 at every bad-b length, 量). `LB-P-D`: `leak none`. **Refuted by** `bad_b` below 2
  with `void 0`: the loopback does not show 1.4's fault on this boot, `W-00`'s gate would be
  vacuous, and no multi-length wire sweep runs (§ 6); a `ph_b` or class other than these: a
  reading against ADJ R6's scope.
* **P11, the fix's loopback map (`LB-V`, the containment gate `W-00`).** `sw done … rc 0`,
  `sw scored 1455 bad_a 0 bad_b 0 void 0 skew 0`, `delta0 0`, `SWEND=00000000` (a reading).
  **Refuted by** any bad length: the fix does not hold at every length in loopback (card 1's
  P9, which held); `W-1` does not run.
* **P12, the fix over every length on the wire (`D2`'s sweep conjunct on boot 2).** In each of
  `W-1a`…`W-1d` (60–423, 424–787, 788–1,151, 1,152–1,514): `sw done mode wire … rc 0`,
  `j = f = d = 0`, `c` = `o` = `h` = two frames a unit (728, 728, 728, 726; with `rlx0` down no
  stack frame falls in a gap, so `inner = outer`), the record-order window holding each length
  once and the probes at 60 (365, 364, 364, 363); in all 2,910 frames and `jfd 0` (block 47:
  the same, 量). **Refuted by** `jfd ≥ 1` in any quarter (the conjunct fails on this boot; the
  later quarters do not run, § 6) or lengths shifted on the capture. A quarter whose page ends
  `rc` other than 0 (an errno after it opened) has not swept its whole sub-range: the conjunct
  is unmeasured from its `sw last` length on, and the later quarters still run if its
  `fault jfd 0` held. **P12's zero depends on P13.**
* **P13, 1.4 bounded (`W-2`, E2's eleven, one bracket per length: 60, 61, 62, 63, 263, 276,
  277, 1511, 1512, 1513, 1514), the owner's bound shown first.** `W-2-EP`: a two-length wire
  sweep at `txlen rlxfw` refused -1 (EPERM) with no mark (a gate), and its page's `sw key` line
  the same as `W-2-V`'s, the records untouched (a reading: on § 6's paths that skip `W-1` the
  key is not `W-1`'s, and the bound is checked before the key, 讀 `rtl819x-nic-tx.h`). Then, at
  the seven faulty lengths: `jfd` Δ 1, `h` Δ 1, `c` Δ 2; at 60, 276, 1,513 and 1,514: `jfd` Δ
  0, `h` Δ 2, `c` Δ 2; in all `jfd` 7, `c` 22, `h` 15 (block 47 read exactly these rows among
  its 35, 量). **Refuted by** a length whose row differs: the loopback map at 1.4 does not
  predict the wire there. Why E2's eleven and not card 1's 35: the control needs only 1.4
  faulting on the wire on this boot, and these eleven are the `tx`-verb arm at the lengths
  `I-S` runs the stack arm at, on the same boot; the 35 cost about 2.5 minutes more and block
  47 read all 35 as predicted.

### 3.7 `D2`'s refutation clause on this boot

* **P14.** *220 of 220 on E2 while `JabberErr`, `FragErr` or `Drop` moves anywhere else in the
  same boot (TCP, the sweep)* reads exactly the brackets whose whole board window ran at
  `txlen vendor`: `E-F1-R0`→`R1`, `E-F2-R0`→`R1`, the eleven `SF-<L>-R0`→`R1`,
  `LB-P-R`→`LB-V-R`, `LB-V-R`→`W-1a-R` … `W-1c-R`→`W-1d-R`, and `D3-00-R`→`D3-TR1-R` …
  `D3-US2-R`→`D3-US3-R` (the twelve trials: TCP and UDP both ways). Predicted `jfd 0` in every
  one. **Refuted by** `jfd ≥ 1` in any, subject to P0 (a): the fix is partial and is not called
  a fix. Excluded, as 1.4's controls or transitions: `E-L1`, the `SL` brackets, `LB-P`, `W-2`,
  the D3 control and every bracket spanning a switch cell. `LB-P-R`→`LB-V-R` spans `LB-V-V`'s
  policy change with `rlx0` down: the only frames in it are `LB-V`'s own, at the fix.

### 3.8 `D3`, and `NET-117` 殘留 (`I-D3`)

Every trial is `NET-111`'s shape (`bench/2026-09-23`, 讀): the board runs its own one-off server
with its own log (block 44's form, `iperf3 -s -1 -f k --logfile /tmp/<t>.log`), `-S0` shows
that server in `ps` (a gate, anchored on the COMMAND column, FW-128) and prints
`/proc/net/snmp` and `/proc/stat`; the host runs the same `iperf 3.1.3` MIPS binary under
`qemu-mips-static` with `timeout 70` (`IPERF`, its digest a gate in `I-0`); `-S1` prints
`/proc/net/snmp` and `/proc/stat`, stops any server still running and prints the server's log;
then a bracket, `brdelta pair`, `iperflog parse`, `brdelta snmp`, and for a board-receives
trial at the fix `iperflog compare`. The liveness gate runs before each trial. TCP
board-receives `TR1`–`TR3` (`-t 30 -i 5 -f m`), TCP board-sends `TS1`–`TS3` (`-R`), UDP
board-receives `UR1`–`UR3` (`-u -l 1400 -b 20M -i 1`), UDP board-sends `US1`–`US3` (`-R`), at
`txlen vendor`; then `txlen rlxfw` and `LUR1`, `LUS1`.

* **P15, `D3` at the fix.** The end-of-test exchange completes in **12 of 12**: each host log
  ends with `iperf Done.` after its summary (TCP: a `receiver` line; UDP: the lost/total line
  from the server's results), its cell's `rc 0`, no `No route to host` and no `iperf3: error`;
  on the board, `iperflog parse` finds a TEST_END summary in each board-receives trial's log
  (exit 0; exit 1 is its design on `-R`). **Refuted by** any of the twelve without
  `iperf Done.`: `D3` is not met on this boot, and the remaining failure is named from the
  host's output (no route, parameter exchange, results exchange), the server log's shape
  (FW-128's TEST_END, CLIENT_TERMINATE or killed), the bracket (`n` against `c`, `jfd`,
  `n_recov_fire`, `n_tx_stop`) and the ring in the bracket's dumps. That is also `D3`'s gate
  clause: E2 passing (P2) while `NET-111`'s exchanges still fail says the length fault was not
  `NET-112`'s whole mechanism.
* **P16, the control at 1.4 (`LUR1`, `LUS1`).** At least one of the two ends without
  `iperf Done.` (at 1.4, UDP board-receives and board-sends completed 0 of 12 over seatings 39
  and 40 (0 of 6 on each), 讀 `NET-111`, `NET-116`; 推 under M1-cover8 the bulk frames are clean
  — 1,442 B, 1,442 mod 8 = 2 — so what 1.4 breaks is the exchange and the connection, as
  `NET-112` read). **Refuted by** both completing: the positive control failed, and this boot's
  12 of 12 says nothing about the fix.
* **P17, what the host printed is the board's own figure.** At each board-receives trial at the
  fix (`TR1`–`TR3`, `UR1`–`UR3`) that completes, `iperflog compare` reads **AGREE** (TCP: the
  host's `receiver` transfer is the board's byte count; UDP: the host's lost/total are the
  board's), the control `NET-116` read 6 of 6 on `eth4`. **Refuted by** DISAGREE: the exchange
  completed with a figure that is not the board's — a finding about the results frame, named
  from its log and the host's.
* **P18, `NET-117` 殘留: where the UDP datagrams the board does not read die** (`UR1`–`UR3` at
  the fix, `LUR1` at 1.4). 讀 2.6.30's `udp.c` in the build cell: `InDatagrams` counts at
  `recvmsg`, when the application reads a datagram, and a socket queue refused for memory adds
  1 to both `RcvbufErrors` and `InErrors`. With L = the host's `Sent N datagrams` − Udp
  `InDatagrams` Δ (`-S0` → `-S1`), the lost datagrams are placed, by thresholds written now, at
  **the socket** if `RcvbufErrors` Δ ≥ 0.9 L; at **IP** if Ip (`InReceives` − `InDelivers`) Δ ≥
  0.9 L; **below IP** if the driver's `n_rx` Δ − Ip `InReceives` Δ ≥ 0.9 L (from the bracket);
  otherwise **undetermined**, with the three differences named. Predicted (推): the socket — the
  receive path is CPU-bound (`NET-117`: 2,286 softirq ticks in `UR1`'s window, 76 % of its 30 s
  if all fell in the data period; `NET-116`: the board 32.63 % busy over the whole window) and
  the fix changes only TX. **Refuted by** `RcvbufErrors` Δ below 0.9 L at any of `UR1`–`UR3`:
  the loss is not the socket's, and the rule above places it. Readings beside it: the loss
  against seating 40's 86.6–87.8 % ± 10 points, and the board's CPU from `/proc/stat` in `-S0`
  and `-S1` (`NET-116`'s instrument, kept).

### 3.9 The maps, `n_writes`, and the host path

* **P19.** `R1-MB0` and `R1-MB1` read block 46's and block 47's map digest (`0927be41…`), one
  `DIFFER` in group 0, 31 the same; `R1-NW0` and `R1-NW1` `n_writes 0`, and
  `recipe_id 06C39CA3` (a reading beside `looprun`'s `RLXFW-ID0`). **Refuted by** another
  digest or group line (flash moved since block 47) or `n_writes` other than 0.
* **P20, the host path (`NET-124` 殘留).** Every liveness gate 4 of 4, every port-3 gate `LinkUp`
  on both readers, every stack bracket `covered yes`, every kernel-log window `follower 1`; the
  kernel log clean of the three gated signatures before power (`urb -104` lines are not gated:
  block 47 read 302 with the board off). The `BUG` trace is counted per window beside the
  host's Δ`tx_packets`, a reading (ADJ R9). If the silent state recurs, it is marked by a
  failed gate and read by § 6's ordered set before any recovery.

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck` refuses
the verbs (`FW-113`); every upload is `looprun`'s, which requires `00000000` read back from the
`AUTOBURN` word before it uploads. 🔴 Every `--send` is at most 127 characters, holds no `$` and
no upper-case word. 🔴 **No gate reads a console mark** (`FW-47`; a `cardnum` row counts zero).
🔴 **Every refusal the card provokes is a gated guard** (`W-2-EP`), and `verbcheck50.py` replays
every write through the committed header before power. 🔴 **No cell holds the ring**: no
`txstall`, no `tx` verb, no read-back. 🔴 **No frame capture is printed**; the captures are cut
at 64 bytes and filtered to the board's address, and only `pcapwin.py` reads them. 🔴 **No line
of the host's kernel log reaches `bench/`**: only `dmesgwin.py`'s counts. 🔴 No host cell prints
a home path into `bench/`. 🔴 No cell touches the reset button or the watchdog. 🔴 `rlx0` goes
down only in the card's own cells, and every `up` finds the ring freshly armed with the engine
off (`NET-58`; the generator refuses otherwise). 🔴 No step removes `/proc/rtl865x/`. 🔴
`sudo -n pkill -INT -x tcpdump` stops every `tcpdump` on the host: `R0-TCPC` requires none
before power, `E-LIVE` and `S-LIVE` exactly one before their arms. 🔴 Exactly one `dmesg`
process, the off-card follower, runs from before `I-0` to after `I-Z`. 🔴 No `iperf3` server
outlives its trial: every `-S1` stops it. ⚠️ Off-card cells are declared in
`bench/2026-09-26b/CORRECTIONS-block48.md` before they run, except those § 6 declares now with
their text (each still logged there as it runs) and a power-off, which § 6 decides now.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-26b --skip S2,S3,S4 --recipe-override 06c39ca3 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 46's, unchanged
`HP` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/rx_packets /sys/class/net/enxfc19286184c9/statistics/tx_packets ; grep '^Icmp:' /proc/net/snmp` — the host read just before a board read (P0 (b))
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — the liveness probe: 60-B frames, clean at every setting
`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`PG <s>` = `ping -I enxfc19286184c9 -c 20 -s <s> -i 0.05 -W 1 -q 10.1.1.3`
`TDE <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap2/<f> ether src 02:52:4c:58:46:57`
`TDS <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap2/<f> 'ether src 02:52:4c:58:46:57 and (ether proto 0x88b5 or (ether proto 0x8100 and ether[16:2] = 0x88b5))'`
`PWE <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py window /home/key/fwre-work/rebuild/s112/r6b3/pcap2/WE.pcap --if enxfc19286184c9 --prev <prev>`
`PWS <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py window /home/key/fwre-work/rebuild/s112/r6b3/pcap2/WS.pcap --if enxfc19286184c9 --prev <prev>`
`PWO` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py order`
`DW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py window /home/key/fwre-work/rebuild/s112/r6b3/host/dmesg-w2.log --prev <prev>`
`SWC` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/swcheck.py page`
`BD` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py`
`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
`ILG` = `/usr/bin/python3 tools/iperflog.py`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — block 46's, unchanged

A `ping`'s `-s` is L − 42. A stimulus cell's longest silence is about 1 s (a trial's `-S1`: its
`sleep 1`; the switch, as block 47 ran it at the same `--idle`) and its `--idle` is 3; a
server-start cell's is its `sleep 2` (the `&` prints nothing) and its `--idle` is 4; § 6's
declared `X-<t>-S0R`'s is its two sleeps, about 3.05 s, and its `--idle` is 6; every read ends
on a pattern (`--until`) that also matches the loader's banner. A sweep cell is one send —
`swclear` first where its key is new, the sweep, then `cat /proc/rtl819x-nic-tx` — and ends on
the page's last `ww` line and the prompt; its cap is 180 s for a full map, 90 s for a quarter,
15 s for one length. Every `-H` cell passes `pcapwin`, and every kernel-log reader passes
`dmesgwin`, a `--prev` list (§ 6, *Chained references*), so each window starts where the
previous one on the path the press took ended.

### Before power

```
CAP --out bench/2026-09-26b/R0-PRE --seconds 3
HOST bench/2026-09-26b/R0-PREC :: ls bench/2026-09-26b/R0-PRE.log bench/2026-09-26b/R0-PRE.timing bench/2026-09-26b/R0-PRE.meta.json && cat bench/2026-09-26b/R0-PRE.meta.json
HOST bench/2026-09-26b/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-26b/R0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9 ; uname -r
HOST bench/2026-09-26b/R0-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-26b/R0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-26b/R0-DW0 :: DW none
HOST bench/2026-09-26b/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-26b/R0-PCAP :: mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/pcap2 && find /home/key/fwre-work/rebuild/s112/r6b3/pcap2 -name '*.pcap' | wc -l
HOST bench/2026-09-26b/R0-IPF :: sha256sum < /home/key/fwre-work/iperf3-port/iperf3 ; ls /usr/bin/qemu-mips-static
HOST bench/2026-09-26b/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/swcheck.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/arith49.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/verbcheck50.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card2/fixtures/MANIFEST.sha256 ; sha256sum < tools/iperflog.py
HOST bench/2026-09-26b/R0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/swcheck.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py --self-test ; /usr/bin/python3 tools/iperflog.py --self-test
HOST bench/2026-09-26b/R0-VERB :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/verbcheck50.py bench/2026-09-26b/PREDICTIONS-B50-block48.md --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card2/verbcheck50.py --self-test bench/2026-09-26b/PREDICTIONS-B50-block48.md --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top
HOST bench/2026-09-26b/R0-H :: HN
```

### The press — the catch, the shell, the opening map, `n_writes`

```
CAP --out bench/2026-09-26b/R1-CATCH --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-26b/R1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-26b/R1Q :: LR --cell R1Q QIMG --iterations 1
CAP --out bench/2026-09-26b/R1-PS --send 'ps' --idle 3 --seconds 30
CAP --out bench/2026-09-26b/R1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-26b/R1-MB0 :: MB bench/2026-09-26b/R1-M0
CAP --out bench/2026-09-26b/R1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
```

### The opening state

```
HOST bench/2026-09-26b/B-00-P :: HP
CAP --out bench/2026-09-26b/B-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/B-00-H :: HN ; DW bench/2026-09-26b/R0-DW0.log
CAP --out bench/2026-09-26b/B-00-T --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
```

### The stack arms' capture

```
HOST& bench/2026-09-26b/W-TCPE :: TDE WE.pcap
```

### `D2`'s second boot: E2 at the fix, at 1.4, at the fix

```
HOST bench/2026-09-26b/E-LIVE :: pgrep -xc tcpdump ; true
CAP --out bench/2026-09-26b/E-F1-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/E-F1-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/E-F1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/B-00-H.log
HOST bench/2026-09-26b/E-F1-P0 :: HP
CAP --out bench/2026-09-26b/E-F1-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-F1-H0 :: HN ; PWE none ; DW bench/2026-09-26b/E-F1-L.log
HOST bench/2026-09-26b/E-F1-E2 :: ISZ 10.1.1.3
HOST bench/2026-09-26b/E-F1-P1 :: HP
CAP --out bench/2026-09-26b/E-F1-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-F1-H1 :: HN ; PWE bench/2026-09-26b/E-F1-H0.log ; DW bench/2026-09-26b/E-F1-H0.log
HOST bench/2026-09-26b/E-F1-D :: BD pair bench/2026-09-26b/E-F1-R0.log,bench/2026-09-26b/X-E-F1-R0.log bench/2026-09-26b/E-F1-R1.log,bench/2026-09-26b/X-E-F1-R1.log --host bench/2026-09-26b/E-F1-H0.log bench/2026-09-26b/E-F1-H1.log --pre bench/2026-09-26b/E-F1-P0.log bench/2026-09-26b/E-F1-P1.log
CAP --out bench/2026-09-26b/E-L1-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/E-L1-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/E-L1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/E-F1-L.log,bench/2026-09-26b/E-F1-H1.log
HOST bench/2026-09-26b/E-L1-P0 :: HP
CAP --out bench/2026-09-26b/E-L1-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-L1-H0 :: HN ; PWE none,bench/2026-09-26b/E-F1-H1.log ; DW bench/2026-09-26b/E-L1-L.log
HOST bench/2026-09-26b/E-L1-E2 :: ISZ 10.1.1.3
HOST bench/2026-09-26b/E-L1-P1 :: HP
CAP --out bench/2026-09-26b/E-L1-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-L1-H1 :: HN ; PWE bench/2026-09-26b/E-L1-H0.log ; DW bench/2026-09-26b/E-L1-H0.log
HOST bench/2026-09-26b/E-L1-D :: BD pair bench/2026-09-26b/E-L1-R0.log,bench/2026-09-26b/X-E-L1-R0.log bench/2026-09-26b/E-L1-R1.log,bench/2026-09-26b/X-E-L1-R1.log --host bench/2026-09-26b/E-L1-H0.log bench/2026-09-26b/E-L1-H1.log --pre bench/2026-09-26b/E-L1-P0.log bench/2026-09-26b/E-L1-P1.log
CAP --out bench/2026-09-26b/E-F2-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/E-F2-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/E-F2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/E-L1-L.log,bench/2026-09-26b/E-L1-H1.log
HOST bench/2026-09-26b/E-F2-P0 :: HP
CAP --out bench/2026-09-26b/E-F2-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-F2-H0 :: HN ; PWE bench/2026-09-26b/E-F1-H1.log,bench/2026-09-26b/E-L1-H1.log ; DW bench/2026-09-26b/E-F2-L.log
HOST bench/2026-09-26b/E-F2-E2 :: ISZ 10.1.1.3
HOST bench/2026-09-26b/E-F2-P1 :: HP
CAP --out bench/2026-09-26b/E-F2-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/E-F2-H1 :: HN ; PWE bench/2026-09-26b/E-F2-H0.log ; DW bench/2026-09-26b/E-F2-H0.log
HOST bench/2026-09-26b/E-F2-D :: BD pair bench/2026-09-26b/E-F2-R0.log,bench/2026-09-26b/X-E-F2-R0.log bench/2026-09-26b/E-F2-R1.log,bench/2026-09-26b/X-E-F2-R1.log --host bench/2026-09-26b/E-F2-H0.log bench/2026-09-26b/E-F2-H1.log --pre bench/2026-09-26b/E-F2-P0.log bench/2026-09-26b/E-F2-P1.log
```

### `D1`'s stack arm: each of E2's eleven lengths in its own bracket, the fix then 1.4

```
CAP --out bench/2026-09-26b/SF-0060-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0060-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0060-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/E-F2-L.log,bench/2026-09-26b/E-F2-H1.log
HOST bench/2026-09-26b/SF-0060-P0 :: HP
CAP --out bench/2026-09-26b/SF-0060-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0060-H0 :: HN ; PWE bench/2026-09-26b/E-L1-H1.log,bench/2026-09-26b/E-F2-H1.log ; DW bench/2026-09-26b/SF-0060-L.log
HOST bench/2026-09-26b/SF-0060-PG :: PG 18
HOST bench/2026-09-26b/SF-0060-P1 :: HP
CAP --out bench/2026-09-26b/SF-0060-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0060-H1 :: HN ; PWE bench/2026-09-26b/SF-0060-H0.log ; DW bench/2026-09-26b/SF-0060-H0.log
HOST bench/2026-09-26b/SF-0060-D :: BD pair bench/2026-09-26b/SF-0060-R0.log,bench/2026-09-26b/X-SF-0060-R0.log bench/2026-09-26b/SF-0060-R1.log,bench/2026-09-26b/X-SF-0060-R1.log --host bench/2026-09-26b/SF-0060-H0.log bench/2026-09-26b/SF-0060-H1.log --pre bench/2026-09-26b/SF-0060-P0.log bench/2026-09-26b/SF-0060-P1.log
CAP --out bench/2026-09-26b/SL-0060-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0060-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0060-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0060-L.log,bench/2026-09-26b/SF-0060-H1.log
HOST bench/2026-09-26b/SL-0060-P0 :: HP
CAP --out bench/2026-09-26b/SL-0060-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0060-H0 :: HN ; PWE bench/2026-09-26b/E-F2-H1.log,bench/2026-09-26b/SF-0060-H1.log ; DW bench/2026-09-26b/SL-0060-L.log
HOST bench/2026-09-26b/SL-0060-PG :: PG 18
HOST bench/2026-09-26b/SL-0060-P1 :: HP
CAP --out bench/2026-09-26b/SL-0060-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0060-H1 :: HN ; PWE bench/2026-09-26b/SL-0060-H0.log ; DW bench/2026-09-26b/SL-0060-H0.log
HOST bench/2026-09-26b/SL-0060-D :: BD pair bench/2026-09-26b/SL-0060-R0.log,bench/2026-09-26b/X-SL-0060-R0.log bench/2026-09-26b/SL-0060-R1.log,bench/2026-09-26b/X-SL-0060-R1.log --host bench/2026-09-26b/SL-0060-H0.log bench/2026-09-26b/SL-0060-H1.log --pre bench/2026-09-26b/SL-0060-P0.log bench/2026-09-26b/SL-0060-P1.log
CAP --out bench/2026-09-26b/SF-0061-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0061-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0061-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0060-L.log,bench/2026-09-26b/SL-0060-H1.log
HOST bench/2026-09-26b/SF-0061-P0 :: HP
CAP --out bench/2026-09-26b/SF-0061-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0061-H0 :: HN ; PWE bench/2026-09-26b/SF-0060-H1.log,bench/2026-09-26b/SL-0060-H1.log ; DW bench/2026-09-26b/SF-0061-L.log
HOST bench/2026-09-26b/SF-0061-PG :: PG 19
HOST bench/2026-09-26b/SF-0061-P1 :: HP
CAP --out bench/2026-09-26b/SF-0061-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0061-H1 :: HN ; PWE bench/2026-09-26b/SF-0061-H0.log ; DW bench/2026-09-26b/SF-0061-H0.log
HOST bench/2026-09-26b/SF-0061-D :: BD pair bench/2026-09-26b/SF-0061-R0.log,bench/2026-09-26b/X-SF-0061-R0.log bench/2026-09-26b/SF-0061-R1.log,bench/2026-09-26b/X-SF-0061-R1.log --host bench/2026-09-26b/SF-0061-H0.log bench/2026-09-26b/SF-0061-H1.log --pre bench/2026-09-26b/SF-0061-P0.log bench/2026-09-26b/SF-0061-P1.log
CAP --out bench/2026-09-26b/SL-0061-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0061-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0061-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0061-L.log,bench/2026-09-26b/SF-0061-H1.log
HOST bench/2026-09-26b/SL-0061-P0 :: HP
CAP --out bench/2026-09-26b/SL-0061-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0061-H0 :: HN ; PWE bench/2026-09-26b/SL-0060-H1.log,bench/2026-09-26b/SF-0061-H1.log ; DW bench/2026-09-26b/SL-0061-L.log
HOST bench/2026-09-26b/SL-0061-PG :: PG 19
HOST bench/2026-09-26b/SL-0061-P1 :: HP
CAP --out bench/2026-09-26b/SL-0061-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0061-H1 :: HN ; PWE bench/2026-09-26b/SL-0061-H0.log ; DW bench/2026-09-26b/SL-0061-H0.log
HOST bench/2026-09-26b/SL-0061-D :: BD pair bench/2026-09-26b/SL-0061-R0.log,bench/2026-09-26b/X-SL-0061-R0.log bench/2026-09-26b/SL-0061-R1.log,bench/2026-09-26b/X-SL-0061-R1.log --host bench/2026-09-26b/SL-0061-H0.log bench/2026-09-26b/SL-0061-H1.log --pre bench/2026-09-26b/SL-0061-P0.log bench/2026-09-26b/SL-0061-P1.log
CAP --out bench/2026-09-26b/SF-0062-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0062-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0062-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0061-L.log,bench/2026-09-26b/SL-0061-H1.log
HOST bench/2026-09-26b/SF-0062-P0 :: HP
CAP --out bench/2026-09-26b/SF-0062-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0062-H0 :: HN ; PWE bench/2026-09-26b/SF-0061-H1.log,bench/2026-09-26b/SL-0061-H1.log ; DW bench/2026-09-26b/SF-0062-L.log
HOST bench/2026-09-26b/SF-0062-PG :: PG 20
HOST bench/2026-09-26b/SF-0062-P1 :: HP
CAP --out bench/2026-09-26b/SF-0062-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0062-H1 :: HN ; PWE bench/2026-09-26b/SF-0062-H0.log ; DW bench/2026-09-26b/SF-0062-H0.log
HOST bench/2026-09-26b/SF-0062-D :: BD pair bench/2026-09-26b/SF-0062-R0.log,bench/2026-09-26b/X-SF-0062-R0.log bench/2026-09-26b/SF-0062-R1.log,bench/2026-09-26b/X-SF-0062-R1.log --host bench/2026-09-26b/SF-0062-H0.log bench/2026-09-26b/SF-0062-H1.log --pre bench/2026-09-26b/SF-0062-P0.log bench/2026-09-26b/SF-0062-P1.log
CAP --out bench/2026-09-26b/SL-0062-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0062-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0062-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0062-L.log,bench/2026-09-26b/SF-0062-H1.log
HOST bench/2026-09-26b/SL-0062-P0 :: HP
CAP --out bench/2026-09-26b/SL-0062-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0062-H0 :: HN ; PWE bench/2026-09-26b/SL-0061-H1.log,bench/2026-09-26b/SF-0062-H1.log ; DW bench/2026-09-26b/SL-0062-L.log
HOST bench/2026-09-26b/SL-0062-PG :: PG 20
HOST bench/2026-09-26b/SL-0062-P1 :: HP
CAP --out bench/2026-09-26b/SL-0062-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0062-H1 :: HN ; PWE bench/2026-09-26b/SL-0062-H0.log ; DW bench/2026-09-26b/SL-0062-H0.log
HOST bench/2026-09-26b/SL-0062-D :: BD pair bench/2026-09-26b/SL-0062-R0.log,bench/2026-09-26b/X-SL-0062-R0.log bench/2026-09-26b/SL-0062-R1.log,bench/2026-09-26b/X-SL-0062-R1.log --host bench/2026-09-26b/SL-0062-H0.log bench/2026-09-26b/SL-0062-H1.log --pre bench/2026-09-26b/SL-0062-P0.log bench/2026-09-26b/SL-0062-P1.log
CAP --out bench/2026-09-26b/SF-0063-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0063-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0063-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0062-L.log,bench/2026-09-26b/SL-0062-H1.log
HOST bench/2026-09-26b/SF-0063-P0 :: HP
CAP --out bench/2026-09-26b/SF-0063-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0063-H0 :: HN ; PWE bench/2026-09-26b/SF-0062-H1.log,bench/2026-09-26b/SL-0062-H1.log ; DW bench/2026-09-26b/SF-0063-L.log
HOST bench/2026-09-26b/SF-0063-PG :: PG 21
HOST bench/2026-09-26b/SF-0063-P1 :: HP
CAP --out bench/2026-09-26b/SF-0063-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0063-H1 :: HN ; PWE bench/2026-09-26b/SF-0063-H0.log ; DW bench/2026-09-26b/SF-0063-H0.log
HOST bench/2026-09-26b/SF-0063-D :: BD pair bench/2026-09-26b/SF-0063-R0.log,bench/2026-09-26b/X-SF-0063-R0.log bench/2026-09-26b/SF-0063-R1.log,bench/2026-09-26b/X-SF-0063-R1.log --host bench/2026-09-26b/SF-0063-H0.log bench/2026-09-26b/SF-0063-H1.log --pre bench/2026-09-26b/SF-0063-P0.log bench/2026-09-26b/SF-0063-P1.log
CAP --out bench/2026-09-26b/SL-0063-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0063-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0063-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0063-L.log,bench/2026-09-26b/SF-0063-H1.log
HOST bench/2026-09-26b/SL-0063-P0 :: HP
CAP --out bench/2026-09-26b/SL-0063-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0063-H0 :: HN ; PWE bench/2026-09-26b/SL-0062-H1.log,bench/2026-09-26b/SF-0063-H1.log ; DW bench/2026-09-26b/SL-0063-L.log
HOST bench/2026-09-26b/SL-0063-PG :: PG 21
HOST bench/2026-09-26b/SL-0063-P1 :: HP
CAP --out bench/2026-09-26b/SL-0063-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0063-H1 :: HN ; PWE bench/2026-09-26b/SL-0063-H0.log ; DW bench/2026-09-26b/SL-0063-H0.log
HOST bench/2026-09-26b/SL-0063-D :: BD pair bench/2026-09-26b/SL-0063-R0.log,bench/2026-09-26b/X-SL-0063-R0.log bench/2026-09-26b/SL-0063-R1.log,bench/2026-09-26b/X-SL-0063-R1.log --host bench/2026-09-26b/SL-0063-H0.log bench/2026-09-26b/SL-0063-H1.log --pre bench/2026-09-26b/SL-0063-P0.log bench/2026-09-26b/SL-0063-P1.log
CAP --out bench/2026-09-26b/SF-0263-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0263-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0263-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0063-L.log,bench/2026-09-26b/SL-0063-H1.log
HOST bench/2026-09-26b/SF-0263-P0 :: HP
CAP --out bench/2026-09-26b/SF-0263-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0263-H0 :: HN ; PWE bench/2026-09-26b/SF-0063-H1.log,bench/2026-09-26b/SL-0063-H1.log ; DW bench/2026-09-26b/SF-0263-L.log
HOST bench/2026-09-26b/SF-0263-PG :: PG 221
HOST bench/2026-09-26b/SF-0263-P1 :: HP
CAP --out bench/2026-09-26b/SF-0263-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0263-H1 :: HN ; PWE bench/2026-09-26b/SF-0263-H0.log ; DW bench/2026-09-26b/SF-0263-H0.log
HOST bench/2026-09-26b/SF-0263-D :: BD pair bench/2026-09-26b/SF-0263-R0.log,bench/2026-09-26b/X-SF-0263-R0.log bench/2026-09-26b/SF-0263-R1.log,bench/2026-09-26b/X-SF-0263-R1.log --host bench/2026-09-26b/SF-0263-H0.log bench/2026-09-26b/SF-0263-H1.log --pre bench/2026-09-26b/SF-0263-P0.log bench/2026-09-26b/SF-0263-P1.log
CAP --out bench/2026-09-26b/SL-0263-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0263-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0263-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0263-L.log,bench/2026-09-26b/SF-0263-H1.log
HOST bench/2026-09-26b/SL-0263-P0 :: HP
CAP --out bench/2026-09-26b/SL-0263-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0263-H0 :: HN ; PWE bench/2026-09-26b/SL-0063-H1.log,bench/2026-09-26b/SF-0263-H1.log ; DW bench/2026-09-26b/SL-0263-L.log
HOST bench/2026-09-26b/SL-0263-PG :: PG 221
HOST bench/2026-09-26b/SL-0263-P1 :: HP
CAP --out bench/2026-09-26b/SL-0263-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0263-H1 :: HN ; PWE bench/2026-09-26b/SL-0263-H0.log ; DW bench/2026-09-26b/SL-0263-H0.log
HOST bench/2026-09-26b/SL-0263-D :: BD pair bench/2026-09-26b/SL-0263-R0.log,bench/2026-09-26b/X-SL-0263-R0.log bench/2026-09-26b/SL-0263-R1.log,bench/2026-09-26b/X-SL-0263-R1.log --host bench/2026-09-26b/SL-0263-H0.log bench/2026-09-26b/SL-0263-H1.log --pre bench/2026-09-26b/SL-0263-P0.log bench/2026-09-26b/SL-0263-P1.log
CAP --out bench/2026-09-26b/SF-0276-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0276-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0276-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0263-L.log,bench/2026-09-26b/SL-0263-H1.log
HOST bench/2026-09-26b/SF-0276-P0 :: HP
CAP --out bench/2026-09-26b/SF-0276-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0276-H0 :: HN ; PWE bench/2026-09-26b/SF-0263-H1.log,bench/2026-09-26b/SL-0263-H1.log ; DW bench/2026-09-26b/SF-0276-L.log
HOST bench/2026-09-26b/SF-0276-PG :: PG 234
HOST bench/2026-09-26b/SF-0276-P1 :: HP
CAP --out bench/2026-09-26b/SF-0276-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0276-H1 :: HN ; PWE bench/2026-09-26b/SF-0276-H0.log ; DW bench/2026-09-26b/SF-0276-H0.log
HOST bench/2026-09-26b/SF-0276-D :: BD pair bench/2026-09-26b/SF-0276-R0.log,bench/2026-09-26b/X-SF-0276-R0.log bench/2026-09-26b/SF-0276-R1.log,bench/2026-09-26b/X-SF-0276-R1.log --host bench/2026-09-26b/SF-0276-H0.log bench/2026-09-26b/SF-0276-H1.log --pre bench/2026-09-26b/SF-0276-P0.log bench/2026-09-26b/SF-0276-P1.log
CAP --out bench/2026-09-26b/SL-0276-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0276-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0276-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0276-L.log,bench/2026-09-26b/SF-0276-H1.log
HOST bench/2026-09-26b/SL-0276-P0 :: HP
CAP --out bench/2026-09-26b/SL-0276-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0276-H0 :: HN ; PWE bench/2026-09-26b/SL-0263-H1.log,bench/2026-09-26b/SF-0276-H1.log ; DW bench/2026-09-26b/SL-0276-L.log
HOST bench/2026-09-26b/SL-0276-PG :: PG 234
HOST bench/2026-09-26b/SL-0276-P1 :: HP
CAP --out bench/2026-09-26b/SL-0276-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0276-H1 :: HN ; PWE bench/2026-09-26b/SL-0276-H0.log ; DW bench/2026-09-26b/SL-0276-H0.log
HOST bench/2026-09-26b/SL-0276-D :: BD pair bench/2026-09-26b/SL-0276-R0.log,bench/2026-09-26b/X-SL-0276-R0.log bench/2026-09-26b/SL-0276-R1.log,bench/2026-09-26b/X-SL-0276-R1.log --host bench/2026-09-26b/SL-0276-H0.log bench/2026-09-26b/SL-0276-H1.log --pre bench/2026-09-26b/SL-0276-P0.log bench/2026-09-26b/SL-0276-P1.log
CAP --out bench/2026-09-26b/SF-0277-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-0277-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-0277-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0276-L.log,bench/2026-09-26b/SL-0276-H1.log
HOST bench/2026-09-26b/SF-0277-P0 :: HP
CAP --out bench/2026-09-26b/SF-0277-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0277-H0 :: HN ; PWE bench/2026-09-26b/SF-0276-H1.log,bench/2026-09-26b/SL-0276-H1.log ; DW bench/2026-09-26b/SF-0277-L.log
HOST bench/2026-09-26b/SF-0277-PG :: PG 235
HOST bench/2026-09-26b/SF-0277-P1 :: HP
CAP --out bench/2026-09-26b/SF-0277-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-0277-H1 :: HN ; PWE bench/2026-09-26b/SF-0277-H0.log ; DW bench/2026-09-26b/SF-0277-H0.log
HOST bench/2026-09-26b/SF-0277-D :: BD pair bench/2026-09-26b/SF-0277-R0.log,bench/2026-09-26b/X-SF-0277-R0.log bench/2026-09-26b/SF-0277-R1.log,bench/2026-09-26b/X-SF-0277-R1.log --host bench/2026-09-26b/SF-0277-H0.log bench/2026-09-26b/SF-0277-H1.log --pre bench/2026-09-26b/SF-0277-P0.log bench/2026-09-26b/SF-0277-P1.log
CAP --out bench/2026-09-26b/SL-0277-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-0277-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-0277-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-0277-L.log,bench/2026-09-26b/SF-0277-H1.log
HOST bench/2026-09-26b/SL-0277-P0 :: HP
CAP --out bench/2026-09-26b/SL-0277-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0277-H0 :: HN ; PWE bench/2026-09-26b/SL-0276-H1.log,bench/2026-09-26b/SF-0277-H1.log ; DW bench/2026-09-26b/SL-0277-L.log
HOST bench/2026-09-26b/SL-0277-PG :: PG 235
HOST bench/2026-09-26b/SL-0277-P1 :: HP
CAP --out bench/2026-09-26b/SL-0277-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-0277-H1 :: HN ; PWE bench/2026-09-26b/SL-0277-H0.log ; DW bench/2026-09-26b/SL-0277-H0.log
HOST bench/2026-09-26b/SL-0277-D :: BD pair bench/2026-09-26b/SL-0277-R0.log,bench/2026-09-26b/X-SL-0277-R0.log bench/2026-09-26b/SL-0277-R1.log,bench/2026-09-26b/X-SL-0277-R1.log --host bench/2026-09-26b/SL-0277-H0.log bench/2026-09-26b/SL-0277-H1.log --pre bench/2026-09-26b/SL-0277-P0.log bench/2026-09-26b/SL-0277-P1.log
CAP --out bench/2026-09-26b/SF-1511-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-1511-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-1511-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-0277-L.log,bench/2026-09-26b/SL-0277-H1.log
HOST bench/2026-09-26b/SF-1511-P0 :: HP
CAP --out bench/2026-09-26b/SF-1511-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1511-H0 :: HN ; PWE bench/2026-09-26b/SF-0277-H1.log,bench/2026-09-26b/SL-0277-H1.log ; DW bench/2026-09-26b/SF-1511-L.log
HOST bench/2026-09-26b/SF-1511-PG :: PG 1469
HOST bench/2026-09-26b/SF-1511-P1 :: HP
CAP --out bench/2026-09-26b/SF-1511-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1511-H1 :: HN ; PWE bench/2026-09-26b/SF-1511-H0.log ; DW bench/2026-09-26b/SF-1511-H0.log
HOST bench/2026-09-26b/SF-1511-D :: BD pair bench/2026-09-26b/SF-1511-R0.log,bench/2026-09-26b/X-SF-1511-R0.log bench/2026-09-26b/SF-1511-R1.log,bench/2026-09-26b/X-SF-1511-R1.log --host bench/2026-09-26b/SF-1511-H0.log bench/2026-09-26b/SF-1511-H1.log --pre bench/2026-09-26b/SF-1511-P0.log bench/2026-09-26b/SF-1511-P1.log
CAP --out bench/2026-09-26b/SL-1511-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-1511-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-1511-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-1511-L.log,bench/2026-09-26b/SF-1511-H1.log
HOST bench/2026-09-26b/SL-1511-P0 :: HP
CAP --out bench/2026-09-26b/SL-1511-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1511-H0 :: HN ; PWE bench/2026-09-26b/SL-0277-H1.log,bench/2026-09-26b/SF-1511-H1.log ; DW bench/2026-09-26b/SL-1511-L.log
HOST bench/2026-09-26b/SL-1511-PG :: PG 1469
HOST bench/2026-09-26b/SL-1511-P1 :: HP
CAP --out bench/2026-09-26b/SL-1511-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1511-H1 :: HN ; PWE bench/2026-09-26b/SL-1511-H0.log ; DW bench/2026-09-26b/SL-1511-H0.log
HOST bench/2026-09-26b/SL-1511-D :: BD pair bench/2026-09-26b/SL-1511-R0.log,bench/2026-09-26b/X-SL-1511-R0.log bench/2026-09-26b/SL-1511-R1.log,bench/2026-09-26b/X-SL-1511-R1.log --host bench/2026-09-26b/SL-1511-H0.log bench/2026-09-26b/SL-1511-H1.log --pre bench/2026-09-26b/SL-1511-P0.log bench/2026-09-26b/SL-1511-P1.log
CAP --out bench/2026-09-26b/SF-1512-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-1512-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-1512-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-1511-L.log,bench/2026-09-26b/SL-1511-H1.log
HOST bench/2026-09-26b/SF-1512-P0 :: HP
CAP --out bench/2026-09-26b/SF-1512-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1512-H0 :: HN ; PWE bench/2026-09-26b/SF-1511-H1.log,bench/2026-09-26b/SL-1511-H1.log ; DW bench/2026-09-26b/SF-1512-L.log
HOST bench/2026-09-26b/SF-1512-PG :: PG 1470
HOST bench/2026-09-26b/SF-1512-P1 :: HP
CAP --out bench/2026-09-26b/SF-1512-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1512-H1 :: HN ; PWE bench/2026-09-26b/SF-1512-H0.log ; DW bench/2026-09-26b/SF-1512-H0.log
HOST bench/2026-09-26b/SF-1512-D :: BD pair bench/2026-09-26b/SF-1512-R0.log,bench/2026-09-26b/X-SF-1512-R0.log bench/2026-09-26b/SF-1512-R1.log,bench/2026-09-26b/X-SF-1512-R1.log --host bench/2026-09-26b/SF-1512-H0.log bench/2026-09-26b/SF-1512-H1.log --pre bench/2026-09-26b/SF-1512-P0.log bench/2026-09-26b/SF-1512-P1.log
CAP --out bench/2026-09-26b/SL-1512-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-1512-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-1512-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-1512-L.log,bench/2026-09-26b/SF-1512-H1.log
HOST bench/2026-09-26b/SL-1512-P0 :: HP
CAP --out bench/2026-09-26b/SL-1512-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1512-H0 :: HN ; PWE bench/2026-09-26b/SL-1511-H1.log,bench/2026-09-26b/SF-1512-H1.log ; DW bench/2026-09-26b/SL-1512-L.log
HOST bench/2026-09-26b/SL-1512-PG :: PG 1470
HOST bench/2026-09-26b/SL-1512-P1 :: HP
CAP --out bench/2026-09-26b/SL-1512-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1512-H1 :: HN ; PWE bench/2026-09-26b/SL-1512-H0.log ; DW bench/2026-09-26b/SL-1512-H0.log
HOST bench/2026-09-26b/SL-1512-D :: BD pair bench/2026-09-26b/SL-1512-R0.log,bench/2026-09-26b/X-SL-1512-R0.log bench/2026-09-26b/SL-1512-R1.log,bench/2026-09-26b/X-SL-1512-R1.log --host bench/2026-09-26b/SL-1512-H0.log bench/2026-09-26b/SL-1512-H1.log --pre bench/2026-09-26b/SL-1512-P0.log bench/2026-09-26b/SL-1512-P1.log
CAP --out bench/2026-09-26b/SF-1513-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-1513-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-1513-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-1512-L.log,bench/2026-09-26b/SL-1512-H1.log
HOST bench/2026-09-26b/SF-1513-P0 :: HP
CAP --out bench/2026-09-26b/SF-1513-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1513-H0 :: HN ; PWE bench/2026-09-26b/SF-1512-H1.log,bench/2026-09-26b/SL-1512-H1.log ; DW bench/2026-09-26b/SF-1513-L.log
HOST bench/2026-09-26b/SF-1513-PG :: PG 1471
HOST bench/2026-09-26b/SF-1513-P1 :: HP
CAP --out bench/2026-09-26b/SF-1513-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1513-H1 :: HN ; PWE bench/2026-09-26b/SF-1513-H0.log ; DW bench/2026-09-26b/SF-1513-H0.log
HOST bench/2026-09-26b/SF-1513-D :: BD pair bench/2026-09-26b/SF-1513-R0.log,bench/2026-09-26b/X-SF-1513-R0.log bench/2026-09-26b/SF-1513-R1.log,bench/2026-09-26b/X-SF-1513-R1.log --host bench/2026-09-26b/SF-1513-H0.log bench/2026-09-26b/SF-1513-H1.log --pre bench/2026-09-26b/SF-1513-P0.log bench/2026-09-26b/SF-1513-P1.log
CAP --out bench/2026-09-26b/SL-1513-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-1513-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-1513-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-1513-L.log,bench/2026-09-26b/SF-1513-H1.log
HOST bench/2026-09-26b/SL-1513-P0 :: HP
CAP --out bench/2026-09-26b/SL-1513-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1513-H0 :: HN ; PWE bench/2026-09-26b/SL-1512-H1.log,bench/2026-09-26b/SF-1513-H1.log ; DW bench/2026-09-26b/SL-1513-L.log
HOST bench/2026-09-26b/SL-1513-PG :: PG 1471
HOST bench/2026-09-26b/SL-1513-P1 :: HP
CAP --out bench/2026-09-26b/SL-1513-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1513-H1 :: HN ; PWE bench/2026-09-26b/SL-1513-H0.log ; DW bench/2026-09-26b/SL-1513-H0.log
HOST bench/2026-09-26b/SL-1513-D :: BD pair bench/2026-09-26b/SL-1513-R0.log,bench/2026-09-26b/X-SL-1513-R0.log bench/2026-09-26b/SL-1513-R1.log,bench/2026-09-26b/X-SL-1513-R1.log --host bench/2026-09-26b/SL-1513-H0.log bench/2026-09-26b/SL-1513-H1.log --pre bench/2026-09-26b/SL-1513-P0.log bench/2026-09-26b/SL-1513-P1.log
CAP --out bench/2026-09-26b/SF-1514-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SF-1514-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SF-1514-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SL-1513-L.log,bench/2026-09-26b/SL-1513-H1.log
HOST bench/2026-09-26b/SF-1514-P0 :: HP
CAP --out bench/2026-09-26b/SF-1514-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1514-H0 :: HN ; PWE bench/2026-09-26b/SF-1513-H1.log,bench/2026-09-26b/SL-1513-H1.log ; DW bench/2026-09-26b/SF-1514-L.log
HOST bench/2026-09-26b/SF-1514-PG :: PG 1472
HOST bench/2026-09-26b/SF-1514-P1 :: HP
CAP --out bench/2026-09-26b/SF-1514-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SF-1514-H1 :: HN ; PWE bench/2026-09-26b/SF-1514-H0.log ; DW bench/2026-09-26b/SF-1514-H0.log
HOST bench/2026-09-26b/SF-1514-D :: BD pair bench/2026-09-26b/SF-1514-R0.log,bench/2026-09-26b/X-SF-1514-R0.log bench/2026-09-26b/SF-1514-R1.log,bench/2026-09-26b/X-SF-1514-R1.log --host bench/2026-09-26b/SF-1514-H0.log bench/2026-09-26b/SF-1514-H1.log --pre bench/2026-09-26b/SF-1514-P0.log bench/2026-09-26b/SF-1514-P1.log
CAP --out bench/2026-09-26b/SL-1514-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/SL-1514-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/SL-1514-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/SF-1514-L.log,bench/2026-09-26b/SF-1514-H1.log
HOST bench/2026-09-26b/SL-1514-P0 :: HP
CAP --out bench/2026-09-26b/SL-1514-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1514-H0 :: HN ; PWE bench/2026-09-26b/SL-1513-H1.log,bench/2026-09-26b/SF-1514-H1.log ; DW bench/2026-09-26b/SL-1514-L.log
HOST bench/2026-09-26b/SL-1514-PG :: PG 1472
HOST bench/2026-09-26b/SL-1514-P1 :: HP
CAP --out bench/2026-09-26b/SL-1514-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/SL-1514-H1 :: HN ; PWE bench/2026-09-26b/SL-1514-H0.log ; DW bench/2026-09-26b/SL-1514-H0.log
HOST bench/2026-09-26b/SL-1514-D :: BD pair bench/2026-09-26b/SL-1514-R0.log,bench/2026-09-26b/X-SL-1514-R0.log bench/2026-09-26b/SL-1514-R1.log,bench/2026-09-26b/X-SL-1514-R1.log --host bench/2026-09-26b/SL-1514-H0.log bench/2026-09-26b/SL-1514-H1.log --pre bench/2026-09-26b/SL-1514-P0.log bench/2026-09-26b/SL-1514-P1.log
```

### The stack arms' capture stopped and windowed

```
HOST bench/2026-09-26b/W-TCPEX :: HN ; sudo -n pkill -INT -x tcpdump && sleep 1 ; HN
HOST bench/2026-09-26b/W-EWALL :: PWE none
HOST bench/2026-09-26b/W-EORD :: PWO /home/key/fwre-work/rebuild/s112/r6b3/pcap2/WE.pcap --if enxfc19286184c9 --tcpdump bench/2026-09-26b/W-TCPE.log --stop bench/2026-09-26b/W-TCPEX.log bench/2026-09-26b/E-F1-P0.log bench/2026-09-26b/E-F1-H0.log bench/2026-09-26b/E-F1-P1.log bench/2026-09-26b/E-F1-H1.log bench/2026-09-26b/E-L1-P0.log bench/2026-09-26b/E-L1-H0.log bench/2026-09-26b/E-L1-P1.log bench/2026-09-26b/E-L1-H1.log bench/2026-09-26b/E-F2-P0.log bench/2026-09-26b/E-F2-H0.log bench/2026-09-26b/E-F2-P1.log bench/2026-09-26b/E-F2-H1.log bench/2026-09-26b/SF-0060-P0.log bench/2026-09-26b/SF-0060-H0.log bench/2026-09-26b/SF-0060-P1.log bench/2026-09-26b/SF-0060-H1.log bench/2026-09-26b/SL-0060-P0.log bench/2026-09-26b/SL-0060-H0.log bench/2026-09-26b/SL-0060-P1.log bench/2026-09-26b/SL-0060-H1.log bench/2026-09-26b/SF-0061-P0.log bench/2026-09-26b/SF-0061-H0.log bench/2026-09-26b/SF-0061-P1.log bench/2026-09-26b/SF-0061-H1.log bench/2026-09-26b/SL-0061-P0.log bench/2026-09-26b/SL-0061-H0.log bench/2026-09-26b/SL-0061-P1.log bench/2026-09-26b/SL-0061-H1.log bench/2026-09-26b/SF-0062-P0.log bench/2026-09-26b/SF-0062-H0.log bench/2026-09-26b/SF-0062-P1.log bench/2026-09-26b/SF-0062-H1.log bench/2026-09-26b/SL-0062-P0.log bench/2026-09-26b/SL-0062-H0.log bench/2026-09-26b/SL-0062-P1.log bench/2026-09-26b/SL-0062-H1.log bench/2026-09-26b/SF-0063-P0.log bench/2026-09-26b/SF-0063-H0.log bench/2026-09-26b/SF-0063-P1.log bench/2026-09-26b/SF-0063-H1.log bench/2026-09-26b/SL-0063-P0.log bench/2026-09-26b/SL-0063-H0.log bench/2026-09-26b/SL-0063-P1.log bench/2026-09-26b/SL-0063-H1.log bench/2026-09-26b/SF-0263-P0.log bench/2026-09-26b/SF-0263-H0.log bench/2026-09-26b/SF-0263-P1.log bench/2026-09-26b/SF-0263-H1.log bench/2026-09-26b/SL-0263-P0.log bench/2026-09-26b/SL-0263-H0.log bench/2026-09-26b/SL-0263-P1.log bench/2026-09-26b/SL-0263-H1.log bench/2026-09-26b/SF-0276-P0.log bench/2026-09-26b/SF-0276-H0.log bench/2026-09-26b/SF-0276-P1.log bench/2026-09-26b/SF-0276-H1.log bench/2026-09-26b/SL-0276-P0.log bench/2026-09-26b/SL-0276-H0.log bench/2026-09-26b/SL-0276-P1.log bench/2026-09-26b/SL-0276-H1.log bench/2026-09-26b/SF-0277-P0.log bench/2026-09-26b/SF-0277-H0.log bench/2026-09-26b/SF-0277-P1.log bench/2026-09-26b/SF-0277-H1.log bench/2026-09-26b/SL-0277-P0.log bench/2026-09-26b/SL-0277-H0.log bench/2026-09-26b/SL-0277-P1.log bench/2026-09-26b/SL-0277-H1.log bench/2026-09-26b/SF-1511-P0.log bench/2026-09-26b/SF-1511-H0.log bench/2026-09-26b/SF-1511-P1.log bench/2026-09-26b/SF-1511-H1.log bench/2026-09-26b/SL-1511-P0.log bench/2026-09-26b/SL-1511-H0.log bench/2026-09-26b/SL-1511-P1.log bench/2026-09-26b/SL-1511-H1.log bench/2026-09-26b/SF-1512-P0.log bench/2026-09-26b/SF-1512-H0.log bench/2026-09-26b/SF-1512-P1.log bench/2026-09-26b/SF-1512-H1.log bench/2026-09-26b/SL-1512-P0.log bench/2026-09-26b/SL-1512-H0.log bench/2026-09-26b/SL-1512-P1.log bench/2026-09-26b/SL-1512-H1.log bench/2026-09-26b/SF-1513-P0.log bench/2026-09-26b/SF-1513-H0.log bench/2026-09-26b/SF-1513-P1.log bench/2026-09-26b/SF-1513-H1.log bench/2026-09-26b/SL-1513-P0.log bench/2026-09-26b/SL-1513-H0.log bench/2026-09-26b/SL-1513-P1.log bench/2026-09-26b/SL-1513-H1.log bench/2026-09-26b/SF-1514-P0.log bench/2026-09-26b/SF-1514-H0.log bench/2026-09-26b/SF-1514-P1.log bench/2026-09-26b/SF-1514-H1.log bench/2026-09-26b/SL-1514-P0.log bench/2026-09-26b/SL-1514-H0.log bench/2026-09-26b/SL-1514-P1.log bench/2026-09-26b/SL-1514-H1.log
```

### The sweeps' capture

```
HOST& bench/2026-09-26b/W-TCPS :: TDS WS.pcap
```

### The wire: the gate's control and map, the fix over every length, then 1.4 at 11

```
HOST bench/2026-09-26b/S-LIVE :: pgrep -xc tcpdump ; true
CAP --out bench/2026-09-26b/W-00-DN --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo irqon > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/W-00-K --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26b/W-00-P :: HP
CAP --out bench/2026-09-26b/W-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-00-H :: HN ; PWS none ; DW bench/2026-09-26b/B-00-H.log,bench/2026-09-26b/E-F1-L.log,bench/2026-09-26b/E-F1-H1.log,bench/2026-09-26b/E-L1-L.log,bench/2026-09-26b/E-L1-H1.log,bench/2026-09-26b/E-F2-L.log,bench/2026-09-26b/E-F2-H1.log,bench/2026-09-26b/SF-0060-L.log,bench/2026-09-26b/SF-0060-H1.log,bench/2026-09-26b/SL-0060-L.log,bench/2026-09-26b/SL-0060-H1.log,bench/2026-09-26b/SF-0061-L.log,bench/2026-09-26b/SF-0061-H1.log,bench/2026-09-26b/SL-0061-L.log,bench/2026-09-26b/SL-0061-H1.log,bench/2026-09-26b/SF-0062-L.log,bench/2026-09-26b/SF-0062-H1.log,bench/2026-09-26b/SL-0062-L.log,bench/2026-09-26b/SL-0062-H1.log,bench/2026-09-26b/SF-0063-L.log,bench/2026-09-26b/SF-0063-H1.log,bench/2026-09-26b/SL-0063-L.log,bench/2026-09-26b/SL-0063-H1.log,bench/2026-09-26b/SF-0263-L.log,bench/2026-09-26b/SF-0263-H1.log,bench/2026-09-26b/SL-0263-L.log,bench/2026-09-26b/SL-0263-H1.log,bench/2026-09-26b/SF-0276-L.log,bench/2026-09-26b/SF-0276-H1.log,bench/2026-09-26b/SL-0276-L.log,bench/2026-09-26b/SL-0276-H1.log,bench/2026-09-26b/SF-0277-L.log,bench/2026-09-26b/SF-0277-H1.log,bench/2026-09-26b/SL-0277-L.log,bench/2026-09-26b/SL-0277-H1.log,bench/2026-09-26b/SF-1511-L.log,bench/2026-09-26b/SF-1511-H1.log,bench/2026-09-26b/SL-1511-L.log,bench/2026-09-26b/SL-1511-H1.log,bench/2026-09-26b/SF-1512-L.log,bench/2026-09-26b/SF-1512-H1.log,bench/2026-09-26b/SL-1512-L.log,bench/2026-09-26b/SL-1512-H1.log,bench/2026-09-26b/SF-1513-L.log,bench/2026-09-26b/SF-1513-H1.log,bench/2026-09-26b/SL-1513-L.log,bench/2026-09-26b/SL-1513-H1.log,bench/2026-09-26b/SF-1514-L.log,bench/2026-09-26b/SF-1514-H1.log,bench/2026-09-26b/SL-1514-L.log,bench/2026-09-26b/SL-1514-H1.log
CAP --out bench/2026-09-26b/LB-P-0061 --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 61 61 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26b/LB-P-1511 --send 'echo sweep 1511 1511 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/LB-P-C :: SWC bench/2026-09-26b/LB-P-1511.log --setting rlxfw --probe 60
HOST bench/2026-09-26b/LB-P-P :: HP
CAP --out bench/2026-09-26b/LB-P-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/LB-P-H :: HN ; PWS bench/2026-09-26b/W-00-H.log ; DW bench/2026-09-26b/W-00-H.log
HOST bench/2026-09-26b/LB-P-D :: BD pair bench/2026-09-26b/W-00-R.log,bench/2026-09-26b/X-W-00-R.log bench/2026-09-26b/LB-P-R.log,bench/2026-09-26b/X-LB-P-R.log --host bench/2026-09-26b/W-00-H.log bench/2026-09-26b/LB-P-H.log --pre bench/2026-09-26b/W-00-P.log bench/2026-09-26b/LB-P-P.log
CAP --out bench/2026-09-26b/LB-V-V --send 'echo txlen vendor > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26b/LB-V-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26b/LB-V-C :: SWC bench/2026-09-26b/LB-V-S.log --setting vendor --probe 60
HOST bench/2026-09-26b/LB-V-P :: HP
CAP --out bench/2026-09-26b/LB-V-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/LB-V-H :: HN ; PWS bench/2026-09-26b/LB-P-H.log ; DW bench/2026-09-26b/LB-P-H.log
HOST bench/2026-09-26b/LB-V-D :: BD pair bench/2026-09-26b/LB-P-R.log,bench/2026-09-26b/X-LB-P-R.log bench/2026-09-26b/LB-V-R.log,bench/2026-09-26b/X-LB-V-R.log --host bench/2026-09-26b/LB-P-H.log bench/2026-09-26b/LB-V-H.log --pre bench/2026-09-26b/LB-P-P.log bench/2026-09-26b/LB-V-P.log
CAP --out bench/2026-09-26b/W-00 --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26b/W-1a-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 423 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
HOST bench/2026-09-26b/W-1a-P :: HP
CAP --out bench/2026-09-26b/W-1a-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-1a-H :: HN ; PWS bench/2026-09-26b/LB-V-H.log ; DW bench/2026-09-26b/LB-V-H.log
HOST bench/2026-09-26b/W-1a-D :: BD pair bench/2026-09-26b/LB-V-R.log,bench/2026-09-26b/X-LB-V-R.log bench/2026-09-26b/W-1a-R.log,bench/2026-09-26b/X-W-1a-R.log --host bench/2026-09-26b/LB-V-H.log bench/2026-09-26b/W-1a-H.log --pre bench/2026-09-26b/LB-V-P.log bench/2026-09-26b/W-1a-P.log
CAP --out bench/2026-09-26b/W-1b-S --send 'echo sweep 424 787 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
HOST bench/2026-09-26b/W-1b-P :: HP
CAP --out bench/2026-09-26b/W-1b-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-1b-H :: HN ; PWS bench/2026-09-26b/W-1a-H.log ; DW bench/2026-09-26b/W-1a-H.log
HOST bench/2026-09-26b/W-1b-D :: BD pair bench/2026-09-26b/W-1a-R.log,bench/2026-09-26b/X-W-1a-R.log bench/2026-09-26b/W-1b-R.log,bench/2026-09-26b/X-W-1b-R.log --host bench/2026-09-26b/W-1a-H.log bench/2026-09-26b/W-1b-H.log --pre bench/2026-09-26b/W-1a-P.log bench/2026-09-26b/W-1b-P.log
CAP --out bench/2026-09-26b/W-1c-S --send 'echo sweep 788 1151 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
HOST bench/2026-09-26b/W-1c-P :: HP
CAP --out bench/2026-09-26b/W-1c-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-1c-H :: HN ; PWS bench/2026-09-26b/W-1b-H.log ; DW bench/2026-09-26b/W-1b-H.log
HOST bench/2026-09-26b/W-1c-D :: BD pair bench/2026-09-26b/W-1b-R.log,bench/2026-09-26b/X-W-1b-R.log bench/2026-09-26b/W-1c-R.log,bench/2026-09-26b/X-W-1c-R.log --host bench/2026-09-26b/W-1b-H.log bench/2026-09-26b/W-1c-H.log --pre bench/2026-09-26b/W-1b-P.log bench/2026-09-26b/W-1c-P.log
CAP --out bench/2026-09-26b/W-1d-S --send 'echo sweep 1152 1514 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
HOST bench/2026-09-26b/W-1d-P :: HP
CAP --out bench/2026-09-26b/W-1d-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-1d-H :: HN ; PWS bench/2026-09-26b/W-1c-H.log ; DW bench/2026-09-26b/W-1c-H.log
HOST bench/2026-09-26b/W-1d-D :: BD pair bench/2026-09-26b/W-1c-R.log,bench/2026-09-26b/X-W-1c-R.log bench/2026-09-26b/W-1d-R.log,bench/2026-09-26b/X-W-1d-R.log --host bench/2026-09-26b/W-1c-H.log bench/2026-09-26b/W-1d-H.log --pre bench/2026-09-26b/W-1c-P.log bench/2026-09-26b/W-1d-P.log
CAP --out bench/2026-09-26b/W-2-V --send 'echo txlen rlxfw > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26b/W-2-EP --send 'echo sweep 64 65 60 wire | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26b/W-2-0060-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 60 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0060-P :: HP
CAP --out bench/2026-09-26b/W-2-0060-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0060-H :: HN ; PWS bench/2026-09-26b/W-00-H.log,bench/2026-09-26b/LB-V-H.log,bench/2026-09-26b/W-1a-H.log,bench/2026-09-26b/W-1b-H.log,bench/2026-09-26b/W-1c-H.log,bench/2026-09-26b/W-1d-H.log ; DW bench/2026-09-26b/W-00-H.log,bench/2026-09-26b/LB-V-H.log,bench/2026-09-26b/W-1a-H.log,bench/2026-09-26b/W-1b-H.log,bench/2026-09-26b/W-1c-H.log,bench/2026-09-26b/W-1d-H.log
HOST bench/2026-09-26b/W-2-0060-D :: BD pair bench/2026-09-26b/W-00-R.log,bench/2026-09-26b/X-W-00-R.log,bench/2026-09-26b/LB-V-R.log,bench/2026-09-26b/X-LB-V-R.log,bench/2026-09-26b/W-1a-R.log,bench/2026-09-26b/X-W-1a-R.log,bench/2026-09-26b/W-1b-R.log,bench/2026-09-26b/X-W-1b-R.log,bench/2026-09-26b/W-1c-R.log,bench/2026-09-26b/X-W-1c-R.log,bench/2026-09-26b/W-1d-R.log,bench/2026-09-26b/X-W-1d-R.log bench/2026-09-26b/W-2-0060-R.log,bench/2026-09-26b/X-W-2-0060-R.log --host bench/2026-09-26b/W-00-H.log,bench/2026-09-26b/LB-V-H.log,bench/2026-09-26b/W-1a-H.log,bench/2026-09-26b/W-1b-H.log,bench/2026-09-26b/W-1c-H.log,bench/2026-09-26b/W-1d-H.log bench/2026-09-26b/W-2-0060-H.log --pre bench/2026-09-26b/W-00-P.log,bench/2026-09-26b/LB-V-P.log,bench/2026-09-26b/W-1a-P.log,bench/2026-09-26b/W-1b-P.log,bench/2026-09-26b/W-1c-P.log,bench/2026-09-26b/W-1d-P.log bench/2026-09-26b/W-2-0060-P.log
CAP --out bench/2026-09-26b/W-2-0061-S --send 'echo sweep 61 61 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0061-P :: HP
CAP --out bench/2026-09-26b/W-2-0061-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0061-H :: HN ; PWS bench/2026-09-26b/W-2-0060-H.log ; DW bench/2026-09-26b/W-2-0060-H.log
HOST bench/2026-09-26b/W-2-0061-D :: BD pair bench/2026-09-26b/W-2-0060-R.log,bench/2026-09-26b/X-W-2-0060-R.log bench/2026-09-26b/W-2-0061-R.log,bench/2026-09-26b/X-W-2-0061-R.log --host bench/2026-09-26b/W-2-0060-H.log bench/2026-09-26b/W-2-0061-H.log --pre bench/2026-09-26b/W-2-0060-P.log bench/2026-09-26b/W-2-0061-P.log
CAP --out bench/2026-09-26b/W-2-0062-S --send 'echo sweep 62 62 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0062-P :: HP
CAP --out bench/2026-09-26b/W-2-0062-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0062-H :: HN ; PWS bench/2026-09-26b/W-2-0061-H.log ; DW bench/2026-09-26b/W-2-0061-H.log
HOST bench/2026-09-26b/W-2-0062-D :: BD pair bench/2026-09-26b/W-2-0061-R.log,bench/2026-09-26b/X-W-2-0061-R.log bench/2026-09-26b/W-2-0062-R.log,bench/2026-09-26b/X-W-2-0062-R.log --host bench/2026-09-26b/W-2-0061-H.log bench/2026-09-26b/W-2-0062-H.log --pre bench/2026-09-26b/W-2-0061-P.log bench/2026-09-26b/W-2-0062-P.log
CAP --out bench/2026-09-26b/W-2-0063-S --send 'echo sweep 63 63 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0063-P :: HP
CAP --out bench/2026-09-26b/W-2-0063-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0063-H :: HN ; PWS bench/2026-09-26b/W-2-0062-H.log ; DW bench/2026-09-26b/W-2-0062-H.log
HOST bench/2026-09-26b/W-2-0063-D :: BD pair bench/2026-09-26b/W-2-0062-R.log,bench/2026-09-26b/X-W-2-0062-R.log bench/2026-09-26b/W-2-0063-R.log,bench/2026-09-26b/X-W-2-0063-R.log --host bench/2026-09-26b/W-2-0062-H.log bench/2026-09-26b/W-2-0063-H.log --pre bench/2026-09-26b/W-2-0062-P.log bench/2026-09-26b/W-2-0063-P.log
CAP --out bench/2026-09-26b/W-2-0263-S --send 'echo sweep 263 263 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0263-P :: HP
CAP --out bench/2026-09-26b/W-2-0263-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0263-H :: HN ; PWS bench/2026-09-26b/W-2-0063-H.log ; DW bench/2026-09-26b/W-2-0063-H.log
HOST bench/2026-09-26b/W-2-0263-D :: BD pair bench/2026-09-26b/W-2-0063-R.log,bench/2026-09-26b/X-W-2-0063-R.log bench/2026-09-26b/W-2-0263-R.log,bench/2026-09-26b/X-W-2-0263-R.log --host bench/2026-09-26b/W-2-0063-H.log bench/2026-09-26b/W-2-0263-H.log --pre bench/2026-09-26b/W-2-0063-P.log bench/2026-09-26b/W-2-0263-P.log
CAP --out bench/2026-09-26b/W-2-0276-S --send 'echo sweep 276 276 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0276-P :: HP
CAP --out bench/2026-09-26b/W-2-0276-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0276-H :: HN ; PWS bench/2026-09-26b/W-2-0263-H.log ; DW bench/2026-09-26b/W-2-0263-H.log
HOST bench/2026-09-26b/W-2-0276-D :: BD pair bench/2026-09-26b/W-2-0263-R.log,bench/2026-09-26b/X-W-2-0263-R.log bench/2026-09-26b/W-2-0276-R.log,bench/2026-09-26b/X-W-2-0276-R.log --host bench/2026-09-26b/W-2-0263-H.log bench/2026-09-26b/W-2-0276-H.log --pre bench/2026-09-26b/W-2-0263-P.log bench/2026-09-26b/W-2-0276-P.log
CAP --out bench/2026-09-26b/W-2-0277-S --send 'echo sweep 277 277 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0277-P :: HP
CAP --out bench/2026-09-26b/W-2-0277-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-0277-H :: HN ; PWS bench/2026-09-26b/W-2-0276-H.log ; DW bench/2026-09-26b/W-2-0276-H.log
HOST bench/2026-09-26b/W-2-0277-D :: BD pair bench/2026-09-26b/W-2-0276-R.log,bench/2026-09-26b/X-W-2-0276-R.log bench/2026-09-26b/W-2-0277-R.log,bench/2026-09-26b/X-W-2-0277-R.log --host bench/2026-09-26b/W-2-0276-H.log bench/2026-09-26b/W-2-0277-H.log --pre bench/2026-09-26b/W-2-0276-P.log bench/2026-09-26b/W-2-0277-P.log
CAP --out bench/2026-09-26b/W-2-1511-S --send 'echo sweep 1511 1511 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1511-P :: HP
CAP --out bench/2026-09-26b/W-2-1511-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1511-H :: HN ; PWS bench/2026-09-26b/W-2-0277-H.log ; DW bench/2026-09-26b/W-2-0277-H.log
HOST bench/2026-09-26b/W-2-1511-D :: BD pair bench/2026-09-26b/W-2-0277-R.log,bench/2026-09-26b/X-W-2-0277-R.log bench/2026-09-26b/W-2-1511-R.log,bench/2026-09-26b/X-W-2-1511-R.log --host bench/2026-09-26b/W-2-0277-H.log bench/2026-09-26b/W-2-1511-H.log --pre bench/2026-09-26b/W-2-0277-P.log bench/2026-09-26b/W-2-1511-P.log
CAP --out bench/2026-09-26b/W-2-1512-S --send 'echo sweep 1512 1512 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1512-P :: HP
CAP --out bench/2026-09-26b/W-2-1512-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1512-H :: HN ; PWS bench/2026-09-26b/W-2-1511-H.log ; DW bench/2026-09-26b/W-2-1511-H.log
HOST bench/2026-09-26b/W-2-1512-D :: BD pair bench/2026-09-26b/W-2-1511-R.log,bench/2026-09-26b/X-W-2-1511-R.log bench/2026-09-26b/W-2-1512-R.log,bench/2026-09-26b/X-W-2-1512-R.log --host bench/2026-09-26b/W-2-1511-H.log bench/2026-09-26b/W-2-1512-H.log --pre bench/2026-09-26b/W-2-1511-P.log bench/2026-09-26b/W-2-1512-P.log
CAP --out bench/2026-09-26b/W-2-1513-S --send 'echo sweep 1513 1513 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1513-P :: HP
CAP --out bench/2026-09-26b/W-2-1513-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1513-H :: HN ; PWS bench/2026-09-26b/W-2-1512-H.log ; DW bench/2026-09-26b/W-2-1512-H.log
HOST bench/2026-09-26b/W-2-1513-D :: BD pair bench/2026-09-26b/W-2-1512-R.log,bench/2026-09-26b/X-W-2-1512-R.log bench/2026-09-26b/W-2-1513-R.log,bench/2026-09-26b/X-W-2-1513-R.log --host bench/2026-09-26b/W-2-1512-H.log bench/2026-09-26b/W-2-1513-H.log --pre bench/2026-09-26b/W-2-1512-P.log bench/2026-09-26b/W-2-1513-P.log
CAP --out bench/2026-09-26b/W-2-1514-S --send 'echo sweep 1514 1514 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1514-P :: HP
CAP --out bench/2026-09-26b/W-2-1514-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-2-1514-H :: HN ; PWS bench/2026-09-26b/W-2-1513-H.log ; DW bench/2026-09-26b/W-2-1513-H.log
HOST bench/2026-09-26b/W-2-1514-D :: BD pair bench/2026-09-26b/W-2-1513-R.log,bench/2026-09-26b/X-W-2-1513-R.log bench/2026-09-26b/W-2-1514-R.log,bench/2026-09-26b/X-W-2-1514-R.log --host bench/2026-09-26b/W-2-1513-H.log bench/2026-09-26b/W-2-1514-H.log --pre bench/2026-09-26b/W-2-1513-P.log bench/2026-09-26b/W-2-1514-P.log
```

### The sweeps' capture stopped and windowed

```
HOST bench/2026-09-26b/W-TCPSX :: HN ; sudo -n pkill -INT -x tcpdump && sleep 1 ; HN
HOST bench/2026-09-26b/W-SWALL :: PWS none
HOST bench/2026-09-26b/W-SORD :: PWO /home/key/fwre-work/rebuild/s112/r6b3/pcap2/WS.pcap --if enxfc19286184c9 --tcpdump bench/2026-09-26b/W-TCPS.log --stop bench/2026-09-26b/W-TCPSX.log bench/2026-09-26b/W-00-P.log bench/2026-09-26b/W-00-H.log bench/2026-09-26b/LB-P-P.log bench/2026-09-26b/LB-P-H.log bench/2026-09-26b/LB-V-P.log bench/2026-09-26b/LB-V-H.log bench/2026-09-26b/W-1a-P.log bench/2026-09-26b/W-1a-H.log bench/2026-09-26b/W-1b-P.log bench/2026-09-26b/W-1b-H.log bench/2026-09-26b/W-1c-P.log bench/2026-09-26b/W-1c-H.log bench/2026-09-26b/W-1d-P.log bench/2026-09-26b/W-1d-H.log bench/2026-09-26b/W-2-0060-P.log bench/2026-09-26b/W-2-0060-H.log bench/2026-09-26b/W-2-0061-P.log bench/2026-09-26b/W-2-0061-H.log bench/2026-09-26b/W-2-0062-P.log bench/2026-09-26b/W-2-0062-H.log bench/2026-09-26b/W-2-0063-P.log bench/2026-09-26b/W-2-0063-H.log bench/2026-09-26b/W-2-0263-P.log bench/2026-09-26b/W-2-0263-H.log bench/2026-09-26b/W-2-0276-P.log bench/2026-09-26b/W-2-0276-H.log bench/2026-09-26b/W-2-0277-P.log bench/2026-09-26b/W-2-0277-H.log bench/2026-09-26b/W-2-1511-P.log bench/2026-09-26b/W-2-1511-H.log bench/2026-09-26b/W-2-1512-P.log bench/2026-09-26b/W-2-1512-H.log bench/2026-09-26b/W-2-1513-P.log bench/2026-09-26b/W-2-1513-H.log bench/2026-09-26b/W-2-1514-P.log bench/2026-09-26b/W-2-1514-H.log
```

### `rlx0` back up at 1.4, after the sweeps' capture has stopped

```
CAP --out bench/2026-09-26b/W-9-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/W-9-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/W-9-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/W-2-1514-H.log
HOST bench/2026-09-26b/W-9-P :: HP
CAP --out bench/2026-09-26b/W-9-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/W-9-H :: HN ; DW bench/2026-09-26b/W-9-L.log
```

### `D3`: twelve trials at the fix, then 1.4's control

```
CAP --out bench/2026-09-26b/D3-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/D3-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/D3-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/W-9-H.log
HOST bench/2026-09-26b/D3-00-P :: HP
CAP --out bench/2026-09-26b/D3-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-00-H :: HN ; DW bench/2026-09-26b/D3-L.log
HOST bench/2026-09-26b/D3-TR1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-00-H.log
CAP --out bench/2026-09-26b/D3-TR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-26b/D3-TR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TR1-P :: HP
CAP --out bench/2026-09-26b/D3-TR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TR1-H :: HN ; DW bench/2026-09-26b/D3-TR1-L.log
HOST bench/2026-09-26b/D3-TR1-D :: BD pair bench/2026-09-26b/D3-00-R.log,bench/2026-09-26b/X-D3-00-R.log bench/2026-09-26b/D3-TR1-R.log,bench/2026-09-26b/X-D3-TR1-R.log --host bench/2026-09-26b/D3-00-H.log bench/2026-09-26b/D3-TR1-H.log --pre bench/2026-09-26b/D3-00-P.log bench/2026-09-26b/D3-TR1-P.log
HOST bench/2026-09-26b/D3-TR1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TR1-S1.log
HOST bench/2026-09-26b/D3-TR1-SN :: BD snmp bench/2026-09-26b/D3-TR1-S0.log bench/2026-09-26b/D3-TR1-S1.log
HOST bench/2026-09-26b/D3-TR1-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-TR1-S1.log bench/2026-09-26b/D3-TR1.log
HOST bench/2026-09-26b/D3-TR2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TR1-L.log,bench/2026-09-26b/D3-TR1-H.log
CAP --out bench/2026-09-26b/D3-TR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-26b/D3-TR2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr2.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TR2-P :: HP
CAP --out bench/2026-09-26b/D3-TR2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TR2-H :: HN ; DW bench/2026-09-26b/D3-TR2-L.log
HOST bench/2026-09-26b/D3-TR2-D :: BD pair bench/2026-09-26b/D3-00-R.log,bench/2026-09-26b/X-D3-00-R.log,bench/2026-09-26b/D3-TR1-R.log,bench/2026-09-26b/X-D3-TR1-R.log bench/2026-09-26b/D3-TR2-R.log,bench/2026-09-26b/X-D3-TR2-R.log --host bench/2026-09-26b/D3-00-H.log,bench/2026-09-26b/D3-TR1-H.log bench/2026-09-26b/D3-TR2-H.log --pre bench/2026-09-26b/D3-00-P.log,bench/2026-09-26b/D3-TR1-P.log bench/2026-09-26b/D3-TR2-P.log
HOST bench/2026-09-26b/D3-TR2-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TR2-S1.log
HOST bench/2026-09-26b/D3-TR2-SN :: BD snmp bench/2026-09-26b/D3-TR2-S0.log bench/2026-09-26b/D3-TR2-S1.log
HOST bench/2026-09-26b/D3-TR2-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-TR2-S1.log bench/2026-09-26b/D3-TR2.log
HOST bench/2026-09-26b/D3-TR3-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TR2-L.log,bench/2026-09-26b/D3-TR2-H.log
CAP --out bench/2026-09-26b/D3-TR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/tr3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m
CAP --out bench/2026-09-26b/D3-TR3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/tr3.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TR3-P :: HP
CAP --out bench/2026-09-26b/D3-TR3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TR3-H :: HN ; DW bench/2026-09-26b/D3-TR3-L.log
HOST bench/2026-09-26b/D3-TR3-D :: BD pair bench/2026-09-26b/D3-TR1-R.log,bench/2026-09-26b/X-D3-TR1-R.log,bench/2026-09-26b/D3-TR2-R.log,bench/2026-09-26b/X-D3-TR2-R.log bench/2026-09-26b/D3-TR3-R.log,bench/2026-09-26b/X-D3-TR3-R.log --host bench/2026-09-26b/D3-TR1-H.log,bench/2026-09-26b/D3-TR2-H.log bench/2026-09-26b/D3-TR3-H.log --pre bench/2026-09-26b/D3-TR1-P.log,bench/2026-09-26b/D3-TR2-P.log bench/2026-09-26b/D3-TR3-P.log
HOST bench/2026-09-26b/D3-TR3-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TR3-S1.log
HOST bench/2026-09-26b/D3-TR3-SN :: BD snmp bench/2026-09-26b/D3-TR3-S0.log bench/2026-09-26b/D3-TR3-S1.log
HOST bench/2026-09-26b/D3-TR3-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-TR3-S1.log bench/2026-09-26b/D3-TR3.log
HOST bench/2026-09-26b/D3-TS1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TR3-L.log,bench/2026-09-26b/D3-TR3-H.log
CAP --out bench/2026-09-26b/D3-TS1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-26b/D3-TS1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TS1-P :: HP
CAP --out bench/2026-09-26b/D3-TS1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TS1-H :: HN ; DW bench/2026-09-26b/D3-TS1-L.log
HOST bench/2026-09-26b/D3-TS1-D :: BD pair bench/2026-09-26b/D3-TR2-R.log,bench/2026-09-26b/X-D3-TR2-R.log,bench/2026-09-26b/D3-TR3-R.log,bench/2026-09-26b/X-D3-TR3-R.log bench/2026-09-26b/D3-TS1-R.log,bench/2026-09-26b/X-D3-TS1-R.log --host bench/2026-09-26b/D3-TR2-H.log,bench/2026-09-26b/D3-TR3-H.log bench/2026-09-26b/D3-TS1-H.log --pre bench/2026-09-26b/D3-TR2-P.log,bench/2026-09-26b/D3-TR3-P.log bench/2026-09-26b/D3-TS1-P.log
HOST bench/2026-09-26b/D3-TS1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TS1-S1.log
HOST bench/2026-09-26b/D3-TS1-SN :: BD snmp bench/2026-09-26b/D3-TS1-S0.log bench/2026-09-26b/D3-TS1-S1.log
HOST bench/2026-09-26b/D3-TS2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TS1-L.log,bench/2026-09-26b/D3-TS1-H.log
CAP --out bench/2026-09-26b/D3-TS2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TS2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-26b/D3-TS2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts2.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TS2-P :: HP
CAP --out bench/2026-09-26b/D3-TS2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TS2-H :: HN ; DW bench/2026-09-26b/D3-TS2-L.log
HOST bench/2026-09-26b/D3-TS2-D :: BD pair bench/2026-09-26b/D3-TR3-R.log,bench/2026-09-26b/X-D3-TR3-R.log,bench/2026-09-26b/D3-TS1-R.log,bench/2026-09-26b/X-D3-TS1-R.log bench/2026-09-26b/D3-TS2-R.log,bench/2026-09-26b/X-D3-TS2-R.log --host bench/2026-09-26b/D3-TR3-H.log,bench/2026-09-26b/D3-TS1-H.log bench/2026-09-26b/D3-TS2-H.log --pre bench/2026-09-26b/D3-TR3-P.log,bench/2026-09-26b/D3-TS1-P.log bench/2026-09-26b/D3-TS2-P.log
HOST bench/2026-09-26b/D3-TS2-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TS2-S1.log
HOST bench/2026-09-26b/D3-TS2-SN :: BD snmp bench/2026-09-26b/D3-TS2-S0.log bench/2026-09-26b/D3-TS2-S1.log
HOST bench/2026-09-26b/D3-TS3-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TS2-L.log,bench/2026-09-26b/D3-TS2-H.log
CAP --out bench/2026-09-26b/D3-TS3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ts3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-TS3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 5 -f m -R
CAP --out bench/2026-09-26b/D3-TS3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ts3.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-TS3-P :: HP
CAP --out bench/2026-09-26b/D3-TS3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-TS3-H :: HN ; DW bench/2026-09-26b/D3-TS3-L.log
HOST bench/2026-09-26b/D3-TS3-D :: BD pair bench/2026-09-26b/D3-TS1-R.log,bench/2026-09-26b/X-D3-TS1-R.log,bench/2026-09-26b/D3-TS2-R.log,bench/2026-09-26b/X-D3-TS2-R.log bench/2026-09-26b/D3-TS3-R.log,bench/2026-09-26b/X-D3-TS3-R.log --host bench/2026-09-26b/D3-TS1-H.log,bench/2026-09-26b/D3-TS2-H.log bench/2026-09-26b/D3-TS3-H.log --pre bench/2026-09-26b/D3-TS1-P.log,bench/2026-09-26b/D3-TS2-P.log bench/2026-09-26b/D3-TS3-P.log
HOST bench/2026-09-26b/D3-TS3-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-TS3-S1.log
HOST bench/2026-09-26b/D3-TS3-SN :: BD snmp bench/2026-09-26b/D3-TS3-S0.log bench/2026-09-26b/D3-TS3-S1.log
HOST bench/2026-09-26b/D3-UR1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-TS3-L.log,bench/2026-09-26b/D3-TS3-H.log
CAP --out bench/2026-09-26b/D3-UR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-UR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-26b/D3-UR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-UR1-P :: HP
CAP --out bench/2026-09-26b/D3-UR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-UR1-H :: HN ; DW bench/2026-09-26b/D3-UR1-L.log
HOST bench/2026-09-26b/D3-UR1-D :: BD pair bench/2026-09-26b/D3-TS2-R.log,bench/2026-09-26b/X-D3-TS2-R.log,bench/2026-09-26b/D3-TS3-R.log,bench/2026-09-26b/X-D3-TS3-R.log bench/2026-09-26b/D3-UR1-R.log,bench/2026-09-26b/X-D3-UR1-R.log --host bench/2026-09-26b/D3-TS2-H.log,bench/2026-09-26b/D3-TS3-H.log bench/2026-09-26b/D3-UR1-H.log --pre bench/2026-09-26b/D3-TS2-P.log,bench/2026-09-26b/D3-TS3-P.log bench/2026-09-26b/D3-UR1-P.log
HOST bench/2026-09-26b/D3-UR1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-UR1-S1.log
HOST bench/2026-09-26b/D3-UR1-SN :: BD snmp bench/2026-09-26b/D3-UR1-S0.log bench/2026-09-26b/D3-UR1-S1.log
HOST bench/2026-09-26b/D3-UR1-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-UR1-S1.log bench/2026-09-26b/D3-UR1.log
HOST bench/2026-09-26b/D3-UR2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-UR1-L.log,bench/2026-09-26b/D3-UR1-H.log
CAP --out bench/2026-09-26b/D3-UR2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-UR2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-26b/D3-UR2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur2.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-UR2-P :: HP
CAP --out bench/2026-09-26b/D3-UR2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-UR2-H :: HN ; DW bench/2026-09-26b/D3-UR2-L.log
HOST bench/2026-09-26b/D3-UR2-D :: BD pair bench/2026-09-26b/D3-TS3-R.log,bench/2026-09-26b/X-D3-TS3-R.log,bench/2026-09-26b/D3-UR1-R.log,bench/2026-09-26b/X-D3-UR1-R.log bench/2026-09-26b/D3-UR2-R.log,bench/2026-09-26b/X-D3-UR2-R.log --host bench/2026-09-26b/D3-TS3-H.log,bench/2026-09-26b/D3-UR1-H.log bench/2026-09-26b/D3-UR2-H.log --pre bench/2026-09-26b/D3-TS3-P.log,bench/2026-09-26b/D3-UR1-P.log bench/2026-09-26b/D3-UR2-P.log
HOST bench/2026-09-26b/D3-UR2-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-UR2-S1.log
HOST bench/2026-09-26b/D3-UR2-SN :: BD snmp bench/2026-09-26b/D3-UR2-S0.log bench/2026-09-26b/D3-UR2-S1.log
HOST bench/2026-09-26b/D3-UR2-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-UR2-S1.log bench/2026-09-26b/D3-UR2.log
HOST bench/2026-09-26b/D3-UR3-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-UR2-L.log,bench/2026-09-26b/D3-UR2-H.log
CAP --out bench/2026-09-26b/D3-UR3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/ur3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-UR3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-26b/D3-UR3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/ur3.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-UR3-P :: HP
CAP --out bench/2026-09-26b/D3-UR3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-UR3-H :: HN ; DW bench/2026-09-26b/D3-UR3-L.log
HOST bench/2026-09-26b/D3-UR3-D :: BD pair bench/2026-09-26b/D3-UR1-R.log,bench/2026-09-26b/X-D3-UR1-R.log,bench/2026-09-26b/D3-UR2-R.log,bench/2026-09-26b/X-D3-UR2-R.log bench/2026-09-26b/D3-UR3-R.log,bench/2026-09-26b/X-D3-UR3-R.log --host bench/2026-09-26b/D3-UR1-H.log,bench/2026-09-26b/D3-UR2-H.log bench/2026-09-26b/D3-UR3-H.log --pre bench/2026-09-26b/D3-UR1-P.log,bench/2026-09-26b/D3-UR2-P.log bench/2026-09-26b/D3-UR3-P.log
HOST bench/2026-09-26b/D3-UR3-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-UR3-S1.log
HOST bench/2026-09-26b/D3-UR3-SN :: BD snmp bench/2026-09-26b/D3-UR3-S0.log bench/2026-09-26b/D3-UR3-S1.log
HOST bench/2026-09-26b/D3-UR3-IC :: ILG compare --duration 30 bench/2026-09-26b/D3-UR3-S1.log bench/2026-09-26b/D3-UR3.log
HOST bench/2026-09-26b/D3-US1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-UR3-L.log,bench/2026-09-26b/D3-UR3-H.log
CAP --out bench/2026-09-26b/D3-US1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-US1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-26b/D3-US1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-US1-P :: HP
CAP --out bench/2026-09-26b/D3-US1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-US1-H :: HN ; DW bench/2026-09-26b/D3-US1-L.log
HOST bench/2026-09-26b/D3-US1-D :: BD pair bench/2026-09-26b/D3-UR2-R.log,bench/2026-09-26b/X-D3-UR2-R.log,bench/2026-09-26b/D3-UR3-R.log,bench/2026-09-26b/X-D3-UR3-R.log bench/2026-09-26b/D3-US1-R.log,bench/2026-09-26b/X-D3-US1-R.log --host bench/2026-09-26b/D3-UR2-H.log,bench/2026-09-26b/D3-UR3-H.log bench/2026-09-26b/D3-US1-H.log --pre bench/2026-09-26b/D3-UR2-P.log,bench/2026-09-26b/D3-UR3-P.log bench/2026-09-26b/D3-US1-P.log
HOST bench/2026-09-26b/D3-US1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-US1-S1.log
HOST bench/2026-09-26b/D3-US1-SN :: BD snmp bench/2026-09-26b/D3-US1-S0.log bench/2026-09-26b/D3-US1-S1.log
HOST bench/2026-09-26b/D3-US2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-US1-L.log,bench/2026-09-26b/D3-US1-H.log
CAP --out bench/2026-09-26b/D3-US2-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us2.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-US2 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-26b/D3-US2-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us2.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-US2-P :: HP
CAP --out bench/2026-09-26b/D3-US2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-US2-H :: HN ; DW bench/2026-09-26b/D3-US2-L.log
HOST bench/2026-09-26b/D3-US2-D :: BD pair bench/2026-09-26b/D3-UR3-R.log,bench/2026-09-26b/X-D3-UR3-R.log,bench/2026-09-26b/D3-US1-R.log,bench/2026-09-26b/X-D3-US1-R.log bench/2026-09-26b/D3-US2-R.log,bench/2026-09-26b/X-D3-US2-R.log --host bench/2026-09-26b/D3-UR3-H.log,bench/2026-09-26b/D3-US1-H.log bench/2026-09-26b/D3-US2-H.log --pre bench/2026-09-26b/D3-UR3-P.log,bench/2026-09-26b/D3-US1-P.log bench/2026-09-26b/D3-US2-P.log
HOST bench/2026-09-26b/D3-US2-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-US2-S1.log
HOST bench/2026-09-26b/D3-US2-SN :: BD snmp bench/2026-09-26b/D3-US2-S0.log bench/2026-09-26b/D3-US2-S1.log
HOST bench/2026-09-26b/D3-US3-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-US2-L.log,bench/2026-09-26b/D3-US2-H.log
CAP --out bench/2026-09-26b/D3-US3-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/us3.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-US3 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-26b/D3-US3-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/us3.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-US3-P :: HP
CAP --out bench/2026-09-26b/D3-US3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-US3-H :: HN ; DW bench/2026-09-26b/D3-US3-L.log
HOST bench/2026-09-26b/D3-US3-D :: BD pair bench/2026-09-26b/D3-US1-R.log,bench/2026-09-26b/X-D3-US1-R.log,bench/2026-09-26b/D3-US2-R.log,bench/2026-09-26b/X-D3-US2-R.log bench/2026-09-26b/D3-US3-R.log,bench/2026-09-26b/X-D3-US3-R.log --host bench/2026-09-26b/D3-US1-H.log,bench/2026-09-26b/D3-US2-H.log bench/2026-09-26b/D3-US3-H.log --pre bench/2026-09-26b/D3-US1-P.log,bench/2026-09-26b/D3-US2-P.log bench/2026-09-26b/D3-US3-P.log
HOST bench/2026-09-26b/D3-US3-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-US3-S1.log
HOST bench/2026-09-26b/D3-US3-SN :: BD snmp bench/2026-09-26b/D3-US3-S0.log bench/2026-09-26b/D3-US3-S1.log
CAP --out bench/2026-09-26b/D3-X-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26b/D3-X-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26b/D3-X-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-L.log,bench/2026-09-26b/D3-US3-L.log,bench/2026-09-26b/D3-US3-H.log
HOST bench/2026-09-26b/D3-X-00-P :: HP
CAP --out bench/2026-09-26b/D3-X-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-X-00-H :: HN ; DW bench/2026-09-26b/D3-X-L.log
HOST bench/2026-09-26b/D3-LUR1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-X-00-H.log
CAP --out bench/2026-09-26b/D3-LUR1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/lur1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-LUR1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M
CAP --out bench/2026-09-26b/D3-LUR1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/lur1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-LUR1-P :: HP
CAP --out bench/2026-09-26b/D3-LUR1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-LUR1-H :: HN ; DW bench/2026-09-26b/D3-LUR1-L.log
HOST bench/2026-09-26b/D3-LUR1-D :: BD pair bench/2026-09-26b/D3-X-00-R.log,bench/2026-09-26b/X-D3-X-00-R.log bench/2026-09-26b/D3-LUR1-R.log,bench/2026-09-26b/X-D3-LUR1-R.log --host bench/2026-09-26b/D3-X-00-H.log bench/2026-09-26b/D3-LUR1-H.log --pre bench/2026-09-26b/D3-X-00-P.log bench/2026-09-26b/D3-LUR1-P.log
HOST bench/2026-09-26b/D3-LUR1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-LUR1-S1.log
HOST bench/2026-09-26b/D3-LUR1-SN :: BD snmp bench/2026-09-26b/D3-LUR1-S0.log bench/2026-09-26b/D3-LUR1-S1.log
HOST bench/2026-09-26b/D3-LUS1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26b/D3-LUR1-L.log,bench/2026-09-26b/D3-LUR1-H.log
CAP --out bench/2026-09-26b/D3-LUS1-S0 --send 'iperf3 -s -1 -f k --logfile /tmp/lus1.log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' --idle 4 --seconds 30
HOST bench/2026-09-26b/D3-LUS1 :: IPERF -c 10.1.1.3 -p 5201 -t 30 -i 1 -f m -u -l 1400 -b 20M -R
CAP --out bench/2026-09-26b/D3-LUS1-S1 --send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/lus1.log' --idle 3 --seconds 40
HOST bench/2026-09-26b/D3-LUS1-P :: HP
CAP --out bench/2026-09-26b/D3-LUS1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26b/D3-LUS1-H :: HN ; DW bench/2026-09-26b/D3-LUS1-L.log
HOST bench/2026-09-26b/D3-LUS1-D :: BD pair bench/2026-09-26b/D3-X-00-R.log,bench/2026-09-26b/X-D3-X-00-R.log,bench/2026-09-26b/D3-LUR1-R.log,bench/2026-09-26b/X-D3-LUR1-R.log bench/2026-09-26b/D3-LUS1-R.log,bench/2026-09-26b/X-D3-LUS1-R.log --host bench/2026-09-26b/D3-X-00-H.log,bench/2026-09-26b/D3-LUR1-H.log bench/2026-09-26b/D3-LUS1-H.log --pre bench/2026-09-26b/D3-X-00-P.log,bench/2026-09-26b/D3-LUR1-P.log bench/2026-09-26b/D3-LUS1-P.log
HOST bench/2026-09-26b/D3-LUS1-IL :: ILG parse --duration 30 bench/2026-09-26b/D3-LUS1-S1.log
HOST bench/2026-09-26b/D3-LUS1-SN :: BD snmp bench/2026-09-26b/D3-LUS1-S0.log bench/2026-09-26b/D3-LUS1-S1.log
HOST bench/2026-09-26b/D3-SUM :: grep -c '^iperf Done[.]$' bench/2026-09-26b/D3-TR1.log bench/2026-09-26b/D3-TR2.log bench/2026-09-26b/D3-TR3.log bench/2026-09-26b/D3-TS1.log bench/2026-09-26b/D3-TS2.log bench/2026-09-26b/D3-TS3.log bench/2026-09-26b/D3-UR1.log bench/2026-09-26b/D3-UR2.log bench/2026-09-26b/D3-UR3.log bench/2026-09-26b/D3-US1.log bench/2026-09-26b/D3-US2.log bench/2026-09-26b/D3-US3.log bench/2026-09-26b/D3-LUR1.log bench/2026-09-26b/D3-LUS1.log ; grep -c 'No route to host' bench/2026-09-26b/D3-TR1.log bench/2026-09-26b/D3-TR2.log bench/2026-09-26b/D3-TR3.log bench/2026-09-26b/D3-TS1.log bench/2026-09-26b/D3-TS2.log bench/2026-09-26b/D3-TS3.log bench/2026-09-26b/D3-UR1.log bench/2026-09-26b/D3-UR2.log bench/2026-09-26b/D3-UR3.log bench/2026-09-26b/D3-US1.log bench/2026-09-26b/D3-US2.log bench/2026-09-26b/D3-US3.log bench/2026-09-26b/D3-LUR1.log bench/2026-09-26b/D3-LUS1.log ; true
```

### The closing map, `n_writes`, the kernel log

```
CAP --out bench/2026-09-26b/R1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-26b/R1-MB1 :: MB bench/2026-09-26b/R1-M1
CAP --out bench/2026-09-26b/R1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
HOST bench/2026-09-26b/Z-DW :: DW bench/2026-09-26b/W-2-1514-H.log,bench/2026-09-26b/W-9-L.log,bench/2026-09-26b/W-9-H.log,bench/2026-09-26b/D3-L.log,bench/2026-09-26b/D3-TR1-L.log,bench/2026-09-26b/D3-TR2-L.log,bench/2026-09-26b/D3-TR3-L.log,bench/2026-09-26b/D3-TS1-L.log,bench/2026-09-26b/D3-TS2-L.log,bench/2026-09-26b/D3-TS3-L.log,bench/2026-09-26b/D3-UR1-L.log,bench/2026-09-26b/D3-UR2-L.log,bench/2026-09-26b/D3-UR3-L.log,bench/2026-09-26b/D3-US1-L.log,bench/2026-09-26b/D3-US2-L.log,bench/2026-09-26b/D3-US3-L.log,bench/2026-09-26b/D3-US3-H.log,bench/2026-09-26b/D3-X-L.log,bench/2026-09-26b/D3-LUR1-L.log,bench/2026-09-26b/D3-LUS1-L.log,bench/2026-09-26b/D3-LUS1-H.log
HOST bench/2026-09-26b/Z-DWALL :: DW none
```

---

## § 6 How the cells are run

**Before any cell** (none of it a cell), in this order: (1) no other WSL job is running — no
build, no desk sweep, nothing started from WSL — because (2) kills every WSL process; (2)
`wsl --shutdown` from PowerShell, then the keeper `wsl -d Ubuntu-24.04 -- sleep 36000` in the
background; (3) the kernel-log follower, from PowerShell in the background:
`wsl -d Ubuntu-24.04 -- bash -c "mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/host && exec dmesg -w > /home/key/fwre-work/rebuild/s112/r6b3/host/dmesg-w2.log"`
— started before the attach, so the attach itself is in the log (card 1's `dmesg-w.log` is not
overwritten); (4) `usbipd list`, read fresh, then `usbipd attach` of the CP2102 and of the GbE
adapter, reading what each prints; (5) in WSL, from the repository root:
`mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/run2`;
`/usr/bin/python3 tools/cardcheck.py numbers` on this card, every row re-derived;
`/usr/bin/python3 tools/check-predictions.py` on this card, reading
**`0 of 580 captures came after the prediction, 580 did not`**; every invocation once through
`runblock.py … --dry`, each ending `ALL ITEMS DONE`. **The catch window opens no later than
23:00 on 2026-09-26**; later, the card is re-dated before power.

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log LOG`, with
LOG `/home/key/fwre-work/rebuild/s112/r6b3/run2/run-NAME.log`, in the order `I-0`, `I-1`,
`I-B`, `I-WE0` (in the background; its transcript read for `BG  W-TCPE … start seen` before
`I-E` starts), `I-E`, `I-S`, `I-WE9`, `I-WS0` (the same, `W-TCPS`), `I-W`, `I-WS9`, `I-U`,
`I-D3` (only as the press-length rule below allows), `I-Z`. `NAME?` marks a cell whose non-zero
exit is a reading; `gate:` items are the decision points; any failed cell or gate stops its own
invocation and interrupts its own background cells, never another invocation's.

**Chained references, on every path.** A kernel-log window's `--prev` (`dmesgwin` 1.2), a
capture window's `--prev` (`pcapwin` 1.3) and a pair's previous read (`brdelta` 1.2: its `R`,
`--host` and `--pre` logs) each name, comma-separated in run order, every log that is that
chain's last on some path this section allows, and the tool reads the last of them that exists
(a `prev_list` or `resolve` line says which); a pair's current read is named with its stand-in
after it (`<read>.log,X-<read>.log`), and so is every previous read; a capture's first window
on one path and not on another begins its list with `none`, the capture's start. The generator
enumerates the paths — the full run, the run without `I-D3`, each event below at every cell it
can happen at (a stand-in read, an arm voided at its first read, a trial not run, a wire
fallback, a host-path failure whose recovery passes or fails, the loader gate), and every
ordered pair of the events that skip cells (a void, a trial not run, a fallback, then also a
host-path failure) — and refuses a card on which a cell on any path reads a log that path never
wrote, reads a list whose last written log is not that chain's last on the path, or names a
read without the stand-in the path wrote for it (its positive controls, `controls50.sh` C19–C20
in the card's working directory: the lists as this card was first drafted, each naming the full
run's predecessor alone, and a pair naming a read without its stand-in, are both refused).
Nothing a recovery types writes a log a list names (`X-HN<n>` is `HN` alone; `X-L<n>` counts
the whole log). Three events on one press are not enumerated: a list holds, in run order, every
predecessor a single event or a pair leaves, so its last existing log is the right one unless a
third event removes a predecessor none of those removes — which the rules below prevent for
voids and for trials not run (a second of either stops, or ends the invocation).

**The owner's power**: `I-1` starts with its catch; the owner is told when it opens and presses
inside its 180 s window, and powers off after `I-Z`, or at once where a stop below says so.

**`I-0`** — before power: the pre-flight, the address, the adapter, no capture, one kernel-log follower and a clean log, the flush, the capture directory, the host's iperf3, the checkers' digests and self-tests, the verb check

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
R0-IPF
gate:grep=^3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8  -$:R0-IPF
gate:grep=^/usr/bin/qemu-mips-static$:R0-IPF
R0-SUM
gate:grep=^6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095  -$:R0-SUM
gate:grep=^030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984  -$:R0-SUM
gate:grep=^2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1  -$:R0-SUM
gate:grep=^e36bd29e4714408ac50d2fe7dd90dde71cb88be5c6007ec22277a0ef0082c890  -$:R0-SUM
gate:grep=^7f7dad0b02e5616943f536e6cdc31c42692a8b1f5de67d2ce0422e7b2728bafe  -$:R0-SUM
gate:grep=^2331a6ecc56a6c54c26e00840ff9e373684433c326c7d01b7a9d386d39dce2e5  -$:R0-SUM
gate:grep=^d8dadf513c2a979431bd8b38183e2117e5afcc5d0ae449aa7818cc030d372698  -$:R0-SUM
gate:grep=^4069cd42f6f8334ed6e1bd5ae8fe44c87333d2a092da27b88f77c9c54f277b90  -$:R0-SUM
gate:grep=^12ab35696c31e3949b4398f02104b7e8dbc5f029338b0e4035110be5ca1be19b  -$:R0-SUM
R0-ST
gate:grep=^pcapwin\ self\-test:\ 29\ of\ 29\ passed$:R0-ST
gate:grep=^brdelta\ self\-test:\ 40\ of\ 40\ passed$:R0-ST
gate:grep=^swcheck\ self\-test:\ 12\ of\ 12\ passed$:R0-ST
gate:grep=^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$:R0-ST
gate:grep=^RESULT:\ 31/31$:R0-ST
R0-VERB
gate:grep=^verbcheck verdict PASS$:R0-VERB
gate:grep=^verbcheck\ self\-test:\ 10\ of\ 10\ passed$:R0-VERB
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

**`I-B`** — the opening state: 1.4's defaults with `rlx0` up, and driver 1.5's page untouched since boot (not a read-back: `R6b-2`'s conjunct was met on block 47)

```run
B-00-P?
B-00-R
gate:until:B-00-R
gate:grep=^version rtl819x-nic 1\.5$:B-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:B-00-R
gate:grep=^nd_up 1$:B-00-R
B-00-H?
B-00-T
gate:until:B-00-T
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):B-00-T
gate:grep=^version rtl819x-nic 1\.5$:B-00-T
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:B-00-T
gate:grep=^v15 last - 0 ok 0 refused 0 txq \d+ arm15 0$:B-00-T
gate:grep=^sw never mode loop from 0 to 0 probe 0 rc 0 bufs 00000000$:B-00-T
gate:grep=^sw key txlen rlxfw txoff 0 txrb 0 mode loop probe 0 rings 0 rec 0$:B-00-T
gate:grep=^mt none 1455 clean 0 bad_b 0 bad_a 0 void 0 skew 0$:B-00-T
```

**`I-WE0`** — the stack arms' host capture (the board's source address, 64 B), in the background until `I-WE9`

```run
W-TCPE
```

**`I-E`** — `D2`'s second boot: E2's eleven lengths at block 45's spacing, the fix, then 1.4, then the fix again

```run
E-LIVE
gate:grep=\A1\n\Z:E-LIVE
E-F1-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F1-SW
E-F1-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F1-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:E-F1-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:E-F1-LS
E-F1-L
gate:grep=^4 packets transmitted, 4 received:E-F1-L
gate:grep=^follower 1$:E-F1-L
E-F1-P0?
E-F1-R0
gate:until:E-F1-R0
gate:grep=^version rtl819x-nic 1\.5$:E-F1-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F1-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F1-R0
gate:grep=^nd_up 1$:E-F1-R0
E-F1-H0?
E-F1-E2?
E-F1-P1?
E-F1-R1
gate:until:E-F1-R1
gate:grep=^version rtl819x-nic 1\.5$:E-F1-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F1-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F1-R1
gate:grep=^nd_up 1$:E-F1-R1
E-F1-H1?
E-F1-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-F1-D
E-L1-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-L1-SW
E-L1-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-L1-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:E-L1-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:E-L1-LS
E-L1-L
gate:grep=^4 packets transmitted, 4 received:E-L1-L
gate:grep=^follower 1$:E-L1-L
E-L1-P0?
E-L1-R0
gate:until:E-L1-R0
gate:grep=^version rtl819x-nic 1\.5$:E-L1-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-L1-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:E-L1-R0
gate:grep=^nd_up 1$:E-L1-R0
E-L1-H0?
E-L1-E2?
E-L1-P1?
E-L1-R1
gate:until:E-L1-R1
gate:grep=^version rtl819x-nic 1\.5$:E-L1-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-L1-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:E-L1-R1
gate:grep=^nd_up 1$:E-L1-R1
E-L1-H1?
E-L1-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-L1-D
E-F2-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F2-SW
E-F2-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F2-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:E-F2-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:E-F2-LS
E-F2-L
gate:grep=^4 packets transmitted, 4 received:E-F2-L
gate:grep=^follower 1$:E-F2-L
E-F2-P0?
E-F2-R0
gate:until:E-F2-R0
gate:grep=^version rtl819x-nic 1\.5$:E-F2-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F2-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F2-R0
gate:grep=^nd_up 1$:E-F2-R0
E-F2-H0?
E-F2-E2?
E-F2-P1?
E-F2-R1
gate:until:E-F2-R1
gate:grep=^version rtl819x-nic 1\.5$:E-F2-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F2-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F2-R1
gate:grep=^nd_up 1$:E-F2-R1
E-F2-H1?
E-F2-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:E-F2-D
```

**`I-S`** — `D1`'s stack arm: each of E2's eleven lengths in its own bracket, 20 requests on a re-armed ring, at the fix and then at 1.4, identical cells

```run
SF-0060-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0060-SW
SF-0060-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0060-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0060-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0060-LS
SF-0060-L
gate:grep=^4 packets transmitted, 4 received:SF-0060-L
gate:grep=^follower 1$:SF-0060-L
SF-0060-P0?
SF-0060-R0
gate:until:SF-0060-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0060-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0060-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0060-R0
gate:grep=^nd_up 1$:SF-0060-R0
SF-0060-H0?
SF-0060-PG?
SF-0060-P1?
SF-0060-R1
gate:until:SF-0060-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0060-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0060-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0060-R1
gate:grep=^nd_up 1$:SF-0060-R1
SF-0060-H1?
SF-0060-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0060-D
SL-0060-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0060-SW
SL-0060-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0060-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0060-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0060-LS
SL-0060-L
gate:grep=^4 packets transmitted, 4 received:SL-0060-L
gate:grep=^follower 1$:SL-0060-L
SL-0060-P0?
SL-0060-R0
gate:until:SL-0060-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0060-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0060-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0060-R0
gate:grep=^nd_up 1$:SL-0060-R0
SL-0060-H0?
SL-0060-PG?
SL-0060-P1?
SL-0060-R1
gate:until:SL-0060-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0060-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0060-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0060-R1
gate:grep=^nd_up 1$:SL-0060-R1
SL-0060-H1?
SL-0060-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0060-D
SF-0061-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0061-SW
SF-0061-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0061-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0061-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0061-LS
SF-0061-L
gate:grep=^4 packets transmitted, 4 received:SF-0061-L
gate:grep=^follower 1$:SF-0061-L
SF-0061-P0?
SF-0061-R0
gate:until:SF-0061-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0061-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0061-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0061-R0
gate:grep=^nd_up 1$:SF-0061-R0
SF-0061-H0?
SF-0061-PG?
SF-0061-P1?
SF-0061-R1
gate:until:SF-0061-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0061-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0061-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0061-R1
gate:grep=^nd_up 1$:SF-0061-R1
SF-0061-H1?
SF-0061-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0061-D
SL-0061-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0061-SW
SL-0061-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0061-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0061-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0061-LS
SL-0061-L
gate:grep=^4 packets transmitted, 4 received:SL-0061-L
gate:grep=^follower 1$:SL-0061-L
SL-0061-P0?
SL-0061-R0
gate:until:SL-0061-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0061-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0061-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0061-R0
gate:grep=^nd_up 1$:SL-0061-R0
SL-0061-H0?
SL-0061-PG?
SL-0061-P1?
SL-0061-R1
gate:until:SL-0061-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0061-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0061-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0061-R1
gate:grep=^nd_up 1$:SL-0061-R1
SL-0061-H1?
SL-0061-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0061-D
SF-0062-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0062-SW
SF-0062-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0062-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0062-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0062-LS
SF-0062-L
gate:grep=^4 packets transmitted, 4 received:SF-0062-L
gate:grep=^follower 1$:SF-0062-L
SF-0062-P0?
SF-0062-R0
gate:until:SF-0062-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0062-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0062-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0062-R0
gate:grep=^nd_up 1$:SF-0062-R0
SF-0062-H0?
SF-0062-PG?
SF-0062-P1?
SF-0062-R1
gate:until:SF-0062-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0062-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0062-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0062-R1
gate:grep=^nd_up 1$:SF-0062-R1
SF-0062-H1?
SF-0062-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0062-D
SL-0062-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0062-SW
SL-0062-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0062-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0062-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0062-LS
SL-0062-L
gate:grep=^4 packets transmitted, 4 received:SL-0062-L
gate:grep=^follower 1$:SL-0062-L
SL-0062-P0?
SL-0062-R0
gate:until:SL-0062-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0062-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0062-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0062-R0
gate:grep=^nd_up 1$:SL-0062-R0
SL-0062-H0?
SL-0062-PG?
SL-0062-P1?
SL-0062-R1
gate:until:SL-0062-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0062-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0062-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0062-R1
gate:grep=^nd_up 1$:SL-0062-R1
SL-0062-H1?
SL-0062-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0062-D
SF-0063-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0063-SW
SF-0063-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0063-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0063-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0063-LS
SF-0063-L
gate:grep=^4 packets transmitted, 4 received:SF-0063-L
gate:grep=^follower 1$:SF-0063-L
SF-0063-P0?
SF-0063-R0
gate:until:SF-0063-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0063-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0063-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0063-R0
gate:grep=^nd_up 1$:SF-0063-R0
SF-0063-H0?
SF-0063-PG?
SF-0063-P1?
SF-0063-R1
gate:until:SF-0063-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0063-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0063-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0063-R1
gate:grep=^nd_up 1$:SF-0063-R1
SF-0063-H1?
SF-0063-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0063-D
SL-0063-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0063-SW
SL-0063-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0063-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0063-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0063-LS
SL-0063-L
gate:grep=^4 packets transmitted, 4 received:SL-0063-L
gate:grep=^follower 1$:SL-0063-L
SL-0063-P0?
SL-0063-R0
gate:until:SL-0063-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0063-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0063-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0063-R0
gate:grep=^nd_up 1$:SL-0063-R0
SL-0063-H0?
SL-0063-PG?
SL-0063-P1?
SL-0063-R1
gate:until:SL-0063-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0063-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0063-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0063-R1
gate:grep=^nd_up 1$:SL-0063-R1
SL-0063-H1?
SL-0063-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0063-D
SF-0263-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0263-SW
SF-0263-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0263-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0263-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0263-LS
SF-0263-L
gate:grep=^4 packets transmitted, 4 received:SF-0263-L
gate:grep=^follower 1$:SF-0263-L
SF-0263-P0?
SF-0263-R0
gate:until:SF-0263-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0263-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0263-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0263-R0
gate:grep=^nd_up 1$:SF-0263-R0
SF-0263-H0?
SF-0263-PG?
SF-0263-P1?
SF-0263-R1
gate:until:SF-0263-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0263-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0263-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0263-R1
gate:grep=^nd_up 1$:SF-0263-R1
SF-0263-H1?
SF-0263-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0263-D
SL-0263-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0263-SW
SL-0263-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0263-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0263-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0263-LS
SL-0263-L
gate:grep=^4 packets transmitted, 4 received:SL-0263-L
gate:grep=^follower 1$:SL-0263-L
SL-0263-P0?
SL-0263-R0
gate:until:SL-0263-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0263-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0263-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0263-R0
gate:grep=^nd_up 1$:SL-0263-R0
SL-0263-H0?
SL-0263-PG?
SL-0263-P1?
SL-0263-R1
gate:until:SL-0263-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0263-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0263-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0263-R1
gate:grep=^nd_up 1$:SL-0263-R1
SL-0263-H1?
SL-0263-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0263-D
SF-0276-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0276-SW
SF-0276-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0276-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0276-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0276-LS
SF-0276-L
gate:grep=^4 packets transmitted, 4 received:SF-0276-L
gate:grep=^follower 1$:SF-0276-L
SF-0276-P0?
SF-0276-R0
gate:until:SF-0276-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0276-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0276-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0276-R0
gate:grep=^nd_up 1$:SF-0276-R0
SF-0276-H0?
SF-0276-PG?
SF-0276-P1?
SF-0276-R1
gate:until:SF-0276-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0276-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0276-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0276-R1
gate:grep=^nd_up 1$:SF-0276-R1
SF-0276-H1?
SF-0276-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0276-D
SL-0276-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0276-SW
SL-0276-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0276-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0276-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0276-LS
SL-0276-L
gate:grep=^4 packets transmitted, 4 received:SL-0276-L
gate:grep=^follower 1$:SL-0276-L
SL-0276-P0?
SL-0276-R0
gate:until:SL-0276-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0276-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0276-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0276-R0
gate:grep=^nd_up 1$:SL-0276-R0
SL-0276-H0?
SL-0276-PG?
SL-0276-P1?
SL-0276-R1
gate:until:SL-0276-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0276-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0276-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0276-R1
gate:grep=^nd_up 1$:SL-0276-R1
SL-0276-H1?
SL-0276-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0276-D
SF-0277-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0277-SW
SF-0277-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0277-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-0277-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-0277-LS
SF-0277-L
gate:grep=^4 packets transmitted, 4 received:SF-0277-L
gate:grep=^follower 1$:SF-0277-L
SF-0277-P0?
SF-0277-R0
gate:until:SF-0277-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-0277-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0277-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0277-R0
gate:grep=^nd_up 1$:SF-0277-R0
SF-0277-H0?
SF-0277-PG?
SF-0277-P1?
SF-0277-R1
gate:until:SF-0277-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-0277-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-0277-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-0277-R1
gate:grep=^nd_up 1$:SF-0277-R1
SF-0277-H1?
SF-0277-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-0277-D
SL-0277-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0277-SW
SL-0277-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0277-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-0277-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-0277-LS
SL-0277-L
gate:grep=^4 packets transmitted, 4 received:SL-0277-L
gate:grep=^follower 1$:SL-0277-L
SL-0277-P0?
SL-0277-R0
gate:until:SL-0277-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-0277-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0277-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0277-R0
gate:grep=^nd_up 1$:SL-0277-R0
SL-0277-H0?
SL-0277-PG?
SL-0277-P1?
SL-0277-R1
gate:until:SL-0277-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-0277-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-0277-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-0277-R1
gate:grep=^nd_up 1$:SL-0277-R1
SL-0277-H1?
SL-0277-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-0277-D
SF-1511-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1511-SW
SF-1511-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1511-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-1511-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-1511-LS
SF-1511-L
gate:grep=^4 packets transmitted, 4 received:SF-1511-L
gate:grep=^follower 1$:SF-1511-L
SF-1511-P0?
SF-1511-R0
gate:until:SF-1511-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-1511-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1511-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1511-R0
gate:grep=^nd_up 1$:SF-1511-R0
SF-1511-H0?
SF-1511-PG?
SF-1511-P1?
SF-1511-R1
gate:until:SF-1511-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-1511-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1511-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1511-R1
gate:grep=^nd_up 1$:SF-1511-R1
SF-1511-H1?
SF-1511-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-1511-D
SL-1511-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1511-SW
SL-1511-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1511-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-1511-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-1511-LS
SL-1511-L
gate:grep=^4 packets transmitted, 4 received:SL-1511-L
gate:grep=^follower 1$:SL-1511-L
SL-1511-P0?
SL-1511-R0
gate:until:SL-1511-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-1511-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1511-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1511-R0
gate:grep=^nd_up 1$:SL-1511-R0
SL-1511-H0?
SL-1511-PG?
SL-1511-P1?
SL-1511-R1
gate:until:SL-1511-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-1511-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1511-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1511-R1
gate:grep=^nd_up 1$:SL-1511-R1
SL-1511-H1?
SL-1511-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-1511-D
SF-1512-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1512-SW
SF-1512-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1512-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-1512-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-1512-LS
SF-1512-L
gate:grep=^4 packets transmitted, 4 received:SF-1512-L
gate:grep=^follower 1$:SF-1512-L
SF-1512-P0?
SF-1512-R0
gate:until:SF-1512-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-1512-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1512-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1512-R0
gate:grep=^nd_up 1$:SF-1512-R0
SF-1512-H0?
SF-1512-PG?
SF-1512-P1?
SF-1512-R1
gate:until:SF-1512-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-1512-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1512-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1512-R1
gate:grep=^nd_up 1$:SF-1512-R1
SF-1512-H1?
SF-1512-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-1512-D
SL-1512-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1512-SW
SL-1512-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1512-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-1512-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-1512-LS
SL-1512-L
gate:grep=^4 packets transmitted, 4 received:SL-1512-L
gate:grep=^follower 1$:SL-1512-L
SL-1512-P0?
SL-1512-R0
gate:until:SL-1512-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-1512-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1512-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1512-R0
gate:grep=^nd_up 1$:SL-1512-R0
SL-1512-H0?
SL-1512-PG?
SL-1512-P1?
SL-1512-R1
gate:until:SL-1512-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-1512-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1512-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1512-R1
gate:grep=^nd_up 1$:SL-1512-R1
SL-1512-H1?
SL-1512-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-1512-D
SF-1513-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1513-SW
SF-1513-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1513-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-1513-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-1513-LS
SF-1513-L
gate:grep=^4 packets transmitted, 4 received:SF-1513-L
gate:grep=^follower 1$:SF-1513-L
SF-1513-P0?
SF-1513-R0
gate:until:SF-1513-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-1513-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1513-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1513-R0
gate:grep=^nd_up 1$:SF-1513-R0
SF-1513-H0?
SF-1513-PG?
SF-1513-P1?
SF-1513-R1
gate:until:SF-1513-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-1513-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1513-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1513-R1
gate:grep=^nd_up 1$:SF-1513-R1
SF-1513-H1?
SF-1513-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-1513-D
SL-1513-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1513-SW
SL-1513-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1513-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-1513-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-1513-LS
SL-1513-L
gate:grep=^4 packets transmitted, 4 received:SL-1513-L
gate:grep=^follower 1$:SL-1513-L
SL-1513-P0?
SL-1513-R0
gate:until:SL-1513-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-1513-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1513-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1513-R0
gate:grep=^nd_up 1$:SL-1513-R0
SL-1513-H0?
SL-1513-PG?
SL-1513-P1?
SL-1513-R1
gate:until:SL-1513-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-1513-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1513-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1513-R1
gate:grep=^nd_up 1$:SL-1513-R1
SL-1513-H1?
SL-1513-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-1513-D
SF-1514-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1514-SW
SF-1514-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1514-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SF-1514-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SF-1514-LS
SF-1514-L
gate:grep=^4 packets transmitted, 4 received:SF-1514-L
gate:grep=^follower 1$:SF-1514-L
SF-1514-P0?
SF-1514-R0
gate:until:SF-1514-R0
gate:grep=^version rtl819x-nic 1\.5$:SF-1514-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1514-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1514-R0
gate:grep=^nd_up 1$:SF-1514-R0
SF-1514-H0?
SF-1514-PG?
SF-1514-P1?
SF-1514-R1
gate:until:SF-1514-R1
gate:grep=^version rtl819x-nic 1\.5$:SF-1514-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SF-1514-R1
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:SF-1514-R1
gate:grep=^nd_up 1$:SF-1514-R1
SF-1514-H1?
SF-1514-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SF-1514-D
SL-1514-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1514-SW
SL-1514-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1514-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:SL-1514-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:SL-1514-LS
SL-1514-L
gate:grep=^4 packets transmitted, 4 received:SL-1514-L
gate:grep=^follower 1$:SL-1514-L
SL-1514-P0?
SL-1514-R0
gate:until:SL-1514-R0
gate:grep=^version rtl819x-nic 1\.5$:SL-1514-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1514-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1514-R0
gate:grep=^nd_up 1$:SL-1514-R0
SL-1514-H0?
SL-1514-PG?
SL-1514-P1?
SL-1514-R1
gate:until:SL-1514-R1
gate:grep=^version rtl819x-nic 1\.5$:SL-1514-R1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SL-1514-R1
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:SL-1514-R1
gate:grep=^nd_up 1$:SL-1514-R1
SL-1514-H1?
SL-1514-D
gate:grep=^path p3 rx d \d+ host outechos d [1-9]\d* covered yes$:SL-1514-D
```

**`I-WE9`** — the stack arms' capture stopped, summed, and windowed by record order

```run
W-TCPEX?
W-EWALL?
W-EORD?
```

**`I-WS0`** — the sweeps' host capture (the board's source address and 0x88B5, tagged or not, 64 B), in the background until `I-WS9`

```run
W-TCPS
```

**`I-W`** — the wire: the loopback positive control and the fix's loopback map (the containment gate), the fix over every length in four brackets, the owner's bound refusing, then 1.4 at E2's eleven, one bracket each

```run
S-LIVE
gate:grep=\A1\n\Z:S-LIVE
W-00-DN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-00-DN
W-00-K
gate:until:W-00-K
gate:grep=^version rtl819x-nic 1\.5$:W-00-K
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-00-K
gate:grep=^nd_up 0$:W-00-K
gate:grep=^irq_taken 1$:W-00-K
gate:grep=^engine_on 0$:W-00-K
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 1 p15 1$:W-00-K
W-00-P?
W-00-R
gate:until:W-00-R
gate:grep=^version rtl819x-nic 1\.5$:W-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-00-R
gate:grep=^nd_up 0$:W-00-R
W-00-H?
LB-P-0061
gate:until:LB-P-0061
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-P-0061
gate:grep=^v15 last sweep (?:15|-71|-61|-145|-4) :LB-P-0061
gate:grep=^sw (?:done|fail|intr) mode loop from 61 to 61 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:LB-P-0061
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:LB-P-0061
LB-P-1511
gate:until:LB-P-1511
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-P-1511
gate:grep=^v15 last sweep (?:19|-71|-61|-145|-4) :LB-P-1511
gate:grep=^sw (?:done|fail|intr) mode loop from 1511 to 1511 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:LB-P-1511
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:LB-P-1511
gate:grep=^mt none 1453 clean 0 bad_b 2 bad_a 0 void 0 skew 0$:LB-P-1511
LB-P-C?
LB-P-P?
LB-P-R
gate:until:LB-P-R
gate:grep=^version rtl819x-nic 1\.5$:LB-P-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-P-R
gate:grep=^nd_up 0$:LB-P-R
LB-P-H?
LB-P-D?
LB-V-V
gate:until:LB-V-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-V-V
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 1 p15 1$:LB-V-V
LB-V-S
gate:until:LB-V-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-V-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :LB-V-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:LB-V-S
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:LB-V-S
LB-V-C?
LB-V-P?
LB-V-R
gate:until:LB-V-R
gate:grep=^version rtl819x-nic 1\.5$:LB-V-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-V-R
gate:grep=^nd_up 0$:LB-V-R
LB-V-H?
LB-V-D?
W-00
gate:until:W-00
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-00
gate:grep=^sw done mode loop from 60 to 1514 probe 60 rc 0 bufs [0-9A-F]{8}$:W-00
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode loop probe 60 rings \d+ rec 1455$:W-00
gate:grep=^sw scored 1455 bad_a 0 bad_b 0 void 0 skew 0 :W-00
gate:grep=^sw delta0 0 reg 1 units 1455 timeout 0 :W-00
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:W-00
W-1a-S
gate:until:W-1a-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1a-S
gate:grep=^v15 last sweep (?:21|-71|-61|-145|-4) :W-1a-S
gate:grep=^sw (?:done|fail|intr) mode wire from 60 to 423 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-1a-S
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-1a-S
W-1a-P?
W-1a-R
gate:until:W-1a-R
gate:grep=^version rtl819x-nic 1\.5$:W-1a-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1a-R
gate:grep=^nd_up 0$:W-1a-R
W-1a-H?
W-1a-D
gate:grep=^fault jfd 0$:W-1a-D
W-1b-S
gate:until:W-1b-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1b-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-1b-S
gate:grep=^sw (?:done|fail|intr) mode wire from 424 to 787 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-1b-S
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-1b-S
W-1b-P?
W-1b-R
gate:until:W-1b-R
gate:grep=^version rtl819x-nic 1\.5$:W-1b-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1b-R
gate:grep=^nd_up 0$:W-1b-R
W-1b-H?
W-1b-D
gate:grep=^fault jfd 0$:W-1b-D
W-1c-S
gate:until:W-1c-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1c-S
gate:grep=^v15 last sweep (?:23|-71|-61|-145|-4) :W-1c-S
gate:grep=^sw (?:done|fail|intr) mode wire from 788 to 1151 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-1c-S
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-1c-S
W-1c-P?
W-1c-R
gate:until:W-1c-R
gate:grep=^version rtl819x-nic 1\.5$:W-1c-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1c-R
gate:grep=^nd_up 0$:W-1c-R
W-1c-H?
W-1c-D
gate:grep=^fault jfd 0$:W-1c-D
W-1d-S
gate:until:W-1d-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1d-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-1d-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1152 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-1d-S
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-1d-S
W-1d-P?
W-1d-R
gate:until:W-1d-R
gate:grep=^version rtl819x-nic 1\.5$:W-1d-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-1d-R
gate:grep=^nd_up 0$:W-1d-R
W-1d-H?
W-1d-D
gate:grep=^fault jfd 0$:W-1d-D
W-2-V
gate:until:W-2-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 1 p15 1$:W-2-V
W-2-EP
gate:until:W-2-EP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-EP
gate:grep=^v15 last sweep -1 :W-2-EP
W-2-0060-S
gate:until:W-2-0060-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0060-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0060-S
gate:grep=^sw (?:done|fail|intr) mode wire from 60 to 60 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0060-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0060-S
W-2-0060-P?
W-2-0060-R
gate:until:W-2-0060-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0060-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0060-R
gate:grep=^nd_up 0$:W-2-0060-R
W-2-0060-H?
W-2-0060-D?
W-2-0061-S
gate:until:W-2-0061-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0061-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0061-S
gate:grep=^sw (?:done|fail|intr) mode wire from 61 to 61 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0061-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0061-S
W-2-0061-P?
W-2-0061-R
gate:until:W-2-0061-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0061-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0061-R
gate:grep=^nd_up 0$:W-2-0061-R
W-2-0061-H?
W-2-0061-D?
W-2-0062-S
gate:until:W-2-0062-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0062-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0062-S
gate:grep=^sw (?:done|fail|intr) mode wire from 62 to 62 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0062-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0062-S
W-2-0062-P?
W-2-0062-R
gate:until:W-2-0062-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0062-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0062-R
gate:grep=^nd_up 0$:W-2-0062-R
W-2-0062-H?
W-2-0062-D?
W-2-0063-S
gate:until:W-2-0063-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0063-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0063-S
gate:grep=^sw (?:done|fail|intr) mode wire from 63 to 63 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0063-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0063-S
W-2-0063-P?
W-2-0063-R
gate:until:W-2-0063-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0063-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0063-R
gate:grep=^nd_up 0$:W-2-0063-R
W-2-0063-H?
W-2-0063-D?
W-2-0263-S
gate:until:W-2-0263-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0263-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0263-S
gate:grep=^sw (?:done|fail|intr) mode wire from 263 to 263 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0263-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0263-S
W-2-0263-P?
W-2-0263-R
gate:until:W-2-0263-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0263-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0263-R
gate:grep=^nd_up 0$:W-2-0263-R
W-2-0263-H?
W-2-0263-D?
W-2-0276-S
gate:until:W-2-0276-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0276-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0276-S
gate:grep=^sw (?:done|fail|intr) mode wire from 276 to 276 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0276-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0276-S
W-2-0276-P?
W-2-0276-R
gate:until:W-2-0276-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0276-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0276-R
gate:grep=^nd_up 0$:W-2-0276-R
W-2-0276-H?
W-2-0276-D?
W-2-0277-S
gate:until:W-2-0277-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0277-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0277-S
gate:grep=^sw (?:done|fail|intr) mode wire from 277 to 277 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0277-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0277-S
W-2-0277-P?
W-2-0277-R
gate:until:W-2-0277-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0277-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0277-R
gate:grep=^nd_up 0$:W-2-0277-R
W-2-0277-H?
W-2-0277-D?
W-2-1511-S
gate:until:W-2-1511-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1511-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1511-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1511 to 1511 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1511-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1511-S
W-2-1511-P?
W-2-1511-R
gate:until:W-2-1511-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1511-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1511-R
gate:grep=^nd_up 0$:W-2-1511-R
W-2-1511-H?
W-2-1511-D?
W-2-1512-S
gate:until:W-2-1512-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1512-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1512-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1512 to 1512 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1512-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1512-S
W-2-1512-P?
W-2-1512-R
gate:until:W-2-1512-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1512-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1512-R
gate:grep=^nd_up 0$:W-2-1512-R
W-2-1512-H?
W-2-1512-D?
W-2-1513-S
gate:until:W-2-1513-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1513-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1513-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1513 to 1513 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1513-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1513-S
W-2-1513-P?
W-2-1513-R
gate:until:W-2-1513-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1513-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1513-R
gate:grep=^nd_up 0$:W-2-1513-R
W-2-1513-H?
W-2-1513-D?
W-2-1514-S
gate:until:W-2-1514-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1514-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1514-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1514 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1514-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1514-S
W-2-1514-P?
W-2-1514-R
gate:until:W-2-1514-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1514-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1514-R
gate:grep=^nd_up 0$:W-2-1514-R
W-2-1514-H?
W-2-1514-D?
```

**`I-WS9`** — the sweeps' capture stopped, summed, and windowed by record order

```run
W-TCPSX?
W-SWALL?
W-SORD?
```

**`I-U`** — `rlx0` back up at 1.4 after the sweeps' capture has stopped: the port-3 and liveness gates and a bracket

```run
W-9-UP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-UP
W-9-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:W-9-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:W-9-LS
W-9-L
gate:grep=^4 packets transmitted, 4 received:W-9-L
gate:grep=^follower 1$:W-9-L
W-9-P?
W-9-R
gate:until:W-9-R
gate:grep=^version rtl819x-nic 1\.5$:W-9-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:W-9-R
gate:grep=^nd_up 1$:W-9-R
W-9-H?
```

**`I-D3`** — `D3`'s first boot: `NET-111`'s twelve `rlx0` trials at the fix, then 1.4's control (one UDP trial each way), each bracketed, with the board's `Udp:` line around each (`NET-117` 殘留)

```run
D3-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-SW
D3-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-LS
D3-L
gate:grep=^4 packets transmitted, 4 received:D3-L
gate:grep=^follower 1$:D3-L
D3-00-P?
D3-00-R
gate:until:D3-00-R
gate:grep=^version rtl819x-nic 1\.5$:D3-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-00-R
gate:grep=^nd_up 1$:D3-00-R
D3-00-H?
D3-TR1-L
gate:grep=^4 packets transmitted, 4 received:D3-TR1-L
gate:grep=^follower 1$:D3-TR1-L
D3-TR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr1\.log *$:D3-TR1-S0
D3-TR1?
D3-TR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-S1
D3-TR1-P?
D3-TR1-R
gate:until:D3-TR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR1-R
gate:grep=^nd_up 1$:D3-TR1-R
D3-TR1-H?
D3-TR1-D?
D3-TR1-IL?
D3-TR1-SN?
D3-TR1-IC?
D3-TR2-L
gate:grep=^4 packets transmitted, 4 received:D3-TR2-L
gate:grep=^follower 1$:D3-TR2-L
D3-TR2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr2\.log *$:D3-TR2-S0
D3-TR2?
D3-TR2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-S1
D3-TR2-P?
D3-TR2-R
gate:until:D3-TR2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR2-R
gate:grep=^nd_up 1$:D3-TR2-R
D3-TR2-H?
D3-TR2-D?
D3-TR2-IL?
D3-TR2-SN?
D3-TR2-IC?
D3-TR3-L
gate:grep=^4 packets transmitted, 4 received:D3-TR3-L
gate:grep=^follower 1$:D3-TR3-L
D3-TR3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/tr3\.log *$:D3-TR3-S0
D3-TR3?
D3-TR3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-S1
D3-TR3-P?
D3-TR3-R
gate:until:D3-TR3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TR3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TR3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TR3-R
gate:grep=^nd_up 1$:D3-TR3-R
D3-TR3-H?
D3-TR3-D?
D3-TR3-IL?
D3-TR3-SN?
D3-TR3-IC?
D3-TS1-L
gate:grep=^4 packets transmitted, 4 received:D3-TS1-L
gate:grep=^follower 1$:D3-TS1-L
D3-TS1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts1\.log *$:D3-TS1-S0
D3-TS1?
D3-TS1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-S1
D3-TS1-P?
D3-TS1-R
gate:until:D3-TS1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS1-R
gate:grep=^nd_up 1$:D3-TS1-R
D3-TS1-H?
D3-TS1-D?
D3-TS1-IL?
D3-TS1-SN?
D3-TS2-L
gate:grep=^4 packets transmitted, 4 received:D3-TS2-L
gate:grep=^follower 1$:D3-TS2-L
D3-TS2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts2\.log *$:D3-TS2-S0
D3-TS2?
D3-TS2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-S1
D3-TS2-P?
D3-TS2-R
gate:until:D3-TS2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS2-R
gate:grep=^nd_up 1$:D3-TS2-R
D3-TS2-H?
D3-TS2-D?
D3-TS2-IL?
D3-TS2-SN?
D3-TS3-L
gate:grep=^4 packets transmitted, 4 received:D3-TS3-L
gate:grep=^follower 1$:D3-TS3-L
D3-TS3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ts3\.log *$:D3-TS3-S0
D3-TS3?
D3-TS3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-S1
D3-TS3-P?
D3-TS3-R
gate:until:D3-TS3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-TS3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-TS3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-TS3-R
gate:grep=^nd_up 1$:D3-TS3-R
D3-TS3-H?
D3-TS3-D?
D3-TS3-IL?
D3-TS3-SN?
D3-UR1-L
gate:grep=^4 packets transmitted, 4 received:D3-UR1-L
gate:grep=^follower 1$:D3-UR1-L
D3-UR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur1\.log *$:D3-UR1-S0
D3-UR1?
D3-UR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-S1
D3-UR1-P?
D3-UR1-R
gate:until:D3-UR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR1-R
gate:grep=^nd_up 1$:D3-UR1-R
D3-UR1-H?
D3-UR1-D?
D3-UR1-IL?
D3-UR1-SN?
D3-UR1-IC?
D3-UR2-L
gate:grep=^4 packets transmitted, 4 received:D3-UR2-L
gate:grep=^follower 1$:D3-UR2-L
D3-UR2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur2\.log *$:D3-UR2-S0
D3-UR2?
D3-UR2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-S1
D3-UR2-P?
D3-UR2-R
gate:until:D3-UR2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR2-R
gate:grep=^nd_up 1$:D3-UR2-R
D3-UR2-H?
D3-UR2-D?
D3-UR2-IL?
D3-UR2-SN?
D3-UR2-IC?
D3-UR3-L
gate:grep=^4 packets transmitted, 4 received:D3-UR3-L
gate:grep=^follower 1$:D3-UR3-L
D3-UR3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/ur3\.log *$:D3-UR3-S0
D3-UR3?
D3-UR3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-S1
D3-UR3-P?
D3-UR3-R
gate:until:D3-UR3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-UR3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-UR3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-UR3-R
gate:grep=^nd_up 1$:D3-UR3-R
D3-UR3-H?
D3-UR3-D?
D3-UR3-IL?
D3-UR3-SN?
D3-UR3-IC?
D3-US1-L
gate:grep=^4 packets transmitted, 4 received:D3-US1-L
gate:grep=^follower 1$:D3-US1-L
D3-US1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us1\.log *$:D3-US1-S0
D3-US1?
D3-US1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-S1
D3-US1-P?
D3-US1-R
gate:until:D3-US1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US1-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US1-R
gate:grep=^nd_up 1$:D3-US1-R
D3-US1-H?
D3-US1-D?
D3-US1-IL?
D3-US1-SN?
D3-US2-L
gate:grep=^4 packets transmitted, 4 received:D3-US2-L
gate:grep=^follower 1$:D3-US2-L
D3-US2-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us2\.log *$:D3-US2-S0
D3-US2?
D3-US2-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-S1
D3-US2-P?
D3-US2-R
gate:until:D3-US2-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US2-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US2-R
gate:grep=^nd_up 1$:D3-US2-R
D3-US2-H?
D3-US2-D?
D3-US2-IL?
D3-US2-SN?
D3-US3-L
gate:grep=^4 packets transmitted, 4 received:D3-US3-L
gate:grep=^follower 1$:D3-US3-L
D3-US3-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/us3\.log *$:D3-US3-S0
D3-US3?
D3-US3-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-S1
D3-US3-P?
D3-US3-R
gate:until:D3-US3-R
gate:grep=^version rtl819x-nic 1\.5$:D3-US3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-US3-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:D3-US3-R
gate:grep=^nd_up 1$:D3-US3-R
D3-US3-H?
D3-US3-D?
D3-US3-IL?
D3-US3-SN?
D3-X-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-SW
D3-X-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:D3-X-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:D3-X-LS
D3-X-L
gate:grep=^4 packets transmitted, 4 received:D3-X-L
gate:grep=^follower 1$:D3-X-L
D3-X-00-P?
D3-X-00-R
gate:until:D3-X-00-R
gate:grep=^version rtl819x-nic 1\.5$:D3-X-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-X-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-X-00-R
gate:grep=^nd_up 1$:D3-X-00-R
D3-X-00-H?
D3-LUR1-L
gate:grep=^4 packets transmitted, 4 received:D3-LUR1-L
gate:grep=^follower 1$:D3-LUR1-L
D3-LUR1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/lur1\.log *$:D3-LUR1-S0
D3-LUR1?
D3-LUR1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-S1
D3-LUR1-P?
D3-LUR1-R
gate:until:D3-LUR1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-LUR1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUR1-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-LUR1-R
gate:grep=^nd_up 1$:D3-LUR1-R
D3-LUR1-H?
D3-LUR1-D?
D3-LUR1-IL?
D3-LUR1-SN?
D3-LUS1-L
gate:grep=^4 packets transmitted, 4 received:D3-LUS1-L
gate:grep=^follower 1$:D3-LUS1-L
D3-LUS1-S0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-S0
gate:grep=^ *[0-9]+ +\S+ +\S+ +\S+ +iperf3 -s -1 -f k --logfile /tmp/lus1\.log *$:D3-LUS1-S0
D3-LUS1?
D3-LUS1-S1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-S1
D3-LUS1-P?
D3-LUS1-R
gate:until:D3-LUS1-R
gate:grep=^version rtl819x-nic 1\.5$:D3-LUS1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):D3-LUS1-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:D3-LUS1-R
gate:grep=^nd_up 1$:D3-LUS1-R
D3-LUS1-H?
D3-LUS1-D?
D3-LUS1-IL?
D3-LUS1-SN?
D3-SUM?
```

**`I-Z`** — the closing map, `n_writes` and the kernel log's last window; then the owner powers off

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
Z-DW?
Z-DWALL?
```

**What each stop means, decided now** — a repeat is always a new name, declared in
`bench/2026-09-26b/CORRECTIONS-block48.md` before it runs, **except the cells whose text this
section fixes now (they are logged there as they run) and a power-off, which this card decides
and which waits for nothing**:

* **The loader gate on any board cell** (the capture holds `Booting...`, `---RealTek`,
  `<RealTek>` or `Linux version`), or the same text in any other failed board cell's capture,
  which is read first: **the owner powers off at once**; no other cell and no `CORRECTIONS`
  entry comes before it. The capture-stop invocations still run (host only); `I-Z` does not,
  and the next card's first map closes this press's bracket. The rest is a new card.
* **`R0-PREC`**, **`R0-ADDR`**, **`R0-FL`**, **`R0-PCAP`**, **`R0-TCPC`**: as card 1's; no
  power until each reads as its gate asks. **`R0-DMSG`** `0`: the follower is not running —
  start it (§ 6 (3)) and run `R0-DMSG2`; `2` or more: another `dmesg` runs, its owner stops it.
  **`R0-DW0`**: an empty log or `follower` not 1 — no power until (3) is redone; a non-zero
  `bug_preempt`, `usbnet_xmit` or `call_trace` with the board off — no power; WSL is restarted
  and both devices re-attached once more ((1)–(4)), and if the fresh log is still not clean the
  owner decides. **`R0-IPF`**: the host's `iperf3` is not the pinned binary, or
  `qemu-mips-static` is absent — no power: `I-D3` could not run `NET-111`'s shapes, and the
  owner decides whether to press without it. **`R0-SUM`**, **`R0-ST`**: a checker is not the
  one this card pins, or fails its own self-test — no power. **`R0-VERB`** not `PASS`, or its
  self-test not all passed: a word the card types does not parse, or a refusal is not a gated
  guard — no power; the card is wrong and is not repaired (a new card).
* **`gate:caught`**, **`R1-FL`**, **`R1Q`**, **`R1-PS`**, the maps and `n_writes`: exactly as
  block 46's § 6 decides them, with this card's names.
* **`B-00-R`** or **`B-00-T`** (the boot is not 1.4's defaults with `rlx0` up, or the page is
  not 1.5's untouched state): no cell after it runs until the owner has read the page.
* **A liveness gate** (`-L`: fewer than 4 of 4, or `follower` not 1), **a port-3 gate** (`-LS`:
  `PSRP3` or `port_status` not `LinkUp`) **or a path gate** (`E-…-D`, `SF-…-D`, `SL-…-D`:
  `covered no`): the host → board path is the question (`NET-124`, `NET-54` 殘留). `follower`
  alone failing: the follower is restarted with (3)'s command with `>>` in place of `>` (it
  appends, so every `window_end` already read still points into the log), the liveness is typed
  again as (8)'s `X-L<n>`, and every kernel-log window since the last `follower 1` is void, and
  so is the next one on the card (it holds the ring the restart printed again). Otherwise,
  **before any recovery and with `rlx0` left as it is**, `NET-54` 殘留 ②'s read set in its order,
  as declared cells whose text is fixed here: (1) `X-SW<n>` `cat /proc/rtl819x-switch` —
  `MACCR`, `FFCR`, `SWTCR0` and `PSRP0/3/5/6/7` with bit 8, which this read clears on this
  image's switch driver 1.1, so it is first; `PSRP1/2/4` are not in its table, so ②'s *eight
  `PSRP`* is read as these five and `port_status`; (2) `X-PHY<n>`
  `echo read 3 0 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg ; echo read 3 1 > /proc/rtl865x/phyReg`
  — port 3's PHY `BMCR` and `BMSR` (`NET-124` 殘留's `phyReg`; the write-side read form 讀
  `bench/2026-09-19/CORRECTIONS-block27.md` F6, 量 `C20-PHYST` on port 0), `BMSR` twice because
  its link bit latches low until read: the first read says whether the link fell, the second
  what it is now; (3) `X-BR<n>`, the full board bracket (`asicCounter`'s port 3 and CPU port)
  between `X-HP<n>` (`HP`) and (5); (4) `X-PS<n>` `cat /proc/rtl865x/port_status`, last; (5)
  `X-HN<n>` on the host, `HN` (no kernel-log window: the next one on the card spans the whole
  episode). Then the recovery, a software action on the host, which runs without the owner's
  word (CLAUDE.md waits for it only for power and physical actions; card 1's § 6 ran the same
  recovery so, by the coordinator's ruling 5a): (6) `X-RA<n>` — from PowerShell, `usbipd list`
  read fresh for the GbE adapter's busid (never the CP2102's), `usbipd detach --busid <b>`,
  `usbipd attach --wsl --busid <b>`, reading what each prints, then `R0-ADDR`'s command again
  in WSL; (7) `X-SW<n>b`, `X-PHY<n>b` and `X-PS<n>b`, the text of (1), (2) and (4) after it —
  they say whether a re-attach bounces port 3's link; a re-attach also ends the running
  `tcpdump` (its interface goes away) and restarts the adapter's `rx_packets`, so `X-TC<n>`
  (`pgrep -xc tcpdump ; true`) reads what runs, that capture's record-order anchor is void (P0
  (c)), and before the invocation continues the capture is started again once as the off-card
  `W-TCPE2` / `W-TCPS2` (`TDE WE2.pcap` / `TDS WS2.pcap`), whose read-time windows then decide
  every later arm's capture readings (P5, P7), marked so; (8) `X-L<n>`,
  `FL 10.1.1.3 ; PL ; DW none` — the liveness gate again, and the whole log counted (a
  reading); none of the recovery's cells writes a log a chained list names. If it passes: the
  invocation continues `--from` the cell after the failed one, and an arm whose path gate
  failed is void, never a result — in `I-E`, `F1` void leaves `F2` as the fix's arm, `L1` void
  leaves this boot without `D2`'s positive control; in `I-S`, that length is unmeasured at that
  setting on this boot and the other setting's arm there is a reading (no repeat: a repeat's
  chained lists would not be ones the generator proved); in `I-D3`, the invocation continues
  `--from` the trial's `-S0`. If it fails: the arms that need the host are skipped — after a
  failure in `I-E` or `I-S` the run continues with `I-WE9`, `I-WS0`, `I-W`, `I-WS9` and `I-Z`
  (`I-U` and `I-D3` are not run), after one in `I-U` or `I-D3` with `I-Z` — the loopback and
  wire sweeps still run (their verdicts are the board's counters; the host's are void), and the
  last liveness cells are readings.
* **WSL itself stops mid-press**: the board is left as it is; WSL is started again with (2)'s
  keeper, the follower with (3)'s command with `>>` in place of `>`, the GbE adapter
  re-attached as the recovery's (6) above (the CP2102 too, if `usbipd list` shows it detached);
  `R0-PRE`'s form is run as `X-PRE<n>` with the board on (3 s, bytes are a reading). The
  interrupted invocation then continues `--from` the interrupted cell if that cell left no log.
  If it left one: a board read is typed again as its stand-in `X-<read>` (as a failed read is,
  below), a sweep or a stimulus is handled as its own kind's failure below, and a host cell's
  partial log stands as its record; the invocation continues `--from` the cell after it, and a
  reader chained to a partial log that holds no `window_end` reports it unreadable (exit 3, a
  reading). The bracket that spans the outage is void, and so is the record-order anchor of the
  capture that was running (P0 (c)).
* **A board bracket's gate** (`until`, `version`, `tx15`, `nd_up`) with no loader text:
  `/dev/ttyUSB0` is checked and the read typed again as its **stand-in `X-<read>`** (the read's
  text under that name, e.g. `X-SF-0061-R1`); if it passes, it stands in and the invocation
  continues `--from` the next cell — every pair after it names `X-<read>` right after `<read>`,
  and `brdelta` reads the last that exists. A `tx15` that is not the arm's policy at an arm's
  first read (`-R0`, `D3-00-R`, `D3-X-00-R`): the switch cell is typed again once as `X-SW<n>`
  and then the read as `X-<read>`; if that matches, it stands in as above; a second mismatch
  voids that arm, and the invocation continues `--from` the cell after the arm's last cell (the
  next arm's switch; after `E-F2-R0` or `SL-1514-R0`, the invocation's end; after `D3-00-R`,
  `D3-X-SW`, the trials at the fix then unmeasured; after `D3-X-00-R`, `D3-SUM`); a second arm
  voided so on this press: no cell runs until the owner has read the page. At any later read of
  an arm (`-R1`, a trial's `-R`) no policy verb has been typed since a read that matched, and
  retyping the switch would destroy the state the read holds: no cell runs until the owner has
  read the page. **If the read returns nothing, garbage, or never ends on the prompt, the owner
  powers off.**
* **A sweep cell's `v15 last sweep` gate with a refusal** (-16, -17, -1, -6 or -22 on the
  page): the board's state is not the one the card and `R0-VERB` simulated; the invocation
  stops, the page is read, and nothing is typed until the decision is in
  `CORRECTIONS-block48.md`. A sweep ended by an errno after it opened (-71, -61, -145, -4, or
  `sw fail`/`intr`) passes its gates: a reading. **A sweep cell's `until`** (no page within its
  cap), no loader text: `X-RT<n>`, `cat /proc/rtl819x-nic-tx`; if the page answers, the sweep's
  state is recorded and the invocation continues `--from` the next cell; **if it does not
  answer within 15 s the board is hung: a reading, and the owner powers off**.
* **`W-00-K`** (`rlx0` not down, IRQ not taken, engine on, or the policy not
  `rlxfw … dirty 1`): no sweep runs; `X-K<n>`, the text of `W-00-DN` then `W-00-K`, once; if it
  fails again, no cell of `I-W` runs until the owner has read the page.
* **`LB-P-1511`'s `mt` gate** (not `bad_b 2`): with `void` > 0, the VOID rule of card 1's § 3.5
  — each VOID length is swept again once in loopback under the same key as the declared cell
  `X-VD<n>` (`echo sweep L L 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx`), and if the
  page then reads `bad_b 2` the invocation continues `--from LB-P-C`. Otherwise (the positive
  control failed: P10's refutation): no multi-length wire sweep runs; `I-W` continues
  `--from W-2-V` (the single-length wire sweeps still run: their verdicts are counters), and
  `D2`'s sweep conjunct is unmeasured on this boot.
* **`W-00`** (the fix's loopback map not clean, complete and registered at `delta0 0`): no
  multi-length wire sweep runs. If only `void` is non-zero, card 1's VOID rule applies with the
  host's Δ`tx_packets` over `LB-P-H` → `LB-V-H`: Δ 0 — `W-1` does not run; Δ > 0 — the
  `X-VD<n>` re-sweeps, then `X-W00` (the text of `W-00`, reading
  `mt none 0 clean 1455 bad_b 0 bad_a 0 void 0 skew 0` instead of its `sw done` and `sw scored`
  gates), and `W-1` runs `--from W-1a-S` only if it passes. Any other failure: `I-W` continues
  `--from W-2-V`, and `D2`'s sweep conjunct is unmeasured on this boot (P11's refutation, not a
  wire result).
* **A wire quarter's `fault jfd 0`** (`W-1a-D` … `W-1d-D`): `D2`'s sweep conjunct fails on this
  boot (P12); the later quarters do not run; `I-W` continues `--from W-2-V`.
* **`W-2-EP`** (its page's `v15 last sweep` not -1: the owner's bound not refusing as written):
  recorded as found, and `W-2` runs (its sweeps are single-length, and the first clears the
  records); the sweep-refusal rule above does not apply to this cell, whose refusal is its
  point.
* **`E-LIVE`** / **`S-LIVE`** `0`: the capture is not running — its invocation's transcript is
  read, and it is started again once as the off-card `W-TCPE2` / `W-TCPS2`; if that fails, the
  arms run without it (P0 (c) and the capture's readings are then untested, the counters
  stand). `2` or more: another `tcpdump` runs, its owner stops it.
* **`D3-<t>-S0`'s `ps` gate** (the trial's own server is not running): the declared cell
  `X-<t>-S0R`,
  `busybox killall iperf3 ; sleep 1 ; iperf3 -s -1 -f k --logfile /tmp/<t>.log > /dev/null 2>&1 & sleep 2 ; ps`
  (`--idle 6 --seconds 30`: its silence is the two sleeps, about 3.05 s, since the `&` prints
  nothing), once; if its `ps` shows the row, the invocation continues `--from D3-<t>`; if not,
  that trial is not run (recorded as not run, never as failed) and the invocation continues
  `--from` the cell after the trial's last cell (the next trial's `-L`; after `US3`, `D3-X-SW`;
  after `LUS1`, `D3-SUM`); a second trial not run: `I-D3` ends there and `I-Z` runs.
* **A stimulus or switch cell exits non-zero** with no loader text (its capture did not end as
  its `--idle` expects): `/dev/ttyUSB0` is checked and `X-RT<n>`, the board read's text, is
  typed (not a stand-in: no list names it); if rlxfw answers, the invocation continues `--from`
  the cell after the stimulus, and the arm's next read decides it (a switch that did not take
  fails that read's `tx15` or `nd_up` gate, above).
* **The press runs long**: after `I-U`, if more than 27 minutes have passed since the catch
  window opened (the estimate puts `I-U`'s end at about 20), `I-D3` is not run: `D3`'s first
  boot and `NET-117` 殘留 move to card 3 (`NOTES-card3.txt` in the card's working directory), and
  `I-Z` runs (its `Z-DW` list holds `I-U`'s last window, which that path wrote). Why 27: with
  the catch window opening at 23:00 at the latest, an `I-D3` started at minute 27 whose every
  trial runs to `timeout 70` puts the press's end, `I-Z` included, at about minute 49 (§ 2),
  23:49, which keeps every capture of the press on the declared date 2026-09-26 with 10 minutes
  before 23:59 (`tools/capdate.py` checks `bench/<date>/` against the captures' day); 27 is the
  owner's answer of 2026-09-26.
* **A host stimulus, a host bracket, a checker's reading, a capture stop, an `iperf3` trial**:
  `NAME?`; never a stop. **A background cell's exit** never stops a run.
* **Anything not listed**: no cell runs until the owner has read it; the decision goes into
  `CORRECTIONS-block48.md` first.

---

## § 7 What this block does not establish

* **The fix under load or over time**: `R6b-4` (`NET-67` 殘留, 30 minutes of traffic that
  includes every formerly bad length). The twelve trials are 30 s each.
* **`D3` on two boots.** This is boot 1; boot 2 is card 3's, with `D3-MISS` ① and ② and `P2`'s
  quiet-image cold boot (ADJ R11: not in seating 42).
* **The stage as the TX DMA engine.** Nothing between descriptor memory and the CPU port's
  receive MAC is measured; P8 places the change between them (推 from 量 parts), and the
  descriptor read-back is block 47's, not repeated here. Nor what the engine fetched.
* **Any mechanism as a cause.** M1-cover8 is the rule left standing, fitted after blocks 45–46
  (推); the per-frame predictions apply it, and a pass leaves it standing, one boot more.
* **The o-identity's cause**, unless a bracket falls under P9 (i) or (ii).
* **Why the UDP datagrams die** where P18 places them: the counter says where, not why; and
  whether `eth4`'s 69 % loss (`NET-117`) dies in the same place — `eth4` is not run here.
* **The fix on the stack path outside E2's eleven lengths**, the 60-B liveness frames and what
  the twelve trials carry; the wire sweep covers every length through `nic_do_tx` in TX slots 0
  and 1 only.
* **The wire's content past 64 bytes**: both captures are cut at 64 B; `D3` runs uncaptured, so
  a failed exchange at the fix is named from the counters, the logs and the ring, not from the
  frames. And the captures' effect on the host (`D3-MISS` ②'s question) is card 3's.
* **The stack arm at another spacing**: `I-S` runs every length at E2's `-i 0.05` only; an
  isolated spacing (M3's other half) is not run, so a spacing effect at a clean length is not
  excluded here.
* **Reply 2 at 61–63 when k is 1 to 5** (P7's decision rule): which branch reply 2 took where
  more than one frame of its length is wrong (the counters are the bracket's); under (b), why a
  legal wrong frame is discarded, past the CPU port's `Drop`; under (a), any byte of it past
  64. No wrong frame of a legal length has been seen to reach the host: block 47's `E-L1` read
  `jab` 581 beside `frag` 3 and `drop` 41, and 3 frames in the 512–1023 bucket that none of the
  bracket's 168 host frames matches (量) — so not every wrong frame read so far was a jabber,
  but none that was not reached the host — and its nine mid-stream cases were (b)- or
  (c)-shaped (P7). H-prev's absolute offset is read at 277 alone (the TCI); at 61–63 it is 推. k
  = 0 and k = 6 are not predicted.
* **Which frame of a bracket the CPU port refused**: how many; P7's per-frame reading rests on
  the capture's answered sequence numbers and the bracket's counts, by elimination (推).
* **The `-EBUSY` a second writer meets while a sweep runs** (one console), and every 1.5 guard
  but the wire bound: read on block 47 (P2 there held) and not repeated.
* **The host adapter's own drops** (`r8153_ecm` has no tally counters), and why `NET-124`
  happened, unless it happens again.
* **`NET-38` 殘留 ③ and `NET-41` 殘留**: ⊘ by their own condition after block 47 (ADJ R7), reopened
  only if this card's fix arm faults.
* A flash write by anything but rlxfw's SPI driver between the two maps that the map does not
  see (`FLS-30`'s limits); `H601`'s 8,192 B are never hashed.

---

```cells
bench/2026-09-26b/R0-PRE
bench/2026-09-26b/R0-PREC
bench/2026-09-26b/R0-ADDR
bench/2026-09-26b/R0-ETH
bench/2026-09-26b/R0-TCPC
bench/2026-09-26b/R0-DMSG
bench/2026-09-26b/R0-DW0
bench/2026-09-26b/R0-FL
bench/2026-09-26b/R0-PCAP
bench/2026-09-26b/R0-IPF
bench/2026-09-26b/R0-SUM
bench/2026-09-26b/R0-ST
bench/2026-09-26b/R0-VERB
bench/2026-09-26b/R0-H
bench/2026-09-26b/R1-CATCH
bench/2026-09-26b/R1-FL
bench/2026-09-26b/R1Q
bench/2026-09-26b/R1-PS
bench/2026-09-26b/R1-M0
bench/2026-09-26b/R1-MB0
bench/2026-09-26b/R1-NW0
bench/2026-09-26b/B-00-P
bench/2026-09-26b/B-00-R
bench/2026-09-26b/B-00-H
bench/2026-09-26b/B-00-T
bench/2026-09-26b/W-TCPE
bench/2026-09-26b/E-LIVE
bench/2026-09-26b/E-F1-SW
bench/2026-09-26b/E-F1-LS
bench/2026-09-26b/E-F1-L
bench/2026-09-26b/E-F1-P0
bench/2026-09-26b/E-F1-R0
bench/2026-09-26b/E-F1-H0
bench/2026-09-26b/E-F1-E2
bench/2026-09-26b/E-F1-P1
bench/2026-09-26b/E-F1-R1
bench/2026-09-26b/E-F1-H1
bench/2026-09-26b/E-F1-D
bench/2026-09-26b/E-L1-SW
bench/2026-09-26b/E-L1-LS
bench/2026-09-26b/E-L1-L
bench/2026-09-26b/E-L1-P0
bench/2026-09-26b/E-L1-R0
bench/2026-09-26b/E-L1-H0
bench/2026-09-26b/E-L1-E2
bench/2026-09-26b/E-L1-P1
bench/2026-09-26b/E-L1-R1
bench/2026-09-26b/E-L1-H1
bench/2026-09-26b/E-L1-D
bench/2026-09-26b/E-F2-SW
bench/2026-09-26b/E-F2-LS
bench/2026-09-26b/E-F2-L
bench/2026-09-26b/E-F2-P0
bench/2026-09-26b/E-F2-R0
bench/2026-09-26b/E-F2-H0
bench/2026-09-26b/E-F2-E2
bench/2026-09-26b/E-F2-P1
bench/2026-09-26b/E-F2-R1
bench/2026-09-26b/E-F2-H1
bench/2026-09-26b/E-F2-D
bench/2026-09-26b/SF-0060-SW
bench/2026-09-26b/SF-0060-LS
bench/2026-09-26b/SF-0060-L
bench/2026-09-26b/SF-0060-P0
bench/2026-09-26b/SF-0060-R0
bench/2026-09-26b/SF-0060-H0
bench/2026-09-26b/SF-0060-PG
bench/2026-09-26b/SF-0060-P1
bench/2026-09-26b/SF-0060-R1
bench/2026-09-26b/SF-0060-H1
bench/2026-09-26b/SF-0060-D
bench/2026-09-26b/SL-0060-SW
bench/2026-09-26b/SL-0060-LS
bench/2026-09-26b/SL-0060-L
bench/2026-09-26b/SL-0060-P0
bench/2026-09-26b/SL-0060-R0
bench/2026-09-26b/SL-0060-H0
bench/2026-09-26b/SL-0060-PG
bench/2026-09-26b/SL-0060-P1
bench/2026-09-26b/SL-0060-R1
bench/2026-09-26b/SL-0060-H1
bench/2026-09-26b/SL-0060-D
bench/2026-09-26b/SF-0061-SW
bench/2026-09-26b/SF-0061-LS
bench/2026-09-26b/SF-0061-L
bench/2026-09-26b/SF-0061-P0
bench/2026-09-26b/SF-0061-R0
bench/2026-09-26b/SF-0061-H0
bench/2026-09-26b/SF-0061-PG
bench/2026-09-26b/SF-0061-P1
bench/2026-09-26b/SF-0061-R1
bench/2026-09-26b/SF-0061-H1
bench/2026-09-26b/SF-0061-D
bench/2026-09-26b/SL-0061-SW
bench/2026-09-26b/SL-0061-LS
bench/2026-09-26b/SL-0061-L
bench/2026-09-26b/SL-0061-P0
bench/2026-09-26b/SL-0061-R0
bench/2026-09-26b/SL-0061-H0
bench/2026-09-26b/SL-0061-PG
bench/2026-09-26b/SL-0061-P1
bench/2026-09-26b/SL-0061-R1
bench/2026-09-26b/SL-0061-H1
bench/2026-09-26b/SL-0061-D
bench/2026-09-26b/SF-0062-SW
bench/2026-09-26b/SF-0062-LS
bench/2026-09-26b/SF-0062-L
bench/2026-09-26b/SF-0062-P0
bench/2026-09-26b/SF-0062-R0
bench/2026-09-26b/SF-0062-H0
bench/2026-09-26b/SF-0062-PG
bench/2026-09-26b/SF-0062-P1
bench/2026-09-26b/SF-0062-R1
bench/2026-09-26b/SF-0062-H1
bench/2026-09-26b/SF-0062-D
bench/2026-09-26b/SL-0062-SW
bench/2026-09-26b/SL-0062-LS
bench/2026-09-26b/SL-0062-L
bench/2026-09-26b/SL-0062-P0
bench/2026-09-26b/SL-0062-R0
bench/2026-09-26b/SL-0062-H0
bench/2026-09-26b/SL-0062-PG
bench/2026-09-26b/SL-0062-P1
bench/2026-09-26b/SL-0062-R1
bench/2026-09-26b/SL-0062-H1
bench/2026-09-26b/SL-0062-D
bench/2026-09-26b/SF-0063-SW
bench/2026-09-26b/SF-0063-LS
bench/2026-09-26b/SF-0063-L
bench/2026-09-26b/SF-0063-P0
bench/2026-09-26b/SF-0063-R0
bench/2026-09-26b/SF-0063-H0
bench/2026-09-26b/SF-0063-PG
bench/2026-09-26b/SF-0063-P1
bench/2026-09-26b/SF-0063-R1
bench/2026-09-26b/SF-0063-H1
bench/2026-09-26b/SF-0063-D
bench/2026-09-26b/SL-0063-SW
bench/2026-09-26b/SL-0063-LS
bench/2026-09-26b/SL-0063-L
bench/2026-09-26b/SL-0063-P0
bench/2026-09-26b/SL-0063-R0
bench/2026-09-26b/SL-0063-H0
bench/2026-09-26b/SL-0063-PG
bench/2026-09-26b/SL-0063-P1
bench/2026-09-26b/SL-0063-R1
bench/2026-09-26b/SL-0063-H1
bench/2026-09-26b/SL-0063-D
bench/2026-09-26b/SF-0263-SW
bench/2026-09-26b/SF-0263-LS
bench/2026-09-26b/SF-0263-L
bench/2026-09-26b/SF-0263-P0
bench/2026-09-26b/SF-0263-R0
bench/2026-09-26b/SF-0263-H0
bench/2026-09-26b/SF-0263-PG
bench/2026-09-26b/SF-0263-P1
bench/2026-09-26b/SF-0263-R1
bench/2026-09-26b/SF-0263-H1
bench/2026-09-26b/SF-0263-D
bench/2026-09-26b/SL-0263-SW
bench/2026-09-26b/SL-0263-LS
bench/2026-09-26b/SL-0263-L
bench/2026-09-26b/SL-0263-P0
bench/2026-09-26b/SL-0263-R0
bench/2026-09-26b/SL-0263-H0
bench/2026-09-26b/SL-0263-PG
bench/2026-09-26b/SL-0263-P1
bench/2026-09-26b/SL-0263-R1
bench/2026-09-26b/SL-0263-H1
bench/2026-09-26b/SL-0263-D
bench/2026-09-26b/SF-0276-SW
bench/2026-09-26b/SF-0276-LS
bench/2026-09-26b/SF-0276-L
bench/2026-09-26b/SF-0276-P0
bench/2026-09-26b/SF-0276-R0
bench/2026-09-26b/SF-0276-H0
bench/2026-09-26b/SF-0276-PG
bench/2026-09-26b/SF-0276-P1
bench/2026-09-26b/SF-0276-R1
bench/2026-09-26b/SF-0276-H1
bench/2026-09-26b/SF-0276-D
bench/2026-09-26b/SL-0276-SW
bench/2026-09-26b/SL-0276-LS
bench/2026-09-26b/SL-0276-L
bench/2026-09-26b/SL-0276-P0
bench/2026-09-26b/SL-0276-R0
bench/2026-09-26b/SL-0276-H0
bench/2026-09-26b/SL-0276-PG
bench/2026-09-26b/SL-0276-P1
bench/2026-09-26b/SL-0276-R1
bench/2026-09-26b/SL-0276-H1
bench/2026-09-26b/SL-0276-D
bench/2026-09-26b/SF-0277-SW
bench/2026-09-26b/SF-0277-LS
bench/2026-09-26b/SF-0277-L
bench/2026-09-26b/SF-0277-P0
bench/2026-09-26b/SF-0277-R0
bench/2026-09-26b/SF-0277-H0
bench/2026-09-26b/SF-0277-PG
bench/2026-09-26b/SF-0277-P1
bench/2026-09-26b/SF-0277-R1
bench/2026-09-26b/SF-0277-H1
bench/2026-09-26b/SF-0277-D
bench/2026-09-26b/SL-0277-SW
bench/2026-09-26b/SL-0277-LS
bench/2026-09-26b/SL-0277-L
bench/2026-09-26b/SL-0277-P0
bench/2026-09-26b/SL-0277-R0
bench/2026-09-26b/SL-0277-H0
bench/2026-09-26b/SL-0277-PG
bench/2026-09-26b/SL-0277-P1
bench/2026-09-26b/SL-0277-R1
bench/2026-09-26b/SL-0277-H1
bench/2026-09-26b/SL-0277-D
bench/2026-09-26b/SF-1511-SW
bench/2026-09-26b/SF-1511-LS
bench/2026-09-26b/SF-1511-L
bench/2026-09-26b/SF-1511-P0
bench/2026-09-26b/SF-1511-R0
bench/2026-09-26b/SF-1511-H0
bench/2026-09-26b/SF-1511-PG
bench/2026-09-26b/SF-1511-P1
bench/2026-09-26b/SF-1511-R1
bench/2026-09-26b/SF-1511-H1
bench/2026-09-26b/SF-1511-D
bench/2026-09-26b/SL-1511-SW
bench/2026-09-26b/SL-1511-LS
bench/2026-09-26b/SL-1511-L
bench/2026-09-26b/SL-1511-P0
bench/2026-09-26b/SL-1511-R0
bench/2026-09-26b/SL-1511-H0
bench/2026-09-26b/SL-1511-PG
bench/2026-09-26b/SL-1511-P1
bench/2026-09-26b/SL-1511-R1
bench/2026-09-26b/SL-1511-H1
bench/2026-09-26b/SL-1511-D
bench/2026-09-26b/SF-1512-SW
bench/2026-09-26b/SF-1512-LS
bench/2026-09-26b/SF-1512-L
bench/2026-09-26b/SF-1512-P0
bench/2026-09-26b/SF-1512-R0
bench/2026-09-26b/SF-1512-H0
bench/2026-09-26b/SF-1512-PG
bench/2026-09-26b/SF-1512-P1
bench/2026-09-26b/SF-1512-R1
bench/2026-09-26b/SF-1512-H1
bench/2026-09-26b/SF-1512-D
bench/2026-09-26b/SL-1512-SW
bench/2026-09-26b/SL-1512-LS
bench/2026-09-26b/SL-1512-L
bench/2026-09-26b/SL-1512-P0
bench/2026-09-26b/SL-1512-R0
bench/2026-09-26b/SL-1512-H0
bench/2026-09-26b/SL-1512-PG
bench/2026-09-26b/SL-1512-P1
bench/2026-09-26b/SL-1512-R1
bench/2026-09-26b/SL-1512-H1
bench/2026-09-26b/SL-1512-D
bench/2026-09-26b/SF-1513-SW
bench/2026-09-26b/SF-1513-LS
bench/2026-09-26b/SF-1513-L
bench/2026-09-26b/SF-1513-P0
bench/2026-09-26b/SF-1513-R0
bench/2026-09-26b/SF-1513-H0
bench/2026-09-26b/SF-1513-PG
bench/2026-09-26b/SF-1513-P1
bench/2026-09-26b/SF-1513-R1
bench/2026-09-26b/SF-1513-H1
bench/2026-09-26b/SF-1513-D
bench/2026-09-26b/SL-1513-SW
bench/2026-09-26b/SL-1513-LS
bench/2026-09-26b/SL-1513-L
bench/2026-09-26b/SL-1513-P0
bench/2026-09-26b/SL-1513-R0
bench/2026-09-26b/SL-1513-H0
bench/2026-09-26b/SL-1513-PG
bench/2026-09-26b/SL-1513-P1
bench/2026-09-26b/SL-1513-R1
bench/2026-09-26b/SL-1513-H1
bench/2026-09-26b/SL-1513-D
bench/2026-09-26b/SF-1514-SW
bench/2026-09-26b/SF-1514-LS
bench/2026-09-26b/SF-1514-L
bench/2026-09-26b/SF-1514-P0
bench/2026-09-26b/SF-1514-R0
bench/2026-09-26b/SF-1514-H0
bench/2026-09-26b/SF-1514-PG
bench/2026-09-26b/SF-1514-P1
bench/2026-09-26b/SF-1514-R1
bench/2026-09-26b/SF-1514-H1
bench/2026-09-26b/SF-1514-D
bench/2026-09-26b/SL-1514-SW
bench/2026-09-26b/SL-1514-LS
bench/2026-09-26b/SL-1514-L
bench/2026-09-26b/SL-1514-P0
bench/2026-09-26b/SL-1514-R0
bench/2026-09-26b/SL-1514-H0
bench/2026-09-26b/SL-1514-PG
bench/2026-09-26b/SL-1514-P1
bench/2026-09-26b/SL-1514-R1
bench/2026-09-26b/SL-1514-H1
bench/2026-09-26b/SL-1514-D
bench/2026-09-26b/W-TCPEX
bench/2026-09-26b/W-EWALL
bench/2026-09-26b/W-EORD
bench/2026-09-26b/W-TCPS
bench/2026-09-26b/S-LIVE
bench/2026-09-26b/W-00-DN
bench/2026-09-26b/W-00-K
bench/2026-09-26b/W-00-P
bench/2026-09-26b/W-00-R
bench/2026-09-26b/W-00-H
bench/2026-09-26b/LB-P-0061
bench/2026-09-26b/LB-P-1511
bench/2026-09-26b/LB-P-C
bench/2026-09-26b/LB-P-P
bench/2026-09-26b/LB-P-R
bench/2026-09-26b/LB-P-H
bench/2026-09-26b/LB-P-D
bench/2026-09-26b/LB-V-V
bench/2026-09-26b/LB-V-S
bench/2026-09-26b/LB-V-C
bench/2026-09-26b/LB-V-P
bench/2026-09-26b/LB-V-R
bench/2026-09-26b/LB-V-H
bench/2026-09-26b/LB-V-D
bench/2026-09-26b/W-00
bench/2026-09-26b/W-1a-S
bench/2026-09-26b/W-1a-P
bench/2026-09-26b/W-1a-R
bench/2026-09-26b/W-1a-H
bench/2026-09-26b/W-1a-D
bench/2026-09-26b/W-1b-S
bench/2026-09-26b/W-1b-P
bench/2026-09-26b/W-1b-R
bench/2026-09-26b/W-1b-H
bench/2026-09-26b/W-1b-D
bench/2026-09-26b/W-1c-S
bench/2026-09-26b/W-1c-P
bench/2026-09-26b/W-1c-R
bench/2026-09-26b/W-1c-H
bench/2026-09-26b/W-1c-D
bench/2026-09-26b/W-1d-S
bench/2026-09-26b/W-1d-P
bench/2026-09-26b/W-1d-R
bench/2026-09-26b/W-1d-H
bench/2026-09-26b/W-1d-D
bench/2026-09-26b/W-2-V
bench/2026-09-26b/W-2-EP
bench/2026-09-26b/W-2-0060-S
bench/2026-09-26b/W-2-0060-P
bench/2026-09-26b/W-2-0060-R
bench/2026-09-26b/W-2-0060-H
bench/2026-09-26b/W-2-0060-D
bench/2026-09-26b/W-2-0061-S
bench/2026-09-26b/W-2-0061-P
bench/2026-09-26b/W-2-0061-R
bench/2026-09-26b/W-2-0061-H
bench/2026-09-26b/W-2-0061-D
bench/2026-09-26b/W-2-0062-S
bench/2026-09-26b/W-2-0062-P
bench/2026-09-26b/W-2-0062-R
bench/2026-09-26b/W-2-0062-H
bench/2026-09-26b/W-2-0062-D
bench/2026-09-26b/W-2-0063-S
bench/2026-09-26b/W-2-0063-P
bench/2026-09-26b/W-2-0063-R
bench/2026-09-26b/W-2-0063-H
bench/2026-09-26b/W-2-0063-D
bench/2026-09-26b/W-2-0263-S
bench/2026-09-26b/W-2-0263-P
bench/2026-09-26b/W-2-0263-R
bench/2026-09-26b/W-2-0263-H
bench/2026-09-26b/W-2-0263-D
bench/2026-09-26b/W-2-0276-S
bench/2026-09-26b/W-2-0276-P
bench/2026-09-26b/W-2-0276-R
bench/2026-09-26b/W-2-0276-H
bench/2026-09-26b/W-2-0276-D
bench/2026-09-26b/W-2-0277-S
bench/2026-09-26b/W-2-0277-P
bench/2026-09-26b/W-2-0277-R
bench/2026-09-26b/W-2-0277-H
bench/2026-09-26b/W-2-0277-D
bench/2026-09-26b/W-2-1511-S
bench/2026-09-26b/W-2-1511-P
bench/2026-09-26b/W-2-1511-R
bench/2026-09-26b/W-2-1511-H
bench/2026-09-26b/W-2-1511-D
bench/2026-09-26b/W-2-1512-S
bench/2026-09-26b/W-2-1512-P
bench/2026-09-26b/W-2-1512-R
bench/2026-09-26b/W-2-1512-H
bench/2026-09-26b/W-2-1512-D
bench/2026-09-26b/W-2-1513-S
bench/2026-09-26b/W-2-1513-P
bench/2026-09-26b/W-2-1513-R
bench/2026-09-26b/W-2-1513-H
bench/2026-09-26b/W-2-1513-D
bench/2026-09-26b/W-2-1514-S
bench/2026-09-26b/W-2-1514-P
bench/2026-09-26b/W-2-1514-R
bench/2026-09-26b/W-2-1514-H
bench/2026-09-26b/W-2-1514-D
bench/2026-09-26b/W-TCPSX
bench/2026-09-26b/W-SWALL
bench/2026-09-26b/W-SORD
bench/2026-09-26b/W-9-UP
bench/2026-09-26b/W-9-LS
bench/2026-09-26b/W-9-L
bench/2026-09-26b/W-9-P
bench/2026-09-26b/W-9-R
bench/2026-09-26b/W-9-H
bench/2026-09-26b/D3-SW
bench/2026-09-26b/D3-LS
bench/2026-09-26b/D3-L
bench/2026-09-26b/D3-00-P
bench/2026-09-26b/D3-00-R
bench/2026-09-26b/D3-00-H
bench/2026-09-26b/D3-TR1-L
bench/2026-09-26b/D3-TR1-S0
bench/2026-09-26b/D3-TR1
bench/2026-09-26b/D3-TR1-S1
bench/2026-09-26b/D3-TR1-P
bench/2026-09-26b/D3-TR1-R
bench/2026-09-26b/D3-TR1-H
bench/2026-09-26b/D3-TR1-D
bench/2026-09-26b/D3-TR1-IL
bench/2026-09-26b/D3-TR1-SN
bench/2026-09-26b/D3-TR1-IC
bench/2026-09-26b/D3-TR2-L
bench/2026-09-26b/D3-TR2-S0
bench/2026-09-26b/D3-TR2
bench/2026-09-26b/D3-TR2-S1
bench/2026-09-26b/D3-TR2-P
bench/2026-09-26b/D3-TR2-R
bench/2026-09-26b/D3-TR2-H
bench/2026-09-26b/D3-TR2-D
bench/2026-09-26b/D3-TR2-IL
bench/2026-09-26b/D3-TR2-SN
bench/2026-09-26b/D3-TR2-IC
bench/2026-09-26b/D3-TR3-L
bench/2026-09-26b/D3-TR3-S0
bench/2026-09-26b/D3-TR3
bench/2026-09-26b/D3-TR3-S1
bench/2026-09-26b/D3-TR3-P
bench/2026-09-26b/D3-TR3-R
bench/2026-09-26b/D3-TR3-H
bench/2026-09-26b/D3-TR3-D
bench/2026-09-26b/D3-TR3-IL
bench/2026-09-26b/D3-TR3-SN
bench/2026-09-26b/D3-TR3-IC
bench/2026-09-26b/D3-TS1-L
bench/2026-09-26b/D3-TS1-S0
bench/2026-09-26b/D3-TS1
bench/2026-09-26b/D3-TS1-S1
bench/2026-09-26b/D3-TS1-P
bench/2026-09-26b/D3-TS1-R
bench/2026-09-26b/D3-TS1-H
bench/2026-09-26b/D3-TS1-D
bench/2026-09-26b/D3-TS1-IL
bench/2026-09-26b/D3-TS1-SN
bench/2026-09-26b/D3-TS2-L
bench/2026-09-26b/D3-TS2-S0
bench/2026-09-26b/D3-TS2
bench/2026-09-26b/D3-TS2-S1
bench/2026-09-26b/D3-TS2-P
bench/2026-09-26b/D3-TS2-R
bench/2026-09-26b/D3-TS2-H
bench/2026-09-26b/D3-TS2-D
bench/2026-09-26b/D3-TS2-IL
bench/2026-09-26b/D3-TS2-SN
bench/2026-09-26b/D3-TS3-L
bench/2026-09-26b/D3-TS3-S0
bench/2026-09-26b/D3-TS3
bench/2026-09-26b/D3-TS3-S1
bench/2026-09-26b/D3-TS3-P
bench/2026-09-26b/D3-TS3-R
bench/2026-09-26b/D3-TS3-H
bench/2026-09-26b/D3-TS3-D
bench/2026-09-26b/D3-TS3-IL
bench/2026-09-26b/D3-TS3-SN
bench/2026-09-26b/D3-UR1-L
bench/2026-09-26b/D3-UR1-S0
bench/2026-09-26b/D3-UR1
bench/2026-09-26b/D3-UR1-S1
bench/2026-09-26b/D3-UR1-P
bench/2026-09-26b/D3-UR1-R
bench/2026-09-26b/D3-UR1-H
bench/2026-09-26b/D3-UR1-D
bench/2026-09-26b/D3-UR1-IL
bench/2026-09-26b/D3-UR1-SN
bench/2026-09-26b/D3-UR1-IC
bench/2026-09-26b/D3-UR2-L
bench/2026-09-26b/D3-UR2-S0
bench/2026-09-26b/D3-UR2
bench/2026-09-26b/D3-UR2-S1
bench/2026-09-26b/D3-UR2-P
bench/2026-09-26b/D3-UR2-R
bench/2026-09-26b/D3-UR2-H
bench/2026-09-26b/D3-UR2-D
bench/2026-09-26b/D3-UR2-IL
bench/2026-09-26b/D3-UR2-SN
bench/2026-09-26b/D3-UR2-IC
bench/2026-09-26b/D3-UR3-L
bench/2026-09-26b/D3-UR3-S0
bench/2026-09-26b/D3-UR3
bench/2026-09-26b/D3-UR3-S1
bench/2026-09-26b/D3-UR3-P
bench/2026-09-26b/D3-UR3-R
bench/2026-09-26b/D3-UR3-H
bench/2026-09-26b/D3-UR3-D
bench/2026-09-26b/D3-UR3-IL
bench/2026-09-26b/D3-UR3-SN
bench/2026-09-26b/D3-UR3-IC
bench/2026-09-26b/D3-US1-L
bench/2026-09-26b/D3-US1-S0
bench/2026-09-26b/D3-US1
bench/2026-09-26b/D3-US1-S1
bench/2026-09-26b/D3-US1-P
bench/2026-09-26b/D3-US1-R
bench/2026-09-26b/D3-US1-H
bench/2026-09-26b/D3-US1-D
bench/2026-09-26b/D3-US1-IL
bench/2026-09-26b/D3-US1-SN
bench/2026-09-26b/D3-US2-L
bench/2026-09-26b/D3-US2-S0
bench/2026-09-26b/D3-US2
bench/2026-09-26b/D3-US2-S1
bench/2026-09-26b/D3-US2-P
bench/2026-09-26b/D3-US2-R
bench/2026-09-26b/D3-US2-H
bench/2026-09-26b/D3-US2-D
bench/2026-09-26b/D3-US2-IL
bench/2026-09-26b/D3-US2-SN
bench/2026-09-26b/D3-US3-L
bench/2026-09-26b/D3-US3-S0
bench/2026-09-26b/D3-US3
bench/2026-09-26b/D3-US3-S1
bench/2026-09-26b/D3-US3-P
bench/2026-09-26b/D3-US3-R
bench/2026-09-26b/D3-US3-H
bench/2026-09-26b/D3-US3-D
bench/2026-09-26b/D3-US3-IL
bench/2026-09-26b/D3-US3-SN
bench/2026-09-26b/D3-X-SW
bench/2026-09-26b/D3-X-LS
bench/2026-09-26b/D3-X-L
bench/2026-09-26b/D3-X-00-P
bench/2026-09-26b/D3-X-00-R
bench/2026-09-26b/D3-X-00-H
bench/2026-09-26b/D3-LUR1-L
bench/2026-09-26b/D3-LUR1-S0
bench/2026-09-26b/D3-LUR1
bench/2026-09-26b/D3-LUR1-S1
bench/2026-09-26b/D3-LUR1-P
bench/2026-09-26b/D3-LUR1-R
bench/2026-09-26b/D3-LUR1-H
bench/2026-09-26b/D3-LUR1-D
bench/2026-09-26b/D3-LUR1-IL
bench/2026-09-26b/D3-LUR1-SN
bench/2026-09-26b/D3-LUS1-L
bench/2026-09-26b/D3-LUS1-S0
bench/2026-09-26b/D3-LUS1
bench/2026-09-26b/D3-LUS1-S1
bench/2026-09-26b/D3-LUS1-P
bench/2026-09-26b/D3-LUS1-R
bench/2026-09-26b/D3-LUS1-H
bench/2026-09-26b/D3-LUS1-D
bench/2026-09-26b/D3-LUS1-IL
bench/2026-09-26b/D3-LUS1-SN
bench/2026-09-26b/D3-SUM
bench/2026-09-26b/R1-M1
bench/2026-09-26b/R1-MB1
bench/2026-09-26b/R1-NW1
bench/2026-09-26b/Z-DW
bench/2026-09-26b/Z-DWALL
bench/2026-09-26b/R1Q-ab2
bench/2026-09-26b/R1Q-2a
bench/2026-09-26b/R1Q-boot
```

```cardnum
cells-fence	580	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^bench/2026-09-26b/
declared-date	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md [*][*]declared date 2026-09-26[*][*]
presses-caught	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/R1-CATCH -{2}esc 180 -{2}esc-period
cap-cells	202	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out
host-cells	375	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST&? bench/2026-09-26b/
send-over-127	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*AUTOBURN
no-esc-after	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP .*-{2}esc-after
no-watchdog-cell	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*(watchdog|rtl819x-wdt)
no-mark-gate	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=RLXFW-
no-txstall-cell	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*txstall
no-readback-cell	0	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST \S+ :: RBC 
board-brackets	86	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/\S+-R[0-9]? -{2}send 'sleep\ 2\ ;\ cat\ /proc/rtl819x\-nic\ /proc/net/snmp\ /proc/net/arp\ /proc/rtl865x/asicCounter\ /proc/rtl819x\-nic' -{2}until 'rx_ph4\ \[0\-9A\-F\]\{8\}\(\?:\\r\\n\)\+\#\ \|Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds 15$
host-pre-reads	86	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/\S+-P[0-9]? :: HP$
loader-gates	200	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
sweeps-full	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/\S+-S -{2}send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' 
sweeps-sub-wire	4	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/W-1[a-d]-S -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep [0-9]+ [0-9]+ 60 wire > 
sweeps-one-wire	11	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/W-2-[0-9]{4}-S -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep ([0-9]+) \2 60 wire > 
sweeps-lbp	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/LB-P-[0-9]{4} -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep ([0-9]+) \2 60 > 
sweeps-wire-all	16	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*echo sweep [0-9 ]+ wire 
swclear-sends	4	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send '[^']*echo swclear > 
switch-cells-e	3	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/E-[FL][12]-SW -{2}send 'ifconfig rlx0 down ; echo txlen (vendor|rlxfw) > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up'
switch-cells-s	22	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/S[FL]-[0-9]{4}-SW -{2}send 'ifconfig rlx0 down ; echo txlen (vendor|rlxfw) > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up'
switch-s-vendor	11	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/SF-[0-9]{4}-SW -{2}send 'ifconfig rlx0 down ; echo txlen vendor > 
switch-s-rlxfw	11	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/SL-[0-9]{4}-SW -{2}send 'ifconfig rlx0 down ; echo txlen rlxfw > 
isz-cells	3	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/E-[FL][12]-E2 :: ISZ 10[.]1[.]1[.]3$
pg-cells	22	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/S[FL]-[0-9]{4}-PG :: PG [0-9]+$
path-gates	25	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\^path p3 rx d .*:(E-[FL][12]|S[FL]-[0-9]{4})-D$
isz-macro-b45	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
isz-macro-here	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
pg-macro	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^`PG <s>` = `ping -I enxfc19286184c9 -c 20 -s <s> -i 0[.]05 -W 1 -q 10[.]1[.]1[.]3`
pg-sizes	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^E2 ping_s 18 19 20 21 221 234 235 1469 1470 1471 1472$
tde-macro	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^`TDE <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap2/<f> ether src 02:52:4c:58:46:57`
tds-macro	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^`TDS <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap2/<f> 'ether src 02:52:4c:58:46:57 and [(]ether proto 0x88b5 or [(]ether proto 0x8100 and ether\[16:2\] = 0x88b5[)][)]'`
tcpdump-cells	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST& bench/2026-09-26b/W-TCP[ES] :: TD[ES] W[ES][.]pcap$
tcpdump-stops	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/W-TCP[ES]X :: HN ; sudo -n pkill -INT -x tcpdump && sleep 1 ; HN$
order-cells	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/W-[ES]ORD :: PWO 
order-logs-e	100	count /home/key/fwre-work/rebuild/s112/r6b3/card2/order-lists.txt ^PWE 
order-logs-s	36	count /home/key/fwre-work/rebuild/s112/r6b3/card2/order-lists.txt ^PWS 
liveness-cells	42	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/\S+-L[0-9]? :: FL 10[.]1[.]1[.]3 ; PL ; DW 
follower-gates	43	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\^follower 1\$:
port3-gates	28	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\^Port3 Force Mode disable
psrp3-gates	28	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\^r PSRP3 
switch-first	28	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status'
map-until-prompt	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/R1-M[01] .* -{2}until 'map_lines \[0-9\][+]\\r\\n# '
nw-cells	2	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^CAP -{2}out bench/2026-09-26b/R1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}seconds 15$
iperf-macro	1	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^`IPERF` = `timeout 70 qemu-mips-static /home/key/fwre-work/iperf3-port/iperf3`
iperf-trials	14	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^HOST bench/2026-09-26b/D3-L?(TR|TS|UR|US)[0-9] :: IPERF -c 10[.]1[.]1[.]3 -p 5201 -t 30 -i [15] -f m
iperf-shapes-b42	12	count bench/2026-09-23/PREDICTIONS-B44-block42.md ^HOST bench/2026-09-23/P1-(TR|TS|UR|US)[123] :: IPERF -c 10[.]1[.]1[.]3 -p 5201 -t 30 -i [15] -f m
iperf-servers	14	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send 'iperf3 -s -1 -f k -{2}logfile /tmp/[a-z]+[0-9][.]log > /dev/null 2>&1 & sleep 2 ; ps ; cat /proc/net/snmp /proc/stat' -{2}idle 4 -{2}seconds 30$
iperf-stops	14	count bench/2026-09-26b/PREDICTIONS-B50-block48.md -{2}send 'cat /proc/net/snmp /proc/stat ; busybox killall iperf3 ; sleep 1 ; cat /tmp/[a-z]+[0-9][.]log' -{2}idle 3 -{2}seconds 40$
iperf-ps-gates	14	count bench/2026-09-26b/PREDICTIONS-B50-block48.md ^gate:grep=\^\ \*\[0\-9\]\+\ \+\\S\+\ \+\\S\+\ \+\\S\+\ \+iperf3\ \-s\ \-1\ \-f\ k\ -{2}logfile /tmp/
iperf-host-bin	3144db60bd3895f582f84e61da306f96f6e668f07cf9a84fef0ebc6b971a97e8	sha256 /home/key/fwre-work/iperf3-port/iperf3
iperf-in-image	1	count /home/key/fwre-work/rebuild/_irfs-p2/rlxfw-initramfs.spec ^file /bin/iperf3 
image-irfs-source	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^initramfs_source\t/home/key/fwre-work/rebuild/_irfs-p2/rlxfw-initramfs[.]spec$
killall-applet	1	count config/image-commands.tsv ^applet\tkillall$
d3-fix-controls	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^D3 control 2 LUR1 LUS1$
d3-fix-twelve	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^D3 fix 12 TR1 TR2 TR3 TS1 TS2 TS3 UR1 UR2 UR3 US1 US2 US3$
udp-rcvbuf-twice	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/udp.c ^\t\t/[*] Note that an ENOMEM error is charged twice [*]/$
udp-indatagrams-at-recvmsg	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/net/ipv4/udp.c ^\t\t\t\tUDP_MIB_INDATAGRAMS, is_udplite[)];$
sha-pcapwin-py	6871c76753f28fac9cdbf7227dfc8fa015d9238ba908c3a70c5aeeda98408095	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py
sha-brdelta-py	030144a35c0bf3251640fc290ac4635e1c00ba84feb07ae9f19b87e34a2b3984	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py
sha-dmesgwin-py	2376af10942ce3aee4faf605246990c0544619c71092fc9f4812057893c9bbf1	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py
sha-swcheck-py	e36bd29e4714408ac50d2fe7dd90dde71cb88be5c6007ec22277a0ef0082c890	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/swcheck.py
sha-arith49-py	7f7dad0b02e5616943f536e6cdc31c42692a8b1f5de67d2ce0422e7b2728bafe	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/arith49.py
sha-arith50-py	2331a6ecc56a6c54c26e00840ff9e373684433c326c7d01b7a9d386d39dce2e5	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.py
sha-verbcheck50-py	d8dadf513c2a979431bd8b38183e2117e5afcc5d0ae449aa7818cc030d372698	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/verbcheck50.py
sha-fixtures-MANIFEST-sha256	4069cd42f6f8334ed6e1bd5ae8fe44c87333d2a092da27b88f77c9c54f277b90	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/fixtures/MANIFEST.sha256
selftest-pcapwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-pcapwin.out ^pcapwin\ self\-test:\ 29\ of\ 29\ passed$
selftest-brdelta	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-brdelta.out ^brdelta\ self\-test:\ 40\ of\ 40\ passed$
selftest-swcheck	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-swcheck.out ^swcheck\ self\-test:\ 12\ of\ 12\ passed$
selftest-dmesgwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-dmesgwin.out ^dmesgwin\ self\-test:\ 9\ of\ 9\ passed$
selftest-verbcheck50	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-verbcheck50.out ^verbcheck\ self\-test:\ 10\ of\ 10\ passed$
verbcheck-pass	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/verbcheck50.out ^verbcheck verdict PASS$
pcapwin-echo-first	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py out[(]"echo_first %d seq %d b10 %s"
b47-el1-61-k13	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/first47.out ^echo_first 2 seq 1 b10 13$
b47-el1-61-seq1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/first47.out ^echo_seq 2 1$
b44-trial-70	1	count /home/key/fwre-work/rebuild/s110/run-I3.log END P1-UR1 rc=124 70[.]0 s
b44-trial-done	1	count /home/key/fwre-work/rebuild/s110/run-I4.log END P1-EU1 rc=0 30[.]2 s
pcapwin-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin.py ^VERSION = "1[.]3"$
brdelta-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta.py ^VERSION = "1[.]2"$
pcapwin-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/pcapwin-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
dmesgwin-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin.py ^VERSION = "1[.]2"$
dmesgwin-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/dmesgwin-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
sha-iperflog	12ab35696c31e3949b4398f02104b7e8dbc5f029338b0e4035110be5ca1be19b	sha256 tools/iperflog.py
selftest-iperflog	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-iperflog.out ^RESULT: 31/31$
b47-el1-cpu	1	count bench/2026-09-26/E-L1-D.log ^cpu crc d 789 jab d 581 frag d 3 drop d 41 dropev d 32 b64 d 24 b65 d 54 b128 d 0 b256 d 81 b512 d 3 b1024 d 43$
b47-el1-host	1	count bench/2026-09-26/E-L1-D.log ^host rx d 168 tx d 1335 inechoreps d 145 outechos d 1327$
b47-prior-window	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^prior47 window E-L1-H0 -> E-L1-H1 records 232 400 frames 168$
b47-prior-census	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^census replies-untagged 145 tagged 19 arp 4 other 0$
b47-prior-tci	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^tagged tci 06E7 count 19 orig 281$
b47-prior-hprev277	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^hprev L 277 block 268 tci-bytes 272 273 payload 230 231 fill E6 E7 vid 1767$
b47-prior-no-256k	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^frames of 256k-4 bytes [(]k 1[.][.]5[)] in the window 0$
b47-prior-62-5	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 62 seq 5 k 2 next absent$
b47-prior-62-7	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 62 seq 7 k 3 next absent$
b47-prior-62-62	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 62 seq 62 k 4 next absent$
b47-prior-62-116	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 62 seq 116 k 4 next absent$
b47-prior-62-132	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 62 seq 132 k 2 next absent$
b47-prior-63-16	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 63 seq 16 k 4 next absent$
b47-prior-63-141	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 63 seq 141 k 3 next absent$
b47-prior-63-143	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 63 seq 143 k 5 next absent$
b47-prior-63-157	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^case L 63 seq 157 k 1 next absent$
b47-prior-cases	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^cases 9 next-absent 9 next-answered 0$
b47-prior-control	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.out ^control L 60 [(]clean[)]: 20 answered, 19 followed by their next, every k 1[.][.]5 reply's next answered [(]6 of 6[)] [(]ok[)]$
b47-prior-tool	b21a97d9ff7c420609d2ec5a839cd171d960b0da6fe569e555748e736f9124d5	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/prior47.py
brdelta-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/brdelta-mutate.out ^mutations: [0-9]+ planted, 0 not as expected$
pcapwin-order-b47	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/order-b47.out ^order-b47: ([0-9]+) of \1 as expected$
fixtures-header	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/fixtures/rtl819x-nic-tx.h
repo-header-is-fixtures	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h
fixtures-nic15check	13198b2c9009b5175026f8bf9fa1d4988d8e5cb466d8e45a63bd9035f5788286	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/fixtures/nic15check.py
repo-nic15check-is-fixtures	13198b2c9009b5175026f8bf9fa1d4988d8e5cb466d8e45a63bd9035f5788286	sha256 tools/nic15check.py
driver-version-1.5	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]5"$
driver-sweep-is-loop-unless-wire	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h else if [(]!strcmp[(]e, " wire"[)][)]$
driver-wire-bound	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h if [(]wire && from != to && txlen != NIC15_LEN_VENDOR[)]$
driver-keycheck-eexist	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h ^\t\treturn -EEXIST;$
driver-tx15-format	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h "tx15 txlen %s txoff %d txrb %d dirty %d p15 %d[\\]n",
driver-sw-format	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h "sw %s mode %s from %u to %u probe %u rc %d bufs %08X[\\]n",
driver-count-return	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h ^\treturn nic15_ret[(]v, rc [?] rc : [(]int[)]count[)];$
image-switch-psrp3-row	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t[{] "PSRP3",\t0x4134, 0, 0 [}],$
image-switch-linkup-bit	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_PSRP_LINKUP\t[(]1u << 4[)]$
errno-eperm	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEPERM\t\t 1\t
errno-eexist	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEEXIST\t\t17\t
errno-eproto	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tEPROTO\t\t71\t
errno-etimedout	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tETIMEDOUT\t145\t
errno-enodata	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tENODATA\t\t61\t
errno-eintr	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEINTR\t\t 4\t
img-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^verdict\tgreen$
img-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^vmlinux_sha256\t900faed7c8bfdf2e984b7abee0bb03cfb6929fc5fe33fa5e6ce696c639037337$
img-manifest-variant	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^variant\tquiet$
img-record-nfjrom	1	count /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9$
img-record-clean	1	count /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
img-nfjrom-sha256	7d7dd4b03a1fdaaf	sha256-16 /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom
img-cell-header	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x-nic-tx.h
img-sysmap-frame	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] nic15_frame$
img-sysmap-page	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] nic15_pf$
img-recipe	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^recipe_id\t06c39ca3$
img-card1-same	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^`QIMG` = `--image /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9`$
b47-mb1-digest	1	count bench/2026-09-26/R1-MB1.log ^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46\s+-$
b47-ef1-220	11	count bench/2026-09-26/E-F1-E2.log ^20 packets transmitted, 20 received,
b47-ef2-220	11	count bench/2026-09-26/E-F2-E2.log ^20 packets transmitted, 20 received,
b47-el1-short	4	count bench/2026-09-26/E-L1-E2.log ^[0-9]+ packets transmitted, (?:[0-9]|1[0-9]) received,
b47-el1-61	1	count bench/2026-09-26/E-L1-E2.log ^179 packets transmitted, 1 received,
b47-el1-1512	1	count bench/2026-09-26/E-L1-E2.log ^179 packets transmitted, 0 received,
b47-w2ep	1	count bench/2026-09-26/W-2-EP.log ^v15 last sweep -1 
b47-w1a-jfd0	1	count bench/2026-09-26/W-1a-D.log ^fault jfd 0$
b47-w1d-jfd0	1	count bench/2026-09-26/W-1d-D.log ^fault jfd 0$
b47-lb1-class5	1	count bench/2026-09-26/LB-1-0061.log ^sw last 61 a 65 1 b 9831 5 
b47-lbv-clean	1	count bench/2026-09-26/LB-V-C.log ^rule M1-cover8 +predicted +0 measured +0 agree 1455 of 1455 
b47-lb2-cover8	1	count bench/2026-09-26/LB-2-C.log ^rule M1-cover8 +predicted +728 measured +728 agree 1455 of 1455 
b47-pcapwin-defect	1	count bench/2026-09-26/E-L1-H1.log ^prev_beyond_file 
b47-tcpdump-626	1	count bench/2026-09-26/W-TCPE.log ^626 packets captured$
b47-bug-282	1	count bench/2026-09-26/Z-DWALL.log ^bug_preempt 282$
b47-dw0-clean	1	count bench/2026-09-26/R0-DW0.log ^bug_preempt 0$
b47-recov-after-page	1	count bench/2026-09-26/CORRECTIONS-block47.md the recovery's four marks
b47-ident-k4	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-brdelta.out ^ +ok +D1 +E-L1-R0 -> E-L1-R1: block 47's o-identity miss, o 168 against c 789 - j 581 - f 3 - d 41 = 164; 
b47-gap-race	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/selftest-brdelta.out ^ +ok +D3 +E-F1-R1 -> E-L1-R0 with the host: host rx 6 against p3 out 5 
b47-rx-f1h0	1	count bench/2026-09-26/E-F1-H0.log /statistics/rx_packets:2291$
b47-rx-f2h1	1	count bench/2026-09-26/E-F2-H1.log /statistics/rx_packets:2912$
b47-payload-fill	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/payload47.out ^payload bytes 16[.][.]21 [(]fill[)], by count: [{]'101112131415': 364[}]$
b47-payload-usec	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/payload47.out ^payload byte 10, byte 11, usec<1e6 -> count: \[[(][(]0, 0, True[)], 23[)], 
b47-payload-tool	e342eb7a33a966f3ba386ddef50758c26137edee9a1aab5b3e091ebcf361e5e5	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card2/payload47.py
b44-ps-row	1	count bench/2026-09-25/P1-TR1-S0.log ^ +[0-9]+ 0 +[0-9]+ S +iperf3 -s -1 -f k -{2}logfile /tmp/TR1[.]log
b44-ur1-lost	2	count bench/2026-09-25/P1-UR1-S1.log 46157/52587 [(]88%[)]
b46-psrp3-fmt	1	count bench/2026-09-22b/A6-SW.log ^r PSRP3 +4134 000000F9 
b46-port-status-fmt	1	count bench/2026-09-17/C2-PORT.log ^LinkUp [|] NWay Mode Enabled
b46-wdt-armed	1	count bench/2026-09-25c/R1Q-boot.log ^RLXFW-W4=00240000
spec-net131-residual	1	count SPEC.md ^[|] `NET-131` 殘留 🆕 [|]
spec-fw145	1	count SPEC.md ^[|] `FW-145` 🆕 [|]
spec-net128	1	count SPEC.md ^[|] `NET-128` 🆕 [|]
notes-25-4	1	count notes/nic-driver.md ^### 25[.]4 P0 refuted in 3 of 66 brackets$
b45-276	1	count bench/2026-09-25b/D1-ISZ.log ^25 packets transmitted, 20 received,
b45-1513	1	count bench/2026-09-25b/D1-ISZ.log ^22 packets transmitted, 20 received,
b47-276	1	count bench/2026-09-26/E-L1-E2.log ^49 packets transmitted, 20 received,
b47-1513	1	count bench/2026-09-26/E-L1-E2.log ^82 packets transmitted, 20 received,
b46-p0-76	1	count notes/nic-driver.md P0's identities hold at 76 of 76 brackets
adj-el1-own	1	count /home/key/fwre-work/rebuild/s112/r6b3/read/ADJ-b47.md OWN bracket [(]o exceeds c.{1,3}j.{1,3}f.{1,3}d by 4
spec-117-loss	1	count SPEC.md 87[.]8／86[.]6 %
spec-117-softirq	1	count SPEC.md 30 s 的 76 %
b47-urb-302	1	count bench/2026-09-26/R0-DW0.log ^urb_104 302$
order-b47-5	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/order-b47.out ^at E-F1-H0[.]log rx 2291 idx 5 
order-b47-626	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/order-b47.out ^at E-F2-H1[.]log rx 2912 idx 626 
arith-controls	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^arith50 controls: 7 of 7 hold 
arith-e2	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^E2 rlxfw +60c 61F 62F 63F 263F 276c 277F 1511F 1512F 1513c 1514c$
arith-e2-fix	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^E2 faulty at 1[.]4 7 clean 4; faulty at the fix 0$
arith-ef	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^EF replies 220 requests 220 buckets 64:20 65-127:60 128-255:0 256-511:60 512-1023:0 1024-1518:80 
arith-sf-60	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SF L 60 ping_s 18 replies 20 jfd 0 bucket 64 d 20$
arith-sf-277	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SF L 277 ping_s 235 replies 20 jfd 0 bucket 256-511 d 20$
arith-sf-1514	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SF L 1514 ping_s 1472 replies 20 jfd 0 bucket 1024-1518 d 20$
arith-sl-61	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SL L 61 mod8 5 faulty seq1 right replies_max 19$
arith-slk-61-1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLK L 61 k 1 ph 256 legal decision-rule if-a wire 252 excess 191$
arith-slk-61-7	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLK L 61 k 7 ph 1792 jabber$
arith-slk-63-6	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLK L 63 k 6 ph 1536 at-acptmaxlen not-predicted$
arith-slk-62-0	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLK L 62 k 0 ph 0 runt not-predicted$
arith-slb-61	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 61 offset 52 payload 10 timestamp usec byte 2: ph 256[*]k k 0[.][.]15, range 0-3840, jabber only above 1536$
arith-slb-63	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 63 offset 52 payload 10 timestamp usec byte 2: 
arith-slb-263	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 263 offset 252 payload 210 fill D2 D3 ph 4819 jabber yes$
arith-slb-277	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 277 offset 268 payload 226 fill E2 E3 ph 8931 jabber yes$
arith-slb-1511	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 1511 offset 1500 payload 1458 fill B2 B3 ph 12979 jabber yes$
arith-slb-1512	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SLB L 1512 offset 1500 payload 1458 fill B2 B3 ph 12979 jabber yes$
arith-sl-276	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SL L 276 mod8 4 clean replies 20 jfd 0 bucket 256-511 d 20$
arith-sl-1513	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SL L 1513 mod8 1 clean replies 20 jfd 0 bucket 1024-1518 d 20$
arith-sl-count	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^SL faulty 7 clean 4$
arith-lbp-61	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^LBP L 61 faulty yes H-prev 9831 H-own 9831 H-slot 9831 
arith-lbp-1511	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^LBP L 1511 faulty yes H-prev 3663 H-own 9831 H-slot 8224 
arith-lbp-mt	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^LBP mt none 1453 clean 0 bad_b 2 bad_a 0 void 0 skew 0$
arith-lbp-hb	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^LBP H-prev hb 9831:1:61-61 3663:1:1511-1511$
arith-lbv	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^LBV swsum 05AF0000 swend 00000000 
arith-w1-total	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^W1 total units 1455 frames 2910 jfd 0$
arith-w1a	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^W1 60-423 units 364 frames 728 jfd 0 cpu_crc 728 host_rx 728 lenby 1:61-423 lenby 365:60$
arith-w1d	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^W1 1152-1514 units 363 frames 726 jfd 0 cpu_crc 726 host_rx 726 lenby 1:1152-1514 lenby 363:60$
arith-w2-total	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^W2 total lengths 11 bad 7 clean 4 jfd 7 cpu_crc 22 host_rx 15$
arith-w2-min	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^W2 smallest predicted wrong ph_b over the bad lengths and the three sources 3663 [(]> AcptMaxLen 1536[)]$
arith-bytes-vendor	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^BYTES 'txlen vendor' 13$
arith-bytes-rlxfw	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^BYTES 'txlen rlxfw' 12$
arith-bytes-lbp	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^BYTES 'sweep 1511 1511 60' 19$
arith-errno-eperm	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^ERRNO EPERM 1 hex FFFFFFFF$
arith-d3-udp	1	count /home/key/fwre-work/rebuild/s112/r6b3/card2/arith50.out ^D3 udp datagrams a 30 s trial at -b 20M -l 1400 is paced to: 53571 
```
