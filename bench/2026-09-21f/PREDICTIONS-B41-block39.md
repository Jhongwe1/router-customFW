# PREDICTIONS — block 39, seating 36 (the loader as a test harness, and whether a stuck descriptor clears)

Frozen before any cell below runs. **declared date 2026-09-21** —
`bench/2026-09-21e` is seating 35's and this is a new power cycle, so it gets
its own directory.

Marks: 量 measured on this device · 讀 read out of code or a dump · 推 inferred,
pending a measurement.

---

## § 0 Two honesty notes, written rather than left to be found

**① The board was powered before this card existed.** The operator asked for
the ESC window first. `bench/2026-09-21f/S0-catch` (22:22:33, 300 s of ESC,
`prompt_seen: true`, 量 **no** `Reboot Result from Watchdog Timeout!` line in
the banner, so a **cold power-on**) is what caught the loader prompt. It is
deliberately **not** in the `cells` fence. No cell below has run and no image
has been uploaded.

**② Two readings were taken before the freeze and they are why § 1 changed.**
Both live outside this repository, in `$FWRE_WORK/rebuild/seat36/`, because
they are setup readings and not cells:

* `X0-arp-with-esc.txt` — 22:25, ARP probe to `10.1.1.1` **while** the ESC
  stream was up: `ip neigh` `INCOMPLETE` ×3, `arping` 5 transmitted / 0
  received.
* `X1-arp-quiet.txt` — 22:28:53, the same probe with the console **quiet** and
  no process holding `/dev/ttyUSB0`: `arping rc=1 received=0`,
  `neigh no-lladdr INCOMPLETE`.

🔴 **Those two together refute the obvious instrument explanation** (that the
ESC stream at 50/s starves the loader's polled NIC service loop) and leave the
one `RUNSHEET` already carried — see § 1.

---

## § 1 🔴 The framing this card inherited is wrong, and the correction is one command

`docs/nic-vendor-diff.md` § 12.5 says, and `docs/KNOWN-ISSUES.md`'s last
section repeats:

> 量 `looprun`'s `S5c`, every seating: **at the loader prompt the board answers
> ARP.**

讀 `RUNSHEET.md:566` (`G3`), which has said the opposite since 2026-08-24:

> `IPCONFIG` gives the **loader** its own address — it synthesises its MAC from
> that address, so it is the board's and not the peer's. **The loader answers
> the network only after this.**

量 `tools/looprun.py:345-363`: `S5` (`rescue`, which sends `AUTOBURN`, then
`LOADADDR`, then `IPCONFIG --ip 10.1.1.1`) is built into the plan **before**
`S5b` and `S5c`. So every `S5c` pass this project has ever recorded was taken
**after** an `IPCONFIG`, and the sentence "the loader answers ARP at its
prompt" was never true of a bare cold boot. `X0`/`X1` are that sentence being
measured for the first time, and it is false.

**This does not kill the experiment; it adds one line to it.** The correction
goes into `docs/nic-vendor-diff.md` § 12.5 and `docs/KNOWN-ISSUES.md` either
way, because a cell that would have read *the loader is dead* on a healthy
board is the most expensive kind of card defect.

---

## § 2 What this block decides, and the refutation conditions

### 2.1 🔴🔴 `A3` / `A5` — the cell this seating exists for

`NET-93`/`NET-94`: the loader drives the **same four TX descriptors**, the same
`TXFD` doorbell and the same `ph_portlist = 0x3F`, with no Linux, no NAPI and
no interrupts underneath it. Blast it with the dose that wedges rlxfw and ask
whether it is still transmitting.

* **It survives** → the engine is fine under this traffic, the fault is in
  rlxfw's software, and every driver-side candidate stays alive.
* **It stops** → the fault is below both implementations, rlxfw is exonerated,
  and `R6-5`'s whole framing — including whether `D5` is reachable on this
  hardware — has to be rewritten.

🔴 **The refutation condition for the instrument, not the board**: `A1` must
read ANSWERS. If it does not, every SILENT below is unattributable and the
whole of Part A is void.

### 2.2 🔴 The dose, and why it is checkable rather than asserted

`tools/netblast.py` carries `bench/2026-09-21e/y5-rateladder.py`'s `blast()`
unchanged. Its `self-test` `C1a`–`C1e` re-derive that file's constants **from
that file** and refuse on drift; 量 22:29, GREEN, 0 failed. So rung 1 —
**0.5 Mbit/s, 8 s, 1,400-byte datagrams to port 9999** — is `Y5`'s dose, which
took rlxfw down in **8.01 s / 347 frames** (`NET-87`).

* 推 rung 1 sends **345 ± 5 frames**. `FRAME_BITS` = 11,568, so
  8.0 s × 0.5 Mbit/s ÷ 11,568 = **345.8**.
* 🔴 If rung 1's frame count is not within 5 % of 345, the two runs did not
  receive the same dose and no comparison with `Y5` may be quoted.

### 2.3 🔴 The loader transmits only when asked, so the TX ring must be loaded

Under Linux, UDP to a closed port provokes an ICMP port-unreachable per
datagram and the TX ring cycles as a side effect. The loader has no IP stack
past ARP and TFTP: it drops every datagram silently. **A ladder without an ARP
load would flood the RX side with the TX ring idle, which is not the
experiment** — `NET-67 殘留` is a TX descriptor that stops being retired.

`--arp-load` keeps ARP requests going for the whole of every step, so each
reply is a TX descriptor completing **during** the blast, and the liveness
reading is continuous rather than a single probe afterwards.

* 推 `A3` rung 1 records **≥ 5** ARP samples, all ok.
* ⚠️ If `n` is 0 or 1 the load did not run and the rung measures RX only; say
  so rather than quoting it.

### 2.4 🟢 The console is a third observable, and it is passive

讀 `docs/nic-vendor-diff.md` § 12.1: on a descriptor that is still owned by the
engine the loader prints **`Assertion fail at file`** and enters
`0x80403DC8: j 0x80403DC8`. A wedge by that path is **visible on the console**
and invisible to an ARP probe.

`A3-CON` and `A5-CON` are `console-capture` with **no `--esc` and no `--send`**
— zero bytes toward the board, so they cannot themselves perturb the loader's
command loop.

* 推 both capture **0 bytes**.
* 🔴 `Assertion fail` in either → the wedge is the assertion path, and that is
  the strongest possible form of the "it stops" outcome.

### 2.5 🟢 And a loader wedge should reset the board for free

讀 the fifteenth update in `CLAUDE.md`: `bsp_machine_restart` aside, this part
has a watchdog, and the **loader's** encoding is `OVSEL=1001`. A loader spinning
in `j 0x80403DC8` stops kicking it.

* 推 if `A3`/`A5` wedge the loader, the board **resets itself**, and the next
  banner carries **`Reboot Result from Watchdog Timeout!`** (量 seating 17, that
  line is present after every watchdog reset and absent after every cold
  power-on).
* 🔴 **Silent on ARP with no reset** → it is *not* the assertion path, and the
  engine stopped without the loader noticing — which is a different and worse
  finding than a wedge.
* ⚠️ This is the recovery plan too: a loader wedge is predicted to cost **zero**
  power presses. If the prediction is wrong it costs one, and that is the whole
  power risk of Part A.

### 2.6 ⚠️ `A2` — an instrument question that affects every future seating

`X0` and `X1` cannot separate *ESC starves the NIC loop* from *no `IPCONFIG`*,
because in both readings there was no `IPCONFIG`. With one in place the two
come apart in fifteen seconds.

* 推 `A2-ARP` reads ANSWERS with the ESC stream up.
* 🔴 SILENT → the ESC stream suppresses the loader's polled NIC service loop,
  no `--esc` capture may run beside a network cell, and `S0-catch`-style windows
  become a thing that has to be closed before the network is used.

### 2.7 🔴 `B` — does a stuck descriptor clear itself, and this decides what gets built

`docs/KNOWN-ISSUES.md`: the 1,548 OWN-bit reads of `NET-88` are twelve
128-iteration tight loops with interrupts off, so they bound recovery on a
**microsecond** scale. Nothing has ever looked at **seconds**.

Wedge with `Y5`'s dose, then read the four TX descriptor OWN bits at
**+5 / +30 / +120 / +600 s**, each paired with a ping.

* **It clears** → the mechanism is starvation and the fix is a deeper ring plus
  a real timeout.
* **It does not clear** → the fix is detect-stall-and-re-arm.
* 🔴 It may **not** use `watchdog_timeo`: `NET-55`/`NET-57` measured the vendor
  setting `tx_queue_len = 0`, so the device is `noqueue`, `dev_watchdog_up()` is
  never called, and `ndo_tx_timeout` is dead code on this board.
* ⚠️ **Refutation of the cell itself**: if `B1-PING` (taken before the blast)
  fails, there is no wedge to observe and the ladder measured nothing.

### 2.8 ⚠️ `R6-6`'s readable half rides along

`VCR0`/`VCR1`/`PVCR0`–`PVCR4` come out of one `cat /proc/rtl819x-switch`.
Two of `R6-6`'s three DoD clauses were **measured unreachable before power**
and stay that way: one cable gives one `LinkUp` (thirteen readings), and rlxfw
cannot write the VLAN table at all (讀 `rtl819x-switch.c:88-92`, the table is
behind the `TACI` indirect path). `R6-7` writes the weaker true statement.

* 推 the seven values agree with seating 33 and seating 35.
* 🔴 A disagreement is a finding and not a slip — it would mean a `PVCR` moved
  without anything writing it.

---

## § 3 The image, and the host side

**Part A needs no image and no boot.** The board is at the loader prompt from
the cold power-on at 22:22.

**Part B** uses **`s32a`**, unchanged from seating 34/35: `RECIPE_ID`
**`84385d91`**, `nfjrom` **1,180,672 B**, sha256 `eee556f46adf9c06…`. The
discriminator is `looprun --image-sha256`; `RECIPE_ID` cannot tell two images
apart here (`FW-99`).

**Host side.** There is no listener to prove — every datagram goes to a
**closed** port, which is the point. What has to be shown alive is the
**generator**, and it is shown three ways rather than by `ss -ltn`:
`netblast self-test` GREEN before the port is opened; the pre-ladder probe in
every `blast` invocation, which **refuses** the run if the target is already
silent; and rung 1's own frame count against § 2.2's 345.

Addresses: host **10.1.1.2** on `enxfc19286184c9`; the **loader** at
**10.1.1.1**; rlxfw at **10.1.1.3** under Linux.

---

## § 4 The cells

`CAP` = `/usr/bin/python3 tools/console-capture.py capture --port /dev/ttyUSB0
--baud 38400`. `HOST <prefix> :: <cmd>` runs on this workstation and its stdout
goes to `<prefix>.log`. `NB` = `/usr/bin/python3 tools/netblast.py`.

🔴 **`A3-CON` and `A3-LADDER` run CONCURRENTLY**, as do `A5-CON`/`A5-LONG`: the
console capture is started first, in the background, and the ladder runs in the
foreground inside its window. They are two cells because they are two
instruments on two wires.

```cells
bench/2026-09-21f/A0-IPCFG
bench/2026-09-21f/A1-ARP
bench/2026-09-21f/A2-CON
bench/2026-09-21f/A2-ARP
bench/2026-09-21f/A3-CON
bench/2026-09-21f/A3-LADDER
bench/2026-09-21f/A4-ARP
bench/2026-09-21f/A5-CON
bench/2026-09-21f/A5-LONG
bench/2026-09-21f/A6-ARP
bench/2026-09-21f/A7-PROMPT
bench/2026-09-21f/B0-SW
bench/2026-09-21f/B1-PING
bench/2026-09-21f/B1-NIC
bench/2026-09-21f/B2-LADDER
bench/2026-09-21f/B3-T5
bench/2026-09-21f/B3-P5
bench/2026-09-21f/B4-T30
bench/2026-09-21f/B4-P30
bench/2026-09-21f/B5-T120
bench/2026-09-21f/B5-P120
bench/2026-09-21f/B6-T600
bench/2026-09-21f/B6-P600
```

### Part A — the loader, no image, no boot

```
#-- A0  § 1. The one command the old framing was missing. Expect: Now your Target IP is 10.1.1.1
CAP --out bench/2026-09-21f/A0-IPCFG --send 'IPCONFIG 10.1.1.1' --seconds 10
#-- A1  🔴 THE POSITIVE CONTROL. SILENT here voids every SILENT below. § 2.1
HOST bench/2026-09-21f/A1-ARP :: NB probe --target 10.1.1.1 --dev enxfc19286184c9 --src 10.1.1.2
#-- A2  § 2.6. ESC stream up; does the polled NIC service loop still answer?
CAP --out bench/2026-09-21f/A2-CON --esc 16 --esc-period 0.02 --seconds 18
HOST bench/2026-09-21f/A2-ARP :: NB probe --target 10.1.1.1 --dev enxfc19286184c9 --src 10.1.1.2
#-- A3  🔴🔴 THE LADDER. Rung 1 is Y5's dose exactly. § 2.1-2.4
CAP --out bench/2026-09-21f/A3-CON --seconds 110
HOST bench/2026-09-21f/A3-LADDER :: NB blast --target 10.1.1.1 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5,1.0,2.0,4.0,8.0 --step-s 8 --arp-load --out bench/2026-09-21f/A3-LADDER.json
HOST bench/2026-09-21f/A4-ARP :: NB probe --target 10.1.1.1 --dev enxfc19286184c9 --src 10.1.1.2
#-- A5  the 30 s rung, at the top of the ladder.
CAP --out bench/2026-09-21f/A5-CON --seconds 50
HOST bench/2026-09-21f/A5-LONG :: NB blast --target 10.1.1.1 --src 10.1.1.2 --dev enxfc19286184c9 --rates 8.0 --step-s 30 --arp-load --out bench/2026-09-21f/A5-LONG.json
HOST bench/2026-09-21f/A6-ARP :: NB probe --target 10.1.1.1 --dev enxfc19286184c9 --src 10.1.1.2
#-- A7  is the command loop still there. § 2.5's reset question is answered by this banner.
CAP --out bench/2026-09-21f/A7-PROMPT --esc 6 --esc-period 0.02 --seconds 10
```

### Part B — `s32a`, one boot through `looprun`, then § 2.7

```
#-- B0  R6-6's readable half. § 2.8
CAP --out bench/2026-09-21f/B0-SW --send 'cat /proc/rtl819x-switch' --seconds 30
#-- B1  the before half. A failure here voids the ladder. § 2.7
HOST bench/2026-09-21f/B1-PING :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21f/B1-NIC --send 'cat /proc/rtl819x-nic' --seconds 25
#-- B2  Y5's dose against rlxfw. 347 frames / 8.01 s / 0.5 Mbit/s is the known wedge.
HOST bench/2026-09-21f/B2-LADDER :: NB blast --target 10.1.1.3 --src 10.1.1.2 --dev enxfc19286184c9 --rates 0.5 --step-s 8 --out bench/2026-09-21f/B2-LADDER.json
#-- B3..B6  the four OWN-bit reads, each paired with a ping. +5 / +30 / +120 / +600 s.
CAP --out bench/2026-09-21f/B3-T5 --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21f/B3-P5 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21f/B4-T30 --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21f/B4-P30 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21f/B5-T120 --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21f/B5-P120 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
CAP --out bench/2026-09-21f/B6-T600 --send 'cat /proc/rtl819x-nic' --seconds 25
HOST bench/2026-09-21f/B6-P600 :: ping -I 10.1.1.2 -c 4 -W 2 -q 10.1.1.3
```

🔴 **`B3`–`B6` are `cat` cells on a board whose network is wedged.** The shell
is on the serial console and is not affected; `FW-64` says one `cat` is **two**
`read_proc` invocations on this kernel, so any per-read counter in that dump
moves by two per cell and not by one.

⚠️ **Part B is conditional on Part A.** If `A3`/`A5` kill the loader, Part B
needs whatever recovery § 2.5 predicts; if the loader survives, Part B runs on
the same power-up through a `looprun` reset. **Neither branch needs a power
press that has not already been spent.**

---

## § 5 What this block does NOT do

* It does not build an image. `P2` — detect-stall recovery, `NET-82`'s
  `ph_mbuf` follow, `FW-107`'s comment — is decided **by** `B3`–`B6` and is
  written up, not built, tonight.
* It does not measure `D5`. `D5` names an `iperf3` figure with its spread over
  ≥ 3 runs and nothing here produces one.
* It does not write the VLAN table, and § 2.8 says why that is measured rather
  than skipped.
* **Zero flash writes, zero `FLR`.** No cell below issues `EW`, `EB`, `FLW` or
  a burn, and Part B's upload lands at `0x80500000`, which is RAM.

```cardnum
cells-fence	23	count bench/2026-09-21f/PREDICTIONS-B41-block39.md ^bench/2026-09-21f/[AB]
declared-date	1	count bench/2026-09-21f/PREDICTIONS-B41-block39.md [*][*]declared date 2026-09-21[*][*]
cap-cells	11	count bench/2026-09-21f/PREDICTIONS-B41-block39.md ^CAP -{2}out
host-cells	12	count bench/2026-09-21f/PREDICTIONS-B41-block39.md ^HOST bench/2026-09-21f/
blast-cells	3	count bench/2026-09-21f/PREDICTIONS-B41-block39.md ^HOST .*NB blast
probe-cells	4	count bench/2026-09-21f/PREDICTIONS-B41-block39.md ^HOST .*NB probe
```
