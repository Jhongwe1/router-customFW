# Corrections to block 32's card — written before the corrected cells ran

`PREDICTIONS-B34-block32.md` is frozen at `0f0fc88` and is not edited.

---

## 0. The ladder stopped at `N2`, and the board is in a state this project has not seen before

### What the block got before it stopped

| cell | reading |
|---|---|
| `R0-REBOOT` | 322 bytes, **`Reboot Result from Watchdog Timeout!` present**, loader prompt caught — `FW-37` and `FW-45` both hold: `busybox reboot -f` is a watchdog bite |
| `R1-BURN` | `00000000`, **after** the rescue, as `CORRECTIONS-block30.md` § 0 requires |
| `R3-BOOT` | **1,874 bytes against a prediction of 1,874**, `RLXFW-ID0=EDC94765` — the fourth independent hit for this image |
| `R6-BASE` | 🟢 **`rp=0 rm=0 Δ=0`, `seen_iisr 00000000`, `n_rx 0`, `n_irq 0`** |
| `R7-NET0` | 🟢 **`InTruncatedPkts 0`** |
| `R8-B0` | 🟢🟢 **20 transmitted, 20 received, 0 % loss** |
| `R9-NB0` | 🟢🟢 after twenty six-frame datagrams: **`Δ=0`**, `seen_iisr 0000320E` — **without bit 16** |

**Two pre-registered questions are answered by those seven rows.**

① **The degradation is accumulated state that a boot clears and `arm` does not.**
`R8-B0` is byte-identical to `H4-f6` (20/20) and to `Z2-f6` (20/168) and to
`Z11-f6` (11/181, after `arm`). Same command, same board, three states: fresh
boot **20/20**, degraded **12 %**, `arm`-repaired **6 %**. Only the boot restores
it.

② **Six frames do not desynchronise the rings.** `R9-NB0` reads `Δ=0` and
`seen_iisr` without bit 16 after 121 frames in twenty bursts of six, from a
baseline that was measured rather than assumed (`R6-BASE`, the first completely
clean NIC reading this project has ever taken: every counter 0, both positions 0,
`seen_iisr` 0).

### 🔴 And then `arm` killed the board

`A1` re-armed (`RLXFW-N-ARM=A15B8000` emitted). `L1` — **one unfragmented
1400-byte ping** — got no reply, and `N1` shows why: `rp=1 rm=1` but
**`rx_idx 2`**. The hardware restarted at slot 0 and the driver did not, so the
driver is one slot ahead of the engine.

⚠️ **That is the flaw this card's § 2 wrote down in advance** — *"`nic_do_arm()`
does not reset `nic_rx_idx`"* — and in `CORRECTIONS-block31.md` § 2 the same
sequence happened to land clean because `rx_idx` had wrapped to 0 by receiving
exactly one frame. **It was luck, it was recorded as luck, and this is the run
where it ran out.**

`A2` re-armed again, `L2` sent one six-frame ping, and `N2` came back **0 bytes**.

### 🔴🔴 0 bytes is not `NET-59`'s state, and the difference is the whole point

| | `NET-59` (seating 29) | here |
|---|---|---|
| `echo RLXFW-LIVE-MARK` | **22 bytes** — the echo, `\r`→`\r\n` | **0 bytes** |
| `busybox reboot -f` + 9,129 ESC | **7,489 bytes**, 3,735 `^[` pairs | — |
| a bare ESC stream | — | **0 bytes** |
| Ethernet PHY | link up | **link up** (`LOWER_UP`) |

量, three probes, two payloads, all zero: `s91-dead1`, `s91-dead2`,
`s91-deadesc`. And the adapter is not the cause — `/dev/ttyUSB0` present and
free, `lsusb` shows the CP210x, `usbipd` reports Attached, and the host's
interface is `LOWER_UP`, so the board is powered and its PHY is linked.

**`NET-59`'s board was running Linux with a working line discipline. This one's
UART is not transmitting at all.** They are different faults and this file does
not merge them.

### 推 — the mechanism, with the source it rests on

讀 `rtl819x-nic.c:1187-1213`: `nic_do_arm()` writes `CPURPDCR0 ← nic_rx_ring`
and `CPURMDCR0 ← nic_mb_ring` and **does not touch `nic_rx_idx`**.
讀 `:768`: `bf = nic_dw(nic_rx_mb, i, 3)` — the buffer address is read out of the
mbuf descriptor, which is **memory the DMA engine writes**.
讀 `:772-774`: `for (k = 0; k < len; k++) skb->data[k] = __raw_readb((void
__iomem *)(bf + k));` — up to 2,046 uncached byte reads at that address, with no
validation of any kind.

With the driver one slot ahead of the engine, `bf` is read from a descriptor the
engine is concurrently rewriting. A KSEG1 read at an address the bus does not
answer is not a fault that `die()` can report — it is a bus hang — and that is
consistent with a UART that stops transmitting while the PHY stays linked.

⚠️ **推, and it is not measured.** What would settle it: `nic_last_rx_ph1/3/4`
and `nic_rx_idx` as of the moment the board stopped, which is exactly what § 1
goes to get.

---

## 1. The post-mortem, and this time the method should work

`PREDICTIONS-B31-postmortem.md` built this instrument and its own validity gate
refuted it, because the board had been unpowered ~14.5 hours and DRAM had decayed
to statistical independence (Hamming distance **47.66 / 52.15 / 53.91 %** from
the written content).

量 `MEM-17`: at **two minutes** unpowered, 1 bit of 22,976 changes. The power
interruption here is requested as **≤ 5 s**.

**The validity gate is unchanged and is quoted rather than restated**: `Q1`, `Q3`
and `Q5` must read exactly what `s91-elfread.py` derives from
`imgwork/r6if1/r6if1-20260920/kroot/vmlinux`, and `Q5` must be byte-identical to
`Q1`. **If any of them differs in one nibble, every number from `Q2` and `Q4` is
discarded and not interpreted.**

```commands
#-- Q1-TXTHI   control, before.  .text at 2 MiB in.
CAP --out bench/2026-09-20b/Q1-TXTHI --send 'DW 80200000 16' --until 'RealTek>' --seconds 15
#-- Q2-NIC     THE PAYLOAD.  the switch driver's tail plus the whole nic_* run.
CAP --out bench/2026-09-20b/Q2-NIC --send 'DW 803CF3F0 108' --until 'RealTek>' --seconds 15
#-- Q3-MAC     control, semantic: 02524c58 46570000 is NET-51's MAC.
CAP --out bench/2026-09-20b/Q3-MAC --send 'DW 8028ED50 4' --until 'RealTek>' --seconds 15
#-- Q4-WDT     rtl819x_wdt_* and rtl819x_ce_*: did the timer wheel stop too?
CAP --out bench/2026-09-20b/Q4-WDT --send 'DW 8064BC90 116' --until 'RealTek>' --seconds 15
#-- Q5-TXTHI2  control, after.  must be byte-identical to Q1-TXTHI.
CAP --out bench/2026-09-20b/Q5-TXTHI2 --send 'DW 80200000 16' --until 'RealTek>' --seconds 15
```

### Predictions, written before the power press

| | prediction | what it would mean otherwise |
|---|---|---|
| `Q1`/`Q3`/`Q5` | **exact**, and `Q5` == `Q1` | a nibble wrong ⇒ DRAM did not retain over 5 s, which would refute `MEM-17`'s own two-minute figure and is the single most surprising outcome available |
| `nic_rx_idx` (`803CF4A4`) | **out of step with the ring positions** — that is the state `N1` measured before the death | in step ⇒ the skew is not what killed it |
| `nic_last_rx_ph1` (`803CF530`) | a length field whose value does not match a 1480-byte fragment | a sane length ⇒ the header side was fine and the buffer pointer is the suspect |
| `nic_n_irq` (`803CF440`) | frozen near `N1`'s 244 | a large value ⇒ it kept taking interrupts after the console died |
| `nic_bufs` (`803CF4A0`) | `A15B8290`, unchanged | changed ⇒ the allocation itself was overwritten |
| `rtl819x_wdt_n_hw_kick` (`8064BCB8`) | 推 frozen — the timer wheel stopped, which is what `NET-59`'s did **not** do | still rising ⇒ only the UART died and the kernel lived, which would be a third distinct fault |

⚠️ **The one-sided asymmetry of `PREDICTIONS-B31-postmortem.md` § 4 still
applies**: `.bss` is KSEG0 and the counters are monotonic, so a DRAM value is a
**lower bound**. A large value confirms; a small one does not refute. The states
— `rx_idx`, the ring positions, `seen_iisr`, `bufs` — escape that, and they are
what the table above is mostly made of.

🔴 **Nothing here writes.** Five `DW`s, no `EW`, no `EB`, no `FLW`, no `J`, no
burn verb, and the reads happen **before** any upload, because an upload to
`0x80500000` would overwrite `0x80500000`–`0x805F1002` and the payload window
sits below it at `0x803CF3F0`.

---

## 2. 🔴🔴 An adversarial pass over this seating's own draft rows found more real errors than the draft had correct results, and the biggest of them dissolves `NET-59` entirely

A second reader was given the frozen cards, every capture and the driver, and
asked to refute rather than confirm. Everything below was **verified again here**
before being written down; the verification is what makes it a correction rather
than a report.

### 2.1 🔴🔴 `NET-59` was never a hang. It was a queue of 189-second `connect()` calls

量 `bench/2026-09-20/D23-ST3`: the cell **typed `cat /proc/stat`** and the board
returned **a complete `iperf3` JSON**, i.e. the output of a command typed three
cells earlier. `D18-IP5` and `D27-U50` are the same shape. And the error in every
one of them is **`unable to connect to server: Connection timed out`** —
`ETIMEDOUT` out of `connect()` — not the `control socket has closed
unexpectedly` that § 0.4 of block 30's card quotes.

讀 `include/net/tcp.h:99,130` in the tree this image was built from:
`TCP_SYN_RETRIES 5` and `TCP_TIMEOUT_INIT ((unsigned)(3*HZ))`. Six SYNs with
exponential backoff is `3 + 6 + 12 + 24 + 48 + 96` = **189 s**.

量, two completion intervals, both from committed `.timing` files and with
`FW-35`'s rule applied (a `.timing` row is written *before* its chunk, so a
byte's arrival is the **last** row with `offset <= b`):

| | typed | its JSON arrives | interval |
|---|---|---|---|
| `D15-IP2` | 02:58:30 | in `D18-IP5`'s window at t = 34.579 s → **03:01:38.6** | **188.6 s** |
| `D16-IP3` | queued; starts when `D15` ends | in `D23-ST3`'s window at t = 19.935 s → **03:04:47.9** | **189.3 s** |

**Nothing was fitted.** The second interval is between consecutive *completions*,
not between typing and completion — and getting that wrong is how this file's
author first mis-attributed it.

**What that costs:**

* 🔴 **`busybox reboot -f`, typed 03:13:15, was never executed.** It sat behind
  further 189 s runs. *"`reboot -f` 無效"* is refuted by mechanism, not by a
  measurement of `reboot`.
* 🔴 **Block 30's § 0.6 is refuted, not merely unproven.** It says the process
  blocks in `sk_stream_wait_memory()` **with no timeout**. It was in `connect()`,
  which has one, and it returned — twice, with the errno printed.
* 🔴 **The `41 vs 22` liveness gate is an "is the shell busy" gate**, not an "is
  the board alive" gate. `X45-l32k-live`'s 22 bytes were taken 35 s into a 189 s
  `connect()`. `CORRECTIONS-block30.md` § 1 promoted *the prompt came back* on
  that false premise. The promotion is still right for a different reason — a
  prompt is strictly more than an echo — but the reason given was wrong.
* 🟢 **And it unifies**: a broken RX path drops the host's SYN-ACK, so `connect()`
  runs its whole retransmit table. One 60-byte frame explains all of it. ⚠️ **推
  for seating 29** — that seating's `seen_iisr` reads `0000320E`, **without**
  bit 16, so the RX fault there is not shown to be `NET-61`'s.

### 2.2 🔴🔴 The TX-queue-death refutation was vacuous, and the fault then appeared for real

Block 30's card claims `tx_stopped 0` at 41 frames refutes TX-queue death. 量
`n_tx` per rung: `C14-f6` **214**, `C16-f14` **216**, `C17-f41` **217** — deltas
of **+2** and **+1**. The 14- and 41-frame rungs applied **no transmit load at
all** (two ARP replies), because the board was not answering. **`tx_stopped 0`
there measured nothing**, and the hypothesis as written — frames handed
back-to-back to `ndo_start_xmit` against a 4-entry ring — was never tested. The
deepest TX burst the ladder produced was six, which is the rung that worked.

🟢 **And `Z11-f6` is that hypothesis happening.** 量, five counters across three
subsystems, all **19**: `ΔFragFails` **+19**, `ΔOutDiscards` **+19**,
`n_xmit_busy` **19**, `n_tx_stop` **19**, and `n_tx_wake 8` + `n_tx_wake_race 11`
= **19**. Thirty datagrams reassembled, **eleven** replies fragmented out
(`ΔFragOKs +11`) and the host counted exactly **11**. `ΔFragCreates` is **124**;
11 × 6 = 66, so 58 fragments were created for the 19 failures — **3.05 before the
queue stops**, against `NIC_TX_DESC` = **4**.

∴ after `arm` the RX side **improved** (30/181 against `Z2`'s 21/168) and a TX
fault appeared that was not there before. `NET-63`'s three-state comparison is
therefore comparing an RX fault with an RX-plus-TX fault, and it says so now.

### 2.3 🟢 The unexplained "+1" is the best single piece of evidence in the seating

Block 30's card reports `ReasmOKs` **42** against a prediction of 41 and treats
the `+1` as noise. 量 the same capture line: `Icmp: 66 **1** 0 …` —
`InErrors` **1** — and **`InMsgs 66 = 61 + 4 + 1`**, **`InDelivers 66 = 42 + 20 +
4`**. One datagram **reassembled out of the wrong bytes and failed at ICMP.**

That is `NET-61` caught in the act at the layer above, and it also means
`218 + 42 = 260` is an identity of two compensating off-by-ones rather than a
confirmation.

### 2.4 Numbers in the draft rows that were simply wrong

| where | written | 量 |
|---|---|---|
| `MEM-18`, and § 3 of the post-mortem card | the two control reads are *"相隔約 90 秒"* | all seven `P*` captures open **18:55:22–18:55:24**; the span is **~2.4 s**. Wrong by ~37× |
| `NET-61` ③ | *"五次讀數"* at Δ4 | **four** (`C16`, `C17`, `Y6`, `Z7`); the other five rows are Δ0 |
| `NET-61` ④ | OWN at `:748`, length at `:755` | **`:751`** and **`:758`**; `bf` at `:768` was right |
| `NET-61` ④ | `nic_refill` `:1227-1234` | the two `nic_re_set` calls that hand ownership back are at **`:1239-1240`**, outside the cited range |
| `NET-62` | *"恰好等於 179"* | two of the four rungs are **180**, and `Y1`/`Y4` are 11-for-10 and 146-for-145. Four of six windows carry an unexplained `+1` |
| block 32's card | the ping count is `-w 10 ÷ -i 0.05` | that gives **200**; the measured interval is 0.0568 s, which gives 179 |
| `NET-61` ①, `notes/nic-driver.md` § 10 | *"逐位元組複製（約 1.88 MB/s）"* | `notes/nic-driver.md:701` and `LOG.md:30599` both record 1.88 MB/s as a **ping-bound floor**, not a copy rate. One owner file contradicting itself 312 lines apart |
| `NET-64` | 推 a bad KSEG1 address hangs the bus | 讀 `:1230-1234`: `bf = nic_bufs + i * NIC_BUF_SZ + NIC_RX_OFFSET` is a **pure function of `i`**, so it can only be one of eight fixed addresses, and `len` is clamped to `≤ 2046` at `:761-762`. **The mechanism has no source support and is withdrawn** |

### 2.5 🔴 And `NET-64`'s state has a contradiction the draft did not notice

`R3-BOOT` carries `RLXFW-W4=00240000` — **my watchdog armed at OVSEL 9 ≈ 84 s**,
which is the very reading block 30's card uses to prove the timer wheel lived
through `NET-59`. The console probes after `N2` ran **well past 84 s** and
returned 0 bytes. So either it bit, and the loader should then have echoed my
ESC stream (量 `X36-escwin2`: the loader echoes raw ESC, 77,655 of them) — it did
not; **or it did not bite, and the CPU was running.** Either branch costs the
"hard hang" reading.

⚠️ **And the adapter exclusion used exactly the readings `CLAUDE.md` 2026-09-17
says are NOT discriminators while the device is attached to WSL.** The one it
says *is* — a command that comes back — is the one that failed. **So the draft
was not even entitled to say the board rather than the link was at fault.**

### 2.6 Five predictions that could not have failed

Recorded because this project's rule is that a tool which cannot fail proves
nothing, and the same applies to a prediction.

* `Z9-arm` → `Z10` *"rp == rm"*: `nic_do_arm()` writes both base registers
  **unconditionally** (`:1196`, `:1204`), so reading them back at base with no
  traffic is a read-back of the driver's own store.
* `P7 == P1` presented as *"the decayed state is stable"*: the board was powered
  and refreshing throughout. It is a *the-loader-did-not-write-here* control and
  nothing more.
* `R6-BASE` *"0/0 on a fresh boot"*: no traffic had occurred.
* Block 32's `L1`/`L2` Δ predicted 0: both are at base by construction.
* `R2-HEAD == C2-HEAD` as evidence the upload landed: `R0-REBOOT` was a 2.4 s
  watchdog reset with DRAM refreshed throughout. To be evidence the card needed a
  `DW 80500000` **before** the upload.

### 2.7 🟢 And two closures the draft was entitled to and did not take

* The `+2` / `+1` residuals on `n_rx` are **ARP**: `Δn_tx` is `+2` and `+1` in
  the same windows, and `InReceives` — which excludes ARP — closes to **zero**
  residual.
* `InTruncatedPkts` is exact if taken at two levels instead of one:
  `Z2` 1008 − 857 = **151**, `Z4` 24 − 1 − 20 = **3**, **151 + 3 = 154**; and
  cumulatively block 32's 5,247 fragments + 24 unfragmented = **5,271 =
  `InReceives`**, with 221 + 875 = **1,096 = `Z1`'s `InTruncatedPkts`**, to the
  packet. ⚠️ `InTruncatedPkts` is per-**skb** (`ip_input.c:532`), so *one per
  failed datagram* compares two different units and is dropped.

---

## 3. The post-mortem ran, its gate fired, and the control is worth more than the payload

**量 2026-09-20 22:04–22:05, power cycle 2 of seating 30.** The operator turned
the board off at ~21:58 unprompted and powered it back on at ~22:04, so the
unpowered interval is **~6–7 minutes** — the start resting on their report and
the end on this desk's own timestamps. The card assumed **≤ 5 s**, so **the
experiment ran outside its own stated precondition.**

### The gate fired

| window | expected, from the ELF | read | differing bits |
|---|---|---|---|
| `Q1b-TXTHI` `80200000` | `.text` | 5 words differ | **5 / 512 = 0.977 %** |
| `Q3b-MAC` `8028ED50` | `02524c58 46570000 …` | word 2 differs | **1 / 128 = 0.781 %** |
| `Q5b-TXTHI2` | same window as `Q1b` | — | **byte-identical to `Q1b`** |

Every one of the five differences is a **single bit**.

🔴 **So `Q2b-NIC`'s and `Q4b-WDT`'s numbers are DISCARDED**, because § 1's rule,
written before the read, says *"If any one of `Q1`, `Q3` and `Q5` differs in one
nibble, every number from `Q2` and `Q4` is discarded and not interpreted."* The
captures are committed and uninterpreted; a later card with a properly derived
tolerance can read them.

Not softening it after the fact is the point. This seating already refused twice
to repair an instrument so it would agree with an experiment.

### 🟢🟢 What the control bought instead — a third point on this part's retention curve

| unpowered | bits flipped | source |
|---|---|---|
| ~2 min | 1 / 22,976 = **0.004 %** | `MEM-17` |
| **~6–7 min** | **6 / 640 = 0.938 %** | **this block** |
| 35.1 min | 598 / 22,976 = **2.603 %** | `MEM-17` |
| ~14.5 h | ≈ **50 %** (statistically independent) | `MEM-18`, `P1`–`P7` |

🟢 And `Q1b == Q5b` byte-identical again: the flips are **stable across the read
session**, which is the same control shape `P1`/`P7` gave.

### 🔴🔴 And the gate's own design is refuted by using it

A binary *one nibble and everything is discarded* cannot express **99.06 %
retained**. It was written for an interval where the answer is either 0 bits or
noise, and it was applied at an interval where the answer is a rate.

**The fix belongs on the next card, not here**: the gate must carry a **bit-count
tolerance derived from the curve above BEFORE the read**, so that "is 1 % close
enough" is answered by a number chosen in advance rather than by whoever is
looking at the screen.

### 🔴 One instrument defect, and it cost one cell

`Q1-TXTHI` came back **45 bytes with no data line**, in 0.0 s: `--until
'RealTek>'` matched the loader's **own backlog** — the `Unknown command !` /
`<RealTek>` still draining from the ESC window that had just been killed — and
ended the capture before the `DW` reply arrived.

⚠️ **The cell is kept, not `--force`d over**: `Q1b`…`Q5b` are new names, and a
four-second drain capture with no `--send` runs first. `console-capture`'s
`--until` arms after the write and cannot tell the payload's answer from
whatever the port was already about to say.

