# RESULTS — block 34, seating 32

What the block measured. The frozen card is `PREDICTIONS-B36-block34.md`;
departures from it are in `CORRECTIONS-block34.md`. Marks: 量 measured on this
device · 讀 read out of code or a dump · 推 inferred, pending a measurement.

---

## § 1 🔴 An overwrite refusal was swallowed and stale files were nearly read as measurements

量 2026-09-21. The corrected register cells of `CORRECTIONS` § 0 were re-run
under the **same output names** with the tool's output sent to `/dev/null`.
`console-capture.py` **refuses to overwrite an existing output file**; the
refusal went to the discarded stream; and the grep that followed read the
**attempt-1 files** and printed their contents as though they were new.

Four of the nine cells had new names and were written fresh; five had old names
and did not move. The printed table was internally consistent and wrong in five
of nine rows.

🔴 This is the repository's own rule one level up — `CLAUDE.md`: *"Reading a
suite's output files is a measurement, so it needs a control — and freshness is
NOT completion."* Here the instrument **said so** and the saying was discarded.

The fix used: attempt-numbered names (`-a2`), never `--force`, because the
attempt-1 files are the evidence `CORRECTIONS` § 0 quotes. The tool's stdout is
not redirected anywhere else in this block.

---

## § 2 The wedge did not come from the card's `D0-WEDGE`, and that is better

The card reproduces `NET-67` with TCP (`D0-WEDGE`). It never ran: the **`D5`
UDP ladder wedged the board on its first rung** — `-b 2M`, board as *receiver*,
carrying no bulk TX at all. The `D2`/`D5`/`D7`/`D9` cells therefore ran against
a **UDP-induced** wedge.

The card had pre-registered what that would mean: *"if a UDP receive rung wedges
the board, then board-side TX is not necessary for `NET-67`"*. Prediction (4) is
**refuted, as written**.

---

## § 3 🔴🔴 `H-POOL` and `H-FC` are refuted by direct measurement

First reading of the SWCORE descriptor-diagnostic block in this project's
history. All 量 through `/proc/rtl865x/memory`, one read per cell.

| register | address | at rest | during the wedge |
|---|---|---|---|
| `GDSR0` | `0xBB806100` | `00120013` | **`0012001E`** |
| `GDSR1` | `0xBB806104` | `00000000` | `00000000` |
| `PCSR0` | `0xBB806108` | `00000000` | `00000000` |
| `PCSR1` | `0xBB80610C` | `00000000` | `00000000` |
| `P6_DCR0` | `0xBB806170` | `00000000` | `00000000` |
| `SBFCR0` | `0xBB804500` | `000000F4` | `000000F4` |
| `CPUTPDCR0` | `0xB8010020` | `A15B8048` | `A15B804C` |
| `CPUICR` | `0xB8010000` | `C4000000` | `C4000000` |

Fields 讀 `rtl865xc_asicregs.h:761-768` and `:1734-1735`:

* `USEDDSC` (bits 25:16) = **18** at rest, **18** during the wedge
* `MaxUsedDsc` (bits 13:0) = **19** at rest, **30** across the whole episode
* `DSCRUNOUT` (bit 27), `TotalDscFctrl_Flag` (bit 26) and
  `SharedBufFCON_Flag` (bit 14) = **0**, at rest and during
* `S_DSC_RUNOUT` (`SBFCR0` bits 9:0) = `0xF4` = **244**

🔴 **`H-POOL` refuted.** 18 of 244 is **7.4 %**; the high-water mark over the
whole episode is 30 of 244 = **12.3 %**; no run-out flag ever set. The ASIC's
shared descriptor pool is nowhere near exhausted. The card's written refutation
condition was exactly this sentence.

🔴 **`H-FC` refuted.** `PCSR0` and `PCSR1` both `00000000` — no output-queue
congestion on any port, CPU port included, during the wedge.

🔴 **`S_DSC_RUNOUT` is 244 on this die, not the 480 the vendor's
`rtl865x_asicCom.c:1052` writes.** A comparison against 480 is against a
constant this part does not carry.

🟢 **`MaxUsedDsc` is not clear-on-read**: `B5-REGa-a2` and `B6-REGa2-a2` both
read `00120013` with the board at rest. The control was written to find out and
it answered no.

🟢 **`CPUTPDCR0` now has two sources sharing no code.** `B5-PAIR` reads
`tpdcr0_pos A15B8048` through the driver's `nic_rd()`; `B5-PAIR2`, seconds
later with no traffic between, reads `b8010020:  A15B8048` through the
**vendor's** `/proc/rtl865x/memory` handler. `n_tx 6`, `tx_idx 2`,
`6 mod 4 = 2`: engine slot and driver index agree at rest. All 88 previous
readings of that register came from one source.

---

## § 4 🟢 The recovery bisection — three rungs, and the fault is in the ring state

| rung | cell | what it writes | recovered? |
|---|---|---|---|
| 1 | `D5-BELL` | `CPUICR` `TXCMD` + `TXFD` doorbell **only** | ❌ ping 0/4, `tx_stopped 1`, `n_tx_wake 0`, four `txd` OWN set, `tpdcr0_pos` unmoved |
| 2 | `D7-CMD` | full `CPUICR` rewrite by plain `=` | ❌ ping 0/4, four `txd` OWN set |
| 3 | `D9-RING` | + all four ring words OWN-clear, + ring bases, + indices | 🟢 **ping 4/4, rtt 1.307 ms**, `tx_stopped` 1 → 0, `n_tx_wake` 0 → 1, four `txd` OWN **clear** |

🔴 **`H-BELL` refuted** — the doorbell was not the problem, and the source's own
refutation condition (`rtl819x-nic.c:1899-1907`) said so in advance.
🔴 **`H-CMD` refuted.**

🟢 Rung 3 recovered to **4/4**, where seating 31's recovery reached only 2/4 —
so `NET-68`'s *"the recovery is partial"* is a property of that seating's
sequence, not of `arm`.

🟢 **A new fact**: rung 2 moved `tpdcr0_pos` from `A15B804C` (slot 3) to
`A15B8040` (slot 0, the ring base) **without writing `CPUTPDCR0`** —
`nic_do_engine` touches only `0x000`, `0x028` and `0x02C`. **Cycling `TXCMD`
resets the engine's TX descriptor pointer to the ring base.**

🟢 **That narrows `arm`'s three changes to one.** Repositioning to the base is
excluded, because rung 2 did exactly that and did not recover; the index reset
is software-only and the engine cannot see it. **The OWN-clear is the only one
of the three that can have acted** — which is what the vendor's own invariant
predicts (讀 `rtl865xc_swNic.c:701-704`: `if (next_index ==
txPktDoneDescIndex[…]) return -1;` — usable depth N−1, one slot always
RISC-owned, a state this driver can and does leave). 🔴 Still 推: no verb on
this image clears one descriptor without the others.

---

## § 5 🔴🔴 The fault requires a TCP connection — six workloads, three negative controls

`notes/nic-driver.md` § 11.6 names *"whether the fault needs TCP"* as the
discriminator and says it *"was not run"*. It ran.

| workload | TCP? | in flight | small TX frames | frames each way | wedge |
|---|---|---|---|---|---|
| flood ping 1400 B (`bench/2026-09-19b/L2-after`) | ✗ | 4 | ✗ | 7,466 TX | ✗ |
| **`G1-FLOOD32`** flood ping 1400 B | ✗ | **34** | ✗ | **27,017** | **✗** |
| **`G3`** bulk flood + concurrent 18-byte ping | ✗ | 34 + 4 | **✓ (3,110)** | 21,388 | **✗** |
| `iperf3` TCP bulk (seating 31) | ✓ | — | ✓ | 26 TX | **✓** |
| `C-2M-r*` `iperf3 -u -R`, board receives | ✓ control | — | ✓ | 51 TX | **✓** |
| `E1-TXUDP` / `H5-D5r1` `iperf3 -u`, board sends | ✓ control | — | ✓ | — | **✓** |

量 `G1-FLOOD32`: **27,005 sent / 26,983 received / 0.0815 % loss / `pipe 34` /
20.852 s**; board counters `nd_stats rx 27017/38942234 tx 27017/38942234`;
`n_tx_stop 0`, `tx_stopped 0`, `n_xmit_busy 0`; all four `txd` OWN clear; ping
4/4 afterwards.

量 `G3`: 18,278 bulk + 3,110 small, concurrently, `n_tx_stop 0`, OWN clear.

**Excluded by measurement**: frame size, in-flight depth, total volume,
direction, bulk transport. **The only factor common to every wedge and absent
from every non-wedge is a TCP connection**, and in two of the six it carried no
bulk data at all. `H5-D5r1` wedged with the host-side server log **empty**, so
the control connection never completed — the TCP handshake is inside the
triggering window.

⚠️ 推, and the experiment that decides it: `iperf3` always opens a TCP control
socket, so **"a TCP connection" and "`iperf3`" are not separated here**. A raw
TCP connection with no `iperf3` — `socat` from the host against any listening
port — separates them, and it was not run. **That is the first cell of the next
seating.**

---

## § 6 The throughput number this seating obtained, and why it is not `D5`

量 `G1-FLOOD32`, host and board agreeing to the byte:

* **38,942,234 bytes in 20.852 s in each direction simultaneously**
* = **1,867,505 B/s = 1.868 MB/s = 14.94 Mbit/s each way**
* = **29.88 Mbit/s aggregate**, at **0.0815 % loss**
* board's own counters: `rx 27017/38942234`, `tx 27017/38942234`

🔴 **This does not satisfy `D5`.** `PROGRESS.md:128` names `iperf3` and nothing
else; a `ping`-derived figure fails the **tool** clause. It is recorded as what
it is: the first measured throughput of this driver, by a method the DoD does
not name.

🟢 It lands inside the bracket derived at the desk, before this run, from
seating 31's `-s` fragment ladder: **24.7–33.1 Mbit/s** aggregate.

---

## § 7 🟢 The loud image makes the fault announce itself

量, from `H3-ECHO` onward: with `CONFIG_PRINTK=y` a wedged board prints

```
[  546.000000] Virtual device rlx0 asks to queue packet!
```

every **1.06 s**, ratelimited. 讀 `net/core/dev.c`, `dev_queue_xmit()`: that is
the `q->enqueue == NULL` branch taken when `netif_tx_queue_stopped()` is true —
the printed composition of `NET-57` (`tx_queue_len = 0` makes `rlx0` a
`noqueue` device) with the wedge. Every outbound packet is dropped there.

**On the quiet image the interface dies silently; on the loud image the kernel
says so once a second.** A second, diagnostic reason for `D6` to need the loud
variant, independent of the DoD's wording.

---

## § 8 🔴 A three-state reading of the state `NET-64` calls "mute"

量, `H7-REC2` and `H8-ECHO`, loud image:

| layer | state | evidence |
|---|---|---|
| kernel | **alive** | ratelimited `printk` every 1.06 s, continuously |
| tty | **alive** | the full 101-character command line echoed back |
| shell | **not executing** | `echo RLXFW-PROBE-E` returns **one** line (the echo) and not two — and `echo` is an ash **builtin**, needing no `fork` and touching no `/proc` |

推, with the experiment that decides it: `printk` reaches the wire through
`prom_putchar`, a polled write that bypasses the tty layer; a userspace write
enters the tty ring buffer and needs the UART **TX interrupt** to drain. A shell
blocked on `write()` while polled `printk` still works is what a lost UART TX
interrupt looks like. **Reading `/proc/interrupts`' serial line across the
transition would settle it, and it was not read.**

🔴 It also explains why `reboot -f` cannot work there — the shell never executes
it — reproducing seating 31's *"7,489 bytes captured, all of it ESC"*. This
seating: **7,883 bytes, all ESC**.

---

## § 9 🔴 A capture returning 0 bytes is NOT evidence of silence during this fault

量, four times: register cells with a 10 s window returned **0 bytes**, and a
single 35 s window afterwards delivered **all eight** of their outputs in order,
plus two full `/proc` dumps and an earlier echo probe. The console backlog
during and after the wedge exceeds 10 s and can exceed 30 s.

Every empty capture in this block was re-taken with a longer window before
anything was concluded from it. The card's § 3 rule 8 — *if the console goes
silent, take a read-only capture first* — becomes sharper: **take a LONGER one,
and never read a short empty window as silence.**

⚠️ **And the mirror of it, which cost a `looprun` invocation.** A byte count was
read as a boot: after the second request to power-cycle, `J0-COLD` returned
**7,792** bytes and that was taken as evidence the board had rebooted. The
uptime stamps inside it — `[914.38]`, `[915.45]`, `[920.29]` — **continue from
`[839.10]` in the previous capture**, so the board had never lost power.
`looprun` then stopped at `S5` with `rc=1` because there was no loader prompt,
and **nothing was uploaded**. 🟢 The guard caught what the byte count did not.
The test used afterwards is the presence of `Booting...` and `ramSize: 32M` and
the absence of `Reboot Result from Watchdog Timeout!`, never a byte count.

---

## § 10 🟢 Three second sources the loud image handed over for free

量, `F1-boot.log`, which is **7,714 bytes** against the quiet image's
**1,874** (+5,840):

* `CPU revision is: 0000cd01` — the kernel's own `PRId`, agreeing with
  `SPEC.md`'s `RLX4181` revision 1, by a route that reads the register rather
  than a vendor header's table.
* `icache: 16kB/16B, dcache: 8kB/16B, scache: 0kB/0B` — agreeing with
  `probe3`'s **experimentally** measured 16 KiB / 16-byte-line I-cache, by a
  completely different method.
* `Calibrating delay loop... 398.95 BogoMIPS (lpj=1994752)` — agreeing with the
  loader banner's `(400MHz)`.

---

## § 11 `D5` and `D6`

🔴 **`D5` NOT OBTAINED, and for the first time the reason is a mechanism rather
than a new suspect.** `PROGRESS.md:128` names `iperf3`; `iperf3` always opens a
TCP control socket; and § 5 measures that a TCP connection is the one factor
present in every wedge and absent from every non-wedge. Five `iperf3`
invocations this seating, five wedges, one of them before the control
connection completed.

🟢🟢 **`D6` IS MET, on all three conjuncts, and the flood is the largest thing
this project has ever moved through its own driver.**

量, image `s31L` (`CONFIG_PRINTK=y`), host `ping -f -w 1800 -l 32 -s 1400`:

| | |
|---|---|
| duration | **1,899.593 s = 31.66 min** |
| host | **2,450,381 sent / 2,450,254 received / +7 duplicates / 0.00518 % loss**, `pipe 37`, rtt 1.476 / 17.313 / 2089.468 ms |
| board RX | **2,450,491 frames / 3,533,456,154 bytes** |
| board TX | **2,450,389 frames / 3,533,309,070 bytes** |
| both ways | **7,066,765,224 bytes = 7.067 GB** |
| **driver drops** | **`drop 0/0`** |
| ring at the end | `n_tx_stop 0`, `tx_stopped 0`, `n_xmit_busy 0`, `n_skb_fail 0`, all four `txd` OWN **clear**, `len 1446` |
| console over the flood | **0 bytes**, `sent: null`, `duration_s 1860.084442`, `stop_reason "--seconds 1860.0 elapsed"` |

Re-derived here rather than copied: `3,533,456,154 ÷ 1,899.593` =
**1,860,112 B/s = 14.881 Mbit/s** receiving; `3,533,309,070 ÷ 1,899.593` =
**1,860,035 B/s = 14.880 Mbit/s** transmitting; **29.761 Mbit/s aggregate**, at
**1,290 frames/s each way**, sustained for 31.66 minutes.

🟢 **That is 0.4 % from `G1-FLOOD32`'s 14.94 Mbit/s**, measured over a run
**91× shorter**. The rate is a property of the path and not of the sample.

The three conjuncts:

1. **zero drops by the driver's own counters** — `drop 0/0`. ⚠️ And the project
   already knows this instrument is blind to loss above it (`NET-62`), so the
   host's **0.00518 %** is quoted beside it rather than instead of it.
2. **zero oops** — on a `PRINTK=y` image the console produced **0 bytes**. An
   oops prints; a wedge prints `Virtual device rlx0 asks to queue packet!` every
   1.06 s (§ 7). Neither appeared.
3. **kernel log captured whole rather than grepped** — one unbroken read-only
   capture, no `--send`, `sent: null` in its own metadata.

🔴 **And the honest limit on conjunct 3, which is mine and not the board's.**
The capture ran **1,860.084 s** and the flood ran **1,899.593 s** — `ping -w`
is a deadline it overshoots while waiting for outstanding replies. **The last
39.5 s of the flood were not captured: 97.9 % coverage, not 100 %.** `F6-POST`,
taken immediately after, shows `drop 0/0` and a clean ring, so nothing
catastrophic happened in that window — **but an oops inside those 39 seconds
would not have been recorded.** The fix is one number: the capture's `--seconds`
must exceed the flood's `-w` by more than the overshoot, and the overshoot is
now measured at **99.6 s** on this path.

🔴 **A second observation, 未定, taken after the flood.** `F8-PING` and three
more pings afterwards return **0/4**, while: ARP resolves (`10.1.1.3 lladdr
02:52:4c:58:46:57 REACHABLE`), the driver reports `n_tx_stop 0` / `tx_stopped 0`
/ OWN clear, and `nd_stats` keeps **advancing in both directions** across the
attempts (`rx 2450511 → 2450517`, `tx 2450401 → 2450404` over four pings).
**So this is not `NET-67`** — the TX path works and the board answers ARP. What
it is, is undetermined: one observation, immediately after 2.45 million frames,
with `+6 rx / +3 tx` for four echo requests, which does not cleanly separate
*no reply generated* from *reply generated and lost*. ⚠️ `busybox`'s `grep` has
no `/bin/` symlink on this image (`FW-96`), so `/proc/net/snmp`'s ICMP counters
— the reading that would settle it — could not be filtered on the board and
were not taken whole.

---

## § 12 Zero flash writes

No `FLW`, `EW`, `EB` or burn command was issued. `AUTOBURN` was read back at
`0x8040D4A0` as `00000000` by `looprun`'s `S5b` before each upload, and every
upload landed at `0x80500000`, which is RAM.

🔴 **That is not the same sentence as "not one flash byte is written".** No
`FLR` bracket ran in this block, so the bracket stands at **1,024 of 4,194,304
= 0.0244 %** and `FLS-26`'s ledger does not move.
