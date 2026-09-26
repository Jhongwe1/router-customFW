# PREDICTIONS — block 47, seating 42 (`R6b-3`, first card: the fix A/B on one boot — the descriptor read back first, then E2 at block 45's spacing under the fix and under 1.4, then sweeps over every length)

**declared date 2026-09-26** — **one power press**; its catch window opens no later than
23:00 that day, or the card is re-dated before power (§ 6).
Block 46 (`bench/2026-09-25c/PREDICTIONS-B48-block46.md`, `R6b-1`) is the last press before
this one. It was a failed reproduction (`NET-123`), so `D1` is recorded undetermined and the
gate moved to `R6b-2`'s image A/B; this card is that A/B's first seating. It is written against
driver 1.5 as `R6b-2` committed it (`rtl819x-nic-tx.h` sha256 `82b1c1c2…`, `NET-1AA`,
`notes/nic-driver.md` § 23), never the proposal.

Marks: **量** measured on the device · **讀** read out of code or a dump ·
**推** inferred, pending a measurement.

---

## § 0 Honesty notes, written rather than left to be found

**① What this block is, and which conjuncts of the gate it carries.** `R6b-3`'s row is
larger than one press (§ 7 and `NOTES-later-cards.txt` in the card's working directory,
the split decided at the desk): this card is its first seating, built so that `D2`'s first
boot happens in it. It boots driver 1.5 (`R6b-2`, the quiet image `r6b2q`) and carries:

| conjunct | carried here | left to a later card |
|---|---|---|
| `R6b-2`'s DoD, *at the default settings the descriptor reads back as 1.4 wrote it* | the first cells (`I-RB`), by the owner's ruling of 2026-09-26: a DIFFER ends the A/B; a VOID is decided in § 6, where `I-RQ` then reads Q at `txrb 1` (P1b), a queue-time reading that does not stand in for it | — |
| `D2`, E2's eleven at block 45's spacing, 220 of 220 on the fix, 1.4 reproducing the loss on the same boot | boot 1 of 2 (`I-E`: fix, 1.4, fix) | boot 2 (card 2, a second block of this seating, drafted and frozen after this card's readings) |
| `D2`, a `tx` sweep over every length 60–1,514 with `JabberErr` Δ 0 | the fix on the wire, 1,455 lengths in four brackets (`W-1a`…`W-1d`), behind a containment gate on the fix's own loopback map | — |
| the owner's bounded 1.4 wire sweep | 35 single-length wire sweeps after the fix's wire sweep (`W-2`); the driver refuses anything wider (`W-2-EP`) | — |
| the mechanism (`R6b-2`'s most-likely-wrong: a fix without its mechanism) | loopback maps under every `txlen`, `txoff 0` and `txrb` value, and the history cells | — |
| `NET-61` 殘留's burst half and `NET-103` 殘留 ④ (re-owned here by `R6b-5`) | block 46 arm C's protocol at E2's eleven, under 1.4 and under the fix (`DS-r`, `DS-v`) | the other 1,444 lengths |
| `NET-54` 殘留 ② and `NET-124` 殘留 | the liveness, port-3 and path gates before and inside every host arm, and § 6's ordered read set on a failure | — |
| `D3` (`NET-111`'s twelve `rlx0` trials, on two boots), `NET-117` 殘留's `Udp:` lines, `D3-MISS` ② and ①, `P2`'s quiet-image cold boot, `D2`'s second boot | — | cards 2 and 3 |

**② Block 46's lessons, each applied here** (`notes/nic-driver.md` § 22, `NET-123`,
`NET-124`, `CLK-38`).
* *A bad frame poisons the run after it* (§ 22.5, 推 from 量). Every sweep unit starts with
  its own re-arm (driver 1.5's sweep: engine off, `arm`, engine on, per length), every policy
  switch passes through `arm`, and every hand-typed frame sequence below starts on a re-armed
  ring. E2 is the exception by definition: it is block 45's regression, eleven lengths back to
  back in one bracket, and the card reads it as a total only (§ 3.3); in the 1.4 arm no
  per-length figure is drawn from it.
* *The host stopped reaching the board mid-block, and nobody knew until the brackets were
  read* (`NET-124`). Before every arm that needs the host, two gates: port 3 reads `LinkUp`
  twice — first through rlxfw's switch driver, whose `PSRP3` line also carries bit 8
  (`LinkDownEventFlag`), which `/proc/rtl865x/port_status` clears without printing, so the
  switch driver is always read first — and the host's `ping` of 60-B frames reads 4 of 4 after
  its neighbour entry is flushed, so an ARP is answered first. Inside every stack arm a third:
  every echo request the host's ICMP layer sent is a frame port 3 received (`BD`'s `path`
  line). A failure is a decided branch (§ 6), never a reading found later. The host's kernel log
  is followed from before the press (`dmesg -w` into `$FWRE_WORK`), so an onset cannot roll out
  of the ring buffer as block 46's did; every window counts its signatures and says whether the
  follower still runs (`follower 1`, gated before every arm).
* *WSL's realtime clock steps against the runner's RAW clock* (`CLK-38`: +0.6–1.1 s every ~33
  s). No verdict on this card rests on a host timestamp, and no capture is mapped onto RAW with
  one offset: every verdict is a counter difference or a count, and every capture is windowed by
  record order.
* *Marks interleave with ash's echo* (`FW-47`; 量 again in block 46's `C-02-X`, where
  `N-ENGOFF` is broken by the echo of the same line). No gate on this card reads a console mark
  (a `cardnum` row counts zero): a sweep is bound to its cell by the page it prints, `v15 last`,
  `sw` and `sw key`. The marks `RLXFW-N-SWEEP=`, `-SWSUM=` and `-SWEND=` are readings.

**③ What reads silicon for the first time tonight.** Driver 1.5, all of it: the `tx15`
line, `/proc/rtl819x-nic-tx`, the behaviour verbs and their refusals, the record key and
`swclear`, the owner's wire bound, and the sweep. Also, on this die: `ifconfig rlx0 down`
followed by `arm` and then `ifconfig rlx0 … up` — `NET-58` measured that a down and up with no
`arm` between them walks the engine off the ring (`X16`), so every `up` on this card finds the
ring freshly armed with the engine off — its last engine act an `arm` or a sweep's end, with no
`engine on`, `tx` or `txstall` since — which the generator refuses to break (the exceptions, by
name, are the guards' own refusals, `VC-02`, `VC-03`, `VC-06`, `VC-EE` and `W-2-EP`, each gated
on its refusal); `irqon` with `rlx0` down; `txstall on` holding filled descriptors for a read,
where `R6-4a` used it to force the stop path; the looped frames of 1,455 units per map; and
captures filtered to the board's source address and cut at 64 bytes. None of the sweep's
predictions has been tested on silicon: they were fitted after blocks 45 and 46
(`PROPOSAL-R6b-2.md` § 2, 推).

**④ The host is restarted before the seating (an engineering decision, written here).**
`NET-124`'s leading candidate is the host side: under `usbip`, the host adapter's transmit
path ran through a kernel `BUG` trace on every frame of the silence, and the onset had
rolled out of the log. A fresh WSL, a fresh attach of both USB devices and a kernel-log
follower started before the attach give this seating a host with no history and a log that
begins at the kernel's boot; `R0-DW0` refuses power unless that log reads `bug_preempt 0`,
`usbnet_xmit 0` and `call_trace 0` (the coordinator's precondition). The price is a few minutes
and every WSL process: the restart waits until no other WSL job is running (§ 6). What the
restart cannot do: tell whether block 46's silence was host history, the board, or the frames.
The liveness, port-3 and path gates and the log decide that if it recurs.

**⑤ Containment, which does not depend on any outcome.**
* **Frames at 1.4's settings on the wire are bounded by construction.** The read-back fills
  three descriptors by the `tx` verb (60, 61 and 1,514 B) and the board's replies to two 61-B
  echo requests, holds them with `TXCMD` clear and discards them by a re-arm; if `TXCMD` clear
  does not hold fetch, those frames are what reaches the wire, no more. `I-RQ`, which runs only
  after a VOID, repeats exactly those held fills at `txrb 1`; what it sends unheld is its
  liveness probes' 60-B replies (and any ARP of the board's) at `txrb 1` — the only frames on
  the wire at a `txrb` other than 0 on this card; `PL`'s frames are clean at every setting, and
  `txrb` changes no length field. `E-L1` is
  block 45's E2 at 1.4, the regression itself; `W-2` is 35 single-length wire sweeps, at
  most one mis-sent frame each (19 predicted, `arith49.out`), and the driver refuses a wire
  sweep over more than one length at any `txlen` but `vendor` (`nic15_sweep_gate`, -EPERM),
  shown refusing at `W-2-EP` before the first of them. Every map at 1.4's settings runs in
  loopback, and only after `LB-1-G` has shown that the positive control's 22 looped frames
  reached neither the CPU port's counters, nor port 3's output, nor the host adapter — a window
  opened after `ifconfig rlx0 down`, so no stack frame can fall inside it: a gate, because
  whether `LBMODE` isolates the CPU port is open (`PROPOSAL-R6b-2.md` § 14). If it fails, no
  map at 1.4's settings runs, and neither do `NET-61`'s runs (§ 6).
* **The fix's full wire sweep is bounded whatever the maps read.** `W-00` reads the fix's own
  loopback map before any multi-length wire sweep: `rc 0`, 1,455 scored, 0 bad a, 0 bad b, 0
  VOID, 0 SKEW, `delta0 0`, the key `txlen vendor … mode loop probe 60`, 1,455 records. If it
  does not read so, no multi-length wire sweep runs. After that, each quarter runs only if the
  quarter before it read `fault jfd 0`: at most one quarter's frames (364 units) can be
  mis-sent before the sweep stops.
* **What the host keeps of a frame.** Two captures, each `tcpdump -Q in -s 64` into
  `$FWRE_WORK/rebuild/s112/r6b3/pcap/`, never the repository: during the stack arms every
  frame from the board's address (`ether src 02:52:4c:58:46:57`, block 46's filter); during
  the sweeps only the board's frames whose EtherType is `0x88B5`, untagged or behind one
  `0x8100` tag with the inner type `0x88B5` at bytes 16–17 — `M4`'s tag at 277 would otherwise
  hide a tagged frame and void that bracket's `w = h` (both filters the owner's, confirmed at
  the freeze on 2026-09-26, FREEZE-READY question 3). 64 bytes hold
  every header this card counts and at most the first bytes of a frame's payload; a mis-sent
  frame's bytes past its buffer never reach the file. The files are read only by `pcapwin.py`
  1.2, which prints counts, lengths and sequence numbers, never an address (self-test 19 of 19;
  16 planted defects each turned it red).
* **Verdicts come from counters**: the CPU port's `CRCAlignErr`, `JabberErr`, `FragErr`,
  `Drop`, port 3's output and input, and the host adapter's counters, read in brackets around
  each experiment. The captures are a reading beside them.

**⑥ Resets.** No cell carries `--esc-after`: it would stream escapes into `ash` for the whole
window of a cell that is not designed to reset (block 46 § 0 ⑤). Instead every `--until` on
the card also ends on the loader's banner (`Booting...`, `---RealTek`), so a reset ends the
capture it happens in at once, and every board cell after the round carries the gate
`\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version))` (292 gates), which then fails: § 6 has the owner power off on the failed
capture's own text, before any other cell. 量 block 46's boot printed `RLXFW-W4=00240000`: the
watchdog is armed by rlxfw's driver at boot and kicked by the kernel; 推 a sweep runs in
process context and yields between units, so the kick continues. No cell touches the
watchdog (a cardnum row counts zero).

**⑦ The clock.** This card claims no duration. A sweep prices itself (`sw` `j0`/`j1`, jiffies
at 100 Hz) and the runner's `END` lines give each cell's length: readings.

**⑧ Runner limits worked around.** The runner's background cells know three programs
(`tcpdump`, `hostprobe run`, `hostclock run`, 讀 `tools/cardrun.py` `background_program`),
so the kernel-log follower is an off-card process started before `I-0` (§ 6), `R0-DMSG`
requires exactly one process named `dmesg` before power, and every kernel-log window prints
how many still run (`follower`). Each capture runs in an invocation of its own (`I-WE0`,
`I-WS0`), because a stop interrupts every background cell of the invocation that stopped. A
cell whose non-zero exit is a reading is declared `NAME?`. Macros take one parameter (讀
`cardrun.expand`), so the checkers' multi-argument calls spell their arguments in the cell.

**⑨ `C-19`** (the console adapter leaving the USB bus) is named, as its row asks: the
kernel-log windows count `USB disconnect`, `cp210x` and `ttyUSB` lines, and the record states
every console drop and every idle longer than a minute with the idle before it.

**⑩ The sweep's records, and what `swclear` is for** (讀 `rtl819x-nic-tx.h`
`nic15_keycheck`, `notes/nic-driver.md` § 23.2). Records accumulate across sweeps under one
key — `txlen`, `txoff`, `txrb`, the mode, the probe and `txrings` — and a sweep under another
key is refused (-EEXIST) while any record exists; `swclear` is the only eraser. So the first
sweep under every new key on this card starts with `swclear` in the same send (18
sends), and sweeps that must accumulate — `LB-1`'s eleven, `W-1`'s four quarters, `W-2`'s
lengths — do not. The mode is the command's, never the register's: `sweep F T P` loops back
(the sweep sets `LBMODE` itself after every `engine on`), and only a trailing ` wire` puts
frames on the wire. `verbcheck49.py` replays the whole card through the committed header's
parser, refusal table, wire bound and key check before power, and refuses any refusal that is
not a gated guard.

---

## § 1 The image

`r6b2q`, driver `rtl819x-nic 1.5`, quiet variant, built twice byte-identical by `R6b-2`
(`r6b2q` = `r6b2q2`). The values below are placeholders until the image the card is frozen
against is chosen (FREEZE-READY.txt's FILL table): recipe `06c39ca3`, `nfjrom`
`/home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom` (`7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9`), vmlinux `900faed7c8bfdf2e984b7abee0bb03cfb6929fc5fe33fa5e6ce696c639037337`. The chain is
checked by this card's own `cardnum` rows once filled: the manifest `verdict green`, `variant
quiet` and that vmlinux; the `rtkimage` record naming that `nfjrom` digest with a CLEAN
tripwire verdict; the `nfjrom` on disk with that digest; the build cell's own
`rtl819x-nic-tx.h` equal to the committed one; the image's `System.map` holding `nic15_frame`,
`nic15_drain`, `nic15_pf` and `rtl819x_sw_read_proc` (the sweep's, the page's and the switch
page's code; the sweep's entry point is static and inlined, 量 `r6b2q`'s map); the
repository's header and `tools/nic15check.py` equal, byte for byte, to the copies the
checkers' fixtures and the verb check were built with. `looprun` pins the `nfjrom` by digest
before the port opens and compares the booted image's `RLXFW-ID0` with the build's.

No cell and no checker names an address from `System.map`: every address the card uses
(`tx_ring`, `tx_ph`, `tx_mb`, `bufs`, `tpdcr0_pos`) is read at run time from the booted
driver's own dump.

---

## § 2 The press, in order

| invocation | what runs | est. min (a guess) |
|---|---|---:|
| `I-0` | before power | 0.2 |
| `I-1` | the catch, the round, the opening map | 4.0 |
| `I-RB` | the read-back | 0.8 |
| `I-RQ` | only after a VOID: Q at `txrb 1` (not in the total) | 0.8 |
| `I-VC` | the guards | 0.6 |
| `I-WE0` | the stack arms' capture starts | 0.0 |
| `I-E` | E2: the fix, 1.4, the fix | 2.5 |
| `I-WE9` | that capture stops | 0.0 |
| `I-WS0` | the sweeps' capture starts | 0.0 |
| `I-LB` | loopback: control, key guard, NET-61, carry-over, the 1.4 and the fix maps | 6.2 |
| `I-W` | the wire: the fix, then 1.4 bounded | 5.7 |
| `I-M` | the mechanism maps, the history cells | 9.5 |
| `I-WS9` | that capture stops | 0.0 |
| `I-Z` | the closing map, `n_writes`, the kernel log | 0.3 |

About 32 minutes from the catch's window to power-off, with 15 s between invocations
(a guess from block 46's transcripts: a bracket 5.2 s, a re-arm 3.2 s, the catch 200.2 s, the
round 21.2 s, a map 13.8 s; a full sweep is guessed at 40 s, of which about 32 s is the four
marks each unit prints at 38,400 baud, 85 B a cycle: `N-ENGOFF` 16 B, `N-ARM` 22, `N-ARMR` 23,
`N-ENGON` 24 with their `RLXFW-` prefix and CRLF). 69 board brackets;
12 full sweeps. `I-0` is before power and not in the figure (its verb check compiles
the header ten times, 5.0 s at this desk). Nor is `I-RQ`: it runs only after a VOID of the
read-back, and adds about 1 min (24 cells, the same guesses).

The order protects `D2`: the read-back first (the owner's ruling) and, only after a VOID, its
fallback `I-RQ`, then the stack A/B, whose
verbs are all 1.4's but the policy switch, then the sweep's first readings in loopback and
`NET-61`'s runs, then the fix on the wire, then 1.4's bounded wire sweep (the owner: *after
the fix arm's full wire sweep*), and last the mechanism maps, which no conjunct of the DoD
needs: if the press runs long, `I-M` is the invocation that is not run (§ 6).

---

## § 3 Predictions, each with what refutes it

### 3.0 What is read, and the names used below

A **bracket** is the board read `<name>-R` (block 46's, unchanged: the driver, the board's
SNMP and ARP, the switch's counters, the driver again) with the host read `<name>-H` after
it; Δ is this bracket minus the previous one. From the board: `n` Δ`n_tx`, the CPU port's
`c` (`CRCAlignErr`), `j`, `f`, `d` (`JabberErr`, `FragErr`, `Drop`), `dropev`
(`etherStatsDropEvents`), its size buckets (a frame of L bytes counts in the bucket of L + 4),
port 3's output `o` and input; from the last intact driver dump `n_recov_fire`, `nd_up`, the
`tx15` line. From the host: `h` Δ`rx_packets`, Δ`tx_packets`, `i` Δ`Icmp.InEchoReps`, Δ
`Icmp.OutEchos`, and the capture's window (`w` frames; echo replies; `vlan8100`; `excess`;
`lenby`). `brdelta.py` prints these for a pair of brackets (self-test 18 of 18, against block
46's own record) and decides three gates: `LB-1-G`'s `leak`, the stack arms' `path` and the
fix's wire quarters' `fault`.

From `/proc/rtl819x-nic-tx` (the layout of the committed `nic15_format`): `w<i>` (what the
last fill of slot i was: F, policy, writer, fill number), `r<i>` (the ring word and the slot's
twelve descriptor words, read uncached at page time), `v15 last <verb> <rc>` (an accepted verb
returns the bytes `echo` wrote, a refusal its errno), `sw <state> mode <loop|wire> from … to …
probe … rc … bufs …`, `sw key …` (the key the records are under), `sw scored … bad_a … bad_b …
void … skew …`, `sw delta0 …`, `sw last …` (the last unit's `ph` and classes, hex), `mt` (the
records counted by code), the map (`m00`…`m11`, one character per pair of lengths: codes 0 no
record, 1 clean, 2 bad b, 3 bad a, 4 VOID, 5 SKEW), `hb n … other … void …` (frame b's looped
`ph_len` over the bad-b lengths) and `ww`. A sweep unit is: re-arm; frame a at L; probe b (at L
when the probe is 0, else at the probe length, after `0x20` is written over the slot's buffer
from the probe's end), sent only when a came back right (on the wire: retired). Every number
predicted below is a line of `arith49.out`, re-derived by the card's `cardnum` rows;
`arith49.py`'s controls reproduce block 46's seven wrong loopback values from the byte law,
refuse the same law with a wrong constant, and reproduce block 46's chain lengths.

### 3.1 The premise, tested in every bracket

* **P0.** At every bracket after the first: `o = c − j − f − d` exactly (block 46: 76 of
  76); `h = o` wherever the host's bracket pairs the board's; `w = h` for the stack arms'
  capture wherever both window ends read `capture_live yes` and `tcpdump_procs 1`, and for
  the sweeps' capture in every bracket while `rlx0` is down (then the board sends nothing
  but the sweep's `0x88B5` frames). In every stack arm (`E-F1`, `E-L1`, `E-F2`), port 3's input
  Δ is at least the host's Δ`Icmp.OutEchos` (every echo request reached port 3; `BD`'s `path
  … covered yes`, a gate). **Refuted by** any bracket where one of these fails by a frame: that
  bracket's stage chain is void, and so is every verdict below that reads it; a stack arm whose
  `path` reads `covered no` is void under `NET-124`, never read as the fix failing (§ 6).

### 3.2 The read-back, first (`I-RB`; `R6b-2`'s DoD by the owner's ruling)

* **P1.** `rbcheck.py` 1.2 (`fill`), whose expected words are driver 1.4's text (讀:
  `nic_xmit`'s and `nic_do_tx`'s seven fill words, alloc's five others) and which agrees with 1.4's own
  statements at `f758d62` executed on the host (`mkfixtures.py`, fixtures pinned), reads:
  `RB-01-C` — on a ring re-armed with `rlx0` down, slots 0, 1, 2 hold the `tx` verb's fills at
  60, 61 and 1,514 B, OWN still set on all three, `tpdcr0_pos` still at `tx_ring`: **`rbcheck
  verdict EQUAL`**; `RB-02-C` — with `rlx0` up the ring has carried the liveness frames, so the
  control is the stall-time capture `RB-02-S` (`txstall on` and both dumps in one send): every
  slot filled since it (fill number above its `txq`) reads OWN, `tpdcr0_pos` and
  `n_recov_fire` read what they read then, at least two of those slots hold `nic_xmit`'s fills
  of the host's 61-B echo replies, and fewer than four were filled: **EQUAL**. A reading beside
  it: the five alloc-only words of every held slot equal alloc's (`docs/nic-vendor-diff.md`
  § 16.4's open question, whether the engine writes into a TX descriptor), and which slots the
  replies took (推 1 and 2; an ARP probe of the board's may take one). **Refuted by** DIFFER at
  either: 1.5 at its defaults does not write what 1.4 writes, every "1.4 arm" below would not
  be 1.4, and the A/B ends (§ 6).
  VOID is not DIFFER: the control failed, and whether 1.5 at its defaults writes 1.4's words is
  **undetermined on this boot** for the path that read VOID -- `R6b-2`'s conjunct is then
  neither met nor refuted. By the owner's answer at the freeze (2026-09-26), after its one
  declared repeat the A/B proceeds: `I-RQ` runs first (P1b), and every 1.4 arm is labelled *1.4
  by `storeseq` (the desk proof, `NET-1AA`); the default-settings read-back VOID on this boot*,
  with `I-RQ`'s verdict beside it (§ 6).
* **P1b, the fallback after a VOID: Q at `txrb 1`** (`I-RQ`, 24 cells, run only when the
  read-back reads VOID, § 6; the owner's answer of 2026-09-26). `I-RB`'s two read-backs again,
  with `txrb 1` set first (`rlx0` down, `echo txrb 1`: `v15 last txrb 7`,
  `tx15 … txrb 1 dirty 1`; the re-arm clears dirty): at `txrb 1` each fill loads the slot's
  twelve descriptor words, uncached, after its last field store and before `OWN` (讀
  `nic15_rb_pre_own`, called by both writers), into Q, which the page prints as `q<i> v1`.
  `rbcheck.py` 1.2 `q` grades Q's seven fill words (`ph` w1, w3, w4 and `mb` w2–w5; the ring
  word is not loaded at `txrb 1`) against P1's 1.4 text, on the slots P1 would grade, and reads
  **`rbcheck verdict EQUAL`** at `RQ-01-C` (slots 0, 1, 2: the `tx` verb at 60, 61 and 1,514 B)
  and at `RQ-02-C` (at least two `nic_xmit` fills of the host's 61-B echo replies since
  `RQ-02-S`). Its controls are Q's own: every graded slot prints `q<i> v1`, and its `w` line
  names a fill at `rb 1` (and, for the `tx` read-back, the path and F expected). The engine's
  pointer and `OWN` are not controls here, because Q was loaded before the slot was handed to
  the engine, so a VOID of P1's kind cannot void it (rbcheck's self-test grades one page EQUAL
  by `q` and VOID by `fill`). The fills are held with `txstall on` as in P1; what `I-RQ` sends
  unheld is its liveness probes' 60-B replies (§ 0 ⑤). Beside it, readings: `RQ-01-F` and
  `RQ-02-F` (P1's read-back of the same dumps, at `txrb 1`, with its stall controls), 1.5's own
  `rb chk N bad M`, and the five alloc-only words in Q. **It is a queue-time reading at a
  non-default setting, not the default-settings read-back**: whatever it reads, `R6b-2`'s
  conjunct stays *undetermined on this boot*. **What it can establish**: that at `txrb 1` the
  words 1.5's two writers stored at `txlen rlxfw` were, loaded back just before `OWN`, 1.4's
  words — the stores `storeseq` proved at the desk, read on silicon on this boot. **What it
  cannot**: what the engine fetched (Q is the CPU's own load, and whether an uncached load
  waits for the write buffer to drain is 推 for the RLX4181, so a Q equal to the store does not
  show the store reached DRAM); anything at `txrb 0`, where no call and no uncached load sit
  between the stores and `OWN` (the default pays one cached load of the policy and a branch),
  so a difference that depends on that timing would not show; `nic_xmit`'s fills at lengths
  other than 61 B (a 60-B one is graded only if the board's ARP reply lands after `RQ-02-S`,
  推); a change to memory after the load (a later store, or the engine writing a descriptor
  word), which rbcheck prints as a reading for every graded word whose `r` differs from Q,
  while it grades Q alone. **Refuted by** DIFFER at either. rbcheck names each differing word
  with the word memory holds at page time (`r now`): the word Q loaded (`same`) says memory
  does not hold 1.4's word either — the stores wrote another word, or never landed (rbcheck
  marks a word equal to alloc's) — and no "1.4 arm" below would be shown to be 1.4; 1.4's word
  (`load-early`) says the load returned a word a store later replaced — the write buffer's
  order, a reading for P12's ordering row, not a refutation of what was stored; neither
  (`other`) is left to the owner. § 6 decides each.
* **P2, the guards the card rests on** (`I-VC`, `VC-EE`, `SW-CLR`, `W-2-EP`, gates): with
  `rlx0` up, `txlen vendor` refuses `-16` and leaves `tx15` at `rlxfw … dirty 0`; `sweep 60 60
  0` refuses `-16` and prints no mark; `sweep 59 1514 60` refuses `-22`; with `rlx0` down
  `txlen vendor` is accepted (`v15 last txlen 13`, 13 = the bytes `echo` wrote) and marks the
  policy dirty; `engine on` then refuses `-151` (ESTALE on this architecture) and so does
  `ifconfig rlx0 up` (`nd_up 0`); `arm` clears dirty and rewrites all four TX slots to alloc's
  words (`VC-07-C`, a reading: `rbcheck alloc`); `txlen rlxfw`, `arm`, `up` returns to 1.4
  (`v15 last txlen 12`, `nd_up 1`) and the host is reached. After `LB-1`'s eleven records, a
  sweep under another key refuses `-17` (EEXIST) with no mark and the records untouched (`rec
  11`), and `swclear` is accepted (`v15 last swclear 8`) and leaves `mt none 1455` and `rec 0`.
  At `txlen rlxfw` a wire sweep over two lengths refuses `-1` (EPERM, the owner's bound) with no
  mark and the wire records untouched; `W-1` at `txlen vendor` is its permitting half.
  **Refuted by** any other return: a guard that does not refuse or permit as written, recorded
  as a finding (§ 6's branch restores 1.4 and the A/B continues, since each switch cell below
  gates its own `tx15`). Untested here: the `-EBUSY` a second writer meets while a sweep runs
  (it needs a second shell, § 7).

### 3.3 The stack A/B (`I-E`): E2 at block 45's spacing — the fix (`F1`), 1.4 (`L1`), the fix (`F2`)

Each arm: the policy switch (`ifconfig rlx0 down`, `txlen`, `arm`, `ifconfig rlx0 up`), the
port-3 and liveness gates, a bracket, block 45's own E2 (`ISZ`: eleven `ping -c 20 -i 0.05
-w 10` runs back to back), a bracket, and the path gate over the pair. The three arms type the
same cells at the same spacing; only the `txlen` word differs.

* **P3, the fix (`F1` and `F2` each; `D2`'s first conjuncts).** 220 of 220 — each of the
  eleven `ping`s `20 packets transmitted, 20 received`; `i` = 220; the capture's window holds
  220 echo replies, eleven identifiers with sequence numbers 1-20 each; `j = f = d = 0`,
  `dropev` Δ 0, the `512 - 1023` bucket Δ 0, `n_recov_fire` Δ 0, `vlan8100 0`, `excess 0`
  only. And the frames are their own lengths at the CPU port: buckets Δ `64:` 20 + a,
  `65 -127:` 60, `128 -255:` 0, `256 - 511:` 60, `1024 - 1518:` 80, `c` = 220 + a, where a is
  the board's ARP frames in the bracket (the capture's `arp` class). **Refuted by** any
  conjunct failing while the arm's `path` reads `covered yes`: `D2` is not met on this boot, and
  which conjunct names what — a frame 4 bytes long at every length (the buckets shift; the
  capture's lengths move by 4) says the vendor's lengths put an extra 4 bytes on this engine's
  wire.
* **P4, 1.4 (`L1`), the positive control.** The loss reproduces: `j + f + d ≥ 1` in the
  bracket **and** at least one of the seven lengths (61, 62, 63, 263, 277, 1,511, 1,512)
  answered fewer than 20 by `-w 10`. **Refuted by** 220 of 220 with no refusal: the positive
  control failed, and this boot says nothing about the fix (the gate's `D2` clause).
  Readings: per-length counts against block 45's (`ping`'s own lines, and the capture's
  sequence numbers per identifier), the tag at 277 (`NET-119`).
* **P3's third reading, order.** `F2` repeats `F1` after `L1` has faulted on the same boot:
  if the fix held only on a fresh history, `F2` fails where `F1` passed.
* **The scope of `D2`'s refutation clause, fixed now.** *220 of 220 while `JabberErr`,
  `FragErr` or `Drop` moves anywhere else in the same boot* reads exactly the brackets whose
  whole board window ran at `txlen vendor`: `E-F1-R0`→`E-F1-R1`, `E-F2-R0`→`E-F2-R1`,
  `LB-2-R`→`LB-V-R` (the fix's loopback map), and `LB-V-R`→`W-1a-R` … `W-1c-R`→`W-1d-R` (the
  fix's wire sweep). Excluded by design, as 1.4's controls or other settings: `E-L1`, `W-2`,
  `LB-1`, `LB-2`, `CO-1`, `CO-2`, `DS-r`, `I-RQ` (`txrb 1`, if it runs), the `M-` maps and the
  history cells; `DS-v` ran at the
  fix with `rlx0` up but shares its bracket (`LB-1-R`→`DS-9-R`) with `DS-r`, so it is read by its
  own dumps (P6b), not by this clause. D2's boot 1 needs `F1` and `L1`; `F2` is the order
  reading.

### 3.4 The sweep's positive control, its containment, NET-61's runs and the carry-over (`I-LB`)

`I-E` ends on the fix, so after the stack's closing bracket (`LB-00-R`, `rlx0` up) the block
types `ifconfig rlx0 down`, `txlen rlxfw` and `irqon` (the interrupt stays handled while the
interface is down); `LB-00-K` gates `rlx0` down and the policy `rlxfw … dirty 1` before the
first sweep, whose own first act is the `arm` that clears it; `LB-00-R2`, read with `rlx0`
down, opens the containment window.

* **P5** (`LB-1`, `sweep L L 0` at each of E2's eleven, block 46's protocol: frame b at L
  again; one unit per sweep, accumulating under one key). Per length, from the page: at 61, 62,
  63, 263, 277, 1,511, 1,512 map code 2 (bad b), frame a right (`ph_a` L + 4, class 1),
  `ph_b` 9,831, 9,831, 9,831, 11,887, 15,999, 3,663, 3,663; at 60, 276, 1,513, 1,514 code 1
  with `ph_b` L + 4; `delta0 0`, `v15 last sweep` the bytes `echo` wrote. Beside it the marks,
  a reading: `SWSUM=00010000` each, `SWEND=00000001` at the seven and `00000000` at the four.
  After the eleven, `mt none 1444 clean 4 bad_b 7 bad_a 0 void 0 skew 0` and `hb n 4 other 0
  void 0` / `hb 9831:3:61-63 11887:1:263-263 15999:1:277-277 3663:2:1511-1512`. Frame b's
  **class** is not predicted (no seating has read the looped b frame's head: block 46's wrong
  frames were dropped, `n_skb_fail` +1 each): 2 (long) says the looped frame carries b's own
  head with a wrong length; C (repeat) that it carries frame a's head — the engine sent a's
  buffer again, or b's slot read a's; D (digit) a head of ours from neither; 5 (alien) a head
  that is not ours. Which one is a reading, and bears on H-prev against H-own/H-slot only
  through the head, not the length word. **Refuted by** any length's map code or `ph_b`
  differing, or `delta0` other than 0: the sweep does not reproduce block 46's arm C, so the
  full maps below are the sweep's own readings and not block 46's instrument extended, and a
  code-path effect cannot be told from a DMA-base one (`bufs` is printed with every sweep).
* **P6, containment (gate `LB-1-G`).** `brdelta` over `LB-00-R2` → `LB-1-R` (`rlx0` down
  throughout): `leak none` — `c` Δ 0, port 3's output Δ 0, host `h` Δ 0. **Refuted by**
  anything reaching any of the three: `LBMODE` does not isolate, and no map at 1.4's settings
  runs, nor `NET-61`'s runs (§ 6).
* **P6b, `NET-61` 殘留's burst half and `NET-103` 殘留 ④** (`DS-r` at 1.4, `DS-v` at the fix;
  block 46 arm C's protocol with `rlx0` up so NAPI harvests: re-arm; `lb on` and `tx` at L; `tx`
  at L, `sleep 1`, `lb off` and the dump). *Every length* in `NET-61` 殘留's prediction is read
  here as E2's eleven, block 46's own lengths; the other 1,444 are not tested by this card
  (§ 7). From `BD series` over each setting's twelve dumps: at 1.4, Δ`n_dsync` +1 and
  Δ`n_skb_fail` +1 at 61, 62, 63, 263, 277, 1,511 and 1,512 (7 of each) and 0 at 60, 276, 1,513
  and 1,514; at the fix 0 and 0 at all eleven; Δ`n_dsync_chk` ≥ 1 in every run (the denominator:
  without it a 0 claims nothing) and Δ`n_rx` 2 (both frames harvested). **Refuted by**
  (`NET-61` 殘留's own clause) any length whose Δ`n_dsync` disagrees with its bad-b membership
  — read from this boot's `LB-1` map (P5), not assumed — or any Δ`n_dsync` ≠ 0 at the fix.
  `NET-103` 殘留 ④: Δ`n_ph_diff`, Δ`n_ph_bad` and `ph_first_*` from the same dumps, a reading
  beside block 46's 0 over 77 reads; `n_ph_bad` ≠ 0 would reopen `NET-103` by its ①. The sweep
  never reads these counters (讀: it classifies with `nic_ph_class` directly and never calls
  `nic_ph_buf` or `nic_dsync_check`; `rlx0` is down, so NAPI does not run; each sweep ends in
  `arm`, which zeroes both RX positions): a 0 read from any sweep's dump is structural, and is
  never taken as `NET-61`'s or `NET-103`'s reading.
* **P7, the byte's source** (`CO-1`, `sweep 61 61 1514`; `CO-2`, `sweep 277 277 61`, 推):
  frame b's `ph_len` is 9,831 / 5,719 / 9,831 at `CO-1` and 15,999 / 9,831 / 8,224 at `CO-2`
  under H-prev (the previous frame's bytes), H-own (the probe's own grid), H-slot (the slot's
  buffer at the previous frame's grid); map code 2 at both. **Refuted by** a value none of the
  three gives: a fourth source.

### 3.5 The full maps (`LB-2` at 1.4, `LB-V` at the fix; probe 60)

* **P8** (`LB-2`, 1.4). `sw done … rc 0`; `sw scored 1455 bad_a 0 bad_b 728 void 0 skew 0`,
  `delta0 0`, `mt none 0 clean 727 bad_b 728 bad_a 0 void 0 skew 0`; bad-b exactly at the 728
  lengths with L mod 8 ∈ {5, 6, 7, 0} (M1-cover8; M1-room8ph, M2-shift8 and M2-shift8m say the
  same at 1.4's settings, so this map does not separate them); the marks `SWSUM=05AF0000`,
  `SWEND=000002D8` (a reading). `hb` equals exactly one of three blocks: H-prev (eight values,
  1,607…15,999, at 92/92/88/88/92/92/92/92 lengths), H-own (9,831 at all 728) or H-slot (8,224
  at 724 and 9,831 at 4). **Refuted by** a length off the set, a bad a, or an `hb` equal to
  none (the byte law does not hold past the first mis-sent frame, or a fourth source).
* **P9** (`LB-V`, the fix). `sw done … rc 0`; `sw scored 1455 bad_a 0 bad_b 0 void 0 skew 0`,
  `delta0 0`, `mt none 0 clean 1455 …` (M1-cover8 and M1-room8ph both predict 0);
  `SWSUM=05AF0000`, `SWEND=00000000`. `delta0 4` would be a `D2` finding in itself: the engine
  loops back four bytes more than `ph_len` at every length, which the classifier absorbs into
  delta0 and the wire does not. **Refuted by** any bad length: the fix does not hold at every
  length — `R6b-2`'s named risk, whose first lengths the proposal lists (64, 80, 96 … and 70,
  86, 102 …); if the bad set equals M2-shift8's (728 at {5, 6, 7, 0}) or M2-shift8m's (727 at
  {1, 2, 3, 4}), that rule, 推-refuted by block 38's V6, returns. **P9's zero depends on P8**:
  if `LB-2` reads 0 bad at 1.4 on the same boot (and `LB-1` 0 of 7), the loopback does not show
  the fault and `LB-V`'s 0 says nothing about the fix.
* **VOID, the rule written now** (`PROPOSAL-R6b-2.md` § 10.7). A unit whose frames were FOREIGN
  twice is VOID: not scored, never bad. Over a map with `void` > 0, the host's Δ`tx_packets`
  across that map's bracket decides: Δ 0 — nothing from the host can have taken an RX slot, and
  the VOID units are the board's own corruption, a finding at those lengths; Δ > 0 — `swcheck`'s
  `void N at …` names them, and each is swept again once in loopback under the same key as a
  declared cell `X-VD<n>` (`echo sweep L L 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx`),
  whose record replaces the VOID one. P8's and P9's `void 0` is therefore a prediction that the
  host stays silent at the board for a map's 32 s, and a VOID is a reading, never a refutation
  of a rule.

### 3.6 The wire (`I-W`)

* **P10, the fix over every length (`D2`'s sweep conjunct).** In each of `W-1a`…`W-1d`
  (60–423, 424–787, 788–1,151, 1,152–1,514; 364, 364, 364 and 363 units): `sw done mode wire
  … rc 0`, `j = f = d = 0`, `c` = `o` = `h` = two frames a unit (728, 728, 728, 726); the capture
  holds them with `lenby 1:` the sub-range (61–423 in the first) and the probes at 60 (365, 364,
  364, 363); in all, 2,910 frames and `jfd 0`. In wire mode the map holds only units whose slots
  retired (code 1) and no per-length verdict; the marks read `SWSUM=016C0000` (`016B0000` for
  the fourth) and `SWEND=00000000`, a reading. **Refuted by** `jfd ≥ 1` in any quarter (the
  conjunct fails; the quarter bisects it, and the sweep stops there, § 6) or lengths shifted on
  the capture (the fix's frames are not their own length on the wire). **What it holds for**:
  `nic_do_tx`'s fills in TX slots 0 and 1, each the first or second frame after a re-arm; the
  stack path (`nic_xmit`) at the fix is tested only by E2's eleven and the 60-B liveness frames
  (§ 7). **P10's zero depends on P11**: if `W-2` reads `jfd 0` at all 19 predicted-bad lengths,
  1.4 did not fault on the wire this boot and `W-1`'s zero says nothing about the fix.
* **P11, 1.4 bounded, one bracket per length** (35 lengths — every residue mod 8 at
  64–71, 768–775 and 1,496–1,503, and E2's eleven — swept in this order: 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 263, 276, 277, 768, 769, 770, 771, 772, 773, 774, 775, 1496, 1497, 1498, 1499, 1500, 1501, 1502, 1503, 1511, 1512, 1513, 1514), each a
  single-length wire sweep, `sw done mode wire from L to L probe 60`, the first after the
  owner's bound refused a two-length one (`W-2-EP`). At the 19 lengths with L mod 8 ∈ {5, 6, 7,
  0}: `jfd` Δ 1, `h` Δ 1 (frame a arrives, b is refused), `c` Δ 2; at the 16 others: `jfd` Δ 0,
  `h` Δ 2, `c` Δ 2. In all: `jfd` 19, `c` 70, `h` 51. Every wrong `ph_b` any of the three
  sources predicts at these lengths is at least 1,607, past `AcptMaxLen` 1,536 (讀 on port 0,
  `notes/switch-driver.md`; the CPU port's own value is unread), so a mis-sent b is a jabber.
  **Refuted by** a length whose row differs: the loopback map at 1.4 does not predict the wire
  there. A mis-sent b that reaches the host (`h` 2 at a bad length, with an extra length on the
  capture) is the case the owner's containment covers; it is counted and its bytes past 64 are
  not kept.

### 3.7 The mechanism maps (`I-M`, loopback, probe 60)

* **P12.** Each map compared, length by length, with four rules (`swcheck.py` 1.1; counts from
  `arith49.out`, bufs mod 8 = 0 as block 46 read it, `A15C8290`):

  | setting | M1-cover8 | M1-room8ph | M2-shift8 | M2-shift8m | `SWEND` under M1-cover8 |
  |---|---:|---:|---:|---:|---|
  | `txlen mlen` | 0 | 728 | 728 | 727 | `00000000` |
  | `txlen ext` | 728 | 0 | 728 | 728 | `000002D8` |
  | `txlen d1` | 182 ({5}) | 728 | 728 | 727 | `000000B6` |
  | `txlen d2` | 364 ({5, 6}) | 728 | 728 | 727 | `0000016C` |
  | `txlen d3` | 546 ({5, 6, 7}) | 728 | 728 | 728 | `00000222` |
  | `txoff 0` | 728 ({5, 6, 7, 0}) | 728 | 728 ({7, 0, 1, 2}) | 728 ({7, 0, 1, 2}) | `000002D8` |
  | `txrb 1`, `2`, `4`, `8` | 728 each | 728 | 728 | 728 | `000002D8` |

  A rule whose set equals a map survives that arm; a map equal to none refutes all four at
  that setting. The `d` series is the one prediction M1-cover8 alone makes, graded. Under
  `txrb`: an ordering fix clears bad-b under 1 or 2 and not under 4 or 8 (their controls);
  M1-cover8 predicts no change under any; `M-rb1`'s and `M-rb2`'s `rb chk N bad 0` is a reading
  (1.5's own check of every fill's Q against what it meant to write), taken as the difference
  from the same line on `M-rb1-V`'s and `M-rb2-V`'s pages: the driver counts from boot, and
  counts `I-RQ`'s fills if it ran. Under `mlen`, `vendor` or
  `d1`–`d3` the first frame a may itself be wrong: the sweep then ends `-71` (`SWEND=FFFFFFB9`,
  the page's `v15 last sweep -71` and `sw noreg` naming the class) — a finding about that
  setting, not a pass (`PROPOSAL-R6b-2.md` § 11.5). The VOID rule of § 3.5 applies to every map.
* **P13, history** (`HI-1`…`HI-4`, 1.4's settings, four `tx` frames after one re-arm with
  `rlx0` down, the looped `ph_len` read from `rxd0`…`rxd3`: r right, w wrong, `-` did not
  land). Nothing refills the 8-mbuf RX ring while `rlx0` is down (讀 `nic_isr` schedules NAPI
  only when `nic_ndev_up`), and a wrong frame takes the chain block 46 measured (2,042 B in the
  first mbuf, 2,044 in each further one: 5 mbufs for 9,831, 2 for 3,663), so a later frame may
  not fit (推: a frame whose chain does not fit is taken as not landing, and nothing after it
  lands). Predicted, per rule and byte source (`arith49.out`):

  | cell | sequence | carried rule, H-prev / H-own | second-frame rule, H-prev / H-own |
  |---|---|---|---|
  | `HI-1` | 60, 61, 61, 60 | `rrw-` / `rrw-` | `rw--` / `rw--` |
  | `HI-2` | 61, 60, 60, 60 | `rw--` / `rw--` | `rrrr` / `rrrr` |
  | `HI-3` | 60, 1,511, 1,511, 60 | `rrww` / `rrw-` | `rww-` / `rwwr` |
  | `HI-4` | 1,511, 60, 60, 60 | `rww-` / `rw--` | `rrrr` / `rrrr` |

  **Refuted by** a pattern equal to none of the four in its row (both rules refuted there). Which
  frames land, and whether a frame that does not fit is dropped or truncated (`MBUF_RUNOUT`), is
  a reading. Void if the host's `tx_packets` moved over `HI-00` → `HI-9` (a host frame can take
  an RX slot).

### 3.8 The maps, `n_writes`, and the host path

* **P14.** `R1-MB0` and `R1-MB1` read block 46's map digest (`0927be41…`), one `DIFFER` in
  group 0, 31 the same; `R1-NW0` and `R1-NW1` `n_writes 0`, and `recipe_id 06C39CA3`
  (a reading beside `looprun`'s `RLXFW-ID0`). **Refuted by** another digest or group line
  (flash moved since block 46) or `n_writes` other than 0.
* **P15, the host path (`NET-124` 殘留), a decision rule written now.** Every liveness gate
  4 of 4, every port-3 gate `LinkUp` on both readers, every stack arm `covered yes`, every
  kernel-log window `follower 1`. Beside them the kernel log, before power clean
  (`bug_preempt 0`, `usbnet_xmit 0`, `call_trace 0`: a precondition, since with the board off
  there is no carrier and so no transmit) and, in the press, read per window as `bug_preempt`
  over Δ`tx_packets`: at least 1 in every window where the path works — the trace is this host's
  `usbnet` under `usbip` on every transmit, not `NET-124`'s signature; 0 while the path works
  and > 0 only in a silent state — it marks that state on the host side, candidate (a). The
  `link_up` count of `I-1`'s windows (the board's power bringing the host adapter's carrier up)
  is the log's in-press positive control. No prediction of which (推 either way).

### 3.9 Which mechanism each arm can refute

| candidate | arm | refuted when |
|---|---|---|
| M1-cover8 (the `m_len` cover rule) | `LB-2`, the `d` series, `mlen`, `ext`, `W-2` | a map off its set (P8, P12); a wire length off its row (P11) |
| M1-room8ph (`m_extsize` − `ph_len`) | `mlen`, `ext`, the `d` series | a map off its set (P12) |
| M2-shift8 / 8m (the buffer address) | `txoff 0`, `LB-V`, `mlen` | P9, P12 |
| an ordering fault (the `OWN` write before the fields land) | `txrb 1`, `2` against `4`, `8`; `I-RQ`'s `load-early`, if it runs (a reading) | P12's `txrb` rows; P1b |
| the byte's source (H-prev, H-own, H-slot) | `LB-2`'s `hb`, `CO-1`, `CO-2` | P7, P8 |
| the carry-over's structure (order or slot) | `HI-1`…`HI-4` | P13 |
| `NET-61`'s ring desync following the bad-b set | `DS-r`, `DS-v` | P6b |
| `M4`, the tag at 277 | `E-L1`'s capture, and the sweeps' capture (tagged `0x88B5` kept) | read, as block 46 did; not a prediction here |
| `M5`, the portlist and flags | — | not in this card |

---

## § 4 Standing rules

🔴 **No flash write**: no `FLW`, `EW`, `EB`, non-zero `AUTOBURN` or `FLR`; `cardcheck`
refuses the verbs (`FW-113`); every upload is `looprun`'s, which requires `00000000` read back
from the `AUTOBURN` word before it uploads. 🔴 Every `--send` is at most 127 characters, holds
no `$` and no upper-case word (the generator refuses one: a macro name would expand inside
it). 🔴 **No gate reads a console mark** (`FW-47`; a `cardnum` row counts zero). 🔴 **Every
refusal the card provokes is a gated guard**: `verbcheck49.py` replays every write through the
committed header before power, and the generator refused to write a card it failed. 🔴 **No
frame capture is printed**, and the captures are cut at 64 bytes and filtered to the board's
address (§ 0 ⑤); only `pcapwin.py` reads them. 🔴 **No line of the host's kernel log reaches
`bench/`**: only `dmesgwin.py`'s counts. 🔴 No host cell prints a home path into `bench/`: the
tools print basenames (`tools/audit-bench-log.py`). 🔴 No cell touches the reset button or the
watchdog. 🔴 `rlx0` goes down only in the card's own cells, and every `up` finds the ring
freshly armed with the engine off (`NET-58`; the generator refuses otherwise, `controls49.sh`
C5). 🔴 No step removes `/proc/rtl865x/`. 🔴 `sudo -n pkill -INT -x tcpdump` stops every
`tcpdump` on the host: `R0-TCPC` requires none before power, `E-LIVE` and `S-LIVE` exactly one
before their arms. 🔴 Exactly one `dmesg` process, the off-card follower, runs from before
`I-0` to after `I-Z`. 🔴 `I-RQ` runs only after a VOID of the read-back, and ends where `I-RB`
ends (`rlx0` up, `txlen rlxfw txoff 2 txrb 0 dirty 0`); no cell after it reads one of its logs.
The generator refuses a card that breaks either, and replays both paths, with `I-RQ` and
without, through the `NET-58` rule and `verbcheck49.py`. ⚠️ Off-card cells are declared in
`bench/2026-09-26/CORRECTIONS-block47.md` before they run, except those § 6 declares now with their text (each is still logged there as
it runs) and a power-off, which § 6 decides now.

---

## § 5 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0 --baud 38400`
`LR` = `/usr/bin/python3 tools/looprun.py --mode bench --out-dir bench/2026-09-26 --skip S2,S3,S4 --recipe-override 06c39ca3 --dwell-seconds 2.5`
`QIMG` = `--image /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom --image-sha256 7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9`
`FL <ip>` = `sudo -n ip neigh flush to <ip>/32 dev enxfc19286184c9 ; ip -4 neigh show <ip> dev enxfc19286184c9 | wc -l` — prints `0`
`HN` = `grep -H . /sys/class/net/enxfc19286184c9/statistics/* ; cat /proc/net/snmp ; ip -s -s link show dev enxfc19286184c9 | grep -v link/ ; ip -4 neigh show 10.1.1.3 dev enxfc19286184c9 | awk '{print $NF}'` — block 46's, unchanged
`PL` = `ping -I enxfc19286184c9 -c 4 -i 0.25 -W 1 -s 18 10.1.1.3` — the liveness probe: 60-B frames, clean at every setting on this card
`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s $s -i 0.05 -w 10 -q <ip>; done`
`TDE <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap/<f> ether src 02:52:4c:58:46:57`
`TDS <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap/<f> 'ether src 02:52:4c:58:46:57 and (ether proto 0x88b5 or (ether proto 0x8100 and ether[16:2] = 0x88b5))'`
`PWE <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py window /home/key/fwre-work/rebuild/s112/r6b3/pcap/WE.pcap --if enxfc19286184c9 --prev <prev>`
`PWS <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py window /home/key/fwre-work/rebuild/s112/r6b3/pcap/WS.pcap --if enxfc19286184c9 --prev <prev>`
`DW <prev>` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/dmesgwin.py window /home/key/fwre-work/rebuild/s112/r6b3/host/dmesg-w.log --prev <prev>`
`RBC` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py`
`SWC` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/swcheck.py page`
`BD` = `/usr/bin/python3 /home/key/fwre-work/rebuild/s112/r6b3/card/brdelta.py`
`MB <cap>` = `tr -d '\r' < <cap>.log | sed -n '/^[0-9A-F]\{6\} /,/^map_lines /p' | awk 1 | sha256sum ; FWRE_WORK=/home/key/fwre-work /usr/bin/python3 tools/flashmap.py compare <cap>.log ; true` — block 46's, unchanged

A `ping`'s `-s` is L − 42 and a `tx` verb's last argument L − 14. A stimulus cell's longest
silence is under 1 s and its `--idle` is 3; every read ends on a pattern (`--until`) that
also matches the loader's banner. A sweep cell is one send — `swclear` first where its key is
new, the sweep, then `cat /proc/rtl819x-nic-tx` — and ends on the page's last `ww` line and the
prompt, whether the sweep was accepted, refused or ended by an errno; its cap is 180 s for a
full map (a guess of 40 s, 4.5×; 讀 about 32 s of console at 38,400), 90 s for a quarter, 15 s
for one length. Every host bracket passes the previous host bracket's log to `pcapwin` and to
`dmesgwin` as `--prev`, per capture and for the kernel log, so each window starts where the
previous one ended.

### Before power

```
CAP --out bench/2026-09-26/R0-PRE --seconds 3
HOST bench/2026-09-26/R0-PREC :: ls bench/2026-09-26/R0-PRE.log bench/2026-09-26/R0-PRE.timing bench/2026-09-26/R0-PRE.meta.json && cat bench/2026-09-26/R0-PRE.meta.json
HOST bench/2026-09-26/R0-ADDR :: sudo -n ip link set enxfc19286184c9 up ; sudo -n ip addr replace 10.1.1.2/24 dev enxfc19286184c9 ; ip -4 addr show dev enxfc19286184c9
HOST bench/2026-09-26/R0-ETH :: /usr/sbin/ethtool -i enxfc19286184c9 ; uname -r
HOST bench/2026-09-26/R0-TCPC :: pgrep -xc tcpdump ; true
HOST bench/2026-09-26/R0-DMSG :: pgrep -xc dmesg ; true
HOST bench/2026-09-26/R0-DW0 :: DW none
HOST bench/2026-09-26/R0-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-26/R0-PCAP :: mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/pcap && find /home/key/fwre-work/rebuild/s112/r6b3/pcap -name '*.pcap' | wc -l
HOST bench/2026-09-26/R0-SUM :: sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/swcheck.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/brdelta.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/dmesgwin.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/verbcheck49.py ; sha256sum < /home/key/fwre-work/rebuild/s112/r6b3/card/fixtures/MANIFEST.sha256
HOST bench/2026-09-26/R0-ST :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/swcheck.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/dmesgwin.py --self-test ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/brdelta.py --self-test
HOST bench/2026-09-26/R0-VERB :: /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/verbcheck49.py bench/2026-09-26/PREDICTIONS-B49-block47.md --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top ; /usr/bin/python3 -B /home/key/fwre-work/rebuild/s112/r6b3/card/verbcheck49.py --self-test bench/2026-09-26/PREDICTIONS-B49-block47.md --cell /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top
HOST bench/2026-09-26/R0-H :: HN
```

### The press — the catch, the shell, the opening map, `n_writes`

```
CAP --out bench/2026-09-26/R1-CATCH --esc 180 --esc-period 0.002 --seconds 200
HOST bench/2026-09-26/R1-FL :: FL 10.1.1.1 ; FL 10.1.1.3
HOST bench/2026-09-26/R1Q :: LR --cell R1Q QIMG --iterations 1
CAP --out bench/2026-09-26/R1-PS --send 'ps' --idle 3 --seconds 30
CAP --out bench/2026-09-26/R1-M0 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-26/R1-MB0 :: MB bench/2026-09-26/R1-M0
CAP --out bench/2026-09-26/R1-NW0 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
```

### The read-back, first

```
CAP --out bench/2026-09-26/RB-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/RB-00-H :: HN ; DW bench/2026-09-26/R0-DW0.log
CAP --out bench/2026-09-26/RB-00-T --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/RB-01-DN --send 'ifconfig rlx0 down' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-01-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-01-S --send 'echo txstall on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-01-T --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-01-R --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RB-01-C :: RBC fill bench/2026-09-26/RB-01-R.log --expect 0:tx:60,1:tx:61,2:tx:1514
CAP --out bench/2026-09-26/RB-01-X2 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-01-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RB-02-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/RB-02-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/RB-00-H.log
CAP --out bench/2026-09-26/RB-02-S --send 'echo txstall on > /proc/rtl819x-nic ; cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RB-02-P :: ping -I enxfc19286184c9 -c 2 -i 0.5 -W 1 -s 19 10.1.1.3
CAP --out bench/2026-09-26/RB-02-R --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RB-02-C :: RBC fill bench/2026-09-26/RB-02-R.log --expect-xmit 61:2 --base bench/2026-09-26/RB-02-S.log
CAP --out bench/2026-09-26/RB-02-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
HOST bench/2026-09-26/RB-02-L2 :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/RB-02-L.log
CAP --out bench/2026-09-26/RB-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/RB-09-H :: HN ; DW bench/2026-09-26/RB-02-L2.log
HOST bench/2026-09-26/RB-09-D :: BD pair bench/2026-09-26/RB-00-R.log bench/2026-09-26/RB-09-R.log --host bench/2026-09-26/RB-00-H.log bench/2026-09-26/RB-09-H.log
```

### Only after a VOID of the read-back: Q at `txrb 1`, then 1.4's defaults again

```
CAP --out bench/2026-09-26/RQ-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/RQ-00-H :: HN ; DW bench/2026-09-26/RB-09-H.log
CAP --out bench/2026-09-26/RQ-01-V --send 'ifconfig rlx0 down ; echo txrb 1 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/RQ-01-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-01-S --send 'echo txstall on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-01-T --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-01-R --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RQ-01-C :: RBC q bench/2026-09-26/RQ-01-R.log --expect 0:tx:60,1:tx:61,2:tx:1514
HOST bench/2026-09-26/RQ-01-F :: RBC fill bench/2026-09-26/RQ-01-R.log --expect 0:tx:60,1:tx:61,2:tx:1514
CAP --out bench/2026-09-26/RQ-01-X2 --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-01-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-02-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/RQ-02-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/RQ-00-H.log
CAP --out bench/2026-09-26/RQ-02-S --send 'echo txstall on > /proc/rtl819x-nic ; cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RQ-02-P :: ping -I enxfc19286184c9 -c 2 -i 0.5 -W 1 -s 19 10.1.1.3
CAP --out bench/2026-09-26/RQ-02-R --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/RQ-02-C :: RBC q bench/2026-09-26/RQ-02-R.log --expect-xmit 61:2 --base bench/2026-09-26/RQ-02-S.log
HOST bench/2026-09-26/RQ-02-F :: RBC fill bench/2026-09-26/RQ-02-R.log --expect-xmit 61:2 --base bench/2026-09-26/RQ-02-S.log
CAP --out bench/2026-09-26/RQ-09-SW --send 'ifconfig rlx0 down ; echo txrb 0 > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/RQ-09-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/RQ-09-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/RQ-00-H.log
CAP --out bench/2026-09-26/RQ-09-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/RQ-09-H :: HN ; DW bench/2026-09-26/RQ-00-H.log
HOST bench/2026-09-26/RQ-09-D :: BD pair bench/2026-09-26/RQ-00-R.log bench/2026-09-26/RQ-09-R.log --host bench/2026-09-26/RQ-00-H.log bench/2026-09-26/RQ-09-H.log
```

### The guards, refusing and permitting

```
CAP --out bench/2026-09-26/VC-01 --send 'echo txlen vendor | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-02 --send 'echo sweep 60 60 0 | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-03 --send 'echo sweep 59 1514 60 | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-04 --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-05 --send 'echo engine on | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-06 --send 'ifconfig rlx0 10.1.1.3 up ; cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-07 --send 'echo arm > /proc/rtl819x-nic ; cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/VC-07-C :: RBC alloc bench/2026-09-26/VC-07.log
CAP --out bench/2026-09-26/VC-08 --send 'echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/VC-08-R --send 'cat /proc/rtl819x-nic /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/VC-09-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/VC-09-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/RB-09-H.log
```

### The stack arms' capture

```
HOST& bench/2026-09-26/W-TCPE :: TDE WE.pcap
```

### The stack A/B

```
HOST bench/2026-09-26/E-LIVE :: pgrep -xc tcpdump ; true
CAP --out bench/2026-09-26/E-F1-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/E-F1-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/E-F1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/VC-09-L.log
CAP --out bench/2026-09-26/E-F1-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-F1-H0 :: HN ; PWE none ; DW bench/2026-09-26/E-F1-L.log
HOST bench/2026-09-26/E-F1-E2 :: ISZ 10.1.1.3
CAP --out bench/2026-09-26/E-F1-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-F1-H1 :: HN ; PWE bench/2026-09-26/E-F1-H0.log ; DW bench/2026-09-26/E-F1-H0.log
HOST bench/2026-09-26/E-F1-D :: BD pair bench/2026-09-26/E-F1-R0.log bench/2026-09-26/E-F1-R1.log --host bench/2026-09-26/E-F1-H0.log bench/2026-09-26/E-F1-H1.log
CAP --out bench/2026-09-26/E-L1-SW --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/E-L1-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/E-L1-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/E-F1-H1.log
CAP --out bench/2026-09-26/E-L1-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-L1-H0 :: HN ; PWE bench/2026-09-26/E-F1-H1.log ; DW bench/2026-09-26/E-L1-L.log
HOST bench/2026-09-26/E-L1-E2 :: ISZ 10.1.1.3
CAP --out bench/2026-09-26/E-L1-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-L1-H1 :: HN ; PWE bench/2026-09-26/E-L1-H0.log ; DW bench/2026-09-26/E-L1-H0.log
HOST bench/2026-09-26/E-L1-D :: BD pair bench/2026-09-26/E-L1-R0.log bench/2026-09-26/E-L1-R1.log --host bench/2026-09-26/E-L1-H0.log bench/2026-09-26/E-L1-H1.log
CAP --out bench/2026-09-26/E-F2-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/E-F2-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/E-F2-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/E-L1-H1.log
CAP --out bench/2026-09-26/E-F2-R0 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-F2-H0 :: HN ; PWE bench/2026-09-26/E-L1-H1.log ; DW bench/2026-09-26/E-F2-L.log
HOST bench/2026-09-26/E-F2-E2 :: ISZ 10.1.1.3
CAP --out bench/2026-09-26/E-F2-R1 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/E-F2-H1 :: HN ; PWE bench/2026-09-26/E-F2-H0.log ; DW bench/2026-09-26/E-F2-H0.log
HOST bench/2026-09-26/E-F2-D :: BD pair bench/2026-09-26/E-F2-R0.log bench/2026-09-26/E-F2-R1.log --host bench/2026-09-26/E-F2-H0.log bench/2026-09-26/E-F2-H1.log
```

### The stack arms' capture stopped

```
HOST bench/2026-09-26/W-TCPEX :: sudo -n pkill -INT -x tcpdump && sleep 1
HOST bench/2026-09-26/W-EWALL :: PWE none
```

### The sweeps' capture

```
HOST& bench/2026-09-26/W-TCPS :: TDS WS.pcap
```

### Loopback: the positive control, the key guard, NET-61's runs, the carry-over, the two full maps

```
HOST bench/2026-09-26/S-LIVE :: pgrep -xc tcpdump ; true
CAP --out bench/2026-09-26/LB-00-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/LB-00-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/E-F2-H1.log
CAP --out bench/2026-09-26/LB-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/LB-00-H :: HN ; PWS none ; DW bench/2026-09-26/LB-00-L.log
CAP --out bench/2026-09-26/LB-00-DN --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo irqon > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/LB-00-K --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/LB-00-R2 --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/LB-00-H2 :: HN ; PWS bench/2026-09-26/LB-00-H.log ; DW bench/2026-09-26/LB-00-H.log
CAP --out bench/2026-09-26/LB-1-0060 --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 60 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0061 --send 'echo sweep 61 61 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0062 --send 'echo sweep 62 62 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0063 --send 'echo sweep 63 63 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0263 --send 'echo sweep 263 263 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0276 --send 'echo sweep 276 276 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-0277 --send 'echo sweep 277 277 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-1511 --send 'echo sweep 1511 1511 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-1512 --send 'echo sweep 1512 1512 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-1513 --send 'echo sweep 1513 1513 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-1514 --send 'echo sweep 1514 1514 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/LB-1-H :: HN ; PWS bench/2026-09-26/LB-00-H2.log ; DW bench/2026-09-26/LB-00-H2.log
HOST bench/2026-09-26/LB-1-G :: BD pair bench/2026-09-26/LB-00-R2.log bench/2026-09-26/LB-1-R.log --host bench/2026-09-26/LB-00-H2.log bench/2026-09-26/LB-1-H.log
CAP --out bench/2026-09-26/VC-EE --send 'echo sweep 61 61 1514 | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/SW-CLR --send 'echo swclear > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-00 --send 'ifconfig rlx0 10.1.1.3 up ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0060-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0060-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0060-B --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0061-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0061-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0061-B --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0062-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0062-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0062-B --send 'echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0063-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0063-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0063-B --send 'echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0263-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0263-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0263-B --send 'echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0276-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0276-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0276-B --send 'echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-0277-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0277-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-0277-B --send 'echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-1511-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1511-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1511-B --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-1512-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1512-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1512-B --send 'echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-1513-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1513-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1513-B --send 'echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-r-1514-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1514-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-r-1514-B --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/DS-r-C :: BD series bench/2026-09-26/DS-r-00.log bench/2026-09-26/DS-r-0060-B.log bench/2026-09-26/DS-r-0061-B.log bench/2026-09-26/DS-r-0062-B.log bench/2026-09-26/DS-r-0063-B.log bench/2026-09-26/DS-r-0263-B.log bench/2026-09-26/DS-r-0276-B.log bench/2026-09-26/DS-r-0277-B.log bench/2026-09-26/DS-r-1511-B.log bench/2026-09-26/DS-r-1512-B.log bench/2026-09-26/DS-r-1513-B.log bench/2026-09-26/DS-r-1514-B.log
CAP --out bench/2026-09-26/DS-v-SW --send 'ifconfig rlx0 down ; echo txlen vendor > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-00 --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0060-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0060-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0060-B --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0061-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0061-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0061-B --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0062-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0062-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0062-B --send 'echo tx 0x3f 0x8800 0 48 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0063-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0063-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0063-B --send 'echo tx 0x3f 0x8800 0 49 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0263-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0263-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0263-B --send 'echo tx 0x3f 0x8800 0 249 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0276-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0276-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0276-B --send 'echo tx 0x3f 0x8800 0 262 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-0277-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0277-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-0277-B --send 'echo tx 0x3f 0x8800 0 263 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-1511-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1511-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1511-B --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-1512-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1512-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1512-B --send 'echo tx 0x3f 0x8800 0 1498 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-1513-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1513-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1513-B --send 'echo tx 0x3f 0x8800 0 1499 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/DS-v-1514-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1514-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-v-1514-B --send 'echo tx 0x3f 0x8800 0 1500 > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/DS-v-C :: BD series bench/2026-09-26/DS-v-00.log bench/2026-09-26/DS-v-0060-B.log bench/2026-09-26/DS-v-0061-B.log bench/2026-09-26/DS-v-0062-B.log bench/2026-09-26/DS-v-0063-B.log bench/2026-09-26/DS-v-0263-B.log bench/2026-09-26/DS-v-0276-B.log bench/2026-09-26/DS-v-0277-B.log bench/2026-09-26/DS-v-1511-B.log bench/2026-09-26/DS-v-1512-B.log bench/2026-09-26/DS-v-1513-B.log bench/2026-09-26/DS-v-1514-B.log
CAP --out bench/2026-09-26/DS-9-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/DS-9-H :: HN ; PWS bench/2026-09-26/LB-1-H.log ; DW bench/2026-09-26/LB-1-H.log
HOST bench/2026-09-26/DS-9-D :: BD pair bench/2026-09-26/LB-1-R.log bench/2026-09-26/DS-9-R.log --host bench/2026-09-26/LB-1-H.log bench/2026-09-26/DS-9-H.log
CAP --out bench/2026-09-26/DS-9-DN --send 'ifconfig rlx0 down ; echo txlen rlxfw > /proc/rtl819x-nic ; echo irqon > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/DS-9-K --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/CO-1 --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 61 61 1514 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/CO-2 --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 277 277 61 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/LB-2-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/LB-2-C :: SWC bench/2026-09-26/LB-2-S.log --setting rlxfw --probe 60
CAP --out bench/2026-09-26/LB-2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/LB-2-H :: HN ; PWS bench/2026-09-26/DS-9-H.log ; DW bench/2026-09-26/DS-9-H.log
CAP --out bench/2026-09-26/LB-V-V --send 'echo txlen vendor > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/LB-V-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/LB-V-C :: SWC bench/2026-09-26/LB-V-S.log --setting vendor --probe 60
CAP --out bench/2026-09-26/LB-V-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/LB-V-H :: HN ; PWS bench/2026-09-26/LB-2-H.log ; DW bench/2026-09-26/LB-2-H.log
HOST bench/2026-09-26/LB-V-D :: BD pair bench/2026-09-26/LB-2-R.log bench/2026-09-26/LB-V-R.log --host bench/2026-09-26/LB-2-H.log bench/2026-09-26/LB-V-H.log
```

### The wire: the fix over every length, then 1.4 at 35

```
CAP --out bench/2026-09-26/W-00 --send 'cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/W-1a-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 423 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-26/W-1a-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-1a-H :: HN ; PWS bench/2026-09-26/LB-V-H.log ; DW bench/2026-09-26/LB-V-H.log
HOST bench/2026-09-26/W-1a-D :: BD pair bench/2026-09-26/LB-V-R.log bench/2026-09-26/W-1a-R.log --host bench/2026-09-26/LB-V-H.log bench/2026-09-26/W-1a-H.log
CAP --out bench/2026-09-26/W-1b-S --send 'echo sweep 424 787 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-26/W-1b-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-1b-H :: HN ; PWS bench/2026-09-26/W-1a-H.log ; DW bench/2026-09-26/W-1a-H.log
HOST bench/2026-09-26/W-1b-D :: BD pair bench/2026-09-26/W-1a-R.log bench/2026-09-26/W-1b-R.log --host bench/2026-09-26/W-1a-H.log bench/2026-09-26/W-1b-H.log
CAP --out bench/2026-09-26/W-1c-S --send 'echo sweep 788 1151 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-26/W-1c-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-1c-H :: HN ; PWS bench/2026-09-26/W-1b-H.log ; DW bench/2026-09-26/W-1b-H.log
HOST bench/2026-09-26/W-1c-D :: BD pair bench/2026-09-26/W-1b-R.log bench/2026-09-26/W-1c-R.log --host bench/2026-09-26/W-1b-H.log bench/2026-09-26/W-1c-H.log
CAP --out bench/2026-09-26/W-1d-S --send 'echo sweep 1152 1514 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 90
CAP --out bench/2026-09-26/W-1d-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-1d-H :: HN ; PWS bench/2026-09-26/W-1c-H.log ; DW bench/2026-09-26/W-1c-H.log
HOST bench/2026-09-26/W-1d-D :: BD pair bench/2026-09-26/W-1c-R.log bench/2026-09-26/W-1d-R.log --host bench/2026-09-26/W-1c-H.log bench/2026-09-26/W-1d-H.log
CAP --out bench/2026-09-26/W-2-V --send 'echo txlen rlxfw > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/W-2-EP --send 'echo sweep 64 65 60 wire | cat > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/W-2-0060-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 60 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0060-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0060-H :: HN ; PWS bench/2026-09-26/W-1d-H.log ; DW bench/2026-09-26/W-1d-H.log
CAP --out bench/2026-09-26/W-2-0061-S --send 'echo sweep 61 61 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0061-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0061-H :: HN ; PWS bench/2026-09-26/W-2-0060-H.log ; DW bench/2026-09-26/W-2-0060-H.log
CAP --out bench/2026-09-26/W-2-0062-S --send 'echo sweep 62 62 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0062-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0062-H :: HN ; PWS bench/2026-09-26/W-2-0061-H.log ; DW bench/2026-09-26/W-2-0061-H.log
CAP --out bench/2026-09-26/W-2-0063-S --send 'echo sweep 63 63 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0063-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0063-H :: HN ; PWS bench/2026-09-26/W-2-0062-H.log ; DW bench/2026-09-26/W-2-0062-H.log
CAP --out bench/2026-09-26/W-2-0064-S --send 'echo sweep 64 64 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0064-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0064-H :: HN ; PWS bench/2026-09-26/W-2-0063-H.log ; DW bench/2026-09-26/W-2-0063-H.log
CAP --out bench/2026-09-26/W-2-0065-S --send 'echo sweep 65 65 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0065-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0065-H :: HN ; PWS bench/2026-09-26/W-2-0064-H.log ; DW bench/2026-09-26/W-2-0064-H.log
CAP --out bench/2026-09-26/W-2-0066-S --send 'echo sweep 66 66 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0066-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0066-H :: HN ; PWS bench/2026-09-26/W-2-0065-H.log ; DW bench/2026-09-26/W-2-0065-H.log
CAP --out bench/2026-09-26/W-2-0067-S --send 'echo sweep 67 67 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0067-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0067-H :: HN ; PWS bench/2026-09-26/W-2-0066-H.log ; DW bench/2026-09-26/W-2-0066-H.log
CAP --out bench/2026-09-26/W-2-0068-S --send 'echo sweep 68 68 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0068-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0068-H :: HN ; PWS bench/2026-09-26/W-2-0067-H.log ; DW bench/2026-09-26/W-2-0067-H.log
CAP --out bench/2026-09-26/W-2-0069-S --send 'echo sweep 69 69 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0069-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0069-H :: HN ; PWS bench/2026-09-26/W-2-0068-H.log ; DW bench/2026-09-26/W-2-0068-H.log
CAP --out bench/2026-09-26/W-2-0070-S --send 'echo sweep 70 70 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0070-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0070-H :: HN ; PWS bench/2026-09-26/W-2-0069-H.log ; DW bench/2026-09-26/W-2-0069-H.log
CAP --out bench/2026-09-26/W-2-0071-S --send 'echo sweep 71 71 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0071-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0071-H :: HN ; PWS bench/2026-09-26/W-2-0070-H.log ; DW bench/2026-09-26/W-2-0070-H.log
CAP --out bench/2026-09-26/W-2-0263-S --send 'echo sweep 263 263 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0263-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0263-H :: HN ; PWS bench/2026-09-26/W-2-0071-H.log ; DW bench/2026-09-26/W-2-0071-H.log
CAP --out bench/2026-09-26/W-2-0276-S --send 'echo sweep 276 276 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0276-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0276-H :: HN ; PWS bench/2026-09-26/W-2-0263-H.log ; DW bench/2026-09-26/W-2-0263-H.log
CAP --out bench/2026-09-26/W-2-0277-S --send 'echo sweep 277 277 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0277-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0277-H :: HN ; PWS bench/2026-09-26/W-2-0276-H.log ; DW bench/2026-09-26/W-2-0276-H.log
CAP --out bench/2026-09-26/W-2-0768-S --send 'echo sweep 768 768 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0768-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0768-H :: HN ; PWS bench/2026-09-26/W-2-0277-H.log ; DW bench/2026-09-26/W-2-0277-H.log
CAP --out bench/2026-09-26/W-2-0769-S --send 'echo sweep 769 769 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0769-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0769-H :: HN ; PWS bench/2026-09-26/W-2-0768-H.log ; DW bench/2026-09-26/W-2-0768-H.log
CAP --out bench/2026-09-26/W-2-0770-S --send 'echo sweep 770 770 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0770-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0770-H :: HN ; PWS bench/2026-09-26/W-2-0769-H.log ; DW bench/2026-09-26/W-2-0769-H.log
CAP --out bench/2026-09-26/W-2-0771-S --send 'echo sweep 771 771 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0771-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0771-H :: HN ; PWS bench/2026-09-26/W-2-0770-H.log ; DW bench/2026-09-26/W-2-0770-H.log
CAP --out bench/2026-09-26/W-2-0772-S --send 'echo sweep 772 772 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0772-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0772-H :: HN ; PWS bench/2026-09-26/W-2-0771-H.log ; DW bench/2026-09-26/W-2-0771-H.log
CAP --out bench/2026-09-26/W-2-0773-S --send 'echo sweep 773 773 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0773-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0773-H :: HN ; PWS bench/2026-09-26/W-2-0772-H.log ; DW bench/2026-09-26/W-2-0772-H.log
CAP --out bench/2026-09-26/W-2-0774-S --send 'echo sweep 774 774 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0774-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0774-H :: HN ; PWS bench/2026-09-26/W-2-0773-H.log ; DW bench/2026-09-26/W-2-0773-H.log
CAP --out bench/2026-09-26/W-2-0775-S --send 'echo sweep 775 775 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-0775-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-0775-H :: HN ; PWS bench/2026-09-26/W-2-0774-H.log ; DW bench/2026-09-26/W-2-0774-H.log
CAP --out bench/2026-09-26/W-2-1496-S --send 'echo sweep 1496 1496 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1496-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1496-H :: HN ; PWS bench/2026-09-26/W-2-0775-H.log ; DW bench/2026-09-26/W-2-0775-H.log
CAP --out bench/2026-09-26/W-2-1497-S --send 'echo sweep 1497 1497 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1497-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1497-H :: HN ; PWS bench/2026-09-26/W-2-1496-H.log ; DW bench/2026-09-26/W-2-1496-H.log
CAP --out bench/2026-09-26/W-2-1498-S --send 'echo sweep 1498 1498 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1498-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1498-H :: HN ; PWS bench/2026-09-26/W-2-1497-H.log ; DW bench/2026-09-26/W-2-1497-H.log
CAP --out bench/2026-09-26/W-2-1499-S --send 'echo sweep 1499 1499 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1499-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1499-H :: HN ; PWS bench/2026-09-26/W-2-1498-H.log ; DW bench/2026-09-26/W-2-1498-H.log
CAP --out bench/2026-09-26/W-2-1500-S --send 'echo sweep 1500 1500 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1500-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1500-H :: HN ; PWS bench/2026-09-26/W-2-1499-H.log ; DW bench/2026-09-26/W-2-1499-H.log
CAP --out bench/2026-09-26/W-2-1501-S --send 'echo sweep 1501 1501 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1501-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1501-H :: HN ; PWS bench/2026-09-26/W-2-1500-H.log ; DW bench/2026-09-26/W-2-1500-H.log
CAP --out bench/2026-09-26/W-2-1502-S --send 'echo sweep 1502 1502 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1502-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1502-H :: HN ; PWS bench/2026-09-26/W-2-1501-H.log ; DW bench/2026-09-26/W-2-1501-H.log
CAP --out bench/2026-09-26/W-2-1503-S --send 'echo sweep 1503 1503 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1503-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1503-H :: HN ; PWS bench/2026-09-26/W-2-1502-H.log ; DW bench/2026-09-26/W-2-1502-H.log
CAP --out bench/2026-09-26/W-2-1511-S --send 'echo sweep 1511 1511 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1511-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1511-H :: HN ; PWS bench/2026-09-26/W-2-1503-H.log ; DW bench/2026-09-26/W-2-1503-H.log
CAP --out bench/2026-09-26/W-2-1512-S --send 'echo sweep 1512 1512 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1512-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1512-H :: HN ; PWS bench/2026-09-26/W-2-1511-H.log ; DW bench/2026-09-26/W-2-1511-H.log
CAP --out bench/2026-09-26/W-2-1513-S --send 'echo sweep 1513 1513 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1513-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1513-H :: HN ; PWS bench/2026-09-26/W-2-1512-H.log ; DW bench/2026-09-26/W-2-1512-H.log
CAP --out bench/2026-09-26/W-2-1514-S --send 'echo sweep 1514 1514 60 wire > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 15
CAP --out bench/2026-09-26/W-2-1514-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-2-1514-H :: HN ; PWS bench/2026-09-26/W-2-1513-H.log ; DW bench/2026-09-26/W-2-1513-H.log
CAP --out bench/2026-09-26/W-9-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/W-9-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/W-9-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/W-2-1514-H.log
CAP --out bench/2026-09-26/W-9-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/W-9-H :: HN ; PWS bench/2026-09-26/W-2-1514-H.log ; DW bench/2026-09-26/W-9-L.log
```

### The mechanism maps and the history cells

```
CAP --out bench/2026-09-26/M-00-DN --send 'ifconfig rlx0 down ; echo irqon > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/M-00-K --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-mlen-V --send 'echo txlen mlen > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-mlen-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-mlen-C :: SWC bench/2026-09-26/M-mlen-S.log --setting mlen --probe 60
CAP --out bench/2026-09-26/M-mlen-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-mlen-H :: HN ; PWS bench/2026-09-26/W-9-H.log ; DW bench/2026-09-26/W-9-H.log
CAP --out bench/2026-09-26/M-ext-V --send 'echo txlen ext > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-ext-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-ext-C :: SWC bench/2026-09-26/M-ext-S.log --setting ext --probe 60
CAP --out bench/2026-09-26/M-ext-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-ext-H :: HN ; PWS bench/2026-09-26/M-mlen-H.log ; DW bench/2026-09-26/M-mlen-H.log
CAP --out bench/2026-09-26/M-d1-V --send 'echo txlen d1 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-d1-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-d1-C :: SWC bench/2026-09-26/M-d1-S.log --setting d1 --probe 60
CAP --out bench/2026-09-26/M-d1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-d1-H :: HN ; PWS bench/2026-09-26/M-ext-H.log ; DW bench/2026-09-26/M-ext-H.log
CAP --out bench/2026-09-26/M-d2-V --send 'echo txlen d2 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-d2-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-d2-C :: SWC bench/2026-09-26/M-d2-S.log --setting d2 --probe 60
CAP --out bench/2026-09-26/M-d2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-d2-H :: HN ; PWS bench/2026-09-26/M-d1-H.log ; DW bench/2026-09-26/M-d1-H.log
CAP --out bench/2026-09-26/M-d3-V --send 'echo txlen d3 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-d3-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-d3-C :: SWC bench/2026-09-26/M-d3-S.log --setting d3 --probe 60
CAP --out bench/2026-09-26/M-d3-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-d3-H :: HN ; PWS bench/2026-09-26/M-d2-H.log ; DW bench/2026-09-26/M-d2-H.log
CAP --out bench/2026-09-26/M-off0-V --send 'echo txlen rlxfw > /proc/rtl819x-nic ; echo txoff 0 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-off0-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-off0-C :: SWC bench/2026-09-26/M-off0-S.log --setting txoff0 --probe 60
CAP --out bench/2026-09-26/M-off0-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-off0-H :: HN ; PWS bench/2026-09-26/M-d3-H.log ; DW bench/2026-09-26/M-d3-H.log
CAP --out bench/2026-09-26/M-rb1-V --send 'echo txoff 2 > /proc/rtl819x-nic ; echo txrb 1 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-rb1-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-rb1-C :: SWC bench/2026-09-26/M-rb1-S.log --setting rlxfw --probe 60
CAP --out bench/2026-09-26/M-rb1-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-rb1-H :: HN ; PWS bench/2026-09-26/M-off0-H.log ; DW bench/2026-09-26/M-off0-H.log
CAP --out bench/2026-09-26/M-rb2-V --send 'echo txrb 2 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-rb2-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-rb2-C :: SWC bench/2026-09-26/M-rb2-S.log --setting rlxfw --probe 60
CAP --out bench/2026-09-26/M-rb2-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-rb2-H :: HN ; PWS bench/2026-09-26/M-rb1-H.log ; DW bench/2026-09-26/M-rb1-H.log
CAP --out bench/2026-09-26/M-rb4-V --send 'echo txrb 4 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-rb4-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-rb4-C :: SWC bench/2026-09-26/M-rb4-S.log --setting rlxfw --probe 60
CAP --out bench/2026-09-26/M-rb4-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-rb4-H :: HN ; PWS bench/2026-09-26/M-rb2-H.log ; DW bench/2026-09-26/M-rb2-H.log
CAP --out bench/2026-09-26/M-rb8-V --send 'echo txrb 8 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/M-rb8-S --send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 180
HOST bench/2026-09-26/M-rb8-C :: SWC bench/2026-09-26/M-rb8-S.log --setting rlxfw --probe 60
CAP --out bench/2026-09-26/M-rb8-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-rb8-H :: HN ; PWS bench/2026-09-26/M-rb4-H.log ; DW bench/2026-09-26/M-rb4-H.log
CAP --out bench/2026-09-26/HI-00-V --send 'echo txrb 0 > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' --until 'ww [0-9]+(?: \S+){8}\r\n# |Booting\.\.\.|---RealTek' --seconds 10
CAP --out bench/2026-09-26/HI-00-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/HI-00-H :: HN ; PWS bench/2026-09-26/M-rb8-H.log ; DW bench/2026-09-26/M-rb8-H.log
CAP --out bench/2026-09-26/HI-1-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-1-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-1-B --send 'echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-1-R --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/HI-1-C :: RBC hist bench/2026-09-26/HI-1-R.log --seq 60,61,61,60
CAP --out bench/2026-09-26/HI-2-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-2-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 47 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-2-B --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-2-R --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/HI-2-C :: RBC hist bench/2026-09-26/HI-2-R.log --seq 61,60,60,60
CAP --out bench/2026-09-26/HI-3-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-3-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-3-B --send 'echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-3-R --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/HI-3-C :: RBC hist bench/2026-09-26/HI-3-R.log --seq 60,1511,1511,60
CAP --out bench/2026-09-26/HI-4-X --send 'echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; echo engine on > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-4-A --send 'echo lb on > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 1497 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-4-B --send 'echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic ; echo tx 0x3f 0x8800 0 46 > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/HI-4-R --send 'cat /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 10
HOST bench/2026-09-26/HI-4-C :: RBC hist bench/2026-09-26/HI-4-R.log --seq 1511,60,60,60
CAP --out bench/2026-09-26/HI-9-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/HI-9-H :: HN ; PWS bench/2026-09-26/HI-00-H.log ; DW bench/2026-09-26/HI-00-H.log
CAP --out bench/2026-09-26/M-9-X --send 'echo lb off > /proc/rtl819x-nic ; echo engine off > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic' --idle 3 --seconds 12
CAP --out bench/2026-09-26/M-9-UP --send 'ifconfig rlx0 10.1.1.3 up' --idle 3 --seconds 12
CAP --out bench/2026-09-26/M-9-LS --send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status' --idle 3 --seconds 12
HOST bench/2026-09-26/M-9-L :: FL 10.1.1.3 ; PL ; DW bench/2026-09-26/HI-9-H.log
CAP --out bench/2026-09-26/M-9-R --send 'sleep 2 ; cat /proc/rtl819x-nic /proc/net/snmp /proc/net/arp /proc/rtl865x/asicCounter /proc/rtl819x-nic' --until 'rx_ph4 [0-9A-F]{8}(?:\r\n)+# |Booting\.\.\.|---RealTek' --seconds 15
HOST bench/2026-09-26/M-9-H :: HN ; PWS bench/2026-09-26/HI-9-H.log ; DW bench/2026-09-26/M-9-L.log
```

### The sweeps' capture stopped

```
HOST bench/2026-09-26/W-TCPSX :: sudo -n pkill -INT -x tcpdump && sleep 1
HOST bench/2026-09-26/W-SWALL :: PWS none
```

### The closing map, `n_writes`, the kernel log

```
CAP --out bench/2026-09-26/R1-M1 --send 'echo map 0 > /proc/rtl819x-spi ; cat /proc/rtl819x-spi-map' --until 'map_lines [0-9]+\r\n# ' --seconds 180
HOST bench/2026-09-26/R1-MB1 :: MB bench/2026-09-26/R1-M1
CAP --out bench/2026-09-26/R1-NW1 --send 'cat /proc/rtl819x-spi' --idle 3 --seconds 15
HOST bench/2026-09-26/Z-DW :: DW bench/2026-09-26/M-9-H.log
HOST bench/2026-09-26/Z-DWALL :: DW none
```

---

## § 6 How the cells are run

**Before any cell** (none of it a cell), in this order: (1) no other WSL job is running — no
`R6b-6` build, no desk sweep, nothing started from WSL — because (2) kills every WSL process;
(2) `wsl --shutdown` from PowerShell, then the keeper `wsl -d Ubuntu-24.04 -- sleep 36000` in
the background; (3) the kernel-log follower, from PowerShell in the background: `wsl -d
Ubuntu-24.04 -- bash -c "mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/host && exec dmesg -w
> /home/key/fwre-work/rebuild/s112/r6b3/host/dmesg-w.log"` — started before the attach, so
the attach itself is in the log; (4) `usbipd list`, read fresh, then `usbipd attach` of the
CP2102 and of the GbE adapter, reading what each prints; (5) in WSL, from the repository root:
`mkdir -p /home/key/fwre-work/rebuild/s112/r6b3/run`; `/usr/bin/python3 tools/cardcheck.py
numbers` on this card, every row re-derived; `/usr/bin/python3 tools/check-predictions.py` on
this card, reading **`0 of 445 captures came after the prediction, 445 did
not`**; every invocation once through `runblock.py … --dry`, each ending `ALL ITEMS DONE`.
**The catch window opens no later than 23:00 on 2026-09-26**; later, the card is re-dated
before power.

**Each invocation** runs from the repository root in WSL as
`/usr/bin/python3 /home/key/fwre-work/rebuild/s109/card/runblock.py CARD NAME --log LOG`, with
LOG `/home/key/fwre-work/rebuild/s112/r6b3/run/run-NAME.log`, in the order `I-0`, `I-1`,
`I-RB`, `I-RQ` (only after a VOID, as below), `I-VC`, `I-WE0` (in the background; its
transcript read for `BG  W-TCPE … start seen` before `I-E` starts), `I-E`, `I-WE9`, `I-WS0` (the same, `W-TCPS`), `I-LB`, `I-W`, `I-M`,
`I-WS9`, `I-Z`. `NAME?` marks a cell whose non-zero exit is a reading; `gate:` items are the
decision points; any failed cell or gate stops its own invocation and interrupts its own
background cells, never another invocation's.

**The owner's power**: `I-1` starts with its catch; the owner is told when it opens and
presses inside its 180 s window, and powers off after `I-Z`, or at once where a stop below
says so.

**`I-0`** — before power: the pre-flight, the address, the adapter, no capture, one kernel-log follower and a clean log, the flush, the capture directory, the checkers' digests and self-tests, the verb check

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
R0-SUM
gate:grep=^036971a201c1d74bb5411daf61e623ae8c5e2b8140f78847b4871b0c457e6ee7  -$:R0-SUM
gate:grep=^80ce6799e5a454e3dd7dbec70fb45bf7ffad119f41f8b6b5c14bca37e4531854  -$:R0-SUM
gate:grep=^e36bd29e4714408ac50d2fe7dd90dde71cb88be5c6007ec22277a0ef0082c890  -$:R0-SUM
gate:grep=^3866b96cbf50007b9176a23bcc709dcce8ef8d046b44ddc0337b08a615500595  -$:R0-SUM
gate:grep=^04c1a5492467fd5c0a4963df0624d95b07a5d9b7616a45e243cf154576a1a4e9  -$:R0-SUM
gate:grep=^7f7dad0b02e5616943f536e6cdc31c42692a8b1f5de67d2ce0422e7b2728bafe  -$:R0-SUM
gate:grep=^34557e8b239d8639271cbaeadc56e9128610f390b653602f74b5957a8f5c4a65  -$:R0-SUM
gate:grep=^4069cd42f6f8334ed6e1bd5ae8fe44c87333d2a092da27b88f77c9c54f277b90  -$:R0-SUM
R0-ST
gate:grep=^pcapwin\ self\-test:\ 19\ of\ 19\ passed$:R0-ST
gate:grep=^rbcheck\ self\-test:\ 52\ of\ 52\ passed$:R0-ST
gate:grep=^swcheck\ self\-test:\ 12\ of\ 12\ passed$:R0-ST
gate:grep=^dmesgwin\ self\-test:\ 6\ of\ 6\ passed$:R0-ST
gate:grep=^brdelta\ self\-test:\ 18\ of\ 18\ passed$:R0-ST
R0-VERB
gate:grep=^verbcheck verdict PASS$:R0-VERB
gate:grep=^verbcheck\ self\-test:\ 9\ of\ 9\ passed$:R0-VERB
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

**`I-RB`** — the read-back, first: at the default settings, do the TX descriptors hold 1.4's words? (the owner's ruling of 2026-09-26: a DIFFER ends the A/B; a VOID is decided in § 6)

```run
RB-00-R
gate:until:RB-00-R
gate:grep=^version rtl819x-nic 1\.5$:RB-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:RB-00-R
gate:grep=^nd_up 1$:RB-00-R
RB-00-H?
RB-00-T
gate:until:RB-00-T
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-00-T
gate:grep=^version rtl819x-nic 1\.5$:RB-00-T
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:RB-00-T
gate:grep=^v15 last - 0 ok 0 refused 0 txq \d+ arm15 0$:RB-00-T
gate:grep=^sw never mode loop from 0 to 0 probe 0 rc 0 bufs 00000000$:RB-00-T
gate:grep=^sw key txlen rlxfw txoff 0 txrb 0 mode loop probe 0 rings 0 rec 0$:RB-00-T
gate:grep=^mt none 1455 clean 0 bad_b 0 bad_a 0 void 0 skew 0$:RB-00-T
RB-01-DN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-DN
RB-01-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-X
RB-01-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-S
RB-01-T
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-T
RB-01-R
gate:until:RB-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-R
gate:grep=^version rtl819x-nic 1\.5$:RB-01-R
RB-01-C
gate:grep=^rbcheck verdict EQUAL$:RB-01-C
RB-01-X2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-X2
RB-01-UP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-01-UP
RB-02-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-02-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:RB-02-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:RB-02-LS
RB-02-L
gate:grep=^4 packets transmitted, 4 received:RB-02-L
gate:grep=^follower 1$:RB-02-L
RB-02-S
gate:until:RB-02-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-02-S
gate:grep=^version rtl819x-nic 1\.5$:RB-02-S
gate:grep=^nd_up 1$:RB-02-S
RB-02-P?
RB-02-R
gate:until:RB-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-02-R
gate:grep=^version rtl819x-nic 1\.5$:RB-02-R
RB-02-C
gate:grep=^rbcheck verdict EQUAL$:RB-02-C
RB-02-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-02-X
RB-02-L2
gate:grep=^4 packets transmitted, 4 received:RB-02-L2
gate:grep=^follower 1$:RB-02-L2
RB-09-R
gate:until:RB-09-R
gate:grep=^version rtl819x-nic 1\.5$:RB-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RB-09-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:RB-09-R
gate:grep=^nd_up 1$:RB-09-R
RB-09-H?
RB-09-D?
```

**`I-RQ`** — **only after a VOID of the read-back** (§ 6; never after two EQUALs or a DIFFER): the fallback the owner asked for, Q at `txrb 1` -- a queue-time reading at a non-default setting, not the default-settings read-back (P1b) -- then the board back at 1.4's defaults

```run
RQ-00-R
gate:until:RQ-00-R
gate:grep=^version rtl819x-nic 1\.5$:RQ-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-00-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:RQ-00-R
gate:grep=^nd_up 1$:RQ-00-R
RQ-00-H?
RQ-01-V
gate:until:RQ-01-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-V
gate:grep=^v15 last txrb 7 :RQ-01-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 1 dirty 1 p15 1$:RQ-01-V
RQ-01-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-X
RQ-01-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-S
RQ-01-T
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-T
RQ-01-R
gate:until:RQ-01-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-R
gate:grep=^version rtl819x-nic 1\.5$:RQ-01-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 1 dirty 0 p15 1$:RQ-01-R
RQ-01-C
gate:grep=^rbcheck verdict EQUAL$:RQ-01-C
RQ-01-F?
RQ-01-X2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-X2
RQ-01-UP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-01-UP
RQ-02-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-02-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:RQ-02-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:RQ-02-LS
RQ-02-L
gate:grep=^4 packets transmitted, 4 received:RQ-02-L
gate:grep=^follower 1$:RQ-02-L
RQ-02-S
gate:until:RQ-02-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-02-S
gate:grep=^version rtl819x-nic 1\.5$:RQ-02-S
gate:grep=^nd_up 1$:RQ-02-S
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 1 dirty 0 p15 1$:RQ-02-S
RQ-02-P?
RQ-02-R
gate:until:RQ-02-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-02-R
gate:grep=^version rtl819x-nic 1\.5$:RQ-02-R
RQ-02-C
gate:grep=^rbcheck verdict EQUAL$:RQ-02-C
RQ-02-F?
RQ-09-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-09-SW
RQ-09-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-09-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:RQ-09-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:RQ-09-LS
RQ-09-L
gate:grep=^4 packets transmitted, 4 received:RQ-09-L
gate:grep=^follower 1$:RQ-09-L
RQ-09-R
gate:until:RQ-09-R
gate:grep=^version rtl819x-nic 1\.5$:RQ-09-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):RQ-09-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:RQ-09-R
gate:grep=^nd_up 1$:RQ-09-R
RQ-09-H?
RQ-09-D?
```

**`I-VC`** — the guards the card rests on, each shown refusing and permitting, and one policy switch through them

```run
VC-01
gate:until:VC-01
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-01
gate:grep=^v15 last txlen -16 :VC-01
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:VC-01
VC-02
gate:until:VC-02
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-02
gate:grep=^v15 last sweep -16 :VC-02
gate:grep=^sw never :VC-02
VC-03
gate:until:VC-03
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-03
gate:grep=^v15 last sweep -22 :VC-03
gate:grep=^sw never :VC-03
VC-04
gate:until:VC-04
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-04
gate:grep=^v15 last txlen 13 :VC-04
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 1 p15 1$:VC-04
VC-05
gate:until:VC-05
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-05
gate:grep=^v15 last engine -151 :VC-05
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 1 p15 1$:VC-05
VC-06
gate:until:VC-06
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-06
gate:grep=^version rtl819x-nic 1\.5$:VC-06
gate:grep=^nd_up 0$:VC-06
gate:grep=^v15 last engine -151 :VC-06
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 1 p15 1$:VC-06
VC-07
gate:until:VC-07
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-07
gate:grep=^version rtl819x-nic 1\.5$:VC-07
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:VC-07
VC-07-C?
VC-08
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-08
VC-08-R
gate:until:VC-08-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-08-R
gate:grep=^version rtl819x-nic 1\.5$:VC-08-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:VC-08-R
gate:grep=^nd_up 1$:VC-08-R
gate:grep=^v15 last txlen 12 :VC-08-R
VC-09-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-09-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:VC-09-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:VC-09-LS
VC-09-L
gate:grep=^4 packets transmitted, 4 received:VC-09-L
gate:grep=^follower 1$:VC-09-L
```

**`I-WE0`** — the stack arms' host capture (the board's source address, 64 B), in the background until `I-WE9`

```run
W-TCPE
```

**`I-E`** — the stack A/B: E2's eleven lengths at block 45's spacing, the fix, then 1.4, then the fix again

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
E-F1-R0
gate:until:E-F1-R0
gate:grep=^version rtl819x-nic 1\.5$:E-F1-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F1-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F1-R0
gate:grep=^nd_up 1$:E-F1-R0
E-F1-H0?
E-F1-E2?
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
E-L1-R0
gate:until:E-L1-R0
gate:grep=^version rtl819x-nic 1\.5$:E-L1-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-L1-R0
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:E-L1-R0
gate:grep=^nd_up 1$:E-L1-R0
E-L1-H0?
E-L1-E2?
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
E-F2-R0
gate:until:E-F2-R0
gate:grep=^version rtl819x-nic 1\.5$:E-F2-R0
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):E-F2-R0
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:E-F2-R0
gate:grep=^nd_up 1$:E-F2-R0
E-F2-H0?
E-F2-E2?
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

**`I-WE9`** — the stack arms' capture stopped and summed

```run
W-TCPEX?
W-EWALL?
```

**`I-WS0`** — the sweeps' host capture (the board's source address and 0x88B5, tagged or not, 64 B), in the background until `I-WS9`

```run
W-TCPS
```

**`I-LB`** — loopback: the sweep's positive control at 1.4's settings and its containment gate, the record-key guard, NET-61's runs at 1.4 and at the fix, the carry-over cells, the full 1.4 map, the fix's full map

```run
S-LIVE
gate:grep=\A1\n\Z:S-LIVE
LB-00-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-00-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:LB-00-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:LB-00-LS
LB-00-L
gate:grep=^4 packets transmitted, 4 received:LB-00-L
gate:grep=^follower 1$:LB-00-L
LB-00-R
gate:until:LB-00-R
gate:grep=^version rtl819x-nic 1\.5$:LB-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-00-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:LB-00-R
gate:grep=^nd_up 1$:LB-00-R
LB-00-H?
LB-00-DN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-00-DN
LB-00-K
gate:until:LB-00-K
gate:grep=^version rtl819x-nic 1\.5$:LB-00-K
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-00-K
gate:grep=^nd_up 0$:LB-00-K
gate:grep=^irq_taken 1$:LB-00-K
gate:grep=^engine_on 0$:LB-00-K
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 1 p15 1$:LB-00-K
LB-00-R2
gate:until:LB-00-R2
gate:grep=^version rtl819x-nic 1\.5$:LB-00-R2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-00-R2
gate:grep=^nd_up 0$:LB-00-R2
LB-00-H2?
LB-1-0060
gate:until:LB-1-0060
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0060
gate:grep=^v15 last sweep (?:14|-71|-61|-145|-4) :LB-1-0060
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 60 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0060
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0060
LB-1-0061
gate:until:LB-1-0061
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0061
gate:grep=^v15 last sweep (?:14|-71|-61|-145|-4) :LB-1-0061
gate:grep=^sw (?:done|fail|intr) mode loop from 61 to 61 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0061
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0061
LB-1-0062
gate:until:LB-1-0062
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0062
gate:grep=^v15 last sweep (?:14|-71|-61|-145|-4) :LB-1-0062
gate:grep=^sw (?:done|fail|intr) mode loop from 62 to 62 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0062
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0062
LB-1-0063
gate:until:LB-1-0063
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0063
gate:grep=^v15 last sweep (?:14|-71|-61|-145|-4) :LB-1-0063
gate:grep=^sw (?:done|fail|intr) mode loop from 63 to 63 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0063
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0063
LB-1-0263
gate:until:LB-1-0263
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0263
gate:grep=^v15 last sweep (?:16|-71|-61|-145|-4) :LB-1-0263
gate:grep=^sw (?:done|fail|intr) mode loop from 263 to 263 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0263
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0263
LB-1-0276
gate:until:LB-1-0276
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0276
gate:grep=^v15 last sweep (?:16|-71|-61|-145|-4) :LB-1-0276
gate:grep=^sw (?:done|fail|intr) mode loop from 276 to 276 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0276
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0276
LB-1-0277
gate:until:LB-1-0277
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-0277
gate:grep=^v15 last sweep (?:16|-71|-61|-145|-4) :LB-1-0277
gate:grep=^sw (?:done|fail|intr) mode loop from 277 to 277 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-0277
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-0277
LB-1-1511
gate:until:LB-1-1511
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-1511
gate:grep=^v15 last sweep (?:18|-71|-61|-145|-4) :LB-1-1511
gate:grep=^sw (?:done|fail|intr) mode loop from 1511 to 1511 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-1511
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-1511
LB-1-1512
gate:until:LB-1-1512
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-1512
gate:grep=^v15 last sweep (?:18|-71|-61|-145|-4) :LB-1-1512
gate:grep=^sw (?:done|fail|intr) mode loop from 1512 to 1512 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-1512
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-1512
LB-1-1513
gate:until:LB-1-1513
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-1513
gate:grep=^v15 last sweep (?:18|-71|-61|-145|-4) :LB-1-1513
gate:grep=^sw (?:done|fail|intr) mode loop from 1513 to 1513 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-1513
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-1513
LB-1-1514
gate:until:LB-1-1514
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-1514
gate:grep=^v15 last sweep (?:18|-71|-61|-145|-4) :LB-1-1514
gate:grep=^sw (?:done|fail|intr) mode loop from 1514 to 1514 probe 0 rc -?\d+ bufs [0-9A-F]{8}$:LB-1-1514
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:LB-1-1514
LB-1-R
gate:until:LB-1-R
gate:grep=^version rtl819x-nic 1\.5$:LB-1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-1-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:LB-1-R
gate:grep=^nd_up 0$:LB-1-R
LB-1-H?
LB-1-G
gate:grep=^leak none$:LB-1-G
VC-EE
gate:until:VC-EE
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):VC-EE
gate:grep=^v15 last sweep -17 :VC-EE
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec \d+$:VC-EE
SW-CLR
gate:until:SW-CLR
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):SW-CLR
gate:grep=^v15 last swclear 8 :SW-CLR
gate:grep=^mt none 1455 clean 0 bad_b 0 bad_a 0 void 0 skew 0$:SW-CLR
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 0 rings \d+ rec 0$:SW-CLR
DS-r-00
gate:until:DS-r-00
gate:grep=^version rtl819x-nic 1\.5$:DS-r-00
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-00
gate:grep=^nd_up 1$:DS-r-00
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:DS-r-00
DS-r-0060-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0060-X
DS-r-0060-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0060-A
DS-r-0060-B
gate:until:DS-r-0060-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0060-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0060-B
DS-r-0061-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0061-X
DS-r-0061-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0061-A
DS-r-0061-B
gate:until:DS-r-0061-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0061-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0061-B
DS-r-0062-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0062-X
DS-r-0062-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0062-A
DS-r-0062-B
gate:until:DS-r-0062-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0062-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0062-B
DS-r-0063-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0063-X
DS-r-0063-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0063-A
DS-r-0063-B
gate:until:DS-r-0063-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0063-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0063-B
DS-r-0263-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0263-X
DS-r-0263-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0263-A
DS-r-0263-B
gate:until:DS-r-0263-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0263-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0263-B
DS-r-0276-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0276-X
DS-r-0276-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0276-A
DS-r-0276-B
gate:until:DS-r-0276-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0276-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0276-B
DS-r-0277-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0277-X
DS-r-0277-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0277-A
DS-r-0277-B
gate:until:DS-r-0277-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-0277-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-0277-B
DS-r-1511-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1511-X
DS-r-1511-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1511-A
DS-r-1511-B
gate:until:DS-r-1511-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-1511-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1511-B
DS-r-1512-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1512-X
DS-r-1512-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1512-A
DS-r-1512-B
gate:until:DS-r-1512-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-1512-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1512-B
DS-r-1513-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1513-X
DS-r-1513-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1513-A
DS-r-1513-B
gate:until:DS-r-1513-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-1513-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1513-B
DS-r-1514-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1514-X
DS-r-1514-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1514-A
DS-r-1514-B
gate:until:DS-r-1514-B
gate:grep=^version rtl819x-nic 1\.5$:DS-r-1514-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-r-1514-B
DS-r-C?
DS-v-SW
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-SW
DS-v-00
gate:until:DS-v-00
gate:grep=^version rtl819x-nic 1\.5$:DS-v-00
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-00
gate:grep=^nd_up 1$:DS-v-00
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:DS-v-00
DS-v-0060-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0060-X
DS-v-0060-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0060-A
DS-v-0060-B
gate:until:DS-v-0060-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0060-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0060-B
DS-v-0061-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0061-X
DS-v-0061-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0061-A
DS-v-0061-B
gate:until:DS-v-0061-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0061-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0061-B
DS-v-0062-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0062-X
DS-v-0062-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0062-A
DS-v-0062-B
gate:until:DS-v-0062-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0062-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0062-B
DS-v-0063-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0063-X
DS-v-0063-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0063-A
DS-v-0063-B
gate:until:DS-v-0063-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0063-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0063-B
DS-v-0263-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0263-X
DS-v-0263-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0263-A
DS-v-0263-B
gate:until:DS-v-0263-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0263-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0263-B
DS-v-0276-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0276-X
DS-v-0276-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0276-A
DS-v-0276-B
gate:until:DS-v-0276-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0276-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0276-B
DS-v-0277-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0277-X
DS-v-0277-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0277-A
DS-v-0277-B
gate:until:DS-v-0277-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-0277-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-0277-B
DS-v-1511-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1511-X
DS-v-1511-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1511-A
DS-v-1511-B
gate:until:DS-v-1511-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-1511-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1511-B
DS-v-1512-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1512-X
DS-v-1512-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1512-A
DS-v-1512-B
gate:until:DS-v-1512-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-1512-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1512-B
DS-v-1513-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1513-X
DS-v-1513-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1513-A
DS-v-1513-B
gate:until:DS-v-1513-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-1513-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1513-B
DS-v-1514-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1514-X
DS-v-1514-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1514-A
DS-v-1514-B
gate:until:DS-v-1514-B
gate:grep=^version rtl819x-nic 1\.5$:DS-v-1514-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-v-1514-B
DS-v-C?
DS-9-R
gate:until:DS-9-R
gate:grep=^version rtl819x-nic 1\.5$:DS-9-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-9-R
gate:grep=^tx15 txlen vendor txoff 2 txrb 0 dirty 0 p15 1$:DS-9-R
gate:grep=^nd_up 1$:DS-9-R
DS-9-H?
DS-9-D?
DS-9-DN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-9-DN
DS-9-K
gate:until:DS-9-K
gate:grep=^version rtl819x-nic 1\.5$:DS-9-K
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):DS-9-K
gate:grep=^nd_up 0$:DS-9-K
gate:grep=^irq_taken 1$:DS-9-K
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 1 p15 1$:DS-9-K
CO-1
gate:until:CO-1
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):CO-1
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :CO-1
gate:grep=^sw (?:done|fail|intr) mode loop from 61 to 61 probe 1514 rc -?\d+ bufs [0-9A-F]{8}$:CO-1
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 1514 rings \d+ rec \d+$:CO-1
CO-2
gate:until:CO-2
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):CO-2
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :CO-2
gate:grep=^sw (?:done|fail|intr) mode loop from 277 to 277 probe 61 rc -?\d+ bufs [0-9A-F]{8}$:CO-2
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 61 rings \d+ rec \d+$:CO-2
LB-2-S
gate:until:LB-2-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-2-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :LB-2-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:LB-2-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:LB-2-S
LB-2-C?
LB-2-R
gate:until:LB-2-R
gate:grep=^version rtl819x-nic 1\.5$:LB-2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-2-R
gate:grep=^nd_up 0$:LB-2-R
LB-2-H?
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
LB-V-R
gate:until:LB-V-R
gate:grep=^version rtl819x-nic 1\.5$:LB-V-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):LB-V-R
gate:grep=^nd_up 0$:LB-V-R
LB-V-H?
LB-V-D?
```

**`I-W`** — the wire: the containment gate, the fix over every length in four brackets, the owner's bound refusing, then 1.4 at 35 lengths, one bracket each

```run
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
gate:grep=^sw key txlen vendor txoff 2 txrb 0 mode (?:loop|wire) probe 60 rings \d+ rec \d+$:W-2-EP
W-2-0060-S
gate:until:W-2-0060-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0060-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0060-S
gate:grep=^sw (?:done|fail|intr) mode wire from 60 to 60 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0060-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0060-S
W-2-0060-R
gate:until:W-2-0060-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0060-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0060-R
gate:grep=^nd_up 0$:W-2-0060-R
W-2-0060-H?
W-2-0061-S
gate:until:W-2-0061-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0061-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0061-S
gate:grep=^sw (?:done|fail|intr) mode wire from 61 to 61 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0061-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0061-S
W-2-0061-R
gate:until:W-2-0061-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0061-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0061-R
gate:grep=^nd_up 0$:W-2-0061-R
W-2-0061-H?
W-2-0062-S
gate:until:W-2-0062-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0062-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0062-S
gate:grep=^sw (?:done|fail|intr) mode wire from 62 to 62 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0062-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0062-S
W-2-0062-R
gate:until:W-2-0062-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0062-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0062-R
gate:grep=^nd_up 0$:W-2-0062-R
W-2-0062-H?
W-2-0063-S
gate:until:W-2-0063-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0063-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0063-S
gate:grep=^sw (?:done|fail|intr) mode wire from 63 to 63 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0063-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0063-S
W-2-0063-R
gate:until:W-2-0063-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0063-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0063-R
gate:grep=^nd_up 0$:W-2-0063-R
W-2-0063-H?
W-2-0064-S
gate:until:W-2-0064-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0064-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0064-S
gate:grep=^sw (?:done|fail|intr) mode wire from 64 to 64 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0064-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0064-S
W-2-0064-R
gate:until:W-2-0064-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0064-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0064-R
gate:grep=^nd_up 0$:W-2-0064-R
W-2-0064-H?
W-2-0065-S
gate:until:W-2-0065-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0065-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0065-S
gate:grep=^sw (?:done|fail|intr) mode wire from 65 to 65 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0065-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0065-S
W-2-0065-R
gate:until:W-2-0065-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0065-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0065-R
gate:grep=^nd_up 0$:W-2-0065-R
W-2-0065-H?
W-2-0066-S
gate:until:W-2-0066-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0066-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0066-S
gate:grep=^sw (?:done|fail|intr) mode wire from 66 to 66 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0066-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0066-S
W-2-0066-R
gate:until:W-2-0066-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0066-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0066-R
gate:grep=^nd_up 0$:W-2-0066-R
W-2-0066-H?
W-2-0067-S
gate:until:W-2-0067-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0067-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0067-S
gate:grep=^sw (?:done|fail|intr) mode wire from 67 to 67 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0067-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0067-S
W-2-0067-R
gate:until:W-2-0067-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0067-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0067-R
gate:grep=^nd_up 0$:W-2-0067-R
W-2-0067-H?
W-2-0068-S
gate:until:W-2-0068-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0068-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0068-S
gate:grep=^sw (?:done|fail|intr) mode wire from 68 to 68 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0068-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0068-S
W-2-0068-R
gate:until:W-2-0068-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0068-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0068-R
gate:grep=^nd_up 0$:W-2-0068-R
W-2-0068-H?
W-2-0069-S
gate:until:W-2-0069-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0069-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0069-S
gate:grep=^sw (?:done|fail|intr) mode wire from 69 to 69 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0069-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0069-S
W-2-0069-R
gate:until:W-2-0069-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0069-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0069-R
gate:grep=^nd_up 0$:W-2-0069-R
W-2-0069-H?
W-2-0070-S
gate:until:W-2-0070-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0070-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0070-S
gate:grep=^sw (?:done|fail|intr) mode wire from 70 to 70 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0070-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0070-S
W-2-0070-R
gate:until:W-2-0070-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0070-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0070-R
gate:grep=^nd_up 0$:W-2-0070-R
W-2-0070-H?
W-2-0071-S
gate:until:W-2-0071-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0071-S
gate:grep=^v15 last sweep (?:20|-71|-61|-145|-4) :W-2-0071-S
gate:grep=^sw (?:done|fail|intr) mode wire from 71 to 71 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0071-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0071-S
W-2-0071-R
gate:until:W-2-0071-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0071-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0071-R
gate:grep=^nd_up 0$:W-2-0071-R
W-2-0071-H?
W-2-0263-S
gate:until:W-2-0263-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0263-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0263-S
gate:grep=^sw (?:done|fail|intr) mode wire from 263 to 263 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0263-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0263-S
W-2-0263-R
gate:until:W-2-0263-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0263-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0263-R
gate:grep=^nd_up 0$:W-2-0263-R
W-2-0263-H?
W-2-0276-S
gate:until:W-2-0276-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0276-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0276-S
gate:grep=^sw (?:done|fail|intr) mode wire from 276 to 276 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0276-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0276-S
W-2-0276-R
gate:until:W-2-0276-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0276-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0276-R
gate:grep=^nd_up 0$:W-2-0276-R
W-2-0276-H?
W-2-0277-S
gate:until:W-2-0277-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0277-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0277-S
gate:grep=^sw (?:done|fail|intr) mode wire from 277 to 277 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0277-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0277-S
W-2-0277-R
gate:until:W-2-0277-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0277-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0277-R
gate:grep=^nd_up 0$:W-2-0277-R
W-2-0277-H?
W-2-0768-S
gate:until:W-2-0768-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0768-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0768-S
gate:grep=^sw (?:done|fail|intr) mode wire from 768 to 768 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0768-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0768-S
W-2-0768-R
gate:until:W-2-0768-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0768-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0768-R
gate:grep=^nd_up 0$:W-2-0768-R
W-2-0768-H?
W-2-0769-S
gate:until:W-2-0769-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0769-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0769-S
gate:grep=^sw (?:done|fail|intr) mode wire from 769 to 769 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0769-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0769-S
W-2-0769-R
gate:until:W-2-0769-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0769-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0769-R
gate:grep=^nd_up 0$:W-2-0769-R
W-2-0769-H?
W-2-0770-S
gate:until:W-2-0770-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0770-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0770-S
gate:grep=^sw (?:done|fail|intr) mode wire from 770 to 770 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0770-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0770-S
W-2-0770-R
gate:until:W-2-0770-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0770-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0770-R
gate:grep=^nd_up 0$:W-2-0770-R
W-2-0770-H?
W-2-0771-S
gate:until:W-2-0771-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0771-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0771-S
gate:grep=^sw (?:done|fail|intr) mode wire from 771 to 771 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0771-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0771-S
W-2-0771-R
gate:until:W-2-0771-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0771-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0771-R
gate:grep=^nd_up 0$:W-2-0771-R
W-2-0771-H?
W-2-0772-S
gate:until:W-2-0772-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0772-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0772-S
gate:grep=^sw (?:done|fail|intr) mode wire from 772 to 772 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0772-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0772-S
W-2-0772-R
gate:until:W-2-0772-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0772-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0772-R
gate:grep=^nd_up 0$:W-2-0772-R
W-2-0772-H?
W-2-0773-S
gate:until:W-2-0773-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0773-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0773-S
gate:grep=^sw (?:done|fail|intr) mode wire from 773 to 773 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0773-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0773-S
W-2-0773-R
gate:until:W-2-0773-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0773-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0773-R
gate:grep=^nd_up 0$:W-2-0773-R
W-2-0773-H?
W-2-0774-S
gate:until:W-2-0774-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0774-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0774-S
gate:grep=^sw (?:done|fail|intr) mode wire from 774 to 774 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0774-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0774-S
W-2-0774-R
gate:until:W-2-0774-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0774-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0774-R
gate:grep=^nd_up 0$:W-2-0774-R
W-2-0774-H?
W-2-0775-S
gate:until:W-2-0775-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0775-S
gate:grep=^v15 last sweep (?:22|-71|-61|-145|-4) :W-2-0775-S
gate:grep=^sw (?:done|fail|intr) mode wire from 775 to 775 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-0775-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-0775-S
W-2-0775-R
gate:until:W-2-0775-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-0775-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-0775-R
gate:grep=^nd_up 0$:W-2-0775-R
W-2-0775-H?
W-2-1496-S
gate:until:W-2-1496-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1496-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1496-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1496 to 1496 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1496-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1496-S
W-2-1496-R
gate:until:W-2-1496-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1496-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1496-R
gate:grep=^nd_up 0$:W-2-1496-R
W-2-1496-H?
W-2-1497-S
gate:until:W-2-1497-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1497-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1497-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1497 to 1497 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1497-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1497-S
W-2-1497-R
gate:until:W-2-1497-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1497-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1497-R
gate:grep=^nd_up 0$:W-2-1497-R
W-2-1497-H?
W-2-1498-S
gate:until:W-2-1498-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1498-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1498-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1498 to 1498 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1498-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1498-S
W-2-1498-R
gate:until:W-2-1498-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1498-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1498-R
gate:grep=^nd_up 0$:W-2-1498-R
W-2-1498-H?
W-2-1499-S
gate:until:W-2-1499-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1499-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1499-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1499 to 1499 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1499-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1499-S
W-2-1499-R
gate:until:W-2-1499-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1499-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1499-R
gate:grep=^nd_up 0$:W-2-1499-R
W-2-1499-H?
W-2-1500-S
gate:until:W-2-1500-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1500-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1500-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1500 to 1500 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1500-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1500-S
W-2-1500-R
gate:until:W-2-1500-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1500-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1500-R
gate:grep=^nd_up 0$:W-2-1500-R
W-2-1500-H?
W-2-1501-S
gate:until:W-2-1501-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1501-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1501-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1501 to 1501 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1501-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1501-S
W-2-1501-R
gate:until:W-2-1501-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1501-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1501-R
gate:grep=^nd_up 0$:W-2-1501-R
W-2-1501-H?
W-2-1502-S
gate:until:W-2-1502-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1502-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1502-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1502 to 1502 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1502-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1502-S
W-2-1502-R
gate:until:W-2-1502-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1502-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1502-R
gate:grep=^nd_up 0$:W-2-1502-R
W-2-1502-H?
W-2-1503-S
gate:until:W-2-1503-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1503-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1503-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1503 to 1503 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1503-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1503-S
W-2-1503-R
gate:until:W-2-1503-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1503-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1503-R
gate:grep=^nd_up 0$:W-2-1503-R
W-2-1503-H?
W-2-1511-S
gate:until:W-2-1511-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1511-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1511-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1511 to 1511 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1511-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1511-S
W-2-1511-R
gate:until:W-2-1511-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1511-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1511-R
gate:grep=^nd_up 0$:W-2-1511-R
W-2-1511-H?
W-2-1512-S
gate:until:W-2-1512-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1512-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1512-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1512 to 1512 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1512-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1512-S
W-2-1512-R
gate:until:W-2-1512-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1512-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1512-R
gate:grep=^nd_up 0$:W-2-1512-R
W-2-1512-H?
W-2-1513-S
gate:until:W-2-1513-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1513-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1513-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1513 to 1513 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1513-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1513-S
W-2-1513-R
gate:until:W-2-1513-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1513-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1513-R
gate:grep=^nd_up 0$:W-2-1513-R
W-2-1513-H?
W-2-1514-S
gate:until:W-2-1514-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1514-S
gate:grep=^v15 last sweep (?:24|-71|-61|-145|-4) :W-2-1514-S
gate:grep=^sw (?:done|fail|intr) mode wire from 1514 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:W-2-1514-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 0 mode wire probe 60 rings \d+ rec \d+$:W-2-1514-S
W-2-1514-R
gate:until:W-2-1514-R
gate:grep=^version rtl819x-nic 1\.5$:W-2-1514-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-2-1514-R
gate:grep=^nd_up 0$:W-2-1514-R
W-2-1514-H?
W-9-UP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-UP
W-9-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:W-9-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:W-9-LS
W-9-L
gate:grep=^4 packets transmitted, 4 received:W-9-L
gate:grep=^follower 1$:W-9-L
W-9-R
gate:until:W-9-R
gate:grep=^version rtl819x-nic 1\.5$:W-9-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):W-9-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:W-9-R
gate:grep=^nd_up 1$:W-9-R
W-9-H?
```

**`I-M`** — the mechanism maps (mlen, ext, d1-d3, txoff 0, txrb 1/2/4/8) and the history cells

```run
M-00-DN
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-00-DN
M-00-K
gate:until:M-00-K
gate:grep=^version rtl819x-nic 1\.5$:M-00-K
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-00-K
gate:grep=^nd_up 0$:M-00-K
gate:grep=^irq_taken 1$:M-00-K
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:M-00-K
M-mlen-V
gate:until:M-mlen-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-mlen-V
gate:grep=^tx15 txlen mlen txoff 2 txrb 0 dirty 1 p15 1$:M-mlen-V
M-mlen-S
gate:until:M-mlen-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-mlen-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-mlen-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-mlen-S
gate:grep=^sw key txlen mlen txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-mlen-S
M-mlen-C?
M-mlen-R
gate:until:M-mlen-R
gate:grep=^version rtl819x-nic 1\.5$:M-mlen-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-mlen-R
gate:grep=^nd_up 0$:M-mlen-R
M-mlen-H?
M-ext-V
gate:until:M-ext-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-ext-V
gate:grep=^tx15 txlen ext txoff 2 txrb 0 dirty 1 p15 1$:M-ext-V
M-ext-S
gate:until:M-ext-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-ext-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-ext-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-ext-S
gate:grep=^sw key txlen ext txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-ext-S
M-ext-C?
M-ext-R
gate:until:M-ext-R
gate:grep=^version rtl819x-nic 1\.5$:M-ext-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-ext-R
gate:grep=^nd_up 0$:M-ext-R
M-ext-H?
M-d1-V
gate:until:M-d1-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d1-V
gate:grep=^tx15 txlen d1 txoff 2 txrb 0 dirty 1 p15 1$:M-d1-V
M-d1-S
gate:until:M-d1-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d1-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-d1-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-d1-S
gate:grep=^sw key txlen d1 txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-d1-S
M-d1-C?
M-d1-R
gate:until:M-d1-R
gate:grep=^version rtl819x-nic 1\.5$:M-d1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d1-R
gate:grep=^nd_up 0$:M-d1-R
M-d1-H?
M-d2-V
gate:until:M-d2-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d2-V
gate:grep=^tx15 txlen d2 txoff 2 txrb 0 dirty 1 p15 1$:M-d2-V
M-d2-S
gate:until:M-d2-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d2-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-d2-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-d2-S
gate:grep=^sw key txlen d2 txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-d2-S
M-d2-C?
M-d2-R
gate:until:M-d2-R
gate:grep=^version rtl819x-nic 1\.5$:M-d2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d2-R
gate:grep=^nd_up 0$:M-d2-R
M-d2-H?
M-d3-V
gate:until:M-d3-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d3-V
gate:grep=^tx15 txlen d3 txoff 2 txrb 0 dirty 1 p15 1$:M-d3-V
M-d3-S
gate:until:M-d3-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d3-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-d3-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-d3-S
gate:grep=^sw key txlen d3 txoff 2 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-d3-S
M-d3-C?
M-d3-R
gate:until:M-d3-R
gate:grep=^version rtl819x-nic 1\.5$:M-d3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-d3-R
gate:grep=^nd_up 0$:M-d3-R
M-d3-H?
M-off0-V
gate:until:M-off0-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-off0-V
gate:grep=^tx15 txlen rlxfw txoff 0 txrb 0 dirty 1 p15 1$:M-off0-V
M-off0-S
gate:until:M-off0-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-off0-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-off0-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-off0-S
gate:grep=^sw key txlen rlxfw txoff 0 txrb 0 mode loop probe 60 rings \d+ rec \d+$:M-off0-S
M-off0-C?
M-off0-R
gate:until:M-off0-R
gate:grep=^version rtl819x-nic 1\.5$:M-off0-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-off0-R
gate:grep=^nd_up 0$:M-off0-R
M-off0-H?
M-rb1-V
gate:until:M-rb1-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb1-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 1 dirty 1 p15 1$:M-rb1-V
M-rb1-S
gate:until:M-rb1-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb1-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-rb1-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-rb1-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 1 mode loop probe 60 rings \d+ rec \d+$:M-rb1-S
M-rb1-C?
M-rb1-R
gate:until:M-rb1-R
gate:grep=^version rtl819x-nic 1\.5$:M-rb1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb1-R
gate:grep=^nd_up 0$:M-rb1-R
M-rb1-H?
M-rb2-V
gate:until:M-rb2-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb2-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 2 dirty 1 p15 1$:M-rb2-V
M-rb2-S
gate:until:M-rb2-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb2-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-rb2-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-rb2-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 2 mode loop probe 60 rings \d+ rec \d+$:M-rb2-S
M-rb2-C?
M-rb2-R
gate:until:M-rb2-R
gate:grep=^version rtl819x-nic 1\.5$:M-rb2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb2-R
gate:grep=^nd_up 0$:M-rb2-R
M-rb2-H?
M-rb4-V
gate:until:M-rb4-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb4-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 4 dirty 1 p15 1$:M-rb4-V
M-rb4-S
gate:until:M-rb4-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb4-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-rb4-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-rb4-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 4 mode loop probe 60 rings \d+ rec \d+$:M-rb4-S
M-rb4-C?
M-rb4-R
gate:until:M-rb4-R
gate:grep=^version rtl819x-nic 1\.5$:M-rb4-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb4-R
gate:grep=^nd_up 0$:M-rb4-R
M-rb4-H?
M-rb8-V
gate:until:M-rb8-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb8-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 8 dirty 1 p15 1$:M-rb8-V
M-rb8-S
gate:until:M-rb8-S
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb8-S
gate:grep=^v15 last sweep (?:17|-71|-61|-145|-4) :M-rb8-S
gate:grep=^sw (?:done|fail|intr) mode loop from 60 to 1514 probe 60 rc -?\d+ bufs [0-9A-F]{8}$:M-rb8-S
gate:grep=^sw key txlen rlxfw txoff 2 txrb 8 mode loop probe 60 rings \d+ rec \d+$:M-rb8-S
M-rb8-C?
M-rb8-R
gate:until:M-rb8-R
gate:grep=^version rtl819x-nic 1\.5$:M-rb8-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-rb8-R
gate:grep=^nd_up 0$:M-rb8-R
M-rb8-H?
HI-00-V
gate:until:HI-00-V
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-00-V
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:HI-00-V
HI-00-R
gate:until:HI-00-R
gate:grep=^version rtl819x-nic 1\.5$:HI-00-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-00-R
gate:grep=^nd_up 0$:HI-00-R
HI-00-H?
HI-1-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-1-X
HI-1-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-1-A
HI-1-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-1-B
HI-1-R
gate:until:HI-1-R
gate:grep=^version rtl819x-nic 1\.5$:HI-1-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-1-R
HI-1-C?
HI-2-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-2-X
HI-2-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-2-A
HI-2-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-2-B
HI-2-R
gate:until:HI-2-R
gate:grep=^version rtl819x-nic 1\.5$:HI-2-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-2-R
HI-2-C?
HI-3-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-3-X
HI-3-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-3-A
HI-3-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-3-B
HI-3-R
gate:until:HI-3-R
gate:grep=^version rtl819x-nic 1\.5$:HI-3-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-3-R
HI-3-C?
HI-4-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-4-X
HI-4-A
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-4-A
HI-4-B
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-4-B
HI-4-R
gate:until:HI-4-R
gate:grep=^version rtl819x-nic 1\.5$:HI-4-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-4-R
HI-4-C?
HI-9-R
gate:until:HI-9-R
gate:grep=^version rtl819x-nic 1\.5$:HI-9-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):HI-9-R
gate:grep=^nd_up 0$:HI-9-R
HI-9-H?
M-9-X
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-9-X
M-9-UP
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-9-UP
M-9-LS
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-9-LS
gate:grep=^r PSRP3 +4134 [0-9A-F]{6}[13579BDF][0-9A-F] [0-9A-F]{8} \d\d$:M-9-LS
gate:grep=^Port3 Force Mode disable\nEEE Status 0\nLinkUp \| NWay Mode Enabled$:M-9-LS
M-9-L
gate:grep=^4 packets transmitted, 4 received:M-9-L
gate:grep=^follower 1$:M-9-L
M-9-R
gate:until:M-9-R
gate:grep=^version rtl819x-nic 1\.5$:M-9-R
gate:grep=\A(?![\s\S]*(?:Booting\.\.\.|---RealTek|<RealTek>|Linux version)):M-9-R
gate:grep=^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1$:M-9-R
gate:grep=^nd_up 1$:M-9-R
M-9-H?
```

**`I-WS9`** — the sweeps' capture stopped and summed

```run
W-TCPSX?
W-SWALL?
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
`bench/2026-09-26/CORRECTIONS-block47.md` before it runs, **except the cells whose text this
section fixes now (they are logged there as they run) and a power-off, which this card
decides and which waits for nothing**:

* **The loader gate on any board cell** (the capture holds `Booting...`, `---RealTek`,
  `<RealTek>` or `Linux version`), or the same text found in any other failed board cell's
  capture, which is read first: **the owner powers off at once**; no other cell and no
  `CORRECTIONS` entry comes before it. The capture-stop invocations still run (host only);
  `I-Z` does not, and the next card's first map closes this press's bracket. The rest is a new
  card.
* **`R0-PREC`**, **`R0-ADDR`**, **`R0-FL`**, **`R0-PCAP`**, **`R0-TCPC`**: as block 46's; no
  power until each reads as its gate asks. **`R0-DMSG`** `0`: the follower is not running —
  start it (§ 6 (3)) and run `R0-DMSG2`; `2` or more: another `dmesg` runs, its owner stops it.
  **`R0-DW0`**: an empty log or `follower` not 1 — no power until (3) is redone; a non-zero
  `bug_preempt`, `usbnet_xmit` or `call_trace` with the board off — no power; WSL is restarted
  and both devices re-attached once more ((1)–(4)), and if the fresh log is still not clean the
  owner decides. **`R0-SUM`**, **`R0-ST`**: a checker is not the one this card pins, or fails
  its own self-test — no power. **`R0-VERB`** not `PASS`, or its self-test not 9 of 9: a word
  the card types does not parse, or a refusal is not a gated guard — no power; the card is
  wrong and is not repaired (a new card).
* **`gate:caught`**, **`R1-FL`**, **`R1Q`**, **`R1-PS`**, the maps and `n_writes`: exactly as
  block 46's § 6 decides them, with this card's names.
* **`RB-00-T`** (the boot page is not driver 1.5's untouched state: a 1.5 verb since boot, a
  record, a sweep): no cell after it runs until the owner has read the page.
* **`RB-01-C` or `RB-02-C` not `rbcheck verdict EQUAL`** — the read-back the owner's ruling
  puts first. DIFFER at either: the A/B ends here; `I-RQ` and `I-VC` … `I-WS9` do not run;
  `I-Z` runs, then power off.
  VOID (the control failed: the pointer moved, a held slot lost OWN, a recovery fired, the ring
  filled, or fewer than two held 61-B replies) is **not a FAIL**: `R6b-2`'s read-back conjunct
  is recorded *undetermined on this boot* for that path. VOID at `RB-01-C`: the invocation
  continues `--from RB-01-X2`. VOID at `RB-02-C`: the invocation continues `--from RB-02-X` to
  its end, and then the stack read-back is repeated once as the declared cells `X-RB2-S`,
  `X-RB2-P`, `X-RB2-R`, `X-RB2-C`, `X-RB2-X` and `X-RB2-L2`, the text of `RB-02-S` … `RB-02-L2`
  under those names (the base of `X-RB2-C` is `X-RB2-S`). By the owner's answer at the freeze
  (FREEZE-READY question 1, 2026-09-26: **proceed, with the fallback**), a VOID at `RB-01-C`,
  or one that survives the repeat at `RB-02-C`, does not end the A/B: **`I-RQ` runs next,
  once** (P1b: Q at `txrb 1`, a queue-time reading, not the default-settings read-back), then
  `I-VC` onward, and every *1.4 arm* is labelled *1.4 by `storeseq` (`NET-1AA`); the
  default-settings read-back VOID on this boot*, with `I-RQ`'s verdict beside it. A DIFFER at
  either read-back takes precedence: `I-RQ` does not run. Two EQUALs (the repeat's included):
  `I-RQ` does not run, and `I-VC` follows `I-RB`.
* **`I-RQ`**, run only after a VOID (above), and once. Its liveness, port-3, bracket and loader
  gates are decided as every invocation's below, except where the host is not reached after the
  recovery: failed at `RQ-02-LS` or `RQ-02-L`, `I-RQ` continues `--from RQ-09-SW` (no stack Q);
  failed at `RQ-09-LS` or `RQ-09-L`, after the restore, it continues `--from RQ-09-R`, and
  those two cells are readings. **`RQ-00-R`** (`I-RQ` does not start from 1.4's defaults with
  `rlx0` up): no cell of it runs until the owner has read the page. **`RQ-01-V`** (`txrb 1` not
  accepted, or `tx15` not `rlxfw … txrb 1 dirty 1`): no Q is read; the invocation continues
  `--from RQ-09-SW`, and the A/B proceeds as on a VOID, without Q. **`RQ-01-C` or `RQ-02-C` not
  `rbcheck verdict EQUAL`**: VOID (a control of Q's failed: a graded slot prints no `q<i> v1`
  line, its `w` line names another fill or a `rb` other than 1, or fewer than two 61-B
  `nic_xmit` fills) is a reading, and the invocation continues `--from RQ-01-F` or
  `--from RQ-02-F`. DIFFER: rbcheck's `q-differ` line decides, before any other cell (a VOID
  verdict's `q-differ` line is not acted on). `same` 1 or more, whatever else the line holds
  (memory at page time holds the word Q loaded, not 1.4's: the stores wrote another word, or
  never landed): the invocation continues `--from RQ-01-F` or `--from RQ-02-F` to its end,
  which puts the board back at 1.4's defaults, and then the A/B ends as a read-back DIFFER ends
  it (`I-VC` … `I-WS9` do not run; `I-Z` runs, then power off). `load-early` only (memory holds
  1.4's word: the load returned a word a store later replaced): nothing about what was stored,
  a reading for P12's ordering row; the invocation continues `--from RQ-01-F` or
  `--from RQ-02-F`, and the A/B proceeds. `other` 1 or more and no `same`: no cell runs until
  the owner has read the page. **`RQ-09-R`** (after the restore, not
  `tx15 txlen rlxfw txoff 2 txrb 0 dirty 0` with `nd_up 1`): the A/B does not start from a
  board off 1.4's defaults; `X-RQ9<n>`, the text of `RQ-09-SW`, then `X-RQ9<n>R`, the text of
  `RQ-09-R`, once; if that fails too, no cell runs until the owner has read the page. On the
  path through `I-RQ`, `VC-09-L`'s kernel-log window starts at `RB-09-H` and so spans `I-RQ`'s
  own windows: windows are not summed across it (`Z-DWALL` counts the whole log once).
* **A liveness gate** (`-L`: fewer than 4 of 4, or `follower` not 1), **a port-3 gate**
  (`-LS`: `PSRP3` or `port_status` not `LinkUp`) **or a path gate** (`E-F1-D`, `E-L1-D`,
  `E-F2-D`: `covered no`): the host → board path is the question (`NET-124`, `NET-54` 殘留).
  `follower` alone failing: the follower is restarted with (3)'s command (a host action, no
  owner's word), the liveness cell is typed again as `<name>2`, and every kernel-log window
  since the last `follower 1` is void. Otherwise, **before any recovery and with `rlx0` left as
  it is**, `NET-54` 殘留 ②'s read set in its order, as declared cells whose text is fixed here:
  (1) `X-SW<n>` `cat /proc/rtl819x-switch` — `MACCR`, `FFCR`, `SWTCR0` and `PSRP0/3/5/6/7`
  with bit 8, which this read clears, so it is first; `PSRP1/2/4` are not in rlxfw's table, so
  ②'s *eight `PSRP`* is read as these five and `port_status`; (2) `X-BR<n>`, the full board
  bracket (`asicCounter`'s port 3 and CPU port); (3) `X-PS<n>` `cat /proc/rtl865x/port_status`,
  last; (4) `X-HN<n>` on the host, `HN ; DW <the previous window>`. Then the recovery, a
  software action on the host (the coordinator's ruling 5a: no owner's word): (5) `X-RA<n>` —
  from PowerShell, `usbipd list` read fresh for the GbE adapter's busid (never the CP2102's),
  `usbipd detach --busid <b>`, `usbipd attach --wsl --busid <b>`, reading what each prints, then
  `R0-ADDR`'s command again in WSL; (6) `X-SW<n>b` and `X-PS<n>b`, the text of (1) and (3) after
  it — the pair says whether a re-attach bounces port 3's link (`R6b-6`'s H3, read for the first
  time); (7) the liveness cell again as `<name>2`. If it passes, the invocation continues
  `--from` the cell after the failed one; a stack arm whose path failed is void, never a result:
  `F1` void leaves `F2` as the fix's arm and loses the order reading, `L1` void leaves this boot
  without its positive control (P4), so it says nothing about the fix. If it fails: the arms that
  need the host are skipped (`I-E`'s remaining arms end at `I-WE9`), the loopback and wire sweeps
  still run (their verdicts are the board's counters; the host's are void), and the last
  liveness cells are readings.
* **WSL itself stops mid-press** (its service timing out, as it did three times at this desk on
  2026-09-26): the board is left as it is; WSL is started again with (2)'s keeper, the follower
  with (3), the GbE adapter re-attached as (5) above (the CP2102 too, if `usbipd list` shows it
  detached); `R0-PRE`'s form is run as `X-PRE<n>` with the board on (a `looprun`-free port
  check: 3 s, bytes are a reading), then the interrupted invocation continues `--from` the
  interrupted cell under its own name if that cell left no log, else under a new name; the
  bracket that spans the outage is void.
* **A board bracket's gate** (`until`, `version`, `tx15`, `nd_up`) with no loader text:
  `/dev/ttyUSB0` is checked and the read typed again as `X-RT<n>`; if it passes, it stands in
  and the invocation continues `--from` the next cell. A `tx15` that is not the arm's policy:
  the switch cell is typed again once as `X-SW<n>`; a second mismatch voids that arm, and the
  invocation continues `--from` the next arm's switch cell. **If the read returns nothing,
  garbage, or never ends on the prompt, the owner powers off.**
* **A sweep cell's `v15 last sweep` gate with a refusal** (-16, -17, -1, -6 or -22 on the page;
  the `sw` and `sw key` lines still name the previous sweep): the board's state is not the one
  the card and `R0-VERB` simulated; the invocation stops, the page is read, and nothing is typed
  until the decision is in `CORRECTIONS-block47.md`. A sweep ended by an errno after it opened
  (-71, -61, -145, -4, or `sw fail`/`intr`) passes its gates: a reading, and the map is that
  setting's finding (P12).
* **A sweep cell's `until`** (no page within its cap), no loader text: `X-RT<n>`, `cat
  /proc/rtl819x-nic-tx`. If the page answers, the sweep's state is recorded and the invocation
  continues `--from` the next cell. **If the page does not answer within 15 s the board is
  hung: a reading, and the owner powers off**; the rest is a new card.
* **`LB-00-K`** (`rlx0` not down, IRQ not taken, or the policy not `rlxfw … dirty 1`): no
  loopback sweep runs; `X-K<n>`, the text of `LB-00-DN` then `LB-00-K`, once; if it fails again,
  `I-LB` ends and `I-W` runs from `W-2-V` (the fix's wire sweep needs `LB-V`).
* **`LB-1-G`** (`leak`): `LBMODE` does not isolate. `VC-EE` and `SW-CLR` still run; `DS-r`,
  `CO-1`, `CO-2` and `LB-2` do not; `I-LB` continues `--from DS-v-SW` (the fix's `NET-61` runs,
  then the fix's map: the fix is predicted clean), and `I-M` does not run.
* **`VC-EE`, `SW-CLR`, `W-2-EP`** (a guard not as written): recorded as found. A `swclear` that
  did not clear: no further sweep runs until the owner has read the page (every later map would
  read another key's records).
* **`W-00`** (the fix's loopback map not clean, complete and registered at `delta0 0`): no
  multi-length wire sweep runs. If only `void` is non-zero, the VOID rule of § 3.5 applies with
  the host's Δ`tx_packets` over `LB-2-H` → `LB-V-H`: Δ 0 — `W-1` does not run; Δ > 0 — the
  `X-VD<n>` re-sweeps, then `X-W00` (the text of `W-00`, without its `sw done … from 60 to 1514`
  and `sw scored` gates, reading `mt none 0 clean 1455 bad_b 0 bad_a 0 void 0 skew 0` instead),
  and `W-1` runs `--from W-1a-S` only if it passes. Any other failure: `I-W` continues `--from
  W-2-V`, and `D2`'s sweep conjunct is unmeasured on this boot (a fix that fails in loopback is
  P9's refutation, not a wire result).
* **A wire quarter's `fault jfd 0`** (`W-1a-D` … `W-1d-D`): `D2`'s sweep conjunct fails on this
  boot (P10); the later quarters do not run; `I-W` continues `--from W-2-V`.
* **An `I-VC` gate**: the guard is recorded as found. Off-card `X-VC`: `ifconfig rlx0 down ; echo
  txlen rlxfw > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10.1.1.3 up`,
  then a read; the A/B continues with `I-WE0`, since every switch cell gates its own `tx15`.
* **`E-LIVE`** / **`S-LIVE`** `0`: the capture is not running — its invocation's transcript is
  read, and it is started again once as the off-card `W-TCPE2` / `W-TCPS2`; if that fails, the
  arms run without it (P0's `w` and the capture's readings are then untested, the counters
  stand). `2` or more: another `tcpdump` runs, its owner stops it.
* **A stimulus or switch cell exits non-zero** with no loader text: `X-RT<n>` as above; if
  rlxfw answers, the invocation continues `--from` that arm's first bracket, and the arm is
  void.
* **The press runs long**: after `I-W`, if more than 50 minutes have passed since the catch,
  `I-M` is not run (the mechanism maps are no conjunct of the DoD); `I-WS9` and `I-Z` run.
* **A host stimulus, a host bracket, a checker's reading, a capture stop**: `NAME?`; never a stop.
  **A background cell's exit** never stops a run.
* **Anything not listed**: no cell runs until the owner has read it; the decision goes into
  `CORRECTIONS-block47.md` first.

---

## § 7 What this block does not establish

* **`D2` on two boots.** This is boot 1; the DoD needs a second with 1.4 reproducing the loss on
  it. That is card 2's, a second block of this seating, drafted and frozen only after this
  card's readings (the owner's answer of 2026-09-26), with its own press: no cell here is `D2`'s
  second boot. Nor `D3` (`NET-111`'s twelve trials, on two boots; card 2 carries the first),
  `NET-117` 殘留 (card 2), `D3-MISS` ② and ①, or `P2`'s quiet image cold boot (card 3).
* **`R6b-2`'s read-back conjunct, if the read-back reads VOID.** `I-RQ`'s Q is a queue-time
  reading at `txrb 1` and does not stand in for it (P1b); nor does it say what the engine fetched.
* **That the fix is the vendor's convention on the wire.** `txlen vendor` sets the three
  length fields as the vendor and the loader do (`NET-122`); it does not copy their buffer
  offset or anything else, and a fix passing here says the lengths suffice on this driver.
* **The fix at every length on every path.** The wire sweep sends through `nic_do_tx`, in TX
  slots 0 and 1, each frame the first or second after a re-arm, after a predecessor at L or at
  60; slots 2 and 3 (slot 3 carries `WRAP`) and the stack path (`nic_xmit`) at the fix are read
  only by E2's eleven lengths and the 60-B liveness frames.
* **`NET-61`'s prediction outside E2's eleven lengths**, and the ring desync's mechanism.
* **Any mechanism as established.** Every rule and every byte source was fitted after the
  data (`PROPOSAL-R6b-2.md` § 14); the maps refute or leave standing, one arm each, one boot.
* **Whether the looped `ph_len` is measured by the engine or carried**, where it is right; and
  where the loop closes relative to the CPU port's framing.
* **That `txstall on` stops descriptor fetch in general**: where P1 reads EQUAL, its control
  shows it held for the frames the read-back filled, on this boot; a VOID says it did not, or
  that another control failed.
* **The `-EBUSY` a second writer meets while a sweep runs**: one console cannot type during a
  sweep; the refusal is the header's (`nic15check` K3) and unread on silicon.
* **The fix under load or over time**: `R6b-4` (`NET-67` 殘留, 30 minutes of traffic).
* **Timing**: "default = 1.4" holds for the stores (`tools/storeseq.py`) and, where P1 reads
  EQUAL, here for the words the engine was given; 1.5 adds loads and a call between them, and a cycle-level
  difference is not tested.
* **The host adapter's own drops** (`r8153_ecm` has no tally counters), and why `NET-124`
  happened, unless it happens again.
* **`NET-38` 殘留 ③ and `NET-41` 殘留**: `R6b-2`'s row puts each in this card only if the
  mechanism it read names their condition; none of their cells is here (FREEZE-READY names it).
* A flash write by anything but rlxfw's SPI driver between the two maps that the map does not
  see (`FLS-30`'s limits); `H601`'s 8,192 B are never hashed.
* **Which frame of a bracket the CPU port refused**: only how many; the wire sweep's brackets
  make that one length, not one frame.

---

```cells
bench/2026-09-26/R0-PRE
bench/2026-09-26/R0-PREC
bench/2026-09-26/R0-ADDR
bench/2026-09-26/R0-ETH
bench/2026-09-26/R0-TCPC
bench/2026-09-26/R0-DMSG
bench/2026-09-26/R0-DW0
bench/2026-09-26/R0-FL
bench/2026-09-26/R0-PCAP
bench/2026-09-26/R0-SUM
bench/2026-09-26/R0-ST
bench/2026-09-26/R0-VERB
bench/2026-09-26/R0-H
bench/2026-09-26/R1-CATCH
bench/2026-09-26/R1-FL
bench/2026-09-26/R1Q
bench/2026-09-26/R1-PS
bench/2026-09-26/R1-M0
bench/2026-09-26/R1-MB0
bench/2026-09-26/R1-NW0
bench/2026-09-26/RB-00-R
bench/2026-09-26/RB-00-H
bench/2026-09-26/RB-00-T
bench/2026-09-26/RB-01-DN
bench/2026-09-26/RB-01-X
bench/2026-09-26/RB-01-S
bench/2026-09-26/RB-01-T
bench/2026-09-26/RB-01-R
bench/2026-09-26/RB-01-C
bench/2026-09-26/RB-01-X2
bench/2026-09-26/RB-01-UP
bench/2026-09-26/RB-02-LS
bench/2026-09-26/RB-02-L
bench/2026-09-26/RB-02-S
bench/2026-09-26/RB-02-P
bench/2026-09-26/RB-02-R
bench/2026-09-26/RB-02-C
bench/2026-09-26/RB-02-X
bench/2026-09-26/RB-02-L2
bench/2026-09-26/RB-09-R
bench/2026-09-26/RB-09-H
bench/2026-09-26/RB-09-D
bench/2026-09-26/RQ-00-R
bench/2026-09-26/RQ-00-H
bench/2026-09-26/RQ-01-V
bench/2026-09-26/RQ-01-X
bench/2026-09-26/RQ-01-S
bench/2026-09-26/RQ-01-T
bench/2026-09-26/RQ-01-R
bench/2026-09-26/RQ-01-C
bench/2026-09-26/RQ-01-F
bench/2026-09-26/RQ-01-X2
bench/2026-09-26/RQ-01-UP
bench/2026-09-26/RQ-02-LS
bench/2026-09-26/RQ-02-L
bench/2026-09-26/RQ-02-S
bench/2026-09-26/RQ-02-P
bench/2026-09-26/RQ-02-R
bench/2026-09-26/RQ-02-C
bench/2026-09-26/RQ-02-F
bench/2026-09-26/RQ-09-SW
bench/2026-09-26/RQ-09-LS
bench/2026-09-26/RQ-09-L
bench/2026-09-26/RQ-09-R
bench/2026-09-26/RQ-09-H
bench/2026-09-26/RQ-09-D
bench/2026-09-26/VC-01
bench/2026-09-26/VC-02
bench/2026-09-26/VC-03
bench/2026-09-26/VC-04
bench/2026-09-26/VC-05
bench/2026-09-26/VC-06
bench/2026-09-26/VC-07
bench/2026-09-26/VC-07-C
bench/2026-09-26/VC-08
bench/2026-09-26/VC-08-R
bench/2026-09-26/VC-09-LS
bench/2026-09-26/VC-09-L
bench/2026-09-26/W-TCPE
bench/2026-09-26/E-LIVE
bench/2026-09-26/E-F1-SW
bench/2026-09-26/E-F1-LS
bench/2026-09-26/E-F1-L
bench/2026-09-26/E-F1-R0
bench/2026-09-26/E-F1-H0
bench/2026-09-26/E-F1-E2
bench/2026-09-26/E-F1-R1
bench/2026-09-26/E-F1-H1
bench/2026-09-26/E-F1-D
bench/2026-09-26/E-L1-SW
bench/2026-09-26/E-L1-LS
bench/2026-09-26/E-L1-L
bench/2026-09-26/E-L1-R0
bench/2026-09-26/E-L1-H0
bench/2026-09-26/E-L1-E2
bench/2026-09-26/E-L1-R1
bench/2026-09-26/E-L1-H1
bench/2026-09-26/E-L1-D
bench/2026-09-26/E-F2-SW
bench/2026-09-26/E-F2-LS
bench/2026-09-26/E-F2-L
bench/2026-09-26/E-F2-R0
bench/2026-09-26/E-F2-H0
bench/2026-09-26/E-F2-E2
bench/2026-09-26/E-F2-R1
bench/2026-09-26/E-F2-H1
bench/2026-09-26/E-F2-D
bench/2026-09-26/W-TCPEX
bench/2026-09-26/W-EWALL
bench/2026-09-26/W-TCPS
bench/2026-09-26/S-LIVE
bench/2026-09-26/LB-00-LS
bench/2026-09-26/LB-00-L
bench/2026-09-26/LB-00-R
bench/2026-09-26/LB-00-H
bench/2026-09-26/LB-00-DN
bench/2026-09-26/LB-00-K
bench/2026-09-26/LB-00-R2
bench/2026-09-26/LB-00-H2
bench/2026-09-26/LB-1-0060
bench/2026-09-26/LB-1-0061
bench/2026-09-26/LB-1-0062
bench/2026-09-26/LB-1-0063
bench/2026-09-26/LB-1-0263
bench/2026-09-26/LB-1-0276
bench/2026-09-26/LB-1-0277
bench/2026-09-26/LB-1-1511
bench/2026-09-26/LB-1-1512
bench/2026-09-26/LB-1-1513
bench/2026-09-26/LB-1-1514
bench/2026-09-26/LB-1-R
bench/2026-09-26/LB-1-H
bench/2026-09-26/LB-1-G
bench/2026-09-26/VC-EE
bench/2026-09-26/SW-CLR
bench/2026-09-26/DS-r-00
bench/2026-09-26/DS-r-0060-X
bench/2026-09-26/DS-r-0060-A
bench/2026-09-26/DS-r-0060-B
bench/2026-09-26/DS-r-0061-X
bench/2026-09-26/DS-r-0061-A
bench/2026-09-26/DS-r-0061-B
bench/2026-09-26/DS-r-0062-X
bench/2026-09-26/DS-r-0062-A
bench/2026-09-26/DS-r-0062-B
bench/2026-09-26/DS-r-0063-X
bench/2026-09-26/DS-r-0063-A
bench/2026-09-26/DS-r-0063-B
bench/2026-09-26/DS-r-0263-X
bench/2026-09-26/DS-r-0263-A
bench/2026-09-26/DS-r-0263-B
bench/2026-09-26/DS-r-0276-X
bench/2026-09-26/DS-r-0276-A
bench/2026-09-26/DS-r-0276-B
bench/2026-09-26/DS-r-0277-X
bench/2026-09-26/DS-r-0277-A
bench/2026-09-26/DS-r-0277-B
bench/2026-09-26/DS-r-1511-X
bench/2026-09-26/DS-r-1511-A
bench/2026-09-26/DS-r-1511-B
bench/2026-09-26/DS-r-1512-X
bench/2026-09-26/DS-r-1512-A
bench/2026-09-26/DS-r-1512-B
bench/2026-09-26/DS-r-1513-X
bench/2026-09-26/DS-r-1513-A
bench/2026-09-26/DS-r-1513-B
bench/2026-09-26/DS-r-1514-X
bench/2026-09-26/DS-r-1514-A
bench/2026-09-26/DS-r-1514-B
bench/2026-09-26/DS-r-C
bench/2026-09-26/DS-v-SW
bench/2026-09-26/DS-v-00
bench/2026-09-26/DS-v-0060-X
bench/2026-09-26/DS-v-0060-A
bench/2026-09-26/DS-v-0060-B
bench/2026-09-26/DS-v-0061-X
bench/2026-09-26/DS-v-0061-A
bench/2026-09-26/DS-v-0061-B
bench/2026-09-26/DS-v-0062-X
bench/2026-09-26/DS-v-0062-A
bench/2026-09-26/DS-v-0062-B
bench/2026-09-26/DS-v-0063-X
bench/2026-09-26/DS-v-0063-A
bench/2026-09-26/DS-v-0063-B
bench/2026-09-26/DS-v-0263-X
bench/2026-09-26/DS-v-0263-A
bench/2026-09-26/DS-v-0263-B
bench/2026-09-26/DS-v-0276-X
bench/2026-09-26/DS-v-0276-A
bench/2026-09-26/DS-v-0276-B
bench/2026-09-26/DS-v-0277-X
bench/2026-09-26/DS-v-0277-A
bench/2026-09-26/DS-v-0277-B
bench/2026-09-26/DS-v-1511-X
bench/2026-09-26/DS-v-1511-A
bench/2026-09-26/DS-v-1511-B
bench/2026-09-26/DS-v-1512-X
bench/2026-09-26/DS-v-1512-A
bench/2026-09-26/DS-v-1512-B
bench/2026-09-26/DS-v-1513-X
bench/2026-09-26/DS-v-1513-A
bench/2026-09-26/DS-v-1513-B
bench/2026-09-26/DS-v-1514-X
bench/2026-09-26/DS-v-1514-A
bench/2026-09-26/DS-v-1514-B
bench/2026-09-26/DS-v-C
bench/2026-09-26/DS-9-R
bench/2026-09-26/DS-9-H
bench/2026-09-26/DS-9-D
bench/2026-09-26/DS-9-DN
bench/2026-09-26/DS-9-K
bench/2026-09-26/CO-1
bench/2026-09-26/CO-2
bench/2026-09-26/LB-2-S
bench/2026-09-26/LB-2-C
bench/2026-09-26/LB-2-R
bench/2026-09-26/LB-2-H
bench/2026-09-26/LB-V-V
bench/2026-09-26/LB-V-S
bench/2026-09-26/LB-V-C
bench/2026-09-26/LB-V-R
bench/2026-09-26/LB-V-H
bench/2026-09-26/LB-V-D
bench/2026-09-26/W-00
bench/2026-09-26/W-1a-S
bench/2026-09-26/W-1a-R
bench/2026-09-26/W-1a-H
bench/2026-09-26/W-1a-D
bench/2026-09-26/W-1b-S
bench/2026-09-26/W-1b-R
bench/2026-09-26/W-1b-H
bench/2026-09-26/W-1b-D
bench/2026-09-26/W-1c-S
bench/2026-09-26/W-1c-R
bench/2026-09-26/W-1c-H
bench/2026-09-26/W-1c-D
bench/2026-09-26/W-1d-S
bench/2026-09-26/W-1d-R
bench/2026-09-26/W-1d-H
bench/2026-09-26/W-1d-D
bench/2026-09-26/W-2-V
bench/2026-09-26/W-2-EP
bench/2026-09-26/W-2-0060-S
bench/2026-09-26/W-2-0060-R
bench/2026-09-26/W-2-0060-H
bench/2026-09-26/W-2-0061-S
bench/2026-09-26/W-2-0061-R
bench/2026-09-26/W-2-0061-H
bench/2026-09-26/W-2-0062-S
bench/2026-09-26/W-2-0062-R
bench/2026-09-26/W-2-0062-H
bench/2026-09-26/W-2-0063-S
bench/2026-09-26/W-2-0063-R
bench/2026-09-26/W-2-0063-H
bench/2026-09-26/W-2-0064-S
bench/2026-09-26/W-2-0064-R
bench/2026-09-26/W-2-0064-H
bench/2026-09-26/W-2-0065-S
bench/2026-09-26/W-2-0065-R
bench/2026-09-26/W-2-0065-H
bench/2026-09-26/W-2-0066-S
bench/2026-09-26/W-2-0066-R
bench/2026-09-26/W-2-0066-H
bench/2026-09-26/W-2-0067-S
bench/2026-09-26/W-2-0067-R
bench/2026-09-26/W-2-0067-H
bench/2026-09-26/W-2-0068-S
bench/2026-09-26/W-2-0068-R
bench/2026-09-26/W-2-0068-H
bench/2026-09-26/W-2-0069-S
bench/2026-09-26/W-2-0069-R
bench/2026-09-26/W-2-0069-H
bench/2026-09-26/W-2-0070-S
bench/2026-09-26/W-2-0070-R
bench/2026-09-26/W-2-0070-H
bench/2026-09-26/W-2-0071-S
bench/2026-09-26/W-2-0071-R
bench/2026-09-26/W-2-0071-H
bench/2026-09-26/W-2-0263-S
bench/2026-09-26/W-2-0263-R
bench/2026-09-26/W-2-0263-H
bench/2026-09-26/W-2-0276-S
bench/2026-09-26/W-2-0276-R
bench/2026-09-26/W-2-0276-H
bench/2026-09-26/W-2-0277-S
bench/2026-09-26/W-2-0277-R
bench/2026-09-26/W-2-0277-H
bench/2026-09-26/W-2-0768-S
bench/2026-09-26/W-2-0768-R
bench/2026-09-26/W-2-0768-H
bench/2026-09-26/W-2-0769-S
bench/2026-09-26/W-2-0769-R
bench/2026-09-26/W-2-0769-H
bench/2026-09-26/W-2-0770-S
bench/2026-09-26/W-2-0770-R
bench/2026-09-26/W-2-0770-H
bench/2026-09-26/W-2-0771-S
bench/2026-09-26/W-2-0771-R
bench/2026-09-26/W-2-0771-H
bench/2026-09-26/W-2-0772-S
bench/2026-09-26/W-2-0772-R
bench/2026-09-26/W-2-0772-H
bench/2026-09-26/W-2-0773-S
bench/2026-09-26/W-2-0773-R
bench/2026-09-26/W-2-0773-H
bench/2026-09-26/W-2-0774-S
bench/2026-09-26/W-2-0774-R
bench/2026-09-26/W-2-0774-H
bench/2026-09-26/W-2-0775-S
bench/2026-09-26/W-2-0775-R
bench/2026-09-26/W-2-0775-H
bench/2026-09-26/W-2-1496-S
bench/2026-09-26/W-2-1496-R
bench/2026-09-26/W-2-1496-H
bench/2026-09-26/W-2-1497-S
bench/2026-09-26/W-2-1497-R
bench/2026-09-26/W-2-1497-H
bench/2026-09-26/W-2-1498-S
bench/2026-09-26/W-2-1498-R
bench/2026-09-26/W-2-1498-H
bench/2026-09-26/W-2-1499-S
bench/2026-09-26/W-2-1499-R
bench/2026-09-26/W-2-1499-H
bench/2026-09-26/W-2-1500-S
bench/2026-09-26/W-2-1500-R
bench/2026-09-26/W-2-1500-H
bench/2026-09-26/W-2-1501-S
bench/2026-09-26/W-2-1501-R
bench/2026-09-26/W-2-1501-H
bench/2026-09-26/W-2-1502-S
bench/2026-09-26/W-2-1502-R
bench/2026-09-26/W-2-1502-H
bench/2026-09-26/W-2-1503-S
bench/2026-09-26/W-2-1503-R
bench/2026-09-26/W-2-1503-H
bench/2026-09-26/W-2-1511-S
bench/2026-09-26/W-2-1511-R
bench/2026-09-26/W-2-1511-H
bench/2026-09-26/W-2-1512-S
bench/2026-09-26/W-2-1512-R
bench/2026-09-26/W-2-1512-H
bench/2026-09-26/W-2-1513-S
bench/2026-09-26/W-2-1513-R
bench/2026-09-26/W-2-1513-H
bench/2026-09-26/W-2-1514-S
bench/2026-09-26/W-2-1514-R
bench/2026-09-26/W-2-1514-H
bench/2026-09-26/W-9-UP
bench/2026-09-26/W-9-LS
bench/2026-09-26/W-9-L
bench/2026-09-26/W-9-R
bench/2026-09-26/W-9-H
bench/2026-09-26/M-00-DN
bench/2026-09-26/M-00-K
bench/2026-09-26/M-mlen-V
bench/2026-09-26/M-mlen-S
bench/2026-09-26/M-mlen-C
bench/2026-09-26/M-mlen-R
bench/2026-09-26/M-mlen-H
bench/2026-09-26/M-ext-V
bench/2026-09-26/M-ext-S
bench/2026-09-26/M-ext-C
bench/2026-09-26/M-ext-R
bench/2026-09-26/M-ext-H
bench/2026-09-26/M-d1-V
bench/2026-09-26/M-d1-S
bench/2026-09-26/M-d1-C
bench/2026-09-26/M-d1-R
bench/2026-09-26/M-d1-H
bench/2026-09-26/M-d2-V
bench/2026-09-26/M-d2-S
bench/2026-09-26/M-d2-C
bench/2026-09-26/M-d2-R
bench/2026-09-26/M-d2-H
bench/2026-09-26/M-d3-V
bench/2026-09-26/M-d3-S
bench/2026-09-26/M-d3-C
bench/2026-09-26/M-d3-R
bench/2026-09-26/M-d3-H
bench/2026-09-26/M-off0-V
bench/2026-09-26/M-off0-S
bench/2026-09-26/M-off0-C
bench/2026-09-26/M-off0-R
bench/2026-09-26/M-off0-H
bench/2026-09-26/M-rb1-V
bench/2026-09-26/M-rb1-S
bench/2026-09-26/M-rb1-C
bench/2026-09-26/M-rb1-R
bench/2026-09-26/M-rb1-H
bench/2026-09-26/M-rb2-V
bench/2026-09-26/M-rb2-S
bench/2026-09-26/M-rb2-C
bench/2026-09-26/M-rb2-R
bench/2026-09-26/M-rb2-H
bench/2026-09-26/M-rb4-V
bench/2026-09-26/M-rb4-S
bench/2026-09-26/M-rb4-C
bench/2026-09-26/M-rb4-R
bench/2026-09-26/M-rb4-H
bench/2026-09-26/M-rb8-V
bench/2026-09-26/M-rb8-S
bench/2026-09-26/M-rb8-C
bench/2026-09-26/M-rb8-R
bench/2026-09-26/M-rb8-H
bench/2026-09-26/HI-00-V
bench/2026-09-26/HI-00-R
bench/2026-09-26/HI-00-H
bench/2026-09-26/HI-1-X
bench/2026-09-26/HI-1-A
bench/2026-09-26/HI-1-B
bench/2026-09-26/HI-1-R
bench/2026-09-26/HI-1-C
bench/2026-09-26/HI-2-X
bench/2026-09-26/HI-2-A
bench/2026-09-26/HI-2-B
bench/2026-09-26/HI-2-R
bench/2026-09-26/HI-2-C
bench/2026-09-26/HI-3-X
bench/2026-09-26/HI-3-A
bench/2026-09-26/HI-3-B
bench/2026-09-26/HI-3-R
bench/2026-09-26/HI-3-C
bench/2026-09-26/HI-4-X
bench/2026-09-26/HI-4-A
bench/2026-09-26/HI-4-B
bench/2026-09-26/HI-4-R
bench/2026-09-26/HI-4-C
bench/2026-09-26/HI-9-R
bench/2026-09-26/HI-9-H
bench/2026-09-26/M-9-X
bench/2026-09-26/M-9-UP
bench/2026-09-26/M-9-LS
bench/2026-09-26/M-9-L
bench/2026-09-26/M-9-R
bench/2026-09-26/M-9-H
bench/2026-09-26/W-TCPSX
bench/2026-09-26/W-SWALL
bench/2026-09-26/R1-M1
bench/2026-09-26/R1-MB1
bench/2026-09-26/R1-NW1
bench/2026-09-26/Z-DW
bench/2026-09-26/Z-DWALL
bench/2026-09-26/R1Q-ab2
bench/2026-09-26/R1Q-2a
bench/2026-09-26/R1Q-boot
```

```cardnum
cells-fence	445	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^bench/2026-09-26/
declared-date	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md [*][*]declared date 2026-09-26[*][*]
presses-caught	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/R1-CATCH -{2}esc 180 -{2}esc-period
cap-cells	294	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out
host-cells	148	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST&? bench/2026-09-26/
send-over-127	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']{128,}'
no-shell-subst	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*[$]
no-flr	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*FLR
no-write-verb	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*(EW |EB |FLW )
no-burn	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*AUTOBURN
no-esc-after	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP .*-{2}esc-after
no-watchdog-cell	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*(watchdog|rtl819x-wdt)
no-mark-gate	0	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=RLXFW-
board-brackets	69	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/\S+-R[0-9]? -{2}send 'sleep\ 2\ ;\ cat\ /proc/rtl819x\-nic\ /proc/net/snmp\ /proc/net/arp\ /proc/rtl865x/asicCounter\ /proc/rtl819x\-nic' -{2}until 'rx_ph4\ \[0\-9A\-F\]\{8\}\(\?:\\r\\n\)\+\#\ \|Booting\\\.\\\.\\\.\|\-\-\-RealTek' -{2}seconds 15$
loader-gates	292	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\\A\(\?!\[\\s\\S\]\*\(\?:Booting\\\.\\\.\\\.\|\-\-\-RealTek\|<RealTek>\|Linux\ version\)\):
sweeps-full	12	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/\S+-S -{2}send 'echo swclear > /proc/rtl819x-nic ; echo sweep 60 1514 60 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' 
sweeps-sub-wire	4	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/W-1[a-d]-S -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep [0-9]+ [0-9]+ 60 wire > 
sweeps-one-wire	35	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/W-2-[0-9]{4}-S -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep ([0-9]+) \2 60 wire > 
sweeps-one-lb1	11	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/LB-1-[0-9]{4} -{2}send '(echo swclear > /proc/rtl819x-nic ; )?echo sweep ([0-9]+) \2 0 > 
sweeps-wire-all	40	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*echo sweep [0-9 ]+ wire 
swclear-sends	18	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send '[^']*echo swclear > 
switch-cells-e	3	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/E-[FL][12]-SW -{2}send 'ifconfig rlx0 down ; echo txlen (vendor|rlxfw) > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up'
isz-cells	3	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/E-[FL][12]-E2 :: ISZ 10[.]1[.]1[.]3$
path-gates	3	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^path p3 rx d .*:E-[FL][12]-D$
isz-macro-b45	1	count bench/2026-09-25b/PREDICTIONS-B47-block45.md ^`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
isz-macro-here	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^`ISZ <ip>` = `for s in 18 19 20 21 221 234 235 1469 1470 1471 1472; do ping -I enxfc19286184c9 -c 20 -s [$]s -i 0[.]05 -w 10 -q <ip>; done`
tde-macro	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^`TDE <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap/<f> ether src 02:52:4c:58:46:57`
tds-macro	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^`TDS <f>` = `timeout 7200 sudo -n tcpdump -n -U -Q in -s 64 -i enxfc19286184c9 -w /home/key/fwre-work/rebuild/s112/r6b3/pcap/<f> 'ether src 02:52:4c:58:46:57 and [(]ether proto 0x88b5 or [(]ether proto 0x8100 and ether\[16:2\] = 0x88b5[)][)]'`
tcpdump-cells	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST& bench/2026-09-26/W-TCP[ES] :: TD[ES] W[ES][.]pcap$
tcpdump-stops	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/W-TCP[ES]X :: sudo -n pkill -INT -x tcpdump && sleep 1$
liveness-cells	11	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/\S+-L2? :: FL 10[.]1[.]1[.]3 ; PL ; DW 
follower-gates	12	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^follower 1\$:
port3-gates	10	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^Port3 Force Mode disable
psrp3-gates	10	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^r PSRP3 
switch-first	10	count bench/2026-09-26/PREDICTIONS-B49-block47.md -{2}send 'cat /proc/rtl819x-switch ; cat /proc/rtl865x/port_status'
rearm-cells	29	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/\S+ -{2}send 'echo\ engine\ off\ >\ /proc/rtl819x\-nic\ ;\ echo\ arm\ >\ /proc/rtl819x\-nic\ ;\ echo\ engine\ on\ >\ /proc/rtl819x\-nic' -{2}idle 3
ds-runs	22	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/DS-[rv]-[0-9]{4}-B -{2}send 'echo tx 0x3f 0x8800 0 [0-9]+ > /proc/rtl819x-nic ; sleep 1 ; echo lb off > /proc/rtl819x-nic ; cat /proc/rtl819x-nic' 
map-until-prompt	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/R1-M[01] .* -{2}until 'map_lines \[0-9\][+]\\r\\n# '
nw-cells	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/R1-NW[01] -{2}send 'cat /proc/rtl819x-spi' -{2}idle 3 -{2}seconds 15$
rq-cells	24	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^bench/2026-09-26/RQ-
rq-run-fences	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^[*][*]`I-RQ`[*][*] — 
rq-txrb1-cell	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/RQ-01-V -{2}send 'ifconfig rlx0 down ; echo txrb 1 > /proc/rtl819x-nic ; cat /proc/rtl819x-nic-tx' 
rq-txrb1-gate	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^v15 last txrb 7 :RQ-01-V$
rq-restore-cell	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/RQ-09-SW -{2}send 'ifconfig rlx0 down ; echo txrb 0 > /proc/rtl819x-nic ; echo arm > /proc/rtl819x-nic ; ifconfig rlx0 10[.]1[.]1[.]3 up' 
rq-restore-gate	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^tx15 txlen rlxfw txoff 2 txrb 0 dirty 0 p15 1\$:RQ-09-R$
rq-q-checks	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/RQ-0[12]-C :: RBC q bench/2026-09-26/RQ-0[12]-R[.]log -{2}expect
rq-q-gates	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^gate:grep=\^rbcheck verdict EQUAL\$:RQ-0[12]-C$
rb-tx-expects	3	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/R[BQ]-01-[CF] :: RBC (fill|q) bench/2026-09-26/R[BQ]-01-R[.]log -{2}expect 0:tx:60,1:tx:61,2:tx:1514$
rb-xmit-expects	3	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/R[BQ]-02-[CF] :: RBC (fill|q) bench/2026-09-26/R[BQ]-02-R[.]log -{2}expect-xmit 61:2 -{2}base bench/2026-09-26/R[BQ]-02-S[.]log$
rq-stall-cells	2	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^CAP -{2}out bench/2026-09-26/RQ-0[12]-S -{2}send 'echo txstall on > 
rq-ping-2	1	count bench/2026-09-26/PREDICTIONS-B49-block47.md ^HOST bench/2026-09-26/RQ-02-P :: ping -I enxfc19286184c9 -c 2 -i 0[.]5 -W 1 -s 19 10[.]1[.]1[.]3$
rbcheck-q-words	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py ^Q_FILL_W = \["ph1", "ph3", "ph4", "mb2", "mb3", "mb4", "mb5"\]$
rbcheck-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py ^VERSION = "1[.]2"$
rbcheck-alloc-only-words	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py ^ALLOC_ONLY = \["ph0", "ph2", "ph5", "mb0", "mb1"\]$
driver-rb-fields	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h ^#define NIC15_RB_FIELDS\t\t0x1\t/[*] 12 slot words into Q, before OWN 
driver-rb-pre-own	2	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c if [(]nic15_pol[.]txrb[)] nic15_rb_pre_own[(]i[)];\t/[*] 1[.]5: before OWN [*]/$
driver-qv-zero-at-txrb0	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\tif [(]!nic15_pol[.]txrb[)]$
driver-q-format	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h nic15_pf[(]&pg, "q%u v%X %08X %08X %08X %08X %08X %08X %08X "$
sha-pcapwin-py	036971a201c1d74bb5411daf61e623ae8c5e2b8140f78847b4871b0c457e6ee7	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py
sha-rbcheck-py	80ce6799e5a454e3dd7dbec70fb45bf7ffad119f41f8b6b5c14bca37e4531854	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/rbcheck.py
sha-swcheck-py	e36bd29e4714408ac50d2fe7dd90dde71cb88be5c6007ec22277a0ef0082c890	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/swcheck.py
sha-brdelta-py	3866b96cbf50007b9176a23bcc709dcce8ef8d046b44ddc0337b08a615500595	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/brdelta.py
sha-dmesgwin-py	04c1a5492467fd5c0a4963df0624d95b07a5d9b7616a45e243cf154576a1a4e9	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/dmesgwin.py
sha-arith49-py	7f7dad0b02e5616943f536e6cdc31c42692a8b1f5de67d2ce0422e7b2728bafe	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.py
sha-verbcheck49-py	34557e8b239d8639271cbaeadc56e9128610f390b653602f74b5957a8f5c4a65	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/verbcheck49.py
sha-fixtures-MANIFEST-sha256	4069cd42f6f8334ed6e1bd5ae8fe44c87333d2a092da27b88f77c9c54f277b90	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/fixtures/MANIFEST.sha256
selftest-pcapwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-pcapwin.out ^pcapwin\ self\-test:\ 19\ of\ 19\ passed$
selftest-rbcheck	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-rbcheck.out ^rbcheck\ self\-test:\ 52\ of\ 52\ passed$
selftest-swcheck	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-swcheck.out ^swcheck\ self\-test:\ 12\ of\ 12\ passed$
selftest-dmesgwin	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-dmesgwin.out ^dmesgwin\ self\-test:\ 6\ of\ 6\ passed$
selftest-brdelta	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-brdelta.out ^brdelta\ self\-test:\ 18\ of\ 18\ passed$
selftest-verbcheck49	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/selftest-verbcheck49.out ^verbcheck\ self\-test:\ 9\ of\ 9\ passed$
verbcheck-pass	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/verbcheck49.out ^verbcheck verdict PASS$
pcapwin-version	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin.py ^VERSION = "1[.]2"$
pcapwin-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/pcapwin-mutate.out ^mutations: 16 planted, 0 not as expected$
rbq-mutations	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/rbq-mutate.out ^rbq mutations: 10 planted, 0 not as expected$
fixtures-14-pinned	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/fixtures/MANIFEST.sha256 ^[0-9a-f]{64} {2}f758d62:config/rlxfw-src/linux-2[.]6[.]30/drivers/net/rtl819x-nic[.]c$
fixtures-header	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/fixtures/rtl819x-nic-tx.h
repo-header-is-fixtures	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h
fixtures-nic15check	13198b2c9009b5175026f8bf9fa1d4988d8e5cb466d8e45a63bd9035f5788286	sha256 /home/key/fwre-work/rebuild/s112/r6b3/card/fixtures/nic15check.py
repo-nic15check-is-fixtures	13198b2c9009b5175026f8bf9fa1d4988d8e5cb466d8e45a63bd9035f5788286	sha256 tools/nic15check.py
driver-version-1.5	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^#define RTL819X_NIC_VERSION\t"rtl819x-nic 1[.]5"$
driver-swend-mark	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c rlxfw_markx[(]"N-SWEND", nic15_swend_val[(]rc, nic15_sw[.]bad_a,$
driver-swsum-mark	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c rlxfw_markx[(]"N-SWSUM", nic15_swsum_val[(]nic15_sw[.]scored,$
driver-sweep-mark	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c rlxfw_markx[(]"N-SWEEP", nic15_swbegin_val[(]wire, from, to[)][)];
driver-sweep-is-loop-unless-wire	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h else if [(]!strcmp[(]e, " wire"[)][)]$
driver-wire-bound	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h if [(]wire && from != to && txlen != NIC15_LEN_VENDOR[)]$
driver-keycheck-eexist	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h ^\t\treturn -EEXIST;$
driver-mark-engoff	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\t\trlxfw_mark[(]"N-ENGOFF"[)];$
driver-mark-arm	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\trlxfw_markx[(]"N-ARM", nic_rx_ring[)];$
driver-mark-armr	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\trlxfw_markx[(]"N-ARMR", [(]u32[)]nic_n_arm_flush[)];$
driver-mark-engon	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic.c ^\trlxfw_markx[(]"N-ENGON", nic_rd[(]NIC_CPUICR[)][)];$
mark-format	1	count config/rlxfw-src/linux-2.6.30/include/linux/rlxfw-mark.h rlxfw_puts_hex[(]"RLXFW-" tag "=",
driver-tx15-format	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h "tx15 txlen %s txoff %d txrb %d dirty %d p15 %d[\\]n",
driver-sw-format	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h "sw %s mode %s from %u to %u probe %u rc %d bufs %08X[\\]n",
driver-count-return	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-nic-tx.h ^\treturn nic15_ret[(]v, rc [?] rc : [(]int[)]count[)];$
switch-psrp3-row	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c ^\t[{] "PSRP3",\t0x4134, 0, 0 [}],$
switch-linkup-bit	1	count config/rlxfw-src/linux-2.6.30/drivers/net/rtl819x-switch.c ^#define RTL819X_PSRP_LINKUP\t[(]1u << 4[)]$
errno-estale	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tESTALE\t\t151\t
errno-eproto	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tEPROTO\t\t71\t
errno-etimedout	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tETIMEDOUT\t145\t
errno-enodata	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/arch/rlx/include/asm/errno.h ^#define\tENODATA\t\t61\t
errno-ebusy	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEBUSY\t\t16\t
errno-einval	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEINVAL\t\t22\t
errno-eexist	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEEXIST\t\t17\t
errno-eperm	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEPERM\t\t 1\t
errno-eintr	1	count /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/include/asm-generic/errno-base.h ^#define\tEINTR\t\t 4\t
img-manifest-green	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^verdict\tgreen$
img-manifest-vmlinux	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^vmlinux_sha256\t900faed7c8bfdf2e984b7abee0bb03cfb6929fc5fe33fa5e6ce696c639037337$
img-manifest-variant	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^variant\tquiet$
img-record-nfjrom	1	count /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/rtkimage-record.tsv ^nfjrom_sha256\t7d7dd4b03a1fdaaf68c29c2212891eb4aa2db8453961eb4728328630c5823ce9$
img-record-clean	1	count /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/rtkimage-record.tsv ^tripwire_verdict\tVENDOR-TRIPWIRE: CLEAN\s+cmd-rc=0
img-nfjrom-sha256	7d7dd4b03a1fdaaf	sha256-16 /home/key/fwre-work/rebuild/s112/r6b2/rtk/r6b2q/rlxfw/kroot/rtkload/nfjrom
img-cell-header	82b1c1c2038497fbb38efa4730861bb87687dd464e40fc12ce3367b1fd19f63d	sha256 /home/key/fwre-work/rebuild/r3-4/cells/r6b2q/top/linux-2.6.30/drivers/net/rtl819x-nic-tx.h
img-sysmap-frame	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] nic15_frame$
img-sysmap-drain	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] nic15_drain$
img-sysmap-page	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] nic15_pf$
img-sysmap-switch	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.System.map ^[0-9a-f]{8} [tT] rtl819x_sw_read_proc$
img-recipe	1	count /home/key/fwre-work/rebuild/r3-4/out/r6b2q.manifest ^recipe_id\t06c39ca3$
b46-mb1-digest	1	count bench/2026-09-25c/R1-MB1.log ^0927be41e91fe4bd32986a48e47c9a3f0d34ce587c7b42324c088b602f45da46\s+-$
b46-bufs	2	count bench/2026-09-25c/C-01-R.log ^bufs A15C8290
b46-c61	1	count notes/nic-driver.md ^[|] 61 [|] A1-02 FAULT.*`26676D10` → 9,831 [|]$
b46-c263	1	count notes/nic-driver.md ^[|] 263 [|] .*`2E6F7D02` → 11,887 [|]$
b46-c277	1	count notes/nic-driver.md ^[|] 277 [|] .*`3E7F4900` → 15,999 [|]$
b46-c1511	1	count notes/nic-driver.md ^[|] 1,511 [|] .*`0E4F5902` → 3,663 [|]$
b46-armc-dsync	1	count notes/nic-driver.md Δ`n_skb_fail` \+1 and Δ`n_dsync` \+1, while Δ`n_rx` is 2 at all 11 runs
b46-p3-frozen	1	count notes/nic-driver.md identical in [*][*]56 of 56[*][*] reads from A2-02-R
b46-bracket-time	1	count /home/key/fwre-work/rebuild/s111/r6b/run/run-I-A.log END A1-01-R rc=0 5[.]2 s
b46-rearm-time	1	count /home/key/fwre-work/rebuild/s111/r6b/run/run-I-B.log END B-01-X rc=0 3[.]2 s
b46-catch-time	1	count /home/key/fwre-work/rebuild/s111/r6b/run/run-I-1.log END R1-CATCH rc=0 200[.]2 s
b46-round-time	1	count /home/key/fwre-work/rebuild/s111/r6b/run/run-I-1.log END R1Q rc=0 21[.]2 s
b46-map-time	1	count /home/key/fwre-work/rebuild/s111/r6b/run/run-I-1.log END R1-M0 rc=0 13[.]8 s
b46-port-status-fmt	1	count bench/2026-09-17/C2-PORT.log ^LinkUp [|] NWay Mode Enabled
b46-psrp3-fmt	1	count bench/2026-09-22b/A6-SW.log ^r PSRP3 +4134 000000F9 
b46-p0-76	1	count notes/nic-driver.md P0's identities hold at 76 of 76 brackets
b46-wdt-armed	1	count bench/2026-09-25c/R1Q-boot.log ^RLXFW-W4=00240000
b46-h601-unhashed	1	count notes/nic-driver.md What it cannot see: `H601`'s 8,192 B, two writes
b46-mark-interleave	1	count bench/2026-09-25c/C-02-X.log ^ne on R>L X/Fproc/Wr-tl8N1-9ExN-nicG
arith-controls	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^arith49 controls: 5 of 5 hold
arith-bufs	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BUFS b46 A15C8290 mod8 0$
arith-lb2-728	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^# LB-2: sweep 60 1514 60 at 1[.]4's settings, loopback: 728 bad-b$
arith-lb2-marks	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB2 swsum 05AF0000 swend 000002D8$
arith-lb2-mt	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB2 mt none 0 clean 727 bad_b 728 bad_a 0 void 0 skew 0$
arith-lbv-marks	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LBV swsum 05AF0000 swend 00000000 
arith-lb2-hprev	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB2 H-prev histogram 1607:92 3663:92 5719:88 7775:88 9831:92 11887:92 13943:92 15999:92$
arith-lb2-hown	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB2 H-own histogram 9831:728$
arith-lb2-hslot	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB2 H-slot histogram 8224:724 9831:4$
arith-co-61	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^CO 61->1514 H-prev 9831 H-own 5719 H-slot 9831$
arith-co-277	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^CO 277->61 H-prev 15999 H-own 9831 H-slot 8224$
arith-w1-total	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 total units 1455 frames 2910 jfd 0$
arith-w1a	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 60-423 units 364 frames 728 jfd 0 cpu_crc 728 host_rx 728 lenby 1:61-423 lenby 365:60$
arith-w1b	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 424-787 units 364 frames 728 jfd 0 cpu_crc 728 host_rx 728 lenby 1:424-787 lenby 364:60$
arith-w1c	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 788-1151 units 364 frames 728 jfd 0 cpu_crc 728 host_rx 728 lenby 1:788-1151 lenby 364:60$
arith-w1d	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 1152-1514 units 363 frames 726 jfd 0 cpu_crc 726 host_rx 726 lenby 1:1152-1514 lenby 363:60$
arith-w1a-marks	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 60-423 sweep 5703C1A7 swsum 016C0000 swend 00000000$
arith-w1d-marks	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W1 1152-1514 sweep 574805EA swsum 016B0000 swend 00000000$
arith-lb1-61	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 L 61 bad-b ph_b 9831 map 2 swsum 00010000 swend 00000001$
arith-lb1-263	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 L 263 bad-b ph_b 11887 map 2 
arith-lb1-277	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 L 277 bad-b ph_b 15999 map 2 
arith-lb1-1511	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 L 1511 bad-b ph_b 3663 map 2 
arith-lb1-60	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 L 60 right ph_b 64 map 1 swsum 00010000 swend 00000000$
arith-lb1-hb	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 hb 9831:3:61-63 11887:1:263-263 15999:1:277-277 3663:2:1511-1512$
arith-lb1-mt	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^LB1 mt none 1444 clean 4 bad_b 7 bad_a 0 void 0 skew 0$
arith-w2-total	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W2 total lengths 35 bad 19 clean 16 jfd 19 cpu_crc 70 host_rx 51$
arith-w2-min	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^W2 smallest predicted wrong ph_b over the bad lengths and the three sources 1607 [(]> AcptMaxLen 1536[)]$
arith-ef	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^EF replies 220 requests 220 buckets 64:20 65-127:60 128-255:0 256-511:60 512-1023:0 1024-1518:80 
arith-m-d1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^M d1 swsum 05AF0000 swend 000000B6$
arith-m-d2	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^M d2 swsum 05AF0000 swend 0000016C$
arith-m-d3	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^M d3 swsum 05AF0000 swend 00000222$
arith-m-mlen	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^M mlen swsum 05AF0000 swend 00000000$
arith-m-sweep	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^M sweep 4C03C5EA 
arith-hi-1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^HI 60-61-61-60 carried/H-prev rrw- carried/H-own rrw- second/H-prev rw-- second/H-own rw--$
arith-hi-2	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^HI 61-60-60-60 carried/H-prev rw-- carried/H-own rw-- second/H-prev rrrr second/H-own rrrr$
arith-hi-3	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^HI 60-1511-1511-60 carried/H-prev rrww carried/H-own rrw- second/H-prev rww- second/H-own rwwr$
arith-hi-4	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^HI 1511-60-60-60 carried/H-prev rww- carried/H-own rw-- second/H-prev rrrr second/H-own rrrr$
arith-ds-rlxfw	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^DS rlxfw 60:0/0 61:1/1 62:1/1 63:1/1 263:1/1 276:0/0 277:1/1 1511:1/1 1512:1/1 1513:0/0 1514:0/0$
arith-ds-vendor	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^DS vendor 60:0/0 61:0/0 62:0/0 63:0/0 263:0/0 276:0/0 277:0/0 1511:0/0 1512:0/0 1513:0/0 1514:0/0$
arith-errno-eexist	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO EEXIST 17 hex FFFFFFEF$
arith-errno-eperm	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO EPERM 1 hex FFFFFFFF$
arith-errno-enodata	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO ENODATA 61 hex FFFFFFC3$
arith-errno-eproto	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO EPROTO 71 hex FFFFFFB9$
arith-errno-etimedout	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO ETIMEDOUT 145 hex FFFFFF6F$
arith-errno-eintr	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^ERRNO EINTR 4 hex FFFFFFFC$
arith-bytes-vendor	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'txlen vendor' 13$
arith-bytes-rlxfw	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'txlen rlxfw' 12$
arith-bytes-swclear	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'swclear' 8$
arith-bytes-txrb1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'txrb 1' 7$
arith-bytes-sweep	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'sweep 60 1514 60' 17$
arith-bytes-sweep-wire	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^BYTES 'sweep 60 1514 60 wire' 22$
arith-rlxfw-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting rlxfw +rule M1\-cover8 +bad +728 
arith-rlxfw-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting rlxfw +rule M1\-room8ph +bad +728 
arith-rlxfw-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting rlxfw +rule M2\-shift8 +bad +728 
arith-rlxfw-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting rlxfw +rule M2\-shift8m +bad +728 
arith-mlen-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting mlen +rule M1\-cover8 +bad +0 
arith-mlen-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting mlen +rule M1\-room8ph +bad +728 
arith-mlen-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting mlen +rule M2\-shift8 +bad +728 
arith-mlen-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting mlen +rule M2\-shift8m +bad +727 
arith-ext-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting ext +rule M1\-cover8 +bad +728 
arith-ext-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting ext +rule M1\-room8ph +bad +0 
arith-ext-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting ext +rule M2\-shift8 +bad +728 
arith-ext-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting ext +rule M2\-shift8m +bad +728 
arith-vendor-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting vendor +rule M1\-cover8 +bad +0 
arith-vendor-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting vendor +rule M1\-room8ph +bad +0 
arith-vendor-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting vendor +rule M2\-shift8 +bad +728 
arith-vendor-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting vendor +rule M2\-shift8m +bad +727 
arith-d1-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d1 +rule M1\-cover8 +bad +182 
arith-d1-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d1 +rule M1\-room8ph +bad +728 
arith-d1-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d1 +rule M2\-shift8 +bad +728 
arith-d1-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d1 +rule M2\-shift8m +bad +727 
arith-d2-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d2 +rule M1\-cover8 +bad +364 
arith-d2-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d2 +rule M1\-room8ph +bad +728 
arith-d2-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d2 +rule M2\-shift8 +bad +728 
arith-d2-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d2 +rule M2\-shift8m +bad +727 
arith-d3-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d3 +rule M1\-cover8 +bad +546 
arith-d3-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d3 +rule M1\-room8ph +bad +728 
arith-d3-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d3 +rule M2\-shift8 +bad +728 
arith-d3-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting d3 +rule M2\-shift8m +bad +728 
arith-txoff0-m1-cover8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txoff0 +rule M1\-cover8 +bad +728 
arith-txoff0-m1-room8ph	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txoff0 +rule M1\-room8ph +bad +728 
arith-txoff0-m2-shift8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txoff0 +rule M2\-shift8 +bad +728 
arith-txoff0-m2-shift8m	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txoff0 +rule M2\-shift8m +bad +728 
arith-txrb1	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txrb-1 rule M1-cover8 bad 728 
arith-txrb2	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txrb-2 rule M1-cover8 bad 728 
arith-txrb4	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txrb-4 rule M1-cover8 bad 728 
arith-txrb8	1	count /home/key/fwre-work/rebuild/s112/r6b3/card/arith49.out ^setting txrb-8 rule M1-cover8 bad 728 
```
