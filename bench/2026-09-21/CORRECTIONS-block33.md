# CORRECTIONS — block 33, seating 31

Written after the block ran. `PREDICTIONS-B35-block33.md` is frozen and is not
edited; everything it got wrong is recorded here.

**`check-predictions`: `29 of 29 captures came after the prediction, 0 did not`.**
Every carded cell was spent before the first wedge, so nothing in the block was
lost to it.

---

## § 0 What the card got right

| | predicted | measured |
|---|---|---|
| `RLXFW-ID0` | `f179cf21` | `f179cf21`, on **four** separate uploads |
| `rx_ring` / `mb_ring` | `A15B8000` / `A15B8020` | identical — so `B4`–`B6`'s literal arguments were valid rather than void |
| `nfjrom` sha256 | `8275a0799abce5a1…` | matched the pin on every `looprun` pre-check |
| `AUTOBURN` at `0x8040D4A0` | `00000000` | `00000000`, every upload |
| detector control | 0 / 4 / 1 | **0 / 4 / 1** |
| H2, in the form that matters | driver index == hardware index | held at every read |

---

## § 1 🔴 H3 is REFUTED, and the card named this exact outcome as a refutation

The card: *"A single datagram of N frames first drives Δ ≠ 0 at **N = 9**, the
first N greater than `NIC_RX_DESC` = 8. Refuted by Δ ≠ 0 at 7 or 8."*

| rung | frames | ping | Δ`n_dsync` | `dsync_last_d` | Δ at the `/proc` read |
|---|---:|---|---:|---:|---|
| `C1` | 7 | 1 recv | 0 | 0 | 0 |
| **`C2`** | **8** | 1 recv | **1** | **3** | **0** |
| `C3` | 9 | 0 recv | 4 | 1 | 1 |
| `C4` | 10 | 1 recv | 3 | 1 | 3 |
| `C5` | 14 | 0 recv | 5 | 2 | 2 |

**The threshold is the ring depth itself, not one past it.**

🔴 **And two older readings are demoted by the same table.**

* **Δ is 1, 2 or 3 and TRANSIENT.** `SPEC.md` `NET-61` records Δ = 4 on four
  readings out of nine, *"恰好錯開 4 格並停在那裡"*. Tonight Δ was never 4, and
  at `C2` the detector saw Δ = 3 during a poll while the `/proc` read taken
  seconds later showed **Δ = 0**.
* 🔴 **So every single-sample Δ reading this project has taken is a LOWER
  BOUND.** A `/proc` read samples the two registers once; the event does not
  wait for it. This is the same class as `IRQ-08`'s discovery that a `TCIR`
  pending bit has a lifetime of at most one 10 ms tick — a register read that
  happens to miss is not a zero.
* ⚠️ **The loss is not monotonic in burst size**: 7 ✓, 8 ✓, 9 ✗, 10 ✓, 14 ✗.
  A datagram is lost if *any* fragment is, so this is consistent with a
  probabilistic corruption rather than a clean threshold. 推 — the block has
  one observation per rung and cannot separate the two.

---

## § 2 🔴 H4 is REFUTED, and it is a negative about the fix itself

The card: *"`n_arm_flush` is non-zero at least once. If every `arm` discards
nothing, the refill loop is dead code on this path and its cost is
unjustified — which is a result about the fix."*

量: **`n_arm_flush 0` at every read, across all six arms and both wedges.** The
RX ring was clean at every arm. The refill loop discarded nothing, ever.

**The loop is not retracted, and the reason is on the TX side rather than the
RX side** — see § 4, where reclaiming the four TX descriptors is what recovers
a wedged board. But the RX half of § 1's claim in the driver comment is, on
this evidence, untriggered code, and it is recorded as such rather than
described as a fix that worked.

---

## § 3 🔴🔴 THE BLOCK'S BIGGEST RESULT WAS NOT ON THE CARD, AND IT REFUTES THE ATTRIBUTION THE CARD WAS BUILT ON

The card exists because seating 30 named `NET-61` — the ring desync — as what
stops `D5`. **That attribution is wrong.**

量, three wedges in one seating, the third with the client **backgrounded** so
the shell stayed free — which is the single change that made the fault
measurable, because every previous observation had the shell blocked behind a
*foreground* client and could see nothing:

| | before | during | after | late |
|---|---|---|---|---|
| `n_rx` | 10 | 19 | 23 | **27** → 35 → **38** |
| `n_napi_poll` | 8 | 16 | 20 | 24 |
| `n_tx` | 7 | 23 | **26** | **26** |
| `tx_stopped` | 0 | 0 | **1** | **1** |
| `n_tx_wake` | 0 | 0 | **0** | **0** |
| `n_tx_timeout` | 0 | 0 | 0 | 0 |
| `n_dsync` | 0 | 0 | **0** | **0** |
| `seen_iisr` | `0000320E` | `0000320E` | `0000320E` | `0000320E` |

**The board is MUTE, not DEAF.** `n_rx` climbs while the host reports 0 replies:
the board is receiving the ICMP requests and cannot send the answers.

The smoking gun, `W6-TXD`:

```
txd0 A15B81D1   txd1 A15B81E9   txd2 A15B8201   txd3 A15B821B
```

**All four TX descriptors have bit 0 set — all four are engine-owned.** The
mechanism, complete:

1. Sustained TCP makes the board transmit continuously (ACKs — the frozen
   `txd` lengths are 82 / 74 / 82 / 74).
2. The engine stops retiring TX descriptors. **Why it stops is not answered by
   this block** and is the residual.
3. All four fill. `nic_xmit` finds slot `tx_idx` engine-owned, calls
   `netif_stop_queue` — `n_tx_stop 1`, `tx_stopped 1`.
4. The wake path tests **the same slot**, which never becomes CPU-owned, so
   `n_tx_wake` stays 0.
5. `ndo_tx_timeout` can never fire: `NET-57`, `tx_queue_len = 0` makes this a
   `noqueue` device.

**What this refutes, by name:**

* 🔴 **"an ingress wedge"** — `NET-54`'s reading. The ingress path is healthy
  throughout; `n_rx` and `n_napi_poll` both keep moving.
* 🔴 **"the board went deaf"** — it hears everything.
* 🔴 **"a hard hang"** — `NET-64`'s headline. The kernel runs, the driver polls,
  the tty echoes.
* 🔴 **`NET-61` as `D5`'s blocker** — `n_dsync 0` through all three wedges, with
  the detector's positive control proven in the same boot. **The desync is not
  involved.**

⚠️ **It is not rate-dependent.** The bandwidth ladder wedged on its **first**
rung, `-b 1M` — 1.25 MB over 10 s, less than half the 2.59 MB carried in the
run before it, and gentler than the 14-frame ping bursts the same boot handled
without trouble.

---

## § 4 🟢 The new `arm` recovers a wedged board, and `NET-54`'s recovery cost is wrong for this fault

量, on an already-wedged board, costing nothing:

```
after `engine off ; arm ; engine on`:
txd0 A15B81D0   txd1 A15B81E8   txd2 A15B8200   txd3 A15B821A     <- bit 0 CLEAR, all four
tx_stopped 1 -> 0      n_tx_wake 0 -> 1      n_tx 26 -> 31
```

Then `ifconfig rlx0 down ; ifconfig rlx0 10.1.1.3 up` took ping to **2/4** and
`n_tx` to 42, `n_rx` to 55.

`docs/KNOWN-ISSUES.md` carries `NET-54` as *only a cold power-on cleared it*.
**For this fault that is now false**, and the reclaim loop in `nic_do_arm()` is
what makes it false — the same loop § 2 records as never having discarded an RX
descriptor.

🔴 **The recovery is NOT durable.** The next traffic re-wedged it: `R6-REST`
returned **1 byte**. So this buys a power cycle back, not a working path.

---

## § 5 🔴 Three instrument defects of mine, and the first is the one with reach

**① A verification that passed because it was taken before the thing it
certified could change.** The host `iperf3` server was started with
`nohup … &` inside `wsl -d Ubuntu-24.04 -- bash -ls`. `CLAUDE.md`'s environment
section already records that such a process **dies with its parent**. I checked
`ss` two seconds later, saw `LISTEN 10.1.1.2:5201`, and recorded it as
verified. The server was dead by the time the board dialled, and the board
wedged against nothing.

**The rule is not "remember that nohup dies".** It is: **a check belongs at the
point of USE, not the point of start.** `bwladder.sh` and `d5run.sh` both
re-read `ss` immediately before each board-side command and refuse rather than
measure. That is the fix, and it is in the scripts rather than in a paragraph.

**② `cardcheck … | tail -25` then `echo RC=$?` reported `RC=0`** — that is
`tail`'s status. `CLAUDE.md` owns this trap in two places and I reproduced it
inside the freeze procedure. Re-run without the pipe, `cardcheck numbers`
exited **2** and refused for want of a `cardnum` fence, which was correct.

**③ The card predicted `rx_idx 0` after an arm and it read 1.** Background ARP
arrived between the arm and the read. The prediction was too literal; the claim
that matters — `rx_idx` equals `(rpdcr0_pos − rx_ring)/4` — held at every read.
**A card should predict the invariant, not a snapshot of a free-running
counter.**

---

## § 6 What the block did not establish

* **`D5` was not obtained**, and the reason is different from seating 30's and
  is measured: sustained TCP wedges the TX ring within seconds at any offered
  rate tried. The `NET-60` half *is* closed — 量 `V1`,
  `Reverse mode, remote host 10.1.1.2 is sending`, so 3.1.3 at both ends
  completes the control exchange that 3.16 could not.
* **`D6` was not attempted**, and the card established before power that it is
  unmeetable on this image at all: `CONFIG_PRINTK` is `set@loud`, so *zero
  oops* and *kernel log captured whole* are unobservable with `PRINTK=n`.
  `s31L` was built for it and **never uploaded**.
* **`R6-6` was not attempted.** Stopped deliberately: two of its three DoD
  clauses were established unreachable before power, and the board's post-
  recovery state (ping 2/4) is not a baseline anything can be measured against.
* **Why the engine stops retiring TX descriptors is unanswered.** That is the
  residual this block hands forward, and it is a sharper question than the one
  it started with.
* ⚠️ `n_rx` rose by more than the fragment count on several rungs (e.g. +14 for
  a 9-fragment datagram). Unexplained; 推 background ARP and stragglers. Not
  chased.
* **Zero flash-write commands, zero `FLR`.** `AUTOBURN` read `00000000` before
  every one of the four uploads.

---

## § 7 Power cycles

**Four**, against a card that budgeted one: the 22:29 cold boot plus three
recoveries at ~01:25, ~01:47 and ~01:58. Every one was a genuine cold power-on,
each confirmed by the loader's own discriminator being **absent**
(`Reboot Result from Watchdog Timeout!`, 0 occurrences in `X4`/`X7`/`X8`).

Three of the four were spent on the same fault. 🟢 **The fourth need not have
been**, and that is § 4's result: `ifconfig down/up` would have done it.
